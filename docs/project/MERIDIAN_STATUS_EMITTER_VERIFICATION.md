# Meridian status emitter — ORSC-side contract verification

**Date:** 2026-09-15 · **Subject:** `meridian/status_emitter.py`, `scripts/emit_meridian_status.py`
**Contract:** `docs/project/MERIDIAN_STATUS_EMITTER_CONTRACT.md` (schema 1)
**Method:** direct calls to `build_status_event` plus one CLI run. Read-only — no database, provider, network,
credential or mutation. Probe: `artifacts/emitter-verification-2026-09-15/verify_emitter_contract.py`.

The objective recorded this as the next step once Today parity completed: the contract is asserted in the
document, so the question is whether the implementation **demonstrates** it. Both halves of that are reported
below, because a verification that only lists failures is as misleading as one that only lists passes.

## Demonstrated (the claims that hold)

| Contract claim | Result |
|---|---|
| Event identifiers are stable and deduplicable | **Holds.** Two builds from the same projection a day apart produced the identical `event_id` (`event_id` excludes observation time). |
| `observed_at` remains fresh metadata | **Holds.** The two builds carried different `observed_at` values. |
| Complete event bounded to 24,000 bytes | **Holds.** 1,216 bytes for the synthetic projection; the emitter raises rather than truncating past the bound. |
| Unparseable source degrades instead of guessing | **Holds.** `tasks = "{not json"` → `health: degraded`, `errors: ["tasks source is malformed"]`. |
| Out-of-order timestamps degrade | **Holds.** Producer newer than observation → `health: degraded` with a bounded reason. |
| Rejects credential-shaped input | **Holds.** A coordination document containing `token = abc123` raised `StatusEmitterError`; nothing was emitted. |
| CLI produces one canonical event | **Holds.** Exit 0, single sorted-key JSON object, `health: observed` on the real repository. |

## Deviations (claims the implementation does not meet)

**1. An unknown tasks `schema_version` raises instead of degrading — and this contradicts the contract's own
rule.** The contract states: *"Missing, malformed, stale, conflicting, or out-of-order data produces
`health: degraded`, explicit unknowns, and bounded errors; the emitter never guesses success."* Fed
`schema_version: 2`, the emitter raises `StatusEmitterError: unknown or malformed tasks version` instead of
producing a degraded event. `_tasks` catches `JSONDecodeError` and `TypeError` but re-raises its own
`StatusEmitterError` (`except StatusEmitterError: raise`), so the version check escapes the degradation path.

This is the forward-compatibility case, which is the one that matters most for a contract intended to evolve:
the grammar most likely to arrive from a future source is exactly what currently aborts the producer rather than
degrading it. Unambiguous contract violation, bounded fix.

**2. `queues.claims` and `queues.ready` are always empty.** Contract source precedence #3: *"`AGENT_COORDINATION.md`
establishes bounded claims/queues."* The implementation passes that document through `_source_text` for safety
checking only and hardcodes `{"claims": [], "ready": []}`. A populated claims table therefore produces an event
asserting there are none — the emitter reports absence of evidence as evidence of absence, which is the failure
mode this project treats as its most serious.

**3. `workflow.phase` and `tracks` are constants.** Contract source precedence #5: *"`MERIDIAN_ROADMAP.md` and
`MERIDIAN_DECISIONS.md` establish phase, tracks, gates, and constraints."* In the implementation `phase` is the
literal `"IMPLEMENT"`, `tracks` is the literal `{"D": "active", "I": "active", "C": "active"}`, and
`release_gate.status` is the literal `"not_released"`. None is derived from the sources the contract names, so a
roadmap phase change could not surface through this event.

## Scope note

Deviation 1 is a defect with a bounded fix and no design question. Deviations 2 and 3 are **scope** gaps: closing
them means parsing the coordination claims table and deriving phase/tracks/gates from the roadmap, which is real
feature work and a design decision about what the event should assert — not a bug fix. They are reported rather
than silently patched, and the round-trip stays unclaimed until the Harness side can independently validate
whatever ORSC produces.

## Standing conclusion

The safety and determinism claims on the ORSC side are **demonstrated, not merely asserted** — stable identity,
bounded size, rejection of credential-shaped input, and degradation on malformed or out-of-order data. Three
documented claims are not: unknown-schema degradation, claims/queues extraction, and phase/track derivation.
Live Harness integration remains unverified from this lane, as the contract itself states.
