#!/usr/bin/env python3
"""Reproduce offline demonstrations of every line plus shared handoffs.

Read the tools before using this runner. Run from the repository root.
Only output evidence under gathering/ and temporary data under test/scratch/.
"""
import json
from pathlib import Path
import subprocess
import sys


def main():
    scratch = Path('test/scratch/gathering32')
    scratch.mkdir(parents=True, exist_ok=True)
    results = []

    def run(name, script, args, expected=0, html=False):
        command = [sys.executable, '-B', script, *args]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        evidence = {'name': name, 'command': ['python3.' + str(sys.version_info.minor)] + command[1:], 'exit_code': result.returncode,
                    'expected_exit_code': expected, 'stderr': result.stderr,
                    'passed': result.returncode == expected}
        if html:
            evidence['html_bytes'] = len(result.stdout.encode())
            evidence['has_html_document'] = '<!doctype html>' in result.stdout.lower()
            evidence['passed'] &= evidence['has_html_document']
        else:
            try:
                evidence['output'] = json.loads(result.stdout)
            except ValueError:
                evidence['output'] = result.stdout
        results.append(evidence)
        return result.stdout

    run('Report Delta retained observations', 'line-1/tools/report-delta/report_delta.py',
        ['line-1/tools/report-delta/observed-before.json', 'line-1/tools/report-delta/observed-after.json', '--same-expectations'])
    probes = json.loads(Path('gathering/live-probes25.json').read_text())
    for name, index in [('before', 0), ('after', 1)]:
        (scratch / (name + '.json')).write_text(json.dumps(probes[index]['stdout']))
    run('Report Delta retained gathering25 observations', 'line-1/tools/report-delta/report_delta.py',
        [str(scratch / 'before.json'), str(scratch / 'after.json'), '--same-expectations'])
    run('CSV key audit composite key', 'line-2/tools/csv-key-audit/audit.py',
        ['line-2/tools/csv-key-audit/demo.csv', '--key', 'item', '--key', 'location'])
    run('CSV key audit ambiguous key', 'line-2/tools/csv-key-audit/audit.py',
        ['line-2/tools/csv-key-audit/demo.csv', '--key', 'item'], 1)
    pair = ['line-2/tools/csv-reconcile/demo-before.csv', 'line-2/tools/csv-reconcile/demo-after.csv', '--key', 'item']
    run('CSV exact reconciliation', 'line-2/tools/csv-reconcile/reconcile.py', pair, 1)
    run('CSV HTML review', 'line-2/tools/csv-review/review.py', pair, 1, html=True)
    run('CSV three-way merge', 'line-2/tools/csv-merge/merge.py',
        [f'line-2/tools/csv-merge/demo-{side}.csv' for side in ('base','left','right')] + ['--key', 'item', '--format', 'csv'])
    run('Import Map example', 'line-3/tools/import-map/import_map.py', ['line-3/tools/import-map/examples', '--json'])
    run('Import Impact real worker', 'line-3/tools/import-impact/impact.py',
        ['line-1/tools/deadline-sentry', 'deadline_sentry', '--json', '--strict'])
    run('Import Delta added cycle', 'line-3/tools/import-delta/delta.py',
        ['line-3/tools/import-delta/examples/before', 'line-3/tools/import-delta/examples/after', '--json', '--check'], 1)
    run('Import Delta real worker unchanged', 'line-3/tools/import-delta/delta.py',
        ['line-1/tools/deadline-sentry'] * 2 + ['--json', '--check', '--strict'])
    abi = 'line-4/tools/abi-workbench/abi_workbench.py'
    run('ABI offline demo', abi, ['--demo'])
    run('ABI published array layout', abi, ['encode', '--abi', 'line-4/tools/abi-workbench/array-example.json', '--function', 'f',
        '--args', '[291,[1110,1929],"0x31323334353637383930","0x48656c6c6f2c20776f726c6421"]'])
    strict = ['decode', '--abi', 'line-4/tools/abi-workbench/alias-example.json', '--function', 'transfer', '--strict', '--data']
    boolean = '0x' + '0' * 63 + '1'
    run('ABI strict boolean', abi, strict + [boolean])
    run('ABI strict rejects surplus', abi, strict + [boolean + '0' * 64], 2)
    output = run('Token Read Plan historical ZTO and IMD', 'shared/token-read-plan/token_read_plan.py', ['demo'])
    assert output == Path('shared/token-read-plan/observed.csv').read_text()
    token_pair = ['shared/token-read-plan/observed.csv'] * 2 + ['--key', 'chain_id', '--key', 'token_address', '--key', 'field']
    run('Checked token CSV review', 'shared/import-drift/checked_review.py', token_pair)
    run('Checked token HTML review', 'shared/import-drift/checked_review.py', token_pair + ['--format', 'html'], html=True)
    snap = run('Import Drift real worker', 'shared/import-drift/drift.py', ['snapshot', 'line-1/tools/endpoint-sentry'])
    (scratch / 'sentry.csv').write_text(snap)
    run('Checked import CSV review', 'shared/import-drift/checked_review.py',
        ['shared/import-drift/observed-sentry23.csv', str(scratch / 'sentry.csv'), '--key', 'module'])
    run('Import merge and impact handoff', 'shared/import-drift/handoff.py',
        ['shared/import-drift/observed-sentry23.csv'] * 3 + ['line-1/tools/endpoint-sentry'])
    run('Import Reach fixture', 'line-3/tools/import-reach/reach.py',
        ['line-3/tools/import-reach/examples', '--json', '--check-unreached'], 1)
    run('Import Reach real worker', 'line-3/tools/import-reach/reach.py',
        ['line-1/tools/deadline-sentry', '--json', '--strict'])
    calldata = '0xa9059cbb' + '0' * 24 + 'd782bdea4ef02a0bd391eb9089470c8080f0a68e' + '0' * 63 + 'c'
    run('ABI inspect canonical calldata', abi, ['decode-call', '--abi',
        'line-4/tools/abi-workbench/alias-example.json', '--function', 'transfer', '--data', calldata])
    run('ABI rejects wrong calldata selector', abi, ['decode-call', '--abi',
        'line-4/tools/abi-workbench/alias-example.json', '--function', 'transfer', '--data', '0x00000000' + calldata[10:]], 2)
    patcher = 'line-2/tools/csv-patch/patch.py'
    plan = run('CSV reviewed inventory patch', patcher, ['plan',
        'line-2/tools/csv-reconcile/demo-before.csv', 'line-2/tools/csv-reconcile/demo-after.csv',
        '--key', 'item', '--key', 'location'])
    plan_path = scratch / 'inventory-plan.json'
    plan_path.write_text(plan)
    applied = run('CSV apply inventory patch', patcher, ['apply',
        'line-2/tools/csv-reconcile/demo-before.csv', str(plan_path)])
    applied_path = scratch / 'inventory.csv'
    applied_path.write_text(applied)
    run('CSV applied inventory matches target', 'line-2/tools/csv-reconcile/reconcile.py',
        [str(applied_path), 'line-2/tools/csv-reconcile/demo-after.csv', '--key', 'item', '--key', 'location'])
    import_base = 'shared/import-drift/observed-sentry.csv'
    import_plan = run('Shared guarded import patch', 'shared/import-drift/patch.py', ['plan',
        import_base, 'shared/import-drift/observed-sentry23.csv', '--key', 'module'])
    import_path = scratch / 'import-plan.json'
    import_path.write_text(import_plan)
    review = run('Shared validated patch HTML', 'shared/import-drift/patch_review.py',
        [import_base, str(import_path)], html=True)
    assert json.loads(Path('shared/import-drift/observed-patch26.json').read_text()) == json.loads(import_plan)
    assert review == Path('shared/import-drift/observed-patch26.html').read_text()
    stale = scratch / 'stale.csv'
    stale.write_bytes(Path(import_base).read_bytes().replace(b'\n', b'\r\n'))
    run('Shared review refuses stale baseline', 'shared/import-drift/patch_review.py',
        [str(stale), str(import_path)], 2)
    run('Cache Lens historical receipt', 'line-1/tools/cache-lens/cache_lens.py',
        ['line-1/tools/cache-lens/observed-live.json', '--shared'])
    run('Cache Lens historical expiry', 'line-1/tools/cache-lens/cache_lens.py',
        ['line-1/tools/cache-lens/observed-live.json', '--shared', '--at', '2026-10-15T19:03:45Z'])
    run('Import Boundaries fixture', 'line-3/tools/import-boundaries/boundaries.py',
        ['line-3/tools/import-boundaries/examples', '--strict', '--json'])
    run('Import Boundaries denied edge', 'line-3/tools/import-boundaries/boundaries.py',
        ['line-3/tools/import-boundaries/examples', '--deny', 'ui:storage', '--json'], 1)
    run('Import Boundaries real worker', 'line-3/tools/import-boundaries/boundaries.py',
        ['line-1/tools/deadline-sentry', '--strict', '--json'])
    run('CSV patch compact inspection', patcher, ['inspect',
        'line-2/tools/csv-reconcile/demo-before.csv', str(plan_path)])
    run('Shared CSV patch compact inspection', 'shared/import-drift/patch.py',
        ['inspect', import_base, str(import_path)])
    run('HTTP evidence receipt snapshot', 'shared/http-evidence/http_evidence.py',
        ['snapshot', 'shared/http-evidence/observed-report.json', '--shared'])
    run('HTTP evidence exact freshness review', 'shared/http-evidence/http_evidence.py',
        ['compare', 'shared/http-evidence/observed-receipt.csv',
         'shared/http-evidence/observed-expired.csv'], 1)
    run('Probe Triage missing public route', 'line-1/tools/probe-triage/probe_triage.py',
        ['line-1/tools/probe-triage/observed-404.json', '--check'], 1)
    run('Probe Triage retained health', 'line-1/tools/probe-triage/probe_triage.py',
        ['line-1/tools/probe-triage/observed-live.json', '--check'])
    run('CSV explicitly renamed composite key', 'line-2/tools/csv-align/align.py',
        ['line-2/tools/csv-align/demo-before.csv', 'line-2/tools/csv-align/demo-after.csv',
         '--key', 'item', '--key', 'location', '--map', 'item', 'sku'], 1)
    run('Import Budget real worker', 'line-3/tools/import-budget/budget.py',
        ['line-1/tools/deadline-sentry', '--json', '--strict'])
    run('Import Budget refuses partial collection', 'line-3/tools/import-budget/budget.py',
        ['line-1/tools/deadline-sentry', '--json', '--max-files', '1'], 2)
    run('ABI explicit overload published layout', abi,
        ['encode', '--abi', 'line-4/tools/abi-workbench/overload-example.json',
         '--function', 'bar(bytes3[2])', '--args', '[["0x616263","0x646566"]]'])
    run('ABI refuses ambiguous bare name', abi,
        ['encode', '--abi', 'line-4/tools/abi-workbench/overload-example.json',
         '--function', 'bar', '--args', '[["0x616263","0x646566"]]'], 2)
    bounded = run('Shared bounded import snapshot real worker',
        'shared/import-drift/bounded_snapshot.py', ['line-1/tools/endpoint-sentry'])
    bounded_path = scratch / 'bounded.csv'
    bounded_path.write_text(bounded)
    assert bounded == snap
    run('Shared bounded import keyed review', 'shared/import-drift/checked_review.py',
        ['shared/import-drift/observed-sentry23.csv', str(bounded_path), '--key', 'module'])
    run('Shared bounded collection refuses partial CSV', 'shared/import-drift/bounded_snapshot.py',
        ['line-1/tools/endpoint-sentry', '--max-files', '1'], 2)
    run('Redirect Lens retained real failed status', 'line-1/tools/redirect-lens/redirect_lens.py',
        ['line-1/tools/redirect-lens/observed-live.json'])
    run('CSV renamed columns readable text', 'line-2/tools/csv-align/align.py',
        ['line-2/tools/csv-align/demo-before.csv', 'line-2/tools/csv-align/demo-after.csv',
         '--key', 'item', '--key', 'location', '--map', 'item', 'sku', '--format', 'text'], 1)
    run('Import Witness actual worker source', 'line-3/tools/import-witness/witness.py',
        ['shared/import-drift', '--json', '--strict'])
    run('Import Witness directed fixture', 'line-3/tools/import-witness/witness.py',
        ['line-3/tools/import-map/examples', '--json', '--strict'], 1)
    run('Import Witness collection refusal', 'line-3/tools/import-witness/witness.py',
        ['line-3/tools/import-map/examples', '--json', '--max-files', '1'], 2)
    tuple_args = ['encode', '--abi', 'line-4/tools/abi-workbench/tuple-example.json',
                  '--function', 'put((uint256,string))', '--args', '[[7,"hi"]]']
    tuple_output = run('ABI nested tuple layout', abi, tuple_args)
    run('ABI nested tuple canonical inspection', abi,
        ['decode-call', '--abi', 'line-4/tools/abi-workbench/tuple-example.json',
         '--function', 'put((uint256,string))', '--data', json.loads(tuple_output)['calldata']])
    run('Shared tuple codec', 'shared/token-read-plan/abi_workbench.py', tuple_args)
    cycle = run('Shared source-linked cycle CSV', 'shared/import-drift/cycle_csv.py',
        ['snapshot', 'line-3/tools/import-map/examples'], 1)
    cycle_path = scratch / 'cycles.csv'
    cycle_path.write_text(cycle)
    run('Shared cycle self-review', 'shared/import-drift/cycle_csv.py',
        ['compare', str(cycle_path), str(cycle_path)])
    run('Shared empty real-worker cycle export', 'shared/import-drift/cycle_csv.py',
        ['snapshot', 'line-1/tools/deadline-sentry'])
    run('Shared cycle budget refuses partial CSV', 'shared/import-drift/cycle_csv.py',
        ['snapshot', 'line-3/tools/import-map/examples', '--max-files', '1'], 2)
    run('Retry Lens retained live capture', 'line-1/tools/retry-lens/retry_lens.py',
        ['line-1/tools/retry-lens/observed-live.json'])
    run('Retry Lens synthetic 503 hint', 'line-1/tools/retry-lens/retry_lens.py',
        ['line-1/tools/retry-lens/demo-503.json'])
    run('Retry Lens historical report is not captured', 'line-1/tools/retry-lens/retry_lens.py',
        ['line-1/tools/endpoint-sentry/live-success.json'])
    gate_pair = ['line-2/tools/csv-gate/demo-before.csv',
                 'line-2/tools/csv-gate/demo-after.csv', '--key', 'item']
    run('CSV Change Gate default rejection', 'line-2/tools/csv-gate/gate.py', gate_pair, 1)
    run('CSV Change Gate explicit allowance', 'line-2/tools/csv-gate/gate.py',
        gate_pair + ['--max-added', '1', '--max-changed', '1', '--allow-change', 'quantity'])
    run('Import Route real worker', 'line-3/tools/import-route/route.py',
        ['line-1/tools/deadline-sentry', 'test_deadline_sentry', 'deadline_sentry', '--json', '--strict'])
    run('Import Route fixture with warnings', 'line-3/tools/import-route/route.py',
        ['line-3/tools/import-map/examples', 'main', 'pkg.helper', '--json', '--strict'], 1)
    run('Import Route unknown module refused', 'line-3/tools/import-route/route.py',
        ['line-1/tools/deadline-sentry', 'missing', 'deadline_sentry', '--json'], 2)
    run('Import Route input budget refused', 'line-3/tools/import-route/route.py',
        ['line-1/tools/deadline-sentry', 'test_deadline_sentry', 'deadline_sentry',
         '--json', '--max-files', '1'], 2)
    param = {'type': 'uint8'}
    for _ in range(33):
        param = {'type': 'tuple', 'components': [param]}
    deep_abi = scratch / 'deep-abi.json'
    deep_abi.write_text(json.dumps([{'type': 'function', 'name': 'f', 'inputs': [param]}]))
    run('ABI excessive tuple nesting refused', abi,
        ['encode', '--abi', str(deep_abi), '--function', 'f', '--args', '[]'], 2)
    run('Shared ABI excessive tuple nesting refused', 'shared/token-read-plan/abi_workbench.py',
        ['encode', '--abi', str(deep_abi), '--function', 'f', '--args', '[]'], 2)
    import_pair = [import_base, 'shared/import-drift/observed-sentry23.csv']
    run('Import Change Gate historical dependency default refusal',
        'shared/import-drift/import_gate.py', import_pair, 1)
    run('Import Change Gate historical dependency allowance',
        'shared/import-drift/import_gate.py',
        import_pair + ['--max-changed', '1', '--allow-change', 'external_imports'])
    run('Import Change Gate full offline HTML', 'shared/import-drift/import_gate.py',
        import_pair + ['--format', 'html'], 1, html=True)
    run('Import Change Gate fresh bounded snapshot unchanged', 'shared/import-drift/import_gate.py',
        [str(bounded_path), str(bounded_path)])
    report = {'ok': all(item['passed'] for item in results), 'results': results,
              'token_historical_csv_byte_identical': True}
    Path('gathering/integration-checks32.json').write_text(json.dumps(report, separators=(',', ':')) + '\n')
    print(json.dumps({'ok': report['ok'], 'checks': len(results),
                      'failed': [r['name'] for r in results if not r['passed']]}, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
