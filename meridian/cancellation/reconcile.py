"""Post-deadline billing verification using Meridian's transaction read model."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from ..trials import Trial
from .workflow import VerificationSignal


def verify_post_deadline_billing(
    trial: Trial,
    transactions: Iterable[Mapping[str, object]],
    *,
    now: datetime | None = None,
    reconciliation_complete: bool,
) -> tuple[set[VerificationSignal], str]:
    """Return positive billing evidence only after a complete reconciliation window.

    ``reconciliation_complete`` must come from a provider sync that covers the
    merchant and the period after the renewal deadline. An empty local query is
    not enough to claim billing stopped.
    """
    if not isinstance(reconciliation_complete, bool):
        raise TypeError("reconciliation_complete must be bool")
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    deadline = datetime.fromisoformat(trial.trial_ends_at.replace("Z", "+00:00"))
    if reference < deadline or not reconciliation_complete:
        return set(), "Insufficient billing history"
    merchant = trial.service.casefold()
    for transaction in transactions:
        description = str(transaction.get("merchant") or transaction.get("description") or "").casefold()
        occurred = transaction.get("occurred_at")
        if merchant not in description or not occurred:
            continue
        timestamp = datetime.fromisoformat(str(occurred).replace("Z", "+00:00"))
        if timestamp >= deadline:
            return set(), "Post-deadline charge detected"
    return {VerificationSignal.BILLING_STOPPED}, "No post-deadline charge in complete reconciliation"
