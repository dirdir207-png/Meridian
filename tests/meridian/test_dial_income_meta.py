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

    Before OS-050 no Crew income surface was ingested at all, so `source: "crew"` on an
    income event was false, and it is what made the dial row read "Source: crew" for a figure
    typed into Settings. It also masked the real gap: the owner read that label and reasonably
    concluded the income was coming from Crew.

    OS-050 now DOES ingest the Crew funding plan, so a Crew record can legitimately be the
    source -- but only by way of the resolution, which is what sets it. The point of this test
    is unchanged and now matters more, not less: the income branch must never hardcode an
    attribution, because a hardcoded "crew" would be right for a plan-backed figure and a lie
    for a configured one.
    """
    service = DIAL_PY.read_text(encoding="utf-8")

    # The established vocabulary, unchanged for records that really do come from Crew.
    # The bill and goal branches sit at different nesting depths, so match the expression
    # rather than its indentation.
    assert service.count('if commitment.legacy_source == "crew"') == 2
    assert service.count('else "manual"') == 2
    # And the income branch no longer hardcodes ANY attribution -- neither the false "crew"
    # nor a literal "manual". The source now comes from the resolution, so it cannot drift
    # away from where the amount actually came from.
    assert '"source": "crew",' not in service
    assert 'str(getattr(paycheck, "source", "") or "manual")' in service
    assert 'getattr(paycheck, "observed_at", None)' in service
    assert 'getattr(paycheck, "basis", "") or "configured"' in service


def test_the_locally_configured_figure_keeps_its_local_label_as_the_last_resort():
    """The premise this test used to pin -- *"no Crew income surface is ingested"* -- is now
    FALSE, and this is the revision it existed to force.

    OS-050 (2026-09-19) ingests the Crew bill-reserve funding plan, which the owner confirmed
    IS their income source, so the label the owner reads now comes from the plan's own name
    and the previously-empty evidence is no longer structural. The locally configured figure
    is untouched by that: it is still a local config, still labelled ``manual``/``configured``,
    and still the documented last resort -- the plan outranks it rather than replacing it.

    The retired word list was replaced deliberately: it filtered for "income"/"paycheck"/
    "earning"/"deposit" in the adapter, so a future ingestion path that used different
    vocabulary would slip past it. The assertions below name the ingestion surface itself.
    """
    paycheck = (ROOT / "meridian/paycheck.py").read_text(encoding="utf-8")
    # The amount is still a local config with an honest label, and the plan leg now
    # sits ABOVE it in the documented chain.
    assert "single paycheck config" in paycheck
    assert 'basis="crew_plan"' in paycheck
    assert '"crew_plan" | "aggregate" | "last_known" | "configured"' in paycheck
    # The adapter normalizes the funding-plan surface into the provider snapshot, which is
    # the only thing that makes the plan leg reachable at all.
    provider = (ROOT / "meridian/providers/crewwork.py").read_text(encoding="utf-8")
    assert "FundingPlanCandidate" in provider
    assert "funding_plans=" in provider


def test_the_projection_cites_the_observation_that_anchors_it():
    """Slice 3's acceptance: an observed amount carries its source, its observation time and
    the evidence ids behind it, plus the basis that says how strong the claim is."""
    from datetime import date

    from meridian.paycheck import ResolvedPaycheck
    from meridian.services.dial import _paycheck_events

    resolved = ResolvedPaycheck(
        cadence="monthly",
        amount=1663.00,
        next_date="2026-10-18",
        active=True,
        basis="last_known",
        source="Veterans Home",
        observed_at="2026-09-18",
        evidence_ids=(99,),
        occurrences=1,
    )
    events = _paycheck_events(resolved, date(2026, 9, 19), date(2026, 10, 31))

    assert events, "a resolved paycheck must project at least one occurrence"
    first = events[0]
    assert first["kind"] == "income"
    assert first["source"] == "Veterans Home"
    assert first["observedAt"] == "2026-09-18"
    assert first["evidenceIds"] == ["99"]
    assert first["basis"] == "last_known"
    # The amount is the observed value, not the configured one.
    assert first["amount"]["minor"] == 166300


def test_an_unobserved_amount_cites_nothing_at_all():
    """The honesty case: a configured figure has no observation behind it, so it must not
    borrow one. This is what "never present a forecast as a fact" means in the payload."""
    from datetime import date

    from meridian.paycheck import ResolvedPaycheck
    from meridian.services.dial import _paycheck_events

    resolved = ResolvedPaycheck(
        cadence="biweekly",
        amount=1663.00,
        next_date="2026-10-02",
        active=True,
        basis="configured",
        source="manual",
    )
    events = _paycheck_events(resolved, date(2026, 9, 19), date(2026, 10, 31))

    assert events
    first = events[0]
    assert first["basis"] == "configured"
    assert first["source"] == "manual"
    assert first["observedAt"] is None
    assert first["evidenceIds"] == []
