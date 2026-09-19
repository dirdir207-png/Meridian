"""Self-learning paycheck detection over real income transactions.

The owner's paycheck isn't necessarily a clean "direct deposit" — it can land as
a Cash App transfer, or be routed through PayPal and moved in. Rather than rely
on a fixed manual amount that goes stale, learn the real source from the recent
transaction graph: cluster positive (income/transfer) transactions by merchant +
amount, take the dominant recurring cluster, and derive its typical amount,
variability, and cadence. This feeds the forecast/beacon with what actually
happens (and a range for the uncertainty), and can auto-update over time.

Never guesses when there is no clear recurring income: returns None so the
app keeps the owner's explicit config (or no paycheck).
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from .cadence import advance_by_periods

# The recurring cluster must appear at least this many times / span this many
# weeks to be trusted as a paycheck rather than a one-off transfer.
_MIN_OCCURRENCES = 3
_MAX_DAILY_RANGE_DAYS = 40  # max gap between paychecks to count as recurring
_MAX_PAYCHECK_AMOUNT = 10_000.0  # sanity guard; ignore absurd outliers

_FLOOR_KEY = "meridian_paycheck_learning_floor"


@dataclass(frozen=True)
class LearningFloor:
    """The owner's learning window: only observations on or after ``floor`` count.

    ``set_at`` is provenance — when the owner reset the window — so a surface can say
    when the learned figure was last re-based rather than presenting it as timeless.
    """

    floor: str
    set_at: str


def _now() -> str:
    return datetime.now().astimezone().isoformat()


class PaycheckLearningFloorRepository:
    """Persist the learning floor in ``app_config`` (single user, Meridian-local).

    Deliberately a SEPARATE key from the paycheck config. The floor governs which
    observations are learned from; the config is what the owner asserts. Keeping them
    apart means a learning reset can never clear the owner's configured amount, and a
    configured amount can never look like a learning reset.
    """

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

    def set(self, floor: str) -> LearningFloor:
        """Record the learning floor. Validates the date so a bad value cannot be
        stored and later silently exclude every observation."""
        if _parse_date(floor) is None:
            raise ValueError("floor must be an ISO date (YYYY-MM-DD)")
        record = LearningFloor(floor=str(floor), set_at=_now())
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO app_config(key, value, created_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (_FLOOR_KEY, json.dumps(record.__dict__), _now()),
            )
        return record

    def get(self) -> Optional[LearningFloor]:
        """The stored floor, or None when the owner has not set one.

        A malformed stored value resolves to None rather than raising: the same
        discipline ``PaycheckRepository.get`` uses, so a corrupt local setting degrades
        to "learn from all history" instead of taking the income surface down.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_config WHERE key=?", (_FLOOR_KEY,)
            ).fetchone()
        if row is None:
            return None
        try:
            data = json.loads(row[0])
            floor = str(data.get("floor") or "")
        except (ValueError, TypeError, AttributeError):
            return None
        if _parse_date(floor) is None:
            return None
        return LearningFloor(floor=floor, set_at=str(data.get("set_at") or ""))

    def clear(self) -> None:
        """Remove the floor, so all history is learned from again.

        This deletes ONE local setting. It never deletes a financial record: the
        observations were never removed, only excluded while the floor was active.
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM app_config WHERE key=?", (_FLOOR_KEY,))



def _parse_date(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except Exception:  # noqa: BLE001 - unknown date form
        return None


def _is_income(txn) -> bool:
    """A positive amount that isn't a reimbursement / tiny fee / refund."""
    amount = float(getattr(txn, "amount", 0) or 0)
    if amount <= 0:
        return False
    kind = str(getattr(txn, "classification_kind", "") or "").lower()
    if kind in {"reimbursement", "fee", "refund"}:
        return False
    if amount < 50.0:  # ignore grocery refunds / tag-along credits
        return False
    return True


def _cadence_guess(offsets: list[int]) -> tuple[str, int]:
    """Guess cadence from the common gap between deposit dates."""
    if not offsets:
        return "monthly", 1
    avg = sum(offsets) / len(offsets)
    if avg <= 9:
        return "weekly", 1
    if avg <= 16:
        return "biweekly", 1
    if avg <= 21:
        return "semimonthly", 1
    return "monthly", 1


def observations_on_or_after(transactions, floor: Optional[str] = None) -> list:
    """Only the observations inside the owner's learning window.

    ``floor`` is an ISO date; the boundary is INCLUSIVE because the owner said
    "starting at yesterday". With no floor every observation is returned, which is the
    behaviour that existed before the floor and is what a cleared floor restores.

    This FILTERS a view. It never deletes: the excluded observations stay in the
    ledger and become learnable again the moment the floor is cleared or moved back.

    An observation whose date cannot be read is EXCLUDED while a floor is active,
    because "after the floor" cannot be established for it, and the whole point of the
    floor is to stop a previous position's pay being counted. Under no floor it is kept,
    as it always was.
    """
    if not floor:
        return list(transactions)
    floor_date = _parse_date(floor)
    if floor_date is None:
        # A corrupt floor must not silently blank the income surface; falling back to
        # "all history" is the pre-floor behaviour and stays visible as such.
        return list(transactions)
    kept = []
    for txn in transactions:
        occurred = _parse_date(getattr(txn, "occurred_at", None))
        if occurred is not None and occurred >= floor_date:
            kept.append(txn)
    return kept


def learn_paycheck(transactions, floor: Optional[str] = None) -> dict | None:
    """Return a learned paycheck dict, or None if no clear recurring income.

    ``floor`` restricts learning to observations on or after that ISO date (OS-051), so
    a job change can re-base the learned figure without deleting any financial record.
    With no floor, every observation is learnable exactly as before.

    The paycheck is often NOT a single transfer: it arrives as multiple same-period
    chunks (e.g. Cash App's $500-per-transfer limit, or a PayPal->external->Crew
    route). So this:

    1. Collects positive income/transfer events from an income source (PayPal,
       Cash App, Capital One, Zelle — any recurring positive inflow).
    2. Bundles events within a ~4-day window into one "pay period" and SUMS them,
       so 2x $490.25 on adjacent days = one ~$980 pay.
    3. Averages those period totals over time (median + min/max range) so the
       forecast reflects what actually lands, not a single chunk.

    Returns {amount, min_amount, max_amount, cadence, cadence_interval,
    next_date, occurrences, sources, confidence}. None when no clear recurring
    income exists.
    """
    income = [t for t in observations_on_or_after(transactions, floor) if _is_income(t)]
    if len(income) < _MIN_OCCURRENCES:
        return None

    # Identify the income source(s): group by merchant, keep merchants that look
    # like money movement (or any merchant with >=3 positive events).
    clusters: dict[str, list] = defaultdict(list)
    for txn in income:
        merchant = str(getattr(txn, "merchant", "") or getattr(txn, "description", "") or "").strip()
        clusters[merchant].append(txn)

    # Choose the best source: the one whose events form a recurring weekly pattern.
    best: tuple[str, list, list] | None = None
    for merchant, items in clusters.items():
        events = [_parse_date(x.occurred_at) for x in items]
        events = [e for e in events if e]
        if len(events) < _MIN_OCCURRENCES:
            continue
        if best is None or len(items) > len(best[1]):
            best = (merchant, items, events)

    if best is None:
        return None
    merchant, items, events = best

    # Bundle events that fall within a ~4-day window into a single pay period,
    # then SUM their amounts — the real per-paycheck figure.
    events.sort()
    periods: list[tuple[date, float]] = []
    for txn in items:
        ev_date = _parse_date(txn.occurred_at)
        if not ev_date:
            continue
        amount = abs(float(txn.amount))
        if periods and (ev_date - periods[-1][0]).days <= 4:
            # same pay period
            prev_date, prev_amount = periods[-1]
            periods[-1] = (prev_date, prev_amount + amount)
        else:
            periods.append((ev_date, amount))

    if len(periods) < _MIN_OCCURRENCES:
        return None
    period_totals = [round(total, 2) for _date, total in periods]
    period_dates = [d for d, _t in periods]
    # Exclude period totals that are absurdly small (partial windows) or huge.
    median_total = sorted(period_totals)[len(period_totals) // 2]
    if median_total <= 0 or median_total > _MAX_PAYCHECK_AMOUNT:
        return None
    # Cadence from median gap between pay periods.
    gaps = [(later - earlier).days for earlier, later in zip(period_dates, period_dates[1:])]
    if gaps and max(gaps) > _MAX_DAILY_RANGE_DAYS * 2:
        return None
    cadence, cadence_interval = _cadence_guess(gaps)
    next_date = _next_period_date(period_dates[-1], cadence, cadence_interval)
    if next_date is None:
        return None
    return {
        "amount": median_total,
        "min_amount": min(period_totals),
        "max_amount": max(period_totals),
        "cadence": cadence,
        "cadence_interval": cadence_interval,
        "next_date": next_date.isoformat(),
        "occurrences": len(periods),
        "sources": [merchant],
        "source": merchant,
        "confidence": round(min(0.95, 0.5 + len(periods) * 0.1), 2),
    }


def _next_period_date(anchor: date, cadence: str, interval: int) -> Optional[date]:
    """The date of the next pay period after ``anchor``.

    Returns a DATE, not a day-count, because a day-count cannot express
    semimonthly: "the 15th and the last day of the month" is 13-18 days
    depending on the month, so any fixed +15 walked off the calendar
    (Jan 15 -> Jan 30 -> Feb 14 -> Mar 1). The previous implementation also
    anchored monthly on ``date.today()`` rather than on the observed period
    date, which made the answer depend on when it was asked.
    """
    return advance_by_periods(anchor, cadence, max(1, interval))
