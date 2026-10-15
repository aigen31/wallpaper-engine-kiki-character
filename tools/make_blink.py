"""Build the blink overlay from the open-eyed girl layer, at source resolution.

Two things make this fiddly, and both come from the eye being tiny.

The eye has to be found without being told where it is.  At source resolution
the lash, the iris and the sclera are all neutral or green (R-G of 0 or less)
while the fringe, the skin and the hair are all warm brown (R-G of +25 and up),
so a flood fill from the iris stops at the eye's real outline -- which is why
the lid that replaces it has no rectangle in it.  Luminance alone cannot do
this: the fringe goes as dark as the lash in shadow.

The shut lash has to be a lash, not a bar.  It is drawn as a shallow, slightly
uneven arc sitting low in the eye, with the rows above and below mixed towards
the lid and the cheek, so its edges fade the way the open lash's do.  The
original lash is inside the region that gets repainted, so only one survives.
"""
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import FRAMED, ensure_dirs  # noqa: E402

ensure_dirs()

SRC = FRAMED / 'girl.png'
OUT = FRAMED / 'girl_closed.png'

EYES = [
    dict(x0=556, x1=588, y0=352, y1=397),      # left eye
    dict(x0=606, x1=646, y0=348, y1=394),      # right eye
]

girl = np.asarray(Image.open(SRC).convert('RGBA')).astype(np.int16)
H, W, _ = girl.shape
R, G, B, A = girl[..., 0], girl[..., 1], girl[..., 2], girl[..., 3]
lum = (R + G + B) / 3.0
eye_like = (R - G < 22) & (A > 0)

out = girl.copy()
for e in EYES:
    x0, x1, y0, y1 = e['x0'], e['x1'], e['y0'], e['y1']
    win = np.zeros((H, W), bool)
    win[y0:y1 + 1, x0:x1 + 1] = True

    seed_mask = (G - np.maximum(R, B) > 18) & (G > 60) & win
    if seed_mask.sum() < 5:
        print(f"  x {x0}..{x1}: no iris seed, skipped")
        continue
    ys, xs = np.nonzero(seed_mask)
    sy, sx = int(np.median(ys)), int(np.median(xs))

    region = eye_like & win
    seen = np.zeros((H, W), bool)
    q = deque([(sy, sx)]); seen[sy, sx] = True
    comp = np.zeros((H, W), bool)
    while q:
        y, x = q.popleft()
        comp[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and region[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))

    span = max(1, x1 - x0)
    for x in range(x0, x1 + 1):
        col = np.nonzero(comp[y0:y1 + 1, x])[0]
        if len(col) < 6:
            continue
        top, bot = y0 + int(col.min()), y0 + int(col.max())

        t = (x - x0) / span
        arc = -1.8 * np.sin(np.pi * t)          # sags in the middle
        ripple = 0.8 * np.sin(7.0 * t + 0.9)
        c = bot - 2 + int(round(arc + ripple))

        seg = girl[top:bot + 1, x, :3]
        core = seg[int(np.argmin(seg.mean(1)))].astype(np.float32)
        cheek = girl[min(H - 1, bot + 3), x, :3].astype(np.float32)
        above = girl[max(0, top - 2), x, :3].astype(np.float32)
        lid_top = above * 0.45 + cheek * 0.55

        for y in range(top, bot + 1):
            if y == c - 1:
                col_c = core * 0.5 + lid_top * 0.5
            elif y == c:
                col_c = core
            elif y == c + 1:
                col_c = core * 0.4 + cheek * 0.6
            elif y < c:
                f = (y - top) / max(1, c - top)
                col_c = lid_top * (1 - f) + cheek * f
            else:
                col_c = cheek
            out[y, x, :3] = np.clip(col_c, 0, 255).astype(np.int16)
            out[y, x, 3] = 255

    ys, xs = np.nonzero(comp)
    print(f"  eye x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}  ({int(comp.sum())} px)")

Image.fromarray(out.astype(np.uint8)).save(OUT)
diff = (np.abs(out[..., :3].astype(int) - girl[..., :3].astype(int)).max(2) > 0) | (out[..., 3] != girl[..., 3])
ys, xs = np.nonzero(diff)
print(f"changed px {int(diff.sum())}  bbox x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}")
