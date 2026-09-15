# ORSC Meridian status emitter handoff

Usage from the ORSC root:

```bash
.venv311/bin/python scripts/emit_meridian_status.py --observed-at 2026-09-15T12:00:00Z
```

The command prints exactly one sanitized JSON event to stdout. On unreadable input it prints only a minimal degraded event and never echoes exception payloads or source content. It reads Git metadata and the five approved project documents; it never opens the separate Harness workspace.

The event is deterministic for a fixed source projection. `event_id` identifies the projection and excludes observation timestamps; `producer_timestamp` identifies when the producer generated the observation and `observed_at` identifies the observation time. Producer-newer-than-observed timestamps are degraded/unknown. Duplicate events are therefore deduplicable while observation freshness remains visible.

This is an ORSC-side handoff, not a live integration. ORSC owns truthful source projection and sanitization. Harness owns independent validation, filtering, deduplication, freshness checks, and rendering. No webhook, network transport, wakeup, steering, approval, execution, provider call, database mutation, financial action, or scheduler is included.

The emitter is intentionally bounded: no universal completion percentage, no balances or transaction detail, no credentials or raw prompts/transcripts/tool output/model reasoning, no raw absolute paths, and no unrestricted URLs. Unknown, stale, malformed, partial, or conflicting sources remain degraded rather than becoming success. See `MERIDIAN_STATUS_EMITTER_CONTRACT.md` for the frozen schema and precedence rules.
