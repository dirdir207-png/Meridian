# Meridian implementation plan — all 22 concepts, all slices

**Status:** plan only. Nothing here is authorized for implementation. This completes the depth the
cross-review deliberately truncated; it does not replace `MERIDIAN_ROADMAP.md` (the trajectory) or
`MERIDIAN_EXECUTION_GAMEPLAN.md` (the execution companion). It answers one question: *how would each slice and
each of the 22 concepts actually be built?*

**Evidence notation.** `[E]` I read or ran it this pass. `[S]` source-inspected. `[R]` reported by the
cross-review and **not** reproduced by me — treat as a lead, not a fact. `[D]` design judgment. `[U]` unresolved.
Historical test claims are not re-certified.

**Baseline:** application `b053911` (R0 landed). Modules below were listed from `meridian/`, `meridian/services/`
and `templates/meridian/partials/` at that commit, so file paths are grounded rather than invented.

## 1. How I build any slice

One recipe, applied identically to all of them. R0 exists to make this enforceable rather than aspirational.

1. **Claim** exact paths in `docs/project/agent-claims.json` (machine-checked) and `AGENT_COORDINATION.md` (human
   channel).
2. **Acceptance case first** — what a user can observe, in one sentence, before any code.
3. **Red test** — the failing assertion that encodes it. Where behaviour does not change, no new test.
4. **Bounded implementation** — smallest change that turns that test green.
5. **Evidence** — `scripts/check_guardrails.py --agent builder --receipt <path>`; the receipt cites the artifact,
   never prose.
6. **Stop conditions** — two failed evidence-based fixes means stop and re-plan; an uncertain write stays
   uncertain and is never retried; a missing owner decision never becomes an implicit yes.

Two rules that govern the whole plan: **intelligence never mutates financial state** (only the constrained
executor, via propose → approve → execute → provider verification), and **missing data is never zero**.

## 2. The 22 concepts → how each would be built

Source: `MERIDIAN_INITIAL_BUILDER_PROMPT.md` §3. Class = the prompt's eight-way classification. State is my
honest reading at `b053911`.

| # | Concept | Class | Substrate at baseline | How it would be built |
|---|---|---|---|---|
1 | Financial digital twin | Foundational now | `observations.py`, `live.py`, `sync.py`, `storage.py` `[E]`; **no production caller of `append_snapshot`** `[R]` | Wire publication into the sync path: `sync.py` → `record_provider_snapshot` → `append_snapshot`, one immutable revision per sync run, current pointer via `load_snapshot`. Additive migration only if a scope/completeness column is genuinely missing. Slice **C2**. |
2 | 7/30/90/365-day projections | Foundational now | `scenarios.py`, `beacon.py`, `services/plan.py` `[E]`; projection accuracy unverified `[U]` | Projections become a pure function over the dated-event stream (C1) rather than over ad-hoc date maths, so horizon is a parameter, not four code paths. Slice **C5**. |
3 | Confidence, uncertainty, assumptions, provenance | Foundational now | `evidence.py`, `observations.py`, `timestamps.py` `[E]` | A typed envelope every advisory result carries, enforced at the boundary so an uncited claim cannot render. Slice **I1**; display in **I2**. |
4 | Living financial constitution | Requires explicit owner policy | `policy.py` exists, **no application callers** `[R]` | Version policy as data with additive migrations; every applicable command links its evaluation; activation stays owner-gated. Slice **C8**. |
5 | Policy evaluator | Requires explicit owner policy | `policy.py` `[E]`, unwired `[R]` | Wire into `write_routing.py` at the decision point, failing closed on missing evidence. Slice **C8**, after C4's typed command contract. |
6 | Specialized financial agents | Foundational later | `meridian/ai/` exists `[E]`; no role runner `[U]` | One role behind a typed envelope before any council. Slice **I1**; disagreement across roles in **I3**. |
7 | Single constrained executor | Foundational now | `crew/actions.py`, `crew/executors.py`, `meridian/write_routing.py` `[E]` | Already the architecture; the work is **completeness** — prove no path mutates outside it, and give every intervention a durable receipt. Slice **C4**. |
8 | Proactive weather and alerts | Foundational later | `proactive.py`, `meridian/billiers.py` `[E]` | One alert lifecycle (detect → explain → resolve/dismiss) with dedupe across restart and reconnect, before any delivery channel. Slice **C6**. |
9 | Balance forensics and anomaly investigation | Safe read-only prototype | `evidence.py`, `services/activity.py`, `reconcile.py` `[E]` | Read-only first: given a balance, resolve contributing events with citations. No writes, so it is a legitimate early prototype. Slice **C7** probe. |
10 | Continuously repaired budgets | Foundational now | `funding.py`, `funding_repo.py`, `commitments.py`, `services/plan.py` `[E]` | Field-complete save/read/restart with caps, zero/null handling and exact shortfalls; repair is a re-evaluation of the same function. Slice **C3**. |
11 | Paycheck landing workflows | Foundational now | `paycheck.py`, `payday.py`, `services/payday.py`, `payday-funding.html` `[E]` | One cash pool allocated across one occurrence stream, with reserve applied **once per occurrence**. Slice **C3** consumer; UI in **D2**. |
12 | Scenario simulation and counterfactual learning | Safe read-only prototype | `scenarios.py` `[E]` | Replay the event stream under modified inputs with explicit horizon assumptions and proven denial of access to actual-state writers. Slice **C5**. |
13 | Refunds and subscription lifecycle | Requires external integration | `documents/`, `connectors/`, `cancellation/`, `gmail_intake.py` `[E]` | Intake → reviewed match → explanation → correction/closure, with ambiguous-match and prompt-injection cases first. Slice **C7**, after C2. |
14 | Bureaucracy and negotiation preparation | Requires external integration | `documents/`, `context.py` `[E]` | Drafting only, from evidence the user already holds; no autonomous sending. Needs its own bounded use-case spec `[D]`. After C7. |
15 | Household resource planning | Requires substantial privacy design | none `[E]` | Multi-party data with per-party consent and isolation. Excluded until a demonstrated unmet job; then its own small spec. Slice **C9** option. |
16 | Crisis-command mode | Requires explicit owner policy | `scenarios.py` has the primitives `[E]` | A rehearsal mode over C5 that must provably not touch actual state. Slice **C9** option; spec before build. |
17 | Causal financial memory | Foundational later | `services/memory.py`, `memory_actions.py`, `context.py` `[E]` | Memory entries cite the events that caused them, so a later explanation can be checked. Depends on C2's identity. |
18 | Temporary personalized tools | Must not be autonomously implemented | none `[E]` | User-authored, sandboxed, permission-diffed, explicitly installed by the owner. Blocked on the sandbox and review gate. |
19 | Connector self-diagnosis | Safe read-only prototype | `connections.py`, `connection_jobs.py`, `services/connections.py`, `providers/` `[E]` | Classify connector failure modes read-only and report; no credential changes. Small, genuinely useful, safe early slice. |
20 | Sandboxed skill generation | Must not be autonomously implemented | none `[E]` | Artifact evaluation, permission diff, explicit owner installation. Blocked; do not prototype without the sandbox. |
21 | Proposed UI evolution | Foundational now | 12 partials `[E]`, governed capture matrix `[E]` | Layout and design matched to the concept one gap at a time, Today → Plan → Activity → Accounts → Settings. Slices **D1–D5**. |
22 | Bounded autonomous CFO behavior | Must not be autonomously implemented | none `[E]` | Only after the constitution, evidence and executor are all proven in production. Explicitly out of scope for this plan. |

**Honest read:** 8 of 22 are deliverable on the current substrate; 5 are read-only prototypes I would want to
prove before trusting; 6 need an owner policy or privacy decision; 3 must not be autonomously built at all. So
"the entirety of the 22 features" divides into *build now*, *prove read-only*, *owner-gated*, and *refuse* — and
that division is itself the most useful output of this document.

## 3. Slice plans

### C0 — one reproducible capture entry point
**Exists** `[E]`: `scripts/preview_observatory_dial.py` (isolated synthetic preview, loopback) and
`scripts/capture_meridian_matrix.py` (canonical capture, assumes login + multiple workspaces). Two private
harnesses exist in `artifacts/dial-refinement-2026-09-12/` `[E]`, one of which can replay my fixtures.
**Build** `[D]`: extend the canonical command with `--workspace`, `--fixture`, `--engine`; require a preview
**identity handshake** declaring synthetic mode, fixture hash and source identity — a loopback URL alone is not
proof of synthetic data. Import the useful behaviour from the private harness (density fixtures, error/overflow
checks, fixed clock, explicit theme) before retiring it.
**Tests**: refuse a preview whose identity is missing or wrong; 10 viewport/theme × viewport/full = 20 files; assert
zero console errors and zero horizontal overflow.
**Acceptance**: one command reproduces the matrix for a named fixture, and a second person can replay it.
**Stop**: browser failures, or an identity response that cannot be trusted without reading bank data.

### C1 — dated occurrence contract
**Exists** `[E]`: `meridian/services/dial.py` `_advance`/`_next_occurrence`, proven to drift —
`(2026-01-31, monthly)` yields **2026-03-28**, and "semimonthly" is `+15 days`, walking off the calendar.
**Build** `[D]`: new `meridian/occurrences.py` — one pure function of `(anchor, cadence, as_of)` returning a civil
date, with monthly clamping to month end, explicit two-anchor monthly vs a distinct `every_15_days` cadence, leap
years, and DST-safe civil dates. `services/dial.py`, `funding.py`, `paycheck.py`, `beacon.py`, `services/plan.py`
all consume it so one occurrence has one identity everywhere.
**Tests**: `Jan31 → Feb28 → Mar31` (not 28); leap year; two-anchor vs 15-day as *different* semantics; DST
boundary; identical IDs/dates across consumers.
**Acceptance**: the drift case returns 2026-03-31 and the dial renders the corrected date.
**Stop**: ambiguous provider cadence — preserve "unknown" rather than invent an anchor.

### C2 — observation publication (the digital twin, concept 1)
**Exists** `[E]` `observations.py` (sha256 canonical hashing, `append_snapshot`, `load_snapshot`), `live.py`,
`sync.py`. **No production caller** `[R]`, so the twin is not maintained.
**Build** `[D]`: call `record_provider_snapshot` from the sync path; one immutable revision per run plus a coherent
current revision; failure rolls back the whole run; restart replays without duplication.
**Tests**: ordinary synthetic sync publishes history + current; empty, partial and out-of-order inputs; failure
rollback; restart replay; scope and completeness proof.
**Acceptance**: after a synthetic sync, history contains exactly one new immutable revision and the current pointer
resolves to it.
**Stop**: partial publication, or a receipt that cannot name its scope.

### C3 — cash allocation (concepts 10, 11)
**Build** `[D]`: field-complete save/read/restart across `funding.py`, `funding_repo.py`, `commitments.py`,
`services/plan.py`, `paycheck.py`; caps, zero/null, distributed strategy, exact shortfall, reserve applied once per
occurrence.
**Tests**: save→read→restart equality; caps and zero/null; shortfall arithmetic; reserve not applied twice.
**Stop**: until reserve carry-forward policy is explicit — do not guess (owner decision, §5).

### C4 — executor completeness (concept 7)
**Exists** `[E]` `crew/actions.py`, `crew/executors.py` (`ExecutorSpec(execute, verifier, precondition)`),
`write_routing.py`. Legacy `move_money` handling reported outside the pipeline `[R]` — **not reproduced by me**;
`app.py:1033` registers it as an `ExecutorSpec`.
**Build** `[D]`: a reachability map from every mutation entry point to the pipeline, with severity per gap; then
per-operation receipts (tampered authority, stale base, double claim, timeout, empty result, uncertain readback,
restart). One operation at a time.
**Acceptance**: for each supported operation, a durable receipt that survives restart, and a proven answer to
"can any path mutate without approval?"
**Stop**: any unresolved write stays unresolved; never resend. This slice is the one that can *falsify* the
constitution, so it outranks cosmetic work.

### C5 — projections and scenarios (concepts 2, 12)
**Build** `[D]`: horizons as a parameter over the C1 event stream; scenario replay with explicit horizon
assumptions; a test that a scenario cannot reach an actual-state writer.
**Acceptance**: 7/30-day then 90/365-day replay with actual state byte-identical afterwards.

### C6 — proactive alert lifecycle (concept 8)
**Build** `[D]`: one alert type (late deposit **or** bill change) end-to-end — detect, explain with citations,
resolve or dismiss; dedupe across restart and reconnect; snooze. Durable event state via an additive migration if
needed. No external delivery without an approved channel.
**Stop**: at the delivery boundary.

### C7 — lifecycle and forensics (concepts 9, 13, 14)
**Build** `[D]`: read-only forensics first (given a balance, cite contributing events); then intake → reviewed
match → explanation → correction/closure for one document class. Ambiguous match, prompt injection, revocation and
retention cases explicit.
**Stop**: at any new credential or scope, external cancellation, or retention decision.

### C8 — constitution and policy (concepts 4, 5)
**Build** `[D]`: policy as versioned data (additive migration); evaluator wired at `write_routing.py`'s decision
point, failing closed on missing evidence; every applicable command links its evaluation. Activation, limits and
grants owner-gated.
**Acceptance**: overrides, expiry and missing-evidence cases all fail closed; each command can name the policy
version that allowed it.

### C9 — optional economic-OS experiments (concepts 15, 16)
**Build** `[D]`: only with its own bounded use-case spec, and only after C5 for crisis rehearsal. Household data,
installation and authority each require separate approval. **Eight-process council remains excluded.**

### D1–D5 — design fidelity (concept 21)
**Exists** `[E]`: 12 partials, governed five-viewport capture matrix, `design-qa.md` with three recorded gaps
(payday amount tight fit; Virgil/bottom-nav overlap; light-theme foregrounds unverifiable by computed ratio).
**Build** `[D]`: Today → Plan → Activity → Accounts → Settings, one visual gap at a time, each verified against the
concept at matching viewport/theme/state, with the owner's iPhone Air (420×912) inside the matrix `[E]`.
**Acceptance**: per workspace, a fresh matrix with zero overflow and a concept comparison reviewed by the owner.
**Stop**: at any material gap, and never treat a different data state as a defect.

### I1–I3 — intelligence (concepts 3, 6)
**I1** `[D]`: `meridian/ai/contracts.py` + `role_runner.py`. Typed envelope (input, evidence bundle, budget,
output with citations, assumptions, confidence, what would change the answer, unavailable state) plus per-role
permissions tested to prove no write path. Exit: **one** synthetic cited answer, not live intelligence.
**I2**: one Forecaster over C1–C3 with hand-calculated fixtures, stale/contradictory inputs and an unavailable
model; disagreement and uncertainty displayed.
**I3**: council only after I2 evaluation passes — bounded sequential deliberation, recorded disagreement, **never
majority vote**, and a typed proposal that never authorizes execution.

#### Design reference for I1: the evidence-batch gate

`[E]` Source-inspected, not installed: `kenz1117/dsh-engram` (MIT, `@kenz1117/dsh-engram` v0.7.5, 2026-09-01) implements
at the agent-runtime layer the discipline I1 needs at the financial layer. Two patterns are worth taking as
*design*, with no dependency, no Harness change and no owner gate — this is in-lane Python.

**1. Sufficiency is enforced by code, not claimed by the model.** In `src/retrieve/evidence.ts`, each search
registers a *batch* of the evidence refs citable in that output, and an assessment may only cite refs from the
same batch. `sufficient` requires the model's claim **and** at least one valid ref **and** an explicit
`nextStrategy === 'answer'` — three conditions, two of which the model cannot satisfy by asserting confidence.
Its own framing is the one to copy: *a retrieval hit means relevant, not sufficient*. Bounds are explicit
(8 refs maximum "so the whole result set cannot be treated as evidence", 20 batches per session, session-isolated,
in-process only, expiring on restart).

Applied to I1: an advisory result renders only when it cites refs from the current batch; the envelope's
confidence field is *advisory*, never the gate. This is the same rule as `H3` ("confident prose fails completion")
and concept 3.

**2. Redaction belongs at the storage boundary, and that plugin gets it half right — instructive.** It redacts
credentials on ingest (`src/security/redact.ts`: PEM blocks first so the assignment rule cannot truncate them, then
Bearer, `sk-`, GitHub, AWS, and generic `key=value` assignments, each replaced by
`[REDACTED:<kind>]` with the type preserved for later audit). But `src/store/sqlite.ts` contains **no redaction call
and no import from `security/`** — it only *observes* the marker, filtering and counting `content LIKE
'%[REDACTED:%'`. So the guarantee holds only while every writer routes through one ingest function.

That is the failure mode this project already hit: my first migration checker enforced at an entry point keyed on
HEAD drift, and a second path walked straight past it. The correct placement is inside the store's insert, so no
future caller can bypass it. Meridian's rule — enforce at the effect boundary — outranks the reference here.

**Boundary:** this is a design source, not a candidate dependency. The plugin is 11 days old, single-author, 2 stars,
18 releases in 11 days, pins all `@deepseek-ai/dsh-*` peers at `*`, ships native binaries
(`onnxruntime-node`, `sharp`, `protobufjs`), and its bundle patch **enables auto-ingest by default** where the
published default is off. Its embedder is verified local (one model download to a `0o700` cache, then offline, data
does not leave the machine). Verdict: take the thinking, not the package.

### V8 — release gates
Applied to **every** releasable capability, never a terminal phase: exact source/dependency/preset identity,
executed gates, matched restore rehearsal (owner-operated where data is real), runtime checks.

## 4. Sequence and dependency truth

`C1 → C3 → C5` and `C0 → D1–D5` are the product spine; `C4` and `C2` are the correctness spine; `I1 → I2 → I3` is
the intelligence spine. C1 and C0 can start together; C3 needs C1; C5 needs C3; I2 needs C1+C2+C3.

For each claimed dependency, what breaks if reversed: C3 before C1 ⇒ contributions and due windows land on wrong
dates, so allocation is wrong *and* looks right. C2 before C4 ⇒ perfectly recorded history of writes that may not
have been authorized. I2 before C1–C3 ⇒ a convincing explanation of inconsistent facts. D2–D5 before C0 ⇒
unreproducible visual acceptance, i.e. the rework loop this project keeps repeating.

## 5. Owner decisions that block specific slices

Reserve carry-forward (blocks C3) · semimonthly anchors where provider data is absent (blocks C1 completeness) ·
daily-driver and release identity (blocks V8 acceptance) · security calibration including the unversioned
`cookies.txt` in the parent tree (blocks any credential migration) · evidence/capture retention · single vs
multi-model runtime · and the household/crisis/autonomy decisions. None of these is needed to start C1.

## 6. What I would not do

No eight-process council · no autonomous financial mutation or transfer · no external delivery · no household
data without consent design · no self-installing tools or skills · no rewriting the roadmap (three would exist) ·
no implementation of the Harness-side items, which are a different repository and owner-gated — the in-lane
substitute (R0) is done and covers scope and evidence, though **not** the post-compaction authority hole.

## 7. Unknowns

`[U]` Whether the reported unwired callers (`move_money` outside the pipeline; policy evaluator; deposit
discovery) are real — the first needs a reachability map, not a grep. Whether the shipped-migration manifest
reflects applied reality — it was generated from working-tree hashes and no database was inspected. Projection
accuracy over 365 days. Real per-slice effort. Whether the council adds value at all.
