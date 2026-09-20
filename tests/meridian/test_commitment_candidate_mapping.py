"""OS-053: one candidate-to-commitment mapping, one declared fallback.

The same provider read used to be mapped into commitments twice -- once in
``meridian/sync.py::sync_providers`` and once in ``meridian/live.py::sync_live_crew`` --
and the two copies had already drifted. The only visible difference was the fallback for
a bill that reported no frequency: production stored ``monthly`` through one path and
``one_time`` through the other, so the same silence produced two different stored
commitments depending on which entry point ran.

The owner settled the contested part on 2026-09-20 -- *"There is always a frequency"* --
so the divergence has never been exercised on real data and this is a latent defect, not
a data correction: no migration, no backfill, and Crew's own stored recurrence values are
untouched. What these tests pin is the *shape* that keeps it latent:

* one fallback, named and asserted here, so it is a declared decision rather than an
  inline ``or`` that a future edit can quietly change on one side only;
* a test that fails if either entry point stops using the shared mapping, because the
  historical defect was the duplication itself, not the value it produced;
* the C01 distinction on update -- a read that reports nothing must not clear what is
  already known.
"""

import pathlib
from datetime import date

from meridian.commitments import (
    UNREPORTED_RECURRENCE_FALLBACK,
    CandidateObservation,
    Commitment,
    CommitmentRepository,
    CommitmentStatus,
    CommitmentType,
    commitment_fields_from_candidate,
    commitment_update_fields,
    observation_of_candidate,
)
from meridian.db import run_migrations
from meridian.live import sync_live_crew
from meridian.providers.base import CommitmentCandidate, ProviderSnapshot
from meridian.repository import FinancialRepository
from meridian.services.plan import _next_occurrence
from meridian.sync import sync_providers

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class SnapshotAdapter:
    provider_name = "crew"
    connection_external_id = "crew-work-assistant"
    connection_name = "Crew (Work Assistant)"

    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_snapshot(self):
        return self.snapshot


def _migrated(tmp_path) -> str:
    path = tmp_path / "m.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    run_migrations(str(path))
    return str(path)


def _candidate(
    *,
    external_id="bill-1",
    name="Rent",
    amount=1500.0,
    recurrence=None,
    due_date="2026-09-16",
    funded_amount=None,
    bill_reserve_id="res:1",
    estimated_next_funding_amount=None,
    reserved_by=None,
):
    return CommitmentCandidate(
        external_id=external_id,
        name=name,
        amount=amount,
        currency="USD",
        due_date=due_date,
        recurrence=recurrence,
        funded_amount=funded_amount,
        bill_reserve_id=bill_reserve_id,
        estimated_next_funding_amount=estimated_next_funding_amount,
        reserved_by=reserved_by,
    )


def _snapshot(*candidates, complete=True):
    return ProviderSnapshot(
        connection_external_id="crew-work-assistant",
        connection_name="Crew (Work Assistant)",
        accounts=(),
        transactions=(),
        commitment_candidates=candidates,
        is_complete=complete,
    )


def _dashboard(*, frequency, reserved=None, total=3000):
    """A Crew-shaped dashboard whose bill reports ``frequency`` verbatim."""
    bill = {
        "id": "bill-1",
        "name": "Rent",
        "amount": 150000,
        "anchorDate": "2026-09-16",
        "frequency": frequency,
    }
    if reserved is not None:
        bill["reservedAmount"] = reserved
    reserve = {"id": "res:1", "bills": [bill]}
    if total is not None:
        reserve["totalReservedAmount"] = total
    return {
        "mode": "read-only",
        "source": "crew",
        "mutations_enabled": False,
        "complete": True,
        "captured_at": "2026-09-11T21:00:00Z",
        "data": {"expenses": {"data": {"currentUser": {"accounts": [
            {"id": "acct:1", "billReserve": reserve},
        ]}}}},
    }


def _stored(due_date="2026-09-16", recurrence="monthly", funded_amount=500.0, **overrides):
    """A stored commitment row as the update branch receives it."""
    values = {
        "id": 1,
        "type": CommitmentType.BILL,
        "name": "Rent",
        "status": CommitmentStatus.ACTIVE,
        "priority": 0,
        "currency": "USD",
        "target_amount": 1500.0,
        "target_date": None,
        "funded_amount": funded_amount,
        "amount": 1500.0,
        "due_date": due_date,
        "recurrence": recurrence,
        "cadence": None,
        "minimum_payment": None,
        "buffer_minimum": None,
        "payoff_strategy": None,
        "backing_account_id": None,
        "legacy_source": "crew",
        "legacy_id": "bill-1",
        "migration_version": None,
        "created_at": "2026-09-01T00:00:00+00:00",
        "updated_at": "2026-09-01T00:00:00+00:00",
        "bill_reserve_id": "res:1",
        "reserved_amount_reported": True,
        "estimated_next_funding_amount": 700.0,
        "reserved_by": "2026-10-16",
    }
    values.update(overrides)
    return Commitment(**values)


# --------------------------------------------------------------------------------------
# The fallback is one named, declared decision.
# --------------------------------------------------------------------------------------


def test_the_single_fallback_is_monthly_and_the_two_paths_share_it():
    """OS-053's decision, asserted rather than inherited from an inline ``or``.

    This test is deliberately about the constant, not about a defaulting mechanism:
    the point of the slice is that the value is *declared once* and both entry points
    reach the same one. Renaming or repointing it is a product decision, and it should
    have to change this assertion to happen.
    """
    assert UNREPORTED_RECURRENCE_FALLBACK == "monthly"


def test_the_fallback_is_monthly_not_one_time():
    """The two are not equivalent, and this is why the choice was not academic.

    ``one_time`` is real Meridian vocabulary meaning "occurs exactly once and does not
    roll forward", so a bill carrying it is dropped from the foreseeable future once its
    anchor date passes. Crew's anchorDate is frequently in the past, so choosing
    ``one_time`` would erase obligations from the forecast that ``monthly`` keeps. The
    expensive failure is erasing an obligation, not continuing one.
    """
    as_of = date(2026, 9, 6)
    past_anchor = date(2026, 1, 16)

    # A one-time bill keeps its (past) anchor, so it is never a future obligation.
    assert _next_occurrence(past_anchor, "one_time", as_of) == past_anchor
    # The fallback rolls the same anchor forward into the future instead.
    assert _next_occurrence(past_anchor, "monthly", as_of) == date(2026, 9, 16)


def test_an_unreported_frequency_uses_the_fallback_on_create():
    fields = commitment_fields_from_candidate(CandidateObservation(
        external_id="bill-1", name="Rent", amount=1500.0,
    ))

    assert fields["recurrence"] == UNREPORTED_RECURRENCE_FALLBACK


def test_a_reported_frequency_is_never_replaced_by_the_fallback():
    """Crew's own value always wins; the fallback only fills a real silence."""
    fields = commitment_fields_from_candidate(CandidateObservation(
        external_id="bill-1", name="Rent", amount=1500.0, recurrence="weekly",
    ))

    assert fields["recurrence"] == "weekly"


# --------------------------------------------------------------------------------------
# The two halves are the only mapping, and they agree with the loops they replaced.
# --------------------------------------------------------------------------------------


def test_no_entry_point_carries_its_own_candidate_to_commitment_loop():
    """The defect was the duplication, so this pins its absence.

    Both files must reach the shared mapping and neither may re-introduce an inline
    recurrence default. This is a source assertion rather than a behavioural one on
    purpose: after unification the two paths are *supposed* to be identical, so no
    behavioural test can distinguish "unified" from "two copies that agree today" --
    which is exactly the state that drifted in the first place.
    """
    for relative in ("meridian/sync.py", "meridian/live.py"):
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "commitment_fields_from_candidate" in source, relative
        assert "commitment_update_fields" in source, relative
        assert 'or "one_time"' not in source, relative
        assert 'or "monthly"' not in source, relative


def test_the_create_mapping_carries_absence_without_inventing_a_figure():
    """C01 on create: a silent read stores 0.0 but never claims Crew reported it."""
    fields = commitment_fields_from_candidate(CandidateObservation(
        external_id="bill-1", name="Rent", amount=1500.0,
    ))

    # funded_amount is NOT NULL DEFAULT 0, so absence has to be carried by the flag.
    assert fields["funded_amount"] == 0.0
    assert fields["reserved_amount_reported"] is False
    # These columns have no zero default: a missing figure is not a zero.
    assert fields["estimated_next_funding_amount"] is None
    assert fields["reserved_by"] is None
    # Identity is the caller's to supply, not the row content's.
    assert "legacy_id" not in fields
    assert "legacy_source" not in fields


def test_the_create_mapping_marks_a_reported_zero_as_reported():
    fields = commitment_fields_from_candidate(CandidateObservation(
        external_id="bill-1", name="Rent", amount=1500.0, funded_amount=0.0,
    ))

    assert fields["funded_amount"] == 0.0
    assert fields["reserved_amount_reported"] is True


def test_an_update_that_reports_no_recurrence_does_not_clobber_the_stored_one():
    """The branch that matters: C01 means silence keeps the known value."""
    stored = _stored(recurrence="monthly")
    fields = commitment_update_fields(
        CandidateObservation(external_id="bill-1", name="Rent", amount=1500.0),
        stored,
    )

    assert fields["recurrence"] == "monthly"

    # And it is the *stored* value, not the create fallback coincidentally matching.
    assert fields["recurrence"] == stored.recurrence


def test_an_update_never_applies_the_create_fallback():
    """A stored row with no recurrence of its own stays unreported, not defaulted.

    The fallback describes a row being created with nothing observed. On update the
    only correct answers are the observed value or the stored one, because inventing a
    frequency on a row that already exists would overwrite Crew's own record.
    """
    stored = _stored(recurrence=None)
    fields = commitment_update_fields(
        CandidateObservation(external_id="bill-1", name="Rent", amount=1500.0),
        stored,
    )

    assert fields["recurrence"] is None


def test_an_update_keeps_every_known_value_the_read_did_not_restate():
    stored = _stored()
    fields = commitment_update_fields(
        CandidateObservation(external_id="bill-1", name="Rent", amount=1600.0),
        stored,
    )

    # Reported here, so the read wins.
    assert fields["amount"] == 1600.0
    # Not reported, so the stored value stands on every count.
    assert fields["due_date"] == stored.due_date
    assert fields["recurrence"] == stored.recurrence
    assert fields["funded_amount"] == stored.funded_amount
    assert fields["reserved_amount_reported"] is True
    assert fields["bill_reserve_id"] == stored.bill_reserve_id
    assert fields["estimated_next_funding_amount"] == stored.estimated_next_funding_amount
    assert fields["reserved_by"] == stored.reserved_by


def test_an_observed_change_replaces_the_stored_value():
    """Symmetry check: absence preserves, but an observed value does update."""
    stored = _stored()
    fields = commitment_update_fields(
        CandidateObservation(
            external_id="bill-1",
            name="Rent (renamed)",
            amount=1500.0,
            recurrence="weekly",
            bill_reserve_id="res:2",
            funded_amount=0.0,
            estimated_next_funding_amount=125.0,
            reserved_by="2026-11-01",
        ),
        stored,
    )

    assert fields["name"] == "Rent (renamed)"
    assert fields["recurrence"] == "weekly"
    assert fields["bill_reserve_id"] == "res:2"
    assert fields["funded_amount"] == 0.0
    assert fields["reserved_amount_reported"] is True
    assert fields["estimated_next_funding_amount"] == 125.0
    assert fields["reserved_by"] == "2026-11-01"


def test_the_translator_copies_exactly_the_declared_fields():
    """A new candidate field must not reach a commitment row by accident."""
    observation = observation_of_candidate(_candidate(
        recurrence="monthly",
        funded_amount=12.0,
        estimated_next_funding_amount=34.0,
        reserved_by="2026-10-16",
    ))

    assert observation == CandidateObservation(
        external_id="bill-1",
        name="Rent",
        amount=1500.0,
        currency="USD",
        recurrence="monthly",
        due_date="2026-09-16",
        funded_amount=12.0,
        bill_reserve_id="res:1",
        estimated_next_funding_amount=34.0,
        reserved_by="2026-10-16",
    )


# --------------------------------------------------------------------------------------
# Production behaviour, through the real entry points.
# --------------------------------------------------------------------------------------


def test_the_live_path_stores_the_declared_fallback_for_a_frequency_less_bill(tmp_path):
    """The production entry point, reached with the real adapter and dashboard shape.

    Unreachable in practice (Crew always reports a frequency) and therefore a pin on a
    product decision rather than a description of live data: if this ever runs against
    a real account, the read changed.
    """
    db = _migrated(tmp_path)

    sync_live_crew(db, snapshot=_dashboard(frequency=None))

    commitment = _stored_commitment(db)
    assert commitment.recurrence == "monthly"


def test_the_live_path_keeps_crews_own_reported_frequency(tmp_path):
    """The value Crew reports is stored verbatim; the fallback is not involved."""
    db = _migrated(tmp_path)

    sync_live_crew(db, snapshot=_dashboard(frequency="WEEKLY"))

    commitment = _stored_commitment(db)
    assert commitment.recurrence == "weekly"


def test_the_live_path_does_not_clobber_a_known_frequency_on_update(tmp_path):
    """One real sync, then a second read that reports no frequency.

    The stored recurrence must survive the second read (C01): the fallback describes a
    row with no observed frequency at all, and this row has one.
    """
    db = _migrated(tmp_path)

    sync_live_crew(db, snapshot=_dashboard(frequency="MONTHLY"))
    assert _stored_commitment(db).recurrence == "monthly"

    sync_live_crew(db, snapshot=_dashboard(frequency=None))

    assert _stored_commitment(db).recurrence == "monthly"


def _stored_commitment(db):
    return CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")


# --------------------------------------------------------------------------------------
# The parity net: both entry points must agree on recurrence too.
# --------------------------------------------------------------------------------------


def test_both_entry_points_agree_on_a_frequency_less_candidate(tmp_path):
    """OS-053 regression: the exact divergence that existed, pinned across both paths.

    OS-048b pinned the two sites equal on the *reserve* facts, which left recurrence as
    the remaining deliberate, untested divergence. This closes it: no candidate may
    produce a different recurrence depending on which entry point ran.
    """
    live_db = _migrated(tmp_path / "live")
    sync_db = _migrated(tmp_path / "sync")

    sync_live_crew(live_db, snapshot=_dashboard(frequency=None))
    sync_providers([SnapshotAdapter(_snapshot(_candidate(recurrence=None)))],
                   FinancialRepository(sync_db))

    live_commitment = _stored_commitment(live_db)
    sync_commitment = _stored_commitment(sync_db)

    assert live_commitment.recurrence == sync_commitment.recurrence == "monthly"


def test_both_entry_points_agree_on_a_reported_frequency(tmp_path):
    """The ordinary case, so the parity assertion is not only about the fallback."""
    live_db = _migrated(tmp_path / "live")
    sync_db = _migrated(tmp_path / "sync")

    sync_live_crew(live_db, snapshot=_dashboard(frequency="MONTHLY"))
    sync_providers([SnapshotAdapter(_snapshot(_candidate(recurrence="monthly")))],
                   FinancialRepository(sync_db))

    live_commitment = _stored_commitment(live_db)
    sync_commitment = _stored_commitment(sync_db)

    assert live_commitment.recurrence == sync_commitment.recurrence == "monthly"


def test_both_entry_points_agree_across_an_update(tmp_path):
    """Parity on the update branch, which the OS-053 handoff left only partly verified."""
    live_db = _migrated(tmp_path / "live")
    sync_db = _migrated(tmp_path / "sync")

    sync_live_crew(live_db, snapshot=_dashboard(frequency="WEEKLY"))
    sync_providers([SnapshotAdapter(_snapshot(_candidate(recurrence="weekly")))],
                   FinancialRepository(sync_db))

    # Second read reports nothing: both paths must preserve, identically.
    sync_live_crew(live_db, snapshot=_dashboard(frequency=None))
    sync_providers([SnapshotAdapter(_snapshot(_candidate(recurrence=None)))],
                   FinancialRepository(sync_db))

    live_commitment = _stored_commitment(live_db)
    sync_commitment = _stored_commitment(sync_db)

    assert live_commitment.recurrence == sync_commitment.recurrence == "weekly"
