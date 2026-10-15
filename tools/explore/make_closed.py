"""Close the eyes on the framed girl layer, at source resolution.

An eye here is a thick black lash arc, the iris under it and the white sclera
below.  A blink is not "hide the iris": the lash itself travels down and the
lid behind it becomes skin.

The eye is found as a connected region rather than column by column: the lash,
the iris and the sclera are all neutral or green (R-G of 0 or less) while the
fringe, the skin and the hair are all warm brown (R-G of +25 and up), so a
flood fill from the iris stays inside the eye and its outline is the eye's own
outline -- which is why the lid that replaces it has no rectangle in it.  The
shut lash is each column's darkest pixel, dropped to the bottom of the region.
"""
import numpy as np
from collections import deque
from PIL import Image

SRC = 'work/we/parts_framed/girl.png'
OUT = 'work/we/parts_framed/girl_closed.png'

girl = np.asarray(Image.open(SRC).convert('RGBA')).astype(np.int16)
H, W, _ = girl.shape
R, G, B, A = girl[..., 0], girl[..., 1], girl[..., 2], girl[..., 3]
lum = (R + G + B) / 3.0
eye_like = (R - G < 22) & (A > 0)

EYES = [
    dict(x0=558, x1=586, y0=355, y1=395, lash=5),
    dict(x0=608, x1=643, y0=350, y1=392, lash=5),
]

out = girl.copy()
report = []

for e in EYES:
    x0, x1, y0, y1, lt = e['x0'], e['x1'], e['y0'], e['y1'], e['lash']
    win = np.zeros((H, W), bool)
    win[y0:y1 + 1, x0:x1 + 1] = True

    # seed on the iris, the safest eye pixel there is
    iris = (G - np.maximum(R, B) > 18) & (G > 60) & win
    if iris.sum() < 5:
        report.append(f"x {x0}..{x1}: no iris seed")
        continue
    ys, xs = np.nonzero(iris)
    sy, sx = int(np.median(ys)), int(np.median(xs))

    region = eye_like & win
    seen = np.zeros((H, W), bool)
    q = deque([(sy, sx)])
    seen[sy, sx] = True
    comp = np.zeros((H, W), bool)
    while q:
        y, x = q.popleft()
        comp[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and region[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))

    for x in range(x0, x1 + 1):
        col = np.nonzero(comp[y0:y1 + 1, x])[0]
        if not len(col):
            continue
        top, bot = y0 + int(col.min()), y0 + int(col.max())
        if bot - top < 4:
            continue
        darkest = top + int(np.argmin(lum[top:bot + 1, x]))
        split = max(top, bot - lt + 1)
        # the lid is shaded, not flat: it runs from the tone just under the
        # fringe to the tone just above the cheek, so it reads as skin
        above = girl[max(0, top - 2), x, :3].astype(np.float32)
        below = girl[min(H - 1, bot + 2), x, :3].astype(np.float32)
        span = max(1, split - top)
        for yy in range(top, split):
            t = (yy - top) / span
            out[yy, x, :3] = np.clip(above * (1 - t) + below * t, 0, 255).astype(np.int16)
            out[yy, x, 3] = 255
        for yy in range(split, bot + 1):
            out[yy, x, :3] = girl[darkest, x, :3]
            out[yy, x, 3] = 255
    ys, xs = np.nonzero(comp)
    report.append(f"x {x0}..{x1}: region {int(comp.sum())} px, x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}")

print("; ".join(report))
Image.fromarray(out.astype(np.uint8)).save(OUT)
diff = (np.abs(out[..., :3].astype(int) - girl[..., :3].astype(int)).max(2) > 0) | (out[..., 3] != girl[..., 3])
ys, xs = np.nonzero(diff)
print(f"changed px {int(diff.sum())}  bbox x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}")
