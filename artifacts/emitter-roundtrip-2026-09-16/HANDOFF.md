# ORSC → Harness status emitter — round-trip handoff

**From:** ORSC / Meridian (`/Users/stephenwest/Openrouter/simplecrew-latest`, branch
`feat/meridian-implementation`)
**Date:** 2026-09-16
**Purpose:** first round-trip test of the ORSC status event against the Harness consumer.

## The artifact

`orsc-status-event.json` in this directory — the emitter's real output, unmodified.

| Fact | Value |
|---|---|
| Command | `.venv311/bin/python scripts/emit_meridian_status.py` |
| Exit code | 0, empty stderr |
| Size | 1145 bytes |
| `event_id` | `meridian-status-8ca1448f70656ae55cf3d26fd4c97d20` |
| `revision` | `d90b2398cf24ecdef173dc95ec1a2952e002ade1` (= HEAD at emit time) |
| `health` | `observed` |
| `schema_version` | 1 |

Transport is stdout only today; ORSC has no sink. The owner reports a Harness-side
transport now exists — please state the contract (path, endpoint, or queue) and ORSC will
emit to it.

## Which fields are derived, and which are NOT

**This is the part that matters.** Five fields are constants or false assertions, not
observation. A consumer that renders them will display fiction.

| Field | Emits | Reality |
|---|---|---|
| `queues.claims` | `[]` | **5 claims are active** in `docs/project/agent-claims.json`: `codex-observatory-assets`, `builder-trackd`, `builder-cadence`, `builder`, `astra` |
| `queues.ready` | `[]` | `task_counts.ready` is `2` — the payload contradicts itself |
| `workflow.phase` | `"IMPLEMENT"` | literal constant, not derived from the roadmap |
| `tracks` | `{"C":"active","D":"active","I":"active"}` | literal constants |
| `release_gate.status` | `"not_released"` | literal constant |

`queues.claims: []` is the serious one: it **asserts absence while evidence exists**. Treat
`queues`, `workflow`, `tracks` and `release_gate` as **unknown** until deviations 2–3 close.

**Derived and safe to consume:** `revision`, `branch`, `health`, `task_counts`,
`evidence.errors`, `observed_at`, `producer_timestamp`, `event_id`, `schema_version`.

**One ambiguity:** `blockers: []` alongside `task_counts.blocked: 5`. These are different
scopes — `blockers` is document-level (source errors or status text), `task_counts.blocked`
is task-level. Surfacing both as "blockers" will read as a contradiction.

## Safety claims, re-verified at this revision

Re-ran `artifacts/emitter-verification-2026-09-15/verify_emitter_contract.py`:

| Claim | Result |
|---|---|
| Malformed tasks source | `health: degraded`, error `tasks source is malformed` |
| Unknown tasks `schema_version` | `health: degraded` (forward-compat fix holds) |
| Credential-shaped input | **rejected**, nothing emitted |
| Out-of-order timestamps | `health: degraded`, `producer timestamp is newer than observation` |
| Bounded size, stable `event_id` | holds; `event_id` excludes observation time, so two builds of the same projection deduplicate while `observed_at` stays fresh |

## Open deviations (from `docs/project/MERIDIAN_STATUS_EMITTER_VERIFICATION.md`)

1. **Fixed** — unknown tasks schema version degraded instead of raising.
2. **Open** — `queues.claims` / `queues.ready` hardcoded empty. Contract precedence #3 assigns
   these to `AGENT_COORDINATION.md`.
3. **Open** — `phase` / `tracks` / `release_gate.status` hardcoded. Contract precedence #5
   assigns these to `MERIDIAN_ROADMAP.md` and `MERIDIAN_DECISIONS.md`.

Deviations 2–3 are **scope** decisions, not bug fixes: either derive the values, or narrow the
contract document to match what the emitter actually does. Missing tests are not the issue — a
test once pinned the wrong behaviour here, which is stronger evidence of a contract gap than a
missing test, because it looks like coverage.

## What ORSC needs from the Harness side

1. The transport contract (where to emit).
2. **Which fields the consumer reads.** If it renders claims/phase/tracks, deviations 2–3
   should close first rather than testing against fabricated values.
3. Confirmation of the validation result — what the Harness accepted, rejected, or could not
   interpret, so ORSC can record it as independently verified rather than self-asserted.

ORSC will not claim the round-trip is verified from its own side. Per the contract's standing
conclusion, live Harness integration remains unverified from this lane.
