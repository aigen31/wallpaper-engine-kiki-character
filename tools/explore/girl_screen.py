import sys, numpy as np
sys.path.insert(0, 'work/we')
from PIL import Image
from seg_tools import largest_cc, fill_holes, dilate, erode

base = Image.open('work/we/base.png').convert('RGB')
A = np.asarray(base).astype(np.int16)
H, W, _ = A.shape
SX0, SY0, SX1, SY1 = 178, 160, 908, 666

def grow(seeds, tol, box):
    x0, y0, x1, y1 = box
    seen = np.zeros((H, W), bool); stack = []
    for (sx, sy) in seeds:
        if not seen[sy, sx]: seen[sy, sx] = True; stack.append((sy, sx))
    while stack:
        y, x = stack.pop(); c = A[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if y0 <= ny < y1 and x0 <= nx < x1 and not seen[ny, nx] and np.abs(A[ny, nx] - c).max() <= tol:
                seen[ny, nx] = True; stack.append((ny, nx))
    return seen

text = np.load('work/we/text_mask.npy')
grown = grow([(190, 400), (880, 400), (200, 600), (860, 300), (250, 200), (890, 620)],
             tol=8, box=(SX0, SY0, SX1, SY1))

ys, xs = np.mgrid[0:H, 0:W]
inside = (xs >= SX0) & (xs < SX1) & (ys >= SY0) & (ys < SY1)
cand = inside & ~grown & ~dilate(text, 2)
print("cand px:", cand.sum())
girl = largest_cc(cand)
girl = fill_holes(girl)
girl = erode(dilate(girl, 3), 3)
print("girl px:", girl.sum())
ys2, xs2 = np.nonzero(girl)
print("bbox x", xs2.min(), xs2.max(), "y", ys2.min(), ys2.max())
np.save('work/we/girl_screen.npy', girl)

vis = np.asarray(base).copy()
overlay = girl
vis[overlay] = [255, 0, 255]
Image.fromarray(vis).save('work/we/crops/girl_screen.png')
# show mask alone on checker
comp = np.zeros((H, W, 3), np.uint8)
comp[..., 0] = np.where(girl, 255, 20); comp[..., 1] = np.where(girl, 0, 20); comp[..., 2] = np.where(girl, 255, 20)
Image.fromarray(comp).save('work/we/crops/girl_screen_mask.png')
