# Meridian Operating System Decisions

## D-001 — Sole workstream

All Meridian/SimpleCrew work is maintained in `/Users/stephenwest/Openrouter/simplecrew-latest`. The shared `/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch` tree is permanently out of bounds.

## D-002 — Creative architecture, anchored implementation

Use creative reasoning for audit and architecture; use anchored, test-driven, one-slice implementation and verification. The custom Harness mode is `Meridian Constitutional Builder`.

## D-003 — Authority separation

Agents may observe, explain, simulate, investigate, forecast, challenge, teach, draft, prepare, test, and propose. Only a constrained executor may mutate financial state through proposal → approval → execution → provider verification.

## D-004 — Visual authority

The newest explicit governing visual design takes precedence over historical screenshots and intermediate captures. Confirm current authority before visual work.

## D-005 — Release control

Production deployment, live acceptance, credential changes, policy activation, and self-modifying installation require explicit owner approval.

## D-006 — Observatory refinement scope (2026-09-12)

Owner requested focused correction toward the original concept, explicitly retaining prominent safe-to-spend on Today and the original large-dial/side-callout composition. Preserve real API data bindings and use synthetic data for visual acceptance. This is the active visual slice; it does not authorize financial execution or production deployment. See `OBSERVATORY_REFINEMENT_2026-09-12.md`.

## D-007 — Development autonomy with action gating (owner, 2026-09-13)

Owner clarification, resolving the ambiguity in the builder prompt's class 8 ("must not be autonomously implemented"). The distinction is between **development and operation**, which may be autonomous, and **value-moving action**, which may not.

- Skills and tools **may be developed autonomously by the agent**, and must be **approved by the owner** before use.
- An autonomous CFO **may be designed and built autonomously**; the **final design is approved by the owner**.
- Autonomous monitoring, suggestions and decisions are permitted — they are rendered as proposals and **sent to the owner for final approval**.
- **Actions remain owner-gated.** Owner statement: "Things can operate autonomously with actions still being owner gated."

This refines `D-003` (authority separation) rather than replacing it: proposing, drafting, simulating and recommending stay free; mutation still requires proposal → approval → execution → provider verification. It also refines `D-005`: the owner-approval requirement applies to **activation of an approved design**, not to the drafting of it.

Consequences: "temporary personalized tools" and "sandboxed skill generation" are no longer blocked in principle and may be developed in this lane, provided the approval is real. "Bounded autonomous CFO behavior" may be designed, with the owner approving the design and every value-moving action.

**Design requirements that make the approval real** (architect's interpretation, `[D]`, not owner wording): an approval is only meaningful if it is specific and revocable, so —

1. The owner approves the **permission set** (an explicit diff), not just the intent. Permissions are enforced in code and **cannot expand as a side effect of a feature**.
2. Tools carry an explicit **lifetime** with a review point; approval is not permanent by default.
3. The pipeline **fails closed**: absent or ambiguous approval halts, rather than the agent promising to wait.
4. An agent may build, but **activation is the owner's act**, consistent with `D-005`.
5. Every autonomous recommendation carries the evidence and confidence that produced it, so the owner can audit the proposal before approving it.

Status: binding for planning. It authorizes development of these capabilities in-lane; it does **not** authorize financial execution, production deployment, or autonomous value movement.

The constraints that will bound an autonomous CFO are being collected as open questions in `CFO_MANDATE_QUESTIONS.md`. Open questions there are not defaults and not permission; the CFO slice cannot start until they are answered and recorded.
