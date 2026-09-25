"""Calculations for Meridian's read-only Today workspace."""

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from meridian.beacon import forecast
from meridian.cadence import next_occurrence
from meridian.commitments import CommitmentType
from meridian.repository import FinancialRepository, ProviderConnectionFreshness
from meridian.services.reserves import reserve_deficit
from meridian.services.safe_to_spend import safe_to_spend

_STALE_AFTER = timedelta(hours=24)
_CASH_ACCOUNT_TYPES = frozenset({"cash", "checking", "savings"})


def _parse_timestamp(value: str) -> Optional[datetime]:
    try:
        base_value, separator, suffix = value.partition("#")
        if separator and (not suffix or not suffix.isdecimal()):
            return None
        parsed = datetime.fromisoformat(base_value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return parsed if parsed.tzinfo is not None else None


def _last_trustworthy_update(
    connections: Sequence[ProviderConnectionFreshness],
    *,
    now: datetime,
) -> Optional[str]:
    timestamps = [
        (parsed, value)
        for connection in connections
        if connection.last_successful_at is not None
        for parsed, value in [
            (_parse_timestamp(connection.last_successful_at), connection.last_successful_at)
        ]
        if parsed is not None and parsed <= now
    ]
    return min(timestamps, key=lambda item: item[0])[1] if timestamps else None


def data_freshness(
    repository: FinancialRepository,
    *,
    account_ids: Optional[Sequence[int]] = None,
    transaction_ids: Optional[Sequence[int]] = None,
    include_all_connections: bool = False,
    include_all_transaction_links: bool = False,
    now: Optional[datetime] = None,
) -> dict[str, Optional[str]]:
    """Describe whether a scope comes from a complete, current provider graph."""
    scope = repository.get_freshness_scope(
        account_ids=account_ids,
        transaction_ids=transaction_ids,
        include_all_connections=include_all_connections,
        include_all_transaction_links=include_all_transaction_links,
    )
    connections = scope.connections
    if not connections:
        if scope.has_unlinked_records:
            return {"status": "stale", "last_updated_at": None}
        return {"status": "unavailable", "last_updated_at": None}

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    source_timestamps = [
        (parsed, value)
        for connection in connections
        for value in connection.source_updated_at
        for parsed in [_parse_timestamp(value) if value is not None else None]
        if parsed is not None
    ]
    last_successful_timestamps = {
        connection.connection_id: _parse_timestamp(connection.last_successful_at)
        if connection.last_successful_at is not None
        else None
        for connection in connections
    }
    complete = all(
        connection.status == "healthy"
        and last_successful_timestamps[connection.connection_id] is not None
        and last_successful_timestamps[connection.connection_id] <= current_time
        and len(connection.source_updated_at) > 0
        for connection in connections
    )
    source_values = sum(
        (list(connection.source_updated_at) for connection in connections),
        [],
    )
    valid_sources = len(source_timestamps) == len(source_values) and all(
        timestamp <= current_time for timestamp, _ in source_timestamps
    )
    if scope.has_unlinked_records or not complete or not valid_sources:
        return {
            "status": "stale",
            "last_updated_at": _last_trustworthy_update(connections, now=current_time),
        }

    oldest, oldest_value = min(source_timestamps, key=lambda item: item[0])
    status = "stale" if current_time - oldest > _STALE_AFTER else "fresh"
    return {"status": status, "last_updated_at": oldest_value}


def _currency_total(values: Sequence[tuple[str, float]]) -> dict[str, object]:
    by_currency: dict[str, float] = {}
    for currency, value in values:
        by_currency[currency] = by_currency.get(currency, 0.0) + value
    ordered = dict(sorted(by_currency.items()))
    if len(ordered) == 1:
        currency, amount = next(iter(ordered.items()))
        return {"amount": amount, "currency": currency, "by_currency": ordered}
    return {"amount": None, "currency": None, "by_currency": ordered}


# The pocket-identity rule lives in ONE place now. This module and dial.py each carried a
# private copy of it that had already drifted once (see dial.py's own docstring), and a third
# lived in plan.py -- so the owner's 2026-09-25 rename of his Crew pocket had to be repeated in
# five places, and Today silently fell through to a different base instead. See
# meridian/services/spend_pocket.py, which is also the seam the durable fix (identify the pocket
# by Crew's own selectedSpendSubaccount) will be filled in behind.


def _unfunded_bill_total(commitment_repository):
    """Sum of unfunded amounts on active bills (known obligations to track)."""
    if commitment_repository is None:
        return None
    total = 0.0
    for commitment in commitment_repository.list_active():
        if commitment.type != CommitmentType.BILL:
            continue
        amount = commitment.amount if commitment.amount is not None else commitment.target_amount
        if amount is None:
            continue
        total += max(0.0, amount - (commitment.funded_amount or 0.0))
    return round(total, 2)


def _coverage_exposure(commitment_repository) -> Optional[dict]:
    """OS-060: bills whose observed reserve does not cover them, stated plainly.

    The reserve is a ONE-WAY LOCK: money enters (bill allocations, then the residual
    sweep) and cannot be transferred back out, and a bill can exceed the reserve
    earmarked for it. Meridian showed the funded figure but never the gap, so a bill
    the reserve cannot cover read as "funded" when it was not *covered* -- "funded" was
    being presented where the owner needs "covered".

    What qualifies, and the distinction is the whole safety property: a bill whose
    amount EXCEEDS its OBSERVED reserved figure, and only when a reserved figure was
    actually reported (``reserved_amount_reported``, 024's flag -- ``commitments.
    funded_amount`` is ``NOT NULL DEFAULT 0``, so the column alone cannot tell a
    reported 0 from silence). This is deliberately ``0 < funded < amount``, which is
    the dial's existing "partial" status, and NOT ``funded < amount``:

    * A bill reading ``0.00`` with the report flag SET is NORMAL and means "not funded
      yet" -- funded is not covered (D-015) -- and flagging it would read as a
      shortfall, which is the false positive this must never produce. Four live bills
      read exactly that way, so the broader test would turn Today into a wall of
      "uncovered" markers.
    * A bill whose reserve was never reported has no observed figure to subtract, so
      there is no gap to state and it is excluded rather than defaulted to zero.

    Read-only arithmetic over two observed values -- the bill amount and Crew's own
    reservedAmount -- and nothing else. It is NOT a forecast, NOT a plan, and NOT a
    judgement of the owner's pocket allocation. Nothing is ever re-targeted at a gap:
    the shortfall is a fact to state, never a condition to repair, and it is resolved
    when the bill is paid from spendable funds. In particular this never implies the
    reserve can be tapped or topped up, because it cannot.
    """
    if commitment_repository is None:
        return None
    items: list[dict] = []
    for commitment in commitment_repository.list_active():
        if commitment.type != CommitmentType.BILL:
            continue
        if not getattr(commitment, "reserved_amount_reported", False):
            # No observed figure: absence is not a report of zero, so there is no
            # gap to state and nothing may be assumed about the reserve.
            continue
        amount = commitment.amount if commitment.amount is not None else commitment.target_amount
        if amount is None:
            continue
        reserved = commitment.funded_amount or 0.0
        if reserved <= 0 or reserved >= amount:
            # 0 is "not funded yet"; >= amount is already covered. Neither is a gap.
            continue
        items.append(
            {
                "id": commitment.id,
                "name": commitment.name,
                "currency": commitment.currency,
                "amount": round(amount, 2),
                "reserved": round(reserved, 2),
                # The difference between what the bill is and what is set aside now.
                "gap": round(amount - reserved, 2),
            }
        )
    if not items:
        # An explicit nothing, so a consumer never has to distinguish an absent key
        # from an empty one, and can never render a figure it was not given.
        return {"count": 0, "items": []}
    items.sort(key=lambda item: (-item["gap"], item["name"]))
    return {"count": len(items), "items": items}


def _next_paycheck_inflow(paycheck, *, now=None):
    """Next expected income from the paycheck config (funding source).

    Returns ``{"date", "amount", "cadence"}`` when a paycheck is configured and
    active, rolling the date forward if ``next_date`` has passed; else None.
    This surfaces the "Next expected income" card instead of an empty cash sum.
    """
    if paycheck is None or not getattr(paycheck, "active", False):
        return None
    amount = getattr(paycheck, "amount", 0) or 0
    if amount <= 0:
        return None
    try:
        from datetime import date as _date

        as_of = (now or datetime.now(timezone.utc)).date()

        next_date = _date.fromisoformat(getattr(paycheck, "next_date", ""))
        cadence = getattr(paycheck, "cadence", "monthly")
        # Roll forward if the configured next date has passed. Anchor-preserving:
        # the shared rule measures each step from the ORIGINAL next_date, so a
        # monthly paycheck configured on the 31st returns to the 31st after
        # February instead of sticking to the 28th, and semimonthly means the
        # 15th and month-end rather than a flat +15 days.
        next_date = next_occurrence(next_date, cadence, as_of)
    except (TypeError, ValueError):
        return None
    return {
        "date": next_date.isoformat(),
        "amount": round(float(amount), 2),
        "cadence": cadence,
    }


def _learned_paycheck_range(repository) -> Optional[tuple[float, float]]:
    """(min, max) of the learned recurring paycheck, for forecast variability."""
    try:
        from meridian.paycheck_learning import learn_paycheck

        transactions, _cursor = repository.list_transactions(limit=200)
        learned = learn_paycheck(transactions)
        if learned:
            return (float(learned["min_amount"]), float(learned["max_amount"]))
    except Exception:  # noqa: BLE001 - learning is best-effort context
        pass
    return None


def _build_beacon_signal(forecast: Optional[dict], safe_amount: Optional[float], safe_status: str, paycheck_amount: Optional[float] = None) -> dict:
    """Derive a genuinely valuable Beacon summary from the forecast + safe-to-spend.

    Not a static "plan is steady": it surfaces the real, actionable signal — a
    shortfall, whether the next paycheck covers it, a negative safe-to-spend, or
    a positive runway — so the Beacon card is worth reading.
    """
    if not forecast or forecast.get("available") is not True:
        return None
    shortfall = forecast.get("first_shortfall")
    covers = bool(forecast.get("paycheck_covers"))
    next_paycheck = forecast.get("next_paycheck")
    runway = forecast.get("runway_days")
    low_point = forecast.get("low_point")
    daily = forecast.get("daily_expense")

    if safe_amount is not None and safe_amount < 0:
        detail = f"Safe to spend is negative (${abs(safe_amount):,.2f}); the next paycheck will restore it."
        title = "You're spending faster than income."
    elif shortfall and covers:
        title = "A shortfall is covered by your next paycheck."
        detail = f"{shortfall.get('cause')} leaves you short on {_iso_short(shortfall.get('date'))}, but your {_iso_short(next_paycheck)} paycheck covers it."
    elif shortfall:
        title = "A shortfall is ahead."
        detail = f"{shortfall.get('cause')} leaves you ${shortfall.get('amount'):,.2f} short on {_iso_short(shortfall.get('date'))}."
    elif runway is not None and runway == 0:
        title = "You're running tight until payday."
        detail = f"Every day costs ${(daily or 0):,.2f} and no runway remains before funding."
    elif runway is not None and runway > 0:
        title = f"About {runway} day{'s' if runway != 1 else ''} of runway."
        detail = f"At ${(daily or 0):,.2f}/day after known obligations, before the next paycheck."
    elif low_point is not None and low_point < 0:
        title = "Your low point dips below zero."
        detail = f"Projected low ${low_point:,.2f} before funding arrives."
    else:
        title = "Your plan is steady."
        detail = "No material change detected."
    # When the paycheck varies (learnt min != max), communicate the range so a
    # single figure isn't mistaken for guaranteed.
    p_range = forecast.get("paycheck_range")
    if p_range and isinstance(p_range, (list, tuple)) and len(p_range) == 2:
        lo, hi = float(p_range[0]), float(p_range[1])
        if hi > lo:
            detail = f"{detail} Paycheck ${lo:,.0f}–${hi:,.0f} depending on the week."
    # Explain the guaranteed base vs typical-with-OT so the planned floor is
    # never confused with the (higher) average that includes overtime.
    if paycheck_amount and paycheck_amount > 0:
        detail = f"{detail} Base ${paycheck_amount:,.2f} is guaranteed; OT is upside."
    return {"title": title, "summary": title, "detail": detail, "evidence": []}


def _iso_short(value) -> str:
    """'2026-09-16' or a full timestamp -> a short 'Sep 16' label (local-safe)."""
    try:
        from datetime import date as _d

        if isinstance(value, str) and len(value) >= 10:
            return _d.fromisoformat(value[:10]).strftime("%b %-d")
    except (ValueError, TypeError):
        pass
    return str(value or "soon")


def _build_virgil_brief(forecast: Optional[dict], beacon: Optional[dict], safe_amount: Optional[float], safe_status: str) -> dict:
    """Virgil's brief: the single most actionable thing right now + evidence.

    Unlike the Beacon (a general status), this is a pointed, decision-ready
    insight — what to do next. Falls back to a calm 'nothing urgent' only when
    nothing material is happening.
    """
    title = "A useful connection"
    summary = "Nothing needs your attention right now."
    evidence = []
    if not forecast or forecast.get("available") is not True:
        return {"title": title, "summary": summary, "evidence": evidence}

    first_shortfall = forecast.get("first_shortfall")
    covers = bool(forecast.get("paycheck_covers"))
    next_paycheck = forecast.get("next_paycheck")
    runway = forecast.get("runway_days")

    if safe_amount is not None and safe_amount < 0:
        title = "You're spending faster than income."
        summary = f"Safe to spend is ${safe_amount:,.2f}; your {_iso_short(next_paycheck)} paycheck restores it."
    elif first_shortfall and covers:
        title = f"{first_shortfall.get('cause')} is covered, but tight."
        summary = f"Short on {_iso_short(first_shortfall.get('date'))}, covered by the {_iso_short(next_paycheck)} paycheck."
    elif first_shortfall:
        title = f"Plan for the {first_shortfall.get('cause')} shortfall."
        summary = f"You'll be ${first_shortfall.get('amount'):,.2f} short on {_iso_short(first_shortfall.get('date'))}; allocate more from the next paycheck."
    elif runway is not None and runway == 0:
        title = "You're running tight to payday."
        summary = f"No runway remains before your {_iso_short(next_paycheck)} paycheck."
    elif runway is not None and runway > 0:
        title = f"You have about {runway} day{'s' if runway != 1 else ''} of runway."
        summary = "Projected to cover known obligations before the next paycheck."
    else:
        title = "Your plan is steady."
        summary = "No material change detected."
    # Attach forecast evidence (commitment factors) so a suggestion can link back.
    for factor in forecast.get("factors") or ():
        if factor.get("kind") == "commitment":
            evidence.append(
                {
                    "id": str(factor.get("name") or factor.get("explanation") or "commitment"),
                    "span": factor.get("explanation") or "commitment",
                    "label": factor.get("explanation") or "commitment",
                }
            )
    return {
        "title": title,
        "summary": summary,
        "evidence": evidence[:3],
    }


def build_today(
    repository: FinancialRepository,
    commitment_repository=None,
    rule_repository=None,
    *,
    now: Optional[datetime] = None,
    paycheck=None,
    spend_selection=None,
) -> dict[str, object]:
    """Build a conservative Today summary from normalized repository records.

    ``spend_selection`` is the newest OBSERVED Crew spend-pocket selection (OS-113), or ``None``
    when no snapshot has been recorded. It decides which pocket the figure treats as spendable, and
    the basis it used travels out in the breakdown so the panel can state which one that was.
    """
    accounts = repository.list_accounts()
    # "Next expected income" from the owner's paycheck config (funding source),
    # if set. Falls back to nothing when no paycheck is configured.
    next_inflow = _next_paycheck_inflow(paycheck, now=now)
    cash_accounts = [
        account
        for account in accounts
        if account.is_active and account.account_type in _CASH_ACCOUNT_TYPES
    ]
    total_cash = _currency_total(
        [(account.currency, account.balance) for account in cash_accounts]
    )
    available_cash = _currency_total(
        [
            (
                account.currency,
                account.available_balance
                if account.available_balance is not None
                else account.balance,
            )
            for account in cash_accounts
        ]
    )

    freshness = data_freshness(
        repository,
        account_ids=[account.id for account in accounts],
        include_all_connections=True,
        now=now,
    )
    beacon = None
    if commitment_repository is not None and rule_repository is not None:
        as_of = (now or datetime.now(timezone.utc)).date()
        beacon = asdict(
            forecast(
                repository,
                commitment_repository,
                rule_repository,
                as_of,
                freshness=freshness["status"],
                paycheck=paycheck,
                paycheck_range=_learned_paycheck_range(repository),
            )
        )

    # R20: coherent cash / bills / goals breakdown + setup + next-run summary.
    breakdown = _commitment_breakdown(commitment_repository) if commitment_repository else None
    setup = _setup_summary(breakdown, rules_configured=rule_repository is not None)
    next_run = _next_run_hint(rule_repository, as_of=None)

    # OS-111, owner-decided 2026-09-25: ONE money rule for the whole product, so Today and Plan
    # cannot publish two different "money you can spend" numbers again.
    #
    # The rule (meridian/services/safe_to_spend.py) is the owner's: everything you have, minus
    # every pocket you have set aside. It replaces TWO things that used to live here --
    #   * the "Free to Spend pocket balance" base, and
    #   * D-019's reserve-deficit subtraction.
    # The reserve is now entered into the account's total SIGNED rather than subtracted as a
    # deficit, which is what makes D-019's case fall out of one term instead of two: Crew holds
    # the reserve at account level, outside every pocket (D-015's arithmetic), so a -324.90
    # reserve lowers the total by exactly the amount the old deficit term removed. Subtracting
    # both would double-count it. Nothing is clamped, so a real overdraft still reports negative
    # (D-019 rule 2).
    #
    # The one name-keyed question left is "which pocket is the spend pocket", and it stays in
    # meridian/services/spend_pocket.py: identifying the pocket by Crew's own selectedSpendSubaccount
    # is OS-113's work, and Today still needs it because pocket accounting has to exempt the pocket
    # the owner actually spends from. When it cannot be identified, NO pocket is treated as
    # spendable and each one is named as set aside -- visible and conservative, rather than
    # silently counting an earmarked pocket as free cash.
    bill_reserves = repository.list_bill_reserves()
    spend = safe_to_spend(accounts, bill_reserves, spend_selection=spend_selection)
    # "Committed" (known obligations) is independent of the figure: it is the unfunded
    # bill/commitment total Meridian is tracking toward, published as an observed input so the card
    # is never dead. It is NOT a subtraction any more -- the breakdown in spend_breakdown is what
    # explains the figure, and it uses pockets, not obligation targets.
    known_obligations = (
        _unfunded_bill_total(commitment_repository) if commitment_repository else None
    )
    deficit = reserve_deficit(bill_reserves)
    if spend is not None:
        safe_amount = spend.amount
        safe_status = "available"
        spend_breakdown = spend.as_payload()
    else:
        # Nothing to reason about: no account in the figured currency holds money at all. A zero
        # would claim an observation the read did not make, so the figure is absent and the status
        # says unavailable (the surface already renders that state, and disables the disclosure).
        safe_amount = None
        safe_status = "unavailable"
        spend_breakdown = None

    # The breakdown is built HERE, by the server, rather than left for the client to derive. The
    # surface must be able to say how the number was reached -- that is the whole point of the
    # owner's request for an explanation on the figure -- and a client that re-derived it could
    # drift from the server that computed it, which is exactly how the figure went wrong before.
    #
    # The name is `spend_breakdown` and NOT `breakdown`: `breakdown` above is the COMMITMENTS
    # breakdown and is returned as the top-level key. Naming this one `breakdown` silently
    # clobbered it, so the top-level key came back holding the safe-to-spend lines and
    # test_breakdown_reports_bills_and_goals failed with a KeyError on 'bills_total'. Caught by
    # the full suite; a run of only the new tests would have passed.
    #
    # The breakdown is now assembled by the rule module and published verbatim; the client still
    # does no arithmetic (OS-079 acceptance 3).

    return {
        "total_cash": total_cash,
        "next_inflow": next_inflow,
        "safe_to_spend": {
            "amount": safe_amount,
            "status": safe_status,
            "breakdown": spend_breakdown,
            "inputs": {
                "available_cash": available_cash,
                "known_obligations": known_obligations,
                "reason": None,
                **deficit.as_payload(),
            },
        },
        "upcoming_events": [],
        "forecast": beacon,
        "beacon": _build_beacon_signal(
            beacon, safe_amount, safe_status,
            paycheck_amount=(getattr(paycheck, "amount", None) if paycheck else None),
        ),
        "brief": _build_virgil_brief(beacon, beacon, safe_amount, safe_status),
        "data_freshness": freshness,
        "breakdown": breakdown,
        # OS-060: a bill the observed reserve cannot cover, stated as an exposure
        # rather than left reading as "funded". Read-only arithmetic over observed
        # values; it proposes nothing and moves nothing.
        "reserve_exposure": (
            _coverage_exposure(commitment_repository) if commitment_repository else None
        ),
        "setup": setup,
        "next_run": next_run,
    }


def _commitment_breakdown(commitment_repository) -> Optional[dict]:
    """Cash/bills/goals summary from active commitments (R20)."""
    if commitment_repository is None:
        return None
    active = [
        c for c in commitment_repository.list_active()
    ]
    bills = [c for c in active if c.type == CommitmentType.BILL]
    goals = [
        c for c in active
        if c.type in (CommitmentType.GOAL, CommitmentType.RESERVE, CommitmentType.BUFFER, CommitmentType.DEBT)
    ]
    return {
        "bills": [
            {
                "id": c.id,
                "name": c.name,
                "target": c.target_amount if c.target_amount is not None else c.amount,
                "funded": c.funded_amount,
            }
            for c in bills
        ],
        "goals": [
            {
                "id": c.id,
                "name": c.name,
                "target": c.target_amount if c.target_amount is not None else c.amount,
                "funded": c.funded_amount,
            }
            for c in goals
        ],
        "bills_total": sum((c.target_amount if c.target_amount is not None else (c.amount or 0)) for c in bills),
        "goals_total": sum((c.target_amount if c.target_amount is not None else (c.amount or 0)) for c in goals),
        "bills_funded": sum(c.funded_amount for c in bills),
        "goals_funded": sum(c.funded_amount for c in goals),
    }


def _setup_summary(breakdown, *, rules_configured: bool) -> dict:
    """R20: honest setup checklist (not fabricated)."""
    if breakdown is None:
        return {"state": "needs_commitments", "items": [{"id": "commitments", "done": False, "label": "Add commitments"}]}
    items = []
    items.append({"id": "commitments", "done": True, "label": "Commitments configured"})
    # Native funding rules configured?
    from meridian.funding_repo import FundingRuleRepository  # noqa: F401

    items.append({"id": "funding_rules", "done": bool(rules_configured), "label": "Funding rules configured"})
    return {"state": "ready" if all(i["done"] for i in items) else "in_progress", "items": items}


def _next_run_hint(rule_repository, *, as_of) -> Optional[dict]:
    """R20: next scheduled funding run hint from the active rule set (best-effort)."""
    if rule_repository is None:
        return None
    try:
        from meridian.funding import project_funding  # noqa: F401

        rules = rule_repository.list_all()
        active = [r for r in rules if getattr(r, "status", "active") == "active"]
        if not active:
            return {"state": "no_rules"}
        return {"state": "rules_present", "rule_count": len(active)}
    except Exception:
        return {"state": "unknown"}
