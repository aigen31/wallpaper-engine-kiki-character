# Kiki // Terminal — Wallpaper Engine web wallpaper

A witch sits in front of an old CRT and the terminal on it keeps scrolling.
Built from one reference image (`article/img/raw/33b91637_000.png`), split into
layers that animate independently of each other.

## Install

Drop the whole folder into Wallpaper Engine ("Create Wallpaper" → pick
`index.html`), or copy it into
`wallpaper_engine/projects/myprojects/` and open it from the editor.
Everything is local — no CDN, no network, no audio capture.

## Layers

Back to front. Each is a full-stage `640×360` RGBA PNG; the entities the brief
named are separate nodes, so none of them is baked into another.

| Node | File | What it is | Animated? |
|---|---|---|---|
| `#bg` | `layers/bg.png` | the room: wall, floor, monitor shell, stand, papers, wand | no |
| `#screen` | `layers/screen.png` | the CRT surface, with the original baked-in text removed | no |
| `#term` | *(canvas)* | the live terminal — the scrolling characters | **yes**, row by row |
| `#halo` | `layers/halo.png` | green bloom around the monitor | **yes**, brightness |
| `#light` | `layers/light.png` | screen light spilling onto the floor | **yes**, brightness |
| `#shadow` | `layers/*/shadow.png` | the witch's cast shadow on the floor | **yes**, twitch + opacity |
| `#girl` | `layers/*/girl.png` | the witch, cut out with alpha | no |
| `#glow` | `layers/*/glow.png` | the screen's light on her hat and hair | **yes**, brightness |
| `#blink` | `layers/*/blink.png` | her shut eyelids, a patch the size of the two eyes | **yes**, blink |

Each raster layer exists twice, under `layers/full/` and `layers/limited/` — see
*Two palettes* below.

`#halo`, `#light` and `#glow` are composited with `mix-blend-mode: screen`, so
they only ever add light — they can never darken what is behind them.

## Two palettes

The **Palette** property switches the whole wallpaper between two renders of the
same frame:

* **Reference (saturated)** — `layers/full/`. No quantisation at all: every
  pixel carries the colour the box filter gave it, so 20 070 distinct colours
  survive in the flattened frame and her eyes stay emerald. This is the
  reference image's own palette.
* **Limited 128 colours** — `layers/limited/`. The same frame snapped to one
  128-colour palette derived from it, plus a single extra ink for the mouth
  (129 in total). Her eyes go olive, the blush flattens.

Both sets are preloaded as `Image()` objects on startup, so flipping the
property is a swap out of the browser cache rather than a fresh decode — no
flash between the two.

## Framing

The scene does not fill the frame. It is authored at 85% and inset — 38 logical
px of bare wall above the hat, 48 px either side, 16 px below the papers — so the
peak of the hat has air around it instead of sitting three pixels off the top
edge.

The strip left around the scene is not black filler: the background layer grows
it out of its own border by heat diffusion, so the wall and the floor simply
continue. That is why there is no rectangle to see at the join — the mean step
across either seam is 0.6/255 horizontally and 0.2/255 vertically in the
finished frame, and the sharpest step anywhere along it is 2/255, against a p99
of 9/255 for the scene's own edges. The floor glow runs off the bottom edge, so
`light` repeats its last row downward to keep reaching it; the bloom and the
glow on the witch never touch an edge, so they need nothing.

## The five animations

**Terminal scroll.** Not a smooth marquee: the buffer advances one whole
character row at a time, the way a tty does when a line is committed. The
newest row types out a few characters per step, then the whole view jumps up
exactly one cell (`CELL_H = 6` logical px). Glyphs come from a hand-drawn 3×5
bitmap font embedded in the page — 15 bits per character, so every glyph is
crisp at any integer scale and there is nothing to anti-alias. The grid is 22×22
characters on the 239×166 CRT surface.

**Light.** `LIGHT_SEQ` is a 16-entry loop over 11 distinct brightness values
between 0.62 and 1.00. Every 1/3.75 s the index advances by one step; halo
opacity, floor-light opacity, terminal brightness and shadow darkness are all
read off that single value. No CSS transition, no interpolation — the lamp
steps. The glow on the witch is advanced on the same tick and never on a clock
of its own, but its own value is damped — see below.

**Glow on her.** The CRT also throws light back onto the witch, and that is what
`layers/*/glow.png` is — a green rim on the underside of the hat brim, the strand
of hair hanging in front of the screen, and the hair on both sides of her face.
It is generated, not painted: `tools/build_glow.py`
weights every pixel of her silhouette by its distance to the CRT surface and by
the downward component of the silhouette's own outward normal — the screen is behind her, so only the
surfaces that curve away towards it catch anything, which is a rim light. It
then runs through the same downscale as everything else.

The falloff is **not** the same in every direction. A lit rectangle spills light
over its top edge and out to the sides, but there is nothing below the glass:
the reach is 150 source px sideways, 105 px upwards (that is what the hat above
the monitor catches) and 18 px downwards. That last number is what keeps the
glow off the hem of her dress and off her boots — a symmetric falloff lit them,
and they sit entirely below the monitor, in no light path at all.

Its opacity is the one place the glow does **not** follow the light step for
step. `LIGHT_SEQ` is deliberately jumpy — neighbouring entries differ by up to
a third, which is what makes the lamp read as a lamp — and on the floor that is
fine, but a two-pixel rim has no area to absorb it: the same jump flashes. So
the glow gets its own loop, built at startup by pushing the same sequence
through a one-pole low pass and mapping the result into a narrow band around
`GLOW_BASE` (0.23). In practice it takes fourteen values between 0.195 and
0.260, and the largest move between any two of them is 0.054 — about 13/255 on
the pixel that changes most, against 48/255 for the glow being there at all. It
is still one discrete number per tick, written in the same call as the halo and
the floor light, so it cannot drift out of sync with them; it just breathes
instead of blinking. The shut lids draw on top of it, and the two never touch:
the eyes sit far enough inside the silhouette that the rim field is zero there.

**Blink.** The lid is not a tween: `blinkTick()` holds a small state machine on
the same 30 Hz tick as everything else. Once every 1.5–5 s the lid comes down
for 2–3 ticks (70–100 ms) and lifts again, with an 18% chance of an immediate
second blink.

What moves is the *lash*, and getting that right took three passes. Hiding the
iris and leaving the lash where it was reads as a squint; closing the eye on the
logical grid but starting the patch at the eye's *bright* pixels leaves the old
lash sitting above the new one, which reads as two lashes. So
`tools/make_blink.py` works at source resolution, where
the eye is ~30×16 px:

* **Finding the eye.** The lash, the iris and the sclera are all neutral or
  green (R−G of 0 or less) while the fringe, the skin and the hair are warm
  brown (R−G of +25 and up), so a flood fill from the iris stops at the eye's
  real outline. That is why the lid has no rectangle in it — luminance alone
  cannot do this, because the fringe goes as dark as the lash in shadow.
* **One lash.** The original lash lies inside the repainted region, so it is
  gone; the new one is drawn low in the eye.
* **A lash, not a bar.** It is a shallow arc with a small ripple — sags in the
  middle, uneven along its length — and the rows above and below it are mixed
  towards the lid and the cheek, so its edges fade the way the open lash's do.

The blink frame is composited through the same pipeline with `WE_GIRL=girl_closed`
and `WE_PALETTE_FROM` reusing the open frame's palette, and the overlay shipped
to the browser is the difference between the two — 198 px (173 in the limited
palette), a patch the size of the two eyes, so the open frame underneath is
never touched.

**Shadow.** It is a projection of the same lamp, so it does not run on its own
clock: `shadowStep()` fires when the light steps. A brighter level pushes the
shadow one logical pixel further from her, an occasional step pulls it back.
The translation is always a whole logical pixel, never fractional, so the
shadow is never resampled.

## Adapted for 4K

The stage is exactly `640×360` and the page scales it with a single integer
transform, snapped when the raw ratio is within 12% of a whole number:

| Viewport | Scale | Result |
|---|---|---|
| 3840×2160 | **6×** | one logical pixel = a uniform 6×6 block |
| 2560×1440 | **4×** | 4×4 |
| 1920×1080 | **3×** | 3×3 |
| 1280×720 | **2×** | 2×2 |

Because the factor is an integer, no pixel is ever half-covered: the art is
never resampled, only duplicated. Odd aspect ratios are covered by the same
transform (the stage crops rather than stretches).

A ratio that does **not** land near a whole number gets two device pixels of
overhang on every side — 1920×1200 resolves to 3.344× and 2560×1600 to 4.456×
instead of 3.333× and 4.444×. That is 0.6% more scale and loses nothing, and it
keeps the stage's own edge off the edge of the viewport. Flush against it, at a
fractional scale, the seam is where a compositor can smear the edge of a blended
layer into a bright one-pixel line across the top. The integer ratios keep their
exact 3× and 6×, because those never had the problem.

## Wallpaper Engine properties

| Property | Default | Effect |
|---|---|---|
| Glow Intensity | 100 | scales the halo, the floor light and the glow on her (0–200%) |
| Terminal Speed | 100 | re-times both the scroll and the light steps (20–300%) |
| Shadow Twitch | on | turns the shadow's movement off |
| Eye Blink | on | turns the blink off |
| Palette | Reference | Reference (saturated) ⇄ Limited 128 colours |
| Scheme color | dark green | required by the WE browser |

The page also honours Wallpaper Engine's global FPS cap through
`applyGeneralProperties` → `wallpaperPropertyListener`.

## Palette and alpha

In the **limited** variant `bg`, `screen`, `girl` and `shadow` all draw from one
128-colour palette derived from the flattened scene, so a pixel is one colour
everywhere and no layer can introduce an off-palette shade at an edge. The
**reference** variant skips that step and keeps the box filter's own colours.

Edges get one more step in both variants. The cut-out came from a model whose
alpha is anti-aliased, and the RGB under a half-covered edge pixel is already
part girl and part room — so an ordinary alpha-weighted downscale hands the
logical edge cell a colour mixed with the wallpaper behind her. Palette
snapping hides that; keeping the reference's own colours does not. With
`crisp_edges` the cell's colour is taken only from its opaque source pixels
while its coverage still comes from the full alpha average, which is what makes
her silhouette read as hair instead of a smudge against the CRT.

The mouth is put back by hand in both. It is a 6×4 px pink dot in the reference;
box-averaging one 2.6 px logical cell dilutes it back into cheek skin, and the
128-colour quantiser then has no entry for it at all — so after the palette step
two logical pixels are painted with the mouth's own ink (#d08a74), which is why
the limited variant counts 129 colours and not 128.

Alpha is binary on the cut-out art — `bg`, `screen` and `girl` — because a
half-covered edge turns into a smeary fringe the moment `image-rendering:
pixelated` blows it up. The `shadow`, `halo`, `light` and `glow` layers keep a
gradient alpha instead: they are light, not silhouettes, and thresholding them
discards almost the whole effect (it once left 1.5% of the glow standing). A
gradient alpha at the logical grid is still pixel art — each logical pixel still
carries exactly one value, and nearest-neighbour scaling keeps it blocky.

None of the four light layers is palette-snapped in either variant. Light is not
a surface, and forcing a glow onto the 128-colour set would band it for no gain.

## Rebuilding the layers

This folder is generated. Everything in `layers/`, and everything the page
draws, comes out of the pipeline in `../tools/` at the repository root:

```
tools/build_all.sh        the whole chain, ~46 s, from reference/ to here
tools/verify.py           87 checks over the shipped PNGs and index.html
```

The build is deterministic — no model inference, no randomness, no timestamps —
so after a run an empty `git diff` under `layers/` means the art was reproduced
exactly and a non-empty one means it moved. The stage-by-stage description, the
shared geometry and the numbers this README quotes are in
`../.agents/docs/pipeline.md`, at the repository root.

The witch's alpha came from ComfyUI's *Remove Background: Qwen Image 2.1*
template, frozen as `reference/kiki-cutout.png` at the repository root.
The model returned the original pixels with a new alpha channel — 67% of opaque
pixels matched the source within ±2/255 and no translation improved the fit — so
her cutout is registered to the scene exactly, not merely similar to it.

The shut lids were **not** made with the image model. Qwen Image 2.1's edit
template was tried on this frame and returned her with the eyes still open and a
large dragon added to the room. At this size the target is too small and too
exact for it, so the lid is authored by hand in
`tools/make_blink.py` — see the blink note above.

