"""The timeline chrome the concept draws around the rows: day dividers, chevrons, footer.

Concept 03 (`concepts/timeline.png`) draws each day as a divider -- a named day bound to
its short date, a hairline rule and a four-pointed star -- closes every row with a
right-pointing chevron, and closes the ledger with "Ask Virgil about this activity".

The divider's moon/sun marker is deliberately NOT asserted here: the kit ships a crescent
but no sunburst, and the concept puts a sunburst on every older day. That is a reported
asset gap rather than something to approximate.
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
