# Meridian's 22 concepts — the vision inventory, in view every session

**Why this document exists.** The owner's own words, 2026-09-25: *"The 22 concepts are clearly stated in the
github as well I believe. I feel we are DRASTICALLY losing site if those concepts arent obvious and kept in
mind. We review all governing documents with every session."* He was right, and the drift was provable
rather than a feeling:

* the concepts are authoritative in `MERIDIAN_INITIAL_BUILDER_PROMPT.md` §3, which the roadmap's §0 lists as
  an active authority — but **no session ritual ever read it**;
* the roadmap's §0.4 also names *"the 22-concept mapping"* as an active authority, yet the only document
  holding such a mapping, `MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md`, is one the roadmap **supersedes** —
  and §0 also says superseded narratives are moved to `archive/` and *"governing requirements are never
  demoted to history"*. So the mapping was demoted by supersession in fact, while remaining an authority on
  paper: a direct contradiction;
* `AGENTS.md`'s orientation tells a session to read the handoff, `PROJECT_INSTRUCTIONS.md`,
  `CURRENT_STATUS.md`, the roadmap, the ledger and the decisions — **and not the concepts**;
* and the current roadmap's 13 uses of the word "concept" are all about *design* concepts — the governing
  visual sets, glyphs, layout — never the product concepts below. Two different meanings of one word, with
  only one of them in the index.

**This document fixes that by being the missing index entry, not by adding a new authority.** It reproduces
the concepts verbatim, carries the classification the builder prompt itself specifies, maps them to the
slices that would build them, and records — per concept — what exists today. It is an inventory **to
evaluate against**, exactly as its source insists.

## The instruction that governs how this list is used

> *"Evaluate—not automatically implement—the following possible capabilities."*
> — `MERIDIAN_INITIAL_BUILDER_PROMPT.md` §3, verbatim

That sentence is the difference the owner draws between **reporting** and **evaluating**. The list is not a
build order, not a promise, and not a funnel that must be emptied. It is the set of possibilities against
which every slice is judged: *which concept does this advance, and which does it quietly neglect?* A slice
that advances none of them needs its own justification, stated out loud.

**And the classification the source requires of each concept, verbatim:**

1. Foundational now · 2. Foundational later · 3. Safe read-only prototype · 4. Requires explicit owner policy
· 5. Requires external integration · 6. Requires substantial privacy/security design · 7. Speculative or
deferred · 8. Must not be autonomously implemented — *"Explain the classification and dependencies."*

## The 22 concepts

Verbatim from `MERIDIAN_INITIAL_BUILDER_PROMPT.md` §3. The class and slice columns are the honest reading
recorded in `MERIDIAN_IMPLEMENTATION_PLAN.md` §2 **at `b053911`** (its own words: *"State is my honest reading
at `b053911`"*), so treat the class column as a dated judgement to re-examine, not as settled fact. The
**State today** column records what this session verified itself on 2026-09-25; anything marked *audit* is
still being checked and must not be quoted as verified.

| # | Concept | Class (at `b053911`) | Slice that would build it | State today (2026-09-25) |
|---|---|---|---|---|
| 1 | Financial digital twin | Foundational now | C2 | Audit |
| 2 | 7-, 30-, 90-, and 365-day projections | Foundational now | C5 | Audit |
| 3 | Explicit confidence, uncertainty, assumptions, and provenance | Foundational now | I1 | **Verified present in the observation stores**: `freshness`, `confidence`, `data_mode`, `snapshot_id`, `assumptions_json`; reinforced today by D-026/D-027 (silence is not zero) |
| 4 | Living financial constitution | Requires explicit owner policy | C8 | Audit (`policy.py` exists, no application callers) |
| 5 | Policy evaluator | Requires explicit owner policy | C8 | Audit (`write_routing.py` is the named decision point) |
| 6 | Specialized financial agents | Foundational later | I1, I3 | **Partial, and better than the plan assumed**: the Investigator and the Skeptic exist behind a shared role runner, with create/edit/delete autopilot commands and `readback_autopilot_rules`; the council records disagreement and structurally cannot produce a verdict (OS-074 verified 44 passing tests). The roadmap names Forecaster, Guardian and Teacher as unbuilt |
| 7 | A single constrained executor | Foundational now | C4 | **Verified**: `meridian/crew_write_actions.py` routes every write through a constrained executor with readback verification, proposal routing lives in `meridian/write_routing.py`, and absence is distinguished from success |
| 8 | Proactive financial weather and alerts | Foundational later | C6 | Audit — this is the owner's stated priority, and the suppression lifecycle is the blocker named in V4 |
| 9 | Balance forensics and anomaly investigation | Safe read-only prototype | C7 probe | Audit — read-only, so a legitimate early prototype |
| 10 | Continuously repaired budgets | Foundational now | C3 | **Verified in part**: commitments, `funded_amount`, reserve observations and (new) dated allocation history; the repair path itself is unaudited |
| 11 | Paycheck landing workflows | Foundational now | C3, D2 | **Verified**: `payday.py` plus `crew_funding_plans` (three rows: two absent, one live) and a bidirectional funding-plan write path with readback verification |
| 12 | Scenario simulation and counterfactual learning | Safe read-only prototype | C5 | Audit |
| 13 | Refunds and subscription lifecycle management | Requires external integration | C7 | Audit |
| 14 | Bureaucracy and negotiation preparation | Requires external integration | C7 | Audit — drafting only, never autonomous sending |
| 15 | Household resource planning | Requires substantial privacy design | C9 option | Audit — excluded until a demonstrated unmet job |
| 16 | Crisis-command mode | Requires explicit owner policy | C9 option | Audit — must provably not touch actual state |
| 17 | Causal financial memory | Foundational later | (unassigned) | Audit — depends on concept 1's identity |
| 18 | Temporary personalized tools | Must not be autonomously implemented | — | Refuse until the sandbox and review gate exist |
| 19 | Connector self-diagnosis | Safe read-only prototype | (unassigned) | Audit — small, safe, genuinely useful |
| 20 | Sandboxed skill generation | Must not be autonomously implemented | — | Refuse; do not prototype without the sandbox |
| 21 | Proposed UI evolution | Foundational now | D1–D5 | **In progress by design**: governed capture matrix, concept-vs-current comparisons, one gap at a time |
| 22 | Bounded autonomous CFO behaviour | Must not be autonomously implemented | — | Refuse; out of scope until constitution, evidence and executor are all proven in production |

**The plan's own honest division of the 22, quoted so nobody re-derives it wrongly:** *"8 of 22 are
deliverable on the current substrate; 5 are read-only prototypes I would want to prove before trusting; 6 need
an owner policy or privacy decision; 3 must not be autonomously built at all."*

## The owner's direction, mapped onto the concepts (2026-09-25)

He asked to *"work toward proactive and reactive culpable intelligence, things should be evaluated not just
regurgitated, perhaps more of the agents in the roadmap need to be built."* In concept terms:

| His word | Concepts it is made of |
|---|---|
| **Proactive** | 8 (weather and alerts), fed by 2 (projections) and 12 (scenarios) |
| **Reactive** | 9 (balance forensics), 19 (connector self-diagnosis), 17 (causal memory) — answering a challenge about *anything*, with citations |
| **Culpable** | 3 (confidence, uncertainty, assumptions, provenance), 4 (living constitution), 5 (policy evaluator) — every claim owns its evidence, its limits and the rule it answers to |
| **More agents** | 6 (specialized financial agents) — the roadmap's own named set, of which the Investigator and Skeptic exist |
| **Bounded** | 7 (single constrained executor) and 22 (bounded autonomous CFO, refused) — evaluating never widens authority |

## How this document is kept in view

1. **Every session reads it** — it is now part of the orientation in `AGENTS.md`, alongside the handoff, the
   roadmap, the ledger and the decisions. It was previously in none of them, which is how it was lost.
2. **Every slice names its concept.** A slice proposal states which of the 22 it advances, or states plainly
   that it advances none and why it is still worth doing.
3. **The State column is evidence, not memory.** A concept may be called built only with a file, a test or a
   run that shows it; the words "audit" above are a debt this session owes, not a claim.
4. **Nothing here is scheduled by being listed.** Assignment lives in the roadmap and the task ledger, and
   promotion is an owner decision.
