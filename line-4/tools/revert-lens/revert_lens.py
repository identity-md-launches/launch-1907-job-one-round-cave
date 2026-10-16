#!/usr/bin/env python3
"""Interpret supplied Solidity revert bytes offline, without guessing collisions."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

CODEC = Path(__file__).resolve().parents[1] / 'abi-workbench' / 'abi_workbench.py'
spec = importlib.util.spec_from_file_location('line4_revert_codec', CODEC)
abi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(abi)

BUILTINS = [
    {'type': 'error', 'name': 'Error', 'inputs': [{'name': 'reason', 'type': 'string'}]},
    {'type': 'error', 'name': 'Panic', 'inputs': [{'name': 'code', 'type': 'uint256'}]},
]
PANICS = {
    0x00: 'generic compiler panic',
    0x01: 'assertion failed',
    0x11: 'arithmetic overflow or underflow',
    0x12: 'division or modulo by zero',
    0x21: 'invalid enum conversion',
    0x22: 'incorrectly encoded storage byte array',
    0x31: 'pop on an empty array',
    0x32: 'array or bytes index out of bounds',
    0x41: 'excessive memory allocation',
    0x51: 'call to an uninitialized internal function',
}
MAX_ERRORS = 256
NOTICE = ('Interpretation of supplied bytes only; error data can be fabricated or '
          'propagated from another contract. No contract identity or execution is verified.')


def read_abi(path):
    source = Path(path).resolve()
    if not source.is_relative_to(Path.cwd().resolve()):
        raise ValueError('ABI path must stay inside the current workspace')
    with source.open('rb') as stream:
        raw = stream.read(abi.MAX_ABI_BYTES + 1)
    if len(raw) > abi.MAX_ABI_BYTES:
        raise ValueError('ABI file exceeds the 1 MiB input limit')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=abi.unique_object)
    except RecursionError as exc:
        raise ValueError('ABI JSON nesting is too deep') from exc


def error_index(entries):
    """Require every supplied error schema to be usable so none hide collisions."""
    abi.validate_abi(entries)
    errors = [entry for entry in entries if entry['type'] == 'error']
    if len(errors) > MAX_ERRORS:
        raise ValueError(f'ABI exceeds {MAX_ERRORS} error entries')
    index = {}
    seen = set()
    builtin_sigs = {abi.input_signature(entry) for entry in BUILTINS}
    for entry in BUILTINS + errors:
        signature = abi.input_signature(entry)  # admits types and budgets first
        if len(signature) > abi.MAX_FUNCTION_REFERENCE:
            raise ValueError('error signature exceeds the 8192-character limit')
        if signature in seen:
            # ABI producers may explicitly list Solidity's built-in errors.
            if signature in builtin_sigs:
                continue
            raise ValueError(f'duplicate error signature: {signature}')
        seen.add(signature)
        selector = abi.keccak256(signature.encode('ascii'))[:4]
        index.setdefault(selector, []).append((signature, entry))
    return index


def decode_revert(entries, data):
    if not isinstance(data, bytes):
        raise ValueError('revert data must be bytes')
    abi.check_budget(max(0, len(data) - 4), 'revert data')
    index = error_index(entries)
    result = {'status': 'empty', 'data_bytes': len(data), 'notice': NOTICE}
    if not data:
        return result
    if len(data) < 4:
        raise ValueError('revert data is shorter than a four-byte selector')
    selector = data[:4]
    result['selector'] = '0x' + selector.hex()
    candidates = index.get(selector, [])
    if not candidates:
        result.update(status='unknown', explanation='selector absent from supplied ABI and built-ins')
        return result
    if len(candidates) != 1:
        result.update(status='ambiguous', signatures=sorted(sig for sig, _ in candidates))
        return result
    signature, entry = candidates[0]
    # Canonical re-encoding rejects gaps, overlaps, trailing data and bad padding.
    values = abi.decode_tuple(entry.get('inputs', []), data[4:], strict=True)
    result.update(status='decoded', signature=signature, arguments=values)
    if signature == 'Panic(uint256)':
        code = values[0]['value']
        result['panic'] = {'code_hex': hex(code),
                           'description': PANICS.get(code, 'unrecognized panic code')}
    return result


def demo():
    # Independently laid-out Error("insufficient ZTO") fixture, not a chain claim.
    reason = b'insufficient ZTO'
    data = bytes.fromhex('08c379a0') + (32).to_bytes(32, 'big')
    data += len(reason).to_bytes(32, 'big') + reason.ljust(32, b'\0')
    return decode_revert([], data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--abi', help='optional workspace-contained JSON ABI with custom errors')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--data', help='raw revert bytes as even-length 0x hex, not an RPC envelope')
    group.add_argument('--demo', action='store_true', help='decode a built-in offline reason fixture')
    args = parser.parse_args()
    try:
        if args.demo and args.abi:
            raise ValueError('--demo does not use --abi')
        result = demo() if args.demo else decode_revert(
            read_abi(args.abi) if args.abi else [], abi.parse_data(args.data, call=True))
    except (ValueError, OSError, RecursionError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'decoded' else 1


if __name__ == '__main__':
    raise SystemExit(main())
