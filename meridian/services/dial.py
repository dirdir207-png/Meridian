"""Read-only Observatory dial view model.

This builds the dated event horizon from normalized Meridian records only. It
never performs a mutation and never invents missing financial facts.

A bill's observed reserved amount remains authoritative. This service also emits a
read-only projection of Crew's proven per-event proration for the bill's next
occurrence when an attached funding plan has a supported cadence. Projections carry
explicit provenance and never become balances or provider claims.
"""

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from meridian.cadence import advance, next_occurrence, next_occurrence_with_index
from meridian.commitments import Commitment, CommitmentType
from meridian.funding import cadence_interval_days, crew_proration_cents
from meridian.services.today import data_freshness

# Currency exponents used to convert the dollar-valued normalized model to
# integer minor units at the rendering boundary. Unknown currencies default to
# two minor places; this list only covers common zero-decimal currencies.
_ZERO_DECIMAL_CURRENCIES = frozenset({"JPY", "KRW", "VND", "CLP", "ISK"})


def _minor(amount: float, currency: str = "USD") -> int:
    if amount is None:
        return 0
    exponent = 0 if (currency or "USD").upper() in _ZERO_DECIMAL_CURRENCIES else 2
    try:
        return int(
            (Decimal(str(amount)) * (Decimal(10) ** exponent)).quantize(
                Decimal(1), rounding=ROUND_HALF_UP
            )
        )
    except (ValueError, TypeError, ArithmeticError):
        return 0


def _date_of(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _advance(anchor: date, recurrence: str) -> Optional[date]:
    """Advance a date by one recurrence period, preserving calendar intent.

    Delegates to the shared cadence rule so the dial cannot disagree with Plan,
    Today or the biller monitor about when a recurring date next occurs. The old
    local version drifted two ways: a monthly clamp became the new anchor
    (Jan 31 -> Feb 28 -> Mar 28 forever) and semimonthly was a flat +15 days.
    """
    return advance(anchor, recurrence)


def _next_occurrence(anchor: date, recurrence: str, as_of: date) -> date:
    """Return the first occurrence on or after ``as_of``.

    A non-recurring or unknown anchor is returned unchanged. The walk is
    anchor-preserving, so an intervening month-end clamp does not become the
    permanent day.
    """
    return next_occurrence(anchor, recurrence, as_of)


def _spend_source_account(accounts):
    """Crew's discretionary 'Free to Spend' pocket, matching Today semantics."""
    def _is_spend(account) -> bool:
        name = (getattr(account, "name", "") or "").strip().casefold()
        return "free to spend" in name or name == "free to spend"

    for account in accounts:
        if _is_spend(account):
            return account
    return None


def _available_to_spend(graph):
    accounts = graph.list_accounts()
    spend = _spend_source_account(accounts)
    if spend is not None and getattr(spend, "available_balance", None) is not None:
        return {
            "minor": _minor(spend.available_balance, spend.currency or "USD"),
            "currency": spend.currency or "USD",
        }
    # Fall back only when there is a single cash currency; never add currencies.
    cash = [
        account
        for account in accounts
        if account.is_active
        and account.account_type in ("cash", "checking", "savings")
        and account.available_balance is not None
    ]
    if not cash:
        return None
    currencies = {account.currency or "USD" for account in cash}
    if len(currencies) != 1:
        return None
    currency = next(iter(currencies))
    return {
        "minor": _minor(sum(account.available_balance for account in cash), currency),
        "currency": currency,
    }


def _horizon(graph, paycheck, as_of: date) -> date:
    """Choose a conservative dial horizon from actual data.

    When a paycheck is configured, the horizon includes the next payday plus a
    two-week lookahead. Without one, it is a labeled 14-day upcoming-events
    horizon rather than an invented payday.
    """
    if paycheck is None or not getattr(paycheck, "active", False):
        return as_of + timedelta(days=14)
    next_date = _date_of(getattr(paycheck, "next_date", ""))
    if next_date is None:
        return as_of + timedelta(days=14)
    try:
        next_date = _next_occurrence(next_date, getattr(paycheck, "cadence", "monthly"), as_of)
    except Exception:  # noqa: BLE001 - malformed config should not block read
        return as_of + timedelta(days=14)
    return max(as_of + timedelta(days=14), next_date + timedelta(days=14))


def _funding_sources_by_reserve(graph) -> dict[tuple[str, str], list]:
    """Index the currently observed funding plans by (provider, bill reserve).

    The plan is the record the owner calls their income source / Funding Cadence, and
    it is attached to a bill reserve; the bill row now carries the reserve that
    contained it (023). Matching those two stored facts is the whole link, and it keys
    on provider record ids, never on a name the owner renames.

    A plan retired by a complete read is excluded (``list_funding_plans`` filters on
    ``absent_since``): a withdrawn cadence must not keep naming a bill's funding
    source.
    """
    index: dict[tuple[str, str], list] = {}
    for plan in graph.list_funding_plans():
        if not plan.bill_reserve_id:
            continue
        index.setdefault((plan.provider, plan.bill_reserve_id), []).append(plan)
    return index


def _resolve_funding_source(commitment, sources: dict[tuple[str, str], list]):
    """Identify the observed funding source for one bill, or decline to.

    Returns ``(source, candidate_ids, plan)``. ``source`` is a dict only when exactly one
    current plan claims the bill's reserve; several plans claiming one reserve is
    ambiguity, and the honest answer is to name none of them rather than to pick the
    first. An empty membership, an unknown provider, or no matching plan all return
    ``(None, (), None)``: the sole global plan is never substituted for a missing link.

    The source is identity and provenance only. It says who funds the bill; it does
    NOT say how much of a dated occurrence is reserved, which stays unknown here. The
    matched plan record is returned separately rather than widened into that payload,
    because the schedule projection needs its anchor date and the source's shape is
    already pinned by its own tests.
    """
    reserve_id = getattr(commitment, "bill_reserve_id", "") or ""
    provider = getattr(commitment, "legacy_source", None)
    if not reserve_id or not provider:
        return None, (), None
    matches = sources.get((provider, reserve_id), [])
    if len(matches) == 1:
        plan = matches[0]
        return (
            {
                "id": plan.external_id,
                "name": plan.name,
                "provider": plan.provider,
                "cadence": plan.cadence,
                "observedAt": plan.observed_at,
                "billReserveId": reserve_id,
            },
            (),
            plan,
        )
    if len(matches) > 1:
        return None, tuple(plan.external_id for plan in matches), None
    return None, (), None


def _crew_schedule(commitment, amount: float, plan, event_date: date, as_of: date):
    """Build one next-occurrence Crew-derived schedule, or no schedule.

    The cadence is only used when it maps to an exact interval and the plan carries an
    anchor, so an unrecognised cadence yields NO schedule rather than a guessed one. The
    unit is the bill's next occurrence only (D-010/D-013 as narrowed): the contribution is
    per funding event, and nothing is multiplied forward across later due dates.
    """
    if plan is None:
        return None
    interval_days = cadence_interval_days(plan.cadence)
    anchor = _date_of(plan.anchor_date)
    if interval_days is None or anchor is None:
        return None
    next_funding = anchor
    while next_funding < as_of:
        next_funding += timedelta(days=interval_days)
    contribution = crew_proration_cents(_minor(amount, commitment.currency), interval_days)
    return {
        "eventDate": next_funding.isoformat(),
        "contribution": {"minor": contribution, "currency": commitment.currency},
        "deadline": event_date.isoformat(),
        "nextFundingDate": next_funding.isoformat(),
        "planName": plan.name or "",
        "basis": "crew_estimate",
        "intervalDays": interval_days,
    }


def _reserve_figure(commitment, amount: float):
    """The reserved figure for one bill, with the basis it may be claimed on.

    Returns ``(funded, status, basis, divisor, attribution, observed_at)``. Precedence
    is D-013's, in order:

    * **observed** -- Crew reported this bill's own ``reservedAmount`` (024's flag says
      so, because the NOT NULL column cannot distinguish a reported 0 from silence).
      Attributed to Crew only when the row itself came from Crew; a local bill's own
      figure is Meridian-side money and is never called Crew's.
    * **unknown** -- no provider-reported per-bill figure. The former even-split
      fallback is retired by D-015 and is never a stated balance.
    """
    provider = getattr(commitment, "legacy_source", None)

    if getattr(commitment, "reserved_amount_reported", False):
        funded = commitment.funded_amount or 0.0
        status = "reserved" if funded >= amount else ("partial" if funded > 0 else "unfunded")
        return (
            funded,
            status,
            "observed",
            None,
            "crew" if provider == "crew" else "meridian",
            commitment.updated_at or None,
        )

    # D-015 retires the even-split fallback. An observed reserve total is not a
    # per-bill balance, so missing per-bill evidence stays explicitly unknown.
    return None, "unknown", "unknown", None, None, None


def _commitment_events(
    commitments: Sequence[Commitment],
    as_of: date,
    horizon_end: date,
    funding_sources: Optional[dict[tuple[str, str], list]] = None,
) -> list[dict]:
    sources = funding_sources if funding_sources is not None else {}
    events: list[dict] = []
    for commitment in commitments:
        if commitment.type not in (CommitmentType.BILL, CommitmentType.GOAL):
            continue

        # Bills: dated cashflow occurrences rolled from the stored anchor.
        if commitment.type == CommitmentType.BILL:
            amount = commitment.amount if commitment.amount is not None else commitment.target_amount
            anchor = _date_of(getattr(commitment, "due_date", None))
            recurrence = getattr(commitment, "recurrence", "") or ""
            if amount is None or anchor is None:
                continue
            funding_source, ambiguous_ids, funding_plan = _resolve_funding_source(
                commitment, sources
            )
            current, period = next_occurrence_with_index(anchor, recurrence, as_of)
            guard = 0
            first_occurrence = True
            while current <= horizon_end and guard < 200:
                if first_occurrence:
                    (
                        funded,
                        status,
                        basis,
                        divisor,
                        attribution,
                        basis_observed_at,
                    ) = _reserve_figure(commitment, amount)
                    reserved = (
                        {
                            "minor": _minor(funded, commitment.currency),
                            "currency": commitment.currency,
                        }
                        if funded is not None and funded > 0
                        else None
                    )
                    funding_schedule = _crew_schedule(
                        commitment, amount, funding_plan, current, as_of
                    )
                else:
                    # D-010/D-013: one reserve is not a per-occurrence amount. Repeating
                    # this bill's figure on every future due date would read as several
                    # times the money, so the later occurrences stay plainly unresolved
                    # while the source identity above still holds on every row.
                    status, basis, divisor, attribution, basis_observed_at = (
                        "unknown",
                        "unknown",
                        None,
                        None,
                        None,
                    )
                    reserved = None
                    funding_schedule = None
                events.append(
                    {
                        "id": f"bill-{commitment.id}-{current.isoformat()}",
                        "date": current.isoformat(),
                        "kind": "bill",
                        "title": commitment.name,
                        "amount": {
                            "minor": _minor(amount, commitment.currency),
                            "currency": commitment.currency,
                        },
                        "fundingStatus": status,
                        "reserved": reserved,
                        # Basis travels with the figure (D-013): "observed" is Crew's own
                        # per-bill number, "derived" is Meridian's even split of the
                        # reserve total and says so with its divisor, "unknown" states
                        # nothing. A consumer can therefore never present a derivation as
                        # an observation, and never attribute one to Crew.
                        "fundingBasis": basis,
                        "fundingBasisDivisor": divisor,
                        "fundingAttribution": attribution,
                        "fundingObservedAt": basis_observed_at,
                        "fundingSchedule": funding_schedule,
                        "fundingSource": funding_source,
                        "fundingSourceAmbiguous": bool(ambiguous_ids),
                        "fundingSourceCandidateIds": list(ambiguous_ids),
                        "source": (
                            "crew"
                            if commitment.legacy_source == "crew"
                            else "manual"
                        ),
                        "observedAt": None,
                        "evidenceIds": [],
                        "detailHref": "/meridian?workspace=plan",
                    }
                )
                first_occurrence = False
                # Anchor-preserving step: measured from the original anchor and
                # tracked by period index, so a February clamp does not become the
                # permanent day and no occurrence is skipped or repeated.
                following = advance(anchor, recurrence, period + 1)
                if following is None or following <= current:
                    break
                period += 1
                current = following
                guard += 1

        # Goals with an explicit target date: surface as dated local planning
        # events, never as bank cashflow.
        elif commitment.type == CommitmentType.GOAL:
            target_date = _date_of(getattr(commitment, "target_date", None))
            target = commitment.target_amount
            if target_date is None or target is None or target_date < as_of or target_date > horizon_end:
                continue
            funded = commitment.funded_amount or 0.0
            remaining = max(0.0, target - funded)
            status = "reserved" if remaining <= 0 else ("partial" if funded > 0 else "unfunded")
            events.append(
                {
                    "id": f"goal-{commitment.id}-{target_date.isoformat()}",
                    "date": target_date.isoformat(),
                    "kind": "goal",
                    "title": commitment.name,
                    "amount": {
                        "minor": _minor(remaining, commitment.currency),
                        "currency": commitment.currency,
                    },
                    "fundingStatus": status,
                    "reserved": (
                        {"minor": _minor(funded, commitment.currency), "currency": commitment.currency}
                        if funded > 0
                        else None
                    ),
                    "source": (
                        "crew"
                        if commitment.legacy_source == "crew"
                        else "manual"
                    ),
                    "observedAt": None,
                    "evidenceIds": [],
                    "detailHref": "/meridian?workspace=plan",
                }
            )
    return events


def _paycheck_events(paycheck, as_of: date, horizon_end: date) -> list[dict]:
    if paycheck is None or not getattr(paycheck, "active", False):
        return []
    amount = getattr(paycheck, "amount", 0) or 0
    if amount <= 0:
        return []
    try:
        from meridian.paycheck import future_paycheck_events

        days = max(1, (horizon_end - as_of).days)
        raw = future_paycheck_events(
            paycheck,
            as_of=as_of,
            horizon_days=days,
        )
    except Exception:  # noqa: BLE001 - paycheck is best-effort read context
        return []
    return [
        {
            "id": f"income-{day.isoformat()}",
            "date": day.isoformat(),
            "kind": "income",
            "title": "Paycheck",
            "amount": {
                "minor": _minor(float(amount), getattr(paycheck, "currency", None) or "USD"),
                "currency": getattr(paycheck, "currency", None) or "USD",
            },
            "fundingStatus": "unknown",
            "reserved": None,
            # Provenance now comes from the RESOLUTION rather than being asserted here.
            # The amount is an aggregate of observed paychecks, or the last observed value,
            # or the configured figure -- and which one it is changes how strongly the
            # number may be claimed, so "basis" travels with it. Neither "source" nor the
            # evidence is ever invented: a figure with nothing behind it carries basis
            # "configured", no observation time and no evidence ids.
            "source": str(getattr(paycheck, "source", "") or "manual"),
            "observedAt": getattr(paycheck, "observed_at", None),
            "evidenceIds": [
                str(item) for item in (getattr(paycheck, "evidence_ids", ()) or ())
            ],
            "basis": str(getattr(paycheck, "basis", "") or "configured"),
            "detailHref": "/meridian?workspace=plan",
        }
        for day, _event_amount in raw
        if as_of <= day <= horizon_end
    ]


def build_dial(
    graph,
    commitments=None,
    *,
    as_of: date,
    paycheck=None,
    now: Optional[datetime] = None,
) -> dict:
    """Build the read-only Observatory dial model."""
    if commitments is None:
        commitments = []
    accounts = graph.list_accounts()
    horizon_end = _horizon(graph, paycheck, as_of)

    events = _commitment_events(
        commitments,
        as_of,
        horizon_end,
        _funding_sources_by_reserve(graph),
    )
    events.extend(_paycheck_events(paycheck, as_of, horizon_end))
    events.sort(key=lambda event: (event["date"], event["kind"], event["title"]))

    freshness = data_freshness(
        graph,
        account_ids=[account.id for account in accounts],
        include_all_connections=True,
        now=now,
    )

    return {
        "timezone": "local",
        "today": as_of.isoformat(),
        "horizonEnd": horizon_end.isoformat(),
        "availableToSpend": _available_to_spend(graph),
        "freshness": freshness.get("status", "unavailable"),
        "observedAt": freshness.get("last_updated_at"),
        "events": events,
        "projections": [],
    }
