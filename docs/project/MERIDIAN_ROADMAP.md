# Meridian — consolidated roadmap (single trajectory)

**Status:** proposal for owner review. Grants no financial authority, approves no deployment, activates no policy.

**Supersedes** (retained as history, not re-read):
`MERIDIAN_OS_ROADMAP.md` (the ten-row table) · `MERIDIAN_VISION_ROADMAP.md` (first roadmap) ·
`MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md` (second roadmap) · and, for planning purposes,
`MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md` (the audit — its findings stay authoritative as findings).

**Provenance:** merged from two separately authored roadmaps. The second is an **informed review** of the
first - it read the first roadmap before writing - so it is *not* a blind independent sample and their
agreement is weak evidence. The execution spine, release boundary, architecture position and command contract
come from the second. The safety-boundary-per-slice discipline, non-goals, adequacy conditions and
operational-hazards section come from the first.
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

1. **One tree:** `simplecrew-latest` is canonical (the only git repo). **The parent directory must not be
   archived wholesale: the canonical project lives *inside* it** (`/Users/stephenwest/Openrouter/simplecrew-latest`).
   Identify and archive *only* duplicate material by name (parent `app.py`, `assistant.py`, `crew/`,
   `crew_broker.py`, `run_preview.py`, `data/`, `backups/`), each with a verified backup and an explicit,
   reviewed list - never a directory move. `cookies.txt` is a credential: never opened, never printed,
   relocated to secure storage or destroyed after review. *Owner approval for every destructive step.*
2. **One branch:** `feat/meridian-implementation`. Stale `test-*`/`scratch-*` remote refs listed for owner
   approval, then pruned. No new branches for experiments.
3. **One harness:** `scripts/preview_observatory_dial.py` (isolated synthetic preview) + one capture script.
   Private per-agent harnesses are retired; a harness that only its author can run is not evidence.
4. **One entry point - not one file.** An index (this document's opening block plus
   `docs/project/README.md`) links the *active authorities*: the builder prompt, `MERIDIAN_DECISIONS.md`, the
   22-concept mapping, `MERIDIAN_VISUAL_CAPTURE_SPEC.md`, this roadmap, the task ledger, the substrate
   inventory, `AGENT_COORDINATION.md` and `design-qa.md`. Superseded narratives move to
   `docs/project/archive/`. Governing requirements are **never** demoted to "history".
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

**Proposed first slice:** a small `scripts/check_guardrails.py`, limited to what can actually be enforced:
a **declared file scope** (claims manifest), **baseline hashes** for files the agent has not declared, a
**staged-diff check** (nothing staged outside the declared scope), a modified-shipped-migration check, and
**executed tests**. It must *not* try to attribute uncommitted changes to an agent - `git status` cannot
identify authorship. Keep it small: guardrail work must not become another open-ended prerequisite.

**Runtime guardrails (the build loop itself).** The agent preset is part of the guardrail surface: it decides
whether project instructions survive, what survives compaction, and which tools may write. A live instance of
this preset has produced unverified claims that nothing stopped (see §7). `CONSTITUTIONAL_BUILDER_REVIEW_2026-09-12.md`
reviews the installed preset and proposes an enforced loop - a re-entry gate before the first mutation, and
completion bound to observed evidence. Those changes are Harness-side and owner-gated, not lane-side.

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

### 3.0 The vision lives in conversations that were never recorded — close that gap as you go (owner, 2026-09-20)

The owner's correction, and it is a standing instruction: *"it has all been discussed, but in chats or with chatgpt
etc, not necessary recorded in governing docs etc, it shouldnt be forgotten."* **Much of Meridian's actual intent —
including the point of the whole product — existed only in chats, not in this repo.** That is a real failure mode,
because a lane that re-orients from the documents cannot see it: work then proceeds faithfully on the parts that
*happened* to be written down, and the parts that did not are quietly lost. Three rules:

1. **Capture at the moment of statement.** When the owner states intent, rationale or a constraint — especially one
   introduced as "as we discussed" — write it into the repo **in that turn**: the roadmap if it changes the
   trajectory, `MERIDIAN_DECISIONS.md` if it is binding, the ledger if it is work, with the durable insight in
   Memory Space as well. Do not defer it to a later cleanup; the next compaction is the deadline.
2. **Record the WHY, not just the WHAT.** The owner's own words: *"The why is important."* A decision without its
   reason gets re-litigated, misapplied, or "fixed" backwards by a later session that can only see the conclusion.
   The two errors in this lane on 2026-09-20 are the evidence: a stale rationale made the dated-occurrence drift
   look unfixed after it was fixed, and an inferred cause was recorded as fact and was false. **Quote the owner's
   wording where it carries the intent**, and mark what is a claim versus what was verified.
3. **Absence from the docs is not absence of a decision.** When the owner references prior context that is not
   written down, **treat it as authoritative and record it**, rather than re-deriving it, asking again, or
   building on a guess. Ask only if the two genuinely conflict.

This is not documentation for its own sake: it is the only mechanism by which a new session, a future lane, or a
different agent inherits the vision instead of guessing at it.

### 3.1 Advisory model recommendations

These recommendations help the owner choose a model when a governed section starts. They are **advisory**:
they do not change a session, bind an agent, modify a preset, or grant authority. Direct selection remains an
owner choice. A fallback is the next sensible manual choice, not an automatic promise.

`rotation/auto` is capacity- and failure-aware, **not task-aware**. Its current chain begins with subscription
Luna, selects the first route whose advertised context envelope fits, and escalates only on a hard failure.
When it is recommended, omit explicit reasoning effort because the alias is a dispatcher rather than a
concrete reasoning model. If a particular section needs Astra or Sol, select that model directly.

| Roadmap section | Recommended model / effort | Fallback | Why |
|---|---|---|---|
| **D — Today** | Sol / high | `rotation/auto` | Governing-concept reconciliation plus implementation judgment |
| **D — Plan** | Sol / high | `rotation/auto` | Financial presentation and interaction fidelity |
| **D — Activity** | Sol / high | `rotation/auto` | Evidence clarity across dense transaction states |
| **D — Accounts** | Sol / high | `rotation/auto` | Financial-state semantics must survive the visual pass |
| **D — Settings** | Sol / medium | `rotation/auto` | Broad but comparatively routine surface integration |
| **D — login and Virgil visual pass** | Sol / high | `rotation/auto` | Identity, authentication, mobile layout, and capability cues meet |
| **I.1 — envelope and permissions** | Astra / xhigh | Sol / high | Cross-system contract and least-authority design |
| **I.2 — one role end to end** | Sol / high | Astra / high for a blocked design review | Deep implementation with a bounded interface already established |
| **I.3 — council mechanics** | Astra / xhigh | Sol / high | Multi-role evidence, disagreement, and authority architecture |
| **I.4 — evaluation and routing evidence** | Sol / high | Astra / high for final policy review | Measurement and implementation precede any router-policy change |
| **C-V1 — trustworthy Today** | Sol / high | `rotation/auto` | Evidence, freshness, date semantics, and owner-visible behavior |
| **C-V2 — paycheck planning** | Astra / high | Sol / high | Financial-model semantics and double-counting risk |
| **C-V3 — authorized intervention** | Astra / xhigh | Sol / high | Approval, execution, readback, and uncertain-write boundaries |
| **C-V4 — proactive closed loop** | Sol / high | Astra / high for policy review | Suppression, feedback, and bounded proactivity |
| **C-V5 — explain and recover value** | Sol / high | `rotation/auto` | Evidence-heavy investigation and workflow integration |
| **C-V6 — advisory roles and constitution** | Astra / xhigh | Sol / high | Role permissions and constitutional boundaries |
| **C-V7 — optional expansion** | Sol / high | Astra / high when a new authority boundary appears | Capability-by-capability implementation under existing gates |
| **C-V8 — release gates** | Sol / high | `rotation/auto` for mechanical reruns only | Release judgment stays on a stable direct model |
| **VIRGIL-A0 — contracts and toolchain** | Astra / xhigh | Sol / high | North-star, threat model, and Meridian-Harness-iOS seams |
| **VIRGIL-A1 — read-only voice slice** | Sol / high | Astra / high for contract conflict | First end-to-end implementation on accepted contracts |
| **VIRGIL-A2 — typed device actions** | Sol / high | Astra / high for capability-boundary review | Deterministic native action implementation and validation |
| **VIRGIL-A3 — proposal bridge** | Astra / xhigh | Sol / high | Voice/model intent reaches a consequential proposal boundary |
| **VIRGIL-A4 — proactive and long-running tasks** | Astra / high | Sol / high | Cross-runtime lifecycle, privacy, expiry, and interruption behavior |
| **VIRGIL-A5 — rich client expansion** | Sol / high | Astra / high when a new authority boundary appears | Incremental client/capability delivery after the spine is proven |
| **Harness router, provider, or preset infrastructure** | Sol / high | Astra / high only for a routing-policy redesign | Infrastructure stays in `Deepseek-Harness`, outside the Meridian product lane |

Two modifiers keep the matrix economical: use Luna / medium for a truly mechanical, already-specified edit or
test/capture rerun; use `rotation/auto` for long, low-risk inspection where context capacity and fallback
continuity matter more than holding one model constant. Neither modifier applies to owner decisions, threat
models, financial semantics, authority changes, or release acceptance.

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
workspace, before any new pages or layers.

Two sources govern, in different roles. `design/observatory-drafts-2026-09-08/` is the **composition authority**
— what each workspace should look like and how its parts are placed. The **2026-09-16 Observatory asset kit**
(`static/img/meridian/observatory/kit-2026-09-16/`, specified by `docs/project/OBSERVATORY_ASSET_KIT_2026-09-16.md`
and the kit's own `README.md`) is the **implementation specification** for the supplied artwork, and it takes
precedence where it speaks: its asset roles, its measured nine-slice guidance, and its explicit corrections — such
as `bank` rather than the concept's semantically incorrect Wi-Fi reserve glyph — override the concept. Where the
older Design Atlas conflicts with a concept's layout, the concept governs.

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

**Intelligence, not prescription — one constraint that outranks the blueprint, stated by the owner (2026-09-20):**

> *"An intelligence is needed because it shouldnt be prescribed to a preordained set of variables, virgil decides
> what needs to be done based on my input and proposes action."*

This is **architectural, not aspirational**. The plan-forming layer must **reason over the actual situation** and
decide what needs doing; it must **not** be a hardcoded decision table, a closed list of recognised variables, or a
rule engine that can only act on cases somebody anticipated. Concretely that forbids: a fixed enumeration of
"things Meridian can adjust" that silently becomes the ceiling on what it can propose; a lookup that maps a
detected condition to a canned response; and any design where a situation not in the table produces nothing at
all. **Authority is unchanged:** the intelligence **decides and proposes** and never executes — the approval gate,
provider verification, provenance, the OS-056 rule (no score may ever remove an approval) and the one-way reserve
lock all still bind, and better reasoning widens no authority.

**Where deterministic work still belongs:** as **tools and checks the intelligence uses** — arithmetic, the
stipulation-satisfaction check, freshness and provenance, readback verification. Determinism is what makes those
*auditable*; it must not stand in for the decision itself. The review test for this track: *could this capability
handle a situation nobody wrote down?* If not, it is prescription wearing intelligence's name.

**The wakeful triage layer beneath it, and why the owner reached for Jev (2026-09-20).** *"Thats also why I
thought Jev might be a good addition, a cheaper underlying layer than can determine if virgil is needed at all for
a set of actions, and is cheaper to essentially be 'always awake and checking conditions' — although there might
be better machinery."* The role is a **cost** role, not an authority role: deep reasoning cannot run on every tick,
so a cheap layer watches continuously and decides **whether the expensive intelligence needs to wake at all**. That
fits the constitution's logic — and it is also the exact place a cheap layer can do harm, so the boundary is
recorded with the role:

- **Triage may decide WHEN TO SPEND; it may never decide WHAT IS SAFE TO IGNORE.** Those are different powers, and
  only the first is cheap. A layer that can decline to escalate is a **silent-loss channel** — the same objection
  the owner raised against a model veto in memory admission — and it stays safe only if escalation decisions are
  **logged, attributable and replayable**, so "what did it pass over?" is always answerable.
- **Deterministic owner-set triggers cannot be suppressed by it.** A stipulation violation, a bill exceeding its
  reserve, a shortfall, a failed verification: these escalate **because a rule says so**, whatever the cheap layer
  thinks of them. This is the OS-056 rule applied to routing — the layer may only **add** friction (raise scrutiny,
  flag, escalate to a proposal) and can never remove an approval or gate an action; "confidence >= .95 -> act" must
  never ship.
- **The honest alternative, which the owner left open ("there might be better machinery").** For *known* conditions,
  plain **deterministic checks are the always-awake layer**: free, replayable and unsuppressible. For conditions
  **nobody wrote down** — precisely where "intelligence, not prescription" needs an intelligence — a cheap model is
  the only thing that can notice. The likely shape is therefore **layered**: deterministic watchers for the known
  and the critical, a cheap model for the unmodelled, and the expensive intelligence woken only when either says so.
  Recorded as a **design direction, not a settled choice**.
- **Authorization status is unchanged:** ORSC-side JEV work is **on hold** (evaluation runs in the Harness lane), so
  this records the intended role and its boundary — not a green light to build it.

No blueprint existed for this. The risk is building a "council" as a vibe rather than an interface. Blueprint,
in order:

**I.1 - Envelope *and permissions* (the missing piece).** One typed task/result contract every role uses:
*input* - the question, an evidence bundle (references with provenance, freshness, confidence), the requester's
authority context, and a budget (time/tokens). *output* - claims each cited to evidence IDs, explicit
assumptions, a confidence, what would change the answer, and an unavailable/failed state. *run record* - model
and provider, prompt version, evidence used, timing, outcome, persisted so a proposal can be audited back to
the reasoning that produced it. **Permissions ship with the envelope, not after it:** per-role tool
restrictions, evidence scope, budgets and failure behaviour are enforced in code, with a test per role proving
it cannot reach a provider write path. No role ever receives a provider write tool.
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

**I.4 - Evaluation.** Measured usefulness on a real journey, refusal correctness when evidence is missing,
citation accuracy, cost per useful proposal. Only after that, consider multi-model routing - recording
provider/model metadata per run.

**I.5 - The owner's original ask, which everything above exists to serve (recorded 2026-09-20).** This is the
capability that motivated Meridian's AI features in the first place, in the owner's words: *"the ability to say
something like, I had to pay 500 dollars to repair my car, I can't cover this bill, look at the foreseeable
future and make any budget/bill/autopilot adjustments necessary (proposals are then generated). I may add a
stipulation like, I need at least 600 dollars free to spend each pay period, so meridian would make sure my
pocket rule is for 600 dollars to free to spend."* One capability, three parts:

1. **An unforeseen cost plus a goal is the input** — "I paid 500 for the car", "I can't cover this bill".
2. **Owner stipulations are standing constraints the plan must satisfy**, e.g. a minimum free-to-spend per pay
   period, which would set the pocket rule accordingly. These are **owner-set policy held in Meridian** (Crew has
   no equivalent) and they *bound the proposal space*. They are not a classifier, they cannot remove an approval,
   and per the OS-056 rule no score may ever become a path around one.
3. **The output is proposals** across budget, bill and autopilot settings — the "one validated plan for the
   executor" that I.3 already specifies, never applied automatically, with each change approved, executed and
   provider-verified.

**Sequencing, stated plainly so it is not attempted early:** this lands at V2/V3 planning on top of I.2 -> I.3, so
it cannot be built first. Its prerequisites and its bounds are recorded in the task ledger as **OS-063**. The
point of writing it down here is that Track I is not idle architecture: this is what it is *for*.

**And the owner frames it as ONE thing, not four (2026-09-20).** *"That's the whole point of shortfall, virgil's
brief, proposals, automation. Its why almost full feature parity was so important. This was the whole point and
vision all along."* So the shortfall machinery, Virgil's brief, the proposal engine and automation are a single
arc, not separate features:

> **detect a shortfall honestly** (evidence; no invented numbers) -> **analyse the foreseeable future** ->
> **generate proposals across every setting that can be adjusted, honouring the owner's stipulations** ->
> **owner approves** -> **execute** -> **verify against the provider** -> **automate only what the owner has
> explicitly preapproved.**

And the front door is natural language: *"I should be able to ask Virgil to analyze my financial situation and
generate proposals to make all the in app adjustments I need to see me through, with any stipulations
included."* Two consequences that change ordering rather than adding scope:

1. **Feature parity is a prerequisite, not polish.** To "make all the in-app adjustments", Meridian must be able
   to **read and adjust everything the owner can adjust in Crew** — bills, reserves, pockets, autopilot rules and
   funding settings — because **an adjustment Meridian cannot read is an adjustment it cannot propose**. That is
   why the connector readback gaps (OS-059) sit **on** this critical path rather than beside it.
2. **Virgil is the interface to this arc, not a separate project.** VIRGIL-A1/A3 are the voice-and-proposal front
   door to exactly this capability; A3 already reads "connect Virgil to the existing proposal state machine and
   approval UI", and its negative test — that speech or model output can never select direct mutation
   provenance — is the safety property the whole arc rests on.

**The proactive half — the same arc pointing outward (owner, 2026-09-20).** *"The later roadmap is where proactive
comes in: 'I noticed you had to spend an extra 500 on ____, I propose to do these things to stay solvent without
being cash starved in the meantime, and then return to steady state on this date, with your approval, I'll take
care of all of it.'"* That is **V4** (proactive help with a closed feedback loop, no alert storms) carrying the
**I.5** payload — and it adds four requirements the reactive form does not have:

1. **Meridian notices.** The trigger is an **observed deviation**, not a request — detection, not prompting.
2. **Solvency and liquidity are BOTH goals.** "Stay solvent **without being cash starved in the meantime**" makes
   the liquidity floor **integral to the plan**, not an optional nicety. A plan that rebuilds the reserve by
   starving spendable cash is not a solution; it reproduces the exact failure it was meant to prevent.
3. **The plan names a recovery date.** "Return to steady state **on this date**" — a proposal must state when
   normal resumes, because a plan with no end date is not a plan, and the owner's whole point is not being left
   with nothing again.
4. **Approval, then execution.** "With your approval, I'll take care of all of it" — one approval authorises the
   whole plan, Meridian executes it, and the receipt is honest. **Approval remains the gate**; nothing is applied
   before it and no part of the plan is exempt from it.

**Two constraints that follow from records already held:** proactivity is where **alert storms** become the live
risk, so V4's suppression/dedupe/feedback lifecycle is a **prerequisite, not a detail** — `proactive.py` is
already wired but its lifecycle is **unverified** in `docs/project/CONCEPT_COVERAGE.md`; and the detection side
must obey the OS-056 rule, so a classifier may only **add** friction. The natural front door for the proactive
offer is **VIRGIL-A4**, which the addendum gates on C-V4 plus one proven I.2 role.

**And a second trigger class, from the owner's inbox (owner, 2026-09-20).** *"Or, I saw your bill increased by 40
dollars in your email, heres what needs to be adjusted with your approval — I approve, and all adjustments occur
etc."* So the triggers are **plural**, and one of them is **inbound notification** (email or statement rather than
an observed transaction). Same shape — notice -> "here is what needs adjusting" -> one approval -> all adjustments
occur — but it carries a **trust boundary that must be designed before it is built**, and none of it is optional:

- **Read-only, least privilege, no credentials in logs.** Meridian reads notifications; it never sends, deletes or
  mutates a mailbox, and no token, cookie, OTP or message body is logged, echoed into stored evidence, or handed
  to a model as instructions.
- **Email content is EVIDENCE, NEVER INSTRUCTIONS.** A notification is untrusted input: it can be wrong, and it can
  be hostile. "Your bill increased by $40" is a **claim to verify against the bill of record**, never a value to
  apply, and never text that can direct tool use — the same rule already applied to web search results.
- **Suppression is a precondition, not a polish item.** One message per bill per cycle is not an alert stream, and
  re-reading the same message must never re-propose the same change. V4's dedupe/lifecycle is what makes that
  true, which is exactly why `proactive.py`'s unverified lifecycle blocks this.
- **Verified against the bill of record before anything moves.** Email raises a *candidate* change; Crew's readback
  is the authority; the proposal cites the observed provider value and shows it beside the claim.
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
**V8** | Release gates - applied to **every** releasable capability, never a terminal phase |

**Virgil dependency addendum:** before planning or closing C-V1, C-V3, C-V4, I.1, I.2, or any voice/iOS/
Shortcuts/Harness-client capability, read `docs/virgil/VIRGIL_ROADMAP_ADDENDUM.md` and check task-ledger gates
`VIRGIL-A0` through `VIRGIL-A5`. The key joins are A1 after trustworthy C-V1 evidence plus I.1 permissions,
A3 only at C-V3's controlled-intervention boundary, and A4 with C-V4's closed feedback loop plus one proven I.2
role. The linked north star and threat-model reconciliation own the detailed contract; this pointer does not
reprioritize the current keystone or grant implementation authority.

**Three repairs to the adopted spine:**

1. ~~**Pull the dated-occurrence math into V1**, or narrow V1's trustworthiness claim.~~ — **DONE, corrected in place 2026-09-20.** The repair was right when written and the defect was real; the claim below is kept as history because it is struck through, not deleted. Proven `[T]`: the dial's
   own recurrence engine drifts — `Jan 31 → Feb 28 → Mar 28` permanently, and "semimonthly" as `+15 days`
   walks off the calendar (`01-15 → 01-30 → 02-14 → 03-01`). V1 cannot be "trustworthy" while its dates drift,
   and every green test stays green because the preview fixture hardcodes its dates. **CORRECTED 2026-09-20: this defect is fixed, so the trust conclusion above no longer applies.** `meridian/cadence.py` now clamps to the month's real length while **preserving the anchor day**, so `Jan 31 → Feb 28 → Mar 31`, and semimonthly is the 15th plus the true month end rather than `+15 days`. The drift cases are pinned at engine level — `test_monthly_anchor_on_the_31st_returns_to_the_31st`, `test_semimonthly_is_the_15th_and_the_last_day_of_the_month`, `test_next_occurrence_does_not_snap_a_clamped_month_forward_permanently` — with 80 tests passing across cadence, funding and payday. **V1's trustworthiness claim is no longer weakened by date drift.**
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
Track I (envelope+permissions → one role → council → eval)          ┘
Track C (V1 ─► V2 ─► V3 ─► V4 ─► V5 ─► V6 ─► V7)   V8 gates apply to EVERY releasable slice
```

- **Parallel tracks are not automatically safe.** D, I and C share contracts and templates, so "different
  files" is not a lock. Use **one integrator**, give **explicit interface ownership** to one agent per shared
  contract, and make write claims **mutually exclusive**. The claims table aids communication; it is not
  exclusion.
- **The keystone** is V1/V2's dated-occurrence model: the dial, Today, Plan, Beacon and funding all read it.
  **It no longer drifts** `[E]` — corrected 2026-09-20 — because `meridian/cadence.py` clamps to the month's real
  length while preserving the anchor day, with the drift cases pinned in `tests/meridian/test_cadence.py`. What
  remains is *consuming* it consistently, not repairing it: the same anchor semantics must reach Today, Plan,
  Beacon and funding.
- **The dial is already connected to live data** `[E]` - the earlier instruction not to wire it is stale. Because
  the model no longer drifts, the priority argument that used to follow from that defect is spent; the live cost
  now is *inconsistent consumption* of the model across surfaces.
- **Next move (revised 2026-09-20):** this line used to ask for the shared dated-event model first. That was
  delivered, so the sequence starts one step later: close Track D's remainder (`OS-038` design gaps, `OS-049`
  browser baseline), then build **Track I.1** — the envelope *and its permissions*, with a test per role proving
  it cannot reach a provider write path — then one useful, evidence-backed role (I.2). In parallel, the Crew
  funding-math arc has reached its measurement phase (`OS-058`, the 2026-10-02 event) and the reserve-versus-amount
  gap display (`OS-060`) is the next product slice. The council stays high priority, with each added role proving
  its value on a real user task.
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
4. **Committed is not served.** Templates and static assets no longer need a restart (`TEMPLATES_AUTO_RELOAD` is
   set, and `static/` is served from disk), but **Python changes do** (`use_reloader = False`), and so does a
   migration that `ALTER`s a table whose record is built as `Model(**dict(row))` — which must be restarted *as part
   of shipping it*, because the running process applies the schema itself and then fails its reads: this is what
   503'd the dial on 2026-09-20. The owner restarts the preview from the Desktop launcher
   (`scripts/restart_preview.command`); the full matrix is in `docs/project/CURRENT_STATUS.md`.
5. **Verification latency.** `update_crew_bill` now shells out synchronously to `crew-readonly` (120 s timeout)
   before it can be verified.
6. **No clean-lint baseline.** ~~`ruff check .` reports **11 pre-existing errors** `[E]` — five in `scripts/`,
   two in the untracked capture harness, one in `tmp/`, plus import sorts.~~ **RE-MEASURED 2026-09-20 `[E]`:**
   `ruff check .` reports **17 errors, and every one is in scratch code** — `artifacts/**` (3 files) and `tmp/**`
   (9 files). **`meridian/`, `scripts/` and `tests/` are all clean.** So the earlier "five in `scripts/`" claim is
   stale and the conclusion changes: the tracked source already passes, and only the **untracked scratch
   directories** fail. A lint gate on the tracked tree is therefore *nearly* available today — it needs
   `artifacts/` and `tmp/` excluded (they are scratch and stay untracked by convention), not a cleanup of source.

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
without owner approval · no commercial compliance, multi-tenancy or pricing · **no payment-arrangement,
one-time-bill or budget-workaround modelling** (Crew has no single-due-date bill option, so the owner works
around it by creating or one-time-modifying bills; owner adjustments are *data*, and modelling them as features
would invent requirements the owner has explicitly disclaimed) · **no lateness or deferral modelling** (real-world
lateness is the owner's business, not the system's).

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
