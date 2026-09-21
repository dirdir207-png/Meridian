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

**§3's `derived` tier was RETIRED on 2026-09-20 by OS-056, implementing D-015 §1.** `_reserve_figure` now
returns `observed` or `unknown` only — the even split of a reserve total is no longer computed, stored in a
payload, or rendered, and `"observed"` is the only basis the client will state. Do not re-introduce a
derived per-bill share: it models something Crew does not do (the total is the *sum* of Crew's own per-bill
allocations), and while it existed it could have handed an unreported bill a share of other bills' money
(OS-055). A per-bill amount that Crew did not report is now stated as unknown, and the honest projection
beside it is Crew's own per-event estimate.

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

Explicitly still open, and not to be guessed: how `totalReservedAmount` is derived, and how Crew chooses which bill holds the balance. The **`2026-10-02`** funding event converts both from inference into measurement, from data Meridian already refreshes every 15 seconds.

**THE FUNDING DERIVATION AND THE EARMARKING RULE — owner's account, 2026-09-20, with the verifiable parts verified.** The owner describes the funding event as an ordered allocation out of **Checking**, which is also the reserve's only source:

1. The **paycheck** lands in Checking. (`billReserve.settings.funding.subaccount` = **Checking**, confirmed in the stored payload — "the reserve only pulls from checking".)
2. **Bill allocations** are set aside into the reserve per bill — the per-event proration Meridian already mirrors, which matched Crew to the cent on all five real bills.
3. **Pocket transfers** move the configured amounts out to the pockets. The owner says this is a **setting**.
4. **Whatever remains in Checking above the sweep threshold is swept into the reserve.** This is a real, named rule in the payload — `SWEEP_EXCESS`, on a condition matching the **Checking** subaccount, triggered by `ACCOUNT_BALANCE_UPDATED`, not paused and not broken: *"Sweep Excess Checking Funds … Removes funds over 1800 in the checking pocket"*. A second rule, **Round Ups** (`ROUND_UP_TRANSFER`, `roundToNearest: 100` = $1.00, into the Fun Money pocket), exists but is `isBroken: true`.
5. **At the observed event the sweep produced nothing**, and the owner's explanation is that the pocket-transfer component *exceeded what was available after the bill allocations* — so Checking never showed an excess. Their sharper point is the risk: **without that pocket-transfer rule, the residual would have been swept and the whole paycheck would have gone into the reserve.**

### What this settles, and what it deliberately does not

**Settled.** The reserve is fed by a **residual sweep** on top of per-bill proration, not by a per-bill split of a bucket; the reserve draws only from Checking; the sweep is a real configured rule; and the pockets claim the residual before the sweep can. This is consistent with the stored observations — Checking `-96.61` (no excess), the reserve unchanged by any sweep, and the per-bill figures matching Crew to the cent.

**One tension left deliberately open, recorded so nobody smooths it over.** The owner's step 2 says bills are allocated into the reserve, but the stored attribution does **not** look like a per-bill ledger: **Rent alone holds the entire reserve** (`funded_amount` = `1097.10`), while its own per-event need is only `663.27`; the other four bills hold `0.00` despite carrying per-event estimates of `46.72 / 34.59 / 96.60 / 42.78`. Nor is the reserve a simple accumulation of bill allocations (one event's five allocations sum to `883.96`, so two events would exceed `1097.10`). So the *funding* order above is settled, while **which bill is credited with holding the reserve — and by what rule — remains open**, to be measured at the 2026-10-02 event rather than inferred. Do not assume each bill accumulates its own allocation; the data already contradicts that.

**Not settled, and not to be guessed — two numbers the payload does not expose.** Both are *connector readback gaps*, not mysteries about the owner's setup:

- **The sweep threshold.** It appears **only in the rule's human description** (`over 1800`); the rule's condition object comes back as `{}` from the current query, so the field is not selected. Whether `1800` means **$18.00 or $1,800** is therefore **undetermined**. Payload amounts are cents elsewhere (`roundToNearest: 100` = $1.00), which is suggestive but not decisive for a prose field, and a guess here would materially change any sweep model. **Do not pick one.**
- **The pocket-transfer allocation.** Each pocket subaccount returns only `clearedBalance / overallBalance / piggyBanked / goal / status` — no transfer amount, percent, schedule, or goal value (`goal` is `null` on all four). So the "pocket transfer component" is **not readable by Meridian today at all**. The owner's statement that it exceeded available funds is *consistent* with the observations but is recorded as **the owner's account, not a measurement**.

**THE ORDERING IS THE RULE — the pockets claim the residual before the reserve can (owner, 2026-09-20).** The owner's sharpening: *if the pocket rule allocates the remaining funds to the Free to Spend pocket, those funds are no longer available to be pulled into the reserve from Checking.* So the reserve and the pockets are competing claimants on one pool — the paycheck sitting in Checking — and the pocket allocation is applied **before** the sweep. Once money has left Checking for a pocket it is out of reach of the reserve. That single ordering explains the observed event completely: the residual went to Free to Spend, Checking never showed an excess, and the sweep took nothing.

Three consequences Meridian must respect:

1. **The reserve is the *last* claimant on a paycheck**, not the first: it receives only what the earlier steps (bill allocations, then pocket transfers) leave in Checking above the threshold. A projection that ordered the sweep first, or that treated a paycheck as reserve-funding on arrival, would overstate the reserve.
2. **Pocket balances are NOT reserve-funding capacity.** Counting Free to Spend (441.89), Emergency Fund or Fun Money as available to fund the reserve would invent capacity that does not exist — the mirror image of the over-reservation error D-015 already forbids. Reserve-funding capacity is a **Checking-only** quantity.
3. **The reverse is also true and must not be conflated.** Pocket money *is* spendable by the owner (it is their money, and they may move it back to Checking themselves), but the reserve cannot pull it. So Meridian must never answer "can the reserve cover this?" and "can the owner spend this?" with the same number: the first is Checking-and-earmark-bounded, the second is not. The two questions stay separate, and neither may be answered by the account total (1442.38), which mixes the reserve with the pockets and is exactly the figure the reserve-level `estimatedNextFundingAmount` misleadingly carries.

**THE AUTOPILOT SETTINGS THAT DRIVE ALL OF IT (owner-supplied screenshot of Crew's "Autopilot settings", 2026-09-20).** The owner supplied the settings surface behind the derivation above; it is the authoritative description of the funding model, and each consequence below traces to one line of it.

| Setting | Value | Crew's own caption |
|---|---|---|
| SOURCE POCKET | Checking | "For bill adjustments and manual top-ups" |
| SURPLUS POCKET | Checking | "Leftover income will be sent here." |
| EARLY FUNDING (DAYS) | 0 | "Ensure bills and pocket transfers are ready on their due dates." |
| AUTOMATIC TOP-UPS | off | "Keep your reserve on track by pulling from the source pocket, even if that pocket goes negative." |
| OPTIMIZE CASH FLOW | on | "Maintain a smaller reserve by funding strategically. (Recommended)" |

1. **SOURCE POCKET = Checking** is the same fact as `billReserve.settings.funding.subaccount = Checking` and the `SWEEP_EXCESS` rule targeting Checking — three independent surfaces agreeing that the reserve draws from Checking alone.
2. **SURPLUS POCKET = Checking** — "leftover income will be sent here" — is where the sweep's input comes from: leftover income lands in Checking and the rule then moves what exceeds the threshold into the reserve.
3. **EARLY FUNDING = 0 days** means bills *and* pocket transfers are funded **on their due dates, not in advance**. A bill showing `reservedAmount = 0.00` is therefore **normal and expected rather than a shortfall**: four of the five bills sit at `0.00` because their due dates are not here yet. **Meridian must never render "unfunded" as "in trouble" while this setting is 0** — the money is in Checking by design and Crew pulls it on the day. The dial's current "not yet set aside" wording is accurate as *state*; it must not acquire a warning connotation.
4. **AUTOMATIC TOP-UPS = off** means the reserve does **not** force-pull from Checking when that would drive the source pocket negative, so the reserve cannot drain Checking and takes surplus only. This is the rule the owner meant by *"if that rule wasn't there, my whole paycheck would have gone into reserve"*: with top-ups on, the reserve pulls to stay on track regardless of the source pocket.
5. **OPTIMIZE CASH FLOW = on** means the reserve is **deliberately kept smaller** than the bills' total need — "maintain a smaller reserve by funding strategically". So `totalReservedAmount` is **not** "the money needed for the bills" and must never be compared against a sum of bill amounts as though the difference were a shortfall. This also resolves the size half of the tension noted just above: the reserve sitting below the sum of the five per-event figures is this setting working as designed, not an anomaly.

**None of these five settings is visible to Meridian today.** The stored `autopilot` node carries only the two rules, and the pockets facet returns balances only — so Meridian currently cannot read the settings that define the funding model, and must not infer them (see OS-059). What Meridian *can* honestly say today is what is observed: the reserve total, the per-bill figures, the next funding date, and the sweep rule's existence.

**Why this matters beyond curiosity.** Because the sweep is a *residual* rule, it can absorb a large share of a paycheck; the pocket-transfer setting is what protects liquidity. Any Meridian projection that modelled "sweep the remainder into the reserve" **without** the pocket component would produce a materially over-reserved picture — presenting money as set aside that is not. Meridian models no sweep at all today, which is the correct posture until those two settings are readable; the honest route is to expose them in the connector's query (see OS-059) rather than to infer them.

**THE RESERVE IS A ONE-WAY LOCK, AND IT DOES NOT NECESSARILY COVER ITS BILL (owner, 2026-09-20).** Two further facts complete the model, and both constrain what Meridian may ever do with a reserve figure.

1. **Money cannot be transferred out of the reserve.** It is one-way: bill allocations and the residual sweep move money *in*, and nothing moves it back *out*. The reserve is therefore **never a liquidity source** — not for an action, not for a proposal, and not as an assumption inside any projection. A Meridian action that presumed a withdrawal from the reserve would be invalid by construction, not merely inadvisable, and no proposal may be drafted on the premise that reserve funds can be redeployed.
2. **A bill can exceed the reserve earmarked for it.** The owner's pending Rent payment is `1442.00` against a reserve holding `1097.10` — a gap of **`344.90`** that must come from spendable cash when the bill is paid. So **"funded" does not mean "covered"**, and a funded figure shown beside a bill amount *without* the gap understates the owner's real exposure. Surfacing that gap is legitimate read-only observation; *acting* on it is not — any reallocation to cover it goes through §4's propose → approve → execute → readback path, and never as a side effect of a display.
3. **The pocket allocation is the owner's liquidity guarantee against that lock, and its value is a policy knob.** In the owner's words: *"that's why I have the pocket rule — to ensure I have enough spendable cash, since money can't be transferred out of reserve."* They state it is set **low because they are currently tight**, and will be **raised on returning to a normal budget**. Meridian must treat it as a **variable policy choice it does not judge**: never a constant, never a target to optimise toward, and never something to change automatically.

**Confirmed:** the owner verified both load-bearing Autopilot toggles read correctly above — **AUTOMATIC TOP-UPS = off** and **OPTIMIZE CASH FLOW = on**.

**THE GAP IS RESOLVED BY PAYMENT, NOT BY RE-TARGETED FUNDING (owner, 2026-09-20).** The September Rent obligation (`1442.00`, due `2026-09-19`) is past due with `1097.10` set aside — a `344.90` gap. The owner's arrangement, in their words: *the gap stays open and is automatically resolved by rent being paid for; then my free to spend is reduced by the gap.* Three consequences, all of which constrain the display and the model:

1. **Nothing is re-targeted at the gap.** No future funding is aimed at closing it, and "the reserve is short" is **not** a condition to repair — it is a fact to state. The payment itself resolves it, drawing the shortfall from spendable funds so Free to Spend falls by the gap. Meridian therefore reports the gap and names where the shortfall comes from; it never allocates toward it and never presents it as an error to fix.
2. **The next Rent occurrence is funded normally.** The owner states roughly half from the next paycheck and the remainder from the one after — which is what Crew's own per-event proration already produces (`663.27` per biweekly event against a `1442.00` bill), so Meridian needs no special case here; it mirrors Crew.
3. **Real-world lateness is explicitly NOT modelled.** In the owner's words: *"it is late in real life, meridian and crew don't need to know that."* So there is **no deferred-obligation concept, no lateness flag, and no owner-intent annotation for this case.** The arrangement is that Meridian and Crew both keep mirroring Crew's schedule and stay silent about the calendar reality. This retires the "deferred by owner" design that was briefly considered — do not build it.

**AI-assisted bill maintenance is PROPOSE-ONLY (owner decision, 2026-09-20).** Some bills carry dates that were entered as one-time entries and should recur; the owner expects to have to modify bills, and asked for the AI to help moving forward. The authorised authority is **propose-only**: Meridian may draft the change and the owner approves each one. This reuses the existing propose → approve → execute engine and **adds no authority**; nothing is automatic, and no preapproved-automation class is authorised today (the owner selected "propose-only" over designing one). Filed as **OS-061**.

**OWNER ADJUSTMENTS ARE DATA, NOT LAW (owner framing, 2026-09-20) — read everything above through this.** The owner's sharpest correction to how the preceding notes should be taken: *"Really think of it as owner made one time decisions and adjustments. Once I am not running behind, it will return to a normal state. Sometimes I just need that flexibility."* The split is therefore:

- **Permanent — the mechanics.** The reserve is one-way; it pulls only from Checking; pockets claim the residual before the sweep; `funded` is not `covered`; per-bill funding mirrors Crew's own proration; a shortfall is met from spendable funds at payment time.
- **Temporary — the owner's values *inside* those mechanics.** The low pocket allocation, the Rent shortfall, any due date or amount he adjusts, and real-world lateness are **state the system absorbs fluidly, never rules to encode.** The steady state is a normal budget; today's tight configuration is expected to pass, and the system must return to normal without carrying a scar.

Three obligations follow, and they bind future work:

1. **Never encode a current arrangement as a rule, a special case, or a guessed "intent."** If Meridian needs owner intent it does not have, it asks or leaves it open — it does not infer one from this month's numbers.
2. **When a bill's date or amount changes, the ingested value and the mirrored logic simply follow**, with no code path, test or fixture that assumes the old value. The owner reports this already works this way by design ("the system is designed to fluidly capture these already and apply the underlying logic") — so the requirement is to *keep* it that way, not to add anything.
3. **No doc or test may pin a temporary arrangement as the steady state.** The owner names the live cases himself: **Verizon and Eversource dates *and* amounts are being adjusted now.**

**The concrete case behind that framing — payment arrangements, and why nothing should be built for them (owner, 2026-09-20).** The owner explains what produces those "one-time" entries: **Crew has NO option for a bill with only one due date.** So when a budget is exceeded and he negotiates a payment arrangement with a biller (his examples: Verizon `75.00` due the 22nd monthly; Eversource `210.00` due the 30th), he must either **create a new bill** for the negotiated amount on the new date, or **modify the existing bill one time** — and usually he also **redoes the original bill so the following month starts on the correct date.** His own framing is the requirement: *"These aren't things crew or meridian have to worry about, the underlying budget system still works the same, it's me tinkering with it because budgets were exceeded and I needed to find a workaround."* Three consequences:

- **Explicit non-goal:** no payment-arrangement feature, no one-time-bill semantics, no workaround modelling, and no lifecycle tracking "this bill was modified for one cycle". Meridian ingests whatever bill set Crew holds and applies the same funding mechanics, because those mechanics are unchanged by any of it.
- **Never flag a one-time bill as an error.** A single-occurrence bill is a legitimate owner workaround, not a defect and not a signal to propose a recurrence. OS-061 carries this prohibition; it is restated here because that task's earlier framing implied the opposite.
- **Expect the bill set to change shape and revert.** Extra or modified bills during a tight cycle are normal, and nothing in ingestion, storage, display or tests may assume the previous bill set.

**Income timing is a separate fact from bill dates — and never assert causation (CORRECTED 2026-09-20).** An entry here briefly claimed Rent's due date went `5th → 16th → 18th` and that Crew had moved it. **That was wrong. The owner corrected it: the due date did not change from the 16th in either Meridian or Crew.** What changed was the **direct deposit date**. He switched his direct deposit **to Crew**, which **does not offer early direct deposit**; previously his check arrived at **Envelope Bank on Wednesday** and he moved the money across with **Cash App over two days**. So **the 18th is an income-arrival date, not a due date.** Three rules, and the first two exist because of this error:

1. **Income arrival is modelled separately from obligation dates.** A paycheck's landing day can move for reasons that have nothing to do with any bill — deposit-provider changes, early-deposit availability, multi-day transfer chains — and the two must never be conflated. **Funding-event timing follows income arrival, not the due date.**
2. **Never assert causation.** Meridian states **what it observed**, never **who caused it**, because it cannot know. This very mistake is the proof of the rule: an inferred cause was written down as fact and turned out to be false.
3. **Never assume a stored due date was either the owner's choice or stable.** Rent's `5th → 16th` *was* an owner change; the error was inferring a *second* change from an income shift that had nothing to do with the bill.

**Payment-arrangement bills are ordinary bills that say so (2026-09-20).** The distinction the owner draws — *"bills specifically that say payment arrangement, and normal bills"* — lives in the **bill data itself** (a separate bill such as `Verizon Payment Arrangement`, coexisting with the plain `Verizon`), **not** in a system field. So Meridian must not invent a payment-arrangement type, flag, or lifecycle: it reads names as names. This also means a workaround is often a **new bill that coexists** with the original rather than a modification of it, which is exactly why the bill count can change and revert.

**RESOLVED — what the reserve-level `estimatedNextFundingAmount` means (owner clarification + arithmetic, 2026-09-20).** This was the third open question above, and it is closed rather than still pending. The owner states that `1435.97` is their **total account balance** and `1097.10` is the **actual amount sitting in the reserve** — and the provider's own payload confirms the accounting identity exactly, to the cent:

```
totalReservedAmount (reserve)      1097.10
+ subaccount balances             +  345.28   (Checking -96.61, Free to Spend 441.89, Emergency 0, Fun 0)
= the owner's total account balance 1442.38
```

Two consequences, both of which change how the field may be used:

1. **It is not a reserve figure at all.** Name notwithstanding, the reserve-level `estimatedNextFundingAmount` is an *account-total* quantity — the reserve plus the spendable subaccounts. Treating it as an amount set aside would overstate the reserve by the whole spendable balance (339–345 today), which is exactly the class of error D-015 exists to prevent. It remains **excluded from every arithmetic path**: never a dividend, and `totalReservedAmount` is never derived from it.
2. **It is a lagged snapshot, not a live balance.** On 2026-09-20 it still reported `1435.97` while the account total had moved to `1442.38` — it was `6.41` behind, and the spendable part it was computed against was `338.87` then versus `345.28` now. A fresh provider read confirms it did not track the change. So the field records what the account total was when Crew last evaluated the reserve; it is not a current-balance surface and must never be presented as one.

This resolution lives here and in the source docstrings rather than in migration 025, whose comment still calls the figure "unexplained": **a shipped migration is frozen by checksum and may never be edited** (the 2026-09-11 immutability rule). The stale comment is a known, deliberate artifact of that rule, not an oversight.

**§2's "compute it" is now backed by §2's own fields (2026-09-20, OS-056b).** §2 says the deterministic schedule *is already described by Crew's own fields*, and that Meridian's job is to compute, present and verify it. The first half of that (OS-056) computed and presented it from the plan's cadence and anchor. The second half is now done: migration 025 persists Crew's own `estimatedNextFundingAmount` (per bill and per reserve), `reservedBy` and `nextFundingDate`, so the payload can state **Crew's figure** (`basis: "crew_reported"`) rather than only Meridian's application of Crew's rule (`basis: "crew_estimate"`). §3's provenance rule is unchanged and now enforced in the stronger direction, because §3 also requires the two to be *verifiable*: both values are computed whenever both exist, and a disagreement is reported as `fundingSchedule.divergence` — so a change in Crew's arithmetic becomes visible instead of silently absorbed by the mirror. Verified against a real read (OS-057): all five bills agree with Crew to the cent. The slice stays read-only — no provider mutation was added, and making Crew reserve by this schedule still goes through §4's propose → approve → execute → readback path.


## D-016 — The harness and outside tools are a sanctioned extension surface; the boundary is AUTHORITY, not mechanism (owner direction, 2026-09-21)

Owner direction, verbatim: *"For future features, I want to you to keep in mind the possibility of using the harness agent/tools/mcps as an extension of meridian if possible, so that creatively, those avenues remain open"* — clarified in the same exchange by *"Composio certainly could be one, it just isn't written. Meridian could call poll the harness or dedicated agent to ingest new gmail through composio on an interval and then feed it into the app, there is no reason such an action would be restricted, and why this harness etc was chosen for the project. It just cant currently."*

**This settles a framing error, and the error is the reason it is written down.** I had twice stated as architecture what was only ever a fact about today: that external ingestion is *impossible* because `composio` appears nowhere in the codebase. The owner corrected it: it is **not built, not forbidden**. The distinction matters because "impossible" closes a design space and "unwritten" leaves it open, and only the second is true. A passing observation about the current code is not a constraint on the design, and stating it as one would quietly have foreclosed exactly the avenue the harness was chosen for.

**The decision.** A harness-mediated agent — with its tools, MCPs, and reach into external services — is a **legitimate and intended way to extend Meridian's capability**, and is to be kept available as a design option for future features. Meridian's own connectors stay the in-process path; this is the second path, for what an in-process connector cannot reasonably reach. The canonical example, and the one that motivated it: Meridian the app has no Gmail access (the API tokens are dead), but a scheduled or on-demand agent CAN read Gmail in full and feed the result back in.

**Why this is the right shape rather than writing every connector into the app.** A capability that lives outside the app can be added, changed or retired without a schema change, a migration, or a redeploy — and the app keeps being the thing that owns the ledger while the agent stays the thing that reaches outward. The inversion is the point: the app defines what it needs, the harness reaches for it.

**Four guardrails, and they are the condition of the latitude rather than a tax on it.**

1. **An external capability may READ, and may PROPOSE. It may never mutate financial state.** Only Meridian's constrained executor does that, and it enforces its own rules — it does not trust an input merely because the harness produced it. This is the existing constitutional boundary (proposal → approval → execution → provider verification), applied unchanged. The harness is a *source of information*, never a second write path.
2. **Reaching further does not extend authority.** A feature may not gain permitted actions because an external agent can perform them. If an outside capability makes some action newly *possible*, that is a reason for a proposal and an owner decision, never for a silent new permission. No feature may expand authority as a side effect of being built.
3. **External data enters through the canonical pipelines and keeps its provenance.** Anything an agent fetches is ingested by the same intake the app uses (quarantine, dedupe, content-before-row, blob store, linking), and its origin is recorded. `scripts/backfill_charge_evidence.py` is the worked example: it writes no rows itself, it replays fetched mail through a transport satisfying the same interface as the app's own, and hands it to the same `ingest_icloud_recent` the poller calls. A side-channel write that bypasses intake is not permitted by this decision.
4. **Anything scheduled must be declared as a service, and its liveness stated honestly.** Composio backfill today runs only while an agent session is live; it is not a service and must never be described as one. An interval-driven ingestion is a different piece of work with a real operational footprint, and building it is a decision to be taken deliberately rather than assumed from this entry.

**What this does not decide.** It does not authorise building the harness ingestion service now; it keeps it available. It does not relax any existing rule about credentials, sensitive data, or provider mutation — the lane boundary stands: the harness filters, redacts and queues, and never receives raw credentials, full transcripts, or unnecessary financial data. And it does not make the harness a dependency: Meridian must remain fully functional on its own connectors, so that the extension path is an addition and never a single point of failure.

**AMENDMENT — the surface is wider than the harness, and the boundary is AUTHORITY, not mechanism (owner, 2026-09-21).** The owner extended the principle immediately: *"Outside tools as well, it gives us the greatest service area."* And then gave the case that proves the first draft was drawn too tightly: *"Say no Crew mutation code was possible that we could find, I can still have computer use physically interact with the crew app if approved and logged in, just as an example. I have access to insight AI that has vast agentic possibilities, etc."*

So the surface is **not** limited to the harness, its tools and its MCPs. It includes **computer use** — driving a real UI as an approved, logged-in actor — third-party agentic platforms, and whatever else is reachable. The deciding question is never *which tool* is used, and never *whether the action is a write*. It is: **whose authority does the action carry?**

That distinction matters because guardrail 1 as first written ("may READ and may PROPOSE, may never mutate") reads as a blanket prohibition on writes, and quoted flatly it would forbid the computer-use case — which the owner explicitly wants available. It is therefore restated:

- **Meridian's own authority stays exactly where D-013 put it.** Meridian never acquires a standing capability to mutate a provider. No agent, tool, MCP or computer-use session may act *as Meridian* to change financial state, and nothing in this decision grants Meridian a new permission.
- **Owner-directed action is a different thing, and is already legitimate.** When the OWNER directs an action that carries the owner's own authority — the computer-use example: an approved, logged-in session physically operating the Crew app — that is the owner acting through a tool, not Meridian expanding its reach. It is not a bypass of proposal → approval → execution, because the owner *is* the approver and the actor. The determinism gate in the write model applies: a direct, unambiguous owner instruction executes; interpretation, composition and uncertainty still go through a proposal.
- **`provider verification` is unchanged and is the point.** Because a UI action cannot return a structured result the way an API can, a computer-use mutation is **UNKNOWN until read back**. It must be verified against a provider read afterwards, and nothing downstream may treat it as done before that readback agrees. A write whose effect cannot be confirmed is recorded as uncertain, never as success.
- **These paths carry their own risk and so their own controls**, which is a reason to be deliberate rather than a reason to forbid: the actor is a UI, so it can be ambiguous in ways an API is not, it can click the wrong control, and its actions are hard to make idempotent (D-016 guardrail 3's "no side-channel writes" is the principle here — an unverified UI click is a side-channel write in spirit). Any such path therefore requires explicit owner approval per action or per bounded batch, an audit record of what was attempted and with what result, a stated scope, and the readback above. **Never auto-retry a financial mutation** applies with full force, because a UI retry is the easiest way to double an action.

**What this does not change.** Authority is not extended by any of it: if an outside capability makes some mutation newly *possible*, that is a reason for a proposal and an owner decision, never for a silent new permission. The lane boundary stands unchanged — no raw credentials, full transcripts, or unnecessary financial data cross it. And Meridian must still work fully without any of these paths.

## D-017 — A bill reserve total is a running balance, and it may be negative (owner, 2026-09-21)

Owner direction, verbatim: *"Negative reserve is correct"*, explained in the same exchange by *"I left out intentionally too much in free to spend, so when rent cleared today it left the reserve negative."*

**This is written down because the opposite was assumed, and the assumption broke the product.** Migration 024 declared

```sql
total_reserved_amount REAL CHECK (total_reserved_amount IS NULL OR total_reserved_amount >= 0)
```

on the reasoning that a reserve total is money set aside and therefore cannot be below zero. On 2026-09-21 that rejected a *correct* value: the owner's live sync raised `sqlite3.IntegrityError: CHECK constraint failed` from `meridian/repository.py`'s reserve upsert on **every** read, so no reserve row, no funding plan and no bills refreshed. Migration 028 rebuilds the table without that clause.

**The decision.** A reserve total is **not a quantity of money set aside; it is a running balance** between what was set aside and what has cleared against it, and a balance can go negative — most easily by the owner deliberately leaving too much in Crew's "free to spend", so a large obligation clears beyond what the reserve holds. Meridian must be able to **record and show** a negative reserve.

**Three consequences that follow directly.**

- **A schema that refuses a real state does not prevent the state; it only prevents Meridian from knowing about it.** The refusal did not make the reserve non-negative, it made Meridian blind to it and left its data stale. Refusing to store reality is never the safe option.
- **The value is recorded as reported: never clamped to zero, never made absolute.** Substituting a plausible positive would present a fabricated figure as a measured one — the same rule already binding elsewhere: never present simulations as real balances.
- **`NULL` keeps its meaning, unchanged.** `NULL` still means "the read did not report a total", which is not evidence that the bucket is empty (C01). Only the `>= 0` clause was removed; the distinction between an unreported total and a real `0.0` survives, and a test asserts it survives the rebuild.

**Do not add a CHECK to a value Meridian only *observes*.** The remaining `>= 0` constraints in the schema are on values Meridian or the owner *states* — `commitments.funded_amount`, funding rules, provider reimbursements — where non-negativity is a real invariant of the concept. `total_reserved_amount` was the one place a *provider-reported balance* carried a constraint that only makes sense for an amount. That distinction is the test to apply before adding the next one.

## D-018 — Medallions and Investigator design handoff scope (owner, 2026-09-21)

The owner selected OS-038 medallion artwork and a customer-facing Investigator design for DeepSeek Harness, explicitly excluding desktop Settings. The owner authorized newly created finished artwork and permitted omission of the full icon pack. The five-hour limit refers to Codex subscription usage, not an implementation deadline. The Investigator should remain open to relevant cross-references from the existing evidence work; do not freeze it into a single-document explanation or rebuild ingestion on assumption.

Deliverables and proposed design: `design/investigator-medallions-2026-09-21/README.md`; follow-on implementation is OS-076. Newly generated artwork must be labeled as such, not as original extracted glyphs. User-facing design review and integration remain open; no financial authority or production deployment is granted.

## D-019 — A negative reserve reduces "safe to spend" (owner-reported, 2026-09-21)

**Owner report, verbatim:** *"Important finding, free to spend is wrong. It should be 100. 424.90 Free to spend less 324.90 negative autopilot reserve. I can manually top up the reserve so that free to spend pocket has 100 in it and then it would likely display correctly, but it's a hole."*

The owner's arithmetic is confirmed by Crew's own UI, which shows **SAFE TO SPEND 100.00** beside Free to Spend 424.90 and Autopilot reserve -324.90. Crew already subtracts the negative reserve; **Meridian** was the one misreporting the figure, by reading the raw pocket balance and calling it safe to spend.

**The wrong assumption, stated verbatim in `meridian/services/today.py` and inherited by the dial:**

> *"Crew has already separated bill/obligation money into other pockets, so no further subtraction."*

That holds while the reserve is at or above zero. **It fails when the reserve is negative.** A negative reserve is an **overdraft**: the reserve has consumed more than it held, and the deficit has not yet been moved out of the spendable pocket. So the pocket balance overstates what is genuinely free to spend by exactly the deficit — and the error is in the **dangerous direction**, because a spending figure that claims more money than exists is one the owner acts on.

**The decision.** `safe_to_spend` (Today) and the dial's available-to-spend both subtract the **reserve overdraft**: the sum of ``-total_reserved_amount`` across currently-observed reserves whose total is negative.

**Four consequences, each load-bearing.**

- **Only NEGATIVE reserves count.** A reserve at or above zero is already reflected in how Crew split the pockets; subtracting it would double-count and *understate* the owner's money — the opposite error, and equally wrong.
- **Nothing is clamped.** If the deficit exceeds the pocket, safe-to-spend is genuinely negative and is reported that way (D-017's rule: never substitute a fabricated figure for an observed state).
- **`None` is not a deficit.** An unreported reserve total is silence, not evidence of an overdraft (C01).
- **The figure must explain itself.** The server assembles the breakdown — the pocket, the subtraction, the result and a plain-language reason — rather than leaving the client to re-derive it, because a client that re-derives the number can drift from the server that computed it, which is how this went wrong in the first place. The owner asked for exactly this: *"I want to add a mouse over or clickable on safe to spend that shows how its calculated."*

**Deliberate divergence from Crew, stated so it is not mistaken for a bug.** Crew's Pockets screen totals the pockets the owner has **selected**, so a POSITIVE reserve would *increase* its Safe to Spend. Meridian does not add a positive reserve, because money earmarked for bills is not free to spend. The two figures therefore agree in the overdraft case and Meridian's is the conservative one otherwise. If that ever needs to change it is a decision, not a bug fix.
