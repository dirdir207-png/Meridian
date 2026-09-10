"""Safe notification payloads for an owning delivery channel."""
from __future__ import annotations

from dataclasses import dataclass

from .notifications import TrialNotification


@dataclass(frozen=True)
class TrialReminderPayload:
    title: str
    body: str
    tag: str
    url: str
    data: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "body": self.body,
            "tag": self.tag,
            "url": self.url,
            "data": self.data,
        }


def build_trial_reminder_payload(
    notification: TrialNotification,
    *,
    service: str,
) -> TrialReminderPayload:
    """Build a channel-neutral reminder; it does not send or approve anything."""
    labels = {
        "7_days": "7 days",
        "3_days": "3 days",
        "1_day": "1 day",
        "deadline": "today",
    }
    label = labels.get(notification.kind)
    if label is None:
        raise ValueError("unknown trial notification kind")
    return TrialReminderPayload(
        title=f"Trial cancellation reminder: {service}",
        body=f"Review {service} and cancel before the trial deadline ({label}).",
        tag=f"trial-{notification.trial_id}-{notification.kind}",
        url=f"/meridian/trials/{notification.trial_id}",
        data={
            "trial_id": notification.trial_id,
            "notification_id": notification.id,
            "kind": notification.kind,
            "read_only": True,
        },
    )
