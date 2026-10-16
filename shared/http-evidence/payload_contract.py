#!/usr/bin/env python3
"""Compare saved HTTP response-contract evidence by URL, entirely offline."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
from urllib.parse import urlsplit

import duplicates
import payload_lens
import reconcile


COLUMNS = ('url', 'outcome', 'source_ok', 'expected_media', 'json_required',
           'minimum_body_bytes', 'media_state', 'json_state', 'body_state',
           'final_status', 'body_sha256', 'report_sha256')


def source_url(report):
    probe = report.get('probe') if report.get('schema') == 'deadline-sentry/v1' else report
    if not isinstance(probe, dict):
        raise ValueError('missing probe')
    url = probe.get('url')
    if not isinstance(url, str) or len(url) > 4096 or any(ord(c) <= 32 or ord(c) == 127 for c in url):
        raise ValueError('invalid requested URL')
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.fragment):
        raise ValueError('need a public, nonsecret HTTPS URL')
    return url, probe


def load_source(path):
    target = Path(path).resolve()
    if not target.is_relative_to(Path.cwd().resolve()):
        raise ValueError('report must stay inside the current workspace')
    info = target.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > payload_lens.MAX_REPORT:
        raise ValueError('report must be a regular file of at most 1 MiB')
    with target.open('rb') as stream:
        raw = stream.read(payload_lens.MAX_REPORT + 1)
    if len(raw) > payload_lens.MAX_REPORT:
        raise ValueError('report exceeds 1 MiB')
    return payload_lens.strict_json(raw), hashlib.sha256(raw).hexdigest()


def snapshot(path, media=None, json_check=False, min_bytes=None):
    """One evidence row. An unknown or failed contract is retained, never passed."""
    source, source_hash = load_source(path)
    judgment = payload_lens.analyze(source, media, json_check, min_bytes)
    url, probe = source_url(source)
    findings = {f['code']: f['state'] for f in judgment['findings']}
    hops = probe.get('hops')
    last = hops[-1] if isinstance(hops, list) and hops else {}
    row = {'url': url, 'outcome': judgment['outcome'],
           'source_ok': str(judgment['source_ok']).lower(),
           'expected_media': judgment['expected']['media_type'] or '',
           'json_required': str(json_check).lower(),
           'minimum_body_bytes': '' if min_bytes is None else str(min_bytes),
           'media_state': findings.get('media_type', ''),
           'json_state': findings.get('json_check', ''),
           'body_state': findings.get('body_bytes', ''),
           'final_status': str(last.get('status', '')),
           'body_sha256': last.get('body_sha256', ''),
           'report_sha256': source_hash}
    # Preserve a strict scalar CSV schema even when a malformed incomplete
    # report retained unusual optional fields.
    if not all(isinstance(row[key], str) for key in COLUMNS):
        raise ValueError('invalid scalar evidence')
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue(), judgment


def compare(before, after):
    reviews = {}
    for label, path in (('before', before), ('after', after)):
        header, _, count = reconcile.load_table(path, ['url'])
        if header != list(COLUMNS) or count == 0:
            raise ValueError('need nonempty payload-contract CSV snapshots')
        reviews[label] = duplicates.inspect(path, ['url'])
    result = reconcile.reconcile(before, after, ['url'])
    return {'format': 'payload-contract-review/v1', 'complete': result['complete']
            and reviews['before']['clean'] and reviews['after']['clean'],
            'duplicate_review': {label: review for label, review in reviews.items()
                                 if not review['clean']},
            'comparison': result,
            'scope': 'Saved evidence only; equal rows do not establish current endpoint health.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest='command', required=True)
    snap = commands.add_parser('snapshot')
    snap.add_argument('report')
    snap.add_argument('--media')
    snap.add_argument('--json-check', action='store_true')
    snap.add_argument('--min-bytes', type=int)
    diff = commands.add_parser('compare')
    diff.add_argument('before')
    diff.add_argument('after')
    args = parser.parse_args(argv)
    try:
        if args.command == 'snapshot':
            output, judgment = snapshot(args.report, args.media, args.json_check, args.min_bytes)
            code = 0 if judgment['outcome'] == 'matches' else 1
        else:
            result = compare(args.before, args.after)
            output = json.dumps(result, indent=2, ensure_ascii=True) + '\n'
            code = 0 if result['complete'] and result['comparison']['equal'] else 1
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
