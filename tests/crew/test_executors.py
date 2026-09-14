import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from crew.actions import ActionState, ActionStore, IllegalTransitionError
from crew.executors import ExecutorSpec, execute_approved_action, expire_stale_approvals

ALLOWED_TYPES = ("move_money",)


@pytest.fixture
def store(tmp_path):
    return ActionStore(db_path=str(tmp_path / "actions.db"), allowed_types=ALLOWED_TYPES)


def make_executors(fn=None, verifier=None):
    return {
        "move_money": ExecutorSpec(
            execute=fn or (lambda params: {"success": True, "result": {"id": "tx-1"}}),
            verifier=verifier,
        )
    }


def seed_approved_action(store, params=None):
    request = store.propose("move_money", params or {"amount": 100}, "r", "ai-helper")
    store.approve(request["id"], decided_by="owner")
    return request["id"]


def test_approved_action_executes_and_verifies(store):
    verifications = []

    def verifier(params, result):
        verifications.append((params, result))
        return {"ok": True, "checked": "transfer-id-present"}

    action_id = seed_approved_action(store)
    final = execute_approved_action(
        store,
        action_id,
        make_executors(verifier=verifier),
        execution_key="execute-once-key",
    )
    assert final["state"] == ActionState.VERIFIED.value
    assert final["execution_key"] == "execute-once-key"
    assert final["result"]["result"]["id"] == "tx-1"
    assert final["verification"]["ok"] is True
    assert verifications[0][0] == {"amount": 100}


def test_action_without_a_verifier_is_accepted_but_never_called_verified(store):
    """A provider-accepted write with no readback is not a verified outcome.

    Fifteen of the registered action types have no verifier. Marking those
    ``verified`` asserts a readback that never happened.
    """
    action_id = seed_approved_action(store)

    final = execute_approved_action(store, action_id, make_executors())

    assert final["state"] == ActionState.EXECUTED.value
    assert final["state"] != ActionState.VERIFIED.value
    assert final["verification"] is None


def test_action_without_a_verifier_records_why_verification_is_missing(store):
    action_id = seed_approved_action(store)

    final = execute_approved_action(store, action_id, make_executors())

    recorded = final["result"]["verification"]
    assert recorded["ok"] is None
    assert recorded["check"] == "no-verifier-registered"
    assert "accepted" in recorded["reason"]


def test_executed_action_without_a_verifier_cannot_be_re_executed(store):
    """Staying EXECUTED must not open a second claim on the same mutation."""
    calls = []

    def executor(params):
        calls.append(params)
        return {"success": True, "result": {"id": "tx-once"}}

    action_id = seed_approved_action(store)
    execute_approved_action(store, action_id, make_executors(fn=executor))

    with pytest.raises(IllegalTransitionError):
        execute_approved_action(store, action_id, make_executors(fn=executor))

    assert len(calls) == 1


def test_explicit_verifier_still_reaches_verified(store):
    """The honest-outcome change must not weaken operations that do read back."""
    action_id = seed_approved_action(store)

    final = execute_approved_action(
        store,
        action_id,
        make_executors(verifier=lambda params, result: {"ok": True, "check": "readback"}),
    )

    assert final["state"] == ActionState.VERIFIED.value
    assert final["verification"]["check"] == "readback"


def test_error_contract_lands_in_failed_without_verification(store):
    calls = []

    def executor(params):
        return {"error": "Transfer outcome is uncertain.", "error_code": "uncertain_write", "verify_state": True}

    def verifier(params, result):
        calls.append("never")

    action_id = seed_approved_action(store)
    final = execute_approved_action(store, action_id, make_executors(fn=executor, verifier=verifier))
    assert final["state"] == ActionState.FAILED.value
    assert final["result"]["error_code"] == "uncertain_write"
    assert final["result"]["verify_state"] is True
    assert calls == []


def test_verifier_exception_stays_unresolved_without_retry(store):
    calls = {"executor": 0}

    def executor(params):
        calls["executor"] += 1
        return {"success": True, "result": {"id": "tx-1"}}

    def verifier(params, result):
        raise RuntimeError("readback boom")

    action_id = seed_approved_action(store)
    final = execute_approved_action(store, action_id, make_executors(fn=executor, verifier=verifier))
    assert final["state"] == ActionState.EXECUTED.value
    assert final["result"]["verification"]["ok"] is None
    assert final["result"]["verification"]["retry_allowed"] is False
    with pytest.raises(IllegalTransitionError):
        execute_approved_action(store, action_id, make_executors(fn=executor, verifier=verifier))
    assert calls["executor"] == 1


def test_executor_exception_persists_uncertain_outcome_without_retry_or_verification(store):
    calls = {"executor": 0, "verifier": 0}

    def broken(params):
        calls["executor"] += 1
        raise RuntimeError("boom")

    def verifier(params, result):
        calls["verifier"] += 1
        return {"ok": True}

    action_id = seed_approved_action(store)
    final = execute_approved_action(store, action_id, make_executors(fn=broken, verifier=verifier))
    assert final["state"] == ActionState.FAILED.value
    assert final["result"]["error_code"] == "executor_exception"
    assert final["result"]["verify_state"] is True
    assert calls == {"executor": 1, "verifier": 0}


def test_unapproved_action_cannot_execute(store):
    request = store.propose("move_money", {}, "r", "owner")
    with pytest.raises(IllegalTransitionError):
        execute_approved_action(store, request["id"], make_executors())


def test_missing_executor_registration_fails_loudly(store):
    action_id = seed_approved_action(store)
    final = execute_approved_action(store, action_id, {})
    assert final["state"] == ActionState.FAILED.value
    assert final["result"]["error_code"] == "no_executor"


def test_failed_verification_overrides_success(store):
    action_id = seed_approved_action(store)
    final = execute_approved_action(
        store,
        action_id,
        make_executors(verifier=lambda params, result: {"ok": False, "reason": "balance unchanged"}),
    )
    assert final["state"] == ActionState.FAILED.value
    assert final["result"]["verification"]["reason"] == "balance unchanged"


def test_concurrent_execution_claims_action_once(store):
    start = threading.Barrier(2)
    executor_calls = []
    executor_calls_lock = threading.Lock()
    concurrent_executor_calls = threading.Barrier(2)

    def executor(params):
        with executor_calls_lock:
            executor_calls.append(params)
        try:
            concurrent_executor_calls.wait(timeout=0.5)
        except threading.BrokenBarrierError:
            pass
        return {"success": True, "result": {"id": "tx-concurrent"}}

    action_id = seed_approved_action(store)

    def execute():
        start.wait()
        try:
            return execute_approved_action(store, action_id, make_executors(fn=executor))
        except IllegalTransitionError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: execute(), range(2)))

    assert len(executor_calls) == 1
    conflicts = [result for result in results if isinstance(result, IllegalTransitionError)]
    terminal_results = [result for result in results if isinstance(result, dict)]
    assert len(conflicts) == 1
    assert str(conflicts[0]) == "Action is not available for execution"
    assert len(terminal_results) == 1
    assert terminal_results[0]["state"] == ActionState.EXECUTED.value


def test_stale_approvals_expire_recent_ones_survive(store, monkeypatch):
    from datetime import datetime, timedelta

    from crew import actions as actions_module

    clock = {"now": datetime(2026, 8, 25, 12, 0, 0)}
    monkeypatch.setattr(actions_module, "_now", lambda: clock["now"])

    stale_id = seed_approved_action(store)

    clock["now"] = clock["now"] + timedelta(hours=2)
    fresh_id = seed_approved_action(store)

    expired_ids = expire_stale_approvals(
        store,
        ttl_seconds=3600,
        now=clock["now"],
    )
    assert stale_id in expired_ids
    assert fresh_id not in expired_ids
    assert store.get(stale_id)["state"] == ActionState.EXPIRED.value
    assert store.get(fresh_id)["state"] == ActionState.APPROVED.value

    with pytest.raises(IllegalTransitionError):
        execute_approved_action(store, stale_id, make_executors())


def test_expiry_sweep_handles_aware_approval_timestamps(store):
    from datetime import datetime, timedelta, timezone

    action_id = seed_approved_action(store)
    decided_at = (datetime.now() - timedelta(hours=2)).replace(tzinfo=timezone.utc).isoformat()
    with store._connect() as connection:
        connection.execute(
            "UPDATE action_requests SET decided_at = ? WHERE id = ?",
            (decided_at, action_id),
        )
        connection.commit()

    expired_ids = expire_stale_approvals(store, ttl_seconds=3600, now=datetime.now())

    assert expired_ids == [action_id]
    assert store.get(action_id)["state"] == ActionState.EXPIRED.value


def test_expiry_sweep_tolerates_claim_race_and_continues(tmp_path):
    from datetime import datetime, timedelta

    class ClaimingActionStore(ActionStore):
        claim_during_sweep = None

        def list_by_state(self, state):
            requests = super().list_by_state(state)
            if state == ActionState.APPROVED and self.claim_during_sweep:
                claimed_id = self.claim_during_sweep
                self.claim_during_sweep = None
                self.claim_for_execution(claimed_id, "sweep-race-key")
                requests.sort(key=lambda request: request["id"] != claimed_id)
            return requests

    racing_store = ClaimingActionStore(
        db_path=str(tmp_path / "actions.db"),
        allowed_types=ALLOWED_TYPES,
    )
    claimed_id = seed_approved_action(racing_store)
    expired_id = seed_approved_action(racing_store)
    racing_store.claim_during_sweep = claimed_id

    expired_ids = expire_stale_approvals(
        racing_store,
        ttl_seconds=3600,
        now=datetime.now() + timedelta(hours=2),
    )

    assert expired_ids == [expired_id]
    assert racing_store.get(claimed_id)["state"] == ActionState.EXECUTING.value
    assert racing_store.get(expired_id)["state"] == ActionState.EXPIRED.value


# --- A12: an approved action must still match the state that was reviewed ---


def make_preconditioned_executor(executed, precondition):
    def execute(params):
        executed.append(params)
        return {"success": True, "result": {"id": "tx-1"}}

    return {"move_money": ExecutorSpec(execute=execute, precondition=precondition)}


def seed_approved_action_with_base_state(store, base_state):
    request = store.propose(
        "move_money", {"amount": 100}, "r", "ai-helper", base_state=base_state
    )
    store.approve(request["id"], decided_by="owner")
    return request["id"]


def test_a_changed_base_state_refuses_and_never_calls_the_executor(store):
    executed = []
    action_id = seed_approved_action_with_base_state(store, {"amount": 100})

    final = execute_approved_action(
        store,
        action_id,
        make_preconditioned_executor(
            executed,
            lambda params, base_state: {
                "ok": False,
                "code": "conflict",
                "reason": "amount changed from 100 to 175",
                "reviewed": base_state,
                "current": {"amount": 175},
            },
        ),
    )

    assert executed == [], "a stale approval must never reach the provider"
    assert final["state"] == ActionState.FAILED.value
    assert final["result"]["error_code"] == "precondition_conflict"
    assert final["result"]["sent_to_provider"] is False
    assert final["result"]["retry_allowed"] is False
    assert final["result"]["precondition"]["reviewed"] == {"amount": 100}
    assert final["result"]["precondition"]["current"] == {"amount": 175}


def test_an_unreadable_base_state_refuses_rather_than_assuming_unchanged(store):
    executed = []
    action_id = seed_approved_action_with_base_state(store, {"amount": 100})

    final = execute_approved_action(
        store,
        action_id,
        make_preconditioned_executor(
            executed,
            lambda params, base_state: {
                "ok": False,
                "code": "unverifiable",
                "reason": "the record could not be read",
            },
        ),
    )

    assert executed == []
    assert final["result"]["error_code"] == "precondition_unverifiable"
    assert final["result"]["sent_to_provider"] is False


def test_an_approval_with_no_recorded_base_state_refuses_closed(store):
    executed = []
    action_id = seed_approved_action(store)  # no base state recorded

    final = execute_approved_action(
        store,
        action_id,
        make_preconditioned_executor(executed, lambda params, base_state: {"ok": True}),
    )

    assert executed == []
    assert final["state"] == ActionState.FAILED.value
    assert final["result"]["error_code"] == "precondition_unverifiable"
    assert "approve" in final["result"]["error"].lower()


def test_a_matching_base_state_executes_normally(store):
    executed = []
    action_id = seed_approved_action_with_base_state(store, {"amount": 100})

    final = execute_approved_action(
        store,
        action_id,
        make_preconditioned_executor(
            executed, lambda params, base_state: {"ok": True, "check": "unchanged"}
        ),
    )

    assert executed == [{"amount": 100}]
    assert final["state"] == ActionState.EXECUTED.value


def test_the_precondition_receives_both_params_and_reviewed_state(store):
    seen = []
    action_id = seed_approved_action_with_base_state(store, {"amount": 100})

    execute_approved_action(
        store,
        action_id,
        make_preconditioned_executor(
            [],  # a separate collector, so the precondition's record is unambiguous
            lambda params, base_state: seen.append((params, base_state)) or {"ok": True},
        ),
    )

    assert seen == [({"amount": 100}, {"amount": 100})]


def test_an_executor_without_a_precondition_is_unaffected(store):
    """Only operation types that opt in get the check; nothing else changes."""
    action_id = seed_approved_action_with_base_state(store, {"amount": 100})

    final = execute_approved_action(store, action_id, make_executors())

    assert final["state"] == ActionState.EXECUTED.value


def test_a_refused_action_cannot_be_executed_again(store):
    action_id = seed_approved_action_with_base_state(store, {"amount": 100})
    executors = make_preconditioned_executor(
        [], lambda params, base_state: {"ok": False, "code": "conflict", "reason": "changed"}
    )
    execute_approved_action(store, action_id, executors)

    with pytest.raises(IllegalTransitionError):
        execute_approved_action(store, action_id, executors)


def test_a_verifier_that_cannot_confirm_stays_executed_not_failed(store):
    """A readback that ran but could not confirm is neither VERIFIED nor FAILED.

    The provider already accepted the write, so a failed readback must not be
    recorded as a failed mutation — it stays EXECUTED (verification pending),
    exactly like the no-verifier-registered case (A06).
    """
    action_id = seed_approved_action(store)

    final = execute_approved_action(
        store,
        action_id,
        make_executors(
            verifier=lambda params, result: {
                "ok": None,
                "check": "crew-bill-readback",
                "reason": "the snapshot could not be read",
            }
        ),
    )

    assert final["state"] == ActionState.EXECUTED.value
    # The note is recorded in the result, not claimed as a verification column.
    assert final["verification"] is None
    assert final["result"]["verification"]["ok"] is None
    assert final["result"]["verification"]["check"] == "crew-bill-readback"
