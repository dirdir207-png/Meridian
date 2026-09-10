"""Provider adapter boundary; no provider call is made by the default implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .approval import ApprovalDecision
from .repository import CancellationAction


class CancellationAdapter(Protocol):
    def submit(self, action: CancellationAction) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ExecutionResult:
    attempted: bool
    state: str
    reason: str
    provider_result: dict[str, Any] | None = None


def execute_approved(
    action: CancellationAction,
    decision: ApprovalDecision,
    *,
    adapter: CancellationAdapter | None = None,
) -> ExecutionResult:
    """Execute only with an approved decision and explicit adapter.

    The default path is a hard stop. This prevents accidental live merchant
    interaction merely because an API endpoint was called.
    """
    if not decision.approved:
        return ExecutionResult(False, "planned", "approval required")
    if adapter is None:
        return ExecutionResult(False, "planned", "no provider adapter configured")
    try:
        result = adapter.submit(action)
    except Exception as error:  # adapter failures must not be reported as cancellation
        return ExecutionResult(False, "failed", f"provider adapter failed: {type(error).__name__}")
    if not isinstance(result, dict):
        return ExecutionResult(False, "failed", "provider adapter returned invalid result")
    return ExecutionResult(True, "attempted", "provider submission completed; verification still required", result)
