# Revert Lens

Read saved Solidity revert bytes entirely offline. Built-in `Error(string)`
reasons and `Panic(uint256)` codes work without an ABI. Supply an ABI to interpret
custom errors, including the Workbench's supported scalar arrays and nested
tuples. Python 3.10+ and the companion `abi-workbench` folder are all it needs;
every runtime import is in the standard library.

Run this command from the repository root to see it working:

```sh
python3 -B line-4/tools/revert-lens/revert_lens.py --demo
```

Tried locally: exit 0, selector `0x08c379a0`, signature `Error(string)`, reason
`insufficient ZTO`. These are explicitly constructed offline bytes, not an
observed ZTO failure, balance, or payment. No network, wallet, key, environment
read, signing, sending, deployment or external writes occur.

Decode your own raw bytes:

```sh
python3 -B line-4/tools/revert-lens/revert_lens.py --data 0x4e487b710000000000000000000000000000000000000000000000000000000000000011
```

Tried locally: `Panic(uint256)` with code `0x11`, described as arithmetic overflow
or underflow. An unrecognized panic code is retained, with no guessed meaning.

For custom errors, add `--abi PATH`. The supplied `token-errors.json` contains
two [ERC-6093](https://eips.ethereum.org/EIPS/eip-6093) error schemas. It is an
interface fixture, not a claim that ZTO or IMD implements that interface. A test
uses ZTO's actual token address only as an illustrative decoded address value.
Any token worker should obtain the actual contract's ABI and saved revert bytes.

Input is raw even-length `0x` hex, with the four-byte selector first. Extract it
from a saved RPC error yourself; this tool does not assume a provider-specific
JSON envelope or contact a provider. Optional ABI paths must resolve inside the
current working directory, including through symlinks. Keep inputs in your
workspace and invoke from its root. ABI JSON accepts a UTF-8 BOM and rejects
duplicate fields.

Exit codes and JSON statuses:

| Exit | Status | Meaning |
| --- | --- | --- |
| 0 | `decoded` | One supplied or built-in signature and canonical argument bytes |
| 1 | `empty` | No bytes; no reason can be inferred |
| 1 | `unknown` | No matching signature in supplied errors or built-ins |
| 1 | `ambiguous` | Multiple distinct signatures share the selector |
| 2 | stderr `error:` | Invalid input, unsupported error schema, duplicate custom signature, budget exceeded, or malformed bytes for a unique known selector |

Ambiguity is reported before inspecting the argument body. Even if only one
candidate could decode that body, the tool does not choose it. Repeated built-in
signatures are merged with the canonical built-in declaration; duplicate custom
signatures are refused, including equivalent `uint`/`uint256` declarations.
Every supplied error schema must be supported, so skipped errors cannot hide a
collision. Unrelated function/event types need only pass structural validation.
An ABI missing an error can still hide collisions; this is not a complete
inventory of any deployed contract.

Matched argument bodies always use strict canonical decoding: malformed offsets,
nonzero padding, gaps, overlaps and trailing words are refused. Unknown selectors
and ambiguous data are not schema-validated. Bodies are limited to 1 MiB plus
the selector; ABI files to 1 MiB; custom-error declarations to 256; signatures
to 8,192 characters. The Workbench's 256-parameter, 32-level tuple, 4,096-node
and 4,096-array-item limits apply. Tuple arrays, nested arrays, dynamic-element
arrays and fixed point remain unsupported. Bounds limit admitted data, not exact
CPU, memory or wall time. Use trusted local regular files; path resolution is
not a sandbox against concurrent filesystem changes.

Regression command:

```sh
python3 -B -m unittest discover -s line-4/tools/revert-lens -v
```

All 13 tests passed locally. They exercise independently laid-out reason,
panic and custom-error bytes, nested tuples, zero arguments, an ERC-6093 fixture,
a known real selector collision, malformed layouts and UTF-8, unsupported
schemas, duplicate signatures, limits, path rejection and CLI exit behavior.
The first run caught a test assertion's incorrect error-message pattern; it was
corrected and the suite passed. Existing codec source was not modified.

The encoding follows the [Solidity ABI error specification](https://docs.soliditylang.org/en/latest/abi-spec.html#errors).
Panic descriptions follow [Solidity's panic table](https://docs.soliditylang.org/en/latest/control-structures.html#panic-via-assert-and-error-via-require).
Error bytes can be fabricated and can propagate from another contract. A decoded
name or panic description verifies neither origin, contract identity, on-chain
state nor actual execution. `decoded` denotes byte interpretation only.
