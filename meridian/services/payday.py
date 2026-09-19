"""Read-only Payday & Funding settings composed from existing Meridian data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from meridian.funding import project_funding
from meridian.paycheck_learning import (
    PaycheckLearningFloorRepository,
    observations_on_or_after,
)
from meridian.payday import recognize_payday
from meridian.services.today import data_freshness


def _rule_payload(rule, commitment) -> dict[str, object]:
    return {
        "id": rule.id,
        "commitment_id": rule.commitment_id,
        "commitment": commitment.name if commitment is not None else "Unknown commitment",
        "kind": rule.kind,
        "amount": float(rule.amount) if rule.amount is not None else None,
        "percent": float(rule.percent) if rule.percent is not None else None,
        "cadence": rule.cadence,
        "paused": rule.paused,
        "priority": rule.priority,
    }


def build_learning_window(graph, transactions=None) -> dict[str, object]:
    """The owner's learnable window, as a reportable payload (OS-051).

    One builder, used by both the settings read and the reset endpoint, so the control
    and the report can never disagree about what the floor currently excludes. The
    excluded count is the point of it: a reset whose effect is invisible is not
    governable.
    """
    stored = PaycheckLearningFloorRepository(graph.db_path).get()
    floor = stored.floor if stored is not None else None
    if transactions is None:
        transactions, _cursor = graph.list_transactions(limit=200)
    included = len(observations_on_or_after(transactions, floor))
    return {
        "active": floor is not None,
        "floor": floor,
        "set_at": stored.set_at if stored is not None else None,
        "included": included,
        "excluded": len(transactions) - included,
    }


def build_payday_settings(graph, commitments, rules, *, as_of: date) -> dict[str, object]:
    transactions, _cursor = graph.list_transactions(limit=200)
    # The owner's learning window (OS-051). It governs which observations may be learned
    # from, so it is read BEFORE recognition and reported alongside the result.
    learning = build_learning_window(graph, transactions)
    pattern = recognize_payday(transactions, as_of=as_of, floor=learning["floor"])
    rule_views = []
    next_contributions = []
    for rule in rules.list_all():
        commitment = commitments.get(int(rule.commitment_id))
        rule_views.append(_rule_payload(rule, commitment))
        if pattern is None or commitment is None:
            continue
        projection = project_funding(
            rule,
            commitment,
            [(pattern.next_date, Decimal(str(pattern.typical_amount)))],
            as_of=as_of,
        )
        for event in projection.events:
            if event.date == pattern.next_date and event.amount > 0:
                next_contributions.append(
                    {
                        "rule_id": rule.id,
                        "commitment": commitment.name,
                        "amount": float(event.amount),
                        "explanation": list(event.explanation),
                    }
                )

    cash_accounts = [
        account
        for account in graph.list_accounts()
        if account.is_active and account.account_type in {"cash", "checking", "savings"}
    ]
    next_run = None
    if pattern is not None:
        next_run = {
            "date": pattern.next_date.isoformat(),
            "kind": "proposal",
            "total": round(sum(item["amount"] for item in next_contributions), 2),
            "contributions": next_contributions,
        }
    return {
        "state": "current" if pattern is not None else "unavailable",
        "pattern": (
            {
                "cadence": pattern.cadence,
                "next_date": pattern.next_date.isoformat(),
                "typical_amount": pattern.typical_amount,
                "confidence": pattern.confidence,
                "evidence_count": len(pattern.evidence_ids),
            }
            if pattern is not None
            else None
        ),
        "funding_source": (
            {
                "account_id": cash_accounts[0].id,
                "name": cash_accounts[0].name,
            }
            if cash_accounts
            else None
        ),
        "rules": rule_views,
        "next_run": next_run,
        "learning": learning,
        "data_freshness": data_freshness(graph, include_all_connections=True),
    }
