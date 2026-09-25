# OS-058 — measuring the 2026-10-02 funding event

**Purpose.** The owner's funding model is described in D-015; what is *not* settled is which bill Crew
credits with holding the reserve and by what rule, whether the event behaves as the ordering predicts,
and when the reserve-level account-total field refreshes. This file is the measurement record, kept
apart from the interpretation: the numbers below were **copied**, never derived.

**Bounds (from the task itself, restated so a future reader cannot widen them).** Measurement, not
modelling. Read-only from a COPY of the preview database, never the live file. No provider mutation, no
transfer, no live-sync write, no automatic retry. `totalReservedAmount` is never derived from anything
and the reserve-level estimate is never treated as a dividend (D-015). A bill at `0.00` is NOT a
shortfall while EARLY FUNDING is 0. Nothing about Crew or Meridian state may be adjusted to make a
hypothesis fit, and a number that does not reconcile is reported as open rather than smoothed.

## BEFORE state — 2026-09-25T18:38:30Z

Taken while the event was still future, as the task requires, from a **consistent** copy
(SQLite backup API, not `cp`: the preview syncs every 15 seconds and a file copy can tear).

| item | value |
|---|---|
| copy | `artifacts/os058-funding-event-2026-09-25/gate-before-20260925T183830Z.db` (untracked) |
| record | `before-20260925T183830Z.json` (same directory) |
| schema / last complete sync | 030 / 2026-09-25T18:38:09Z |
| `crew_bill_reserves.total_reserved_amount` | **0.0** |
| `crew_bill_reserves.next_funding_date` | **2026-10-02** |
| `crew_bill_reserves.estimated_next_funding_amount` | 1435.97 (account-total, lagged — NOT a reserve figure) |
| Σ non-fallback account balances | 16.69 |

Per-bill `funded_amount`, with the date each is reserved for:

| bill | funded | reserved_by | bill amount |
|---|---|---|---|
| Eversource | 0.00 | **2026-09-30** | 210.00 |
| Xfinity | 0.00 | **2026-09-30** | 93.00 |
| Rent | 0.00 | 2026-10-16 | 1442.00 |
| Verizon Payment Arrangement | 0.00 | 2026-10-16 | 75.20 |
| Verizon | 0.00 | 2026-10-22 | 101.57 |

Two `Test` commitments also exist (`legacy_source='crew'`, no `reserved_by`, amount 0.01) and are
carried in the record but treated as non-bills: they hold nothing and no funding date.

## The prediction, recorded BEFORE the event so it can be falsified

A measurement that only describes what happened afterwards is a story. This is what the D-015 ordering
predicts, written down while it is still a prediction:

1. **2026-09-30 — an intermediate event.** Eversource and Xfinity are reserved *before* the 10-02
   funding, so their allocations should appear first. If the reserve genuinely holds nothing until it
   is swept, `total_reserved_amount` should still be 0 on 09-30 while these two bills become non-zero.
2. **2026-10-02 — the funding event.** `next_funding_date` is that day, so either the reserve total or
   the per-bill allocations should move. Per D-015 the paycheck lands in Checking, the reserve is
   funded from Checking alone, and a sweep to the reserve happens only if Checking exceeded 1800.
3. **The account-total field.** `estimated_next_funding_amount` (1435.97 now) is lagged; after the
   event it should refresh, and at that moment it should equal that moment's account total. Whether it
   refreshes *on* 10-02 or later is exactly what point (3) of the task asks.
4. **Attribution.** Rent held the whole 1097.10 in the 2026-09-20 read while its own per-event need was
   663.27, and the other four held 0.00 — so the reserve is NOT an accumulation of bill allocations
   (one event's five allocations would sum to 883.96, and two events would exceed 1097.10). If Rent is
   credited again with the whole amount, the rule is "one bill is credited", not "each bill holds its
   own share"; if the credit rotates or splits, say so and leave the rule open rather than inventing
   one from a single sample.

## A LABELLED simulation of the event lives elsewhere, on purpose

`OS058_EVENT_SIMULATION_2026-10-02.md` pre-registers what each surviving candidate rule predicts, with
the arithmetic, so the observation below can score them. It is deliberately a **separate document**: this
file must contain only what was observed, and the task's own limits forbid substituting a model for the
measurement. Do not quote the simulation as a result, and never present a simulated value as a balance.

## Procedure (repeatable, so the measurement does not depend on one session's memory)

Run `.venv/bin/python tmp/os058_before_snapshot.py` again — it takes a *new* dated copy and record
without touching the previous ones, so the series accumulates:

* on/after **2026-09-30**, for the intermediate event;
* on/after **2026-10-02**, for the funding event itself.

Then compare per-bill `funded_amount` deltas against each bill's `reserved_by`, and compare the
reserve-level figures against the account balances in the same record. The numbers are already stored
by the 15-second refresh, so no new tooling and no code change is needed — and **no value may be
derived** to fill a gap in the series.

---

## Owner-authorized manual-capacity experiment — 2026-09-25T21:06:07Z

This is deliberately separate from the scheduled-event measurement above. The owner explicitly
authorized real, internal Bill Reserve top-ups to settle the allocation order now; these are provider
mutations, not a simulation or a passive observation. Each top-up had one submission, a complete,
error-free before read, and a fresh complete settling read. No uncertain result was retried.

Starting at a $0.00 reserve, five ordered top-ups ($1.00, $75.20, $101.57, $93.00, and $210.00) left a
final reserve total of **$480.77**. The settled provider fields were:

| allocation order | bill | bill amount | settled `reservedAmount` |
|---:|---|---:|---:|
| 1 | Verizon Payment Arrangement | $75.20 | $75.20 |
| 2 | Verizon | $101.57 | $101.57 |
| 3 | Xfinity | $93.00 | $93.00 |
| 4 | Eversource | $210.00 | $210.00 |
| 5 | Rent | $1,442.00 | $1.00 |

The parts equal the whole exactly: 48077 cents of per-bill `reservedAmount` equals the 48077-cent
`totalReservedAmount`. This establishes two observable behaviours for this exact state: Crew caps a
bill at its stated amount, then cascades excess to the next bill; and the complete current order is the
five rows above. The first two bills were 9 and 3 days overdue. The next two shared the earliest
non-overdue `reservedBy` date, with Xfinity before Eversource; Rent followed. That is consistent with
`daysOverdue DESC`, then `reservedBy ASC`, plus a deterministic tie-breaker, but the tie-breaker's
implementation is not inferred from this experiment alone. The 2026-09-04 non-overdue Rent allocation
also means overdue status is a priority when present, not a necessary condition for allocation.

One operational observation is now mandatory for future measurements: the immediate post-write read can
transiently show every bill non-zero while the reserve total is much smaller. Each subsequent complete
read reconciled exactly. Treat the settling read, not the immediate read, as the observation.

---

## Owner-authorized same-deadline tie-break experiment — 2026-09-25T21:19:10Z

The capacity cascade left Xfinity before Eversource when both reported `reservedBy=2026-09-30`, but one
pair alone could have reflected creation order. The owner therefore authorized temporary same-date bills.
A $2 bill created before a $5 bill was fully funded before Eversource, but that first pair was
creation-order-confounded. The decisive reverse pair created a **$300** bill first and a **$200** bill
second, both with the same 2026-09-30 anchor. Before the second creation the $300 bill held $211.00.
After the second creation, the complete settling read reported the later-created $200 bill at **$200.00**
and the earlier-created $300 bill at **$0.00**; the 48077-cent per-bill sum still equalled the 48077-cent
reserve total.

This establishes the observed current ordering as: higher `daysOverdue` first; then earlier
`reservedBy`; then lower bill amount for an otherwise equal deadline. It does not establish Crew's source
implementation or every possible further tie-breaker, but it refutes creation order as the amount-tie
rule. The temporary `Allocation Probe*` bills are live Crew records and intentionally remain visible for
the owner to revise or remove with the planned bill overhaul; no deletion was silently performed.

---

## Additional read-only checks — 2026-09-25T21:33Z

The same complete Crew snapshot carried one biweekly funding plan (`WEEKLY`, interval 2) and eleven
bills. Crew's reported `estimatedNextFundingAmount` matched the 14-day proration formula for **11/11**
bills, including every temporary probe. This validates the per-event estimate path, not the reserve
balance: estimates remain projections and are not added to `totalReservedAmount`.

The parent physical debit card and four virtual cards all reported the same selected spend-subaccount
identity. The spend-pocket selection therefore agrees across all five observed card surfaces in this
read.

Autopilot exposed two rules: `Sweep Excess Checking Funds` is active and unbroken, triggered by
`ACCOUNT_BALANCE_UPDATED`, with the description "Removes funds over 1800 in the checking pocket";
`Round Ups` is unpaused but marked broken. The Bill Reserve's funding subaccount was present. The
snapshot did not expose an account-level balance in the pockets facet, so the reserve-level estimate
versus account-total reconciliation remains unresolved and is not inferred here.

---

## Retrospective, 2026-09-25 — what the held artifacts already settle (item 1 of the agreed order)

Run before the 10-02 event, from artifacts already held: the 2026-09-04 capture (bills facet, which
carries Crew's own `reservedAmount`, `reservedBy`, `daysOverdue`, `dayOfMonth`, `status` per bill), the
2026-09-19 record in `CREW_FUNDING_MATH_2026-09-19.md`, and a live capture at 2026-09-25T19:42Z.

**Three dates, side by side:**

| date | bucket | credited bill | that bill's `reservedBy` | `daysOverdue` across bills |
|---|---|---|---|---|
| 2026-09-04 | 71098¢ ($710.98) | **Rent** (all of it) | 2026-09-16 (tied soonest with VPA) | `None` for every bill |
| 2026-09-19 | 109710¢ ($1,097.10) | **Rent** (all of it) | 2026-09-16 — **3 days past** | Rent 3, others not |
| 2026-09-25 | 0¢ | none (bucket empty) | — | VPA 9, Verizon 3, others none |

**1. Crew's `bills` array is a SORT, not a fixed list — and the key is now proven.** Order matches
`(daysOverdue desc, reservedBy asc)` on BOTH dates, exactly: on 09-04 every bill was un-overdue, so the
order is pure `reservedBy` ascending (Rent 09-16, VPA 09-16, Eversource 09-20, Verizon 09-22, Xfinity
09-28); on 09-25 the two overdue bills lead (VPA 9, Verizon 3) and the rest follow by `reservedBy`
(Eversource 09-30, Xfinity 09-30, Rent 10-16). Consequence: "Rent is first in the array" was never a
fact about Rent, it was a fact about Rent's *deadline* — which is why it changed when the deadlines did.

**2. "The credit goes to the overdue bill" is REFUTED.** On 2026-09-04 no bill was overdue — the capture's
`daysOverdue` is `None` for all five, and that field is demonstrably populated when a bill IS overdue
(it reads VPA 9 and Verizon 3 on 09-25, from the same facet) — yet the bucket was non-zero and credited
entirely to Rent. So the credit does not require an overdue bill.

**3. A CORRECTION to `CREW_FUNDING_MATH_2026-09-19.md`.** That document refuted nearest-due-first with
"Rent (due 2026-10-16) holds everything while Eversource and Xfinity (due 2026-09-30, sooner) hold
nothing". But 10-16 was Rent's due date having already rolled forward, while Crew's own `reservedBy` for
Rent at that read was **2026-09-16 — already 3 days past**, i.e. SOONER than Eversource/Xfinity's
09-30. Stated in terms of the field Crew actually uses, the rule survives instead of being refuted:

> **The credited bill is the one with the soonest `reservedBy`** — the next reservation whose deadline is
> nearest, whether or not it has passed.

It fits all three dates: 09-04 Rent (09-16, tied with VPA, larger bill wins or array order decides),
09-19 Rent (09-16, past), and 09-25 nothing to credit (bucket empty). The original refutation compared
the wrong field: a due date that had rotated, not the deadline Crew funds against.

**4. The prediction this yields for the 10-02 measurement, sharpened.** Today the soonest `reservedBy`
belongs to **Eversource and Xfinity (both 2026-09-30, Eversource first in array order)** — so if the rule
above holds, the next non-zero credit goes to ONE of those two, and **Rent being credited again would
refute it**. "Credit the largest bill" predicts Rent, so the two readings are freshly distinguishable —
whereas before this retrospective they could not be told apart at all.

**5. Left OPEN, per the task's bounds (no smoothing):**
* The `reservedBy` of Eversource and Xfinity was `2026-09-20` and `2026-09-28` on 09-04 but `2026-09-30`
  for both on 09-25. Either the field rolls, or their day-of-month changed, or the 09-19 document
  conflated `dayOfMonth` with `reservedBy`. The artifacts do not settle it.
* No transaction in the stored set mentions Rent (0 rows match), and the 08-12..08-22 window contains no
  Rent-sized outflow — so the reserve going 1097.10 → 0 between 09-20 and 09-25 is *consistent with*
  Rent's occurrence being settled (its `reservedBy` rolled forward to 10-16), but the money movement is
  not visible in synced transactions. Whether the reserve paid it, or it was swept elsewhere, is open.

---

## Independent verification of the experiment records, and what is still open (2026-09-25, Meridian lane)

The two experiment sections above landed in this repository from the parallel lane. Their claims were
checked against the **live database**, not accepted from the write-up, and the results are recorded here
so the record is verified rather than merely asserted.

**Verified, claim by claim.** Every temporary bill exists with the stated amount and settled allocation:
`Allocation Probe $200 Second` 200.00 funded / `$300 First` 0.00, `Small` 2.00, `Small Second` 1.00,
`Large First` 3.00, `Large` 5.00. `crew_bill_reserves.total_reserved_amount` is 480.77 and the reported
per-bill amounts sum to **480.77 exactly**, so parts still equal the whole. The real bills read Verizon
101.57, VPA 75.20, Xfinity 93.00, Eversource 0.00, Rent 0.00.

**A critique of mine, withdrawn on the evidence.** I first objected that the reversed pair could not
distinguish "lower amount wins" from "fund whatever the available cash covers", since 480.77 − 280.77 =
200.00 exactly. The record defeats that objection: the `$300` bill **held 211.00 before the second bill
existed** and lost it to the later, lower `$200` bill. Funds were therefore not the binding constraint,
and the tie-break conclusion stands on the reallocation, not on a funding opportunity. Creation order is
refuted as the tie rule.

**Still open, and NOT resolved by either experiment.** The rule "lower amount wins an otherwise equal
deadline" **contradicts the 2026-09-04 capture**, where Rent (1442.00) and VPA (75.20) shared
`reservedBy=2026-09-16` and the entire 710.98 sat on **Rent**, the larger. The likeliest reconciliation is
that a single read is a *mid-cascade* state — VPA having already been settled and released — rather than a
tie outcome at all. That is a hypothesis, not a finding, and the dated history built in OS-114 item 2 is
what would settle it: a series shows whether a bill's share is *released* after it is paid.

**Two facts that must travel with any figure from this window.**

1. **The 480.77 is artificial and the owner does not hold it** (owner, verbatim: *"No, I do not have that
   amount, it's artificial"*). It was injected by the authorised experiment, so today's Today figure
   (−469.38) and any history rows written now reflect injected money, not the owner's position.
2. **The shape is ordinary even though this instance is artificial** (owner, verbatim: *"It still lets you
   top up to reserve regardless"*, *"It's like a preordained negative and backfill"*): a negative funding
   account mirroring a positive reserve is designed behaviour awaiting the next income. Recorded as
   **D-027** so it is never again diagnosed as a defect.

**Operational consequence the owner should decide on before 2026-09-30.** Eversource carries a real
210.00 obligation due 09-30 and currently holds **0.00**, having been displaced by probe bills that hold
211.00 of the same bucket between them. Two paths, and the choice is his because both are provider
mutations: unwind the experiment before the 09-30/10-02 window (remove the probe bills and the injected
reserve) so OS-058 measures a clean reserve, or keep them and accept that the 10-02 measurement describes
a polluted state in which part of the owner's real paycheck will backfill an injected amount.

**Deployment held for the same reason:** the OS-114 ingest fix is committed but the live sync bridge has
NOT been restarted, so no artificial allocation has entered the history as `data_mode='actual'`.

---

## The VPA test — the one criterion that settles the tie-break question, and both lanes now agree on it

The parallel lane answered the open contradiction directly, and its correction is accepted here:

> *"That is the correct correction. … 'lower amount wins' is not a universal Crew rule. It may describe
> only a settled capacity cascade. Your mid-cascade hypothesis is plausible: VPA may have already been
> funded and released before that capture, leaving Rent holding the current reserve."*

**The criterion, stated so a future reader can apply it mechanically:** the OS-114 history settles this
if and only if it carries **consecutive observations around the transition** — specifically, whether VPA
**ever held an amount and then released it** while Rent stayed funded. If VPA reads zero in **every**
dated observation, the amount tie-break does not describe the natural state and is falsified for it.

**Why the history as built can meet it.** One row is written per bill per capture, and the live bridge
syncs roughly every 15 seconds, so a hold-then-release transition necessarily produces consecutive rows
rather than a single overwritten value — which is precisely what the old mutable column could never show.
The relevant distinction is already expressible: `reserved_amount = 0.00` with
`reserved_amount_reported = 1` is a **release** (Crew stating zero), while `NULL` with the flag false is
**silence** (Crew not saying). Only the first tests the hypothesis, and conflating them would answer the
question with the wrong fact.

**What that test is waiting on — the only thing blocking it.** Recording is deliberately held while the
live reserve contains the **injected** 480.77 and the probe bills: evaluating "did VPA hold and release"
against a state where artificial money and six probe bills compete for the same bucket would answer a
different question. Both lanes reached the same operational conclusion independently, so it is recorded
once here:

> **Unwind the experiment before 2026-09-30, or label the 10-02 measurement as CONTAMINATED.**

That is an owner decision, because both paths are provider mutations. Nothing else is outstanding from
this lane's side: the ingest fix is committed and waiting, the evidence is verified and committed, and the
retrospective, history, and simulation are delivered.

---

## PRE-UNWIND record — 2026-09-25, before the owner removes the injected top-ups

The owner's plan: *"remove the manual top ups (by deleting and recreating income source, thats the only
way)"*, then report back. Deleting and recreating the income source changes **its id** and, critically,
**its anchor date** — and the anchor is what makes the next funding 2026-10-02. So the state is recorded
FIRST, verbatim, so the unwind can be proved rather than assumed.

| what | value before the unwind |
|---|---|
| reserve id | `QmlsbFJlc2VydmU6OGQyZjNlOGYtZDI0MS00MDY3LWI4OGUtMGQ1NDRlNzc4MDc5` |
| `totalReservedAmount` | 48077 cents ($480.77) — the INJECTED amount, which the owner does not hold |
| `nextFundingDate` | **2026-10-02** |
| `estimatedNextFundingAmount` | 167148 cents ($1,671.48) — a projection, never added to the reserve |
| income source id | `RnVuZGluZ1BsYW46ZmY2YjQyMDctNmVhZS00ODEwLTg1YzUtM2FlMTNkM2QxYmZk` |
| income source | 1663.00, `biweekly`, **anchor 2026-09-04** → 09-18 → **10-02** |

**What must be verified AFTER, and why each one matters:**

1. **`nextFundingDate` is still 2026-10-02** (or the new date is recorded and OS-058's window moves with
   it). A recreated income source that anchors on the day of recreation would push the next funding to
   **2026-10-09** and silently move the measurement window out from under the pre-registered simulation.
2. **The reserve reads 0.00 and every probe reads 0.00**, so the bucket holds no injected money and the
   probe bills stop competing for it.
3. **The new income-source id, cadence, amount and anchor are recorded.** A delete-and-recreate is a
   DELIBERATE discontinuity: our records will show the old plan absent and a new one appearing. Writing
   that down is what stops it later being read as a provider anomaly or a data loss.

**Two facts to carry into the unwind, neither caused by it:**

* Every `Allocation Probe*` bill carries `reservedBy 2026-09-30` — the SAME deadline as Eversource. Under
  the behaviour the experiment measured (equal deadline → lower amount first), the probes of 2.00, 3.00,
  5.00 and 200.00 all outrank a real 210.00 bill. Keeping them for the bill overhaul and giving them a
  later deadline stops them competing with a real obligation.
* Eversource's 210.00 falls due **2026-09-30**, while income lands **2026-10-02**, with roughly 11.39 on
  hand. On Crew's own numbers that obligation has no funding source inside the reserve before it is due.
  This is arithmetic stated for the owner, not advice — and it is the kind of thing Meridian exists to
  surface rather than discover late.
