"""C01: an unreported reserve is not a zero reserve.

``_cents_to_dollars`` returned 0.0 for a missing field, so a bill whose reserve
Crew never reported was indistinguishable from a bill whose reserve was
explicitly emptied. Because ``funded_amount`` is NOT NULL locally, that
conflation then wrote 0.0 and erased the amount Meridian last knew — the same
family of silent loss the owner reported for the deleted pocket.
"""

from meridian.commitments import CommitmentRepository
from meridian.db import run_migrations
from meridian.providers.crewwork import CrewWorkSnapshotAdapter


def _dashboard(bills):
    return {
        "mode": "read-only",
        "source": "crew",
        "complete": True,
        "captured_at": "2026-09-11T21:00:00Z",
        "data": {
            "expenses": {
                "data": {
                    "currentUser": {"accounts": [{"billReserve": {"bills": bills}}]}
                }
            }
        },
    }


def _bill_node(bill_id, name, amount_cents=9500, **fields):
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


def test_an_unreported_reserve_is_not_read_as_a_zero_reserve():
    dashboard = _dashboard(
        [
            _bill_node("bill-unknown", "No reserve reported"),
            _bill_node("bill-empty", "Empty reserve", reservedAmount=0),
            _bill_node("bill-held", "Reserved", reservedAmount=5000),
        ]
    )

    assert _candidate(dashboard, "bill-unknown").funded_amount is None
    assert _candidate(dashboard, "bill-empty").funded_amount == 0.0
    assert _candidate(dashboard, "bill-held").funded_amount == 50.0


def test_an_unreported_reserve_never_erases_what_meridian_knew(tmp_path):
    """The owner-visible consequence: a silent read must not zero a known reserve."""
    from meridian.live import sync_live_crew

    db = str(tmp_path / "m.db")
    run_migrations(db)

    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Rent", reservedAmount=5000)]))
    repo = CommitmentRepository(db)
    assert repo.get_commitment_by_legacy("crew", "bill-1").funded_amount == 50.0

    # Crew stops reporting the reserve field entirely.
    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Rent")]))

    assert repo.get_commitment_by_legacy("crew", "bill-1").funded_amount == 50.0


def test_an_explicitly_emptied_reserve_does_clear_it(tmp_path):
    """Absence is preserved; a real zero is still recorded as zero."""
    from meridian.live import sync_live_crew

    db = str(tmp_path / "m.db")
    run_migrations(db)

    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Rent", reservedAmount=5000)]))
    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Rent", reservedAmount=0)]))

    assert CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1").funded_amount == 0.0


def test_a_new_bill_with_no_reported_reserve_starts_at_zero(tmp_path):
    """The local column is NOT NULL, and a new bill has no prior knowledge."""
    from meridian.live import sync_live_crew

    db = str(tmp_path / "m.db")
    run_migrations(db)

    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Rent")]))

    assert CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1").funded_amount == 0.0
