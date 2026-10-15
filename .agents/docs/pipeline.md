# The pipeline

Seven stages, in order. `tools/build_all.sh` runs them; `SKIP_UPSTREAM=1` starts
at stage 4, which is the difference between a 46-second run and a two-minute one.

| Stage | Script | Reads | Writes |
|---|---|---|---|
| 1 inpaint | `build_screen.py` | source, cut-out | `build/parts/screen_plate_full.png`, `hole.npy`, `text_mask.png` |
| 2 split | `build_layers.py` | source, cut-out, plate | `build/parts/{bg,screen,girl,light,halo}.png` |
| 3 shadow | `build_shadow.py` | cut-out | `build/parts/shadow.png` |
| 4 glow | `build_glow.py` | `girl` | `build/parts/glow.png` |
| 5 frame | `reframe.py` | all of `parts/` | `build/parts_framed/` |
| 6 eyes | `make_blink.py` | `parts_framed/girl.png` | `parts_framed/girl_closed.png` |
| 7 stage | `compose.py` ×4, `emit_layers.py` | `parts_framed/` | `build/stage_*/`, `wallpaper/layers/` |

`tools/preview.py` flattens a stage the way the browser does, at the browser's
opacities, and is the only way to see a change without opening Wallpaper Engine.

## Geometry, and the trap in it

`tools/paths.py` is the single source for every coordinate. Two of them are easy
to get wrong and expensive to debug:

- **`CROP = (0, 24, 1664, 960)`.** The reference is 1664×960; the scene is
  authored on the 1664×936 left after the top 24 rows. So *raw* coordinates are
  *cropped* ones plus 24 on y, and `SCREEN_RAW` exists only for stage 1, which
  works on the untouched source. Everything downstream is cropped.
- **`PX = SRC_W / STAGE_W` = 2.6.** Float. Written as `1664 // 640` it is 2, and
  the terminal canvas lands 30 px off the glass. `verify.py` catches exactly that
  by deriving the canvas rectangle from `SCREEN` and comparing it to `index.html`.

`reframe.py` then insets the framed scene to `FRAME_SCALE = 0.85` pasted at
`FRAME_TOP = 99`, which is what gives 48 logical px of margin either side and 38
above the hat. `compose.py` has to undo that to put the mouth back, so it reads
the same three constants rather than repeating `0.85, 125, 99`.

## The three-stage relaxation

Both `build_screen.py` and `reframe.py` fill an unknown region by relaxation,
and both need **coarse-to-fine rounds** — `((16, 120), (6, 80), (2, 60))`,
largest radius first. A single radius cannot cross the region in a sane number
of passes: the glass hole is 271 915 px across 500-odd pixels, and `radius 4,
260 passes` diffuses about 64 px and leaves the witch smeared onto the glass.
The coarse round carries the boundary across, the fine rounds put the detail
back. If you change the region size, change the coarse radius with it.

## What each stage is allowed to decide

- `build_layers.py` picks the **light colour** (90, 200, 110) as a literal. It
  used to sample it from the spill and then ignore the sample; the phosphor is
  one green everywhere, and a sampled hue drifts with the crop.
- `build_glow.py` owns the **asymmetric reach** (150 px sideways, 105 up, 18
  down). The 18 is load-bearing: the hem of her dress and her boots sit below
  the glass, in no light path at all.
- `compose.py` owns the **alpha rule** — binary for cut-outs, gradient for light
  — and the **mouth**, which it paints back after the quantiser has dropped it.
- `emit_layers.py` owns the **blink overlay**, which is a difference between the
  two eye states rather than a layer, and the copy into `wallpaper/layers/`.

## Numbers this repo stands behind

Measured on the current scripts, all reproduced by `tools/build_all.sh`:

| | |
|---|---|
| whole run | 46 s, `build/` grows to 113 MB |
| glass inpaint | 271 915 px hole = 68 382 text + 185 633 witch |
| framing | art 1414×796 at (125, 99) |
| glow | 204 611 source px, stage rows 41..268; exposure 1.000 on the brim, 0.000 on the boots |
| blink | 198 px (reference) / 173 px (limited), from 1117 changed source px |
| palette | 128 entries; limited uses 125/96/121 colours on bg/screen/girl |
| shipped | 8 layers × 2 variants, 640×360, 948 KB total |

`README.md` quotes these too. When one moves, move it in both places —
`verify.py` asserts the behaviour, not the numbers, so it will stay green while
the prose is quietly wrong.
