"""OS-048b: the observed reserve state is persisted, in both mapping sites.

D-013 permits the dial to state a per-dated-occurrence reserved figure, and names the
even split of the reserve's total set-aside funds as the fallback. That fallback has a
dividend (Crew's ``billReserve.totalReservedAmount``) and this slice stores it: the
connector already read it for write verification (``readback_reserve_totals``) and the
preview read it for its own summary, but nothing persisted it, so no stored read could
divide by it.

The second stored fact is the per-bill one. ``commitments.funded_amount`` is
``REAL NOT NULL DEFAULT 0`` (005) and C01 deliberately pins that a bill whose reserve
Crew never reported reads 0.0 -- the same value as a bill Crew reported as emptied.
``reserved_amount_reported`` records which of those two happened, so the dial can say
"not yet set aside" for a real zero and stay silent for missing data.

Both facts follow the 020/021/022 discipline: absence is recorded rather than deleted,
only a complete read may conclude a withdrawal, and an unobserved facet is evidence of
nothing at all.
"""

from meridian.commitments import CommitmentRepository
from meridian.db import run_migrations
from meridian.live import sync_live_crew
from meridian.providers.base import NormalizedBillReserve, ProviderSnapshot
from meridian.providers.crewwork import CrewWorkSnapshotAdapter
from meridian.repository import FinancialRepository
from meridian.sync import sync_providers


class SnapshotAdapter:
    provider_name = "crew"
    connection_external_id = "crew-work-assistant"
    connection_name = "Crew (Work Assistant)"

    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_snapshot(self):
        return self.snapshot


def _reserve_facet(*, reserve_id="res:1", total=3000, bills=(), plans=(), with_facet=True):
    data = {}
    if with_facet:
        reserve = {"id": reserve_id, "fundingPlans": list(plans), "bills": list(bills)}
        if total is not None:
            reserve["totalReservedAmount"] = total
        data["expenses"] = {"data": {"currentUser": {"accounts": [
            {"id": "acct:1", "billReserve": reserve},
        ]}}}
    return {
        "mode": "read-only",
        "source": "crew",
        "mutations_enabled": False,
        "complete": True,
        "captured_at": "2026-09-11T21:00:00Z",
        "data": data,
    }


def _snapshot(bill_reserves, *, complete=True):
    return ProviderSnapshot(
        connection_external_id="crew-work-assistant",
        connection_name="Crew (Work Assistant)",
        accounts=(),
        transactions=(),
        bill_reserves=bill_reserves,
        is_complete=complete,
    )


def _migrated(tmp_path) -> str:
    path = tmp_path / "m.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    run_migrations(str(path))
    return str(path)


# --- migration ---------------------------------------------------------------------


def test_migration_024_stores_the_reserve_total_and_the_reported_flag(tmp_path):
    import sqlite3

    db = _migrated(tmp_path)
    with sqlite3.connect(db) as connection:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'crew_bill_reserves'"
        ).fetchone()
        columns = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info(commitments)").fetchall()
        }
        version = connection.execute(
            "SELECT name FROM schema_migrations WHERE version = '024'"
        ).fetchone()

    assert table == (1,)
    assert version is not None, "024 must be registered"
    assert "reserved_amount_reported" in columns, "the flag must exist on commitments"
    assert columns["reserved_amount_reported"][3] == 1, "the flag must be NOT NULL"


def test_migration_024_backfills_only_amounts_that_could_have_been_stated(tmp_path, monkeypatch):
    """The backfill is an implication, not a guess.

    A positive ``funded_amount`` cannot be the absence of data: absence writes 0.0, so
    any positive value came from something that stated it. A stored 0.0 stays
    unreported, because that is exactly the case C01 says is indistinguishable.
    """
    import shutil
    import sqlite3

    from meridian import db as db_module

    legacy_migrations = tmp_path / "pre-024-migrations"
    legacy_migrations.mkdir()
    for source in sorted(db_module.MIGRATIONS_DIR.glob("*.sql")):
        if source.name >= "024":
            continue
        shutil.copy(source, legacy_migrations / source.name)

    monkeypatch.setattr(db_module, "MIGRATIONS_DIR", legacy_migrations)
    db = str(tmp_path / "legacy.db")
    assert run_migrations(db)[-1] == "023_commitment_bill_reserve.sql"

    with sqlite3.connect(db) as connection:
        connection.execute(
            "INSERT INTO commitments (type, name, status, priority, currency,"
            " funded_amount, created_at, updated_at) VALUES"
            " ('bill', 'Stated', 'active', 3, 'USD', 50.0, '2026-01-01', '2026-01-01'),"
            " ('bill', 'Silent', 'active', 3, 'USD', 0.0, '2026-01-01', '2026-01-01')"
        )
        connection.commit()

    monkeypatch.undo()
    assert run_migrations(db) == [
        "024_crew_bill_reserve_observations.sql",
        "025_crew_reported_funding_schedule.sql",
        "026_calendar_context.sql",
        "027_ai_run_records.sql",
        "028_allow_negative_bill_reserve.sql",
        "029_crew_pocket_goals.sql",
        "030_crew_spend_selection.sql",
        # 031 keeps the dated per-bill allocation history (OS-114); it applies after 030 and
        # is listed here because this test enumerates every migration the database applies.
        "031_crew_bill_allocation_observations.sql",
    ]

    with sqlite3.connect(db) as connection:
        rows = dict(
            connection.execute(
                "SELECT name, reserved_amount_reported FROM commitments"
            ).fetchall()
        )
    assert rows == {"Stated": 1, "Silent": 0}


# --- provider boundary -------------------------------------------------------------


def test_the_adapter_converts_the_reserve_total_from_cents(tmp_path):
    snapshot = CrewWorkSnapshotAdapter(_reserve_facet(total=3000)).fetch_snapshot()

    assert [entry.total_reserved_amount for entry in snapshot.bill_reserves] == [30.0]
    assert snapshot.bill_reserves[0].external_id == "res:1"
    assert snapshot.bill_reserves[0].observed_at == "2026-09-11T21:00:00Z"


def test_an_unreported_reserve_total_stays_absent_not_zero():
    """C01's rule at the reserve level: missing is not an emptied bucket."""
    snapshot = CrewWorkSnapshotAdapter(_reserve_facet(total=None)).fetch_snapshot()

    assert len(snapshot.bill_reserves) == 1
    assert snapshot.bill_reserves[0].total_reserved_amount is None


def test_a_reported_zero_reserve_total_is_a_real_observation():
    snapshot = CrewWorkSnapshotAdapter(_reserve_facet(total=0)).fetch_snapshot()

    assert snapshot.bill_reserves[0].total_reserved_amount == 0.0


def test_an_unobserved_facet_reports_none_rather_than_empty():
    """``None`` is "not observed"; ``()`` would be "observed as empty"."""
    snapshot = CrewWorkSnapshotAdapter(_reserve_facet(with_facet=False)).fetch_snapshot()

    assert snapshot.bill_reserves is None


# --- persistence -------------------------------------------------------------------


def test_a_provider_read_persists_the_reserve_total(tmp_path):
    repository = FinancialRepository(_migrated(tmp_path))
    sync_providers(
        [SnapshotAdapter(_snapshot((NormalizedBillReserve(
            external_id="res:1", total_reserved_amount=30.0,
            observed_at="2026-09-11T21:00:00Z",
        ),)))],
        repository,
    )

    stored = repository.list_bill_reserves()
    assert [entry.external_id for entry in stored] == ["res:1"]
    assert stored[0].total_reserved_amount == 30.0
    assert stored[0].provider == "crew"
    assert stored[0].observed_at == "2026-09-11T21:00:00Z"


def test_an_unreported_total_never_erases_an_observed_one(tmp_path):
    repository = FinancialRepository(_migrated(tmp_path))
    repository.upsert_bill_reserve(
        provider="crew", external_id="res:1", total_reserved_amount=30.0,
        observed_at="2026-09-11T21:00:00Z",
    )

    repository.upsert_bill_reserve(
        provider="crew", external_id="res:1", total_reserved_amount=None,
        observed_at="2026-09-12T21:00:00Z",
    )

    stored = repository.get_bill_reserve("crew", "res:1")
    assert stored.total_reserved_amount == 30.0


def test_a_withdrawn_reserve_is_excluded_without_being_deleted(tmp_path):
    repository = FinancialRepository(_migrated(tmp_path))
    repository.upsert_bill_reserve(
        provider="crew", external_id="res:1", total_reserved_amount=30.0,
        observed_at="2026-09-11T21:00:00Z",
    )
    repository.mark_absent_bill_reserves(provider="crew", observed_external_ids=())

    assert repository.list_bill_reserves() == []
    assert repository.get_bill_reserve("crew", "res:1").absent_since is not None


def test_a_complete_read_that_no_longer_returns_a_reserve_marks_it_absent(tmp_path):
    repository = FinancialRepository(_migrated(tmp_path))
    sync_providers(
        [SnapshotAdapter(_snapshot((NormalizedBillReserve(
            external_id="res:1", total_reserved_amount=30.0,
        ),)))],
        repository,
    )

    sync_providers([SnapshotAdapter(_snapshot(()))], repository)

    assert repository.list_bill_reserves() == []


def test_a_partial_read_never_concludes_a_reserve_was_withdrawn(tmp_path):
    repository = FinancialRepository(_migrated(tmp_path))
    sync_providers(
        [SnapshotAdapter(_snapshot((NormalizedBillReserve(
            external_id="res:1", total_reserved_amount=30.0,
        ),)))],
        repository,
    )

    sync_providers([SnapshotAdapter(_snapshot((), complete=False))], repository)

    assert [entry.external_id for entry in repository.list_bill_reserves()] == ["res:1"]


# --- both mapping sites ------------------------------------------------------------


def _dashboard(*, total=3000, reserved=None, frequency="MONTHLY"):
    bill = {"id": "bill-1", "name": "Rent", "amount": 150000,
            "anchorDate": "2026-09-16", "frequency": frequency}
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


def test_the_live_crew_path_persists_the_reserve_and_the_reported_flag(tmp_path):
    db = _migrated(tmp_path)
    sync_live_crew(db, snapshot=_dashboard(total=3000, reserved=50000))

    repository = FinancialRepository(db)
    assert repository.get_bill_reserve("crew", "res:1").total_reserved_amount == 30.0
    commitment = CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")
    assert commitment.funded_amount == 500.0
    assert commitment.reserved_amount_reported is True


def test_a_silent_reserve_field_leaves_the_flag_unset(tmp_path):
    """A read that does not report the amount is not a report of nothing."""
    db = _migrated(tmp_path)
    sync_live_crew(db, snapshot=_dashboard(total=3000, reserved=None))

    commitment = CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")
    assert commitment.funded_amount == 0.0
    assert commitment.reserved_amount_reported is False


def test_a_reported_zero_sets_the_flag(tmp_path):
    db = _migrated(tmp_path)
    sync_live_crew(db, snapshot=_dashboard(total=0, reserved=0))

    commitment = CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")
    assert commitment.funded_amount == 0.0
    assert commitment.reserved_amount_reported is True


def test_both_mapping_sites_store_the_same_reserve_facts(tmp_path):
    """OS-053's two candidate-to-commitment loops must not diverge on this field.

    ``sync_providers`` has no production caller while ``live.py`` duplicates its loop;
    OS-048a copied the membership field into both rather than silently changing
    production semantics. The reserve observation and the reported flag are copied the
    same way, and this pins that the two paths agree.

    EXTENDED by OS-053, which unified the two loops into one mapping (see
    ``meridian/commitments.py`` and ``test_commitment_candidate_mapping.py``). This test
    is kept as the safety net that fails if a second copy is ever re-introduced, and it
    now pins ``recurrence`` as well -- the field whose divergence was the original
    defect (``monthly`` in production vs ``one_time`` in the unused copy).
    """
    live_db = _migrated(tmp_path / "live")
    sync_db = _migrated(tmp_path / "sync")

    sync_live_crew(live_db, snapshot=_dashboard(total=3000, reserved=50000))
    sync_providers(
        [SnapshotAdapter(CrewWorkSnapshotAdapter(_dashboard(
            total=3000, reserved=50000,
        )).fetch_snapshot())],
        FinancialRepository(sync_db),
    )

    live_repo = FinancialRepository(live_db)
    sync_repo = FinancialRepository(sync_db)
    live_commitment = CommitmentRepository(live_db).get_commitment_by_legacy("crew", "bill-1")
    sync_commitment = CommitmentRepository(sync_db).get_commitment_by_legacy("crew", "bill-1")

    assert live_repo.get_bill_reserve("crew", "res:1").total_reserved_amount == (
        sync_repo.get_bill_reserve("crew", "res:1").total_reserved_amount
    )
    assert live_commitment.reserved_amount_reported is True
    assert sync_commitment.reserved_amount_reported is True
    assert live_commitment.funded_amount == sync_commitment.funded_amount == 500.0
    # OS-053: the same read must not store a different recurrence on either path.
    assert live_commitment.recurrence == sync_commitment.recurrence == "monthly"
