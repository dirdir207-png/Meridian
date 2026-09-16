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


def test_dial_formats_observed_timestamps_human_readably():
    js = _read("static/js/meridian/dial.js")
    assert "function formatObservedAt" in js
    assert "Intl.DateTimeFormat" in js
    # The ticket must use the human formatter, not the raw ISO string.
    assert "formatObservedAt(observed)" in js



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


def test_today_observatory_dial_is_primary_before_forecast_hero():
    today = _read("templates/meridian/partials/today.html")
    assert today.count("data-observatory-dial") >= 1
    # The compact safe-to-spend strip sits above the dial, matching the
    # Observatory information hierarchy.
    assert today.index("data-today-safe") < today.index("data-observatory-dial-wrap")
    assert today.index("data-observatory-dial-wrap") < today.index("data-today-hero")
    # The dial should be rendered once, inside the primary Today column.
    assert today.index("data-observatory-dial-wrap") < today.index("data-today-brief")



def test_asset_manifest_lists_observatory_assets():
    manifest = _read("static/img/meridian/observatory/ASSET_MANIFEST.md")
    css = _read("static/css/meridian/observatory.css")
    assert "dial-ornament.svg" in manifest
    assert "observatory-engraving.svg" in manifest
    assert "paper-texture.webp" in manifest
    assert "ink-texture.webp" in manifest
    assert "paper-texture.webp" in css
    assert "ink-texture.webp" in css


def test_dial_instrument_matches_concept_layers():
    js = _read("static/js/meridian/dial.js")
    css = _read("static/css/meridian/dial.css")
    assert "renderInstrumentOverlay" in js
    assert "dial-plate.png" in css
    assert (ROOT / "static/img/meridian/observatory/dial-plate.png").is_file()
    assert "obs-dial-center" in js
    assert "obs-dial-day-labels" in js
    assert ".obs-dial-face" in css
    assert ".obs-dial-center" in css
    assert ".obs-dial-day-label" in css


def test_dial_event_rail_lists_all_upcoming_events():
    js = _read("static/js/meridian/dial.js")
    css = _read("static/css/meridian/dial.css")
    assert "Upcoming money moments" in js
    assert "event.date >= state.model.today" in js
    assert ".obs-event-date" in css


def test_today_explore_plan_cta_follows_dial():
    html = _read("templates/meridian/partials/today.html")
    css = _read("static/css/meridian/dial.css")
    assert "Explore my plan" in html
    assert "obs-explore-plan" in css
    assert "href=\"/meridian?workspace=plan\"" in html


def test_dial_interaction_handlers_receive_container():
    js = _read("static/js/meridian/dial.js")
    assert "function renderDialSVG(state, container)" in js
    assert "function renderEventList(state, container)" in js
    assert "update(state, container);" in js


def test_dial_markers_have_orbit_leader_lines():
    js = _read("static/js/meridian/dial.js")
    css = _read("static/css/meridian/dial.css")
    assert "obs-dial-leader" in js
    assert "stroke-dasharray: 3 4" in css


def test_dial_selects_first_upcoming_event_by_default():
    js = _read("static/js/meridian/dial.js")
    assert "const initialEvent" in js
    assert "selectedEventId: initialEvent" in js
    assert 'mode: initialEvent ? "explore" : "today"' in js


def test_observatory_today_stage_gets_full_width_on_desktop():
    css = _read("static/css/meridian/observatory.css")
    assert "@media (min-width: 1101px)" in css
    assert ".obs-shell .m-today-layout" in css
    assert "grid-template-columns: minmax(0, 1fr)" in css


def test_today_safe_to_spend_shows_real_observation_stamp():
    html = _read("templates/meridian/partials/today.html")
    js = _read("static/js/meridian/today.js")
    css = _read("static/css/meridian/today.css")
    assert "data-sts-observed" in html
    assert "Crew · observed" in js
    assert "m-observatory-safe-observed" in css


def test_today_command_copy_matches_observatory_direction():
    html = _read("templates/meridian/partials/today.html")
    # The owner selected the concept with prominent spendable/horizon first;
    # the workspace's accessible Today heading remains in the shell template.
    assert 'data-sts-label>Safe to spend</dt>' in html
    assert "data-sts-horizon" in html
    assert 'class="obs-today-orbit" data-editorial-headline' in html
    assert html.index("data-today-safe") < html.index("data-observatory-dial-wrap")


def test_dial_event_glyphs_come_from_the_kit_and_are_resolved_semantically():
    """The kit README distinguishes electricity from Internet and maps the rest of
    the semantic set. A kind-only glyph repeats one badge across unrelated bills, and
    the legacy icon directory has no wifi/bank/house glyph to resolve to."""
    js = _read("static/js/meridian/dial.js")
    assert "export function eventIconName" in js
    assert "/static/img/meridian/observatory/kit-2026-09-16/icons/" in js
    assert "/static/img/meridian/observatory/icons/" not in js


def test_dial_event_glyph_mapping_holds_under_node():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const { eventIconName } = await import('./static/js/meridian/dial.js');
      const cases = [
        [{ kind: 'bill', title: 'Electric' }, 'lightning-charge'],
        [{ kind: 'bill', title: 'Internet' }, 'wifi'],
        [{ kind: 'bill', title: 'Rent' }, 'house'],
        [{ kind: 'bill', title: 'Groceries' }, 'basket'],
        [{ kind: 'bill', title: 'Bus pass' }, 'bus-front'],
        [{ kind: 'bill', title: 'Streaming subscription' }, 'controller'],
        [{ kind: 'bill', title: 'Bill reserve' }, 'bank'],
        [{ kind: 'income', title: 'Paycheck' }, 'star'],
        [{ kind: 'goal', title: 'Japan trip' }, 'flag'],
        [{ kind: 'transfer', title: 'Move to savings' }, 'arrow-right'],
        [{ kind: 'bill', title: 'Zzz unrecognised' }, 'lightning-charge'],
        [{ kind: undefined, title: undefined }, 'lightning-charge'],
      ];
      for (const [event, expected] of cases) {
        const got = eventIconName(event);
        if (got !== expected) {
          throw new Error(`${JSON.stringify(event)}: expected ${expected}, got ${got}`);
        }
      }
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_dial_pointer_is_prominent_and_keeps_a_mint_selection_cue():
    """Handoff item 3: the pointer exists but its prominence needs work. It must read
    as a needle with a bright rimmed tip, not as another engraved tick."""
    css = _read("static/css/meridian/dial.css")
    js = _read("static/js/meridian/dial.js")
    assert "stroke: #a5d4bf; stroke-width: 7" in css
    assert "stroke-linecap: round" in css
    assert "r: 13px" in css
    # The tip keeps a brass rim so it separates from the parchment ring beneath it.
    assert "stroke: #c6aa71" in css
    # The needle reaches further inward, so it reads as a pointer across the ring.
    assert "positionOnArc(VIEWBOX.cx, VIEWBOX.cy, 118, pointerAngle)" in js


def test_dial_pointer_runs_stay_clear_of_the_centre_readout():
    """Lengthening the needle must not drive it under the selected amount text."""
    js = _read("static/js/meridian/dial.js")
    assert "const pointerStart = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, 118, pointerAngle);" in js
    # The centre readout is a separate HTML overlay; the SVG needle stays outside it.
    assert "VIEWBOX.r - 84, pointerAngle" in js


def test_dial_event_badges_weight_the_rim_with_brass_and_rivets():
    """Kit nuance: a coloured disk, a double brass rim and rivets. A plain navy
    double border loses the brass weight the concept uses on every badge."""
    css = _read("static/css/meridian/dial.css")
    # The heavy navy double border and the thin brass outline it replaced are gone.
    assert "3px double" not in css
    assert "outline: 1px solid #c6aa71" not in css
    # Brass band plus a double navy hairline now defines the rim.
    assert "border: 2px solid #c6aa71" in css
    assert "inset 0 0 0 1px #20263b, inset 0 0 0 2px #c6aa71" in css
    assert ".obs-event-list--orbit .obs-event-kind::before" in css
    assert ".obs-event-list--orbit .obs-event-kind::after" in css


def test_mobile_callout_column_fits_ordinary_words():
    """Diagnosed callout defect at ≤700px: the title spans the whole rail column, so the
    rail width *is* the title's measure. At 116px the column left 110px while the word
    "arrangement" measures 112.7px at 17px serif, so `overflow-wrap: break-word` split an
    ordinary word across two lines. The rail now leaves room at 16px instead."""
    css = _read("static/css/meridian/dial.css")
    assert "grid-template-columns: minmax(0, 1fr) 130px" in css
    assert (
        ".obs-event-list--orbit .obs-event-title { font-size: 16px; "
        "grid-column: 1 / -1; overflow-wrap: break-word; }" in css
    )
    assert "minmax(0, 1fr) 116px" not in css
