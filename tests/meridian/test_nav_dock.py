"""Observatory slice: the bottom dock — taller, with the concepts' ornate glyphs.

The owner asked for the dock to be taller and its icons more ornate, matching the
concepts. Measured on the governing concept `design/observatory-drafts-2026-09-08/01-today.png`
(853px wide):

* the dock panel spans y=1672..1823, i.e. **152px** tall = **17.8%** of the frame's width;
* it is a rounded panel inset from the screen edges, with a hairline border all round;
* each item stacks its glyph above its label, and the glyphs are line engravings: a
  ringed compass rose with cardinal ticks, a folding map carrying a dotted route to a
  cross, rising columns, and a ringed profile;
* the current workspace is marked by a lilac rule UNDER its label, with no fill behind
  the item.

The suite cannot see pixels, so these guards pin the source facts those measurements
produced, and `tests/browser/test_meridian_shell.py` covers the rendered behaviour.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHELL = ROOT / "static/css/meridian/shell.css"
OBSERVATORY = ROOT / "static/css/meridian/observatory.css"
NAV_DIR = ROOT / "static/img/meridian/observatory/nav"

GLYPHS = {
    "today": "compass-rose.svg",
    "plan": "charted-map.svg",
    "activity": "rising-bars.svg",
    "accounts": "ringed-profile.svg",
}


def _read(path):
    return path.read_text(encoding="utf-8")


def test_the_four_dock_glyphs_are_engravings_rather_than_placeholders():
    """Each glyph must be real line art: several drawn elements, no raster, and
    `currentColor` so the link's own colour drives it through the mask."""
    for workspace, filename in GLYPHS.items():
        path = NAV_DIR / filename
        assert path.is_file(), f"the {workspace} dock glyph {filename} is missing"
        svg = _read(path)
        assert svg.startswith("<svg"), f"{filename} is not an SVG"
        assert "currentColor" in svg, f"{filename} must take the link's colour"
        # An engraving, not a single silhouette: the concepts' glyphs carry at least a
        # body, a page or a ring plus an inner mark.
        assert svg.count("<path") + svg.count("<circle") >= 3, (
            f"{filename} is too plain to be the concept's engraving"
        )
        assert "<image" not in svg and "base64" not in svg, f"{filename} must not embed a raster"


def test_the_dock_stacks_its_glyph_over_its_label_and_is_much_taller():
    css = _read(SHELL)
    # Stacking is most of what makes the dock taller, and it is what the concept shows.
    assert "flex-direction: column" in css
    # The item's floor grew from 56px; the whole dock measures 76px = 18.1% of 420px
    # against the concept's 17.8%.
    assert "min-height: 64px" in css
    assert "width: 34px" in css, "the dock glyphs must be drawn larger than the rail's 20px"
    assert "font-size: 15px" in css
    # The concept's dock is a rounded panel inset from the screen edges, not a full-bleed
    # bar with only a top border.
    assert "border-radius: var(--m-radius-lg)" in css
    assert "margin: 0 2%" in css
    # The concept separates the four workspaces with a hairline rule.
    assert "border-left: 1px solid var(--m-border)" in css


def test_the_active_dock_marker_sits_under_the_label_and_carries_no_fill():
    """The concept marks the current workspace with a rule UNDER its label, and draws no
    block behind the item. The marker stays a physical, non-colour cue, so the active
    state still does not depend on colour alone."""
    shell = _read(SHELL)
    observatory = _read(OBSERVATORY)
    # Scope to the dock: shell.css also carries the desktop rail's own ::before bar, and
    # the first match in the file belongs to that rail, not the dock.
    dock = shell.split("@media (max-width: 900px) {", 1)[1]
    marker = dock.split('.m-nav-item[aria-current="page"]::before', 1)[1].split("}", 1)[0]
    assert "bottom: 3px" in marker, "the marker belongs under the label, as the concept draws it"
    assert "top: auto" in marker, "the marker must not sit above the glyph any more"
    assert "height: 3px" in marker
    # The fill the concept does not draw is gone, and the reason is recorded in the CSS.
    # Scoped to the nav rule: the same rgba value is also the `--m-aurora` gradient token,
    # which is an unrelated decorative wash and must stay.
    active = observatory.split('.obs-shell .m-nav-item[aria-current="page"] {', 1)[1].split("}", 1)[0]
    assert "background: none" in active
    assert "rgba(193, 169, 226, 0.16)" not in active
    # Observatory keeps the ink; shell.css keeps the geometry. That split is unchanged.
    assert ".obs-shell .m-nav-item[aria-current=\"page\"]::before" in observatory
    assert "var(--obs-lilac)" in observatory


def test_the_rail_keeps_the_kit_glyphs_and_only_the_dock_uses_the_engravings():
    """The dock's engravings supersede the kit silhouettes there, but the change is scoped
    to the dock: nothing may silently redirect a kit glyph used elsewhere."""
    css = _read(SHELL)
    for filename in GLYPHS.values():
        assert f"observatory/nav/{filename}" in css
    # The kit's own files are untouched and still on disk for the surfaces that use them.
    kit = ROOT / "static/img/meridian/observatory/kit-2026-09-16/icons"
    for name in ("compass.svg", "map.svg", "bar-chart.svg", "person-circle.svg"):
        assert (kit / name).is_file(), f"the kit glyph {name} was removed, not superseded"
