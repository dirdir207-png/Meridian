-- 025: Persist Crew's OWN reported funding schedule, not just Meridian's projection of it.
--
-- Why this migration exists. OS-056 (D-015) had Meridian MIRROR Crew's published rule:
-- bill.estimatedNextFundingAmount = ceil(amount * interval_days / 30.4375). That is a
-- projection -- Meridian applying Crew's arithmetic to data Meridian already stored -- and
-- it is labelled exactly that way. But the provider states the same three facts itself, in
-- the same read Meridian already performs, and Meridian was discarding them at the mapping
-- boundary:
--
--   * per bill   estimatedNextFundingAmount -- Crew's own per-event figure for that bill
--   * per bill   reservedBy                 -- Crew's own deadline for the reservation
--   * per reserve nextFundingDate           -- Crew's own next funding event
--   * per reserve estimatedNextFundingAmount -- Crew's own reserve-level figure
--
-- The live query already selects all four (app.py, the `expenses` facet), so this is an
-- ingestion gap, not a connector gap.
--
-- Why it is worth storing. Two reasons, and the second is the point of the slice.
--
-- (1) Provenance. A provider-reported figure is an OBSERVATION and outranks Meridian's
-- application of the provider's rule (D-013's order of authority). Until these columns
-- existed, the app could only ever say "Meridian computed this from Crew's rule"; with them
-- it can say "Crew reported this", which is the stronger and citable statement.
--
-- (2) The divergence test. With BOTH figures stored, the computed value and the reported
-- value can be compared on real data. That comparison is the best correctness evidence
-- available for the mirrored rule, and it is the only way to notice that Crew's arithmetic
-- has changed under us. Neither figure is derived from the other, and neither is written
-- into the other's column.
--
-- WHAT IS DELIBERATELY NOT CLAIMED. The reserve-level estimatedNextFundingAmount ($1,435.97
-- in the 2026-09-19 read) is still UNEXPLAINED: it is not the sum of the per-bill estimates,
-- not the plan amount, and not a per-bill figure scaled. It is stored as an observation with
-- its own provenance so the 2026-10-02 funding event can be measured against what Crew
-- predicted, and it is excluded from every arithmetic path -- it must never be used to
-- derive totalReservedAmount, which is itself an observed sum (OS-055). Storing a number is
-- not explaining it.
--
-- ABSENCE DISCIPLINE (C01 and 024, unchanged). All four columns are NULLABLE, so NULL means
-- "this read did not report it" -- never "zero", and never "Crew says there is nothing".
-- A read that omits a field must never clear a value Meridian already knew; the write paths
-- pass the stored value through in that case, exactly as they do for funded_amount and
-- bill_reserve_id. No backfill is attempted: nothing in the pre-025 schema can distinguish a
-- reported zero from silence for these fields, so guessing one here would manufacture
-- provenance the provider never gave.
--
-- Amounts are dollars (Crew reports cents; the adapter converts at the provider boundary),
-- and the dates are the provider's own ISO strings, stored verbatim rather than parsed, so a
-- malformed value stays visible as malformed instead of silently becoming NULL.
ALTER TABLE commitments ADD COLUMN estimated_next_funding_amount REAL;

ALTER TABLE commitments ADD COLUMN reserved_by TEXT;

ALTER TABLE crew_bill_reserves ADD COLUMN estimated_next_funding_amount REAL;

ALTER TABLE crew_bill_reserves ADD COLUMN next_funding_date TEXT;
