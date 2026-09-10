"""Deterministic escalation planning; this module never sends or disputes."""
from __future__ import annotations

from dataclasses import dataclass

from ..trials import Trial
from .repository import CancellationAction


@dataclass(frozen=True)
class EscalationStep:
    channel: str
    purpose: str
    requires_owner: bool
    blocked_reason: str | None = None


def build_escalation_plan(
    trial: Trial,
    actions: list[CancellationAction],
    *,
    allow_payment_dispute: bool = False,
) -> dict[str, object]:
    """Produce the next human-reviewable route without performing it."""
    attempted = {action.channel for action in actions}
    steps: list[EscalationStep] = []
    ladder = (
        ("live_browser", "Re-open the account and capture the final cancellation state.", True),
        ("support", "Ask support for cancellation and a confirmation reference.", True),
        ("email", "Send a dated cancellation notice and retain delivery evidence.", True),
        ("certified_mail", "Prepare certified mail when digital channels fail.", True),
    )
    for channel, purpose, requires_owner in ladder:
        if channel in attempted:
            continue
        steps.append(EscalationStep(channel, purpose, requires_owner))
    if allow_payment_dispute:
        steps.append(EscalationStep("payment_dispute", "Prepare a disputed-charge packet after a post-deadline charge.", True))
    return {
        "service": trial.service,
        "trial_id": trial.id,
        "status": trial.status,
        "next": [step.__dict__ for step in steps],
        "read_only": True,
        "requires_owner": True,
        "guardrails": [
            "Do not claim cancellation until positive verification exists.",
            "Do not submit a dispute without owner review and a post-deadline charge.",
        ],
    }
