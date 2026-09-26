# Concept coverage matrix

**What this is.** Every concept from the builder prompt's product vision (`MERIDIAN_INITIAL_BUILDER_PROMPT.md`
§3), mapped to the slice that owns it and its **measured** state. The concept names below are copied from that
list and a test asserts they still match it exactly, so a concept cannot be silently dropped — deleting a row or
renaming a concept fails the suite.

**Why it exists.** This project has repeatedly lost work by conflating "the module exists" with "the app uses it",
and "the app uses it" with "the user can see it". Three live examples, all verified in this repository:

- `observations.py` is imported by the API yet **`append_snapshot` and `record_provider_snapshot` have zero
  callers outside their own module** — so the digital twin is defined and never maintained.
- `meridian/policy.py` has **no importer** in `app.py`, `meridian/api.py` or `write_routing.py` — the policy
  evaluator exists and nothing consults it. (Reported by the cross-review, confirmed here.)
- `meridian/cancellation/` is fully built — 15 modules, 9 endpoints, 19 passing tests — yet went unmentioned in
  the roadmap narrative and was reported by the owner as a forgotten dead page. It is neither forgotten nor dead;
  it is `built-wired` with a near-absent UI.

**State vocabulary** (fixed; a state outside this list fails the test):

| State | Means |
|---|---|
`not-started` | no substrate |
`substrate-only` | modules exist, nothing in the running app depends on them |
`built-unwired` | modules exist and are imported, but the code path is never invoked |
`built-wired` | reachable from the running application |
`built-visible` | a user-facing surface exists **and** renders against the design system |
`accepted` | the owner has accepted the real journey |
`gated` | deliberately blocked on an owner decision |

Evidence is `[E]` unless marked `[R]`. "Wired" claims cite the importing file; "unwired" claims cite the absence
of a caller, which was measured by scanning imports across 108 production files.

| # | Concept | Slice | State | Evidence | Gate |
|---|---|---|---|---|---|
| 1 | financial digital twin | C2 | `built-unwired` | CONFIRMED AGAIN 2026-09-25: `record_provider_snapshot` (`meridian/observations.py:185`) still has zero callers; migration 019's `financial_observations` has readers (`meridian/api.py:272,283,297`) and no writer. MEASURED 2026-09-25 in OS-123: **0 rows** (read-only `select count(*)`, the preview database; no values read), so the twin is unwired AND unpopulated — and migration 027's `ai_run_records` is likewise 0 rows because only `scripts/investigate.py`/`scripts/evaluate_roles.py` construct the store (`INTEGRATION_AUDIT_2026-09-25.md` §3.4/P4) | — |
| 2 | 7-, 30-, 90-, and 365-day projections | C5 | `built-wired` | `scenarios`, `beacon` imported by `meridian/api.py`, `app.py`, `services/plan.py`; horizon coverage unverified `[U]` | — |
| 3 | explicit confidence, uncertainty, assumptions, and provenance | I1 | `built-wired` | **FALSIFIED ROW, corrected 2026-09-25.** The envelope EXISTS: `meridian/ai/envelope.py` (typed `EnvelopeTask`/`Claim`/`EnvelopeResult`/`RunRecord`, per-role permissions, import-time refusal of any provider-write grant) and two roles run on it — Investigator (`meridian/ai/investigator.py:60`) and Skeptic (`meridian/ai/skeptic.py:72`). Rediscovered gap, from the same audit: the binding half is declared and UNWIRED — `evidence_in_scope()` has no production caller, `RolePermissions.tools` is consulted only at import, and `Budget` is enforced nowhere. Recorded as a decision owed | — |
| 4 | living financial constitution | C8 | `built-unwired` | `meridian/policy.py` has no importer; versioning absent | owner policy |
| 5 | policy evaluator | C8 | `built-unwired` | confirmed: no `policy` import in `app.py`, `meridian/api.py`, `write_routing.py` | owner policy |
| 6 | specialized financial agents | I1–I3 | `substrate-only` | **FALSIFIED ROW, corrected 2026-09-25: 2 of the 5 roadmap roles are BUILT.** Investigator (`meridian/ai/investigator.py:60`, 15 tests) and Skeptic (`meridian/ai/skeptic.py:72`, 18 tests), both on `EvidenceBoundRole`, wired through `scripts/investigate.py --council`. Forecaster, Guardian and Teacher exist ONLY as permission entries (`envelope.py:355-394`) — the Forecaster's single propose-tool points at `meridian/funding_proposals.py:22`, which ALREADY EXISTS. Jev is not built and is on hold (`MERIDIAN_ROADMAP.md:310-311`). Virgil has a prompt and live routes but no permissions entry, no run record and no citation validation | — |
| 7 | a single constrained executor | C4 | `built-wired` | **2026-09-25: completeness FAILS.** The pipeline is real — 17 registered types, 16 with readback verifiers, `retry_allowed: False` on every failure path — but a SECOND write surface in `app.py` bypasses it: direct Crew GraphQL with live credentials, no router, no proposal, no readback, no retry guard, reachable from shipped UI (`static/js/ui/modals.js:152,289,306,416`), guarded only by `@login_required`. See D-031 and `CREW_CAPABILITY_MATRIX.md`. Also: `POST /api/actions/mutate` defaults provenance to `owner_direct`, and `top_up_crew_reserve` is the one registered action with no verifier | owner decision, `OS-119` |
| 8 | proactive financial weather and alerts | C6 | `built-wired` | `proactive` ← `meridian/api.py`; no lifecycle/dedupe verification. **CORRECTED 2026-09-25 (OS-123): a delivery channel EXISTS** — the advisor panel renders the weather's events and explanations (`static/js/ui/advisor_fab.js:263-291`, `/api/meridian/weather` ← `meridian/api.py:927`), so this row's "no delivery channel" was stale. What does not exist is any FEEDBACK path — no table, route, field or control lets the owner say an alert was useful or wrong (exact search, `INTEGRATION_AUDIT_2026-09-25.md` §3.5/S6). The state is left at `built-wired` rather than raised to `built-visible` because this audit captured workspaces, not the Virgil panel state; raising it needs that capture | channel |
| 9 | balance forensics and anomaly investigation | C7 | `substrate-only` | `evidence` wired; `reconcile` ← `meridian/sync.py`; no read-only forensics surface | — |
| 10 | continuously repaired budgets | C3 | `built-wired` | **2026-09-25:** commitments, `funded_amount`, reserve observations and the 031 dated per-bill allocation history all persist and are verified by readback on the write path. The REPAIR path itself — re-evaluating a budget and acting on the difference — is unaudited and unassigned | — |
| 11 | paycheck landing workflows | C3 | `built-wired` | **2026-09-25:** `meridian/services/payday.py` plus `crew_funding_plans` (three rows observed: two absent, one live) with a BIDIRECTIONAL write path — `create/update/delete_paycheck_funding_plan` all registered with readback verifiers (`CWA:674,678,682`) — and the deployed refresh loop persists them (`meridian/live.py:100-117`). The unification of payday with funding is `OS-104` | — |
| 12 | scenario simulation and counterfactual learning | C5 | `built-wired` | `scenarios` ← `meridian/api.py`; no proof of actual-state isolation. **DEFECT FOUND 2026-09-25 (OS-123):** the comparison mixes two definitions of runway — the base comes from `beacon.forecast()` (`meridian/beacon.py:137`, obligations subtracted, clamped at 0) and the scenario is recomputed as `starting_cash / daily_expense` (`meridian/scenarios.py:24`), so `run_scenario(base, {})` reports **+10 days with NO changes requested** (`comparison['starting_cash']` and `['low_point']` are 0.0). The tests cannot see it: the fixture sets `1000 / 20 == 50`, where both formulas agree (`tests/meridian/test_scenarios.py:8-24`). `INTEGRATION_AUDIT_2026-09-25.md` §3.5/S7 | — |
| 13 | refunds and subscription lifecycle management | C7 | `built-wired` | `meridian/cancellation/` 15 modules, 9 endpoints, 19 passing tests; UI 484B partial + 969B JS | retention, credentials |
| 14 | bureaucracy and negotiation preparation | C7 | `built-wired` | `brief`, `escalation` ← `meridian/api.py`; **no UI surface at all**; `context` has no importer | — |
| 15 | household resource planning | C9 | `not-started` | no module | consent design |
| 16 | crisis-command mode | C9 | `not-started` | no module; C5 primitives would be the basis | owner policy |
| 17 | causal financial memory | C2 / C7 | `substrate-only` | `memory_actions`, `services/memory` wired; `context` has no importer | — |
| 18 | temporary personalized tools | C9 | `gated` | no module. Permitted to develop under `D-007`; needs sandbox, permission diff, lifetime | permission set |
| 19 | connector self-diagnosis | C2 / V8 | `built-wired` | `connections`, `connection_jobs` ← `meridian/api.py`; no failure-mode classification verified | — |
| 20 | sandboxed skill generation | C9 | `gated` | no module. Permitted under `D-007`; runtime enforcement is Harness-side and unowned | permission set |
| 21 | proposed UI evolution | D1–D5 | `built-visible` | 12 partials, 9 with JS; `trials` (484B) and `payday-funding` (no JS) thin; 3 gaps in `design-qa.md`. **OS-123, 2026-09-25:** the Today forecast chart cannot render — its `[data-forecast*]` markup was deleted in `c1d627f` (10 lines removed, 0 added, never re-added) while its guard, 11 CSS rules and a browser assertion remain — and the whole legacy front end (22 JS modules, the only service-worker registration, the only Web Push path) is reachable only through the unlinked `/debug` (`INTEGRATION_AUDIT_2026-09-25.md` §3.2/T1, T2) | owner visual acceptance |
| 22 | bounded autonomous CFO behavior | C9 | `gated` | no module. Constraint questions collected in `CFO_MANDATE_QUESTIONS.md` | authority design |

## How to read this

Three states are the ones that mislead, and each has a live example above:

- **`built-unwired` (#1, #4, #5)** — looks finished in a file listing, does nothing. Concepts 4 and 5 are the
  constitution and its evaluator: the machinery of bounded authority exists and no code path consults it.
- **`built-wired` but not `built-visible` (#13, #14)** — reachable and tested, invisible to the user. Concept 14
  has no UI at all; concept 13 has a 969-byte text dump with the intended `.m-trial-row` component orphaned in CSS.
- **`gated` (#18, #20, #22)** — not blocked in principle. `D-007` permits autonomous development with owner
  approval of the permission set; the gate is the permission set and lifetime, not permission to exist.

## Keeping this honest

Each row is falsifiable: a `built-wired` claim names the importing file, an `unwired` claim names the absent
caller, and both were measured by scanning imports across production files rather than inferred from the presence
of a module. When a slice lands, its row changes state in the same commit — a row that moves to `built-visible` or
`accepted` must cite the artifact that proves it, and `accepted` requires the owner's acceptance, never an agent's
assertion.

---

## Roadmap carriers — measured 2026-09-25

This matrix answers *which slice owns a concept*. The owner asked a different question — whether the trajectory
itself still carries the concepts — and the answer is **no, not all of them**. Read against
`MERIDIAN_ROADMAP.md`: **12 carried, 3 partial, 7 absent.**

**Carried (12):** 3 (Track I.1), 4 (V6), 6 (Track I.2/I.3), 7 (V3), 8 (V4, the strongest carrier in the
document), 10 (I.5), 11 (V2), 13 (V5), 15 (V7), 16 (V7), 18 (V7), 21 (Track D).

**Partial (3):** 5 (policy appears only as constitution authority; the roadmap never names a policy evaluator),
9 (only via V5's word "investigate"; `forensics` and `anomaly` appear nowhere), 20 (only as "Builder proposals";
`skill` and `sandbox` appear nowhere).

**Absent from the roadmap entirely (7):** **1** financial digital twin, **2** projections (and `horizon`,
`365` appear nowhere), **12** scenario simulation (every `simulat*` hit is guardrail text, not a capability),
**14** bureaucracy/negotiation, **17** causal financial memory, **19** connector self-diagnosis, **22** bounded
autonomous CFO.

Two ironies worth keeping: concepts **1, 3 and 17** — the digital twin, provenance, and causal memory — are
precisely the "culpable intelligence" the owner named, and 1 and 17 have no roadmap carrier at all. And
`MERIDIAN_ROADMAP.md` uses the word "concept" 13 times, every one of them meaning a **design** concept, never a
product concept: two meanings, one word, and only one of them was in the index.

**Five concepts have no slice id anywhere** — 17, 18, 19, 20, 22 — confirmed independently by the
implementation plan's own table (`:39-60`) and by this matrix's Slice column. Concept 14 is internally
inconsistent in that plan: assigned in the slice heading (`:135`), unassigned in the table (`:53`).

**And the implementation plan itself is an orphan**: `MERIDIAN_IMPLEMENTATION_PLAN.md` is referenced by no
governing document — not `AGENTS.md`, not the handoff, not the doc index, not the roadmap — and carries no
supersession record either. Its only substantive reference is `MERIDIAN_CONCEPTS.md`.
