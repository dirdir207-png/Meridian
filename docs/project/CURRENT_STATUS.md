# Enhanced SimpleCrew — Current Status

## RESUME HERE — session handoff (2026-09-19, at `f46880a`)

Written so a fresh session continues from the repository rather than from a conversation. This
supersedes the 2026-09-16 RESUME HERE further down, which is kept as history.

### The owner's ruling on funding — read this first

Verbatim: *"All the bills also display funding unknown, the funding should link to a Funding
Cadence setup by the user. I went to check mine in Meridian, which should coincide with the
paycheck in Crew, but I am unable to scroll on the settings page. For instance if I make a
payday that titles 'Veteran's Home', and that is what is allocated toward my bills/expenses,
they are funded by Veterans Home. Which is the 'State of New Hampshire' transaction or the
Income Source in Crew, currently State of New Hampshire in Crew, now changed to Veterans Home."*

What that settles, and what it forbids:

- A bill's funding **is knowable**, and the link is the **Funding Cadence the user sets up** —
  not a per-bill reserve. The dial's `fundingStatus: "unknown"` for bills is honest only while
  that link is unimplemented; the owner expects it implemented, so "unknown" is now a recorded
  gap rather than a settled design choice.
- The funding identity is the **income source / payday**, and the owner **renames** it
  ("State of New Hampshire" → "Veteran's Home" in Crew). Any evidence link must therefore key
  on the source record, never on the merchant text of a deposit, which drifts on rename.
- The observed "State Of New Hampshire" transaction and the Crew Income Source are one thing
  seen from two sides. That is the provenance anchor for a projected paycheck.

### Verified: the Income Source is never INGESTED from Crew

The owner: *"It doesnt appear to pull the Income source from crew."* Confirmed, and it is not a
partial gap -- the surface is absent entirely.

- `meridian/providers/crewwork.py` reads `expenses...billReserve.bills[]` (bills with
  `reservedAmount`), `pockets...subaccounts[]`, `autopilot`, `virtual_cards` and
  `userSpendConfig.selectedSpendSubaccount`. It contains **zero** references to income,
  paycheck, payday, earning or deposit. There is no income surface to read.
- The dial's Paycheck events do not come from Crew at all. `meridian/paycheck.py` describes
  itself as a "**single paycheck config** (cadence, amount, next date)", persisted locally and
  set by hand. That is the source of the `+$1,663.00` projections.

**Correction, round 2 of the same day.** The heading above first read "never pulled from Crew",
and it said there was "no income surface to read". That was too strong, and it understated how
close this is. Crew does expose a paycheck funding plan, and the connector already requests it:
`meridian/providers/crewwork.py::readback_funding_plans()` parses
`expenses...accounts[].billReserve.fundingPlans[]` and returns each entry with its parent
`billReserveId`, "so a plan can be attributed to the reserve it belongs to rather than matched by
name alone". A plan's shape is `{"id", "name", "amount"}` in cents.

That is the owner's model, already in the data: a stable `id`, the payday title as `name`
("Veteran's Home"), the cadence `amount`, and `billReserveId` joining the plan to the bills it
funds.

What is missing is therefore **ingestion and identity, not the read**. The plans are fetched only
to verify a write that just happened, used, and discarded: nothing persists them, so nothing can
cite them, and the hand-set local paycheck stays the only source of the projection.

**And a Crew funding plan IS the owner's "Funding Cadence".** The write path fixes the shape
(`create_crew_paycheck_funding_plan`):

```
{"billReserveId": "res:1", "name": "Cash App", "amount": 42720,
 "frequency": "WEEKLY", "frequencyInterval": 2, "anchorDate": "2026-09-04"}
```

So a plan carries the payday **title**, its **amount** (cents, per the expenses facet's documented
convention, with bills read through `_cents_to_dollars`), its **cadence**
(`frequency` + `frequencyInterval` + `anchorDate`), and the **reserve it funds**. That is exactly
what the owner described, and Meridian can already do three of the four things needed:

| Capability | State |
|---|---|
| Write a cadence to Crew (`create`/`update`/`delete_crew_paycheck_funding_plan`) | **exists**, readback-verified |
| Read a cadence from Crew (`readback_funding_plans()`) | **exists**, but only for write verification |
| Ingest a cadence into the app's own model | **missing** |
| Show the cadence and cite it against a projected paycheck | **missing** |

So the app can already *set up* the owner's funding cadence in Crew and *prove* the write landed,
and still cannot *display* it. The gap is display and identity, not plumbing.

Three consequences, all following from that one fact:

1. A projected paycheck can never cite the observed deposit as evidence -- `observedAt` null and
   `evidenceIds` empty are structural, not an omission.
2. A rename in Crew can never reach Meridian. The owner's "State of New Hampshire" ->
   "Veteran's Home" edit is invisible here, because the local config carries its own name.
3. Per-bill funding cannot resolve either, so the dial's `fundingStatus: "unknown"` for bills is
   the honest report of a missing pipeline rather than a decision anyone made.

### Fixed and committed this session

| Commit | What |
|---|---|
| `e8999eb` | Income rows stop claiming a funding status — the Paycheck row said "Funding unknown" while displaying `+$1,663.00`, which is why the amount could not be found |
| `b166e0b` | Plan stops stamping every commitment "FUNDED" — the owner's card read "Underfunded" beside "FUNDED $0" |
| `4d372cf` | Any control nested in a row owns its own events — fixed "apply to future matching" opening the evidence card; replaces the enumeration that caused it |
| `2368214` | Plan view switch painted a fixed paper cream onto the page, so "Rules"/"Crew" vanished in the light edition |
| `d833f44` | Settings could not scroll on a phone — a clipped middle row, which is what blocked reaching the Funding Cadence at all |
| `f46880a` | `archive_commitment`: local commitments had **no removal path at all** (four stuck "Journey Test Bill" rows) |
| `78bcf87` | Corrected my own over-claim: the funding cadence is fetched, just not ingested |
| `91dabf9` | The paycheck projection stops attributing itself to Crew (`source: "crew"` was false, and only ever announced to assistive tech) |
| `e7874b6` | The expected paycheck is resolved from observations, with `source`/`observedAt`/`evidenceIds`/`basis` from that resolution |
| `ebf30f4` | The outstanding directives recorded for handoff |

From the same session, earlier: the Activity timeline convergence (`22f10e5`, `b256199`,
`2438821`), the space-key fix (`5cd16ee`), and the `:8081` restart record (`8d5a5b7`).

## The owner's rule for expected income — APPROVED 2026-09-19

Verbatim: *"I would say if not enough data is available for an aggregate expected income, it
should default to the value of the last known source (the paycheck from yesterday) for example"*

That is the linking rule this objective was waiting on, and it is a fallback chain rather than a
single source:

1. **Enough data for an aggregate** -> the aggregate expected income, citing the observations it
   aggregates.
2. **Not enough data** -> the **value of the last known source** (the most recent observed
   paycheck), citing that observation.
3. **No observations at all** -> the configured paycheck, labelled as configured.

It maps onto primitives that already exist, which is why it can be built without inventing
anything:

| Rule element | Existing primitive |
|---|---|
| "enough data for an aggregate" | `paycheck_learning._MIN_OCCURRENCES = 3`, already tested |
| "aggregate expected income" | `learn_paycheck()["amount"]` — the median of pay-period totals |
| "the last known source" | the most recent transaction whose `classification_kind` is `income` |
| the source's name | `learn_paycheck()["source"]`, or that deposit's merchant |
| confidence | `learn_paycheck()["confidence"]` |

Two consequences worth stating, because they are the difference between a forecast and a false
claim:

- **Every branch cites a real observation** where one exists, so `observedAt` and `evidenceIds`
  become genuinely meaningful instead of "should be filled in". `observedAt` is the observed
  deposit's time; `evidenceIds` are the deposits used. Nothing is inferred from merchant text
  alone, and the Crew funding plan — which the owner renames — is not the identity.
- **The branch must be visible.** An aggregate and a single last-known value are different
  strengths of claim, so which one produced the figure has to be labelled rather than flattened
  into one number. A fallback presented as an expectation would be exactly the
  forecast-as-fact error this project forbids.

Still unresolved, and NOT answered by this rule: whether the Crew funding plan becomes the
single source of truth for the cadence (`OS-048`). The owner's rule answers *how to compute the
expected amount and cite it*; it does not say the plan is authoritative over the local config.



## The owner's full ruling on income — 2026-09-19, SUPERSEDES the precedence question above

Three statements, verbatim, because each one decides something:

> *"Moving forward paychecks are deposited directly to crew, unlike transfers from cash app etc
> previously, this was the first paycheck to hit directly"*

> *"as such, it should default to that value and moving forward aggregate after 3"*

> *"Additionallly, If I set a payment cadence in Meridian, it should set that cadence as the
> income source in Crew, the same way Crew should be populating the cadence in Meridian. So delete
> should delete it in crew and vice versa. It should remain what it is currently for the
> foreseeable future (unless I change jobs, nothing really should change)"*

> *"The only deviation for Meridian is most likely the aggregation, I'm not sure if crew also does
> that naturally"*

### 1. The payment mechanism changed, which is why the fallback matters now

Paychecks used to arrive as transfers **from Cash App**; they are now deposited **directly into
Crew**, and the first such deposit has just happened. That has a sharp consequence the earlier
notes did not have:

- A learned aggregate over history describes the **superseded** channel. `learn_paycheck` groups
  by merchant and returns one `source`, so a "Cash App" aggregate is the OLD pattern, not the
  forward expectation. Presenting it as expected income would report a mechanism the owner has
  left.
- The new direct deposit is **one** observation, so no aggregate exists yet, and the owner's rule
  applies exactly: **default to the value of the last known source.**
- Aggregation must not blend the two channels. A number averaged across a retired payout route and
  a new one is neither.

### 2. Precedence is RESOLVED: observed-first, aggregate at three

"it should default to that value and moving forward aggregate after 3" settles the question raised
in the section above it: the observed value wins, and the aggregate takes over once there are
three occurrences -- the existing `paycheck_learning._MIN_OCCURRENCES = 3`.

So the expected-income chain is: **aggregate (> = 3 occurrences) -> value of the last known source
-> (nothing observed) the configured value.** The configured figure is a last resort, not the
authority. The owner should expect their `$1,663.00` to be superseded by what the deposits say.

### 3. New requirement: the cadence is ONE record, kept in sync both ways

This is larger than a display fix and is the owner's explicit instruction:

- Setting a payment cadence **in Meridian** must set that cadence as the **income source in Crew**.
- Crew must populate the cadence **back into Meridian**.
- **Deletes are symmetric**: deleting in Meridian deletes it in Crew, and vice versa.
- The value is expected to be **stable** ("nothing really should change" unless the owner changes
  jobs), so the design should not assume churn.

### 4. Aggregation is Meridian's own deviation

The owner expects aggregation to be Meridian-side and is unsure whether Crew does it natively. So
an aggregate that Crew does not hold is legitimate, but it is **Meridian's derivation** and must be
labelled as such rather than presented as a Crew fact.

### Open verification before any of this is built

**Is Crew's "income source" the same object as the `fundingPlans` the app already writes?** The
answer decides whether section 3 is a display-and-sync job on existing primitives or needs a new
provider capability:

- `create_crew_paycheck_funding_plan` / `update_...` / `delete_...` already exist, are
  readback-verified, and carry `{billReserveId, name, amount, frequency, frequencyInterval,
  anchorDate}` — a name, an amount and a cadence, which is what an income source looks like.
- If they are the same object, symmetric delete and two-way sync build on paths that already
  exist and are already proven against the provider.
- If "income source" is a distinct Crew object, the write side needs a new capability, which must
  be added as its own bounded slice with its own coverage record -- not as a side effect.

**Safety, unchanged:** a cadence write is a provider write. It must ride the existing
proposal -> approval -> execution -> provider verification pipeline, and no authority is expanded
to make the sync symmetrical.

### The precedence conflict this rule exposes — needs one more answer

`meridian/api.py::_paycheck_config` is **manual-first**:

```python
manual = PaycheckRepository(graph.db_path).get()
if manual is not None:
    return manual                      # "Prefers the owner's explicit config"
learned = _learned_paycheck(graph)     # only reached when NOTHING is configured
```

The docstring is deliberate about it: *"Prefers the owner's explicit config; when none is set,
auto-learn the typical recurring income."*

The owner's rule is **observed-first with a fallback** — the aggregate when there is enough data,
else the value of the last known source. Those two orders disagree, and for this owner the
disagreement is not academic: they DO have a manual config (the one showing `+$1,663.00`), so
manual-first means the learned leg never runs at all, and it is exactly why their figure cites no
evidence.

Applying the rule literally would therefore **replace the owner's own configured amount with a
learned or last-observed one**. That is a change in whose number the app reports, and it is not
something to infer from a rule about how to aggregate:

- If the **observed value wins**, the configured amount becomes a fallback for when there are no
  observations — and the owner should expect `$1,663.00` to be replaced by whatever the deposits
  say. That is legible as "the app reports reality rather than my entry".
- If the **configured value wins**, the rule only governs when nothing is configured, and the
  owner's figure keeps its current prominence — with the evidence problem unsolved for them
  personally.

Recorded rather than guessed, because the two answers produce different numbers on the owner's own
Today page, and the second one silently changes what "expected income" means.

### Sizing the sync requirement: there is no income-source write in the connector

Checking whether the owner's two-way sync instruction (`OS-050`) can build on existing paths
produced a clear negative, and the repository already contains the precedent for how to treat it.

- `cancel_income_source` exists **only** as a string in `meridian/write_routing.py`'s
  `_PLAN_LEVEL_TYPES` (and a test of the routing model). It is **not** in `app.py`'s
  `allowed_types`, **not** in `crew_write_actions`' executor map, and **not** in the connector.
  So there is no income-source write capability anywhere in the app.
- `update_crew_virtual_card` was retired on 2026-09-14 for exactly this reason, and the recorded
  reason is the governing precedent: *"the connector exposes no write operation for it ... The
  capability to perform the write did not exist, so no readback verifier could have made it work.
  ... would reinstate on: a connector write operation for the card update, plus a readback
  verifier and an owner decision."*

What DOES exist and is already proven against the provider is the funding-plan lifecycle:
`create_crew_paycheck_funding_plan` / `update_...` / `delete_...`, all readback-verified, carrying
`{billReserveId, name, amount, frequency, frequencyInterval, anchorDate}`.

So the owner's requirement splits, and the split is not a matter of effort:

| Requirement | Feasibility today |
|---|---|
| Meridian sets a cadence and it appears as the income source in Crew | **only if** Crew's income source IS the funding-plan object |
| Crew populates the cadence back into Meridian | **feasible** — `readback_funding_plans()` already reaches the field; it needs ingesting |
| Delete in Meridian deletes in Crew | **feasible** for a funding plan; otherwise no capability exists |
| Delete in Crew reflects in Meridian | **feasible** by the existing absence-reconciliation pattern used for bills |

**The single question that decides it:** is the Crew object the owner calls the "income source" the
same object as `billReserve.fundingPlans`? The evidence is suggestive and not conclusive -- a
funding plan has a name, an amount and a cadence attached to the bill reserve it funds, which is
what an income source would look like. If it is the same object, most of the requirement builds on
paths already proven. If it is distinct, the honest answer follows the virtual-card precedent:
**do not add the action type**, because an allowed type with no provider capability can only fail
with `no_executor` after the owner has approved it.


## Handoff additions — 2026-09-19, at `e7874b6`

Two owner directives arrived after the ruling above. Both are recorded here because both were
otherwise only in conversation, and the second one is new work.

### 1. CONFIRMED: the income source IS the bill-reserve funding plan

Owner: *"Yes, it would be bill reserve funding plans, but I think you came to the conclusion
already."*

That is the question that sized `OS-050`, and it resolves it favourably:

- The **write** path the owner requires already exists and is readback-verified:
  `create_crew_paycheck_funding_plan` / `update_...` / `delete_...`.
- The **read** path exists: `readback_funding_plans()`.
- Therefore the `update_crew_virtual_card` retirement precedent **does not apply**. That
  precedent exists for a capability the connector never exposed; here the connector exposes the
  capability, so the work is ingestion, identity and UI rather than a new provider feature.
- Symmetric delete is expressible: deleting in Meridian -> `delete_crew_paycheck_funding_plan`;
  deleting in Crew -> the absence-reconciliation pattern already used for bills.

### 2. NEW: the learning must be governable and resettable

Owner, verbatim: *"you can implement learn check, but starting at yesterday. There needs to be a
nested owner operable setting to reset the learning. If I change jobs and have a different pay
rate, or at a different cadence, weekly vs bi weekly for instance, I shouldnt be including the
learned pay from previous positions"* ... *"so it needs to be governable and resettable if
needed"*.

The requirement, stated as constraints:

- Learning must respect a **floor**: only observations on or after that point count. "Starting at
  yesterday" is the floor immediately after a reset, so a reset makes the previous history
  ineligible rather than merely ignored by accident.
- The floor is an **owner-operable nested setting** — nested inside the income/paycheck area, not
  a top-level control.
- It must be **resettable** without deleting financial records. A reset changes which
  observations Meridian aggregates; it must never delete transactions or Crew data.
- The reason is concrete and expected: a job change brings a different pay rate or a different
  cadence (weekly vs biweekly), and the aggregate must not blend the previous position's pay into
  the new one.

This is a governance requirement about a **derived** number, so it stays inside Meridian: it
governs which observations feed the learning, and it writes nothing to Crew.

Note for whoever implements it: the rule now has TWO exclusions that must both hold -- the
channel rule already shipped (aggregate only the most recently observed channel, so a retired
payout route cannot win) and the floor rule (never look back past the reset). They are
independent: the channel rule separates two live-ish sources, the floor rule separates this job
from the last one.

### Open, in the order I would take them

**Done since this list was written** (do not re-do): slice 3 shipped in `e7874b6` — the expected
paycheck is now resolved from observations with the owner's rule (aggregate the CURRENT channel
at >= 3 observations, else the last observed value, else the configured figure), and the
projection carries `source`, `observedAt`, `evidenceIds` and `basis` from that resolution. The
false `source: "crew"` attribution is gone (`91dabf9`). The local-commitment Delete shipped
(`f46880a`). Settings scrolls (`d833f44`).

1. **`OS-051` — make the learning governable and resettable** (owner directive, not started).
   A learning FLOOR so only observations on or after it count, set by a nested owner-operable
   control in the income area, resettable without deleting any financial record, persisted across
   restarts. Reason given by the owner: a job change brings a different pay rate or cadence and
   the previous position's pay must not be blended in. Note it is INDEPENDENT of the channel rule
   already shipped — that separates two live sources, this separates this job from the last one.
2. **`OS-050` — two-way sync of the cadence with Crew**, now confirmed feasible: the income
   source IS the bill-reserve funding plan, so the write path already exists and is
   readback-verified. Remaining work is ingestion (`readback_funding_plans` is fetched but thrown
   away), identity (key on the plan id, never the name the owner renames), the mirror UI, and
   symmetric delete on both sides.
3. **The Funding Cadence link — the keystone.** Bills should read as funded by the cadence the
   user configured rather than "Funding unknown". `docs/project/MERIDIAN_ROADMAP.md` already
   names the dated-occurrence model as the keystone and as drifting; this is that. Bills are
   funded through a plan attached to a bill reserve, so reserve membership may already answer
   "which bills does this payday fund" -- confirm that with the owner rather than assuming it.
3. **Settings parity** — approved by the owner, still not started. The scroll fix (`d833f44`)
   removed the practical blocker; the remaining one is that the isolated synthetic preview
   (`scripts/preview_observatory_dial.py`) has no Settings route, so governed captures of
   `design/observatory-extension-2026-09-18/concepts/settings.png` are not yet possible.
4. **Remaining "funded" wording on Plan.** The per-row stamp is fixed; the coverage summary
   and the "N% funded" subline still use the word for the same aggregate. Deliberately left
   pending the owner's call, recorded in the `b166e0b` message.
5. **The authored sunburst.** `kit-2026-09-18/icons/sun.svg` is written in this repository, is
   **not** part of the supplied 61-icon Bootstrap set, and is the one file there not covered by
   the LICENSE beside it. Astra has not reviewed it.
6. **The browser-suite baseline is not green and is unexplained**: 43 failed / ~21 passed /
   28 errors with this work stashed and the same with it applied. Treat browser-level
   verification as resting on a reconstructed baseline until that is diagnosed.

### Measured state at handoff (refresh at `ebf30f4`; the numbers below this line are the
### earlier snapshot unless restated)

`feat/meridian-implementation`, HEAD `f46880a`, tree clean, nothing pushed (16 commits ahead of
`origin/feat-meridian-implementation`). Non-browser suite **1264 passed, 1 skipped**; Ruff,
`node --check` and `git diff --check` clean. The `:8081` preview was **restarted after the
`app.py` change** (it has no Python reloader, so `archive_commitment` would otherwise have
failed on click); its connector sync completed `status=complete accounts=6 transactions=100
errors=0`. The `:8093` isolated synthetic preview is the only permitted capture source; never
produce fidelity evidence from `:8081`.

## Repository navigation — 2026-09-18

Added concise directory introductions and overview navigation links. Neutral commit descriptions replace internal commentary in the main page's latest-change rows for the affected directories. All 22 future concepts and the interactive dial description are preserved. Documentation only; Git history, runtime behavior, untracked material, and other checkouts are unchanged. Verification: README links, concept count, GitHub rendering, and diff checks; published-page verification follows merge.

## Full future roadmap restored — 2026-09-18

Owner correction to the landing-page review: all 22 concepts are now individually listed as future features, including financial agents, skill generation, and bounded CFO behavior. Human-facing descriptions remain separate from internal instructions. Verified the names and count against `CONCEPT_COVERAGE.md`, GitHub Markdown rendering, and diff whitespace. Evidence: `docs/project/LANDING_PAGE_REVIEW_2026-09-18.md`. Documentation only; no runtime change or app deployment.

## Repository overview review — 2026-09-18

Reviewed Luna's README at `8f7d424` against the published `main` overview. Replaced the Beacon header with existing Observatory engraving; rewrote the page for human readers; removed internal agent/implementation guidance and local-environment commands; corrected the completed repository rename; separated current features, roadmap, and concept imagery. Detailed product scope remains in the existing project records. Branch: `feat/meridian-implementation`. Evidence: `docs/project/LANDING_PAGE_REVIEW_2026-09-18.md`. Documentation only; no app deployment or runtime behavior change. Publication is tracked in the review evidence.

## RESUME HERE — open work, measured (2026-09-16, at `5c732f9`)

Written so a fresh session can continue from the repository rather than from a conversation. Every number below was
measured, not estimated. Ledger entries: `MERIDIAN_OS_TASKS.json` **OS-035…OS-039**.

**Fixed and verified this round.** The empty evidence ticket's text collision (at `≤700px` the ticket is
`grid-template-columns: 1fr auto` with named areas, and the empty state's two children have none, so they
auto-placed into two columns and overlapped: both occupied `606..682`; now `606..631` / `637..684`). The dial's
left-clipping regression (80px bleed clipped 64px, ~20% of the instrument; now 0px clipped).

**Open, in the order I would take them:**

1. **OS-035 — Today instrument centring, INCOMPLETE.** Space above the dial is `29px` against `233px` below. The
   panel row is as tall as the event-list column and `align-items: start` pinned the instrument to the top.
   `.obs-dial-instrument` already carries `align-self: center`, which moved it `0 → 29px` but did not balance it.
   **The trap:** `align-self` must go on `.obs-dial-instrument`, the grid item — putting it on
   `.obs-dial-svg-wrap` does nothing, because the wrap lives *inside* the instrument. I made exactly that mistake.

2. **OS-036 — connector runs terminate on nothing** (owner-reported on device: "several lines" running straight
   down to no row). Not diagnosed. Lead: `renderConnectors` re-anchors runs after the event rows are replaced
   (`dial.js` `update()`).

3. **OS-038 — remaining concept-reconciliation gaps**, each a bounded slice. **3 of 5 delivered:** the lilac
   wavy title underline (Today/Activity/Accounts; the concepts show none on Plan) on 2026-09-17, the Plan
   bordered tab bar on 2026-09-18, and the rotated/notched/notted Accounts ticket on 2026-09-18. **2 remain:**
   the Accounts connectors as curved dashed paths with an end node each and star-tipped separators, and richer
   medallion glyphs — the last of which Finding 4 records as an **asset decision for Astra, not a CSS fix**. All
   measurements live in `artifacts/astra-fidelity-review-2026-09-16/README.md` → Finding 4.

4. **OS-037 — pointer on "Next day", could NOT reproduce, blocked pending the owner.** In the isolated preview the
   pointer *does* move on Next day (angle `-120° → -60°` over two steps). Two traps worth keeping: do not read
   `x1` as "pinned" (equal `x` across steps is just `sin(-120°) == sin(-60°)`), and rule out a stale cached JS
   bundle on the device with a hard refresh before changing code.

5. **OS-039 — the Accounts rotunda engraving: RESOLVED 2026-09-18.** The owner supplied the dedicated Accounts
   illustration, `accounts-ticket-building.png` (a colonnaded domed archive building with scrolls and an open
   ledger), which now replaces the provisional reuse of the Today dial's `observatory-landscape.png` on this
   surface. Recorded precisely rather than overclaimed: it is the owner-supplied governing art, *not* a
   reproduction of the concept's "rotunda on a rocky knoll". Verified to have real transparency (56.2% of pixels
   fully transparent, corners `(0,0,0,0)`) and to render at 92×92 in its 1:1 box. See `design-qa.md`.

**Standing traps from this round, all of which cost real time:**

- The dark canvas is `#141b32` (measured mean of the four concepts), and Today's own shell is `#161c34`. The
  callout column is a hard floor at **130px** — below that "arrangement" splits mid-word.
- A **one-sided dial bleed adds only clipped area, never visible area** (`wrap spans -b .. track`), so the dial
  grows only rightward. The wrap is `calc(100% + 24px)` / `margin: 0 0 0 -12px`; do not raise it past the 12px
  column gap without a scrim, or the brass ring lands behind "Internet"/"Reserved".
- **Theme resolution and the theme toggle are different code paths.** Probing one proves nothing about the other;
  a passing resolution probe is what produced a wrong "the app is fine" verdict earlier.
- **Luminance, not eyeballing, catches theme-capture failures** — the two passes looked plausible side by side.
- Temporary review tooling lives in untracked `tmp/probe_*.py`; `artifacts/` holds all captures and the Astra
  package and is untracked by convention.

## Astra's handoff landed, and reconciled against the Activity work (2026-09-18)

Astra finished an extension lane and staged it in `design/observatory-extension-2026-09-18`. Landed in two
commits, both **attributed to Astra, not to me**:

- `8ed5d40` — deterministic category expansion + semantic icon pack (9 files)
- `fc747cc` — the design handoff: 4 concepts, 62 SVGs, 3 assets, tokens (73 files, 11MB)

### The trap, and why it was not obeyed

`BUILD_HANDOFF.md:20` specifies **"Dark canvas `#172334`, surface `#202b40`"**. Both are superseded: `#172334`
is the value `0b8fdaa` replaced (its message: lighter and greener than every concept), and `#202b40` is exactly
the surface tint the owner asked to remove *today* and `d03aa48` removed. Obeying that line would have reverted
both.

**Astra's own artwork settles it.** Sampling each new concept against its own content areas:

| concept | page bg | content area | delta |
|---|---|---|---|
| timeline | rgb(18,29,49) | rgb(18,30,49) | **1** |
| review | rgb(18,28,47) | rgb(18,29,47) | **1** |
| settings | rgb(19,28,47) | rgb(19,28,46) | **~0** |

Unified, exactly as the owner described. The stale line is prose the pixels do not support — so the rule is
that **Astra's artwork is the authority, and its prose token list is not**.

`tokens.css` is unaffected and adoptable: it defines only `--obs-action #e99a48`, `--obs-action-hover #f3b272`,
`--obs-action-ink #20263b`, `--obs-unknown`, `--obs-confirmed #a5d4bf`, `--obs-selection #c1a9e2`. **No canvas,
no surface** — so there is no real token conflict, and no second orange should be added beside it.

### The Activity list, reconciled

| owner's Activity item | owner | status |
|---|---|---|
| Ornate icons | **Astra** | **delivered** — expanded semantic icon pack; do not duplicate |
| Icon/category mapping | **Astra** | **delivered** — `CATEGORY_ICONS`, category-first with the internet/wifi case preserved |
| "Approve category" → "Confirm category" | Astra's file | `activity.js` — needs Astra or a coordinated edit |
| Tabs: deeper orange + star above selection | **Builder** | **complete** — `--obs-action`, orange underline, decorative selection star |
| Buttons as tickets (filled / open-outlined) | **Builder** | **complete** — orange confirm/approve plate plus open brass correction ticket |
| Full-bleed lines with stars at each end | **Builder** | **complete** — one full-width brass rule with decorative end stars |
| "N categories to review" banner | **Builder**, blocked | no pending-count exists anywhere in the code — needs a data source |

Also relevant: the handoff's own split — "Timeline = what happened, no approval button on every ordinary row;
Review = what needs a decision, confirm/change is local bookkeeping and **never** bank authorization". That is
consistent with Meridian's write model and governs the delivered Activity build.

### Activity orange actions and ruled tabs delivered

The bounded Activity presentation slice is complete in `activity.html` and `activity.css`: the Activity root opts
into Astra's one action orange (`--obs-action: #e99a48`), the selected tab carries that orange with a decorative
star above it, the full-width brass rule has decorative stars at both ends, and Review actions share a clipped
ticket silhouette. The local category confirmation is filled orange; correction is transparent with a continuous
brass ticket edge. Mint is unchanged as a status colour and no financial semantics, route, provider call, data
contract, or JavaScript changed.

Two defects found in review are fixed in the same slice, both recorded because they were measurement findings:

- **Orange could not carry the selected tab's text in the light edition.** `#e99a48` reaches only **1.95:1**
  against the light page, below even the 3:1 large-text floor. The light edition now paints the label in the
  handoff's own dark action ink (`--obs-action-ink`) at **12.78:1** while the star and underline stay orange. Dark
  keeps the orange label at **7.45:1**. **No second orange was introduced** — that is what the one-action-orange
  rule forbids. The orange cue itself therefore remains **1.95:1 in the light edition** (the same order as the
  pre-existing brass hairline); the readable state is carried by the label, not by the star.
- **`clip-path` severs a normal border at every chamfer**, so the "open ticket" control rendered as disconnected
  strokes, not an outline. Correction now draws two stacked clipped polygons — a brass edge plus a 1px-inset page
  -coloured face — giving one unbroken ticket outline with no extra markup.

The unavailable "N categories to review" strip remains excluded: the Activity payload still exposes no pending
count and this slice does not invent one. The existing "Approve category" copy also remains unchanged because it
is owned by `activity.js`, outside this presentation-only claim.

Verification used the isolated synthetic preview only. `artifacts/observatory-activity-actions-2026-09-18/`
contains Review-state viewport and full-page captures for five governed viewports × both themes. All ten records
show zero horizontal overflow and zero console errors. An explicit toggle probe moved dark → light, with mean
viewport luminance **36.84 → 207.52**; computed styles resolved the fill to `rgb(233, 154, 72)`, the correction
edge to brass `rgb(198, 170, 113)` over an opaque face (`rgb(20, 27, 50)` dark / `rgb(244, 236, 223)` light), and
the two controls to 44px. At 390/420/430 CSS px the two controls stay on one row at 420/430 and wrap at 390.
Keyboard traversal reaches **both** actions:
`:focus-visible` is true, the ring is a 3px inset stroke in `--obs-action-ink` over the orange fill (**6.55:1**
in both editions) and in `--m-ink` over the correction face (**13.5:1** dark / **12.78:1** light). All three
generated stars are present.

### Activity follow-up: icons, page-colour surfaces and the review count

Owner review of the live preview on 2026-09-18 reported three things: "all the icons just
show a question mark", "no icons on the timeline page", and "Time [Timeline] also still
appears to have the lighter box in front of the dark background we did away with". All
three were reproduced and fixed; a fourth item, the review count, was previously blocked
and was explicitly authorised in the same review.

**Every row showed one glyph because the resolver short-circuited.** Live transactions
carry an explicit `classification.category` of `"uncategorized"`. That value is truthy but
is not an assigned category, so `transactionIconName` returned `question-circle` before it
ever reached the merchant patterns — the merchant tables were only consulted for rows with
no category field at all, which the live ledger never has. The resolver now consults the
merchant patterns whenever nothing is assigned or suggested, so the ring identifies the
merchant while the category line still states that no category is known. Measured on the
live preview at 420×912, the ledger went from **one distinct glyph to nine**
(`arrow-left-right`, `arrow-repeat`, `basket`, `fork-knife`, `fuel-pump`, `key`,
`lightning-charge`, `question-circle`, `receipt`) across Circle K, Cumberland Farms,
KeyMe, Shell, OpenAI and the rest.

**The timeline had no glyph at all.** The ringed glyph was constructed inside the
`state.mode === "review"` branch, so the default Timeline tab rendered unadorned text.
It is now built in both modes.

**`bank` was mapped and never shipped.** A CSS mask whose asset is missing draws an empty
ring, which reads as a broken icon rather than a deliberate one. It now resolves to the
kit's `piggy-bank`, and a new guard compares every mapped name against the shipped asset
set so the next one fails at test time rather than on a phone.

**The lighter box survived the token fix.** OS-043 moved `--obs-surface` to `var(--obs-bg)`
and its guard asserted the token declarations — but seven separate rules painted the
retired `#202b40` / `#fffaf0` values directly and never read those tokens. Measured before
the change, `.m-ledger-card` resolved to `rgba(32,43,64,0.78)` against a `#141b32` page,
and the light edition to `rgba(255,250,240,0.9)`. All seven now read the token the fix
moved; borders and hairlines are untouched. Verified across four workspaces × both themes:
every surface resolves to its own page colour — `rgb(20,27,50)` for Activity/Plan/Accounts,
`rgb(22,28,52)` for Today, `rgb(244,236,223)` in light — with zero horizontal overflow.

**The review count now exists.** It was blocked in the previous slice because the Activity
payload exposed no pending count; the owner authorised building the data source. Rather
than add a second definition that could drift, the route derives the figure from the very
queue the Review tab lists, so the badge and the strip cannot disagree with the rows beneath
them. The payload carries `review_count` in **every** mode, because the tab badge is visible
in every mode. The tab shows the concept's filled orange counter (filled orange with dark
ink clears contrast in both editions; it is orange as *text* on the light parchment that
does not), the tab's accessible name becomes "Review, N decisions to review" rather than a
bare "Review 3", and the concept's parchment strip appears in **Review mode only** — the
timeline carries the kit's own banner instead, so the two do not stack.

Recorded limits: the count describes the review queue as currently defined — the most recent
200 transactions, confidence below 0.7 — and is not a claim about the whole ledger.

**The `:8081` preview has since been restarted (owner's instruction) and the badge is live.**
`run_preview.py` auto-reloads templates but not Python, so the process that predated the API
change could not report a count. The restart re-ran its connector sync, which completed
cleanly (`provider=crew status=complete accounts=6 transactions=100 errors=0`), and the live
preview on real data now shows the badge at **8** with the Review tab listing **8** rows — the
figure and the list still come from one queue, so they cannot disagree. The banner's stamp
came back as "Observed activity · Updated Sep 19, 1:50 AM", the real refresh time rather than
the fixture's. The count moved from 12 to 8 because the restart re-synced from the provider;
that is the sync changing the queue, not the derivation.

**The light edition's action colour is the palette's green, on the owner's instruction.**
"Let's do the green or mint on light instead." Orange could not carry the selected tab's
label there (1.95:1), and the earlier answer — dark ink — solved contrast while losing the
concept's "label in the action colour". The light edition now maps the Activity action
triple to `--m-healthy`, which the light Observatory block already defines as `#25644f`:
**5.94:1** as text on the parchment, and the same reversed onto the filled control. The
label therefore stays in the action colour in both editions from **one** declaration —
orange at 7.45:1 in dark, green at 5.94:1 in light — and the earlier light-only override
disappears. No second brand colour was invented and no new hex was added: the two
`#e99a48` declarations are the only orange left, and a guard asserts exactly that.

Governed captures for this follow-up live in
`artifacts/observatory-activity-followup-2026-09-18/` (timeline, authority
`concepts/timeline.png`) and `artifacts/observatory-activity-followup-review-2026-09-18/`
(Review, authority `concepts/review.png`), untracked by convention: five device presets
both editions, ten manifest records each, every one naming a concept file that exists, with
zero overflow and zero console errors. The single most complete frame is the mobile-air
dark Review viewport, which shows the count badge, the strip, the Confirm/Change pair with
their kit glyphs, and the page-colour card at once.

**A row with nothing to confirm now offers one primary control, not a dead one.** The owner
reported the pair as "very subdued or greyed out as inactive", and that was accurate: the
confirmation control rendered `disabled`, so the row's only available action was the least
prominent thing on it. Concept 03 shows a single filled "Choose category" and no disabled
control; the row now matches, and the control keeps `data-review-correct`, so the existing
handler opens the category editor exactly as before — only the emphasis changed. **Nothing
in the review actions is rendered disabled any more**, and the muted `:disabled` styling was
removed rather than left as dead CSS.

The confirmable row now reads **"Confirm <category>"** and **"Change"**, replacing
"Approve category" and "Correct", and both controls carry the kit's own glyphs
(`check-circle`, `pencil-square`, `tag`). `ACTION_ICONS` had been exported from
`kit-icons.js` and **used nowhere**, so Astra's action icons for the Review tab had never
rendered at all. The glyph is a masked span painted with `currentColor`, so it takes the
button's ink and stays out of the accessibility tree; the label keeps the accessible name.

Geometry was tuned rather than assumed: the two controls share a row at 420px (measured
187px + 105px, both exactly 44px — a single line), which needed the basis raised and the
side padding tightened. A larger basis wrapped them onto separate rows, which is not the
concept's layout.

### The timeline's parchment banner

Concept 03 draws "Your money, in order." over an observed stamp, above the day dividers.
The banner is the first Activity surface that states **when** the ledger was observed, so the
honesty rules mattered more than the styling, and they are encoded in the mapper rather than
left to the view.

`activityBannerCopy()` lives in `api.js` beside the existing `freshnessText`, so it is
DOM-free and a Node round-trip exercises every branch instead of a source pattern. It
composes the stamp from the **same** freshness payload the rest of the shell already fetches,
which means there is no second notion of "current" to drift:

- **fresh** → "Your money, in order." / "Observed activity · Updated Sep 8, 9:42 AM"
- **stale** → the same headline, but the line itself says "Last observed … · Not current",
  because the headline read alone would present stale data as current
- **unavailable** → **no banner at all**, because that headline claims an order nothing has
  observed yet

The timeline owns the banner and Review owns the decision strip, so the two parchment
surfaces never stack. The banner reuses the kit's `parchment-ticket.png` at the same measured
80-slice as the Review and Accounts strips, and its roundel and ornaments are the kit's own
`moon.svg` and `star.svg`, masked so they inherit their ink.

One deliberate deviation: the banner **keeps the full date** in its stamp. The concept shows a
time alone ("Updated 11:40"), but the synthetic fixture's newest observation is ten days older
than "today" — a time-only stamp would read as freshly observed. At phone widths the
decorative stars stand down so the stamp still fits one line.

Still open from the same concept: the day-part moon/sun markers on the dividers, the row
chevrons, and the "Ask Virgil about this activity" footer. **The kit ships `moon.svg` and no
sun glyph at all**, and no sun asset exists in any governing design bundle, so it is reported
as a missing asset rather than approximated.

### The timeline's dividers, chevrons and ledger footer

Read directly from `concepts/timeline.png` rather than from notes: each day divider carries a
**crescent moon** on Today and a **sunburst** on Yesterday, the day's name bound to its short
date, a thin gold rule ending in a **four-pointed star**, and every transaction row ends in a
right-pointing **chevron**. The ledger closes with "Ask Virgil about this activity".

**Built.** The dividers now read `Wed, Sep 16 ── ✦` — a named day bound to its short date, a
hairline rule, and the same four-pointed sparkle the Activity tabs already use. The label comes
from a new `dayDividerLabel` in `format.js`, kept separate from `dayLabel` because that one also
feeds the row meta lines and must not move. Every timeline row closes with a chevron: a
typographic mark, since the kit ships no chevron glyph, hidden from assistive tech because the
row already announces "Open details". The ledger closes with "Ask Virgil about this activity",
which carries the shell's **existing** `data-open-advisor` hook — the one `today.js` already
binds to `window.advisorSetOpen` from the advisor FAB — so it adds an entry point without
adding a capability, a route or a prompt of its own. Clicking it opens the real advisor.

**Not built, and deliberately so: the divider's moon/sun marker.** The concept puts a crescent
on Today and a **sunburst** on older days. The supplied icon set is exactly the 61 icons
installed, and it contains `moon.svg` and **no sunburst** — nor does any governing design
bundle. The handoff forbids approximating engraved art, so this is reported as a missing asset
rather than filled with something I drew. The marker slot is left for it.

One recorded deviation: the banner's stamp uses the app's existing middle-dot separator where
the concept draws a bullet, because every other separator in Activity is a middle dot and one
screen should not mix them.

### The concept's crescent and sunburst, and one trigger instead of two

The divider markers are now the concept's own pair: **a crescent on Today, a sunburst on every
older day**, chosen from a single `dayOffset()` so the marker and the label cannot disagree about
which day is today. `dayLabel` reads the same helper rather than repeating the arithmetic.

**The sunburst is authored in this repository, and that is a recorded decision rather than an
oversight.** The supplied icon set is exactly the 61 icons installed; it is **Bootstrap Icons**
(MIT, "The Bootstrap Authors"), and it ships `bi-moon` without `bi-sun`, while no governing design
bundle has a sun either. I searched the npm cache and both checkouts for a local copy and found
none, and there is no internet from this workspace, so the alternative to authoring it was to
wait. **The owner chose to author it.** The file states its own provenance in its header, is drawn
to the kit's metrics (16x16, `currentColor`) **and to its outline weight** -- `bi-moon` and
`bi-star` are the outline variants, so a solid disc would have been the odd one out -- and was
compared beside the supplied moon and star at 8x before being wired in. It is nonetheless the one
icon in that directory **not covered by the Bootstrap Icons LICENSE** sitting next to it, and
Astra has not reviewed it.

The shell's floating advisor trigger now stands down on Activity, where the ledger's own "Ask
Virgil about this activity" footer opens the same panel. Two controls for one panel on one screen
is a duplicate affordance, not a convenience. The rule uses the same `body:has(...)` mechanism
`advisor.css` already uses to hide the trigger while the panel is open, and only the trigger
stands down -- the open panel keeps its own close control.

The fixture gained a row dated to the **capture clock's** day, deliberately: the dividers and
their markers are decided against the browser's clock and governed captures are taken with
`--frozen-clock 2026-09-18T19:50:00-04:00`, so without that anchor a capture shows a fourth
sunburst and never the crescent.

### Two defects in the inline category editor

The owner reported: *"when manually writing a category, pressing the space key brings up the
evidence so you cannot have more than 1 word"*. That was accurate, and it was one line in
`transaction-inspector.js`.

**Spaces were swallowed by the row's own keyboard shortcut.** A timeline row is
`role="button"`, so a document-level listener treats Enter and Space anywhere inside a row as
"activate the row", calls `preventDefault()`, and opens the inspector. But
`openInlineCategoryEditor` does `const container = row` — **the editor is inserted into the
transaction row** — so every space typed into the category field bubbled to that listener, was
prevented, and opened the evidence instead of reaching the input. Multi-word categories such
as "Personal Care" or "Home Office" were impossible to type. The row now activates only when
the row *itself* is the focused target, which is the guard `plan.js` already used. The same
bug also meant the review card's own selection checkbox could not be toggled from the
keyboard: Space on the checkbox opened the inspector instead of toggling it.

**The field opened prefilled with the literal word "uncategorized".** The prefill test was
`category !== "Uncategorized"` — case-sensitive — while the provider writes lowercase
`"uncategorized"`, so the guard missed and the field opened with that placeholder as its
value; saving would have filed "uncategorized" as a real category. It now uses
`categoryIsAssigned()`, the same predicate the ledger, the glyph resolver and the review
labels already share.

Guarded by a browser test that types a two-word category, asserts the space reaches the field
and no evidence opens, and asserts the row still opens the inspector from the keyboard when
the row itself has focus. Baseline check for the wider browser suite: with these changes
stashed it reports 43 failed / 21 passed / 28 errors, and with them 43 failed / 22 passed /
28 errors — the same failures, plus this one new passing test. Those pre-existing failures are
environmental and were not caused by this change.

### Three referenced handoff files are missing

`index.html`, `manifest.json` (provenance, dimensions, SHA-256) and `VERIFICATION.md` (Astra's measured checks)
are **not present**. So the assets' declared hashes cannot be verified and the "148 focused tests" claim cannot
be audited from the handoff alone. `BUILD_SPEC.md` was checked and is *not* missing — it lives in the
2026-09-08 set. Recorded so the next session neither chases them nor assumes provenance was checked.

## The day arc now starts clear of the dial's building (2026-09-18)

**Owner, 2026-09-18:** *"Can we modify the dial so that the lowest point on the left hand side is still above
the building imagery? It defaults into the building for today and is not visually appealing. Where the hand sits
per day to say."*

**Root cause — it was a convention difference, not a widget bug.** The arc ran **−120° … +120°**, so **day 0
(today) sat at −120°**, putting the hand at **(129, 399)** — precisely where the kit's `dial-plate.png` draws its
observatory. The concept is no help on the collision itself: **its dial has no building at all** (verified in both
lower quadrants of `01-today.png`), so the observatory is the kit's addition and there is no authority for how a
hand should treat it.

**Measured the building by ray-casting the plate** (1254px, ring centre 626,632 → viewBox 300,300), requiring an
**8-sample run** of light pixels so the sky's star sparkles are not mistaken for it — a first pass *without* that
run test reported intrusions on the right side where there is no building at all, which is worth remembering.

| | |
|---|---|
| building intrudes into the sky disc | **only between −140° and −110°** |
| reaches inward to | r = **150–182** |
| hand runs | r = **118–198** |
| roofline: inner edge at −110° → −105° | **165 → 283** (near-vertical) |

**Delivered:** `ARC_START` **−120 → −100**, `ARC_END` unchanged. The sweep narrows 240° → 220°, which also stops
the visible rim arc short of the roofline. The hand's **r=198** tip now clears the building's nearest edge
(**r=283** at that angle) by **85 units on every day**, and every day keeps a **full-length hand**. Day 0 sits at
−100°, day 1 at −91.5°, day 2 at −83.1°.

**Why this option.** Three were measured and offered; this was the chosen one. The *narrow* option — clamp the
hand's outer radius at the roofline — was rejected because the hand would visibly change length for the 1–2 days
in that band (at 14 days only day 0 is affected), so it would read as a glitch rather than a design. The *full
concept-arc* rework (today near the top, sweeping clockwise to ~+200°) was declined as too large a relocation.

**The guard reads the constant rather than matching a literal.** `test_the_day_arc_starts_clear_of_the_dials_building_art`
parses `ARC_START` out of the source and fails below **−105** — the measured roofline. Proved to bite by
re-setting it to −120, which fails with the exact diagnosis. The existing geometry round-trip had three endpoint
assertions updated.

**Visible and intended:** every day's position moved by up to 20° at the lower-left end, so the arc is now
asymmetric about the top (midpoint +10° rather than 0°). Drag input clamps to the same new range, so scrubbing
and the rendered positions cannot disagree.

Verified: non-browser suite **1189 passed, 1 skipped**; browser dial file unchanged at its same 6 pre-existing
failures. Captures `artifacts/observatory-dial-arc-2026-09-18/` — 10 files, zero console errors, zero horizontal
overflow.

## The dial is placed evenly now — and my earlier revert was wrong (2026-09-18)

**Owner, 2026-09-18:** *"I am much less concerned with the size of the dial, I just want it evenly placed
vertically."* That single sentence resolves the composition question OS-035 had been carrying: the complaint
was never the dial's **size**, it is its **vertical placement**.

**What I had left them with.** `d0e0cd6` reverted an `align-self: center` on the instrument. That revert was
right that the old rule did not fix the report, and **wrong about what was wanted**: with `align-items: start`
the dial sat **0px** from the panel top with **all 48px** of its row's slack beneath it — 0 above / 252 below,
the worst possible arrangement for "evenly placed". Removing the centring did not merely fail to help; it
produced the extreme.

**The concept settles it.** In concept 01 the dial spans ~**435px** inside a band whose callouts span ~**490px**
— roughly **25px above, 30px below**. Centred, not pinned. The concept has almost no slack because its two
columns are near-equal height; our 48px is an artefact of the rail cap (318px) being taller than the dial
(270px), and `align-items: start` put every pixel of it below.

**Fixed:** `[data-observatory-dial] .obs-dial-instrument { align-self: center; }` at ≤700px. Measured after:
**24px above / 24px below inside the band**, matching the concept's 25/30. Unchanged at 1024px and 1440px,
where the dial (486/620px) is taller than the rail (418px) so the band has no slack and centring is a no-op.

**Why the old objection no longer applies.** The revert's second reason was real: centring made the dial's
position track the event-list length, because the row grew with the list. But `d0e0cd6` *also* capped the rail,
so the band is now bounded and the offset is a derived 24px rather than a drifting one. The objection was true
against the uncapped rail; it is not true now.

**One test had to be reconciled, and it was pointed the wrong way.** `test_long_event_list_does_not_push_dial_down_or_split_amounts`
asserted `dial.y - panel.y <= 8` with the message *"The event list must not vertically center the dial"* — it
**demanded the arrangement you had just rejected**. Its mechanism was superseded by your requirement; its
*reason* (no drift with list length) is preserved. It now asserts the dial sits at the band's centre,
`abs(centred − band_slack/2) <= 2`, which fails both on pinned-to-top (0) and pushed-down-by-the-list.

**What this does not do, stated plainly.** It balances the dial in its own band. It does **not** equalise
space above and below across the whole panel — that still measures 24 above / 228 below, because the controls
row and the evidence ticket sit below the band and `align-self` cannot reach them. Panel-level equalisation
would require the dial's column to span all three rows, which would squeeze the controls and the 130px callout
column into one narrow strip. Worth noting: the concept also has substantial content below its dial band (the
"Bills reserved" strip), so content below is not itself the defect.

Verified: non-browser suite **1189 passed, 1 skipped**; browser dial file back to **6 failed / 13 passed** — the
same 6 pre-existing failures, none dial-placement related. Captures
`artifacts/observatory-dial-centring-2026-09-18/` — 10 files, zero console errors, zero horizontal overflow.

## The Accounts ticket: tilted, notched and dotted (2026-09-18)

**OS-038 item 3.** Finding 4 recorded our summary ticket as *"axis-aligned, square-cornered and plain"* against
a concept that sets it at an angle, punches a semicircular notch out of each side, and insets a fine dotted
border.

**The angle is measured, not guessed.** Two independent features **inside** the concept's ticket agree: its own
top edge (**−3.7°** over 656 columns, robust fit) and the brass rule under the amount (**−3.21°** over 104
columns). The rule is the cleaner, purely internal feature, so the panel takes **−3.2°**. The text tilts with
the panel, because that is what the concept draws.

Built: the rotation; the dotted inset border as `outline: 1px dotted var(--obs-brass)` with
`outline-offset: -14px`, which needs **no third pseudo-element** and stays out of the accessibility tree; and the
two notches as `::before`/`::after` circles in `var(--obs-bg)` at mid-height, so they rotate with the panel and
need no mask-composite support. The kit's nine-slice, scalloped edges and corner rivets are **preserved** — the
treatments are added to that panel, not a replacement for it.

**One deviation, arrived at by measurement.** The notch is **36px**, larger than the ~25px the concept's own
notch measures. The reason is concrete: the concept's ticket edge is **smooth**, so a concept-sized bite reads
instantly, while the kit's `parchment-ticket.png` already carries **~10px scallops** down the same edge — at
22px the notch read as a *missing scallop* rather than a punched hole. Enlarging it is what makes the concept's
gesture legible on the kit's edge. Recorded in the CSS and the ledger rather than left as an unexplained size.

**The rotation was checked for overflow, because a rotated box is wider than the box that laid out:** 388×164 at
−3.2° gives a bounding width of ~397px against a 388px column. Measured **zero** horizontal overflow at
390/420/430px (bounding x=11.7, widths 366.6/396.5/406.5), and the governed capture confirms it at all five
viewports in both themes.

Verified: non-browser suite **1189 passed, 1 skipped** (+1 guard that also asserts the kit's nine-slice
*survives* the change); captures `artifacts/observatory-accounts-ticket-2026-09-18/` — 10 files, zero console
errors, zero horizontal overflow. Presentation only.

## Plan's tabs: the concept's bordered bar, not pills (2026-09-18)

**OS-038 item 4.** Concept 02 draws **one rounded container with a brass border**, divided into **three equal
cells by thin vertical rules**, whose **active cell is parchment-filled with a brass star medallion at its left
edge** — and that container's top edge doubles as the separator between the header and the tabs. Activity keeps
the ruled-underline treatment concept 03 shows; the two workspaces are deliberately different.

Measured on the concept (852px wide, so **0.493** to a 420px viewport): container ~733×82px → **~361×40px**;
active cell **254px**, i.e. an equal third; medallion ~70px → **~34px**. The app had **three pills in a muted
trough** — a different construction, not a different shade.

Built: one rounded container with a `var(--obs-brass)` border and `overflow: hidden` so the parchment clips to
the rounded ends; a 1px brass left border on every cell after the first for the rules; the active cell
parchment-filled with `--obs-paper-ink` (the ticket ink the kit requires on parchment); and the medallion as a
dark disc ringed in brass carrying a brass star mask. Built to **44px** rather than the concept's 40px because
the cells are buttons and 44px is the touch-target floor — a 4px deviation **recorded rather than quietly
missed**.

**Two layout defects were found while verifying, and both are worth keeping.** The cells were **not** equal
thirds (measured 148/119/119): every cell is `box-sizing: border-box`, so a zero flex basis is floored by the
active cell's own 42px medallion gutter. A one-third percentage basis fixed that at the base rule — but the
existing `@media (max-width: 600px)` block carried `flex: 1` (i.e. `1 1 0%`) and **re-imposed the asymmetry at
exactly the widths the concept's equal cells matter**. Both are corrected and both are guarded. Measured after:
**118.7/118.7/118.7** at 390px, 128.7 at 420px, 132 at 430px — labels fitting, zero horizontal overflow.

Verified: non-browser suite **1188 passed, 1 skipped** (+2 guards in `tests/meridian/test_plan_map.py`);
captures `artifacts/observatory-plan-tabs-2026-09-18/` — 10 files, Plan × five governed viewports × two themes,
zero console errors, zero horizontal overflow. Presentation only; no route, data, financial, provider or
authority change.

## The bottom dock: taller, with the concepts' ornate glyphs (2026-09-18)

**Owner-reported:** *"Taller icon dock at the bottom I noticed as well, in the concept. Also with more ornate
icons."* Both halves were measured against concept 01 before anything changed, and the owner was right on both.

**What the concept actually draws.** The dock panel spans `y=1672..1823` of an 853px-wide frame: **152px** tall,
i.e. **17.8%** of the frame's width. It is a **rounded panel inset** from the screen edges (x=17..836, 2.0% each
side) ending 2.5% above the bottom, with a hairline border and **hairline rules between the workspaces**. Each
item **stacks its glyph above its label**. The ringed compass glyph is ~72px = **8.4%** of the width — about
**34px** at a 420px viewport. The current workspace is marked by a lilac rule **under its label**, with **no fill
behind the item**.

**What the app did.** At 420px: dock **65px = 15.5%** of width, glyphs **20px**, labels **12px**, each item laid
out as a **row** with the glyph *beside* the label, and the active marker a bar **above** the glyph. The kit's
glyphs are 16px Bootstrap silhouettes, which read as blobs at dock size.

**Delivered.** Stacked layout (which is most of the height), glyphs 20→**34px**, labels 12→**15px**, item floor
56→64px, the panel reworked as the concept's rounded inset floating dock with hairline rules between workspaces,
the active marker moved **under** the label, and the lilac fill behind the active item **removed**. Measured
after: **76px = 18.1%** of a 420px viewport against the concept's 17.8% — a ratio of **1.02**. Four glyphs were
drawn in-repo in `static/img/meridian/observatory/nav/` to the concept's engravings: a ringed compass rose with
cardinal ticks, a folded three-panel map with a dotted route and a cross, four ascending columns on a baseline,
and a ringed profile. They remain single-colour CSS masks driven by `currentColor`, the existing documented
mechanism — the concept inks the active glyph lilac and the rest muted, which is exactly what that does.

**One test had to be reconciled, and it was the right call.** `test_shell_maps_each_workspace_to_its_supplied_kit_glyph`
hard-coded the kit's filenames, so it failed the moment the owner's request was implemented. Its value was always
the *invariant* — one workspace, one real glyph, both mask properties — not one file's path, so it now guards that
and is renamed `..._to_its_own_glyph_and_the_file_exists`. The kit's Bootstrap files are **not deleted**: they stay
on disk and still serve the surfaces that use them.

**Scope limit, re-measured:** the desktop rail is untouched — 150px wide, row layout, 20px glyphs, no inset, zero
overflow.

**Recorded, not chased:** at 390px the dock is 19.5% of the viewport width against the concept's 17.8%, because
the glyph and label are fixed sizes while the viewport narrows. The concept is a single fixed-width composition,
so this is noted rather than tuned to one width.

Verified: non-browser suite **1186 passed, 1 skipped** (+4 new guards); captures
`artifacts/observatory-dock-2026-09-18/` — 40 files, four workspaces × five governed viewports × two themes, zero
console errors, zero horizontal overflow, light/dark luminance deltas 151–159.

## OS-036 reproduced at last, and the instrument centring reverted (2026-09-18)

**The connector bug is real, and the missing condition was the one recorded as untested: a longer event
list.** `renderConnectors` drew a run for every event in the horizon, on the assumption that every row had
somewhere on screen to land. The rail (`.obs-dial-events`) is internally scrollable, so with a 14-event
horizon its content is **1591px** tall inside a **330px** client box, and **11 of those 14 rows** sat below
the rail's visible area while still receiving a run. Those runs left the dial, ran down past the rail to
`y=1754`, and were cut off by the connector layer's own `overflow: hidden` at `y=746.9` — dashed lines
stopping in mid-air. That is the owner's *"running straight down connecting to nothing, several lines"*.

Fixed in two parts: a run is drawn **only** when its row's centre is inside the rail's visible box, and the
rail re-runs `renderConnectors` **on scroll** so the surviving runs keep following their rows. Bound where
the rail is created, so the listener is discarded with the element `update()` replaces — no separate binding
to keep in sync. After the fix the same page draws **3 runs, each ending exactly on its own visible row**,
and scrolling to the middle and the bottom re-anchors to `ev-7/8/9` and `ev-11/12/13` with every run still on
a visible row.

The behavioural guard was verified to **fail without the fix** (`14 runs for 11 hidden rows`), so it catches
the regression rather than describing it.

**The instrument centring is reverted, and the earlier OS-035 verdict corrected.** Commit `5c732f9` added
`align-self: center` to the instrument to balance the space around the dial. Measured, it does not do that:
the documented 29px above / 233px below only becomes 0/262, because the void the owner is looking at is the
**second panel row** (controls + evidence ticket), which `align-self` cannot reach. What it does do is make
the dial's vertical position depend on the **number of events**: at 390px a 12-event horizon centres a 240px
dial in a 300px row and pushes it 30px down — exactly what
`test_long_event_list_does_not_push_dial_down_or_split_amounts` fails on. A layout whose position moves with
the list length is the regression, not the fix. Removing it, plus the bound below, turned **3 of the 9**
pre-existing `tests/browser` failures green.

Removing the centring exposed the second half of the same test, `rail.height <= dial.height + 48`. The rail
was capped at `calc(100vw - 90px)`, 12px taller than that bound at every governed mobile width. The cap is
now **derived** rather than guessed: the dial's height equals its wrap's width, which is the panel width
minus the 130px callout column minus the 12px gap plus the 24px bleed; the panel is `100vw - 32px`, so the
dial is `100vw - 150px` and the bound `+ 48px` gives `calc(100vw - 102px)` — 288/318/328px against dials of
240/270/280px at 390/420/430px.

**Still open, and not fixed here.** The owner's actual complaint — a large void under the dial — is a
composition question, not a centring one. The dial is **63.6%** of viewport width against the concept's
**82.5%**, and the callout column is a hard **130px** floor, so closing that needs the callouts moved rather
than a CSS value changed. It is escalated for the owner rather than guessed at.

Of the 9 pre-existing `tests/browser/test_dial_fidelity.py` failures, **3 are now green**. The remaining 6 are
**unrelated to this work** and recorded precisely rather than left vague: **4** are
`test_dial_layout_in_actual_template_and_stylesheets` failing on the topbar's theme-toggle label being
**20.86px** wide at 390/430px where the test requires `<= 1px` (a topbar concern, not the dial); **2** are
`test_iphone_air_dial_and_right_callouts_have_separate_hit_areas` requiring **10px** of clearance between the
dial wrap's right edge and the rail, where the current design deliberately spends the full 12px column gap
and lands at 0px — the ring meets the column's box without crossing any callout text, so the test's
expectation and the documented clearance decision conflict and one of them has to be re-decided.

Verified: non-browser suite **1182 passed, 1 skipped**; `ruff` clean; `git diff --check` clean.

## The supplied Accounts illustration, and the red suite it left behind (2026-09-18)

**What arrived.** The owner supplied `static/img/meridian/observatory/accounts-ticket-building.png` — "a new asset
for the accounts page, the missing one". It is a colonnaded domed archive building with an arched entrance, gilt
dome, scrolls, a wax-sealed document and an open ledger. It closes **OS-039**, which had been recorded as blocked
because it could not be closed by effort: the kit's only fit for that surface was the **Today dial's** hilltop
observatory, and presenting that as a match would have been the same unsanctioned reuse the Accounts guard exists
to prevent.

**Recorded precisely, not overclaimed.** The asset is *not* a reproduction of the concept's "colonnaded domed
rotunda on a rocky knoll" — this building stands on a flat plinth among foliage and scrolls. It is the
owner-supplied governing art for this surface, and no pixel-equivalence with the concept engraving is claimed.

**Verified, not assumed.** Decoding the PNG confirms genuine transparency rather than a baked-in backing: alpha
range 0..255, **56.2%** of pixels fully transparent, all four corners `(0,0,0,0)` (the handoff's "real
transparency" rule). Rendered at 420×912 DPR 3 in the isolated synthetic preview, the art box measures **92×92**
(its `clamp(92px, 28%, 188px)` minimum) in a **1:1** box, the resolved background is the new asset, and the
engraving reads cleanly on the parchment with the parchment showing through.

**A red suite was left behind, and is now green.** A parallel lane swapped the asset and updated
`test_accounts_ticket.py`, but `test_accounts_assets_strip.py` still asserted that the *old* asset
(`observatory-landscape.png`) was present in `accounts.css`. The suite therefore failed on `HEAD`. That guard's
intent is reuse *restraint*, not a particular filename, so it now asserts both restraints — Accounts borrows
neither the Activity telescope **nor** Today's `observatory-landscape.png` — and that its own asset is present and
on disk. The module docstring and the `accounts.html` comment that still described the old asset were corrected
with it.

**A size note, recorded rather than acted on.** The asset is **2.0 MB** for a display slot of at most 188 CSS px.
That is within existing project precedent (`dial-plate.png` is 3.0 MB) and its alpha is correct, so it ships as
supplied; downscaling the owner's art is an optional follow-up, not something to do unasked.

Verified: full non-browser suite **1181 passed, 1 skipped** (the previously failing
`test_accounts_assets_strip` guard now passes); `ruff` clean on tracked source; `git diff --check` clean.
Presentation and docs only — **no** route, data, financial, provider or authority change. Not deployed.

## Today dial: the left-clipping regression, and the geometry that caps its size (2026-09-16)

**The regression.** The previous lane widened the dial's left bleed from 42px to 80px. Measured at the governed
mobile widths that clipped **64px** of the instrument (~20%) against 26px (~9%) at 42px, so the dial read as
clipped rather than bleeding. The owner reported it from a device screenshot. Restored, then reworked as below.

**The non-obvious geometry, which is why raising the bleed never made the dial look bigger.** The wrap spans
`-bleed .. track`, so the dial's right edge lands on `track` and its left edge on `-bleed`: everything a one-sided
bleed adds falls in the *clipped* region. 42px and 80px of bleed both left exactly `track` px visible — raising it
from 42 to 80 bought no visible size at all and only hid more. Corollary: **visible size grows only rightward.**

**Two hard floors cap how large it can get.**

1. The callout column cannot shrink below **130px**. At 116px the word "arrangement" (112.7px at 17px serif) splits
   mid-word via `overflow-wrap: break-word`. A width sweep that only checked `scrollWidth` reported 96px as safe;
   it was wrong, because overflow is not the same failure as a word not fitting. An existing test caught it.
2. Rightward growth past the 12px column gap puts the bright brass ring behind "Internet" and "Reserved" and the
   text loses contrast. Verified by capture, not assumed.

**What changed.** The wrap now grows **symmetrically**: `calc(100% + 24px)` with `margin: 0 0 0 -12px`, spending the
column gap on each side. The rendered dial goes 258–298px → **272–312px**, and left-clipping goes 26px → **0px**
(the dial now starts 4px inside the viewport). Callouts stay clear of the ring. Verify at 390px if this changes.

Guarded by `test_mobile_dial_grows_on_both_sides_and_keeps_the_callout_column`, which pins the +24/-12 pair, keeps
the 130px column, and fails if 42px, 56px or 80px of one-sided bleed returns.

Verified: full non-browser suite **1177 passed, 1 skipped**; `ruff` clean; `git diff --check` clean. Captures in
`artifacts/observatory-today-dialfinal-2026-09-16/` — 10 files, zero overflow, zero console errors — inspected at
420×912 and confirmed the ring is fully visible with the callout text legible over plain background.

**Still not as large as the owner's reference, and that needs a decision rather than more CSS.** The reference
composition makes the dial dominant with the callout detail carried by the parchment ticket below it. Reaching that
size requires the dial to extend under the callout list, which needs one of: a scrim behind the callout text, moving
the callouts (which would drop real information unless relocated), or shortening their labels. None of those is a
tweak, so it is left open for the owner rather than guessed at.

## Capture tooling was producing wrong light-theme evidence, and the tab treatment is ruled (2026-09-16)

**A tooling defect that invalidated part of this session's evidence.** The "light" capture for every workspace
after the first was in fact a dark render. `theme.js` resolves `localStorage` before `prefers-color-scheme`, and
`capture_meridian_matrix.py` opens one context per (viewport, theme) and then reuses a single page across *all*
workspaces — so once the app had written `meridian-theme`, every later page load in that context kept it, and only
the first workspace in each context got the emulated scheme. The images were labelled light and looked plausible
side by side, which is why it survived review: comparing the two passes showed *no* difference rather than an
obvious error.

Measured on the saved captures: Today's two themes differed by 101.6 mean luminance while Plan, Activity and
Accounts differed by **0.1** — indistinguishable. The fix pins `localStorage` to the same theme the harness passes
as `color_scheme`, before any app script runs. Re-verified on a fresh 80-capture matrix: deltas are now 114.7
(Today), 144.0 (Plan), 175.8 (Activity) and 159.9 (Accounts).

**This corrects a claim I made to the owner and wrote into the Astra handoff package**: I reported the light theme
as an *application* defect. It is not. Probing the live shell background returns `rgb(244, 236, 223)` for light on
all four workspaces, and `dial.css` has carried a correct theme-aware override all along. The application was
right and the tooling was wrong.

**Activity's mode row is now ruled, not pilled.** Concept 03 puts the three labels on a brass rule with the active
one underlined beneath its label; the pill treatment read as a generic segmented control and put a filled chip
where the concept has a label resting on a line. That rule is also the line separating the header from the tab
row. The scroll-through also exposed the failure honestly: a test asserting the ruled treatment had been left
failing by the other lane's in-flight pass, so this change makes the suite green rather than adding to it.

Verified: **1176 passed, 1 skipped** (full non-browser suite); `--obs-brass` (`#c6aa71`) and `--m-space-6` (32px)
confirmed to exist rather than assumed. Capture in `artifacts/observatory-activity-tabs-2026-09-16/` — 10 files,
zero overflow, zero console errors — inspected at 420×912 and confirmed to show the brass rule and the active
underline.

### Coordination note

The working tree held 23 modified tracked files from the ChatGPT lane with `builder-trackd-today-parity`
(generation 2) claimed over exactly this surface. Committed as one attributed commit (`63d2865`) at the owner's
direction, recording that one test failed there. That lane's claim is left as its author wrote it.

### Still open — verified against the concepts, not yet reconciled

Measured, so the next pass does not have to re-derive it:

- **Background is too light and too green.** The concepts average `#141b32`; ours is `#172334`. Today's dark
  override (`#101a28`) is conversely *darker* than its concept (`#161c34`).
- **The wavy title underline is absent.** The concepts carry a short lilac squiggle under the page title, on
  Today, Activity and Accounts (not Plan).
- **The date under the wordmark** is absent on the workspaces whose concepts show it.
- **The Accounts ticket** is a rotated, notch-edged ticket with an inset dotted border, scattered brass stars and
  a crescent; ours is axis-aligned and plain.
- **The Accounts connectors** are curved dashed paths with a node at each end, colour-matched per row, plus
  star-tipped dotted row separators. The straight vertical rail built here is the wrong construction.
- **The Plan tab row** is one bordered bar divided into three cells whose top edge forms the separator line, with
  a parchment-filled active cell and a brass star medallion at its left.
- **The Accounts engraving differs.** The concept draws a colonnaded rotunda; the kit's `observatory-landscape.png`
  is a different engraving. This needs art from Astra — it will not be faked.
  *Resolved 2026-09-18:* the owner supplied `accounts-ticket-building.png`, the dedicated Accounts illustration,
  which now serves this surface. See the top of this file.

## Accounts — the closing parchment strip, and the handoff round closed (2026-09-16)

**Accounts batch 4.** Concept 04 ends the page with a compact parchment strip for tracked items, and the kit
names `parchment-ticket.png` for exactly that shape of surface — *"Evidence, account summary, compact income
ticket"* — so the "Assets & Contracts" section reuses the same measured 80-slice as the other three tickets. The
concept's engraving on that strip has **no counterpart in the kit**: the only engraving that would fit is the
telescope, which the kit scopes to Activity with sparing reuse in Settings. Rather than perform an unsanctioned
reuse, the strip takes the ticket's material and hierarchy with no invented illustration, and a guard asserts the
telescope stays out of `accounts.css`.

The label override needed three classes again, for the reason recorded in batch 1: `.obs-shell .m-section-label`
sets that colour at (0,2,0), so a two-class selector ties and the winner falls to stylesheet order. That trap is
now commented in both places and guarded in both.

**Reconciliation completed in this round:**

- `MERIDIAN_ROADMAP.md` §Track D previously named only `design/observatory-drafts-2026-09-08/` as visual
  authority, which had been stale since the 2026-09-16 kit became the governing implementation specification. It
  now states the split explicitly: the concept set is the **composition authority**, the kit is the
  **implementation specification** and takes precedence where it speaks — including its explicit corrections such
  as `bank` rather than the concept's semantically incorrect Wi-Fi reserve glyph.
- The blanket `Builder (this lane)` claim row in `AGENT_COORDINATION.md`, open since 2026-09-13, is released. Its
  `docs/project/*` scope had been superseded by these path-scoped per-slice claims; the row now says so instead of
  sitting `active` and implying work was being held.

Verified: `tests/meridian/test_accounts_assets_strip.py` 3 new guards; full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1165 passed, 1 skipped**; Ruff and
`git diff --check` clean. Capture at 5 viewports × 2 themes in `artifacts/observatory-accounts-assets-2026-09-16/`
with zero overflow and zero console errors, inspected at 420×912.

### State of the handoff integration

Six of the kit's assets are now consumed in production, each by the surface the kit names for it:

| Kit asset | Surface it now serves |
|---|---|
| `parchment-ticket.png` | Today's evidence ticket, Plan's next-income strip, Accounts' summary panel, Accounts' closing strip |
| `plan-map.png` | Plan's folded allocation map |
| `apricot-button.png` | Plan's primary action plate |
| `activity-telescope.png` | Activity's header vignette |
| `observatory-landscape.png` | Today's dial layer only. **No longer on Accounts** as of 2026-09-18, when the dedicated asset below replaced it there |
| `accounts-ticket-building.png` | Accounts' summary-ticket illustration (owner-supplied 2026-09-18) |
| `medallion-frame.png` | Accounts' account medallions |
| `title-rule.svg` | The lilac wavy rule under the workspace title on Today/Activity/Accounts (drawn in-repo; not on Plan) |

Two items remain **open and owner-gated**, and are not claimed as done:

1. **Activity's parchment "N categories to review" strip.** The transaction payload exposes no awaiting-review
   field, so any count would have to be derived from an invented confidence threshold — placing a derived figure
   where the concept shows a fact. Needs the owner's decision on what it counts and what it says.
2. **Settings (concept 05).** The isolated preview serves only `today`, `plan`, `funding-rules`, `activity` and
   `accounts`; `/meridian/settings?section=connections` 404s there. The kit itself defers Settings art *"only
   after its preview route is available"*, so no Settings parity can honestly be claimed.

Also open, smaller: Activity's row-level action plate (the concept reuses the apricot button there) and the
concept's underlined tab treatment; Accounts' connection strip; Plan's row scale lines and exact header/tab order;
and the older Today open gaps already listed in the roadmap.

Deployed: nothing. No route, data, financial, provider or authority change across any slice.

## Accounts — the connector rail (2026-09-16)

Accounts batch 3 completes the medallion motif. Concept 04 does not just place three medallions; it threads the
rows on a dashed rail with a small node beside each one, so the accounts read as the concept's *"financial
constellation"* rather than a stack of separate tiles. The rows now carry that rail, with each node in its own
row's tint — lilac beside cash, mint beside savings.

Three details make it read as a deliberate rail rather than a stray border, and each has a guard:

- **The line stops at the end medallions.** `:first-child` starts the rail at the row's vertical centre and
  `:last-child` ends it there, so it never dangles past the first or last node.
- **Rows without a medallion are excluded.** Archived rows carry no medallion, so a node beside one would mark
  nothing; the selector is scoped `:not(.m-account-row-archived)`.
- **The node colour comes from the row, not the medallion.** The tint attribute now sits on the row as well, so
  the rail reads one token instead of needing a second colour table to drift out of sync.

The rail required a 30px left gutter on the row so it sits clear of the medallion. That costs real width, so I
checked mobile specifically rather than assuming: it holds, with zero overflow in the manifest at all five
viewports.

Verified: `tests/meridian/test_accounts_rail.py` 3 new guards; full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1162 passed, 1 skipped**; Ruff and
`git diff --check` clean. Capture at 5 viewports × 2 themes in `artifacts/observatory-accounts-rail-2026-09-16/`
with zero overflow and zero console errors, inspected at 1440×900 and 420×912.

Deployed: nothing. No route, data, financial, provider or authority change. Still open in Accounts: the
connection strip and the "Assets & documents" ticket.

## Accounts — the account medallion from the supplied frame asset (2026-09-16)

Accounts batch 2, and the concept's most distinctive motif: each account row carries a coloured medallion.
The kit supplies the frame and names its contract in one sentence — `medallion-frame.png` is a *"Decorative frame
above a code-owned colored disk and semantic SVG icon."* Opening the asset confirmed it is a brass double ring
with four evenly-spaced rivets, so all three layers are now present: the supplied ring above a tinted disk, with
the role's icon on top.

The disk tint follows the concept's three colours — lilac for cash, mint for savings, apricot for investments —
with a quieter slate for the roles the concept does not show. Choosing a signal colour for those would say
something the data does not, so they stay neutral.

**I deliberately did not swap the glyph set, and the reason is in the kit itself.** The kit's vocabulary
prescribes `bank` for reserves and supplies no equivalent for liabilities, investments or reimbursements. Our
five role line-icons already distinguish those cases accurately, so replacing them would have lost meaning rather
than gained fidelity. The `bank`-for-reserves instruction is recorded in the code comment next to the tint map,
and a guard asserts all five role icons survive, so a later pass cannot quietly drop them.

Verified: `tests/meridian/test_accounts_medallion.py` 3 new guards — including one that would fail if the
treatment regressed to the previous rounded square, so the guard is not satisfiable by a weaker implementation.
Full non-browser suite `./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1159 passed, 1 skipped**;
Ruff and `git diff --check` clean. Capture at 5 viewports × 2 themes in
`artifacts/observatory-accounts-medallion-2026-09-16/` with zero overflow and zero console errors, inspected at
1440×900 and 420×912.

Deployed: nothing. No route, data, financial, provider or authority change. Still open in Accounts: the concept's
connector rail linking the medallions, the connection strip, and the "Assets & documents" ticket.

## Accounts — the parchment summary panel from the supplied ticket and dome (2026-09-16)

Track D reaches the fourth workspace, against concept **04**. Its dominant element is a large parchment panel
carrying the cash figure, and the kit names both assets for it: `parchment-ticket.png` for an *"account summary"*
and `observatory-landscape.png` for the *"Accounts decorative vignette"*. The dome-on-a-hill engraving in the
concept is that second asset — confirmed by opening it, not assumed from its name.

*Superseded 2026-09-18:* that second asset is the **Today dial's** building, and the owner has since supplied
`accounts-ticket-building.png` as the dedicated Accounts illustration. Accounts no longer uses
`observatory-landscape.png`. The analysis above stays as the record of what was decided on 2026-09-16.

The "Available cash" card is now that panel: the ticket as a nine-slice at the same measured 80-slice the Today,
Plan and Activity tickets use, with the dome set beside the figure and the provenance note beneath it. Both
figures stay code-owned HTML on the blank face, and the summary grid gives the panel the concept's prominence
(`2.1fr / 1fr`) while the Liabilities figure keeps its own card — nothing was dropped to make room.

**A contrast failure was caught by inspecting the capture, not by reading the CSS.** The first render put the
section label in **pale lilac on the parchment** — the exact case the kit calls out in as many words ("On
parchment, use dark navy text; do not carry pale lilac/mint text over without checking contrast"). My override
used two classes, which ties on specificity with `.m-accounts-net-card .m-section-label` (0,2,0) — and that rule
appears **later** in the file, so it won. The selector is now three classes with a comment explaining that the
depth is deliberate, and a guard pins it. The figure's `data-signal` colouring is suppressed on the parchment for
the same reason: it is a cash total, not a warning, and pale mint would not have survived the paper.

Verified: `tests/meridian/test_accounts_ticket.py` 3 new guards (asset nine-slice, no figure dropped, and the
contrast rule with its specificity rationale); full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1156 passed, 1 skipped**; Ruff and
`git diff --check` clean. Capture at 5 viewports × 2 themes in
`artifacts/observatory-accounts-ticket-2026-09-16/` with zero overflow and zero console errors, inspected at
420×912 in both themes.

Deployed: nothing. No route, data, financial, provider or authority change. Still open in Accounts: the concept's
large coloured account medallions with their connector rail, the connection strip, and the "Assets & documents"
ticket.

## Activity — the framed category glyph on ledger rows (2026-09-16)

Activity batch 2, and the concept's most-repeated motif: every row in concept 03's review list carries its
category glyph inside a thin ring with a small marker dot. Review cards now carry that ring, with the glyph
resolved semantically from the row's own text.

**A real resolver bug was caught by testing behaviourally rather than by reading source.** The first
implementation scanned the merchant, description and category in one pass. The fixture's rows are "Internet" and
"Electric", and *both* carry the category "Utilities" — so the electricity rule matched on the broad category and
painted a **lightning bolt on the Internet row**, which is exactly the confusion the kit's own mapping calls out
("lightning-charge (electricity) vs wifi (Internet)"). The resolver now scans the specific text (merchant,
description) first and only falls back to the broad category. A Node round-trip test pins the distinction, and it
immediately caught a second gap: "Steam" — the concept's own example row — matched nothing at all and fell through
to the neutral mark, so the canonical streaming and console merchants were added.

**The glyph is decorative, not authoritative.** It is a CSS mask painted with `currentColor` rather than an
`<img>` (an external SVG's `currentColor` resolves to black inside an image — the defect fixed on Plan), it is
`aria-hidden`, and the category text beside it stays the statement of record. An unrecognised row keeps a neutral
compass rather than borrowing a meaning it does not have.

**Not done: concept 03's parchment "N categories to review" strip.** The transaction payload exposes no
"awaiting review" field, so any count would have to be derived from a confidence threshold — that is inventing a
classification policy, and it would put a derived number where the concept shows a fact. It stays open pending an
owner decision on what the figure should count and what it should say.

Verified: `tests/meridian/test_activity_glyph.py` 3 new guards, one of which is a real Node round-trip over ten
cases rather than a source-string check; full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1153 passed, 1 skipped**; Ruff and
`git diff --check` clean. Captured in review mode via `--ui-state-selector '[data-activity-mode="review"]'` at 5
viewports × 2 themes in `artifacts/observatory-activity-glyph-2026-09-16/`, zero overflow and zero console
errors, and inspected at 420×912.

Deployed: nothing. No route, data, financial, provider or authority change.

## Activity — the header vignette from the supplied telescope asset (2026-09-16)

Track D reaches the third workspace, against concept **03**. The kit names `activity-telescope.png` for the
*"Activity top-right vignette"* and adds two constraints: *"About 130–170 CSS px wide on mobile. Do not let it
squeeze the heading or touch target."* Both are honoured here.

**The header was structurally wrong before this slice, and the measurement showed it.** A geometry probe found
the Activity header copy sitting at x 815–1339 of a 1088px-wide header — hard right — with the Filter button
centred below it and the **entire left half empty**. The cause was `.m-command-header`'s column flex combined with
`align-items: flex-end` on `.m-activity-command`, with `.m-filter-button { align-self: center }`. Concept 03 puts
the copy at the left and the art at the right, so the empty half was exactly the station the vignette needed. The
copy is now left-aligned (x 251–775 at 1440) and the vignette takes the top-right station.

**The no-squeeze rule forced a deliberate mobile difference, recorded rather than hidden.** At 1440px there is a
free right column, so the vignette is absolutely positioned top-right at `clamp(128px, 16vw, 176px)` and the copy
is held clear with `max-width: calc(100% - clamp(140px, 18vw, 196px))`. Below 601px our owner-accepted heading is
a full sentence ("One financial timeline."), not the concept's single word "Activity", so there is **no** free
right column beside it: an absolutely placed vignette would overlap the heading or force it to wrap further. The
vignette therefore moves into the flow above the Filter button at 148px — inside the kit's stated mobile band —
so the heading keeps its full measure and the art still reads.

Verified: header height unchanged at 1440px (248px) with the copy's right edge at 775 against a vignette starting
at ~1163, so no overlap and no layout growth; at 420px the header grows only by the vignette's own 148px with the
Filter button below it. Zero overflow in the manifest. `tests/meridian/test_activity_vignette.py` 3 new guards;
full non-browser suite `./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1150 passed, 1 skipped**;
Ruff and `git diff --check` clean. Capture at 5 viewports × 2 themes in
`artifacts/observatory-activity-vignette-2026-09-16/`.

Deployed: nothing. No route, data, financial, provider or authority change. Still open in Activity: the parchment
"N categories to review" summary strip, framed circular category glyphs on the ledger rows, and the concept's
underlined tab treatment.

## Plan — the primary action plate from the supplied button asset (2026-09-16)

The third Plan batch. Concept 02's primary action is a wide apricot plate, and the kit specifies
`apricot-button.png` for exactly that: *"Primary action plate ... Use behind a real button/link. HTML label and
arrow; at least 44px target. Nine-slice for variable width."* The "New commitment" button now carries that plate
behind its real HTML label and plus glyph.

**The slice offsets were measured, not guessed.** The asset is 2172×724 but its plate occupies only y 171–515,
sitting behind ~170px of transparent padding — so a naive uniform slice would mis-assign the chamfer and the four
rivets to the tiled middle band and repeat them. Measuring the silhouette profile gave the chamfered end caps a
width of ~230px, which became `190 230 190 230 fill / 10px 34px round`: the caps keep their chamfer and rivets,
the thin top and bottom slices keep the plate's edge lines, and `fill` carries the fibrous apricot centre so the
label stays code-owned.

Verified programmatically at 1440px and 420px: `border-image-source` resolves to `apricot-button.png`, the slice
is `190 230 fill`, width `10px 34px`, the button measures **222×58** (above the kit's 44px target), the label
renders in the plate's dark ink `rgb(44, 29, 13)`, and document overflow is 0. Inspected in the capture: the
chamfered corners, triple edge lines, four rivets and fibrous apricot all read correctly at mobile. Also
`tests/meridian/test_plan_map.py` 8 guards (one new); full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1147 passed, 1 skipped**; Ruff and
`git diff --check` clean. Capture at 5 viewports × 2 themes in `artifacts/observatory-plan-cta-2026-09-16/`.

Deployed: nothing. No route, data, financial, provider or authority change. Plan's remaining gaps are now
narrow: row-level scale lines and chevrons on the commitment rows, and the exact header/tab order.

## Plan — the next-income strip from the supplied ticket asset (2026-09-16)

The second Plan batch. Concept 02 carries the next income as a **perforated parchment strip**, and the kit names
that exact role for `parchment-ticket.png`: *"Evidence, account summary, compact income ticket"*. The funding card
was still a dark `.m-surface` panel, so it now reuses the ticket as a nine-slice border image with `fill`, at the
same 80-slice the Today evidence ticket uses. Nine-slice keeps the scalloped ends, cut corners and corner rivets
fixed while the band reflows, and `fill` carries the blank centre, so the date, amount and caption stay
code-owned HTML and the card's own data hooks are untouched.

Text on the parchment takes the ticket ink rather than the shell's cream — the section label brass, the figure
dark ink, the amount the incoming green — matching how the Today evidence ticket handles the same material. The
concept flanks the strip with a small compass star, added here as two decorative `::before`/`::after` masks, and
the dark surface's hover lift is dropped because a parchment band should not lift like a panel.

Copy is deliberately unchanged: the owner accepts the live wording, so "Funding schedule" and "Next paycheck"
stay as they are rather than becoming "Next income".

Verified programmatically rather than only by eye, at 420px and 1440px: `border-image-source` resolves to
`parchment-ticket.png`, `border-top-width` is 20px, both ornaments carry a mask at 22px, the amount renders
`$1,660` from HTML, the card measures 388×197 and 441×197, and document overflow is 0 at both widths. Also
`tests/meridian/test_plan_map.py` 7 guards (one new); full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1146 passed, 1 skipped**; Ruff and
`git diff --check` clean. Capture at 5 viewports × 2 themes in `artifacts/observatory-plan-income-2026-09-16/`.

Deployed: nothing. No route, data, financial, provider or authority change. Still open in Plan: row-level scale
lines and chevrons, the bottom apricot CTA (`apricot-button.png`, which the kit specifies for exactly that), and
the exact header/tab order.

## Plan — the folded allocation map from the supplied asset (2026-09-16)

Track D moves to the second workspace, against concept **02**. The workspace led with a coverage donut and kept
the allocation in a "secondary support" strip as a generic stacked bar plus a swatch legend
(`data-allocation-bar`/`data-allocation-legend`). Concept 02 carries no bar and no legend: the allocation is a
**folded parchment map** with separate medallions. The kit README is explicit — *"Plan: install the map below the
tabs with semantic allocation summaries and separate medallions"* — and its `plan-map.png` ("Plan allocation
backdrop; no money or labels in image") is that map.

The bar and legend are replaced by the map, installed as the first block inside the plan view pane, ahead of the
coverage/funding summary. It renders:

- the kit's folded-map art as a CSS background at its own `1536 / 1024` aspect ratio, so it is never stretched;
- one medallion per allocation segment, built from `plan.allocation.segments`, each with its own kit glyph, its
  own label and its own amount — every figure stays code-owned HTML;
- brass leader rules from each medallion to the map's hub, and a decorative compass rose at that hub.

**Stations are composition, not data.** The kit warns that "constellations do not encode money", and the removed
bar sized each slice by `amount / cash_total`, which is exactly the claim the map must not make. So a medallion's
place is fixed by the concept: `Available` is pinned to the lower hub because that is the station the concept
reserves for money left over, the other segments take left then right in service order, and any further segment
reuses the last station rather than inventing a position the concept does not define.

**Two defects found and fixed during verification, both visible in the capture.** The first render put a bank
glyph on the Goals medallion; the handoff maps goals to `flag`, so the resolver now keys goals to `flag`. The
second was worse: the glyphs were `<img>` elements, and an external SVG's `currentColor` resolves to black inside
an image, so the glyph on the navy "right" medallion was nearly invisible. Glyphs and the compass rose are now
CSS masks driven by a `--m-medallion-icon` custom property, so each disk colours its own glyph — dark ink on the
lilac and brass disks, cream on the navy one.

**Deliberately not claimed.** Concept 02 also tags each medallion with a status ("Reserved", "Available to
plan."). The plan service exposes no per-segment status, and deriving one would present an inference as fact, so
the medallions carry label and amount only. Also not yet matched in this workspace: the concept's row-level scale
lines, its perforated "Next income" strip, its bottom apricot CTA and the exact header/tab order.

**A production-vocabulary problem handled without inventing data.** The plan service emits `"Committed to
commitments"` and `"Unfunded commitments"`, far longer than the preview fixture's `"Bills"`/`"Goals"`, and the
medallion block had a 34% max-width with no wrap rule, so a long label could run off the parchment. The block now
wraps inside its station and the left/right stations sit lower (32% → 38%) for headroom. The capture uses the
synthetic fixture, so the long-label case is guarded by test rather than by pixel — that limit is recorded here
rather than papered over.

Verified: `tests/meridian/test_plan_map.py` 6 guards (order below the tabs, decorative art, stations not amounts,
the wrap constraint, a regression guard for the mask-glyph defect, and the kit asset's SHA-256 against its
manifest); full non-browser suite `./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1145 passed,
1 skipped**; Ruff and `git diff --check` clean. `tests/browser/test_plan.py` was updated from the removed legend
to assert the medallions (it is `APP_URL`-gated and unexecuted here). Capture at 5 viewports × 2 themes in
`artifacts/observatory-plan-map-2026-09-16/` (zero overflow, zero console errors), inspected at 420×912 and
1440×900.

Deployed: nothing. No route, data, financial, provider or authority change.

## Today — coordinate-anchored connector runs (2026-09-16)

Handoff step 3, third batch, and the last item the handoff names for Today. The concept ties each rim marker to
its callout with a dashed run, and the handoff requires connectors "tied to actual event coordinates". Nothing of
the sort existed: the only decoration was a fixed 25px dashed rule pinned to the list item's own midline, reading
no dial coordinate at all, and it was switched off at ≤900px — exactly where concepts 01/06 place the runs.

Both ends now come from live geometry. `renderConnectors` projects each upcoming event's marker with the same
`dayToAngle`/`positionOnArc` call `renderDialSVG` uses, converts it into panel coordinates through the dial's own
box, and terminates the run at that event's callout row, whose box it reads directly. Runs are redrawn whenever
`update()` replaces the event rows — the rows are replaced, so stale anchors would otherwise point at detached
nodes — and through a `ResizeObserver` on the panel, because both ends move when either side resizes. `stop()`
disconnects the observer and removes the fallback `resize` listener.

Layer safety: the overlay is `aria-hidden`, `pointer-events: none` and clipped to the panel, so it cannot capture
a callout click or a dial drag, and cannot widen the document. A run with nowhere to go (target not at least 6px
clear of the marker) is skipped rather than drawn backwards through the instrument.

Verified: `tests/meridian/test_dial_js.py` 30 passed (1 new guard); full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1139 passed, 1 skipped**;
`tests/browser/test_dial_fidelity.py` **18 passed** with a new test that proves every drawn run starts inside the
dial, ends at its own row's left edge minus 4px, lands on that row's midline within 1.5px, reports
`pointerEvents: none` and `aria-hidden`, spans no more than the panel and adds no document overflow. Ruff and
`git diff --check` clean. Capture at 4 viewports × 2 themes in
`artifacts/observatory-today-connectors-2026-09-16/`; inspected at 420×912 and 1440×900.

This closes the three items the handoff names for Today: shaped ticket, prominent pointer, connectors tied to
real coordinates — plus the semantic badge work its `Nuances` section requires. Deployed: nothing. No route,
data, financial, provider or authority change. **Plan (concept 02) is the next Track D workspace.**

Committed as three precise batches: `7077f1e` (semantic badges, pointer, callout legibility), `4d5f0e1` (shaped
ticket), `e028725` (connector runs and their geometry proof).

## Today — shaped evidence ticket from the supplied asset (2026-09-16)

Handoff step 3, second batch. The evidence ticket was a rectangular parchment card: `ticket-corners.svg` drew
only four brass right-angle brackets, so the "shaped silhouette" reading was carried solely by the round date
stamp. It now uses the kit's `parchment-ticket.png` as a nine-slice border image with `fill`: the supplied art
brings the scalloped side rails, the cut corners, the four corner rivets and the fibrous paper, while nine-slice
keeps those corner features fixed as the HTML content reflows and `fill` carries the blank centre through. Every
word and amount stays code-owned. Border width 16 → 24px (10 → 20px at mobile).

Sizing was checked before widening rather than assumed, because `tests/browser/test_dial_fidelity.py:87` caps the
ticket at 260px: the mobile ticket measured 193.6px, leaving 66.4px of headroom, and the +20px frame lands well
inside the cap. The fidelity suite stays **17 passed**, confirming the cap, the `<time datetime>` contract, the
exactly-twice `$84.00` and the no-overflow assertions all survive the new frame, at 390/430/1024/1440 in both
themes.

Verified: `tests/meridian/test_dial_js.py` 29 passed (1 new guard); full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1138 passed, 1 skipped**; dial fidelity **17 passed**;
Ruff and `git diff --check` clean. Capture at 4 viewports × 2 themes in `artifacts/observatory-today-ticket-2026-09-16/`,
inspected at mobile and at desktop full-page to confirm the nine-slice tiles without seams.

Deployed: nothing. No route, data, financial, provider or authority change. Still open in step 3: the
coordinate-anchored connector runs from dial markers to their callouts — no connector geometry exists at any
width today, and the concept places those runs precisely at the ≤900px widths where the current decorative
bridge is switched off.

## Today — semantic badges, prominent pointer, callout legibility (2026-09-16)

Handoff step 3, first batch, against concept **06** (functional dial/evidence) with **01** supporting.

- **Semantic event glyphs.** `dial.js` mapped a badge by generic `kind` only, so every bill rendered the same
  lightning bolt — the exact duplication the kit's `Nuances` and `README` call out. The dial service emits only
  `kind` plus the commitment's own name, and `normalizeEvent` is a strict whitelist, so the glyph is now resolved
  by `eventIconName(event)` from the event's own title, with the kit README's mapping (electricity →
  `lightning-charge`, Internet → `wifi`, rent → `house`, groceries → `basket`, transit → `bus-front`,
  entertainment → `controller`, reserves → `bank`, goal → `flag`, transfer → `arrow-right`) and a kind fallback.
  Presentation only: no financial meaning is inferred, and an unrecognised name keeps the kind glyph. The badge
  now reads its glyphs from the kit icon directory, which also forces the `goal`/`transfer` remap because the kit
  has no `bullseye` or `arrow-left-right`.
- **Badge weight.** The weightless navy `3px double` border with a separate brass outline was replaced by the
  concept's anatomy: coloured disk, brass band with navy hairlines inside and outside (so the rim reads as two
  fine rings), and rivets straddling the band. Rivets are darkened brass with a brass outline so they stay legible
  on the lilac, mint, brass and grey disks.
- **Pointer prominence.** The needle is now a 7px round-capped mint stroke with a glow and a 13px brass-rimmed
  tip, and reaches further inward (radius 132 → 118). Both the render path and `paintSVGSelection` were updated —
  the pointer start radius is computed in two places, and changing one alone would have made the needle snap on
  the first repaint.

**Medallion frame not used, with a measurement.** The kit's `medallion-frame.png` is the concept's rim-plus-rivets,
but its native stroke measures 48px across a 1254px canvas, so at badge scale it collapses to ≈1.7px at 44px and
≈2.5px at 64px — the *double* rim the nuance requires cannot survive there. It is specified for medallions up to
627 CSS px (2x) / 418 (3x) and should be used when a medallion at that scale is introduced (Activity/Settings).
The badge anatomy is reproduced in CSS at the small sizes instead.

**Pre-existing defect fixed, with attribution.** `tests/browser/test_dial_fidelity.py` was already red at
`HEAD 1a9599f` before this batch: `test_long_event_list_does_not_push_dial_down_or_split_amounts[390|420|430]`
(3 failed, 14 passed). Confirmed pre-existing by stashing this batch's three files and reproducing the identical
3 failures. Measured cause: at ≤700px the callout title spans the whole rail column, so the rail width *is* the
title's measure — at 116px the column left 110px while the word "arrangement" measures 112.7px at 17px serif, so
`overflow-wrap: break-word` split an ordinary word across two lines. Fix: rail 116 → 130px and title 17 → 16px.
The suite is now **17 passed**.

Verified: `tests/meridian/test_dial_js.py` 28 passed (4 new guards); full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1137 passed, 1 skipped**; `tests/browser/test_dial_fidelity.py`
**17 passed** (was 3 failed / 14 passed); Ruff and `git diff --check` clean. Governed capture of Today at
4 viewports × 2 themes in `artifacts/observatory-today-step3-2026-09-16/`; the rendered capture confirms the
Internet badge resolving to the wifi glyph, the lightning bolt retained on Electric, the star on Payday's mint
disk, and a single-line callout title.

Deployed: nothing. No connector geometry, ticket art, route, data, financial, provider or authority change.
Still open in step 3: coordinate-anchored connectors from dial markers to callouts, and the shaped ticket.

## Observatory shared identity — type, wordmark and navigation (2026-09-16)

Owner correction recorded: the 2026-09-16 Astra handoff and its supplied kit are the **governing implementation
specification**, not an optional aid, and the older Design Atlas must not govern a conflicting layout.
Composition authority is concept **06** for Today's functional dial/evidence with **01** supporting, and **02–05**
for Plan, Activity, Accounts and Settings. This entry covers handoff step 2 only.

Implemented the shared identity layer. The bundled licensed pairing is self-hosted from the kit directory
(`LibreBaskerville.ttf` → `--m-font-serif`, `SourceSans3.ttf` → `--m-font-sans`), and the Observatory layer's own
`--obs-font-*` tokens were pointed at the same families — without that second change `.obs-shell` would have kept
rendering in host fallbacks. One `templates/meridian/partials/wordmark.html` now renders the accented Meridian
wordmark in the desktop rail and both mobile headers; the apricot four-point star is a CSS pseudo-element on the
dotless letter, so it adds no text to the accessibility tree. The four supplied glyphs (compass, map, bar-chart,
person-circle) render as CSS masks so each link's `currentColor` drives them, always beside a visible label and
with `aria-hidden="true"`, so a glyph can never become the only name for a workspace. The active entry keeps its
physical marker and gains the concept's lilac label and glyph.

Removed as dead by that change: the literal "M" prefix in both mobile headers, `.m-topbar-title`, and the
`.m-branded-wordmark` rules. `dial.css` held a live rule sizing `.m-topbar-title` for the Today mobile header; it
was retargeted to `.m-wordmark` instead of being left on a removed selector, which would have silently dropped
the concept's large mobile wordmark.

Verified: RED→GREEN `tests/meridian/test_observatory_identity.py` (9 checks). Full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1131 passed, 1 skipped**. Ruff clean on both
changed test files; `git diff --check` clean. Governed capture matrix against the isolated synthetic preview
(`scripts/preview_observatory_dial.py` on `:8093`, `--skip-login`): **40 records = 4 workspaces × 5 viewports ×
2 themes**, with zero horizontal overflow and zero console errors in every record; artifacts in
`artifacts/observatory-identity-2026-09-16/`. Rendered-property probe at 1440×900 DPR 1 and 420×912 DPR 3: four
glyphs masked at 20×20 with labels intact and `aria-hidden="true"`; active bar 3px (rail) / 47px (dock) in lilac
**and** an active lilac label; the wordmark accent pseudo-element present; both bundled faces report `loaded`;
wordmark computed family `Meridian Serif`. All six consumed kit files match the kit manifest SHA-256 exactly.

Deployed: nothing. No route, workspace-geometry, data, financial, provider or authority change; the four
workspaces, Settings separation, URL persistence and focus behaviour are untouched. Settings still returns 404 in
the isolated preview, so no Settings parity is claimed — `05-settings` stays governed by handoff step 6. Next:
handoff step 3, Today geometry and event callouts against concept 06.

Committed as `82c5a174550f87370414ae625582b87ba042fd7e`. Governed evidence carrying the consumed kit hashes and
the exact consuming revision is `artifacts/observatory-identity-2026-09-16/identity-evidence.json`; the 40-record
contract manifest and the full-resolution captures sit beside it.

## Observatory artwork kit and preview comparison — 2026-09-16

Implemented the owner's requested separate art handoff in `static/img/meridian/observatory/kit-2026-09-16/`: eight transparent decorative PNGs (map, telescope, observatory, moon, blank dial ring, blank ticket, action plate and medallion frame), 22 MIT SVG icons, two SIL OFL font files, a standalone gallery/board, scoped typography/color examples, prompts, provenance and hash manifest. These are reference-based reconstructions; the fonts and library icons are explicitly proposed matches, not recovered identities. Production UI files and existing assets are unchanged.

Verified: all seven original concept PNGs match the PDF appendix's decoded pixels; all eight exported PNGs have alpha transparency and match manifest hashes; 22 SVGs parse without script elements; font files and licenses are present and both fonts load in the browser. Inspected all eight pieces on indigo and white in the running gallery, with no broken images, horizontal overflow or console errors at 1200×900. At 420×912, no overflow was found and the initial viewport was visually checked after resetting a browser capture scaling defect; earlier malformed exports are rejected. Focused current-preview findings and accepted captures cover Today, Plan, Activity Review and Accounts; Settings returns 404 in this isolated preview. No full governed parity matrix or app visual acceptance is claimed.

Deployed: nothing. No financial/provider call, banking change or production layout change. The build-team handoff is `docs/project/OBSERVATORY_ASSET_KIT_2026-09-16.md`; verification is `artifacts/observatory-asset-kit-2026-09-16/verification.json`. Next: Track D consumes the kit one visual gap at a time and regenerates governed captures; missing source artwork is no longer a blocker. Concurrent emitter handoff commit `4037e08` was preserved.

## Readiness contract probe repair — 2026-09-15

Implemented the bounded Astra-lane follow-up in `scripts/verify_readiness.py`: replaced the removed `_verify_stored` import and call with the current `_verify_crew_bill_reserve_readback()` verifier factory. Added a regression test in `tests/test_readiness_tools.py` covering successful probe execution and the corrected anchor-preserving calendar values. Refreshed `artifacts/readiness-2026-09-13/contract-probes.json`; it is synthetic-only, records zero provider calls, and now reports `monthly_second: "2026-03-31"` and `semimonthly_next: "2026-01-31"`.

Tested: `./.venv311/bin/python -m pytest -q tests/test_readiness_tools.py` — **4 passed**; `./.venv311/bin/ruff check scripts/verify_readiness.py tests/test_readiness_tools.py` — clean; `./.venv311/bin/python scripts/verify_readiness.py probes --output <fresh-temp-file>` — exit 0; fresh output matched the refreshed artifact before commit; `git diff --check` — clean. No provider call, credential access, deployment, financial mutation, or live data use.

Deployed: nothing. Implementation and verification remain local/synthetic only. Next: review and integrate this bounded patch as part of the readiness evidence chain; no external-provider acceptance is claimed.

## ORSC sanitized Meridian status emitter — 2026-09-15

Implemented the bounded read-only ORSC status emitter for a separate Harness handoff. `meridian/status_emitter.py` projects only Git metadata, `MERIDIAN_OS_TASKS.json`, `AGENT_COORDINATION.md`, `CURRENT_STATUS.md`, `MERIDIAN_ROADMAP.md`, and `MERIDIAN_DECISIONS.md` into schema version 1. `scripts/emit_meridian_status.py` emits one canonical JSON event to stdout and fails closed to a minimal degraded event without echoing unsafe source or exception content.

The contract defines stable source-derived `event_id`, producer/observation timestamps, bounded queues, Track D/I/C state, task counts, release gate, evidence, blockers and safest next slice. Missing, malformed, stale, out-of-order or conflicting input is unknown/degraded, never guessed success. Secrets, tokens, cookies, OTPs, prompts, transcripts, tool output, reasoning, absolute paths, unrestricted URLs, balances and unnecessary financial detail are rejected. No database, provider, network, webhook, financial mutation, agent-control, Harness or scheduling path is connected.

Tests: `tests/meridian/test_status_emitter.py` 17 passed; changed-path Ruff and `git diff --check` passed. No browser check was applicable. Harness must independently validate, filter, deduplicate, freshness-check and render; live Harness mode is not claimed until it integrates and verifies the contract. Committed as `b98e6994748739eb1accae17e5834931878e9fc8` after final review.

Last consolidated: 2026-09-15 (dated occurrences: chained stepping made drift-free by construction)

## Dated occurrences — the drift is now unreachable by chaining, not just by convention — 2026-09-15

Follow-on to the consolidation below. Converting the callers fixed the **indexed** path (`advance(anchor, rec, n)`), but a caller that *held* an intermediate date and fed it back in still drifted: `advance(advance(2026-01-31, "monthly"), "monthly")` returned `2026-03-28`, not `2026-03-31`. That is not hypothetical — `scripts/verify_readiness.py`'s calendar probe does exactly that, and the recorded baseline in `artifacts/readiness-2026-09-13/contract-probes.json` **encodes the drift as the expected value** (`monthly_second: "2026-03-28"`, `semimonthly_next: "2026-01-30"`).

Root cause: `datetime.date` is immutable with no `__dict__`, so the intended day cannot be attached to a returned date. The first attempt used `object.__setattr__`, which **silently failed** and left chaining still drifting — caught only by checking the returned value rather than trusting the change.

Fix: `_Occurrence`, a `date` subclass carrying `intended_day` in a `__slots__` slot. Every step remembers the day it is keeping, so a clamp is temporary even across held dates:

```
chained monthly      2026-01-31 → 02-28 → 03-31 → 04-30 → 05-31 → 06-30
chained annually     2024-02-29 → 2025-02-28 → 2026-02-28 → 2027-02-28 → 2028-02-29
chained semimonthly  2026-01-15 → 01-31 → 02-15 → 02-28 → 03-15 → 03-31
```

Verified the carrier is transparent everywhere it could leak: `==` and `hash` match a plain `date` (so dict/set membership and sorting are unaffected), `isoformat`, `str` and JSON behave as before, SQLite round-trips it, and `.replace(day=…)` deliberately **discards** the carried day because replacing the day is an explicit override.

Consequence for the readiness record, stated rather than silently edited: the probe would now write `2026-03-31` and `2026-01-31`. The `2026-09-13` artifact is left as-is (it is a dated snapshot of what was measured then, and the audit's own claim is "do not silently treat old observations as fixed"), but it is now **known stale on two fields**. Two further defects in that same file were found and are **not** mine to fix: `scripts/verify_readiness.py` imports `_verify_stored`, removed back in `708e201`, so the `probes` command raises `ImportError` and has not run since; and it imports `next_occurrence_with_index`'s predecessor shape. That script is Astra's declared scope, so this is recorded for that lane rather than edited here. `artifacts/readiness-2026-09-13/runtime-wiring.json` also still reports `crew_initiate_transfer` as `"verifier": false`, stale since the transfer slice.

Tested: 7 more cadence tests pin the chained contract, chained-equals-indexed agreement, the cross-cadence non-leak, date-transparency, and the `.replace` override. `tests/meridian` **794 passed** (was 787); full non-browser **1101 passed, 1 skipped** (was 1094). Ruff, `git diff --check` clean.

Mutation checks: eight deliberate breaks, each caught. **Three mutants were retired as equivalent, not counted as caught** — `annual-never-recovers`, `walk-refeeds-previous` and `semimonthly-can-stall` are all repaired by the carried day on the following step, so they can no longer fail a test. That is a robustness gain (the drift is now unreachable by construction), and recording it is the same discipline applied to the earlier equivalent mutant. Replaced with mutants that do change behaviour: months-ignoring-the-period-count (12 failures), period-index off-by-one (1), sticky-day dropped (4), annual forced to the 28th (2), unknown defaulting to weekly (5), walk not accumulating (6), semimonthly skipping the 15th (1), semimonthly flat +15 (9). Reverted from a byte-identical backup; `git checkout` was not used.

Deployed: nothing. Pure date arithmetic — no provider call, migration, endpoint, authority or money movement.

## Dated occurrences — seven implementations replaced by one rule — 2026-09-15

The roadmap's keystone defect ("the dial's own recurrence engine drifts") is fixed, and it was **wider than recorded**: not three implementations but **seven**, in six modules, and they disagreed in three separate ways. Measured before the change:

| Defect | Evidence (before) |
|---|---|
| Monthly drifted **permanently** after any clamp | `dial`/`billers`/`paycheck` on a Jan 31 anchor: Jan 31 → Feb 28 → **Mar 28 → Apr 28 → May 28**. The clamped February value became the new anchor. |
| Semimonthly meant **two different things** | `paycheck`, `paycheck_learning`, `dial`, `plan`, `today` used a flat `+15 days` (Jan 15 → Jan 30 → Feb 14 → **Mar 1** — off the calendar); only `payday` used "the 15th and month-end". |
| Annual Feb 29 collapsed and **never recovered** | `date(year+1, 2, 29)` raised, the handler fell back to Feb 28, and no later leap year restored the 29th. |
| `payday`'s semimonthly branch was **unreachable** | A semimonthly schedule has 13–18 day gaps, a superset of the biweekly 13–15 window, and the biweekly test ran first — so semimonthly was reported as biweekly. |

**New module: `meridian/cadence.py`.** One rule with the single constraint that fixes the whole class: **month positions are derived from the anchor's day, never from the previous occurrence's day.** A clamp is therefore temporary — Feb 29 clamps to Feb 28 during the walk and still returns on Feb 29 four years later.

Converted to it (`billers`, `paycheck`, `paycheck_learning`, `payday`, `services/dial`, `services/plan`, `services/today`). Verified sequences:

```
monthly     2026-01-31 anchor → 02-28, 03-31, 04-30, 05-31, 06-30, 07-31
semimonthly 2026-01-15 anchor → 01-31, 02-15, 02-28, 03-15, 03-31, 04-15
annually    2024-02-29 anchor → 2025-02-28, 2026-02-28, 2027-02-28, 2028-02-29
```

**A second bug found while fixing the first, in my own new code.** `advance(anchor, rec, n)` is correct, but the *iterating* callers fed each result back in as the new anchor, which reintroduced the drift through the other door (Jan 31 → Feb 28 → Mar 28). `next_occurrence_with_index()` now performs the anchor-preserving walk and returns the period index, so callers enumerate without guessing where the walk stands. That index was itself wrong on the first attempt — it reported k=1 for an occurrence that is k=0 when the anchor already satisfies `as_of`, which silently **skipped every second paycheck** (Sep → Nov → Jan). Caught by the existing `test_future_paycheck_events_generates_from_next_date` expecting three monthly paychecks in 90 days and receiving two.

Not consolidated, deliberately: `funding._monthly_dates` holds `day_of_month` fixed while iterating, so it is already anchor-preserving and correct; it returns a list, so folding it in would be a shape change with no defect to fix.

Tested: new `tests/meridian/test_cadence.py` (37 tests) pinning every defect above plus the vocabulary, unknown-recurrence and index contracts; plus consumer-level regressions in `test_biller_monitor.py` (31st anchor returns to the 31st; semimonthly uses month-end) and `test_payday.py` (semimonthly reachable; an all-equal 14-day gap stays biweekly). `tests/meridian` **787 passed** (was 746); full non-browser suite **1094 passed, 1 skipped** (was 1053). Ruff, `git diff --check` and the guardrail receipt clean.

Mutation checks: seven deliberate breaks, **each caught** — month-shift ignoring the period count (11 failures), period-index off-by-one (1), semimonthly flat +15 (7), annual never recovering (1), unknown recurrence defaulting to weekly (5), the walk re-feeding itself (3), semimonthly able to stall (7). **One earlier mutant was equivalent, not caught, and that is recorded rather than hidden:** re-clamping an already-clamped day is idempotent, so it could never fail a test. It was replaced. All mutations reverted from a file backup verified byte-identical; `git checkout` was not used.

Deployed: nothing. No provider call, migration, endpoint, authority or money movement — pure date arithmetic. Verified: synthetic dates and isolated unit tests only; no live bank data was used.

## C4 — `crew_initiate_transfer` verified by readback; coverage now 16 of 17 — 2026-09-14

The `builder-c4-transfer` claim was released by **doing the work it reserved**. The previous session claimed nine files for it and wrote no code, because one edit failed a read-freshness check and was never retried — so the reservation sat over the tree with nothing behind it.

**The recorded blocker was wrong, and in this lane's favour.** Two entries in `AGENT_COORDINATION.md` and one in the section below state that the transfer stayed unimplemented because "the write's transfer id is uncaptured". Reading the connector source settles it: `write_operations/initiate_transfer.graphql` is `initiateTransfer(input: $input) { result { id __typename } }`, and `crewwrite.py::_result` returns exactly that object — so the write's result **does** carry the transfer id. `transactions.graphql` already selects `transfer { id type status }`. Both halves of an identity match were already present; nothing was ever waiting on a capture.

Implemented:

- `CrewWorkSnapshotAdapter.readback_transfers()` — the observed transfer links from the transactions facet. `None` when the facet was not returned (unobserved), `[]` when it was observed with no transfer links. Never collapsed, per the standing facet rule.
- `_verify_crew_transfer()` — check `crew-transfer-readback`. Presence of the write's transfer id on an observed transaction is provider truth for the write.

The asymmetry is the whole design: **presence confirms, absence is unresolved — never failed.** The connector reads a single page of transactions (`pageSize` 100, `cursor: null`), so an id that is absent from this read may simply be on a page that was never fetched. A single read cannot tell "not yet visible / not on this page" from "the write failed", so it must not claim failure. An unread facet, an incomplete snapshot, and a write result carrying no transfer id are all unresolved. Matching on amount and account was refused, as before: it can report a **false confirmed transfer**.

One design choice recorded rather than buried: the verifier gates on `snapshot.is_complete`, the convention already used by all fifteen prior verifiers here. That is conservative — an unrelated facet's failure keeps a present transfer unresolved. Tightening it to the transactions facet alone would change every verifier, so it was not slipped into this slice.

**Scope limit, stated plainly (this is the honest part):** the transfer is structurally proposable through the generic `POST /api/actions/propose`, which accepts any allowed type, but **no UI control and no automated proposer calls it** — a grep finds only `app.py`'s allowed list and the registry. So this verifies the **engine path**, not an owner-reachable feature. It must not be described as a live capability. For the same reason `top_up_crew_reserve` stays last: it is the only type with no verifier. Also noted: `artifacts/readiness-2026-09-13/runtime-wiring.json` recorded this executor as `"verifier": false`; that field is now stale.

Tested: 5 verifier tests + 3 accessor tests added. The verifier-less test was narrowed to `top_up_crew_reserve` (it previously asserted the transfer had no verifier, which is no longer true), and the coverage guard moved from fifteen pinned readback types to sixteen. `tests/meridian` **746 passed** (was 737); full non-browser suite **1053 passed, 1 skipped**; Ruff, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-transfer` clean.

Mutation checks: four deliberate breaks, each caught by its intended test — absence-made-failed, inverted match, empty-read-as-unobserved, and removed no-id guard. Anchors were asserted to match **exactly once** before applying, which is the specific failure the previous slice hit twice; a helper under `tmp/mutcheck/` did the replacement and refused on a non-unique anchor. All mutations reverted from file backups and verified byte-identical — `git checkout` was not used.

Deployed: nothing. No provider call, no connector change, no migration, no authority change. Remaining unverified: **1 of 17** — `top_up_crew_reserve`.

## C4 — five more operations verified; coverage now 15 of 17 — 2026-09-14

The owner applied the connector patch, landing as `bd7d8b1` in `CrewWorkAssistantOTP` ("Select billReserve.id, fundingPlans and family reassignmentRules"). Verified by reading the two operation files and the commit, not by assumption: `expenses.graphql` now selects `billReserve.id` and `fundingPlans { id name amount frequency frequencyInterval anchorDate reassignmentRule { id match minAmount maxAmount } }`, and `family.graphql` now selects `family.reassignmentRules { id match minAmount maxAmount assignmentSubaccount { id displayName } }`.

Implemented in this lane (the half that was always in-lane):

- `CrewWorkSnapshotAdapter` gained three read-only accessors: `readback_funding_plans` (each plan carries its parent `billReserveId`, so a plan is **attributable to its reserve** rather than name-matched), `readback_reserve_totals` (keyed by reserve id), and `readback_reassignment_rules`.
- Five verifiers: `create/update/delete_crew_paycheck_funding_plan` and `create/delete_crew_pocket_reassignment_rule`, with checks `crew-funding-plan-{create,update,delete}-readback` and `crew-reassignment-rule-{create,delete}-readback`.

Three of the five do **not** depend on the write result, which matters: `update` and `delete` are identified by the id in the approved proposal, and a delete's absence-of-rule is confirmed from an observed-empty list. The two `create` verifiers do depend on the connector returning the new object's id; if it returns none the receipt stays **unresolved** with that stated as the reason. It deliberately does **not** fall back to matching by name, because a same-named plan that already existed would then be reported as a confirmed new write — a false confirmation. `test_funding_plan_create_without_a_provider_id_stays_unresolved` pins that.

Rules held from the previous slices: an **unobserved** facet is `None` and can never confirm (least of all a deletion), while an **observed-empty** list is a real provider statement; absence confirms a deletion but never a creation. Each of these is pinned by its own test for the new facets.

Tested: 14 new tests (5 accessor + 9 verifier) plus the coverage guard updated from ten pinned readback types to fifteen. Focused suite 98 passed; `tests/meridian` **737 passed** (was 721); full non-browser suite **1044 passed, 1 skipped**; Ruff on all five changed files, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-funding-rules` clean.

Mutation checks — and one correction about them: five deliberate breaks were attempted. Three were caught (`absence confirms a funding-plan create`, `unobserved family facet reads as empty rules`, and a changed reassignment delete check name). **Two of the five did not test what I intended**: the anchor string `the rule is still present after the delete` appears **twice** in the file (autopilot and reassignment verifiers), so `replace(..., 1)` hit the *autopilot* verifier both times and failed the autopilot test rather than the new one. A fifth attempt using the reassignment verifier's unique check-name anchor did fail `test_reassignment_rule_delete_readback_confirms_absence_and_flags_presence` as intended. Recorded because a mutation check that silently targets the wrong function is worse than no check — it produces false confidence. All mutations were reverted from file backups and verified byte-identical, never via `git checkout`.

Deployed: nothing. Verified: synthetic payloads and isolated unit tests only — **no live provider call was made from this lane**, and the newly composed queries have not been run against the live server by me. The owner's live connector is the only place that can confirm the composed selections return data. Remaining unverified: **1 of 17** — `top_up_crew_reserve` (needs base-state capture plus a precondition; the handoff is explicit that a changed reserve amount is not proof of a particular top-up; the sequence is its own slice). *(This paragraph originally said 2 of 17 and named `crew_initiate_transfer` as blocked on "the transfer id from the write result, which is still uncaptured" — that reason was wrong and the gap is closed in the section above.)*

All readback types except `top_up_crew_reserve` now have a readback verifier registered in `write-coverage.json`; the `crew_initiate_transfer` gap has been closed with a readback verifier that confirms the provider-returned transfer id appears on an observed transaction. Absence from a single fetched page cannot confirm failure — only presence confirms success — so the receipt stays unresolved, never failed.

## Connector readback fields — verified patch handed to the owner, not applied — 2026-09-14

The owner authorized the connector edit on 2026-09-14 (`expenses.graphql`: `billReserve.id` + `fundingPlans`; `family.graphql`: `reassignmentRules`). **This lane could not make it**, and the reason is the guardrail rather than an oversight:

```
agent-admission: edit is denied because file_path resolves outside this lane (path-escape).
The lane is /Users/stephenwest/Openrouter/simplecrew-latest; …resolves elsewhere.
Mutate inside the lane, or state the change and let the owner make it.
```

That guard is a boundary the owner installed, so it was **not** bypassed with a sandbox escalation — routing around it is precisely what it exists to prevent. The guard's own second route was taken instead: the change is stated, verified and ready.

Deliverable: `docs/project/CONNECTOR_READBACK_FIELDS_PATCH.md` (the patch, the resulting files, the verification and the apply steps) plus the machine-applicable `docs/project/connector-readback-fields.patch`.

Verified before handing over, read-only and in-lane:

- Both proposed documents pass that repository's **own** `crew_work_assistant.safety.assert_read_only` gate (no `mutation`, is a query document).
- `operations.PLACEHOLDER_MARKER` (`CAPTURE_FROM_CREW_WEB_APP`) is absent from both, so `load_operation` will not raise.
- Braces balanced in both.
- **`git apply --check` against the live working tree: clean for both files.**
- Every added field name is **live-verified**, not authored — each appears in an accepted live query in `CREW_DISCOVERY_HANDOFF.md` Appendix A.

What it unblocks: **6 of the 7** remaining readback types (funding-plan create/update/delete, reserve top-up, pocket reassignment-rule create/delete). `crew_initiate_transfer` is excluded because it needs a mutation-result transfer id, which remains uncaptured.

**Honest limit:** each added field is individually live-accepted, but the *composed* documents have not been sent to the server. That residual risk is small, real, and stated in the handoff. It is also unverifiable from this lane without a live call.

Not a mutation: two field selections inside existing queries. No new operation file, no allowlist entry, no write path. The repository's `auth.py` modification and untracked `uv.lock` are untouched and must be preserved; the apply steps stage only the two `operations/` files.

Next after it lands: the in-lane adapter accessors and the six verifiers, then the manifest moves those six types from `verification: none` to `readback`. For `top_up_crew_reserve` the discipline is fixed by the handoff — **a changed reserve amount is not proof of a particular top-up**, so attribution keys on `billReserve.id`, which is why the `id` selection is in this patch rather than a total-only comparison.

## `update_crew_virtual_card` retired from the allowed set — 2026-09-14

Owner-authorized on 2026-09-14. This closes the last known allowed-but-unexecutable gap, and it is the **one** resolution this lane could take without a connector change.

Why it could never work: the type was listed in `ActionStore.allowed_types` in `app.py` but no executor was registered for it, so an approved action could only fail with `error_code: "no_executor"`. The cause was upstream — the connector exposes **no write operation** for a card update: `src/crew_work_assistant/crew_write_cli.py` and its 18 `write_operations/*.graphql` specs contain no `update_virtual_card` (verified by grep; `create_virtual_card` exists, `update_virtual_card` does not). No readback verifier could have made the action work, because the capability to perform the write did not exist.

Change: the type was removed from `allowed_types` in `app.py` with an explanatory comment pointing at the manifest. This **removes a capability** rather than adding one, and removes nothing that functioned — nothing in ORSC proposed it (grep found only `app.py`, `write-coverage.json` and the guard test; no JS/API caller).

Recorded rather than erased: `docs/project/write-coverage.json` gains a `retired_action_types` section carrying the reason, the resolution, the note that `create_crew_virtual_card` is unaffected, and what would reinstate it (a connector write operation, a readback verifier, and an owner decision). `allowed_without_executor` is now empty. A new guard, `test_retired_update_virtual_card_cannot_silently_return`, pins it in **both** directions — it must not reappear as allowed, and it must not vanish from the record either.

**Clarification worth keeping** (this caused a moment of confusion): `create_crew_virtual_card` is a *different* action type and is fully verified by readback from the `virtual_cards` facet, including `user.userSpendConfig.selectedSpendSubaccount`. Retiring the *update* does not touch card readback. `test_create_virtual_card_is_unaffected_by_the_retirement` asserts that explicitly.

Tested: 15 coverage tests pass, including three new ones (no-executor check on all recorded crew types, the retirement pin, and the create-unaffected check). One test of mine was renamed because its name claimed more than it checked: `test_no_allowed_type_lacks_an_executor` → `test_every_manifest_crew_write_type_registers_an_executor`, since it verifies the recorded Crew write registry and not the app-level allowed set (which the AST-based test covers). `tests/meridian` **721 passed** (was 718); full non-browser suite **1028 passed, 1 skipped**; Ruff on `app.py` and the guard clean (three dead variables from the edit were removed); `git diff --check` and `scripts/check_guardrails.py --agent builder-c4-retire-uvc` clean.

Still unaddressed in ORSC: `meridian/crew_commands.py` carries an `UPDATE_VIRTUAL_CARD_MUTATION` constant (via `crew.operations`) that is now unreachable. It is left in place deliberately — removing it risks an import elsewhere and is a separate cleanup — so it is recorded here rather than silently deleted.

Deployed: nothing. Verified: source inspection, AST read of `allowed_types`, and isolated tests only. Next: the authorized connector edit adding `billReserve.id` + `fundingPlans` to `expenses.graphql` and `reassignmentRules` to `family.graphql`, which unblocks 6 of the 7 remaining readback types.

## C4 readback — reconciled against `CREW_DISCOVERY_HANDOFF.md` (2026-09-14)

Astra's live capture (`CREW_DISCOVERY_HANDOFF.md`, 2026-09-14) was reconciled against this lane's gap list. The handoff is authoritative for live-verified shapes; this section records what it does and does not change. **"Not implemented" and "not captured" are different failures and are separated below.**

### Correction of this lane's own reporting

Two claims I made earlier were false and are withdrawn:

- **Commit `3831437` does not exist.** It appears in no ref in ORSC, is absent from the connector repository, and has zero reflog entries (`git cat-file -t 3831437` → `Not a valid object name` in both). It was invented, along with the message that cited it.
- **`update_crew_virtual_card` was reported as "Verified (no readback, but tested)".** That is false. It has no executor in ORSC and no operation in the connector, so it is not verified in any sense. It is a write-capability gap (section D below).

Also noted: commits `28f1141` and `131a337` were both created with the identical message "Enforce verification coverage for every allowed action type". Harmless but sloppy; recorded so the history is not misread as a single commit.

### A — Implemented, and the path is live-verified by the capture (8 of 17)

`autopilot` (`family.rules[]`), `virtual_cards` (`family.parents[]/children[].virtualDebitCards[]`, and `user.userSpendConfig.selectedSpendSubaccount`), and `expenses` (`accounts[].billReserve.bills[]` with `reservedAmount`) are all confirmed live. So `create/delete_crew_autopilot_rule`, `create_crew_virtual_card`, `set_crew_spend_pocket`, `update_crew_bill`, `update_crew_bill_reserve_settings`, `create_crew_bill` and `archive_crew_bill` rest on observed paths, not inference.

### A′ — Implemented, but NOT confirmed by this capture (2 of 17)

`create_crew_pocket` and `delete_crew_pocket` read `data.pockets…subaccounts[]`. **The handoff's Appendix C lists `accounts`, `autopilot`, `virtual_cards`, `expenses` and `transactions` — not `pockets`.** These two verifiers therefore remain source-established only and must not be described as live-verified.

### B — Shape captured, NOT implemented: blocked on the connector's query selections (6 of 17)

Live evidence exists for every one of these; the blocker is that the connector's operations do not request the fields, so ORSC cannot read them. Verified by reading the connector source:

| Operation | Live evidence in the handoff | What the connector selects today |
|---|---|---|
| `create/update/delete_crew_paycheck_funding_plan` | `billReserve.fundingPlans[]` with `id, name, amount, frequency, frequencyInterval, anchorDate, reassignmentRule{id, match, minAmount, maxAmount}` (Appendix A, `FundingPlanReadback`) | `expenses.graphql` selects `billReserve{nextFundingDate, totalReservedAmount, estimatedNextFundingAmount, settings.funding.subaccount, bills}` — **no `fundingPlans`** |
| `create/delete_crew_pocket_reassignment_rule` | `family.reassignmentRules` — query **accepted**, response **observed empty** (Appendix A, `ReassignmentRead`) | `family.graphql` selects `id, children, parents` — **no `reassignmentRules`** |
| `top_up_crew_reserve` | `billReserve.id` verified, plus `totalReservedAmount` and `settings.funding.{subaccount, surplusSubaccount}` (Appendix A, `ReserveSettingsVerified`) | `expenses.graphql` does **not** select `billReserve.id`, so a top-up cannot be attributed to the reserve it targeted |

Closing these needs an additive connector change (select the captured fields, or add the captured operations). The queries already exist and were accepted by the server, so this is implementation, not discovery.

Discipline the handoff requires here: **a changed reserve amount is not proof of a particular top-up** — attribution must use `billReserve.id`, not a delta.

### C — Shape captured, plausibly implementable in-lane, but depends on an uncaptured write result (1 of 17)

`crew_initiate_transfer`. The connector's `transactions.graphql` **already selects `transfer { id type status }`** (line 17), and the handoff found a non-null `transaction.transfer.id` plus a working `node(id) Transfer` shape (Appendix B). Identity matching on `transfer.id` is sound, and the handoff explicitly forbids the weaker alternative (*"a historical transfer's existence is not proof it matches a proposed action"*).

It is not implemented because verification needs the **transfer id returned by the write**, and the handoff records that mutation result shapes are not yet established ("Establish mutation input types/defaults and success/error outcomes where source alone is insufficient"). Pagination compounds it: the connector fetched one page, and the observed non-null transfer link was on page two — so a freshly created transfer may be absent from the read and must report **unresolved**, never confirmed or failed.

### D — Not a readback gap at all (1)

`update_crew_virtual_card` is in ORSC's `ActionStore.allowed_types`, has no executor, and `crew-write` exposes no `update_virtual_card` operation. The capability to perform the write does not exist, so no verifier can make it work. Parked at the owner's and Astra's direction; the correct resolutions remain "add the write op + verifier" or "retire the type from `allowed_types`".

### E — Genuinely uncaptured (does not block the 17)

Per the handoff's own remaining work: `SweepExcessAction` destination/threshold fields, `NumericAttributeCondition` fields, auto-cancel and card-inheritance semantics, mutation input defaults, and GraphQL introspection (returned errors — so schema introspection is **not** an available route). Also `cancelDate`/`expiresAt` were rejected as `DebitCard` fields and must not be implemented as guesses.

### Documentation correction carried forward

The handoff corrects an earlier illustrative shape: live `formula.conditions` is an **object** (e.g. `AndCondition` with nested `conditions`), not an array. No code in this lane reads `conditions`, so nothing shipped is affected. `docs/project/CREW_GRAPHQL_CATALOG.md` describes `conditions.and.conditions` as a *create-rule input* nesting; that input claim is neither confirmed nor refuted by this read-only capture and is left as-is rather than "corrected" on inference.

### One further connector defect, recorded not fixed

The connector's existing `ActivityDetail` operation fails validation: `latestDebitCardTransactionDetail` is no longer accepted on `CashTransaction`. Crew suggested `relatedTransactions`, which is **not** established as equivalent. This does not affect ORSC (which reads `snapshot` only), but it is a real defect in that repository.

### Status

Implemented and verified coverage is **10 of 17** Crew write types; of those, **8 rest on live-verified paths and 2 (pockets) do not**. Six are blocked only on connector field selection with their shapes already captured; one needs a mutation result shape; one needs the write capability itself. No provider call, credential, migration or authority changed in this reconciliation.

## C4 — three more operations verified from facets that were already being fetched — 2026-09-13

**This corrects the blocker recorded below.** I had reported the remaining readback work as needing a capture or a connector change. For three of those operations that was wrong, and the error was mine: I read Meridian's adapter instead of the connector's actual output. `CrewReadClient.snapshot()` (`client.py:113–122`) has always fetched **eight** facets — `accounts, pockets, transactions, expenses, family, physical_cards, virtual_cards, autopilot` — and Meridian's adapter read only four, silently discarding `virtual_cards` and `autopilot` along with the data needed to verify card and rule writes.

Implemented: `CrewWorkSnapshotAdapter` gained three read-only accessors (`_facet_payload`, `readback_virtual_cards`, `readback_autopilot_rules`) and three operations gained provider readback verifiers — **`create_crew_virtual_card`** (cards facet, provider-returned card id, compared on name and colour), **`create_crew_autopilot_rule`** (rules facet, provider-returned rule id, compared on name), and **`delete_crew_autopilot_rule`** (rules facet, identified by the approved proposal's own `rule_id`). Verified coverage rises from **6 to 9** of the 17 Crew write types.

Two design rules were applied deliberately, and both are pinned by tests:

- **An unobserved facet is not an empty facet.** The connector omits a facet it could not read and records the failure in `errors`; a facet that returns no records is a different fact. The accessors return `None` for unobserved and `[]` for observed-empty, so a failed read can never masquerade as "the provider says no card exists" — the same error class as an unreported reserve read as zero (C01).
- **Absence confirms a deletion, never a creation.** A card or rule absent from one read is `ok: null` (unresolved), because propagation delay is indistinguishable from failure in a single read. Presence after a delete is a provider-confirmed contradiction — the direction that can never falsely claim something is gone. `ok: null` remains non-resubmittable, including across restart.

Scope and safety: no endpoint, schema, migration, authority, routing, retry or provider-call change; the connector itself was **not** modified. The one provider interaction added is the existing read-only `capture_crew_snapshot` call the other verifiers already use.

Tested: 4 new adapter tests and 10 new verifier tests (including a facet-absent case for both facets and a fresh-process restart case), and the coverage guard was updated from six pinned readback types to nine. Focused suite **55 passed**; `tests/meridian` **706 passed** (was 691); full non-browser suite **1013 passed, 1 skipped**. Ruff on all five changed files, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-facets` clean. Mutation checks: four deliberate breaks were each caught — unobserved-facet-returns-empty (1 failure), absence-confirms-creation (1), present-rule-confirms-deletion (1), and the rule-facet counterpart of the first (2). All were reverted and the files verified byte-identical to their backups.

**Process failure in this slice, recorded because it destroyed work:** a mutation check used `git checkout -- meridian/crew_write_actions.py` to revert a deliberate break — which discarded the *uncommitted* verifiers themselves, not just the mutation, because `git checkout` restores from `HEAD` and this file's work was not yet committed. The file dropped back to six verifiers and 8 tests failed. Caught immediately by re-running the suite, re-applied from the recorded source, and the remaining mutation checks were redone with file backups instead. Lesson: for a mutation check on uncommitted work, back up the file and restore from the copy — never `git checkout`.

Deployed: nothing. Verified: synthetic facet payloads and isolated unit tests only; **no live provider call was made**, so the assumed nesting inside `data` is inferred from the connector's query specs rather than observed. That is the main open risk in this slice: if the real nesting differs, each accessor returns `None` and every new verifier stays unresolved — honest, but not useful. Confirming it needs one credential-free captured payload, which is the next step. Remaining unverified: 8 Crew write types. Next: confirm the two facet shapes against a captured payload, then resume the `--variables` connector change for targeted reads.

## C4 remaining readback — blocked on the provider read surface (evidenced) — 2026-09-13

The 11 unverified operations cannot be given an honest readback verifier with the evidence available in this repository. This is now **evidenced from source**, not asserted: `meridian/providers/crewwork.py` has exactly three collectors (`_collect_accounts`, `_collect_transactions`, `_collect_commitment_candidates`) and reads exactly these provider fields — `data.pockets…accounts[].subaccounts[]` (`id`, `displayName`, `isPrimary`, `overallBalance`, `clearedBalance`), `data.accounts…accounts[]` (`id`, `displayName`), `data.transactions…cashTransactions.edges[]` (`id`, `occurredAt`, title/merchant/subaccount/amount), and `data.expenses…accounts[].billReserve.bills[]` (`id`, `name`, `amount`, `anchorDate`, `frequency`, `reservedAmount`). Nothing else.

Per type, the specific missing field:

| Operation | Missing readback evidence |
|---|---|
| `create/update/delete_crew_paycheck_funding_plan` | No funding-plan object is read at all — no plan id, name, amount, frequency or anchorDate readback |
| `create/delete_crew_autopilot_rule` | No rule object is read — no rule id, name, `isPaused`, formula or triggers |
| `create/delete_crew_pocket_reassignment_rule` | No reassignment-rule object is read — no rule id or `match` |
| `create_crew_virtual_card` | No card surface is read — no `virtualDebitCards`/card id |
| `top_up_crew_reserve` | `billReserve` is read **only** for its `bills[]`; there is no bill-reserve id and no reserve total, so a top-up cannot be attributed to the reserve it targeted |
| `set_crew_spend_pocket` | The selected spend pocket lives in `userSpendConfig.selectedSpendSubaccount`, which is not read. `subaccounts[].isPrimary` is read, but it is the account's primary pocket, **not** proven to be the user's spend selection — treating it as the same signal could produce a false confirmation or a false contradiction, so it is not used |
| `crew_initiate_transfer` | Transactions are read, but the connector's result contract (whether a usable transfer/cash-transaction id is returned) is not captured. Matching on amount plus account alone would be weak evidence capable of reporting a **false confirmed transfer** — the worst available failure — so it is refused |

Closing any of these needs evidence this lane cannot obtain without an owner-approved action: either a credential-free captured read payload for the relevant surface, an extension of the read-only connector (a different repository), or a one-off owner-approved live capture. Live banking data and credentials are prohibited in this lane, so none of the 11 can be advanced here.

Two things are **not** blocked and remain available: the `update_crew_virtual_card` resolution (owner decision: add a card readback verifier, or retire the type from `allowed_types`) and any further honesty work on surfaces that render outcomes.

Also checked this round and found **not** a gap: the legacy account approval panel (`static/js/api/account.js`) lists only `/api/actions/pending`, which returns `proposed` actions. A proposed action has no verification receipt by definition, so there is nothing for it to render. It was inspected and correctly left unchanged.

## C4 write-coverage manifest is now enforced — 2026-09-13

Implemented (completeness half of C4, concept "single constrained executor"): `docs/project/write-coverage.json` records an explicit verification decision for **every** registered Crew write action type — `readback` (naming the receipt `check`) or `none` (with the concrete reason no readback exists). `tests/meridian/test_write_coverage.py` makes it enforced rather than descriptive: a newly registered action type with no recorded decision fails the suite; a type cannot silently gain or lose a verifier; a readback entry's `check` string must actually appear in `meridian/crew_write_actions.py`; a `none` entry must not claim a check name; a stale entry fails. The file also records the **engine-level** verifiers registered in `app.py` (so the coverage picture spans both registries) and the `update_crew_virtual_card` allowed-but-unexecutable gap.

Measured current coverage `[E]`: **28 allowed action types, all now recorded.** 17 registered Crew write types — **6 verified by provider readback, 11 without a verifier**; 4 engine-level types in `app.py` that carry verifiers; 6 memory types (asset/contract) that all verify by local re-read; and 1 allowed-but-unexecutable type. The 11 unverified types are recorded individually with the specific missing readback shape (funding plans, autopilot rules, pocket reassignment rules, virtual card, reserve top-up, spend pocket, transfer), so the gap is enumerable instead of an approximate "15 of 27" from a hand count.

Self-correction made in this slice, recorded because the first draft would have shipped another partial inventory: the manifest initially covered only the 17 Crew write types while its own wording implied it covered the allowed set. The 6 `MEMORY_ACTION_TYPES` (create/update/delete asset and contract) are also in `ActionStore.allowed_types` and all register verifiers, so they were added, and `test_manifest_covers_every_allowed_action_type` now reads the real `allowed_types` out of `app.py` by AST (app.py is **not** imported — that would create the live database and a key file) and fails on any allowed type that is unrecorded or any recorded type that is not allowed.

Also recorded, and independently confirmed this round: `update_crew_virtual_card` is listed in `ActionStore.allowed_types` in `app.py` (line 1026) but **no executor is registered for it** (the Crew registry registers `create_crew_virtual_card`, not the update). An approved action of that type therefore fails closed with `error_code: "no_executor"`. It cannot mutate anything, but it is an owner-visible dead end: the owner can approve a card update and watch it fail every time. It is recorded as an `open-gap` with its next action, not silently dropped.

Tested: 12 new tests, all passing. Their teeth were verified by six deliberate mutations — deleting a recorded Crew entry, flipping a type from `readback` to `none`, giving a type an invented `check` name, adding an unregistered Crew type, dropping `delete_contract` from memory coverage, and adding a non-allowed type — each failing the intended tests (2, 2, 1, 3, 2 and 2 failures respectively), with the manifest restored byte-identical afterwards. Focused suite (coverage + outcome + history + review) **25 passed**; `tests/meridian` **691 passed** (was 679); Ruff on the changed test file and `git diff --check` clean. No provider call, credential, database, deployment, preset or migration was involved — the registries are read with temporary database paths.

Honest limits and a second correction made in this slice: the manifest's first draft asserted two engine-level check names (`transfer-verification`, `funding-rule-verification`) that I had **not** verified against the source. Grepping `app.py` showed the real values are `confirmed-transfer-id` and `funding-rule-state-reread`; the manifest was corrected to the actual strings, and a test now pins them to the source so the same invention cannot ship. No browser check ran. This slice adds no verifier to any operation: it makes the existing coverage legible and prevents silent regression.

Deployed: nothing. Verified: registry introspection, static source analysis, manifest assertions and mutation checks only. Remaining gaps: the 11 unverified operations need provider readback shapes (currently capture- or owner-gated); `update_crew_virtual_card` needs either an executor with a card readback verifier **or** removal from `allowed_types`, and which of those is right is an owner product decision (retiring a capability is not the agent's call) — it needs no new provider contract either way. Full C4 reachability and live owner acceptance remain open. Next: ask the owner which resolution they want for `update_crew_virtual_card`, and meanwhile close one of the 11 unverified types whose readback shape already exists.


## C4 receipt reaches Plan and Memory — 2026-09-13

Implemented: the shared outcome interpreter `static/js/meridian/action-outcome.js` is now receipt-aware, so every surface that interprets a durable action result — Plan (`plan.js`, 4 call sites) and Memory management (`memory-manage.js`) — renders the same recorded receipt the Settings history renders, instead of a generic line. An accepted action whose readback could not confirm it now names the recorded check and reason ("could not confirm … crew-bill-readback: readback unavailable: timed out") and still forbids resubmission; a provider-confirmed contradiction is named as a contradiction ("Provider readback contradicted this change … It was accepted once and must not be resubmitted; reconcile in Actions & Approvals"); a verifier exception stays pending, never a terminal failure invented from an exception. The `verified` path is the only `ok` tone and the only state that refreshes.

Scope and safety: presentation only. No endpoint, schema, migration, authority, routing, retry or provider call changed; no surface gained an approve/execute/reject control. The surfaces still do not re-derive a receipt themselves (a test asserts neither `plan.js` nor `memory-manage.js` mentions `provider_truth` or `summarizeVerification`), so there is one interpreter and one receipt module.

Tested: 2 new tests in `tests/meridian/test_action_outcome_js.py` execute the interpreter under Node with the payload shapes `crew/executors.py` stores — unresolved/timed-out, verifier-exception, no-verifier, provider-contradicted, and the preserved uncertain-write copy — and pin that Plan/Memory receive the receipt through the shared interpreter rather than re-deriving it. Focused suite (outcome + receipt + review + history + haptics) **44 passed**; `tests/meridian` **679 passed**; full non-browser suite **986 passed, 1 skipped**. Ruff on the changed test file, `node --check` on the changed JS, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-outcome-receipt` all clean. No live provider, credentials, deployment, preset or migration change.

Honest limits: no browser check ran, so on-screen rendering is not claimed; and this slice deliberately did **not** alter the pre-existing fallback copy for a bare `executed` record, which remains the generic "verification is still pending" line — a first draft of the test asserted stronger copy than the code produced, and the test was corrected rather than the copy.

Deployed: nothing. Verified: synthetic payloads and isolated unit tests only. Remaining gaps: funding-plan/autopilot-rule/reassignment-rule/virtual-card/reserve readback still need a provider contract; full C4 reachability and live owner acceptance remain open. Next: one further operation-specific readback once a readback shape exists.

## C4 verification receipt is now visible — 2026-09-13

Implemented (honest-receipt half of C4, concept "single constrained executor"): the read-only Settings action history now renders the durable post-execution verification receipt instead of hiding it in the stored JSON. New presentational module `static/js/meridian/action-verification.js` reads the receipt from **both** places the pipeline writes it — `action.verification` (`mark_verified`) and `action.result.verification` (`mark_executed`, `record_verification_pending`, `mark_failed`) — and classifies it tri-state: `confirmed` (ok true), `contradicted` (ok false, provider truth), `unresolved` (ok null, or no verifier registered at all). An unresolved receipt renders as "the provider accepted this change, but the readback could not confirm it. Do not resubmit it."; an action with no receipt renders as no verifier registered and unconfirmed. **`ok: null` can no longer be read as success or as failure.** Reasons, requested and observed values are shown verbatim; nothing is inferred.

Scope and safety: presentation only. No endpoint, schema, migration, authority, routing, retry or provider call changed; the surface still exposes no approve/execute/reject control, and `actions.js` remains read-only. Styles were appended to the existing shared `static/css/meridian/action-review.css` (reusing its grid tokens) so no new stylesheet or script tag was added. The success tone is applied only to `confirmed`.

Tested: new `tests/meridian/test_action_verification_js.py` executes the module under Node against the exact payload shapes `crew/executors.py` stores — confirmed, unresolved/timed-out, verifier-exception, provider-contradicted, no-verifier, and absent-field cases — and asserts the renderer builds a read-only receipt without `innerHTML`. Focused suite (receipt + review + history + outcome) **15 passed**; `tests/meridian` **677 passed** (was 673); Ruff on the changed test file, `node --check` on both JS files, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-receipt-ui` all clean. No live provider, credentials, deployment, preset or migration change.

Discipline note (`[D]`, recorded because it is a real defect in this slice's process): the first attempt at this change truncated `static/js/meridian/actions.js` from 108 to 59 lines with a shell heredoc, deleting `render()`, `load()` and the refresh wiring. It was caught by `git diff --stat` before any test run, restored from `HEAD`, and redone with targeted edits; the final diff is +8/−1 on that file. The claim was also recorded in the same round as the edits rather than before them. Both are recorded rather than hidden: a slice that damages a file and repairs it is not a clean slice, even when the end state is correct.

Deployed: nothing. Verified: synthetic payloads and isolated unit tests only; **no browser check was run**, so "renders correctly in the running Settings page" is not claimed. Remaining gaps: funding-plan/autopilot-rule/reassignment-rule/virtual-card/reserve readback still need a provider contract; full C4 reachability and live owner acceptance remain open. Next: review, then one further operation-specific readback once a readback shape exists.

## C4 funding-plan readback — blocked pending provider contract

The next low-risk registered operations are paycheck funding-plan create/update/delete. The mutation inputs are captured in `docs/project/crew_mutations.json` and the read operation names/fields are cataloged, but the application has no normalized funding-plan fields, provider adapter mapping, or readback fixture. Implementing a verifier now would invent the provider's returned identity/field semantics and could misreport financial state. No code changes were made in this round; the claim was released. Safe next action: establish a credential-free read-only funding-plan snapshot shape (fixture or owner-approved capture), then resume one operation-specific verifier.

## C4 pocket deletion readback repair — 2026-09-13

Implemented: `delete_crew_pocket` now verifies absence from a fresh, complete Crew snapshot. Complete absence is verified; presence is provider-confirmed failure; missing, partial, stale, malformed, timeout, or exception readback remains unresolved and non-retryable. No accepted deletion is resubmitted, including after restart. Proposal → owner approval → single-attempt execution → provider verification remains intact.

Tested: focused C4/routing suites **69 passed**; `tests/meridian` **673 passed**; changed-path Ruff, `git diff --check`, and guardrail receipt passed. Synthetic fake-provider coverage proves complete absence, partial readback, and no resubmission. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: verifier-less financial operations, full mutation reachability, and live owner acceptance. Next: continue to the next low-risk operation-specific readback slice.

## C4 pocket readback repair — 2026-09-13

Implemented: `create_crew_pocket` now verifies the provider-generated pocket ID and returned identity fields against a fresh, complete Crew snapshot. Incomplete, missing, malformed, timeout, exception, or mismatched readback remains unresolved or provider-confirmed failure as appropriate; the accepted operation is non-retryable and never resubmitted. Proposal → owner approval → single-attempt execution → provider verification remains intact.

Tested: focused C4/routing suites **67 passed**; `tests/meridian` **671 passed**; changed-path Ruff, `git diff --check`, and guardrail receipt passed. Synthetic fake-provider cases cover complete confirmation, incomplete readback, and no resubmission. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: other verifier-less operations, full mutation reachability, and live owner acceptance. Next: continue to the next low-risk operation-specific readback slice.

## C4 create-bill readback repair — 2026-09-13

Implemented: `create_crew_bill` now verifies the provider-generated bill ID and requested name/amount against a fresh, complete Crew snapshot. Missing, partial, stale, malformed, timeout, exception, or mismatched readback is unresolved (`executed`, `ok: null`) unless provider truth proves a mismatch; the accepted create is never resubmitted, including after restart. The existing proposal → owner approval → single-attempt execution → provider verification pipeline is preserved.

Tested: focused C4 suite (`tests/meridian/test_crew_write_actions.py tests/crew/test_executors.py`) **53 passed**; `tests/meridian` **669 passed**; changed-path Ruff, `git diff --check`, and guardrail receipt passed. Synthetic fake-provider coverage proves complete confirmation and incomplete readback/no-resubmit. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: other verifier-less operations, full mutation reachability, and live owner acceptance. Next: review this commit.

## C4 archive readback repair — 2026-09-13

Implemented: `archive_crew_bill` now uses a fresh complete Crew snapshot verifier. A complete readback proving the bill is absent is verified; a still-present bill is a provider-confirmed failure; missing, partial, stale, malformed, timeout, exception, or otherwise inconclusive readback remains `executed` with `ok: null`, `provider_truth: false`, and `retry_allowed: false`. The accepted operation is never resubmitted, including after restart.

Tested: focused C4 suite (`tests/meridian/test_crew_write_actions.py tests/crew/test_executors.py`) **51 passed**; changed-path Ruff and `git diff --check` passed. Synthetic fake-provider coverage includes complete present/absent, partial, exception and restart/no-retry cases. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: other verifier-less operations and full mutation reachability/live owner acceptance. Next: review and then select one further operation-specific readback.

## C4 post-execution financial verification repair — 2026-09-13

Implemented: reserve-setting writes now verify against a fresh, complete Crew snapshot rather than local commitments; missing, partial, stale, malformed, mismatched, timed-out, and exception readbacks remain explicitly unresolved (`executed`, `ok: null`, `provider_truth: false`, `retry_allowed: false`). A missing bill is no longer reported as confirmed deletion for bill updates. Verifier exceptions after provider acceptance no longer become false terminal failures. The existing proposal → owner approval → single claim/execution → provider verification pipeline remains unchanged; unresolved actions are non-claimable and never resubmitted.

Tested: RED reproduction from `scripts/verify_readiness.py probes` recorded the reserve verifier's no-local-ID false success, local-ID `AttributeError`, and partial-readback false deletion. RED→GREEN focused suite `tests/meridian/test_crew_write_actions.py tests/crew/test_executors.py` — **48 passed**; `tests/meridian` — **664 passed**; Ruff on changed paths, `git diff --check`, and `scripts/check_guardrails.py --agent builder --receipt <temp>` — clean. Synthetic cases cover complete match, missing/partial/stale/malformed/mismatched readback, timeout, verifier exception, and fresh-process restart; each asserts one provider submission and no retry. Preset identity/guard check: installed `Meridian Constitutional Builder` files at `/Users/stephenwest/.dsh/.agent-presets/meridian-constitutional-builder`, `verify_preset.py` — **33 invariants passed**. No live provider, credentials, deployment, preset modification, or migration change.

Deployed: nothing. Verified: synthetic provider/readback and isolated application tests only; no live financial acceptance or production deployment. Remaining gaps: other verifier-less operations still require future operation-specific readbacks; C4-wide mutation reachability and owner/live acceptance remain open. Next: perform one bounded operation-specific readback expansion after review.

## Expanded readiness audit — 2026-09-13

Implemented: reusable `scripts/verify_readiness.py`, safety tests, [readiness report](MERIDIAN_READINESS_AUDIT.md), prerequisite order and gameplan supplement. Tested: isolated application image **953 passed, 7 skipped, 1 failed** (machine-local Crew CLI unavailable); selected Harness suites **236 passed**; audit-tool safety checks **3 passed**. Synthetic restore passed across 21 migrations, WAL backup, failed-migration rollback, wrong-key/tamper rejection, fresh-process authenticated routes and unresolved-action non-retryability. Runtime inventory: 199 routes, 27 executors; allowed `update_crew_virtual_card` lacks executor. Static/probe evidence identifies remaining authority, verification, observation, recurrence, scenario and intake gaps. New maintainer R0 and Docker exclusions were reconciled rather than reported as unimplemented.

Deployed: nothing. Verified: synthetic recovery and stated test scope only; no fresh physical-device capture, live financial acceptance, production restore or installed-preset activation. Evidence: `artifacts/readiness-2026-09-13/`. Next: H0 custom-preset negative acceptance tests and bounded C4 financial verification repair, then C1/C2 event/observation integration. Preserve unrelated dirty files; this audit does not authorize live changes.

## Forward gameplan — 2026-09-13

Planning deliverable: [MERIDIAN_EXECUTION_GAMEPLAN.md](MERIDIAN_EXECUTION_GAMEPLAN.md), sections D1–D8 plus disagreements, one first move and unknowns. Evidence in `artifacts/gameplan-2026-09-13/`. Fresh remote listing returned only `main` and `feat/meridian-implementation`; 23 local tracking entries include 17 absent-server non-ancestor tips that must be preserved/reviewed before pruning. Ruff still reports 11 findings. Two disposable Git-fixture probes demonstrate defects in the proposed guardrail script's migration check. No cleanup, application implementation, preset installation, Harness restart, deployment or live acceptance occurred. Next proposed Harness move: H0 keyless red specification for the combined authority/re-entry gate, after owner approval of D3/D4. Full economic-OS vision remains subject to the mapped product contracts and evaluation; the plan is not a completion claim.

## Dial alignment incident fixed — 2026-09-12

**iPhone Air follow-up:** corrected an additional 18px horizontal overlap by keeping the enlarged dial inside its right grid boundary and adding a 12px gutter. WebKit and Chromium tests at 420×912 pass; **47 focused checks passed** and eight device-specific captures show zero overflow. Corrected CSS verified on the running local preview. Details and evidence are in the incident report below.

See [DIAL_ALIGNMENT_FIX_2026-09-12.md](DIAL_ALIGNMENT_FIX_2026-09-12.md). Implemented top-aligned dial, bounded scrollable callouts, full-width mobile titles/amounts, a separate date-control row and preview template auto-reload. Twelve synthetic events reproduced an 879px blank offset before the fix. **71 focused tests passed**, Ruff/diff checks passed; a 16-capture dense-data matrix reports zero overflow/page errors. Existing local preview on 8081 reloaded with the same database path/runtime configuration; login HTTP 200 and all three served UI asset hashes verified. No image publication, financial mutation, credential change or migration. Authenticated phone rendering has not been recaptured; broader visual QA remains separately tracked.

## Observatory refinement checkpoint — 2026-09-12

**Paused at owner request (usage budget).** Code/assets are saved; latest focused verification is **68 passed**, Ruff clean and diff whitespace clean. Safe-to-spend and original side-callout composition are restored, with keyboard focus fixes and a compact evidence card. The last full matrix had zero overflow/page errors but predates the compact-card adjustment; final screenshot review remains pending. Resume from the latest section in [OBSERVATORY_REFINEMENT_2026-09-12.md](OBSERVATORY_REFINEMENT_2026-09-12.md). No production deployment or live-data change.

Owner requested a focused visual correction, then emphasized prominent safe-to-spend and the original dial-left/callouts-right composition. Work is saved but not yet declared complete: [checkpoint and evidence](OBSERVATORY_REFINEMENT_2026-09-12.md). Implemented: dial artwork/layout and keyboard-focus correction, Today safe-to-spend presentation, isolated synthetic full-template preview. Latest composition browser checks: 7 passed; earlier focused suite: 36 passed. Final full Today matrix/review remains pending. No production deployment or live financial/data/credential change. Continue from this checkpoint; preserve unrelated files.

## Second roadmap review — 2026-09-11

See [MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md](MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md). This informed, single-agent review compares the first vision roadmap with governing documents and targeted source at `a20702716046f2beadfd1d6c1f3801585a9beeeb`. It proposes capability-based delivery, accounts for all 22 concepts and findings A–G, and selects V1.1 (ordinary sync → persisted observation → explained Today amount) as the next proposed bounded slice. No roadmap proposal is recorded as an accepted owner decision.

Implemented: documentation only. Tested: 45 focused policy/proactive/scenario/dial checks passed (exact command in report); isolated synthetic probes characterize observation identity/freshness/empty captures and recurrence drift. Verified after the computer interruption: report is intact; pytest and Playwright packages are installed, and the Chromium executable exists. The older Playwright-install blocker and “entire Observatory unbuilt” claim must not guide current planning. No fresh browser journey, full-suite gate, live provider acceptance, deployment or live-data change occurred. No independent review is claimed.

OS-001 links this partial audit evidence; its existing status is retained pending reconciliation of the full task contract. Next: review the second roadmap and prepare the bounded V1.1 implementation packet. Preserve the first roadmap and historical completion records; do not treat ledger closure as whole-product acceptance.

## Canonical sources

> This copy of the project is the **separate OpenRouter build** living on
> `dirdir207-png/ORSC`. It does not touch the preexisting SimpleCrew repository
> (`dirdir207-png/SimpleCrew`), its branches, or the upstream project, which
> continue independently. All work here stays on ORSC.

- Repository: `dirdir207-png/ORSC` (separate Meridian build)
- Default branch: `main` (unchanged; this build is developed on a branch)
- Implementation branch: `feat/meridian-implementation` (on ORSC)
- SimpleCrew-side branches (`ox-alpha/meridian-overhaul` and others) are owned by the other project and are not used by this build
- Approved design: `docs/superpowers/specs/2026-08-26-meridian-product-overhaul-design.md`
- Implementation plan: `docs/superpowers/plans/2026-08-26-meridian-overhaul-implementation.md`
- Model strategy: `docs/superpowers/plans/2026-08-26-meridian-model-and-token-strategy.md`
- Codex CLI handoff: `docs/project/CODEX_CLI_HANDOFF.md`
- Approved specifications override informal chat history when they conflict.

## Architecture and safety decisions

- Enhanced SimpleCrew runs on the always-on Mac.
- Crew GraphQL is the primary banking-data path.
- Crew credentials and bearer/session tokens remain server-side/local and must never be exposed to browser or Base44 frontend code.
- Tailscale is the intended private remote-access path (`docs/REMOTE_ACCESS.md`).
- Existing SimpleCrew authentication/passkey protection remains in place.
- Financial mutations must never be retried automatically; uncertain transfer outcomes surface as `uncertain_write` / verify-state.

## Milestone status

### Slice 1 — Trustworthy foundation and shell: COMPLETE ✅

Tasks 1–8 fully implemented, tested, and pushed to `feat/meridian-implementation`:
- Production config, CI, Docker, browser-smoke gates (Task 1)
- Atomic/idempotent action execution with EXECUTING claim state (Task 2)
- Versioned migrations (001–004), normalized financial read model (Task 3)
- Crew data adapter → Meridian graph (Task 4)
- `/api/meridian/*` read APIs (Task 5)
- Editorial Wealth design tokens, responsive shell (Task 6)
- Today workspace, Activity ledger with cursor pagination (Task 7)
- Transaction inspector (Task 8)
- **Slice 1 Docker gate passed: 204 tests, Ruff clean, meridian:slice1 image verified**

### Slice 2 — Commitments and funding: COMPLETE ✅

Tasks 9–12 fully implemented, tested, and pushed to `feat/meridian-implementation`:
- Unified Meridian Commitments with dataclass + repository (Task 9)
- Funding calculus with 7 rule kinds, DST-immune, carry-forward (Task 10)
- Idempotent scheduled funding proposals with dedup (Task 11)
- Plan workspace: service, API, UI (Task 12)
- **Slice 2 Docker gate passed: 259 tests + 28 browser skips, Ruff clean, meridian:slice2 image verified**

### Crew Session Broker — COMPLETE ✅ (merged to main)

- AES-256-GCM encrypted credential storage, macOS Keychain adapter
- Loopback broker API with capability authentication
- Cookie-aware transport, Docker-side broker transport
- Renewal endpoints, LaunchAgent installer, Docker Compose template
- **150 broker-focused tests passing** (2 pre-existing Meridian advisor failures unrelated)

### Slice 3 — Unified providers and transaction intelligence: COMPLETE IN CURRENT BRANCH ✅

- Tasks 13–16 (providers, reconciliation hardening) are consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 4 — Advanced intelligence and consolidation: COMPLETE IN CURRENT BRANCH ✅

- Tasks 17–20 are consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 5 — Document Intelligence: COMPLETE IN CURRENT BRANCH ✅

- Tasks 21–23 are consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 6 — Life Context: COMPLETE IN CURRENT BRANCH ✅

- Task 24 is consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 7 — Asset and Contract Memory: COMPLETE (Task 26 done in current branch)

- Task 25 is consolidated in the ORSC `feat/meridian-implementation` branch.
- Task 26 (evidence memory across workspaces + asset/contract management) is complete in
  `feat/meridian-implementation` per `docs/superpowers/specs/2026-08-31-task26-evidence-memory-design.md`
  and `docs/superpowers/plans/2026-08-31-task26-evidence-memory.md`:
  - Four memory endpoints: `GET /api/meridian/memory/{today|plan|activity|accounts}`.
  - Six pipeline action types: `create/update/delete_asset`, `create/update/delete_contract`
    (propose→approve→execute; executors/verifiers in `meridian/memory_actions.py`).
  - Management proposal API: `POST/PATCH/DELETE /api/meridian/assets` and `/contracts`.
  - Evidence content resolves end-to-end (`MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY` configured;
    `DerivedKeyProvider` in `meridian/storage.py`).
  - Frontend: per-workspace memory regions, Assets & Contracts management UI, pending
    memory-proposal approval rendering.

> Historical per-task commit SHAs (`726e00e`…`a092c4a`) were local-only and never
> existed on GitHub; this build tracks the ORSC branch tip instead.

## Current test suite

- Fresh gate run on `feat/meridian-implementation` (2026-09-06):
  - Ruff clean (`ruff check app.py crew meridian tests` — import-sort/warnings fixed,
    including removal of the dead `build_command_payload` / `reconcile_crew_mutation`
    imports in `app.py`).
  - Full unit suite: **535 passed, 60 skipped** (skips are the Playwright browser
    tests that require a running `APP_URL`).
  - `pip-audit -r requirements.txt`: **no known vulnerabilities**.
  - Browser suite (against the live preview): `test_capability_parity.py` (3),
    `test_plan.py` + `test_meridian_shell.py` (18), plus the R30 parity contract —
    see docs/project/PRIVATE_RELEASE_ACCEPTANCE.md §1/§5.
- Historical Slice-2 / 445-test counts are superseded by the 2026-09-06 gate above.

### R32 (private daily-use release) — 2026-09-06

See `docs/project/PRIVATE_RELEASE_ACCEPTANCE.md` for the full record. Summary:
- Tested image digest `sha256:6ac1fac8f1c1…`; `docker-compose.yml` pinned to
  `meridian:r32-test` (no more `build: .`).
- 2 fresh read-only Crew captures (6 accounts / 100 txns each); app + collector
  restart, last-good offline recovery, and unchanged-tab refresh verified.
- **Two recorded non-green items (not release-blocking, but explicit):**
  1. The active daily-use instance is the local preview (port 8081) running from
     source, not the tested Docker digest — compose target matches digest, the
     daily instance does not.
  2. Autopilot query schema drift (`Cannot query field "entities" on type "Rule"`)
     leaves every sync `status=partial` (errors=1, autopilot null). The query spec
     lives in WorkAssistant (`operations/*.graphql`, owner-gated), **not** ORSC;
     benign to accounts/transactions/commitments.


### Observatory implementation — 2026-09-08 (ongoing small slices)

- Branch: `feat/meridian-implementation`; ahead of origin by 41 commits after this session.
- Slice 1 (already on branch): Observatory visual tokens/layer, decorative SVG placeholder
  asset set, and a fixture-driven accessible dial (`static/css/meridian/observatory.css`,
  `static/css/meridian/dial.css`, `static/js/meridian/dial.js`,
  `static/meridian-observatory-preview.html`).
- Slice 2 (commits `fc83417`, `c825358`): read-only data-driven dial API and view model
  (`meridian/services/dial.py`, `GET /api/meridian/dial`), Today partial wiring, evidence
  ticket, currency/minor-unit safety, and Observatory shell remapping for the Meridian
  main and Settings templates.
- Slice 3 (commit `27db882`): Observatory login/application-shell slice.
  - `templates/login.html` now uses the Meridian wordmark, indigo/paper palette, and the
    decorative engraving while preserving passkey/password controls, API calls, and error
    handling.
  - `static/css/meridian/observatory.css` adds `[data-meridian-shell] { background: transparent; }`
    so the body’s indigo radial atmosphere shows through the app shell.
- Slice 4 (commit `865c3dc`): read-only Plan scenario preview.
  - New authenticated `POST /api/meridian/plan/scenario` calls the existing pure
    `meridian.scenarios.run_scenario` service. It returns `read_only: true`, validates
    numeric inputs, and does not update the repository.
  - Plan UI adds an Observatory-styled “Scenario preview” card with before/after projection
    rows and an explicit “Preview — no changes applied” note. No apply/approval control is
    wired yet.
- Slice 5 (commit `d258aa4`): Accounts connection freshness.
  - The Accounts connection rail now consumes the backend’s computed `data_freshness` instead
    of inferring freshness only from per-connection health, adding an explicit partial state.
- Slice 6 (commit `397d835`): Settings Payday & Funding workspace.
  - The existing payday partial and proposal-only controller are now reachable from Settings.
  - Added readable Meridian/Observatory styling for the payday summary, editor, and preview.
  - The only payday write path remains the existing funding-rule proposal endpoint.
- Slice 7 (commit `622c705`): Accounts-to-Activity filtered navigation.
  - Account rows now expose an “Activity” action that switches to the Activity workspace in
    timeline mode and applies that account filter through `MeridianActivity.openAccount`.
- Slice 8 (commit `c6614cc`): Activity pattern comparisons.
  - Pattern cards now include human-readable detail lines for recurring cadence, category
    shifts, merchant trends, and cash-flow changes, while preserving clickable evidence rows.
- Slice 9 (commit `5550425`): Settings action history.
  - Added `ActionStore.list_recent` and `GET /api/meridian/actions`.
  - Added a read-only Settings “Actions & approvals” section listing proposed, approved,
    executing, executed, verified, rejected, expired, and failed states. No approve/execute
    controls are duplicated in this slice.
- Slice 10 (commit `fcdcea2`): Today dial hierarchy.
  - Moved the read-only Observatory dial into the primary Today column, directly under the
    command header, so it is no longer below the fold on mobile.
- Slice 11 (commit `c1d627f`): Today compact safe-to-spend strip.
  - The safe-to-spend label/figure now appears as a quiet strip above the dial, matching the
    reference hierarchy rather than a large forecast card leading the page.
- Slice 12 (commit `a6a9eea`): Settings Security & Data.
  - Added a read-only Security & Data section listing passkey metadata and explicit
    safeguards. It never renders credential IDs, tokens, or secret material.
- Slice 13 (commit `6b63abd`): Accounts decorative constellation.
  - Added the same restrained map ornament to the Accounts command header without encoding
    account relationships or amounts.
- Slice 14 (commit `e1e0606`): Accessible Add Connection overlay.
  - The connection chooser now traps Tab/Shift+Tab focus in addition to Escape and focus
    restoration.
- Slice 15 (commit `ad06c50`): Transaction source stamp.
  - The transaction detail sheet now shows a quiet “Source observation” line using the
    existing freshness timestamp, keeping dated source and balance distinct.
- Dial concept-focus pass (commits `c81d776` through `1c04dba`):
  - Solid parchment instrument face, engraved rim/rivets, dark sky disk, starfield,
    observatory engraving, golden star-centered pointer, and compact real-data center.
  - Day labels around the instrument, upcoming-money event orbit cards with kind icons,
    “Days to payday →”, “Turn to explore your week”, and “Explore my plan” CTA.
  - Fixed dial selection so clicking an event or marker updates the center and evidence ticket.
  - Dial now defaults to the first upcoming money moment, so the instrument is populated on load.
  - Added orbit leader lines, kind-colored markers, and a stronger observatory/lunar engraving.
  - Added engraved ticket corners to the selected-event evidence ticket.
  - Added full-width desktop Today staging so the dial/event rail is concept-scale rather than compressed beside Virgil.
  - Added Today command hierarchy: Today title, truthful orbit subtitle, and a real Crew observation stamp.
  - Added deterministic paper/ink WEBP textures to the decorative asset set.
   - Added a readable orbit bridge between desktop event cards and the dial, while hiding
     decorative connectors on mobile where the rail stacks below the instrument.

  - Added `tests/browser/test_observatory_dial.py`: Playwright verifies event selection updates
    the center/ticket, no non-GET request occurs during selection, and 390px has no horizontal
    overflow. Local run: 2 passed against the source preview.
- Verified in this session:
  - `tests/meridian` — 520 passed, including the formerly date-sensitive dial fixture with a
    frozen clock and explicit `build_dial(..., now=...)` value.
  - `tests/meridian/test_dial_js.py tests/meridian/services/test_dial.py` — 26 passed.
  - `APP_URL=http://127.0.0.1:8081 pytest tests/browser/test_observatory_dial.py -q` — 2 passed.
  - `ruff check app.py crew meridian tests` — clean.
  - Full non-browser baseline — 651 passed, 1 skipped, 1 pre-existing isolated failure in
    `tests/test_app_evidence_integration.py::test_evidence_content_resolves` (unrelated to
    Observatory; the test’s `app` fixture is not authenticated/configured in this run).
- Safety: no live financial mutation was executed or added in these slices. The dial and
  plan-scenario endpoints are read-only, scenario apply is intentionally not wired, and the
  payday/action-history surfaces are proposal-only or read-only.
- Next action: continue Observatory visual parity with activity detail sheet polish, Accounts
  constellation/detail, Settings security & data, Virgil/action-approval controls, accessible
  overlay/keyboard/safe-area/reduced-motion checks, then browser visual compares against
  `design/observatory-drafts-2026-09-08/`.

## Current blockers

- **Daily instance from source, not the tested digest:** the running preview on
  port 8081 is `run_preview_local.sh`; the Docker port-8080 slot is occupied by a
  pre-existing deployment from another project directory. "Deployed==tested" is
  met for the compose target only. (Autopilot schema drift was resolved 2026-09-06
  in WorkAssistant `a96f2d5` — snapshot now `complete: true, errors: {}`, sync
  `status=complete`.)
- TokenX routing unavailable: sub-agent spawning is blocked in this session, so parallel execution must occur in a verified Codex CLI environment or run sequentially in the parent.
- AI providers: owner's OpenAI key has no credits (429); OpenRouter free-tier quota tight
- Verification workflow: Playwright screenshot harness against isolated instance gates all UI changes

## Codex CLI handoff

A corrected handoff document has been created at `docs/project/CODEX_CLI_HANDOFF.md` containing:
- All project document references
- Current repository state
- Git evidence that Tasks 13–25 are implemented
- Task 26 scope and file locations
- Parallel agent lanes with disjoint write scopes
- TDD workflow requirements
- Model routing strategy
- Safety rules and commit conventions
- Final automated and owner-only acceptance gates

## Next action

- Task 26 and R30/R31 are complete in `feat/meridian-implementation`; the branch is pushed to
  `dirdir207-png/ORSC`. No merge to `main` (separate build by design).
- R32 acceptance recorded (see PRIVATE_RELEASE_ACCEPTANCE.md). Not yet a fully
  green formal release while the two gaps above stand; local daily use is safe.
- Remaining owner-gated tracks: R32 autopilot schema fix (WorkAssistant), R33/R34
  connected billers (depend on R32, partner-gated), and the R25 credential source.

Remaining gate (desktop / owner): reconcile the autopilot query in WorkAssistant and
optionally move the daily-use instance onto the tested Docker digest, then re-run
the §5 live acceptance to clear the two non-green items.

## Immutable observation foundation — 2026-09-10 (approved slice)

- Added additive migration `019_immutable_observations.sql` and credential-free `ObservationRepository`.
- Provider snapshots are appended as immutable actual observations with deterministic payload hashes, snapshot identity, source/update timestamps, freshness, confidence, and assumptions.
- Replays of the same observed snapshot are idempotent; partial and empty snapshots remain explicitly labeled.
- Added authenticated read-only `GET /api/meridian/observations`, exposing metadata only and never raw observation payloads.
- Verification: 542 `tests/meridian` tests passed; targeted Ruff and `git diff --check` passed. No financial mutation was added or executed.
- Added reproducible actual snapshot loading and a strictly read-only `SimulationInput` boundary; simulation inputs must reference an actual snapshot and are labeled `simulated`.
- Added authenticated read-only snapshot and simulation-preview endpoints; no actual repository or financial state is changed.
- Verification for this continuation: targeted observation tests passed; no financial mutation was added or executed.
- Next action: review and commit this bounded digital-twin continuation.

## Trial Canceler / Meridian Sentinel foundation — 2026-09-10 (committed)

A separate additive foundation was implemented and committed in this ORSC lane; it is documented in
`docs/project/TRIAL_CANCELER_HANDOFF.md` and is **not yet shipped or wired
to a UI, scheduler, browser extension, mail/transaction intake, or live Crew card
flow**. It adds `meridian/trials.py`, `meridian/cancellation/`, migrations 016–017,
and authenticated `/api/meridian/trials*` / cancellation-action routes. The state
machine requires positive billing evidence before `Billing stopped`; no merchant action
or financial mutation was executed. `tests/meridian` passed 520 tests after the change.
Parallel Observatory dirty/untracked files were not altered by this work.

## Whole-project safety continuation — 2026-09-10

- Revisited the governing product spec, implementation plan, consolidated handoff, release acceptance,
  current status, and Trial Canceler handoff; reconciled the latter's stale uncommitted label.
  Historical unchecked plan boxes are not treated as current
  status; the consolidated handoff's concrete findings drive follow-up work.
- Hardened the durable action pipeline so an approved action older than the configured 3600-second TTL
  is atomically marked `expired` during execution claim, closing the pending-list/execute race. Invalid
  approval timestamps fail closed. Added regression coverage.
- Fixed a real 390px Accounts overflow caused by the account list sheet's intrinsic min-content width;
  responsive and capability-parity browser coverage now pass (8 tests).
- Verification: full suite `730 passed, 64 skipped`; `tests/meridian` 520 passed; action-store tests
  11 passed; memory contract tests 5 passed; sync reserve regression 5 passed. Observatory browser tests
  require the running preview (`APP_URL`) and were previously verified separately. A fresh browser-suite
  attempt is unavailable in this environment because `.venv311` lacks optional `pytest-playwright`;
  this is an environment gate, not an application failure. The evidence integration expectation was
  reconciled with
  the intentionally safe HTML evidence viewer.
- Hardened the approval cleanup sweep to compare legacy naive and newer timezone-aware approval
  timestamps safely; added regression coverage for aware timestamps.
- Hardened the authenticated mutation endpoint to reject malformed JSON shapes before routing; added
  HTTP regression coverage for non-object bodies, params, and missing action types. Routing now also
  fails closed for a missing/non-string action type before provenance-specific branching.
- Docker Compose configuration validates successfully (`docker compose config -q`); the tested digest
  is still not deployed to the daily-use instance, so release remains owner-gated.
- Corrected provider synchronization to treat an explicit zero reserve as authoritative instead of
  retaining the prior local reserve; omitted reserves still preserve existing observations.


## Read-only constitution evaluator — 2026-09-10

- Added `meridian/policy.py` with typed `Constitution`, `ActionPlan`, and structured `PolicyDecision` models.
- Evaluation fails closed while inactive, reports rules/evidence/assumptions/confidence/recovery, and never approves or executes actions.
- Automatic actions without bounded limits are blocked; otherwise results remain `requires_approval`.
- Verification: `tests/meridian` passed 548 tests; Ruff and `git diff --check` passed. No policy activation or financial mutation occurred.
- Commits: `7a6c985` (implementation) and `23c03ae` (status/ledger documentation).

## Capture-contract harness — 2026-09-10

- Added pure capture metadata validation in `tests/browser/capture_contract.py` for the governed four viewport/DPR pairs, light/dark themes, and required deterministic fields.
- Added four contract tests covering the complete 8-state matrix, missing metadata, mismatched DPR/theme, and JSON-safe serialization.
- Documented harness usage in `docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md`. This changes no product behavior and does not regenerate visual baselines.
- Verification: capture-contract tests passed; Ruff and `git diff --check` passed.

## Capture-matrix runner — 2026-09-10

- Added `scripts/capture_meridian_matrix.py` to execute the full governed viewport/theme/DPR matrix and emit a validated metadata manifest.
- The runner explicitly configures reduced motion and theme, waits for network/fonts/data settlement, disables animations/transitions, and requires the fixture and frozen clock to be named.
- Existing approved baselines were not regenerated; no product behavior or financial data was changed.

## Deterministic capture-runner hardening — 2026-09-10

- The matrix runner now freezes browser `Date`, disables interval polling before application scripts load, and captures both initial viewport and full-page artifacts.
- Capture targets are restricted to isolated loopback previews, and workspace metadata maps to the governing Observatory concept filenames.
- Approved visual baselines were not regenerated; no product or financial behavior changed.

## Four-workspace invariant restored — 2026-09-10

- Removed Trials as a fifth primary workspace from `navigation.html`, `shell.js`, and `MERIDIAN_WORKSPACES` in `app.py`, restoring the governing four‑workspace invariant.
- Moved Trials into the **Settings** surface as a new `section=trials` entry, matching the precedent of Payday & Funding and Actions & Approvals.
- Repaired `index.html` structural corruption from commit `5ea003d`: removed the spliced Trials `<section>` and restored the Accounts workspace's `data-workspace-section="accounts"` element.
- Added `trials` to the Settings sections list in `app.py` and wired the partial + `trials.js` include into `settings.html`.
- The Trials capability (API, `trials.py`, `cancellation/` logic, deadline ledger) remains fully reachable at `/api/meridian/trials*` and via `/meridian/settings?section=trials`; no API surface or safety semantics changed.
- Verification: 13 checks pass in `tests/test_meridian_workspace_invariant.py`, including rendered-DOM parsing that proves the four workspace sections parse with intact attributes and no leaked tag syntax; 566 tests passed; Ruff and `git diff --check` clean.
- Negative control: reintroducing the corrupted markup fails 7 of those checks, confirming the guard has teeth.
- Commits: `dbdca2f` (code and regression tests), `7c4efab` (status record).

## Proactive financial weather slice — 2026-09-10

- Added `meridian/proactive.py`: a pure, read-only projection that groups near-term Observatory dial events and classifies a financial-weather `state` (`steady` / `tight` / `strained` / `unknown`).
- Noise control: each group is capped at three events and reports an `omitted` count; zero, duplicate, and unparseable events are suppressed and counted rather than rendered.
- Freshness behaviour fails closed: when dial freshness is not `fresh`, or the available balance is missing, the state is `unknown` at confidence 0.2 with the reason recorded as an assumption. Missing data is never treated as zero, and amounts are never added across currencies.
- Every state and group carries a plain-language explanation, and each event explains its own funding meaning.
- Exposed via read-only `GET /api/meridian/weather` (login required, `@_safe_read`), reusing `build_dial` so the dial stays the single source of dates and amounts. No UI, mutation, or authority change.
- Verification: `tests/meridian` 563 passed (12 new proactive unit tests plus API cases for auth, shape, invalid `as_of`, and zero repository writes on read); full suite 793 passed, 56 skipped, with the pre-existing `tests/test_capture_contract.py` environment gate unchanged; Ruff and `git diff --check` clean.
- Commit: `768c7e4`.

## Bill funding target respects an existing reserve — 2026-09-10

- Fixed D01 from the consolidated handoff. `meridian/funding.py::_commitment_target` returned a bill's full amount and ignored its reserve, so a bill with `amount=120.00` and `funded_amount=100.00` projected 120.00 more instead of 20.00 — over-allocating by 100.00 through `project_funding` (used by Plan and Payday).
- Bills now use the same remaining-target rule goals already used: `max(0, target - funded_amount)`, so a fully reserved bill projects nothing and an over-reserved bill can never produce a negative target or shortfall.
- `services/plan.py` keeps its separate full-target `_commitment_target` (it subtracts `funded_amount` itself) and is intentionally unchanged.
- Verification: RED->GREEN — three new tests in `tests/meridian/test_funding.py` fail against the previous behaviour and pass with the fix; `tests/meridian` 566 passed; Ruff and `git diff --check` clean.
- Commit: `44bf73b`.

## Honest Plan action-outcome rendering — 2026-09-10

- Closed A07 from the consolidated handoff. Plan previously treated every successful HTTP response as successful execution, hard-coded `data-state="ok"`, and could display `Executed (failed).` or `Deleted (failed).`.
- Added pure `static/js/meridian/action-outcome.js`; all four Plan mutation call sites now interpret the returned durable action state. `verified` is the only successful terminal outcome; `executed` / `executing` stay visibly pending verification; `failed`, `rejected`, `expired`, unknown, and uncertain outcomes fail closed with recovery guidance and no blind-resend copy.
- Destructive views refresh only after `verified`, never merely because the route was direct or HTTP returned 200. Uncertain failures preserve server detail and instruct the owner to read Crew state before trying again.
- Added the existing caution-token tone for pending action notes; no new visual component or design authority was introduced. No preview was running on port 8081, so this slice makes no browser-capture claim.
- Verification: RED->GREEN — three new tests failed before the helper/integration/style existed; Node exercises every durable state and source guards reject the old false-success copy; `tests/meridian` 569 passed; Node syntax, Ruff, and `git diff --check` clean.
- Commit: `57ba383`.

## Memory retains failed and uncertain action outcomes — 2026-09-10

- Closed A09 from the consolidated handoff. Memory management previously treated every HTTP-200 execute response as success: it wrote `executed`, removed the proposal row, hid the pending container, and refreshed Accounts without inspecting the durable action state.
- The execute response body now passes through the shared action-outcome interpreter. Only `verified` removes the row and refreshes memory. Failed, uncertain, rejected, expired, executing, executed, and malformed outcomes remain visible with honest recovery copy.
- The Execute control is disabled after a durable outcome, so failure/uncertainty cannot become a blind resend path; recovery routes through Actions & Approvals and Crew-state readback.
- Verification: RED->GREEN — three focused tests failed against the old behavior; focused source/integration coverage 11 passed; `tests/meridian` 572 passed; Node syntax, Ruff, and `git diff --check` clean.
- Commit: `72b6bc0`.

## Exact recorded action review details — 2026-09-10

- Implemented the recorded-detail half of A10 across the Settings history, Memory approvals, and the legacy account approval panel. Every surface now displays all stored operation parameters, including exact amounts, sources, destinations, memos, and nested fields.
- Added shared `action-review.js`: values are rendered with `textContent` only; secret-shaped keys are recursively replaced with `[redacted]`; no action data is inserted through `innerHTML`.
- Review truth fails closed. If a durable action does not contain reviewed before/after or preserved-field evidence, the surface says **not recorded** rather than inferring it from the rationale or requested parameters.
- Scope boundary: this does **not** close A12. Fresh base-state capture, source-version/precondition checks, conflict detection, and true before/after comparison remain separate work.
- Verification: RED->GREEN — four contract tests failed before implementation; focused action-history/memory/browser-source coverage 15 passed; `tests/meridian` 576 passed; isolated preview browser shell/smoke 18 passed; Node syntax, Ruff, and `git diff --check` clean. The temporary preview was stopped afterward.
- Commit: `f27f553`.

## Structured Crew write outcomes — 2026-09-10

- Closed the structured-outcome portion of A04. Crew connector failures no longer collapse into a generic executor exception: `blocked`, `rejected`, and `uncertain` classifications plus their sanitized messages now survive into the durable action result.
- Timeouts, unreadable connector responses, and connector-reported uncertainty are explicitly stored with `verify_state=true` and `retry_allowed=false`. The executor is invoked exactly once, no verifier runs after a failed result, and the owner-facing recovery path remains Crew-state readback before any new request.
- Scope boundary: this does not implement automated reconciliation, operation-specific provider readback, typed action input schemas, or A12 stale-base preconditions. No action authority, mutation registry, retry policy, or UI route changed.
- Verification: RED→GREEN focused connector/pipeline tests; 34 focused action/outcome tests passed; `tests/meridian` 581 passed; full suite 811 passed, 64 skipped; Ruff and `git diff --check` clean. Browser-only tests were collected but skipped without `APP_URL`; no UI changed. Independent read-only review reported no findings.

## Meridian identity on auth and first-run surfaces — 2026-09-10

Owner-reported symptom: the landing page and the installed Home Screen app showed
"SimpleCrew" again. Diagnosis found three separate causes, only one of which was in
ORSC's control:

1. **Port 8080 is not this build.** `docker ps` shows container `simplecrew`, image
   `simplecrewbranch-finance-app`, compose working directory
   `/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`, created 2026-09-06. Its
   `/login` is titled `SimpleCrew - Login`. Opening `localhost:8080` shows that other
   product, not ORSC Meridian. Stopping it is owner action outside this repository.
2. **`/login` renders `register.html` whenever the users table is empty**, so
   `register.html` *is* the first-run landing page. Commit `27db882` gave the Observatory
   treatment only to `login.html` and `index.html`, so every fresh database still landed on
   the untouched `SimpleCrew - Setup` page. This was an incomplete branding sweep, not a
   revert of earlier work.
3. **A stale cache kept the old name installed.** `static/sw.js` answered
   `/manifest.json` from a cache-first branch under an unchanged cache name
   (`simple-finance-v12`), so an installed app kept the previous product name even after
   the file was corrected.

Changes: `register.html` now uses the same approved Observatory treatment already applied
to `login.html` (identical `obs-shell`, obs tokens, card/field/button classes) with Meridian
copy; the `login.html` footer, `base.html`, and `onboarding.html` no longer carry another
product name; `static/manifest.json` is named Meridian with the Observatory background and
theme colors; `sw.js` now treats `/manifest.json` as network-first, bumps `CACHE_NAME` to
`simple-finance-v13` so existing installs drop the stale manifest, and uses Meridian push
defaults. Every register/login form id, name, autocomplete, placeholder, endpoint, payload,
and error path is preserved.

Verification: RED→GREEN — 13 guards in `tests/meridian/test_auth_branding.py` failed first
(wrong manifest name, SimpleCrew on all four templates, cache-first manifest) and pass now.
Rendered through the real first-run path with an empty database, `/login` returns
`Meridian - Setup`, `apple-mobile-web-app-title: Meridian`, **zero** `SimpleCrew` occurrences,
and `manifest.json` name `Meridian`. Full suite 826 passed, 64 skipped; Ruff,
`git diff --check`, `node --check static/sw.js`, and manifest JSON validation all clean.

Owner-visible remains:
- The running preview on port 8081 (`run_preview.py:46`, `debug=False, use_reloader=False`)
  caches Jinja templates in-process, so it will keep serving the old page until it is
  restarted. This is why the symptom persisted across previous fixes.
- An already-saved iOS Home Screen icon keeps its cached name; remove and re-add it once to
  pick up the new manifest.
- `static/js/app.js` console log strings still say SimpleCrew. They are developer-console
  text with no user-visible surface and are deliberately left out of this slice.

## Accepted is not verified for verifier-less operations — 2026-09-10

Finding A05 from the consolidated handoff: `crew/executors.py` substituted `{"ok": True}`
whenever an executor registered no verifier, so a provider acceptance was recorded as
`verified`. An audit of the live registry shows the scale of the overstatement —
**15 of 27 registered action types have no verifier at all**, including
`crew_initiate_transfer`, `top_up_crew_reserve`, `set_crew_spend_pocket`,
`create_crew_pocket`, both pocket-reassignment rules, the three paycheck-funding-plan
operations, `create_crew_virtual_card`, and the bill/pocket/rule create and archive
operations.

Change: a successful execution with no registered verifier now stays in `executed`
(verification pending) and records why, inside the durable result payload:

```
"verification": {"ok": null, "check": "no-verifier-registered", "reason": "..."}
```

Only a readback verifier may move an action to `verified`. The explicit-verifier path is
unchanged, a failing verifier still lands in `failed`, and a verifier that raises still
lands in `failed` with `verifier_exception`. `executed` remains non-claimable, so the
existing single-claim guarantee still prevents a second execution of the same action; a
regression test now pins that.

No authority, routing, retry, or mutation behaviour changed, and no new state or schema was
introduced — `executed` already existed and already rendered honestly. The UI needed no
change: `static/js/meridian/action-outcome.js` has treated `executed` as
"sent, verification pending, do not resubmit" since OS-007, and the memory/asset/contract
flows are unaffected because all six of those operations do register real verifiers.

Scope boundary: this makes the recorded outcome honest. It does **not** implement the
readback service that would later confirm these operations (handoff A15) or operation-specific
provider readback (A06), so a verifier-less action now stays `executed` until such a service
exists. That is the truthful state rather than a silent success.

Review consequence fixed in the same slice: `archive_crew_bill` is verifier-less, and its Plan
Delete control relied on `outcome.refresh` to reload the list and drop the archived row. With
that refresh now unreachable, the row would have stayed listed behind a live Delete button that
creates a **second** archive request. The bill-archive control now disables itself after a
durable outcome, exactly as the rule-delete control already did. A new guard test asserts that
every destructive Plan control refuses a second request, and a negative control (removing the
guard) makes it fail. This closes a widened resend path rather than shipping it as a side
effect of the truth fix.

Verification: RED→GREEN — 3 new executor tests plus 1 pipeline test failed before the change;
the one pre-existing expectation that a verifier-less `create_crew_pocket` reached `verified`
was corrected to `executed`. Full suite 832 passed, 64 skipped; Ruff, `git diff --check`, and
`node --check static/js/meridian/plan.js` clean.

Known follow-ups found by review, deliberately not in this slice: the recorded
`no-verifier-registered` reason is stored but not yet rendered in the Approvals history; and
`meridian/crew_write_actions.py::_verify_stored` still derives its result from local commitment
state, so the two `update_crew_bill*` types are not true provider readbacks either (handoff A06).

## Absent provider accounts are reconciled, not left frozen — 2026-09-11

Finding C02 from the consolidated handoff, with C04's rule applied: Meridian only
ever upserted the accounts a provider returned, so an account the provider stopped
returning kept `is_active = 1` and a frozen `source_updated_at` forever. Because
freshness is the oldest in-scope account observation, that single orphan pinned the
whole workspace to `stale` indefinitely while transactions stayed current. This was
not hypothetical: the owner's database holds one such row (a pocket Crew no longer
returns, last observed four days before its neighbours).

Change — reconciliation, deliberately **not** a weaker freshness rule:

- `absent_since` (migration 020) records the moment a complete read concluded an
  account is gone. The row keeps its history; it only stops being a current observation.
- `sync_provider` reconciles only when `snapshot.is_complete and errors == 0`, so a
  partial or errored read never concludes a deletion, and the scope is the reading
  provider's **own connection**, so another provider's accounts are never archived.
- `mark_absent_accounts` marks a row absent once (`absent_since` is set only where it
  is still null), so one observation cannot masquerade as a repeatedly refreshed fact.
- An account the provider returns again is reactivated and its absence evidence cleared.
- The freshness join no longer counts a concluded-absent account — in either direction:
  it can no longer pin the workspace stale, and it can no longer rescue it. A connection
  whose every account was archived therefore reports `stale`, and an unreconciled frozen
  account still pins `stale` exactly as before.
- `_reclassify_relations` no longer indexes the active-account map directly: an absent
  account keeps its row, so its historical transactions are still classified in the
  account context they were recorded under instead of aborting the sync.
- Account reads select only the columns the database actually has, mirroring the
  existing transaction-column tolerance, so a reader meeting a database that has not
  yet applied migration 020 does not fail.

No authority changed: this writes no provider state, adds no routing, retry, or mutation
path, and never deletes or restores anything. The owner's deleted pocket is **not**
recreated — its row is archived locally and its 19 historical transactions remain.

Verification: RED→GREEN — 12 tests in `tests/meridian/test_sync_reconciliation.py`
(the in-flight draft could not even collect: it had no `repository` fixture, and its
absence logic did not exist), plus 1 migration test that pins both account-column
tolerance branches on a database stopped before 020. Seven mutation checks confirm the
tests are load-bearing: removing the reconciliation call, the freshness exclusion, the
reactivation reset, the once-only guard, the completeness gate, the unmigrated-database
column filter, or the conditional absence reset each fails the tests that pin it. Full
suite 845 passed, 56 skipped, with the one pre-existing `playwright`-unavailable capture
test failing identically with this change stashed. Ruff clean on changed paths (the 7
reported findings are pre-existing, in `scripts/` and `tmp/pdfs/`), `git diff --check` clean.

Verified end to end on a **copy** of the owner's database with a live, complete,
read-only Crew snapshot (`complete: true`, `errors: 0`): Crew returned 6 accounts, one
local pocket was absent from that read, that pocket was archived with `absent_since`
while its 19 transactions stayed linked, no other account changed, and workspace
freshness moved `stale` → `fresh`. The real database was not modified and no
credential, token, or payload was logged.

Owner-visible consequence, and the next slice: `list_accounts` lists only current
accounts, so an archived account now correctly leaves the Accounts workspace and stops
counting in cash math. That is honest, but a silent disappearance is exactly the
experience the owner reported as data loss, so the archived row must be shown as
archived with its provenance rather than vanishing (OS-014).

Known follow-ups found while reviewing this slice, deliberately not fixed here:
`app.py::sync_crew_to_meridian` logs `report.accounts_upserted`, `report.transactions_upserted`
and `report.error`, none of which exist on `SyncReport`; the resulting `AttributeError` is
caught and printed as a sync failure even though the sync itself succeeded, so that path's
log is untrue. Absence reconciliation is implemented for accounts only — Crew bills and
other collections (C02's other half), C03's delete-reload, and C05's null-versus-empty
semantics are untouched.

## An archived account is reported, not silently dropped — 2026-09-11

OS-013 archived accounts a complete provider read concluded are gone, but
`list_accounts` returns only current accounts, so the owner's deleted pocket simply
left the Accounts workspace. That is correct for cash math — a withdrawn observation
must not count as current money — but a silent disappearance is the same experience
the owner reported as data loss. This slice makes the archived row visible with
provenance and, deliberately, without a current balance.

Change:

- `repository.list_archived_accounts(limit=50)` returns archived rows newest
  conclusion first, each paired with how many of its transactions survive. A
  database that has not applied migration 020 cannot have archived anything, so it
  reports none rather than failing on the new column.
- `build_accounts` reports an `archived` list (name, provider, account type,
  `absent_since`, `last_observed_at`, `retained_transactions`) **and no amount**: the
  last known figure is history, not a current balance. The list is bounded.
- `templates/meridian/partials/accounts.html` gains a "No longer returned" section
  that ships collapsed and empty, reusing the existing workspace section pattern
  (`section` + `h2` + `aria-labelledby`). It adds no interactive control at all.
- `static/js/meridian/archived-accounts.js` is a new pure module whose labels are
  executed by tests: `describeArchivedAccount` (provider no longer returns this
  account · last observed date · concluded absent date · N transactions kept in
  Activity) and `describeTransactionAccount` (the ledger label, marked when the
  account is archived).
- Activity now labels the account a transaction belongs to, in both the ledger and
  the Review card, and marks the ones whose account the provider no longer returns.
  This also removes a dead `transaction.accountName` reference that expected a field
  the API never sent. The API resolves `account_name` and `account_archived` from the
  account rows, including archived ones, so historical rows keep their account context.

No authority changed: nothing here mutates provider state, adds a control, or
introduces an approval/execution path. The archived row offers no action because there
is nothing the owner could safely change from it.

Verification: RED→GREEN — 11 tests in `tests/meridian/test_archived_accounts.py`
(6 of the 9 first-run tests failed on the missing read model, then the ordering test
was rewritten until a mutation could break it) plus 4 API/rendered-page tests in
`tests/meridian/test_api.py`. Mutation checks confirm the guards are load-bearing:
ordering by row id instead of conclusion time, rendering a balance in an archived row,
and dropping the ledger's account label each fail a test. Full suite 860 passed,
56 skipped, with the same pre-existing `playwright`-unavailable capture failure.
Ruff clean on changed paths, `git diff --check` clean, `node --check` clean on all
three touched modules.

Verified end to end on a **copy** of the owner's database with a live, complete,
read-only Crew snapshot: 6 accounts reported as current, 1 reported as archived with
`absent_since`, `last_observed_at` and **19 retained transactions**, no amount
exposed for it, its Activity label marked archived, and 0 current rows wrongly marked
archived. The real database was not modified; no credential, token, or payload was
logged, and the temporary copies were deleted.

Not verified here, and recorded rather than claimed: the browser/viewport pass for this
surface. `playwright` is unavailable in this environment, so `tests/browser/*` (including
`test_accounts.py`) skips and the pre-existing capture-contract test fails for the same
reason. The section reuses existing workspace markup and adds no interactive control, and
every label carries its meaning in text rather than by colour alone, but a real
viewport/contrast pass still has to run where the browser tooling exists.

Known follow-ups, deliberately not in this slice: an archived account's rows offer no
"view its history in Activity" control, because the Activity account filter is populated
from current accounts only and a filter entry for a non-current account would be
inconsistent; `transaction.accountName` was removed rather than aliased, so the ledger
sub-line now reads from the API's `account_name`; and absent-account reconciliation still
covers accounts only (Crew bills and other collections remain open under C02).

## The preview outage, its cause, and its repair — 2026-09-11

The preview app served 503 on every financial endpoint (Today, dial, Accounts,
memory) while `/api/actions/pending` kept returning 200. The log named the cause
exactly:

    meridian refresh failed: RuntimeError: Applied migration 020 has a name or checksum mismatch

`020_account_absence_reconciliation.sql` was edited *after* an earlier revision of it
had already been applied to the preview database `/private/tmp/gate-preview/gate.db`.
`meridian/db.py` keeps migration history append-only and refuses to run when an applied
migration's name or checksum no longer matches the file, so every `run_migrations`
call raised and every repository read failed. The guard did its job; the verification
that preceded the edit was wrong — it confirmed only that `savings_data.db` was still
at 019 and never checked the preview database, which is the one the running app uses.

Repair: `gate.db` was backed up to `gate.db.pre-020-checksum-repair`, then the recorded
checksum for 020 was reconciled to the current file **after confirming the schema effect
was identical** (`absent_since` present, `idx_financial_accounts_absent` present — the
two revisions differed only in comment text). Verified by readback: `run_migrations`
returns `[]` without raising, repository reads work, and the refresh log shows
`meridian refresh provider=crew status=complete accounts=6 transactions=100 errors=0`
with no further checksum errors. No other database carries 020 (`savings_data.db` is at
019; the 2026-08-30 production backup is unaffected).

Lesson, now a rule: **a migration file is immutable from the moment any database may
have applied it — including throwaway preview and `/tmp` databases.** Ship a new
migration instead of editing a shipped one, and when a shipped file does change, check
every database the app can reach before assuming the change is free.

Still outstanding because it needs a restart, not a code change: the preview process
started 2026-09-10 13:08 and therefore runs the code as it was before commits `9486820`,
`eef9ce0` and `0030ae9`. Until it restarts, absent-account reconciliation never runs, so
the orphan row keeps Today at `stale` pinned to 2026-09-07, and the Accounts "No longer
returned" section is not served (Jinja has the previous template cached).

Follow-up finding: the 503 body reads "Try again after your provider reconnects", which
misattributes a schema/migration failure to the provider. The message should distinguish
"we could not read your data" from "your provider is unavailable".

## A12 — an approved Crew write is refused when the reviewed state changed — 2026-09-11

The write-integrity gap from the handoff: an approved action carried only its
requested parameters, never the state the reviewer actually saw, and execution
claimed the action before comparing anything. A bill edited between approval and
execution — by another surface, an agent, or the sync cadence — would still receive
the approved write.

This slice makes the guard real for one operation, `update_crew_bill`:

- `action_requests` gains `base_state_json` (nullable, self-migrating); `propose`
  accepts a `base_state` captured by the proposal path from the same local record the
  reviewer's screen was rendered from (name and amount only, never a fabricated whole).
- `ExecutorSpec` gains an optional `precondition`, evaluated after the atomic claim and
  **before any provider call**. A mismatch refuses the action as `precondition_conflict`;
  a missing or unreadable reviewed state refuses as `precondition_unverifiable` (fail
  closed). The recorded outcome says `sent_to_provider: false`, `retry_allowed: false`,
  and `provider_truth: false` — it compares our own record, not a provider readback.
- Because `FAILED` is terminal, a refusal can never be retried or silently re-run.
- Wired to `update_crew_bill` only; the other 21 action types are untouched.

Non-goals, stated explicitly: this does **not** provide provider truth (A06 remains
open); it did **not** add a new action state (a refusal is a `failed` action with a
distinct error code); and it did not change the Plan UI, which already proposes with
the Crew bill id.

Verified RED→GREEN: 7 engine tests plus 4 wired-operation tests; neutralising the guard
turns 5 of them red (including "a changed bill is refused and never reaches Crew").
Full suite 875 passed, 56 skipped, with the same pre-existing playwright-unavailable
capture failure; Ruff and `git diff --check` clean.

## C06 — one canonical Crew connector — 2026-09-11

Handoff C06: two Crew adapters represented the same provider over the same account
id space under two connection identities. `CrewReadAdapter` (GraphQL client) wrote
connection `current-user`; `CrewWorkSnapshotAdapter` (read-only `crew-readonly` CLI)
wrote `crew-work-assistant`. If both ever ran, accounts would migrate connections and
the emptied connection would hold the whole workspace `stale`.

Decision (owner authorized): the canonical connector is the read-only CrewWorkAssistant
snapshot under `crew-work-assistant`. It is the only path that has ever produced data in
either database, and a read-only CLI fits the observe-never-mutate boundary better than a
bearer-token GraphQL client.

Change: `app.py::sync_crew_snapshot` now delegates to `meridian.live.sync_live_crew`, so
the cadence gate, the legacy `/api/savings` refresh, and the live loop all write the one
identity. The `CrewReadAdapter` and `sync_provider` module imports were removed from
`app.py` (`sync_provider` remains the sync engine inside `meridian/sync`, still used by
the snapshot adapter). `CrewReadAdapter` the class and `crew_client` the GraphQL client
are left in place — `crew_client` still serves the legacy savings read, the health check,
and session renewal; deleting them is a separate cleanup.

Verified: the routing test now asserts the legacy path calls `sync_live_crew` on the app's
DB, so a revert to the client adapter fails; the two tests that patched the removed
`sync_provider` name were repointed to the live seam. Full suite 875 passed, 56 skipped,
same pre-existing playwright-unavailable failure; Ruff and `git diff --check` clean.

## A06 — a Crew bill write is now verified against the provider, not local state — 2026-09-11

The verify leg of propose→approve→execute→verify was hollow for Crew bill writes:
`_verify_stored` re-read the *local* commitment and explicitly never failed an accepted
Crew write over local state, so "verification" could not actually verify anything.

`update_crew_bill` now verifies against a fresh Crew snapshot (`capture_crew_snapshot` →
`CrewWorkSnapshotAdapter`) and compares the requested `name` and `amount` (normalizing
cents↔dollars) against what Crew now reports:

- matched → `VERIFIED` (`provider_truth: true`);
- mismatch, or the bill is gone → `FAILED` (`verification_failed`, with `requested` and
  `observed` recorded, `provider_truth: true`);
- snapshot unreadable → stays `EXECUTED` (`verification pending`, `provider_truth: false`)
  — never VERIFIED, never FAILED, because Crew already accepted the write.

Engine: `execute_approved_action` now treats a verifier's `ok is None` as "verification
pending" via the new `ActionStore.record_verification_pending` (an in-place result note
with no state change), instead of `bool(None) → False → failed`. This generalises the
OS-012 no-verifier-registered honesty to "a readback ran but could not confirm."

Composes with A12: A12 refuses a write whose reviewed state changed *before* it runs;
A06 confirms the provider state *after* it lands. Scope is `update_crew_bill` only; every
other verifier is unchanged. A `FAILED` verification is terminal — no automatic retry.

Verified RED→GREEN: 1 engine test plus 3 wired tests (matched/mismatch/unreadable);
neutralising the `ok is None` branch turns 2 red, including "cannot be read stays
executed". Full suite 879 passed, 56 skipped, same pre-existing playwright-unavailable
failure; Ruff and `git diff --check` clean.

## C02 for bills — a complete Crew read now concludes absence for bills it stops returning — 2026-09-11

OS-013 reconciled accounts; bills were left unreconciled, so a Crew bill that disappeared
stayed a live obligation locally forever. This mirrors the account rule onto commitments.

Migration 021 adds `commitments.absent_since`. `CommitmentRepository.mark_absent_bills`
archives (and timestamps) this provider's bills that a complete read no longer returns,
scoped by `legacy_source` so another provider's commitments are never touched. The row,
its funded amount and its transactions are kept — absence is evidence about the local read
model, not a deletion.

Deliberate deviations from the account rule, both conservative:

- **An empty enumeration never concludes absence.** Unlike accounts (where an empty
  observed set archives everything in scope), a read that listed no bills at all is
  treated as an unreadable surface rather than "every bill disappeared".
- **The bill is archived, not left active.** Accounts carry `is_active`; commitments carry
  a lifecycle `status`, so absence sets `status='archived'` and `absent_since` together.
  `absent_since` is what distinguishes provider absence from the owner's own archive.

Re-observing a bill clears its absence and restores it to `active`, but only for rows that
were concluded absent — an owner-archived bill is never silently revived. Both upsert paths
are wired (`sync_live_crew` and `sync_providers`), gated on a complete, error-free read.

Verified RED→GREEN: 9 tests (repository scoping, idempotence, no-provider-identity,
reactivation, owner-archive protection, plus two end-to-end sync tests through the real
adapter); neutralising the completeness gate turns the incomplete-read test red. Full suite
888 passed, 56 skipped, same pre-existing playwright-unavailable failure; Ruff and
`git diff --check` clean. `tests/meridian/test_migrations.py` gained 021 in its expected
migration lists.

Companion slice still open: Plan-surface provenance for an absent bill (the OS-014 parallel),
so the owner can see *why* a bill they remember vanished instead of it silently leaving Plan.

## A bill the provider stops returning now stays visible in Plan — 2026-09-11

The OS-014 parallel for bills. OS-018 archives a bill a complete read no longer returns,
which meant it left Plan silently — re-creating, for bills, the exact experience the owner
reported as data loss. The read model now reports it with provenance instead.

- `CommitmentRepository.list_absent_bills(limit=50)` returns concluded-absent bills, newest
  conclusion first, bounded to 1..200 like the archived-account list.
- `build_plan` exposes `absent_bills` as `{id, name, provider, absent_since}` — deliberately
  **no amount and no funded figure**, because a last known figure is not a current obligation.
- `static/js/meridian/absent-bills.js` holds the label logic as pure functions
  (`describeAbsentBill`), so it is executed in tests rather than only asserted as text.
- `plan.js` renders a "No longer returned" section into `[data-absent-bill-list]`; the section
  is `hidden` until something is actually reported, so it cannot read as a permanent fixture,
  and the row carries no amount and no control.
- `templates/meridian/partials/plan.html` gains the section, mirroring the Accounts wording.

No backend latency cost: unlike the A06 readback verifier, this reads local rows only.

Verified: 10 Python tests (repository ordering/bounds, service payload, live-vs-absent
separation, template presence, renderer shape) plus one API-level test through the
authenticated test client, plus one Node test executing the label logic. Mutation check:
dropping the absence filter turns 2 red. Full suite 898 passed, 56 skipped, same pre-existing
playwright-unavailable failure; Ruff, `git diff --check`, `node --check plan.js` and a Jinja
parse of the partial are all clean.

**Verification gap, stated plainly:** no browser, viewport, contrast or accessibility check was
possible — `playwright` is not installed in this environment, so all 56 browser tests skip. The
section is verified at the payload, label and markup level only; it has not been seen rendered.

## C01 — an unreported reserve is no longer read as a zero reserve — 2026-09-11

`_cents_to_dollars` returned `0.0` for a missing field, so a bill whose `reservedAmount` Crew
never reported was indistinguishable from a bill whose reserve had been explicitly emptied.
Because `commitments.funded_amount` is `NOT NULL`, that conflated zero was then written on
every read — **erasing the amount Meridian last knew**. Same family of silent loss as the
deleted pocket, arriving through a different door.

Fix: a nullable `_cents_to_dollars_or_none`, used only for `reservedAmount`, so an absent field
stays `None`. Both upsert paths already handled `None` correctly (`else existing.funded_amount`
on update, `0.0` on create) and were simply never handed a `None` — so this one-line change
activates intent that was already written, rather than adding new behaviour.

Deliberately not changed: `amount` keeps the non-nullable helper. An absent `amount` still reads
as `0.0`, which local validation rejects *loudly* (bills require a positive amount) instead of
silently — and that loud failure aborts the whole refresh tick for one malformed bill. Recorded
as a follow-up rather than folded into this slice.

Also flagged, not fixed: `update_bill_reserve_settings` passes its payload straight to the
crew-write CLI and its parameter contract is **not documented** (only `TopUpReserve` is
catalogued), so I did not invent a fail-closed guard keyed on a guessed field name. The endpoint
has no UI caller today, so the risk is latent — but a guard must exist before any UI derives a
reserve value from local state.

Verified: 4 new tests (2 targeting the fix, 2 regression guards proving an explicit zero still
clears and a new bill still starts at zero) plus the existing provider tests; reverting the fix
turns the 2 target tests red. Full suite 902 passed, 56 skipped, same pre-existing
playwright-unavailable failure; Ruff and `git diff --check` clean.
