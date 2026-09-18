"""Configurable paycheck (funding source) for per-bill funding projections.

Meridian's funding rules (fixed_per_paycheck / percent_of_paycheck) need
future paycheck inflow events to allocate money toward bills. Previously these
came only from detected recurring income transactions; the owner asked for a
way to set a simple or crew-style paycheck explicitly.

This module persists a single paycheck config (cadence, amount, next date) in
``app_config`` and generates dated inflow events that ``build_plan`` feeds into
funding projections. It is read-side planning metadata; it never moves money.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .cadence import advance as cadence_advance
from .cadence import next_occurrence_with_index

_PAYCHECK_KEY = "meridian_paycheck_config"
_VALID_CADENCE = ("weekly", "biweekly", "monthly", "semimonthly")


@dataclass(frozen=True)
class PaycheckConfig:
    cadence: str
    amount: float
    next_date: str  # ISO date of the next paycheck
    active: bool = True

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, raw: str) -> "PaycheckConfig":
        data = json.loads(raw)
        return cls(
            cadence=str(data.get("cadence") or "monthly"),
            amount=float(data.get("amount") or 0),
            next_date=str(data.get("next_date") or ""),
            active=bool(data.get("active", True)),
        )


def _now() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


class PaycheckRepository:
    """Persist the owner's paycheck config in app_config (single user)."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        return conn

    def save(self, config: PaycheckConfig) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO app_config(key, value, created_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (_PAYCHECK_KEY, config.to_json(), _now()),
            )

    def get(self) -> Optional[PaycheckConfig]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_config WHERE key=?", (_PAYCHECK_KEY,)
            ).fetchone()
        if row is None:
            return None
        try:
            return PaycheckConfig.from_json(row[0])
        except (ValueError, TypeError, KeyError):
            return None

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM app_config WHERE key=?", (_PAYCHECK_KEY,))


def _next_after(anchor: date, cadence: str) -> date:
    """Advance ``anchor`` one cadence period.

    Delegates to the shared calendar-aware rule so a monthly paycheck anchored on
    the 31st stays on the 31st and semimonthly means the 15th and month-end,
    rather than drifting under a flat +15 days. An unrecognised cadence keeps the
    previous conservative default (one week).
    """
    advanced = cadence_advance(anchor, cadence)
    if advanced is None:
        return anchor + timedelta(days=7)
    return advanced


def future_paycheck_events(
    config: PaycheckConfig,
    *,
    as_of: date,
    horizon_days: int = 90,
) -> list[tuple[date, float]]:
    """Generate dated paycheck inflow events from ``config.next_date`` onward.

    Returns ``[(date, amount), ...]`` up to ``horizon_days`` ahead, anchored so
    the first entry is the next paycheck >= ``as_of``.
    """
    if not config.active or config.amount <= 0:
        return []
    events: list[tuple[date, float]] = []
    horizon = as_of + timedelta(days=horizon_days)
    anchor = date.fromisoformat(config.next_date)
    events: list[tuple[date, float]] = []
    horizon = as_of + timedelta(days=horizon_days)
    anchor = date.fromisoformat(config.next_date)
    # Anchor-preserving, index-correct walk. Occurrence number k is
    # ``advance(anchor, cadence, k)``, and the walk reports which k it landed on,
    # so every following step is simply the next k. Deriving the next occurrence
    # from ``current`` instead would let a February clamp become the permanent day;
    # guessing the index would skip or repeat a paycheck.
    current, period = next_occurrence_with_index(anchor, config.cadence, as_of)
    while current <= horizon and period <= 400:
        events.append((current, config.amount))
        following = cadence_advance(anchor, config.cadence, period + 1)
        if following is None or following <= current:
            break
        period += 1
        current = following
    return events


def build_cash_events(
    current_cash: float,
    paycheck: Optional[PaycheckConfig],
    *,
    as_of: date,
    horizon_days: int = 90,
) -> list[tuple[date, float]]:
    """Compose the funding cash timeline: current cash + future paychecks."""
    events: list[tuple[date, float]] = []
    if current_cash > 0:
        events.append((as_of, current_cash))
    if paycheck is not None:
        events.extend(future_paycheck_events(paycheck, as_of=as_of, horizon_days=horizon_days))
    return sorted(events, key=lambda item: item[0])
