"""Local trial ledger and conservative deadline calculations."""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .db import run_migrations

_STATUSES = {"trial", "active", "canceled", "unknown"}
_SOURCES = {"checkout_capture", "receipt", "transaction", "manual", "inferred"}
_TIERS = {"direct", "propose", "autonomous"}


def _parse(value: str, field: str, tz: str = "UTC") -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        try:
            parsed = parsed.replace(tzinfo=ZoneInfo(tz))
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
    return parsed


def _iso(value: datetime) -> str:
    return value.isoformat()


@dataclass(frozen=True)
class Trial:
    id: int
    service: str
    account_identifier: str | None
    plan_name: str | None
    status: str
    trial_started_at: str
    trial_ends_at: str
    cancel_by: str
    buffer_days: int
    price_after: float | None
    cadence: str | None
    timezone: str
    source_of_truth: str
    confidence: float
    allowlisted: bool
    essential: bool
    autonomy_tier: str
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrialRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        run_migrations(db_path)

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _validate(data: dict[str, Any], *, existing: Trial | None = None) -> dict[str, Any]:
        merged = existing.as_dict() if existing else {}
        merged.update({key: value for key, value in data.items() if value is not None})
        service = merged.get("service")
        if not isinstance(service, str) or not service.strip():
            raise ValueError("service is required")
        timezone_name = merged.get("timezone", "UTC")
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, TypeError):
            raise ValueError("timezone must be a valid IANA timezone")
        started = _parse(merged.get("trial_started_at"), "trial_started_at", timezone_name)
        ends = _parse(merged.get("trial_ends_at"), "trial_ends_at", timezone_name)
        if ends <= started:
            raise ValueError("trial_ends_at must be after trial_started_at")
        buffer_days = merged.get("buffer_days", 1)
        if isinstance(buffer_days, bool) or not isinstance(buffer_days, int) or not 0 <= buffer_days <= 90:
            raise ValueError("buffer_days must be an integer from 0 to 90")
        cancel_by = ends - timedelta(days=buffer_days)
        if cancel_by < started:
            cancel_by = started
        status = merged.get("status", "trial")
        source = merged.get("source_of_truth", "manual")
        tier = merged.get("autonomy_tier", "propose")
        if status not in _STATUSES or source not in _SOURCES or tier not in _TIERS:
            raise ValueError("invalid trial status, source_of_truth, or autonomy_tier")
        confidence = merged.get("confidence", 1.0)
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        result = dict(merged)
        result.update(service=service.strip(), timezone=timezone_name, trial_started_at=_iso(started),
                      trial_ends_at=_iso(ends), cancel_by=_iso(cancel_by), buffer_days=buffer_days,
                      status=status, source_of_truth=source, autonomy_tier=tier,
                      confidence=float(confidence), allowlisted=bool(merged.get("allowlisted", False)),
                      essential=bool(merged.get("essential", False)))
        return result

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Trial:
        return Trial(**{key: (bool(row[key]) if key in {"allowlisted", "essential"} else row[key]) for key in row.keys()})

    def create(self, **data: Any) -> Trial:
        values = self._validate(data)
        now = datetime.now(timezone.utc).isoformat()
        columns = ["service", "account_identifier", "plan_name", "status", "trial_started_at", "trial_ends_at", "cancel_by", "buffer_days", "price_after", "cadence", "timezone", "source_of_truth", "confidence", "allowlisted", "essential", "autonomy_tier", "created_at", "updated_at"]
        with self._connect() as db:
            cursor = db.execute(f"INSERT INTO trials ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", tuple(values.get(c, now if c in {"created_at", "updated_at"} else None) for c in columns))
            trial_id = cursor.lastrowid
        return self.get(trial_id)

    def get(self, trial_id: int) -> Trial | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM trials WHERE id = ?", (trial_id,)).fetchone()
        return self._from_row(row) if row else None

    def list(self, *, include_canceled: bool = False) -> list[Trial]:
        query = "SELECT * FROM trials"
        if not include_canceled:
            query += " WHERE status != 'canceled'"
        query += " ORDER BY cancel_by ASC, id ASC"
        with self._connect() as db:
            return [self._from_row(row) for row in db.execute(query)]

    def update(self, trial_id: int, **changes: Any) -> Trial:
        current = self.get(trial_id)
        if current is None:
            raise KeyError(trial_id)
        values = self._validate(changes, existing=current)
        now = datetime.now(timezone.utc).isoformat()
        fields = ["service", "account_identifier", "plan_name", "status", "trial_started_at", "trial_ends_at", "cancel_by", "buffer_days", "price_after", "cadence", "timezone", "source_of_truth", "confidence", "allowlisted", "essential", "autonomy_tier"]
        with self._connect() as db:
            db.execute(f"UPDATE trials SET {','.join(f'{f}=?' for f in fields)}, updated_at=? WHERE id=?", tuple(values.get(f) for f in fields) + (now, trial_id))
        return self.get(trial_id)


def deadline_events(trial: Trial, *, now: datetime | None = None) -> list[dict[str, str]]:
    """Return deterministic escalation checkpoints for a trial deadline.

    Events are derived from the stored cancel-by instant, never from wall-clock
    date arithmetic. This keeps DST and owner-timezone behavior stable.
    """
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    cancel_by = _parse(trial.cancel_by, "cancel_by", trial.timezone)
    checkpoints = (("7_days", 7), ("3_days", 3), ("1_day", 1), ("deadline", 0))
    return [
        {"kind": kind, "due_at": _iso(cancel_by - timedelta(days=days)), "overdue": str(cancel_by - timedelta(days=days) < reference).lower()}
        for kind, days in checkpoints
    ]
