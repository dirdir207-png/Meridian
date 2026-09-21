"""OS-085: the Connections row states are stated as HAIRLINES, not tinted fills.

WHY A STATIC GUARD RATHER THAN A SCREENSHOT. The change only affects hover, focus and selection,
and a governed capture records the DEFAULT state -- so the capture matrix could not see it either
way. Driving those states needs a live browser, and the browser has been unavailable in this
environment: four Playwright launches hung until the 300s cap and reset the shell, on two different
servers. So this file pins the CONTRACT (the rules that produce the states) and the rendered result
stays unverified, which is stated here rather than implied otherwise.

WHY IT MATTERS. The app's own row language states a state by CLARIFYING THE RULE: in this same
stylesheet, a.m-settings-row:hover/:focus-visible does exactly one thing, border-color:
--m-border-strong. The connection row already carried the right material (border-bottom: 1px solid
--m-border) and then painted --m-healthy-wash over it -- a fill where the rest of the app uses a
rule, which is the pattern the owner forbids: parchment is a MATERIAL, separated by hairline and
engraving and never by a tinted fill (2026-09-18).
"""
import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "static/css/meridian" / "settings.css"
ROW = ".m-connection-row-settings"


def _blocks(css, selector):
    """Every rule body whose selector contains `selector`."""
    pattern = re.compile(re.escape(selector) + r"[^{]*\{([^}]*)\}")
    return [m.group(1) for m in pattern.finditer(css)]


def test_hover_and_focus_clarify_the_hairline_instead_of_filling():
    css = CSS.read_text(encoding="utf-8")
    # The selector is outside the body, so match the compound rule directly.
    match = re.search(
        re.escape(ROW) + r":hover,\s*" + re.escape(ROW) + r":focus-visible\s*\{([^}]*)\}", css
    )
    assert match, "the connection row's hover/focus rule is missing"
    body = match.group(1)
    assert "--m-border-strong" in body, "hover no longer clarifies the hairline"
    assert "background" not in body, (
        "hover reintroduced a fill; the app's row language states a state by clarifying the rule"
    )


def test_selection_adds_a_marginal_rule_rather_than_a_fill():
    css = CSS.read_text(encoding="utf-8")
    match = re.search(
        re.escape(ROW) + r'\[aria-pressed="true"\]\s*\{([^}]*)\}', css
    )
    assert match, "the connection row's selected-state rule is missing"
    body = match.group(1)
    assert "box-shadow" in body and "--m-border-strong" in body, (
        "selection no longer draws a hairline down the leading edge"
    )
    assert "background" not in body, "selection reintroduced a tinted fill"


def test_no_connection_row_state_paints_a_tinted_fill():
    """The owner's rule, enforced across every state of this row."""
    css = CSS.read_text(encoding="utf-8")
    for body in _blocks(css, ROW):
        assert "--m-healthy-wash" not in body, (
            "a connection row state paints a tinted fill; separation is by hairline and engraving"
        )
