# CSV Duplicate Review

Explain why a proposed CSV key is ambiguous before trying to reconcile or
patch datasets. For each duplicate group this read-only tool distinguishes
identical full rows from conflicting rows, lists the differing columns, and
shows every distinct field value with all its logical CSV record numbers.
Empty key components are flagged even in singleton groups. Nothing is paired,
selected, deduplicated or rewritten.

From the repository root, with Python 3.9+ and no dependencies or network:

```sh
python3 -B line-2/tools/csv-duplicates/duplicates.py line-2/tools/csv-duplicates/demo.csv --key item --key location --format text
```

Observed: six records, four distinct keys, one identical duplicate group
(`flint/north`), one conflicting group (`ochre/south`, quantity `2` versus
`3`), and one empty-key singleton. Exit **1 is expected**: it means findings,
not a failed execution. Exit 0 means unique nonempty keys; exit 2 means invalid
input/options. Omit `--format text` for structured `csv-duplicates/v1` JSON.
Repeat `--key` for composite keys. Record 1 is the header; record numbers are
logical records, so quoted multiline values occupy one record.

For an actual retained dataset, this also works offline:

```sh
python3 -B line-2/tools/csv-duplicates/duplicates.py shared/token-read-plan/observed.csv --key chain_id --key token_address --key field
```

Observed: six historical ZTO-first/IMD-second observations, six distinct keys,
no findings, exit 0. This is retained data, not a fresh chain observation.
Using just `token_address` instead produces two conflicting groups because
three different fields were recorded per token; key choice remains yours.

Checks:

```sh
python3 -B -m unittest discover -s line-2/tools/csv-duplicates -p 'test_*.py' -v
```

All 12 tests passed, covering full-row duplicates, conflicting values with
repeated occurrences, composite and empty keys, exact strings, multiline CSV,
control-safe text, malformed input, CLI statuses and unchanged input bytes.
The reused reconciler's 17 tests also passed in scratch.

Uses the committed sibling `csv-reconcile/reconcile.py` bounded reader:
UTF-8 with optional BOM, strict CSV, distinct nonempty headers, at most 16 MiB
and 100,000 data records, and resolved input paths within the current working
directory. Keep both tool folders together. Entire tables and reports are in
memory; output is complete and may exceed input size. These limits are not
CPU, memory or output budgets. Do not parse a changing input file concurrently.

Values remain exact strings: whitespace, case and numeric spellings are not
normalized. An identical duplicate is still ambiguous and is never declared
safe to remove. Empty-key group counts overlap duplicate categories.
`clean` establishes syntactic key eligibility only, not semantic identity or
correctness of values. JSON/text escape control characters; neither format
is intended as executable code. Output is stdout; the tool never writes data.
