"""pixelkit - pixel art without dependencies.

Everything here is Python standard library only (zlib, struct). No PIL, no
numpy, no numpy-free compromise: it writes real PNG files that any editor
opens, including Pixel Studio.

Design intent: an AI agent should be able to author a sprite as *data*
(a grid of palette indices), render it, read the PNG back to look at it, and
iterate. Every function is deterministic so a diff means a real change.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

# --------------------------------------------------------------------------
# PNG
# --------------------------------------------------------------------------


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path: str, width: int, height: int, pixels: list[list[RGBA]]) -> None:
    """Write an 8-bit RGBA PNG. ``pixels`` is row-major, ``pixels[y][x]``."""
    if len(pixels) != height:
        raise ValueError(f"expected {height} rows, got {len(pixels)}")

    raw = bytearray()
    for row in pixels:
        if len(row) != width:
            raise ValueError(f"expected {width} columns, got {len(row)}")
        raw.append(0)  # filter type 0 (None)
        for pixel in row:
            r, g, b, a = pixel
            raw += bytes((r & 255, g & 255, b & 255, a & 255))

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")

    with open(path, "wb") as fh:
        fh.write(png)


def read_png(path: str) -> tuple[int, int, list[list[RGBA]]]:
    """Read an 8-bit, non-interlaced RGB/RGBA PNG."""
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")

    pos = 8
    width = height = depth = color_type = 0
    idat = bytearray()
    palette: list[RGB] = []

    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        tag = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        pos += 12 + length

        if tag == b"IHDR":
            width, height, depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", body
            )
            if depth != 8 or interlace != 0:
                raise ValueError("only 8-bit non-interlaced PNG supported")
        elif tag == b"PLTE":
            palette = [
                (body[i], body[i + 1], body[i + 2]) for i in range(0, len(body), 3)
            ]
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValueError(f"unsupported colour type {color_type}")

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out: list[list[RGBA]] = []
    prev = bytearray(stride)
    i = 0

    for _ in range(height):
        ftype = raw[i]
        i += 1
        line = bytearray(raw[i : i + stride])
        i += stride
        _unfilter(ftype, line, prev, channels)
        row: list[RGBA] = []
        for x in range(width):
            chunk = line[x * channels : (x + 1) * channels]
            if color_type == 6:
                row.append((chunk[0], chunk[1], chunk[2], chunk[3]))
            elif color_type == 2:
                row.append((chunk[0], chunk[1], chunk[2], 255))
            elif color_type == 0:
                row.append((chunk[0], chunk[0], chunk[0], 255))
            elif color_type == 4:
                row.append((chunk[0], chunk[0], chunk[0], chunk[1]))
            else:  # palette
                r, g, b = palette[chunk[0]]
                row.append((r, g, b, 255))
        out.append(row)
        prev = line

    return width, height, out


def _unfilter(ftype: int, line: bytearray, prev: bytearray, bpp: int) -> None:
    if ftype == 0:
        return
    if ftype == 1:  # Sub
        for i in range(bpp, len(line)):
            line[i] = (line[i] + line[i - bpp]) & 255
    elif ftype == 2:  # Up
        for i in range(len(line)):
            line[i] = (line[i] + prev[i]) & 255
    elif ftype == 3:  # Average
        for i in range(len(line)):
            left = line[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
    elif ftype == 4:  # Paeth
        for i in range(len(line)):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[i] = (line[i] + pr) & 255
    else:
        raise ValueError(f"bad filter type {ftype}")


# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------


def hex_to_rgb(value: str) -> RGB:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) == 8:
        v = v[:6]
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def rgb_to_hex(rgb: RGB) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def ramp(base: str, steps: int = 5, spread: float = 0.22) -> list[RGB]:
    """Build a light-to-dark colour ramp around ``base``.

    Pixel art almost never uses flat colours: each material gets a ramp and the
    shading picks a step. The ramp deliberately shifts hue as it darkens (cool,
    blue-shifted shadows) instead of only scaling brightness, which is what
    separates hand-made sprites from gradient-filled ones.
    """
    import colorsys

    r, g, b = hex_to_rgb(base)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    out: list[RGB] = []
    n = max(1, steps - 1)
    for i in range(steps):
        t = i / n
        lightness = min(1.0, max(0.0, l + (0.5 - t) * spread * 2.2))
        hue = (h + (t - 0.5) * 0.04) % 1.0
        sat = min(1.0, max(0.0, s * (1.08 - abs(t - 0.5) * 0.35)))
        rr, gg, bb = colorsys.hls_to_rgb(hue, lightness, sat)
        out.append((int(rr * 255), int(gg * 255), int(bb * 255)))
    return out


def _dist(a: RGB, b: RGB) -> int:
    # Weighted so green dominates, matching perceived luminance.
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return 2 * dr * dr + 4 * dg * dg + 3 * db * db


def nearest(rgb: RGB, palette: list[RGB]) -> RGB:
    return min(palette, key=lambda p: _dist(rgb, p))


def quantize(
    pixels: list[list[RGBA]], palette: list[RGB], dither: str | None = None
) -> list[list[RGBA]]:
    """Map an image onto ``palette``.

    ``dither`` is ``None``, ``"bayer"`` (ordered 4x4) or ``"floyd"``.
    Ordered dithering is the pixel-art default; Floyd-Steinberg creates noise
    that looks wrong at 1x and should be used sparingly.
    """
    h = len(pixels)
    w = len(pixels[0]) if h else 0
    buf = [[list(p[:3]) for p in row] for row in pixels]

    bayer = [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
    ]

    out: list[list[RGBA]] = []
    for y in range(h):
        row: list[RGBA] = []
        for x in range(w):
            src = tuple(buf[y][x])
            if dither == "bayer":
                bias = (bayer[y % 4][x % 4] / 16.0 - 0.5) * 28
                src = tuple(
                    max(0, min(255, int(c + bias))) for c in src
                )
                chosen = nearest(src, palette)
            elif dither == "floyd":
                chosen = nearest(src, palette)
                err = [src[i] - chosen[i] for i in range(3)]
                for dx, dy, f in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        for i in range(3):
                            buf[ny][nx][i] = max(
                                0, min(255, buf[ny][nx][i] + err[i] * f)
                            )
            else:
                chosen = nearest(src, palette)
            alpha = pixels[y][x][3]
            row.append((chosen[0], chosen[1], chosen[2], alpha))
        out.append(row)
    return out


# --------------------------------------------------------------------------
# Sprites
# --------------------------------------------------------------------------


@dataclass
class Sprite:
    width: int
    height: int
    pixels: list[list[RGBA]]

    def save(self, path: str) -> None:
        write_png(path, self.width, self.height, self.pixels)

    def scaled(self, factor: int) -> "Sprite":
        if factor < 1:
            raise ValueError("factor must be >= 1")
        rows = []
        for row in self.pixels:
            new_row = []
            for pixel in row:
                new_row.extend([pixel] * factor)
            for _ in range(factor):
                rows.append(list(new_row))
        return Sprite(self.width * factor, self.height * factor, rows)

    def flip(self) -> "Sprite":
        return Sprite(
            self.width, self.height, [list(reversed(row)) for row in self.pixels]
        )

    def outline(self, colour: RGB, diagonal: bool = False) -> "Sprite":
        """Add a 1px outline around every opaque region.

        1px dark outline is the single highest-impact trick in pixel art: it
        separates the sprite from any background, and it is what makes small
        sprites read at 1x.
        """
        h, w = self.height, self.width
        out = [list(row) for row in self.pixels]
        offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diagonal:
            offsets += [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        for y in range(h):
            for x in range(w):
                if self.pixels[y][x][3] == 0:
                    continue
                for dx, dy in offsets:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and self.pixels[ny][nx][3] == 0:
                        out[ny][nx] = (colour[0], colour[1], colour[2], 255)
        return Sprite(w, h, out)

    def palette_colours(self) -> list[RGB]:
        seen: dict[RGB, int] = {}
        for row in self.pixels:
            for r, g, b, a in row:
                if a:
                    seen[(r, g, b)] = seen.get((r, g, b), 0) + 1
        return [c for c, _ in sorted(seen.items(), key=lambda kv: -kv[1])]


def from_ascii(rows: list[str], mapping: dict[str, RGBA | None]) -> Sprite:
    """Build a sprite from text.

    ``"."`` is transparent by convention. This is the most legible way for a
    human or an agent to author a sprite, and it keeps the design reviewable in
    a diff.
    """
    if not rows:
        raise ValueError("no rows")
    width = len(rows[0])
    grid: list[list[RGBA]] = []
    for y, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"row {y} has length {len(row)}, expected {width}")
        out_row: list[RGBA] = []
        for ch in row:
            if ch == ".":
                out_row.append((0, 0, 0, 0))
                continue
            if ch not in mapping:
                raise ValueError(f"no mapping for {ch!r} in row {y}")
            value = mapping[ch]
            if value is None:
                out_row.append((0, 0, 0, 0))
            elif len(value) == 3:
                out_row.append((value[0], value[1], value[2], 255))
            else:
                out_row.append(value)  # type: ignore[arg-type]
        grid.append(out_row)
    return Sprite(width, len(rows), grid)


def to_ascii(sprite: Sprite, palette: list[RGBA] | None = None) -> str:
    """Inverse of :func:`from_ascii`, for inspecting a rendered sprite."""
    if palette is None:
        palette = list(sprite.palette_colours())
        palette = [(r, g, b, 255) for r, g, b in palette]
    glyphs = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lines = []
    for row in sprite.pixels:
        line = []
        for pixel in row:
            if pixel[3] == 0:
                line.append(".")
                continue
            idx = min(
                range(len(palette)),
                key=lambda i: _dist(pixel[:3], palette[i][:3]),
            )
            line.append(glyphs[idx % len(glyphs)])
        lines.append("".join(line))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Sheets
# --------------------------------------------------------------------------


def sheet(sprites: list[Sprite], columns: int | None = None) -> Sprite:
    """Pack sprites into a grid sheet (row-major, uniform cell size)."""
    if not sprites:
        raise ValueError("no sprites")
    cw = max(s.width for s in sprites)
    ch = max(s.height for s in sprites)
    cols = columns or len(sprites)
    rows = (len(sprites) + cols - 1) // cols
    width, height = cols * cw, rows * ch
    canvas = [[(0, 0, 0, 0)] * width for _ in range(height)]

    for index, sprite in enumerate(sprites):
        ox = (index % cols) * cw
        oy = (index // cols) * ch
        for y in range(sprite.height):
            for x in range(sprite.width):
                canvas[oy + y][ox + x] = sprite.pixels[y][x]
    return Sprite(width, height, canvas)
