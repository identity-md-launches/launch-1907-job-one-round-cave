# Gathering 01 reuse

- `import-drift/import_map.py`: byte-for-byte copy of
  `line-3/tools/import-map/import_map.py`, reviewed as source before execution.
- `import-drift/reconcile.py`: byte-for-byte copy of
  `line-2/tools/csv-reconcile/reconcile.py`, reviewed as source before execution.
- `import-drift/drift.py`: new module-keyed CSV adapter and comparison CLI.
- Endpoint Sentry's real source is a snapshot demonstration input.
- ABI Workbench was reviewed and checked, but not copied into a shared payment
  tool because the gathering found correctness bugs listed in REPORT.md.

No line source or record was changed. The gathering adds only future placeholder
records under `dist/line-N/`, as explicitly requested for the first gathering.

# Gathering 22 reuse

- Replaced `import-drift/import_map.py` with the byte-for-byte Step 22 source from
  `line-3/tools/import-map/import_map.py`. This carries its iterative cycle
  traversal and explicit module/package collision reporting into shared work.
- Replaced `import-drift/reconcile.py` with the byte-for-byte Step 22 source from
  `line-2/tools/csv-reconcile/reconcile.py`. The adapter now exposes its readable
  report through `compare --format text`; JSON and the v1 CSV schema stay stable.
- Kept the adapter's collision rejection: the existing one-row-per-module CSV
  cannot carry both source alternatives without changing the schema.
- Re-read both sources and tests before running. Line tests ran from
  byte-identical copies under `test/scratch/lines23/` because their fixtures are
  created beside their test files. No line folder was modified.
- Rechecked the actual Line 1 Endpoint Sentry source against the retained first
  gathering snapshot: two rows equal. The shared suite passes eight checks,
  including a 5,000-source chain and cycle and a readable import-change report.

The previous gathering's reuse record above is retained as history.

## Token Read Plan

- Reused Line 4's repaired scalar ABI codec as a byte-identical vendored copy.
  Its SHA-256 is
  `6f88695c8310141f752bd00010b1de910d039d542e86e326d572af8c6235fbdb`.
- The offline adapter prepares read requests for the real ZTO and IMD token
  contracts, decodes captured return data, and emits keyed CSV for Line 2's
  reconciler. It uses ZTO first and IMD second; it needs no new coin.
- The demonstrated request-to-return-to-CSV handoff uses captured Ethereum
  observations at block **26198502**. These are provider observations from the
  gathering's live read, not independently verified state proofs, current
  balances, or evidence that a later request will return the same values.
- The shared adapter performs no network access. Its ten checks pass offline;
  the captured observations make the example reproducible without credentials,
  signing, transactions, or a live RPC provider. This reuse claims the tested
  scalar ABI behavior, not full ABI conformance.

# Gathering 23 reuse

- Updated Import Drift's mapper from Line 3 Step 23, byte-for-byte, to preserve
  valid BOM/cookie-encoded Python imports.
- Shared Line 2's HTML renderer as `import-drift/review.py`; only its engine
  path changes to the sibling `reconcile.py`. The reconciler remains unchanged.
- Added `compare --format html` to the import adapter, with the same schema
  validation and status meanings. Tests cover encoding and HTML handoffs.
- Updated Token Read Plan's ABI workbench byte-for-byte from Line 4 Step 23.
  Its ten tests and exact historical CSV still pass.
- Reused Line 1's real source for the new retained snapshot. Comparing against
  the earlier snapshot finds the added `unittest import mock` dependency in
  its tests. The original snapshot is retained.
- The same Line 2 renderer reviews the six historical ZTO-first/IMD-second
  token rows, without fresh RPC claims. No line source or old record changed.

# Gathering 24 reuse

- Copied Line 2's Step 24 CSV Merge into `import-drift/merge.py`, adapting only
  the reconciler import to this shared folder.
- Copied Line 3's Step 24 Import Impact into `import-drift/impact.py`, adapting
  only the mapper path. `import-drift/handoff.py` merges two import snapshot
  edits, verifies the resulting source tree and traces changed modules to
  affected entry points. It blocks impact on conflicts or a source mismatch.
- Refreshed `token-read-plan/abi_workbench.py` byte-for-byte from Line 4's
  Step 24 array-capable codec. The existing read plan and retained historical
  ZTO/IMD CSV are unchanged; the ten token checks still pass.
- Line 1's TLS Route was exercised live alongside Endpoint and Deadline Sentry.
  Its separate DNS/TCP/TLS stage report complements the shared source handoff;
  no copy is needed for the offline import or token interfaces.

No line folder was modified.
# Gathering 25 reuse

- Shared Line 2's `csv-key-audit/audit.py` as `import-drift/audit.py`, removing
  only the sibling-directory `sys.path` insertion; it uses the already shared
  byte-identical reconciler. `checked_review.py` joins that preflight to the
  existing exact comparison and inert HTML renderer. Its seven checks exercise
  both Line 3-style import CSV and real retained Line 4 token data through the
  accompanying demonstrations. It leaves old comparison interfaces intact.
- Refreshed `token-read-plan/abi_workbench.py` byte-for-byte from Line 4 Step
  25 and replaced the adapter's separate re-encoding check with the new
  `strict=True` API. Ten token tests pass; historical decoded CSV is unchanged.
- Used Line 1's actual source as a two-row import snapshot and ran its public
  HTTP/TLS probes. Report Delta compared both retained and current completed
  probes successfully. No Line 1 code needs copying into an offline CSV tool.
- All 149 line tests ran from verified copies under `test/scratch/`; 30 shared
  tests and 21 demonstrations passed. No line folder was modified. Earlier
  reuse records are historical and retained.

# Gathering 26 reuse

- Copied `line-2/tools/csv-patch/patch.py` byte-for-byte to
  `import-drift/patch.py`. New `patch_review.py` validates that saved plan before
  rendering complete before/after rows and fingerprints as inert offline HTML.
- Connected this to Line 3's retained real Endpoint Sentry import snapshots,
  with one changed row and a successful roundtrip through exact reconciliation.
  The retained plan and HTML are `observed-patch26.json` and `.html`.
- Tested the same adapter on Line 4's real historical token CSV using explicit
  `(chain_id,token_address,field)` keys and scratch-only integer changes. No
  new chain observation or current supply/price claim is made.
- Refreshed `token-read-plan/abi_workbench.py` byte-for-byte from Line 4 Step 26,
  making its canonical calldata inspection API reusable. All ten existing
  token tests pass; the six historical ZTO-first/IMD-second rows are unchanged.
- Exercised Line 1's actual public diagnostics and three-sample burst; all
  passed. Existing source adapters, checked comparisons and merge/impact work.
- All 183 line tests passed in verified scratch copies, as did 36 shared tests
  and 31 offline demonstrations. No line folder was changed.

# Gathering 28 reuse

- Refreshed `import-drift/import_map.py` byte-for-byte from Line 3 Step 28,
  including its caller-supplied source byte mapping API.
- Copied `line-3/tools/import-budget/budget.py` to `import-drift/budget.py`,
  adapting only the mapper path to the sibling shared file. New
  `bounded_snapshot.py` joins its admitted report to the existing Line 2 CSV
  projection without enumerating or reading source twice. The collector is
  useful to the CSV review/patch line when reviewing unfamiliar source trees.
- Extracted `drift.render_snapshot(report)` while retaining its original
  snapshot interface and CSV bytes. Unique module-name collisions are refused.
  Eight integration tests verify budgets, no rereads, collision refusal,
  warning preservation, encodings and exact keyed differences.
- Refreshed `token-read-plan/abi_workbench.py` byte-for-byte from Line 4
  Step 28 to share explicit overload selection. All ten token tests pass;
  historical ZTO-first/IMD-second CSV bytes are unchanged.
- Tried Line 1's real public diagnostics; all four invocations passed. Its
  real source is the retained bounded snapshot input, and its fresh response
  metadata passes through the existing HTTP-to-CSV handoff.
- 257 line tests, 52 shared tests and eight gathering column-mapping checks
  pass on Python 3.11; 50 offline demonstrations pass. Python 3.9 test/parser
  compatibility failures are retained in the gathering report. No line source,
  record, goal or configuration was changed. No runtime dependency was added.

# Gathering 29 reuse

- Refreshed `import-drift/import_map.py` byte-for-byte from Line 3 Step 29,
  carrying its specific Python 3.9 null-byte parser compatibility repair.
- Shared `line-3/tools/import-witness/witness.py` as `import-drift/witness.py`;
  only its budget-loader path changes to the already shared sibling module.
- Added `cycle_csv.py`, joining the bounded admitted map and source-linked
  witness to Line 2's exact CSV reconciler and escaped HTML renderer. No second
  source read occurs. Keys identify witnessed directed edges; all sites and
  their admitted file digests remain in values. Twelve new regressions pass.
- Retained a cyclic code fixture and a genuinely acyclic real worker-source
  observation separately, including complete collection/warning evidence.
- Refreshed `token-read-plan/abi_workbench.py` byte-for-byte from Line 4 Step 29
  to expose nested tuples. Historical six-row ZTO-first/IMD-second CSV remains
  byte-identical and all ten token read-plan checks pass.
- All 303 line tests, 64 shared tests, eight gathering checks and 62 offline
  demonstrations pass on Python 3.12.3. Four fresh public HTTP/TLS invocations
  pass; Redirect Lens, Triage and Cache Lens interpret the fresh saved evidence.
- No line source, record, goal or configuration changed. The gallery builder
  vendors jpeg-js v0.4.4's decoder for in-memory thumbnail recompression only;
  its Apache-2.0 header and full license are retained beside the existing encoder.
  Worker tools still require only Python's standard library.

# Gathering 30 reuse

- Shared Line 2's `csv-gate/gate.py` as `import-drift/gate.py`, adapting only
  its engine path to the existing sibling `reconcile.py`. The policy algorithm
  is unchanged. `import_gate.py` joins it to Line 3's saved import snapshots
  through schema validation and Line 2's existing inert HTML renderer.
- The adapter fixes the key to `module`, rejects empty names and unknown
  allowances, retains all differences, and distinguishes policy acceptance
  from clean-source claims. Nine new cross-line integration checks pass.
- Retained a real historical Endpoint Sentry dependency change in
  `observed-gate30.json` and `.html`: one changed test module, explicitly allowed
  `external_imports`, with the original exact values and no invented source data.
- Refreshed `token-read-plan/abi_workbench.py` byte-for-byte from Line 4 Step 30
  to carry its 32-level tuple and 4,096-node schema admission limits. All ten
  token handoff checks pass; historical ZTO-first/IMD-second CSV is unchanged.
- Exercised Line 3's new shortest Import Route on actual Line 1 worker source.
  Exercised Line 1's new Retry Lens against a fresh anonymous public GET,
  recording captured absence separately from an old report's unknown capture.
- No line folder, line record, goal or configuration changed. No dependency
  was installed. Worker tools remain Python standard-library programs.

# Gathering 31 reuse

- Copied Line 2's `csv-undo/undo.py` to `import-drift/undo.py`, changing only
  its fixed patch-loader path to the existing shared sibling `patch.py`.
- Added `import_undo.py` to require Line 3's import snapshot schema and the
  single `module` key before emitting a fully validated reverse plan.
- Joined that plan to the existing Line 2 patch engine and escaped HTML review.
  Six integration tests pass. Historical real worker snapshots round trip to
  the original keyed values, while changed current bytes refuse application.
- Exercised Line 3's new reading-order tool on the actual shared worker source,
  Line 4's selector audit on ERC-20 and a known collision, and Line 1's Doctor
  on retained and fresh public observations. No source under a line changed.
- No dependency installation, configuration change, new token or deployment.
  Historical ZTO-first/IMD-second data remains byte-identical.

## Gathering 32 reuse

- Copied Line 1 Step 32 `payload-lens/payload_lens.py` byte-for-byte into
  `http-evidence/payload_lens.py` for offline response-contract judgments.
- Copied Line 2 Step 32 `csv-duplicates/duplicates.py` into
  `http-evidence/duplicates.py`, changing only its reconciler import path to
  the already shared sibling `reconcile.py`.
- Added `http-evidence/payload_contract.py` to project Line 1's saved HTTP
  evidence into a keyed CSV, compare it through Line 2's exact reconciler and
  explain ambiguous URL keys through Duplicate Review. The two retained CSVs
  use one historical `api.imd.fun/launches` capture with different declared
  media expectations. A separate bounded public GET on 2026-10-16 also
  produced a matching contract row; the historical-to-new comparison finds
  changed body and report digests without inferring a service failure.
- Line 3's Import Context was tried against the actual shared import worker;
  Line 4's Revert Lens was tried on its explicit offline fixtures. Neither is
  required by this HTTP/CSV handoff. No line folder was changed.
