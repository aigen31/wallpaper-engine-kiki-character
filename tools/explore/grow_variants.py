import sys, numpy as np
sys.path.insert(0, 'work/we')
from PIL import Image
from seg_tools import largest_cc, fill_holes, dilate, erode

base = Image.open('work/we/base.png').convert('RGB')
A = np.asarray(base).astype(np.int16)
H, W, _ = A.shape
SX0, SY0, SX1, SY1 = 178, 160, 908, 666

def grow(seeds, tol):
    seen = np.zeros((H, W), bool); stack = []
    for (sx, sy) in seeds:
        if not seen[sy, sx]: seen[sy, sx] = True; stack.append((sy, sx))
    while stack:
        y, x = stack.pop(); c = A[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if SY0 <= ny < SY1 and SX0 <= nx < SX1 and not seen[ny, nx] and np.abs(A[ny, nx] - c).max() <= tol:
                seen[ny, nx] = True; stack.append((ny, nx))
    return seen

seeds = [(190, 400), (880, 400), (200, 600), (860, 300), (250, 200), (890, 620), (200, 640), (700, 640)]
text = np.load('work/we/text_mask.npy')
ys, xs = np.mgrid[0:H, 0:W]
inside = (xs >= SX0) & (xs < SX1) & (ys >= SY0) & (ys < SY1)
for tol in (10, 14, 18, 24):
    g = grow(seeds, tol)
    non = inside & ~g & ~dilate(text, 2)
    print(f"tol={tol:2d} grown={g.sum():6d} non-grown-cand={non.sum():6d}")
    vis = np.asarray(base).copy()
    vis[non] = [255, 0, 255]
    Image.fromarray(vis).crop((150, 140, 960, 700)).save(f'work/we/crops/gv_{tol}.png')
