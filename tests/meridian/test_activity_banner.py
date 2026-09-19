"""Concept 03's parchment banner above the day dividers.

The concept draws "Your money, in order." over an observed stamp. The banner is the
first surface in Activity that states WHEN the ledger was observed, so the honesty
rules matter more than the styling: a stale graph must say so in the line itself, and
an unconnected graph must not show a headline claiming an order nothing has observed.

The copy is composed by `activityBannerCopy` in api.js, next to `freshnessText`, so it
is DOM-free and a Node round-trip can exercise every branch rather than a source
pattern.
"""
import json
import shutil
import subprocess

import pytest

ROOT = "."
BANNER_MODULE = "static/js/meridian/api.js"
ACTIVITY_SCRIPT = "static/js/meridian/activity.js"
WORKSPACE = "templates/meridian/partials/activity.html"
STYLE = "static/css/meridian/activity.css"

# The synthetic fixture's own timestamp, so the assertions below name real output.
STAMP = "2026-09-08T13:42:00Z"


def _read(relative):
    from pathlib import Path

    return (Path(__file__).resolve().parents[2] / relative).read_text(encoding="utf-8")


def _banner_copy(cases):
    """Round-trip the pure mapper through Node, the way the glyph tests do."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = (
        "const m = await import('./%s');\n"
        "const cases = %s;\n"
        "console.log(JSON.stringify(cases.map((c) => m.activityBannerCopy(c))));\n"
        % (BANNER_MODULE, json.dumps(cases))
    )
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_a_fresh_ledger_states_what_was_observed_and_when():
    copy, = _banner_copy([{"status": "fresh", "last_updated_at": STAMP}])

    assert copy["title"] == "Your money, in order."
    assert copy["meta"].startswith("Observed activity \u00b7 Updated")
    # The stamp keeps its DATE: a time-only stamp reads as "today" on a ledger whose
    # newest row may be days old.
    assert "Sep 8" in copy["meta"].replace("\u00a0", " ")


def test_a_stale_ledger_says_it_is_not_current_in_the_line_itself():
    copy, = _banner_copy([{"status": "stale", "last_updated_at": STAMP}])

    assert copy["title"] == "Your money, in order."
    assert "Not current" in copy["meta"]
    assert "Last observed" in copy["meta"]
    # The stamp must never be presented as a plain "Updated", which would read as live.
    assert "Updated" not in copy["meta"]


def test_an_unconnected_ledger_gets_no_banner_rather_than_a_claim():
    copies = _banner_copy(
        [
            {"status": "unavailable", "last_updated_at": None},
            {"status": "unavailable", "last_updated_at": STAMP},
            None,
            {},
        ]
    )

    assert copies == [None, None, None, None]


def test_a_missing_stamp_still_does_not_invent_one():
    fresh, stale = _banner_copy(
        [
            {"status": "fresh", "last_updated_at": None},
            {"status": "stale", "last_updated_at": None},
        ]
    )

    assert fresh["meta"] == "Observed activity"
    assert stale["meta"] == "Observed activity \u00b7 Not current"


def test_the_banner_belongs_to_the_timeline_and_the_strip_to_review():
    html = _read(WORKSPACE)
    script = _read(ACTIVITY_SCRIPT)

    assert "data-activity-banner" in html
    assert "data-activity-banner-title" in html
    assert "data-activity-banner-meta" in html
    # The default template renders nothing rather than a headline before data arrives.
    assert "m-activity-banner" in html and "hidden>" in html
    # One mapper, called from the fetch path.
    assert "setActivityBanner(root, payload.data_freshness)" in script
    assert "activityBannerCopy" in script.split("from \"./api.js\"", 1)[0]
    # The two parchment surfaces are mutually exclusive by mode.
    assert 'banner.hidden = copy === null || state.mode !== "timeline"' in script
    assert 'strip.hidden = value === 0 || state.mode !== "review"' in script


def test_the_banner_reuses_the_kits_parchment_and_own_glyphs():
    css = _read(STYLE)

    banner = css.split(".m-activity-banner {", 1)[1].split("}", 1)[0]
    assert "kit-2026-09-16/parchment-ticket.png" in banner
    assert "80 fill / 20px round" in banner
    # A `display` declaration outranks the UA `[hidden]` rule.
    assert ".m-activity-banner[hidden]" in css
    # The roundel and the ornaments are the kit's shipped art, masked so they inherit ink.
    assert "kit-2026-09-18/icons/moon.svg" in css
    assert "kit-2026-09-18/icons/star.svg" in css
    # At phone widths the decorative stars stand down so the stamp keeps one line.
    # Matched on the rule itself: the file has earlier `max-width: 600px` blocks.
    assert "  .m-activity-banner-stars {\n    display: none;\n  }" in css
    assert "  .m-activity-banner-roundel {\n    width: 38px;\n    height: 38px;\n  }" in css
