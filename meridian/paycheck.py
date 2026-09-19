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


_MAX_EVIDENCE_IDS = 12


@dataclass(frozen=True)
class ResolvedPaycheck:
    """A paycheck projection AND the provenance of its amount.

    Deliberately NOT part of ``PaycheckConfig``. The config is what the owner set and is
    persisted verbatim through ``PaycheckRepository``; ``basis``, ``source``, ``observed_at``
    and ``evidence_ids`` are DERIVED. Folding them into the persisted config would write
    derived provenance to the database and later read it back as though the owner had
    configured it.

    It exposes the same attribute names as ``PaycheckConfig`` (cadence/amount/next_date/
    active) so the dial's ``getattr``-based readers take either one unchanged.

    ``basis`` is not decoration: an aggregate over three observed paychecks and a single
    last-observed value are different strengths of claim, and a consumer that cannot tell
    them apart cannot report the amount honestly.
    """

    cadence: str
    amount: float
    next_date: str
    active: bool
    basis: str  # "aggregate" | "last_known" | "configured"
    source: str
    observed_at: Optional[str] = None
    evidence_ids: tuple = ()
    occurrences: int = 0


def _income_transactions(transactions):
    return [
        txn
        for txn in transactions or ()
        if str(getattr(txn, "classification_kind", "") or "") == "income"
    ]


def _observed_day(txn) -> Optional[str]:
    raw = str(getattr(txn, "occurred_at", "") or "")
    return raw[:10] if len(raw) >= 10 else None


def resolve_expected_paycheck(transactions, configured=None) -> Optional[ResolvedPaycheck]:
    """The owner's approved rule (2026-09-19, verbatim in docs/project/CURRENT_STATUS.md):

        "it should default to that value and moving forward aggregate after 3"

    The rule is applied to the CURRENT income channel, not to income in general, and that
    distinction is the difference between an honest number and a wrong one. ``learn_paycheck``
    groups by merchant and returns a single source, so calling it across all history would
    happily return a three-occurrence aggregate for a channel the owner has stopped using --
    and that aggregate would then be reported as the expected income. The owner's mechanism
    just changed in exactly that way (paychecks now deposit directly into Crew, where they
    previously arrived as Cash App transfers), so:

      1. identify the channel from the MOST RECENTLY observed income transaction;
      2. aggregate WITHIN that channel once it has enough occurrences (``learn_paycheck``
         returns None below ``paycheck_learning._MIN_OCCURRENCES``, so the threshold is the
         existing one rather than a second copy);
      3. otherwise use that channel's last observed value -- "default to that value";
      4. otherwise fall back to the owner's configured figure, which is the last resort.

    A retired channel therefore cannot win, and two channels are never averaged together,
    because a number averaged across a retired payout route and a new one describes neither.

    Known limitation, stated rather than hidden: with fewer than three observations the AMOUNT
    is observed but the SCHEDULE is not, so the cadence and next date come from the configured
    config when there is one and otherwise from the last observed date advanced by one month.
    ``basis`` describes where the amount came from, not the schedule.
    """
    from .paycheck_learning import learn_paycheck

    income = _income_transactions(transactions)

    if income:
        latest = max(income, key=lambda txn: str(getattr(txn, "occurred_at", "") or ""))
        channel = str(getattr(latest, "merchant", "") or "")
        current = [
            txn for txn in income if str(getattr(txn, "merchant", "") or "") == channel
        ]
        learned = learn_paycheck(current)

        if learned:
            days = [day for day in (_observed_day(txn) for txn in current) if day]
            ids = tuple(
                getattr(txn, "id")
                for txn in current[:_MAX_EVIDENCE_IDS]
                if getattr(txn, "id", None) is not None
            )
            return ResolvedPaycheck(
                cadence=str(learned.get("cadence") or "monthly"),
                amount=float(learned.get("amount") or 0.0),
                next_date=str(learned.get("next_date") or ""),
                active=True,
                basis="aggregate",
                source=channel or "manual",
                observed_at=max(days) if days else None,
                evidence_ids=ids,
                occurrences=int(learned.get("occurrences") or 0),
            )

        day = _observed_day(latest)
        cadence = "monthly"
        next_date = ""
        if configured is not None:
            cadence = str(getattr(configured, "cadence", "") or cadence)
            next_date = str(getattr(configured, "next_date", "") or "")
        if not next_date and day:
            try:
                from datetime import date as _date

                advanced = cadence_advance(_date.fromisoformat(day), cadence, 1)
                next_date = advanced.isoformat() if advanced else ""
            except Exception:  # noqa: BLE001 - a malformed date must not block a read
                next_date = ""
        return ResolvedPaycheck(
            cadence=cadence,
            amount=abs(float(getattr(latest, "amount", 0) or 0.0)),
            next_date=next_date,
            active=True,
            basis="last_known",
            source=channel or "manual",
            observed_at=day,
            evidence_ids=(
                (getattr(latest, "id"),)
                if getattr(latest, "id", None) is not None
                else ()
            ),
            occurrences=len(current),
        )

    if configured is not None:
        return ResolvedPaycheck(
            cadence=str(getattr(configured, "cadence", "") or "monthly"),
            amount=float(getattr(configured, "amount", 0) or 0.0),
            next_date=str(getattr(configured, "next_date", "") or ""),
            active=bool(getattr(configured, "active", True)),
            basis="configured",
            source="manual",
        )

    return None
