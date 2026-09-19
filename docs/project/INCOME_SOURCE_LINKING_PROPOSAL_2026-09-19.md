# Income-source linking rule — proposal awaiting owner approval

**Status: proposed, not approved. Nothing here is implemented.**
Raised 2026-09-19 at `6ebf854`. Ledger: `OS-048`. Owner ruling recorded in
`docs/project/CURRENT_STATUS.md`.

Slice 3 of the active work is "wire `observedAt`/`evidenceIds` on projected income
occurrences to the Crew-observed transaction that anchors them, **on an explicit
owner-approved linking rule**". The rule is the owner's call, because a wrong rule asserts a
false relationship between two money records. This document exists so that decision can be
made from evidence rather than from the code.

## What is verified, and why it changes the question

1. **The Crew income source is not *ingested*.** `meridian/providers/crewwork.py` maps the
   bill reserve, pockets, autopilot, virtual cards and the spend-pocket config, and contains
   zero references to income, paycheck, payday, earning or deposit.

   **Corrected in round 2, and it changes this proposal's cost estimate.** Crew *does* expose a
   paycheck funding plan and the connector already requests it: `readback_funding_plans()`
   parses `expenses...accounts[].billReserve.fundingPlans[]` and returns `{"id", "name",
   "amount"}` (cents) with the parent `billReserveId`. It is fetched only to verify a write and
   then discarded. So the missing piece is ingestion and identity, not a provider read.
2. **The dial's Paycheck is a local hand-set config.** `meridian/paycheck.py` is, in its own
   words, a "single paycheck config (cadence, amount, next date)". That is where the
   `+$1,663.00` projection comes from — not from Crew.
3. **The owner renames the income source.** "State of New Hampshire" → "Veteran's Home", in
   Crew. So any rule keyed on a deposit's merchant text breaks the next time it is renamed.

Consequence: `observedAt: null` and `evidenceIds: []` on a projected paycheck are **structural,
not an omission**. There is currently no record that both (a) is the projection's true origin
and (b) is an observation. A rule that simply filled these fields from the nearest matching
deposit would be inventing a relationship the system does not have.

## The three candidate rules

### Option A — cite what actually generates the projection (truthful today, no new authority)

The projection cites the local paycheck config it came from, and says so: `source: "manual"` /
configured, with `observedAt` still null and no deposit claimed as evidence.

- **Gains:** nothing asserted that is not true; implementable immediately; no new authority.
- **Does not gain:** the Crew linkage the owner wants. The row would say "from your configured
  paycheck", which is accurate but is not evidence about their money.
- **Verdict:** only worth doing if the owner wants the empty evidence ticket to stop being
  empty *before* the real fix. It should not be mistaken for the real fix.

### Option B — ingest the Crew Income Source and key on its record (the real fix)

Read Crew's income source, key the paycheck on that record's id (never on merchant text), and
let projected occurrences cite the source record plus the observed deposits that fall on its
cadence. This is the same shape as the bill side, where `reservedAmount` and `anchorDate` come
from Crew rather than being re-derived locally.

- **Gains:** the rename propagates automatically, because the identity is a record; the
  evidence is real; and per-bill funding ("funded by Veterans Home") becomes expressible at
  all, which is the owner's stated model. The plan already carries a complete cadence
  (`frequency`, `frequencyInterval`, `anchorDate`), a title, an amount and the reserve it funds,
  so nothing about the cadence has to be invented or re-derived.
- **Costs, revised down twice:** no new provider read is needed, and the write side already
  exists and is readback-verified (`create`/`update`/`delete_crew_paycheck_funding_plan`). What is
  needed is persistence for the plans, a decision on whether the local paycheck config becomes a
  cache of the plan or is retired, and the owner's answer on recurrence authority.
- **Partly self-answering:** allocation may not need a per-bill assignment the owner maintains,
  because a plan is attached to a bill reserve and the reserve holds the bills. "Which bills does
  this payday fund" can follow from reserve membership. That still needs the owner to confirm it
  is the intended meaning rather than a coincidence of the data model.
- **Verdict:** this is `OS-048`, and it is the target. It is closer than the first draft said,
  and it still cannot be built on a guessed rule.

### Option C — forecast from observed deposits (no Crew income surface needed)

Derive the expected paycheck from the deposit history and cite those deposits as evidence.

- **Gains:** honest without new ingestion: the evidence really is those deposits.
- **Costs:** it presents a **forecast** as the expected paycheck. The standing rule is that a
  forecast must never be presented as a fact, so the surface would have to label it as derived,
  and the owner must approve that framing.
- **Verdict:** viable as the interim, but only with explicit forecast labelling.

## The recommendation

**B, with A as a strictly-labelled interim and C not used to fill the row.** A is safe but
cosmetic; C risks a forecast reading as an observation; only B gives the owner the model they
described. The two questions that gate B are recorded on `OS-048` and are the owner's to
answer:

1. **Allocation:** when a payday funds several bills, is the relationship "this payday covers
   these bills" a per-bill assignment the owner maintains, or a derived split of the total?
   (`billReserveId` on the plan suggests the reserve's membership may already be the answer.)
2. **Recurrence authority:** the plan carries its own cadence, so a Crew plan and the local
   `paycheck.py` config are two copies of the same idea. Confirm that the plan should become the
   single source of truth (with the local config retired or reduced to a cache), and that where
   observed deposits disagree with the plan's cadence the app reports the plan and shows the
   deposits separately, rather than silently preferring one.

Until those are answered, the dial's `fundingStatus: "unknown"` for bills and the empty evidence
ticket on a projected paycheck stay as they are: honest reports of a missing pipeline rather
than defects to be papered over.

**What changed across the two drafts of this document, stated plainly.** It began as "add a
provider read to discover the income source". It is now "persist a surface the app already
fetches, and display a record the app can already write". The owner's decision is correspondingly
smaller: not whether to build an integration, but whether the Crew funding plan becomes the
single source of truth for the cadence.
