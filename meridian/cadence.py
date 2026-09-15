"""One calendar-aware rule for advancing a dated occurrence.

Why this module exists: the same question — "what is the next occurrence of a
recurring date?" — had six separate implementations across the codebase
(``billers``, ``payday``, ``paycheck``, ``paycheck_learning``,
``services.dial``, ``services.plan``, ``services.today``), and three of them
disagreed. The measured consequences, before this module:

  * **Monthly drifted permanently.** Every implementation clamped the day to the
    target month and then treated the *clamped* date as the new anchor, so a bill
    anchored on the 31st walked Jan 31 → Feb 28 → Mar 28 → Apr 28… and never
    returned to the 31st. ``plan._next_occurrence(2026-01-31, "monthly",
    2026-04-01)`` answered ``2026-04-28``; the correct answer is ``2026-04-30``.
  * **Semimonthly meant two different things.** ``paycheck``, ``paycheck_learning``,
    ``services.dial``, ``services.plan`` and ``services.today`` advanced by a flat
    ``+15 days`` (Jan 15 → Jan 30 → Feb 14 → Mar 1…, which walks off the calendar),
    while ``payday`` used "the 15th and the last day of the month". Only the second
    is a real pay schedule.
  * **Annual Feb 29 collapsed.** ``date(year + 1, 2, 29)`` raised in a non-leap year
    and the handlers fell back to Feb 28 *permanently*, so the 29th never returned
    in the next leap year.

The rule this module implements is deliberately narrow: **month positions are
always derived from the anchor's day, never from the previous occurrence's day.**
That single constraint is what stops a clamp from becoming a permanent drift.
Feb 29 can clamp to Feb 28 during the walk and still return to Feb 29 four years
later, because the anchor day is retained rather than overwritten.

No money, provider, storage or authority behaviour is involved: this is date
arithmetic only.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Optional

__all__ = [
    "MONTHLY",
    "SEMIMONTHLY",
    "advance",
    "advance_by_periods",
    "next_occurrence",
    "normalize",
    "supported",
]

MONTHLY = "monthly"
WEEKLY = "weekly"
BIWEEKLY = "biweekly"
SEMIMONTHLY = "semimonthly"

# Accept every spelling the codebase and the provider actually use, so a caller
# can never fall back to a private duplicate just because it received "bi-weekly".
_ALIASES = {
    "weekly": WEEKLY,
    "week": WEEKLY,
    "biweekly": BIWEEKLY,
    "bi-weekly": BIWEEKLY,
    "fortnight": BIWEEKLY,
    "monthly": MONTHLY,
    "month": MONTHLY,
    "semimonthly": SEMIMONTHLY,
    "semi-monthly": SEMIMONTHLY,
    "twice-monthly": SEMIMONTHLY,
    "twicemonthly": SEMIMONTHLY,
    "annually": "annually",
    "annual": "annually",
    "yearly": "annually",
    "year": "annually",
}

SUPPORTED = frozenset({WEEKLY, BIWEEKLY, MONTHLY, SEMIMONTHLY, "annually"})


def normalize(recurrence: Optional[str]) -> Optional[str]:
    """The canonical cadence name, or None when the recurrence is not understood.

    Returning None rather than a default is deliberate: an unrecognised
    recurrence must stop a roll-forward loop, never silently become weekly.
    """
    if not isinstance(recurrence, str):
        return None
    return _ALIASES.get(recurrence.strip().lower())


def supported(recurrence: Optional[str]) -> bool:
    return normalize(recurrence) is not None


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


class _Occurrence(date):
    """A date that remembers the day it is trying to keep across a clamp.

    ``date`` is immutable and has no ``__dict__``, so the intended day cannot be
    attached to a plain date. This subclass carries it as a slot. It behaves as a
    ``date`` for every practical purpose (comparison, arithmetic, ``isoformat``,
    ``str``) and JSON/protocol encoders fall back to the ``date`` representation.

    Why it is needed: chained stepping (`advance(advance(a))`) holds an
    intermediate date, and without a remembered day the February clamp becomes the
    permanent anchor — the exact bug this module exists to remove.
    """

    __slots__ = ("intended_day",)

    def __new__(cls, year: int, month: int, day: int, intended_day: Optional[int] = None):
        self = super().__new__(cls, year, month, day)
        self.intended_day = day if intended_day is None else intended_day
        return self


def _intended_day(anchor: date) -> int:
    """The day this occurrence is trying to keep.

    Normally the occurrence's own day. When the date came out of a clamp — Jan 31
    walked into February and became Feb 28 — this is the 31st, so a later step can
    restore it.
    """
    return getattr(anchor, "intended_day", anchor.day)


def _shift_months(anchor: date, months: int) -> date:
    """Move ``anchor`` by whole months, keeping its intended day where allowed.

    The intended day survives a clamp, so 2026-01-31 -> 2026-02-28 (February has
    no 31st) -> 2026-03-31, whether the caller steps by period index or feeds each
    result back in.
    """
    day = _intended_day(anchor)
    total = (anchor.year * 12 + (anchor.month - 1)) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    return _Occurrence(year, month, min(day, _days_in_month(year, month)), day)


def _shift_years(anchor: date, years: int) -> date:
    """Move by whole years, keeping the intended day — so Feb 29 recovers."""
    day = _intended_day(anchor)
    year = anchor.year + years
    return _Occurrence(year, anchor.month, min(day, _days_in_month(year, anchor.month)), day)


def _next_semimonthly(anchor: date) -> date:
    """The next 15th-or-month-end slot strictly after ``anchor``.

    Semimonthly means the 15th and the last day of the month — the real pay
    schedule — not a flat 15-day step. ``strictly after`` matters: from the 15th
    the next slot is that month's last day, and from a month's last day it is the
    following month's 15th. Non-strict behaviour would return its own input and
    spin the callers' roll-forward loops.

    The slot day is NOT carried as the intended day: a month-end slot is a
    position in the semimonthly schedule, not a request to keep the 31st. Carrying
    it would make a later monthly step jump from the 28th to the 31st.
    """
    intended = _intended_day(anchor)
    last = _days_in_month(anchor.year, anchor.month)
    if anchor.day < 15:
        return _Occurrence(anchor.year, anchor.month, 15, intended)
    if anchor.day < last:
        return _Occurrence(anchor.year, anchor.month, last, intended)
    year = anchor.year + (1 if anchor.month == 12 else 0)
    month = 1 if anchor.month == 12 else anchor.month + 1
    return _Occurrence(year, month, 15, intended)


def advance(anchor: date, recurrence: Optional[str], periods: int = 1) -> Optional[date]:
    """Advance ``anchor`` by ``periods`` recurrence periods, or None if unknown.

    ``periods`` must be >= 1. The result is always computed from THIS ``anchor``,
    so a caller that wants an anchored sequence must call
    ``advance(original, rec, periods=n)`` rather than feeding each result back in
    as the new anchor. Re-feeding is what made the old code drift:

        2026-01-31 -> 2026-02-28 -> 2026-03-28 -> 2026-04-28   (wrong)
        advance(2026-01-31, 'monthly', 3) == 2026-04-30          (correct)

    ``next_occurrence`` below is the anchor-preserving walk; prefer it over
    hand-rolling a loop.
    """
    cadence = normalize(recurrence)
    if cadence is None or periods < 1:
        return None
    if cadence == WEEKLY:
        return anchor + timedelta(days=7 * periods)
    if cadence == BIWEEKLY:
        return anchor + timedelta(days=14 * periods)
    if cadence == MONTHLY:
        return _shift_months(anchor, periods)
    if cadence == "annually":
        return _shift_years(anchor, periods)
    # semimonthly: an interval count is not a day count, so step slot by slot.
    # Each slot's position is a property of the anchor month, so this does not
    # accumulate error the way a flat +15 days does.
    current = anchor
    for _ in range(periods):
        nxt = _next_semimonthly(current)
        if nxt <= current:  # defensive: never stall or loop backwards
            break
        current = nxt
    return current


def advance_by_periods(anchor: date, cadence: Optional[str], interval: int) -> Optional[date]:
    """``advance`` with an explicit interval multiplier (weekly/biweekly/monthly).

    Semimonthly has no meaningful integer multiplier ladder, so it advances one
    slot and the interval is ignored — callers that carry an interval are
    expressing a weekly/biweekly/monthly repeat.
    """
    cadence_name = normalize(cadence)
    if cadence_name is None:
        return None
    if cadence_name == SEMIMONTHLY:
        interval = 1
    return advance(anchor, cadence_name, max(1, interval))


def next_occurrence_with_index(
    anchor: date, recurrence: Optional[str], as_of: date
) -> tuple[date, int]:
    """``(occurrence, period_index)`` for the first occurrence on/after ``as_of``.

    ``period_index`` is the k for which ``advance(anchor, recurrence, k)`` equals
    the returned occurrence, with k = 0 meaning "the anchor itself" — which is the
    correct index whenever the anchor already satisfies ``as_of``, because
    ``advance(anchor, rec, 1)`` is the FIRST step AFTER the anchor, not the anchor.

    Getting this wrong is silent: reporting k = 1 for an anchor that is itself the
    occurrence makes the caller's next step k = 2, skipping an occurrence entirely.
    """
    if normalize(recurrence) is None:
        return anchor, 0
    if anchor >= as_of:
        return anchor, 0
    current = anchor
    for periods in range(1, 401):
        candidate = advance(anchor, recurrence, periods)
        if candidate is None or candidate <= current:
            return current, periods - 1
        current = candidate
        if current >= as_of:
            return current, periods
    return current, 400


def next_occurrence(anchor: date, recurrence: Optional[str], as_of: date) -> date:
    """The first occurrence on or after ``as_of``; the anchor when unsupported.

    Steps are measured from the ORIGINAL ``anchor`` at an increasing period
    count, never by feeding the previous result back in. That distinction is the
    whole point of this module: re-feeding loses the anchor day, so a monthly
    anchor on the 31st would return the 28th forever after its first February.

    An unknown recurrence returns the anchor unchanged, matching the previous
    behaviour of the callers that used this shape: they treat a non-recurring
    date as a single literal occurrence.
    """
    return next_occurrence_with_index(anchor, recurrence, as_of)[0]
