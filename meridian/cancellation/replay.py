"""Deterministic end-to-end cancellation workflow replay against a stub adapter."""
from __future__ import annotations

from dataclasses import dataclass

from .approval import evaluate_submission
from .executor import CancellationAdapter, execute_approved
from .repository import CancellationRepository
from .workflow import CancellationState, VerificationSignal


@dataclass(frozen=True)
class ReplayResult:
    action_id: int
    attempted: bool
    verified: bool
    status: str
    events: tuple[str, ...]


def replay_stubbed_cancellation(
    repository: CancellationRepository,
    action_id: int,
    adapter: CancellationAdapter,
    *,
    verification: VerificationSignal | None = None,
) -> ReplayResult:
    """Exercise attempt and verification without contacting a real provider."""
    action = repository.get(action_id)
    if action is None:
        raise KeyError(action_id)
    events = ["loaded"]
    decision = evaluate_submission(
        action,
        owner_approved=True,
        known_recipe=True,
        confidence=1,
    )
    result = execute_approved(action, decision, adapter=adapter)
    if not result.attempted:
        return ReplayResult(action_id, False, False, result.reason, tuple(events + ["blocked"]))
    action = repository.transition(action_id, CancellationState.ATTEMPTED)
    events.append("attempted")
    if verification is None:
        repository.transition(action_id, CancellationState.UNVERIFIED)
        return ReplayResult(action_id, True, False, "Unverified", tuple(events + ["unverified"]))
    if verification not in {VerificationSignal.BILLING_STOPPED, VerificationSignal.CARD_CLOSED}:
        repository.transition(action_id, CancellationState.AWAITING_ACK)
        return ReplayResult(action_id, True, False, "Acknowledged", tuple(events + ["acknowledged"]))
    repository.transition(action_id, CancellationState.AWAITING_ACK)
    repository.transition(action_id, CancellationState.VERIFIED, signals={verification})
    return ReplayResult(action_id, True, True, "Billing stopped", tuple(events + ["verified"]))
