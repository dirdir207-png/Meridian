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
    assert ".m-activity-toolbar .m-activity-tabs" in css
    assert "border-bottom: 1px solid var(--obs-brass)" in css
    assert '.m-activity-tab[aria-pressed="true"]::after' in css


def test_activity_vignette_respects_the_kits_size_guidance():
    """Kit: "About 130-170 CSS px wide on mobile"."""
    css = _read("static/css/meridian/activity.css")
    # The narrow-width rule sits inside the kit's stated mobile band.
    assert "width: 148px" in css
    # The wide-width rule is fluid and bounded rather than unbounded.
    assert "clamp(128px, 16vw, 176px)" in css


def test_activity_opts_into_the_handoffs_single_action_orange():
    css = _read("static/css/meridian/activity.css")
    activity_root = css.split(".m-activity {", 1)[1].split("}", 1)[0]
    assert "--obs-action: #e99a48" in activity_root
    # The light edition swaps the ACTION to the palette's existing green rather than
    # inventing a second brand orange, because #e99a48 cannot carry text on parchment.
    light_root = css.split("html[data-theme=\"light\"] .m-activity {", 1)[1].split("}", 1)[0]
    assert "--m-activity-action: var(--m-healthy)" in light_root
    assert "--m-activity-action-ink: var(--m-canvas)" in light_root
    # The dark root stays the handoff's orange, and no second orange hex is declared.
    declarations = [
        line.strip()
        for line in css.splitlines()
        if "#e99a48" in line and line.strip().startswith("--")
    ]
    assert declarations == [
        "--obs-action: #e99a48;",
        "--m-activity-action: #e99a48;",
    ], declarations
    # Mint remains a semantic confirmed/incoming colour, never the unreviewed action.
    approve = css.split(".m-review-approve {", 1)[1].split("}", 1)[0]
    assert "background: var(--m-activity-action)" in approve
    assert "var(--m-healthy)" not in approve


def test_activity_tabs_use_action_cues_with_a_selection_star_and_end_stars():
    html = _read("templates/meridian/partials/activity.html")
    css = _read("static/css/meridian/activity.css")
    assert 'class="m-segmented m-activity-tabs"' in html

    tabs = css.split(".m-activity-tabs {", 1)[1].split("}", 1)[0]
    assert "width: 100%" in tabs
    assert "border-bottom: 1px solid var(--obs-brass)" in tabs
    assert ".m-activity-tabs::before," in css
    assert ".m-activity-tabs::after {" in css
    assert 'content: "✦"' in css

    # One declaration now serves both editions: the token resolves to orange in dark
    # and to the deep green in light, so the label always sits in the action colour.
    selected = css.split('.m-activity-tab[aria-pressed="true"] {', 1)[1].split("}", 1)[0]
    assert "color: var(--m-activity-action)" in selected
    assert '.m-activity-tab[aria-pressed="true"]::before' in css
    underline = css.split('.m-activity-tab[aria-pressed="true"]::after {', 1)[1].split("}", 1)[0]
    assert "background: var(--m-activity-action)" in underline


def test_review_actions_use_filled_and_continuously_outlined_ticket_silhouettes():
    css = _read("static/css/meridian/activity.css")
    actions = css.split(".m-review-actions .m-button {", 1)[1].split("}", 1)[0]
    assert "min-height: 44px" in actions
    assert "clip-path: polygon(" in actions

    approve = css.split(".m-review-approve {", 1)[1].split("}", 1)[0]
    assert "background: var(--m-activity-action)" in approve
    assert "color: var(--m-activity-action-ink)" in approve

    correct = css.split(".m-review-correct {", 1)[1].split("}", 1)[0]
    assert "background: transparent" in correct
    assert "border-color: transparent" in correct
    outer_edge = css.split(".m-review-actions .m-review-correct::before {", 1)[1].split("}", 1)[0]
    assert "background: var(--obs-brass)" in outer_edge
    assert "clip-path: inherit" in outer_edge
    inner_face = css.split(".m-review-actions .m-review-correct::after {", 1)[1].split("}", 1)[0]
    assert "inset: 1px" in inner_face
    assert "clip-path: polygon(" in inner_face


def test_review_action_focus_rings_contrast_with_each_ticket_face():
    css = _read("static/css/meridian/activity.css")
    approve_focus = css.split(
        ".m-review-actions .m-review-approve:focus-visible {", 1
    )[1].split("}", 1)[0]
    assert "var(--m-activity-action-ink)" in approve_focus
    correct_focus = css.split(
        ".m-review-actions .m-review-correct:focus-visible::after {", 1
    )[1].split("}", 1)[0]
    assert "var(--m-ink)" in correct_focus
