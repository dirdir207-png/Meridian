"""Explicit approval gate for cancellation submissions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .repository import CancellationAction


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    requires_confirmation: bool
    reason: str
    expires_at: str | None = None


def evaluate_submission(
    action: CancellationAction,
    *,
    owner_approved: bool,
    known_recipe: bool,
    confidence: float,
    allowlisted: bool = False,
    essential: bool = False,
    multi_operation: bool = False,
) -> ApprovalDecision:
    """Decide whether a provider submit control may be exposed.

    This is intentionally a decision object, not an executor. A direct route is
    allowed only for a verified deterministic recipe; all other routes require
    explicit current owner approval.
    """
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if allowlisted:
        return ApprovalDecision(False, True, "allowlisted service requires confirmation")
    if essential:
        return ApprovalDecision(False, True, "essential service requires per-service confirmation")
    requires = (not known_recipe) or confidence < 0.9 or multi_operation
    if requires and not owner_approved:
        return ApprovalDecision(False, True, "owner approval required for uncertain or composed cancellation")
    if not owner_approved and action.channel != "live_browser":
        return ApprovalDecision(False, True, "owner approval required before outbound cancellation")
    expires = (datetime.now(timezone.utc).replace(microsecond=0)).isoformat()
    return ApprovalDecision(True, False, "submission may be presented to the provider", expires)
