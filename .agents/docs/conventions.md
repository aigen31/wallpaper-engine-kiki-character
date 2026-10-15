# Conventions

## Language

Code prose — docstrings, comments, commit messages — is **English**. Nothing
user-facing in this repo is Cyrillic, and the reference art carries no text of
its own (the terminal's is generated from `SCRIPT` in `index.html`).

## Shape of a script

Every script in `tools/` is executable from any working directory, so it starts
the same way and resolves its own parent before importing anything local:

```python
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import PARTS, SCREEN, ensure_dirs  # noqa: E402
```

Then: read, compute, write, and **print one line saying what came out** with the
number that would look wrong if it were wrong — `hole 271915`, `blink 198 px`,
`exposure: ... boots 0.000`. Those lines are the only progress reporting there
is, and they are what makes a 46-second build readable.

No path is spelled out twice. `tools/paths.py` holds every directory, the two
inputs and the geometry; a literal `1664` or `0.85` anywhere else is a bug
waiting for the next crop.

## Docstrings

A docstring says *why* the step exists and what it costs — not what the next
line does. The most valuable ones record the failure the code was written to
avoid:

> "the empty `<img>` silently rendered nothing, and it read as 'the light on the
> witch does not work'"

> "`radius 4, 260 passes` diffuses about 64 px and leaves the witch smeared
> across the glass"

If a constant looks arbitrary, the docstring is where its history goes. A future
reader changing `18.0` to `105.0` for symmetry is the exact failure to prevent.

## Style

- Lines wrap near 100 columns.
- Snake case, `CAPS` for module-level constants, `f'{name}.png'` over `os.path.join`.
- numpy for anything pixel-wise, `PIL.Image` for resize and blur. Nothing else:
  the pipeline has to run without a GPU, a display or a package manager beyond
  pip.
- A new dependency needs a reason that survives "can this be twenty lines of
  numpy?".

No formatter or linter is configured. Keep diffs local; do not reflow untouched
code.

## The wallpaper page

`index.html` is ES5 and stays ES5. It runs inside Wallpaper Engine's embedded
Chromium, which is old enough that arrow functions, template literals and `let`
are not the place to find out. `var` and `function`, no build step, no bundler,
no framework — the whole page is one file by design, because that is the only
shape the host can load.

CSS keeps every raster layer on the same grid: `position: absolute; left: 0;
top: 0; width: 100%; height: 100%` plus `image-rendering: pixelated`. A layer
that opts out of either is no longer pixel art.
