"""Observatory slice: the Plan allocation map (concept 02).

Kit README: "install the map below the tabs with semantic allocation summaries and
separate medallions", and "constellations do not encode money". These guards protect
both halves of that: the map art is decorative and carries no figures, and every
figure is code-owned HTML that comes from the plan payload.
"""
import hashlib
import json
import re
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


def test_the_kit_fallback_glyph_is_still_a_mask_and_the_generated_marks_are_not():
    """Regression guard for a defect caught by inspecting the capture, not by a test: an external
    SVG's currentColor resolves to black inside an <img>, which made the glyph on the navy station
    nearly invisible. The KIT glyphs are therefore still CSS masks.

    OS-087's glyph half changed the picture without weakening that finding, so this guard is
    RETARGETED rather than deleted. The three concept marks are generated rasters that carry their
    own brass, highlight and shadow; masking one would replace every pixel with a single token and
    flatten exactly the relief the owner asked for ("the concept ones look almost raised"). So the
    two paths now have OPPOSITE requirements, and both are asserted here:

      * the kit fallback (used only for an unexpected segment, never the concept's three stations)
        stays a mask driven by `--m-medallion-icon`;
      * a generated mark is a background IMAGE driven by `--m-mark`, and its rule must carry no
        mask property at all, or the relief disappears silently.
    """
    js = _read("static/js/meridian/plan.js")
    # The mark NAMES moved to their own DOM-free module on 2026-09-24 (see
    # tests/meridian/test_plan_map_marks.py for why), so this guard reads both files rather
    # than being deleted: the rendering path stays in plan.js, the vocabulary lives beside the
    # mapping it belongs to.
    marks_js = _read("static/js/meridian/plan-map-marks.js")
    css = _read("static/css/meridian/plan.css")

    # Kit fallback: still a mask.
    assert "m-plan-medallion-glyph" in js
    assert "--m-medallion-icon" in js
    assert "mask: var(--m-medallion-icon)" in css

    # Generated marks: image, never mask.
    assert "m-plan-medallion-mark" in js
    assert "--m-mark" in js
    # The segment URL is BUILT from the mark name, so the literal file name is not in the JS: the
    # guard pins the template and the names instead, or it would pass on a hub-only literal.
    assert 'plan-map-${mark}.png' in js
    for name in ("rotunda", "mountain-flag", "star-rose"):
        assert name in marks_js
    mark_rule = css.split(".m-plan-medallion-mark {", 1)[1].split("}", 1)[0]
    assert "var(--m-mark)" in mark_rule
    assert "mask" not in mark_rule, "a mask on a generated mark flattens its relief"
    assert "background-color" not in mark_rule, "the mark carries its own metal"

    # The hub and Available share ONE star rose, exactly as the concept draws them.
    assert "m-plan-map-hub-mark" in js
    hub_rule = css.split(".m-plan-map-hub-mark {", 1)[1].split("}", 1)[0]
    assert "var(--m-mark)" in hub_rule
    assert "mask" not in hub_rule
    assert "star-rose" in marks_js


def test_every_segment_maps_to_a_mark_the_concept_actually_draws():
    """The concept draws exactly three marks. `allocationMark` may not invent a fourth, and
    an unexpected segment must return `null` rather than borrowing a station's meaning.

    RETARGETED 2026-09-24 to the module the mapping now lives in. Its behaviour is covered
    precisely by the round trip in tests/meridian/test_plan_map_marks.py; what this guard adds
    is that the vocabulary stays closed -- only the three delivered assets are named, and an
    unmatched label still has an explicit `null` path rather than a fall-through.
    """
    js = _read("static/js/meridian/plan.js")
    marks_js = _read("static/js/meridian/plan-map-marks.js")
    fn = marks_js.split("function allocationMark(label) {", 1)[1].split("\n}", 1)[0]
    assert 'return "star-rose"' in fn
    assert 'return "mountain-flag"' in fn
    assert 'return "rotunda"' in fn
    assert "return null" in fn
    # Only the three delivered assets may be referenced.
    for name in ("rotunda", "mountain-flag", "star-rose"):
        assert f"plan-map-{name}.png" in js or name in fn
    # No <img> glyph remains in the medallion renderer.
    assert "glyph.src" not in js


def test_the_medallion_disc_and_glyph_still_differ_in_colour():
    """The navy station must not paint its glyph in the same navy. Asserted on the INTENT rather
    than on the cream literal it used to be achieved with: the concept draws all three stations as
    one medallion -- a dark disc carrying a BRASS glyph -- so the stations were unified on
    2026-09-23 and this now pins the disc/glyph pair that must differ, not the old value. It also
    still pins the KIT fallback's mechanism, because that path is the one the <img> defect broke."""
    css = _read("static/css/meridian/plan.css")
    js = _read("static/js/meridian/plan.js")
    assert "mask: var(--m-medallion-icon) center / contain no-repeat" in css
    assert "background-color: currentColor" in css
    assert "background: #20263b" in css
    assert "color: #c6aa71" in css
    assert "glyph.src" not in js


def test_plan_map_medallion_labels_wrap_inside_their_station():
    """The preview fixture uses short labels (Bills/Goals); the service emits longer
    ones ("Bills"), so the block must wrap rather than escape the
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


def test_plan_tabs_are_the_concepts_bordered_bar_not_pills():
    """Concept 02 draws ONE rounded container with a brass border, divided into three
    EQUAL cells by thin vertical rules, whose active cell is parchment-filled with a brass
    star medallion at its left edge. The previous treatment was three pills in a muted
    trough, which is a different construction, not a different shade.

    Measured on the concept (852px wide, 0.493 to a 420px viewport): container ~733x82px
    -> ~361x40px; active cell 254px = an equal third; medallion ~70px -> ~34px. The bar is
    built to 44px rather than the concept's 40px because its cells are buttons and 44px is
    the touch-target floor."""
    css = (ROOT / "static/css/meridian/plan.css").read_text()
    seg = css.split(".m-plan-seg {", 1)[1].split("}", 1)[0]
    assert "border: 1px solid var(--obs-brass)" in seg
    assert "border-radius: var(--m-radius-pill)" in seg
    assert "overflow: hidden" in seg, "the active parchment must clip to the rounded ends"

    tab = css.split(".m-seg-tab {", 1)[1].split("}", 1)[0]
    # Equal thirds. A zero basis is floored by the active cell's own padding, which made
    # the cells 148/119/119; a percentage basis is the same for all three.
    assert "flex: 1 1 33.3333%" in tab
    assert "min-width: 0" in tab
    assert "min-height: 44px" in tab
    assert "border-radius: 0" in tab, "cells are cells, not pills"
    assert "var(--m-font-serif)" in tab

    # The thin rules between cells, and only between them.
    assert ".m-seg-tab + .m-seg-tab" in css
    assert "border-left: 1px solid var(--obs-brass)" in css

    # The active cell: parchment with the ticket ink the kit requires on parchment.
    active = css.split(".m-seg-tab.is-active {", 1)[1].split("}", 1)[0]
    assert "background: var(--obs-paper)" in active
    assert "color: var(--obs-paper-ink)" in active
    assert "box-shadow: none" in active

    # The medallion: a dark disc ringed in brass with a brass star, at the cell's left.
    disc = css.split(".m-seg-tab.is-active::before {", 1)[1].split("}", 1)[0]
    assert "border-radius: 50%" in disc
    assert "border: 1px solid var(--obs-brass)" in disc
    star = css.split(".m-seg-tab.is-active::after {", 1)[1].split("}", 1)[0]
    assert "background-color: var(--obs-brass)" in star
    assert "icons/star.svg" in star
    assert "mask:" in star and "-webkit-mask:" in star


def test_plan_mobile_rule_does_not_reintroduce_the_unequal_cells():
    """A `flex: 1` inside the <=600px block overrode the equal basis at exactly the widths
    the concept's equal cells matter, so the basis lives in one place and the mobile rule
    only centres the labels.

    This reads EVERY `max-width: 600px` block, not just the first. Inserting an unrelated
    mobile rule ahead of it (the ornament band, 2026-09-24) made the single-first-block
    version fail on `assert ".m-seg-tab" in block` — a false failure about a rule that was
    still present, which is the failure mode a guard must not have. The sheet now has
    several such blocks and CSS resolves the cascade across all of them, so the guard must
    see them all to be describing the sheet the browser actually loads.
    """
    css = (ROOT / "static/css/meridian/plan.css").read_text()
    block = _at_rule_blocks(css, "@media (max-width: 600px) {")
    assert ".m-seg-tab {" in block
    tab_rule = block.split(".m-seg-tab {", 1)[1].split("}", 1)[0]
    # Strip CSS comments first: the rule's own comment records the removed `flex: 1`, and
    # matching that text would make this guard fire on its own documentation.
    declarations = re.sub(r"/\*.*?\*/", "", tab_rule, flags=re.S)
    assert "flex:" not in declarations, "a shorthand flex here overrides the one-third basis"
    assert "text-align: center" in declarations


def _at_rule_blocks(css: str, header: str) -> str:
    """Concatenate the BODIES of every `header` at-rule, brace-balanced.

    Same helper as tests/meridian/test_plan_row_disclosure.py, and for the same reason: this
    sheet carries several `max-width: 600px` blocks and a guard that reads only the first or
    only the last silently stops describing half the mobile layout.
    """
    out = []
    start = 0
    while True:
        index = css.find(header, start)
        if index == -1:
            return "\n".join(out)
        cursor = index + len(header)
        depth = 1
        while cursor < len(css) and depth:
            if css[cursor] == "{":
                depth += 1
            elif css[cursor] == "}":
                depth -= 1
            cursor += 1
        out.append(css[index + len(header) : cursor - 1])
        start = cursor


def test_the_hub_mark_is_sized_by_its_bezel_not_its_canvas():
    """The browser guard in tests/browser/test_plan_ornaments.py converts the hub mark's BOX
    height into a painted bezel width using the constant ``213 / 256``. That constant is a
    measurement of the delivered asset, so it is re-measured here from the PNG itself: if the
    art is ever regenerated with a different bezel-to-canvas ratio, the browser guard's
    arithmetic would silently start describing a different shape. This test fails first.

    Measured 2026-09-24: canvas 217x256, ink rows 2..254, the widest (mid-height) row spans
    x 2..214 -- a 213px bezel -- and the six rows at each end are 7-13px wide, which are the
    north and south rivet knobs rather than part of the circular bezel.

    Pillow is a dev-only dependency (the roadmap records two runners disagreeing over
    playwright for the same reason), so this skips rather than failing a runner without it.
    """
    pytest = __import__("pytest")
    Image = pytest.importorskip("PIL.Image")

    asset = ROOT / "static/img/meridian/observatory/plan-map-hub-compass.png"
    image = Image.open(asset).convert("RGBA")
    alpha = image.split()[3]
    width, height = image.size

    rows = []
    for y in range(height):
        filled = [x for x in range(width) if alpha.getpixel((x, y)) > 16]
        if filled:
            rows.append((y, filled[0], filled[-1], len(filled)))
    assert rows, "the hub mark asset has no ink at all"

    top, bottom = rows[0][0], rows[-1][0]
    widest = max(rows, key=lambda row: row[3])
    bezel = widest[2] - widest[1] + 1

    # The knobs are why the canvas is taller than the bezel: they must be much narrower.
    assert rows[0][3] < bezel * 0.1 and rows[-1][3] < bezel * 0.1, (
        "the asset's end rows are expected to be the narrow rivet knobs; a wide end row means "
        "the bezel is no longer 213/256 of the canvas and the browser guard's constant is stale"
    )
    assert abs(bezel / (bottom - top + 1) - 213 / 256) < 0.01, (
        f"the hub mark's bezel-to-canvas ratio changed: measured {bezel}/{bottom - top + 1}"
    )

    # The CSS must therefore use a non-square box, or a square one caps the bezel below the disc.
    css = _read("static/css/meridian/plan.css")
    desktop = css.split(".m-plan-map-hub-mark {", 1)[1].split("}", 1)[0]
    assert "width: 64px;" in desktop and "height: 75px;" in desktop, (
        "a square box cannot fill the circle: the bezel is 83% of the canvas height"
    )
