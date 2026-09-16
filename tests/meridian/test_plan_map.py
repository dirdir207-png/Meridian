"""Observatory slice: the Plan allocation map (concept 02).

Kit README: "install the map below the tabs with semantic allocation summaries and
separate medallions", and "constellations do not encode money". These guards protect
both halves of that: the map art is decorative and carries no figures, and every
figure is code-owned HTML that comes from the plan payload.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_plan_command_copy_matches_the_governing_concept():
    html = (ROOT / "templates/meridian/partials/plan.html").read_text()
    assert '<h2 class="m-editorial-headline">Plan</h2>' in html
    assert "Give every dollar a destination." in html


def test_plan_places_navigation_and_map_before_creation_actions():
    html = (ROOT / "templates/meridian/partials/plan.html").read_text()
    assert html.index("data-plan-seg") < html.index("data-allocation-map")
    assert html.index("data-allocation-map") < html.index("data-plan-new-commitment")


def test_plan_places_commitments_immediately_after_the_map_before_coverage():
    html = (ROOT / "templates/meridian/partials/plan.html").read_text()
    assert html.index("data-allocation-map") < html.index("data-commitment-list")
    assert html.index("data-commitment-list") < html.index("data-coverage")
KIT = ROOT / "static/img/meridian/observatory/kit-2026-09-16"


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_plan_map_installs_below_the_tabs_and_before_the_summary_cards():
    html = _read("templates/meridian/partials/plan.html")
    assert "data-allocation-map" in html
    assert "data-allocation-medallions" in html
    assert "data-allocation-links" in html
    # "below the tabs": the map follows the view pane opening and precedes the
    # coverage/funding summary the earlier layout led with.
    tabs = html.index("data-plan-seg")
    pane = html.index('data-plan-view-pane="plan"')
    map_at = html.index("data-allocation-map")
    summary = html.index("m-plan-summary-grid")
    assert tabs < pane < map_at < summary
    # The previous generic bar + legend are gone, not merely hidden.
    assert "data-allocation-bar" not in html
    assert "data-allocation-legend" not in html


def test_plan_map_art_is_decorative_and_every_figure_is_html():
    html = _read("templates/meridian/partials/plan.html")
    js = _read("static/js/meridian/plan.js")
    css = _read("static/css/meridian/plan.css")
    # The art and the leader rules are hidden from assistive tech; the medallions are not.
    assert 'class="m-plan-map-art obs-art" aria-hidden="true"' in html
    assert 'aria-hidden="true" focusable="false" data-allocation-links' in html
    # Medallion text is built from the payload, never baked into the artwork.
    assert "m-plan-medallion-label" in js
    assert "label.textContent = segment.label" in js
    assert "amount.textContent = money(segment.amount)" in js
    # The backdrop is a CSS background of the supplied kit asset, and the map keeps
    # that asset's own aspect ratio instead of stretching it.
    assert "kit-2026-09-16/plan-map.png" in css
    assert "aspect-ratio: 1536 / 1024" in css


def test_plan_map_stations_are_composition_not_amounts():
    """A station must not be sized by the money, or the map would claim to encode the
    split the way the previous stacked bar did."""
    js = _read("static/js/meridian/plan.js")
    assert "ALLOCATION_STATIONS" in js
    assert "medallion.style.left = `${station.left}%`" in js
    assert "medallion.style.top = `${station.top}%`" in js
    # The removed bar sized each slice by amount / cash_total; that math is gone.
    assert "segment.amount / cash" not in js
    # "Available" is pinned to the concept's lower hub whatever order it arrives in.
    assert "/available/i.test(segment.label)" in js


def test_plan_map_glyphs_are_masks_so_each_disk_colours_its_own_glyph():
    """Regression guard for a defect caught by inspecting the capture, not by a test:
    an external SVG's currentColor resolves to black inside an <img>, which made the
    glyph on the navy station nearly invisible. The glyphs are CSS masks instead."""
    js = _read("static/js/meridian/plan.js")
    css = _read("static/css/meridian/plan.css")
    assert "m-plan-medallion-glyph" in js
    assert "--m-medallion-icon" in js
    assert "m-plan-map-hub-rose" in js
    # The medallion and rose glyphs are masks painted with currentColor, so the disk's
    # own colour decides the glyph colour.
    assert "mask: var(--m-medallion-icon) center / contain no-repeat" in css
    assert "background-color: currentColor" in css
    # The navy station must not paint its glyph in the same navy.
    assert "color: #ead8b5" in css
    # No <img> glyph remains in the medallion renderer.
    assert "glyph.src" not in js


def test_plan_map_medallion_labels_wrap_inside_their_station():
    """The preview fixture uses short labels (Bills/Goals); the service emits longer
    ones ("Committed to commitments"), so the block must wrap rather than escape the
    parchment on the side where the nearest edge is closest."""
    css = _read("static/css/meridian/plan.css")
    assert "max-width: 34%" in css
    assert "overflow-wrap: anywhere" in css


def test_plan_income_strip_uses_the_kit_ticket_and_keeps_its_figures_in_html():
    """Concept 02's next-income strip. The kit's stated role for this asset is
    "Evidence, account summary, compact income ticket", so the strip reuses it rather
    than inventing a shape; the date and amount must stay code-owned."""
    css = _read("static/css/meridian/plan.css")
    html = _read("templates/meridian/partials/plan.html")
    assert "parchment-ticket.png" in css
    # Nine-slice preserves the scalloped ends and corner rivets rather than stretching
    # the whole border, and `fill` carries the blank centre.
    assert "80 fill / 20px round" in css
    # The band sits on the parchment card, so it must not keep the dark surface's fill.
    assert ".m-plan-summary-grid .m-plan-funding-card" in css
    # The data hooks that carry the figures survive the restyle.
    assert "data-next-paycheck-date" in html
    assert "data-next-paycheck-amount" in html
    assert "data-funding-caption" in html
    assert "data-plan-shortfall" in html


def test_plan_primary_action_uses_the_kit_plate_behind_a_real_button():
    """Concept 02's primary action is the apricot plate, and the kit specifies this
    asset for exactly that: "Primary action plate ... Use behind a real button/link.
    HTML label and arrow; at least 44px target. Nine-slice for variable width." The
    slice offsets are measured from the asset, whose plate sits behind ~170px of
    transparent padding."""
    css = _read("static/css/meridian/plan.css")
    html = _read("templates/meridian/partials/plan.html")
    assert "kit-2026-09-16/apricot-button.png" in css
    assert "190 230 190 230 fill / 10px 34px round" in css
    # The kit's minimum target, and a real button carrying an HTML label beneath the art.
    assert "min-height: 44px" in css
    assert "data-plan-new-commitment" in html
    assert "Add a bill or goal" in html


def test_plan_kit_assets_are_consumed_byte_for_byte():
    manifest = json.loads((KIT / "manifest.json").read_text())
    entry = next(a for a in manifest["assets"] if a["file"] == "plan-map.png")
    digest = hashlib.sha256((KIT / "plan-map.png").read_bytes()).hexdigest()
    assert digest == entry["sha256"]
