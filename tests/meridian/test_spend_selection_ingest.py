"""The ingest half of OS-113: a sync records WHICH pocket Crew says the owner spends from.

The three answers are the point, and each is a rule rather than a detail:

  * an observed selection is RECORDED, with the capture identifying the observation;
  * an UNOBSERVED facet records nothing at all, so a failed read cannot become "no selection"
    (the C01 unreported-is-not-zero rule);
  * an adapter that cannot answer records nothing, and a reader that raises never fails the sync —
    provenance must not be able to cost the owner the money that was reconciled.

Every case here runs the real ``sync_provider`` against a real migrated database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from meridian.providers.base import NormalizedAccount, ProviderSnapshot
from meridian.repository import FinancialRepository
from meridian.spend_selection import SpendSelectionStore
from meridian.sync import sync_provider

POCKET = "U3ViYWNjb3VudDplZGM4Y2I4OC1mMjM0LTQzMjEtOGEzYi1kMjc5MGU5ODFhN2E="
OTHER = "U3ViYWNjb3VudDo5OWFkZjc2YS0wZjIyLTQ0ZjctOTg5YS0xNzEwODIyZTY2M2E="


def _snapshot() -> ProviderSnapshot:
    return ProviderSnapshot(
        connection_external_id="crew-household",
        connection_name="Crew",
        accounts=(
            NormalizedAccount(
                external_id=POCKET, name="Safe to Spend", account_type="pocket", balance=15.45,
                source_updated_at="2026-09-25T12:00:00Z",
            ),
        ),
        transactions=(),
        is_complete=True,
    )


class _Base:
    provider_name = "crew"
    connection_external_id = "crew-household"
    connection_name = "Crew"

    def __init__(self, observed, captured_at="2026-09-25T12:00:00+00:00"):
        self._observed = observed
        self._captured_at = captured_at

    def fetch_snapshot(self):
        return _snapshot()

    def readback_capture_time(self):
        return self._captured_at


class ObservedAdapter(_Base):
    def readback_selected_spend_pocket(self):
        return self._observed


class PlainAdapter(_Base):
    """A provider that has no notion of a selected spend pocket (no such method at all)."""


class RaisingAdapter(_Base):
    def readback_selected_spend_pocket(self):
        raise RuntimeError("the cards facet blew up")


@pytest.fixture()
def repository(tmp_path: Path) -> FinancialRepository:
    repo = FinancialRepository(str(tmp_path / "financial.db"))
    return repo


def _rows(repository: FinancialRepository):
    with sqlite3.connect(repository.db_path) as connection:
        return connection.execute(
            "SELECT snapshot_id, observed_at, resolution, selected_external_id, freshness, "
            "assumptions_json FROM crew_spend_selection_observations ORDER BY id"
        ).fetchall()


def test_a_sync_records_the_selection_crew_itself_reports(repository: FinancialRepository):
    report = sync_provider(ObservedAdapter((POCKET,)), repository)
    assert report.status == "complete"
    rows = _rows(repository)
    assert len(rows) == 1
    snapshot_id, observed_at, resolution, selected, freshness, assumptions = rows[0]
    # The CAPTURE identifies the observation, and the capture's own time dates it.
    assert snapshot_id == "crew:2026-09-25T12:00:00+00:00"
    assert observed_at == "2026-09-25T12:00:00+00:00"
    assert resolution == "selected"
    assert selected == POCKET
    assert freshness == "fresh"
    assert "cards facet" in assumptions
    # And the read path's own accessor returns it.
    latest = SpendSelectionStore(repository.db_path).latest()
    assert latest is not None and latest.selected_external_id == POCKET


def test_re_ingesting_one_capture_does_not_add_a_second_observation(repository: FinancialRepository):
    sync_provider(ObservedAdapter((POCKET,)), repository)
    sync_provider(ObservedAdapter((OTHER,)), repository)  # same capture time, different read
    rows = _rows(repository)
    assert len(rows) == 1, "one capture is one observation, whatever a retry reads"
    assert rows[0][3] == POCKET


def test_an_unobserved_facet_records_nothing_at_all(repository: FinancialRepository):
    sync_provider(ObservedAdapter(None), repository)
    assert _rows(repository) == []
    assert SpendSelectionStore(repository.db_path).latest() is None, (
        "an unread facet must stay unobserved rather than becoming 'no selection'"
    )


def test_an_observed_absence_is_recorded_as_such(repository: FinancialRepository):
    sync_provider(ObservedAdapter(()), repository)
    rows = _rows(repository)
    assert len(rows) == 1
    assert rows[0][2] == "none" and rows[0][3] is None


def test_disagreeing_cards_are_recorded_without_choosing(repository: FinancialRepository):
    sync_provider(ObservedAdapter((POCKET, OTHER)), repository)
    rows = _rows(repository)
    assert len(rows) == 1
    assert rows[0][2] == "ambiguous" and rows[0][3] is None


def test_a_provider_without_the_concept_records_nothing(repository: FinancialRepository):
    report = sync_provider(PlainAdapter(None), repository)
    assert report.status == "complete"
    assert _rows(repository) == []


def test_a_failing_reader_never_fails_the_sync(repository: FinancialRepository):
    report = sync_provider(RaisingAdapter(None), repository)
    assert report.status == "complete", "provenance must not be able to fail a sync"
    assert report.accounts_synced == 1
    assert _rows(repository) == []
    # The money still landed: the account was reconciled even though the selection was not recorded.
    with sqlite3.connect(repository.db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM financial_accounts").fetchone()[0]
    assert count == 1


def test_an_incomplete_snapshot_records_its_selection_as_partial(repository: FinancialRepository):
    class PartialAdapter(ObservedAdapter):
        def fetch_snapshot(self):
            snapshot = _snapshot()
            return ProviderSnapshot(
                connection_external_id=snapshot.connection_external_id,
                connection_name=snapshot.connection_name,
                accounts=snapshot.accounts,
                transactions=snapshot.transactions,
                is_complete=False,
            )

    sync_provider(PartialAdapter((POCKET,)), repository)
    rows = _rows(repository)
    assert len(rows) == 1
    assert rows[0][4] == "partial", (
        "a partial read's selection must not be stored as fresh -- the read path dates its claim "
        "with this"
    )
