# The Wallpaper Engine side

`wallpaper/` is the deliverable and it is self-contained: drop the whole folder
into Wallpaper Engine, or copy it to
`wallpaper_engine/projects/myprojects/` and open it from the editor. Nothing is
fetched — no CDN, no fonts, no audio capture — and `verify.py` fails the build if
a `src`/`href` ever grows a scheme.

**Ship every file.** The one field failure this repo has had was an incomplete
upload: `glow.png` was missing from the copy, the `<img>` silently rendered
nothing, and it read as "the light on the witch does not work". Wallpaper Engine
gives no console for a missing subresource, and neither does it tell you the
layer list is short. If a layer looks absent, check the folder before the code.

**Re-import after changing the folder.** Wallpaper Engine caches the project; a
redraw is not a reload.

## The two files the host reads

`project.json` declares the properties; `index.html` reads them through
`window.wallpaperPropertyListener`. `verify.py` cross-checks the names in both
directions, because a typo in either is silent.

| Property | Type | Default | What the page does with it |
|---|---|---|---|
| `schemecolor` | colour | dark green | nothing — the host requires it |
| `intensity` | slider 0–200 | 100 | scales halo, floor light and the glow on her |
| `scrollspeed` | slider 20–300 | 100 | re-times the scroll *and* the lamp |
| `flicker` | bool | on | enables the shadow's twitch |
| `blink` | bool | on | enables the blink |
| `palette` | combo | `full` | swaps `layers/full/` for `layers/limited/` |

`applyGeneralProperties` also receives `fps`, the host's frame cap. It is
honoured in the render loop and deliberately not declared — it is not ours.

## Layer order and blending

Back to front, and the order is load-bearing:

```
bg  screen  term(canvas)  halo  light  shadow  girl  glow  blink
```

`halo`, `light` and `glow` are the only blended elements, all
`mix-blend-mode: screen`, so they can add light and never subtract it. `glow`
must come *after* `girl` or it blends with the room instead of with her;
`blink` must come last so the shut lids are never covered by the rim light.

`#stage` has a `transform`, which makes it a stacking context and therefore
isolates the blending to the stage. Do not remove the transform to "clean up"
the CSS: without it the blend reaches the page backdrop.

## Frame-stepped animation

One `requestAnimationFrame` loop, and every animation is quantised to it:

- one tick is `1000/30` ms, so nothing moves between ticks;
- the lamp advances one `LIGHT_SEQ` entry per 8 ticks (3.75/s), and the halo,
  the floor light, the shadow, the terminal brightness and the glow are all
  written in that same call — they cannot drift apart;
- the terminal advances a whole character row or a few characters per tick,
  never a fraction;
- a blink is 2–3 ticks down and 45–150 ticks up.

The one place a value is *not* the raw light level is the glow on her: it is the
same sequence through a one-pole low pass, mapped into 0.195…0.260. The light
sequence is jumpy by design and a two-pixel rim has no area to absorb a jump.
See the **Glow on her** section of [`wallpaper/README.md`](../../wallpaper/README.md).

## The integer scale

The page is authored on a single 640×360 grid and blown up by one transform, so
a logical pixel is always a whole number of device pixels: 3× at 1080p, 4× at
1440p, 6× at 4K. The ratio snaps to an integer when it is within 12% of one.

A ratio that does *not* snap — 3.333× at 1920×1200, 4.444× at 2560×1600, every
16:10 panel — gets two device pixels of overhang on each side instead. It costs
0.6% of scale, and it keeps the stage's edge off the viewport's edge, which at a
fractional scale is where a compositor can smear a blended layer's edge into a
bright one-pixel line across the top.

`image-rendering: pixelated` is on every raster layer. Removing it from one
layer and not the others is worse than removing it everywhere.
