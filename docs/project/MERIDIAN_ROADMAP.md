# Meridian — consolidated roadmap (single trajectory)

**Status:** proposal for owner review. Grants no financial authority, approves no deployment, activates no policy.

**Supersedes** (retained as history, not re-read):
`MERIDIAN_OS_ROADMAP.md` (the ten-row table) · `MERIDIAN_VISION_ROADMAP.md` (first roadmap) ·
`MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md` (second roadmap) · and, for planning purposes,
`MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md` (the audit — its findings stay authoritative as findings).

**Provenance:** merged from two independently produced roadmaps. The execution spine, release boundary,
architecture position and command contract come from the second roadmap. The safety-boundary-per-slice
discipline, the non-goals, the adequacy conditions and the operational-hazards section come from the first.
The merge record is §11.

**Tagging:** `[E]` evidence read in source/committed · `[D]` design judgment · `[U]` unknown pending evidence
or an owner decision · `[S]` source-inspected · `[T]` tested this pass.

---

## 0. Consolidation — one tree, one branch, one harness, one doc set

The current confusion is real and measurable `[E]`:

| Problem | Evidence |
|---|---|
**Two trees, one unversioned** | `/Users/stephenwest/Openrouter/` is a full copy of the project with **no `.git`** — a frozen snapshot (`app.py` Aug 31, 324,245 bytes vs the lane's Sep 11, 334,748 bytes). It also holds unversioned `cookies.txt` and `data/savings_data.db`. |
**Branch sprawl** | 23 remote refs, of which **18 are `test-*` / `scratch-*` / `ref-only-*` relics**. |
**Harness sprawl** | Three artifact dirs and two private preview/capture harnesses, built because each agent could not see the previous one's. |
**Doc sprawl** | `CURRENT_STATUS.md` 64 KB, the substrate inventory 54 KB, the handoff 47 KB, the second roadmap 46 KB, the first 21 KB — overlapping running narratives with no single entry point. |

**Target state:**

1. **One tree:** `simplecrew-latest` is canonical (the only git repo). The unversioned parent becomes an
   archive outside the working path. Before moving: confirm nothing unique is needed from its `data/` and
   `backups/`, and handle `cookies.txt` as a credential — never opened, never printed, moved to secure storage
   or destroyed after review. *Owner approval required for the destructive half.*
2. **One branch:** `feat/meridian-implementation`. Stale `test-*`/`scratch-*` remote refs listed for owner
   approval, then pruned. No new branches for experiments.
3. **One harness:** `scripts/preview_observatory_dial.py` (isolated synthetic preview) + one capture script.
   Private per-agent harnesses are retired; a harness that only its author can run is not evidence.
4. **One doc set:** this document (trajectory), `CURRENT_STATUS.md` (status log),
   `MERIDIAN_SUBSTRATE_INVENTORY.md` (what exists), `AGENT_COORDINATION.md` (who is doing what),
   `design-qa.md` (visual acceptance). Everything else is history.
5. **One trajectory:** the three tracks in §5.

---

## 1. Guardrails — keeping the project on track

**Binding constraints** (`AGENTS.md`, `MERIDIAN_DECISIONS.md`) — never traded for speed:

- Intelligence and authority stay separate. Agents observe, explain, simulate, forecast, investigate, teach,
  draft, test, propose. Only the constrained executor mutates financial state.
- proposal → approval → execution → **provider verification**, always. No bypass.
- Never auto-retry a financial mutation. An uncertain write stays unknown until readback.
- Never present stale as current, a forecast as fact, a simulation as a balance, or a recommendation as
  permission. **Missing data is never zero.**
- Actual, inferred and simulated values stay isolated with provenance and timestamps.
- Never expand authority as a side effect of a feature.
- **Owner-gated, permanently:** production deployment, live acceptance, credential changes, authority-policy
  activation, self-modifying installation.
- Work only in `simplecrew-latest`. Never read, copy from, or write the shared ChatGPT tree.

**Mechanical guardrails** (checkable by a machine, so they cannot quietly lapse):

| Guardrail | Check | Status |
|---|---|---|
Shipped migration is immutable | checksum/history validation in `run_migrations` | exists `[E]` |
One runner for browser/capture | browser tests require `.venv311` (playwright is dev-only) | **needs enforcing** |
No commit on a red suite | run the focused suite before commit | **manual today** |
No committing another agent's work | inspect `git status` for foreign uncommitted files before staging | **manual today** |
No whitespace/lint debt | `git diff --check`, Ruff | exists |
Simulation cannot reach real state | a test proving isolation, not a convention | **to build** |

**Proposed first slice:** one `scripts/check_guardrails.py` that fails loudly on the mechanical set above
(red suite, foreign uncommitted files, browser tests run under the wrong interpreter, a modified shipped
migration, a new private harness dir). Small, testable, and it makes §1 real instead of aspirational.

**Process guardrails:** one bounded slice at a time · test-first · never claim completion because a schema,
endpoint, button, prompt or placeholder exists · when blocked, do safe read-only, testing, documentation or
simulation work rather than guessing · never clean up artifacts without instruction.

---

## 2. Where agents communicate

Multiple agents share one lane, and the concurrent-writer hazard has already bitten twice: Astra's
uncommitted dial work sat while I committed docs, and my stale `preserved/` patch would have reverted three
commits if applied. There is no lock and no channel.

**`docs/project/AGENT_COORDINATION.md`** is the channel: a **claims table** (who is editing which files right
now) and an **append-only log** (what was done, what changed, what was handed off, what is blocked).

Rules:

1. **Claim before editing** — add a row naming the files you are about to touch.
2. **Release on commit** — remove the row when your work is committed, with the commit SHA.
3. **Never commit another agent's uncommitted files.** Check `git status` first; stage explicitly by path.
4. **Never apply a stale patch** without checking it against current `HEAD`.
5. **Handoffs state state, not intent:** what is verified, what is not, what the next agent must not assume.

---

## 3. Memory and context — what lives where

Context is not memory. Four durable tiers, each with a job:

| Tier | Holds | Rule |
|---|---|---|
**Runtime memory** (`MEMORY.md`, `USER.md`) | Hot working facts: environment traps, owner decisions, lessons | Automatic compaction; re-persist anything critical that must survive |
**Managed Documents** | Durable project knowledge, searchable by a future session | Routing description that says *when* to consult it |
**Repo docs** | Canonical, versioned truth (§0.4) | The only place a claim becomes authoritative |
**Task ledger** (`MERIDIAN_OS_TASKS.json`) | What is done, in flight, blocked | Update in the same commit as the work |

Rules: durable progress belongs in the repo, the ledger, tests and commits — **not** in conversation. After
any compaction or handover, re-read `AGENTS.md`, this document, `CURRENT_STATUS.md`, the ledger, recent
commits and the relevant source before continuing. Never assume work survived without verifying it. A
documented claim is not a verified claim: mark `[E]` only what you read or ran.

---

## 4. Release boundary (adopted from the second roadmap)

**First product release is done when** phone and desktop users can understand current cash *and its age*,
inspect the next obligations, save/read/restart local planning choices, rehearse changed income, and follow
supported authorized interventions to an honest terminal or unresolved state — with every visible claim
carrying evidence, and unavailable capabilities explicit. Ship only after isolated tests, responsive journey
acceptance, a matched restore, and exact running-identity checks, then owner-approved live acceptance.

**Maturity levels, each with its own acceptance; no universal "finished" percentage:**
usable daily driver → proactive assistant → evidence-based economic copilot → optional household / Builder /
limited-policy experiments.

---

## 5. The three tracks

### Track D — Design and layout fidelity *(high priority)*

**Goal:** match the governing concept — **layout *and* design** — as closely as possible, workspace by
workspace, before any new pages or layers. `design/observatory-drafts-2026-09-08/` is the visual authority.

Order: **Today** (`01-today`) → Plan (`02`) → Activity (`03`) → Accounts (`04`) → Settings (`05`), then
login and Virgil.

Per workspace, acceptance is: captured at all four governed viewports × both themes, side-by-side and where
possible overlay-compared against its concept, gaps listed, then owner-visible acceptance. Review order is
structure → typography → spacing → controls → decoration; **one gap at a time**, recapture after each.
Fixtures only — never live bank data for fidelity captures.

- **Immediate item `[E]`:** right-side alignment on Today.
- **Known open gaps `[E]`:** payday amount is a tight fit in the callout at mobile; the inline Virgil control
  overlaps the bottom navigation on mobile; light-theme foregrounds are unverified (a computed-ratio probe is
  *not* a valid method here — gradient and parchment backgrounds defeat it; inspect the capture).
- **Explicit:** a visual redesign never closes a correctness finding.

### Track I — Higher intelligence and the agent council *(high priority)*

No blueprint existed for this. The risk is building a "council" as a vibe rather than an interface. Blueprint,
in order:

**I.1 — The envelope (the missing piece).** One typed task/result contract every role uses:
*input* — the question, an evidence bundle (references with provenance, freshness, confidence), the requester's
authority context, and a budget (time/tokens). *output* — claims each cited to evidence IDs, explicit
assumptions, a confidence, what would change the answer, and an unavailable/failed state. *run record* — model
and provider, prompt version, evidence used, timing, outcome, persisted so a proposal can be audited back to
the reasoning that produced it. **Enforced in code: no role ever receives a provider write tool.**

**I.2 — One role, end to end.** Ship the Forecaster or Investigator first — read-only, evidence-bound,
immediately useful. Adversarial tests: hallucinated citation, missing evidence, contradictory sources,
unavailable model. Prove the envelope before adding roles.

**I.3 — Council mechanics.** Only then, multi-role deliberation on one bounded question: Forecaster proposes,
Skeptic supplies counterexamples, Guardian objects on policy/evidence, Investigator brings causal evidence,
Teacher explains. **Disagreement is recorded and shown, never settled by majority vote.** Evidence disputes
escalate to source or calculation checks; value disputes return to the owner. Output is **one validated plan**
for the executor — never a debate transcript.

**I.4 — Guardrails.** An authority matrix in code (per role: allowed tools, data scope, budget). A test per
role asserting it cannot reach a provider write path. Policy evaluation stays separate from proposal. Every
advisory result carries freshness, confidence and assumptions.

**I.5 — Evaluation.** Measured usefulness on a real journey, refusal correctness when evidence is missing,
citation accuracy, cost per useful proposal. Only after that, consider multi-model routing — recording
provider/model metadata per run.

**I.6 — Non-goals.** No bank tools for any role. No autonomous external action. No eight processes before the
envelope is proven. No majority-vote settling of financial judgment. The Operator is *not* an agent with bank
tools; the deterministic executor alone holds write capability.

### Track C — Capability spine (adopted from the second roadmap)

| Slice | Outcome |
|---|---|
**V1** | Explained, trustworthy Today — cash and its age, next obligations, evidence per claim |
**V2** | Plan a paycheck without counting the same cash twice |
**V3** | Finish an authorized intervention and get an honest receipt |
**V4** | Proactive help with a closed feedback loop (no alert storms) |
**V5** | Explain, investigate and recover value (evidence, refunds, subscriptions, warranties) |
**V6** | Inspectable advisory roles and constitution (couples to Track I) |
**V7** | Optional expansion: crisis planning, household rehearsal, temporary tools, Builder proposals |
**V8** | Release gates: executed suites, responsive journey acceptance, matched restore, exact running identity |

**Three repairs to the adopted spine:**

1. **Pull the dated-occurrence math into V1**, or narrow V1's trustworthiness claim. Proven `[T]`: the dial's
   own recurrence engine drifts — `Jan 31 → Feb 28 → Mar 28` permanently, and "semimonthly" as `+15 days`
   walks off the calendar (`01-15 → 01-30 → 02-14 → 03-01`). V1 cannot be "trustworthy" while its dates drift,
   and every green test stays green because the preview fixture hardcodes its dates.
2. **Adopt the command contract and its line:** authenticated intent → typed reviewed parameters + base
   revision → durable authorization and claim → one submission → structured provider evidence →
   confirmed/unresolved receipt. This corrects a real ambiguity in the first roadmap.
3. **Drop two flawed rubric rules** from the comparison protocol: the mandatory disagreement quota (forced
   disagreement rewards theatre) and "more conservative always wins, owner preference last" (that lets a
   reviewer invent restrictions that outrank owner intent). Documented boundaries bind; reviewer-invented
   caution does not.

---

## 6. Critical path and parallel lanes

```
Track D (Today → Plan → Activity → Accounts → Settings)   ─┐
                                                            ├─► owner-visible acceptance
Track I (envelope → one role → council → eval)            ─┘
Track C (V1 ─► V2 ─► V3 ─► V4 ─► V5 ─► V6 ─► V7 ─► V8)
```

- **Parallelism is safe** because the tracks touch different files: D is templates/CSS/JS, I is new agent
  modules, C is services and repositories. **Claim files in `AGENT_COORDINATION.md` before editing.**
- **The keystone** is V1/V2's dated-occurrence model: the dial, Today, Plan, Beacon and funding all read it,
  and it is currently drifting `[T]`.
- **Do not** wire the dial to live data before that model lands — it would inherit the defects and be rebuilt.

---

## 7. Verification strategy and operational hazards

Every slice: focused tests, Ruff, `git diff --check`, a capture where visual, evidence recorded in the ledger,
and a precise commit. Never claim completion because a schema, endpoint, button or prompt exists.

**Hazards that have already cost real time `[E]`** — both belong in every agent's working knowledge:

1. **Two runners disagree.** `uv run --with-requirements requirements.txt` cannot import playwright (dev-only)
   or see the system `crew-readonly` binary; `.venv311/bin/python` can. A browser test failing under the wrong
   runner proves nothing about the tooling.
2. **Interrupted browser runs leave orphan Chromium processes that make later runs hang.** Clear with
   `pkill -9 -f 'chromiumdev_[p]rofile'` — bracket a character so the pattern cannot match your own command line.
3. **Migration immutability.** Once any database has applied a migration file its checksum is frozen; editing
   it 503s every financial endpoint. The preview uses `/tmp/gate-preview/gate.db`. Ship a new migration.
4. **Committed ≠ served.** The preview does not reload code and dies with the harness; restarting is required
   for a change to take effect.
5. **Verification latency.** `update_crew_bill` now shells out synchronously to `crew-readonly` (120 s timeout)
   before it can be verified.

---

## 8. Owner decisions — and what proceeds without them

| Decision | Disposition |
|---|---|
Definition of done | Staged release boundary (§4) adopted. Owner may re-prioritise; safe discovery and bounded plans do not require settling the whole future. |
Daily driver | Inspect the actual target before proposing deployment. Immutable release identity recommended. |
Security calibration | Do the concrete exposure analysis first (unversioned `cookies.txt`, plaintext stores, absent CSRF) and bring a proposal; do not ask the owner to bless a blanket risk acceptance. |
Date/recurrence semantics | Calendar anchors and reserve carry-forward are genuine modelling choices with money consequences — owner input needed before V2. |
Observatory scope | Concept fidelity first, workspace by workspace; new pages after. |
Memory/evidence retention | Retention policy for evidence blobs and the capture catalog. |
Agent runtime | Single provider first; multi-model only after measured benefit. |
Consolidation | Approval needed for the destructive half of §0 (moving the unversioned tree, pruning stale refs). |

---

## 9. Non-goals

No autonomous external transfers · no automatic subscription cancellation · no self-deploying code · no live
connector repair · no agent council as eight processes · no household integrations · no policy activation
without owner approval · no commercial compliance, multi-tenancy or pricing.

---

## 10. Open unknowns

- Whether the unversioned parent holds anything unique in `data/` or `backups/` before archival.
- Effort calibration: no slice has yet been measured end to end, so all estimates remain invented.
- Whether the concept's Plan/Activity/Accounts/Settings layouts require structural changes or re-skinning.
- Whether the observation store's publication path (no production caller today `[E]`) is the natural seam for
  the agent envelope's evidence bundles.

---

## 11. Merge record

| Conflict | Options | Rule applied | Resolution |
|---|---|---|---|
Unit of progress | phases (1st) vs capabilities (2nd) | verifiability | **Capabilities V1–V8** as the spine |
Definition of done | one definition first (1st) vs staged boundary (2nd) | owner intent | **Staged boundary**; requiring the whole future up front was the weaker position |
Verification timing | Phase 0 enablers first (1st) vs attached per release (2nd) | evidence | **Attached per release** — the first roadmap's Phase 0 premise (Playwright absent) was factually wrong |
Architecture | silent (1st) vs explicit position (2nd) | evidence | **Adopt the second's** architecture and command contract |
Date math placement | Phase 1 (1st) vs V2 (2nd) | evidence | **Pull into V1** — drift is proven, and V1 claims trustworthiness |
Safety framing | per-phase boundary (1st) + precedence rules | safety | Keep per-slice boundaries; **discard** the quota and conservative-precedence rules as unsound |
Operational hazards | absent from both | evidence | **Added** — migration immutability, runners, orphans, committed≠served, latency |
