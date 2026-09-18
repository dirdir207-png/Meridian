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


def _verify_crew_bill_reserve_readback():
    """Verify reserve-setting writes against a fresh, complete Crew snapshot.

    Local commitments are not provider truth. Any unreadable, incomplete,
    stale, malformed, or non-matching readback remains unresolved after the
    provider accepted the write; it must never authorize a retry.
    """

    def verify(params: Dict[str, Any], _result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        bill_id = str(params.get("billReserveId") or params.get("billId") or "")
        requested = {key: params[key] for key in ("name", "amount", "reservedAmount") if key in params}
        try:
            dashboard = capture_crew_snapshot()
            if not isinstance(dashboard, dict) or dashboard.get("freshness") in {"stale", "expired"}:
                raise ValueError("provider snapshot is stale or malformed")
            snapshot = CrewWorkSnapshotAdapter(dashboard).fetch_snapshot()
        except Exception as exc:  # noqa: BLE001 - accepted writes stay unresolved
            return {"ok": None, "check": "crew-bill-reserve-readback", "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete or not bill_id:
            return {"ok": None, "check": "crew-bill-reserve-readback", "provider_truth": False,
                    "reason": "provider readback is incomplete or has no bill identity",
                    "requested": requested}
        candidate = next((c for c in snapshot.commitment_candidates if c.external_id == bill_id), None)
        if candidate is None:
            return {"ok": None, "check": "crew-bill-reserve-readback", "provider_truth": False,
                    "reason": "the requested bill was not present in the readback",
                    "requested": requested}
        observed = {"name": candidate.name, "amount": round(candidate.amount * 100),
                    "reservedAmount": (round(candidate.funded_amount * 100)
                                       if candidate.funded_amount is not None else None)}
        mismatches = [key for key, expected in requested.items()
                      if expected is not None and observed.get(key) != expected]
        if mismatches:
            return {"ok": None, "check": "crew-bill-reserve-readback", "provider_truth": False,
                    "reason": f"readback fields differ: {', '.join(mismatches)}",
                    "requested": requested, "observed": observed}
        if not requested:
            return {"ok": None, "check": "crew-bill-reserve-readback", "provider_truth": False,
                    "reason": "readback contained no requested fields to verify", "observed": observed}
        return {"ok": True, "check": "crew-bill-reserve-readback", "provider_truth": True,
                "requested": requested, "observed": observed}

    return verify


def _verify_crew_bill_readback():
    """Verify an update_crew_bill against a fresh provider snapshot.

    Replaces the local-commitment re-read (A06): Crew's own snapshot is the
    authoritative confirmation. Outcomes: ok True (matched), ok False (mismatch
    or the bill is gone — provider_truth True), or ok None (the snapshot could
    not be read — neither verified nor failed; the action stays EXECUTED).
    """

    def verify(params: Dict[str, Any], _result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        bill_id = str(params.get("billId") or "")
        requested = {
            "name": params.get("name"),
            "amount": (
                round(float(params["amount"])) if params.get("amount") is not None else None
            ),
        }

        try:
            dashboard = capture_crew_snapshot()
            snapshot = CrewWorkSnapshotAdapter(dashboard).fetch_snapshot()
        except Exception as exc:  # noqa: BLE001 - an unreadable snapshot cannot confirm
            return {
                "ok": None,
                "check": "crew-bill-readback",
                "provider_truth": False,
                "reason": f"readback unavailable: {exc}",
                "requested": requested,
            }

        candidate = next(
            (c for c in snapshot.commitment_candidates if c.external_id == bill_id),
            None,
        )
        if candidate is None:
            return {
                "ok": None,
                "check": "crew-bill-readback",
                "provider_truth": False,
                "reason": "the requested bill was not present in the readback; deletion is unconfirmed",
                "requested": requested,
                "observed": None,
            }

        observed = {
            "name": candidate.name,
            "amount": round(candidate.amount * 100),
        }
        mismatches = []
        if requested["name"] is not None and candidate.name != requested["name"]:
            mismatches.append("name")
        if (
            requested["amount"] is not None
            and round(candidate.amount * 100) != requested["amount"]
        ):
            mismatches.append("amount")

        if mismatches:
            return {
                "ok": False,
                "check": "crew-bill-readback",
                "provider_truth": True,
                "reason": f"bill fields differ from the write: {', '.join(mismatches)}",
                "requested": requested,
                "observed": observed,
            }
        return {
            "ok": True,
            "check": "crew-bill-readback",
            "provider_truth": True,
            "matched": observed,
        }

    return verify


def _verify_archived_crew_bill():
    """Confirm an archive only from a fresh, complete provider snapshot."""
    def verify(params: Dict[str, Any], _result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter
        bill_id = str(params.get("billId") or params.get("billReserveId") or "")
        try:
            snapshot = CrewWorkSnapshotAdapter(capture_crew_snapshot()).fetch_snapshot()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": "crew-bill-archive-readback", "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": {"billId": bill_id}}
        if not snapshot.is_complete or not bill_id:
            return {"ok": None, "check": "crew-bill-archive-readback", "provider_truth": False,
                    "reason": "provider readback is incomplete or has no bill identity",
                    "requested": {"billId": bill_id}}
        present = any(c.external_id == bill_id for c in snapshot.commitment_candidates)
        return {"ok": not present, "check": "crew-bill-archive-readback",
                "provider_truth": True, "reason": "bill absent from complete provider readback" if not present else "bill remains present after archive",
                "requested": {"billId": bill_id}, "observed": {"present": present}}

    return verify


def _verify_created_crew_bill():
    """Confirm a created bill exists in a fresh, complete provider snapshot."""
    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        bill_id = str(provider_result.get("id") or "")
        requested = {key: params.get(key) for key in ("name", "amount") if params.get(key) is not None}
        try:
            snapshot = CrewWorkSnapshotAdapter(capture_crew_snapshot()).fetch_snapshot()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": "crew-bill-create-readback", "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}
        if not snapshot.is_complete or not bill_id:
            return {"ok": None, "check": "crew-bill-create-readback", "provider_truth": False,
                    "reason": "provider readback is incomplete or has no created bill identity",
                    "requested": requested}
        candidate = next((c for c in snapshot.commitment_candidates if c.external_id == bill_id), None)
        if candidate is None:
            return {"ok": None, "check": "crew-bill-create-readback", "provider_truth": False,
                    "reason": "created bill was not present in the readback", "requested": requested,
                    "observed": None}
        observed = {"id": bill_id, "name": candidate.name, "amount": round(candidate.amount * 100)}
        mismatches = [key for key, expected in requested.items() if observed.get(key) != expected]
        if mismatches:
            return {"ok": False, "check": "crew-bill-create-readback", "provider_truth": True,
                    "reason": f"created bill fields differ: {', '.join(mismatches)}",
                    "requested": requested, "observed": observed}
        return {"ok": True, "check": "crew-bill-create-readback", "provider_truth": True,
                "requested": requested, "observed": observed}

    return verify


def _verify_created_crew_pocket():
    """Confirm a created pocket by provider-generated identity and fields."""
    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter
        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        pocket_id = str(provider_result.get("id") or "")
        requested = {key: params.get(key) for key in ("name", "type", "targetAmount") if params.get(key) is not None}
        try:
            snapshot = CrewWorkSnapshotAdapter(capture_crew_snapshot()).fetch_snapshot()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": "crew-pocket-create-readback", "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}
        if not snapshot.is_complete or not pocket_id:
            return {"ok": None, "check": "crew-pocket-create-readback", "provider_truth": False,
                    "reason": "provider readback is incomplete or has no created pocket identity",
                    "requested": requested}
        accounts = {a.external_id: a for a in snapshot.accounts}
        candidate = accounts.get(pocket_id)
        if candidate is None:
            return {"ok": None, "check": "crew-pocket-create-readback", "provider_truth": False,
                    "reason": "created pocket was not present in the readback", "requested": requested}
        observed = {"id": pocket_id, "name": candidate.name, "type": candidate.account_type}
        mismatches = [key for key, expected in requested.items() if observed.get(key) != expected]
        if mismatches:
            return {"ok": False, "check": "crew-pocket-create-readback", "provider_truth": True,
                    "reason": f"created pocket fields differ: {', '.join(mismatches)}",
                    "requested": requested, "observed": observed}
        return {"ok": True, "check": "crew-pocket-create-readback", "provider_truth": True,
                "requested": requested, "observed": observed}
    return verify


def _verify_deleted_crew_pocket():
    """Confirm pocket deletion only from a fresh, complete provider snapshot."""
    def verify(params: Dict[str, Any], _result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter
        pocket_id = str(params.get("id") or params.get("subaccountId") or params.get("subaccount_id") or "")
        try:
            snapshot = CrewWorkSnapshotAdapter(capture_crew_snapshot()).fetch_snapshot()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": "crew-pocket-delete-readback", "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": {"id": pocket_id}}
        if not snapshot.is_complete or not pocket_id:
            return {"ok": None, "check": "crew-pocket-delete-readback", "provider_truth": False,
                    "reason": "provider readback is incomplete or has no pocket identity",
                    "requested": {"id": pocket_id}}
        present = any(account.external_id == pocket_id for account in snapshot.accounts)
        return {"ok": not present, "check": "crew-pocket-delete-readback", "provider_truth": True,
                "reason": "pocket absent from complete provider readback" if not present else "pocket remains present after deletion",
                "requested": {"id": pocket_id}, "observed": {"present": present}}
    return verify


def _verify_created_crew_virtual_card():
    """Confirm a created virtual card from the connector's card facet.

    The facet has always been fetched and Meridian used to discard it, so this
    needs no connector change. A card that is not yet visible is UNRESOLVED, not
    a failure: a single read cannot tell propagation delay from a failed write.
    """
    check = "crew-card-create-readback"

    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        card_id = str(provider_result.get("id") or "")
        requested = {key: params.get(key) for key in ("name", "card_color") if params.get(key) is not None}
        try:
            adapter = CrewWorkSnapshotAdapter(capture_crew_snapshot())
            snapshot = adapter.fetch_snapshot()
            cards = adapter.readback_virtual_cards()
        except Exception as exc:  # noqa: BLE001 - an unreadable snapshot cannot confirm
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete or cards is None or not card_id:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": ("provider readback is incomplete, did not include the card facet, "
                               "or the write returned no card identity"),
                    "requested": requested}

        candidate = next((c for c in cards if str(c.get("id") or "") == card_id), None)
        if candidate is None:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "the created card was not present in the readback",
                    "requested": requested, "observed": None}

        observed = {"id": card_id, "name": candidate.get("name"), "card_color": candidate.get("color")}
        mismatches = []
        if requested.get("name") is not None and observed["name"] != requested["name"]:
            mismatches.append("name")
        if requested.get("card_color") is not None and observed["card_color"] != requested["card_color"]:
            mismatches.append("card_color")
        if mismatches:
            return {"ok": False, "check": check, "provider_truth": True,
                    "reason": f"created card fields differ: {', '.join(mismatches)}",
                    "requested": requested, "observed": observed}
        return {"ok": True, "check": check, "provider_truth": True,
                "requested": requested, "observed": observed}

    return verify


def _verify_autopilot_rule(*, expect_absent: bool):
    """Confirm an autopilot-rule create or delete from the rules facet.

    Absence confirms a deletion but NEVER a creation: a created rule that is not
    yet visible is unresolved, because one read cannot distinguish propagation
    from failure. Presence after a deletion is a provider-confirmed contradiction
    — the safe direction, since it can never falsely claim a rule is gone.
    """
    check = ("crew-autopilot-rule-delete-readback" if expect_absent
             else "crew-autopilot-rule-create-readback")

    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        if expect_absent:
            # A deletion is identified by the approved proposal's own rule id.
            rule_id = str(params.get("rule_id") or params.get("ruleId") or "")
        else:
            rule_id = str(provider_result.get("id") or "")
        requested = {"name": params.get("name")} if params.get("name") is not None else {}
        try:
            adapter = CrewWorkSnapshotAdapter(capture_crew_snapshot())
            snapshot = adapter.fetch_snapshot()
            rules = adapter.readback_autopilot_rules()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete or rules is None or not rule_id:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": ("provider readback is incomplete, did not include the rule facet, "
                               "or the rule identity is unavailable"),
                    "requested": requested}

        present = next((r for r in rules if str(r.get("id") or "") == rule_id), None)
        if expect_absent:
            return {"ok": present is None, "check": check, "provider_truth": True,
                    "reason": ("rule absent from the provider readback" if present is None
                               else "the rule is still present after the delete"),
                    "requested": requested, "observed": {"present": present is not None}}
        if present is None:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "the created rule was not present in the readback",
                    "requested": requested, "observed": None}
        observed = {"id": rule_id, "name": present.get("name")}
        if requested.get("name") is not None and observed["name"] != requested["name"]:
            return {"ok": False, "check": check, "provider_truth": True,
                    "reason": "created rule fields differ: name",
                    "requested": requested, "observed": observed}
        return {"ok": True, "check": check, "provider_truth": True,
                "requested": requested, "observed": observed}

    return verify


def _verify_set_crew_spend_pocket():
    """Confirm the selected spend pocket from the cards facet.

    The selection is live-verified as ``user.userSpendConfig.selectedSpendSubaccount``
    on each card, so this needs no connector change. A written but unconfirmed
    change stays unresolved; the value is only reported as contradicted when the
    provider clearly shows a different selection.
    """
    check = "crew-spend-pocket-readback"

    def verify(params: Dict[str, Any], _result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        target = str(params.get("subaccount_id") or params.get("subaccountId") or "")
        requested = {"subaccount_id": target}
        try:
            adapter = CrewWorkSnapshotAdapter(capture_crew_snapshot())
            snapshot = adapter.fetch_snapshot()
            observed = adapter.readback_selected_spend_pocket()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete or observed is None or not target:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": ("provider readback is incomplete, did not include the cards facet, "
                               "or the requested pocket is unknown"),
                    "requested": requested}
        if not observed:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "no card exposed a selected spend pocket to compare against",
                    "requested": requested}
        if len(observed) > 1:
            # Two different selections cannot both be current; refuse to pick one.
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "the provider reported conflicting selected spend pockets",
                    "requested": requested, "observed": {"selected": list(observed)}}

        selected = observed[0]
        if selected == target:
            return {"ok": True, "check": check, "provider_truth": True,
                    "requested": requested, "observed": {"selected": selected}}
        return {"ok": False, "check": check, "provider_truth": True,
                "reason": "the provider still reports a different selected spend pocket",
                "requested": requested, "observed": {"selected": selected}}

    return verify


def _verify_crew_funding_plan(*, expect_absent: bool, expect_created: bool):
    """Confirm a paycheck funding-plan write from the reserve's fundingPlans.

    Runs on the ``expenses`` facet, whose ``billReserve.fundingPlans`` selection
    was added to the connector for exactly this. A plan is identified by its
    provider id — for update and delete the id comes from the approved proposal,
    and for create from the write result. Absence confirms a deletion but never a
    creation; a plan still present after a delete is a provider contradiction.
    """
    check = (
        "crew-funding-plan-delete-readback" if expect_absent
        else "crew-funding-plan-create-readback" if expect_created
        else "crew-funding-plan-update-readback"
    )

    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        if expect_absent or not expect_created:
            plan_id = str(params.get("fundingPlanId") or params.get("funding_plan_id") or "")
        else:
            plan_id = str(provider_result.get("id") or "")
        requested = {
            key: params[wire]
            for wire, key in (("name", "name"), ("amount", "amount"))
            if params.get(wire) is not None
        }
        try:
            adapter = CrewWorkSnapshotAdapter(capture_crew_snapshot())
            snapshot = adapter.fetch_snapshot()
            plans = adapter.readback_funding_plans()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete or plans is None or not plan_id:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": ("provider readback is incomplete, did not include the funding-plan "
                               "selection, or no plan identity is available"),
                    "requested": requested}

        present = next((p for p in plans if str(p.get("id") or "") == plan_id), None)
        if expect_absent:
            return {"ok": present is None, "check": check, "provider_truth": True,
                    "reason": ("plan absent from the provider readback" if present is None
                               else "the plan is still present after the delete"),
                    "requested": requested, "observed": {"present": present is not None}}
        if present is None:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "the plan was not present in the readback",
                    "requested": requested, "observed": None}

        observed = {"id": plan_id, "name": present.get("name"), "amount": present.get("amount")}
        mismatches = []
        if requested.get("name") is not None and observed["name"] != requested["name"]:
            mismatches.append("name")
        if requested.get("amount") is not None and observed["amount"] != requested["amount"]:
            mismatches.append("amount")
        if mismatches:
            return {"ok": False, "check": check, "provider_truth": True,
                    "reason": f"plan fields differ from the write: {', '.join(mismatches)}",
                    "requested": requested, "observed": observed}
        return {"ok": True, "check": check, "provider_truth": True,
                "requested": requested, "observed": observed}

    return verify


def _verify_crew_reassignment_rule(*, expect_absent: bool):
    """Confirm a pocket reassignment-rule write from ``family.reassignmentRules``.

    Identified by the provider rule id — from the approved proposal for a delete,
    from the write result for a create. An unobserved facet can never confirm a
    deletion, and a still-present rule after a delete is a provider contradiction.
    """
    check = ("crew-reassignment-rule-delete-readback" if expect_absent
             else "crew-reassignment-rule-create-readback")

    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        if expect_absent:
            rule_id = str(params.get("reassignment_rule_id") or params.get("reassignmentRuleId") or "")
        else:
            rule_id = str(provider_result.get("id") or "")
        requested = {"match": params.get("match")} if params.get("match") is not None else {}
        try:
            adapter = CrewWorkSnapshotAdapter(capture_crew_snapshot())
            snapshot = adapter.fetch_snapshot()
            rules = adapter.readback_reassignment_rules()
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete or rules is None or not rule_id:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": ("provider readback is incomplete, did not include the reassignment-rule "
                               "selection, or no rule identity is available"),
                    "requested": requested}

        present = next((r for r in rules if str(r.get("id") or "") == rule_id), None)
        if expect_absent:
            return {"ok": present is None, "check": check, "provider_truth": True,
                    "reason": ("rule absent from the provider readback" if present is None
                               else "the rule is still present after the delete"),
                    "requested": requested, "observed": {"present": present is not None}}
        if present is None:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "the created rule was not present in the readback",
                    "requested": requested, "observed": None}
        observed = {"id": rule_id, "match": present.get("match")}
        if requested.get("match") is not None and observed["match"] != requested["match"]:
            return {"ok": False, "check": check, "provider_truth": True,
                    "reason": "created rule fields differ: match",
                    "requested": requested, "observed": observed}
        return {"ok": True, "check": check, "provider_truth": True,
                "requested": requested, "observed": observed}

    return verify


def _verify_crew_transfer():
    """Confirm crew_initiate_transfer from the provider-returned transfer id.

    Identity, not similarity: the write result carries a transfer id (the
    connector's ``initiate_transfer.graphql`` selects ``result { id }``), and the
    transactions facet already selects ``transfer { id type status }``. An observed
    transaction whose transfer id equals the write's is provider truth for the
    write. Matching on amount and account instead would be weak evidence capable of
    reporting a false confirmed transfer, so it is not done.

    The asymmetry is deliberate and is the whole design:

      * PRESENCE confirms. The provider showed the exact transfer id.
      * ABSENCE is UNRESOLVED, never failed. The connector reads a single page of
        transactions (pageSize 100, null cursor), so an id that is not in this read
        may simply be on a page that was never fetched. A single read cannot
        distinguish "not yet visible / not on this page" from "the write failed",
        so it must not claim failure.
      * An unobserved transactions facet, an incomplete snapshot, an unreadable
        snapshot, or a write result with no transfer id are all UNRESOLVED rather
        than confirmations or failures.
    """
    check = "crew-transfer-readback"

    def verify(params: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        from .live import capture_crew_snapshot
        from .providers.crewwork import CrewWorkSnapshotAdapter

        provider_result = ((result.get("crew") or {}).get("result") or {}) if isinstance(result, dict) else {}
        transfer_id = str(provider_result.get("id") or "")
        requested = {"transfer_id": transfer_id} if transfer_id else {}

        try:
            adapter = CrewWorkSnapshotAdapter(capture_crew_snapshot())
            snapshot = adapter.fetch_snapshot()
        except Exception as exc:  # noqa: BLE001 - an unreadable snapshot cannot confirm
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": f"readback unavailable: {exc}", "requested": requested}

        if not snapshot.is_complete:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "provider readback is incomplete", "requested": requested}

        transfers = adapter.readback_transfers()
        if transfers is None:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "transactions facet was not observed in the readback",
                    "requested": requested}

        if not transfer_id:
            # The write returned no transfer identity, so there is nothing to match
            # on. Stay unresolved rather than falling back to amount or account.
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": "the write result carried no transfer identity to match on",
                    "requested": requested}

        matched = next((t for t in transfers if t.get("transfer_id") == transfer_id), None)
        if matched is None:
            return {"ok": None, "check": check, "provider_truth": False,
                    "reason": ("the write's transfer id was not present in the observed "
                               "transactions; a single page cannot prove it is absent"),
                    "requested": requested,
                    "observed": {"observed_transfer_ids": [t.get("transfer_id") for t in transfers]}}

        return {"ok": True, "check": check, "provider_truth": True,
                "requested": requested,
                "observed": {"id": matched.get("external_id"),
                             "transfer_id": matched.get("transfer_id"),
                             "type": matched.get("transfer_type"),
                             "status": matched.get("status"),
                             "subaccount_id": matched.get("subaccount_id")}}

    return verify


def crew_write_executors(db_path: str) -> Dict[str, tuple[Callable, Optional[Callable]]]:
    """Register the Crew write executor specs (params-dict adapters)."""
    def _exec(op: str):
        return _crew_write_executor(op)

    no_verify = None
    base: Dict[str, tuple[Callable, Optional[Callable]]] = {
        "update_crew_bill": (_exec("update_bill"), _verify_crew_bill_readback()),
        "update_crew_bill_reserve_settings": (
            _exec("update_bill_reserve_settings"),
            _verify_crew_bill_reserve_readback(),
        ),
        "create_crew_autopilot_rule": (_exec("create_autopilot_rule"), _verify_autopilot_rule(expect_absent=False)),
        "create_crew_bill": (_exec("create_bill"), _verify_created_crew_bill()),
        "archive_crew_bill": (_exec("archive_bill"), _verify_archived_crew_bill()),
        "create_crew_pocket": (_exec("create_subaccount"), _verify_created_crew_pocket()),
        "delete_crew_pocket": (_exec("delete_subaccount"), _verify_deleted_crew_pocket()),
        "crew_initiate_transfer": (_exec("initiate_transfer"), _verify_crew_transfer()),
        "create_crew_paycheck_funding_plan": (
            _exec("create_paycheck_funding_plan"),
            _verify_crew_funding_plan(expect_absent=False, expect_created=True),
        ),
        "update_crew_paycheck_funding_plan": (
            _exec("update_paycheck_funding_plan"),
            _verify_crew_funding_plan(expect_absent=False, expect_created=False),
        ),
        "delete_crew_paycheck_funding_plan": (
            _exec("delete_paycheck_funding_plan"),
            _verify_crew_funding_plan(expect_absent=True, expect_created=False),
        ),
        "top_up_crew_reserve": (_exec("top_up_reserve"), no_verify),
        "delete_crew_autopilot_rule": (_exec("delete_rule"), _verify_autopilot_rule(expect_absent=True)),
        "create_crew_pocket_reassignment_rule": (
            _exec("create_pocket_reassignment_rule"),
            _verify_crew_reassignment_rule(expect_absent=False),
        ),
        "delete_crew_pocket_reassignment_rule": (
            _exec("delete_pocket_reassignment_rule"),
            _verify_crew_reassignment_rule(expect_absent=True),
        ),
        "set_crew_spend_pocket": (
            _exec("set_spend_pocket"),
            _verify_set_crew_spend_pocket(),
        ),
        "create_crew_virtual_card": (
            _exec("create_virtual_card"),
            _verify_created_crew_virtual_card(),
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
