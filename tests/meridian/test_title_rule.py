"""Observatory slice: the lilac wavy rule under the workspace title (OS-038).

Concepts 01 (Today), 03 (Activity) and 04 (Accounts) each carry a short wavy lilac
rule between the workspace title and its subline. Concept 02 (Plan) does NOT, and the
ledger records that distinction explicitly, so the guards below protect both halves:
the rule is installed where the concepts show it, and it stays off Plan.

The asset is drawn from measurements rather than invented, and the numbers in those
measurements are pinned here so a later edit cannot silently change the ornament into
something else. It is decorative, so it must not enter the accessibility tree.
"""
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]

ASSET = "static/img/meridian/observatory/title-rule.svg"
CSS = "static/css/meridian/workspaces.css"
WITH_RULE = (
    "templates/meridian/partials/today.html",
    "templates/meridian/partials/activity.html",
    "templates/meridian/partials/accounts.html",
)
PLAN = "templates/meridian/partials/plan.html"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_title_rule_asset_is_drawn_from_the_measured_concepts():
    """The asset exists, is decorative, and keeps the wave measured from the concepts:
    a 4-unit stroke and a 5-unit peak-to-peak amplitude in a 72x12 CSS px box."""
    asset = ROOT / ASSET
    assert asset.is_file(), "the title rule asset is missing"

    root = ElementTree.parse(asset).getroot()
    assert root.get("aria-hidden") == "true"
    assert root.get("focusable") == "false"
    assert root.get("viewBox") == "0 0 72 12"

    paths = root.findall("{http://www.w3.org/2000/svg}path")
    assert len(paths) == 1, "the rule is one drawn stroke, not a stack of shapes"
    path = paths[0]
    assert path.get("fill") == "none"
    # A 4-unit stroke with a 5-unit peak-to-peak wave: the concepts' own 1.23-1.28
    # peak-to-stroke ratio, held as a scale-independent number rather than a pixel size.
    assert path.get("stroke-width") == "4"
    assert path.get("stroke-linecap") == "round"
    # The concepts' own lilac, not a theme variable -- the rule is lilac on both themes.
    assert path.get("stroke", "").lower() == "#a28ec9"

    d = path.get("d", "")
    assert d.startswith("M2 6"), "the stroke must start where the measured rule starts"
    # A smooth wave: two S continuations and one crest, as the concepts show.
    assert d.count("S") == 2, "the rule is one wave, not a chain of segments"
    # Peak-to-peak 5 units about a 6-unit centre: half-amplitude 2.5 = 0.75 x 3.333.
    assert "2.67" in d and "9.33" in d


def test_title_rule_is_installed_on_the_three_concepts_that_carry_it():
    for relative in WITH_RULE:
        html = _read(relative)
        assert 'class="m-title-rule" aria-hidden="true"' in html, relative
        # The rule belongs between the title and the subline, never above the title.
        title_at = html.index("m-editorial-headline") if "m-editorial-headline" in html else html.index("obs-today-title")
        rule_at = html.index("m-title-rule")
        assert title_at < rule_at, f"{relative}: the rule must follow the title"


def test_plan_has_no_title_rule_because_concept_02_shows_none():
    html = _read(PLAN)
    assert "m-title-rule" not in html, "concept 02 has no wavy rule; do not add one to Plan"


def test_title_rule_css_points_at_the_asset_at_its_measured_size():
    css = _read(CSS)
    assert ".m-title-rule {" in css
    assert Path(ASSET).name in css, "the CSS must reference the title-rule asset"
    assert "width: 72px" in css
    assert "height: 12px" in css
    # Decorative art must never intercept a click meant for the title or a control.
    assert "pointer-events: none" in css
