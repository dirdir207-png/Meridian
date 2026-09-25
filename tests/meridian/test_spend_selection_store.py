"""Crew's observed spend-pocket selection: what may be stored, and what must never be.

The rule this file defends (OS-113): a snapshot can say three things about the selected spend pocket —
"this one", "none", or "the cards disagree" — and an UNOBSERVED facet says nothing at all, which must
be the ABSENCE OF A ROW rather than a stored "none". Collapsing those two would let a facet the
connector failed to read become the claim that the owner has no spend pocket, which is the C01
unreported-is-not-zero rule applied to a setting that changes what Safe to Spend means.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from meridian.db import run_migrations
from meridian.spend_selection import (
    RESOLUTION_AMBIGUOUS,
    RESOLUTION_NONE,
    RESOLUTION_SELECTED,
    SpendSelectionStore,
    resolution_for_observed,
)

# The owner's real pocket, from his own Capture (2026-09-04) and byte-identical to
# financial_accounts.external_id in both readable databases.
POCKET = "U3ViYWNjb3VudDplZGM4Y2I4OC1mMjM0LTQzMjEtOGEzYi1kMjc5MGU5ODFhN2E="
OTHER = "U3ViYWNjb3VudDo5OWFkZjc2YS0wZjIyLTQ0ZjctOTg5YS0xNzEwODIyZTY2M2E="


@pytest.fixture()
def store(tmp_path: Path) -> SpendSelectionStore:
    db_path = tmp_path / "gate.db"
    run_migrations(str(db_path))
    return SpendSelectionStore(db_path)


def test_the_provider_return_value_maps_onto_the_three_storable_answers():
    # The provider method's documented contract, exactly as readback_selected_spend_pocket() states it.
    assert resolution_for_observed(None) is None  # unobserved -> NOTHING is written
    assert resolution_for_observed(()) == RESOLUTION_NONE  # observed, no selection
    assert resolution_for_observed((POCKET,)) == RESOLUTION_SELECTED
    assert resolution_for_observed((POCKET, OTHER)) == RESOLUTION_AMBIGUOUS


def test_an_unobserved_facet_writes_no_row_at_all(store: SpendSelectionStore):
    recorded = store.record(
        provider="crew", connection_external_id="conn", snapshot_id="snap-1",
        observed=None, observed_at="2026-09-25T12:00:00Z",
    )
    assert recorded is None
    assert store.latest() is None, "an unobserved facet must not become a stored answer"


def test_a_single_selection_is_recorded_with_its_provenance(store: SpendSelectionStore):
    row = store.record(
        provider="crew", connection_external_id="conn", snapshot_id="snap-1",
        observed=(POCKET,), observed_at="2026-09-25T12:00:00Z", freshness="fresh",
        confidence=0.9, assumptions=("cards agreed",),
    )
    assert row is not None
    assert row.resolution == RESOLUTION_SELECTED
    assert row.selected_external_id == POCKET
    assert row.is_usable is True
    assert row.observed_at == "2026-09-25T12:00:00Z"
    assert row.confidence == 0.9
    assert row.data_mode == "actual"
    # The provenance a payload may carry, and nothing about balances.
    evidence = row.as_evidence()
    assert evidence["resolution"] == RESOLUTION_SELECTED
    assert evidence["snapshot_id"] == "snap-1"
    assert "balance" not in evidence


def test_an_observed_absence_is_stored_as_an_answer_but_is_not_usable(store: SpendSelectionStore):
    row = store.record(
        provider="crew", connection_external_id="conn", snapshot_id="snap-2",
        observed=(), observed_at="2026-09-25T13:00:00Z",
    )
    assert row is not None and row.resolution == RESOLUTION_NONE
    assert row.selected_external_id is None
    assert row.is_usable is False, (
        "an observed absence is an answer a caller must fall back from, never one it may resolve"
    )


def test_disagreeing_cards_are_kept_as_ambiguous_and_choose_nothing(store: SpendSelectionStore):
    row = store.record(
        provider="crew", connection_external_id="conn", snapshot_id="snap-3",
        observed=(POCKET, OTHER), observed_at="2026-09-25T14:00:00Z",
    )
    assert row is not None and row.resolution == RESOLUTION_AMBIGUOUS
    assert row.selected_external_id is None, "an ambiguous read must not pick one of the two"
    assert set(row.observed_external_ids) == {POCKET, OTHER}
    assert row.is_usable is False


def test_the_newest_observation_wins_and_its_date_is_visible(store: SpendSelectionStore):
    store.record(provider="crew", connection_external_id="conn", snapshot_id="old",
                 observed=(OTHER,), observed_at="2026-09-01T00:00:00Z")
    store.record(provider="crew", connection_external_id="conn", snapshot_id="new",
                 observed=(POCKET,), observed_at="2026-09-25T00:00:00Z")
    latest = store.latest()
    assert latest is not None and latest.selected_external_id == POCKET
    assert latest.observed_at == "2026-09-25T00:00:00Z"
    history = store.history()
    assert [row.snapshot_id for row in history] == ["new", "old"]


def test_re_ingesting_one_snapshot_cannot_manufacture_a_second_selection(
    store: SpendSelectionStore,
):
    first = store.record(provider="crew", connection_external_id="conn", snapshot_id="snap-x",
                         observed=(POCKET,), observed_at="2026-09-25T12:00:00Z")
    again = store.record(provider="crew", connection_external_id="conn", snapshot_id="snap-x",
                         observed=(OTHER,), observed_at="2026-09-25T12:00:00Z")
    assert first is not None and again is not None
    assert again.selected_external_id == POCKET, "the first observation of a snapshot stands"
    assert len(store.history()) == 1


def test_the_schema_refuses_a_selected_row_without_an_id(store: SpendSelectionStore):
    # The CHECK constraint is the schema's own copy of the rule, so a future writer cannot store a
    # 'selected' resolution that names nothing.
    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(store.db_path) as connection:
            connection.execute(
                """INSERT INTO crew_spend_selection_observations (
                       provider, connection_external_id, snapshot_id, observed_at, resolution,
                       selected_external_id, freshness
                   ) VALUES ('crew', 'conn', 'snap-z', '2026-09-25T12:00:00Z', 'selected', NULL,
                             'fresh')"""
            )


def test_an_unknown_freshness_is_refused_rather_than_stored(store: SpendSelectionStore):
    with pytest.raises(ValueError):
        store.record(provider="crew", connection_external_id="conn", snapshot_id="snap-f",
                     observed=(POCKET,), observed_at="2026-09-25T12:00:00Z", freshness="probably-fine")
