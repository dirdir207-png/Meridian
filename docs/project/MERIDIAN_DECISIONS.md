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

## D-020 — Owner-direct in-app edits are excluded from the proposal requirement (owner, 2026-09-21)

The owner, restating a rule he had already recorded: *"actions directly made by me in the app
circumvent the need for proposal, I can directly execute."* This is the third time it has had to be
said, so it is written down here as a decision rather than left in the write model's description.

**The rule.** The gate is intent-confidence and determinism, never *who* initiated. An edit the
owner makes directly in the app, stating an exact value on a single target, **executes** and does
not enter a proposal queue. A proposal is required for what is genuinely uncertain: AI-interpreted
or composed changes, low-confidence values, plan-level changes that move policy money, and anything
scheduled with no human in the loop. **The exclusion is therefore  it covers the owner's
direct, fully-specified edits and nothing else, and a change that widened it to everything would
delete an approval gate, which is the worse failure.

**Where it is already implemented.** `meridian/write_routing.py` classifies on provenance plus
determinism (`OWNER_DIRECT` executes immediately; `_PLAN_LEVEL_TYPES` always propose regardless of
provenance), and `POST /api/actions/mutate` (`app.py:4194`) is the general entry point that calls
`route_mutation(...)` with `provenance` defaulting to `owner_direct`.

**Where it is NOT, and this is a defect rather than a design choice.** Every route built on
`_management_payload` returns a proposal unconditionally, because the sink behind it
(`_meridian_memory_proposal_sink`, `app.py:1299-1317`) calls `action_store.propose(...)` and never
consults the router. That covers **bills, rules, assets and contracts**, so on those surfaces the
owner's own unambiguous in-app edits have been parking for approval. The direct path exists; the
management routes bypass it.

**Consequences.** (1) The payday work (OS-083) reuses `POST /api/actions/mutate` and deliberately
adds **no** parallel proposal-only route; a second path would park the owner's edits again while
looking like progress. (2) Bringing the management routes onto the router is its own slice
(OS-084), not a side effect of a feature. (3) Nothing may widen the exclusion beyond direct,
fully-specified owner intent.

## D-021 — Image generation runs through Runway via Composio; no bespoke image adapter (owner, 2026-09-22)

Owner decision after weighing the two routes: "We'll stick with runway."

The rejected alternative was a purpose-built Harness plugin calling the OpenAI Image API directly. It is a sound design and was declined on NECESSITY, not on quality, because the fact that decides it is that the existing connection already brokers the same models: `gpt_image_2`, `gpt_image_2_5_sunburst` and `gpt_image_2_5_flare` are authorised on the account tier, alongside `gemini_image3_pro`, `gemini_image3.1_flash`, `gen4_image`, `gen4_image_turbo`, `seedream5_pro` and `seedream5_lite`. Writing and maintaining an adapter to reach a model that is already reachable would add a second credential surface and a second failure mode for no capability gain. The adapter's own headline recommendation — GPT Image — was therefore already satisfied by the connection made minutes earlier.

Standing consequences:

1. The route is Runway through the existing Composio connection. It is a THIRD-PARTY service: prompts leave this machine, which the decision authorises. It also spends Runway credits (500 at decision time), so a generation is a SPEND and needs owner authorisation the same way any other spend does. Nothing generates credits unattended.

2. This is established by inspection, not assumption: DSH has NO image-generation capability of its own. A grep for `generate_image` and `images/generations` across `packages` and `apps` returns nothing, and there is no image or vision package in the catalog. The claim that the Harness needs an image adapter is right about the GAP and wrong about the REMEDY, and the distinction is the whole decision.

3. Generated assets follow the delivery convention the repository already enforces through its own guards: one design record per delivery (a README plus an `assets.json` carrying kind, source_reference, dimensions, mode and a sha256 that must be VERIFIED to recompute), a row in `design/README.md`'s chronological index, and the files TRACKED in git. An asset that is generated but untracked works locally and vanishes in any clone; a record that is unindexed makes D-004 answer WRONGLY rather than decline to answer.

4. Being generated is not being INTEGRATED. Delivery and integration are separate decisions, and an asset arriving in `design/` changes no shipped surface.

5. A bespoke image adapter may be revisited for a SPECIFIC need — a model Runway does not broker, or a requirement that generation never pass through a third party. It must NOT be re-proposed as a general quality upgrade: quality was the argument tested, and it did not hold.

6. Mechanics worth not rediscovering: the tool accepts up to three reference images (taggable), which is how the 2026-09-22 calibration ornament was made from the Settings concept, and it returns a task id with an ESTIMATED credit cost, so spend is visible before it is spent. The tool schema confirms `gen4_image` and `gen4_image_turbo` as accepted model constants; the exact string for the brokered `gpt_image_2` family is confirmed on first real use rather than assumed from the tier list.

## D-022 — In the light theme, content boxes carry the dark textured blue and parchment is the page only (owner, 2026-09-23)

Owner direction, reviewing the light theme: *"to avoid washout, I think the best option is keep the background the light color and have the boxes have the same textured blue as dark mode."*

1. In the LIGHT theme `--m-canvas` stays parchment (`#f4ecdf`), and content boxes become the dark textured blue: `#141b32` plus `ink-texture.webp`. Each box therefore flips its LOCAL `--m-ink*`, `--m-border*`, `--m-surface` and `--m-surface-muted` tokens, because a dark box on a light page needs cream ink and a dark control surface inside it while the page keeps dark ink and light controls.

2. This SUPERSEDES OS-043's light-theme rule that "every content surface resolves to the page colour and separation is drawn with hairlines, not fills". Fills are back in the light theme; parchment is now the page only. OS-043's rule stands unchanged for the dark theme.

3. The reason is measured rather than a matter of taste. On a parchment surface the Observatory accent inks read: mint `#a5d4bf` **1.40:1**, slate `#b9c2d2` **1.53:1**, apricot `#f3b272` **1.57:1**, lilac `#c1a9e2` **1.78:1**, brass `#c6aa71` **1.91:1**. Every accent in the system was drawn against indigo and not one of them works on parchment. Keeping the boxes indigo keeps every accent exactly as designed, instead of darkening each one per theme — and it deletes that whole class of problem rather than patching it colour by colour.

4. TWO FAILURES THIS CAUSED, both caught by capture rather than by reading the CSS, and both worth not rediscovering:
   - `.m-account-name` was pinned to `#20263b` by the light-theme block for a CREAM surface. Once its sheet turned indigo, the account name became dark-on-dark and vanished from the Accounts page. A hex pinned for one surface is a bug waiting for that surface to move.
   - Flipping the INK on a box is not enough. Controls inside it kept the light `--m-surface` for their background while inheriting the box's cream ink, so the connection-health buttons computed `background rgb(244,236,223)` with `color rgb(238,228,207)` — cream on cream, invisible. The surface tokens must flip with the ink.

5. Scope is EXPLICIT, not a shell-wide token flip. The boxes are enumerated in the light-theme rule in `observatory.css` so each surface can be verified on its own and unwound on its own. Page-level controls (selects, inputs, buttons, links, hover states) are deliberately excluded: they sit on the parchment page, and darkening them would float dark chrome on a light page. Still parchment as of this decision, and therefore still to do: the advisor and inspector overlays, the Settings hub's detail pane, and Plan's selected-rule panel.

## D-023 — The Plan bill row's collapsed form, and the five measurements that decided its layout (owner direction, 2026-09-23)

Owner direction, verbatim: *"lets make that information fit in a cohesive and visually appealing way ... all the additional info can be added to the drop down, which would then display all of the attached evidence. The evidence Icon can just be an indicator that evidence exists. As it sits, with all the extra info, the next income and add a bill don't fit on the first page."*

Implemented in OS-089 against `docs/project/PLAN_MOBILE_CONCEPT_ALIGNMENT_SPEC_2026-09-23.md` and `design/observatory-drafts-2026-09-08/02-plan.png`. These five points are decisions rather than implementation notes, because each one was contested by a measurement.

1. **One date per row, and the duplicate is DROPPED rather than moved.** The app carried a bill's next date twice: as `due <date>` inside the fact line, and again as the NEXT column. The spec's first draft moved BOTH into the disclosure, which would have left the collapsed row with no date at all while the concept plainly draws `Sep11` under the name. Corrected: the row keeps ONE date — the same `nextDateForCommitment` value the desktop NEXT column renders, so the two cannot disagree — the `due ...` fragment is deleted from the fact line, and on mobile the NEXT cell is not rendered into the grid at all. This also removes `due <date>` from the DESKTOP fact line, which is the one deliberate desktop content change in this slice: the duplication being removed is the desktop NEXT column's own.

2. **The section banner is `Upcoming bills`, and the type tag is removed for bills only.** Owner-confirmed against the concept, and applied to the visible heading AND both `aria-label`s together, because renaming one and not the others gives screen-reader users a different name for the list than sighted users. The `BILL` tag is gone from bill rows, since the banner above them now says what the list is. It is KEPT for every other type: this list can hold a goal — the synthetic fixture carries one and the service can return one — and a bills banner over a goal row would state something untrue. A goal therefore still says `GOAL` beside its name. The heading stays uppercase, which is the app's shared `m-section-label` treatment; the concept draws it in sentence case, and that cosmetic difference is recorded here rather than silently applied to one label out of the whole app.

3. **The status badge rides the DETAIL line, beside the date, and not the name line.** The spec's row diagram puts the badge beside the name, and the owner reported it disappearing on long names (*"like it is on everything but verizon payment arrangement"*). Measured at 420px, the name column is about **144px**. With the row wrapping, a long name pushed the badge onto a second line; with the badge sharing the name's line as a flex item, its 85px left the name about **50px**, which rendered `Verizon Payment Arrangement` and `Verizon Payment` as the SAME visible string — the exact collapse the spec forbids. So the name takes the whole cell and truncates with a prefix ellipsis, and the badge takes the detail line, where it can neither wrap away nor be truncated. `display: contents` on the name wrapper is what lets one line hold the name while the next holds the date and the badge; the wrapper is a plain `div` with no role, so spending its box removes nothing from the accessibility tree. The type tag and the status badge share that area and cannot co-occur: the script renders the tag only for a non-bill, and the badge only from `biller_status`, which `meridian/billers.py` returns as `on_track` for anything that is not a bill.

4. **The one-screen acceptance test was met by compacting the Plan command block on mobile, and by measuring the band instead of guessing it.** The spec's acceptance test — next income AND the add control reachable on one 420x912 screen — is the stated reason for the slice, and the numbers did not support it. On mobile the shell's canvas (`.m-main`, which owns the scrolling) is **68..826px**, and the add control sat at **1427px**. The spec's three changes alone brought it to 879px, still past the fold. Two further mobile-only changes closed it, neither removing a control, a figure or a word:
   - the Plan command block drops the `PLAN` kicker — the word appeared three times above the fold, as the kicker, the headline and the active tab — and the headline comes down from 2.25rem to 1.75rem, which is still larger than the governing concept draws it (the concept's equivalent block is ~153px against the app's 302px);
   - the bills band is capped at **120px**, measured so the income strip is fully on the first screen and the add control's top edge sits 37px inside the canvas. That band shows two rows and scrolls; the concept needs no scroll only because it draws three bills and no coverage card.

   Measured after: income strip **675..777px**, add control top **789px**, collapsed row **61/62px** against 113/114px before.

5. **The medallion material needed no generation.** See OS-087: `kit-2026-09-16/medallion-frame.png` is already a rendered bevelled brass ring with four rivets, and the Plan map's three stations and hub were the last surfaces still drawing their own flat ring from a 2px border plus inset box-shadows. They now layer the real asset, so the flat circle and its doubled edge are gone. The Runway spend the owner authorised for the medallion work was therefore NOT used. It remains available for the genuinely generative half — the engraved glyphs — and per D-021 it must be stated before it happens.

6. **The funding bar belongs to the ROW, not to the disclosure — and the top of the page is compressed further than point 4 allowed (owner, second pass, 2026-09-23).** After seeing the first build on his iPhone Air the owner sent a screenshot and three corrections, quoted verbatim:

   > *"The spacing isn't really working on mobile, bills section is too small, can you make the parchment move closer to the top and bills closer to the parchment so we can extend bills and move the other components up, or is my phone just too small for the same layout as the concept? ... everything is a lot closer together in the concept, even Plan is closer to the Meridian at the top, if need be, I would even remove the Plan and center give every dollar a destination, if needed"*

   > *"Also I would still want progress bars"*

   **His phone is not too small, and that is a measurement rather than reassurance.** The iPhone Air is 420 CSS px wide and 912 tall, which is exactly the `mobile-air` viewport in `MERIDIAN_VISUAL_CAPTURE_SPEC.md` and exactly the concept's own device: `02-plan.png` is 852×1846 at 0.494 scale. The concept fits because its top block is ~148px tall against the app's ~250px, not because its screen is bigger.

   What changed in response, all mobile-only:
   - the funding PROGRESS BAR moved out of the disclosure back onto the collapsed row, as a 2px hairline with a dot marking where the funded share ends — the concept draws exactly this on every bill row, and the spec's §3 had put it in the panel. Exactly one bar exists, so the row and the panel can never disagree about the share. On desktop the bar is a row cell too, which moves it from between the fact line and the invoice entries to directly under the name: one short line, recorded here because the governed desktop diff shows it;
   - the `Plan` HEADLINE is removed and `Give every dollar a destination.` carries the block, centred, which the owner pre-authorised. The kicker was already gone; the workspace is still named by the tab bar's active tab and the document title, and heading structure is preserved by the section headings;
   - every gap between the topbar, the command block, the tab bar and the map is tightened to 6px, and the map's own margins are 0/6px, so the parchment sits close under the tabs and the bills close under the parchment;
   - the income TICKET collapsed from **102px to 68px**: label, date and figure now share one line with the caption beneath, which is the concept's own composition (~55px) and where most of the height the bills section needed had been hiding;
   - the bills band went from **120px to a measured `min(170px, 19svh)`** — two and a half rows instead of one and a half. The `svh` term is deliberate: the owner's phone loses roughly 100px to the status bar and the home-indicator inset that a desktop Chromium preview cannot reproduce, and sizing the band against the small viewport height is what stops it crowding the ticket and the add control on a real handset.

   Measured after, at 420x912 on the isolated preview: map section **191..449** (was 236..495), bills band **473..643**, income ticket **673..741**, add control **753..811**, all inside the canvas (`m-main`, 68..826), with the collapsed row at **69px**.


7. **Everything that carried no information was tightened, so THREE bills fit — and the row's height was never the medallion (owner, third pass, 2026-09-23).** Verbatim: *"Can we get everything a little closer together to allow three bills to show?"* Two findings decided it, both measured rather than assumed:

   - **The collapsed row's height is set by the 44px disclosure toggle, not by the medallion.** Row 1 measured 44px while the medallion is 34px and the name cell 34px: the chevron button's touch-target floor was the tallest thing in the row. That 44px is KEPT. The row came down from **69px to 61/62px** by tightening only padding and the funding bar's own margin, which also brings the row to the concept's own ~60px pitch (`02-plan.png`'s 121px row pitch at 0.494 scale).
   - **The map's box must be SCALED, not narrowed.** Narrowing it to 89% width shrank the parchment and the stations' boxes but not their type, so `Goals $200.00` broke across two lines. The capture caught it; the numbers looked correct. A `transform: scale(0.89)` scales art, stations and type together, so the composition is untouched and only its size changes: **259px → 231px**. The reclaim is a ratio, not a pixel count — the scale wastes 11% of a box whose height is its width / 1.5, i.e. 7.33% of the container width, which is what a percentage margin resolves against. `display: flow-root` on the section keeps that reclaim from being swallowed by margin collapsing.

   Everything else taken back is a padding or a margin that carries no information: the shell's 24px canvas pad → 6px, the tab bar's 16px bottom margin → 0, the 8px between rows → 4px, the funding footer's 12px → 6px. **No control, figure or word was removed.** Measured after, at 420x912: row 61/62px, band **200px showing three whole rows** (three rows need 193px of the 198px client box), map section 157..387, ticket 637..705, and the add control's bottom at **823px, still inside the canvas (826px)**.

   **One implementation lesson worth keeping, because it fails silently.** The third pass overrides rules declared earlier in the same `max-width: 600px` media query at the same specificity, and CSS breaks that tie by ORDER. The first attempt put the overrides earlier, so the row margin simply did not move — no error, no warning, and the measurement was the only thing that showed it. The block is therefore declared last in the sheet, is labelled as the pass it is, and a guard asserts its position.

8. **The plan map's second station becomes GOALS, not "Unfunded commitments" (owner, 2026-09-23).** Owner: *"I could make a goal for say, vehicle registration. Its not a bill, but I want to build funds toward it all year- this would be a pocket goal instead of a bill"*, and on the choice: *"I agree with switch to goals"*.

   **This is a data change, not an icon change, and the analysis below is why it must not be treated as a swap of labels.** The concept (`02-plan.png`) and the Observatory kit's own map specimen both name the three stations **Bills / Goals / Available**. The live service instead emits `Committed to commitments` / `Unfunded commitments` / `Available` (`meridian/services/plan.py:496-502`), so the concept's mountain mark could never appear on a real plan.

   **A correction to the first reading of this, recorded because the wrong version is the tempting one.** It looks like the map mixes cash with a shortfall and therefore fails to sum. It does not: `plan.py:447` defines `available = max(0, cash_total - committed - unfunded)`, so the three segments partition `cash_total` by PURPOSE — money already moved to commitments, money still needed for commitments, and money free of either. That is coherent, and `Available` here means "free cash net of obligations", not "money in the account".

   The consequences that make this a real slice:

   * **`unfunded` must keep subtracting from `available`** even after it stops being a station, or the map's Available figure would start overstating genuinely free cash — a silent change to a financial number, which is exactly the class of change that is never a side effect here. `obligations.unfunded` already carries the figure (`plan.py:474`) and the per-bill callouts and the ticket already show it, so nothing is lost by removing the station.
   * **Goal money is pocket money.** A goal in Crew is a target on a pocket (`createSubaccount` carries `goal` and `targetAmount`; `meridian/crew_commands.py:32,167-175`), so the Goals station's figure is the balance held in pockets that carry a goal. Those balances are part of `cash_total`, so the partition must be re-derived rather than appended to, or the map would double-count pocket cash.
   * **The read path does not carry the goal value yet.** `meridian/providers/crew.py:12-20` requests `subaccounts { id displayName name overallBalance isPrimary }` and no `goal`, and `meridian/services/accounts.py` has no pocket accessor. The provider query and its normalisation are the first thing to extend.
   * **Do NOT extend `app.py:~1776`.** There is a second, legacy path that fetches subaccounts over its own direct HTTP call with its own credential helper, requests `goal`, and then only sums BALANCES of non-checking pockets into a variable called `total_goals` — so it neither uses the goal value nor is named for what it does. It is a pre-existing duplication, not a foundation: the new figure goes through the provider layer, and the legacy path is left exactly as found unless separately scheduled.

## D-024 — ONE money rule: everything you have, less every pocket you set aside (owner, 2026-09-25)

The owner's order: *"make Today and Plan publish one 'money you can spend' number instead of two."*
The rule is his, stated before any code was written: *"the safe to spend figure is calculating by
taking the total amount of funds in the account and reducing it by all obligations where funds have
been tucked away ... Available balance, or total balance, less bill reserve (a collective
expense/bill bucket) less goals/other not immediately spendable buckets"*, and on the goals term:
*"should be money sitting in pocket."*

**The rule, in one place — `meridian/services/safe_to_spend.py`.**

```
total     = Σ money accounts (cash, checking, savings, pocket) + reserve   [reserve SIGNED]
set aside = every active pocket EXCEPT the spend pocket, positive balances only
amount    = total − Σ set aside − max(0, reserve)                          [NEVER clamped]
```

**Why the reserve is entered SIGNED, and why that is not a detail.** Crew holds the reserve at
ACCOUNT level, outside every pocket — D-015's own arithmetic on the live read: reserve `1097.10` +
`345.28` across the four subaccounts = `1442.38`, "the owner's live total to the cent". A pool built
from account rows alone therefore omits it entirely, and subtracting it as well would double-count it.
Entering it signed means an overdrawn reserve (`-324.90`) lowers the total by exactly the amount the
old deficit term removed: **the owner's `424.90` against a `-324.90` reserve is `100.00` from one term
instead of two.** A reserve that HOLDS money nets to zero inside the total and is reported as its own
named line — the owner's worked example (total `1000`, bill reserve `100`, emergency fund `100` →
`800`, not `900`).

**The premise this replaced was false, and it was falsified by artifacts rather than by argument.**
The pending ledger entry asserted that "Plan already implements the owner's rule", and on that basis
Today was to adopt `plan.py`'s arithmetic. Three measured facts say otherwise:

- `plan.py:448-455` built its base from `cash`/`checking`/`savings` **only**, while
  `meridian/providers/crewwork.py:540` types every non-primary Crew pocket as `"pocket"`. The sets are
  disjoint, so the station subtracted goal-pocket money from a base that never contained it — while the
  comment above it claimed the opposite ("their current balances are already inside cash_total"). The
  repo's own fixture proves the base: `tests/meridian/services/test_plan.py:236-255` could only sum to
  `1500.00` because the `250.00` pocket sat OUTSIDE the base it was subtracted from.
- Plan's bill term was `committed + unfunded` with `committed = Σ min(funded, target)`, which cancels
  exactly, i.e. the term was arithmetically `Σ target`: **every bill's full amount, funded or not.**
- Plan could not see the overdraft at all. A negative reserve exists only in
  `crew_bill_reserves.total_reserved_amount` (what migration `028` permits); `commitments.funded_amount`
  is still `CHECK >= 0` and nothing copies one into the other.

Adopting it would have moved the owner's headline to `0.00` while the pocket he spends from held
`15.45` — the unification would have been an adoption of a defect. **The recommendation was withdrawn
before any file was touched, and the correction is what this decision records.**

**Superseded explicitly. Each is superseded as rule; the original text is left in place, unedited,
because the history of a rule is part of the record.**

- **D-019 rule 1 ("only NEGATIVE reserves count") — SUPERSEDED as mechanism.** It was a workaround for
  a base that did not contain the reserve. The reserve is now inside the total, signed, so both signs
  are handled by one term and neither can be double-counted. Its *purpose* is met more strictly: a
  negative reserve reduces the figure, a positive one does not inflate it.
- **D-019 rule 2 ("nothing is clamped") — REAFFIRMED, and now enforced in both workspaces.**
  `plan.py`'s `max(_ZERO, ...)` is removed and `plan.js` no longer floors the figure in prose. Under
  this rule the only way to go negative is a genuinely negative total, i.e. a real overdraft.
- **D-023 point 8's "`unfunded` must keep subtracting from `available`" — SUPERSEDED.** Money the owner
  has not yet set aside is not subtracted from what is free to spend; the obligation figures stay where
  that decision already said nothing is lost by removing the station (summary `unfunded`,
  `coverage_ratio`, `first_shortfall`, the per-bill views, the callouts and the ticket).
- **D-023 point 8's partition — SUPERSEDED by the same partition, corrected.** The three stations no
  longer partition a base that excluded pockets: `cash_total` is now the account's total, and the
  stations are **Bills** (the reserve), **Goals** (every other set-aside pocket) and **Available** (the
  shared figure). They sum to the published base by construction, which the agreement test asserts.

**What did NOT change, stated so it is not read as scope.** `unfunded`, `coverage_ratio`,
`first_shortfall`, the timeline and its shortfall projection, the funding model's own cash events, the
per-bill `funded`/`target` views and every action path are untouched. No migration, no route, no
provider write, no deployment, no authority change: this is read-only arithmetic on observed values.

**Two consequences that must not be discovered later.**

- **The spend-pocket question is now MORE load-bearing on Today, not less.** Pocket accounting has to
  exempt the pocket the owner spends from, so OS-113 (identify it by Crew's own
  `selectedSpendSubaccount`) and OS-112 (the owner's selection surface) remain prerequisites. When it
  cannot be identified, NO pocket is treated as spendable and every one is named as set aside —
  visible, conservative, and never the direction that presents earmarked money as free. A rename is
  also no longer a silent basis change: the same rule runs, and the affected pocket simply appears as
  a line.
- **The label vocabulary moved with the rule.** The base line is `Total balance` — it names the BASIS,
  not a pocket — and every subtraction carries its pocket's own Crew name (the owner's OS-079 wording,
  which instructed exactly this). OS-079's separate `Cash accounts` label existed because that branch
  had a different basis; under one rule the basis is the same quantity, so the lines carry which
  pockets were set aside and the label no longer implies a basis change that does not happen.

**Verified.** Whole `tests/` tree green, lint clean, and `tests/meridian/test_safe_to_spend_agreement.py`
builds BOTH payloads from one seeded database and asserts they state the same figure, so the two
workspaces cannot drift apart again. Rendered at 420x912 DPR 3 in both themes: the owner's example
`800.00`, his D-019 case `100.00`, an overdrawn pocket `-83.14`, the map `-120.00` with no breakage.

---

## D-025 — Which pocket the owner spends from is Crew's own SELECTION, not an English name (owner, 2026-09-25)

**The decision.** The pocket that Safe to Spend leaves spendable is identified by Crew's own
`userSpendConfig.selectedSpendSubaccount`, matched to an account by **Crew's id**. The existing
two-name allow-list stays, demoted to an **explicit, named fallback**: a figure that falls back must
say it fell back. Both halves were put to the owner before any file was touched, because OS-113's own
limit forbids shipping the migration without explicit approval, and he chose "make the selection
authoritative" with "keep the two-name allow-list as a named fallback".

**Why the name had to go, in evidence rather than in principle.** The mechanism is not merely
inelegant; it is measurably ambiguous in the owner's own reads:

| database | what the allow-list matches | what that means |
|---|---|---|
| `gate.db` | `'Safe to Spend'` (active) **and** `'Free to Spend'` (inactive since 2026-09-17) | a list-order match can land on a retired pocket |
| `savings_data.db` | **two ACTIVE pockets both named `'Free to Spend'`** (`Subaccount:99adf76a…`, `Subaccount:edc8cb88…`) | no name-based rule can tell them apart at all |

And the answer was already being fetched and thrown away. `readback_selected_spend_pocket()` reads the
setting with the right semantics (unobserved / none / one / ambiguous) and was used only for write
verification. Run over the owner's real 2026-09-04 capture it returns exactly one id,
`Subaccount:edc8cb88-f234-4321-8a3b-d2790e981a7a`, which is byte-identical to
`financial_accounts.external_id` for the pocket named `'Safe to Spend'` in `gate.db` and
`'Free to Spend'` in `savings_data.db` — the rename itself, and proof that an id-keyed rule survives
one.

**What changes.** `meridian/services/spend_pocket.py::resolve_spend_pocket()` answers the question in
one place and reports its basis: `crew_selection`, `name`, or `none`, with a status recording
`selected` / `selected_unmatched` / `selected_inactive` / `none` / `ambiguous` / `unobserved`.
`safe_to_spend` publishes both in its breakdown, so Today's panel and Plan's map can state which
mechanism produced the figure. The selection is observed at ingest (migration **030**,
`crew_spend_selection_observations`) and dated: newest row wins, and an observation carries its
snapshot, capture time, freshness and confidence.

**Two call sites are FIXED rather than changed, because they were wrong about the pocket.**
`dial.py:89` called `find_spend_pocket(accounts)` with no active filter, so with a retired
`'Free to Spend'` row present its figure depended on row order; `plan.py:97` took the **last** name
match. Both now go through the resolver, and the Plan id map refuses to choose when several active
names match — a blank id routes the write safely instead of writing to a pocket chosen by list order.

**What is deliberately NOT done.** An unobserved facet writes **no row**, never a row saying `none`:
`resolution_for_observed(None)` returns `None` and the store writes nothing, so a failed read cannot
become the claim that the owner has no spend pocket (the C01 rule, applied to this setting). The
name allow-list is not pattern-matched and not extended by inference; it is still a short explicit
list, and a new name remains a deliberate one-line edit. The browser's badge/emblem use of the list
(`accounts.js:78`) is left alone in this slice and recorded as OS-113's remainder with a trigger,
because it publishes no figure and the Accounts payload is the honest place to send the resolution.

**Verified.** Whole `tests/` tree 2098 passed, 102 skipped (only the HANDOFF-staleness guard, which a
clean-tree regeneration satisfies); ruff clean over `app.py meridian/ scripts/ tests/`;
`git diff --check` clean. New: store (9 tests), the real `sync_provider` ingest (8), the resolver (10,
including the two-identically-named-active-pockets case), four `_crew_ids` cases, and the agreement
test that moves Today **and** Plan to `160.00` together when a selection names a pocket the name rule
would have set aside — while the unobserved case stays at `100.00` on the name rule with basis `none`.

**Amended 2026-09-25, by the owner's own clarification — what the setting MEANS, and the blind spot it
exposed.** Owner: *"The spend pocket in crew refers to what pocket the physical card drops from … it
still always [coincides] with free to spend."* Two consequences, both acted on:

1. **The meaning is narrower and more useful than "the discretionary pocket":** Crew's spend pocket is
   the funding source of the PHYSICAL card, per user, repeated on every card. That is exactly the
   question Safe to Spend has to answer — which pocket does the money he actually swipes leave — and it
   is why matching by Crew's id rather than by name is the right mechanism.
2. **It exposed a real blind spot in what D-025 shipped.** The selection also rides the
   `physical_cards` facet (`currentUser.family.parents[i].activePhysicalDebitCard.user`), verified in
   his capture, and `readback_selected_spend_pocket()` read only `virtual_cards`. With both surfaces
   agreeing today (they do — the same `Subaccount:edc8cb88…` on the physical card and all three virtual
   cards) nothing was wrong yet, but a physical card pointing at a *different* pocket would have been
   **invisible to the figure instead of reported as a disagreement.** Closed by reading both surfaces
   at ingest: `readback_selected_spend_pocket(include_physical_cards=True)`.

The flag exists, and defaults to False, because the two callers ask different questions. The money
figure must include the physical card, since a divergence is precisely what it must not miss, and it
records one as `ambiguous` rather than resolving it. Write VERIFICATION asks only "did the write I just
made take effect on the surface it writes to" — reading a second surface there could report a failure
while the physical card merely lags behind a write that succeeded, and a false verification failure on
a money path is worse than a narrower question. Both behaviours are pinned by tests in
`tests/meridian/providers/test_crewwork.py`.

## D-026 — The per-bill reserved amount is the ONE reserve bucket's internal allocation, and it is kept as dated history (owner direction + arithmetic, 2026-09-25)

**The owner's premise, and the arithmetic that confirms it.** Owner: *"Reserve is one bucket, so I'm not
sure it's possible, but you may be referring to its internal bill allocation. If possible, 1."* He is
right that there is one bucket, and the reading makes the history MORE meaningful rather than less:

* his 2026-09-04 capture contains exactly **one** `totalReservedAmount` value — 71098 cents ($710.98);
* the five per-bill `reservedAmount` values in that same capture sum to **71098 cents exactly**, 0 cents
  of difference, so the per-bill figures ARE that one bucket's internal allocation;
* the allocation is **lumpy, not proportional**: Rent held the entire $710.98 while the other four bills
  held $0.00, and on 2026-09-20 the bucket's whole $1,097.10 was again attributed to Rent alone.

**The decision.** Per-bill reserved amounts are recorded as **append-only, dated observations**
(`crew_bill_allocation_observations`, migration 031, `meridian/bill_allocation.py`), one row per bill per
capture, replacing nothing. `commitments.funded_amount` and `commitments.reserved_amount_reported` keep
their existing meaning and behaviour — history is an addition, not a new source of truth. This follows
the pattern migration 030 established for the spend-pocket selection, including the capture timestamp as
the identity, so re-ingesting one capture adds no second entry.

**Why the column was not enough.** `funded_amount` IS Crew's per-bill `reservedAmount`, but it is a
single value overwritten on every sync: the same number that answers "how is the bucket allocated right
now" destroys the answer to "how did it get that way". Observed so far — Rent holding $710.98 on
2026-09-04, $1,097.10 on 2026-09-20, and $0.00 on 2026-09-25 — and until now nothing could distinguish a
bucket that moved because a bill was paid from one that moved because a sync dropped a value.

**C01, encoded rather than remembered.** `reserved_amount` is NULL exactly when Crew stated no amount,
and `reserved_amount_reported` records the silence, so an unstated figure can never be read as $0.00. A
row IS written in that case, which deliberately differs from the selection table (030) where an
unobserved facet writes no row at all: there the whole read was absent, whereas here the bill was
observed and only its amount was silent — the same distinction `commitments` already draws.

**Bounds.** This decides nothing about money and changes no figure. It never treats the reserve-level
`totalReservedAmount` as a dividend (D-015), it does not derive one quantity from another, and a
simulated row must be marked `data_mode='simulated'` so it can never be mistaken for an observation of
real money. It exists so that OS-058's still-open question — *which bill is credited with holding the
reserve, and by what rule* — is answered from a series of dated observations rather than from argument.

**Also fixed in passing, because it is the same defect class:** `sync_providers` (the plural entry point,
and the only path that writes commitments) builds a local wrapper adapter carrying none of the readback
methods `sync_provider` looks for, so an ingest through it left the spend-pocket selection **unobserved**
— OS-113's mechanism silently inert on one of its two entry points. Both observation hooks now run there
with the real adapter.

## D-027 — A negative funding account paired with a positive reserve is Crew's PREORDAINED negative, backfilled by income (owner, 2026-09-25)

**Owner's words:** *"It still lets you top up to reserve regardless"* and *"It's like a preordained
negative and backfill."*

**The model, stated so it is not re-derived as a defect.** Crew permits the Bill Reserve to be topped up
beyond the cash in its funding account. The owner's real data on 2026-09-25 shows the shape exactly:
Checking `clearedBalance = -48077` cents verbatim, the reserve's `totalReservedAmount = 48077` cents, and
pockets holding 11.39 — i.e. the reserve's figure and the funding account's negative are **mirrors of one
another**, and the negative is *intended*, to be made up by the next income. The owner confirms he never
held that 480.77: in this instance it was injected by an authorised experiment, while the
negative-then-backfill **shape** is ordinary product behaviour.

**What Meridian must therefore do, and must not do:**

* **Report it, never clamp it.** D-024's "never clamped" is what makes Today read `-469.38` in this
  state: 11.39 of real money, less 480.77 earmarked beyond it. That is a truthful statement of a
  pre-committed position, so the figure is **not** a bug and must not acquire a floor.
* **Never read the negative as an error, a failed write, or an overdraft to be corrected.** It is an
  advance earmark awaiting backfill, so no repair path, retry, or "fix the balance" behaviour may key off
  it.
* **Never derive the reserve from the account balance, or the account balance from the reserve.** They
  are two views of one movement; deriving one from the other double-counts it. This is the second time
  this pair has bitten: the rule adds the reserve into the total AND subtracts it as a set-aside, which
  is self-consistent only while the mirror is counted too.
* **This is a DOCUMENTED, user-visible feature, not an edge case** (owner, verbatim: *"Thats why you can
  have automatic top up, it fills the bill reserve completely, but leaves pockets negative, it explains
  this directly in the crew app"*). Crew's own automatic top-up fills the Bill Reserve **completely** and
  leaves the pockets negative; the app says so. So a persistently negative figure is a *supported* state,
  and a surface that shows it must explain it rather than look broken. That is a display question for the
  owner, not a rule to invent here.
* **D-015's "AUTOMATIC TOP-UPS = off" is NOT contradicted.** That recorded a *setting* as read on
  2026-09-19; the 2026-09-25 experiment **called the top-up operation directly**, five times. The setting
  and the operation are different things, which is why both records can be true.
* **Meridian cannot currently see that setting, and that is a real gap.** The live snapshot exposes no
  top-up / early-funding / source-pocket field at all (checked 2026-09-25), so Meridian can observe the
  *effect* of a top-up but not the configuration that produces it, and cannot tell an owner why his own
  figure moves. Earmarked in the ledger rather than built here.
* **Keep artificial amounts out of the observation stores.** A reserve figure an experiment injected is
  NOT an observation of the owner's money. When the injected 480.77 is unwound the shape may remain
  ordinary, but the amount must never enter history as `data_mode='actual'` — which is why the ingest
  fix below is committed but deliberately NOT deployed while that injected amount is live.
