"""The ingest half of OS-114, driven through the REAL `sync_providers` path.

Two things are proven here, and the second is a gap this work closed:

1. every observed bill's share of the reserve is recorded as history, once per capture, with silence
   kept distinct from zero; and
2. `sync_providers` — the plural entry point, which is the only path that writes commitments — records
   the spend pocket too. Its local wrapper adapter carries none of the readback methods `sync_provider`
   looks for, so before this the selection was silently unobserved on that path.

The mutable side must NOT change: `commitments.funded_amount` keeps behaving exactly as it did, because
history is an addition, not a new source of truth.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from meridian.bill_allocation import BillAllocationStore
from meridian.commitments import CommitmentRepository
from meridian.providers.base import (
    CommitmentCandidate,
    NormalizedAccount,
    ProviderSnapshot,
)
from meridian.repository import FinancialRepository
from meridian.spend_selection import SpendSelectionStore
from meridian.sync import sync_provider, sync_providers

RENT = "QmlsbDphNjcwMDQzNS0xNzc5LTRhOTEtYjMxNS1hNTE3MjlmYTA5NGE="
POCKET = "U3ViYWNjb3VudDplZGM4Y2I4OC1mMjM0LTQzMjEtOGEzYi1kMjc5MGU5ODFhN2E="
CAPTURE = "2026-09-25T19:42:08.674714+00:00"


class Adapter:
    """A Crew-shaped adapter: a snapshot, a capture time, and the selection readback."""

    provider_name = "crew"
    connection_external_id = "crew-household"
    connection_name = "Crew"

    def __init__(self, snapshot, selection=(POCKET,)):
        self.snapshot = snapshot
        self._selection = selection

    def fetch_snapshot(self):
        return self.snapshot

    def readback_capture_time(self):
        return CAPTURE

    def readback_selected_spend_pocket(self, *, include_physical_cards: bool = False):
        return self._selection


def snapshot(candidates) -> ProviderSnapshot:
    return ProviderSnapshot(
        connection_external_id="crew-household",
        connection_name="Crew",
        accounts=(
            NormalizedAccount(
                external_id="crew-checking", name="Checking", account_type="checking",
                balance=250.0, source_updated_at="2026-09-25T00:00:00Z",
            ),
        ),
        transactions=(),
        commitment_candidates=tuple(candidates),
        is_complete=True,
    )


def candidate(external_id, name, funded):
    return CommitmentCandidate(
        external_id=external_id, name=name, amount=1442.0, funded_amount=funded,
        bill_reserve_id="BillReserve:1", reserved_by="2026-10-16",
        estimated_next_funding_amount=663.27,
    )


@pytest.fixture
def repository(tmp_path: Path) -> FinancialRepository:
    return FinancialRepository(str(tmp_path / "ingest.db"))


def test_every_observed_bill_is_recorded_with_its_capture(monkeypatch, repository):
    adapter = Adapter(snapshot([
        candidate(RENT, "Rent", 710.98),
        candidate("QmlsbDp4", "Xfinity", None),
    ]))
    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)

    reports = sync_providers([adapter], repository)

    assert [report.status for report in reports] == ["complete"]
    store = BillAllocationStore(repository.db_path)
    capture = store.allocations_at(CAPTURE)
    assert {row.bill_external_id: row.reserved_amount for row in capture} == {RENT: 710.98, "QmlsbDp4": None}
    # Silence is recorded as silence, and the bill it belongs to is still named at the time of the read.
    silent = store.latest("QmlsbDp4")
    assert silent.is_reported is False and silent.bill_name == "Xfinity"
    # The metadata Crew gives about the reservation travels with the observation.
    assert silent.reserved_by == "2026-10-16"
    assert silent.estimated_next_funding_amount == 663.27


def test_the_spend_pocket_is_recorded_on_the_plural_path_too(monkeypatch, repository):
    """The gap this closed: `sync_providers` used to leave the selection unobserved entirely."""
    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)
    sync_providers([Adapter(snapshot([candidate(RENT, "Rent", 0.0)]))], repository)

    selection = SpendSelectionStore(repository.db_path).latest()
    assert selection is not None, "an ingest through sync_providers must record the selection"
    assert selection.selected_external_id == POCKET
    assert selection.resolution == "selected"


def test_re_ingesting_the_same_capture_adds_no_second_observation(monkeypatch, repository):
    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)
    adapter = Adapter(snapshot([candidate(RENT, "Rent", 710.98)]))
    sync_providers([adapter], repository)
    sync_providers([adapter], repository)

    store = BillAllocationStore(repository.db_path)
    assert len(store.history(RENT)) == 1
    assert len(SpendSelectionStore(repository.db_path).history()) == 1


def test_a_broken_readback_does_not_fail_the_sync(monkeypatch, repository):
    """Provenance must never cost the owner a reconciled run."""
    class Broken(Adapter):
        def readback_capture_time(self):
            raise RuntimeError("no timestamp")

    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)
    reports = sync_providers([Broken(snapshot([candidate(RENT, "Rent", 5.0)]))], repository)

    assert [report.status for report in reports] == ["complete"]
    # The fallback identity is this run's own, so the observation is still recorded and dated.
    assert len(BillAllocationStore(repository.db_path).history(RENT)) == 1


def test_history_is_an_addition_and_the_mutable_column_still_behaves(monkeypatch, repository):
    """`commitments.funded_amount` is unchanged by this work — history does not replace it."""
    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)
    sync_providers([Adapter(snapshot([candidate(RENT, "Rent", 710.98)]))], repository)

    commitment = CommitmentRepository(repository.db_path).get_commitment_by_legacy("crew", RENT)
    assert commitment.funded_amount == 710.98
    assert commitment.reserved_amount_reported is True
    # A LATER capture updates the mutable column, which is exactly why history had to exist.
    later = Adapter(snapshot([candidate(RENT, "Rent", 0.0)]))
    later.readback_capture_time = lambda: "2026-09-30T12:00:00+00:00"
    sync_providers([later], repository)

    commitment = CommitmentRepository(repository.db_path).get_commitment_by_legacy("crew", RENT)
    assert commitment.funded_amount == 0.0
    history = BillAllocationStore(repository.db_path).history(RENT)
    assert [row.reserved_amount for row in history] == [0.0, 710.98], (
        "the overwritten value must survive in history, which is the whole point"
    )


def test_the_SINGULAR_path_records_too_because_that_is_what_production_calls(monkeypatch, repository):
    """The regression this file exists for.

    Production syncs through `sync_provider` (the singular function, called by
    `scripts/meridian_sync_live.py`), while the hooks were first written into `sync_providers`. The
    live history therefore stayed EMPTY while the database was being synced every 15 seconds on
    live money — the worst kind of silent gap, because everything else looked healthy.
    """
    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)
    report = sync_provider(Adapter(snapshot([candidate(RENT, "Rent", 710.98)])), repository)

    assert report.status == "complete"
    history = BillAllocationStore(repository.db_path).history(RENT)
    assert [row.reserved_amount for row in history] == [710.98]
    assert SpendSelectionStore(repository.db_path).latest() is not None


def test_the_plural_wrapper_does_not_hide_the_adapters_readbacks(monkeypatch, repository):
    """`sync_providers` wraps the adapter so the snapshot is not fetched twice; the wrapper must
    forward the readback surfaces rather than swallow them, or the singular hooks above see an
    adapter that cannot answer and record nothing."""
    monkeypatch.setattr("meridian.sync._now_iso", lambda: CAPTURE)
    sync_providers([Adapter(snapshot([candidate(RENT, "Rent", 42.0)]))], repository)

    assert SpendSelectionStore(repository.db_path).latest() is not None
    assert [row.reserved_amount for row in
            BillAllocationStore(repository.db_path).history(RENT)] == [42.0]
