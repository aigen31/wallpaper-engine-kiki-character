import os, sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import BUILD, STAGE_H, STAGE_W  # noqa: E402

STAGE = Path(os.environ.get('WE_STAGE', BUILD / 'stage'))
H, W = STAGE_H, STAGE_W
GLOW_OP = float(os.environ.get('WE_GLOW', '0.55'))   # the browser's nominal
def load(n):
    return np.asarray(Image.open(f'{STAGE}/{n}.png').convert('RGBA')).astype(np.float32)
def over(a, b, mode='normal', op=1.0):
    aa = (a[..., 3:4] / 255.0) * op
    bb = b[..., 3:4] / 255.0
    if mode == 'screen':
        res = (255 - (255 - a[..., :3]) * (255 - b[..., :3]) / 255.0) * aa + b[..., :3] * bb * (1 - aa)
    else:
        res = a[..., :3] * aa + b[..., :3] * bb * (1 - aa)
    o = b.copy(); o[..., :3] = res; o[..., 3] = ((aa + bb * (1 - aa)) * 255)[..., 0]
    return o
c = np.zeros((H, W, 4), np.float32); c[..., 3] = 255
for n, m, op in (('bg','normal',1),('screen','normal',1),('halo','screen',0.16),
                 ('light','screen',0.22),('shadow','normal',0.60),('girl','normal',1),
                 ('glow','screen',GLOW_OP)):
    c = over(load(n), c, m, op)
out = os.environ.get('WE_OUT', str(STAGE / 'preview.png'))
Image.fromarray(c.astype(np.uint8)).save(out)
Image.fromarray(c.astype(np.uint8)).resize((W*2, H*2), Image.NEAREST).save(out.replace('.png','@2x.png'))
print("preview ->", out)
