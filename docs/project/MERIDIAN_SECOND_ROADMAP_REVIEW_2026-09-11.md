# Meridian: second roadmap and evidence review

## Declaration

- Author: Codex, single-agent informed review. No independent or blind review is claimed: the supplied conversation already disclosed the first roadmap.
- Review date: September 11, 2026 session date.
- Target: dependable personal daily use, followed by the broader personal economic OS. The 22 concepts are a starting inventory, not an exhaustive product specification or a promise to implement every idea.
- Baseline: ORSC `feat/meridian-implementation`, `a20702716046f2beadfd1d6c1f3801585a9beeeb`. Dirty/untracked artifacts are preserved. Source at this commit is not proof of the running deployment.
- Evidence: [S] source inspected; [T] synthetic behavior tested this review; [H] historical document/ledger claim; [P] proposed design; [U] unresolved. A section's tag applies to its recommendations unless a row overrides it.
- Owner decisions: the first roadmap's seven questions are resolved/deferred/disputed individually in section 9. No new authority or deployment approval is inferred.
- Limits: targeted source review, not exhaustive code audit; no fresh browser/live-provider acceptance, full-suite run, deployed-image inspection, credential inspection, or live database access. No application implementation or deployment.

## 1. Assessment

[P] The first roadmap is a useful inventory but should not become the ultimate implementation plan unchanged. Its central insight survives: closing a remediation ledger does not complete the product. Its completion estimates, several baseline claims, and its long serial dependency chain do not survive examination.

[S/H] There is substantial working substrate and a partially implemented Observatory. The exact remaining product scope is not measurable as a percentage: the denominator is intentionally open, and the existing ledgers count engineering slices rather than owner-accepted journeys. Neither “essentially done” nor “20–30% done” is supported by this review.

[P] Organize work by useful journeys with reusable domain contracts underneath. Deliver a trustworthy Today, then a coherent funding rehearsal, then a dependable intervention lifecycle, then evidence-driven assistance. Keep release and restoration checks attached to every release rather than making the first useful release wait for a Builder or eight agents.

## 2. What exists and what remains

| Capability | Evidence now | Remaining completion contract |
|---|---|---|
| Four-workspace app and visual foundation | [S] Templates/controllers for Today, Plan, Activity, Accounts; shared Observatory CSS is loaded | Full responsive interaction and concept-fidelity acceptance across workspaces |
| Observatory dial and evidence ticket | [S] `services/dial.py`, `dial.js`, `dial.css`, Today partial; [T] targeted dial tests pass; [H] Sep 9 handoff records two browser tests | Correct recurrence and source semantics; complete visual acceptance; consistent dates and evidence across views. Do not rebuild from zero |
| Crew read integration | [S] `live.py` calls CrewWorkSnapshotAdapter and normalized sync, then upserts bills | Snapshot-to-history publication, shared revision semantics, collection completeness and lifecycle acceptance |
| Financial observation history | [S] Hash IDs, append/load methods, actual/simulation types and read APIs exist | Normal sync wiring, canonical membership/identity, empty snapshot representation, time-relative freshness, coherent replay of planning inputs |
| Policy evaluator | [S/T] Read-only decisions for types, automatic limits and buffer; four focused tests pass | Persisted/versioned owner policy, override/expiry model, enforcement linkage. Evaluation is not authorization |
| Proactive weather | [S/T] Grouping and weather code; focused tests pass | Useful intervention lifecycle, suppression, correction feedback, rearming, source freshness, measured notification usefulness |
| Funding and scenarios | [S/T] Rules, paycheck models, forecasts and pure scenario comparisons exist | Shared dated cash events, reserve attribution, preserved anchors, cash conservation, horizon-consistent recomputation and meaningful confidence |
| Actions and Crew writes | [S/H] Durable claims, outcome handling, base-state/readback slices and 19 ledger completions | Server-owned authority, typed field preservation, per-operation outcomes, uncertain/abandoned recovery and owner-observed acceptance |
| Account/bill absence | [S/H] OS-013/014/018/019 and current live sync preserve absent records/history | Per-collection freshness and completeness proof, explicit deletion reconciliation, multi-connection scoping |
| Evidence, documents, assets, contracts, context | [S/H] Schemas, repositories, memory actions, APIs and connectors exist | One demonstrated intake → extraction → reviewed match → explanation → correction → retention/revocation journey |
| Trial/subscription assistance | [S/H] Capture, deadline, workflow, dry-run execution, reminders and escalation modules | Actual delivery/lifecycle wiring, ambiguous matches, refund/charge verification; external cancellation remains separately authorized |
| Other financial providers | [S/H] SimpleFin/LunchFlow/Splitwise normalization modules; inventory finds no active Meridian registration | Verify configuration-driven reachability when a user journey needs that provider. Do not wire all providers merely because adapters exist |
| Reproducible verification/release | [S/T] pytest and Playwright installed in `.venv311`; 45 targeted tests passed | Browser binary and isolated-app execution, enforced CI checks, exact release identity, matched database/image restore, actual served acceptance |

[H] The ledger contains 20 tasks: 19 `complete`, OS-001 `ready`. OS-002 is observations, OS-003 policy, OS-005 proactive weather: this is not a remediation-only ledger. The labels are retained as historical assertions, not promoted to full product verification. OS-001 should be reconciled against its actual deliverables rather than left ready indefinitely.

## 3. Disagreements with the first roadmap

| Claim or choice | Kind | Finding and replacement |
|---|---|---|
| “The entire Observatory UI” is unbuilt | Factual | [S] The app imports Observatory CSS and dial JS; the Today dial has substantial implementation. [H] Sep 9 handoff describes commits and browser results. Treat it as partial and finish it |
| Playwright is absent; nothing downstream can be verified | Factual/sequencing | [T] `find_spec` finds pytest and Playwright; 45 targeted tests run. [S] dev requirements pin both. Installation is not the blocker; executed isolated acceptance and enforcement are |
| Snapshot identity is unknown/missing | Factual | [S] `append_snapshot` hashes identity and `load_snapshot` reconstructs it. The gap is adequacy and integration, not absence |
| The inventory will fill every unknown | Factual | [S] It uses static import heuristics and explicitly excludes runtime. Its provider rows conflict with its own summary. Neither provider acceptance nor owner preferences can be settled by that inventory |
| Accounts ignores `data_freshness` | Factual | [S] `loadAccounts` passes it to `renderConnections`, which renders computed labels. Navigation still contains static reassuring text; a search found no controller for its profile attributes. Split the claims |
| “Design-complete” | Factual | [S] Later phases omit required module/migration/rollback/dependency fields; `8→9` is outside the eight-category taxonomy; proactive and several lifecycle concepts lack delivery slices. Treat as proposal, not execution-ready plan |
| Finish all verification infrastructure before any correctness work | Sequencing | [T] Small isolated tests already execute. [P] Add the required harness/checks within each slice; CI and restore remain release gates, not prerequisites for pure date corrections |
| Write integrity follows complete Observatory integration | Sequencing | [S] `app.py` still accepts/defaults caller provenance. [P] Address reachable authority defects before enabling affected live operations. Read-only UI work does not need to wait for every write operation |
| Simulation follows write-path completion | Sequencing | [P] A simulator with no command capabilities can ship after coherent inputs. Its independence must be tested. It need not wait for virtual-card writes |
| Release follows Builder | Sequencing/value | [P] Release useful bounded capabilities repeatedly. A dependable private daily driver does not require code generation or all eight roles |
| Seven owner decisions block all progress | Sequencing/value | [P] Most are future gates or engineering choices. Keep runtime selection and scope provisional; ask only when a concrete implementation would cross that boundary |
| Initial non-goals permanently exclude household work | Factual/value | [S] Architecture says “Non-goals for the initial slice.” [P] Preserve future household evaluation without inventing permission to integrate anyone else's data |
| Source-on-8081 can never be “deployed == tested” | Factual/design | [P] A source release can be identified by commit, dirty state, dependency/config manifest and restarted process. An immutable image is recommended for reproducibility, not the sole conceivable identity proof |
| “More conservative always wins” and owner preference comes last | Value/process | [P] Preserve binding authority constraints; do not let a reviewer invent stricter product restrictions and automatically outrank owner intent. Distinguish genuine boundaries from optional ceremony |
| An agreeing adversarial review has not happened | Method | [P] Evidence-supported agreement is valid. Forced disagreement rewards theater. Keep concrete falsification attempts and negative results; reject mandatory disagreement quotas |

[P] Delete from the merged roadmap: the unsupported completion percentage; the blanket Playwright-install blocker; the “Observatory from zero” scope; the release-after-Builder dependency; and blanket claims that all seven questions block work. Retain the source/assumption separation, isolated simulation, exact outcomes, visual capture contract and restoration requirements.

### Fresh load-bearing findings

- [S] Searching `meridian/` and `app.py` found no production caller of `record_provider_snapshot` or `append_snapshot` outside `observations.py`. APIs load history, but `live.py`/`sync.py` do not populate this store. External/manual callers remain [U]. A digital twin table is not yet a proven continuously maintained twin.
- [T] A temporary synthetic database showed that reversing otherwise identical object order changes snapshot ID; a complete observation from 2000 stores freshness as `fresh`; an empty complete snapshot produces zero records and therefore no loadable snapshot through this row-based design. These tests characterize the store, not the freshness of the running UI. Define capture identity, content identity and current freshness separately.
- [T] Dial recurrence advances January 15 semimonthly to January 30, and January 31 monthly twice to March 28. Preserve original calendar anchors and explicitly distinguish twice-monthly from 15-day intervals.
- [S] `scenarios.py` adjusts low point using `expense_change * 30` and copies other forecast fields. This is a useful pure comparison primitive, not established 7/30/90/365 event replay.
- [S] `live.py` writes normalized accounts/transactions and commitments through separate repository calls. A coherent replay boundary across all planning inputs needs design and failure-path verification; a content hash alone does not provide it.

## 4. Architecture and release model

[P] Retain a modular Flask/SQLite application. Three alternatives:

| Option | Benefit | Cost/failure mode | Choice |
|---|---|---|---|
| Extend current modules with explicit publication and command boundaries | Reuses working app, migrations, UI and tests | Hidden legacy callers; require reachability and failure tests | Start here |
| Durable event-driven modules inside the same app | Reliable alert/reminder recovery and replay | Ordering, duplicate delivery and migration complexity | Add a small durable work/outbox seam when the first alert lifecycle needs it |
| Separate intelligence service | Stronger process isolation and independent scaling | Auth, deployment, queue and version compatibility overhead | Defer until measured isolation or operational needs justify it |

[P] Target flow: one captured source → validated observation/publication → versioned current read models → deterministic calculations → UI/advisor. Historical observation and current derived state have different responsibilities. Plan replay includes commitment/schedule versions and assumptions, not only accounts and transactions.

[P] Commands: authenticated intent → typed reviewed parameters/base revision → durable authorization and claim → one submission → structured provider evidence → confirmed/unresolved receipt. The conversational advisor and Operator role propose plans; the deterministic executor alone holds financial write capability. Do not make the Operator an agent with bank tools.

[P] The first product release is done when phone and desktop users can understand current cash and its age, inspect the next obligations, save/read/restart local planning choices, rehearse changed income, and follow supported authorized interventions to an honest terminal or unresolved state. Each visible claim has evidence; unavailable capabilities are explicit. Ship only after isolated tests, responsive journey acceptance, matched restore and exact running identity checks, then owner-approved live acceptance. This is a proposed release boundary, not a demand that the owner define the entire future now.

[P] Separate maturity levels: usable daily driver → proactive assistant → evidence-based economic copilot → optional household/Builder/limited-policy experiments. Every level has its own acceptance; no universal “economic OS finished” percentage.

## 5. Delivery roadmap

[P] All rows are proposals. IDs V1–V8 identify capabilities, not fixed-duration phases. Expand only the next slice into code-level tasks. Each implemented slice follows the existing one-slice workflow; logical parallelism below is not authorization to delegate.

### V1 — An explained, trustworthy Today

- Objective/outcome: select a current amount or money event and see what it means, its source, observation age, and why information is missing. Reuse the Observatory dial and ticket.
- Dependencies: synthetic test harness for this journey; exact existing source contracts. No new external authorization.
- Modules: `live.py`, `sync.py`, `observations.py`, `repository.py`, `services/today.py`, `services/dial.py`, `api.py`, dial/Today/navigation controllers and partials.
- Migration: inspect need for a snapshot envelope/manifest and publication reference; retain old observation rows. Never rewrite history to make identity consistent.
- Boundary: read-only provider interaction; no bank execution, no fabricated funded amounts. Complete/partial and old/current remain distinct.
- Tests: one synthetic capture drives visible current data and replayable evidence; failed publication cannot expose half a revision; empty/partial/reordered captures, stale clock, unknown spend identity, keyboard selection, zero network writes.
- Rollback: retain prior schema/data and reversible UI routing; disable new publication consumer without deleting observations. Keep unavailable states honest.
- Exit: selected amount/event matches its frozen observation and linked metadata; restart preserves evidence; error and stale cases are visible at required mobile/desktop viewports.

### V2 — Plan a paycheck without counting money twice

- Objective/outcome: save a named schedule and bill details; see what the next paycheck can fund and rehearse a smaller/later deposit.
- Dependencies: identified/versioned inputs from V1 for integrated replay; pure date/allocator work can start earlier.
- Modules: `paycheck.py`, `payday.py`, `funding.py`, `funding_repo.py`, `commitments.py`, `beacon.py`, `scenarios.py`, `services/plan.py`, `services/dial.py`, Plan/payday controllers.
- Migration: occurrence IDs and reserve/payment links if current schema cannot represent them; explicit schedule revisions and source ownership. Establish additive migration from inspected current schema before coding.
- Boundary: local saves remain local; scenarios have no credentials, executor or real-state write repository. Unknown recurrence/amount does not silently become monthly/zero.
- Tests: preserved month-end and semimonthly anchors; leap/DST civil days; null versus zero; one cash pool; reserve applied once; known income included; transaction/day coverage; same occurrence dates across Plan/Today/dial; field-complete save/read/restart.
- Rollback: preserve inputs; route unavailable calculations to explicit unavailable state instead of restoring a known-wrong authoritative number. Restore matched image/DB if migration compatibility requires it.
- Exit: hand-calculated 7/30-day scenarios match all displayed totals and shortfalls; no doubled cash/reserves; saved schedule survives restart; 90/365 scenarios subsequently replay the same engine with explicit horizon uncertainty rather than multiplied averages.

### V3 — Finish an authorized intervention and keep its receipt

- Objective/outcome: review exact bill/pocket/transfer changes and see confirmed, rejected or unresolved results after reload/restart.
- Dependencies: operation-specific base-state evidence and isolated contract tests. Triage A01/A02 early; this is not downstream of every V2 feature or every UI screen.
- Modules: `app.py` action routes, `write_routing.py`, `crew_commands.py`, `crew/actions.py`, `crew/executors.py`, `crew_write_actions.py`, `mutations.py`, action/Plan/memory controllers. External connector contracts inspected separately; changes there require its applicable authorization.
- Migration: durable operation/result/readback lineage where missing, exact reviewed parameters/revisions and recovery state.
- Boundary: server establishes authority; typed validation and exact field preservation; one submission; uncertainty never implies rejection or permission to retry. Provider idempotency is recorded per operation, never assumed from a local UUID.
- Tests: tampered provenance, incomplete payload, untouched matching fields, stale approval, racing claims, accepted-but-timeout, empty response, restart during execution, durable approved/unresolved list and accessible destructive confirmation.
- Rollback: disable affected submissions while retaining receipts and read-only reconciliation; never roll back by resending.
- Exit: each supported operation has capture/contract → adapter → UI → authority → submission → readback evidence. Unknown operations remain unavailable. Live writes only under distinct explicit owner approval, one attempt each.

### V4 — Proactive help with a closed feedback loop

- Objective/outcome: deposit-late, bill-increase or upcoming-shortfall notices explain what changed, offer a useful next step, and stop repeating after dismissal/resolution.
- Dependencies: V1 evidence; V2 dated events for cashflow claims. Drafting notifications does not require V3 execution.
- Modules: `proactive.py`, `deposit_discovery.py`, `paycheck_learning.py`, `billers.py`, cancellation reminders, Today/advisor.
- Migration: durable event identity, first/last observation, suppression, snooze, resolved/reopened state, delivery attempts as needed by the chosen channel.
- Boundary: observe/explain/propose; no financial adjustments or external messages without applicable authorization. Missing source never produces reassurance.
- Tests: duplicate captures, restart, repeated event, revised evidence, false-positive correction, snooze expiry and resolved recurrence; no alert storm on reconnect.
- Rollback: disable delivery while retaining local event history and preferences.
- Exit: one complete signal lifecycle demonstrated with synthetic changes and later owner-approved acceptance. Record useful/actioned/dismissed/incorrect counts; set thresholds after a pilot, not invented numeric targets.

### V5 — Explain, investigate and recover value

- Objective/outcome: explain balance changes; match a receipt/refund; follow a subscription or warranty obligation; prepare an evidence-backed dispute/negotiation brief.
- Dependencies: V1 identity; V2 for causal money calculations; only the specific connector needed by the selected journey.
- Modules: `evidence.py`, `storage.py`, `ingest.py`, document extract/reconcile, `context.py`, `assets.py`, `contracts.py`, `memory_actions.py`, connections/intake/cancellation and memory UI.
- Migration: reviewed links, corrections, claim provenance, lifecycle states and retention metadata where missing.
- Boundary: least necessary data; account-scoped authorization/cursors/revocation. Distinguish observed changes from causal hypotheses. No sending, cancellation, dispute filing or external billing change implied by a draft.
- Tests: duplicate intake, ambiguous matches, refund split/partial/pending status, extraction failure, owner correction persistence, malicious document instructions, disconnect/revoke/retention and cross-account isolation.
- Rollback: pause ingestion and new links; retain owner records; reversal of derived links is auditable. Deletion follows approved retention rules, never rollback convenience.
- Exit: one input → reviewed evidence → useful finding → correction/closure journey per capability; full lifecycle claims require their own acceptance, not one generalized “memory complete.”

### V6 — Inspectable advisory roles and constitution

- Objective/outcome: grounded forecasts, understandable policy objections, visible disagreement and reviewable proposals using shared evidence.
- Dependencies: V1 for cited context, V2 for forecasts, V5 for investigations. V3 required only when connecting a proposal to execution.
- Modules: `meridian/ai/advisor.py`, `policy.py`, typed task/result interfaces and action integration.
- Migration: policy versions/overrides/expiry and evaluation records when persistence is introduced; advisory run provenance/usage with minimization.
- Boundary: start with existing runtime provider. Role names are responsibilities, not eight required processes. Tools are allowlisted per role, with no provider-write access. Rule evaluation, activation and execution remain distinct.
- Tests: contradictory sources, missing evidence, stale policy/base state, expiry, malicious evidence, invented citations, structured-output rejection, unavailable model and fallback; policy failure cannot grant permission.
- Rollback: disable new advisory role or evaluator integration without altering existing approvals; preserve audit trail.
- Exit: selected role improves a defined journey against deterministic fixtures and owner feedback. Policy activation waits for explicit owner-selected limits/overrides; no hidden autonomy expansion.

### V7 — Optional economic-OS expansion

- Objective/outcome: crisis planning, household rehearsal, temporary tools and sandboxed connector/UI/skill proposals when a real unmet need justifies them.
- Dependencies: crisis rehearsal uses V2; household data requires privacy/authority design; Builder uses a specific bounded proposal contract and sandbox. Not prerequisites for daily-use release.
- Modules: selected existing domain service plus narrow new crisis/household/tool adapters; decide file-level scope only after discovery.
- Migration: separate participant/scenario contexts or proposal artifacts when actually required, never speculative infrastructure first.
- Boundary: no autonomous external transfers; no household data access, live connector repair, code installation or deployment by inference. Bounded CFO authority requires a separately approved policy design and cannot weaken standing prohibitions.
- Tests: principal isolation, permission diff, budget/time limits, rollback rehearsal, malicious generated tool, sandbox escape tests appropriate to the selected sandbox, no side effects on rejection.
- Rollback: disable/revoke optional capability; preserve underlying financial records and evidence.
- Exit: one useful evaluated experiment with explicit keep/change/drop decision; installation/activation requires concrete owner review. An idea can be rejected without being a product failure.

### V8 — Release and operate each usable increment

- Objective/outcome: the tested version is the served version, with working provider configuration and a recoverable prior state.
- Dependencies: the chosen release scope passes its acceptance; not all V1–V7.
- Modules: development requirements, `.github/workflows/`, preview/deployment launcher, production config, migration/backup runbooks and acceptance harness.
- Migration: no invented schema requirement; rehearsal covers the actual release migrations and legacy import-time schema work.
- Boundary: isolated synthetic testing; no live bank fixtures in captures. Secret-store migration, production deployment and live acceptance remain owner-gated.
- Tests: gate fails on intentional check failure; browser checks run rather than skip; required viewport/theme captures are inspected; restore exact prior artifact/database into isolation and compare invariants; runtime identity/provider configuration smoke check without printing credentials.
- Rollback: restored tested artifact and matched database/config with post-restore read-only smoke; stop/start persistence alone is insufficient.
- Exit: commands/results, source and dependency identity, image digest when applicable, served identity, backup/restore evidence, limitations and owner acceptance recorded for each release.

### Dependencies and first move

[P] V1 enables reliable evidence for V2/V4/V5. V2 enables useful forecasting/simulation and crisis rehearsal. V3 shares evidence contracts but can proceed independently of visual completion. V6 consumes the specific domain contracts its selected role needs. V7 is optional. V8 gates every release. Geometry and pure calculation tests can run before integrated publication; no claim of full live correctness follows from that.

[P] **Exactly one first slice: V1.1 — publish one synthetic Crew observation through the ordinary sync path and explain its current spendable amount in the existing Today evidence ticket.** Bound it to accounts/current spendable, capture/observation identity and fresh/stale/partial/empty states. Do not add all occurrence types, all eight agents or all UI surfaces. This resolves a demonstrable integration gap, uses existing UI, exercises verification, and gives the next capability a dependable input.

[P] Before implementing V1.1, produce the bounded patch plan from `live.py`, `sync.py`, `observations.py`, the existing Today/dial/API contracts and applicable migrations. Specify transaction ownership, empty-envelope identity and failure rollback. Confirm the actual current-spend identity contract from authorized evidence; if unknown, return unavailable. Build only against isolated fixtures first. V1.1's exit is one coherent capture → persisted observation → current read model → visible explanation journey, including restart and failure cases. This is a proposed next slice, not implementation authorization or a claim it was built here.

## 6. All 22 vision concepts accounted for

[P] Classes retain the original taxonomy: 1 now; 2 later foundation; 3 read-only prototype; 4 owner policy; 5 external integration; 6 substantial privacy design; 7 speculative/deferred; 8 never autonomously implement. Multiple classes describe distinct boundaries, not an invented ninth class. Complexity is relative design judgment, not a time estimate.

| # | Concept | Class | Existing support → missing result | Value / complexity / delivery |
|---|---|---|---|---|
| 1 | Financial digital twin | 1 | Observation types/hash/read API → continuously published coherent replay | Trust every downstream result; high; V1/V2 |
| 2 | 7/30/90/365-day projections | 1,2 | Forecasts/Plan → dated replay, horizon consistency and uncertainty | Plan cash needs; high; V2 |
| 3 | Confidence, uncertainty, assumptions, provenance | 1 | Metadata/freshness → evidence on every important claim | Know when to rely on a result; medium; all slices |
| 4 | Living financial constitution | 3,4 | Basic evaluator → policy authoring, version, override, expiry and review | Inspect constraints; high; V6 |
| 5 | Policy evaluator | 1,4 | Read-only evaluator → validated plan/evidence integration | Consistent objections without granting authority; medium; V3/V6 |
| 6 | Specialized financial agents | 2,3 | Advisor → bounded responsibilities, evaluations and disagreement | Better help for defined jobs; high; V6 |
| 7 | Single constrained executor | 1 | Actions/executors → all reachable writes enforce one contract | Trust interventions; high; V3, triage early |
| 8 | Proactive weather and alerts | 1,3 | Grouping/weather → durable useful signal lifecycle | Notice actionable changes; medium; V4 |
| 9 | Balance forensics/anomaly investigation | 3 | Evidence/revisions → explained deltas and unresolved alternatives | Understand surprising changes; high; V5 |
| 10 | Continuously repaired budgets | 3,4 | Funding/commitments → proposed recalculation, diff, acceptance/undo | Keep plans usable as facts change; high; V2/V4; consequential application via V3 |
| 11 | Paycheck landing workflows | 1,3,4 | Paycheck/deposit primitives → expected/observed match, shortfall and reviewed funding | Finish the payday job; high; V2/V4/V3 |
| 12 | Scenarios/counterfactual learning | 1,3 | Pure scenario function → isolated replay and later actual-versus-projected explanation | Test choices and learn; high; V2/V5 |
| 13 | Refund/subscription lifecycle | 3,5,4 | Trials/cancellation/reimbursements → capture through verified charge/refund/closure | Recover value; high; V5; external acts separately gated |
| 14 | Bureaucracy/negotiation preparation | 3,6 | Documents/contracts → sourced draft brief and missing-evidence checklist | Reduce administrative effort; medium; V5 |
| 15 | Household resource planning | 7,6,5 | No accepted integrated journey established → participants, consent and isolated scenarios | Shared planning if wanted; high; V7 |
| 16 | Crisis-command mode | 3,4 | Forecast/commitment building blocks → essentials view and reviewed response options | Useful during income interruption; medium/high; V7 after V2 |
| 17 | Causal financial memory | 2,3,6 | Evidence links → versioned explanations distinguishing cause from correlation | Avoid relearning past choices; high; V5 |
| 18 | Temporary personalized tools | 3,7 | No complete builder journey established → bounded disposable tool proposal | Solve an actual one-off need; medium/high; V7 |
| 19 | Connector self-diagnosis | 1,3 | Health/read path → stage-specific diagnosis and recovery guidance | Restore trustworthy inputs; medium; V1/V8, repair proposal V7 |
| 20 | Sandboxed skill generation | 7,8 | No accepted installation path → testable artifact and permission diff | Optional extensibility; high; V7, never self-install |
| 21 | Proposed UI evolution | 1,3 | Existing Observatory/dial → completed accessible journeys and fidelity | Make the app enjoyable and effective; medium/high; V1 onward |
| 22 | Bounded autonomous CFO behavior | 4,6,7,8 | No authority granted → separately bounded policy case and failure design | Speculative delegation value; high; V7 decision gate, standing prohibitions retained |

### Beyond the list: a continuing product-discovery loop

[P] After each accepted capability, capture three things: what the owner could finish, where they still needed another tool/manual effort, and what useful question the app could not answer. Maintain an opportunity record with user job, evidence, existing support, smallest experiment, authority/privacy boundary and keep/change/drop result. Promote an idea to the delivery backlog only when its next experiment is bounded and testable.

[P] Candidate opportunities to validate, not automatically add: onboarding/data completeness, learning from changed plans, correction/undo across surfaces, travel or irregular-income planning, and a coherent connection recovery experience. The owner need not invent the next features alone; the AI should derive and test proposals from actual friction. Avoid turning the 22-item list into a new ceiling or an obligation to build low-value features.

## 7. Engineering finding disposition

[P] Every original group is carried forward. “Ledger-closed” below is [H], not a fresh per-operation verification. Retain regression checks; do not reopen implemented fixes merely because a stale handoff lists them.

| Findings | Disposition / owner capability |
|---|---|
| A01, A02 | V3 early authority/input boundary; source still warrants work |
| A03 | Preserve local atomic claims; V3 tests; not provider idempotency |
| A04, A15 | OS-010 claims structured outcome improvement; integrated abandoned/uncertain reconciliation remains V3 |
| A05, A06 | OS-012/017 ledger-closed portions; retain and prove per-operation V3 readback |
| A07, A09, A10 | OS-007/008/009 ledger-closed; V3 browser receipt/review regressions |
| A08 | V3 durable proposed/approved/unresolved history after reload |
| A11 | Historical execution-expiry correction claimed; validate atomic claim-time behavior in V3 |
| A12 | OS-015 ledger-closed; retain preflight checks and document residual race without provider conditional write |
| A13, A14 | V3 destructive intent and actual provider idempotency capability matrix |
| B01 | UpdateBill exists; preserve discovery, evaluate parity rather than rediscovering absence |
| B02, B03, B04 | V3 preserved patch fields/typed contracts; V2 local field preservation separately |
| B05, B06, B08, B09 | V3 identity, virtual-card path, required response proof and connector-path equivalence; unverified operation stays unavailable |
| B07 | V3 exact reviewed document/contract boundary; inspect installed connector scope before changes |
| C01 | OS-020 ledger-closed; retain absent-versus-zero tests in V1/V2 |
| C02, C04 | OS-013/018 ledger-closed portions; V1 verifies completeness, freshness and connection scope |
| C03, C05 | V3 delete readback → local history; V1/V2 explicit missing/null/clear semantics |
| C06 | OS-016 ledger-closed; V1 verifies canonical sync path remains consistent |
| D01 | OS-006 ledger-closed immediate reserve correction; V2 occurrence lifecycle still necessary |
| D02–D09 | V2 shared dated inputs, preserved calendar anchors, conserved allocation, income, observed-day expense baseline, occurrence-linked reserves |
| E: conservative freshness, nav text, Accounts, stale targets, labels/times | V1/V3. Accounts binding already exists; keep regression. Preserve capture/source/sync/projection times and source identity; do not use transaction age as account freshness |
| F: session baseline, plaintext stores, evidence key storage, credential logging | Preserve session controls; V8 concrete threat/path review, remove unsafe logging; credential migration needs protected destination, backup and owner approval |
| F: card reveal/cache, CSRF/origin, proxy/redirect trust, OAuth state | V3/V8 before exposing affected writes/authentication/reveal flows; no blanket request to accept all risk |
| F: provider revoke, iCloud cursor/downtime, retention | V5 per-connector lifecycle tests and data minimization |
| F: capture catalog identifiers, headers, secret-store convergence | V8 sanitized schema-only documentation, exposure assessment without printing values, scoped header policy and protected storage plan; no automatic rotation/deletion |
| G: source/remote/runtime identity, 8080/8081, model config | V8 inspect actual intended runtime; older observations do not establish current deployment |
| G: CI, dev tools/browser skips, mutable tags/test history | V8 executed gates; dev tools exist; pin actual artifact and preserve historical results as historical |
| G: migrations/import-time schema, backup/restore, DB location | V8 isolated full-start upgrade/restore rehearsal; never infer DB location from cwd; preserve checksum/history guarantees |
| G: live served acceptance and actual provider parity | V8 release gate, then explicitly authorized owner acceptance; no automated financial writes |

## 8. Agent responsibilities without an agent bureaucracy

[P] Begin with structured functions/advisor tasks; split processes/providers only for demonstrated benefit. All roles receive minimum necessary evidence and return typed outputs with citations, assumptions, freshness and failure status. None receives banking write tools.

| Role | Inputs → result | Allowed tools / failure / trigger |
|---|---|---|
| Forecaster | Snapshot + dated plan → projection/ranges | Read/simulate; unavailable on insufficient inputs; request or changed plan |
| Guardian | Typed proposal + policy/evidence → rule objections | Read/evaluate; fail closed on missing policy/evidence; proposal |
| Skeptic | Claim/forecast + evidence → counterexamples/disagreement | Read/recompute; explicit unresolved dispute; selected high-impact result |
| Investigator | Observed delta + linked records → explanation candidates | Scoped evidence reads; never invent cause; owner request or anomaly |
| Teacher | Selected result + explanation preference → understandable explanation | Read/draft; admit unavailable facts; contextual request |
| Negotiator | Owner objective + selected documents → preparation/options | Read/draft only; no send/commit; explicit request |
| Operator | Approved-workflow context → constrained plan/status explanation | Read/propose only; deterministic executor separately enforces authority; owner action |
| Builder | Bounded unmet need + sandbox contract → diff/test/permission proposal | Isolated synthetic tools; no install/secrets/live providers; explicit scoped experiment |

[P] Record disagreements; do not settle by majority vote. Evidence disputes require source/calculation checks; value disputes return to the owner. Capture actual model/provider/usage metadata and useful-output evaluations before introducing multi-model routing.

## 9. Owner decisions and what can proceed without them

| Original question | Disposition |
|---|---|
| 1. Definition of done | Proposed staged release boundary in section 4. Owner may change priorities; safe discovery and bounded plans do not require settling the whole future |
| 2. Daily driver | Inspect actual target/version before proposing deployment. Default plan recommends immutable release identity; switching the owner's runtime is a deployment decision |
| 3. Security calibration | Do concrete exposure/path analysis and a protected migration proposal first. Do not ask owner to bless “plaintext + no CSRF” as a blanket prerequisite |
| 4. Reserve/semimonthly semantics | Calendar distinction and source field contracts are engineering evidence; verify native cadence. Owner choice is needed for genuinely ambiguous reserve carry-forward/strategy only when the implementing slice needs it |
| 5. Observatory scope | Recommend finish Today first and preserve other working screens. No need to ask all-or-nothing replacement before producing the next plan |
| 6. Retention | Needed before changing retention/importing new sensitive material. Existing-evidence inspection and synthetic design can proceed. Do not assume permission to retain/delete live capture data |
| 7. Agent runtime | Inspect existing configuration, preserve it by default. No multi-model decision blocks typed role interfaces or deterministic domain work |

[U] Future concrete owner gates: deployment/real served acceptance, individually authorized financial mutations, credential changes, new external accounts/scopes, policy activation/limits, household data participation, retention changes and generated tool installation. Present the finished proposal at the relevant gate, not a speculative questionnaire now.

## 10. Comparison and merge recommendation

[P] Retain first-roadmap coverage and safety boundaries, replace its factual baseline with section 2, replace its serial spine with section 5, and make sections 6–7 mandatory coverage appendices. This is a candidate for the ultimate roadmap; owner values and the next bounded implementation plan remain reviewable rather than silently approved.

| Rubric dimension | First roadmap assessment | Proposed improvement here |
|---|---|---|
| Definition of done | Adequate proposal, overbroad blocking claim | Staged release outcomes |
| 22 concepts | Adequate inventory, taxonomy error and weak delivery mapping | All 22 mapped to work, value, boundary and relative complexity |
| A–G findings | Weak explicit closure/defer accounting | Disposition for every numbered finding and grouped E/F/G bullets |
| Sequencing | Weak unsupported serial chain | Evidence-based capability dependencies and recurring releases |
| Safety | Strong stated invariants; Operator/executor ambiguity | Separate role from deterministic executor |
| Verification | Adequate intent, stale tool assumptions | Fresh targeted results; explicit missing integration/browser/live evidence |
| Evidence discipline | Weak baseline accuracy despite tags | Distinguish source, synthetic, historical, proposal and unknown |
| Owner gates | Strong caution, unnecessary global blockers | Gate the concrete affected action |
| Non-goals | Initial exclusions overgeneralized | Initial scope versus optional future development |
| Estimability | Weak late phases; one infrastructure phase won't calibrate all work | Next-slice contract; measure domain, UI and integration work separately |
| Anti-pattern resistance | Useful rubric but forced disagreement/strictness incentives | Falsification without quotas; evidence over rhetorical confidence |

[P] Remaining planning work is explicit: V1.1's code-level transaction/migration contract; current runtime identity; comprehensive operation matrix; real source-field ambiguities; isolated browser evidence; live acceptance; per-slice estimates after comparable work is measured. Far-future V7 modules are intentionally not invented. Measure implementation effort, review/rework, blocked time and accepted outcomes; do not estimate token usage from transcript length.

## 11. Evidence and handoff

[T] At baseline above, command:

```sh
.venv311/bin/python -m pytest -q tests/meridian/test_policy.py tests/meridian/test_proactive.py tests/meridian/test_scenarios.py tests/meridian/test_dial_js.py tests/meridian/services/test_dial.py
```

Result: **45 passed in 0.42s**, exit 0. These are domain/static/Node-backed checks, not browser acceptance. A separate import-spec check confirmed pytest and Playwright packages are installed. After the owner's installation clarification and computer interruption, a fresh check confirmed the Playwright Chromium executable exists. Browser launch and application browser acceptance were not exercised by this review.

[T] A disposable synthetic SQLite observation repository and pure date helpers produced: reordered identical members change snapshot identity = true; old complete capture stored freshness = fresh; empty complete capture = zero records; semimonthly Jan 15 → Jan 30; monthly Jan 31 → Feb 28 → Mar 28. Temporary directory removed automatically. No app import, provider invocation or live DB use in these probes.

[S] Principal source anchors: `meridian/observations.py` append/load/build_simulation_input; `meridian/live.py` sync_live_crew; `meridian/sync.py`; `meridian/services/dial.py` _advance; `meridian/scenarios.py` run_scenario; `meridian/policy.py`; `app.py` api_actions_mutate; `meridian/write_routing.py`; `static/js/meridian/accounts.js` loadAccounts/renderConnections; `templates/meridian/partials/navigation.html`; `templates/meridian/index.html`; `requirements-dev.txt`; `.github/workflows/docker-image.yml`.

[H] Governing/evidence reads: ORSC AGENTS, PROJECT_INSTRUCTIONS, MERIDIAN_DECISIONS, INITIAL_BUILDER_PROMPT, OS_ARCHITECTURE, OS_ROADMAP, OS_TASKS, CURRENT_STATUS, consolidated Sep 8 handoff, Sep 9 dial handoff, substrate inventory, first vision roadmap, comparison protocol and Observatory BUILD_SPEC sections. Shared-tree brief/decisions/status/work cycle and principal audit were read for the user's current workspace context; their old defects/decisions were not imported as current ORSC requirements. No files in that shared tree were changed.

[S/H] Repository boundary reconciliation: current user context points to the shared tree, while the supplied conversation and ORSC governing decisions identify ORSC as current development destination. This review is saved only in ORSC alongside its subject documents; no cross-tree synchronization, branch switch or feature integration occurred. The shared-tree read-only recovery helper returned no ready task; its manifest validator reports 34 structurally valid tasks. That does not certify ORSC completeness.

[P] Handoff: review this candidate against the first proposal, accept/edit the next useful capability, then prepare V1.1's bounded implementation packet. Preserve prior documents as historical proposals; do not bulk mark tasks verified or start future features merely because this roadmap lists them.
