"""Read-only proactive layer: grouped meaningful events and financial weather.

This derives a small, explainable view from an existing Observatory dial model.
It never mutates financial state, never calls a connector, and never treats
missing data as zero: when the dial's freshness is not ``fresh`` or the
available balance is unknown, the weather is reported as ``unknown`` with a
lowered confidence instead of a reassuring state.

The output is deterministic for one dial model, so the dial stays the single
source of the underlying dates and amounts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any, Mapping, Optional, Sequence

DEFAULT_WINDOW_DAYS = 14
_ATTENTION_WINDOW_DAYS = 3
_MAX_EVENTS_PER_GROUP = 3
_FRESH = "fresh"

_OBLIGATION_KINDS = frozenset({"bill", "goal"})
_INCOME_KINDS = frozenset({"income"})
_UNFUNDED_STATUSES = frozenset({"unfunded", "partial"})
_ZERO_DECIMAL_CURRENCIES = frozenset({"JPY", "KRW", "VND", "CLP", "ISK"})


@dataclass(frozen=True)
class MeaningfulEvent:
    """One near-term dial event reduced to the fields the weather layer uses."""

    id: str
    date: str
    kind: str
    title: str
    amount_minor: int
    currency: str
    funding_status: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventGroup:
    """A capped, labelled group of related near-term events."""

    key: str
    label: str
    severity: str
    explanation: str
    events: tuple[MeaningfulEvent, ...]
    omitted: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "severity": self.severity,
            "explanation": self.explanation,
            "events": [event.to_dict() for event in self.events],
            "omitted": self.omitted,
        }


@dataclass(frozen=True)
class FinancialWeather:
    """The proactive view: one weather state plus its grouped evidence."""

    state: str
    confidence: float
    freshness: str
    observed_at: Optional[str]
    headline: str
    explanation: str
    window_days: int
    groups: tuple[EventGroup, ...]
    assumptions: tuple[str, ...]
    suppressed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "confidence": self.confidence,
            "freshness": self.freshness,
            "observedAt": self.observed_at,
            "headline": self.headline,
            "explanation": self.explanation,
            "windowDays": self.window_days,
            "groups": [group.to_dict() for group in self.groups],
            "assumptions": list(self.assumptions),
            "suppressed": self.suppressed,
        }


def _parse_date(value: object) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _is_amount(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _available_minor(dial: Mapping[str, Any]) -> tuple[Optional[int], Optional[str]]:
    available = dial.get("availableToSpend")
    if not isinstance(available, Mapping):
        return None, None
    minor = available.get("minor")
    currency = available.get("currency")
    if not _is_amount(minor):
        return None, None
    return int(minor), currency if isinstance(currency, str) and currency else "USD"


def _meaningful_event(raw: object) -> Optional[MeaningfulEvent]:
    """Reduce one dial event, dropping anything that is not a real signal.

    Zero, negative, boolean, or unparseable amounts are dropped rather than
    rendered, so a placeholder row cannot masquerade as a commitment.
    """
    if not isinstance(raw, Mapping):
        return None
    amount = raw.get("amount")
    if not isinstance(amount, Mapping):
        return None
    minor = amount.get("minor")
    if not _is_amount(minor) or int(minor) <= 0:
        return None
    event_id = raw.get("id")
    title = raw.get("title")
    kind = raw.get("kind")
    day = raw.get("date")
    if not all(isinstance(value, str) and value for value in (event_id, title, kind, day)):
        return None
    currency = amount.get("currency")
    funding_status = raw.get("fundingStatus")
    return MeaningfulEvent(
        id=str(event_id),
        date=str(day),
        kind=str(kind),
        title=str(title),
        amount_minor=int(minor),
        currency=currency if isinstance(currency, str) and currency else "USD",
        funding_status=funding_status if isinstance(funding_status, str) else "unknown",
        explanation=_event_explanation(str(kind), str(title), funding_status),
    )


def _event_explanation(kind: str, title: str, funding_status: object) -> str:
    if kind in _OBLIGATION_KINDS:
        if funding_status == "unfunded":
            return f"{title} is due and has no money reserved yet."
        if funding_status == "partial":
            return f"{title} is due and only partly funded."
        if funding_status == "reserved":
            return f"{title} is due and fully reserved."
        return f"{title} is due; its funding state is not known."
    if kind in _INCOME_KINDS:
        return f"{title} is expected income, not a commitment."
    return f"{title} is scheduled."


def _format_amount(minor: int, currency: str) -> str:
    exponent = 0 if currency.upper() in _ZERO_DECIMAL_CURRENCIES else 2
    scale = 10 ** exponent
    whole, remainder = divmod(abs(minor), scale)
    sign = "-" if minor < 0 else ""
    if exponent == 0:
        return f"{sign}{whole:,} {currency}"
    return f"{sign}{whole:,}.{remainder:0{exponent}d} {currency}"


def _group(
    key: str,
    label: str,
    severity: str,
    explanation: str,
    events: Sequence[MeaningfulEvent],
) -> Optional[EventGroup]:
    if not events:
        return None
    ordered = sorted(events, key=lambda event: (event.date, event.title, event.id))
    return EventGroup(
        key=key,
        label=label,
        severity=severity,
        explanation=explanation,
        events=tuple(ordered[:_MAX_EVENTS_PER_GROUP]),
        omitted=max(0, len(ordered) - _MAX_EVENTS_PER_GROUP),
    )


def _total_label(events: Sequence[MeaningfulEvent], currency: str) -> str:
    if not events:
        return "nothing"
    total = sum(event.amount_minor for event in events)
    return _format_amount(total, currency)


def build_financial_weather(
    dial: Mapping[str, Any],
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> FinancialWeather:
    """Group near-term dial events and classify the financial weather.

    Raises:
        ValueError: when ``window_days`` is not a positive integer.
    """
    if not isinstance(window_days, int) or isinstance(window_days, bool) or window_days < 1:
        raise ValueError("window_days must be a positive integer")

    freshness = dial.get("freshness")
    freshness = freshness if isinstance(freshness, str) and freshness else "unavailable"
    observed_at = dial.get("observedAt") if isinstance(dial.get("observedAt"), str) else None
    as_of = _parse_date(dial.get("today"))
    window_end = as_of + timedelta(days=window_days - 1) if as_of is not None else None
    # Never claim a window wider than the dial actually modelled: clamp to the
    # dial horizon when it is present and still in the future.
    horizon_end = _parse_date(dial.get("horizonEnd"))
    if window_end is not None and horizon_end is not None and as_of is not None and horizon_end >= as_of:
        window_end = min(window_end, horizon_end)

    near: list[MeaningfulEvent] = []
    suppressed = 0
    seen: set[str] = set()
    for raw in dial.get("events") or ():
        event = _meaningful_event(raw)
        if event is None or event.id in seen:
            suppressed += 1
            continue
        seen.add(event.id)
        if as_of is None or window_end is None:
            # Without a trustworthy today we cannot bound the window, so we
            # keep the event out rather than guessing a near-term date.
            continue
        day = _parse_date(event.date)
        if day is None or day < as_of or day > window_end:
            continue
        near.append(event)

    obligations = [event for event in near if event.kind in _OBLIGATION_KINDS]
    income = [event for event in near if event.kind in _INCOME_KINDS]
    gaps = [event for event in obligations if event.funding_status in _UNFUNDED_STATUSES]

    currencies = {event.currency.upper() for event in near}
    available_minor, available_currency = _available_minor(dial)
    if available_currency is not None:
        currencies.add(available_currency.upper())
    primary = (available_currency or (near[0].currency if near else "USD"))
    assert primary is not None

    next_due = min((event for event in obligations), key=lambda event: event.date, default=None)
    due_soon_attention = False
    if next_due is not None and as_of is not None:
        next_day = _parse_date(next_due.date)
        due_soon_attention = next_day is not None and (next_day - as_of).days <= _ATTENTION_WINDOW_DAYS

    groups = tuple(
        group
        for group in (
            _group(
                "due_soon",
                "Obligations due soon",
                "attention" if due_soon_attention else "info",
                (
                    f"{len(obligations)} obligation(s) totalling "
                    f"{_total_label(obligations, primary)} fall in the next {window_days} days."
                ),
                obligations,
            ),
            _group(
                "funding_gaps",
                "Funding gaps",
                "attention" if any(event.funding_status == "unfunded" for event in gaps) else "watch",
                f"{len(gaps)} of the near-term obligations are not fully funded.",
                gaps,
            ),
            _group(
                "income_expected",
                "Income expected",
                "info",
                (
                    f"{len(income)} income item(s) totalling "
                    f"{_total_label(income, primary)} are expected in the next {window_days} days."
                ),
                income,
            ),
        )
        if group is not None
    )

    assumptions: list[str] = []
    if freshness != _FRESH:
        state = "unknown"
        confidence = 0.2
        assumptions.append(f"provider freshness is {freshness}")
        headline = "Financial weather is unknown"
        explanation = (
            "Recent provider data is not current, so Meridian does not assert a weather state."
        )
    elif available_minor is None:
        state = "unknown"
        confidence = 0.2
        assumptions.append("available balance is unknown")
        headline = "Financial weather is unknown"
        explanation = (
            "The available balance could not be read, so near-term coverage cannot be judged."
        )
    elif len(currencies) > 1:
        state = "unknown"
        confidence = 0.3
        assumptions.append("near-term amounts span multiple currencies")
        headline = "Financial weather is unknown"
        explanation = (
            "Amounts span more than one currency, and Meridian does not add currencies together."
        )
    else:
        obligations_total = sum(event.amount_minor for event in obligations)
        income_total = sum(event.amount_minor for event in income)
        covered = available_minor + income_total
        if obligations_total > covered:
            state = "strained"
            confidence = 1.0
            headline = "Obligations exceed available cash plus expected income"
            explanation = (
                f"Near-term obligations total {_format_amount(obligations_total, primary)}, but "
                f"available cash plus expected income is only "
                f"{_format_amount(covered, primary)}."
            )
        elif obligations_total > available_minor:
            state = "tight"
            confidence = 1.0
            headline = "Expected income is required to cover near-term obligations"
            explanation = (
                f"Available cash of {_format_amount(available_minor, primary)} does not cover "
                f"near-term obligations of {_format_amount(obligations_total, primary)}; "
                "expected income must arrive on time."
            )
        else:
            state = "steady"
            confidence = 1.0
            headline = "Available cash covers near-term obligations"
            explanation = (
                f"Available cash of {_format_amount(available_minor, primary)} covers "
                f"near-term obligations of {_format_amount(obligations_total, primary)}."
            )

    return FinancialWeather(
        state=state,
        confidence=confidence,
        freshness=freshness,
        observed_at=observed_at,
        headline=headline,
        explanation=explanation,
        window_days=window_days,
        groups=groups,
        assumptions=tuple(assumptions),
        suppressed=suppressed,
    )
