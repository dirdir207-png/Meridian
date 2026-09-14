"""Tests for Crew write-back executors plugged into the action pipeline."""

import pytest

from crew.actions import ActionStore
from crew.executors import ExecutorSpec
from meridian.crew_write_actions import crew_write_executors


def test_executors_register_all_verified_write_types(tmp_path):
    db = str(tmp_path / "m.db")
    specs = crew_write_executors(db)
    assert set(specs) == {
        "update_crew_bill",
        "update_crew_bill_reserve_settings",
        "create_crew_autopilot_rule",
        "create_crew_bill",
        "archive_crew_bill",
        "create_crew_pocket",
        "delete_crew_pocket",
        "crew_initiate_transfer",
        "create_crew_paycheck_funding_plan",
        "update_crew_paycheck_funding_plan",
        "delete_crew_paycheck_funding_plan",
        "top_up_crew_reserve",
        "delete_crew_autopilot_rule",
        "create_crew_pocket_reassignment_rule",
        "delete_crew_pocket_reassignment_rule",
        "set_crew_spend_pocket",
        "create_crew_virtual_card",
    }
    for spec in specs.values():
        assert callable(spec[0])


def test_propose_approve_execute_roundtrip(tmp_path, monkeypatch):
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=set(crew_write_executors(db)))
    executors = {
        key: ExecutorSpec(execute=fn, verifier=vf)
        for key, (fn, vf) in crew_write_executors(db).items()
    }

    # Registry the real execute_crew_write is mocked so the subprocess is safe.
    from meridian import crew_write, crew_write_actions

    def fake(operation, input_payload, **kwargs):
        return {"ok": True, "result": {"id": "bill-1"}, "retry_allowed": False}

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", fake)
    monkeypatch.setattr(crew_write, "execute_crew_write", fake)

    # The readback verifier must not shell out to the real crew-readonly in
    # this roundtrip test; simulate an unavailable readback so the action ends
    # EXECUTED (the dedicated A06 tests cover matched/mismatch readbacks).
    import meridian.live as live

    monkeypatch.setattr(
        live,
        "capture_crew_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("readback unavailable in test")),
    )

    from crew.executors import execute_approved_action

    request = store.propose(
        "update_crew_bill",
        {
            "billId": "QmlsbDox",
            "name": "Verizon",
            "amount": 9500,
            "frequency": "MONTHLY",
            "frequencyInterval": 1,
            "anchorDate": "2026-01-22",
        },
        "Rename/live Crew bill",
        requested_by="owner",
    )
    store.approve(request["id"], decided_by="owner")
    result = execute_approved_action(store, request["id"], executors)
    assert result["state"] in ("executed", "verified")
    assert result.get("result", {}).get("success") is True
    assert result.get("result", {}).get("crew", {}).get("ok") is True


def test_unknown_write_type_rejected_by_store(tmp_path):
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=set(crew_write_executors(db)))
    try:
        store.propose("delete_everything", {}, "nope", requested_by="owner")
    except ValueError:
        return
    raise AssertionError("unknown action type must be rejected")


@pytest.mark.parametrize(
    ("connector_outcome", "expected"),
    [
        (
            {
                "ok": False,
                "error": "uncertain",
                "message": "Outcome unknown; verify in Crew.",
                "retry_allowed": False,
                "verify_state": True,
            },
            {
                "success": False,
                "error": "Outcome unknown; verify in Crew.",
                "error_code": "uncertain",
                "retry_allowed": False,
                "verify_state": True,
            },
        ),
        (
            {
                "ok": False,
                "error": "blocked",
                "message": "Input did not pass the connector gate.",
                "retry_allowed": False,
            },
            {
                "success": False,
                "error": "Input did not pass the connector gate.",
                "error_code": "blocked",
                "retry_allowed": False,
                "verify_state": False,
            },
        ),
        (
            {
                "ok": False,
                "error": "rejected",
                "message": "Crew rejected the operation.",
                "retry_allowed": False,
            },
            {
                "success": False,
                "error": "Crew rejected the operation.",
                "error_code": "rejected",
                "retry_allowed": False,
                "verify_state": False,
            },
        ),
    ],
)
def test_executor_preserves_structured_connector_failures(
    tmp_path, monkeypatch, connector_outcome, expected
):
    from meridian import crew_write_actions

    monkeypatch.setattr(
        crew_write_actions,
        "execute_crew_write",
        lambda operation, input_payload: connector_outcome,
    )
    executor = crew_write_actions.crew_write_executors(str(tmp_path / "m.db"))[
        "update_crew_bill"
    ][0]

    assert executor({"billId": "Bill:1"}) == expected


def test_uncertain_connector_outcome_is_persisted_without_retry(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions

    calls = []

    def uncertain(operation, input_payload):
        calls.append((operation, input_payload))
        return {
            "ok": False,
            "error": "uncertain",
            "message": "Outcome unknown; verify in Crew.",
            "retry_allowed": False,
            "verify_state": True,
        }

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", uncertain)
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=("update_crew_bill",))
    execute, verifier = crew_write_actions.crew_write_executors(db)["update_crew_bill"]
    request = store.propose(
        "update_crew_bill",
        {"billId": "Bill:1", "name": "Rent"},
        "Update the bill",
        requested_by="owner",
    )
    store.approve(request["id"], decided_by="owner")

    outcome = execute_approved_action(
        store,
        request["id"],
        {"update_crew_bill": ExecutorSpec(execute=execute, verifier=verifier)},
    )

    assert calls == [("update_bill", {"billId": "Bill:1", "name": "Rent"})]
    assert outcome["state"] == "failed"
    assert outcome["result"] == {
        "success": False,
        "error": "Outcome unknown; verify in Crew.",
        "error_code": "uncertain",
        "retry_allowed": False,
        "verify_state": True,
    }


def test_verifier_less_crew_write_stays_executed_and_is_never_claimed_verified(
    tmp_path, monkeypatch
):
    """Real verifier-less Crew ops (transfer, reserve top-up, pocket create).

    Fifteen of the registered action types register no verifier. A provider
    acceptance must not be reported as a verified outcome.
    """
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions

    calls = []

    def accepted(operation, input_payload):
        calls.append(operation)
        return {"ok": True, "result": {"id": "xfer-1"}, "retry_allowed": False}

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", accepted)
    db = str(tmp_path / "m.db")
    specs = crew_write_actions.crew_write_executors(db)
    for action_type in ("crew_initiate_transfer", "top_up_crew_reserve"):
        assert specs[action_type][1] is None, f"{action_type} unexpectedly has a verifier"

        store = ActionStore(db, allowed_types=(action_type,))
        execute, verifier = specs[action_type]
        request = store.propose(action_type, {"amount": 100}, "Move money", requested_by="owner")
        store.approve(request["id"], decided_by="owner")

        outcome = execute_approved_action(
            store, request["id"], {action_type: ExecutorSpec(execute=execute, verifier=verifier)}
        )

        assert outcome["state"] == "executed", action_type
        assert outcome["verification"] is None, action_type
        assert outcome["result"]["verification"]["check"] == "no-verifier-registered"

    assert calls == ["initiate_transfer", "top_up_reserve"]


def test_autopilot_rule_executor_enriches_formula_before_write(tmp_path, monkeypatch):
    """The create-autopilot executor must inject real accountId into the action so
    Crew never rejects a null accountId."""
    from meridian import crew_write_actions

    seen = {}
    def fake_execute(operation, input_payload):
        seen["operation"] = operation
        seen["payload"] = input_payload
        return {"ok": True, "result": {}}

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", fake_execute)
    specs = crew_write_actions.crew_write_executors(str(tmp_path / "m.db"))
    executor = specs["create_crew_autopilot_rule"][0]
    executor({
        "name": "Zz Diag",
        "account_id": "Acct:checking",
        "subaccount_id": "Sub:fts",
        "formula": {
            "name": "Zz Diag",
            "triggers": ["ACCOUNT_DEPOSIT_RECEIVED"],
            "actions": [{"roundUpTransfer": {"roundToNearest": 100}}],
        },
    })
    assert seen["operation"] == "create_autopilot_rule"
    formula = seen["payload"]["formula"]
    action = formula["actions"][0]["roundUpTransfer"]
    assert action["accountId"] == "Acct:checking"
    assert action["accountType"] == "ACCOUNT"
    assert action["roundToNearest"] == 100


def test_set_spend_pocket_executor_reaches_write(tmp_path, monkeypatch):
    """set_crew_spend_pocket executor passes user/subaccount ids to the CLI."""
    from meridian import crew_write_actions

    seen = {}
    def fake_execute(operation, input_payload):
        seen["operation"] = operation
        seen["payload"] = input_payload
        return {"ok": True, "result": {}}

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", fake_execute)
    specs = crew_write_actions.crew_write_executors(str(tmp_path / "m.db"))
    executor = specs["set_crew_spend_pocket"][0]
    executor({"user_id": "User:1", "subaccount_id": "Sub:2"})
    assert seen["operation"] == "set_spend_pocket"
    assert seen["payload"]["user_id"] == "User:1"
    assert seen["payload"]["subaccount_id"] == "Sub:2"


def test_create_virtual_card_executor_reaches_write(tmp_path, monkeypatch):
    """create_crew_virtual_card executor passes the card input to the CLI."""
    from meridian import crew_write_actions
    seen = {}
    def fake_execute(operation, input_payload):
        seen["operation"] = operation
        seen["payload"] = input_payload
        return {"ok": True, "result": {}}
    monkeypatch.setattr(crew_write_actions, "execute_crew_write", fake_execute)
    specs = crew_write_actions.crew_write_executors(str(tmp_path / "m.db"))
    executor = specs["create_crew_virtual_card"][0]
    executor({"user_id": "User:1", "name": "Zz Card", "subaccount_id": "Sub:2", "card_color": "TEAL"})
    assert seen["operation"] == "create_virtual_card"
    assert seen["payload"]["user_id"] == "User:1"
    assert seen["payload"]["name"] == "Zz Card"


# --- A12: an approved Crew bill write must still match the reviewed record ---


def _migrated_db(tmp_path):
    from meridian.db import run_migrations

    db = str(tmp_path / "m.db")
    run_migrations(db)
    return db


def _seed_bill(db, bill_id="QmlsbDox", name="Verizon", amount=95.0):
    from meridian.commitments import CommitmentRepository, CommitmentType

    repo = CommitmentRepository(db)
    repo.create(
        type=CommitmentType.BILL,
        name=name,
        amount=amount,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id=bill_id,
    )
    return repo.get_commitment_by_legacy("crew", bill_id)


def test_capture_base_state_records_only_the_reviewed_fields(tmp_path):
    from meridian.crew_write_actions import capture_base_state

    db = _migrated_db(tmp_path)
    _seed_bill(db, bill_id="QmlsbDox", name="Verizon", amount=95.0)

    state = capture_base_state(
        "update_crew_bill",
        {"billId": "QmlsbDox", "name": "Verizon", "amount": 9500},
        db,
    )

    assert state["source"] == "commitment"
    assert state["crew_bill_id"] == "QmlsbDox"
    assert state["observed_at"]
    # The wire amount is cents; the reviewed record is local dollars, and the
    # precondition compares local against local — never params against local.
    assert state["values"] == {"name": "Verizon", "amount": 95.0}


def test_capture_base_state_is_absent_for_unknown_records_and_types(tmp_path):
    from meridian.crew_write_actions import capture_base_state

    db = _migrated_db(tmp_path)

    assert capture_base_state("update_crew_bill", {"billId": "Missing"}, db) is None
    _seed_bill(db, bill_id="QmlsbDox", name="Verizon", amount=95.0)
    assert capture_base_state("create_crew_pocket", {"name": "x"}, db) is None


def _prepare_approved_bill_write(tmp_path, monkeypatch):
    from crew.actions import ActionStore
    from meridian import crew_write_actions

    db = _migrated_db(tmp_path)
    bill = _seed_bill(db, bill_id="QmlsbDox", name="Verizon", amount=95.0)

    calls = []
    monkeypatch.setattr(
        crew_write_actions,
        "execute_crew_write",
        lambda op, payload: calls.append((op, payload)) or {"ok": True},
    )

    base_state = crew_write_actions.capture_base_state(
        "update_crew_bill",
        {"billId": "QmlsbDox", "name": "Verizon", "amount": 9500},
        db,
    )
    assert base_state is not None

    store = ActionStore(db, allowed_types=("update_crew_bill",))
    request = store.propose(
        "update_crew_bill",
        {"billId": "QmlsbDox", "name": "Verizon", "amount": 9500},
        "Update the bill",
        requested_by="owner",
        base_state=base_state,
    )
    store.approve(request["id"], decided_by="owner")
    return db, bill, calls, store, request["id"]


def _bill_executors(db):
    from crew.executors import ExecutorSpec
    from meridian.crew_write_actions import (
        crew_write_executors,
        crew_write_preconditions,
    )

    execute = crew_write_executors(db)["update_crew_bill"][0]
    return {
        "update_crew_bill": ExecutorSpec(
            execute=execute,
            precondition=crew_write_preconditions(db)["update_crew_bill"],
        )
    }


def test_a_changed_bill_is_refused_and_never_reaches_crew(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian.commitments import CommitmentRepository

    db, bill, calls, store, action_id = _prepare_approved_bill_write(tmp_path, monkeypatch)

    # Another surface edits the bill between approval and execution.
    CommitmentRepository(db).update(bill.id, name="Verizon (changed)")

    outcome = execute_approved_action(store, action_id, _bill_executors(db))

    assert calls == [], "the stale write must never reach Crew"
    assert outcome["state"] == "failed"
    assert outcome["result"]["error_code"] == "precondition_conflict"
    assert outcome["result"]["sent_to_provider"] is False
    assert outcome["result"]["retry_allowed"] is False
    assert outcome["result"]["precondition"]["reviewed"] == {
        "name": "Verizon",
        "amount": 95.0,
    }
    assert outcome["result"]["precondition"]["current"] == {
        "name": "Verizon (changed)",
        "amount": 95.0,
    }


def test_an_unchanged_bill_executes_normally(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action

    db, bill, calls, store, action_id = _prepare_approved_bill_write(tmp_path, monkeypatch)

    outcome = execute_approved_action(store, action_id, _bill_executors(db))

    assert calls == [
        ("update_bill", {"billId": "QmlsbDox", "name": "Verizon", "amount": 9500})
    ]
    # This spec has no verifier, so a successful write stays EXECUTED, never
    # VERIFIED — the check here is that the precondition allowed it to run.
    assert outcome["state"] == "executed"



# --- A06: an update_crew_bill is verified by a provider readback, not local state ---


def _readback_dashboard(bill_id, name, amount_cents):
    return {
        "mode": "read-only",
        "source": "crew",
        "complete": True,
        "captured_at": "2026-09-11T21:00:00Z",
        "data": {
            "expenses": {
                "data": {
                    "currentUser": {
                        "accounts": [
                            {
                                "billReserve": {
                                    "bills": [
                                        {
                                            "id": bill_id,
                                            "name": name,
                                            "amount": amount_cents,
                                            "anchorDate": "2026-01-22",
                                            "frequency": "MONTHLY",
                                            "reservedAmount": amount_cents,
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        },
    }


def _bill_write_executor(db):
    from crew.executors import ExecutorSpec
    from meridian.crew_write_actions import crew_write_executors

    execute, verify = crew_write_executors(db)["update_crew_bill"]
    return execute, {"update_crew_bill": ExecutorSpec(execute=execute, verifier=verify)}


def _seed_approved_bill(db, bill_id="Bill:1", name="Verizon", amount=9500):
    from crew.actions import ActionStore

    store = ActionStore(db, allowed_types=("update_crew_bill",))
    request = store.propose(
        "update_crew_bill",
        {"billId": bill_id, "name": name, "amount": amount},
        "Update the bill",
        requested_by="owner",
    )
    store.approve(request["id"], decided_by="owner")
    return store, request["id"]


def test_crew_bill_readback_confirms_the_provider_state(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", lambda op, p: {"ok": True})
    monkeypatch.setattr(live, "capture_crew_snapshot", lambda: _readback_dashboard("Bill:1", "Verizon", 9500))

    db = str(tmp_path / "m.db")
    store, action_id = _seed_approved_bill(db)
    execute, executors = _bill_write_executor(db)

    outcome = execute_approved_action(store, action_id, executors)

    assert outcome["state"] == "verified"
    assert outcome["verification"]["check"] == "crew-bill-readback"
    assert outcome["verification"]["provider_truth"] is True


def test_crew_bill_readback_fails_a_write_that_does_not_land(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", lambda op, p: {"ok": True})
    # Crew now reports a different name and amount than what was requested.
    monkeypatch.setattr(live, "capture_crew_snapshot", lambda: _readback_dashboard("Bill:1", "T-Mobile", 17500))

    db = str(tmp_path / "m.db")
    store, action_id = _seed_approved_bill(db)
    execute, executors = _bill_write_executor(db)

    outcome = execute_approved_action(store, action_id, executors)

    assert outcome["state"] == "failed"
    assert outcome["result"]["error_code"] == "verification_failed"
    assert outcome["result"]["verification"]["provider_truth"] is True
    assert outcome["result"]["verification"]["requested"]["name"] == "Verizon"
    assert outcome["result"]["verification"]["observed"]["name"] == "T-Mobile"


def test_reserve_settings_readback_confirms_fresh_provider_state(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    calls = []
    monkeypatch.setattr(crew_write_actions, "execute_crew_write",
                        lambda op, payload: calls.append((op, payload)) or {"ok": True})
    monkeypatch.setattr(live, "capture_crew_snapshot",
                        lambda: _readback_dashboard("Bill:1", "Verizon", 9500))
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=("update_crew_bill_reserve_settings",))
    request = store.propose("update_crew_bill_reserve_settings",
                            {"billReserveId": "Bill:1", "reservedAmount": 9500},
                            "Update reserve", requested_by="owner")
    store.approve(request["id"], decided_by="owner")
    outcome = execute_approved_action(store, request["id"], {
        "update_crew_bill_reserve_settings": ExecutorSpec(
            *crew_write_executors(db)["update_crew_bill_reserve_settings"])
    })
    assert outcome["state"] == "verified"
    assert outcome["verification"]["provider_truth"] is True
    assert calls == [("update_bill_reserve_settings", {"billReserveId": "Bill:1", "reservedAmount": 9500})]


@pytest.mark.parametrize("snapshot", [
    {"mode": "read-only", "source": "crew", "mutations_enabled": False, "complete": False, "data": {}},
    {"mode": "read-only", "source": "crew", "mutations_enabled": False, "complete": True, "data": {}},
    {"mode": "read-only", "source": "crew", "mutations_enabled": False, "complete": True, "freshness": "stale", "data": {}},
    {"mode": "read-only", "source": "crew", "mutations_enabled": False, "complete": True, "data": {"expenses": "bad"}},
])
def test_reserve_settings_inconclusive_readback_is_unresolved_and_not_retried(
    tmp_path, monkeypatch, snapshot
):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    calls = []
    monkeypatch.setattr(crew_write_actions, "execute_crew_write",
                        lambda op, payload: calls.append(op) or {"ok": True})
    monkeypatch.setattr(live, "capture_crew_snapshot", lambda: snapshot)
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=("update_crew_bill_reserve_settings",))
    request = store.propose("update_crew_bill_reserve_settings",
                            {"billReserveId": "Bill:1", "reservedAmount": 9500},
                            "Update reserve", requested_by="owner")
    store.approve(request["id"], decided_by="owner")
    spec = {"update_crew_bill_reserve_settings": ExecutorSpec(
        *crew_write_executors(db)["update_crew_bill_reserve_settings"])}
    outcome = execute_approved_action(store, request["id"], spec)
    assert outcome["state"] == "executed"
    assert outcome["result"]["verification"]["ok"] is None
    assert outcome["result"]["verification"]["provider_truth"] is False
    with pytest.raises(Exception):
        execute_approved_action(store, request["id"], spec)
    assert calls == ["update_bill_reserve_settings"]


def test_reserve_settings_verifier_exception_is_unresolved_after_restart(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    calls = []
    monkeypatch.setattr(crew_write_actions, "execute_crew_write",
                        lambda op, payload: calls.append(op) or {"ok": True})
    monkeypatch.setattr(live, "capture_crew_snapshot", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=("update_crew_bill_reserve_settings",))
    request = store.propose("update_crew_bill_reserve_settings",
                            {"billReserveId": "Bill:1", "reservedAmount": 9500},
                            "Update reserve", requested_by="owner")
    store.approve(request["id"], decided_by="owner")
    spec = {"update_crew_bill_reserve_settings": ExecutorSpec(
        *crew_write_executors(db)["update_crew_bill_reserve_settings"])}
    outcome = execute_approved_action(store, request["id"], spec)
    restarted = ActionStore(db, allowed_types=("update_crew_bill_reserve_settings",)).get(request["id"])
    assert outcome["state"] == restarted["state"] == "executed"
    assert restarted["result"]["verification"]["ok"] is None
    assert restarted["result"]["verification"]["retry_allowed"] is False if "retry_allowed" in restarted["result"]["verification"] else True
    assert calls == ["update_bill_reserve_settings"]


def test_reserve_settings_missing_bill_is_unresolved_not_deleted(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    calls = []
    monkeypatch.setattr(crew_write_actions, "execute_crew_write",
                        lambda op, payload: calls.append(op) or {"ok": True})
    monkeypatch.setattr(live, "capture_crew_snapshot", lambda: _readback_dashboard("Other:1", "Other", 100))
    db = str(tmp_path / "m.db")
    store = ActionStore(db, allowed_types=("update_crew_bill_reserve_settings",))
    request = store.propose("update_crew_bill_reserve_settings",
                            {"billReserveId": "Bill:1", "reservedAmount": 9500},
                            "Update reserve", requested_by="owner")
    store.approve(request["id"], decided_by="owner")
    spec = {"update_crew_bill_reserve_settings": ExecutorSpec(
        *crew_write_executors(db)["update_crew_bill_reserve_settings"])}
    outcome = execute_approved_action(store, request["id"], spec)
    assert outcome["state"] == "executed"
    assert outcome["result"]["verification"]["ok"] is None
    assert calls == ["update_bill_reserve_settings"]


def test_crew_bill_readback_that_cannot_be_read_stays_executed(tmp_path, monkeypatch):
    from crew.executors import execute_approved_action
    from meridian import crew_write_actions, live

    monkeypatch.setattr(crew_write_actions, "execute_crew_write", lambda op, p: {"ok": True})

    def unavailable():
        raise RuntimeError("crew-readonly snapshot timed out")

    monkeypatch.setattr(live, "capture_crew_snapshot", unavailable)

    db = str(tmp_path / "m.db")
    store, action_id = _seed_approved_bill(db)
    execute, executors = _bill_write_executor(db)

    outcome = execute_approved_action(store, action_id, executors)

    assert outcome["state"] == "executed"
    assert outcome["result"]["verification"]["ok"] is None
    assert outcome["result"]["verification"]["check"] == "crew-bill-readback"
