"""C02 for bills: a complete Crew read concludes absence for bills it stops returning.

Mirrors the account reconciliation (OS-013): absence is evidence about the local
read model only. The row keeps its history and simply stops being a current
observation, and only a complete, error-free read of that provider may conclude it.
"""

from meridian.commitments import CommitmentRepository, CommitmentStatus, CommitmentType
from meridian.db import run_migrations


def _repo(tmp_path):
    db = str(tmp_path / "m.db")
    run_migrations(db)
    return CommitmentRepository(db)


def _bill(repo, bill_id, name="Verizon", amount=95.0, source="crew"):
    return repo.create(
        type=CommitmentType.BILL,
        name=name,
        amount=amount,
        recurrence="monthly",
        legacy_source=source,
        legacy_id=bill_id,
    )


def test_a_complete_read_archives_a_bill_it_no_longer_returns(tmp_path):
    repo = _repo(tmp_path)
    kept = _bill(repo, "bill-kept", name="Verizon")
    gone = _bill(repo, "bill-gone", name="T-Mobile")

    archived = repo.mark_absent_bills(provider="crew", observed_external_ids=("bill-kept",))

    assert archived == 1
    assert repo.get(kept.id).absent_since is None
    assert repo.get(kept.id).status is CommitmentStatus.ACTIVE
    concluded = repo.get(gone.id)
    assert concluded.absent_since is not None
    assert concluded.status is CommitmentStatus.ARCHIVED
    # History is kept, never deleted.
    assert concluded.amount == 95.0


def test_absence_is_scoped_to_the_reading_provider(tmp_path):
    repo = _repo(tmp_path)
    other = _bill(repo, "sf-1", name="Other", source="simplefin")

    archived = repo.mark_absent_bills(provider="crew", observed_external_ids=("anything",))

    assert archived == 0
    assert repo.get(other.id).absent_since is None


def test_absence_is_never_concluded_from_an_empty_read(tmp_path):
    repo = _repo(tmp_path)
    gone = _bill(repo, "bill-gone")

    archived = repo.mark_absent_bills(provider="crew", observed_external_ids=())

    assert archived == 0
    assert repo.get(gone.id).absent_since is None


def test_absence_is_recorded_once_not_repeatedly(tmp_path):
    repo = _repo(tmp_path)
    gone = _bill(repo, "bill-gone")
    repo.mark_absent_bills(provider="crew", observed_external_ids=("x",))
    first = repo.get(gone.id).absent_since

    again = repo.mark_absent_bills(provider="crew", observed_external_ids=("x",))

    assert again == 0
    assert repo.get(gone.id).absent_since == first


def test_a_bill_with_no_provider_identity_is_never_concluded_absent(tmp_path):
    repo = _repo(tmp_path)
    local = repo.create(
        type=CommitmentType.BILL, name="Local bill", amount=10.0, recurrence="monthly"
    )

    archived = repo.mark_absent_bills(provider="crew", observed_external_ids=("x",))

    assert archived == 0
    assert repo.get(local.id).absent_since is None


def test_reobserving_an_absent_bill_reactivates_it(tmp_path):
    repo = _repo(tmp_path)
    gone = _bill(repo, "bill-gone")
    assert repo.mark_absent_bills(provider="crew", observed_external_ids=("x",)) == 1

    repo.update(gone.id, name="T-Mobile")

    restored = repo.get(gone.id)
    assert restored.absent_since is None
    assert restored.status is CommitmentStatus.ACTIVE


def test_reactivation_does_not_revive_an_owner_archived_bill(tmp_path):
    repo = _repo(tmp_path)
    bill = _bill(repo, "bill-1")
    repo.archive(bill.id)

    repo.update(bill.id, name="Renamed")

    assert repo.get(bill.id).status is CommitmentStatus.ARCHIVED


# --- wiring: only a complete read may conclude absence ---


def _dashboard(bills, *, complete=True):
    return {
        "mode": "read-only",
        "source": "crew",
        "complete": complete,
        "captured_at": "2026-09-11T21:00:00Z",
        "data": {
            "expenses": {
                "data": {
                    "currentUser": {"accounts": [{"billReserve": {"bills": bills}}]}
                }
            }
        },
    }


def _bill_node(bill_id, name, amount_cents=9500):
    return {
        "id": bill_id,
        "name": name,
        "amount": amount_cents,
        "anchorDate": "2026-01-22",
        "frequency": "MONTHLY",
        "reservedAmount": 0,
    }


def test_a_complete_sync_archives_a_bill_crew_stopped_returning(tmp_path):
    from meridian.live import sync_live_crew

    db = str(tmp_path / "m.db")
    run_migrations(db)
    sync_live_crew(
        db,
        snapshot=_dashboard([_bill_node("bill-1", "Verizon"), _bill_node("bill-2", "T-Mobile")]),
    )

    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Verizon")]))

    repo = CommitmentRepository(db)
    assert [c.legacy_id for c in repo.list_active()] == ["bill-1"]
    assert repo.get_commitment_by_legacy("crew", "bill-2").absent_since is not None


def test_an_incomplete_sync_never_concludes_absence(tmp_path):
    from meridian.live import sync_live_crew

    db = str(tmp_path / "m.db")
    run_migrations(db)
    sync_live_crew(
        db,
        snapshot=_dashboard([_bill_node("bill-1", "Verizon"), _bill_node("bill-2", "T-Mobile")]),
    )

    sync_live_crew(db, snapshot=_dashboard([_bill_node("bill-1", "Verizon")], complete=False))

    repo = CommitmentRepository(db)
    assert repo.get_commitment_by_legacy("crew", "bill-2").absent_since is None
    assert len(repo.list_active()) == 2
