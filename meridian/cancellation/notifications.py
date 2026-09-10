"""Durable, idempotent reminder materialization for trial deadlines.

This records reminders for a future delivery adapter. It never sends mail, pushes,
or performs a merchant action itself.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from ..db import run_migrations
from ..trials import TrialRepository
from .deadlines import upcoming_deadlines


@dataclass(frozen=True)
class TrialNotification:
    id: int
    trial_id: int
    kind: str
    due_at: str
    status: str
    created_at: str
    sent_at: str | None


class TrialNotificationRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        run_migrations(db_path)

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TrialNotification:
        return TrialNotification(**dict(row))

    def materialize_due(self, *, now: datetime | None = None) -> list[TrialNotification]:
        reference = now or datetime.now(timezone.utc)
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        trials = TrialRepository(self.db_path).list()
        due = [event for event in upcoming_deadlines(trials, now=reference) if event["overdue"] == "true"]
        created_at = reference.isoformat()
        with self._connect() as db:
            for event in due:
                db.execute(
                    "INSERT OR IGNORE INTO trial_notifications (trial_id, kind, due_at, created_at) VALUES (?, ?, ?, ?)",
                    (event["trial_id"], event["kind"], event["due_at"], created_at),
                )
            rows = db.execute(
                "SELECT * FROM trial_notifications WHERE status = 'pending' ORDER BY due_at, id"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def list(self, *, status: str | None = None) -> list[TrialNotification]:
        query = "SELECT * FROM trial_notifications"
        params: tuple[str, ...] = ()
        if status is not None:
            if status not in {"pending", "sent", "dismissed"}:
                raise ValueError("invalid notification status")
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY due_at, id"
        with self._connect() as db:
            return [self._from_row(row) for row in db.execute(query, params)]

    def mark_sent(self, notification_id: int) -> TrialNotification:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE trial_notifications SET status='sent', sent_at=? WHERE id=? AND status='pending'",
                (now, notification_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(notification_id)
        with self._connect() as db:
            row = db.execute("SELECT * FROM trial_notifications WHERE id=?", (notification_id,)).fetchone()
        return self._from_row(row)
