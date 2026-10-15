"""Shrink the whole scene inside the frame and give it headroom.

The artwork is scaled about a point and re-pasted into a fresh canvas; the
strip left around it is not left black, it is grown out of the artwork's own
border by heat diffusion, so the room's wall and floor simply continue.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (FRAME_SCALE, FRAME_TOP, FRAMED, PARTS, PX,  # noqa: E402
                   SRC_H, SRC_W, ensure_dirs)

ensure_dirs()

SRC = PARTS
DST = FRAMED
W, H = SRC_W, SRC_H
SCALE = FRAME_SCALE                # how much smaller the scene becomes
TOP_PX = FRAME_TOP                 # 38 logical px of wall above the hat
DW = int(round(W * SCALE))
DH = int(round(H * SCALE))
DX = (W - DW) // 2
DY = TOP_PX
print(f"art -> {DW}x{DH} at ({DX},{DY});  margins "
      f"l={DX} r={W-DX-DW} t={DY} b={H-DY-DH} src px  "
      f"= {DX/PX:.0f}/{DY/PX:.0f} logical")

rect = np.zeros((H, W), bool)
rect[DY:DY + DH, DX:DX + DW] = True


def paste_scaled(rgba):
    """Scale the layer with premultiplied alpha and drop it into a new canvas.

    The resize has to run on premultiplied colour -- on a straight-alpha RGBA
    image LANCZOS mixes the colour of a transparent neighbour into an opaque
    edge pixel.  But what leaves this function has to be *straight* alpha
    again, because that is what compose.py's downscale expects: it premultiplies
    a second time (and divides the resize result by the resized alpha).  Leaving
    the canvas premultiplied cost every light layer a factor of its own alpha --
    `halo` shipped at 19% of its colour instead of 100%, and a screen blend with
    a near-black source adds almost nothing.
    """
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    pm = np.concatenate([rgba[..., :3].astype(np.float32) * a, rgba[..., 3:4]], -1)
    # float planes, not uint8: rounding the premultiplied colour to 8 bits
    # before the resize and then dividing by a smaller alpha costs the light
    # layers another ~25% of their colour
    small = np.stack([np.asarray(Image.fromarray(pm[..., i], 'F').resize((DW, DH), Image.LANCZOS))
                      for i in range(4)], -1)
    al = small[..., 3:4]
    small[..., :3] /= np.maximum(al / 255.0, 1e-3)      # back to straight alpha
    small = np.clip(small, 0, 255)
    canvas = np.zeros((H, W, 4), np.float32)
    canvas[DY:DY + DH, DX:DX + DW] = small
    return canvas


def diffuse(plane, rounds=((16, 90), (6, 60), (2, 40))):
    """Grow the border out of the pasted art (Dirichlet heat diffusion)."""
    plane = plane.copy()
    for r, n in rounds:
        blur = ImageFilter.GaussianBlur(r)
        for _ in range(n):
            b = np.asarray(Image.fromarray(
                np.clip(plane, 0, 255).astype(np.uint8)).filter(blur)).astype(np.float32)
            plane[~rect] = b[~rect]
    return plane


def rgb_only(name, canv, channels):
    out = canv.copy()
    sub = out[..., channels]
    planes = [diffuse(sub[..., i]) for i in range(sub.shape[-1])]
    out[..., channels] = np.stack(planes, -1)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f'{DST}/{name}.png')
    print("saved", name)


for name in ('bg', 'screen', 'girl', 'light', 'halo', 'shadow', 'glow'):
    rgba = np.asarray(Image.open(f'{SRC}/{name}.png').convert('RGBA'))
    canv = paste_scaled(rgba)
    if name == 'bg':
        # opaque everywhere: the wall and floor have to continue, and the
        # grown strip must count as painted rather than as a hole
        canv[..., 3] = 255.0
        rgb_only(name, canv, slice(0, 3))
    elif name == 'light':
        # the floor glow runs off the bottom edge, so it has to keep going;
        # left/right/top stay empty because the lamp does not reach there.
        # The whole RGBA row is repeated, not just its alpha: a black pixel
        # with alpha still adds nothing under `mix-blend-mode: screen`.
        last = canv[DY + DH - 1, DX:DX + DW, :].copy()
        for y in range(DY + DH, H):
            canv[y, DX:DX + DW, :] = last
        Image.fromarray(np.clip(canv, 0, 255).astype(np.uint8)).save(f'{DST}/{name}.png')
        print("saved", name)
    elif name == 'halo':
        # the bloom never touches a frame edge, so nothing to continue
        Image.fromarray(np.clip(canv, 0, 255).astype(np.uint8)).save(f'{DST}/{name}.png')
        print("saved", name)
    else:
        Image.fromarray(np.clip(canv, 0, 255).astype(np.uint8)).save(f'{DST}/{name}.png')
        print("saved", name)
