import pytest

from meridian.cancellation import (
    CancellationRepository,
    CancellationState,
    VerificationSignal,
)
from meridian.trials import TrialRepository


def test_repository_persists_honest_workflow(tmp_path):
    db_path = str(tmp_path / "cancel.db")
    TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    repo = CancellationRepository(db_path)
    action = repo.create(1, "live_browser")
    action = repo.transition(action.id, CancellationState.ATTEMPTED)
    action = repo.transition(action.id, CancellationState.AWAITING_ACK)
    assert action.status_label == "Requested"
    with pytest.raises(ValueError, match="billing-stopped"):
        repo.transition(action.id, CancellationState.VERIFIED, signals={VerificationSignal.CONFIRMATION_REFERENCE})
    action = repo.transition(action.id, CancellationState.VERIFIED, signals={VerificationSignal.BILLING_STOPPED})
    assert action.status_label == "Billing stopped"
    assert repo.get(action.id).completed_at is not None


def test_repository_rejects_illegal_transition(tmp_path):
    db_path = str(tmp_path / "cancel.db")
    TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    repo = CancellationRepository(db_path)
    action = repo.create(1, "email")
    with pytest.raises(ValueError, match="invalid"):
        repo.transition(action.id, CancellationState.VERIFIED, signals={VerificationSignal.BILLING_STOPPED})
