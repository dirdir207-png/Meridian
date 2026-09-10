"""Small scheduler seam for trial reminders.

The default cycle is persistence-only. A delivery callback must be explicitly
provided by an owning runtime, keeping outbound notification policy outside the
trial ledger.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from .notifications import TrialNotification, TrialNotificationRepository


def run_reminder_cycle(
    db_path: str,
    *,
    now: datetime | None = None,
    deliver: Callable[[TrialNotification], Any] | None = None,
) -> list[TrialNotification]:
    repository = TrialNotificationRepository(db_path)
    pending = repository.materialize_due(now=now)
    if deliver is None:
        return pending
    delivered: list[TrialNotification] = []
    for notification in pending:
        deliver(notification)
        delivered.append(repository.mark_sent(notification.id))
    return delivered
