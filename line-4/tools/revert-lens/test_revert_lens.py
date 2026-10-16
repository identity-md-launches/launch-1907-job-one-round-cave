import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import revert_lens as tool


def word(n):
    return n.to_bytes(32, 'big')


def error(name, *types):
    return {'type': 'error', 'name': name, 'inputs': [{'type': t} for t in types]}


class RevertLensTests(unittest.TestCase):
    def test_independent_standard_reason_layout(self):
        data = bytes.fromhex('08c379a0') + word(32) + word(4) + b'oops' + bytes(28)
        result = tool.decode_revert([], data)
        self.assertEqual(result['signature'], 'Error(string)')
        self.assertEqual(result['arguments'][0]['value'], 'oops')
        self.assertEqual(result['status'], 'decoded')

    def test_empty_and_unicode_reasons(self):
        for text in ['', 'ZTO: \u26a0']:
            raw = text.encode()
            data = bytes.fromhex('08c379a0') + word(32) + word(len(raw)) + raw
            data += bytes(-len(raw) % 32)
            self.assertEqual(tool.decode_revert([], data)['arguments'][0]['value'], text)

    def test_panic_and_unknown_code(self):
        for code, description in [(0x11, 'arithmetic overflow or underflow'),
                                  (0x32, 'array or bytes index out of bounds'),
                                  (0xff, 'unrecognized panic code')]:
            result = tool.decode_revert([], bytes.fromhex('4e487b71') + word(code))
            self.assertEqual(result['panic']['code_hex'], hex(code))
            self.assertEqual(result['panic']['description'], description)

    def test_published_custom_error_example(self):
        # Solidity ABI spec: InsufficientBalance(uint256,uint256), 0xcf479181.
        data = bytes.fromhex('cf479181') + word(0) + word(10**18)
        result = tool.decode_revert([error('InsufficientBalance', 'uint256', 'uint256')], data)
        self.assertEqual(result['signature'], 'InsufficientBalance(uint256,uint256)')
        self.assertEqual([p['value'] for p in result['arguments']], [0, 10**18])

    def test_real_token_address_is_only_fixture_data(self):
        entries = json.loads(Path(__file__).with_name('token-errors.json').read_text())
        # ZTO is the fixture's address value, not an observed sender or balance.
        data = bytes.fromhex('e450d38c') + bytes.fromhex('00'*12 + 'd782bdea4ef02a0bd391eb9089470c8080f0a68e')
        result = tool.decode_revert(entries, data + word(12) + word(13))
        self.assertEqual(result['signature'], 'ERC20InsufficientBalance(address,uint256,uint256)')
        self.assertEqual(result['arguments'][0]['value'], '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e')
        self.assertEqual(result['arguments'][1]['value'], 12)

    def test_unknown_empty_and_truncated(self):
        self.assertEqual(tool.decode_revert([], b'')['status'], 'empty')
        self.assertEqual(tool.decode_revert([], bytes.fromhex('12345678'))['status'], 'unknown')
        for n in [1, 2, 3]:
            with self.assertRaisesRegex(ValueError, 'shorter'):
                tool.decode_revert([], b'\x12' * n)
        with self.assertRaises(ValueError):
            tool.decode_revert([], bytes.fromhex('4e487b71'))

    def test_known_collision_never_disambiguated_by_payload(self):
        entries = [error('burn', 'uint256'), error('collate_propagate_storage', 'bytes16')]
        result = tool.decode_revert(entries, bytes.fromhex('42966c68') + word(1))
        self.assertEqual(result['status'], 'ambiguous')
        self.assertEqual(result['signatures'], ['burn(uint256)', 'collate_propagate_storage(bytes16)'])
        self.assertNotIn('arguments', result)

    def test_duplicates_and_builtin_declarations(self):
        with self.assertRaisesRegex(ValueError, 'duplicate error signature'):
            tool.error_index([error('No', 'uint'), error('No', 'uint256')])
        result = tool.decode_revert(tool.BUILTINS, bytes.fromhex('4e487b71') + word(1))
        self.assertEqual(result['signature'], 'Panic(uint256)')

    def test_unsupported_error_refuses_incomplete_selector_index(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            tool.decode_revert([error('Other', 'bytes[]')], bytes.fromhex('4e487b71') + word(1))
        # Function and event type support do not affect the error inventory.
        entries = [{'type': 'function', 'name': 'f', 'inputs': [{'type': 'bytes[]'}]}]
        self.assertEqual(tool.decode_revert(entries, b'')['status'], 'empty')

    def test_strict_rejections(self):
        selector = bytes.fromhex('08c379a0')
        good = selector + word(32) + word(1) + b'x' + bytes(31)
        malformed = [good + word(0), good[:-1], good[:-1]+b'x',
                     selector + word(64) + word(0) + good[36:],
                     selector + word(0) + word(0),
                     selector + word(32) + word(1) + b'\xff' + bytes(31)]
        for data in malformed:
            with self.subTest(data=data.hex()), self.assertRaises(ValueError):
                tool.decode_revert([], data)

    def test_zero_argument_and_nested_tuple_errors(self):
        entry = error('Stopped')
        signature = 'Stopped()'
        selector = tool.abi.keccak256(signature.encode())[:4]
        self.assertEqual(tool.decode_revert([entry], selector)['arguments'], [])
        entry = {'type': 'error', 'name': 'Detail', 'inputs': [
            {'type': 'tuple', 'components': [{'type': 'uint256'}, {'type': 'string'}]}]}
        selector = tool.abi.keccak256(b'Detail((uint256,string))')[:4]
        data = selector + word(32) + word(7) + word(64) + word(2) + b'hi' + bytes(30)
        self.assertEqual(tool.decode_revert([entry], data)['arguments'][0]['value'], [7, 'hi'])

    def test_budgets_and_schema(self):
        with self.assertRaisesRegex(ValueError, '256 error entries'):
            tool.error_index([error('E'+str(i)) for i in range(257)])
        with self.assertRaisesRegex(ValueError, 'byte ABI budget'):
            tool.decode_revert([], bytes(tool.abi.MAX_DATA_BYTES + 5))
        p = {'type': 'uint256'}
        for _ in range(33):
            p = {'type': 'tuple', 'components': [p]}
        with self.assertRaisesRegex(ValueError, '32 levels'):
            tool.error_index([{'type':'error', 'name':'E', 'inputs':[p]}])
        for entries in [{}, [None], [error('bad name')]]:
            with self.assertRaises(ValueError):
                tool.error_index(entries)

    def test_workspace_reader_and_clean_cli_failures(self):
        with tempfile.TemporaryDirectory(dir='test/scratch') as tmp:
            path = Path(tmp)/'abi.json'
            cases = [('{}', '0x', 2), ('[]', '0x', 1),
                     ('[]', '0x12345678', 1), ('[]', '0xno', 2),
                     ('[]', '0x4e487b71' + word(0x12).hex(), 0),
                     ('[{"type":"error","name":"A","name":"B"}]', '0x', 2)]
            for raw, data, status in cases:
                path.write_text(raw)
                out, err = io.StringIO(), io.StringIO()
                with patch('sys.argv', ['lens', '--abi', str(path), '--data', data]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    self.assertEqual(tool.main(), status)
                if status == 2:
                    self.assertEqual(out.getvalue(), '')
                    self.assertTrue(err.getvalue().startswith('error:'))
                    self.assertNotIn('Traceback', err.getvalue())
                else:
                    self.assertEqual(err.getvalue(), '')
                    json.loads(out.getvalue())
            path.write_bytes(b' ' * (tool.abi.MAX_ABI_BYTES + 1))
            with self.assertRaisesRegex(ValueError, '1 MiB'):
                tool.read_abi(path)
        # Refuses the path before any read; no outside file is inspected.
        with self.assertRaisesRegex(ValueError, 'inside the current workspace'):
            tool.read_abi(Path.cwd().parent / 'nonexistent-abi.json')


if __name__ == '__main__':
    unittest.main()
