from __future__ import annotations

import os
import tempfile

import pytest

import pixelkit as pk


def test_png_roundtrip_rgba():
    pixels = [
        [(255, 0, 0, 255), (0, 255, 0, 128)],
        [(0, 0, 255, 255), (0, 0, 0, 0)],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "t.png")
        pk.write_png(path, 2, 2, pixels)
        w, h, back = pk.read_png(path)
    assert (w, h) == (2, 2)
    assert back == pixels


def test_png_roundtrip_larger():
    import random

    rng = random.Random(0)
    pixels = [
        [(rng.randrange(256), rng.randrange(256), rng.randrange(256), rng.choice([0, 255]))
         for _ in range(17)]
        for _ in range(13)
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "t.png")
        pk.write_png(path, 17, 13, pixels)
        w, h, back = pk.read_png(path)
    assert (w, h) == (17, 13)
    assert back == pixels


def test_write_png_rejects_bad_shape():
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError):
            pk.write_png(os.path.join(tmp, "x.png"), 2, 2, [[(0, 0, 0, 255)]])


def test_hex_roundtrip():
    assert pk.hex_to_rgb("#4fc3f7") == (79, 195, 247)
    assert pk.rgb_to_hex((79, 195, 247)) == "#4fc3f7"
    assert pk.hex_to_rgb("#fff") == (255, 255, 255)


def test_ramp_is_monotonic_and_hued():
    ramp = pk.ramp("#4fc3f7", steps=5)
    assert len(ramp) == 5
    lums = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in ramp]
    assert lums == sorted(lums, reverse=True)


def test_from_ascii_and_back():
    art = ["..x..", ".xxx.", "xxxxx"]
    sprite = pk.from_ascii(art, {"x": (255, 0, 0)})
    assert sprite.width == 5 and sprite.height == 3
    assert sprite.pixels[0][0][3] == 0
    text = pk.to_ascii(sprite)
    assert text.splitlines()[2] == "00000"


def test_from_ascii_rejects_ragged_rows():
    with pytest.raises(ValueError):
        pk.from_ascii(["..x", ".xx."], {"x": (255, 0, 0)})


def test_outline_rings_the_shape():
    art = ["..x..", ".xxx.", "xxxxx"]
    sprite = pk.from_ascii(art, {"x": (255, 0, 0)}).outline((0, 0, 0))
    assert sprite.pixels[0][1][3] == 255           # edge filled by outline
    assert sprite.pixels[0][0][3] == 0             # diagonal-only corner left alone
    assert sprite.pixels[0][2][:3] == (255, 0, 0)  # core untouched


def test_outline_diagonal_fills_corners():
    art = ["..x..", ".xxx.", "xxxxx"]
    sprite = pk.from_ascii(art, {"x": (255, 0, 0)}).outline((0, 0, 0), diagonal=True)
    assert sprite.pixels[0][0][3] == 255


def test_scaled_is_nearest_neighbour():
    sprite = pk.from_ascii(["ab"], {"a": (1, 2, 3), "b": (4, 5, 6)})
    big = sprite.scaled(3)
    assert (big.width, big.height) == (6, 3)
    assert big.pixels[0][0] == big.pixels[0][2] == (1, 2, 3, 255)
    assert big.pixels[0][3] == (4, 5, 6, 255)


def test_flip():
    sprite = pk.from_ascii(["ab"], {"a": (1, 2, 3), "b": (4, 5, 6)})
    assert sprite.flip().pixels[0][0][:3] == (4, 5, 6)


def test_sheet_layout():
    a = pk.from_ascii(["xx", "xx"], {"x": (255, 0, 0)})
    b = pk.from_ascii(["y"], {"y": (0, 255, 0)})
    s = pk.sheet([a, b], columns=2)
    assert s.width == 4 and s.height == 2
    assert s.pixels[0][2][:3] == (0, 255, 0)


def test_quantize_is_deterministic():
    sprite = pk.from_ascii(["xyz"], {"x": (10, 20, 30), "y": (200, 100, 50), "z": (0, 0, 0)})
    palette = [(0, 0, 0), (255, 255, 255)]
    a = pk.quantize(sprite.pixels, palette, dither="bayer")
    b = pk.quantize(sprite.pixels, palette, dither="bayer")
    assert a == b
    assert all(p[:3] in palette for p in a[0])


def test_palette_colours_sorted_by_frequency():
    sprite = pk.from_ascii(["xyy"], {"x": (1, 1, 1), "y": (2, 2, 2)})
    assert sprite.palette_colours()[0] == (2, 2, 2)
