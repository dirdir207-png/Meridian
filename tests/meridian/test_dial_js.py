"""Observatory slice: shared visual layer and accessible dial scaffolding.

These are static source-presence tests; the pure geometry helpers are also
syntax-checked through the module import when a JS runtime is available in the
environment (the browser and Node paths exercise them separately).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

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


def test_dial_js_pure_geometry_round_trips_with_node():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const dial = await import('./static/js/meridian/dial.js');
      const { civilDaysBetween, dayToAngle, angleToDay, addDays } = dial;
      const close = (a, b) => Math.abs(a - b) < 1e-9;
      if (civilDaysBetween('2026-03-08', '2026-03-09') !== 1) throw new Error('DST civil-day mismatch');
      if (civilDaysBetween('2026-09-08', '2026-09-08') !== 0) throw new Error('same-day mismatch');
      if (civilDaysBetween('2024-02-28', '2024-03-01') !== 2) throw new Error('leap-day mismatch');
      if (!close(dayToAngle(0, 14), -120)) throw new Error('arc start');
      if (!close(dayToAngle(14, 14), 120)) throw new Error('arc end');
      if (angleToDay(dayToAngle(7, 14), 14) !== 7) throw new Error('angle->day round trip');
      if (angleToDay(-120, 1) !== 0 || angleToDay(120, 1) !== 1) throw new Error('N=1 endpoints');
      if (addDays('2025-12-31', 1) !== '2026-01-01') throw new Error('year rollover');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_dial_js_exports_pure_geometry_helpers():
    js = _read("static/js/meridian/dial.js")
    assert "export function civilDaysBetween" in js
    assert "export function dayToAngle" in js
    assert "export function angleToDay" in js
    assert "export function positionOnArc" in js
    assert "export function renderDial" in js


def test_dial_js_hides_decorative_svg_and_supplies_accessibility_valuetext():
    js = _read("static/js/meridian/dial.js")
    assert 'setAttribute("aria-hidden", "true")' in js
    assert "describeSelectedDay" in js
    assert 'aria-valuetext", describeSelectedDay' in js


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


def test_meridian_app_opt_into_observatory_shell():
    index = _read("templates/meridian/index.html")
    settings = _read("templates/meridian/settings.html")
    css = _read("static/css/meridian/observatory.css")
    assert '<body class="obs-shell">' in index
    assert '<body class="obs-shell">' in settings
    assert 'static/css/meridian/observatory.css' in settings
    assert '.obs-shell .m-nav-item[aria-current="page"]::before' in css
    assert 'mix-blend-mode: screen' in css


def test_observatory_shell_transparency_shows_app_backdrop():
    css = _read("static/css/meridian/observatory.css")
    assert ".obs-shell [data-meridian-shell]" in css
    assert "background: transparent" in css


def test_login_observatory_treatment_preserves_auth_controls():
    login = _read("templates/login.html")
    assert '<body class="obs-shell">' in login
    assert "Meridian - Login" in login
    assert "static/css/meridian/observatory.css" in login
    # The Observatory restyle must not remove the existing authentication
    # controls or their server routes.
    assert 'id="passkeyLoginSection"' in login
    assert 'id="passkeyLoginBtn"' in login
    assert 'id="showPasswordLoginBtn"' in login
    assert 'id="passwordLoginForm"' in login
    assert 'id="loginForm"' in login
    assert "/api/auth/passkeys/available" in login
    assert "/api/auth/login" in login
    assert "/api/auth/webauthn/authenticate/options" in login
    assert "/api/auth/webauthn/authenticate/verify" in login


def test_asset_manifest_lists_observatory_assets():
    manifest = _read("static/img/meridian/observatory/ASSET_MANIFEST.md")
    assert "dial-ornament.svg" in manifest
    assert "observatory-engraving.svg" in manifest
