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


def _navy_scene(size: int = 12) -> bytes:
    """A field whose colour the SUBJECT also contains -- the case colour keying exists for.

    The field is navy (15,26,42). The subject is a dark patch only ~19 units away from it (the
    moon's unlit limb, which is the same navy), plus a bright patch. A luminance key cannot
    separate the dark patch from the field; a colour key can.
    """
    field = bytes([15, 26, 42])
    rows = [field * size for _ in range(size)]
    dark = bytes([29, 39, 46])      # distance ~19.5 from the field: must survive
    bright = bytes([235, 225, 190])  # the lit crescent: must survive
    rows[4] = field * 2 + dark * 4 + field * (size - 6)
    rows[6] = field * 2 + bright * 4 + field * (size - 6)
    return _rgb_png(size, size, rows)


def test_colour_key_keeps_a_subject_that_contains_the_field_colour(tmp_path: Path):
    """The reason the colour strategy exists, pinned as a test rather than as a comment.

    `moon-engraving.png` is a line-art scene whose flat navy field ALSO fills the moon's unlit
    limb, with the cratered interior only ~19 RGB units away. Luminance keying at any floor that
    removes the field also removes the moon's centre, so luminance and colour are asserted to
    behave DIFFERENTLY on the same input -- which is what makes this a real capability rather
    than a second name for the first one.
    """
    source = tmp_path / "scene.png"
    source.write_bytes(_navy_scene())
    destination = tmp_path / "scene-keyed.png"

    report = keyer.key_flat_colour_background(source, destination, tolerance=12)
    width, height, mode, pixels = keyer.read_png(destination)
    assert mode == "RGBA"
    assert width == 12 and height == 12

    alpha = lambda x, y: pixels[(y * width + x) * 4 + 3]  # noqa: E731
    assert alpha(0, 0) == 0, "the flat field must clear"
    assert alpha(5, 4) == 255, "a subject tone ~19 units from the field must stay opaque"
    assert alpha(5, 6) == 255, "the lit part must stay opaque"
    assert report["transparent_fraction"] > 0.5
    assert report["strategy"] == "colour"
    assert report["reference_colour"] == [15, 26, 42], "read from the frame's corners"

    # The same input through the luminance strategy loses the subject -- measured, rather than
    # asserted as an exception. At a floor that clears the field (30, above the field's own
    # luminance of ~24.8), the dark patch is NOT zeroed: it survives at a few percent alpha,
    # because the luminance key ramps alpha across the 30..white_point span. That is worse than
    # crisp removal for this asset -- the moon's limb would be a ghost -- and it is why the
    # strategy had to be colour distance rather than a retuned floor.
    luminance_target = tmp_path / "scene-luminance.png"
    keyer.key_flat_background(source, luminance_target, floor=30)
    lw, lh, _, lpixels = keyer.read_png(luminance_target)
    luminance_alpha = lpixels[((4 * lw) + 5) * 4 + 3]
    assert luminance_alpha < 40, (
        "the luminance key is expected to leave the dark patch nearly invisible, which is the "
        f"defect this strategy avoids; measured alpha {luminance_alpha}"
    )
    assert alpha(5, 4) == 255, "the colour key keeps the same patch fully opaque"


def test_colour_key_refuses_a_frame_that_is_not_mostly_field(tmp_path: Path):
    """The same guard the luminance path has, for the same reason: a key that leaves a
    near-opaque rectangle is exactly the failure this tool exists to prevent."""
    # Navy CORNERS (so the reference reads as a field) over a body that is mostly NOT that
    # colour: the corner-majority reference cannot rescue it, and the fraction guard refuses.
    # A uniformly coloured frame is deliberately NOT the case here -- its corners define the
    # field, so every pixel matches and it keys cleanly, which the next assertion pins.
    size = 8
    navy = bytes([15, 26, 42])
    red = bytes([210, 90, 70])
    busy_rows = [red * size for _ in range(size)]
    # Only the four CORNER pixels are the field colour, so the corner reference reads navy while
    # the frame is overwhelmingly not navy: 4 of 64 pixels key, well below the 20% guard.
    busy_rows[0] = navy + red * (size - 2) + navy
    busy_rows[size - 1] = navy + red * (size - 2) + navy
    source = tmp_path / "busy.png"
    source.write_bytes(_rgb_png(size, size, busy_rows))
    with pytest.raises(ValueError, match="flat colour background"):
        keyer.key_flat_colour_background(source, tmp_path / "out.png", tolerance=12)

    uniform = tmp_path / "uniform.png"
    uniform.write_bytes(_rgb_png(size, size, [navy * size for _ in range(size)]))
    report = keyer.key_flat_colour_background(uniform, tmp_path / "uniform-out.png", tolerance=12)
    assert report["transparent_fraction"] == 1.0, (
        "a uniformly coloured frame IS all field: its corners define the colour, so it clears"
    )


def test_the_cli_reaches_both_strategies(tmp_path: Path):
    """The strategy is a CLI choice, so the default must stay luminance (existing callers) and
    `--strategy colour` must reach the colour path."""
    source = tmp_path / "scene.png"
    source.write_bytes(_navy_scene())
    assert keyer.main([str(source), str(tmp_path / "via-cli.png"), "--strategy", "colour"]) == 0
    _, _, mode, pixels = keyer.read_png(tmp_path / "via-cli.png")
    assert mode == "RGBA"
    assert pixels[3] == 0, "the CLI's colour path must clear the field"
