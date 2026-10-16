"""Behavioral checks for the HTTP/CSV response-contract handoff."""
import csv
import io
from pathlib import Path
import tempfile
import unittest

import payload_contract as tool


SOURCE = 'line-1/tools/endpoint-doctor/observed-live.json'


class PayloadContractChecks(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def save(self, name, content):
        path = self.root / name
        path.write_text(content)
        return path

    def test_retained_real_probe_and_equal_comparison(self):
        csv_text, judgment = tool.snapshot(SOURCE, 'application/json', True, 1)
        self.assertEqual(judgment['outcome'], 'matches')
        row = next(csv.DictReader(io.StringIO(csv_text)))
        self.assertEqual(row['url'], 'https://api.imd.fun/launches')
        self.assertEqual(row['source_ok'], 'true')
        self.assertEqual(row['body_state'], 'match')
        self.assertNotIn('"launches"', csv_text)
        baseline = self.save('baseline.csv', csv_text)
        result = tool.compare(baseline, baseline)
        self.assertTrue(result['complete'])
        self.assertTrue(result['comparison']['equal'])

    def test_changed_expectation_is_explained_by_exact_key(self):
        before, _ = tool.snapshot(SOURCE, 'application/json', True, 1)
        after, judgment = tool.snapshot(SOURCE, 'text/html', True, 1)
        self.assertEqual(judgment['outcome'], 'mismatch')
        report = tool.compare(self.save('before.csv', before), self.save('after.csv', after))
        self.assertTrue(report['complete'])
        self.assertEqual(report['comparison']['summary']['changed'], 1)
        fields = report['comparison']['changed'][0]['fields']
        self.assertIn('outcome', fields)
        self.assertIn('expected_media', fields)
        self.assertIn('media_state', fields)

    def test_duplicate_url_is_explained_without_pairing(self):
        baseline, _ = tool.snapshot(SOURCE, 'application/json', True, 1)
        rows = baseline.splitlines(keepends=True)
        duplicate = self.save('duplicate.csv', baseline + rows[1])
        report = tool.compare(self.save('single.csv', baseline), duplicate)
        self.assertFalse(report['complete'])
        self.assertEqual(report['comparison']['summary']['ambiguous_keys'], 1)
        review = report['duplicate_review']['after']
        self.assertEqual(review['summary']['identical_duplicate_groups'], 1)
        self.assertEqual(review['findings'][0]['records'], [2, 3])

    def test_workspace_and_json_refusals(self):
        with self.assertRaises(ValueError):
            tool.snapshot('/tmp/outside-report.json', 'application/json')
        malformed = self.save('duplicate.json', '{"schema":1,"schema":2}')
        with self.assertRaises(ValueError):
            tool.snapshot(malformed, 'application/json')


if __name__ == '__main__':
    unittest.main()
