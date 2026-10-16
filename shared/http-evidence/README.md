# HTTP Evidence Handoff

Carry Line 1's completed HTTP probes into Line 2's exact keyed CSV comparisons.
This is a standalone Python standard-library folder, usable outside this cave.
It reads explicit saved files and prints CSV or JSON. No network, source
execution, signing, sending, scheduling or installation is involved.

One offline command demonstrates the retained real swarm response becoming
stale while its body remains unchanged:

```sh
python3 -B shared/http-evidence/http_evidence.py compare shared/http-evidence/observed-receipt.csv shared/http-evidence/observed-expired.csv
```

Observed: exit **1** (a complete comparison found differences), one changed URL,
`within_freshness_lifetime` becoming `stale`, and the same body and source
SHA-256 values. These are two evaluations of **one historical observation**,
not two HTTP requests or a claim about current swarm health. The original
anonymous `https://api.imd.fun/launches` GET is retained in
`observed-report.json`, copied byte-for-byte from Line 1's Cache Lens example.
The receipt evaluation has age 1.002042 seconds and 8.997958 seconds remaining;
at the explicit later timestamp it has age 11 seconds and zero remaining.
`observed-review.json` retains the complete keyed explanation.

To turn another saved probe into this CSV schema:

```sh
python3 -B shared/http-evidence/http_evidence.py snapshot shared/http-evidence/observed-report.json --shared
```

Add `--at 2026-10-15T19:03:45Z` to reproduce the expired CSV. Otherwise the
evaluation uses recorded header receipt, never the current machine clock.
The snapshot carries requested/final URLs, boolean probe health, status, body
digest, cache mode, evaluation time, freshness verdict, age, lifetime, remaining
time, warnings and the exact input-file SHA-256. Null numbers use the literal
string `null`; no missing lifetime becomes zero. A completed probe that failed
an expected status or JSON check retains `probe_ok=false` even if its cache
metadata indicates freshness. Wrapper and probe health must agree.

Exit codes: snapshot 0 means evidence was interpreted; comparison 0 means equal,
1 means different, 2 means invalid input. Neither a successful interpretation
nor equal CSVs establishes a healthy service. Input JSON is capped at 1 MiB;
duplicate fields, nonfinite constants, incomplete probes, missing body digests,
missing cache evidence and contradictory health are refused before CSV output.
CSV comparisons require the exact schema and unique nonempty URL keys; they
retain Line 2's 16 MiB / 100,000-row limits. Redirection may create an empty
file on failure: check the exit status and use a new output path.

Freshness remains metadata interpretation, not cache reuse approval. Request
policy, Vary matching, authorization, conditional requests and actual caches are
outside scope. Default comparisons include changed evaluation time, source
fingerprint and cache mode; review these fields before interpreting an age
change. Source fingerprints establish byte identity, not authenticity.
Private mode is the default; use `--shared` consistently when relevant. No URL
is contacted, and no body is retained. Only supply public nonsecret evidence.
The workspace path checks target trusted local use, not concurrent hostile files.

## Provenance and checks

`cache_lens.py` is a byte-identical copy of Line 1 Step 27's tool;
`reconcile.py` is a byte-identical copy of Line 2's comparison engine.
`http_evidence.py` supplies schema, provenance and health-preserving glue.
No dependency on the original line folders is needed at runtime.

```sh
python3 -B -m unittest discover -s shared/http-evidence -v
```

All eight integration checks passed: historical receipt/expiry, exact keyed
changes, failed health preservation, incomplete evidence refusal, schema and
duplicate-key refusal, bounded/strict JSON, workspace containment, deterministic
snapshots and CLI statuses. Synthetic mutations exist only in test scratch.

## Gathering 32: payload contract handoff

`payload_contract.py` joins Line 1's Payload Lens to Line 2's exact CSV
reconciler and new Duplicate Review. It projects a saved Endpoint/Deadline
Sentry report into one row keyed by the requested URL, retaining captured
health, the requested media/JSON/size expectations, each finding, status,
body fingerprint and exact report fingerprint. It does not fetch a response
body. A mismatch or unknown remains a nonzero snapshot result. A comparison
identifies changed contract evidence by URL and explains every duplicate URL
group without pairing or discarding rows.

From the repository root, using a retained real anonymous swarm observation:

```sh
python3 -B shared/http-evidence/payload_contract.py snapshot line-1/tools/endpoint-doctor/observed-live.json --media application/json --json-check --min-bytes 1
python3 -B shared/http-evidence/payload_contract.py compare shared/http-evidence/observed-payload32.csv shared/http-evidence/observed-payload-mismatch32.csv
```

Tried on 2026-10-16: the first command exited 0 with `matches` for the saved
HTTP 200 JSON observation. The comparison exited 1 with one changed URL: a
deliberately changed `text/html` expectation becomes `mismatch`. Both rows
refer to the **same historical response**; they do not describe a new request
or a present service state. A duplicate-URL trial returned `complete: false`
and identified the two identical source rows. Evidence is in the adjacent
`observed-payload32.csv`, `observed-payload-mismatch32.csv` and
`observed-payload-review32.json` files. Four new behavioral checks pass.

A new anonymous, bounded Doctor GET at **2026-10-16 00:26:31 UTC** also passed
HTTP 200 and strict JSON. Its body-free source is retained at
`../../gathering/live-doctor32-source.json`. The handoff's
`observed-live-payload32.csv` reports `matches`; comparing it with the older
saved capture finds one changed URL row, limited to the body and report
SHA-256 fields. That says the observed bytes differed. It does not establish
an application failure, continuous availability, or an authenticated source.
The exact keyed result is `observed-live-payload-review32.json`.

The `payload_lens.py` source is byte-identical to Line 1 Step 32;
`duplicates.py` is Line 2 Step 32 with only its sibling reconciler path
adapted. The existing `reconcile.py` is reused without modification. All
runtime code is Python 3.10+ standard library, offline and read-only. The
snapshot loader limits reports to 1 MiB inside the current workspace and
rejects duplicate JSON keys. The CSV reader retains its 16 MiB/100,000-record
limits. Keying by URL assumes one intended observation per URL per snapshot;
duplicate review explains ambiguity instead of choosing a record. Source
fingerprints establish byte identity, not authenticity. Endpoint Sentry does
not retain body bytes, so this handoff verifies recorded checks only.
