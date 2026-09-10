from meridian.policy import ActionPlan, Constitution, evaluate_constitution


def test_inactive_constitution_fails_closed():
    result = evaluate_constitution(Constitution(), ActionPlan("transfer", 10))
    assert result.decision == "cannot_evaluate"
    assert result.confidence == 0.0


def test_policy_blocks_prohibited_action_and_low_buffer():
    constitution = Constitution(minimum_buffer=100, prohibited_action_types=("transfer",), active=True)
    result = evaluate_constitution(constitution, ActionPlan("transfer", 10), evidence={"remaining_after_action": 80})
    assert result.decision == "blocked"
    assert set(result.blocking_rules) == {"prohibited_action_types", "minimum_buffer"}


def test_policy_requires_clarification_when_evidence_missing():
    result = evaluate_constitution(Constitution(minimum_buffer=100, active=True), ActionPlan("transfer", 10))
    assert result.decision == "requires_clarification"
    assert "remaining_after_action is not available" in result.assumptions


def test_automatic_action_never_becomes_authorized():
    constitution = Constitution(maximum_automatic_amount=50, active=True)
    result = evaluate_constitution(constitution, ActionPlan("fund", 20, automatic=True))
    assert result.decision == "requires_approval"
    assert "explicit owner approval" in result.recovery_action
