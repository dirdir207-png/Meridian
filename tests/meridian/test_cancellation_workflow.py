import pytest

from meridian.cancellation import (
    CancellationState,
    VerificationSignal,
    advance,
    route_cancellation,
    verification_status,
)


def test_click_does_not_count_as_cancellation():
    assert verification_status(set()) == "Unverified"
    assert verification_status({VerificationSignal.ACCOUNT_PAGE}) == "Requested"
    assert verification_status({VerificationSignal.CONFIRMATION_REFERENCE}) == "Acknowledged"
    assert verification_status({VerificationSignal.BILLING_STOPPED}) == "Billing stopped"


def test_billing_ground_truth_beats_weak_signal():
    assert verification_status({VerificationSignal.ACCOUNT_PAGE, VerificationSignal.BILLING_STOPPED}) == "Billing stopped"


def test_state_machine_rejects_skipping_verification():
    assert advance(CancellationState.PLANNED, CancellationState.ATTEMPTED) is CancellationState.ATTEMPTED
    with pytest.raises(ValueError, match="invalid"):
        advance(CancellationState.ATTEMPTED, CancellationState.VERIFIED)
    with pytest.raises(ValueError, match="invalid"):
        advance(CancellationState.VERIFIED, CancellationState.ATTEMPTED)


def test_routing_guardrails():
    direct = route_cancellation(known_recipe=True, confidence=1, allowlisted=False, essential=False)
    assert (direct.tier, direct.requires_approval) == ("direct", False)
    for kwargs in (
        {"allowlisted": True},
        {"essential": True},
        {"high_risk_channel": True},
        {"known_recipe": False},
        {"confidence": 0.5},
        {"multi_operation": True},
    ):
        base = dict(known_recipe=True, confidence=1, allowlisted=False, essential=False)
        base.update(kwargs)
        assert route_cancellation(**base).requires_approval is True
