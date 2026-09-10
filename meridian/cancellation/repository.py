"""Durable cancellation attempts; provider adapters remain outside this store."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from ..cancellation.workflow import (
    CancellationState,
    VerificationSignal,
    advance,
    status_for_transition,
)
from ..db import run_migrations


@dataclass(frozen=True)
class CancellationAction:
    id: int
    trial_id: int
    channel: str
    state: str
    status_label: str
    confirmation_reference: str | None
    started_at: str | None
    completed_at: str | None
    artifact_ids: list[str]
    notes: str | None
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CancellationRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        run_migrations(db_path)

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CancellationAction:
        data = dict(row)
        data["artifact_ids"] = json.loads(data["artifact_ids"] or "[]")
        return CancellationAction(**data)

    def create(self, trial_id: int, channel: str, *, notes: str | None = None) -> CancellationAction:
        if not isinstance(channel, str) or not channel.strip():
            raise ValueError("channel is required")
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            if db.execute("SELECT 1 FROM trials WHERE id = ?", (trial_id,)).fetchone() is None:
                raise ValueError("trial_id does not reference an existing trial")
            cursor = db.execute(
                "INSERT INTO cancellation_actions (trial_id, channel, state, status_label, notes, created_at, updated_at) VALUES (?, ?, 'planned', 'Unverified', ?, ?, ?)",
                (trial_id, channel.strip(), notes, now, now),
            )
            action_id = cursor.lastrowid
        return self.get(action_id)

    def get(self, action_id: int) -> CancellationAction | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM cancellation_actions WHERE id = ?", (action_id,)).fetchone()
        return self._from_row(row) if row else None

    def list_for_trial(self, trial_id: int) -> list[CancellationAction]:
        with self._connect() as db:
            return [self._from_row(row) for row in db.execute("SELECT * FROM cancellation_actions WHERE trial_id = ? ORDER BY id", (trial_id,))]

    def transition(self, action_id: int, target: CancellationState, *, signals: set[VerificationSignal] | None = None, confirmation_reference: str | None = None, artifact_ids: list[str] | None = None, notes: str | None = None) -> CancellationAction:
        current = self.get(action_id)
        if current is None:
            raise KeyError(action_id)
        current_state = CancellationState(current.state)
        advance(current_state, target)
        now = datetime.now(timezone.utc).isoformat()
        label = status_for_transition(target, signals)
        started = current.started_at or (now if target is CancellationState.ATTEMPTED else None)
        completed = now if target in {CancellationState.VERIFIED, CancellationState.ESCALATED, CancellationState.FAILED} else current.completed_at
        with self._connect() as db:
            db.execute(
                "UPDATE cancellation_actions SET state=?, status_label=?, confirmation_reference=?, started_at=?, completed_at=?, artifact_ids=?, notes=?, updated_at=? WHERE id=?",
                (target.value, label, confirmation_reference or current.confirmation_reference, started, completed, json.dumps(artifact_ids if artifact_ids is not None else current.artifact_ids), notes if notes is not None else current.notes, now, action_id),
            )
        return self.get(action_id)
