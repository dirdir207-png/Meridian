"""Read-only deadline projection for UI and future notification schedulers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from ..trials import Trial, deadline_events


def upcoming_deadlines(
    trials: Iterable[Trial],
    *,
    now: datetime | None = None,
    include_overdue: bool = True,
) -> list[dict[str, object]]:
    """Flatten active trial checkpoints in chronological order.

    This function only plans reminders. It never creates an action or contacts a
    merchant, making it safe for read-only views and dry-run schedulers.
    """
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    projected: list[dict[str, object]] = []
    for trial in trials:
        if trial.status in {"canceled", "unknown"}:
            continue
        for event in deadline_events(trial, now=reference):
            if not include_overdue and event["overdue"] == "true":
                continue
            projected.append({"trial_id": trial.id, "service": trial.service, **event})
    return sorted(projected, key=lambda event: str(event["due_at"]))
