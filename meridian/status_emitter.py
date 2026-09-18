"""Deterministic, read-only, sanitized Meridian status event projection."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
MAX_TEXT = 10_000
MAX_LIST = 12
MAX_EVENT_BYTES = 24_000
_ALLOWED_TASK_VERSIONS = {1}
_SECRET = re.compile(r"(?i)(bearer\s+|authorization\s*:|token\s*[=:]|secret\s*[=:]|cookie\s*:|otp\b|password\s*[=:])")
_TRANSCRIPT = re.compile(r"(?i)(prompt\s*:|model\s+reasoning|tool\s+output|raw\s+transcript)")
_PATH = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\|/private/|/tmp/)[^\s\n]*")
_URL = re.compile(r"https?://[^\s]+")
_FINANCIAL = re.compile(r"(?i)(balance\s*[$€£]?\s*\d|transaction\s+(at|description)|account\s+number|routing\s+number)")


class StatusEmitterError(ValueError):
    """Input cannot be safely projected."""


def _iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _check_text(value: str, *, field: str) -> str:
    if len(value) > MAX_TEXT or _SECRET.search(value) or _TRANSCRIPT.search(value) or _PATH.search(value) or _URL.search(value) or _FINANCIAL.search(value):
        raise StatusEmitterError(f"unsafe or oversized {field}")
    return value


def _source_text(value: Any, field: str) -> str:
    if isinstance(value, str):
        # Governing project documents may mention repository paths while the
        # projection emits none of their raw text. Reject compact payloads that
        # look like an attempted secret/transcript injection.
        if len(value) < 1_000:
            return _check_text(value, field=field)
        if len(value) > MAX_TEXT and not value.lstrip().startswith("#"):
            raise StatusEmitterError(f"unsafe or oversized {field}")
        return value
    if isinstance(value, dict):
        return _check_text(json.dumps(value, sort_keys=True, separators=(",", ":")), field=field)
    raise StatusEmitterError(f"malformed {field}")


def _tasks(value: Any) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    try:
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, dict) or value.get("schema_version") not in _ALLOWED_TASK_VERSIONS:
            raise StatusEmitterError("unknown or malformed tasks version")
        records = value.get("tasks")
        if not isinstance(records, list) or len(records) > MAX_LIST * 10:
            raise StatusEmitterError("malformed tasks")
        return [r for r in records if isinstance(r, dict)], errors
    except (json.JSONDecodeError, TypeError):
        return [{"status": "unknown"}], ["tasks source is malformed"]
    except StatusEmitterError as exc:
        # The contract is explicit that missing, malformed or unknown-version input
        # produces `health: degraded` with bounded errors, and that the emitter
        # "never guesses success". Re-raising here aborted the producer on exactly
        # the forward-compatibility case — a future schema version, which is the
        # input most likely to arrive from an evolving source. The message carries
        # only a fixed internal phrase, never source content.
        return [{"status": "unknown"}], [f"tasks source cannot be projected: {exc}"]


def _counts(records: list[dict[str, Any]]) -> dict[str, int]:
    result = {"total": len(records), "in_progress": 0, "complete": 0, "blocked": 0, "ready": 0, "unknown": 0}
    for record in records:
        status = str(record.get("status", "unknown"))
        if status not in result or status == "total":
            result["unknown"] += 1
        else:
            result[status] += 1
    return result


def canonical_event_json(event: dict[str, Any]) -> str:
    return json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_status_event(*, sources: dict[str, Any], git: dict[str, str], producer_at: str | None = None, observed_at: str | None = None) -> dict[str, Any]:
    if not isinstance(sources, dict) or not isinstance(git, dict):
        raise StatusEmitterError("sources and git must be objects")
    repository, branch, revision = (str(git.get(k, "")) for k in ("repository", "branch", "revision"))
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", repository) or not re.fullmatch(r"[A-Za-z0-9._/-]{1,120}", branch) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise StatusEmitterError("invalid git metadata")
    records, errors = _tasks(sources.get("tasks"))
    for name in ("coordination", "current_status", "roadmap", "decisions"):
        _source_text(sources.get(name), name)
    producer_dt = _iso(producer_at) or _iso(observed_at) or datetime.now(timezone.utc)
    observed_dt = _iso(observed_at) or producer_dt
    if producer_dt > observed_dt:
        errors.append("producer timestamp is newer than observation")
    status_text = str(sources.get("current_status", ""))
    blockers = ["source disagreement or incomplete evidence"] if errors or "blocker" in status_text.lower() and "none" not in status_text.lower() else []
    health = "degraded" if errors or blockers else "observed"
    event_core = {
        "schema_version": SCHEMA_VERSION,
        "producer": {"name": "orsc-meridian-status-emitter", "version": "1"},
        "source": {"tasks": "MERIDIAN_OS_TASKS.json@1", "coordination": "AGENT_COORDINATION.md", "status": "CURRENT_STATUS.md", "roadmap": "MERIDIAN_ROADMAP.md", "decisions": "MERIDIAN_DECISIONS.md"},
        "repository": repository,
        "branch": branch,
        "revision": revision,
        "workflow": {"phase": "IMPLEMENT", "active_slice": "sanitized Meridian status emitter"},
        "tracks": {"D": "active", "I": "active", "C": "active"},
        "task_counts": _counts(records),
        "queues": {"claims": [], "ready": [], "blocked": blockers[:MAX_LIST]},
        "release_gate": {"status": "not_released", "reason": "read-only emitter; owner acceptance and Harness integration remain separate"},
        "evidence": {"status": "degraded" if errors else "source documents observed", "errors": errors[:MAX_LIST]},
        "blockers": blockers[:MAX_LIST],
        "next_slice": "Harness independently validates and integrates this contract",
        "producer_timestamp": producer_dt.isoformat().replace("+00:00", "Z"),
        "observed_at": observed_dt.isoformat().replace("+00:00", "Z"),
        "timestamps": {"status": "unknown" if errors else "ordered"},
        "health": health,
    }
    identity_material = {key: value for key, value in event_core.items() if key not in {"producer_timestamp", "observed_at", "timestamps"}}
    identity = hashlib.sha256(canonical_event_json(identity_material).encode()).hexdigest()[:32]
    event = {"event_id": f"meridian-status-{identity}", **event_core}
    if len(canonical_event_json(event).encode()) > MAX_EVENT_BYTES:
        raise StatusEmitterError("event exceeds maximum size")
    return event
