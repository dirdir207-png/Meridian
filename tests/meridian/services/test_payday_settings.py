"""OS-051 — the Settings income area must show the learning window it is using.

Owner, verbatim: *"you can implement learn check, but starting at yesterday. There needs
to be a nested owner operable setting to reset the learning."*

The control lives in the Payday & Funding area, so that area has to report the floor it
actually applied — including how many observations it excluded. A reset whose effect is
invisible is not governable, and a figure learned from a windowed history must not look
like one learned from everything.
"""

from datetime import date

import pytest

from meridian.classify import classify_deterministic
from meridian.paycheck_learning import PaycheckLearningFloorRepository
from meridian.repository import FinancialRepository
from meridian.services.payday import build_payday_settings


class _Commitments:
    def get(self, commitment_id):
        return None

    def list_active(self):
        return []


class _Rules:
    def list_all(self):
        return []


@pytest.fixture
def repository(tmp_path):
    return FinancialRepository(str(tmp_path / "payday.db"))


class _Txn:
    """The minimal classification input ``classify_deterministic`` reads."""

    def __init__(self, amount, description, merchant, occurred_at="2026-09-18T12:00:00Z"):
        self.amount = amount
        self.description = description
        self.merchant = merchant
        self.account_type = "checking"
        self.relation_type = None
        self.occurred_at = occurred_at


def _income(repository, account_id, *, external_id, day, amount=2500.0):
    row = repository.upsert_transaction(
        provider="crew",
        external_id=external_id,
        account_id=account_id,
        amount=amount,
        occurred_at=f"{day}T12:00:00Z",
        description="Payroll",
        merchant="Employer",
        status="posted",
    )
    # Income is a CLASSIFICATION, not a transaction column, so it is recorded the same
    # way the sync records it rather than passed to upsert_transaction.
    repository.record_classification(
        row.id,
        classify_deterministic(
            _Txn(amount, "Payroll", "Employer", occurred_at=f"{day}T12:00:00Z")
        ),
    )
    return row


def _account(repository):
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    return repository.upsert_account(
        provider="crew",
        external_id="checking-1",
        name="Checking",
        account_type="checking",
        balance=100.0,
        connection_id=run.connection_id,
    )


def _seed_two_jobs(repository):
    account = _account(repository)
    for index, day in enumerate(["2026-06-05", "2026-06-19", "2026-07-03"], start=1):
        _income(repository, account.id, external_id=f"old-{index}", day=day, amount=1200.0)
    for index, day in enumerate(
        ["2026-09-04", "2026-09-18", "2026-10-02", "2026-10-16"], start=1
    ):
        _income(repository, account.id, external_id=f"new-{index}", day=day)
    return account


def test_without_a_floor_the_learned_window_covers_all_history(repository):
    _seed_two_jobs(repository)

    payload = build_payday_settings(
        repository, _Commitments(), _Rules(), as_of=date(2026, 10, 31)
    )

    learning = payload["learning"]
    assert learning["active"] is False
    assert learning["floor"] is None
    assert learning["excluded"] == 0
    assert learning["included"] > 0


def test_the_floor_narrows_the_learned_window_and_says_how_much_it_excluded(repository):
    _seed_two_jobs(repository)
    PaycheckLearningFloorRepository(repository.db_path).set("2026-09-01")

    payload = build_payday_settings(
        repository, _Commitments(), _Rules(), as_of=date(2026, 10, 31)
    )

    learning = payload["learning"]
    assert learning["active"] is True
    assert learning["floor"] == "2026-09-01"
    assert learning["set_at"]
    # The three old-job deposits are excluded; the four new ones remain.
    assert learning["excluded"] == 3
    assert learning["included"] == 4


def test_the_floor_changes_the_recognised_schedule(repository):
    """The point of the control: what the owner reads must come from the new job once the
    old position is outside the window."""
    _seed_two_jobs(repository)

    before = build_payday_settings(
        repository, _Commitments(), _Rules(), as_of=date(2026, 10, 31)
    )
    PaycheckLearningFloorRepository(repository.db_path).set("2026-09-01")
    after = build_payday_settings(
        repository, _Commitments(), _Rules(), as_of=date(2026, 10, 31)
    )

    # The seven deposits span two jobs with a two-month gap between them, so the
    # unfiltered history matches no single cadence and nothing is recognised...
    assert before["pattern"] is None
    # ...and inside the window the new job's regular biweekly sequence is recognised.
    assert after["pattern"] is not None
    assert after["pattern"]["typical_amount"] == 2500.0
    assert after["pattern"]["evidence_count"] == 4


def test_the_floor_is_resettable_and_restores_the_earlier_window(repository):
    _seed_two_jobs(repository)
    floors = PaycheckLearningFloorRepository(repository.db_path)
    floors.set("2026-09-01")

    floors.clear()
    payload = build_payday_settings(
        repository, _Commitments(), _Rules(), as_of=date(2026, 10, 31)
    )

    assert payload["learning"]["active"] is False
    assert payload["learning"]["excluded"] == 0


def test_no_income_leaves_the_window_reported_and_the_pattern_unavailable(repository):
    _seed_two_jobs(repository)
    floors = PaycheckLearningFloorRepository(repository.db_path)
    floors.set("2026-12-01")

    payload = build_payday_settings(
        repository, _Commitments(), _Rules(), as_of=date(2026, 12, 31)
    )

    # A window that leaves nothing must claim no pattern, and must not fall back to the
    # excluded history to fill the gap.
    assert payload["pattern"] is None
    assert payload["state"] == "unavailable"
    assert payload["learning"]["active"] is True
    assert payload["learning"]["included"] == 0
