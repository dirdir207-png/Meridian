"""Observatory slice: the Activity header vignette (concept 03).

Kit README: "Activity top-right vignette; reuse sparingly in Settings", "About 130-170
CSS px wide on mobile. Do not let it squeeze the heading or touch target." These guards
protect both halves of that instruction: the art is installed and decorative, and the
header is arranged so the art never competes with the heading.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_activity_command_copy_matches_the_governing_concept():
    html = (ROOT / "templates/meridian/partials/activity.html").read_text()
    assert '<h2 class="m-editorial-headline">Activity</h2>' in html
    assert "Every movement, accounted for." in html


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_activity_vignette_installs_the_kit_asset_decoratively():
    html = _read("templates/meridian/partials/activity.html")
    css = _read("static/css/meridian/activity.css")
    assert 'class="m-activity-vignette obs-art" aria-hidden="true"' in html
    # The kit's own asset, referenced once, as a background rather than a content image.
    assert "kit-2026-09-16/activity-telescope.png" in css
    # Decorative art must not intercept a click meant for the header controls.
    assert "pointer-events: none" in css


def test_activity_vignette_cannot_squeeze_the_heading_or_a_touch_target():
    """The kit is explicit that this art must not squeeze the heading. The header copy
    was right-aligned on a column flex, which left the concept's station empty and the
    heading pushed away from it; the copy is left-aligned now and the art takes that
    station only where a free right column exists."""
    css = _read("static/css/meridian/activity.css")
    assert ".m-activity-command {" in css
    assert "align-items: flex-start" in css
    # Above 600px the vignette is absolutely placed in the freed right column and the
    # copy is held clear of it.
    assert "@media (min-width: 601px)" in css
    assert "position: absolute" in css
    assert "max-width: calc(100% - clamp(140px, 18vw, 196px))" in css
    # The governing short title leaves a real right station on mobile too, so the
    # art stays absolute and the copy keeps a bounded measure.
    assert "@media (max-width: 600px)" in css
    assert ".m-activity-vignette { position: absolute" in css
    assert ".m-activity-command-copy { max-width: calc(100% - 156px)" in css


def test_activity_mobile_keeps_filters_open_without_the_extra_filter_button():
    css = _read("static/css/meridian/activity.css")
    assert ".m-filter-button { display: none; }" in css


def test_activity_tabs_use_the_concepts_ruled_underline_treatment():
    css = _read("static/css/meridian/activity.css")
    assert ".m-activity-toolbar .m-segmented" in css
    assert "border-bottom: 1px solid var(--obs-brass)" in css
    assert '.m-button[aria-pressed="true"]::after' in css


def test_activity_vignette_respects_the_kits_size_guidance():
    """Kit: "About 130-170 CSS px wide on mobile"."""
    css = _read("static/css/meridian/activity.css")
    # The narrow-width rule sits inside the kit's stated mobile band.
    assert "width: 148px" in css
    # The wide-width rule is fluid and bounded rather than unbounded.
    assert "clamp(128px, 16vw, 176px)" in css
