"""Observatory slice: shared visual layer and accessible dial scaffolding.

These are static source-presence tests; the pure geometry helpers are also
syntax-checked through the module import when a JS runtime is available in the
environment (the browser and Node paths exercise them separately).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_observatory_css_defines_direction_tokens():
    css = _read("static/css/meridian/observatory.css")
    for token in ("--obs-bg: #172334", "--obs-ink: #eee4cf", "--obs-lilac: #c1a9e2",
                  "--obs-mint: #a5d4bf", "--obs-apricot: #f3b272", "--obs-paper: #ead8b5"):
        assert token in css


def test_dial_css_defines_instrument_surface():
    css = _read("static/css/meridian/dial.css")
    assert ".obs-dial-arc" in css
    assert ".obs-dial-track-hit" in css
    assert ".obs-dial-marker" in css
    assert ".obs-dial-pointer" in css
    assert "prefers-reduced-motion" in css or "transition-duration" in css


def test_dial_js_exports_pure_geometry_helpers():
    js = _read("static/js/meridian/dial.js")
    assert "export function civilDaysBetween" in js
    assert "export function dayToAngle" in js
    assert "export function angleToDay" in js
    assert "export function positionOnArc" in js
    assert "export function renderDial" in js


def test_dial_js_keeps_drag_and_range_accessibility_contract():
    js = _read("static/js/meridian/dial.js")
    assert "setPointerCapture" in js
    assert "pointercancel" in js
    assert "requestAnimationFrame" in js
    assert 'type = "range"' in js
    assert "aria-valuetext" in js


def test_preview_page_is_served_from_static():
    html = _read("static/meridian-observatory-preview.html")
    assert 'css/meridian/observatory.css' in html
    assert 'css/meridian/dial.css' in html
    assert './js/meridian/dial.js' in html
    assert "synthetic fixtures only" in html


def test_asset_manifest_lists_observatory_assets():
    manifest = _read("static/img/meridian/observatory/ASSET_MANIFEST.md")
    assert "dial-ornament.svg" in manifest
    assert "observatory-engraving.svg" in manifest
