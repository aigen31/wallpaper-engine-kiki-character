"""Where everything lives, and the geometry every stage of the build agrees on.

Each script here is runnable from anywhere, so nothing is resolved against the
shell's working directory. The split is deliberate:

* `reference/` holds the two inputs a human supplied and nothing else.
* `build/` holds everything the pipeline derives. It is ignored by git.
* `wallpaper/` holds the only thing that ships.

The geometry constants live here rather than being repeated per script because
they are *shared*: the CRT rectangle is the inpaint's hole, the light field's
source, the glow's origin and the terminal canvas's position in the browser, and
those four have to agree to the pixel or the text scrolls off the glass.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'reference'
BUILD = ROOT / 'build'
PARTS = BUILD / 'parts'
FRAMED = BUILD / 'parts_framed'
WALLPAPER = ROOT / 'wallpaper'
LAYERS = WALLPAPER / 'layers'

SOURCE = REFERENCE / 'kiki-source.png'   # the reference frame, 1664x960 RGBA
CUTOUT = REFERENCE / 'kiki-cutout.png'   # the same frame, alpha = the witch

# The scene is authored on a 1664x936 grid: the source is cropped to an exact
# 16:9 before anything else touches it. The 24 rows off the top are ceiling.
CROP = (0, 24, 1664, 960)
SRC_W, SRC_H = 1664, 936
STAGE_W, STAGE_H = 640, 360
# Source pixels per logical pixel. Float: this is the number the terminal canvas
# position is derived from, and `1664 // 640 == 2` puts it 30 px off the glass.
PX = SRC_W / STAGE_W

# The CRT surface, in *cropped* coordinates. Raw coordinates are these plus the
# 24 rows CROP takes off, which is the off-by-24 that bites every new script.
SCREEN = (178, 160, 908, 666)
SCREEN_RAW = (SCREEN[0], SCREEN[1] + CROP[1], SCREEN[2], SCREEN[3] + CROP[1])

# reframe.py insets the scene inside the frame. compose.py has to undo it to put
# the mouth back, so the three numbers are named rather than spelled out twice.
FRAME_SCALE = 0.85
FRAME_TOP = 99


def ensure_dirs():
    for d in (BUILD, PARTS, FRAMED, LAYERS):
        d.mkdir(parents=True, exist_ok=True)
