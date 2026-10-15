#!/usr/bin/env bash
# Rebuild every shipped raster, from reference/kiki-source.png to
# wallpaper/layers/. Nothing here is nondeterministic -- there is no model
# inference and no randomness -- so after a run `git status` is the honest
# answer to "did that change the art?".
#
#   tools/build_all.sh              # the whole chain
#   SKIP_UPSTREAM=1 tools/build_all.sh   # from build/parts onwards
#
# SKIP_UPSTREAM exists because the first three steps are minutes of heat
# diffusion and only matter when the reference or a threshold in
# build_screen/build_layers/build_shadow changed.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
PY="${PYTHON:-$ROOT/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "no interpreter at $PY -- run: python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if [ -z "${SKIP_UPSTREAM:-}" ]; then
  echo "== 1/6  inpaint the baked terminal text out of the glass"
  "$PY" tools/build_screen.py
  echo "== 2/6  split the frame into parts at source resolution"
  "$PY" tools/build_layers.py
  echo "== 3/6  project the witch's shadow onto the floor"
  "$PY" tools/build_shadow.py
else
  echo "== 1-3/6  skipped (SKIP_UPSTREAM)"
fi

echo "== 4/6  the screen's light back onto her"
"$PY" tools/build_glow.py

echo "== 5/6  frame the scene, shut the eyes, downscale four ways"
"$PY" tools/reframe.py
"$PY" tools/make_blink.py
WE_PARTS="$ROOT/build/parts_framed" WE_STAGE="$ROOT/build/stage_full" \
  WE_PALETTE=0 "$PY" tools/compose.py
WE_PARTS="$ROOT/build/parts_framed" WE_STAGE="$ROOT/build/stage_limited" \
  WE_PALETTE=128 "$PY" tools/compose.py
WE_PARTS="$ROOT/build/parts_framed" WE_STAGE="$ROOT/build/stage_full_closed" \
  WE_PALETTE=0 WE_GIRL=girl_closed "$PY" tools/compose.py
WE_PARTS="$ROOT/build/parts_framed" WE_STAGE="$ROOT/build/stage_limited_closed" \
  WE_PALETTE=128 WE_GIRL=girl_closed \
  WE_PALETTE_FROM="$ROOT/build/stage_limited/palette.npy" "$PY" tools/compose.py

echo "== 6/6  blink diff, and the stage into wallpaper/layers"
"$PY" tools/emit_layers.py

echo
echo "now run: $PY tools/verify.py"
