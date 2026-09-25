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


def resolve_cadence(pattern, funding_plans) -> dict[str, object]:
    """THE cadence, resolved in the order the rest of the app already uses.

    `meridian/api.py::_paycheck_config` has answered this question the same way since 2026-09-19: Crew's
    funding plan outranks every other leg, on the owner's directive that the paycheck "SHOULD be a crew
    record", and `meridian/providers/base.py::FundingPlanCandidate` calls that record the owner's "income
    source / Funding Cadence". This settings payload reported only the OBSERVED pattern instead, so the
    Cadence card could read "Not recognized" beside a Crew cadence listed lower on the same page
    (owner-reported 2026-09-24: "payday is the funding mechanism, so the payday and when it lands is the
    cadence, this isn't consistent").

    One resolver, one answer, and the source is named so the card can say where the figure came from
    rather than implying the app does not know. When Crew reports more than one distinct cadence the
    card names the record it used and says how many others exist -- a single figure must not silently
    stand in for several.
    """
    crew = [
        plan
        for plan in funding_plans
        if isinstance(plan, dict) and plan.get("cadence")
    ]
    if crew:
        governing = crew[0]
        distinct = {str(plan["cadence"]) for plan in crew}
        return {
            "value": governing["cadence"],
            "source": "crew",
            "source_label": "Crew paycheck",
            "plan_id": governing.get("id"),
            "plan_name": governing.get("name"),
            "other_records": len(crew) - 1,
            "distinct_cadences": len(distinct),
            "conflict": len(distinct) > 1,
        }
    if pattern is not None:
        return {
            "value": pattern.cadence,
            "source": "observed",
            "source_label": "Learned from your deposits",
            "confidence": pattern.confidence,
            "deposits": len(pattern.evidence_ids),
            "other_records": 0,
            "distinct_cadences": 1,
            "conflict": False,
        }
    return {
        "value": None,
        "source": None,
        "source_label": None,
        "other_records": 0,
        "distinct_cadences": 0,
        "conflict": False,
    }


def build_payday_settings(graph, commitments, rules, *, as_of: date) -> dict[str, object]:
    transactions, _cursor = graph.list_transactions(limit=200)

    # Crew's funding plans, so the surface can ADDRESS one. The plan id is Crew's own
    # external_id and is the identity the write path needs: the write operations are
    # update/delete_crew_paycheck_funding_plan, and the manifest records that the update is
    # 'Identified by the approved proposal's fundingPlanId'. The NAME is deliberately not the
    # key -- the record's own docstring says the owner renames the plan, so anything keyed on
    # the name breaks on the next rename. Best-effort like the paycheck context path: a read
    # failure must not take the whole settings page down.
    funding_plans: list[dict[str, object]] = []
    try:
        from meridian.repository import FinancialRepository

        financial = (
            graph
            if isinstance(graph, FinancialRepository)
            else FinancialRepository(graph.db_path)
        )
        funding_plans = [
            {
                "id": record.external_id,
                "name": record.name,
                "amount": record.amount,
                "cadence": record.cadence,
            }
            for record in financial.list_funding_plans()
            if getattr(record, "absent_since", None) is None
        ]
    except Exception:  # noqa: BLE001 - observations are best-effort context
        funding_plans = []
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
        # ONE cadence for the surface, resolved in the app's own precedence rather than from the
        # observed pattern alone (OS-104). The observed pattern is still reported separately below,
        # because "what Crew says" and "what Meridian has seen" are different facts and both matter.
        "cadence": resolve_cadence(pattern, funding_plans),
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
        "funding_plans": funding_plans,
        "rules": rule_views,
        "next_run": next_run,
        "learning": learning,
        "data_freshness": data_freshness(graph, include_all_connections=True),
    }
