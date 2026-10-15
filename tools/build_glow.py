"""Build the screen-light rim on the witch herself.

The floor spill (`light`), the bloom (`halo`) and the cast shadow are all
*away* from her; nothing in the layer stack said anything about the light the
CRT throws back onto the hat and the hair hanging in front of it.  That is what
this layer is.

It is a light-transport field, not a hand-painted mask:

* **Exposure.**  Every girl pixel is weighted by its distance to the CRT
  surface (the 178..908 x 160..666 rectangle in these crops).  Inside the
  rectangle the screen fills her whole field of view; outside it the weight
  falls off as a Gaussian, so the hat crown fades out with height and the boots
  down on the floor barely register.
* **Rim vs body.**  The screen sits *behind* her, roughly parallel to the image
  plane, so a surface turned towards the camera receives almost nothing from it
  -- only the surfaces that curve away towards the screen do.  That is exactly
  a rim light, so the field is built from the distance into her own silhouette:
  a tight ring at the outline plus a much weaker wash over the first dozen
  pixels inside it.
* **Which way the edge faces.**  Weighting every pixel of the outline equally
  gives her a green sticker outline, and the crown of the hat lights up even
  though the screen is nowhere near it.  The screen is below and behind her, so
  the lit surfaces are the ones turned *downwards*: the underside of the brim,
  the low edge of the strand, the under-curve of the cloak.  The outward
  normal is read off the blurred silhouette itself, and its downward component
  weights the field.  A side edge keeps a third of the strength (light does
  wrap around a screen that wide); the top of the hat gets nothing.
* **Colour.**  Taken from the layers that already exist -- `halo` is (70, 210,
  120) and `light` is (90, 200, 110) -- so this glows with the same phosphor as
  the rest of the lamp and cannot drift to a different green.

Alpha is a gradient, like `halo`/`light`/`shadow`: this is light, not a
silhouette, and thresholding it would delete the falloff that makes it read as
light at all.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import PARTS, SCREEN, ensure_dirs  # noqa: E402

ensure_dirs()

GIRL = PARTS / 'girl.png'
OUT = PARTS / 'glow.png'

# The CRT surface, from paths.py: the same rectangle the inpaint fills and the
# browser puts the terminal canvas on.
SX0, SY0, SX1, SY1 = SCREEN

EXPOSURE_SIDE = 150.0   # source px; how far the screen reaches left and right
EXPOSURE_UP = 105.0     # above its top edge, where the hat still catches it
EXPOSURE_DOWN = 18.0    # below its bottom edge -- almost nothing
RIM_W = 3.5           # source px; how tight the outline ring is
BODY_W = 15.0         # source px; the wash just inside the outline
RIM, BODY = 0.85, 0.30
SIDE = 0.30           # strength kept on an edge that faces sideways, not down
LC = (90, 205, 115)   # the lamp's own colour, off the halo/light layers
GAIN = 0.85           # headroom: the browser's nominal opacity sits below 1

girl = np.asarray(Image.open(GIRL).convert('RGBA')).astype(np.float32)
H, W, _ = girl.shape
mask = girl[..., 3] > 128

# ------------------------------------------------------- depth into the body
# Chebyshev distance to the nearest transparent pixel, by repeated erosion.
# Only the first ~16 px matter, and the outline of a 1664x936 cut-out is the
# only place this is read, so a filter loop beats a distance transform here.
inset = np.zeros((H, W), np.int16)
cur = mask.copy()
for k in range(1, 17):
    e = np.asarray(Image.fromarray((cur * 255).astype(np.uint8))
                   .filter(ImageFilter.MinFilter(3))) > 0
    if not e.any():
        break
    inset[e] = k
    cur = e

# ------------------------------------------------------------------ exposure
# Asymmetric on the vertical axis, and that asymmetry is the whole point.  The
# screen is a lit rectangle: light spills over its top edge, so the hat above
# the monitor catches it, but there is no light *below* the glass at all.  The
# old symmetric falloff lit the hem of her dress and the boots, which sit below
# the monitor entirely -- they are not in the light path, they only looked like
# they were.
yy, xx = np.mgrid[0:H, 0:W]
dx = np.maximum.reduce([SX0 - xx, xx - SX1, np.zeros_like(xx)]).astype(np.float32)
dy_up = np.maximum(SY0 - yy, 0).astype(np.float32)
dy_dn = np.maximum(yy - SY1, 0).astype(np.float32)
exposure = np.exp(-((dx / EXPOSURE_SIDE) ** 2
                    + (dy_up / EXPOSURE_UP) ** 2
                    + (dy_dn / EXPOSURE_DOWN) ** 2))

# ------------------------------------------------- which way each edge faces
# The outward normal of the silhouette, off a blurred copy of the mask: the
# gradient of a blurred shape points inwards, so its negative points out.
soft = np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                  .filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255.0
gy, gx = np.gradient(soft)
mag = np.hypot(gx, gy)
nx = np.divide(-gx, mag, out=np.zeros_like(gx), where=mag > 1e-4)
ny = np.divide(-gy, mag, out=np.zeros_like(gy), where=mag > 1e-4)
facing = SIDE + (1.0 - SIDE) * np.clip(ny, 0.0, 1.0)   # 1 = turned downwards

rim = np.exp(-(inset / RIM_W) ** 2)
body = np.exp(-(inset / BODY_W) ** 2)

field = exposure * facing * (RIM * rim + BODY * body)
field = np.clip(field * GAIN, 0.0, 1.0) * mask

out = np.zeros((H, W, 4), np.float32)
out[..., 0], out[..., 1], out[..., 2] = LC
out[..., 3] = field * 255.0
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)

lit = field > 0.02
ys, xs = np.nonzero(lit)
print(f"glow.png written: {int(lit.sum())} px  bbox x {xs.min()}..{xs.max()} "
      f"y {ys.min()}..{ys.max()}")
print(f"  peak alpha {out[..., 3].max():.0f}  mean facing on the downward "
      f"edges {np.percentile(facing[mask & (inset < 4)], 75):.2f}, on the "
      f"upward ones {np.percentile(facing[mask & (inset < 4)], 25):.2f}")
print(f"  exposure: hat crown {exposure[12:60, 300:900].mean():.3f}  brim "
      f"{exposure[180:250, 333:526].mean():.3f}  strand "
      f"{exposure[240:520, 430:540].mean():.3f}  hem of the dress "
      f"{exposure[700:800, 300:900].mean():.3f}  boots "
      f"{exposure[800:930, 400:800].mean():.3f}")
print(f"  lit px below the screen's bottom edge (source y>{SY1}): "
      f"{int((field[SY1:, :] > 0.02).sum())}")
