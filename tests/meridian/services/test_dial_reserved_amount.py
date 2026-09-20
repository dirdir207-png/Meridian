"""OS-048b: the dial states a per-bill reserved amount, with its basis.

D-013 permits a per-dated-occurrence reserved figure and fixes the order of
authority: *"Precedence: a provider-reported per-bill figure is an observation and
outranks any Meridian derivation."* The owner's rule for the fallback is an even
allocation of the reserve's total set-aside funds across the bills in that reserve
— one share per bill — while spreading a reserve across future *occurrences* stays
forbidden (D-010).

Two stored facts make that possible and neither existed before migration 024:

* `commitments.funded_amount` is Crew's per-bill `reservedAmount`, and
  `reserved_amount_reported` says whether it was actually reported. The column is
  NOT NULL DEFAULT 0 (C01), so without the flag "Crew reported zero" and "Crew never
  reported it" are the same stored value.
* the reserve's own total set-aside funds (`crew_bill_reserves`), which is the only
  honest dividend for the even split. Dividing the funding plan's own amount, or
  summing the bills, would invent a figure.

The events here are the payload contract, so these tests read them directly. Copy
rendering is pinned separately, under Node, in ``test_dial_js.py``.
"""

from datetime import date

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.repository import FinancialRepository
from meridian.services.dial import build_dial

AS_OF = date(2026, 9, 8)


class _Paycheck:
    """A configured next payday, used only to widen the horizon past one occurrence."""

    active = True
    next_date = "2026-10-05"
    cadence = "semimonthly"
    amount = 1663.0
    currency = "USD"
    source = "crew"
    observed_at = "2026-09-11T21:00:00Z"
    evidence_ids = ()
    basis = "observed"


def _repository(tmp_path) -> FinancialRepository:
    return FinancialRepository(str(tmp_path / "financial.db"))


def _reserve(repository, *, reserve_id="reserve-1", total=3000.0, provider="crew",
             observed_at="2026-09-11T21:00:00Z"):
    """Persist one observed reserve total (Crew's ``billReserve.totalReservedAmount``)."""
    return repository.upsert_bill_reserve(
        provider=provider,
        external_id=reserve_id,
        total_reserved_amount=total,
        observed_at=observed_at,
    )


def _bill(commitments, *, name="Rent", amount=1500.0, funded=0.0, reported=False,
          reserve_id="reserve-1", provider="crew", bill_id=None,
          due_date="2026-09-16", recurrence="monthly"):
    return commitments.create(
        type=CommitmentType.BILL,
        name=name,
        amount=amount,
        due_date=due_date,
        recurrence=recurrence,
        legacy_source=provider,
        legacy_id=bill_id or f"crew-{name.lower()}",
        bill_reserve_id=reserve_id,
        funded_amount=funded,
        reserved_amount_reported=reported,
    )


def _plan(repository, *, reserve_id="reserve-1", name="Veterans Home", plan_id="plan-1"):
    return repository.upsert_funding_plan(
        provider="crew",
        external_id=plan_id,
        bill_reserve_id=reserve_id,
        name=name,
        amount=1200.0,
        cadence="semimonthly",
        observed_at="2026-09-11T21:00:00Z",
    )


def _bill_events(dial):
    return [event for event in dial["events"] if event["kind"] == "bill"]


def _bill_event(dial, name="Rent"):
    return next(event for event in _bill_events(dial) if event["title"] == name)


def _dial(repository, commitments, paycheck=None):
    return build_dial(
        repository,
        commitments.list_active(),
        as_of=AS_OF,
        paycheck=paycheck,
    )


# --- 1. observed outranks derived -------------------------------------------------


def test_an_observed_reserved_amount_wins_over_the_derived_split(tmp_path):
    """D-013: the provider's per-bill figure is an observation, so it outranks a split.

    Both figures are available and they disagree (observed 1200, split 1500). The
    observed one must win, and because it is an observation the payload must not
    carry a divisor or a Meridian attribution.
    """
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _reserve(repository, total=3000.0)  # 3000 across two bills = a 1500 split
    rent = _bill(commitments, funded=1200.0, reported=True)
    _bill(commitments, name="Internet", amount=100.0, funded=60.0, reported=True)

    event = _bill_event(_dial(repository, commitments))

    assert event["reserved"] == {"minor": 120000, "currency": "USD"}
    assert event["fundingStatus"] == "partial"
    assert event["fundingBasis"] == "observed"
    assert event["fundingAttribution"] == "crew"
    assert event["fundingBasisDivisor"] is None
    # The observation time is the row's own last write, which is when the read that
    # reported the amount stored it (023's rule for the membership in the same read).
    assert event["fundingObservedAt"] == commitments.get(rent.id).updated_at


# --- 2. the derived fallback is labelled and attributed to Meridian ---------------


def test_retired_derived_split_stays_unknown(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _reserve(repository, total=3000.0)
    _bill(commitments, funded=0.0, reported=False)
    _bill(commitments, name="Internet", amount=100.0, funded=0.0, reported=False)

    event = _bill_event(_dial(repository, commitments))

    # D-015 retires the even split: a reserve total is not a per-bill balance.
    assert event["reserved"] is None
    assert event["fundingStatus"] == "unknown"
    assert event["fundingBasis"] == "unknown"
    assert event["fundingBasisDivisor"] is None
    assert event["fundingObservedAt"] is None


def test_retired_derived_split_has_no_attribution(tmp_path):
    """D-013: a Meridian-side figure must never be attributed to Crew or read as observed."""
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _reserve(repository, total=3000.0)
    _bill(commitments, funded=0.0, reported=False)
    _bill(commitments, name="Internet", amount=100.0, funded=0.0, reported=False)

    event = _bill_event(_dial(repository, commitments))

    assert event["fundingAttribution"] is None
    assert event["fundingBasis"] == "unknown"
    assert event["fundingBasisDivisor"] is None


def test_retired_derived_split_does_not_create_a_shortfall_figure(tmp_path):
    """The fallback obeys the same shortfall arithmetic as an observation."""
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _reserve(repository, total=3000.0)  # / 3 bills = 1000.00
    _bill(commitments, funded=0.0, reported=False)
    _bill(commitments, name="Internet", amount=100.0, funded=0.0, reported=False)
    _bill(commitments, name="Phone", amount=100.0, funded=0.0, reported=False)

    event = _bill_event(_dial(repository, commitments))

    assert event["reserved"] is None
    assert event["fundingStatus"] == "unknown"
    assert event["fundingBasis"] == "unknown"


def test_an_unobserved_reserve_total_leaves_the_figure_unknown(tmp_path):
    """No total means no dividend, and a missing dividend is not zero."""
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _bill(commitments, funded=0.0, reported=False)

    event = _bill_event(_dial(repository, commitments))

    assert event["reserved"] is None
    assert event["fundingStatus"] == "unknown"
    assert event["fundingBasis"] == "unknown"
    assert event["fundingBasisDivisor"] is None
    assert event["fundingAttribution"] is None


# --- 3. unreported is not zero ----------------------------------------------------


def test_unreported_is_unknown_while_a_reported_zero_is_not_yet_set_aside(tmp_path):
    """C01's distinction, now representable: absence is not an emptied reserve.

    Both rows store ``funded_amount`` 0.0 because the column is NOT NULL, so the
    reported flag is the only thing that separates them. One is ``unknown`` (nothing
    was ever said); the other is ``unfunded`` with basis ``observed`` (Crew said zero,
    which the UI renders as "not yet set aside").
    """
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _bill(commitments, name="Never reported", funded=0.0, reported=False)
    _bill(commitments, name="Reported zero", funded=0.0, reported=True)

    dial = _dial(repository, commitments)

    unreported = _bill_event(dial, "Never reported")
    assert unreported["fundingStatus"] == "unknown"
    assert unreported["reserved"] is None
    assert unreported["fundingBasis"] == "unknown"

    reported = _bill_event(dial, "Reported zero")
    assert reported["fundingStatus"] == "unfunded"
    assert reported["reserved"] is None
    assert reported["fundingBasis"] == "observed"
    assert reported["fundingAttribution"] == "crew"


# --- 4. no negative shortfall -----------------------------------------------------


def test_a_reserved_amount_at_or_above_the_bill_is_covered(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _bill(commitments, name="Exact", funded=1500.0, reported=True, bill_id="crew-exact")
    _bill(commitments, name="Over", funded=1600.0, reported=True, bill_id="crew-over")

    dial = _dial(repository, commitments)

    exact = _bill_event(dial, "Exact")
    assert exact["fundingStatus"] == "reserved"
    assert exact["reserved"] == {"minor": 150000, "currency": "USD"}

    over = _bill_event(dial, "Over")
    # The stored figure is reported as reported; the never-negative remainder is the
    # renderer's clamp, pinned under Node. What matters here is that the status is
    # "reserved", so no shortfall is ever derived from a surplus.
    assert over["fundingStatus"] == "reserved"
    assert over["reserved"] == {"minor": 160000, "currency": "USD"}


# --- 5. one date carries the figure -----------------------------------------------


def test_only_the_earliest_occurrence_in_the_horizon_carries_the_figure(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _reserve(repository, total=3000.0)
    _bill(commitments, funded=1500.0, reported=True)
    _bill(commitments, name="Internet", amount=100.0, funded=0.0, reported=False)

    events = [event for event in _bill_events(_dial(repository, commitments, _Paycheck()))
              if event["title"] == "Rent"]

    assert len(events) >= 2, "the horizon must span more than one occurrence to test this"
    assert events[0]["reserved"] == {"minor": 150000, "currency": "USD"}
    assert events[0]["fundingBasis"] == "observed"
    for later in events[1:]:
        assert later["reserved"] is None
        assert later["fundingStatus"] == "unknown"
        assert later["fundingBasis"] == "unknown"


def test_the_same_reserve_total_is_never_multiplied_by_future_dates(tmp_path):
    """D-010's prohibition, kept after D-013 narrowed it.

    The derived share is one bill's share of the bucket (1000.00 here). If the figure
    were repeated on every future occurrence the horizon would report 3000.00 for a
    single 1500.00 obligation, which is the misreading the ruling exists to prevent.
    """
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _reserve(repository, total=3000.0)
    _bill(commitments, funded=0.0, reported=False)
    _bill(commitments, name="Internet", amount=100.0, funded=0.0, reported=False)
    _bill(commitments, name="Phone", amount=100.0, funded=0.0, reported=False)

    events = [event for event in _bill_events(_dial(repository, commitments, _Paycheck()))
              if event["title"] == "Rent"]

    assert len(events) >= 2
    assert all(event["reserved"] is None for event in events)
    assert all(event["fundingBasis"] == "unknown" for event in events)


# --- 6. D-010 identity survives, and local money is never called Crew's -----------


def test_the_funding_source_stays_on_every_occurrence_while_the_figure_does_not(tmp_path):
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    _plan(repository)
    _reserve(repository, total=3000.0)
    _bill(commitments, funded=1500.0, reported=True)
    _bill(commitments, name="Internet", amount=100.0, funded=0.0, reported=False)

    events = [event for event in _bill_events(_dial(repository, commitments, _Paycheck()))
              if event["title"] == "Rent"]

    assert len(events) >= 2
    for event in events:
        assert event["fundingSource"]["id"] == "plan-1"
    assert events[0]["reserved"] is not None
    assert events[1]["reserved"] is None


def test_a_local_bills_own_reserve_is_never_attributed_to_crew(tmp_path):
    """A Meridian-side figure of the owner's own is stated, and never called Crew's."""
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Local bill",
        amount=40.0,
        due_date="2026-09-16",
        recurrence="monthly",
        funded_amount=25.0,
        reserved_amount_reported=True,
    )

    event = _bill_event(_dial(repository, commitments), "Local bill")

    assert event["reserved"] == {"minor": 2500, "currency": "USD"}
    assert event["fundingStatus"] == "partial"
    assert event["fundingBasis"] == "observed"
    assert event["fundingAttribution"] == "meridian"


def test_a_positive_stored_amount_is_itself_a_statement(tmp_path):
    """A positive amount cannot be the absence of data, so it implies the flag.

    This mirrors the 024 backfill rule for rows written before the column existed:
    ``funded_amount`` only reaches a positive value through something that stated it
    (a Crew report, a legacy balance, or the owner), because absence writes 0.0.
    """
    repository = _repository(tmp_path)
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="Legacy bill",
        amount=40.0,
        due_date="2026-09-16",
        recurrence="monthly",
        funded_amount=12.0,
    )

    event = _bill_event(_dial(repository, commitments), "Legacy bill")

    assert event["fundingBasis"] == "observed"
    assert event["fundingAttribution"] == "meridian"
    assert event["reserved"] == {"minor": 1200, "currency": "USD"}
