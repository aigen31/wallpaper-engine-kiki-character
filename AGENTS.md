# AGENTS.md

A Wallpaper Engine web wallpaper, regenerated from one reference frame by a
seven-stage Python pipeline. The art is not drawn: it is derived, deterministically,
from `reference/` — and every derived pixel is checked against a gate.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt      # numpy, Pillow — nothing else
```

## Check your work

```bash
./.venv/bin/python tools/verify.py     # 87 checks, ~1 s, non-zero exit on failure
tools/build_all.sh                     # regenerate wallpaper/layers/, ~46 s
git status --short wallpaper/layers/   # empty iff the rebuild reproduced the art
```

Run the gate before you call a change done. Run the rebuild whenever you touched
anything under `tools/` — the diff it leaves *is* the answer to "did the art
move?". Nothing here is nondeterministic, so a change that was not meant to be
visible must leave that diff empty.

## Where to look

| Need | Read |
|---|---|
| What this is, how to install it, the measured numbers | [README.md](README.md) |
| The wallpaper itself — layers, animations, palettes, properties | [wallpaper/README.md](wallpaper/README.md) |
| The seven stages, the shared geometry, the constants | [pipeline](.agents/docs/pipeline.md) |
| The Wallpaper Engine contract and the traps in it | [wallpaper-engine](.agents/docs/wallpaper-engine.md) |
| How to prove a change is good | [verification](.agents/docs/verification.md) |
| Script shape, language, ES5 rule, dependencies | [conventions](.agents/docs/conventions.md) |
| The venv, the host gotchas, ComfyUI provenance | [environment](.agents/docs/environment.md) |
| The writing skills vendored in this repo | [skills](.agents/docs/skills.md) |
