"""Observatory slice: the Plan bill row's disclosure and its compact mobile layout (concept 02).

The concept gives each bill a chevron rather than a permanent row of action buttons, and that
disclosure is what makes the compact row possible at all: the three buttons were what forced the
tall card. These guards protect the contract from both directions -- the expanded state lives on
the ROW so the stylesheet owns the presentation, and the control carries a real expanded state so
the collapsed actions stay reachable without depending on the chevron's rotation as the only cue.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/meridian/plan.css").read_text(encoding="utf-8")


def test_the_disclosure_is_a_real_button_carrying_its_own_expanded_state():
    assert "m-plan-row-toggle" in JS
    assert 'rowToggle.type = "button"' in JS
    assert 'rowToggle.setAttribute("aria-expanded", "false")' in JS
    # The click handler must update the attribute as well as the row, or the accessible state
    # and the visual state can disagree.
    assert 'rowToggle.setAttribute("aria-expanded", expanded ? "false" : "true")' in JS
    # The label names the action, so the control does not rely on the chevron's direction. The
    # wording is built from a ternary, so the assertion is on that expression rather than on the
    # two finished sentences, which never appear contiguously in the source.
    assert "Show actions for" in JS
    assert '${expanded ? "Show" : "Hide"} actions for' in JS


def test_the_expanded_state_lives_on_the_row_so_the_stylesheet_owns_presentation():
    assert 'row.dataset.expanded = "false"' in JS
    assert 'row.dataset.expanded = expanded ? "false" : "true"' in JS
    assert '.m-plan-table-row[data-expanded="true"] .m-plan-cell-action' in CSS


def test_the_toggle_is_removed_from_the_desktop_grid_entirely():
    # The desktop template is four columns. A fifth cell would either create an implicit column
    # or wrap, so the toggle is display:none above the breakpoint rather than merely hidden.
    assert ".m-plan-cell-toggle {\n  display: none;\n}" in CSS


def test_the_action_hiding_rule_is_the_later_of_the_two_that_style_the_cell():
    """Regression guard for the actual first-attempt defect.

    `display: none` was written in the mobile layout block, and a LATER mobile rule re-declared
    `display: flex` for the same cell, so the actions stayed visible, the row measured 162px and
    the disclosure appeared to do nothing. The state rule must therefore come after the layout
    rule, which is what this asserts by position.
    """
    layout = CSS.index("Actions arrive with the disclosure")
    assert CSS.index('display: none;', layout) < CSS.index("display: flex;", layout), (
        "the collapsed state must be declared before the expanded state"
    )
    assert ".m-plan-table-row[data-expanded=\"true\"] .m-plan-cell-action" in CSS


def test_the_mobile_figures_use_the_concepts_orange():
    # 02-plan.png measures rgb(242,135,62) on all three bill amounts. The shell's --obs-apricot is
    # rgb(243,178,114), a lighter tone the concept does not use for figures.
    assert "color: #f2873e" in CSS
    assert "02-plan.png measures rgb(242,135,62)" in CSS


def test_the_bills_scroll_inside_a_fixed_band_so_the_rest_fits_underneath():
    assert "max-height: 44vh" in CSS
    assert "overscroll-behavior: contain" in CSS
