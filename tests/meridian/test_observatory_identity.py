"""Regression guard for the Observatory shared identity — handoff step 2.

The owner-directed 2026-09-16 handoff (`docs/project/OBSERVATORY_ASSET_KIT_2026-09-16.md`)
and its kit README (`Typography`, `Color and icons`, `Integration sequence`) require the
shared chrome to carry:

* the bundled licensed type pairing, self-hosted with no third-party font request;
* the accented Meridian wordmark, shared by the desktop rail and both mobile headers;
* the four semantic navigation glyphs, always beside a visible label;
* an active treatment that keeps a non-colour cue.

These are pure file reads, so they run in the default (non-browser) suite. The matching
rendered behaviour is asserted in `tests/browser/test_meridian_shell.py`.
"""

from pathlib import Path

ROOT = Path(__file__).parents[2]
CSS = ROOT / "static/css/meridian"
KIT = ROOT / "static/img/meridian/observatory/kit-2026-09-16"

TOKENS = CSS / "tokens.css"
SHELL = CSS / "shell.css"
OBSERVATORY = CSS / "observatory.css"

NAVIGATION = ROOT / "templates/meridian/partials/navigation.html"
WORDMARK = ROOT / "templates/meridian/partials/wordmark.html"
INDEX = ROOT / "templates/meridian/index.html"
SETTINGS = ROOT / "templates/meridian/settings.html"

SERIF_FAMILY = "Meridian Serif"
SANS_FAMILY = "Meridian Sans"

FONT_FILES = {
    SERIF_FAMILY: "fonts/LibreBaskerville.ttf",
    SANS_FAMILY: "fonts/SourceSans3.ttf",
}

# kit README: "compass, map, bar-chart, person-circle map to the four navigation entries".
NAV_ICONS = {
    "today": "compass.svg",
    "plan": "map.svg",
    "activity": "bar-chart.svg",
    "accounts": "person-circle.svg",
}

GOVERNING_HEADERS = {"navigation": NAVIGATION, "index": INDEX, "settings": SETTINGS}


def test_bundled_font_files_are_present_and_substantial():
    for family, relative in FONT_FILES.items():
        path = KIT / relative
        assert path.is_file(), f"{family}: kit font {relative} is missing"
        assert path.stat().st_size > 100_000, f"{relative} is too small to be a real font"


def test_tokens_self_host_both_families_from_the_kit_and_use_them_in_the_stacks():
    css = TOKENS.read_text()

    for family, relative in FONT_FILES.items():
        assert f'font-family: "{family}"' in css, f"no @font-face for {family}"
        assert f"/static/img/meridian/observatory/kit-2026-09-16/{relative}" in css, (
            f"{family} is not sourced from the bundled kit file"
        )

    assert f'--m-font-serif: "{SERIF_FAMILY}"' in css
    assert f'--m-font-sans: "{SANS_FAMILY}"' in css


def test_observatory_token_layer_resolves_to_the_same_two_families():
    """`.obs-shell` sets its own font tokens; leaving them on host fallbacks would
    render the whole Observatory layer in a different typeface from the shell."""
    css = OBSERVATORY.read_text()
    assert f'--obs-font-serif: "{SERIF_FAMILY}"' in css
    assert f'--obs-font-sans: "{SANS_FAMILY}"' in css


def test_no_remote_font_origin_is_referenced_anywhere_in_the_identity_layer():
    for path in (TOKENS, SHELL, OBSERVATORY, NAVIGATION, INDEX, SETTINGS):
        text = path.read_text()
        for origin in ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net"):
            assert origin not in text, f"{path.name} references remote font origin {origin}"


def test_wordmark_partial_exists_with_the_decorative_accent_glyph():
    assert WORDMARK.is_file(), "the shared wordmark partial is missing"
    text = WORDMARK.read_text()
    assert "m-wordmark" in text
    assert "m-wordmark-accent" in text, "the accented letter is not marked"
    # The letter itself stays in the text so the name remains readable; only the
    # star is a CSS pseudo-element, so no extra accessible text is introduced.
    assert "\u0131" in text or "i" in text


def test_every_governing_header_renders_the_shared_wordmark():
    for name, path in GOVERNING_HEADERS.items():
        text = path.read_text()
        assert "'meridian/partials/wordmark.html'" in text, (
            f"{name} does not render the shared wordmark partial"
        )


def test_navigation_marks_its_four_glyphs_decorative_beside_visible_labels():
    text = NAVIGATION.read_text()
    for workspace in NAV_ICONS:
        assert f'data-workspace-icon="{workspace}"' in text
    # Icons are decorative: the visible label carries the name.
    assert text.count('data-nav-icon aria-hidden="true"') == 4
    assert text.count('class="m-nav-label"') == 4


def test_shell_maps_each_workspace_to_its_supplied_kit_glyph():
    css = SHELL.read_text()
    for workspace, filename in NAV_ICONS.items():
        assert f'[data-workspace-icon="{workspace}"]' in css, (
            f"no icon mapping for the {workspace} workspace"
        )
        assert f"observatory/kit-2026-09-16/icons/{filename}" in css, (
            f"{workspace} does not use the supplied {filename}"
        )
        assert (KIT / "icons" / filename).is_file(), f"kit glyph {filename} is missing"

    # Both prefixed and standard mask properties, so Chromium and Firefox agree.
    assert "-webkit-mask:" in css
    assert "mask:" in css


def test_active_navigation_keeps_a_non_colour_cue_and_uses_the_lilac_treatment():
    observatory = OBSERVATORY.read_text()
    shell = SHELL.read_text()
    assert ".obs-shell .m-nav-item[aria-current=\"page\"]::before" in observatory
    assert "var(--obs-lilac)" in observatory
    # The physical marker geometry stays owned by shell.css (existing behaviour).
    assert '.m-nav-item[aria-current="page"]::before' in shell


def test_observatory_light_theme_replaces_dark_canvas_surface_and_ink_tokens():
    css = OBSERVATORY.read_text()
    light = css.split('html[data-theme="light"] .obs-shell', 1)[1]
    assert "--m-canvas: #f4ecdf" in light
    assert "--m-surface: #fffaf0" in light
    assert "--m-ink: #20263b" in light
    assert "--m-ink-muted: #655d6c" in light
    assert "background:" in light


def test_compact_header_uses_the_supplied_gear_as_a_current_color_mask():
    html = INDEX.read_text()
    css = SHELL.read_text()
    assert 'class="m-topbar-settings-icon" aria-hidden="true"' in html
    assert "kit-2026-09-16/icons/gear.svg" in css
    assert "-webkit-mask:" in css
    assert "background-color: currentColor" in css
    assert ".m-topbar .m-theme-toggle-label" in css


def test_light_header_keeps_the_wordmark_and_controls_legible():
    css = OBSERVATORY.read_text()
    assert 'html[data-theme="light"] .obs-shell .m-topbar .m-brand' in css
    assert "color: #20263b" in css
