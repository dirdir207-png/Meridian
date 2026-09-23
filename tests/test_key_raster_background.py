"""`scripts/key_raster_background.py` turns an opaque generated master into an RGBA ornament.

Generated rasters come back on a flat dark background, which is unusable on the Observatory's
indigo and parchment surfaces. The tool derives alpha from luminance so one asset can sit on
either theme, and reports the alpha coverage that `ASSET_MANIFEST.md` documents for shipped
rasters (`accounts-ticket-building.png` records its transparent fraction and corner pixels).

The decoder is checked against a SHIPPED asset, not only against this file's own encoder, so a
codec bug cannot pass by agreeing with itself.
"""

import struct
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import key_raster_background as keyer  # noqa: E402


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _rgb_png(width: int, height: int, rows: list[bytes]) -> bytes:
    """Encode rows of raw RGB into a PNG. Independent of the tool's own encoder."""
    raw = b"".join(b"\x00" + row for row in rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )


def _subject_on_black(size: int = 8) -> bytes:
    black = bytes([0, 0, 0]) * size
    rows = [black] * size
    for y in (3, 4):
        rows[y] = black[: 3 * 3] + bytes([255, 200, 120]) * 2 + black[: 3 * 3]
    return _rgb_png(size, size, rows)


def test_decodes_a_shipped_raster(tmp_path: Path):
    """Ground truth outside this test's own encoder: a real asset from the repository."""
    shipped = ROOT / "static/img/meridian/observatory/dial-plate.png"
    width, height, mode, _pixels = keyer.read_png(shipped)
    assert (width, height) == (1254, 1254)
    assert mode == "RGB"


def test_flat_background_becomes_transparent_and_the_subject_survives(tmp_path: Path):
    src = tmp_path / "master.png"
    src.write_bytes(_subject_on_black())
    dst = tmp_path / "keyed.png"

    stats = keyer.key_flat_background(src, dst, floor=16)

    width, height, mode, rgba = keyer.read_png(dst)
    assert mode == "RGBA"
    assert (width, height) == (8, 8)
    assert rgba[3] == 0, "the flat black corner must be fully transparent"
    centre = (4 * width + 3) * 4
    assert rgba[centre + 3] == 255, "the bright subject must survive keying"
    assert stats["transparent_fraction"] > 0.5


def test_reports_the_alpha_facts_the_manifest_records(tmp_path: Path):
    src = tmp_path / "master.png"
    src.write_bytes(_subject_on_black())
    dst = tmp_path / "keyed.png"

    stats = keyer.key_flat_background(src, dst, floor=16)

    assert stats["mode"] == "RGBA"
    assert stats["dimensions"] == [8, 8]
    assert stats["corners"] == [[0, 0, 0, 0]] * 4
    assert stats["visible_bounds"] == [3, 3, 5, 5]


def test_cropping_trims_the_empty_margin_the_model_leaves(tmp_path: Path):
    """A tall subject centred in a wide frame wastes the layout box; crop it to the ink."""
    src = tmp_path / "master.png"
    src.write_bytes(_subject_on_black())
    dst = tmp_path / "keyed.png"

    stats = keyer.key_flat_background(src, dst, floor=16, crop_pad=1)

    width, height, _mode, rgba = keyer.read_png(dst)
    assert (width, height) == (4, 4), "subject at x/y 3..4 with one pixel of pad is a 4x4 box"
    assert stats["dimensions"] == [4, 4]
    assert rgba[3] == 0, "the padded corner is background, so it must stay transparent"
    assert rgba[(1 * width + 1) * 4 + 3] == 255, "the subject must survive the crop"


def test_a_master_without_a_flat_dark_background_fails_loud(tmp_path: Path):
    """A bright background would key to a near-opaque rectangle. Refuse it, do not ship it."""
    src = tmp_path / "master.png"
    src.write_bytes(_rgb_png(8, 8, [bytes([250, 250, 250]) * 8] * 8))

    with pytest.raises(ValueError, match="not a flat dark background"):
        keyer.key_flat_background(src, tmp_path / "keyed.png", floor=16)
