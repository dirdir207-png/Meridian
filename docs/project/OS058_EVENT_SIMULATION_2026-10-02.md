# SIMULATION — the 2026-10-02 funding event, pre-registered (NOT an observation)

> **This document is not evidence and not a balance.** Nothing in it was observed. It is a labelled
> simulation of what two candidate rules predict, written BEFORE the events so the measurement can score
> them. OS-058's answer must come from observation; its own limits say "measurement, not modelling", so
> this file is explicitly NOT that task's result and must never be quoted as one. No simulated value may
> be written into the database or shown as a balance.

## Why it exists

The 09-18 retrospective (in `OS058_FUNDING_EVENT_MEASUREMENT.md`) refuted "the credit goes to the overdue
bill" and corrected a refutation in `CREW_FUNDING_MATH_2026-09-19.md`, leaving one rule standing and one
competitor that the held artifacts cannot separate:

| | rule | predicts the next credit goes to |
|---|---|---|
| **A** | the bill with the soonest `reservedBy` (the next reservation deadline, passed or not) | **Eversource/Xfinity** (both 09-30) |
| **B** | the largest bill | **Rent** (1442.00) |

They agree on every observation we hold, because Rent was both the soonest-deadline bill and the largest
bill on 09-04 and 09-19. Today they diverge: the soonest `reservedBy` is Eversource/Xfinity (09-30) while
the largest bill is Rent. So the 09-30 and 10-02 events discriminate between them for the first time.

## Observed inputs (these ARE facts, dated)

| input | value | source |
|---|---|---|
| funding plan | **1663.00**, `biweekly`, anchored 2026-09-04 | `crew_funding_plans`, 09-25 |
| next funding date | **2026-10-02** | `crew_bill_reserves.next_funding_date` |
| bucket total, 09-25 | **0.00** (and 0.00 at both 09-30-preview reads) | `crew_bill_reserves` |
| bill amounts | Rent 1442.00 · Eversource 210.00 · Verizon 101.57 · Xfinity 93.00 · VPA 75.20 | `commitments.amount` |
| `reservedBy` | Eversource **09-30** · Xfinity **09-30** · Rent 10-16 · VPA 10-16 · Verizon 10-22 | live capture 19:42Z |
| per-event needs (Crew's own) | Rent 663.27 · Eversource 96.60 · VPA 46.72 · Xfinity 42.78 · Verizon 34.59 | funding-math doc, 09-19 |

## Scenario A — the soonest-`reservedBy` rule

If the bucket is filled to 1663.00 and spent on the nearest deadlines first, the split would be:

| bill | credited | arithmetic |
|---|---|---|
| Eversource | 210.00 | its full amount, deadline 09-30 |
| Xfinity | 93.00 | its full amount, deadline 09-30 |
| Rent | 1360.00 | the remainder, next deadline 10-16 |
| **bucket total** | **1663.00** | 210.00 + 93.00 + 1360.00 — the identity `parts == whole` must still hold |

**The signature A must leave, in order:** Eversource and/or Xfinity go non-zero **first** (at or before
09-30), and the bucket total equals the **sum** of the credited bills — not one bill's share.

## Scenario B — the largest-bill rule

| bill | credited | arithmetic |
|---|---|---|
| Rent | up to 1442.00 | the largest bill, credited before any other |
| others | 0.00 | unchanged |
| **bucket total** | 1442.00 (or Rent's share) | equals Rent's own `reservedAmount`, as on 09-04 and 09-19 |

**The signature B must leave:** on 09-30 **Eversource and Xfinity read 0.00** while the credit sits with
Rent, and the bucket total equals Rent's `reservedAmount` alone.

## How the measurement scores this, and what would falsify each

* **A falsified** if, once the bucket is non-zero, the credit is on a bill that is neither Eversource nor
  Xfinity while both remain 0.00 and their 09-30 deadline has passed.
* **B falsified** if Eversource or Xfinity carries a non-zero credit at a moment when Rent's is 0.00.
* **Both falsified** (a third rule we have not named) if the credit is spread over bills in a way neither
  table describes, or rotates between reads. That outcome is a real possibility and is to be reported as
  an open question, not smoothed into A or B.
* **Neither testable** if the bucket stays 0.00 through 10-02 — in which case the honest report is that
  the event did not happen as `next_funding_date` predicted, which is itself worth knowing.

## What this simulation deliberately does NOT do

It does not model Crew's algorithm, derive any quantity from another, treat the reserve-level estimate as
a dividend (D-015), or predict a balance the owner can spend. It predicts only **which observed field
moves first and what the numbers must add up to** — the smallest claim that can still be wrong.
