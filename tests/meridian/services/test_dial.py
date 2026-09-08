from datetime import date

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


def test_build_dial_returns_empty_horizon_when_no_records(tmp_path):
    repository = _connected_repository(tmp_path)
    result = build_dial(repository, [], as_of=date(2026, 9, 8))
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
