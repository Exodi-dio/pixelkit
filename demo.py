"""Demo: generate, render, inspect, export.

Run: ``python demo.py`` - writes PNGs into ``out/``.
"""

from __future__ import annotations

import math
import os

import pixelkit as pk

OUT = "out"
os.makedirs(OUT, exist_ok=True)


def orb(size: int = 32, colour: str = "#4fc3f7") -> pk.Sprite:
    """A shaded sphere: lighting model, then palette quantisation + dither.

    This is the pattern to reuse: build a smooth field mathematically, then let
    a short palette and ordered dithering do the pixel-art translation. It
    beats hand-placing hundreds of pixels and stays deterministic.
    """
    cx = cy = (size - 1) / 2
    radius = size / 2 - 1
    ramp = pk.ramp(colour, steps=6)
    palette = ramp + [(12, 14, 20)]

    light = (-0.45, -0.7)
    base: list[list[pk.RGBA]] = []

    for y in range(size):
        row: list[pk.RGBA] = []
        for x in range(size):
            dx = (x - cx) / radius
            dy = (y - cy) / radius
            d = math.hypot(dx, dy)
            if d > 1.0:
                row.append((0, 0, 0, 0))
                continue

            # Lambert-ish shading on a sphere, plus a rim term.
            nz = math.sqrt(max(0.0, 1.0 - d * d))
            lambert = max(0.0, dx * light[0] + dy * light[1] + nz * 0.85)
            # Rim darkening: without it a sphere reads as a flat vertical
            # gradient. This is the pixel-art equivalent of ambient occlusion.
            rim = 0.45 + 0.55 * nz
            shade = (0.10 + 0.90 * lambert) * rim
            band = int(round((1.0 - shade) * (len(ramp) - 1)))
            band = max(0, min(len(ramp) - 1, band))
            row.append((*ramp[band], 255))
        base.append(row)

    sprite = pk.Sprite(size, size, base)
    sprite = pk.Sprite(
        size, size, pk.quantize(sprite.pixels, palette, dither="bayer")
    )
    return sprite


def slime() -> pk.Sprite:
    """A hand-authored sprite, for the ASCII authoring path."""
    ramp = pk.ramp("#6bd36b", steps=4)
    art = [
        "................",
        "................",
        ".....hhhhhh.....",
        "...hhhbbbbhhh...",
        "..hhbbbbbbbbhh..",
        ".hhbbbbbbbbbbhh.",
        ".hbbbbbbbbbbbbh.",
        ".bbbbwbbbbwbbbb.",
        ".sbbbwbbbbwbbbs.",
        ".sbbbbbbbbbbbbs.",
        "..sbbbbbbbbbbs..",
        "..sbbbsssssbbs..",
        "...ssssssssss...",
        "....ssssssss....",
        "................",
        "................",
    ]
    mapping = {
        "h": (*ramp[0], 255),
        "b": (*ramp[1], 255),
        "s": (*ramp[2], 255),
        "w": (255, 255, 255, 255),
    }
    return pk.from_ascii(art, mapping).outline((10, 22, 14))


def main() -> None:
    ball = orb(32)
    ball.save(os.path.join(OUT, "orb.png"))
    ball.scaled(6).save(os.path.join(OUT, "orb_x6.png"))

    blob = slime()
    blob.save(os.path.join(OUT, "slime.png"))
    blob.scaled(8).save(os.path.join(OUT, "slime_x8.png"))

    timeline = pk.sheet([blob, blob.flip(), ball, ball.scaled(1)], columns=4)
    timeline.scaled(4).save(os.path.join(OUT, "sheet_x4.png"))

    print("orb palette:", [pk.rgb_to_hex(c) for c in ball.palette_colours()])
    print("slime palette:", [pk.rgb_to_hex(c) for c in blob.palette_colours()])
    print("\nslime as text:\n" + pk.to_ascii(blob))


if __name__ == "__main__":
    main()
