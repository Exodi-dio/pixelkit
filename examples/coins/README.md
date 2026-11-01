# Coin icon set

Bronze / silver / gold, 16x16 masters with nearest-neighbour exports at 32 and 48.

![coin set](coin_set_16_x6.png)

Regenerate with `python build.py` (writes into `out/`; the committed files are
copied from there).

## Design notes

- **16px is the master.** 32 and 48 are nearest-neighbour scale-ups, not
  re-renders. Rendering the coin procedurally at 32 produced flat "seal"
  shapes that lost the pixel-art read - see the git history.
- **Rim is 1px and asymmetric**: lit on the upper-left, in shadow on the
  lower-right. Symmetric rims make the coin look like a flat washer.
- **Face uses two shade terms**: a directional light and a curvature term.
  Either one alone gives a gradient blob.
- **Emblem is engraved**, not stamped: a dark shape with a 1px highlight
  above it. At 16px a flat stamp just reads as a hole.
- **Silver is capped one band darker** (`light_cap=1`); at full brightness its
  specular blew out the whole upper-left quadrant.

## Palette

| Metal | Ramp base | Outline |
| --- | --- | --- |
| bronze | `#c98a4b` | `#3a2110` |
| silver | `#b9c7d8` | `#141920` |
| gold | `#f5c542` | `#3b2a10` |

Import `coin_*_16.png` into Pixel Studio, not the scaled copies.
