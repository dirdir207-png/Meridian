import json
from pathlib import Path

import pytest

from meridian.status_emitter import (
    SCHEMA_VERSION,
    StatusEmitterError,
    build_status_event,
    canonical_event_json,
)


def sources(**overrides):
    base = {
        "tasks": {"schema_version": 1, "tasks": [{"id": "OS-021", "status": "in_progress"}]},
        "coordination": "# Agent coordination\n| Builder | `meridian/status_emitter.py` | active |\n",
        "current_status": "# Current Status\n\nVerified: bounded emitter slice.\nBlockers: none.\n",
        "roadmap": "# Roadmap\n\n## Track D\n## Track I\n## Track C\n",
        "decisions": "# Decisions\n\nOwner constraints: read-only; proposal -> approval -> execution -> verification.\n",
    }
    base.update(overrides)
    return base


def test_valid_projection_is_versioned_bounded_and_sanitized():
    event = build_status_event(sources=sources(), git={"repository": "ORSC", "branch": "feat/test", "revision": "a" * 40}, observed_at="2026-09-15T12:00:00Z")
    assert event["schema_version"] == SCHEMA_VERSION
    assert event["repository"] == "ORSC"
    assert event["workflow"]["phase"] == "IMPLEMENT"
    assert event["tracks"] == {"D": "active", "I": "active", "C": "active"}
    assert event["task_counts"] == {"total": 1, "in_progress": 1, "complete": 0, "blocked": 0, "ready": 0, "unknown": 0}
    assert len(canonical_event_json(event).encode()) <= 24_000
    assert "completion" not in canonical_event_json(event).lower()


def test_canonical_output_and_identity_are_stable():
    kwargs = {"sources": sources(), "git": {"repository": "ORSC", "branch": "main", "revision": "b" * 40}, "observed_at": "2026-09-15T12:00:00Z"}
    first, second = build_status_event(**kwargs), build_status_event(**kwargs)
    assert first == second
    assert canonical_event_json(first) == canonical_event_json(second)
    assert first["event_id"] == second["event_id"]


def test_duplicate_generation_has_same_event_identity_but_fresh_observation():
    a = build_status_event(sources=sources(), git={"repository": "ORSC", "branch": "main", "revision": "c" * 40}, observed_at="2026-09-15T12:00:00Z")
    b = build_status_event(sources=sources(), git={"repository": "ORSC", "branch": "main", "revision": "c" * 40}, observed_at="2026-09-15T12:01:00Z")
    assert a["event_id"] == b["event_id"]
    assert a["observed_at"] != b["observed_at"]


def test_malformed_partial_and_conflicting_sources_degrade():
    event = build_status_event(sources=sources(tasks="{"), git={"repository": "ORSC", "branch": "main", "revision": "d" * 40})
    assert event["health"] == "degraded"
    assert event["task_counts"]["unknown"] == 1
    conflict = build_status_event(sources=sources(current_status="# Current\nBlockers: blocked by conflicting roadmap gate."), git={"repository": "ORSC", "branch": "main", "revision": "e" * 40})
    assert conflict["health"] == "degraded"
    assert conflict["blockers"]


@pytest.mark.parametrize("bad", [
    "token=abc", "Authorization: Bearer secret", "Set-Cookie: x=y", "OTP 123456",
    "prompt: system instructions", "model reasoning: hidden", "/Users/someone/private/file.txt",
    "https://example.com/private", "balance $123.45 transaction at shop",
])
def test_unsafe_source_content_is_rejected(bad):
    with pytest.raises(StatusEmitterError):
        build_status_event(sources=sources(current_status=bad), git={"repository": "ORSC", "branch": "main", "revision": "f" * 40})


def test_oversized_source_is_rejected():
    with pytest.raises(StatusEmitterError):
        build_status_event(sources=sources(current_status="x" * 10_001), git={"repository": "ORSC", "branch": "main", "revision": "1" * 40})


def test_unknown_tasks_version_degrades_instead_of_raising():
    """The contract requires degraded, not an exception, for unusable input.

    An unknown schema version is the forward-compatibility case: a future source
    is the input most likely to arrive, and it must produce a bounded degraded
    event rather than aborting the producer. This assertion previously pinned the
    raising behaviour, which contradicted the contract it was meant to protect.
    """
    event = build_status_event(
        sources=sources(tasks={"schema_version": 99, "tasks": []}),
        git={"repository": "ORSC", "branch": "main", "revision": "2" * 40},
    )

    assert event["health"] == "degraded"
    assert event["evidence"]["errors"], "a degraded event must carry a bounded reason"
    # Explicit unknown, never a fabricated zero-task success.
    assert event["task_counts"]["unknown"] >= 1


def test_missing_tasks_source_degrades_instead_of_raising():
    event = build_status_event(
        sources={k: v for k, v in sources().items() if k != "tasks"},
        git={"repository": "ORSC", "branch": "main", "revision": "2" * 40},
    )

    assert event["health"] == "degraded"
    assert event["evidence"]["errors"]


def test_stale_and_out_of_order_timestamps_are_unknown():
    event = build_status_event(sources=sources(), git={"repository": "ORSC", "branch": "main", "revision": "3" * 40}, producer_at="2020-01-01T00:00:00Z", observed_at="2019-01-01T00:00:00Z")
    assert event["health"] == "degraded"
    assert event["timestamps"]["status"] == "unknown"


def test_no_mutation_or_control_surface_in_source():
    text = Path("meridian/status_emitter.py").read_text()
    assert "sqlite" not in text.lower()
    assert "requests" not in text.lower()
    assert "approve" not in text.lower()
    assert "execute" not in text.lower()


def test_cli_payload_is_json_object_only():
    payload = json.loads(canonical_event_json(build_status_event(sources=sources(), git={"repository": "ORSC", "branch": "main", "revision": "4" * 40}, observed_at="2026-09-15T12:00:00Z")))
    assert set(payload) >= {"schema_version", "event_id", "producer", "repository", "workflow", "tracks", "task_counts", "queues", "release_gate", "evidence", "blockers", "next_slice", "producer_timestamp", "observed_at"}
