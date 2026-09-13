# Meridian project documents — start here

**Canonical repo:** `/Users/stephenwest/Openrouter/simplecrew-latest` (the only tree; the parent directory is an
unversioned snapshot) · **branch:** `feat/meridian-implementation`.

Read this file first. It says which documents are **authoritative**, which are **living**, and which are
**superseded** — so a reader never has to guess whether a document is current. Superseded documents stay in the
tree on purpose: they are the record of how decisions were reached.

## Governing authorities (bind the work)

| Document | What it governs |
|---|---|
`MERIDIAN_INITIAL_BUILDER_PROMPT.md` | The mission, the 22-concept vision, the eight-class taxonomy, agent roles |
`MERIDIAN_DECISIONS.md` | Owner decisions (sole workstream, authority separation, visual authority, release control) |
`MERIDIAN_OS_ARCHITECTURE.md` | Layer boundaries, sequence, non-goals |
`MERIDIAN_VISUAL_CAPTURE_SPEC.md` | The capture matrix (five viewports × two themes) and determinism contract |
`AGENTS.md` (repo root) | Working rules, financial safety, visual protocol |
`PROJECT_INSTRUCTIONS.md` | Branch, secret-handling and status rules |
`design/observatory-drafts-2026-09-08/` | **The visual authority** — the concepts layout and design must match |

## Living documents (updated as work proceeds)

| Document | Role |
|---|---|
`MERIDIAN_ROADMAP.md` | **The single trajectory** — three tracks, release boundary, merge record |
`CURRENT_STATUS.md` | Status log: what shipped, what is blocked |
`MERIDIAN_SUBSTRATE_INVENTORY.md` | What exists in the code: modules, schema, stubs, wiring |
`AGENT_COORDINATION.md` | **Who is doing what** — claims table and append-only log |
`design-qa.md` | Visual acceptance state and known gaps |
`MERIDIAN_OS_TASKS.json` | The task ledger |

## Reference (consult, do not re-derive)

`MERIDIAN_EXECUTION_GAMEPLAN.md` — proposed D1–D8 execution plan: named consolidation candidates, current ref inventory, owners/interfaces, bounded slices, preset migration, first Harness prompt, session architecture and acceptance. Complements the roadmap; does not approve installation, cleanup, restart or deployment.

`CREW_GRAPHQL_CATALOG.md` · `crew_mutations.json` · `BILLER_CAPABILITIES.md` ·
`CREW_SESSION_BROKER_CLI_HANDOFF.md` · `CODEX_CLI_HANDOFF.md` · `MERIDIAN_ROADMAP_COMPARISON_PROTOCOL.md`
(how to adjudicate competing plans) · **`CONSTITUTIONAL_BUILDER_REVIEW_2026-09-12.md`** — review of the
installed agent preset and the proposed operational loop: the *runtime* layer of guardrails. Its changes are
Harness-side and owner-gated, not lane-side. · **`PRESET_GUARDRAIL_IMPLEMENTATION.md`** — the concrete design for
implementing that review: Harness-side changes with anchors and proofs, and the lane-side half (claims manifest,
`check_guardrails.py`, re-entry packet) buildable now. · **`../superpowers/specs/2026-09-09-trial-canceler-design.md`**
— the design for the trial/subscription-lifecycle subsystem. Indexed here because that subsystem is already
**built and wired** (15 modules, 9 endpoints, 19 passing tests) while going unmentioned in the roadmap narrative,
which is how finished work comes to look forgotten.

## Superseded (history — never cite as current)

| Document | Superseded by |
|---|---|
`MERIDIAN_OS_ROADMAP.md` (ten-row table) | `MERIDIAN_ROADMAP.md` |
`MERIDIAN_VISION_ROADMAP.md` (first roadmap) | `MERIDIAN_ROADMAP.md` §11 merge record |
`MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md` (second, informed review) | `MERIDIAN_ROADMAP.md` §11 |
`MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md` | Findings stay authoritative as findings; its delivery order does not |
`OBSERVATORY_DIAL_HANDOFF_2026-09-09.md`, `OBSERVATORY_REFINEMENT_2026-09-12.md`, `DIAL_ALIGNMENT_FIX_2026-09-12.md` | Completed checkpoints; state lives in `design-qa.md` and `CURRENT_STATUS.md` |

## Reading order for a new session

1. `AGENTS.md` → 2. this file → 3. `MERIDIAN_ROADMAP.md` → 4. `CURRENT_STATUS.md` → 5. `AGENT_COORDINATION.md`
(claim your files) → 6. `MERIDIAN_OS_TASKS.json` → 7. recent commits → 8. the source you are about to change.

Mark what you verify `[E]`; mark judgment `[D]`. A documented claim is not a verified claim.
