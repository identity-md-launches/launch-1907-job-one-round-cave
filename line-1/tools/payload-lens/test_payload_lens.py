import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import payload_lens as lens


ROOT = Path(__file__).resolve().parents[3]
REAL = ROOT / 'line-1/tools/endpoint-doctor/observed-live.json'


class PayloadLensTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = json.loads(REAL.read_text())

    def test_real_swarm_capture_meets_declared_contract(self):
        result = lens.analyze(self.real, 'application/json', True, 1)
        self.assertEqual(result['outcome'], 'matches')
        self.assertEqual([f['state'] for f in result['findings']], ['match'] * 3)
        self.assertEqual(result['findings'][0]['evidence'], '/probe/hops/0/content_type')

    def test_status_pass_with_html_type_is_mismatch(self):
        report = copy.deepcopy(self.real)
        report['probe']['hops'][0]['content_type'] = 'text/html; charset=utf-8'
        result = lens.analyze(report, 'application/json', True)
        self.assertEqual(result['outcome'], 'mismatch')
        self.assertEqual(result['findings'][0]['observed'], 'text/html')

    def test_json_header_without_body_validation_is_unknown(self):
        report = copy.deepcopy(self.real)
        report['probe']['checks'].pop()
        result = lens.analyze(report, 'application/json', True)
        self.assertEqual(result['outcome'], 'unknown')
        self.assertEqual(result['findings'][1]['state'], 'unknown')

    def test_zero_body_fails_minimum(self):
        report = copy.deepcopy(self.real)
        report['probe']['hops'][0]['body_bytes'] = 0
        result = lens.analyze(report, min_bytes=1)
        self.assertEqual(result['outcome'], 'mismatch')

    def test_underlying_failed_status_cannot_become_contract_pass(self):
        report = copy.deepcopy(self.real)
        report['probe']['ok'] = False
        report['ok'] = False
        report['probe']['hops'][0]['status'] = 404
        report['probe']['checks'][0].update(actual=404, ok=False)
        result = lens.analyze(report, 'application/json', True)
        self.assertEqual(result['outcome'], 'source_failed')

    def test_json_error_is_incomplete_even_with_body_metadata(self):
        report = copy.deepcopy(self.real)
        report['probe']['ok'] = False
        report['ok'] = False
        report['probe']['error'] = {'kind': 'json', 'message': 'bad body'}
        report['probe']['checks'].pop()
        result = lens.analyze(report, 'application/json', True)
        self.assertEqual(result['outcome'], 'incomplete')
        self.assertEqual(result['findings'][0]['evidence'], '/probe/error')

    def test_watchdog_without_probe_is_unobserved(self):
        result = lens.analyze({'schema': 'deadline-sentry/v1', 'ok': False}, 'application/json')
        self.assertEqual(result['outcome'], 'unobserved')

    def test_invalid_evidence_is_rejected(self):
        cases = []
        for change in (
            lambda p: p['probe'].update(ok=True, error={'kind': 'body'}),
            lambda p: p['probe']['hops'][0].update(body_sha256='bad'),
            lambda p: p['probe']['hops'][0].update(status=True),
            lambda p: p['probe'].update(final_url='https://different.example/'),
            lambda p: p['probe']['checks'][0].update(ok=1),
            lambda p: p.update(ok=False),
            lambda p: p['probe']['checks'][0].update(actual=404, ok=True),
        ):
            report = copy.deepcopy(self.real)
            change(report)
            cases.append(report)
        for report in cases:
            with self.subTest(report=report['probe']):
                with self.assertRaises(ValueError):
                    lens.analyze(report, 'application/json')

    def test_media_and_expectation_syntax(self):
        self.assertEqual(lens.media_type('Application/JSON; charset=utf-8'), 'application/json')
        self.assertIsNone(lens.media_type('unknown'))
        for media in ('*/json', 'application/json; charset=utf-8', 'bad\nvalue'):
            with self.assertRaises(ValueError):
                lens.analyze(self.real, media)
        with self.assertRaises(ValueError):
            lens.analyze(self.real)
        with self.assertRaises(ValueError):
            lens.analyze(self.real, min_bytes=-1)

    def test_strict_json_rejects_duplicates_and_nonfinite(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'):
            with self.assertRaises(ValueError):
                lens.strict_json(raw)

    def test_cli_on_real_saved_report(self):
        command = [sys.executable, '-B', str(Path(lens.__file__).resolve()),
                   str(REAL), '--media', 'application/json', '--json-check', '--min-bytes', '1']
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['outcome'], 'matches')


if __name__ == '__main__':
    unittest.main()
