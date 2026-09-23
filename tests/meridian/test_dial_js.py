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
    # --obs-bg is the measured mean of the four governing concepts (Today #161c34,
    # Plan #131830, Activity #131b30, Accounts #151c34 -> (20,27,50)). It was
    # #172334, which was lighter and greener than all four.
    for token in ("--obs-bg: #141b32", "--obs-ink: #eee4cf", "--obs-lilac: #c1a9e2",
                  "--obs-mint: #a5d4bf", "--obs-apricot: #f3b272", "--obs-paper: #ead8b5"):
        assert token in css


def test_mobile_dial_grows_on_both_sides_and_keeps_the_callout_column():
    """The dial grows symmetrically; a one-sided bleed would not have shown at all.

    With the wrap spanning `-b .. track`, the dial's right edge lands on `track`, so a
    one-sided bleed puts everything it adds into the clipped region -- 42px and 80px of
    bleed both left exactly `track` px visible. That is why the value was raised to 80px
    without making the dial look any bigger, while clipping ~20% of it.

    Enlarging the visible dial therefore requires growing it toward the right as well, and
    the left track cannot be widened to help: the callout column is a floor at 130px
    because "arrangement" measures 112.7px at 17px serif and splits mid-word below that.
    """
    css = _read("static/css/meridian/dial.css")
    # Grows on both sides: +24 total, spending the 12px column gap on each side.
    assert "calc(100% + 24px)" in css
    assert "margin: 0 0 0 -12px" in css
    # Growth past the gap put the brass ring behind "Internet"/"Reserved" and cost the
    # text its contrast, so the larger value is pinned out.
    assert "calc(100% + 56px)" not in css
    assert "margin: 0 0 0 -28px" not in css
    # The one-sided over-bleed that clipped ~20% of the dial must not return either.
    assert "calc(100% + 80px)" not in css
    assert "margin: 0 0 0 -80px" not in css
    # The callout column stays at its measured floor.
    assert "grid-template-columns: minmax(0, 1fr) 130px" in css


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
      if (!close(dayToAngle(0, 14), -100)) throw new Error('arc start');
      if (!close(dayToAngle(14, 14), 120)) throw new Error('arc end');
      if (angleToDay(dayToAngle(7, 14), 14) !== 7) throw new Error('angle->day round trip');
      if (angleToDay(-100, 1) !== 0 || angleToDay(120, 1) !== 1) throw new Error('N=1 endpoints');
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


def test_dial_js_funding_source_copy_declines_to_guess():
    """The funder is named only from an observed source; ambiguity names nobody.

    Executed, not grepped: these three outcomes are the whole honesty contract of the
    slice, and a same-looking string in the file would prove none of them.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const dial = await import('./static/js/meridian/dial.js');
      const { fundingSourceValue, fundingSourceSummary } = dial;
      const named = { fundingSource: { id: 'plan-1', name: "Veterans Home" } };
      if (fundingSourceSummary(named) !== 'Funding source: Veterans Home') throw new Error('named source');
      if (fundingSourceValue(named) !== "Veterans Home") throw new Error('named value');
      if (fundingSourceSummary({}) !== '') throw new Error('missing link must stay silent');
      if (fundingSourceSummary(null) !== '') throw new Error('no event must stay silent');
      const ambiguous = { fundingSource: null, fundingSourceAmbiguous: true,
                          fundingSourceCandidateIds: ['plan-1', 'plan-2'] };
      if (fundingSourceSummary(ambiguous) !== 'Funding source: Not determined (multiple candidates)') {
        throw new Error('ambiguity must name nobody');
      }
      // A source with no provider record id is not citable and must not be shown.
      const unidentified = { fundingSource: { name: 'Veterans Home' } };
      if (fundingSourceSummary(unidentified) !== '') throw new Error('uncitable source');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_dial_js_reports_the_reservation_status_beside_the_source():
    js = _read("static/js/meridian/dial.js")
    # The ticket keeps the funding/reserved row even when a source is named, so the
    # unresolved amount is never implied to be known.
    assert 'rowData.push(["Funding source", sourceValue])' in js
    assert 'rowData.push(["Funding", fundingLabel(event.fundingStatus)])' in js


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


def test_dial_opens_on_today_while_preloading_the_next_event_evidence():
    js = _read("static/js/meridian/dial.js")
    assert "const initialEvent" in js
    assert "selectedDate: model.today" in js
    assert "selectedEventId: initialEvent ? initialEvent.id : null" in js
    assert 'mode: "today"' in js
    assert 'state.mode === "today"' in js
    # RETARGETED 2026-09-24. This asserted `'kicker.textContent = "Safe to spend"' in js`, i.e.
    # that the dial's CENTRE states the safe-to-spend figure. The owner has since asked for the
    # concept's arrangement -- "Safe-to-spend moved back outside the compass to match the
    # concept as it originally was" -- so the centre must NOT state it, and the figure is made
    # readable outside by un-hiding the header block. The assertion is inverted rather than
    # deleted, so a future edit that reintroduces the duplicate fails here.
    assert 'kicker.textContent = "Safe to spend"' not in js, (
        "the dial's centre must not duplicate the safe-to-spend figure; it belongs outside the "
        "compass, where the header block states it"
    )
    assert '"Choose a day to explore"' in js, "the centre keeps its neutral no-selection copy"


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


def test_dial_connector_runs_use_real_dial_and_row_geometry():
    """The concept ties each rim marker to its callout with a dashed run, and the handoff
    names connectors "tied to actual event coordinates". The previous decoration was a
    fixed 25px dashed rule pinned to the list item's own midline that read no dial
    coordinate at all, and it was off at <=900px where the concepts place the runs."""
    js = _read("static/js/meridian/dial.js")
    css = _read("static/css/meridian/dial.css")
    assert "function renderConnectors" in js
    # Start is the marker's own projection; end is the callout row's box.
    assert "positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 84, angle)" in js
    assert "data-connector-for" in js
    assert "row.getBoundingClientRect()" in js
    # Redrawn whenever the rows are replaced and whenever either side resizes.
    assert "renderConnectors(state, container);" in js
    assert "ResizeObserver" in js
    # Decorative and safe: hidden from assistive tech, clipped so it cannot widen the
    # document, and never a hit target over the callouts or the drag track.
    assert 'layer.setAttribute("aria-hidden", "true")' in js
    assert "pointer-events: none" in css
    assert "overflow: hidden" in css


def test_dial_connector_runs_never_target_a_row_the_rail_does_not_show():
    """The owner reported runs "running straight down connecting to nothing, several
    lines". Reproduced 2026-09-18 with a 14-event horizon: the rail is internally
    scrollable, so 11 of the 14 rows sat below the rail's visible box while every one of
    them still got a run. Those runs left the dial, ran down past the rail, and were cut
    off by the layer's own `overflow: hidden` in mid-air -- a line to nowhere.

    The guard is twofold: a run is only drawn for a row whose centre is inside the rail's
    visible box, and the rail re-runs the connectors on scroll so the runs that remain
    keep following their rows instead of staying where those rows used to be."""
    js = _read("static/js/meridian/dial.js")
    # The rail's visible box is read, and each row's centre is tested against it.
    assert 'panel.querySelector(".obs-dial-events")' in js
    assert "rail.getBoundingClientRect()" in js
    assert "rowMidY < railBox.top || rowMidY > railBox.bottom" in js
    # Scrolling the rail must re-anchor the runs. Bound where the rail is created, so the
    # listener is discarded with the element that update() replaces.
    assert '"scroll"' in js
    assert "renderConnectors(state, container)" in js


def test_evidence_ticket_uses_the_supplied_shaped_asset():
    """Nuance: tickets use shaped silhouettes, layered hairline borders and subtle
    fibrous paper, with corners fixed as text reflows. The kit's parchment-ticket.png
    carries the scalloped rails, cut corners, corner rivets and fibre; the previous
    ticket-corners.svg drew only four brass brackets, so the card read as a rectangle."""
    css = _read("static/css/meridian/dial.css")
    assert "kit-2026-09-16/parchment-ticket.png" in css
    # Nine-slice with `fill` keeps the corners fixed and the blank centre carrying the paper.
    assert "80 fill / 24px round" in css
    assert "ticket-corners.svg\") 40 / 24px" not in css


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


def test_the_day_arc_starts_clear_of_the_dials_building_art():
    """The kit's `dial-plate.png` draws an observatory in the dial's lower-left. The day arc
    started at -120deg, which put day 0 -- today -- at (129,399): straight into the building.
    Owner, 2026-09-18: "It defaults into the building for today and is not visually
    appealing... Where the hand sits per day."

    Measured on the plate (1254px, ring centre 626,632 -> viewBox 300,300): the building
    intrudes into the sky disc ONLY between -140deg and -110deg, reaching inward to r=150-182
    against a hand that runs r=118-198. Its inner edge jumps from 165 at -110deg to 283 at
    -105deg -- a near-vertical roofline -- so a start at -100 leaves the hand's r=198 tip 85
    units clear of it on every day of the horizon.

    The threshold below is that measured roofline, not a preference: anything below -105
    puts the hand back into the artwork.
    """
    import re

    js = _read("static/js/meridian/dial.js")
    match = re.search(r"const ARC_START = (-?\d+(?:\.\d+)?);", js)
    assert match, "ARC_START must stay a plain literal so this guard can read it"
    start = float(match.group(1))
    assert start > -105, (
        f"ARC_START={start}deg puts the hand back into the dial's building art: the kit's "
        f"roofline begins at -110deg and the hand reaches r=198 there, inside the 150-182 "
        f"building edge. -100 is the measured-safe start."
    )
    assert "const ARC_END = 120;" in js, "only the start moved; the sweep narrows to 220deg"


def test_dial_js_states_the_reserved_amount_and_its_basis():
    """OS-048b: the four copy states, executed rather than grepped.

    D-013 requires a stated figure to carry its basis, and D-015 retired the even-split
    model so "observed" is the only basis that may be stated at all.
    ``test_dial_reserved_amount.py`` pins which basis the service emits; this pins what
    the owner reads, including the two states that must stay silent, the surplus that
    must not read as a negative shortfall, and a legacy "derived" payload that must no
    longer be promoted into a stated figure.

    The money strings are built with the same ``Intl`` call the module uses, so the
    assertions hold under any locale while still requiring the exact wording.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const dial = await import('./static/js/meridian/dial.js');
      const { fundingReserveValue, fundingReserveSummary, fundingBasisNote,
              fundingReserveLine } = dial;
      const money = (minor) => new Intl.NumberFormat(undefined, {
        style: 'currency', currency: 'USD', currencyDisplay: 'narrowSymbol',
        minimumFractionDigits: 2, maximumFractionDigits: 2,
      }).format(minor / 100);
      const amount = { minor: 150000, currency: 'USD' };
      const base = { date: '2026-10-01', amount, fundingStatus: 'reserved',
                     fundingBasis: 'observed', fundingAttribution: 'crew',
                     fundingObservedAt: '2026-09-11T21:00:00Z' };

      // covered
      const covered = { ...base, reserved: { minor: 150000, currency: 'USD' } };
      const wantCovered = money(150000) + ' of ' + money(150000) + ' set aside';
      if (fundingReserveSummary(covered) !== wantCovered) {
        throw new Error('covered copy: ' + fundingReserveSummary(covered));
      }

      // partial, with the exact shortfall
      const partial = { ...base, reserved: { minor: 120000, currency: 'USD' },
                        fundingStatus: 'partial' };
      const wantPartial = money(120000) + ' of ' + money(150000) + ' set aside \\u2014 '
                          + money(30000) + ' short';
      if (fundingReserveSummary(partial) !== wantPartial) {
        throw new Error('partial copy: ' + fundingReserveSummary(partial));
      }

      // a reported zero is stated; missing data is not
      const emptied = { ...base, reserved: null, fundingStatus: 'unfunded' };
      const wantEmptied = money(150000) + ' \\u2014 not yet set aside';
      if (fundingReserveSummary(emptied) !== wantEmptied) {
        throw new Error('emptied copy: ' + fundingReserveSummary(emptied));
      }
      const unknown = { ...base, reserved: null, fundingStatus: 'unknown',
                        fundingBasis: 'unknown', fundingAttribution: null };
      if (fundingReserveSummary(unknown) !== '') throw new Error('unknown must stay silent');
      if (fundingReserveValue({ amount, reserved: { minor: 0, currency: 'USD' } }) !== '') {
        throw new Error('a figure with no basis must not be stated');
      }

      // a surplus is never a negative shortfall
      const over = { ...base, reserved: { minor: 160000, currency: 'USD' } };
      const wantOver = money(160000) + ' of ' + money(150000) + ' set aside';
      if (fundingReserveSummary(over) !== wantOver) {
        throw new Error('surplus copy: ' + fundingReserveSummary(over));
      }

      // D-015 retired the even-split model, so a legacy payload still carrying a
      // "derived" figure must no longer be promoted into a stated amount. No surface may
      // show it as money, and the estimate vocabulary must not survive anywhere.
      const legacyDerived = { ...base, reserved: { minor: 150000, currency: 'USD' },
                              fundingBasis: 'derived', fundingAttribution: 'meridian',
                              fundingBasisDivisor: 3 };
      if (fundingReserveSummary(legacyDerived) !== '') {
        throw new Error('a retired derivation must not be stated: '
                        + fundingReserveSummary(legacyDerived));
      }
      if (fundingReserveValue(legacyDerived) !== '') {
        throw new Error('a retired derivation must not be stated');
      }
      if (fundingBasisNote(legacyDerived) !== '') {
        throw new Error('a retired derivation must have no ticket note');
      }
      if (fundingReserveSummary(legacyDerived).indexOf('Meridian estimate') !== -1) {
        throw new Error('the retired estimate vocabulary must not survive');
      }
      if (fundingBasisNote(covered).indexOf('observed from Crew') !== 0) {
        throw new Error('observed note: ' + fundingBasisNote(covered));
      }

      // the day-context line carries the date the figure belongs to
      const short = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' })
        .format(new Date(2026, 9, 1));
      if (fundingReserveLine(covered) !== 'Next due ' + short + ' \\u00b7 ' + wantCovered) {
        throw new Error('day line: ' + fundingReserveLine(covered));
      }
      if (fundingReserveLine(unknown) !== '') throw new Error('no figure, no day line');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_dial_js_ticket_states_the_bill_level_basis():
    """The ticket carries the bill's own figure and where it came from.

    Grep is enough here because the Node test above already executed the copy: this
    only pins that the ticket uses it, and that a bill with a stated figure no longer
    falls through to the unresolved "Funding" row.
    """
    js = _read("static/js/meridian/dial.js")
    # The label is deliberately the short form: the ticket's row grid sizes its label
    # column for AMOUNT / FUNDING SOURCE / RESERVED, and "Set aside for this bill" wrapped
    # onto a second line that collided with its own value at 420px (measured in
    # tests/browser/test_dial_reserved_amount.py, which pins that they cannot overlap).
    assert 'rowData.push(["Set aside", `${figure} · ${fundingBasisNote(event)}`])' in js
    assert "fundingBasisNote(event)" in js
    # The unresolved row survives for the cases that are genuinely unknown.
    assert 'rowData.push(["Funding", fundingLabel(event.fundingStatus)])' in js
