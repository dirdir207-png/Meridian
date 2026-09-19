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

## D-008 — Human-facing repository overview (owner, 2026-09-18)

The owner requested review and correction of the GitHub landing page: Meridian branding, Observatory artwork, and no AI-centric instructions or directions. README.md now presents the product, current limitations, roadmap, and clearly labeled design concepts for human readers. Agent workflow, model routing, implementation status jargon, prompts, and verification commands stay out of the landing page. Existing Observatory artwork is reused to avoid unnecessary generation cost. This is a documentation change, not a change to product scope or financial authority.

## D-009 — Preserve the full future roadmap in the overview (owner, 2026-09-18)

The owner clarified that all roadmap concepts belong on the human-facing landing page as future features. Restored all 22 individually named concepts with plain-language intended benefits and explicit future status. D-008 excludes agent-facing instructions, not product features involving AI or agents; it must not be used to compress away the roadmap.


## D-010 — Preserve Crew funding relationships (owner, 2026-09-19)

Owner: "Bills are already funded by a particular funding source or income source in Crew (only one exists presently)- but this can be made to be done in Crew as well, as long as it doesnt break cross functionality."

Use Crew's existing relationship as the authority; do not invent a Meridian-only allocation or infer it from the number/name of income sources. Preserve interoperability. Managing the relationship in Crew is acceptable. This is not approval of a specific provider mutation. Source identity is separate from how much money is reserved for a dated bill occurrence; do not spread a reserve total across future occurrences.

Read-only inspection at `ade532d`: funding plans persist `bill_reserve_id`, but `_collect_commitment_candidates` drops the containing reserve ID and `CommitmentCandidate` has no such field. The next slice must retain the observed relationship before resolving a source. Missing or ambiguous links remain explicit. See `DEEPSEEK_HANDOFF_2026-09-19.md`.

## D-011 — Icon replacement scope and usage (owner, 2026-09-19)

The supplied generic icon pack does not match the concept. The long-term goal is to replace all icons with closer concept-matched artwork. The owner accepts generating only the missing sun now when full-set generation is expensive. This checkpoint uses one built-in image generation; no full-pack generation or replacement. Keep generated artwork outside the Bootstrap-licensed directory and record provenance. Usage cost is not known in advance. The owner subsequently requested a clean, usage-conscious handoff for DeepSeek, prioritizing visual progress.

## D-012 — Page-specific design authority (owner, 2026-09-19)

Owner: "September 18 only filled in pages that had no concept before. If there is overlap, September 16th is the standard, otherwise drop back to the 8th".

September 18 is additive, not a blanket replacement. Use September 16 where a page has an overlapping standard, September 18 for previously missing pages/surfaces, and September 8 as fallback. Historical does not mean unusable. Record the exact reference for each comparison; do not silently promote a rendered screenshot into a concept.

Located locally: September 16 asset kit and its artwork handoff, September 8 page concepts, and September 18 Review/Timeline/Settings/Virgil studies. The September 16 kit README explicitly says its assets do not supersede reference composition and points to September 8 PNGs. No separate September 16 page-concept directory was found in the inspected design/kit paths; this limits reference discovery, not the owner's precedence rule. Use the documented September 8 compositions plus September 16 assets unless an actual September 16 page reference is located. The September 18 Timeline concept supplies the missing sun reference for this bounded slice.
