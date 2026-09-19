"""The Plan card must not stamp every commitment "FUNDED".

The owner: "All bills report FUNDED whether fully funded or not" -- and sent a screenshot of
two bills reading "Underfunded" beside "FUNDED $0" on the same card. The mobile stacked
layout injected the column label through a `::before` whose `content` was an unconditional
"Funded", so the word was a verdict attached to every row rather than a label attached to a
column.

The figure it labels is Crew's own `reservedAmount` (capped at the bill), which is why the
label is "Reserved": the same word the card's own fact line already uses, and the same word
Crew uses for the field. These tests pin the label to that meaning so the two cannot drift.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_CSS = ROOT / "static/css/meridian/plan.css"
PLAN_HTML = ROOT / "templates/meridian/partials/plan.html"
CREWWORK = ROOT / "meridian/providers/crewwork.py"


def test_the_card_labels_the_figure_reserved_rather_than_asserting_funded():
    css = PLAN_CSS.read_text(encoding="utf-8")
    block = css.split(".m-plan-cell-funded::before {", 1)[1].split("}", 1)[0]

    assert 'content: "Reserved";' in block
    assert 'content: "Funded";' not in block
    # A column label, not a status stamp: the shortfall is already the badge's job.
    assert "color: var(--m-ink-faint);" in block
    assert "var(--m-healthy)" not in block


def test_no_surface_still_labels_the_column_funded():
    """The stacked label and the desktop column header are the same column, so they must
    not disagree -- and a screen reader reads the column header for every cell."""
    css = PLAN_CSS.read_text(encoding="utf-8")
    html = PLAN_HTML.read_text(encoding="utf-8")

    assert 'role="columnheader">Reserved<' in html
    assert 'role="columnheader">Funded<' not in html
    assert 'content: "Funded"' not in css


def test_the_label_matches_what_the_figure_actually_is():
    """`funded` is Crew's `reservedAmount` capped at the bill amount. If that ever stops
    being true, the label "Reserved" becomes the next wrong word."""
    provider = CREWWORK.read_text(encoding="utf-8")
    assert 'reserved = _cents_to_dollars_or_none(bill.get("reservedAmount"))' in provider
    assert "funded_amount=reserved," in provider

    service = (ROOT / "meridian/services/plan.py").read_text(encoding="utf-8")
    assert 'funded = _money(commitment.funded_amount)' in service
    # Capped at the target, so a reserve larger than the bill cannot read as over-funded.
    assert '"funded": float(min(funded, target))' in service
