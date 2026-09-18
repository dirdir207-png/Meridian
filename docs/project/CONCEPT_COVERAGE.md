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
| 1 | financial digital twin | C2 | `built-unwired` | `observations.py` imported by `meridian/api.py`; **`append_snapshot`/`record_provider_snapshot` have zero callers** | — |
| 2 | 7-, 30-, 90-, and 365-day projections | C5 | `built-wired` | `scenarios`, `beacon` imported by `meridian/api.py`, `app.py`, `services/plan.py`; horizon coverage unverified `[U]` | — |
| 3 | explicit confidence, uncertainty, assumptions, and provenance | I1 | `substrate-only` | `evidence` wired for storage; **no `meridian/ai/contracts.py`** — no role envelope to carry the fields | — |
| 4 | living financial constitution | C8 | `built-unwired` | `meridian/policy.py` has no importer; versioning absent | owner policy |
| 5 | policy evaluator | C8 | `built-unwired` | confirmed: no `policy` import in `app.py`, `meridian/api.py`, `write_routing.py` | owner policy |
| 6 | specialized financial agents | I1–I3 | `substrate-only` | `meridian/ai/` present (`classifier`, `advisor` wired); no role runner, no council | — |
| 7 | a single constrained executor | C4 | `built-wired` | `actions` ← `app.py`, `write_routing.py`; `executors` ← `app.py`. Completeness unproven; `mutations` has no importer | — |
| 8 | proactive financial weather and alerts | C6 | `built-wired` | `proactive` ← `meridian/api.py`; no lifecycle/dedupe verification, no delivery channel | channel |
| 9 | balance forensics and anomaly investigation | C7 | `substrate-only` | `evidence` wired; `reconcile` ← `meridian/sync.py`; no read-only forensics surface | — |
| 10 | continuously repaired budgets | C3 | `built-wired` | `funding`, `funding_repo`, `commitments` wired; **`funding_proposals` has no importer** | reserve policy |
| 11 | paycheck landing workflows | C3 / D2 | `built-wired` | `paycheck`, `payday`, `services/payday` wired; `payday-funding.html` 2675B with **no JS** | — |
| 12 | scenario simulation and counterfactual learning | C5 | `built-wired` | `scenarios` ← `meridian/api.py`; no proof of actual-state isolation | — |
| 13 | refunds and subscription lifecycle management | C7 | `built-wired` | `meridian/cancellation/` 15 modules, 9 endpoints, 19 passing tests; UI 484B partial + 969B JS | retention, credentials |
| 14 | bureaucracy and negotiation preparation | C7 | `built-wired` | `brief`, `escalation` ← `meridian/api.py`; **no UI surface at all**; `context` has no importer | — |
| 15 | household resource planning | C9 | `not-started` | no module | consent design |
| 16 | crisis-command mode | C9 | `not-started` | no module; C5 primitives would be the basis | owner policy |
| 17 | causal financial memory | C2 / C7 | `substrate-only` | `memory_actions`, `services/memory` wired; `context` has no importer | — |
| 18 | temporary personalized tools | C9 | `gated` | no module. Permitted to develop under `D-007`; needs sandbox, permission diff, lifetime | permission set |
| 19 | connector self-diagnosis | C2 / V8 | `built-wired` | `connections`, `connection_jobs` ← `meridian/api.py`; no failure-mode classification verified | — |
| 20 | sandboxed skill generation | C9 | `gated` | no module. Permitted under `D-007`; runtime enforcement is Harness-side and unowned | permission set |
| 21 | proposed UI evolution | D1–D5 | `built-visible` | 12 partials, 9 with JS; `trials` (484B) and `payday-funding` (no JS) thin; 3 gaps in `design-qa.md` | owner visual acceptance |
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
