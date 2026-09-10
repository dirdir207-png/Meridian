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


def test_deadline_projection_is_read_only_and_skips_terminal_trials(tmp_path):
    from datetime import datetime

    from meridian.cancellation.deadlines import upcoming_deadlines
    from meridian.trials import TrialRepository

    repo = TrialRepository(str(tmp_path / "deadline.db"))
    active = repo.create(service="Active", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-20T00:00:00Z")
    repo.create(service="Canceled", status="canceled", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-20T00:00:00Z")
    events = upcoming_deadlines(repo.list(include_canceled=True), now=datetime.fromisoformat("2026-09-10T00:00:00+00:00"))
    assert {event["trial_id"] for event in events} == {active.id}
    assert all(event["service"] == "Active" for event in events)


def test_post_deadline_reconciliation_is_conservative(tmp_path):
    from datetime import datetime, timezone

    from meridian.cancellation.reconcile import verify_post_deadline_billing
    from meridian.trials import TrialRepository
    trial = TrialRepository(str(tmp_path / "reconcile.db")).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    signals, reason = verify_post_deadline_billing(trial, [], now=now, reconciliation_complete=False)
    assert not signals and "Insufficient" in reason
    signals, reason = verify_post_deadline_billing(trial, [], now=now, reconciliation_complete=True)
    assert signals and "complete" in reason
    signals, reason = verify_post_deadline_billing(
        trial, [{"merchant": "Example", "occurred_at": "2026-09-12T00:00:00Z"}],
        now=now, reconciliation_complete=True,
    )
    assert not signals and "charge" in reason


def test_escalation_plan_skips_attempted_channels(tmp_path):
    from meridian.cancellation.escalation import build_escalation_plan
    from meridian.cancellation.repository import CancellationRepository
    from meridian.trials import TrialRepository

    db_path = str(tmp_path / "escalation.db")
    trial = TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    repo = CancellationRepository(db_path)
    action = repo.create(trial.id, "email")
    plan = build_escalation_plan(trial, [action])
    channels = [step["channel"] for step in plan["next"]]
    assert "email" not in channels
    assert channels[0] == "live_browser"
    assert plan["read_only"] is True
    assert plan["requires_owner"] is True


def test_submission_approval_never_auto_approves_risky_routes(tmp_path):
    from meridian.cancellation.approval import evaluate_submission
    from meridian.cancellation.repository import CancellationRepository
    from meridian.trials import TrialRepository

    db_path = str(tmp_path / "approval.db")
    trial = TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    action = CancellationRepository(db_path).create(trial.id, "email")
    denied = evaluate_submission(action, owner_approved=False, known_recipe=True, confidence=1)
    assert denied.approved is False
    approved = evaluate_submission(action, owner_approved=True, known_recipe=False, confidence=0.5)
    assert approved.approved is True
    assert approved.expires_at is not None


def test_execution_requires_approval_and_adapter(tmp_path):
    from meridian.cancellation.approval import ApprovalDecision
    from meridian.cancellation.executor import execute_approved
    from meridian.cancellation.repository import CancellationRepository
    from meridian.trials import TrialRepository

    db_path = str(tmp_path / "executor.db")
    trial = TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    action = CancellationRepository(db_path).create(trial.id, "live_browser")
    denied = execute_approved(action, ApprovalDecision(False, True, "approval required"))
    assert denied.attempted is False
    approved = ApprovalDecision(True, False, "approved")
    assert execute_approved(action, approved).attempted is False
    result = execute_approved(action, approved, adapter=type("Adapter", (), {"submit": lambda _, value: {"reference": "R1"}})())
    assert result.attempted is True
    assert result.state == "attempted"


def test_dry_run_adapter_never_contacts_external_service(tmp_path):
    from meridian.cancellation.adapters import DryRunAdapter
    from meridian.cancellation.approval import ApprovalDecision
    from meridian.cancellation.executor import execute_approved
    from meridian.cancellation.repository import CancellationRepository
    from meridian.trials import TrialRepository

    db_path = str(tmp_path / "dry-run.db")
    trial = TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    action = CancellationRepository(db_path).create(trial.id, "email")
    result = execute_approved(action, ApprovalDecision(True, False, "approved"), adapter=DryRunAdapter())
    assert result.attempted is True
    assert result.provider_result["dry_run"] is True
    assert result.provider_result["external_contact"] is False
