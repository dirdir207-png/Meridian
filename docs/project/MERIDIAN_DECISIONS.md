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

## D-013 — How a dated occurrence's reserved amount may be stated (owner, 2026-09-19)

Owner, verbatim: *"The per dated occurance can be strictly user facing on the meridian side, or it can be an even allocation of total set aside funds, split evenly across commitments. Since Bill reserve is a single bucket, I'm not sure how it allocates per bill in Crew currently."*

What this settles:

1. A per-dated-occurrence reserved figure **may** be shown. It may be a Meridian-side allocation the owner sets, or a Meridian-derived even split of the reserve's set-aside total across the bills in that reserve. Neither is forbidden. The owner is explicit that they do not know how Crew itself allocates per bill inside the single reserve bucket, so no Crew allocation may be assumed from the bucket total alone.
2. D-010 is narrowed, not overturned. Its prohibition is about spreading a reserve total across **future occurrences**. Dividing across **commitments** (one share per bill) is now permitted; multiplying a bill's share by the number of future dates it recurs is still forbidden.
3. Precedence: a provider-reported per-bill figure is an observation and outranks any Meridian derivation. `_collect_commitment_candidates` already carries Crew's per-bill `reservedAmount` into `funded_amount` (nullable, per C01), so when Crew reports it that is the figure to use — the dial currently ignores it for bills and hardcodes `fundingStatus: "unknown"` with `reserved: null`.
4. Attribution: a Meridian-side or derived figure must be labelled as Meridian-side/derived together with its basis, must never be attributed to Crew, and must never be presented as a provider balance or as an observed reservation.

Status: implemented in OS-048b (2026-09-19) — see D-014. The display question D-013 left open is answered by stating the figure on the earliest occurrence only.

## D-014 — Persist the observed reserve state, and how the dial may state a reserved amount (owner, 2026-09-19)

Owner ruling when shown the audit: **"Option B"** — land all four copy states in one slice, which means persisting the two observed facts D-013's fallback needs rather than approximating them.

What the audit found, and what this settles:

1. **D-013's "total set aside funds" was never stored.** Crew's `billReserve.totalReservedAmount` is observed by the connector (`readback_reserve_totals`) but was persisted nowhere in Meridian: no column, no table. The only reserve-scoped number that *was* stored — the funding plan's own amount (022) — is the plan's per-cadence figure, not the bucket balance, so dividing it across bills would have fabricated a number. `crew_bill_reserves` (migration 024) now stores the observed total, keyed on Crew's own reserve id, nullable, with the 020/021/022 absence discipline. **A missing total is never treated as an empty bucket and never becomes a dividend.**
2. **C01 made "reported zero" and "never reported" indistinguishable in storage.** `commitments.funded_amount` is `REAL NOT NULL DEFAULT 0`, and C01 deliberately keeps a bill with no reported reserve at 0.0. `commitments.reserved_amount_reported` (024) records which happened. A read that does not report the field never clears the flag, for the same reason C01 refuses to let a silent read erase a known amount. The backfill sets the flag only where `funded_amount > 0`: absence writes 0.0, so a positive value could only have come from something that stated it.
3. **Order of authority (implemented once, in `_reserve_figure`)**: observed per-bill figure → labelled derived even split → unknown. The derived share is `total / number of bills in that reserve`; it carries `fundingBasis: "derived"`, its divisor, and `fundingAttribution: "meridian"`. Attribution to Crew is granted only when the stored row itself came from Crew, so a local bill's own figure is never called Crew's.
4. **One occurrence, never the whole schedule.** The figure is stated on the earliest occurrence in the horizon only; every later occurrence of the same bill keeps `"unknown"`. D-010's prohibition stands as narrowed by D-013: one share per bill is permitted, multiplying it across future dates is not.
5. **Labelled wherever it is stated.** D-013 §4 applies to every surface, not just the ticket: the centre, the event row and the accessibility text all read a derived figure as "(Meridian estimate)", and the ticket adds the divisor. A payload that carries a reserved amount with no basis is not promoted into the figure line at all — an unlabelled number can only be read as an observation.

Found while verifying, and fixed in the same slice because the feature is otherwise dead in the running app: **the production refresh path stored neither observed fact.** Funding plans and reserve totals were written only by `sync_providers`, which OS-053 established has no production caller; `app.py` refreshes through `meridian.live.sync_live_crew`. That path now writes both, Meridian-local and provider-read-only, with the same tri-state absence rule. This is a persistence correction, not an authority change: no provider mutation, no transfer, no live sync in this slice.

Ratified by the owner on 2026-09-19, shown the delivered copy: *"Split across 3 bills is fine, I can always adjust after."* The derived figure's divisor wording ("Meridian estimate, split across 3 bills" in the evidence ticket, "(Meridian estimate)" on the row and in the centre) is accepted as delivered, and is explicitly a presentation choice the owner may revise — changing it touches no storage, no precedence and no provenance.

**Correction to D-013's premise, from live data (2026-09-19, after the owner authorized restarting `:8081`).** D-013 permits the even split on the owner's belief that the reserve is *"a single bucket"* whose per-bill allocation inside Crew is unknown. The live read says Crew does allocate per bill: in reserve `BillReserve:8d2f3e8f-…`, Rent reports `reservedAmount` 1097.10 and the other four bills report 0.00 each — explicitly reported, not absent (`reserved_amount_reported = 1` on all five) — and `totalReservedAmount` = 1097.10 is exactly their **sum**. So the total is not a pooled figure to be divided; it is the sum of allocations Crew already made. Consequences, recorded rather than acted on: the `derived` branch is **dormant** on this data (precedence correctly stops at `observed`, so the approved copy currently appears nowhere), and if it ever fired on a partially-reported reserve it would hand an unreported bill a share of *other bills'* money. That is OS-055, an owner decision with candidate rules; **no behaviour was changed silently**, because the risk is dormant and the choice is a product one. The precedence itself (D-013 §3) is unaffected and was confirmed correct on live data: all three bills in the current horizon emit `fundingBasis: "observed"`, `fundingAttribution: "crew"`, `reserved: null`, and state Crew's own "not yet set aside" instead of "unknown".

## D-015 — Mirror Crew's own funding arithmetic; retire the invented split (owner direction, 2026-09-19)

Owner direction, verbatim: *"ideally it should be deterministic based on the due date of the bill, paycheck amount, cadence so that bills are funded by their due date, or at the last funding event before the due date"*, refined by *"it can mimic exactly how the beacon budget app works, or Simple Bank before it shut down, thats what all of this, including crew, is based on"* and *"see if you can discern the actual calculations used by Crew based on reserve amount and funding rules."*

The third instruction is what resolved the design question, and it makes the first two concrete. Reverse-engineered from one read-only connector snapshot and **proven exact on all five bills** (`docs/project/CREW_FUNDING_MATH_2026-09-19.md`):

```
bill.estimatedNextFundingAmount = ceil( bill.amount * interval_days / 30.4375 )
```

`interval_days` is the funding plan's cadence in days (14 here: `frequency WEEKLY, frequencyInterval 2`), `30.4375` is `365.25/12`. Every bill therefore accrues a **daily-rate share of its monthly amount from every funding event** — the Simple/Beacon "fund it by its due date" mechanic, already running inside Crew. Crew also states, per bill, **`reservedBy`** — the next due date that reservation is for — and, per reserve, **`nextFundingDate`**, the next event.

What this settles:

1. **Meridian must mirror Crew's rule, not invent one.** The even split of a reserve total (OS-048b's `derived` branch) is retired as a model: it is not what Crew does, and on live data it is also arithmetically refuted, as is a proportional split and a nearest-due-first waterfall. A bill's contribution does not change when another bill joins the reserve, which is what a split of a bucket would do and the proration does not.
2. **The deterministic schedule is already described by Crew's own fields.** `reservedBy` is the deadline; `nextFundingDate` plus the plan's cadence and anchor enumerate the events; `estimatedNextFundingAmount` is the per-event contribution. Meridian's job is to compute, present and verify that schedule — not to approximate it.
3. **Provenance stays strict.** `estimatedNextFundingAmount` is a figure Crew *estimates*, not money Crew holds; `reservedAmount` is what it holds now. A projection built from the estimate must be labelled as Crew's estimate/forecast and must never be shown as an observed balance, and `totalReservedAmount` (observed) must never be derived from it. D-013's order of authority stands: observed beats projected.
4. **Money movement stays bounded.** Computing or displaying a schedule is read-only advice. Making Crew reserve by that schedule is a provider mutation and must go through propose → approve → execute → readback (`meridian/funding_proposals.py::propose_due_funding` is the existing path). Nothing in a schedule slice may write.

Explicitly still open, and not to be guessed: how `totalReservedAmount` is derived, how Crew chooses which bill holds the balance, and what the reserve-level `estimatedNextFundingAmount` means. The **`2026-10-02`** funding event converts all three from inference into measurement, from data Meridian already refreshes every 15 seconds.
