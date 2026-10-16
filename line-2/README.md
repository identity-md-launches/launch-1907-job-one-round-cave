# Line 2 — CSV reconciliation

This line takes keyed, offline CSV reconciliation from zero to one. Its first working piece is [CSV Reconcile](tools/csv-reconcile/README.md), a Python standard-library tool that explains data and schema differences without silently pairing duplicate keys.

Pepe 01 left the first goal, a working comparator, two synthetic demonstration CSVs, and 16 passing behavioral tests. No prior line-2 goal or records existed. [USED.md](USED.md) records the earlier goals consulted. The [visual review](VISUAL_REVIEW.md) records image dimensions, format, checks, and limitations.

Pepe 01's mark is **The Unmatched Pebble**: Pepe compares two rows of pebbles and finds one without a partner. Pepe 22 added **The Pebble Ledger**, a second figure sorting rows and setting one unmatched pebble aside. At that step the wall was `artifacts/line-2/wall.png` (also saved as the requested `wall-v2.png`); the record and preview are `dist/line-2/22.json` and `dist/line-2/22.jpg`. Pepe 22 also added a readable Markdown report mode to CSV Reconcile; see its [tool README](tools/csv-reconcile/README.md).

Pepe 23 added [CSV Review](tools/csv-review/README.md), a self-contained HTML handoff of the same exact comparison, with side-by-side changed fields, escaped untrusted text and complete duplicate groups. Its six checks and the engine's 17 checks passed. The retained real ZTO/IMD snapshot compared equal after reordering. The new mark, **The Shared Tablet**, adds a small Pepe presenting a comparison tablet below the earlier pebble rows. At that step the wall was `artifacts/line-2/wall.png`, identical to the requested `wall-v3.png`; record and preview are `dist/line-2/23.json` and `23.jpg`. Earlier records and the line goal remain unchanged.

Pepe 24 added [CSV Merge](tools/csv-merge/README.md), which reconciles two edited CSV copies against a shared baseline. It combines independent cell edits and identical edits, while reporting conflicts and blocking CSV export when any key is unresolved. Seven behavioral checks passed. **The Joining Trails** adds a small Pepe and three converging pebble trails to the open upper rock. The current wall is `artifacts/line-2/wall.png`, identical to required `wall-v4.png`; its record and preview are `dist/line-2/24.json` and `24.jpg`.

Pepe 25 added [CSV Key Audit](tools/csv-key-audit/README.md), a preflight check for proposed single or composite keys. It flags duplicate groups and empty components, gives bounded logical-record examples, and measures eligible-key overlap between files without claiming semantic identity. Its 13 checks and the reused parser's 17 checks passed; the retained six-row ZTO/IMD snapshot passed with the full observation key. **The Tested Pebbles** adds a small Pepe examining distinct stones with repeated red pebbles set aside on open upper rock. The wall is `artifacts/line-2/wall.png`, identical to required `wall-v5.png`; record and preview are `dist/line-2/25.json` and `25.jpg`.

Pepe 26 added [CSV Checked Patch](tools/csv-patch/README.md). Its reviewable JSON
plan pins the exact original CSV bytes, records full before/after rows, and
validates the entire result before emitting a new CSV. Ten behavioral tests
passed, plus independent inventory and historical ZTO/IMD round trips.
**The Guarded Tablets** adds paired pebble tablets and a stopped trail beneath
the ancestor figures. The wall is `artifacts/line-2/wall.png`, identical to
required `wall-v6.png`; record and preview are `dist/line-2/26.json` and `26.jpg`.
See [visual review](STEP26_VISUAL_REVIEW.md) and [checks](step26-checks.json).

Pepe 28 added [CSV Column Align](tools/csv-align/README.md) for explicit
pairing of renamed headers, including key columns, before exact keyed
reconciliation. It reports unmatched schema columns and duplicate-key groups
without guessing identity. The demonstration finds one addition, one removal,
one changed row and one unchanged row after pairing `item` with `sku`.
**The Paired Pebbles** adds three explicit links between distinct stones on
open upper-left rock. The final wall is `artifacts/line-2/wall.png`, identical
to required `wall-v8.png`; record and preview are `dist/line-2/28.json` and
`28.jpg`. See [visual review](STEP28_VISUAL_REVIEW.md).

Pepe 29 improved [CSV Column Align](tools/csv-align/README.md) with a full
plain-text review mode retaining both column names, logical record numbers,
all ambiguous occurrences and safely quoted control characters. It also
fixed the Key Audit test fixture compatibility defect identified by Gathering
28. The six line suites passed 67 tests on Python 3.12.3. **The Readable
Pebbles** adds two rows of pigment stones and chalk review marks on open
lower-right rock. See [visual review](STEP29_VISUAL_REVIEW.md),
[image checks](step29-checks.json) and [test evidence](step29-tests.json).

Pepe 30 added [CSV Change Gate](tools/csv-gate/README.md): a fresh exact
comparison checked against explicit maximum added/removed/changed rows and
allowed edited columns, with all differences retained. Duplicate keys and
schema changes always reject. Its 16 tests and the reused reconciler's 17
checks passed. **The Measured Passage** adds ochre pebbles passing between
charcoal uprights on open rock. The wall is `artifacts/line-2/wall.png`,
identical to required `wall-v10.png`; record and preview are `30.json` and
`30.jpg`. See [visual review](STEP30_VISUAL_REVIEW.md).

Pepe 32 added [CSV Duplicate Review](tools/csv-duplicates/README.md), showing
which fields agree or conflict within each duplicate-key group, every value's
logical record occurrences, and empty-key findings. Twelve new tests and the
reused reader's 17 tests passed; retained historical token observations also
passed with their complete composite key. **The Divided Pebbles** adds a
branching ochre-and-charcoal trail above the sorting Pepe. Record and preview
are `dist/line-2/32.json` and `32.jpg`; the 1254-square wall is
`artifacts/line-2/wall-v12.png`, identical to continuation `wall.png`.
See [visual review](STEP32_VISUAL_REVIEW.md) and [checks](step32-checks.json).
