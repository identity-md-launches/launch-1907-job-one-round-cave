#!/usr/bin/env python3
"""Round 31 offline trials; outputs only evidence and scratch files."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    scratch = Path('test/scratch/gathering32/trials')
    scratch.mkdir(parents=True, exist_ok=True)
    results = []

    def run(name, script, args, expected=0, html=False):
        command = [sys.executable, '-B', script, *map(str, args)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        row = {'name': name, 'command': command, 'exit_code': result.returncode,
               'expected_exit_code': expected, 'passed': result.returncode == expected,
               'stderr': result.stderr}
        if html:
            row['html_bytes'] = len(result.stdout.encode())
            row['passed'] &= '<!doctype html>' in result.stdout.lower()
        else:
            try:
                row['output'] = json.loads(result.stdout)
            except ValueError:
                row['output'] = result.stdout
        results.append(row)
        return result.stdout

    doctor = 'line-1/tools/endpoint-doctor/endpoint_doctor.py'
    retained = 'line-1/tools/endpoint-doctor/observed-live.json'
    run('Doctor retained real observation', doctor, ['--report', retained])
    run('Doctor explicit historical aging', doctor,
        ['--report', retained, '--at', '2026-10-16T00:00:00Z'])
    run('Doctor fresh saved observation', doctor,
        ['--report', 'gathering/live-doctor31-source.json', '--require-complete'])

    original = 'line-2/tools/csv-reconcile/demo-before.csv'
    forward = 'line-2/tools/csv-patch/demo-plan.json'
    undo = run('CSV reverse inventory plan', 'line-2/tools/csv-undo/undo.py', [original, forward])
    undo_path = scratch / 'undo.json'
    undo_path.write_text(undo)
    patcher = 'line-2/tools/csv-patch/patch.py'
    current = scratch / 'current.csv'
    current.write_text(run('CSV forward inventory apply', patcher, ['apply', original, forward]))
    run('CSV reverse inspection', patcher, ['inspect', current, undo_path])
    restored = scratch / 'restored.csv'
    restored.write_text(run('CSV reverse apply', patcher, ['apply', current, undo_path]))
    run('CSV restored keyed equality', 'line-2/tools/csv-reconcile/reconcile.py',
        [original, restored, '--key', 'item', '--key', 'location'])
    current.write_bytes(current.read_bytes().replace(b'\n', b'\r\n'))
    run('CSV undo refuses changed current bytes', patcher, ['apply', current, undo_path], 2)

    order = 'line-3/tools/import-order/order.py'
    run('Import dependency reading fixture', order,
        ['line-3/tools/import-order/examples', '--from', 'cli'])
    run('Import dependency reading actual shared worker', order,
        ['shared/import-drift', '--json', '--strict'])
    run('Import order input budget refuses partial plan', order,
        ['shared/import-drift', '--json', '--max-files', '1'], 2)

    audit = 'line-4/tools/selector-audit/selector_audit.py'
    run('ERC20 selectors', audit, ['--abi', 'line-4/tools/selector-audit/erc20.json'])
    collision = scratch / 'collision.json'
    collision.write_text(json.dumps([{'type': 'function', 'name': name,
        'inputs': [{'type': kind}], 'outputs': []} for name, kind in
        [('burn', 'uint256'), ('collate_propagate_storage', 'bytes16')]]))
    run('Known distinct-signature selector collision', audit, ['--abi', collision], 1)

    baseline = 'shared/import-drift/observed-sentry.csv'
    plan = 'shared/import-drift/observed-patch26.json'
    shared_reverse = run('Shared reverse real import change',
        'shared/import-drift/import_undo.py', [baseline, plan])
    shared_reverse_path = Path('test/scratch/gathering32/trials/observed-undo32.json')
    shared_reverse_path.write_text(shared_reverse)
    current = Path('test/scratch/gathering32/trials/observed-current32.csv')
    current.write_text(run('Shared forward import patch',
        'shared/import-drift/patch.py', ['apply', baseline, plan]))
    html = run('Shared reverse escaped HTML review', 'shared/import-drift/patch_review.py',
        [current, shared_reverse_path], html=True)
    Path('test/scratch/gathering32/trials/observed-undo32.html').write_text(html)
    restored = scratch / 'shared-restored.csv'
    restored.write_text(run('Shared reverse import apply',
        'shared/import-drift/patch.py', ['apply', current, shared_reverse_path]))
    run('Shared restored import equality', 'shared/import-drift/drift.py',
        ['compare', baseline, restored])
    report = {'ok': all(r['passed'] for r in results), 'results': results}
    Path('gathering/inherited-new-tool-checks32.json').write_text(json.dumps(report, separators=(',', ':')) + '\n')
    print(json.dumps({'ok': report['ok'], 'checks': len(results),
                      'failed': [r['name'] for r in results if not r['passed']]}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__':
    raise SystemExit(main())
