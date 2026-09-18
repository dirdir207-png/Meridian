# Meridian — Vision Roadmap (proposed)

Status: **proposal for owner review.** This does not grant financial authority, approve
deployment, or activate any policy. It is subordinate to `MERIDIAN_DECISIONS.md`,
`MERIDIAN_OS_ARCHITECTURE.md` and the governing visual authority.

Confidence is marked on every claim:

- **[E]** — evidence-based: read in source, committed, or verified in this repo.
- **[D]** — design judgment: a defensible recommendation, not a fact. Challenge it.
- **[U]** — unknown: requires the substrate inventory or an owner decision. Never assume.

Companion document: `MERIDIAN_SUBSTRATE_INVENTORY.md` (module/schema/stub/test inventory,
produced by a read-only discovery pass). Where this roadmap says **[U]**, that inventory is
the intended source of truth.

---

## 0. Why the previous roadmap was inadequate

`MERIDIAN_OS_ROADMAP.md` is a ten-row phase table with outcomes and exit evidence, but it has
no per-phase scope, no dependencies between phases, no affected modules, no test strategy, and
no acceptance definition. `MERIDIAN_OS_TASKS.json` is a real ledger, but it covers **remediation
findings only** (OS-001…OS-020). The builder prompt's deliverables — a *vision-to-system mapping*
and a *phased roadmap* — were never produced:

```
grep -rl "digital twin" docs/   →   only MERIDIAN_INITIAL_BUILDER_PROMPT.md (the request itself)
```

**[E]** So today the project has a defect ledger and no product plan. That is the gap this
document addresses.

---

## 1. Definition of done (the missing keystone)

**[U] — this is the single most important owner decision.** Without it, no phase can be called
finished, and "we failed to develop an adequate roadmap" recurs indefinitely.

Proposed definition **[D]**, for the owner to accept, edit, or reject:

> Meridian is *delivered* when the owner can, on a phone and on the desktop, (1) see actual,
> stale, inferred and simulated states as visually distinct, (2) explore upcoming obligations on
> the dial and trace any number to its calculation and source evidence, (3) run 7/30/90/365-day
> scenarios without touching real money, (4) see every proposed intervention with its exact
> parameters and recovery path, and (5) approve or reject it — with the whole of it passing
> machine verification (unit, browser, visual, migration) and a rehearsed restore.

Note what that definition deliberately excludes: autonomous transfers, autonomous cancellation,
self-deploying code, and any policy activation the owner has not personally approved.

---

## 2. Standing constraints (apply to every phase)

**[E]** From `AGENTS.md`, `MERIDIAN_DECISIONS.md`, the architecture doc and the builder prompt:

1. Intelligence and authority stay separate. Agents observe/explain/simulate/forecast/propose;
   only the constrained executor mutates financial state.
2. proposal → approval → execution → **provider verification**, always. No bypass.
3. Never auto-retry a financial mutation. Uncertain writes stay unknown until readback.
4. Never present stale as current, forecast as fact, simulation as balance, or recommendation
   as permission. Missing data is never zero.
5. Actual / inferred / simulated values stay isolated, with provenance and timestamps.
6. Never expand authority as a side effect of a feature.
7. Owner-gated, permanently: production deployment, live acceptance, credential changes,
   authority-policy activation, self-modifying installation.
8. One bounded vertical slice at a time; test-first; verify before claiming.

Every phase below carries a **safety boundary** field. If a phase cannot state one, it is not
ready to be scheduled.

---

## 3. Vision-to-system mapping (builder-prompt deliverable C)

Classification uses the builder prompt's eight categories:
`1` foundational now · `2` foundational later · `3` safe read-only prototype ·
`4` requires explicit owner policy · `5` requires external integration ·
`6` requires substantial privacy/security design · `7` speculative/deferred ·
`8` must not be autonomously implemented.

| Concept (from the prompt) | Class | Existing support **[E]** | What is missing **[E]/[D]** |
|---|---|---|---|
Financial digital twin | 1 | Immutable observation store (migration 019), normalized read model, providers | Reproducible snapshot identity; strict actual/simulated boundary **[U]** |
7/30/90/365-day projections | 1 | Plan horizons; scenario preview exists | One shared dated-occurrence model; assumption/confidence surfacing |
Explicit confidence, uncertainty, assumptions, provenance | 1 | `financial_observations` carries confidence/assumptions; action outcomes carry reasons | Not surfaced consistently in UI **[U]** |
Living financial constitution | 4 | Read-only evaluator (OS-003) | Activation, overrides, expiry, emergency behavior, review intervals — **owner-gated** |
Policy evaluator | 4 | Read-only, returns structured decision shape | Wiring decisions to the executor; blocked-action tests |
Specialized financial agents | 2 | An advisor exists | The eight roles as structured interfaces; tool/authority matrix |
Single constrained executor | 1 | **Exists** — `ActionStore` + `ExecutorSpec` + precondition (A12) + readback (A06) | Typed operation schemas; consolidated approvals |
Proactive financial weather / alerts | 1 | Weather + grouped events (OS-005) | Noise controls and freshness behaviour unverified in the UI **[U]** |
Balance forensics / anomaly investigation | 2 | Evidence store, evidence memory | The investigation surface itself — **not started [E]** |
Continuously repaired budgets | 2 | Funding rules, commitments | Repair semantics (what may be auto-adjusted, and who approves it) **[U]** |
Paycheck landing workflows | 2 | Paycheck config, payday logic **[U] depth** | End-to-end landing flow **[U]** |
Scenario simulation / counterfactual learning | 1 | Scenario preview in Plan | Isolated 7/30/90/365 with explicit assumptions; provable isolation |
Refunds / subscription lifecycle | 3→4 | Trial canceler foundation (017, 018) | Lifecycle coverage; cancellation policy is **owner-gated** |
Bureaucracy / negotiation preparation | 3 | Document intelligence, evidence | Preparation surfaces — not started |
Household resource planning | 7 | — | Deferred (explicit non-goal in the architecture doc) |
Crisis-command mode | 2 | — | Not started |
Causal financial memory | 2 | Evidence memory, memory proposals | Causal linking beyond evidence adjacency **[U]** |
Temporary personalized tools | 3 | — | Not started (Builder-adjacent) |
Connector self-diagnosis | 2 | Connection health, broker health | Diagnosis + repair proposal path (repair never autonomous) |
Sandboxed skill generation | 8→9 | — | Builder phase; installation owner-gated |
Proposed UI evolution | 1 | Full build spec + 7 references | **The entire Observatory UI** (see Phase 3) |
Bounded autonomous CFO behaviour | 4/8 | — | Needs policy + limits; never fully autonomous |

---

## 4. Phases

Each phase uses the builder prompt's required G-format. Phases 1 and 3 are the two that can run
**in parallel lanes** — that is the main scheduling insight in this document.

### Phase 0 — Verification enablers *(blocks credibility of everything after it)*

- **Objective:** make "verified" mean something machine-checkable.
- **User-visible outcome:** none directly; it is what makes every later claim honest.
- **Dependencies:** none.
- **Scope:** install/pin Playwright and the capture harness against an isolated instance;
  make the capture contract (§ visual protocol in `AGENTS.md`) runnable; add a real CI gate
  (pytest + Ruff + browser + migration checks) to the publish workflow; automate a
  backup/restore rehearsal; resolve deployed-vs-tested identity.
- **Affected modules:** `.github/workflows/*`, `run_preview*.sh`, `scripts/`, capture scripts **[U]**.
- **Migration needs:** none.
- **Safety boundary:** test/fixture data only; never live bank data for parity captures.
- **Test strategy:** the gate *is* the test — it must fail when a check fails (prove it by
  deliberately breaking one).
- **Rollback:** revert the workflow file; nothing touches runtime.
- **Exit criteria:** a deliberately broken commit is rejected by automation; a restore from a
  stopped-app backup is rehearsed and recorded; a browser capture can be produced on demand.
- **Why first:** **[E]** `CURRENT_STATUS.md` lists Playwright as gating all UI changes and
  records that the running preview is source-on-8081, not the tested artifact. Every phase below
  claims verification. Without Phase 0, "done" is an opinion.

### Phase 1 — Financial event model *(the correctness keystone)*

- **Objective:** one shared dated-occurrence model that Today, Plan, Beacon, funding and the dial
  all read from.
- **User-visible outcome:** dates stop disagreeing between views; a bill's funding need stops
  ignoring its reserve; the same cash is never spent twice.
- **Dependencies:** Phase 0 (to verify). Design decisions from the owner (§6, decision 4).
- **Scope [E]:** D02 date-string normalization at the domain boundary; D03 displayed vs computed
  due date; D04 recurring anchors in Beacon; D05 semimonthly/monthly drift; D06 one cash allocator;
  D07 paycheck argument through forecasts; D08 day-rate correctness; D09 occurrence-linked reserve
  lifecycle; plus C03 (delete ≠ reconciliation) and C05 (null schedule semantics), and the E-group
  freshness/provenance remainder (nav hard-coding, Accounts ignoring `data_freshness`, stale
  `_crew_ids` targets, source labels for local vs Crew-backed vs inferred).
- **Affected modules:** `meridian/services/{today,plan,beacon,funding,dial}.py`,
  `meridian/{funding,funding_repo,commitments}.py` **[U — confirm in inventory]**.
- **Migration needs:** likely a dated-occurrence table; **[U]** until the inventory maps the
  current schema.
- **Safety boundary:** read/model only. No new mutation authority. If a repair implies changing a
  real allocation, it stays a proposal.
- **Test strategy:** turn the handoff's synthetic reproductions (D02 `2026-09-16` at Sep-8;
  D05 `Jan31→Feb28→Mar28`; D06 same-cash reuse) into regression tests, test-first.
- **Rollback:** model changes are additive; keep the old computation behind a flag until the new
  one passes the synthetics **[D]**.
- **Exit criteria:** the handoff's D-synthetics pass; all five surfaces read one occurrence list.
- **Note:** the handoff is explicit — do **not** fix D01 by subtracting today's reserve from every
  future occurrence, and do **not** fix D02 in a renderer.

### Phase 2 — Observatory shell and visual system *(Lane B — parallel with Phase 1)*

- **Objective:** build the visual product against fixtures, claiming no live correctness.
- **User-visible outcome:** Meridian looks and feels like the Observatory.
- **Dependencies:** visual authority `design/observatory-drafts-2026-09-08/` **[E]**; Phase 0 for
  capture verification. **Not** dependent on Phase 1 — the build spec explicitly allows synthetic
  prototyping earlier ("Synthetic visual prototyping can proceed earlier without claiming live
  correctness") **[E]**.
- **Scope [E]:** tokens + shared shell; dial date geometry and state reducer as **pure functions**
  (date↔angle round trip, endpoints, N=1, same-day events, month/year/leap/DST, pointer angle
  discontinuity); SVG + HTML controls + keyboard + pointer; Today + evidence ticket; then Plan,
  Rules, Crew controls, scenario preview, Activity modes, Accounts, Settings/connections, login,
  Virgil — all on shared primitives.
- **Affected modules:** new `static/js/meridian/dial.js`, `static/css/meridian/{observatory,dial}.css`,
  decorative assets, dial + evidence-ticket partials; integrate with existing
  `{today,plan,activity,accounts,connections,shell}.js` **[E]**.
- **Migration needs:** none.
- **Safety boundary:** fixtures only; **no live mutation access from the UI layer**; never import
  server secrets into frontend.
- **Test strategy:** the dial's pure-function tests are the core; plus keyboard/pointer parity,
  focus survival, 320px label collision, reduced-motion, and "no network mutation during dial or
  scenario exploration".
- **Rollback:** new surfaces ship behind the existing shell; old surfaces remain until parity.
- **Exit criteria:** every workspace captured against its reference at 1440×900, 1024×768 (DPR 1)
  and 430×932, 390×844 (DPR 3), light and dark, with captures *inspected* — not merely produced.
- **Warning [E]:** the build spec states that the specification and PNGs alone meet **none** of the
  implemented/tested/verified/deployed gates. Mock-image dates must never become source constants.

### Phase 3 — Connect the Observatory to real read APIs

- **Objective:** replace fixtures with live reads, honestly.
- **Dependencies:** Phases 1 and 2 both substantially complete.
- **Scope:** wire read APIs through adapters; no client-side fictional fallback; render empty,
  stale, error, many-event and long-name states in every workspace.
- **Safety boundary:** read paths only.
- **Exit criteria:** no fixture data reachable in a shipped path; stale data visibly stale.

### Phase 4 — Write paths, typed validation, and exact outcome mapping

- **Objective:** the remaining write-integrity work, now demanding exact UI outcome rendering.
- **Scope [E]:** A01 (server-established execution provenance), A02 (typed operation schemas:
  money units/ranges, enum/date validation, target-relationship checks), A04/A15 (one integrated
  readback/reconciliation service for uncertain and abandoned executions), A13 (consistent
  destructive confirmation), A14 (document actual provider idempotency); B02 (bill editor silently
  defaults schedule), B03 (matching fields cleared), B04 (API vs CLI requirements disagree),
  B05 (spend-pocket identity), B06 (virtual-card wiring), B08 (empty result must not imply verified).
- **Safety boundary:** every change here must *narrow* or *clarify* authority. Typed schemas reject
  malformed operations before submission; uncertain outcomes stay unknown.
- **Exit criteria:** an operation missing a required field is rejected **before** submission with a
  useful message; a failed execution is never success-styled; an uncertain write is unresolvable
  without readback.

### Phase 5 — Simulation and scenario layer

- **Objective:** isolated 7/30/90/365-day projections with explicit assumptions and confidence.
- **Scope:** reproducible scenarios; counterfactual learning; provable isolation from real state.
- **Safety boundary:** simulation writes must be structurally incapable of reaching the real ledger
  or the executor. Prove it with a test, not a convention.
- **Exit criteria:** deterministic scenario tests; a test that demonstrates simulation cannot
  mutate actual state.

### Phase 6 — Constitution activation *(owner-gated)*

- **Objective:** policy that actually governs, inspectably.
- **Scope:** protected obligations, survival buffer, maximum automatic amount, allowed
  source/destination accounts, prohibited classes, external-transfer policy, cancellation policy,
  confirmation levels, temporary overrides, expiry, emergency behaviour, review intervals.
- **Safety boundary:** activation is owner-gated (D-005). The evaluator returns a structured
  decision and never executes.
- **Exit criteria:** every mutation carries a policy result; blocked-action tests pass; the owner
  can inspect *why* something was blocked.

### Phase 7 — Evidence, forensics, anomaly investigation

- **Objective:** trace every important number to its calculation and source evidence.
- **Safety boundary:** read-only investigation. Privacy review required before any new retention.
- **Exit criteria:** balance forensics on a real (non-synthetic) fixture reach owner-acceptable explanation.

### Phase 8 — Agents (structured roles)

- **Objective:** the eight roles (Forecaster, Guardian, Skeptic, Investigator, Teacher, Negotiator,
  Operator, Builder) behind structured interfaces.
- **Scope:** for each — responsibilities, inputs, outputs, allowed/forbidden tools, authority,
  evidence requirements, failure behaviour, sync/scheduled/event-driven. Disagreement must be
  visible and evidence-linked; the executor receives **one** validated plan, never a debate transcript.
- **Safety boundary:** no mutation authority. Operator remains the constrained executor.
- **Exit criteria:** tool/authority matrix published; adversarial tests; an agent cannot reach a
  provider write path.

### Phase 9 — Operations: consolidated approvals

- **Objective:** one place for approved interventions with idempotency, readback and receipts.
- **Exit criteria:** receipts for every intervention; an uncertain write cannot be re-submitted
  without going through reconciliation.

### Phase 10 — Builder (sandboxed proposals)

- **Objective:** proposals for skills/UI/connectors with a permission diff.
- **Safety boundary:** installation is owner-gated; nothing self-installs.
- **Exit criteria:** a proposal can be reviewed, diffed, and rejected without side effects.

### Phase 11 — Release

- **Objective:** owner-approved deployment of a specifically identified artifact.
- **Exit criteria:** tested digest pinned by digest (not mutable tag), live acceptance on real
  served behaviour, rollback rehearsal recorded, backup verified.

---

## 5. Critical path and parallel lanes

```
Phase 0 ──┬─► Phase 1 (event model) ──┬─► Phase 3 ──┬─► Phase 4 ──► Phase 5 ──► Phase 6 ──► 7 ──► 8 ──► 9 ──► 10 ──► 11
          └─► Phase 2 (Observatory) ───┘
```

- **Critical path [D]:** 0 → 1 → 3 → 4. Correctness, then connection, then write integrity.
  Everything the owner will actually touch sits downstream of these.
- **Parallelizable:** Phase 2 (visual, fixtures) alongside Phase 1; Phase 7 alongside Phase 8.
- **Sequencing judgment [D]:** build the dial's pure functions early (Phase 2) because dial
  geometry is independent of the data model, but **do not** wire it to live data until Phase 1
  lands — otherwise the dial inherits the D-section defects and gets rebuilt.

---

## 6. Owner decisions required (builder prompt deliverable J)

Only decisions that genuinely cannot be answered from the repository:

1. **Definition of done** — accept, edit, or reject §1. *Blocks every phase's exit criteria.*
2. **Daily driver** — keep source-on-8081 as the daily instance, or move to a pinned tested digest?
   *Affects Phase 0 scope and whether "deployed == tested" can ever be claimed.*
3. **Security calibration (F-group)** — is plaintext-token SQLite and the absent CSRF token an
   accepted risk for personal use, or is hardening scheduled? *(No credentials were disclosed,
   rotated or migrated by the audit; this is a policy call.)*
4. **D-section semantics** — how should a reserve carry forward across periods, and what is the
   intended meaning of semimonthly vs every-15-days? *These are money modelling choices; the
   handoff forbids guessing them in a renderer.*
5. **Observatory scope** — replace all existing surfaces, or shell-and-Today first with later
   workspaces following? *Affects Phase 2 exit criteria.*
6. **Privacy retention** — retention policy for evidence blobs and the tracked capture catalog
   that contains live-looking identifiers.
7. **Agent runtime** — single provider or multi-model? *Cost, privacy and determinism implications.*

---

## 7. Explicit non-goals (builder prompt deliverable I)

**[E]** From the architecture doc and handoff: no autonomous external transfers; no automatic
subscription cancellation; no self-deploying code; no live connector repair; no agent council;
no household integrations; no authority-policy activation without explicit owner approval. Also
out of scope per the handoff: commercial compliance, multi-tenancy, pricing, unrelated
integrations, and creating new branches or delegating merely to execute this plan.

---

## 8. What would make this roadmap *adequate* rather than merely *coherent*

This document is design-complete but evidence-incomplete. To upgrade it:

1. **Substrate inventory** — being produced at `MERIDIAN_SUBSTRATE_INVENTORY.md` **[U]**. It fills
   every `[U]` above: module states, schema map, stub/dead-code audit, test-coverage gaps.
2. **Effort calibration** — one phase (recommend Phase 0) executed and measured, then the rest
   estimated from its actuals. Estimates before that are invented.
3. **The owner decisions in §6** — five of the seven change scheduling, not just wording.

Answer to the question that prompted this document: I can produce the *structure* and the
*sequencing* now — that is what this file is — but "adequate" in the sense of *plannable and
estimable* requires the inventory and the seven decisions. Neither is a matter of more reasoning;
both are matters of evidence and owner intent.
