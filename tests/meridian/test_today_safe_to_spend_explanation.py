"""OS-079 contract: the real Today partial, stylesheet and module carry the affordance.

The behavioural tests live in tests/browser/test_safe_to_spend_explanation.py and run against an
isolated fixture. A fixture mirrors markup, and mirrored markup drifts, so this file pins the same
hooks in the REAL partial -- and pins the three properties the owner actually ruled on:

  1. Completeness is the DATA's job. The panel renders `safe_to_spend.breakdown` as sent; the
     client performs no arithmetic, so it cannot drift from the server that computed the figure.
  2. Hairlines and engraving, never a fill (owner, 2026-09-18).
  3. The rules must be VISIBLE. --m-border measures 1.14:1 against parchment (#e3ded4 on #f4ecdf),
     so it separates nothing; the app's decorative rule is brass.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTIAL = ROOT / "templates" / "meridian" / "partials" / "today.html"
STYLES = ROOT / "static" / "css" / "meridian" / "today.css"
MODULE = ROOT / "static" / "js" / "meridian" / "today.js"
FIXTURE = ROOT / "tests" / "browser" / "fixtures" / "safe-to-spend-explanation.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_the_partial_carries_a_real_button_so_the_disclosure_is_keyboard_reachable():
    partial = _read(PARTIAL)
    assert 'data-sts-explain' in partial
    assert 'type="button"' in partial, "the trigger must be a real button, not a div with a handler"
    assert 'aria-controls="m-sts-explanation"' in partial
    assert 'aria-expanded="false"' in partial, "it must declare its collapsed state up front"
    # The mark is decoration and must not be announced.
    assert 'class="m-sts-explain-mark" aria-hidden="true"' in partial


def test_the_panel_is_present_but_hidden_so_it_cannot_flash_before_the_payload_arrives():
    partial = _read(PARTIAL)
    assert 'data-sts-explanation hidden' in partial
    assert 'id="m-sts-explanation"' in partial, "aria-controls must resolve to this element"


def test_the_label_hook_still_exists_because_today_js_writes_to_it():
    """today.js sets the label text from the payload. Moving the hook onto a wrapper or renaming
    it would throw on every page load, and the button now wraps that span."""
    assert 'class="m-sts-explain-label" data-sts-label' in _read(PARTIAL)
    assert 'root.querySelector("[data-sts-label]")' in _read(MODULE)


def test_the_client_renders_the_servers_lines_and_performs_no_arithmetic():
    """The D-019 rule, as a property of the source: the amounts come from `breakdown`, are handed
    straight to the formatter, and are never added, subtracted or recomputed."""
    module = _read(MODULE)
    body = module.split("function renderSafeToSpendExplanation(root, sts) {", 1)[1].split(
        "\nfunction render(root, payload)", 1
    )[0]
    assert "breakdown.lines" in body
    # The amount is passed STRAIGHT through to the row helper; nothing is added to it on the way.
    assert "row(entry.label, entry.amount)" in body, "lines must be rendered as sent"
    assert "formatCurrency(amount, currency)" in body, "the row helper formats, it does not compute"
    assert "breakdown.result" in body, "the result comes from the payload too, not from the lines"
    for forbidden in ("reduce(", "- entry", "+ entry", "Math."):
        assert forbidden not in body, f"the explanation client must not compute: {forbidden}"


def test_the_panel_is_separated_by_hairlines_and_never_a_fill():
    """Owner, 2026-09-18: hairline and engraving only. The single `background` allowed is the
    engraving's punch-through on the top rule, which masks the rule behind a glyph."""
    styles = _read(STYLES)
    panel = styles.split(".m-sts-explanation {", 1)[1].split("}", 1)[0]
    assert "border-top: 1px solid var(--obs-brass)" in panel
    assert "border-bottom: 1px solid var(--obs-brass)" in panel
    assert "background" not in panel, "the panel must not carry a fill"


def test_the_rules_are_brass_because_the_token_border_is_invisible_on_parchment():
    """Measured, not assumed: --m-border is #e3ded4, which is 1.14:1 on the light theme's
    #f4ecdf canvas -- the value already recorded as a trap in CURRENT_STATUS.md. A ruling that
    requires separation BY hairline is not satisfied by a hairline nobody can see."""
    styles = _read(STYLES)
    section = styles.split("Safe-to-Spend explanation (OS-079)", 1)[1]
    panel = section.split(".m-sts-explanation {", 1)[1].split("}", 1)[0]
    assert "--m-border" not in panel, "the separating rules must not use the invisible border token"
    result_rule = section.split(".m-sts-line--result {", 1)[1].split("}", 1)[0]
    assert "--obs-brass" in result_rule


def test_the_fixture_carries_every_hook_it_needs_and_the_partial_has_them_too():
    """The fixture is a mirror. This makes a one-sided edit fail here rather than leaving the
    browser tests silently exercising markup the product no longer ships."""
    fixture = _read(FIXTURE)
    partial = _read(PARTIAL)
    for hook in (
        "data-sts-explain",
        "data-sts-explanation",
        "data-sts-figure",
        "data-sts-label",
        "data-sts-note",
        "data-sts-horizon",
        "data-sts-observed",
        "data-freshness",
        "data-today-error",
    ):
        assert hook in fixture, f"the fixture is missing {hook}"
        assert hook in partial, f"the real partial no longer carries {hook}"


def test_the_fixture_wraps_its_payload_in_safe_to_spend():
    """The client reads `payload.safe_to_spend || {}`. A fixture that put the object at the top
    level would render the EMPTY state and every behavioural test would pass against nothing."""
    assert '"safe_to_spend": payload' in _read(
        ROOT / "tests" / "browser" / "test_safe_to_spend_explanation.py"
    )
