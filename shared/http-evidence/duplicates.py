#!/usr/bin/env python3
"""Explain duplicate and empty CSV keys offline; never select or delete rows."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def _engine():
    source = Path(__file__).resolve().parent / 'reconcile.py'
    spec = importlib.util.spec_from_file_location('duplicate_reconciler', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


engine = _engine()


def inspect(path, keys):
    if not keys or any(not k for k in keys) or len(keys) != len(set(keys)):
        raise engine.InputError('provide distinct, nonempty key columns')
    header, groups, total = engine.load_table(path, keys)
    findings = []
    identical = conflicting = empty = 0
    for key, rows in sorted(groups.items()):
        missing = [column for column, value in zip(keys, key) if value == '']
        if len(rows) == 1 and not missing:
            continue
        fields = {}
        differing = []
        for column in header:
            variants = {}
            for row in rows:
                variants.setdefault(row['values'][column], []).append(row['record'])
            fields[column] = [{'value': value, 'records': records, 'count': len(records)}
                              for value, records in sorted(variants.items())]
            if len(variants) > 1:
                differing.append(column)
        kind = 'singleton'
        if len(rows) > 1:
            kind = 'conflicting' if differing else 'identical'
            if differing:
                conflicting += 1
            else:
                identical += 1
        if missing:
            empty += 1
        findings.append({'key': dict(zip(keys, key)), 'empty_key_columns': missing,
                         'duplicate_kind': kind, 'records': [r['record'] for r in rows],
                         'differing_columns': differing, 'fields': fields})
    return {'format': 'csv-duplicates/v1', 'keys': list(keys), 'columns': header,
            'clean': not findings,
            'summary': {'records': total, 'distinct_keys': len(groups),
                        'identical_duplicate_groups': identical,
                        'conflicting_duplicate_groups': conflicting,
                        'empty_key_groups': empty, 'finding_groups': len(findings)},
            'findings': findings}


def render_text(report):
    # JSON quoting keeps embedded newlines, terminal controls and headers inert.
    q = lambda value: json.dumps(value, ensure_ascii=True, sort_keys=True)
    lines = ['CSV duplicate-key review', 'Keys: ' + q(report['keys']),
             'Summary: ' + q(report['summary'])]
    for group in report['findings']:
        lines.extend(['', 'Key: ' + q(group['key']),
                      'Records: ' + q(group['records']),
                      'Duplicate kind: ' + group['duplicate_kind'],
                      'Empty key columns: ' + q(group['empty_key_columns']),
                      'Differing columns: ' + q(group['differing_columns'])])
        for column, variants in group['fields'].items():
            lines.append('Field ' + q(column) + ':')
            for variant in variants:
                lines.append('  ' + q(variant['value']) + ' at records ' + q(variant['records']))
    lines.append('No rows selected, paired, changed or removed.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', help='UTF-8 CSV within the current working directory')
    parser.add_argument('--key', required=True, action='append', help='repeat for composite key')
    parser.add_argument('--format', choices=('json', 'text'), default='json')
    args = parser.parse_args(argv)
    try:
        report = inspect(args.csv, args.key)
    except (OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(render_text(report) if args.format == 'text' else
          json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report['clean'] else 1


if __name__ == '__main__':
    sys.exit(main())
