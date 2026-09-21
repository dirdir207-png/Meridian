# ORSC Meridian Agent Instructions

## Sole project boundary

This is the sole and only Meridian/SimpleCrew workstream. Work only inside:

`/Users/stephenwest/Openrouter/simplecrew-latest`

Use the current branch `feat/meridian-implementation` unless the owner explicitly directs otherwise. Never modify, read for authority, copy from, or synchronize with:

`/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`

Preserve unrelated tracked and untracked files. Never delete or clean up artifacts without explicit instruction.

## Governing sources

Before substantial work, inspect `docs/project/PROJECT_INSTRUCTIONS.md`, `docs/project/CURRENT_STATUS.md`, relevant governing handoffs, and managed project Documents. The current visual authority is the newest explicitly governing design set; currently verify `design/observatory-drafts-2026-09-08/` before use. Older captures are historical evidence unless explicitly promoted.

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

## Financial safety

Agents may observe, explain, simulate, forecast, investigate, challenge, teach, draft, prepare, test, and propose. Only the constrained executor may mutate financial state. Never expose secrets. Never auto-retry mutations. Never perform external transfers autonomously. Preserve proposal → approval → execution → provider verification. Treat uncertain writes as unknown until readback. Keep actual, inferred, and simulated values separate; stale data must remain visibly stale; missing data is not zero.

## Visual fidelity protocol

Visual work must use the newest governing concept set and the locked capture contract in `docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md`. Required CSS viewports are 1440×900, 1024×768, 430×932, 390×844, and 420×912 (the owner's iPhone Air). Use DPR 1 for desktop/tablet and DPR 3 for mobile. Explicitly set light or dark theme; never inherit the OS default. Disable animation, transitions, reduced-motion effects, polling, timers, and auto-refresh. Wait for `document.fonts.ready`, network idle, and all Meridian data requests to settle. Use deterministic synthetic seed data and a fixed clock; never use live bank data for parity captures. Lock workspace, selected record, proposal state, connection state, scroll position, and `fullPage` behavior. Capture both the initial viewport and any explicitly defined full-page artifact. Validate 390×844, 420×912, 430×932, and 1440×900 in both themes. Never compare a mobile concept to a desktop capture or treat a different page length/data state as a design defect. For each comparison, preserve the concept aspect ratio and record concept path, current path, viewport, DPR, theme, fixture, clock, state, fullPage setting, commit, and capture date. Generate side-by-side and overlay/difference views when tooling permits. Review structure first, then typography, spacing, controls/accessibility, and decoration; change one visual gap at a time and recapture.

## Verification and release

Never claim completion because only a schema, endpoint, button, prompt, or placeholder exists. Production deployment, live acceptance, credential changes, authority-policy activation, and self-modifying installation are owner-gated. When blocked, do safe read-only inspection, testing, documentation, or simulation rather than guessing.
