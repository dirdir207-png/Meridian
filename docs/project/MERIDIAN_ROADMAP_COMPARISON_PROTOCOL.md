# Meridian — roadmap comparison protocol and merge rules

Purpose: two (or more) independently produced Meridian roadmaps must be compared so the
**ultimate copy** is decided by criteria, not by which one reads better. This document is the
rubric, the conflict rules, the merge procedure, and the final structure.

Companion: `MERIDIAN_VISION_ROADMAP.md` (the first sample), `MERIDIAN_SUBSTRATE_INVENTORY.md`
(evidence source for `[U]` markers).

---

## 1. Should the second intelligence read the first one first?

This is a real methodological choice, and it changes what the comparison can prove:

| Setup | What it proves | What it cannot prove |
|---|---|---|
**Blind** — reads the governing docs but *not* `MERIDIAN_VISION_ROADMAP.md` | An independent sample: it can reveal phases, dependencies and concepts the first one **missed** | Nothing about whether the first one is *wrong*, only incomplete |
**Informed** — reads the first roadmap, then critiques or rewrites it | An adversarial review: it can falsify specific claims and sequencing | Independence — it will anchor on the first roadmap's structure |

**Recommendation: run both.** One blind (to find omissions), one informed (to stress-test
reasoning). They answer different questions; comparing a blind sample against an informed
critique is more useful than two anchors against each other.

### 1a. Blind prompt (paste as-is)

```
You are producing a roadmap for Meridian, a personal-use financial operating system in
/Users/stephenwest/Openrouter/simplecrew-latest (branch feat/meridian-implementation).

Read these governing documents first, in this order:
  AGENTS.md
  docs/project/MERIDIAN_INITIAL_BUILDER_PROMPT.md     (the mission, the 22-concept vision,
                                                       the 8-class taxonomy, the audit spec A–K)
  docs/project/MERIDIAN_OS_ARCHITECTURE.md
  docs/project/MERIDIAN_OS_ROADMAP.md
  docs/project/MERIDIAN_DECISIONS.md
  docs/project/PROJECT_INSTRUCTIONS.md
  docs/project/MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md   (findings A01–A15, B01–B09,
                                                              C01–C06, D01–D09, E, F, G)
  docs/project/CURRENT_STATUS.md
  docs/project/MERIDIAN_OS_TASKS.json
  design/observatory-drafts-2026-09-08/BUILD_SPEC.md

Do NOT read docs/project/MERIDIAN_VISION_ROADMAP.md — you are the independent sample.

Produce a roadmap with:
 1. A declaration header (see the protocol document's §2) — required, first section.
 2. A definition of done for the product as a whole, or an explicit argument that none is needed.
 3. Classification of all 22 concepts from the builder prompt into its 8 categories, with
    existing support and what is missing for each.
 4. Phases, each in this exact field-set: objective | user-visible outcome | dependencies |
    affected modules | migration needs | safety boundary | test strategy | rollback | exit criteria.
 5. Critical path, and which phases can run in parallel.
 6. Owner decisions required, with why each cannot be answered from the repository.
 7. Explicit non-goals.
 8. A statement of what would make your roadmap plannable-but-not-yet-plannable — i.e. what you
    could not determine and would need to measure.

Tag every substantive claim: [E] read in source/committed, [D] design judgment, [U] unknown.
Never guess. Do not invent capabilities that the documents forbid. Financial-safety rules in
AGENTS.md and MERIDIAN_DECISIONS.md are binding constraints, not preferences.
```

### 1b. Informed prompt (paste as-is)

```
Read docs/project/MERIDIAN_VISION_ROADMAP.md and docs/project/MERIDIAN_ROADMAP_COMPARISON_PROTOCOL.md,
plus the governing documents listed in the protocol's §1a prompt.

Your job is adversarial review, not agreement. For each of these, either falsify it with evidence
from the repository, or state why it survives:
  - the phase sequence, and especially the claim that Phase 0 (verification enablers) must precede
    all correctness and UI work;
  - the two-lane parallelisation (event model ∥ Observatory at fixture level), including the claim
    that dial geometry is data-model independent;
  - the adequacy claim that the substrate inventory and seven owner decisions are what is missing,
    rather than something else;
  - the classification of all 22 concepts;
  - every [D] judgment and every [U] marker.

Then produce your own roadmap in the same required format. Where you disagree, say which of the two
is more conservative and why. Do not restate the first roadmap as your own.
```

### 1c. The shared-ancestor problem (read this before trusting the comparison)

Both roadmaps are likely to descend from the **same ancestor**: the consolidated handoff's
"prioritized work order" (action truth -> write integrity -> sync convergence -> financial event
model -> recovery/release -> Observatory -> owner acceptance). The first roadmap's phase sequence
follows that spine. A second roadmap that also reads the handoff will very likely reproduce a
similar spine — and a comparison of two documents sharing an ancestor **confirms the ancestor
rather than testing it**. The governing documents themselves were authored by the same class of
intelligence that will now review them, so "blind to the first roadmap" is *not* the same as
"blind to the project's framing."

Consequence: agreement between the two roadmaps is weak evidence. Only disagreement is
informative, and only if the disagreement is at the level of the spine rather than the pieces.

### 1d. Third prompt — the spine skeptic (paste as-is)

Run this one in addition to 1a and 1b. It is the only variant that can change the *shape* of the
answer rather than its detail:

```
Read the governing documents listed in the protocol's §1a prompt, but NOT
docs/project/MERIDIAN_VISION_ROADMAP.md.

Your task is to attack the ancestry of the plan, not the plan itself. Specifically, treat the
consolidated handoff's "prioritized work order" as an untested hypothesis and argue against it:

 1. Should any product work at all precede remediation? Argue the case that the Observatory UI
    or the simulation layer should come before the remaining findings, including the D-section,
    and say what concretely breaks if it does.
 2. Is the D-section really the keystone? What if the actual blocker is something else the handoff
    never examined — the app.py monolith, the unwired provider adapters, the uneven evidence/
    document/context wiring, or something neither of us has looked at?
 3. Is a phase model the right structure at all for this project, or does the substrate's shape
    (legacy monolith + layered Meridian + unwired breadth) argue for a different organising
    principle, e.g. capability-completion rather than phase completion?
 4. Which of the handoff's 48 findings would you *drop* or downgrade, and why?
 5. If you could do exactly one thing first, what is it, and what does the first roadmap get wrong
    about that choice?

Then produce your own roadmap in the required format. State explicitly which of your disagreements
are factual (evidence could settle them), which are sequencing (a dependency test could settle
them), and which are value judgements only the owner can settle.
```


---

## 2. Declaration header — required from every roadmap

Without these, roadmaps cannot be compared. Any submission missing them is returned.

```
Roadmap author / model:
Date:
Target scope:        (personal-use daily driver | full vision | other, stated explicitly)
Definition of done:  (stated, or "none proposed" with reasoning)
Evidence tier:       (did it read source, or only documents? which files?)
Tagging convention:  ([E]/[D]/[U] adopted | other, described)
Answers to the seven owner decisions:  (answered | deferred | disputed — per decision 1..7)
Known gaps:          (what the author could not determine)
```

## 3. Normalised phase schema

Phases must be diffable field-by-field. A phase that omits **safety boundary** or **exit criteria**
is not schedulable and is scored as absent, not as partially complete.

```
Phase N — <name>
  objective:
  user-visible outcome:
  dependencies:            (phases, decisions, or evidence)
  affected modules:        (paths)
  migration needs:         (none | schema changes described)
  safety boundary:         (what this phase must NOT be able to do)
  test strategy:           (unit | integration | browser | visual | migration)
  rollback:
  exit criteria:           (machine-checkable where possible)
```

## 4. Coverage checklists

### 4a. All 22 concepts must appear and be classified

financial digital twin · 7/30/90/365-day projections · explicit confidence/uncertainty/assumptions/
provenance · living financial constitution · policy evaluator · specialized financial agents ·
single constrained executor · proactive financial weather and alerts · balance forensics and anomaly
investigation · continuously repaired budgets · paycheck landing workflows · scenario simulation and
counterfactual learning · refunds and subscription lifecycle management · bureaucracy and negotiation
preparation · household resource planning · crisis-command mode · causal financial memory · temporary
personalized tools · connector self-diagnosis · sandboxed skill generation · proposed UI evolution ·
bounded autonomous CFO behaviour.

| Concept | First roadmap | Second roadmap | Winner / merged form |
|---|---|---|---|
| *(one row per concept; record phase, class, and whether support is claimed correctly)* | | | |

### 4b. All findings must be accounted for

| Group | IDs | First roadmap covers | Second roadmap covers | Notes |
|---|---|---|---|---|
| A. Action authority & outcomes | A01–A15 | | | |
| B. Mutation completeness | B01–B09 | | | |
| C. Sync convergence | C01–C06 | | | |
| D. Financial event model | D01–D09 | | | |
| E. Freshness & provenance | bullets | | | |
| F. Security | bullets | | | |
| G. Deployment, tests, recovery | bullets | | | |

**Rule:** a roadmap may *defer* a finding, but it must say so explicitly. Silence is an omission.

## 5. The eleven comparison dimensions

Score each as **strong / adequate / weak / absent**, with the evidence for the score.

1. **Keystone** — does it resolve the missing definition of done, or repeat the same gap?
2. **Coverage of the 22 concepts** — all present, correctly classified?
3. **Coverage of findings A–G** — every group addressed or explicitly deferred?
4. **Sequencing soundness** — are dependencies real dependencies, or asserted? *Test it: for each
   claimed dependency, ask what concretely breaks if the order is reversed.*
5. **Safety boundaries** — does every phase state what it must not be able to do? Does any phase
   quietly expand authority?
6. **Verifiability** — are exit criteria machine-checkable? Does it confront the Playwright /
   CI-gate / deployed-vs-tested blockers, or route around them by asserting success?
7. **Evidence discipline** — are unknowns marked, or presented as facts? Count the `[U]`s; a
   roadmap with zero unknowns has not read carefully enough.
8. **Owner-gated compliance** — deployment, live acceptance, credential change, policy activation,
   self-modifying installation all still gated?
9. **Non-goals** — stated and consistent with the architecture doc?
10. **Estimability** — could this be scheduled tomorrow? If not, does it say what is missing?
11. **Anti-pattern resistance** — see §9.

## 6. Falsifiable claims to test (do not evaluate by feel)

Run these against each roadmap as text — they are mechanical:

1. **Capability invention:** grep the roadmap for autonomous transfer, automatic cancellation,
   self-deploying, live connector repair, agent council. Any *positive* commitment to these
   violates D-003 / AGENTS.md and the architecture doc's non-goals.
2. **Legitimacy by placeholder:** does any phase's exit criterion amount to "a schema/endpoint/
   button/prompt exists"? That is explicitly forbidden ("never claim completion because only a
   schema, endpoint, button, prompt, or placeholder exists").
3. **Simulation isolation:** does the simulation phase state that it is *structurally* incapable of
   reaching real state, with a test — or only that it "won't"?
4. **Freshness honesty:** does anything permit a stale value to render as current?
5. **Missing data as zero:** does anything collapse "unknown" into 0 (the class of bug C01 was)?
6. **Owner authority:** does any phase activate policy, deploy, or install without owner approval?
7. **Evidence tier honesty:** does the roadmap claim verification it could not have performed
   (e.g. browser verification while Playwright is absent)?

## 7. Conflict resolution rules

When the two roadmaps disagree, resolve in this order — the first rule that applies wins:

1. **Safety invariant** — the more conservative option wins, always. Safety boundaries are not
   traded for speed, coverage, or elegance.
2. **Evidence** — the claim supported by repository evidence beats the claim supported by
   reasoning. Where both cite evidence, the one citing *source* (not documentation) wins.
3. **Verifiability** — the option whose exit criteria are machine-checkable beats the one that
   requires a human to agree it looks right.
4. **Owner preference** — only then. Where two options are equally safe, evidenced and verifiable,
   the owner chooses, and the choice is recorded in `MERIDIAN_DECISIONS.md`.

Record every resolved conflict as: `conflict → options → rule applied → resolution → why`.
Unresolved conflicts are **not** silently merged; they are listed as open decisions.

### 7a. Classify every disagreement before resolving it

The precedence rules in §7 assume all disagreements are the same kind. They are not. Classify first:

| Kind | Test | Settled by |
|---|---|---|
**Factual** | Can repository evidence settle it? (e.g. "is `assets.py` wired?") | Evidence. Read the source. Both parties must accept the finding. |
**Sequencing** | Does reversing the order concretely break something? | The dependency test: name what fails, or the dependency is withdrawn. |
**Value** | Would two well-informed people still differ? (scope, risk appetite, what "done" means) | The owner only. Record in `MERIDIAN_DECISIONS.md`. |

Miscategorising is the common failure: a *value* disagreement dressed as *factual* (pretending
evidence settles a scope choice), or a *factual* one treated as opinion (leaving a verifiable claim
unresolved). If a disagreement cannot be settled by the first two tests within its own terms, it is
a value disagreement and belongs to the owner.

### 7b. Obligations on the adversarial reviewer

An adversarial review that agrees with everything has not been performed. Require it to:

1. Name **at least three things it would delete** from the reviewed roadmap, not merely add.
2. State **the single first move** it would make if only one were possible, and why the reviewed
   roadmap's first move is wrong or right.
3. Declare, for each disagreement, whether it is factual, sequencing, or value (§7a).
4. Cite **source** (not documentation) for any factual claim, per the evidence tier in §2.


## 8. Merge procedure for the ultimate copy

1. **Union the coverage.** Every concept and every finding from either roadmap appears in the
   merged one; nothing is dropped for brevity. Assign each to a phase.
2. **Keep the stricter safety boundary** wherever the two state one.
3. **Keep the more verifiable exit criteria**, and where both are weak, write a better one rather
   than choosing.
4. **Sequence by dependency truth, not by either roadmap's confidence.** For each phase, ask: what
   concretely fails if this runs before its claimed dependencies? Rebuild the order from answers.
5. **Carry forward every `[U]` from either roadmap** as an open item with an owner (inventory,
   measurement, or owner decision). An unresolved unknown is a task, not a footnote.
6. **Carry forward every open decision** from §6 of the first roadmap and equivalents from the
   second.
7. **Adopt one tagging convention** across the merged document and re-tag anything imported.
8. **State what changed and why** relative to each input — so the merge itself is auditable.

## 9. The ultimate copy — required structure

```
0. Declaration header (§2) + provenance: which roadmaps, which authors, which dates, what merged
1. Definition of done (owner-accepted, versioned)
2. Standing constraints (safety invariants, binding)
3. Vision-to-system mapping: all 22 concepts, classified, with support and gaps
4. Findings ledger: A–G with status (closed / open / explicitly deferred) — ties to OS-001..OS-0NN
5. Phases, all in §3 schema, ordered by §8.4
6. Critical path + parallel lanes
7. Verification strategy, including the Phase-0 enablers and what remains unverifiable without them
8. Owner decisions, with status
9. Explicit non-goals
10. Open unknowns ([U]) with an owner and a method for each
11. Merge record: conflicts, rules applied, resolutions
```

## 10. Anti-patterns to score against

- **Roadmap theater** — phases that sound ambitious with no exit criteria. Score: absent verifiability.
- **Remediation forever** — a roadmap made mostly of defect fixes with no product phases. The
  inverse failure of the current situation.
- **UI-first** — building the Observatory before the data model it renders, then rebuilding it.
- **AI magic phase** — "add agents" with no tool/authority matrix, no structured outputs, no
  adversarial tests.
- **Capability invention** — quietly granting autonomy the documents forbid.
- **Confidence laundering** — judgments presented as evidence; unknowns absent entirely.
- **Owner-decisions-as-tasks** — burying a decision that only the owner can make inside a phase
  that assumes an answer.
- **Silent deferral** — dropping a finding or concept without saying so.
