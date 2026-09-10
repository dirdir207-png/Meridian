from datetime import datetime

import pytest

from meridian.trials import TrialRepository


@pytest.fixture
def repository(tmp_path):
    return TrialRepository(str(tmp_path / "trials.db"))


def test_create_derives_cancel_by_in_local_timezone(repository):
    trial = repository.create(
        service="Example",
        trial_started_at="2026-09-10T09:00:00-04:00",
        trial_ends_at="2026-09-17T09:00:00-04:00",
        buffer_days=2,
        timezone="America/New_York",
        source_of_truth="checkout_capture",
        confidence=1,
    )
    assert trial.cancel_by == "2026-09-15T09:00:00-04:00"
    assert trial.source_of_truth == "checkout_capture"


def test_rejects_inferred_or_invalid_terms(repository):
    with pytest.raises(ValueError, match="after"):
        repository.create(service="X", trial_started_at="2026-09-10T00:00:00Z", trial_ends_at="2026-09-09T00:00:00Z")
    with pytest.raises(ValueError, match="confidence"):
        repository.create(service="X", trial_started_at="2026-09-10T00:00:00Z", trial_ends_at="2026-09-11T00:00:00Z", confidence=2)


def test_update_recomputes_deadline_and_preserves_history_shape(repository):
    trial = repository.create(service="X", trial_started_at="2026-09-10T00:00:00Z", trial_ends_at="2026-09-20T00:00:00Z")
    updated = repository.update(trial.id, trial_ends_at="2026-09-25T00:00:00Z", buffer_days=3, status="active")
    assert updated.status == "active"
    assert updated.cancel_by == "2026-09-22T00:00:00+00:00"
    assert repository.get(trial.id).id == trial.id


def test_list_orders_by_earliest_deadline(repository):
    later = repository.create(service="Later", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-30T00:00:00Z")
    earlier = repository.create(service="Earlier", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    assert [item.id for item in repository.list()] == [earlier.id, later.id]


def test_deadline_events_are_anchored_to_cancel_by(repository):
    from meridian.trials import deadline_events

    trial = repository.create(
        service="X",
        trial_started_at="2026-09-01T09:00:00-04:00",
        trial_ends_at="2026-09-20T09:00:00-04:00",
        buffer_days=1,
        timezone="America/New_York",
    )
    events = deadline_events(trial, now=datetime.fromisoformat("2026-09-10T00:00:00+00:00"))
    assert [event["kind"] for event in events] == ["7_days", "3_days", "1_day", "deadline"]
    assert events[-1]["due_at"] == "2026-09-19T09:00:00-04:00"
    assert events[0]["overdue"] == "false"
