-- 024: Persist the observed reserve state the per-bill reserved amount needs.
--
-- Why this migration exists: D-013 (owner, 2026-09-19) permits a per-dated-occurrence
-- reserved figure and fixes its order of authority -- a provider-reported per-bill
-- figure is an observation and outranks any Meridian derivation -- with an even
-- allocation of the reserve's total set-aside funds across the commitments in that
-- reserve as the permitted fallback. Two observed facts are needed for that, and
-- neither was stored.
--
-- (1) The dividend. Crew's billReserve.totalReservedAmount is the reserve's total
-- set-aside funds ("Bill reserve is a single bucket", D-013). The connector already
-- read it (readback_reserve_totals, and the preview's own expenses summary) but nothing
-- persisted it, so no stored read could divide by it. The only reserve-scoped number
-- that WAS stored is the funding plan's own amount (022), which is the plan's
-- per-cadence funding amount, not the bucket balance: dividing that across bills would
-- invent a figure. crew_bill_reserves keeps the observed total with its provenance.
--
-- (2) The per-bill statement. commitments.funded_amount is Crew's per-bill
-- reservedAmount (C01), and it is REAL NOT NULL DEFAULT 0 (005), so a bill whose
-- reserve Crew never reported is stored as 0.0 -- exactly like a bill Crew reported as
-- emptied. reserved_amount_reported records which of those happened, so the dial can
-- state "not yet set aside" for a real zero and stay silent for missing data instead of
-- presenting absence as a fact. A read that does not report the field never clears the
-- flag, for the same reason C01 refuses to let a silent read erase what Meridian knew.
--
-- Absence follows the 020/021/022 precedent rather than deleting: a complete provider
-- read that no longer returns a reserve sets absent_since and the row keeps its history,
-- so a withdrawn reserve is distinguishable from an unobserved facet.
--
-- NULL total_reserved_amount means "not reported", never "no money set aside". Amounts
-- are dollars, matching the rest of Meridian; Crew reports cents and the adapter
-- converts at the provider boundary. Both tables key on the provider's own reserve id,
-- never on a name, because the owner renames these records in Crew.
CREATE TABLE crew_bill_reserves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    total_reserved_amount REAL CHECK (
        total_reserved_amount IS NULL OR total_reserved_amount >= 0
    ),
    currency TEXT NOT NULL DEFAULT 'USD',
    observed_at TEXT,
    synced_at TEXT NOT NULL,
    absent_since TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (provider, external_id)
);

-- Current reserves are what the dial resolves against; it filters on absent_since.
CREATE INDEX idx_crew_bill_reserves_current
    ON crew_bill_reserves(provider, absent_since);

-- The per-bill flag (see (2) above).
ALTER TABLE commitments ADD COLUMN reserved_amount_reported INTEGER NOT NULL DEFAULT 0;

-- The backfill is an implication, not a guess: absence writes 0.0, so a positive
-- funded_amount could only have come from something that stated it -- a Crew report, a
-- migrated legacy balance, or the owner's own figure. A stored 0.0 stays unreported,
-- because that is precisely the case C01 documents as indistinguishable.
UPDATE commitments SET reserved_amount_reported = 1 WHERE funded_amount > 0;
