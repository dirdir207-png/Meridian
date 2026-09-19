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


def test_the_projection_does_not_claim_crew_provenance_for_a_local_paycheck():
    """The amount comes from the locally configured paycheck, so it must not be attributed
    to Crew.

    Crew's income source is never ingested -- the adapter reads no income surface at all --
    so `source: "crew"` on an income event was false, and it is what made the dial row read
    "Source: crew" for a figure typed into Settings. It also masked the real gap: the owner
    read that label and reasonably concluded the income was coming from Crew.

    A Crew funding plan does exist (name, amount, frequency, anchorDate, billReserveId) and
    the app can already write one, but nothing ingests it yet. Until something does, "manual"
    is the honest word -- the same one the bill and goal branches use for a non-Crew record.
    """
    service = DIAL_PY.read_text(encoding="utf-8")

    # The established vocabulary, unchanged for records that really do come from Crew.
    # The bill and goal branches sit at different nesting depths, so match the expression
    # rather than its indentation.
    assert service.count('if commitment.legacy_source == "crew"') == 2
    assert service.count('else "manual"') == 2
    # And the income branch no longer hardcodes the false attribution.
    assert '"source": "crew",' not in service
    assert service.count('"source": "manual",') == 1


def test_the_paycheck_is_still_described_as_locally_configured():
    """Pin the premise of the fix: if a Crew income surface is ever ingested, this test should
    be the thing that fails and forces the label to be revisited."""
    paycheck = (ROOT / "meridian/paycheck.py").read_text(encoding="utf-8")
    assert "single paycheck config" in paycheck
    provider = (ROOT / "meridian/providers/crewwork.py").read_text(encoding="utf-8")
    for word in ("income", "paycheck", "earning", "deposit"):
        assert word not in provider.lower(), f"adapter now mentions {word!r}; revisit the label"
