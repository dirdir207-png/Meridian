"""Persistence for AI run records -- the audit trail behind an answer.

Track I.1 (MERIDIAN_ROADMAP.md §6) requires the run record to be *"persisted so a proposal
can be audited back to the reasoning that produced it"*. ``RunRecord.as_dict()`` carried it;
this keeps it.

**What is stored, and what is deliberately not.** ``ai_run_records`` holds WHICH role ran,
on which model and provider, with which prompt version, on WHICH evidence, for how long and
with what outcome. It holds **no claim text, no model output and no evidence body**. A run
record is a pointer to the reasoning, not a copy of it: a second store of generated financial
prose would sit outside the evidence store and outside the surfaces that know how to label
provenance and freshness. The requirement is to audit back to the reasoning, not to keep a
transcript.

**Evidence ids are references, not foreign keys.** An audit row must survive evidence being
revoked or having its content deleted, and must still be able to say what was consulted.
A cascade would erase the very row that explains why an answer was given.

**Recording is not authority.** Rows here describe what a READ-ONLY role did. Nothing in this
module can approve, execute or mutate provider state, and the module imports no write path.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from meridian.ai.envelope import RunRecord
from meridian.db import run_migrations


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class StoredRun:
    """A persisted run record, with the row it occupies."""

    id: int
    role: str
    provider: str
    model: str
    prompt_version: str
    evidence_ids: tuple[str, ...]
    started_at: str
    ended_at: str
    outcome: str
    recorded_at: str


class RunRecordStore:
    """Read and write AI run records.

    Deliberately narrow: there is no update and no delete. An audit trail that can be edited
    is not an audit trail, and nothing in this project needs to rewrite history here. If a
    run must be superseded, record another run.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        run_migrations(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def record(self, run: RunRecord, *, recorded_at: str | None = None) -> StoredRun:
        """Persist one run record and return it with its id."""
        payload = run.as_dict()
        evidence_ids = payload["evidence_ids"]
        if not isinstance(evidence_ids, list):
            raise ValueError("run record evidence_ids must be a list")
        stamp = recorded_at or _now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ai_run_records (
                    role, provider, model, prompt_version, evidence_ids,
                    started_at, ended_at, outcome, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["role"],
                    payload["provider"],
                    payload["model"],
                    payload["prompt_version"],
                    json.dumps(list(evidence_ids), sort_keys=True),
                    payload["started_at"],
                    payload["ended_at"],
                    payload["outcome"],
                    stamp,
                ),
            )
            row_id = cursor.lastrowid
        stored = self.get(int(row_id))
        if stored is None:  # pragma: no cover - the insert above either worked or raised
            raise RuntimeError("run record vanished immediately after being written")
        return stored

    def get(self, record_id: int) -> StoredRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM ai_run_records WHERE id = ?", (record_id,)
            ).fetchone()
        return _to_stored(row) if row is not None else None

    def list_recent(self, *, role: str | None = None, limit: int = 20) -> list[StoredRun]:
        """Newest first. ``limit`` is clamped to a sane range so a caller cannot ask for the
        whole table by accident."""
        limit = max(1, min(int(limit), 200))
        sql = "SELECT * FROM ai_run_records"
        params: list[object] = []
        if role is not None:
            sql += " WHERE role = ?"
            params.append(role)
        sql += " ORDER BY recorded_at DESC, id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [_to_stored(row) for row in rows]

    def count(self, *, role: str | None = None) -> int:
        sql = "SELECT COUNT(*) AS total FROM ai_run_records"
        params: Sequence[object] = ()
        if role is not None:
            sql += " WHERE role = ?"
            params = (role,)
        with self._connect() as connection:
            row = connection.execute(sql, params).fetchone()
        return int(row["total"]) if row is not None else 0


def _to_stored(row: sqlite3.Row) -> StoredRun:
    try:
        evidence_ids = tuple(json.loads(row["evidence_ids"] or "[]"))
    except (TypeError, ValueError):
        # A malformed array must not make the audit trail unreadable: the row is still
        # returned, with no evidence ids, rather than raising and hiding every other run.
        evidence_ids = ()
    return StoredRun(
        id=int(row["id"]),
        role=row["role"],
        provider=row["provider"],
        model=row["model"],
        prompt_version=row["prompt_version"],
        evidence_ids=evidence_ids,
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        outcome=row["outcome"],
        recorded_at=row["recorded_at"],
    )
