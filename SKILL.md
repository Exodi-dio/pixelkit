---
name: pixel-art
description: Author, render, inspect and export pixel art sprites, icons, tiles and sprite sheets with no dependencies. Use for game assets, UI icons, app artwork, character sprites, or any request mentioning pixels, sprites, tiles, pixel art, or retro graphics.
---

# Pixel art

Generate real PNGs, then **look at them and iterate**. The loop that matters:

1. Author the sprite (as data or ASCII)
2. Render to PNG
3. Read the PNG back with the read tool — actually look at it
4. Critique it, change something specific, re-render
5. Export for the target (Pixel Studio, game engine, UI)

Never ship a sprite you have not looked at. Pixel art fails at 1x in ways that
are invisible in code: one bad pixel reads as a hole, one extra shade reads as
mud.

## Setup

`pixelkit.py` is stdlib-only (zlib, struct). Copy it next to your work, or add
its directory to `sys.path`. No PIL, no numpy, no install.

```python
import sys; sys.path.insert(0, "/path/to/pixelkit")
import pixelkit as pk
```

## The three ways to author

**ASCII** — best for characters, icons, anything with a silhouette you want to
review in a diff. `.` is transparent.

```python
art = [
    "..hhhh..",
    ".hbbbbh.",
    "hbwbbwbh",
    "hbbbbbbh",
    ".hbbbbh.",
    "..ssss..",
]
mapping = {
    "h": (*pk.ramp("#6bd36b", 4)[0], 255),
    "b": (*pk.ramp("#6bd36b", 4)[1], 255),
    "s": (*pk.ramp("#6bd36b", 4)[2], 255),
    "w": (255, 255, 255, 255),
}
sprite = pk.from_ascii(art, mapping).outline((10, 22, 14))
sprite.save("slime.png")
```

**Procedural** — best for orbs, gradients, tiles, textures. Build a smooth
field mathematically, then quantise + dither it into pixel art.

```python
palette = pk.ramp("#4fc3f7", steps=6)
sprite = pk.Sprite(w, h, field).outline((12, 14, 20))
sprite = pk.Sprite(w, h, pk.quantize(sprite.pixels, palette, dither="bayer"))
```

**Palette-first** — best for consistency across a set. Define the palette once,
map every sprite onto it:

```python
palette = [pk.hex_to_rgb(c) for c in ["#1a1c2c","#5d275d","#b13e53","#ef7d57"]]
sprite = pk.Sprite(w, h, pk.quantize(sprite.pixels, palette, dither="bayer"))
```

## Inspection

```python
print(pk.to_ascii(sprite))            # text view, diffable
print(sprite.palette_colours())        # how many colours am I using?
sprite.scaled(8).save("preview.png")   # 8x nearest-neighbour for viewing
```

Read `preview.png` with the read tool at **4x-8x**. Viewing at 1x is useless —
you cannot see individual pixels. Viewing at 2x is not enough either.

## Rules that separate good from bad

These are not stylistic preferences. Breaking them is why sprites look amateur:

- **One light source, always.** Top-left is the default. Every highlight agrees
  with it or the sprite reads as broken.
- **1px dark outline** (`sprite.outline(...)`). Highest-impact single trick —
  it separates the sprite from any background. Skip it only for tiles.
- **Ramp, never flat fill.** Each material gets 3-5 shades from `pk.ramp()`.
  Shadows shift hue (cooler/blue), not just brightness.
- **No anti-aliasing.** Every pixel is either fully opaque or fully
  transparent. Partial alpha is for UI shadows only.
- **Silhouette first.** Squint: can you tell what it is? If not, fix the
  outline before adding any shading.
- **Even pixel density.** Rotated lines produce staircases — decide the step
  pattern and repeat it, don't let it vary.
- **Dither sparingly.** Ordered (`bayer`) for texture fields. Floyd-Steinberg
  only on large gradients; at 1x it reads as noise on small sprites.
- **Respect the grid.** 16x16, 32x32, 64x64. Non-power-of-two sizes fight
  every engine's atlas packer.

## Sizes

| Use | Size |
| --- | --- |
| UI icon (small) | 16x16 |
| UI icon | 24x24 or 32x32 |
| Character / item sprite | 32x32 or 48x48 |
| Tile | 16x16 (or 32x32 at 2x scale) |
| App artwork | 64x64 to 128x128 |

## Pixel Studio handoff

Pixel Studio has no API. The handoff is a PNG:

1. Export at the exact final size (not the scaled preview).
2. Use RGBA PNG with a transparent background.
3. On the phone, Pixel Studio → new project → **Import image** → pick the PNG.
4. Keep the palette small (≤16 colours) so Pixel Studio's palette view stays
   usable and edits stay consistent.

Import `sprite.png`, not `sprite_x8.png` — the scaled file is for your eyes
only, and importing it gives you an 8x-larger canvas of blocky pixels.

## Sprite sheets

```python
sheet = pk.sheet([idle, walk1, walk2], columns=3)
sheet.save("player_sheet.png")
```

Cells are uniform (max width/height across frames). Keep every frame the same
size or animation will jitter — padding is free, jitter is not.

## Animating

Change one thing per frame. A 4-frame bounce moves the body 1px and squashes it
1px; it does not also change the colour and the eyes. At 32x32, 2-4 frames is
plenty — more frames read as mush at 1x.

## Failure modes to check before delivering

- Sprite drifts off-centre between frames → animation jitters
- Outline has holes where two shapes touch
- Highlight on the wrong side relative to other assets in the set
- More than ~16 colours on a small sprite → mud
- Delivered the 8x preview instead of the 1x asset
