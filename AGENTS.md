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

## Financial safety

Agents may observe, explain, simulate, forecast, investigate, challenge, teach, draft, prepare, test, and propose. Only the constrained executor may mutate financial state. Never expose secrets. Never auto-retry mutations. Never perform external transfers autonomously. Preserve proposal → approval → execution → provider verification. Treat uncertain writes as unknown until readback. Keep actual, inferred, and simulated values separate; stale data must remain visibly stale; missing data is not zero.

## Visual fidelity protocol

Visual work must use the newest governing concept set, exact matching viewport dimensions, the same theme, deterministic fixture data, frozen time, loaded fonts, disabled animation, and settled network state. Never compare a mobile concept to a desktop capture or treat a different page length/data state as a design defect. For each comparison, preserve the concept aspect ratio and record concept path, current path, viewport, fixture, commit, and capture date. Generate side-by-side and overlay/difference views when tooling permits. Review structure first, then typography, spacing, controls/accessibility, and decoration; change one visual gap at a time and recapture.

## Verification and release

Never claim completion because only a schema, endpoint, button, prompt, or placeholder exists. Production deployment, live acceptance, credential changes, authority-policy activation, and self-modifying installation are owner-gated. When blocked, do safe read-only inspection, testing, documentation, or simulation rather than guessing.
