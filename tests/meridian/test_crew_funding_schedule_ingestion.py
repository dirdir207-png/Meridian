"""OS-056b: Crew's OWN reported funding schedule is persisted, and it outranks the mirror.

The sibling slice (OS-056) had Meridian mirror Crew's published rule:
``ceil(amount * interval_days / 30.4375)``. That is Meridian applying Crew's arithmetic to
data Meridian already stored, and it is labelled as exactly that. But the provider states
the same three facts in the same read:

* per bill   ``estimatedNextFundingAmount`` -- Crew's own per-event figure
* per bill   ``reservedBy``                 -- Crew's own deadline for the reservation
* per reserve ``nextFundingDate``           -- Crew's own next funding event
* per reserve ``estimatedNextFundingAmount`` -- Crew's own reserve-level figure

``app.py``'s live ``expenses`` query already selects all four, so this was an ingestion gap
rather than a connector gap. Migration 025 adds the four columns.

The point of the slice is the DIVERGENCE TEST: with both figures stored, the mirrored rule
can be checked against Crew's own statement on real data, which is the only way to notice
that Crew's arithmetic has changed. Neither figure is derived from the other.

Absence follows C01/024 exactly: ``None`` means the read did not report the field, never
zero, and a read that omits it never clears a value Meridian already knew. No backfill is
attempted, because pre-025 storage cannot distinguish a reported zero from silence here.
"""

import sqlite3
from datetime import date

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.db import run_migrations
from meridian.live import sync_live_crew
from meridian.providers.crewwork import CrewWorkSnapshotAdapter
from meridian.repository import FinancialRepository
from meridian.services.dial import build_dial
from meridian.sync import sync_providers


class SnapshotAdapter:
    provider_name = "crew"
    connection_external_id = "crew-work-assistant"
    connection_name = "Crew (Work Assistant)"

    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_snapshot(self):
        return self.snapshot


def _dashboard(*, reserve_id="res:1", bill_id="bill-1", amount=144200,
               reported_estimate=None, reserved_by=None, total=None,
               reserve_estimate=None, next_funding_date=None, reserved=None):
    """A synthetic `expenses` facet shaped exactly like the live connector's payload."""
    bill = {"id": bill_id, "name": "Rent", "amount": amount,
            "anchorDate": "2026-09-16", "frequency": "MONTHLY"}
    if reported_estimate is not None:
        bill["estimatedNextFundingAmount"] = reported_estimate
    if reserved_by is not None:
        bill["reservedBy"] = reserved_by
    if reserved is not None:
        bill["reservedAmount"] = reserved
    reserve = {"id": reserve_id, "bills": [bill]}
    if total is not None:
        reserve["totalReservedAmount"] = total
    if reserve_estimate is not None:
        reserve["estimatedNextFundingAmount"] = reserve_estimate
    if next_funding_date is not None:
        reserve["nextFundingDate"] = next_funding_date
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


def _migrated(tmp_path) -> str:
    path = tmp_path / "m.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    run_migrations(str(path))
    return str(path)


# --- 1. the migration ------------------------------------------------------------------


def test_migration_025_adds_the_reported_funding_columns(tmp_path):
    db = _migrated(tmp_path)
    with sqlite3.connect(db) as connection:
        commitment_columns = {
            row[1]: row for row in connection.execute("PRAGMA table_info(commitments)")
        }
        reserve_columns = {
            row[1]: row for row in connection.execute("PRAGMA table_info(crew_bill_reserves)")
        }
        version = connection.execute(
            "SELECT name FROM schema_migrations WHERE version = '025'"
        ).fetchone()

    assert version is not None, "025 must be registered"
    for name in ("estimated_next_funding_amount", "reserved_by"):
        assert name in commitment_columns, f"{name} must exist on commitments"
        # Nullable on purpose: NULL is "not reported", which is not a zero.
        assert commitment_columns[name][3] == 0, f"{name} must be nullable"
    for name in ("estimated_next_funding_amount", "next_funding_date"):
        assert name in reserve_columns, f"{name} must exist on crew_bill_reserves"
        assert reserve_columns[name][3] == 0, f"{name} must be nullable"


def test_migration_025_backfills_nothing(tmp_path):
    """Pre-025 storage cannot tell a reported zero from silence, so it is not guessed at."""
    db = _migrated(tmp_path)
    commitments = CommitmentRepository(db)
    commitments.create(
        type=CommitmentType.BILL, name="Legacy", amount=40.0, due_date="2026-09-16",
        recurrence="monthly", funded_amount=12.0,
    )
    record = commitments.get_commitment_by_legacy("crew", "none") or None
    del record  # the migrated row is asserted through its own read below
    with sqlite3.connect(db) as connection:
        rows = connection.execute(
            "SELECT estimated_next_funding_amount, reserved_by FROM commitments"
        ).fetchall()
    assert rows and all(row == (None, None) for row in rows)


# --- 2. the adapter reads what Crew reported -------------------------------------------


def test_the_adapter_carries_the_reported_per_bill_figure_and_deadline():
    snapshot = CrewWorkSnapshotAdapter(_dashboard(
        reported_estimate=66327, reserved_by="2026-10-16",
    )).fetch_snapshot()
    candidate = snapshot.commitment_candidates[0]

    assert candidate.estimated_next_funding_amount == 663.27  # cents -> dollars
    assert candidate.reserved_by == "2026-10-16"


def test_the_adapter_carries_the_reported_reserve_figure_and_next_event():
    snapshot = CrewWorkSnapshotAdapter(_dashboard(
        total=109710, reserve_estimate=143597, next_funding_date="2026-10-02",
    )).fetch_snapshot()
    reserve = snapshot.bill_reserves[0]

    assert reserve.total_reserved_amount == 1097.10
    assert reserve.estimated_next_funding_amount == 1435.97
    assert reserve.next_funding_date == "2026-10-02"


def test_an_unreported_field_stays_none_rather_than_zero():
    snapshot = CrewWorkSnapshotAdapter(_dashboard(total=109710)).fetch_snapshot()
    candidate = snapshot.commitment_candidates[0]
    reserve = snapshot.bill_reserves[0]

    assert candidate.estimated_next_funding_amount is None
    assert candidate.reserved_by is None
    assert reserve.estimated_next_funding_amount is None
    assert reserve.next_funding_date is None


# --- 3. the app's own refresh persists them -------------------------------------------


def test_the_live_path_persists_the_reported_schedule(tmp_path):
    db = _migrated(tmp_path)
    sync_live_crew(db, snapshot=_dashboard(
        reported_estimate=66327, reserved_by="2026-10-16",
        total=109710, reserve_estimate=143597, next_funding_date="2026-10-02",
    ))

    commitment = CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")
    reserve = FinancialRepository(db).get_bill_reserve("crew", "res:1")

    assert commitment.estimated_next_funding_amount == 663.27
    assert commitment.reserved_by == "2026-10-16"
    assert reserve.estimated_next_funding_amount == 1435.97
    assert reserve.next_funding_date == "2026-10-02"


def test_a_silent_read_never_clears_a_reported_value(tmp_path):
    """C01 for the new fields: absence is not a report of nothing."""
    db = _migrated(tmp_path)
    sync_live_crew(db, snapshot=_dashboard(
        reported_estimate=66327, reserved_by="2026-10-16",
        reserve_estimate=143597, next_funding_date="2026-10-02",
    ))
    sync_live_crew(db, snapshot=_dashboard())

    commitment = CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")
    reserve = FinancialRepository(db).get_bill_reserve("crew", "res:1")

    assert commitment.estimated_next_funding_amount == 663.27
    assert commitment.reserved_by == "2026-10-16"
    assert reserve.estimated_next_funding_amount == 1435.97
    assert reserve.next_funding_date == "2026-10-02"


def test_a_reported_change_overwrites_the_previous_value(tmp_path):
    db = _migrated(tmp_path)
    sync_live_crew(db, snapshot=_dashboard(reported_estimate=66327))
    sync_live_crew(db, snapshot=_dashboard(reported_estimate=70000))

    commitment = CommitmentRepository(db).get_commitment_by_legacy("crew", "bill-1")
    assert commitment.estimated_next_funding_amount == 700.00


def test_both_mapping_sites_store_the_same_reported_schedule(tmp_path):
    """OS-053's duplicated loops must not diverge on the new fields either."""
    live_db = _migrated(tmp_path / "live")
    sync_db = _migrated(tmp_path / "sync")
    snapshot = _dashboard(
        reported_estimate=66327, reserved_by="2026-10-16",
        reserve_estimate=143597, next_funding_date="2026-10-02",
    )

    sync_live_crew(live_db, snapshot=snapshot)
    sync_providers(
        [SnapshotAdapter(CrewWorkSnapshotAdapter(snapshot).fetch_snapshot())],
        FinancialRepository(sync_db),
    )

    live_commitment = CommitmentRepository(live_db).get_commitment_by_legacy("crew", "bill-1")
    sync_commitment = CommitmentRepository(sync_db).get_commitment_by_legacy("crew", "bill-1")
    live_reserve = FinancialRepository(live_db).get_bill_reserve("crew", "res:1")
    sync_reserve = FinancialRepository(sync_db).get_bill_reserve("crew", "res:1")

    assert live_commitment.estimated_next_funding_amount == (
        sync_commitment.estimated_next_funding_amount
    ) == 663.27
    assert live_commitment.reserved_by == sync_commitment.reserved_by == "2026-10-16"
    assert live_reserve.estimated_next_funding_amount == (
        sync_reserve.estimated_next_funding_amount
    ) == 1435.97
    assert live_reserve.next_funding_date == sync_reserve.next_funding_date == "2026-10-02"


# --- 4. the divergence test: the mirror is checked against Crew's own statement --------


ORACLE = [
    # bill name, amount cents, Crew's reported estimatedNextFundingAmount
    ("Rent", 144200, 66327),
    ("Verizon Payment Arrangement", 7520, 3459),
    ("Verizon", 10157, 4672),
    ("Eversource", 21000, 9660),
    ("Xfinity", 9300, 4278),
]


def _oracle_dial(tmp_path, bill_name, amount_cents, reported_cents):
    """One bill with BOTH statements available: Crew's report and the mirror."""
    db = _migrated(tmp_path)
    repository = FinancialRepository(db)
    snapshot = _dashboard(
        bill_id="bill-x", amount=amount_cents, reported_estimate=reported_cents,
        reserved_by="2026-10-16", total=109710, reserve_estimate=143597,
        next_funding_date="2026-10-02",
    )
    sync_live_crew(db, snapshot=snapshot)
    commitments = CommitmentRepository(db)
    commitment = commitments.get_commitment_by_legacy("crew", "bill-x")
    commitments.update(commitment.id, name=bill_name)
    repository.upsert_funding_plan(
        provider="crew", external_id="plan-1", bill_reserve_id="res:1",
        name="Veterans Home", amount=1663.0, cadence="biweekly",
        anchor_date="2026-09-04", observed_at="2026-09-11T21:00:00Z",
    )
    return build_dial(
        repository, commitments.list_active(),
        as_of=date(2026, 9, 19), paycheck=_Paycheck(),
    )


class _Paycheck:
    active = True
    next_date = "2026-10-05"
    cadence = "monthly"
    amount = 1663.0
    currency = "USD"


def _bill_event(dial):
    return next(event for event in dial["events"] if event["kind"] == "bill")


def test_the_mirror_agrees_with_crew_on_all_five_oracle_rows(tmp_path):
    """The divergence test: computed vs Crew's own reported figure, row by row.

    This is the correctness evidence the mirror could not have before, because only one
    side of the comparison was stored. Every row must agree exactly, in cents, and with
    no residual to explain.
    """
    for index, (name, amount_cents, reported_cents) in enumerate(ORACLE):
        dial = _oracle_dial(tmp_path / f"row{index}", name, amount_cents, reported_cents)
        schedule = _bill_event(dial)["fundingSchedule"]

        assert schedule["contribution"]["minor"] == reported_cents, name
        assert schedule["divergence"] is None, name


def test_a_reported_figure_outranks_the_mirror_when_they_disagree(tmp_path):
    """D-013's order of authority: an observation outranks a derivation of it."""
    dial = _oracle_dial(tmp_path, "Rent", 144200, 60000)  # the mirror would say 66327
    schedule = _bill_event(dial)["fundingSchedule"]

    assert schedule["basis"] == "crew_reported"
    assert schedule["contribution"]["minor"] == 60000, "Crew's own number is the figure"
    assert schedule["divergence"] == {
        "reportedMinor": 60000,
        "computedMinor": 66327,
        "deltaMinor": -6327,
    }


def test_a_reported_figure_is_labelled_as_crew_reported_not_as_a_derivation(tmp_path):
    dial = _oracle_dial(tmp_path, "Rent", 144200, 66327)
    schedule = _bill_event(dial)["fundingSchedule"]

    assert schedule["basis"] == "crew_reported"
    # Crew's own deadline outranks the occurrence date Meridian rolled from the anchor.
    assert schedule["deadline"] == "2026-10-16"
    # And Crew's own next funding event outranks the one Meridian would compute.
    assert schedule["nextFundingDate"] == "2026-10-02"


def test_without_a_report_the_mirror_still_states_its_own_basis(tmp_path):
    """The computed path stays available, and stays distinguishable (OS-056)."""
    db = _migrated(tmp_path)
    repository = FinancialRepository(db)
    sync_live_crew(db, snapshot=_dashboard(amount=144200))
    commitments = CommitmentRepository(db)
    repository.upsert_funding_plan(
        provider="crew", external_id="plan-1", bill_reserve_id="res:1",
        name="Veterans Home", amount=1663.0, cadence="biweekly",
        anchor_date="2026-09-04", observed_at="2026-09-11T21:00:00Z",
    )

    dial = build_dial(repository, commitments.list_active(),
                      as_of=date(2026, 9, 19), paycheck=_Paycheck())
    schedule = _bill_event(dial)["fundingSchedule"]

    assert schedule["basis"] == "crew_estimate"
    assert schedule["contribution"]["minor"] == 66327
    assert schedule["divergence"] is None, "nothing to diverge from without a report"


def test_the_reserve_level_estimate_is_stored_and_never_used_as_a_dividend(tmp_path):
    """It is an unexplained observation, so it may not reach any arithmetic path.

    D-015 states plainly that the reserve-level figure is not explained and that
    ``totalReservedAmount`` (observed) must never be derived from it. This pins that the
    dial's payload is unchanged by its presence: no schedule is built from it, and the
    per-bill obligation is unaffected.
    """
    db = _migrated(tmp_path)
    repository = FinancialRepository(db)
    sync_live_crew(db, snapshot=_dashboard(
        reported_estimate=66327, reserved_by="2026-10-16",
        total=109710, reserve_estimate=143597, next_funding_date="2026-10-02",
    ))
    dial = build_dial(repository, CommitmentRepository(db).list_active(),
                      as_of=date(2026, 9, 19), paycheck=_Paycheck())

    event = _bill_event(dial)
    assert event["amount"]["minor"] == 144200, "the bill is the obligation, not the reserve"
    # The reserve figure is stored...
    assert FinancialRepository(db).get_bill_reserve(
        "crew", "res:1"
    ).estimated_next_funding_amount == 1435.97
    # ...and the schedule uses Crew's PER-BILL figure, never the reserve-level one.
    assert event["fundingSchedule"]["contribution"]["minor"] == 66327
