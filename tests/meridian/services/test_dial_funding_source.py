"""OS-048: the dial names an observed funding source without inventing a reserve.

The owner's complaint was "All the bills also display funding unknown ... they are
funded by Veterans Home" (D-010). Two different questions hide in that sentence and
this slice answers only the first:

* who funds the bill -> an observed fact: the current Crew funding plan attached to
  the reserve that contained the bill, keyed on record ids;
* how much of a dated occurrence is reserved -> still unknown, and the event keeps
  saying so.

These tests pin the honest half: the source is named with its provenance, ambiguity
declines to choose, a missing link is never filled from the sole global plan, and no
reserved amount appears from source identity alone.
"""

from datetime import date

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.repository import FinancialRepository
from meridian.services.dial import build_dial

AS_OF = date(2026, 9, 8)


def _repository(tmp_path) -> FinancialRepository:
    return FinancialRepository(str(tmp_path / "financial.db"))


def _bill(commitments, *, reserve_id="", name="Rent", provider="crew", bill_id="crew-rent"):
    return commitments.create(
        type=CommitmentType.BILL,
        name=name,
        amount=1500.0,
        due_date="2026-09-16",
        recurrence="monthly",
        legacy_source=provider,
        legacy_id=bill_id,
        bill_reserve_id=reserve_id,
    )


def _plan(repository, *, reserve_id="reserve-1", name="Veterans Home", plan_id="plan-1",
          provider="crew", observed_at="2026-09-11T21:00:00Z"):
    return repository.upsert_funding_plan(
        provider=provider,
        external_id=plan_id,
        bill_reserve_id=reserve_id,
        name=name,
        amount=1200.0,
        cadence="semimonthly",
        observed_at=observed_at,
    )


def _bill_event(dial):
    return next(event for event in dial["events"] if event["kind"] == "bill")


def test_an_observed_membership_names_the_funding_source(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository)
    _bill(commitments, reserve_id="reserve-1")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"] == {
        "id": "plan-1",
        "name": "Veterans Home",
        "provider": "crew",
        "cadence": "semimonthly",
        "observedAt": "2026-09-11T21:00:00Z",
        "billReserveId": "reserve-1",
    }
    assert event["fundingSourceAmbiguous"] is False
    assert event["fundingSourceCandidateIds"] == []


def test_source_identity_never_becomes_a_reserved_amount(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository)
    _bill(commitments, reserve_id="reserve-1")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    # The plan holds 1200.00 and the bill is 1500.00; neither number may be presented
    # as what is reserved for this dated occurrence.
    assert event["fundingStatus"] == "unknown"
    assert event["reserved"] is None


def test_a_renamed_plan_is_the_same_source(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository, name="State of New Hampshire")
    _bill(commitments, reserve_id="reserve-1")
    _plan(repository, name="Veterans Home")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"]["id"] == "plan-1"
    assert event["fundingSource"]["name"] == "Veterans Home"


def test_an_unobserved_membership_is_not_filled_from_the_only_plan(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    # Exactly one plan exists in the whole app; it must still not be assumed to fund
    # a bill whose own membership was never observed.
    _plan(repository)
    _bill(commitments, reserve_id="")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"] is None
    assert event["fundingSourceAmbiguous"] is False


def test_a_membership_with_no_matching_plan_stays_unknown(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository, reserve_id="some-other-reserve")
    _bill(commitments, reserve_id="reserve-1")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"] is None


def test_a_retired_plan_no_longer_names_a_source(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository)
    repository.mark_absent_funding_plans(provider="crew", observed_external_ids=())
    _bill(commitments, reserve_id="reserve-1")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"] is None


def test_two_plans_on_one_reserve_are_reported_as_ambiguous(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository, plan_id="plan-1", name="Veterans Home")
    _plan(repository, plan_id="plan-2", name="Second Cadence")
    _bill(commitments, reserve_id="reserve-1")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    # Never pick one of two: report the ambiguity and name neither.
    assert event["fundingSource"] is None
    assert event["fundingSourceAmbiguous"] is True
    assert set(event["fundingSourceCandidateIds"]) == {"plan-1", "plan-2"}


def test_a_plan_from_another_provider_is_not_a_match(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository, provider="other-provider", plan_id="plan-other")
    _bill(commitments, reserve_id="reserve-1", provider="crew")

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"] is None


def test_a_local_bill_is_never_given_a_provider_source(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository)
    # A locally created bill inherits no provider identity, so even a stored reserve
    # id cannot resolve a provider plan for it.
    commitments.create(
        type=CommitmentType.BILL,
        name="Local bill",
        amount=40.0,
        due_date="2026-09-16",
        recurrence="monthly",
        bill_reserve_id="reserve-1",
    )

    event = _bill_event(build_dial(repository, commitments.list_active(), as_of=AS_OF))

    assert event["fundingSource"] is None
