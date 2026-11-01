"""Coin icon set - 16x16 base, gold and silver."""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, "/root/.config/opencode/skills/pixel-art")
import pixelkit as pk

OUT = "out"
os.makedirs(OUT, exist_ok=True)

EMBLEM = [
    "..x..",
    ".x.x.",
    "x...x",
    ".x.x.",
    "..x..",
]


def coin(size: int, base: str, outline: str, light_cap: int = 0) -> pk.Sprite:
    ramp = pk.ramp(base, steps=6)          # ramp[0] lightest .. ramp[5] darkest
    dark = pk.hex_to_rgb(outline)

    cx = cy = (size - 1) / 2
    radius = size / 2 - 0.5
    rim = radius - 1.35                     # 1px recessed rim

    grid: list[list[pk.RGBA]] = [[(0, 0, 0, 0)] * size for _ in range(size)]

    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > radius:
                continue

            if d > rim:
                # Rim: lit on the upper-left, in shadow on the lower-right.
                lit = (-dx - dy) > 0
                colour = ramp[2] if lit else ramp[4]
            else:
                # Beveled face. Two terms: a directional light and a
                # curvature term that falls off toward the edge. Without the
                # second term the disc is a flat gradient; without the first
                # it is a radial blob.
                bevel = 1.0 - (d / rim) ** 2
                lambert = max(0.0, (-dx * 0.62 - dy * 0.72)) / (radius + 1e-6)
                shade = 0.34 + 0.46 * lambert + 0.30 * bevel
                top = min(len(ramp) - 1, light_cap)
                if shade > 0.86:
                    colour = ramp[top]      # tight specular, not a wedge
                elif shade > 0.66:
                    colour = ramp[min(top + 1, 4)]
                elif shade > 0.42:
                    colour = ramp[2]
                else:
                    colour = ramp[3]

            grid[y][x] = (*colour, 255)

    # Engraved emblem: dark shape with a 1px highlight above it. Bevel beats a
    # flat stamp at this size - a flat shape just reads as a hole.
    ox = (size - len(EMBLEM[0])) // 2
    oy = (size - len(EMBLEM)) // 2
    marks: list[tuple[int, int, bool]] = []
    for yy, line in enumerate(EMBLEM):
        for xx, ch in enumerate(line):
            if ch == "x":
                marks.append((ox + xx, oy + yy, True))

    for px, py, is_core in marks:
        if 0 <= px < size and 0 <= py < size:
            grid[py][px] = (*ramp[5], 255)

    for px, py, _ in marks:
        hy = py - 1
        if 0 <= hy < size and grid[hy][px][3] and all(
            not (px == mx and hy == my) for mx, my, _ in marks
        ):
            grid[hy][px] = (*ramp[1], 255)

    sprite = pk.Sprite(size, size, grid)
    return pk.Sprite(size, size, _outline_alpha(sprite.pixels, dark))


def _outline_alpha(pixels: list[list[pk.RGBA]], colour: pk.RGB) -> list[list[pk.RGBA]]:
    h, w = len(pixels), len(pixels[0])
    out = [list(row) for row in pixels]
    for y in range(h):
        for x in range(w):
            if pixels[y][x][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and pixels[ny][nx][3] == 0:
                    out[ny][nx] = (*colour, 255)
    return out


def main() -> None:
    metals = {
        "bronze": ("#c98a4b", "#3a2110", 1),
        "silver": ("#b9c7d8", "#141920", 1),
        "gold":   ("#f5c542", "#3b2a10", 0),
    }

    small: list[pk.Sprite] = []
    large: list[pk.Sprite] = []

    for name, (base, outline, cap) in metals.items():
        icon16 = coin(16, base, outline, light_cap=cap)
        icon32 = icon16.scaled(2)
        icon48 = icon16.scaled(3)
        icon16.save(f"{OUT}/coin_{name}_16.png")
        icon32.save(f"{OUT}/coin_{name}_32.png")
        icon48.save(f"{OUT}/coin_{name}_48.png")
        icon16.scaled(6).save(f"{OUT}/coin_{name}_16_x6.png")
        small.append(icon16)
        large.append(icon32)
        print(name, [pk.rgb_to_hex(c) for c in icon16.palette_colours()])

    sheet16 = pk.sheet(small, columns=3)
    sheet16.save(f"{OUT}/coin_set_16.png")
    sheet16.scaled(6).save(f"{OUT}/coin_set_16_x6.png")

    sheet32 = pk.sheet(large, columns=3)
    sheet32.save(f"{OUT}/coin_set_32.png")
    pk.sheet([s.scaled(3) for s in small], columns=3).save(f"{OUT}/coin_set_48.png")

    print()
    print(pk.to_ascii(small[2]))


if __name__ == "__main__":
    main()
