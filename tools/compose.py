"""Downscale the framed layers to the 640x360 logical stage.

Three things happen here and nowhere else:

* **The box downscale** to the logical grid, with a different alpha rule for
  cut-outs and for light.
* **The palette**, once, from the flattened scene -- and only for the variants
  that want it. Two of the four runs reuse the palette another run derived, so
  the open and shut frames cannot drift apart.
* **The mouth**, put back by hand after the quantiser has thrown it away.

Environment variables, because this is the one script the build runs four
times: `WE_PARTS`, `WE_STAGE`, `WE_PALETTE` (128, or 0 for the reference's own
colours), `WE_GIRL` (which girl layer to composite, so the shut-eyed frame goes
through an identical downscale) and `WE_PALETTE_FROM` (reuse a palette file).
"""
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (BUILD, FRAME_SCALE, FRAME_TOP, PARTS as PARTS_DEFAULT,  # noqa: E402
                   SCREEN, SOURCE, STAGE_H, STAGE_W, SRC_W, ensure_dirs)

PARTS = Path(os.environ.get('WE_PARTS', PARTS_DEFAULT))
STAGE = Path(os.environ.get('WE_STAGE', BUILD / 'stage'))
ensure_dirs()
STAGE.mkdir(parents=True, exist_ok=True)
LW, LH = STAGE_W, STAGE_H
PALETTE = int(os.environ.get('WE_PALETTE', '128'))   # 0 = reference colours
W_SRC = SRC_W
MOUTH_RGB = np.array((208, 138, 116), np.float32)
SX0, SY0, SX1, SY1 = SCREEN          # the glass, cropped coords

def load(name):
    return np.asarray(Image.open(f'{PARTS}/{name}.png').convert('RGBA')).astype(np.float32)

def downscale(rgba, binary=True, crisp_edges=False):
    """Premultiplied box downscale to the logical stage.

    `binary` is right for cut-out art -- a half-covered sprite edge turns into
    a smeary fringe once `image-rendering: pixelated` blows it up.  It is wrong
    for the light layers: those are gradients by nature, and thresholding them
    throws away almost the whole glow.

    `crisp_edges` matters for the cut-out.  The model's alpha is anti-aliased,
    and its RGB under a half-covered edge pixel is already part girl, part
    room -- so the ordinary alpha-weighted average hands the logical edge cell
    a colour mixed with the wallpaper behind her.  Snapping to a palette hides
    that; keeping the reference's own colours does not.  With `crisp_edges` the
    cell's colour is taken only from its opaque source pixels, while its
    coverage still comes from the full alpha average.
    """
    a = rgba[..., 3:4] / 255.0
    pm = rgba[..., :3] * a
    img = Image.fromarray(np.concatenate([pm, rgba[..., 3:4]], -1).astype(np.uint8))
    img = img.resize((LW, LH), Image.BOX)
    arr = np.asarray(img).astype(np.float32)
    al = arr[..., 3:4]
    rgb = np.where(al > 0, arr[..., :3] / np.maximum(al / 255.0, 1e-3), 0)

    if crisp_edges:
        solid = (rgba[..., 3:4] > 200).astype(np.float32)
        # both tracks are premultiplied and both stay in 0..255, so the
        # resized colour / resized coverage is the mean of the opaque pixels
        pack = np.concatenate([rgba[..., :3] * a * solid, rgba[..., 3:4] * solid], -1)
        w = np.asarray(Image.fromarray(pack.astype(np.uint8)).resize((LW, LH), Image.BOX)).astype(np.float32)
        den = w[..., 3:4]                 # coverage, 0..255
        oc = w[..., :3]                   # premultiplied colour, 0..255
        good = den > 0.5 * 255.0          # at least half the cell is opaque
        rgb = np.where(good, oc / np.maximum(den, 1e-3) * 255.0, rgb)

    out = np.zeros((LH, LW, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = np.where(al[..., 0] >= 128, 255.0, 0.0) if binary else np.clip(al[..., 0], 0, 255)
    return out

GIRL_SRC = os.environ.get('WE_GIRL', 'girl')   # 'girl_closed' builds the blink frame
names = ['bg', 'screen', 'girl', 'light', 'halo', 'shadow', 'glow']
SOFT = {'light', 'halo', 'shadow', 'glow'}   # gradients, not cut-outs
layers = {n: downscale(load(GIRL_SRC if n == 'girl' else n), binary=(n not in SOFT),
                       crisp_edges=(n == 'girl')) for n in names}
np.save(f'{STAGE}/layers.npy', layers, allow_pickle=True)

# ---------------------------------------------------------------- palette
def flatten(order):
    out = np.zeros((LH, LW, 3), np.float32)
    for n in order:
        l = layers[n]
        a = (l[..., 3:4] / 255.0)
        blend = l[..., :3] if n in ('light', 'halo', 'shadow') else l[..., :3]
        out = out * (1 - a) + blend * a
    return out

base = flatten(['bg', 'screen', 'girl'])
opaque = (layers['girl'][..., 3] > 0) | (layers['screen'][..., 3] > 0) | np.ones((LH, LW), bool)
FROM = os.environ.get('WE_PALETTE_FROM')
if FROM and os.path.exists(FROM):
    pal = np.load(FROM)
    print("palette loaded:", len(pal), "entries from", FROM)
elif PALETTE > 0:
    px = base.reshape(-1, 3).astype(np.uint8)
    im = Image.fromarray(px.reshape(LH, LW, 3)).quantize(colors=PALETTE, method=Image.MEDIANCUT)
    pal = np.array(im.getpalette()[: PALETTE * 3], np.uint8).reshape(-1, 3).astype(np.float32)
    np.save(f'{STAGE}/palette.npy', pal)
    print("palette entries:", len(pal))
else:
    pal = None
    print("palette: reference colours, no quantisation")

def snap(rgb):
    flat = rgb.reshape(-1, 3)
    d = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(-1)
    return pal[d.argmin(1)].reshape(rgb.shape)

if pal is not None:
    for n in ('bg', 'screen', 'girl', 'shadow'):   # light layers stay gradients
        layers[n][..., :3] = snap(layers[n][..., :3])

# ---------------------------------------------------------------- mouth
# The mouth is a 6x4 px pink dot in the reference.  Box-averaging one 2.6 px
# logical cell dilutes it back into cheek skin, and the quantiser then has no
# entry for it at all, so it is put back on purpose -- two logical pixels, the
# way the reference draws it.
def restore_mouth(rgba):
    S, DY = FRAME_SCALE, FRAME_TOP
    DX = (W_SRC - int(round(W_SRC * S))) // 2      # where reframe.py pasted it
    SC = W_SRC / LW
    sx0, sy0, sx1, sy1 = 553, 363, 560, 369        # after the 24-row crop
    X0 = (DX + sx0 * S) / SC; X1 = (DX + sx1 * S) / SC
    Y0 = (DY + sy0 * S) / SC; Y1 = (DY + sy1 * S) / SC
    x0, x1 = int(round(X0)), int(round(X1)) - 1
    y0, y1 = int(round(Y0)), int(round(Y1)) - 1
    rgba[y0:y1 + 1, x0:x1 + 1, :3] = MOUTH_RGB
    rgba[y0:y1 + 1, x0:x1 + 1, 3] = 255.0
    print(f"mouth restored at stage x {x0}..{x1} y {y0}..{y1} colour {MOUTH_RGB}")

restore_mouth(layers['girl'])

np.save(f'{STAGE}/layers.npy', layers, allow_pickle=True)
for n in names:
    Image.fromarray(layers[n].astype(np.uint8)).save(f'{STAGE}/{n}.png')

# ---------------------------------------------------------------- previews
def over(a, b, mode='normal'):
    """a over b (both premultiplied-by-alpha floats)."""
    aa = a[..., 3:4] / 255.0
    bb = b[..., 3:4] / 255.0
    if mode == 'screen':
        src = 255 - (255 - a[..., :3]) * (255 - b[..., :3]) / 255.0
        res = src
        oa = aa + bb * (1 - aa)
    else:
        res = a[..., :3] * aa + b[..., :3] * bb * (1 - aa)
        oa = aa + bb * (1 - aa)
    out = b.copy()
    out[..., :3] = res
    out[..., 3] = (oa * 255)[..., 0]
    return out

comp = np.zeros((LH, LW, 4), np.float32)
comp[..., 3] = 255
comp = over(layers['bg'], comp)
comp = over(layers['screen'], comp)
comp = over(layers['halo'], comp, 'screen')
comp = over(layers['light'], comp, 'screen')
comp = over(layers['shadow'], comp)
comp = over(layers['girl'], comp)
comp = over(layers['glow'], comp, 'screen')
Image.fromarray(comp.astype(np.uint8)).save(f'{STAGE}/composite.png')
Image.fromarray(comp.astype(np.uint8)).resize((LW * 2, LH * 2), Image.NEAREST).save(f'{STAGE}/composite@2x.png')

# the reference at the same scale, for eyeballing a composite against it
orig = np.asarray(Image.open(SOURCE).convert('RGB'))[24:960]
Image.fromarray(orig).resize((LW, LH), Image.BOX).save(f'{STAGE}/reference_small.png')
print("stage written")
