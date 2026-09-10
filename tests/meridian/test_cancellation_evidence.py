import hashlib

import pytest

from meridian.cancellation import CancellationRepository
from meridian.evidence import EvidenceRepository
from meridian.trials import TrialRepository


def test_cancellation_action_links_existing_evidence(tmp_path):
    db_path = str(tmp_path / "evidence.db")
    TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    action = CancellationRepository(db_path).create(1, "email")
    evidence = EvidenceRepository(db_path).add_item(
        source_kind="test", source_id="mail-1", content_hash=hashlib.sha256(b"confirmation").hexdigest(),
        mime_type="message/rfc822", size_bytes=12, title="Cancellation confirmation",
    )
    repo = CancellationRepository(db_path)
    link = repo.attach_evidence(action.id, evidence.id, relation="confirmation", provenance="mail_intake")
    assert link["evidence_id"] == evidence.id
    assert repo.list_evidence(action.id)[0]["relation"] == "confirmation"


def test_cancellation_action_rejects_missing_evidence(tmp_path):
    db_path = str(tmp_path / "evidence.db")
    TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    repo = CancellationRepository(db_path)
    action = repo.create(1, "email")
    with pytest.raises(ValueError, match="evidence_id"):
        repo.attach_evidence(action.id, 999)


def test_due_notifications_are_idempotent(tmp_path):
    from datetime import datetime, timezone

    from meridian.cancellation.notifications import TrialNotificationRepository

    db_path = str(tmp_path / "notifications.db")
    TrialRepository(db_path).create(service="Example", trial_started_at="2026-09-01T00:00:00Z", trial_ends_at="2026-09-10T00:00:00Z")
    repo = TrialNotificationRepository(db_path)
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    first = repo.materialize_due(now=now)
    second = repo.materialize_due(now=now)
    assert len(first) == 4
    assert len(second) == 4
    sent = repo.mark_sent(first[0].id)
    assert sent.status == "sent"


def test_notification_repository_rejects_invalid_status(tmp_path):
    from meridian.cancellation.notifications import TrialNotificationRepository

    with pytest.raises(ValueError, match="status"):
        TrialNotificationRepository(str(tmp_path / "notifications.db")).list(status="bogus")
