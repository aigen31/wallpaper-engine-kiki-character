"""Project the witch's silhouette onto the floor as her cast shadow.

The lamp is high and behind her, and the floor is close, so the shadow is short
and thrown sideways rather than stretched away: her silhouette is squashed to a
fifth of its height, shifted off the side the screen is not on, then blurred.

`FLATTEN` is the number that was wrong for a long time. On an 895 px silhouette
the first attempt used 0.42, which lands the shadow in the middle of the frame
instead of on the floor at all; 0.20 puts it where the reference has it.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import CROP, CUTOUT, PARTS, PX, ensure_dirs  # noqa: E402

ensure_dirs()

alpha = np.asarray(Image.open(CUTOUT).convert('RGBA'))[..., 3][CROP[1]:CROP[3], CROP[0]:CROP[2]]
H, W = alpha.shape
ys, _ = np.nonzero(alpha > 12)
y0, y1 = ys.min(), ys.max()

FLATTEN = 0.20      # the lamp sits high behind her, so the shadow is short
SHIFT_X = 34        # and thrown to the far side of her from the screen
BLUR = 10
BOOST = 1.45

src = Image.fromarray((alpha > 12).astype(np.uint8) * 255)
sq_h = max(1, int((y1 - y0) * FLATTEN))
sq = src.crop((0, y0, W, y1 + 1)).resize((W, sq_h), Image.BILINEAR)

out = Image.new("L", (W, H), 0)
out.paste(sq, (0, y1 - sq_h + 1))

arr = np.asarray(out).astype(np.float32) / 255.0
arr = np.roll(arr, SHIFT_X, axis=1)
arr = np.asarray(Image.fromarray((arr * 255).astype(np.uint8))
                 .filter(ImageFilter.GaussianBlur(BLUR))).astype(np.float32) / 255.0
arr = np.clip(arr * BOOST, 0, 1)

rgba = np.zeros((H, W, 4), np.uint8)
rgba[..., 3] = (arr * 255).astype(np.uint8)
Image.fromarray(rgba).save(PARTS / 'shadow.png')

rows = np.nonzero(arr.any(1))[0]
print(f"shadow y {rows.min()}..{rows.max()} "
      f"(logical {rows.min() / PX:.0f}..{rows.max() / PX:.0f} of {360})")
