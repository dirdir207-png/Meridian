# ORSC Meridian Agent Instructions

## Sole project boundary

This is the sole and only Meridian/SimpleCrew workstream. Work only inside:

`/Users/stephenwest/Openrouter/simplecrew-latest`

Use the current branch `feat/meridian-implementation` unless the owner explicitly directs otherwise. Never modify, read for authority, copy from, or synchronize with:

`/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`

Preserve unrelated tracked and untracked files. Never delete or clean up artifacts without explicit instruction.

## Governing sources

**Read `docs/project/HANDOFF.md` FIRST — it is the orientation map for a new or compacted session.** Section 1 lists every governing source with its sha256, so **compare a hash against the file you are reading** to see immediately whether the handoff is stale; if one differs, regenerate with `scripts/generate_handoff.py` before trusting the rest. It is generated from the governing docs and must never be hand-edited; if it disagrees with a doc, the doc wins. (`--check` is DISABLED and known broken — it reported false staleness; use the hash comparison.) Then inspect `docs/project/PROJECT_INSTRUCTIONS.md`, `docs/project/CURRENT_STATUS.md`, relevant governing handoffs, and managed project Documents. **And read `docs/project/MERIDIAN_CONCEPTS.md` — the 22 concepts, with the builder prompt's own instruction that they are to be EVALUATED, not automatically implemented.** Every slice must name which concept it advances, or state plainly why it advances none. The concepts were authoritative in `MERIDIAN_INITIAL_BUILDER_PROMPT.md` §3 and named by the roadmap's §0 while appearing in NO session reading list, which is exactly how a project loses sight of them while believing it reviews everything (found 2026-09-25). The current visual authority is the NEWEST explicitly governing design set, and **no single set covers every surface** — apply the sets in PRECEDENCE, not as rivals: `design/observatory-extension-2026-09-18/` governs everything it covers (`settings`, `virgil`, `review`, `timeline`, and its `assets/` and `icons/`), and **anything it does not cover is governed by `design/observatory-drafts-2026-09-08/`** (`today`, `plan`, `activity`, `accounts`, plus the shared design language its `BUILD_SPEC.md` records). Owner's formulation, 2026-09-21: *"The sept 18th studies are the governing documents, anything NOT covered by them is covered by the other."* So a 09-08 file is NOT globally superseded and must not be dismissed as historical because a newer set exists — check first whether the newer set actually speaks to that surface. Older captures remain historical evidence unless explicitly promoted.

**Before ending a session, or at any context checkpoint, regenerate the handoff** (`scripts/generate_handoff.py`) and record anything session-emergent in `docs/project/session-emergent.json`. The next session is usually the one that depends on it, and the owner has named handoff reliability as the deciding factor when context runs out.

## Engineering workflow

Use: DISCOVER → RECONCILE → ARCHITECT → PLAN → APPROVE → IMPLEMENT → VERIFY → REVIEW → DOCUMENT → COMMIT.

Implement one bounded vertical slice at a time. Prefer test-first development. Run targeted tests, relevant browser/accessibility checks, lint, and `git diff --check`. Review the final diff for secrets and unrelated changes. Update `docs/project/CURRENT_STATUS.md` and commit only intended files.

## Continuity — momentum and project state are checked together

Every continuation, compaction resumption, or new session must reconcile **two** inputs before acting, and must never act on one alone:

1. **Project state** — `docs/project/MERIDIAN_ROADMAP.md` (the trajectory and its stated next move), the task ledger, `docs/project/MERIDIAN_DECISIONS.md`, and open owner gates.
2. **Session momentum** — what this session just did, and the claims table in `docs/project/AGENT_COORDINATION.md`.

**Neither is authoritative by itself.** Session momentum is not the roadmap: finishing a slice creates an obvious next step, and that step can still be off the critical path. Conversely the roadmap is not a plan for this hour — it may already be satisfied, or superseded by a newer owner decision.

The rule: **state in writing where the candidate work sits on the roadmap before starting it.** If it is not on the current critical path or in the ledger, say so plainly, record it as an earmark if it is worth keeping, and let the owner choose. Do not silently substitute momentum for priority, and do not quote a fact about the current code as though it were a design constraint.

Existing workstreams can hold priority over new ones; the roadmap's own stated next move wins unless the owner redirects.

## Handoffs must reconcile the governing order with the session

A handoff is the artifact the owner relies on between sessions, so it may never be a summary of the conversation. **It is a projection of the governing doc set, and it must say so.** Read the documents, not the session, and then reconcile the two.

Every handoff states, explicitly:

1. **BASIS** — the governing sources it was derived from, by path, and the commit it was read at. A handoff that cannot name them is a session summary and must be labelled as one.
2. **THE ASSIGNED ORDER** — the roadmap's current critical path and its stated next move, quoted rather than paraphrased; the open gates in the task ledger; and the in-flight tasks with their declared track/phase.
3. **SESSION-EMERGENT ITEMS, SEPARATED.** Anything that arose during the session — a new idea, a discovered defect, a proposed slice — is listed **apart** from the assigned order, marked as emergent, and given a ledger id if it is worth keeping. It must never appear in the same list as assigned work, because that is how a session idea acquires the authority of the plan.
4. **PROMOTION, NOT ASSUMPTION.** An emergent item does not become planned work by appearing in a handoff. Promotion is an explicit owner decision, recorded in the ledger and, when it changes the sequence, in the roadmap.
5. **WHAT WAS NOT TOUCHED** — the tracks and slices that still stand unstarted, so their absence is visible rather than assumed.

**The reconciliation is a check, not a promise.** Run `scripts/roadmap_handoff_check.py` before writing a handoff; it verifies that every roadmap item exists in the ledger, that everything in flight declares a track, and that no session-emergent item is silently presented as assigned. A handoff written without running it is not a handoff.

**Why this exists.** Session momentum is genuinely useful — it is where discoveries come from — but it is not the build order, and the two were previously indistinguishable in a handoff. The original sequence is the thing being protected. Keep the drift visible and the owner decides; do not let it dissolve into the summary of a good conversation.

## Financial safety

Agents may observe, explain, simulate, forecast, investigate, challenge, teach, draft, prepare, test, and propose. Only the constrained executor may mutate financial state. Never expose secrets. Never auto-retry mutations. Never perform external transfers autonomously. Preserve proposal → approval → execution → provider verification. Treat uncertain writes as unknown until readback. Keep actual, inferred, and simulated values separate; stale data must remain visibly stale; missing data is not zero.

## Visual fidelity protocol

Visual work must use the newest governing concept set and the locked capture contract in `docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md`. Required CSS viewports are 1440×900, 1024×768, 430×932, 390×844, and 420×912 (the owner's iPhone Air). Use DPR 1 for desktop/tablet and DPR 3 for mobile. Explicitly set light or dark theme; never inherit the OS default. Disable animation, transitions, reduced-motion effects, polling, timers, and auto-refresh. Wait for `document.fonts.ready`, network idle, and all Meridian data requests to settle. Use deterministic synthetic seed data and a fixed clock; never use live bank data for parity captures. Lock workspace, selected record, proposal state, connection state, scroll position, and `fullPage` behavior. Capture both the initial viewport and any explicitly defined full-page artifact. Validate 390×844, 420×912, 430×932, and 1440×900 in both themes. Never compare a mobile concept to a desktop capture or treat a different page length/data state as a design defect. For each comparison, preserve the concept aspect ratio and record concept path, current path, viewport, DPR, theme, fixture, clock, state, fullPage setting, commit, and capture date. Generate side-by-side and overlay/difference views when tooling permits. Review structure first, then typography, spacing, controls/accessibility, and decoration; change one visual gap at a time and recapture.

## Verification and release

Never claim completion because only a schema, endpoint, button, prompt, or placeholder exists. Production deployment, live acceptance, credential changes, authority-policy activation, and self-modifying installation are owner-gated. When blocked, do safe read-only inspection, testing, documentation, or simulation rather than guessing.
