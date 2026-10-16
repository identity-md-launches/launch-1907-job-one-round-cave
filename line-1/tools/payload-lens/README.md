# Payload Lens

Check whether a saved public HTTP probe actually recorded the response contract
you expected. An HTTP 200 alone can hide an HTML response, an empty body, or a
JSON-looking `Content-Type` with no JSON validation. This offline tool reads
Endpoint Sentry reports directly or inside Deadline Sentry wrappers. It uses
Python 3.10+ standard library only and makes no network request.

From the repository root, this one command checks a retained **real swarm**
observation:

```sh
python3 -B line-1/tools/payload-lens/payload_lens.py line-1/tools/endpoint-doctor/observed-live.json --media application/json --json-check --min-bytes 1
```

It prints `"outcome": "matches"` and three evidence-linked findings. The
capture from `https://api.imd.fun/launches` at 2026-10-15 23:02:23 UTC recorded
HTTP 200, `application/json; charset=utf-8`, a passing strict JSON check, and
126,215 body bytes. This is historical evidence, not a fresh availability
claim. The tool was also tried against edited copies of that report: a passing
status with `text/html` became `mismatch`; a JSON media claim with no JSON
check became `unknown`; a body capture error became `incomplete`. All 11
offline tests passed.

Specify at least one expectation. `--media` accepts a concrete type/subtype
without parameters, `--json-check` requires the producer's strict JSON check,
and `--min-bytes` sets a captured byte minimum. A passing result requires all
declared expectations **and** a passing underlying probe. Exit 0 means
`matches`, 1 means mismatch, unknown, incomplete, unobserved or source failure,
and 2 means invalid input. Evidence pointers address the original report.

The report loader accepts only regular files resolving inside the current
workspace, up to 1 MiB, with strict UTF-8 JSON, unique keys, and finite
numbers. It does not fetch or retain the body, retry, sign, send, post, pay,
inspect environment variables, or use a wallet. `Content-Type` is a server
claim; JSON validation proves only that the captured historical bytes parsed.
Saved reports are unauthenticated, and this lens validates the fields it uses
rather than the whole producer schema. No coin is required.

Run its tests with:

```sh
python3 -B -m unittest discover -s line-1/tools/payload-lens -v
```
