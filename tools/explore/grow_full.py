import sys, numpy as np
sys.path.insert(0, 'work/we')
from PIL import Image
from seg_tools import largest_cc, fill_holes, dilate, erode

base = Image.open('work/we/base.png').convert('RGB')
A = np.asarray(base).astype(np.int16)
H, W, _ = A.shape

def grow(seeds, tol):
    seen = np.zeros((H, W), bool); stack = []
    for (sx, sy) in seeds:
        if not seen[sy, sx]: seen[sy, sx] = True; stack.append((sy, sx))
    while stack:
        y, x = stack.pop()
        c = A[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and np.abs(A[ny, nx] - c).max() <= tol:
                seen[ny, nx] = True; stack.append((ny, nx))
    return seen

seeds = [(190, 400), (880, 400), (200, 600), (860, 300),   # screen
         (20, 20), (1600, 20), (20, 900), (1600, 900),      # corners: wall/floor
         (1200, 880), (1000, 700), (300, 900), (60, 700)]   # floor
for tol in (6, 9, 12):
    g = grow(seeds, tol)
    print(f"tol={tol:2d} grown {g.sum():7d} / {H*W}")
    vis = np.asarray(base).copy()
    vis[g] = [255, 0, 255]
    Image.fromarray(vis).save(f'work/we/crops/growfull_{tol}.png')
