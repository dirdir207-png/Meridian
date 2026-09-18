"""Strict checkout/receipt capture adapter for creating trial records."""
from __future__ import annotations

from typing import Any

from ..trials import Trial, TrialRepository

_REQUIRED = ("service", "trial_started_at", "trial_ends_at")


def capture_trial(repository: TrialRepository, payload: dict[str, Any]) -> Trial:
    """Persist only explicit merchant terms; never guess a renewal date.

    Callers may pass additional checkout metadata, but dates must be supplied by
    the merchant surface or receipt parser and are recorded as checkout evidence.
    """
    missing = [field for field in _REQUIRED if not payload.get(field)]
    if missing:
        raise ValueError(f"explicit trial terms required: {', '.join(missing)}")
    values = {
        key: payload[key]
        for key in (
            "service", "account_identifier", "plan_name", "trial_started_at",
            "trial_ends_at", "buffer_days", "price_after", "cadence", "timezone",
            "allowlisted", "essential", "autonomy_tier", "confidence",
        )
        if key in payload
    }
    values["source_of_truth"] = "checkout_capture"
    return repository.create(**values)
