"""Income rows must not carry a funding status.

The owner's own ledger showed "Funding unknown" under a Paycheck row that was displaying
+$1,663.00 -- and it made the amount look unknown, which is why the owner asked where the
payday amount was at all.

Funding is a BILL concept: a bill may or may not have a reserve covering a future
occurrence, and the deliberate honesty rule is that the dial says "unknown" rather than
spreading one reserve across every due date. Income is not funded, it arrives, so the
vocabulary does not apply. The server still emits the field; the rendering is what must not
claim it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAL_JS = ROOT / "static/js/meridian/dial.js"
DIAL_PY = ROOT / "meridian/services/dial.py"


def _render_block() -> str:
    script = DIAL_JS.read_text(encoding="utf-8")
    return script.split('body.className = "obs-event-body";', 1)[1].split(
        "button.append(kind, body, amount);", 1
    )[0]


def test_income_rows_do_not_render_a_funding_status():
    block = _render_block()

    assert 'if (event.kind !== "income") {' in block
    # The meta is created INSIDE that guard, so income rows cannot produce one.
    guard, rest = block.split('if (event.kind !== "income") {', 1)
    assert "obs-event-meta" not in guard
    assert 'meta.textContent = fundingLabel(event.fundingStatus);' in rest
    assert "body.append(meta);" in rest


def test_bills_keep_the_funding_status_including_its_honest_unknown():
    """The rule being removed must not be removed for bills, where "unknown" is the
    deliberate refusal to spread one reserve across every future occurrence."""
    script = DIAL_JS.read_text(encoding="utf-8")
    assert 'unknown: "Funding unknown",' in script
    assert 'reserved: "Reserved",' in script
    assert "function fundingLabel(status)" in script

    service = DIAL_PY.read_text(encoding="utf-8")
    # The bill branch still refuses to claim a reserve covers an occurrence.
    assert '"fundingStatus": "unknown",' in service
    assert "does not safely link one reserve to each" in service
