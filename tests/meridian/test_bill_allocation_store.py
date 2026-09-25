"""The reserve's internal allocation, kept as history rather than a single overwritten number.

The owner's correction frames this file: the reserve is ONE bucket, and the per-bill figure is that
bucket's internal allocation. The arithmetic that proves the relationship is checked here on his real
numbers (2026-09-04: the five per-bill values sum to 71098 cents exactly, matching the bucket), and the
cases that matter are the ones a single mutable column cannot express:

* an amount Crew never stated must stay SILENT, not become $0.00 (C01);
* one capture must not be able to rewrite another's history when it is re-ingested;
* the rotation the owner asked about — one bill holding the whole bucket, then none of them — must be
  readable as a series, which is the entire point of the table.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from meridian.bill_allocation import BillAllocationStore, parts_equal_whole
from meridian.db import run_migrations

# Crew's own bill ids, from the owner's live data.
RENT = "QmlsbDphNjcwMDQzNS0xNzc5LTRhOTEtYjMxNS1hNTE3MjlmYTA5NGE="
EVERSOURCE = "QmlsbDo0Y2EzNTc5Zi0zYzJhLTQ3ZjUtOTlkNS1hYzEwYzM0YzRjYTA="
XFINITY = "QmlsbDplNDZiMzg5MC1mNzllLTRlMTctOGU3ZS1lMzlmNGU5Njg4MDY="


@pytest.fixture()
def store(tmp_path: Path) -> BillAllocationStore:
    db_path = tmp_path / "gate.db"
    run_migrations(str(db_path))
    return BillAllocationStore(db_path)


def test_the_owners_real_numbers_prove_parts_equal_the_whole(store: BillAllocationStore):
    """2026-09-04: Rent held 71098 cents while the other four held nothing, and the bucket read 71098.

    This is the check that established the per-bill figure IS the bucket's internal allocation, so it is
    run rather than asserted in prose.
    """
    for bill, amount in ((RENT, 710.98), (EVERSOURCE, 0.0), (XFINITY, 0.0)):
        store.record(
            provider="crew", connection_external_id="crew-1", bill_external_id=bill,
            observed_at="2026-09-04T18:10:19Z", reserved_amount=amount,
            bill_name={"QmlsbDphNjcwMDQzNS0xNzc5LTRhOTEtYjMxNS1hNTE3MjlmYTA5NGE=": "Rent",
                       "QmlsbDo0Y2EzNTc5Zi0zYzJhLTQ3ZjUtOTlkNS1hYzEwYzM0YzRjYTA=": "Eversource",
                       "QmlsbDplNDZiMzg5MC1mNzllLTRlMTctOGU3ZS1lMzlmNGU5Njg4MDY=": "Xfinity"}[bill],
        )

    capture = store.allocations_at("2026-09-04T18:10:19Z")
    assert len(capture) == 3
    assert parts_equal_whole(capture, 710.98) is True
    # The two bills that held nothing are REPORTED zeros, not silence: Crew said 0.
    zero_rows = [item for item in capture if item.reserved_amount == 0.0]
    assert len(zero_rows) == 2 and all(item.is_reported for item in zero_rows)


def test_an_amount_crew_never_stated_is_silence_not_zero(store: BillAllocationStore):
    """C01: the mutable column stores 0.0 with a flag; history stores the distinction itself."""
    row = store.record(
        provider="crew", connection_external_id="crew-1", bill_external_id=XFINITY,
        observed_at="2026-09-25T19:42:00Z", reserved_amount=None, bill_name="Xfinity",
    )

    assert row is not None
    assert row.reserved_amount is None
    assert row.is_reported is False
    evidence = row.as_evidence()
    assert evidence["reserved_amount"] is None
    assert evidence["reserved_amount_reported"] is False


def test_the_schema_itself_refuses_a_reported_amount_that_is_missing(store: BillAllocationStore):
    """The CHECK is the schema's own copy of the rule, so a future writer cannot store the confusion."""
    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(store.db_path) as connection:
            connection.execute(
                "INSERT INTO crew_bill_allocation_observations ("
                " provider, connection_external_id, bill_external_id, observed_at, reserved_amount,"
                " reserved_amount_reported) VALUES ('crew', 'c', 'b', 't', NULL, 1)"
            )
    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(store.db_path) as connection:
            connection.execute(
                "INSERT INTO crew_bill_allocation_observations ("
                " provider, connection_external_id, bill_external_id, observed_at, reserved_amount,"
                " reserved_amount_reported) VALUES ('crew', 'c', 'b', 't', 12.5, 0)"
            )


def test_re_ingesting_one_capture_cannot_rewrite_its_history(store: BillAllocationStore):
    first = store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                         observed_at="2026-09-25T19:42:00Z", reserved_amount=100.0)
    again = store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                         observed_at="2026-09-25T19:42:00Z", reserved_amount=999.0)

    assert first is not None and again is not None
    assert again.reserved_amount == 100.0, "the first observation of a capture stands"
    assert len(store.history(RENT)) == 1


def test_the_rotation_is_readable_as_a_series(store: BillAllocationStore):
    """What the mutable column destroys: Rent holding the bucket, then nothing, then Eversource."""
    store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                 observed_at="2026-09-04T18:10:19Z", reserved_amount=710.98, bill_name="Rent")
    store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                 observed_at="2026-09-25T19:42:08Z", reserved_amount=0.0, bill_name="Safe to Spend")
    store.record(provider="crew", connection_external_id="c", bill_external_id=EVERSOURCE,
                 observed_at="2026-09-30T12:00:00Z", reserved_amount=210.0, bill_name="Eversource")

    rent = store.history(RENT)
    assert [(row.observed_at, row.reserved_amount) for row in rent] == [
        ("2026-09-25T19:42:08Z", 0.0),
        ("2026-09-04T18:10:19Z", 710.98),
    ]
    assert [row.bill_external_id for row in store.allocations_at("2026-09-30T12:00:00Z")] == [EVERSOURCE]
    assert store.capture_times() == (
        "2026-09-30T12:00:00Z", "2026-09-25T19:42:08Z", "2026-09-04T18:10:19Z",
    )
    assert store.latest(RENT).reserved_amount == 0.0


def test_an_observation_without_a_bill_id_is_refused(store: BillAllocationStore):
    assert store.record(provider="crew", connection_external_id="c", bill_external_id="",
                        observed_at="2026-09-25T19:42:00Z", reserved_amount=1.0) is None
    assert store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                        observed_at="", reserved_amount=1.0) is None


def test_parts_equal_whole_declines_to_claim_agreement_it_cannot_show():
    """No bucket total, or no reported amounts, is NOT agreement."""
    assert parts_equal_whole([], 100.0) is None
    assert parts_equal_whole([], None) is None


def test_simulated_history_is_marked_as_such(store: BillAllocationStore):
    """A simulation must never be mistakable for an observation of real money."""
    row = store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                       observed_at="2026-10-02T12:00:00Z", reserved_amount=1663.0,
                       data_mode="simulated")
    assert row is not None and row.data_mode == "simulated"
    with pytest.raises(ValueError):
        store.record(provider="crew", connection_external_id="c", bill_external_id=RENT,
                     observed_at="2026-10-03T12:00:00Z", reserved_amount=1.0, data_mode="wishful")
