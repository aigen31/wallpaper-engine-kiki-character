"""Turn the four stage builds into the eight PNGs the wallpaper actually loads.

Two jobs, both trivial and both easy to get wrong by hand:

* **The blink overlay is a difference, not a layer.** `compose.py` renders the
  whole frame twice, once with her eyes open and once shut; what ships is the
  pixels that changed, taken from the shut frame. Anything else would need the
  open frame's pixels to be transparent underneath, and they are not.
* **The shipped folder is written in one place.** `wallpaper/layers/` is
  overwritten from `build/`, so the deliverable can never be a hand-edited copy
  that no longer matches the pipeline.
"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import BUILD, LAYERS, ensure_dirs  # noqa: E402

# Soft layers keep a gradient alpha; these two never do.
SHIPPED = ('bg', 'screen', 'girl', 'light', 'halo', 'shadow', 'glow')


def girl(variant):
    return np.asarray(Image.open(BUILD / f'stage_{variant}' / 'girl.png').convert('RGBA')).astype(np.int16)


def main():
    ensure_dirs()
    for variant in ('full', 'limited'):
        open_eyes, shut = girl(variant), girl(f'{variant}_closed')
        diff = (open_eyes != shut).any(2)
        blink = np.zeros_like(shut)
        blink[diff] = shut[diff]
        # kept in build/ as well, so verify.py can compare every shipped layer
        # against the build without knowing that this one is special
        Image.fromarray(blink.astype(np.uint8)).save(BUILD / f'stage_{variant}' / 'blink.png')
        Image.fromarray(blink.astype(np.uint8)).save(LAYERS / variant / 'blink.png')
        ys, xs = np.nonzero(diff)
        print(f"{variant:8s} blink {int(diff.sum()):4d} px  x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}")

        for name in SHIPPED:
            shutil.copyfile(BUILD / f'stage_{variant}' / f'{name}.png', LAYERS / variant / f'{name}.png')
    print(f"shipped {len(SHIPPED) + 1} layers x 2 variants -> {LAYERS}")


if __name__ == '__main__':
    main()
