"""Verify the ORSC status-emitter contract against the implementation.

The contract is asserted in MERIDIAN_STATUS_EMITTER_CONTRACT.md; this checks
whether the implementation actually satisfies it. Read-only: pure function calls
and one CLI run, no database, no provider, no network.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from meridian.status_emitter import (
    MAX_EVENT_BYTES,
    StatusEmitterError,
    build_status_event,
    canonical_event_json,
)

GIT = {"repository": "ORSC", "branch": "feat/meridian-implementation", "revision": "a" * 40}

COORDINATION = "# Agent coordination\n\n| Agent | Files | Since | Status |\n|---|---|---|---|\n| Builder | a.py | 2026-09-15 | active |\n"
STATUS_DOC = "# Current status\n\nNo open blockers. Verified evidence recorded.\n"
ROADMAP = "# Roadmap\n\n## Track D — Design fidelity\n"
DECISIONS = "# Decisions\n\nD-007 development autonomy with action gating.\n"


def sources(**overrides):
    base = {
        "tasks": json.dumps({"schema_version": 1, "tasks": [
            {"id": "T1", "status": "complete"}, {"id": "T2", "status": "ready"},
        ]}),
        "coordination": COORDINATION,
        "current_status": STATUS_DOC,
        "roadmap": ROADMAP,
        "decisions": DECISIONS,
    }
    base.update(overrides)
    return base


results = {}

# 1. event_id must exclude observation time so the same projection deduplicates.
first = build_status_event(sources=sources(), git=GIT, producer_at="2026-09-15T10:00:00Z", observed_at="2026-09-15T10:00:00Z")
second = build_status_event(sources=sources(), git=GIT, producer_at="2026-09-16T11:30:00Z", observed_at="2026-09-16T11:30:00Z")
results["event_id_stable_across_time"] = first["event_id"] == second["event_id"]
results["observed_at_is_fresh"] = first["observed_at"] != second["observed_at"]

# 2. Size bound.
blob = canonical_event_json(first).encode()
results["event_bytes"] = len(blob)
results["within_max_event_bytes"] = len(blob) <= MAX_EVENT_BYTES

# 3. Contract: coordination establishes bounded claims/queues.
results["queues_claims"] = first["queues"]["claims"]
results["queues_ready"] = first["queues"]["ready"]

# 4. Contract: roadmap/decisions establish phase and tracks.
results["workflow_phase"] = first["workflow"]["phase"]
results["tracks"] = first["tracks"]

# 5. Contract: missing/malformed tasks -> degraded, never a guess.
try:
    degraded = build_status_event(sources=sources(tasks="{not json"), git=GIT, producer_at="2026-09-15T10:00:00Z", observed_at="2026-09-15T10:00:00Z")
    results["malformed_tasks"] = {"health": degraded["health"], "errors": degraded["evidence"]["errors"]}
except StatusEmitterError as exc:
    results["malformed_tasks"] = {"raised_instead_of_degrading": str(exc)}

# 6. Contract: an unsupported tasks schema version should also degrade.
try:
    bumped = build_status_event(sources=sources(tasks=json.dumps({"schema_version": 2, "tasks": []})), git=GIT, producer_at="2026-09-15T10:00:00Z", observed_at="2026-09-15T10:00:00Z")
    results["unknown_schema_version"] = {"health": bumped["health"], "errors": bumped["evidence"]["errors"]}
except StatusEmitterError as exc:
    results["unknown_schema_version"] = {"raised_instead_of_degrading": str(exc)}

# 7. Safety: a secret-shaped coordination doc must be rejected, not emitted.
try:
    build_status_event(sources=sources(coordination="token = abc123"), git=GIT, producer_at="2026-09-15T10:00:00Z", observed_at="2026-09-15T10:00:00Z")
    results["rejects_secret_shaped_input"] = False
except StatusEmitterError:
    results["rejects_secret_shaped_input"] = True

# 8. Stale/out-of-order timestamps.
out_of_order = build_status_event(sources=sources(), git=GIT, producer_at="2026-09-15T12:00:00Z", observed_at="2026-09-15T10:00:00Z")
results["out_of_order"] = {"health": out_of_order["health"], "errors": out_of_order["evidence"]["errors"]}

print(json.dumps(results, indent=2))
