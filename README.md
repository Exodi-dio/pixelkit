# pixelkit

Pixel art toolkit for AI agents. **Standard library only** — no PIL, no numpy,
no install step. Runs fine in Termux.

The point is not just drawing. It is closing the loop: generate a PNG, read it
back with the agent's image tool, critique it, change one thing, regenerate.
Code alone cannot tell you a sprite looks wrong; looking at it can.

```python
import pixelkit as pk

palette = pk.ramp("#4fc3f7", steps=6)
sprite = pk.Sprite(w, h, field)
sprite = pk.Sprite(w, h, pk.quantize(sprite.pixels, palette, dither="bayer"))
sprite.save("orb.png")

print(pk.to_ascii(sprite))          # text view, diffable
sprite.scaled(8).save("preview.png")  # 8x nearest neighbour, for viewing
```

## What's in it

| Function | Purpose |
| --- | --- |
| `write_png` / `read_png` | real 8-bit RGBA PNG in and out |
| `ramp(base, steps)` | light→dark ramp with hue shifting |
| `quantize(pixels, palette, dither)` | palette mapping, bayer or Floyd-Steinberg |
| `from_ascii` / `to_ascii` | author and inspect sprites as text |
| `Sprite.scaled` / `.flip` / `.outline` | nearest-neighbour transforms, 1px outline |
| `sheet(sprites, columns)` | pack frames into a uniform sheet |

## Demo

```bash
python demo.py   # writes out/orb.png, out/slime.png, out/sheet_x4.png
python -m pytest tests -q
```

## Pixel Studio

No API exists, so the handoff is a PNG: export at the exact final size, import
in Pixel Studio, keep the palette small. `SKILL.md` documents the full
workflow and the art rules that make sprites read at 1x.

## License

MIT.
