#!/usr/bin/env python3
"""Run reviewed tool suites from scratch copies; never write into line folders.

Run from the repository root. Python standard library only. No network.
The JSON result is local test evidence, not independent certification.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def main():
    scratch = Path('test/scratch/gathering32/suites')
    sources = sorted(Path('.').glob('line-*/tools/*/test_*.py'))
    sources += sorted(Path('shared').glob('*/test_*.py'))
    sources += sorted(Path('gathering').glob('test_*.py'))
    suites = sorted({p.parent for p in sources})
    hashes = {}
    for root in [Path(f'line-{i}/tools') for i in range(1, 5)] + [Path('shared'), Path('gathering')]:
        for source in sorted(root.rglob('*')):
            if not source.is_file() or source.suffix not in ('.py', '.csv', '.json'):
                continue
            if '__pycache__' in source.parts:
                continue
            target = scratch / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
            hashes[source.as_posix()] = digest

    def check(suite):
        command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(scratch / suite), '-v']
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        found = re.search(r'Ran (\d+) tests?', result.stderr)
        return {'suite': suite.as_posix(), 'command': ['python3.' + str(sys.version_info.minor)] + command[1:],
                'exit_code': result.returncode, 'tests': int(found[1]) if found else 0,
                'elapsed_seconds': round(time.monotonic() - start, 3),
                'stdout': result.stdout, 'stderr': result.stderr}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, suites))
    for source, digest in hashes.items():
        assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == digest
    report = {'python_version': sys.version.split()[0], 'round': 32, 'source_copies_identical': True,
              'sources_unchanged_after_checks': True, 'results': results,
              'line_tests': sum(r['tests'] for r in results if r['suite'].startswith('line-')),
              'gathering_tests': sum(r['tests'] for r in results if r['suite'] == 'gathering'),
              'shared_tests': sum(r['tests'] for r in results if r['suite'].startswith('shared/')),
              'ok': all(r['exit_code'] == 0 for r in results)}
    Path('gathering/test-runs32.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
