# Import Context

See the syntactic surroundings of each explicit import in an unfamiliar Python
project without executing its code. This standard-library Python 3.10+ tool adds
outermost-first context records to the existing Import Map: function/class
bodies, if/else branches, try/except/else/finally, loops, with blocks and match
cases. Import resolution, edges, entry points, cycles and warnings remain intact.

From the repository root, offline:

```sh
python3 -B line-3/tools/import-context/context.py line-3/tools/import-context/examples
```

Observed: exit 0; eight import sites, two directly in the module body and six
nested. The example distinguishes imports beneath TYPE_CHECKING, its alternate
branch, an exception handler and a function. `optional_backend` is an external
name in source; it need not be installed because the source is never executed.

For a real project, pass its explicit Python import root within the current
workspace. `--json` preserves the complete map, per-site `contexts` and zero-based
UTF-8 byte `column`, collection inventory, hashes and limits. Context `line`
values and import `line` values are one-based. Each context names the AST `kind`
and child `branch`; for example, `Try.handlers / ExceptHandler.body` identifies
an exception handler, while `Try.finalbody` identifies a finally suite. Function
and class records include their names. Duplicate imports remain separate sites.

`--strict` exits 1 for any mapped issue, cycle or recognized dynamic call;
otherwise a completed scan exits 0. Invalid roots, exceeded input budgets or
analysis failures exit 2, with a refusal envelope and no partial map. Available
limits are `--max-files`, `--max-file-bytes`, `--max-total-bytes`, `--max-entries`
and `--max-depth`, inherited unchanged from Import Budget.

Actual source-only trial:

```sh
python3 -B line-3/tools/import-context/context.py shared/import-drift --json --strict
```

Observed exit 0: 27 modules, 44 local edges, 202 import sites (201 module-body,
one nested), no mapper issues, cycles or recognized dynamic calls. The retained
[observed-source.json](observed-source.json) includes the admitted source hashes.
This describes those bytes, not later versions of the tree.

Ten behavioral tests cover nested contexts, branch separation, guard spelling,
match/async constructs, duplicate same-line sites, relative resolution, source
encodings, warnings, budget refusal and source execution traps:

```sh
python3 -B -m unittest discover -s line-3/tools/import-context -p 'test_*.py' -v
```

## Limits

Context describes syntax, never reachability or execution timing. Both branches
stay in the graph. A class body can execute during import; a function can be
called immediately; a module-body import can still fail or be bypassed. Labels
for `TYPE_CHECKING` and `typing.TYPE_CHECKING` recognize exactly those positive
spellings. They do not resolve aliases, rebinding, negation or truth values.
Even the main-guard label is syntactic and can occur inside a function.

Import Budget collects source once; both AST passes use that same immutable
in-memory byte snapshot. No inspected Python is imported. Dynamic loading,
installed-package resolution and implicit package initialization are outside
the mapper's model. The root-level `__init__.py` and shadowed collision sources
remain outside its mapped modules; they still count toward collection budgets.
Parse failures and collisions remain visible. Hidden/dependency directories and
symlinks are skipped. Collection limits bound input sizes, not CPU, memory,
output size or elapsed time. Use a stable tree: this is not an OS sandbox.

The sibling delivered Import Budget and Import Map tools are required; no
third-party dependency, network, wallet or coin is needed.
