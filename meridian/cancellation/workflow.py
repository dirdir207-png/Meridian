"""Action -> verify -> escalate state machine for subscription cancellation.

This module deliberately contains no browser or provider calls. Adapters submit
observations into these typed transitions; a click alone can never become proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CancellationState(StrEnum):
    PLANNED = "planned"
    ATTEMPTED = "attempted"
    AWAITING_ACK = "awaiting_ack"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    ESCALATED = "escalated"
    FAILED = "failed"


class VerificationSignal(StrEnum):
    ACCOUNT_PAGE = "account_page"
    CONFIRMATION_REFERENCE = "confirmation_reference"
    BILLING_STOPPED = "billing_stopped"
    CARD_CLOSED = "card_closed"


_SIGNAL_RANK = {
    VerificationSignal.ACCOUNT_PAGE: 1,
    VerificationSignal.CONFIRMATION_REFERENCE: 2,
    VerificationSignal.BILLING_STOPPED: 3,
    VerificationSignal.CARD_CLOSED: 4,
}

_ALLOWED = {
    CancellationState.PLANNED: {CancellationState.ATTEMPTED},
    CancellationState.ATTEMPTED: {
        CancellationState.AWAITING_ACK,
        CancellationState.UNVERIFIED,
        CancellationState.FAILED,
    },
    CancellationState.AWAITING_ACK: {
        CancellationState.VERIFIED,
        CancellationState.UNVERIFIED,
        CancellationState.ESCALATED,
    },
    CancellationState.UNVERIFIED: {CancellationState.ATTEMPTED, CancellationState.ESCALATED},
    CancellationState.ESCALATED: {CancellationState.ATTEMPTED, CancellationState.VERIFIED},
    CancellationState.VERIFIED: set(),
    CancellationState.FAILED: {CancellationState.ATTEMPTED, CancellationState.ESCALATED},
}


@dataclass(frozen=True)
class RoutingResult:
    tier: str
    requires_approval: bool
    reason: str


def advance(current: CancellationState, target: CancellationState) -> CancellationState:
    """Validate and return a legal transition; terminal success cannot regress."""
    if target not in _ALLOWED.get(current, set()):
        raise ValueError(f"invalid cancellation transition: {current} -> {target}")
    return target


def verification_status(signals: set[VerificationSignal] | frozenset[VerificationSignal]) -> str:
    """Return the honest user-facing status for observed verification signals."""
    if not signals:
        return "Unverified"
    if not all(isinstance(signal, VerificationSignal) for signal in signals):
        raise ValueError("signals must contain VerificationSignal values")
    strongest = max(_SIGNAL_RANK[signal] for signal in signals)
    if strongest >= _SIGNAL_RANK[VerificationSignal.BILLING_STOPPED]:
        return "Billing stopped"
    if strongest == _SIGNAL_RANK[VerificationSignal.CONFIRMATION_REFERENCE]:
        return "Acknowledged"
    return "Requested"


def route_cancellation(
    *,
    known_recipe: bool,
    confidence: float,
    allowlisted: bool,
    essential: bool,
    high_risk_channel: bool = False,
    multi_operation: bool = False,
) -> RoutingResult:
    """Apply canceler guardrails without silently upgrading uncertain work."""
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if allowlisted:
        return RoutingResult("propose", True, "service is allowlisted")
    if essential:
        return RoutingResult("propose", True, "essential service requires per-service confirmation")
    if high_risk_channel:
        return RoutingResult("propose", True, "high-risk channel requires confirmation")
    if not known_recipe:
        return RoutingResult("propose", True, "merchant recipe is not verified")
    if confidence < 0.9:
        return RoutingResult("propose", True, "terms or merchant match are uncertain")
    if multi_operation:
        return RoutingResult("propose", True, "cancellation is a composed multi-operation plan")
    return RoutingResult("direct", False, "verified recipe and deterministic action")


def status_for_transition(target: CancellationState, signals: set[VerificationSignal] | None = None) -> str:
    """Map a persisted state to honest copy; verified requires positive evidence."""
    if target is CancellationState.VERIFIED:
        status = verification_status(signals or set())
        if status != "Billing stopped":
            raise ValueError("verified requires billing-stopped or card-closed evidence")
        return status
    if target is CancellationState.AWAITING_ACK:
        return "Requested"
    if target is CancellationState.ESCALATED:
        return "Failed — needs you"
    if target is CancellationState.FAILED:
        return "Failed — needs you"
    return "Unverified"
