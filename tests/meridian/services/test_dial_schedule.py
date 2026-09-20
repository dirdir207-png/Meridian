from datetime import date

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.repository import FinancialRepository
from meridian.services.dial import build_dial


class _Paycheck:
    active = True
    next_date = "2026-10-05"
    cadence = "monthly"
    amount = 1663.0
    currency = "USD"


def test_dial_emits_next_occurrence_crew_schedule_with_estimate_basis(tmp_path):
    repository = FinancialRepository(str(tmp_path / "financial.db"))
    repository.upsert_funding_plan(
        provider="crew",
        external_id="plan-1",
        bill_reserve_id="reserve-1",
        name="Veterans Home",
        amount=1663.0,
        cadence="biweekly",
        anchor_date="2026-09-04",
        observed_at="2026-09-19T22:00:00Z",
    )
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Rent",
        amount=1442.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-rent",
        bill_reserve_id="reserve-1",
    )

    dial = build_dial(repository, commitments.list_active(), as_of=date(2026, 9, 19), paycheck=_Paycheck())
    event = next(item for item in dial["events"] if item["kind"] == "bill")

    assert event["date"] == "2026-10-16"
    assert event["fundingSchedule"] == {
        "eventDate": "2026-10-02",
        "contribution": {"minor": 66327, "currency": "USD"},
        "deadline": "2026-10-16",
        "nextFundingDate": "2026-10-02",
        "planName": "Veterans Home",
        "basis": "crew_estimate",
        "intervalDays": 14,
    }


def test_dial_has_no_schedule_without_an_observed_plan(tmp_path):
    repository = FinancialRepository(str(tmp_path / "financial.db"))
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Rent",
        amount=1442.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-rent",
        bill_reserve_id="reserve-1",
    )

    dial = build_dial(repository, commitments.list_active(), as_of=date(2026, 9, 19), paycheck=_Paycheck())
    event = next(item for item in dial["events"] if item["kind"] == "bill")
    assert event["fundingSchedule"] is None
