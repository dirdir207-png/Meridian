from datetime import datetime, timezone

from meridian.cancellation.brief import build_cancellation_brief
from meridian.trials import TrialRepository


def test_brief_is_human_actionable_and_marks_overdue(tmp_path):
    trial = TrialRepository(str(tmp_path / "brief.db")).create(
        service="Example", account_identifier="owner@example.test", plan_name="Plus",
        trial_started_at="2026-09-01T09:00:00-04:00", trial_ends_at="2026-09-10T09:00:00-04:00",
        buffer_days=1, timezone="America/New_York",
    )
    brief = build_cancellation_brief(trial, now=datetime(2026, 9, 10, tzinfo=timezone.utc), existing_channels=["email"])
    assert brief["service"] == "Example"
    assert brief["overdue"] is True
    assert brief["days_remaining"] < 0
    assert any(item["already_attempted"] for item in brief["channels"] if item["channel"] == "email")
    assert len(brief["evidence_checklist"]) == 3
