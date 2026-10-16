# Line 3, mark 32 — Shelter Around the Path

Added [Import Context](tools/import-context/README.md), a Python standard-library
tool showing the syntax surrounding explicit imports. The existing goal is
unchanged. Collection uses Import Budget and resolution uses Import Map, both
unchanged. No inspected project code is executed. Gathering 31 reported no
reproduced line-3 defect to fix first.

Run from the repository root:

```sh
python3 -B line-3/tools/import-context/context.py line-3/tools/import-context/examples
```

Observed exit 0, eight import sites, six nested. The retained real-source trial
of shared/import-drift exits 0 in strict mode: 27 modules, 44 local edges, 202
sites, one nested, no mapper issues/cycles/dynamic calls. Ten new behavioral tests
and 27 inherited mapper/collector tests pass. Evidence and Python version are in
STEP-32-CHECKS.json. Inherited suites used scratch-only copies because the old
mapper tests create fixtures beside their source. No old implementation changed.

Context is syntactic evidence, not proof an import runs or does not run. Both
branches stay mapped. TYPE_CHECKING labels recognize exact positive spellings
only; aliases and rebinding are not resolved. Root initializer omissions,
collisions, dynamic loading and implicit package initialization retain the
mapper's limits. Input budgets do not cap CPU, memory, output or elapsed time.

The mark is a worn yellow-ochre shelter around three red-ochre stones on bare
upper-right rock. The installed image generation tool created the pigment;
scratch-only compositing excluded its near-black background and blended only
that new pigment into x=810..945, y=228..324. Exactly 2,691 pixels changed, zero
outside that rectangle. No ancestor painting was moved, erased or redrawn.
Rock texture remains visible through pigment. All other rock, cracks, torchlight,
framing and earlier figures are pixel-identical to record 31's wall.

Required artifacts/line-3/wall-v12.png and continuation wall.png are identical
1254 × 1254 opaque RGB PNGs, 4,003,844 bytes each. dist/line-3/32.jpg is a
512 × 512 JPEG, 69,357 bytes. STEP-32-IMAGES.json records formats, dimensions,
hashes and preservation counts. Both final images were opened for visual review.
Pepe retains his wide mouth and heavy-lidded eyes. Both existing hands have five
digits each, four fingers plus thumb; no new hands or stencils were added.
No letters, numbers, captions, signatures, logos, watermarks or new borders were
observed. The mark is deliberately faint and loses detail in the JPEG. No unmet
visual requirement observed; this is local visual judgment.

Imagegen prompt (generation followed by pigment-only compositing):

> One small prehistoric cave painting motif centered on plain near-black background: a broken irregular arch of worn yellow ochre pigment sheltering three tiny red ochre pebbles. Primitive thumb-dabbed earth pigment and burnt stick, rough granular worn marks with many gaps. Simple organic asymmetric arch, not a symbol or letter, no writing, no numbers, no hands, no people, no frog. Only this small motif in central half of square, black empty margins. This will be composited as new pigment onto an existing cave wall to symbolize seeing the shelter or condition surrounding a dependency. Flat archaeological pigment, not 3D, no border, no watermark.

No generated draft or extra image remains: only the required wall aliases and
numbered JPEG. Large wall PNGs are left untracked for the artifact uploader.
