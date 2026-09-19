"""The timeline chrome the concept draws around the rows: dividers, chevrons, footer.

Concept 03 (`concepts/timeline.png`) draws each day as a divider -- a crescent on Today
and a sunburst on older days, the day's name bound to its short date, a hairline rule and
a four-pointed star -- closes every row with a right-pointing chevron, and closes the
ledger with "Ask Virgil about this activity".

The crescent is the kit's shipped `moon.svg`. The sunburst is NOT from the supplied set:
the kit is Bootstrap Icons and ships bi-moon without bi-sun, and no governing design
bundle has a sun. It is authored in this repository to the kit's metrics, at the kit's
outline weight, and says so in its own header -- which is why this file also pins that
provenance rather than treating it as supplied art.
"""
import json
import shutil
import subprocess

import pytest

FORMAT_MODULE = "static/js/meridian/format.js"
ACTIVITY_SCRIPT = "static/js/meridian/activity.js"
WORKSPACE = "templates/meridian/partials/activity.html"
STYLE = "static/css/meridian/activity.css"


def _read(relative):
    from pathlib import Path

    return (Path(__file__).resolve().parents[2] / relative).read_text(encoding="utf-8")


def _divider_labels():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = (
        "const m = await import('./%s');\n"
        "const now = new Date();\n"
        "const day = 24 * 60 * 60 * 1000;\n"
        "const out = {\n"
        "  today: m.dayDividerLabel(now.toISOString()),\n"
        "  yesterday: m.dayDividerLabel(new Date(now.getTime() - day).toISOString()),\n"
        "  older: m.dayDividerLabel(new Date(now.getTime() - 5 * day).toISOString()),\n"
        "  invalid: m.dayDividerLabel('not-a-date'),\n"
        "  row_label_unchanged: m.dayLabel(now.toISOString()),\n"
        "};\n"
        "console.log(JSON.stringify(out));\n" % FORMAT_MODULE
    )
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=".",
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_the_divider_names_the_day_and_binds_it_to_its_date():
    labels = _divider_labels()

    assert labels["today"].startswith("Today \u00b7 ")
    assert labels["yesterday"].startswith("Yesterday \u00b7 ")
    # Older days take the compact form the concept's density implies, not the long one.
    assert "," in labels["older"]
    assert str(__import__("datetime").date.today().year) not in labels["older"]
    assert labels["invalid"] == "Unknown date"


def test_the_row_meta_label_is_untouched_by_the_divider_change():
    """`dayLabel` also feeds the row meta lines, so the divider must not have moved it."""
    labels = _divider_labels()

    assert labels["row_label_unchanged"] == "Today"


def test_the_divider_is_a_label_a_hairline_rule_and_a_decorative_star():
    script = _read(ACTIVITY_SCRIPT)
    css = _read(STYLE)

    assert "function dayHeading(isoTimestamp)" in script
    assert "dayDividerLabel(isoTimestamp)" in script
    assert "dayDividerLabel" in script.split("from \"./format.js\"", 1)[0]
    # The rule and star are decoration; the label carries the heading's meaning.
    assert 'rule.setAttribute("aria-hidden", "true")' in script
    assert 'star.setAttribute("aria-hidden", "true")' in script
    assert ".m-day-heading-label" in css
    assert ".m-day-heading-rule" in css
    # CSS escapes are backslash + hex; a \u sequence would render the literal text.
    star = css.split(".m-day-heading-star::before {", 1)[1].split("}", 1)[0]
    assert 'content: "\\2726"' in star
    assert "\\u2726" not in css


def test_every_timeline_row_closes_with_a_chevron_the_kit_does_not_ship():
    script = _read(ACTIVITY_SCRIPT)
    css = _read(STYLE)

    # Built only for the ledger rows, never for the review cards.
    assert 'if (state.mode !== "review") {' in script
    assert 'chevron.className = "m-row-chevron"' in script
    assert 'chevron.textContent = "\\u203a"' in script
    assert 'chevron.setAttribute("aria-hidden", "true")' in script
    chevron = css.split(".m-row-chevron {", 1)[1].split("}", 1)[0]
    assert "flex: 0 0 auto" in chevron
    # It stands down on the narrowest rows so it cannot push the amount off the line.
    assert "  .m-row-chevron {\n    display: none;\n  }" in css


def test_the_ledger_footer_opens_the_advisor_that_already_exists():
    """No new entry point: the shell's own `data-open-advisor` hook, already bound by
    today.js to `window.advisorSetOpen` from the advisor FAB."""
    html = _read(WORKSPACE)
    css = _read(STYLE)

    assert "m-activity-ask" in html
    assert 'data-open-advisor' in html
    assert "Ask Virgil about this activity" in html
    assert 'class="m-activity-ask-roundel"' in html
    assert "kit-2026-09-18/icons/star.svg" in css
    ask = css.split(".m-activity-ask {", 1)[1].split("}", 1)[0]
    assert "background: none" in ask
    assert "kit-2026-09-18/icons/moon.svg" in css


def _day_offsets():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = (
        "const m = await import('./%s');\n"
        "const now = new Date();\n"
        "const day = 24 * 60 * 60 * 1000;\n"
        "console.log(JSON.stringify({\n"
        "  today: m.dayOffset(now.toISOString()),\n"
        "  yesterday: m.dayOffset(new Date(now.getTime() - day).toISOString()),\n"
        "  older: m.dayOffset(new Date(now.getTime() - 4 * day).toISOString()),\n"
        "  invalid: m.dayOffset('not-a-date'),\n"
        "}));\n" % FORMAT_MODULE
    )
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=".",
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_the_divider_marker_is_the_concepts_crescent_on_today_and_sun_otherwise():
    """The pair must come from ONE notion of "today" so the moon and the label cannot
    disagree about which day is today."""
    offsets = _day_offsets()

    assert offsets["today"] == 0
    assert offsets["yesterday"] == -1
    assert offsets["older"] < -1
    assert offsets["invalid"] is None

    script = _read(ACTIVITY_SCRIPT)
    assert 'marker.dataset.dayMarker = dayOffset(isoTimestamp) === 0 ? "moon" : "sun";' in script
    assert "kitIconUrl(marker.dataset.dayMarker)" in script
    assert 'marker.setAttribute("aria-hidden", "true")' in script
    # dayLabel must read the same helper rather than repeating the arithmetic.
    assert "const diffDays = dayOffset(isoTimestamp);" in _read(FORMAT_MODULE)


def test_the_sunburst_is_authored_here_and_the_crescent_is_supplied():
    """Provenance matters: the supplied set is Bootstrap Icons and has no sun, so the
    sun file must declare that it was authored in-repo rather than misrepresenting
    itself as part of the licensed set."""
    from pathlib import Path

    icons = Path(__file__).resolve().parents[2] / "static/img/meridian/observatory/kit-2026-09-18/icons"
    sun = (icons / "sun.svg").read_text(encoding="utf-8")
    moon = (icons / "moon.svg").read_text(encoding="utf-8")

    assert "Authored in this repository" in sun
    assert "NOT part of the supplied set" in sun
    # Same metrics and weight convention as its neighbours.
    assert 'width="16" height="16"' in sun and 'viewBox="0 0 16 16"' in sun
    assert "currentColor" in sun
    # bi-moon is the supplied crescent; the sun did not come from the same source.
    assert "bi bi-moon" in moon
    assert "Authored" not in moon


def test_the_floating_trigger_stands_down_where_the_ledger_offers_its_own():
    """Two controls for one panel on one screen is a duplicate affordance, not a
    convenience. The shell's trigger hides on Activity; the ledger footer opens the
    identical advisor, and the open panel keeps its own close control."""
    css = _read(STYLE)

    rule = css.split(
        'body:has([data-workspace-section="activity"]:not([hidden])) #advisor-fab.m-advisor-trigger {',
        1,
    )[1].split("}", 1)[0]
    assert "display: none !important" in rule
    # Same mechanism advisor.css already uses for the open-panel case.
    assert "body:has(#advisor-panel[data-open])" in _read("static/css/meridian/advisor.css")
