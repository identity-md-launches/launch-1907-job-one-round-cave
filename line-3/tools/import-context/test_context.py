"""Behavioral tests; fixtures stay under workspace test/scratch, never execute."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('context_tool', Path(__file__).with_name('context.py'))
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


class ContextTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def scan(self, source, more=None):
        (self.root / 'app.py').write_bytes(source if isinstance(source, bytes) else source.encode())
        for name, text in (more or {}).items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        return C.analyze(self.root)

    def imports(self, result):
        return next(m['imports'] for m in result['map']['modules'] if m['module'] == 'app')

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = C.main([str(self.root), '--json', *args])
        return code, json.loads(out.getvalue())

    def test_nested_branch_order_and_local_resolution(self):
        r = self.scan('import base\nclass A:\n def method(self):\n  if ready:\n   from pkg import child\n  else:\n   import base\n',
                      {'base.py': '', 'pkg/__init__.py': '', 'pkg/child.py': ''})
        sites = self.imports(r)
        self.assertEqual(sites[0]['contexts'], [])
        self.assertEqual(sites[1]['resolved'], 'pkg.child')
        self.assertEqual([(x['kind'], x['branch'], x['line']) for x in sites[1]['contexts']],
                         [('ClassDef', 'body', 2), ('FunctionDef', 'body', 3), ('If', 'body', 4)])
        self.assertEqual(sites[2]['contexts'][-1]['branch'], 'orelse')
        self.assertEqual(r['context_summary'], {'import_sites': 3, 'nested_sites': 2, 'module_body_sites': 1})

    def test_guard_labels_do_not_claim_truth_or_follow_aliases(self):
        r = self.scan('if TYPE_CHECKING:\n import a\nelse:\n import b\nif typing.TYPE_CHECKING:\n import c\nif TC:\n import d\nif not TYPE_CHECKING:\n import e\nif "__main__" == __name__:\n import f\n')
        contexts = [site['contexts'][-1] for site in self.imports(r)]
        self.assertEqual([c['guard'] for c in contexts],
                         ['type_checking_spelling'] * 3 + ['condition', 'condition', 'main_guard'])
        self.assertEqual(contexts[1]['branch'], 'orelse')
        self.assertIn('not whether', r['scope'])

    def test_try_handlers_else_finally_remain_distinct(self):
        r = self.scan('try:\n import a\nexcept ImportError:\n import b\nelse:\n import c\nfinally:\n import d\n')
        self.assertEqual([[x['branch'] for x in i['contexts']] for i in self.imports(r)],
                         [['body'], ['handlers', 'body'], ['orelse'], ['finalbody']])
        self.assertEqual(self.imports(r)[1]['contexts'][1]['kind'], 'ExceptHandler')

    def test_match_async_loop_with_and_loop_else(self):
        r = self.scan('async def f():\n async for x in items:\n  async with x:\n   import a\n else:\n  import b\n match value:\n  case 1 if guard:\n   import c\n')
        sites = self.imports(r)
        self.assertEqual([x['kind'] for x in sites[0]['contexts']],
                         ['AsyncFunctionDef', 'AsyncFor', 'AsyncWith'])
        self.assertEqual(sites[1]['contexts'][-1]['branch'], 'orelse')
        self.assertEqual([x['kind'] for x in sites[2]['contexts']],
                         ['AsyncFunctionDef', 'Match', 'match_case'])
        self.assertEqual(sites[2]['contexts'][-1]['line'], 8)

    def test_duplicate_same_line_imports_keep_columns_and_aliases(self):
        r = self.scan('if ready: import a, b as bee; import a\nfrom pkg import c, c as see\n',
                      {'pkg/__init__.py': '', 'pkg/c.py': ''})
        sites = self.imports(r)
        self.assertEqual([s['target'] for s in sites], ['a', 'a', 'b', 'pkg import c', 'pkg import c'])
        self.assertEqual([s['column'] for s in sites[:3]], [10, 30, 10])
        self.assertTrue(all(s['contexts'] for s in sites[:3]))
        self.assertEqual([s['resolved'] for s in sites[3:]], ['pkg.c', 'pkg.c'])

    def test_encoded_source_hash_and_no_execution(self):
        marker = self.root / 'executed'
        source = ('# coding: latin-1\n# caf\xe9\n' +
                  f'open({str(marker)!r}, "w").write("bad")\n' +
                  'def f():\n import child\n').encode('latin-1')
        r = self.scan(source, {'child.py': ''})
        self.assertEqual(r['inventory']['manifest'][0]['sha256'], hashlib.sha256(source).hexdigest())
        self.assertEqual(self.imports(r)[0]['line'], 5)
        self.assertFalse(marker.exists())
        self.assertEqual(self.cli('--strict')[0], 0)

    def test_issues_cycles_dynamic_and_collision_preserved(self):
        r = self.scan('import app\n__import__("unknown")\n',
                      {'bad.py': '\x00', 'pkg.py': 'import shadow\n', 'pkg/__init__.py': 'import app\n'})
        self.assertEqual({i['type'] for i in r['map']['issues']}, {'parse_error', 'module_collision'})
        self.assertEqual(r['map']['cycles'], [['app']])
        self.assertEqual(r['map']['modules'][0]['dynamic_import_lines'], [2])
        self.assertNotIn('shadow', [i['target'] for m in r['map']['modules'] for i in m['imports']])
        self.assertEqual(self.cli('--strict')[0], 1)
        self.assertIn('Dynamic call:', C.format_text(r))
        self.assertIn('Issue:', C.format_text(r))

    def test_budget_refusal_has_no_partial_report(self):
        self.scan('import b\n', {'b.py': ''})
        for args in [('--max-files', '1'), ('--max-file-bytes', '1'),
                     ('--max-total-bytes', '1'), ('--max-entries', '1'), ('--max-depth', '0')]:
            code, result = self.cli(*args)
            self.assertEqual(code, 2)
            self.assertEqual(set(result), {'status', 'error'})
        code, result = self.cli('--max-files', '1')
        self.assertEqual(result['error']['type'], 'budget_exceeded')

    def test_empty_root_and_root_initializer_are_honest(self):
        (self.root / '__init__.py').write_text('import os\n')
        result = C.analyze(self.root)
        self.assertEqual(result['context_summary']['import_sites'], 0)
        self.assertEqual(result['inventory']['files'], 1)
        self.assertEqual(result['map']['modules'], [])

    def test_snapshot_matches_original_mapper_without_context_fields(self):
        r = self.scan('import core\nif flag:\n import missing\n', {'core.py': 'import app\n'})
        budget = C.load_budget()
        sources, _ = budget.collect(self.root, budget.DEFAULTS, budget.load_mapper().SKIP_DIRS)
        expected = budget.load_mapper().inspect(self.root, source_bytes=sources)
        for module in r['map']['modules']:
            for site in module['imports']:
                site.pop('contexts')
                site.pop('column')
        self.assertEqual(r['map'], expected)


if __name__ == '__main__':
    unittest.main()
