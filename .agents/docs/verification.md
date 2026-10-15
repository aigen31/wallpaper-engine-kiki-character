# Proving a change

## The gate

```bash
./.venv/bin/python tools/verify.py
```

87 checks, one line each, non-zero exit on the first failure. It reads only the
shipped PNGs and `wallpaper/index.html`, so it runs in a second and needs no
build. Each group binds something that actually broke once:

| Group | What it binds |
|---|---|
| files, size | all 8 layers × 2 variants present, all 640×360 |
| alpha | binary on `bg`/`screen`/`girl`/`blink`, a real ramp on the light layers |
| palette | limited stays ≤ 129 colours, the reference variant is not quantised, the mouth ink survives |
| blink | a patch of 40–400 px, on the eyes — not a whole frame covering the open one |
| glow | never below y275, never on the eyes |
| light | no light layer touches row 0 — that line appeared across the top of a 16:10 monitor |
| browser | the page names exactly the layers on disk, loads nothing from the network, reads only declared properties, and puts the terminal canvas on the glass |
| build | every shipped PNG is byte-identical to what `build/` holds |

The last group is skipped, not failed, when `build/` is absent — a fresh clone
has no build output.

## The honest check

`verify.py` compares the shipped PNGs against the build directory, so it only
catches a hand-edited or stale layer. The stronger question is whether the
pipeline still produces the same art, and that one is:

```bash
tools/build_all.sh
git status --short wallpaper/layers/
```

Nothing here is nondeterministic — no model inference, no randomness, no
timestamps in the output — so an empty `git diff` means the run reproduced the
art exactly and a non-empty one means the art moved. 46 seconds. That is the
check to run after touching any threshold in `tools/`.

## Numbers are claims

`README.md` and [pipeline](pipeline.md) quote measured values: the run time, the
hole size, the glow's reach, the blink patch, the colour counts. Every one is a
property of the current scripts and the current reference. `verify.py` asserts
behaviour, not numbers, so it stays green while the prose goes quietly wrong.
When a number moves, grep for it and move it in both places.

## Adding a check

Put a `check("what it binds", condition, detail)` next to the fault it defends,
in the group for the stage that owns it. Prefer one that fails loudly on a real
regression over one that restates the implementation — a check that re-derives
the build from the same code it is checking proves nothing.
