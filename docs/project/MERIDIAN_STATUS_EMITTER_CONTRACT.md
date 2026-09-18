# Meridian status emitter contract

**Schema:** `1` · **Producer:** `orsc-meridian-status-emitter/1`

ORSC emits one canonical JSON object describing repository/project evidence. It is a read-only observation event, not a command, alert, approval, forecast, balance, or permission.

## Envelope

Required fields: `schema_version` (integer, known value `1`), `event_id` (stable SHA-256-derived identifier), `producer` (`name`, `version`), `source` (approved source/version labels), `repository`, `branch`, `revision` (40-hex source revision), `workflow` (`phase`, `active_slice`), `tracks` (`D`, `I`, `C`), `task_counts`, `queues`, `release_gate`, `evidence`, `blockers`, `next_slice`, `producer_timestamp`, `observed_at`, `timestamps`, and `health`.

Strings are bounded to 10,000 bytes/characters, lists to 12 entries, and the complete UTF-8 event to 24,000 bytes. Identifiers are constrained to safe ASCII forms. `event_id` excludes observation time so duplicate generation for the same source projection deduplicates; `observed_at` remains fresh metadata.

## Source precedence and disagreement

1. Git metadata establishes repository, branch, and source revision.
2. `MERIDIAN_OS_TASKS.json` establishes task counts (schema version 1 only).
3. `AGENT_COORDINATION.md` establishes bounded claims/queues.
4. `CURRENT_STATUS.md` supplies verified evidence and blockers.
5. `MERIDIAN_ROADMAP.md` and `MERIDIAN_DECISIONS.md` establish phase, tracks, gates, and constraints.

No source overrides a safety constraint. Missing, malformed, stale, conflicting, or out-of-order data produces `health: degraded`, explicit unknowns, and bounded errors; the emitter never guesses success.

## Safety and ownership boundary

The emitter rejects credentials, authorization headers, tokens, cookies, OTPs, prompts, raw transcripts, tool output, model reasoning, absolute paths, unrestricted URLs, balances, transaction descriptions, and unnecessary financial details. It performs no database write, provider call, network transport, webhook, financial mutation, retry, scheduling, approval, agent control, or Harness call. It does not emit universal completion percentages.

ORSC produces this sanitized event only. Harness independently validates schema, filters/redacts, deduplicates by `event_id`, freshness-checks timestamps, and renders it. Live Harness mode is not claimed until Harness independently integrates and verifies this contract.

## Example

```json
{"schema_version":1,"event_id":"meridian-status-…","producer":{"name":"orsc-meridian-status-emitter","version":"1"},"repository":"ORSC","branch":"feat/meridian-implementation","revision":"0123456789abcdef0123456789abcdef01234567","workflow":{"phase":"IMPLEMENT","active_slice":"sanitized Meridian status emitter"},"health":"observed"}
```
