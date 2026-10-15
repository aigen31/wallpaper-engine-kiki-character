import sys, numpy as np
sys.path.insert(0, 'work/we')
from PIL import Image

base = Image.open('work/we/base.png').convert('RGB')
A = np.asarray(base).astype(np.int16)
H, W, _ = A.shape
SX0, SY0, SX1, SY1 = 178, 160, 908, 666

def grow(seeds, tol=7, box=None):
    """Region-grow where the step to a 4-neighbour is small in every channel."""
    x0, y0, x1, y1 = box or (0, 0, W, H)
    seen = np.zeros((H, W), bool)
    stack = []
    for (sx, sy) in seeds:
        if not seen[sy, sx]:
            seen[sy, sx] = True; stack.append((sy, sx))
    while stack:
        y, x = stack.pop()
        c = A[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if ny < y0 or ny >= y1 or nx < x0 or nx >= x1 or seen[ny, nx]:
                continue
            if np.abs(A[ny, nx] - c).max() <= tol:
                seen[ny, nx] = True
                stack.append((ny, nx))
    return seen

for tol in (5, 8, 12):
    g = grow([(190, 400), (880, 400), (200, 600), (860, 300)], tol=tol,
             box=(SX0, SY0, SX1, SY1))
    print(f"tol={tol:2d} grown {g.sum():7d} of {((SX1-SX0)*(SY1-SY0))} inside screen")
    vis = np.asarray(base).copy()
    vis[g] = [255, 0, 255]
    Image.fromarray(vis).save(f'work/we/crops/grow_{tol}.png')
