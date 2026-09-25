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
