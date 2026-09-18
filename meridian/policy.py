"""Read-only constitution evaluation; this module never executes actions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class Constitution:
    minimum_buffer: Optional[float] = None
    maximum_automatic_amount: Optional[float] = None
    allowed_action_types: tuple[str, ...] = ()
    prohibited_action_types: tuple[str, ...] = ()
    active: bool = False


@dataclass(frozen=True)
class ActionPlan:
    action_type: str
    amount: Optional[float] = None
    source_account: Optional[str] = None
    destination_account: Optional[str] = None
    automatic: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    rules_evaluated: tuple[str, ...]
    blocking_rules: tuple[str, ...]
    evidence: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: float
    recovery_action: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("rules_evaluated", "blocking_rules", "evidence", "assumptions"):
            result[key] = list(result[key])
        return result


def evaluate_constitution(constitution: Constitution, plan: ActionPlan, *, evidence: Mapping[str, Any] | None = None) -> PolicyDecision:
    """Evaluate a plan without approving, proposing, or executing it."""
    if not constitution.active:
        return PolicyDecision("cannot_evaluate", (), (), (), ("constitution is inactive",), 0.0, "Owner must explicitly activate a constitution before evaluation.")
    evidence = evidence or {}
    evaluated: list[str] = []
    blocked: list[str] = []
    facts: list[str] = []
    assumptions: list[str] = []
    if plan.action_type in constitution.prohibited_action_types:
        evaluated.append("prohibited_action_types")
        blocked.append("prohibited_action_types")
    if constitution.allowed_action_types and plan.action_type not in constitution.allowed_action_types:
        evaluated.append("allowed_action_types")
        blocked.append("allowed_action_types")
    if plan.automatic and constitution.maximum_automatic_amount is None:
        evaluated.append("maximum_automatic_amount")
        blocked.append("automatic_amount_limit_missing")
    elif plan.automatic and plan.amount is not None and plan.amount > constitution.maximum_automatic_amount:
        evaluated.append("maximum_automatic_amount")
        blocked.append("maximum_automatic_amount")
    if plan.automatic and plan.amount is None:
        evaluated.append("automatic_amount_present")
        blocked.append("automatic_amount_missing")
    if constitution.minimum_buffer is not None:
        evaluated.append("minimum_buffer")
        remaining = evidence.get("remaining_after_action")
        if remaining is None:
            assumptions.append("remaining_after_action is not available")
        elif float(remaining) < constitution.minimum_buffer:
            blocked.append("minimum_buffer")
            facts.append(f"remaining_after_action={float(remaining):.2f}")
    confidence = 1.0 if not assumptions else 0.5
    if blocked:
        return PolicyDecision("blocked", tuple(evaluated), tuple(blocked), tuple(facts), tuple(assumptions), confidence, "Do not execute; resolve the blocking rule or provide current evidence.")
    if assumptions:
        return PolicyDecision("requires_clarification", tuple(evaluated), (), tuple(facts), tuple(assumptions), confidence, "Provide the missing evidence before evaluating this plan.")
    return PolicyDecision("requires_approval", tuple(evaluated), (), tuple(facts), (), confidence, "Create a proposal and obtain explicit owner approval; this evaluator does not authorize execution.")
