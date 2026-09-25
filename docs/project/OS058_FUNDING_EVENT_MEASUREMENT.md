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
