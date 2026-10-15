"""Clean the baked terminal text out of the CRT screen surface.

The reference has a build log baked into the glass. It cannot simply be painted
out: the glass is a gradient, and a flat fill reads as a hole. So the text and
the witch are marked unknown, and the pixels around them are grown inwards by
repeated Gaussian passes -- a Dirichlet heat equation solved by relaxation --
until the unknown region is filled from its own boundary.

**The relaxation has to run at three scales, coarse to fine.** The hole is
271 915 px: the witch alone occupies 185 633 of them inside the glass, which is
500-odd pixels across. One radius cannot cross that. A single `radius 4, 260
passes` loop -- which is what this script once contained -- diffuses about 64 px
and leaves the witch smeared across the glass; the plate has to be recognisably
smooth glass before `build_layers.py` is allowed to put it behind her. Radius 16
carries the boundary across the hole, 6 and 2 put the fine gradient back. The
rounds are the same shape `reframe.py` uses to grow the border, for the same
reason and with the same numbers.

The witch is masked along with the text because she stands in front of the
glass: her pixels are not glass either, and letting them seed the diffusion
would bleed her silhouette into the plate.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import CUTOUT, PARTS, SCREEN_RAW, SOURCE, ensure_dirs  # noqa: E402

ensure_dirs()

rgb = np.asarray(Image.open(SOURCE).convert('RGB')).astype(np.float32)
alpha = np.asarray(Image.open(CUTOUT).convert('RGBA'))[..., 3]
H, W, _ = rgb.shape
SX0, SY0, SX1, SY1 = SCREEN_RAW

R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
greenness = G - (R + B) / 2
box = np.zeros((H, W), bool)
box[SY0:SY1, SX0:SX1] = True
text = (greenness > 12) & (G > 40) & box
tm = Image.fromarray((text * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
text_d = np.asarray(tm) > 127
girl = alpha > 12
gm = Image.fromarray((girl * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
girl_d = np.asarray(gm) > 127
hole = box & (text_d | girl_d)
print(f"text {text.sum()} px, girl in the glass {(girl & box).sum()}, hole {hole.sum()}")
Image.fromarray(np.where(hole, 255, rgb.mean(2)).astype(np.uint8)).save(PARTS / 'text_mask.png')

known = ~hole
img = rgb.copy()
for radius, passes in ((16, 120), (6, 80), (2, 60)):
    blur = ImageFilter.GaussianBlur(radius)
    for _ in range(passes):
        b = np.asarray(Image.fromarray(img.astype(np.uint8)).filter(blur)).astype(np.float32)
        img = np.where(known[..., None], rgb, b)
plate = np.clip(img, 0, 255).astype(np.uint8)
Image.fromarray(plate).save(PARTS / 'screen_plate_full.png')
Image.fromarray(plate[SY0:SY1, SX0:SX1]).save(PARTS / 'screen_plate_crop.png')
np.save(PARTS / 'hole.npy', hole)
print(f"plate written, {hole.sum()} px filled of {(SY1 - SY0) * (SX1 - SX0)} in the glass")
