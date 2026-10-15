"""The gate. Run this before calling any change to the wallpaper done.

Every check here is a bug that actually shipped once, or a coupling that would
break silently. None of them restates the build; they all fail on a real
regression. Exits non-zero on the first failed check, and prints one line per
check either way.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (FRAME_SCALE, FRAME_TOP, LAYERS, PX, SCREEN, SRC_W,  # noqa: E402
                   STAGE_H, STAGE_W, WALLPAPER)

VARIANTS = ('full', 'limited')
CUTOUTS = ('bg', 'screen', 'girl', 'blink')      # alpha must be 0 or 255
GRADIENTS = ('light', 'halo', 'shadow', 'glow')  # alpha must be a real ramp
MOUTH_RGB = (208, 138, 116)

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = '') -> None:
    global checks
    checks += 1
    if not ok:
        failures.append(name)
    print(f"[{'ok' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ''))


def load(variant: str, name: str) -> np.ndarray:
    return np.asarray(Image.open(LAYERS / variant / f'{name}.png').convert('RGBA'))


# --------------------------------------------------------------- the files
for variant in VARIANTS:
    for name in CUTOUTS + GRADIENTS:
        p = LAYERS / variant / f'{name}.png'
        check(f'{variant}/{name}.png exists', p.exists(), str(p) if not p.exists() else '')

if failures:
    print('\nthe layer set is incomplete; nothing else can be checked')
    raise SystemExit(1)

for variant in VARIANTS:
    for name in CUTOUTS + GRADIENTS:
        a = load(variant, name)
        check(f'{variant}/{name} is {STAGE_W}x{STAGE_H}',
              a.shape[:2] == (STAGE_H, STAGE_W), str(a.shape))

# ------------------------------------------------------------------- alpha
# A half-covered edge becomes a smeary fringe the moment `image-rendering:
# pixelated` blows it up, so the cut-outs are binary. Light is the opposite:
# thresholding it once left 1.5% of the glow standing.
for variant in VARIANTS:
    for name in CUTOUTS:
        a = load(variant, name)[..., 3]
        bad = int(((a != 0) & (a != 255)).sum())
        check(f'{variant}/{name} alpha is binary', bad == 0, f'{bad} partial px')
    for name in GRADIENTS:
        a = load(variant, name)[..., 3]
        nz = a[a > 0]
        check(f'{variant}/{name} alpha is a ramp',
              len(nz) == 0 or (nz != 255).any() or a.max() < 255,
              f'{len(nz)} px, all {nz.max() if len(nz) else 0}')

# ------------------------------------------------------------------ palette
# The limited variant has to be *limited*, and the mouth ink is the deliberate
# extra entry: two logical pixels the quantiser has no colour for.
for name in ('bg', 'screen', 'girl'):
    a = load('limited', name)
    cols = len(np.unique(a[a[..., 3] > 0][:, :3], axis=0))
    check(f'limited/{name} stays inside the palette', cols <= 129, f'{cols} colours')

g_full = load('full', 'girl')
g_lim = load('limited', 'girl')
full_cols = len(np.unique(g_full[g_full[..., 3] > 0][:, :3], axis=0))
lim_cols = len(np.unique(g_lim[g_lim[..., 3] > 0][:, :3], axis=0))
check('the reference variant is not quantised', full_cols > lim_cols * 4,
      f'{full_cols} vs {lim_cols} colours')

mouth = np.all(g_lim[..., :3] == MOUTH_RGB, axis=2) & (g_lim[..., 3] > 0)
check('the mouth ink survived the quantiser', 2 <= int(mouth.sum()) <= 8,
      f'{int(mouth.sum())} px of {MOUTH_RGB}')

# ------------------------------------------------------------------- blink
# The overlay is the difference between the two eye states, so it is a patch
# the size of the eyes and nothing else. A whole-frame blink layer would mean
# the open frame underneath is being covered up.
for variant in VARIANTS:
    a = load(variant, 'blink')
    n = int((a[..., 3] > 0).sum())
    ys, xs = np.nonzero(a[..., 3] > 0)
    check(f'{variant}/blink is a patch, not a frame', 40 <= n <= 400, f'{n} px')
    check(f'{variant}/blink sits on the eyes',
          n > 0 and 190 <= xs.min() and xs.max() <= 280 and 120 <= ys.min() and ys.max() <= 170,
          f'x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}')

# -------------------------------------------------------------------- glow
# Three separate faults are pinned here. The glow must not reach the floor (the
# screen emits nothing below its own glass), it must not swallow the eyes, and
# no light layer may touch the top row -- that last one put a bright line across
# the top of a 16:10 monitor.
for variant in VARIANTS:
    glow = load(variant, 'glow')
    a = glow[..., 3]
    below = int(a[275:].sum())
    check(f'{variant}/glow never reaches the floor', below == 0, f'{below} px below y275')
    eyes = a[131:158, 206:256].max() if a.size else 0
    check(f'{variant}/glow stays out of the eyes', eyes <= 32, f'max alpha {eyes} on the eyes')

for variant in VARIANTS:
    for name in ('halo', 'light', 'glow'):
        a = load(variant, name)[..., 3]
        check(f'{variant}/{name} leaves the top row empty', int(a[0].sum()) == 0,
              f'row 0 sums to {int(a[0].sum())}')

# ----------------------------------------------------------- the browser
html = (WALLPAPER / 'index.html').read_text()
m = re.search(r'var LAYER_NAMES = \[([^\]]*)\]', html)
named = [s.strip().strip('"') for s in m.group(1).split(',')] if m else []
on_disk = sorted(p.stem for p in (LAYERS / 'full').glob('*.png'))
check('index.html names exactly the layers on disk', sorted(named) == on_disk,
      f'page {sorted(named)} vs disk {on_disk}')

bad = re.findall(r'(?:src|href)="(?!#)([^"]+)"', html)
external = [u for u in bad if '://' in u or u.startswith('//')]
check('the wallpaper loads nothing from the network', not external, str(external))

props = json.loads((WALLPAPER / 'project.json').read_text())
declared = set(props.get('general', {}).get('properties', {}))
# Only the user properties: `applyGeneralProperties` is handed `fps` by the
# host and it is deliberately not something the wallpaper declares.
user_block = html.split('applyUserProperties', 1)[1].split('applyGeneralProperties', 1)[0]
read = set(re.findall(r'p\.(\w+)', user_block))
check('every property the page reads is declared', read <= declared,
      f'page {sorted(read)} vs project.json {sorted(declared)}')

# The terminal has to land on the glass. Both numbers are derived from one
# rectangle in paths.py, and this is the only place that notices if the canvas
# drifts off it. The origin floors and the far edge ceils, because the canvas
# has to cover every logical cell the glass touches -- 160..666 source is 166
# rows once it has been through the 0.85 inset, not the 165 the midpoint gives.
import math  # noqa: E402

sx0, sy0, sx1, sy1 = SCREEN
dx = (SRC_W - int(round(SRC_W * FRAME_SCALE))) // 2


def cell(v):
    return v / PX


want = (math.floor(cell(dx + sx0 * FRAME_SCALE)),
        math.floor(cell(FRAME_TOP + sy0 * FRAME_SCALE)),
        math.ceil(cell(dx + sx1 * FRAME_SCALE)) - math.floor(cell(dx + sx0 * FRAME_SCALE)),
        math.ceil(cell(FRAME_TOP + sy1 * FRAME_SCALE)) - math.floor(cell(FRAME_TOP + sy0 * FRAME_SCALE)))
got = re.search(r'#term\s*\{[^}]*left:\s*(\d+)px;\s*top:\s*(\d+)px;\s*'
                r'width:\s*(\d+)px;\s*height:\s*(\d+)px', html)
got = tuple(int(g) for g in got.groups()) if got else None
check('the terminal canvas sits on the glass', got == want, f'page {got}, glass {want}')

# ------------------------------------------------------------- the build
if (Path(__file__).resolve().parents[1] / 'build' / 'stage_full').exists():
    for variant in VARIANTS:
        for name in CUTOUTS + GRADIENTS:
            built = Path(__file__).resolve().parents[1] / 'build' / f'stage_{variant}' / f'{name}.png'
            same = built.exists() and built.read_bytes() == (LAYERS / variant / f'{name}.png').read_bytes()
            check(f'{variant}/{name} shipped is what the build produced', same,
                  'differs -- rerun tools/emit_layers.py' if not same else '')
else:
    print('[skip] no build/ directory; shipped-vs-built comparison not run')

print(f"\n{checks - len(failures)}/{checks} checks passed")
raise SystemExit(1 if failures else 0)
