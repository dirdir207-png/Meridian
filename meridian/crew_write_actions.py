"""Crew write-back executors for the proposal→approval→execute pipeline.

Each executor wraps meridian.crew_write.execute_crew_write so an approved
proposal can push a bill/rule change to Crew through the crew-write CLI.
The ExecutorSpec.execute gets the proposal params; the verifier re-reads the
local commitment to confirm the change landed.
"""

from typing import Any, Callable, Dict, Optional

from .commitments import CommitmentRepository
from .crew_write import execute_crew_write

# Wire field -> local commitment field, for the fields `update_crew_bill` can
# change. Only the fields an action actually touches are compared, so unrelated
# churn between approval and execution cannot refuse a still-valid write.
_BILL_REVIEWED_FIELDS = {"name": "name", "amount": "amount"}

# Params payloads follow the Crew wire contract (camelCase) so the executor is a
# thin pass-through; the UI/proposal layer maps local records to wire form.


def _crew_write_executor(operation: str):
    def execute(params: Dict[str, Any]) -> Dict[str, Any]:
        # Autopilot rule create/edit must be run through the verified formula
        # builder so the required per-action ids (accountId/subaccountId) are
        # filled — otherwise Crew rejects the raw {roundToNearest} with a null
        # accountId. We send the enriched variables (not the raw params).
        if operation in ("create_autopilot_rule", "edit_autopilot_rule"):
            from .crew_commands import build_command_payload

            kind = "edit_autopilot_rule" if operation == "edit_autopilot_rule" else "create_autopilot_rule"
            try:
                _op, _query, variables = build_command_payload(kind, dict(params))
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc
            outcome = execute_crew_write(operation, variables.get("input") or params)
        else:
            outcome = execute_crew_write(operation, params)
        if not outcome.get("ok"):
            error_code = outcome.get("error") or "failed"
            return {
                "success": False,
                "error": outcome.get("message") or "Crew write failed",
                "error_code": error_code,
                "retry_allowed": False,
                "verify_state": error_code == "uncertain" or bool(outcome.get("verify_state")),
            }
        # execute_approved_action expects an explicit success flag.
        return {"success": True, "crew": outcome}

    return execute


def _verify_stored(db_path: str, check_field: str):
    """Returns a verifier that re-reads the commitment for an expected value.

    The Crew write acceptance is the authoritative result; the local re-read is
    advisory (records may not be created locally yet, or the refresh hasn't
    repulled the change). Never fail an accepted Crew write over local state.
    """
    repo = CommitmentRepository(db_path)

    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        commitment_id = params.get("commitment_id")
        if commitment_id is None:
            return {"ok": True, "check": "crew-write-accepted", "note": "no local record to re-read"}
        record = repo.get_commitment(int(commitment_id))
        expected = params.get(check_field)
        actual = getattr(record, check_field) if record else None
        local_ok = record is not None and (expected is None or actual == expected)
        return {"ok": local_ok or bool(result.get("ok")), "check": f"commitment-{check_field}"}

    return verify


def crew_write_executors(db_path: str) -> Dict[str, tuple[Callable, Optional[Callable]]]:
    """Register the Crew write executor specs (params-dict adapters)."""
    def _exec(op: str):
        return _crew_write_executor(op)

    no_verify = None
    base: Dict[str, tuple[Callable, Optional[Callable]]] = {
        "update_crew_bill": (_exec("update_bill"), _verify_stored(db_path, "name")),
        "update_crew_bill_reserve_settings": (
            _exec("update_bill_reserve_settings"),
            _verify_stored(db_path, "name"),
        ),
        "create_crew_autopilot_rule": (_exec("create_autopilot_rule"), no_verify),
        "create_crew_bill": (_exec("create_bill"), no_verify),
        "archive_crew_bill": (_exec("archive_bill"), no_verify),
        "create_crew_pocket": (_exec("create_subaccount"), no_verify),
        "delete_crew_pocket": (_exec("delete_subaccount"), no_verify),
        "crew_initiate_transfer": (_exec("initiate_transfer"), no_verify),
        "create_crew_paycheck_funding_plan": (
            _exec("create_paycheck_funding_plan"),
            no_verify,
        ),
        "update_crew_paycheck_funding_plan": (
            _exec("update_paycheck_funding_plan"),
            no_verify,
        ),
        "delete_crew_paycheck_funding_plan": (
            _exec("delete_paycheck_funding_plan"),
            no_verify,
        ),
        "top_up_crew_reserve": (_exec("top_up_reserve"), no_verify),
        "delete_crew_autopilot_rule": (_exec("delete_rule"), no_verify),
        "create_crew_pocket_reassignment_rule": (
            _exec("create_pocket_reassignment_rule"),
            no_verify,
        ),
        "delete_crew_pocket_reassignment_rule": (
            _exec("delete_pocket_reassignment_rule"),
            no_verify,
        ),
        "set_crew_spend_pocket": (
            _exec("set_spend_pocket"),
            no_verify,
        ),
        "create_crew_virtual_card": (
            _exec("create_virtual_card"),
            no_verify,
        ),
    }
    return base


def _bill_record(params: Dict[str, Any], db_path: str):
    """The local record behind a Crew bill proposal, or None when unknown.

    The Plan UI proposes by Crew bill id; other callers may pass the local
    commitment id. Either way this is the same record the reviewer's screen was
    rendered from, which is what the precondition compares against.
    """
    repo = CommitmentRepository(db_path)
    commitment_id = params.get("commitment_id")
    if commitment_id is not None:
        try:
            record = repo.get(int(commitment_id))
        except (TypeError, ValueError):
            return None
        if record is not None:
            return record
    bill_id = params.get("billId")
    if bill_id:
        return repo.get_commitment_by_legacy("crew", str(bill_id))
    return None


def _reviewed_values(record, params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        local_field: getattr(record, local_field, None)
        for wire_field, local_field in _BILL_REVIEWED_FIELDS.items()
        if wire_field in params
    }


def capture_base_state(
    action_type: str, params: Dict[str, Any], db_path: str
) -> Optional[Dict[str, Any]]:
    """Record the state a reviewer is about to approve, when the type declares one.

    Returns None for every type that has no declared base state, so the absence
    is visible rather than silently fabricated. An approval recorded without one
    is refused at execution, never executed on an assumption.
    """
    if action_type != "update_crew_bill":
        return None
    record = _bill_record(params, db_path)
    if record is None:
        # No local record to compare against: record nothing, so execution
        # refuses rather than mutating a record whose reviewed state we never saw.
        return None
    return {
        "source": "commitment",
        "commitment_id": record.id,
        "crew_bill_id": str(params.get("billId") or record.legacy_id or ""),
        "observed_at": record.updated_at,
        "values": _reviewed_values(record, params),
    }


def _bill_precondition(db_path: str):
    """Refuse a bill write whose reviewed state no longer holds locally.

    This compares our own record against what was approved. It is NOT a provider
    readback: a change made in Crew that we have not re-synced is invisible here,
    which is why the refusal payload records provider_truth=False.
    """

    def precondition(params: Dict[str, Any], base_state: Any) -> Dict[str, Any]:
        reviewed = (base_state or {}).get("values") or {}
        current_record = _bill_record(params, db_path)
        if current_record is None:
            return {
                "ok": False,
                "code": "unverifiable",
                "reason": "the local record for this bill could not be read",
                "reviewed": reviewed,
                "current": None,
                "check": "commitment-base-state",
            }
        current = {
            field: getattr(current_record, field, None)
            for field in reviewed
        }
        if current != reviewed:
            return {
                "ok": False,
                "code": "conflict",
                "reason": "the record changed after this action was approved",
                "reviewed": reviewed,
                "current": current,
                "check": "commitment-base-state",
            }
        return {"ok": True, "check": "commitment-base-state", "reviewed": reviewed}

    return precondition


def crew_write_preconditions(db_path: str) -> Dict[str, Callable]:
    """Preconditions, keyed by action type. Only types listed here are guarded."""
    return {"update_crew_bill": _bill_precondition(db_path)}
