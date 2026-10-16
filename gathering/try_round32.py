#!/usr/bin/env python3
"""Offline demonstrations of all four new line pieces and the shared handoff."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys


def main():
    scratch = Path('test/scratch/gathering32/round32')
    scratch.mkdir(parents=True, exist_ok=True)
    results = []

    def run(label, script, args, expected=0):
        command = [sys.executable, '-B', script, *map(str, args)]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15)
        results.append({'name': label, 'command': command, 'exit_code': completed.returncode,
                        'expected_exit_code': expected, 'passed': completed.returncode == expected,
                        'stdout_bytes': len(completed.stdout.encode()),
                        'stderr': completed.stderr[:1000]})
        return completed.stdout

    saved = 'line-1/tools/endpoint-doctor/observed-live.json'
    payload = run('Payload Lens retained real JSON response',
                  'line-1/tools/payload-lens/payload_lens.py',
                  [saved, '--media', 'application/json', '--json-check', '--min-bytes', '1'])
    assert json.loads(payload)['outcome'] == 'matches'
    duplicates = run('CSV Duplicate Review demonstration',
                     'line-2/tools/csv-duplicates/duplicates.py',
                     ['line-2/tools/csv-duplicates/demo.csv', '--key', 'item',
                      '--key', 'location'], 1)
    assert json.loads(duplicates)['summary']['finding_groups'] == 3
    clean = run('CSV Duplicate Review retained ZTO/IMD rows',
                'line-2/tools/csv-duplicates/duplicates.py',
                ['shared/token-read-plan/observed.csv', '--key', 'chain_id',
                 '--key', 'token_address', '--key', 'field'])
    assert json.loads(clean)['clean']
    context = run('Import Context actual shared source',
                  'line-3/tools/import-context/context.py',
                  ['shared/import-drift', '--json', '--strict'])
    mapped = json.loads(context)
    assert mapped['status'] == 'complete' and mapped['context_summary']['import_sites'] > 0
    example = run('Import Context nested fixture',
                  'line-3/tools/import-context/context.py',
                  ['line-3/tools/import-context/examples', '--json'])
    assert json.loads(example)['context_summary']['nested_sites'] > 0
    revert = run('Revert Lens offline constructed reason',
                 'line-4/tools/revert-lens/revert_lens.py', ['--demo'])
    assert json.loads(revert)['signature'] == 'Error(string)'
    panic = run('Revert Lens offline panic bytes',
                'line-4/tools/revert-lens/revert_lens.py',
                ['--data', '0x4e487b71' + '0'*62 + '11'])
    assert json.loads(panic)['panic']['code_hex'] == '0x11'

    handoff = 'shared/http-evidence/payload_contract.py'
    common = [saved, '--json-check', '--min-bytes', '1']
    matching = run('Shared matching contract snapshot', handoff,
                   ['snapshot', *common, '--media', 'application/json'])
    mismatching = run('Shared mismatched contract snapshot', handoff,
                      ['snapshot', *common, '--media', 'text/html'], 1)
    before = Path('shared/http-evidence/observed-payload32.csv')
    after = Path('shared/http-evidence/observed-payload-mismatch32.csv')
    before.write_text(matching)
    after.write_text(mismatching)
    assert next(csv.DictReader(io.StringIO(matching)))['outcome'] == 'matches'
    assert next(csv.DictReader(io.StringIO(mismatching)))['outcome'] == 'mismatch'
    comparison = run('Shared exact keyed contract review', handoff,
                     ['compare', before, after], 1)
    review = json.loads(comparison)
    assert review['complete'] and review['comparison']['summary']['changed'] == 1
    Path('shared/http-evidence/observed-payload-review32.json').write_text(
        json.dumps(review, indent=2) + '\n')
    duplicate = scratch / 'duplicate.csv'
    duplicate.write_text(matching + matching.splitlines(keepends=True)[1])
    duplicate_review = run('Shared ambiguous URL diagnosis', handoff,
                           ['compare', before, duplicate], 1)
    asserted = json.loads(duplicate_review)
    assert not asserted['complete']
    assert asserted['duplicate_review']['after']['summary']['identical_duplicate_groups'] == 1
    report = {'round': 32, 'ok': all(row['passed'] for row in results),
              'context_summary': mapped['context_summary'], 'results': results}
    Path('gathering/new-tool-checks32.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'ok': report['ok'], 'checks': len(results),
                      'context_summary': report['context_summary']}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__':
    raise SystemExit(main())
