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

1. **The Crew Income Source is not read at all.** `meridian/providers/crewwork.py` maps the
   bill reserve, pockets, autopilot, virtual cards and the spend-pocket config, and contains
   zero references to income, paycheck, payday, earning or deposit. There is no income surface
   in the adapter to link to.
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
  all, which is the owner's stated model.
- **Costs:** a new provider read, a migration of the local paycheck config into a projection of
  it, and decisions the owner has to make — allocation semantics (which bills a payday covers)
  and recurrence authority (who wins when the configured cadence and the observed deposits
  disagree).
- **Verdict:** this is `OS-048`, and it is the target. It cannot be built on a guessed rule.

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
2. **Recurrence authority:** if the configured cadence and the observed deposits disagree, which
   is the truth the app reports?

Until those are answered, the dial's `fundingStatus: "unknown"` for bills and the empty evidence
ticket on a projected paycheck stay as they are: honest reports of a missing pipeline rather
than defects to be papered over.
