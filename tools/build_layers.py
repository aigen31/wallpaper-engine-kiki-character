"""Split the reference frame into its parts at source resolution.

Five of the seven layers are born here. Each is a decision about what a pixel
belongs to:

* **bg** -- everything that is neither the glass nor the witch. The witch's hole
  is filled by diffusion rather than left transparent, because the wall and the
  floor have to continue behind her once `reframe.py` grows the border, and the
  glass is overwritten with the inpainted plate.
* **screen** -- the plate, alpha = the CRT rectangle. Drawn over `bg`, so the
  room never shows through the glass.
* **girl** -- the reference's own pixels, alpha from the cut-out model.
* **light** -- the floor spill, taken from the *greenness* of the reference
  (`G - (R+B)/2`), which is what separates the screen's green wash from the warm
  paper, the wood and the witch. Inside the glass and under the witch it is
  zeroed: the glass is the source, and her own pixels are lit by the separate
  glow layer.
* **halo** -- the bloom hugging the monitor shell, two blur radii of the CRT
  rectangle added together.

The shadow is **not** built here. `build_shadow.py` owns it: the projection
needs a different flattening than anything else in this file and having two
scripts write the same PNG meant whichever ran last won.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (CROP, CUTOUT, FRAMED, PARTS, SCREEN, SOURCE,  # noqa: E402
                   ensure_dirs)

ensure_dirs()

rgb = np.asarray(Image.open(SOURCE).convert('RGB')).astype(np.float32)[CROP[1]:CROP[3], CROP[0]:CROP[2]]
alpha = np.asarray(Image.open(CUTOUT).convert('RGBA'))[..., 3][CROP[1]:CROP[3], CROP[0]:CROP[2]]
plate = np.asarray(Image.open(PARTS / 'screen_plate_full.png').convert('RGB')).astype(np.float32)[CROP[1]:CROP[3], CROP[0]:CROP[2]]
H, W, _ = rgb.shape
print(f"stage {W}x{H}")

SX0, SY0, SX1, SY1 = SCREEN
R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
ys, xs = np.mgrid[0:H, 0:W]
in_screen = (xs >= SX0) & (xs < SX1) & (ys >= SY0) & (ys < SY1)


def dil(mask, r):
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                      .filter(ImageFilter.MaxFilter(2 * r + 1))) > 127


girl = alpha > 12
girl_d = dil(girl, 2)

# ---------------------------------------------------------------- background
# fill the witch's hole with a dark smooth extension of her surroundings
hole = girl_d.copy()
img = rgb.copy()
for r, n in ((16, 90), (5, 60), (2, 40)):
    blur = ImageFilter.GaussianBlur(r)
    for _ in range(n):
        b = np.asarray(Image.fromarray(img.astype(np.uint8)).filter(blur)).astype(np.float32)
        img = np.where(hole[..., None], b, rgb)
bg = np.clip(img, 0, 255)
# the glass is drawn by its own layer, so it must not also be in the room
bg[in_screen] = plate[in_screen]

# ---------------------------------------------------------------- screen
scr_rgba = np.zeros((H, W, 4), np.uint8)
scr_rgba[..., :3] = np.clip(plate, 0, 255).astype(np.uint8)
scr_rgba[in_screen, 3] = 255

# ---------------------------------------------------------------- girl
girl_rgba = np.zeros((H, W, 4), np.uint8)
girl_rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
girl_rgba[..., 3] = np.clip(alpha, 0, 255)

# ---------------------------------------------------------------- light
green = np.clip(G - (R + B) / 2.0, 0, None)
L = np.clip((green - 3.0) / 10.0, 0, 1)      # the spill only: below 3 is noise
L[in_screen] = 0
L[girl_d] = 0
L = np.asarray(Image.fromarray((L * 255).astype(np.uint8))
               .filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255.0
light = np.zeros((H, W, 4), np.uint8)
# The colour is fixed rather than sampled: the screen's phosphor is the same
# green everywhere, and sampling it per-run let the hue drift with the crop.
light[..., 0], light[..., 1], light[..., 2] = 90, 200, 110
light[..., 3] = np.clip(L * 255, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- halo
# soft green bloom hugging the monitor, from the CRT rectangle outward
m = np.zeros((H, W), np.uint8)
m[SY0 - 6:SY1 + 10, SX0 - 8:SX1 + 8] = 255
h = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(26))).astype(np.float32) / 255.0
h2 = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(60))).astype(np.float32) / 255.0
halo_mask = np.clip(h * 0.55 + h2 * 0.45, 0, 1)
halo_mask[in_screen] = 0
halo_mask[girl_d] = 0
halo = np.zeros((H, W, 4), np.uint8)
halo[..., 0], halo[..., 1], halo[..., 2] = 70, 210, 120
halo[..., 3] = np.clip(halo_mask * 255, 0, 255).astype(np.uint8)

for name, arr in (('bg', bg), ('screen', scr_rgba), ('girl', girl_rgba),
                  ('light', light), ('halo', halo)):
    Image.fromarray(arr.astype(np.uint8)).save(PARTS / f'{name}.png')
    print("saved", name)

# previews of the additive layers over black, to eyeball the shapes
for name in ('light', 'halo'):
    a = np.asarray(Image.open(PARTS / f'{name}.png').convert('RGBA')).astype(np.float32)
    al = a[..., 3:4] / 255
    Image.fromarray(np.clip(a[..., :3] * al, 0, 255).astype(np.uint8)).save(PARTS / f'{name}_preview.png')
