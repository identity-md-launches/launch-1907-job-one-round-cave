#!/usr/bin/env python3
"""Check a saved Endpoint Sentry response contract without fetching its body."""

import argparse
import json
import math
from pathlib import Path
import re
import stat
import sys


SCHEMA = 'payload-lens/v1'
TOKEN = r"[!#$%&'*+.^_`|~0-9A-Za-z-]+"
MEDIA = re.compile(rf'^{TOKEN}/{TOKEN}$')
HEX256 = re.compile(r'^[0-9a-f]{64}$')
MAX_REPORT = 1024 * 1024


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def constant(_value):
        raise ValueError('non-JSON constant')

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('non-finite number')
        return number

    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=constant, parse_float=finite)


def load_report(name):
    root = Path.cwd().resolve()
    path = Path(name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('report must be inside the current workspace')
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_REPORT:
        raise ValueError('report must be a regular file of at most 1 MiB')
    with path.open('rb') as stream:
        raw = stream.read(MAX_REPORT + 1)
    if len(raw) > MAX_REPORT:
        raise ValueError('report exceeds 1 MiB')
    return strict_json(raw)


def media_type(value):
    if not isinstance(value, str) or len(value) > 512:
        raise ValueError('invalid recorded Content-Type')
    if not value:
        return None
    essence = value.split(';', 1)[0].strip()
    return essence.lower() if MEDIA.fullmatch(essence) and '*' not in essence else None


def required_media(value):
    if (not isinstance(value, str) or len(value) > 128 or not MEDIA.fullmatch(value)
            or '*' in value):
        raise ValueError('--media must be a concrete type/subtype without parameters')
    return value.lower()


def analyze(source, expected_media=None, require_json=False, min_bytes=None):
    """Return evidence-linked results; unknown evidence never becomes a pass."""
    if expected_media is not None:
        expected_media = required_media(expected_media)
    if min_bytes is not None and (type(min_bytes) is not int or min_bytes < 0 or
                                  min_bytes > 16777216):
        raise ValueError('--min-bytes must be between 0 and 16777216')
    if expected_media is None and not require_json and min_bytes is None:
        raise ValueError('specify at least one response expectation')
    if not isinstance(source, dict):
        raise ValueError('report must be an object')
    wrapper = source.get('schema') == 'deadline-sentry/v1'
    prefix = '/probe' if wrapper else ''
    if wrapper:
        if type(source.get('ok')) is not bool:
            raise ValueError('invalid watchdog health')
        if 'probe' not in source:
            if source.get('ok') is not False:
                raise ValueError('watchdog without probe must report failure')
            return {'schema': SCHEMA, 'outcome': 'unobserved', 'source_ok': False,
                    'expected': {'media_type': expected_media, 'json_check': require_json,
                                 'min_bytes': min_bytes},
                    'findings': [{'code': 'no_probe', 'state': 'unknown', 'evidence': '/',
                                  'detail': 'The watchdog supplied no HTTP response.'}],
                    'limits': ['No body is retained or fetched.']}
        probe = source['probe']
    else:
        probe = source
    if not isinstance(probe, dict) or probe.get('schema') != 'endpoint-sentry/v1':
        raise ValueError('expected an Endpoint Sentry or Deadline Sentry report')
    if type(probe.get('ok')) is not bool:
        raise ValueError('missing or invalid probe health')
    if wrapper and source['ok'] != probe['ok']:
        raise ValueError('watchdog and worker health disagree')
    hops, checks = probe.get('hops'), probe.get('checks')
    if not isinstance(hops, list) or len(hops) > 11 or not isinstance(checks, list) or len(checks) > 16:
        raise ValueError('invalid or excessive response evidence')
    for hop in hops:
        if not isinstance(hop, dict) or type(hop.get('status')) is not int or not 100 <= hop['status'] <= 599:
            raise ValueError('invalid hop status')
    for check in checks:
        if (not isinstance(check, dict) or not isinstance(check.get('name'), str) or
                type(check.get('ok')) is not bool):
            raise ValueError('invalid check')
    error = probe.get('error')
    if error is not None and (not isinstance(error, dict) or not isinstance(error.get('kind'), str)):
        raise ValueError('invalid error evidence')
    if error is not None and probe['ok']:
        raise ValueError('successful probe cannot contain an error')
    final_url = probe.get('final_url')
    if final_url is not None and (not isinstance(final_url, str) or len(final_url) > 4096):
        raise ValueError('invalid final URL')
    if final_url and (not hops or hops[-1].get('url') != final_url):
        raise ValueError('final URL contradicts terminal hop')
    if probe['ok'] and not final_url:
        raise ValueError('successful probe lacks terminal response')
    if final_url and error is None:
        status_checks = [check for check in checks if check['name'] == 'status']
        if len(status_checks) != 1:
            raise ValueError('complete response needs one status check')
        status_check = status_checks[0]
        expected_status = status_check.get('expected')
        if (type(expected_status) is not int or not 100 <= expected_status <= 599 or
                type(status_check.get('actual')) is not int or
                status_check['actual'] != hops[-1]['status'] or
                status_check['ok'] != (status_check['actual'] == expected_status) or
                probe['ok'] != all(check['ok'] for check in checks)):
            raise ValueError('status or health contradicts checks')

    result = {'schema': SCHEMA, 'outcome': 'unknown', 'source_ok': probe['ok'],
              'checked_at': probe.get('checked_at'),
              'expected': {'media_type': expected_media, 'json_check': require_json,
                           'min_bytes': min_bytes}, 'findings': [],
              'limits': ['Content-Type is a server claim, not proof of body format.',
                         'A JSON check refers to the captured historical body only.',
                         'No body is retained or fetched; no current health is inferred.']}
    findings = result['findings']
    if error is not None:
        findings.append({'code': 'capture_error', 'state': 'unknown',
                         'evidence': prefix + '/error',
                         'detail': 'The probe ended during ' + error['kind'] + '; contract is incomplete.'})
    if not final_url:
        findings.append({'code': 'no_terminal_response', 'state': 'unknown',
                         'evidence': prefix + '/hops',
                         'detail': 'No complete terminal response was recorded.'})
    if error is not None or not final_url:
        result['outcome'] = 'incomplete'
        return result

    hop = hops[-1]
    hp = prefix + '/hops/' + str(len(hops) - 1)
    if type(hop.get('body_bytes')) is not int or hop['body_bytes'] < 0 or hop['body_bytes'] > 16777216:
        raise ValueError('invalid body byte count')
    if not isinstance(hop.get('body_sha256'), str) or not HEX256.fullmatch(hop['body_sha256']):
        raise ValueError('complete response lacks body digest')
    if hop.get('body_truncated'):
        raise ValueError('complete response cannot be truncated')

    if expected_media is not None:
        observed = media_type(hop.get('content_type', ''))
        state = 'unknown' if observed is None else ('match' if observed == expected_media else 'mismatch')
        findings.append({'code': 'media_type', 'state': state,
                         'evidence': hp + '/content_type', 'observed': observed,
                         'detail': ('Recorded Content-Type matches expectation.' if state == 'match'
                                    else 'Recorded Content-Type is absent or malformed.' if state == 'unknown'
                                    else 'Recorded Content-Type differs from expectation.')})
    if require_json:
        matches = [(i, c) for i, c in enumerate(checks) if c['name'] == 'json']
        if len(matches) > 1:
            raise ValueError('multiple JSON checks')
        state = ('unknown' if not matches else 'match' if matches[0][1]['ok'] else 'mismatch')
        findings.append({'code': 'json_check', 'state': state,
                         'evidence': prefix + '/checks' + ('/' + str(matches[0][0]) if matches else ''),
                         'detail': ('Strict JSON validation passed on the captured body.' if state == 'match'
                                    else 'No strict JSON check was requested in the capture.' if state == 'unknown'
                                    else 'The recorded strict JSON check failed.')})
    if min_bytes is not None:
        state = 'match' if hop['body_bytes'] >= min_bytes else 'mismatch'
        findings.append({'code': 'body_bytes', 'state': state,
                         'evidence': hp + '/body_bytes', 'observed': hop['body_bytes'],
                         'detail': 'Captured byte count meets minimum.' if state == 'match'
                                   else 'Captured byte count is below minimum.'})
    if not probe['ok']:
        result['outcome'] = 'source_failed'
    elif any(f['state'] == 'mismatch' for f in findings):
        result['outcome'] = 'mismatch'
    elif any(f['state'] == 'unknown' for f in findings):
        result['outcome'] = 'unknown'
    else:
        result['outcome'] = 'matches'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('report', help='saved report inside current workspace')
    parser.add_argument('--media', help='expected media type, e.g. application/json')
    parser.add_argument('--json-check', action='store_true', help='require recorded strict JSON validation')
    parser.add_argument('--min-bytes', type=int, help='minimum captured body bytes')
    args = parser.parse_args(argv)
    try:
        result = analyze(load_report(args.report), args.media, args.json_check, args.min_bytes)
    except (OSError, ValueError, UnicodeError, RecursionError, OverflowError):
        print(json.dumps({'schema': SCHEMA, 'error': 'Invalid report, expectation, or workspace path.'}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0 if result['outcome'] == 'matches' else 1


if __name__ == '__main__':
    sys.exit(main())
