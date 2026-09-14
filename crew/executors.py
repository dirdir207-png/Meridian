"""Executor registry for approved actions.

Each whitelisted action type maps to one vetted function (wrapped as a
params-dict adapter) plus an optional verifier that confirms the outcome after
execution. Executors inherit the safety semantics of the functions they wrap
(e.g., move_money's no-retry / uncertain-write contract).

A successful execution with no registered verifier ends in EXECUTED
(verification pending), never VERIFIED: only a readback may claim verification.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .actions import ActionState, ActionStore, IllegalTransitionError


@dataclass(frozen=True)
class ExecutorSpec:
    execute: Callable[[Dict[str, Any]], Dict[str, Any]]
    verifier: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None
    # Optional guard evaluated after the atomic claim and BEFORE any provider
    # call. It compares the state the approver reviewed against the state now,
    # and returns a dict: {"ok": True} to proceed, or {"ok": False,
    # "code": "conflict"|"unverifiable", "reason": ..., "reviewed": ...,
    # "current": ...} to refuse. Declaring one makes a missing reviewed state a
    # refusal, never an assumption of agreement.
    precondition: Optional[Callable[[Dict[str, Any], Any], Dict[str, Any]]] = None

    def __repr__(self) -> str:
        return "ExecutorSpec()"


def _precondition_payload(
    code: str,
    message: str,
    reviewed: Any,
    current: Any,
    reason: str,
    check: Optional[str] = None,
) -> Dict[str, Any]:
    """The recorded refusal of an action whose reviewed state no longer holds.

    ``provider_truth`` is False on purpose: this compares our own record against
    what was approved. It is not a provider readback and must not be read as one.
    """
    return {
        "error": message,
        "error_code": code,
        "sent_to_provider": False,
        "retry_allowed": False,
        "verify_state": True,
        "precondition": {
            "check": check,
            "reason": reason,
            "reviewed": reviewed,
            "current": current,
            "provider_truth": False,
        },
    }


def _precondition_refusal(
    spec: "ExecutorSpec", request: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Refuse the action, or return None when execution may proceed.

    A mutation must never run against state its approver did not review, so a
    missing or unreadable reviewed state refuses rather than assuming agreement.
    """
    if spec.precondition is None:
        return None

    base_state = request.get("base_state")
    if base_state is None:
        return _precondition_payload(
            "precondition_unverifiable",
            "This approval was recorded before Meridian captured the state that was "
            "reviewed, so it cannot be checked against anything. Nothing was sent to "
            "Crew. Review the record and approve it again.",
            reviewed=None,
            current=None,
            reason="no reviewed state was recorded with this approval",
        )

    try:
        verdict = spec.precondition(request.get("params") or {}, base_state)
    except Exception as exc:  # noqa: BLE001 - any failure here must refuse
        return _precondition_payload(
            "precondition_unverifiable",
            "The state that was reviewed could not be checked, so nothing was sent to "
            f"Crew ({exc}). Review the record and approve it again.",
            reviewed=base_state,
            current=None,
            reason="the precondition could not be evaluated",
        )

    if isinstance(verdict, dict) and verdict.get("ok"):
        return None

    verdict = verdict if isinstance(verdict, dict) else {}
    conflicting = verdict.get("code") == "conflict"
    return _precondition_payload(
        "precondition_conflict" if conflicting else "precondition_unverifiable",
        verdict.get("reason")
        or (
            "The record changed after you approved this action, so nothing was sent to "
            "Crew. Review it and approve again."
        ),
        reviewed=verdict.get("reviewed", base_state),
        current=verdict.get("current"),
        reason=verdict.get("reason") or "",
        check=verdict.get("check"),
    )


def _failure(payload: Dict[str, Any], error: str, code: str) -> Dict[str, Any]:
    payload.setdefault("error", error)
    payload.setdefault("error_code", code)
    return payload


def execute_approved_action(
    store: ActionStore,
    request_id: str,
    executors: Dict[str, ExecutorSpec],
    execution_key: Optional[str] = None,
) -> Dict[str, Any]:
    request = store.claim_for_execution(request_id, execution_key or uuid.uuid4().hex)

    spec = executors.get(request["type"])
    if spec is None:
        return store.mark_failed(
            request_id,
            _failure({}, f"No executor registered for action type '{request['type']}'", "no_executor"),
        )

    refusal = _precondition_refusal(spec, request)
    if refusal is not None:
        # The claim already moved the action to EXECUTING, so this is recorded as
        # a failure. FAILED is terminal, which is what makes the refusal
        # unretryable: nothing re-runs a mutation that lost its reviewed state.
        return store.mark_failed(request_id, refusal)

    try:
        result = spec.execute(request.get("params") or {})
    except Exception as exc:
        return store.mark_failed(
            request_id,
            _failure(
                {"verify_state": True},
                str(exc) or "Executor raised an exception",
                "executor_exception",
            ),
        )

    if not isinstance(result, dict) or not result.get("success"):
        payload = result if isinstance(result, dict) else {}
        return store.mark_failed(
            request_id,
            _failure(payload, "Action did not complete successfully", "action_failed"),
        )

    if spec.verifier is None:
        # No readback verifier is registered for this operation. The provider
        # accepted the write, but Meridian cannot confirm the resulting state, so
        # the action stays EXECUTED (verification pending) instead of claiming
        # VERIFIED. Marking it verified would assert a readback that never
        # happened — see A05 in the consolidated handoff.
        store.mark_executed(
            request_id,
            result={
                **result,
                "verification": {
                    "ok": None,
                    "check": "no-verifier-registered",
                    "reason": (
                        f"No readback verifier is registered for '{request['type']}'. "
                        "The provider accepted the write; the resulting state is unconfirmed."
                    ),
                },
            },
        )
        return store.get(request_id)

    store.mark_executed(request_id, result=result)

    try:
        verification = spec.verifier(request["params"] or {}, result)
        ok = verification.get("ok")
    except Exception as exc:
        # The provider accepted the write; a verifier failure cannot prove that
        # it failed. Preserve an unresolved, terminally non-retryable receipt.
        return store.record_verification_pending(
            request_id,
            {
                "ok": None,
                "check": "verifier-exception",
                "provider_truth": False,
                "reason": f"Verification raised: {exc}" if str(exc) else "Verification raised",
                "retry_allowed": False,
            },
        )

    if ok is None:
        # A readback verifier ran but could not confirm the resulting state. The
        # provider already accepted the write, so this is neither VERIFIED nor
        # FAILED: it stays EXECUTED (verification pending), mirroring the
        # no-verifier-registered honesty (A06).
        return store.record_verification_pending(
            request_id,
            {
                "ok": None,
                "check": verification.get("check") if isinstance(verification, dict) else None,
                "provider_truth": bool(verification.get("provider_truth")) if isinstance(verification, dict) else False,
                "reason": (
                    verification.get("reason") if isinstance(verification, dict) else None
                )
                or "The resulting state could not be confirmed.",
                "retry_allowed": False,
            },
        )

    if not ok:
        return store.mark_failed(
            request_id,
            _failure(
                {"verification": verification},
                "Post-execution verification failed",
                "verification_failed",
            ),
        )

    return store.mark_verified(request_id, verification=verification)


def expire_stale_approvals(
    store: ActionStore,
    ttl_seconds: float,
    now: Optional[datetime] = None,
) -> List[str]:
    """Expire APPROVED actions older than ttl; returns expired ids."""
    reference = now or datetime.now()
    expired_ids: List[str] = []
    for request in store.list_by_state(ActionState.APPROVED):
        decided_at = request.get("decided_at")
        if not decided_at:
            continue
        try:
            approved_at = datetime.fromisoformat(decided_at)
            # SQLite stores both legacy naive timestamps and newer aware ones;
            # compare them on the same wall-clock basis rather than raising a
            # TypeError during the scheduled cleanup sweep.
            if approved_at.tzinfo is not None and reference.tzinfo is None:
                reference_for_compare = reference.replace(tzinfo=approved_at.tzinfo)
            elif approved_at.tzinfo is None and reference.tzinfo is not None:
                reference_for_compare = reference.replace(tzinfo=None)
            else:
                reference_for_compare = reference
            age = (reference_for_compare - approved_at).total_seconds()
        except (TypeError, ValueError):
            continue
        if age >= ttl_seconds:
            try:
                store.expire(request["id"])
            except IllegalTransitionError:
                continue
            expired_ids.append(request["id"])
    return expired_ids
