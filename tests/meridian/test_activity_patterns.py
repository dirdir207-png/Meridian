"""Observatory slice: Activity patterns are human-readable comparisons.

Patterns should expose a plain-language detail line in addition to clickable
evidence, so the owner can see what changed without decoding numeric fields.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_pattern_service_adds_plain_language_details():
    service = _read("meridian/services/activity.py")
    assert '"detail": f"Repeats about every' in service
    assert '"detail": f"Recently categorized as' in service
    assert '"detail": (' in service
    assert "Earlier half" in service


def test_pattern_ui_renders_detail_line():
    js = _read("static/js/meridian/activity.js")
    css = _read("static/css/meridian/activity.css")
    assert "m-pattern-detail" in js
    assert "pattern.detail" in js
    assert ".m-pattern-detail" in css
