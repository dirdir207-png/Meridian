"""Explicitly inert adapter implementations for integration and dry-run tests."""
from __future__ import annotations

from typing import Any

from .repository import CancellationAction


class DryRunAdapter:
    """Return a planned provider result without contacting any external service."""

    def __init__(self, *, reference: str = "dry-run"):
        self.reference = reference

    def submit(self, action: CancellationAction) -> dict[str, Any]:
        return {
            "dry_run": True,
            "reference": self.reference,
            "channel": action.channel,
            "external_contact": False,
        }
