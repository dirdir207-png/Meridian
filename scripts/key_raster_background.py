"""Key a generated raster's flat dark background to alpha.

Generated masters arrive opaque, with the subject drawn on a flat dark field, which cannot sit on
the Observatory's indigo and parchment surfaces. This derives alpha from luminance so one asset
serves both themes, and reports the alpha coverage that `ASSET_MANIFEST.md` records for shipped
rasters (`accounts-ticket-building.png` states its transparent fraction and corner pixels).

The white point is the 99.5th luminance percentile rather than 255, because these services render
bright line art without reaching pure white; normalising to the observed ink keeps the lines fully
opaque instead of translucent. `--floor` kills the low-amplitude haze a render leaves on "black".

Only 8-bit non-interlaced PNGs are decoded (greyscale, RGB, and both with alpha). Anything else
fails loud rather than guessing, and a master whose background is not mostly dark is REFUSED: keying
it would produce a near-opaque rectangle, which is the failure this guards against. `--crop-pad`
then trims the transparent margin a model leaves around a centred subject.
"""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path

_CHANNELS_BY_COLOR_TYPE = {0: 1, 2: 3, 4: 2, 6: 4}
_MODE_BY_COLOR_TYPE = {0: "L", 2: "RGB", 4: "LA", 6: "RGBA"}
_CHANNELS_BY_MODE = {"L": 1, "RGB": 3, "LA": 2, "RGBA": 4}


def _chunk(tag: bytes, body: bytes) -> bytes:
    return (
        struct.pack(">I", len(body))
        + tag
        + body
        + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    )


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _unfilter(filter_type: int, line: bytearray, previous: bytearray, bpp: int) -> None:
    """Reverse one PNG scanline filter in place; `previous` is the already-reconstructed line."""
    if filter_type == 0:
        return
    for i in range(len(line)):
        a = line[i - bpp] if i >= bpp else 0
        b = previous[i]
        c = previous[i - bpp] if i >= bpp else 0
        if filter_type == 1:
            delta = a
        elif filter_type == 2:
            delta = b
        elif filter_type == 3:
            delta = (a + b) >> 1
        elif filter_type == 4:
            delta = _paeth(a, b, c)
        else:
            raise ValueError(f"unknown PNG filter type {filter_type}")
        line[i] = (line[i] + delta) & 0xFF


def read_png(path: Path) -> tuple[int, int, str, bytes]:
    """Decode a PNG into `(width, height, mode, pixels)` with raw 8-bit samples."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    position = 8
    header = None
    compressed = bytearray()
    while position < len(data):
        (length,) = struct.unpack(">I", data[position : position + 4])
        tag = data[position + 4 : position + 8]
        body = data[position + 8 : position + 8 + length]
        position += 12 + length
        if tag == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            compressed += body
        elif tag == b"IEND":
            break
    if header is None:
        raise ValueError(f"{path} has no IHDR chunk")
    width, height, depth, color_type, _compression, _filter, interlace = header
    if depth != 8 or color_type not in _CHANNELS_BY_COLOR_TYPE or interlace != 0:
        raise ValueError(
            f"{path} is not an 8-bit non-interlaced PNG "
            f"(depth={depth}, color_type={color_type}, interlace={interlace})"
        )
    channels = _CHANNELS_BY_COLOR_TYPE[color_type]
    stride = width * channels
    raw = zlib.decompress(bytes(compressed))
    if len(raw) != (stride + 1) * height:
        raise ValueError(f"{path} IDAT holds {len(raw)} bytes, expected {(stride + 1) * height}")
    pixels = bytearray(stride * height)
    previous = bytearray(stride)
    source = 0
    for y in range(height):
        filter_type = raw[source]
        source += 1
        line = bytearray(raw[source : source + stride])
        source += stride
        _unfilter(filter_type, line, previous, channels)
        pixels[y * stride : (y + 1) * stride] = line
        previous = line
    return width, height, _MODE_BY_COLOR_TYPE[color_type], bytes(pixels)


def write_rgba_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    """Write 8-bit RGBA samples as a non-interlaced PNG."""
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride : (y + 1) * stride]
    body = b"".join(
        (
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)),
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)),
            _chunk(b"IEND", b""),
        )
    )
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + body)


def alpha_report(width: int, height: int, rgba: bytes) -> dict:
    """Report the alpha facts a design record carries: coverage, corner pixels and visible bounds.

    `corners` is ordered top-left, top-right, bottom-right, bottom-left. `visible_bounds` is the
    half-open box `[left, top, right, bottom]` around every pixel with a non-zero alpha.
    """
    total = width * height
    transparent = 0
    left, top, right, bottom = width, height, 0, 0
    for index in range(total):
        alpha = rgba[index * 4 + 3]
        if alpha == 0:
            transparent += 1
            continue
        x, y = index % width, index // width
        left, top = min(left, x), min(top, y)
        right, bottom = max(right, x + 1), max(bottom, y + 1)
    corner_indexes = (0, width - 1, total - 1, total - width)
    return {
        "mode": "RGBA",
        "dimensions": [width, height],
        "transparent_fraction": round(transparent / total, 4),
        "corners": [list(rgba[i * 4 : i * 4 + 4]) for i in corner_indexes],
        "visible_bounds": [left, top, right, bottom] if right else [0, 0, 0, 0],
    }


def crop_to_bounds(
    width: int, height: int, rgba: bytes, bounds: list[int], pad: int
) -> tuple[int, int, bytes]:
    """Trim to `bounds` expanded by `pad`, clamped to the image, keeping the box half-open."""
    left = max(0, bounds[0] - pad)
    top = max(0, bounds[1] - pad)
    right = min(width, bounds[2] + pad)
    bottom = min(height, bounds[3] + pad)
    new_width, new_height = right - left, bottom - top
    cropped = bytearray(new_width * new_height * 4)
    for y in range(new_height):
        start = ((top + y) * width + left) * 4
        cropped[y * new_width * 4 : (y + 1) * new_width * 4] = rgba[start : start + new_width * 4]
    return new_width, new_height, bytes(cropped)


def key_flat_background(
    src: Path,
    dst: Path,
    *,
    floor: int = 16,
    min_transparent_fraction: float = 0.2,
    crop_pad: int | None = None,
) -> dict:
    """Derive alpha from luminance and write the result to `dst`.

    `crop_pad` trims the result to the ink plus that many pixels of margin; a tall subject centred
    in a wide frame otherwise wastes its layout box. The background guard runs BEFORE the crop,
    because cropping removes exactly the transparent margin that guard measures.

    Raises `ValueError` when the source background is not mostly dark, because keying such a master
    would emit a near-opaque rectangle rather than an ornament.
    """
    width, height, mode, pixels = read_png(src)
    channels = _CHANNELS_BY_MODE[mode]
    total = width * height

    luminance = []
    for index in range(total):
        sample = index * channels
        if channels >= 3:
            red, green, blue = pixels[sample], pixels[sample + 1], pixels[sample + 2]
        else:
            red = green = blue = pixels[sample]
        luminance.append((2126 * red + 7152 * green + 722 * blue) // 10000)

    ordered = sorted(luminance)
    white_point = ordered[min(total - 1, int(0.995 * (total - 1)))]
    if white_point <= floor:
        raise ValueError(
            f"{src} is not a flat dark background: its 99.5th luminance percentile is "
            f"{white_point}, at or below the floor {floor}"
        )

    span = white_point - floor
    rgba = bytearray(total * 4)
    for index in range(total):
        sample = index * channels
        lum = luminance[index]
        alpha = 0 if lum <= floor else min(255, (lum - floor) * 255 // span)
        if channels >= 3:
            rgba[index * 4] = pixels[sample]
            rgba[index * 4 + 1] = pixels[sample + 1]
            rgba[index * 4 + 2] = pixels[sample + 2]
        else:
            rgba[index * 4] = rgba[index * 4 + 1] = rgba[index * 4 + 2] = pixels[sample]
        if channels in (2, 4):
            alpha = alpha * pixels[sample + channels - 1] // 255
        rgba[index * 4 + 3] = alpha

    report = alpha_report(width, height, bytes(rgba))
    if report["transparent_fraction"] < min_transparent_fraction:
        raise ValueError(
            f"{src} is not a flat dark background: only {report['transparent_fraction']:.1%} of "
            f"pixels key to transparent, below the required {min_transparent_fraction:.0%}"
        )

    if crop_pad is not None:
        width, height, rgba = crop_to_bounds(
            width, height, bytes(rgba), report["visible_bounds"], crop_pad
        )
        report = alpha_report(width, height, rgba)

    write_rgba_png(dst, width, height, rgba)
    report["source"] = str(src)
    report["floor"] = floor
    report["white_point"] = white_point
    if crop_pad is not None:
        report["crop_pad"] = crop_pad
    return report


def main(argv: list[str] | None = None) -> int:
    """Key one master and print its alpha report as JSON."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--floor", type=int, default=16)
    parser.add_argument("--min-transparent-fraction", type=float, default=0.2)
    parser.add_argument(
        "--crop-pad",
        type=int,
        default=None,
        help="trim to the visible ink plus this many pixels of margin",
    )
    args = parser.parse_args(argv)
    report = key_flat_background(
        args.source,
        args.destination,
        floor=args.floor,
        min_transparent_fraction=args.min_transparent_fraction,
        crop_pad=args.crop_pad,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
