"""OS-048a: the observed bill -> bill-reserve membership survives ingestion.

The owner's funding source is a Crew funding plan attached to a bill reserve
(D-010). The plans already store their reserve (022), but the bill side dropped the
containing reserve id on the way in, so no join existed and the dial could only say
"funding unknown" for every bill. These tests pin the ingestion half: the id is read,
stored, and never invented or erased by a read that did not observe it.

Nothing here calls a provider. ``sync_live_crew`` accepts a synthetic snapshot, which
is the same production entry point the app uses.
"""

from __future__ import annotations

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.db import run_migrations
from meridian.live import sync_live_crew
from meridian.providers.crewwork import CrewWorkSnapshotAdapter


def _dashboard(bills, *, reserve_fields=None, captured_at="2026-09-11T21:00:00Z"):
    reserve = {"bills": bills}
    if reserve_fields:
        reserve.update(reserve_fields)
    return {
        "mode": "read-only",
        "source": "crew",
        "complete": True,
        "captured_at": captured_at,
        "data": {
            "expenses": {
                "data": {"currentUser": {"accounts": [{"billReserve": reserve}]}}
            }
        },
    }


def _bill(bill_id, name, *, amount_cents=9500, **fields):
    return {
        "id": bill_id,
        "name": name,
        "amount": amount_cents,
        "anchorDate": "2026-01-22",
        "frequency": "MONTHLY",
        **fields,
    }


def _candidate(dashboard, bill_id):
    snapshot = CrewWorkSnapshotAdapter(dashboard).fetch_snapshot()
    return next(c for c in snapshot.commitment_candidates if c.external_id == bill_id)


def test_candidate_carries_the_containing_reserve_id():
    dashboard = _dashboard(
        [_bill("bill-rent", "Rent")], reserve_fields={"id": "reserve-uuid-1"}
    )

    assert _candidate(dashboard, "bill-rent").bill_reserve_id == "reserve-uuid-1"


def test_a_reserve_without_an_id_is_unobserved_not_empty_membership():
    # The older fixtures carry no reserve id. That must read as "not observed", and
    # it must never be turned into a fabricated id.
    dashboard = _dashboard([_bill("bill-rent", "Rent")])

    candidate = _candidate(dashboard, "bill-rent")

    assert candidate.bill_reserve_id == ""
    # The rest of the candidate is unchanged by this slice.
    assert candidate.funded_amount is None


def test_sync_stores_the_membership(tmp_path):
    db_path = str(tmp_path / "gate.db")
    run_migrations(db_path)

    sync_live_crew(
        db_path,
        snapshot=_dashboard(
            [_bill("bill-rent", "Rent")], reserve_fields={"id": "reserve-uuid-1"}
        ),
    )

    stored = CommitmentRepository(db_path).get_commitment_by_legacy("crew", "bill-rent")
    assert stored is not None
    assert stored.bill_reserve_id == "reserve-uuid-1"


def test_an_unobserved_reserve_id_does_not_erase_an_observed_one(tmp_path):
    db_path = str(tmp_path / "gate.db")
    run_migrations(db_path)
    sync_live_crew(
        db_path,
        snapshot=_dashboard(
            [_bill("bill-rent", "Rent")], reserve_fields={"id": "reserve-uuid-1"}
        ),
    )

    # A later complete read that does not report the reserve id is not evidence that
    # the bill left its reserve.
    sync_live_crew(
        db_path,
        snapshot=_dashboard([_bill("bill-rent", "Rent")], captured_at="2026-09-12T21:00:00Z"),
    )

    stored = CommitmentRepository(db_path).get_commitment_by_legacy("crew", "bill-rent")
    assert stored.bill_reserve_id == "reserve-uuid-1"


def test_a_different_observed_reserve_id_replaces_the_membership(tmp_path):
    db_path = str(tmp_path / "gate.db")
    run_migrations(db_path)
    sync_live_crew(
        db_path,
        snapshot=_dashboard(
            [_bill("bill-rent", "Rent")], reserve_fields={"id": "reserve-uuid-1"}
        ),
    )

    # Moving the bill to another reserve in Crew is an observation, and it wins.
    sync_live_crew(
        db_path,
        snapshot=_dashboard(
            [_bill("bill-rent", "Rent")],
            reserve_fields={"id": "reserve-uuid-2"},
            captured_at="2026-09-12T21:00:00Z",
        ),
    )

    stored = CommitmentRepository(db_path).get_commitment_by_legacy("crew", "bill-rent")
    assert stored.bill_reserve_id == "reserve-uuid-2"


def test_membership_survives_a_rename_of_the_bill(tmp_path):
    db_path = str(tmp_path / "gate.db")
    run_migrations(db_path)
    sync_live_crew(
        db_path,
        snapshot=_dashboard(
            [_bill("bill-rent", "State of New Hampshire")],
            reserve_fields={"id": "reserve-uuid-1"},
        ),
    )

    sync_live_crew(
        db_path,
        snapshot=_dashboard(
            [_bill("bill-rent", "Veteran's Home")],
            reserve_fields={"id": "reserve-uuid-1"},
            captured_at="2026-09-12T21:00:00Z",
        ),
    )

    stored = CommitmentRepository(db_path).get_commitment_by_legacy("crew", "bill-rent")
    assert stored.name == "Veteran's Home"
    assert stored.bill_reserve_id == "reserve-uuid-1"


def test_local_commitments_keep_an_unobserved_membership(tmp_path):
    db_path = str(tmp_path / "gate.db")
    run_migrations(db_path)
    repository = CommitmentRepository(db_path)

    created = repository.create(
        type=CommitmentType.BILL, name="Owner bill", amount=10.0, due_date="2026-02-01"
    )

    assert created.bill_reserve_id == ""
    assert repository.get(created.id).bill_reserve_id == ""


def test_membership_round_trips_through_the_commitments_store(tmp_path):
    db_path = str(tmp_path / "gate.db")
    run_migrations(db_path)
    repository = CommitmentRepository(db_path)

    created = repository.create(
        type=CommitmentType.BILL,
        name="Rent",
        amount=1500.0,
        due_date="2026-02-01",
        legacy_source="crew",
        legacy_id="bill-rent",
        bill_reserve_id="reserve-uuid-1",
    )
    assert created.bill_reserve_id == "reserve-uuid-1"
    assert repository.get_commitment_by_legacy("crew", "bill-rent").bill_reserve_id == "reserve-uuid-1"

    updated = repository.update(created.id, bill_reserve_id="reserve-uuid-2")
    assert updated.bill_reserve_id == "reserve-uuid-2"
    assert repository.get(created.id).bill_reserve_id == "reserve-uuid-2"
