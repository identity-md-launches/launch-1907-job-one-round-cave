"""Behavioral checks; fixtures remain under test/scratch/."""
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().with_name('duplicates.py')
spec = importlib.util.spec_from_file_location('duplicates', SOURCE)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        root = Path('test/scratch')
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'input.csv'

    def write(self, rows):
        with self.path.open('w', encoding='utf-8', newline='') as stream:
            csv.writer(stream).writerows(rows)

    def test_identical_is_still_ambiguous(self):
        self.write([['id', 'v'], ['a', '2'], ['a', '2']])
        report = d.inspect(self.path, ['id'])
        self.assertFalse(report['clean'])
        self.assertEqual(report['summary']['identical_duplicate_groups'], 1)
        self.assertEqual(report['findings'][0]['fields']['v'],
                         [{'value': '2', 'records': [2, 3], 'count': 2}])

    def test_conflicting_columns_and_all_occurrences(self):
        self.write([['id', 'v', 'same'], ['a', '2', 'x'], ['a', '3', 'x'], ['a', '2', 'x']])
        group = d.inspect(self.path, ['id'])['findings'][0]
        self.assertEqual(group['differing_columns'], ['v'])
        self.assertEqual(group['fields']['v'][0]['records'], [2, 4])
        self.assertEqual(group['fields']['same'][0]['records'], [2, 3, 4])

    def test_empty_singleton(self):
        self.write([['id', 'v'], ['', '2']])
        r = d.inspect(self.path, ['id'])
        self.assertEqual(r['summary']['empty_key_groups'], 1)
        self.assertEqual(r['findings'][0]['duplicate_kind'], 'singleton')

    def test_composite_key(self):
        self.write([['id', 'place'], ['a', 'x'], ['a', 'y']])
        self.assertTrue(d.inspect(self.path, ['id', 'place'])['clean'])
        self.assertFalse(d.inspect(self.path, ['id'])['clean'])

    def test_strings_not_normalized(self):
        self.write([['id', 'v'], ['01', '2'], ['1', '2'], [' 1', '2']])
        self.assertTrue(d.inspect(self.path, ['id'])['clean'])

    def test_logical_records_multiline_and_quoting(self):
        self.write([['id', 'v'], ['a', 'first\nsecond'], ['a', 'comma,quote"']])
        g = d.inspect(self.path, ['id'])['findings'][0]
        self.assertEqual(g['records'], [2, 3])
        self.assertEqual({v['value'] for v in g['fields']['v']}, {'first\nsecond', 'comma,quote"'})

    def test_controls_escaped_in_text(self):
        self.write([['id', '\x1b[31m'], ['a', 'x\ny'], ['a', 'z']])
        text = d.render_text(d.inspect(self.path, ['id']))
        self.assertNotIn('\x1b', text)
        self.assertIn('\\u001b', text)
        self.assertIn('x\\ny', text)

    def test_invalid_key_requests(self):
        self.write([['id'], ['a']])
        for keys in ([], [''], ['id', 'id'], ['missing']):
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                d.inspect(self.path, keys)

    def test_invalid_csv(self):
        for body in ('id,id\na,b\n', 'id,v\na\n', 'id,v\n"unterminated'):
            self.path.write_text(body)
            with self.subTest(body=body), self.assertRaises(ValueError):
                d.inspect(self.path, ['id'])

    def test_header_only(self):
        self.write([['id', 'v']])
        self.assertTrue(d.inspect(self.path, ['id'])['clean'])

    def test_cli_statuses_and_read_only(self):
        self.write([['id'], ['a'], ['a']])
        original = self.path.read_bytes()
        for key, expected in [('id', 1), ('absent', 2)]:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(d.main([str(self.path), '--key', key]), expected)
        self.assertEqual(self.path.read_bytes(), original)
        self.write([['id'], ['a']])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(d.main([str(self.path), '--key', 'id']), 0)
        self.assertTrue(json.loads(out.getvalue())['clean'])

    def test_empty_duplicate_is_counted_in_both_categories(self):
        self.write([['id', 'v'], ['', 'x'], ['', 'y']])
        s = d.inspect(self.path, ['id'])['summary']
        self.assertEqual((s['empty_key_groups'], s['conflicting_duplicate_groups'], s['finding_groups']), (1, 1, 1))


if __name__ == '__main__':
    unittest.main()
