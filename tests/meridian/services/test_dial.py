from datetime import date, datetime, timezone

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.paycheck import PaycheckConfig
from meridian.repository import FinancialRepository
from meridian.services.dial import build_dial


def _connected_repository(tmp_path):
    repository = FinancialRepository(str(tmp_path / "financial.db"))
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    repository.upsert_account(
        provider="crew",
        external_id="free-to-spend",
        name="Free to Spend",
        account_type="savings",
        balance=1284.52,
        available_balance=1284.52,
        connection_id=run.connection_id,
        source_updated_at="2026-09-08T09:00:00Z",
        synced_at="2026-09-08T09:00:00Z",
    )
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=0,
        errors=0,
    )
    return repository


def test_build_dial_includes_bill_without_false_reserve_claims(tmp_path):
    repository = _connected_repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Electric",
        amount=84.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="crew-electric",
    )

    result = build_dial(
        repository,
        commitments.list_active(),
        as_of=date(2026, 9, 8),
    )

    assert result["today"] == "2026-09-08"
    assert result["horizonEnd"] == "2026-09-22"
    assert result["availableToSpend"] == {
        "minor": 128452,
        "currency": "USD",
    }
    electric = [event for event in result["events"] if event["kind"] == "bill"]
    assert electric
    event = electric[0]
    assert event["date"] == "2026-09-16"
    assert event["title"] == "Electric"
    assert event["amount"] == {"minor": 8400, "currency": "USD"}
    # Until the reserve is linked to a specific occurrence, do not claim a
    # reserved/partial funding state.
    assert event["fundingStatus"] == "unknown"
    assert event["reserved"] is None


def test_build_dial_includes_paycheck_horizon_events(tmp_path):
    repository = _connected_repository(tmp_path)
    paycheck = PaycheckConfig(
        cadence="biweekly",
        amount=1240.0,
        next_date="2026-09-14",
        active=True,
    )

    result = build_dial(
        repository,
        [],
        as_of=date(2026, 9, 8),
        paycheck=paycheck,
    )

    assert result["horizonEnd"] == "2026-09-28"
    income_dates = [event["date"] for event in result["events"] if event["kind"] == "income"]
    assert income_dates == ["2026-09-14", "2026-09-28"]
    assert result["events"][0]["amount"] == {"minor": 124000, "currency": "USD"}


def test_build_dial_returns_empty_horizon_when_no_records(tmp_path, monkeypatch):
    fixed_now = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "meridian.repository._now",
        lambda: fixed_now.isoformat().replace("+00:00", "Z"),
    )
    repository = _connected_repository(tmp_path)
    result = build_dial(
        repository,
        [],
        as_of=fixed_now.date(),
        now=fixed_now,
    )
    assert result["events"] == []
    assert result["freshness"] == "fresh"


def test_build_dial_uses_zero_decimal_currency_minor_units(tmp_path):
    repository = FinancialRepository(str(tmp_path / "financial.db"))
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    repository.upsert_account(
        provider="crew",
        external_id="free-to-spend-jpy",
        name="Free to Spend",
        account_type="savings",
        balance=1000,
        available_balance=1000,
        currency="JPY",
        connection_id=run.connection_id,
        source_updated_at="2026-09-08T09:00:00Z",
        synced_at="2026-09-08T09:00:00Z",
    )
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=0,
        errors=0,
    )

    result = build_dial(repository, [], as_of=date(2026, 9, 8))

    assert result["availableToSpend"] == {"minor": 1000, "currency": "JPY"}


def _store_mail(repo, source_id, title, sender, body="Invoice attached."):
    import hashlib

    data = body.encode()
    return repo.add_item(
        source_kind="mail",
        source_id=source_id,
        mime_type="text/plain",
        content_hash=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        title=title,
        sender=sender,
    )


def test_a_bill_event_carries_the_same_invoice_plan_shows(tmp_path):
    """The owner's requirement, stated as behaviour: "View bill should link to the mail ingested
    invoice we already have attached to the same bill on plan".

    So this asserts the coupling rather than the mechanism -- the dial's event resolves to the SAME
    evidence id and the SAME content URL that `bill_invoice_link` (the Plan surface's matcher)
    resolves the bill to. If the two ever disagreed, Today would open a different document than
    Plan does for one bill, which is the failure this test exists to catch.
    """
    from meridian.evidence import EvidenceRepository
    from meridian.services.plan import bill_invoice_link

    repository = _connected_repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Verizon",
        amount=75.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="crew-verizon",
    )

    evidence = EvidenceRepository(repository.db_path)
    invoice = _store_mail(
        evidence,
        "m-verizon-bill",
        "Your Verizon bill is ready",
        "Verizon <billing@verizon.com>",
    )
    _store_mail(
        evidence,
        "m-verizon-promo",
        "Verizon: upgrade your phone today",
        "Verizon <deals@verizon.com>",
    )

    result = build_dial(
        repository,
        commitments.list_active(),
        as_of=date(2026, 9, 8),
        evidence_repository=evidence,
    )
    bill_events = [event for event in result["events"] if event["kind"] == "bill"]
    assert bill_events, "the bill must produce an event"
    carried = bill_events[0]["invoice"]
    expected = bill_invoice_link(evidence, "Verizon")

    assert carried is not None, "a bill with matching bill mail must carry its invoice"
    assert expected is not None
    assert carried["id"] == expected["id"] == invoice.id
    # The path is the same document Plan opens; the dial appends its ORIGIN so the evidence page's
    # Back control returns to Today rather than to Plan (owner, 2026-09-24: "it's a one way street,
    # we need a back button on those"). Asserted as "the same URL plus a from=" so a future change
    # of origin cannot silently point the two surfaces at different documents.
    assert carried["content_url"] == f"{expected['content_url']}?from=today"
    assert carried["content_url"].startswith(f"/api/meridian/evidence/{invoice.id}/content")
    assert "promo" not in carried["title"].lower(), "a marketing email is not the bill's invoice"


def test_a_bill_without_invoice_mail_carries_no_invoice(tmp_path):
    """The other half: no invoice mail means no invoice, rather than a link to something else. The
    ticket falls back to the Plan workspace in that case, and it must not claim an invoice."""
    from meridian.evidence import EvidenceRepository

    repository = _connected_repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Eversource",
        amount=210.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="crew-eversource",
    )
    evidence = EvidenceRepository(repository.db_path)
    _store_mail(
        evidence,
        "m-unrelated",
        "Your water bill is ready",
        "City Water <billing@citywater.example>",
    )

    result = build_dial(
        repository,
        commitments.list_active(),
        as_of=date(2026, 9, 8),
        evidence_repository=evidence,
    )
    bill_events = [event for event in result["events"] if event["kind"] == "bill"]
    assert bill_events
    assert bill_events[0]["invoice"] is None


def test_the_dial_still_builds_when_the_evidence_store_is_unavailable(tmp_path):
    """An invoice link is a nice-to-have; the dial is the product. A broken evidence store must
    cost the link, not the page."""
    repository = _connected_repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Electric",
        amount=84.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="crew-electric",
    )

    class Exploding:
        def list_items(self, **kwargs):
            raise RuntimeError("evidence store is down")

    result = build_dial(
        repository,
        commitments.list_active(),
        as_of=date(2026, 9, 8),
        evidence_repository=Exploding(),
    )
    assert result["events"], "the dial must still produce its events"
    assert all(event["invoice"] is None for event in result["events"])
