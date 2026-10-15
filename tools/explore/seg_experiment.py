import sys, numpy as np
sys.path.insert(0, 'work/we')
from seg_tools import largest_cc, fill_holes, dilate, erode
from PIL import Image

base = Image.open('work/we/base.png').convert('RGB')
A = np.asarray(base).astype(np.float64)
H, W, _ = A.shape
SX0, SY0, SX1, SY1 = 178, 160, 908, 666
R, G, B = A[..., 0], A[..., 1], A[..., 2]
green = G - (R + B) / 2
text = (green > 15) & (G > 45)
np.save('work/we/text_mask.npy', text)

ys, xs = np.mgrid[0:H, 0:W]
inside = (xs >= SX0) & (xs < SX1) & (ys >= SY0) & (ys < SY1)

def design(x, y, deg=3):
    feats = []
    for i in range(deg + 1):
        for j in range(deg + 1 - i):
            feats.append((x ** i) * (y ** j))
    return np.stack(feats, axis=-1)

xs_n = (xs - SX0) / (SX1 - SX0)
ys_n = (ys - SY0) / (SY1 - SY0)
Phi = design(xs_n, ys_n, 3)
fit_mask = inside & ~dilate(text, 2)
print("screen px:", inside.sum(), "text px:", text.sum(), "fit px:", fit_mask.sum())

w = fit_mask.copy()
for it in range(4):
    X = Phi[w]
    XtX = X.T @ X + 1e-6 * np.eye(X.shape[1])
    coef = np.linalg.solve(XtX, X.T @ A[w])
    pred = Phi @ coef
    resid = np.abs(A - pred).max(2)
    lim = [60, 30, 18, 12][it]
    w = fit_mask & (resid < lim)
plate = np.clip(Phi @ coef, 0, 255)
np.save('work/we/plate_screen.npy', plate.astype(np.uint8))

resid = np.abs(A - plate).max(2)
fg = inside & (resid > 12) & ~dilate(text, 1)
print("fg raw px:", fg.sum())
fg = erode(dilate(fg, 2), 2)
fg = largest_cc(fg)
fg = fill_holes(fg)
fg = erode(dilate(fg, 2), 2)
print("fg final px:", fg.sum(), "bbox:",
      np.nonzero(fg.any(1))[0].min(), np.nonzero(fg.any(1))[0].max(),
      np.nonzero(fg.any(0))[0].min(), np.nonzero(fg.any(0))[0].max())
np.save('work/we/fg_screen.npy', fg)

vis = np.asarray(base).copy()
vis[fg] = [255, 0, 255]
Image.fromarray(vis).save('work/we/crops/seg_screen_fg.png')
vis2 = np.asarray(base).copy()
vis2[inside] = np.clip(0.45 * vis2[inside] + 0.55 * plate[inside], 0, 255).astype(np.uint8)
Image.fromarray(vis2).save('work/we/crops/seg_plate.png')
