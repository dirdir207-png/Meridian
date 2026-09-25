"""Crew's observed spend-pocket selection — recorded, dated, and read back in ONE place.

**Why this exists (OS-113, owner-approved 2026-09-25).** ``meridian/services/spend_pocket.py`` decided
which Crew pocket is the discretionary spend pocket by matching an English name. That mechanism is
measurably ambiguous, not merely inelegant: in ``gate.db`` the allow-list matches both ``'Safe to
Spend'`` (active) and ``'Free to Spend'`` (inactive since 2026-09-17), and in ``savings_data.db`` it
matches two ACTIVE pockets both named ``'Free to Spend'`` — no name-based rule can tell those apart.

Crew publishes the answer itself. ``userSpendConfig.selectedSpendSubaccount`` is a per-user setting
repeated on every virtual and physical card, the connector has always fetched it, and
``CrewWorkSnapshotAdapter.readback_selected_spend_pocket()`` already reads it with the right semantics.
Run over the owner's real historical capture that method returns exactly one id —
``Subaccount:edc8cb88-f234-4321-8a3b-d2790e981a7a`` — which is byte-identical to
``financial_accounts.external_id`` for the pocket now named ``'Safe to Spend'``.

**What is stored, and what is deliberately not.** A row records what ONE snapshot said, and only in
the three forms a snapshot can actually take:

    resolution = 'selected'   exactly one id, and ``selected_external_id`` carries it
    resolution = 'none'       the facet was observed and exposed no selection
    resolution = 'ambiguous'  the cards disagreed; the observed ids are kept, nothing is chosen

An UNOBSERVED facet writes no row at all. Storing it as ``'none'`` would collapse "Crew did not say"
into "Crew said no", which is the C01 unreported-is-not-zero rule applied to this setting.

**Reading it is not the same as trusting it.** ``latest()`` returns the newest row with its
``observed_at``, ``freshness`` and confidence, so a caller can date the claim it used, name the basis
it chose, and never present a stale selection as the current one. Nothing here decides anything: the
resolution lives in ``meridian/services/spend_pocket.py``, which prefers an observed selection and
falls back to the explicit name allow-list while SAYING which basis it used.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

#: The vocabulary a snapshot's observation can take. ``None`` (unobserved) is not a member: it writes
#: nothing, so it can never be stored as if it were an answer.
RESOLUTION_SELECTED = "selected"
RESOLUTION_NONE = "none"
RESOLUTION_AMBIGUOUS = "ambiguous"
RESOLUTIONS = (RESOLUTION_SELECTED, RESOLUTION_NONE, RESOLUTION_AMBIGUOUS)

#: Freshness mirrors ``financial_observations`` exactly, so the two stores cannot drift apart in what
#: they mean by a stale or partial read.
FRESHNESS = ("fresh", "stale", "partial", "unavailable")


@dataclass(frozen=True)
class SpendSelection:
    """One snapshot's answer about which pocket the owner spends from."""

    provider: str
    connection_external_id: str
    snapshot_id: str
    observed_at: str
    resolution: str
    selected_external_id: Optional[str] = None
    observed_external_ids: tuple[str, ...] = ()
    freshness: str = "fresh"
    confidence: Optional[float] = None
    assumptions: tuple[str, ...] = ()
    data_mode: str = "actual"
    id: Optional[int] = None

    @property
    def is_usable(self) -> bool:
        """Can a reader act on this row?

        Only a single, unambiguous selection is usable. ``'none'`` and ``'ambiguous'`` are answers,
        but they are answers that a caller must FALL BACK from while saying so, never answers it may
        resolve by preference.
        """
        return self.resolution == RESOLUTION_SELECTED and bool(self.selected_external_id)

    def as_evidence(self) -> dict:
        """The provenance a payload can carry without leaking a balance or a raw snapshot."""
        return {
            "resolution": self.resolution,
            "selected_external_id": self.selected_external_id,
            "observed_external_ids": list(self.observed_external_ids),
            "observed_at": self.observed_at,
            "freshness": self.freshness,
            "snapshot_id": self.snapshot_id,
        }


def resolution_for_observed(observed: Optional[Iterable[str]]) -> Optional[str]:
    """Map ``readback_selected_spend_pocket()``'s return value onto a stored resolution.

    The provider method's own contract, kept exactly as it is documented there:

        None      -> the facet was not observed          -> no row (returns None here)
        ()        -> observed, no card exposed a value   -> 'none'
        (one,)    -> the provider's current value        -> 'selected'
        (a, b)    -> the cards disagreed                 -> 'ambiguous'

    Returning ``None`` for the unobserved case is the whole point: it is the caller's signal that
    nothing may be written, so a missing read cannot become a stored "no selection".
    """
    if observed is None:
        return None
    values = tuple(str(value) for value in observed if str(value))
    if not values:
        return RESOLUTION_NONE
    if len(values) == 1:
        return RESOLUTION_SELECTED
    return RESOLUTION_AMBIGUOUS


class SpendSelectionStore:
    """Append-only store for observed spend-pocket selections."""

    def __init__(self, db_path) -> None:
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def record(
        self,
        *,
        provider: str,
        connection_external_id: str,
        snapshot_id: str,
        observed: Optional[Iterable[str]],
        observed_at: str,
        freshness: str = "fresh",
        confidence: Optional[float] = None,
        assumptions: Sequence[str] = (),
        data_mode: str = "actual",
    ) -> Optional[SpendSelection]:
        """Record one snapshot's observation. Returns the row written, or ``None`` if unobserved.

        Idempotent per snapshot: re-recording the same snapshot id updates nothing and returns the
        row that already exists, so a retried ingest cannot manufacture a competing selection.
        """
        resolution = resolution_for_observed(observed)
        if resolution is None:
            return None  # unobserved is not an answer; see the module docstring
        if freshness not in FRESHNESS:
            raise ValueError(f"unknown freshness {freshness!r}")
        values = tuple(str(value) for value in (observed or ()) if str(value))
        selected = values[0] if resolution == RESOLUTION_SELECTED else None
        payload = (
            provider, connection_external_id, snapshot_id, observed_at, resolution, selected,
            json.dumps(list(values)), freshness, confidence, json.dumps(list(assumptions)), data_mode,
        )
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM crew_spend_selection_observations "
                "WHERE snapshot_id = ? AND provider = ?",
                (snapshot_id, provider),
            ).fetchone()
            if existing is not None:
                return self._row(existing)
            connection.execute(
                """INSERT INTO crew_spend_selection_observations (
                       provider, connection_external_id, snapshot_id, observed_at, resolution,
                       selected_external_id, observed_external_ids_json, freshness, confidence,
                       assumptions_json, data_mode
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                payload,
            )
            row = connection.execute(
                "SELECT * FROM crew_spend_selection_observations "
                "WHERE snapshot_id = ? AND provider = ?",
                (snapshot_id, provider),
            ).fetchone()
        return self._row(row) if row is not None else None

    def latest(self, *, provider: str = "crew",
               connection_external_id: Optional[str] = None) -> Optional[SpendSelection]:
        """The newest observation recorded, or ``None`` when nothing was ever observed."""
        query = "SELECT * FROM crew_spend_selection_observations WHERE provider = ?"
        params: list[object] = [provider]
        if connection_external_id is not None:
            query += " AND connection_external_id = ?"
            params.append(connection_external_id)
        query += " ORDER BY observed_at DESC, id DESC LIMIT 1"
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return self._row(row) if row is not None else None

    def history(self, *, provider: str = "crew", limit: int = 20) -> tuple[SpendSelection, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM crew_spend_selection_observations WHERE provider = ? "
                "ORDER BY observed_at DESC, id DESC LIMIT ?",
                (provider, max(1, min(int(limit), 200))),
            ).fetchall()
        return tuple(self._row(row) for row in rows)

    @staticmethod
    def _row(row) -> SpendSelection:
        return SpendSelection(
            provider=row["provider"],
            connection_external_id=row["connection_external_id"],
            snapshot_id=row["snapshot_id"],
            observed_at=row["observed_at"],
            resolution=row["resolution"],
            selected_external_id=row["selected_external_id"],
            observed_external_ids=tuple(json.loads(row["observed_external_ids_json"] or "[]")),
            freshness=row["freshness"],
            confidence=row["confidence"],
            assumptions=tuple(json.loads(row["assumptions_json"] or "[]")),
            data_mode=row["data_mode"],
            id=row["id"],
        )


__all__ = [
    "FRESHNESS",
    "RESOLUTIONS",
    "RESOLUTION_AMBIGUOUS",
    "RESOLUTION_NONE",
    "RESOLUTION_SELECTED",
    "SpendSelection",
    "SpendSelectionStore",
    "resolution_for_observed",
]
