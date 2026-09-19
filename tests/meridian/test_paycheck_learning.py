"""Self-learning paycheck detection tests."""
from datetime import datetime, timezone

from meridian.paycheck_learning import _cadence_guess, learn_paycheck


class Tx:
    def __init__(self, merchant, amount, occurred_at, classification_kind="income"):
        self.merchant = merchant
        self.description = merchant
        self.amount = amount
        self.occurred_at = occurred_at
        self.classification_kind = classification_kind


def _dt(day):
    return datetime(2026, 9, day, 12, 0, tzinfo=timezone.utc).isoformat()


def test_learns_recurring_cash_app_paycheck_collapsing_same_day_pairs():
    """Cash App records a transfer + a split on the same payday; collapse those
    so the cadence reflects the real biweekly period, and detect the amount."""
    txns = [
        Tx("Cash App", 490.25, "2026-07-22T20:01:59+00:00"),
        Tx("Cash App", 490.25, "2026-07-22T20:02:30+00:00"),
        Tx("Cash App", 490.25, "2026-07-22T20:03:00+00:00"),
        Tx("Cash App", 490.25, "2026-08-05T15:00:00+00:00"),
        Tx("Cash App", 490.25, "2026-08-05T15:01:00+00:00"),
        Tx("Cash App", 490.25, "2026-08-19T12:00:00+00:00"),
        Tx("Cash App", 490.25, "2026-08-19T12:01:00+00:00"),
    ]
    learned = learn_paycheck(txns)
    assert learned is not None
    assert learned["source"] == "Cash App"
    # Three pay periods (Jul 22, Aug 5, Aug 19) -> biweekly, ~$980-1470 per period.
    assert learned["cadence"] == "biweekly"
    assert learned["occurrences"] == 3


def test_ignores_one_off_income():
    """A single large deposit is not a paycheck (need >=3 occurrences)."""
    txns = [Tx("Some Employer", 2000.0, "2026-09-01T12:00:00+00:00") for _ in range(2)]
    learned = learn_paycheck(txns)
    assert learned is None


def test_ignores_tiny_or_reimbursement_credits():
    txns = [
        Tx("Splitwise", 59.99, "2026-09-05T02:50:03+00:00", "reimbursement"),
        Tx("Interest paid", 0.46, "2026-09-01T09:46:56+00:00", "income"),
        Tx("Cash App", 490.25, "2026-08-19T20:01:59+00:00", "transfer"),
    ]
    learned = learn_paycheck(txns)
    assert learned is None


def test_reports_amount_variability_range():
    """When the recurring amount varies, the learnt range reflects it."""
    txns = [
        Tx("Employer", 1500.0, "2026-08-01T12:00:00+00:00"),
        Tx("Employer", 1500.0, "2026-08-15T12:00:00+00:00"),
        Tx("Employer", 1750.0, "2026-09-01T12:00:00+00:00"),
    ]
    learned = learn_paycheck(txns)
    assert learned is not None
    assert learned["min_amount"] == 1500.0
    assert learned["max_amount"] == 1750.0
    assert learned["amount"] == 1500.0  # median


def test_cadence_guess_buckets():
    assert _cadence_guess([7, 7]) == ("weekly", 1)
    assert _cadence_guess([14, 14]) == ("biweekly", 1)
    assert _cadence_guess([30, 31]) == ("monthly", 1)


# ---------------------------------------------------------------------------
# OS-051: the learning floor.
#
# Owner, verbatim: "you can implement learn check, but starting at yesterday.
# There needs to be a nested owner operable setting to reset the learning. If I
# change jobs and have a different pay rate, or at a different cadence, weekly vs
# bi weekly for instance, I shouldnt be including the learned pay from previous
# positions" ... "so it needs to be governable and resettable if needed".
#
# A floor changes WHICH observations are learned from. It is not a deletion: no
# financial record may ever be removed by it.
# ---------------------------------------------------------------------------

from meridian.paycheck_learning import (  # noqa: E402
    PaycheckLearningFloorRepository,
    observations_on_or_after,
)


def test_floor_repository_persists_and_round_trips(tmp_path):
    repo = PaycheckLearningFloorRepository(str(tmp_path / "floor.db"))
    assert repo.get() is None

    saved = repo.set("2026-09-18")

    assert saved.floor == "2026-09-18"
    stored = repo.get()
    assert stored == saved
    # Provenance: when the owner set it, not just what they set.
    assert stored.set_at


def test_floor_repository_clear_restores_all_history(tmp_path):
    repo = PaycheckLearningFloorRepository(str(tmp_path / "floor.db"))
    repo.set("2026-09-18")

    repo.clear()

    assert repo.get() is None


def test_floor_is_stored_apart_from_the_paycheck_config(tmp_path):
    """A reset must not be confusable with configuration. The floor lives under its
    own key, so clearing the learned window can never clear the owner's amount."""
    from meridian.paycheck import PaycheckConfig, PaycheckRepository

    db = str(tmp_path / "shared.db")
    PaycheckRepository(db).save(
        PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    )
    floor_repo = PaycheckLearningFloorRepository(db)
    floor_repo.set("2026-09-18")

    floor_repo.clear()

    # The owner's configured figure is untouched by the learning reset.
    configured = PaycheckRepository(db).get()
    assert configured is not None
    assert configured.amount == 1663.00


def test_observations_before_the_floor_are_excluded_and_after_are_kept():
    txns = [
        Tx("Old Employer", 2000.0, "2026-08-01T12:00:00+00:00"),
        Tx("New Employer", 2500.0, "2026-09-18T12:00:00+00:00"),
    ]

    kept = observations_on_or_after(txns, "2026-09-18")

    assert [t.merchant for t in kept] == ["New Employer"]


def test_the_floor_boundary_is_inclusive():
    """The owner said "starting at yesterday", so the floor day itself counts."""
    txns = [Tx("Employer", 2500.0, "2026-09-18T00:00:00+00:00")]

    assert len(observations_on_or_after(txns, "2026-09-18")) == 1


def test_no_floor_keeps_every_observation():
    txns = [
        Tx("Old Employer", 2000.0, "2020-01-01T12:00:00+00:00"),
        Tx("New Employer", 2500.0, "2026-09-18T12:00:00+00:00"),
    ]

    assert observations_on_or_after(txns, None) == list(txns)


def test_learning_ignores_a_previous_jobs_pay_after_a_reset():
    """The owner's stated reason: "I shouldnt be including the learned pay from
    previous positions". Three old deposits would otherwise aggregate happily."""
    old_job = [
        Tx("Old Employer", 1200.0, "2026-06-05T12:00:00+00:00"),
        Tx("Old Employer", 1200.0, "2026-06-19T12:00:00+00:00"),
        Tx("Old Employer", 1200.0, "2026-07-03T12:00:00+00:00"),
    ]
    new_job = [Tx("New Employer", 2500.0, "2026-09-18T12:00:00+00:00")]

    # Without a floor the old job is the dominant recurring cluster...
    assert learn_paycheck([*old_job, *new_job])["amount"] == 1200.0
    # ...and with a floor it is not learnable at all.
    assert learn_paycheck([*old_job, *new_job], floor="2026-09-01") is None


def test_a_floor_that_excludes_everything_learns_nothing_rather_than_guessing():
    old_job = [
        Tx("Old Employer", 1200.0, "2026-06-05T12:00:00+00:00"),
        Tx("Old Employer", 1200.0, "2026-06-19T12:00:00+00:00"),
        Tx("Old Employer", 1200.0, "2026-07-03T12:00:00+00:00"),
    ]

    assert learn_paycheck(old_job, floor="2026-09-19") is None
