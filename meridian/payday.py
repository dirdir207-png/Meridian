"""Conservative, deterministic recognition of recurring payday evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import median

from .cadence import advance


@dataclass(frozen=True)
class PaydayPattern:
    cadence: str
    next_date: date
    typical_amount: float
    confidence: float
    evidence_ids: tuple[int, ...]


def _transaction_date(transaction) -> date | None:
    value = getattr(transaction, "occurred_at", None)
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def recognize_payday(transactions, *, as_of: date, floor: str | None = None) -> PaydayPattern | None:
    """Recognize only well-supported recurring positive-income patterns.

    ``floor`` is the owner's learning window (OS-051): only observations on or after it
    are considered, so a job change can re-base the recognised schedule without deleting
    any financial record. With no floor all history is considered, exactly as before.
    The filter runs FIRST, so the pattern's ``evidence_ids`` and confidence describe the
    observations actually used rather than the excluded history.
    """
    from .paycheck_learning import observations_on_or_after

    evidence = []
    for transaction in observations_on_or_after(transactions, floor):
        occurred = _transaction_date(transaction)
        if (
            occurred is None
            or occurred > as_of
            or float(getattr(transaction, "amount", 0)) <= 0
            or getattr(transaction, "classification_kind", None) != "income"
        ):
            continue
        evidence.append((occurred, transaction))
    evidence.sort(key=lambda item: item[0])
    if len(evidence) < 4:
        return None

    intervals = [
        (current[0] - prior[0]).days
        for prior, current in zip(evidence, evidence[1:])
    ]
    cadence = None
    # Order matters: a semimonthly schedule produces 13-18 day gaps, which is a
    # SUPERSET of the biweekly 13-15 window. Testing biweekly first therefore made
    # the semimonthly branch unreachable — a 15/13/16-day pattern was reported as
    # biweekly. The narrower weekly and biweekly windows are tested first here,
    # and a pattern whose gaps are not all equal resolves to semimonthly.
    if all(6 <= value <= 8 for value in intervals):
        cadence = "weekly"
    elif all(13 <= value <= 15 for value in intervals) and len(set(intervals)) == 1:
        cadence = "biweekly"
    elif all(27 <= value <= 33 for value in intervals):
        cadence = "monthly"
    elif all(13 <= value <= 18 for value in intervals):
        cadence = "semimonthly"
    if cadence is None:
        return None
    next_date = advance(evidence[-1][0], cadence)
    if next_date is None:
        return None

    expected_interval = {
        "weekly": 7,
        "biweekly": 14,
        "semimonthly": 15,
        "monthly": round(median(intervals)),
    }[cadence]
    mean_deviation = sum(abs(value - expected_interval) for value in intervals) / len(
        intervals
    )
    confidence = max(0.55, min(0.95, 0.95 - mean_deviation * 0.08))
    return PaydayPattern(
        cadence=cadence,
        next_date=next_date,
        typical_amount=round(
            float(median(float(getattr(item, "amount")) for _day, item in evidence)),
            2,
        ),
        confidence=round(confidence, 2),
        evidence_ids=tuple(int(getattr(item, "id")) for _day, item in evidence),
    )
