# Environment

## Dependencies

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

numpy and Pillow. Nothing else, and nothing at runtime — the wallpaper itself is
HTML, CSS and PNGs, and the browser loads none of it from disk beyond
`wallpaper/`.

## Where the repo lives

The canonical path is `/home/aigen31/Work/wallpaper-engine-kiki-character`, and
`/home/aigen31/Work` is a symlink to `/mnt/disk1/work`. Both spellings resolve to
the same tree; scripts print the `/mnt/disk1` form because that is what
`Path.resolve()` returns. Nothing depends on which one you use.

## Host gotchas

- **`build/` is 113 MB** and grows back from nothing on the next run. Deleting it
  costs one rebuild, so it is never worth committing and never worth keeping
  around "just in case".
- **No GPU, no display, no network.** The pipeline is pure Python. The one stage
  that needed a model is already done and frozen in `reference/`.
- **Wallpaper Engine is not available here.** The page has only ever been
  exercised in a headless Chromium at 1080p/1440p/4K and at 16:10. Behaviour
  inside the host is inferred from its documented contract, not observed — say so
  rather than claiming a fix is confirmed in Wallpaper Engine.

## ComfyUI

`tools/comfy/` holds the two workflows the reference was prepared with — a
background removal and an image edit — kept for provenance. Neither is on the
build path: they produced `reference/kiki-cutout.png` once, and the pipeline
consumes that file, not the model. The image-edit workflow is the one that
failed at closing her eyes (it returned the eyes open and added a dragon to the
room), which is why the lids are authored by hand in `make_blink.py`.

`tools/explore/` is the same kind of thing: the segmentation and grid experiments
that led to the current stages. They are kept so the reasoning is auditable, and
they are **not** wired into the build and not updated when the layout moves.
