import pytest

from tests.browser.capture_contract import (
    CAPTURE_MATRIX,
    CaptureMetadata,
    required_matrix,
    validate_metadata,
)


def metadata(**overrides):
    values = dict(concept_path="design/current.png", current_path="capture.png", viewport="mobile-small",
                  theme="dark", fixture="preview-v1", frozen_clock="2026-09-10T12:00:00Z",
                  ui_state="today-selected-default", full_page=True, commit="abc1234",
                  captured_at="2026-09-10T12:01:00Z", dpr=3)
    values.update(overrides)
    return values


def test_matrix_matches_governing_four_viewports_and_two_themes():
    assert len(required_matrix()) == 8
    assert CAPTURE_MATRIX["desktop"] == {"width": 1440, "height": 900, "dpr": 1}
    assert CAPTURE_MATRIX["mobile-small"]["dpr"] == 3


def test_metadata_requires_all_determinism_fields():
    validate_metadata(metadata())
    with pytest.raises(ValueError, match="missing"):
        validate_metadata({"viewport": "desktop"})


def test_metadata_rejects_wrong_dpr_and_theme():
    with pytest.raises(ValueError, match="DPR"):
        validate_metadata(metadata(viewport="desktop", dpr=3))
    with pytest.raises(ValueError, match="theme"):
        validate_metadata(metadata(theme="system"))


def test_metadata_serializes_as_json_safe_dict():
    result = CaptureMetadata(**metadata()).to_dict()
    assert result["full_page"] is True
    assert result["viewport"] == "mobile-small"


def test_capture_script_uses_full_matrix_dpr_theme_and_manifest():
    source = __import__("pathlib").Path("scripts/capture_meridian_matrix.py").read_text()
    assert "for viewport_name, viewport in CAPTURE_MATRIX.items()" in source
    assert "for theme in THEMES" in source
    assert 'device_scale_factor=viewport["dpr"]' in source
    assert "color_scheme=theme" in source
    assert 'reduced_motion="reduce"' in source
    assert "manifest.write_text" in source
    assert "validate_metadata(metadata)" in source
