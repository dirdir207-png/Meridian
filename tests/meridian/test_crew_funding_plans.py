"""OS-050 — persist the Crew funding plan the sync already fetches.

Owner directive, verbatim: *"Right, it SHOULD be a crew record though, the paycheck"*.

`meridian/live.py::capture_crew_snapshot` fetches a fresh snapshot per sync and nothing
caches it, and `readback_funding_plans()` already parsed `billReserve.fundingPlans` — used
to verify a write and then discarded. So the plan was readable all along and simply never
kept. These tests cover KEEPING it: the row, its reserve identity, and the absence rule.

Nothing here mutates a provider. The only writes are to Meridian's own SQLite, exactly like
the account and transaction ingestion that already exists beside it.
"""

from meridian.providers.base import (
    FundingPlanCandidate,
    NormalizedAccount,
    ProviderSnapshot,
)
from meridian.repository import FinancialRepository
from meridian.sync import sync_providers


def _plan(external_id="plan:1", name="Veterans Home", amount=1663.00, cadence="biweekly",
          anchor_date="2026-09-04", bill_reserve_id="res:1", observed_at="2026-09-19T12:00:00Z"):
    return FundingPlanCandidate(
        external_id=external_id,
        name=name,
        amount=amount,
        bill_reserve_id=bill_reserve_id,
        cadence=cadence,
        anchor_date=anchor_date,
        observed_at=observed_at,
    )


class _Adapter:
    """A read-only adapter over a fixed snapshot, as sync_providers consumes."""

    provider_name = "crew"
    connection_external_id = "crew-work-assistant"
    connection_name = "Crew (Work Assistant)"

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def fetch_snapshot(self):
        return self._snapshot


def _snapshot(*, plans, complete=True, errors=()):
    return ProviderSnapshot(
        connection_external_id="crew-work-assistant",
        connection_name="Crew (Work Assistant)",
        accounts=(NormalizedAccount("acct-1", "Checking", "checking", 100.0),),
        transactions=(),
        funding_plans=plans,
        is_complete=complete,
        errors=tuple(errors),
    )


# --- the row itself -------------------------------------------------------


def test_a_plan_round_trips_with_its_reserve_and_cadence(tmp_path):
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    repository.upsert_funding_plan(
        provider="crew",
        external_id="plan:1",
        bill_reserve_id="res:9",
        name="Veterans Home",
        amount=1663.00,
        cadence="biweekly",
        anchor_date="2026-09-04",
        observed_at="2026-09-19T12:00:00Z",
    )

    stored = repository.list_funding_plans()

    assert len(stored) == 1
    plan = stored[0]
    assert plan.external_id == "plan:1"
    assert plan.name == "Veterans Home"
    assert plan.amount == 1663.00
    assert plan.bill_reserve_id == "res:9"
    assert plan.cadence == "biweekly"
    assert plan.anchor_date == "2026-09-04"
    assert plan.observed_at == "2026-09-19T12:00:00Z"


def test_a_later_read_of_the_same_plan_updates_it_rather_than_duplicating(tmp_path):
    """The plan id is Crew's identity, so a rename in Crew updates the one row. If a
    re-read inserted a second row the app would hold two records for one income source
    and could not say which the owner renamed."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    common = dict(provider="crew", external_id="plan:1", bill_reserve_id="res:9",
                  amount=1663.00, cadence="biweekly", anchor_date="2026-09-04")
    repository.upsert_funding_plan(observed_at="2026-09-19T12:00:00Z",
                                   name="State of New Hampshire", **common)
    repository.upsert_funding_plan(observed_at="2026-09-20T12:00:00Z",
                                   name="Veteran's Home", **common)

    stored = repository.list_funding_plans()

    assert len(stored) == 1
    # The rename is the observed truth, and the timestamp advances with it.
    assert stored[0].name == "Veteran's Home"
    assert stored[0].observed_at == "2026-09-20T12:00:00Z"


def test_a_withdrawn_plan_stops_being_current_without_being_deleted(tmp_path):
    """"delete should delete it in crew and vice versa" (the owner). The READ half of
    that is recognising the withdrawal; the row keeps its history, exactly as an
    archived account or an absent bill does."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    repository.upsert_funding_plan(
        provider="crew", external_id="plan:1", bill_reserve_id="res:9",
        name="Veterans Home", amount=1663.00, cadence="biweekly",
        anchor_date="2026-09-04", observed_at="2026-09-19T12:00:00Z",
    )

    repository.mark_absent_funding_plans(provider="crew", observed_external_ids=())

    assert repository.list_funding_plans() == []
    # The record survives; only its currentness changed.
    assert repository.get_funding_plan("crew", "plan:1").absent_since is not None


def test_a_plan_absent_from_but_re_observed_becomes_current_again(tmp_path):
    """The row was kept, so a re-appearing plan is a fresh observation rather than a
    new record — otherwise a re-created cadence would orphan its own history."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    repository.upsert_funding_plan(
        provider="crew", external_id="plan:1", bill_reserve_id="res:9",
        name="Veterans Home", amount=1663.00, cadence="biweekly",
        anchor_date="2026-09-04", observed_at="2026-09-19T12:00:00Z",
    )
    repository.mark_absent_funding_plans(provider="crew", observed_external_ids=())

    repository.upsert_funding_plan(
        provider="crew", external_id="plan:1", bill_reserve_id="res:9",
        name="Veterans Home", amount=1700.00, cadence="biweekly",
        anchor_date="2026-09-04", observed_at="2026-09-25T12:00:00Z",
    )

    stored = repository.list_funding_plans()
    assert len(stored) == 1
    assert stored[0].amount == 1700.00
    assert stored[0].absent_since is None


# --- ingestion through the sync (the only path that ever sees a fresh snapshot) ---


def test_sync_persists_the_plans_it_observes(tmp_path):
    """The snapshot is never cached on disk, so a plan that is not persisted during the
    sync is gone until the next one. That is the whole gap this slice closes."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))

    sync_providers([_Adapter(_snapshot(plans=(_plan(),)) )], repository)

    stored = repository.list_funding_plans()
    assert [p.external_id for p in stored] == ["plan:1"]
    assert stored[0].name == "Veterans Home"


def test_sync_does_not_conclude_absence_from_an_unobserved_facet(tmp_path):
    """The C01 rule. A facet the connector could not read arrives as ``None``; treating
    that as "no plans" would silently retire a cadence the owner still has, on the
    strength of a failed read."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    sync_providers([_Adapter(_snapshot(plans=(_plan(),)))], repository)

    sync_providers([_Adapter(_snapshot(plans=None))], repository)

    assert len(repository.list_funding_plans()) == 1


def test_sync_does_not_conclude_absence_from_an_incomplete_read(tmp_path):
    """Only a complete, error-free read may conclude a plan is gone — the same condition
    the account and bill absence rules use."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    sync_providers([_Adapter(_snapshot(plans=(_plan(),)))], repository)

    sync_providers([_Adapter(_snapshot(plans=(), complete=False))], repository)

    assert len(repository.list_funding_plans()) == 1


def test_a_complete_read_that_no_longer_returns_a_plan_retires_it(tmp_path):
    """The positive case of the same rule: a complete read that observed the surface and
    found the plan gone is evidence the cadence was removed in Crew."""
    repository = FinancialRepository(str(tmp_path / "plans.db"))
    sync_providers([_Adapter(_snapshot(plans=(_plan(),)))], repository)

    sync_providers([_Adapter(_snapshot(plans=()))], repository)

    assert repository.list_funding_plans() == []
    assert repository.get_funding_plan("crew", "plan:1").absent_since is not None
