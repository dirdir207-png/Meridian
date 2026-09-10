"""Deterministic human hand-off brief for trials that need owner action."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from ..trials import Trial

_CHANNEL_LADDER = (
    ("live_browser", "Open the merchant account in a live session and cancel; do not accept pause or downgrade.", True),
    ("official_api", "Use the merchant's official account cancellation control, if available.", False),
    ("email", "Send a cancellation notice and retain delivery/acknowledgement evidence.", False),
    ("support", "Contact support and request cancellation; record the confirmation reference.", False),
)


def build_cancellation_brief(
    trial: Trial,
    *,
    now: datetime | None = None,
    existing_channels: Iterable[str] = (),
) -> dict[str, object]:
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    deadline = datetime.fromisoformat(trial.cancel_by.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    seconds_remaining = int((deadline - reference).total_seconds())
    days_remaining = seconds_remaining // 86400
    used = set(existing_channels)
    channels = [
        {"channel": channel, "instruction": instruction, "recommended": recommended, "already_attempted": channel in used}
        for channel, instruction, recommended in _CHANNEL_LADDER
    ]
    return {
        "service": trial.service,
        "account_identifier": trial.account_identifier,
        "plan_name": trial.plan_name,
        "deadline": trial.cancel_by,
        "buffer_days": trial.buffer_days,
        "timezone": trial.timezone,
        "days_remaining": days_remaining,
        "overdue": seconds_remaining < 0,
        "status": trial.status,
        "channels": channels,
        "evidence_checklist": [
            "Cancellation confirmation or reference number",
            "Account page showing no active renewal",
            "Post-deadline transaction check",
        ],
        "guardrails": [
            "Do not accept pause, downgrade, or retention offers unless explicitly chosen.",
            "Do not report Billing stopped without positive verification evidence.",
        ],
    }
