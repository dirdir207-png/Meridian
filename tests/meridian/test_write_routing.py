"""Write-routing classifier tests: owner-direct vs proposal decision table."""
from meridian.write_routing import Provenance, classify_action


def test_owner_direct_fully_specified_executes_without_proposal():
    d = classify_action(
        Provenance.OWNER_DIRECT.value, "update_crew_bill",
        {"amount": 1500.0, "deterministic": True},
    )
    assert d.requires_proposal is False
    assert "owner-direct" in d.reason


def test_ai_interpreted_requires_proposal():
    d = classify_action(
        Provenance.AI_INTERPRETED.value, "update_crew_bill", {"amount": 1500.0}
    )
    assert d.requires_proposal is True
    assert "interpretation" in d.reason


def test_composed_multi_op_requires_proposal():
    d = classify_action(
        Provenance.AI_COMPOSED.value, "cancel_income_source",
        {"amount": 30.0, "ops": ["cancel_income", "move_money"]},
    )
    assert d.requires_proposal is True
    assert "multi-action" in d.reason or "composed" in d.reason


def test_low_confidence_requires_proposal_even_for_owner_direct():
    d = classify_action(
        Provenance.OWNER_DIRECT.value, "update_crew_bill",
        {"amount": 1500.0}, low_confidence=True,
    )
    assert d.requires_proposal is True
    assert "low-confidence" in d.reason


def test_under_specified_requires_proposal():
    d = classify_action(
        Provenance.OWNER_DIRECT.value, "update_crew_bill",
        {"needs_amount": True, "amount": None},
    )
    assert d.requires_proposal is True
    assert "under-specified" in d.reason


def test_plan_level_budget_change_owner_direct_executes():
    # Owner-direct + fully-specified plan-level change executes (owner authority).
    d = classify_action(
        Provenance.OWNER_DIRECT.value, "update_autopilot_settings", {"optimize": True}
    )
    assert d.requires_proposal is False
    assert "owner-direct" in d.reason


def test_plan_level_budget_type_proposal_for_non_owner_provenance():
    # reallocate_budget is plan-level: proposal for AI / scheduled, direct for owner.
    for prov in (Provenance.SCHEDULED.value, Provenance.AI_INTERPRETED.value):
        d = classify_action(prov, "reallocate_budget", {"amount": 100.0})
        assert d.requires_proposal is True
        assert "plan-level" in d.reason or "require confirmation" in d.reason
    d = classify_action(Provenance.OWNER_DIRECT.value, "reallocate_budget", {"amount": 100.0})
    assert d.requires_proposal is False


def test_explicit_confidence_below_threshold_requires_proposal():
    d = classify_action(
        Provenance.OWNER_DIRECT.value, "update_crew_bill",
        {"amount": 100.0, "confidence": 0.5},
    )
    assert d.requires_proposal is True


def test_unknown_provenance_defaults_to_proposal():
    d = classify_action("from_the_void", "update_crew_bill", {"amount": 1.0})
    assert d.requires_proposal is True


def test_fund_transfer_between_pockets_owner_direct_executes():
    d = classify_action(
        Provenance.OWNER_DIRECT.value, "move_money_between_pockets", {"amount": 30.0}
    )
    assert d.requires_proposal is False


def test_route_mutation_direct_vs_proposal_paths():
    """Owner-direct fully-specified routes direct; AI-composed routes to a proposal."""
    import tempfile

    from crew.actions import ActionStore
    from meridian.write_routing import route_mutation

    db = tempfile.mktemp(suffix=".db")
    store = ActionStore(db, allowed_types=("update_crew_bill", "move_money_between_pockets"))

    # Direct: owner sets Rent exactly -> should NOT require proposal, and should
    # attempt execution (no executor registered -> the direct path still returns
    # an action; here we only assert the routing decision + proposal gate).
    direct = route_mutation(
        store, {}, action_type="update_crew_bill",
        params={"amount": 1500.0, "deterministic": True},
        rationale="set rent", requested_by="owner",
        provenance="owner_direct",
    )
    assert direct["routing_direct"] is True
    assert direct["routing"].requires_proposal is False

    # AI-composed multi-op -> proposal (action stays PROPOSED, no auto-execute).
    prop = route_mutation(
        store, {}, action_type="move_money_between_pockets",
        params={"amount": 30.0, "ops": ["a", "b"]},
        rationale="ai interpreted cancel+move", requested_by="owner",
        provenance="ai_composed",
    )
    assert prop["routing_direct"] is False
    assert prop["routing"].requires_proposal is True
    assert prop["action"]["state"] == "proposed"


def test_direct_mutation_runs_executor_proposal_does_not(monkeypatch):
    """Owner-direct must attempt the executor; AI-interpreted must only propose."""
    import tempfile

    from crew.actions import ActionStore
    from crew.executors import ExecutorSpec
    from meridian.write_routing import route_mutation

    db = tempfile.mktemp(suffix=".db")
    store = ActionStore(db, allowed_types=("create_crew_pocket",))
    calls = []

    def fake_create(params):
        calls.append(params)
        return {"success": True, "crew": {"ok": True}}

    executors = {"create_crew_pocket": ExecutorSpec(execute=fake_create, verifier=None)}

    # Owner-direct, fully-specified -> executes (fake called).
    direct = route_mutation(
        store, executors, action_type="create_crew_pocket",
        params={"account_id": "Acct:1", "name": "Savings", "type": "SAVINGS"},
        rationale="set pocket", requested_by="owner", provenance="owner_direct",
    )
    assert direct["routing_direct"] is True
    # create_crew_pocket has no readback verifier, so the accepted write stays
    # EXECUTED (verification pending) and is never claimed as VERIFIED.
    assert direct["action"]["state"] == "executed"
    assert calls, "owner-direct mutation should have reached the executor"

    # AI-interpreted -> proposal only, executor never called.
    calls.clear()
    prop = route_mutation(
        store, executors, action_type="create_crew_pocket",
        params={"account_id": "Acct:1", "name": "Savings", "type": "SAVINGS"},
        rationale="ai interpreted", requested_by="owner", provenance="ai_interpreted",
    )
    assert prop["routing_direct"] is False
    assert prop["action"]["state"] == "proposed"
    assert calls == [], "AI-interpreted mutation must NOT reach the executor until approved"


# ── Payday (OS-083): the owner's rule, pinned for the paycheck funding plan ──
# The owner, 2026-09-21: "actions directly made by me in the app circumvent the need for proposal,
# I can directly execute." Both halves are pinned below, and the second matters as much as the
# first: a change that made every payday edit direct would delete an approval gate, which is the
# opposite failure and the worse one.
#
# Why this type specifically: the paycheck funding plan IS Crew's payday mechanism, and three
# operations for it already ship with executors and readback verifiers
# (meridian/crew_write_actions.py:674-685), so payday is the first non-plan-level Crew write whose
# route needed confirming. It is deliberately NOT in _PLAN_LEVEL_TYPES.


def test_owner_direct_payday_edit_executes_without_a_proposal():
    """A direct, fully-specified payday edit must NOT be parked for approval.

    The params are the ones docs/project/write-coverage.json documents for this type rather than
    invented ones: fundingPlanId is the identity the readback verifier uses, and the verifier
    compares name and amount.
    """
    d = classify_action(
        Provenance.OWNER_DIRECT.value,
        "update_crew_paycheck_funding_plan",
        {"fundingPlanId": "plan-123", "amount": 1200.0, "deterministic": True},
    )
    assert d.requires_proposal is False, (
        "the owner's own unambiguous payday edit was routed to a proposal; the write model keys on "
        "intent-confidence and determinism, not on who initiated"
    )
    assert "owner-direct" in d.reason


def test_composed_or_uncertain_payday_edit_still_requires_a_proposal():
    """The approval gate survives: an assembled or low-confidence payday change proposes."""
    composed = classify_action(
        Provenance.AI_COMPOSED.value,
        "update_crew_paycheck_funding_plan",
        {"fundingPlanId": "plan-123", "amount": 1200.0},
    )
    assert composed.requires_proposal is True

    uncertain = classify_action(
        Provenance.OWNER_DIRECT.value,
        "update_crew_paycheck_funding_plan",
        {"fundingPlanId": "plan-123", "amount": 1200.0},
        low_confidence=True,
    )
    assert uncertain.requires_proposal is True, (
        "a low-confidence payday edit executed directly, which removes the owner's approval gate"
    )


def test_payday_mutation_reaches_its_executor_only_on_the_direct_path():
    """END-TO-END for the paycheck funding plan, which the classifier tests above do not cover.

    Those two prove the DECISION; this proves the CONSEQUENCE: that a direct, fully-specified
    owner edit actually reaches the executor that talks to Crew, and that an interpreted or
    low-confidence edit does not reach it at all. Without this, "the owner's direct edit executes"
    would rest on the router's reasoning rather than on anything observed.

    The executor here is a local fake so the call is observable; the REAL registration for this type
    (and its readback verifier) is guarded separately by tests/meridian/test_write_coverage.py,
    which fails if a registered type loses its executor.
    """
    import tempfile

    from crew.actions import ActionStore
    from crew.executors import ExecutorSpec
    from meridian.write_routing import route_mutation

    db = tempfile.mktemp(suffix=".db")
    store = ActionStore(db, allowed_types=("update_crew_paycheck_funding_plan",))
    calls = []

    def fake_update(params):
        calls.append(params)
        return {"success": True, "crew": {"ok": True}}

    executors = {
        "update_crew_paycheck_funding_plan": ExecutorSpec(execute=fake_update, verifier=None)
    }

    # The owner sets the amount on one plan, directly and unambiguously.
    direct = route_mutation(
        store, executors, action_type="update_crew_paycheck_funding_plan",
        params={"fundingPlanId": "plan-123", "amount": 1200.0, "deterministic": True},
        rationale="set the payday amount", requested_by="owner", provenance="owner_direct",
    )
    assert direct["routing_direct"] is True, (
        "the owner's direct payday edit was routed to a proposal instead of executing"
    )
    assert calls, "the owner's direct payday edit never reached the executor, so nothing was written"

    # An AI-assembled change must wait for approval and must not touch Crew.
    calls.clear()
    interpreted = route_mutation(
        store, executors, action_type="update_crew_paycheck_funding_plan",
        params={"fundingPlanId": "plan-123", "amount": 1200.0},
        rationale="ai assembled a payday change", requested_by="owner",
        provenance="ai_interpreted",
    )
    assert interpreted["routing_direct"] is False
    assert interpreted["action"]["state"] == "proposed"
    assert calls == [], "an interpreted payday edit reached the executor before the owner approved"

    # Low confidence is the subtler case: the owner asked, but the value is not solid, so the
    # approval gate must still stand.
    calls.clear()
    uncertain = route_mutation(
        store, executors, action_type="update_crew_paycheck_funding_plan",
        params={"fundingPlanId": "plan-123", "amount": 1200.0},
        rationale="guessed from a partial request", requested_by="owner",
        provenance="owner_direct", low_confidence=True,
    )
    assert uncertain["routing_direct"] is False
    assert calls == [], "a low-confidence payday edit reached the executor without approval"
