-- 031: keep DATED observations of each bill's reserved amount -- the reserve's internal allocation.
--
-- WHY (OS-114, owner-authorised 2026-09-25). The owner's own correction is the premise: *"Reserve is one
-- bucket, so I'm not sure it's possible, but you may be referring to its internal bill allocation."*
-- He is right that it is one bucket, and the arithmetic makes the case stronger rather than weaker. In
-- the owner's 2026-09-04 capture the five per-bill `reservedAmount` values sum to the bucket's own
-- `totalReservedAmount` EXACTLY (71098 = 71098 cents, difference 0) and only ONE distinct
-- totalReservedAmount exists, so the per-bill figure IS the bucket's internal allocation.
--
-- Why it needs its OWN table: `commitments.funded_amount` already holds that number and
-- `reserved_amount_reported` the flag that says whether Crew stated it (C01, migration 024). Both are
-- single values OVERWRITTEN on every sync, so the same number that answers "how is the bucket
-- allocated right now" destroys the answer to "how did it get that way". Concretely: the capture shows
-- Rent holding the entire $710.98 on 2026-09-04 while the other four held $0.00, the reserve read
-- $1,097.10 on 2026-09-20, and $0.00 on 2026-09-25 -- and nothing on our side can say whether the
-- bucket moved because a bill was paid or because a sync dropped a value. This table is that history.
--
-- WHY IT MATTERS RATHER THAN DECORATES: the allocation is lumpy, not proportional. One bill holds the
-- whole bucket at a time, so the history is what makes the rotation visible, and OS-058's open question
-- ("which bill is credited, and by what rule") is answerable only against a series of these rows.
--
-- THE C01 RULE, ENCODED. `reserved_amount` is NULL exactly when Crew did not state one, and
-- `reserved_amount_reported` records that it was silent, so a missing figure can never be read as
-- $0.00. That is deliberately DIFFERENT from the spend-selection table (030), where an unobserved facet
-- writes no row at all: there the whole read is absent, whereas here the BILL was observed and only its
-- amount was silent -- the same distinction `commitments` already draws.
CREATE TABLE crew_bill_allocation_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    connection_external_id TEXT NOT NULL,
    -- Crew's own bill id, the same value `commitments.legacy_id` holds, so history joins by identity
    -- rather than by a name the owner renames.
    bill_external_id TEXT NOT NULL,
    -- The name AS OBSERVED. Evidence, not a key: it is what lets a row still be read after a rename.
    bill_name TEXT,
    observed_at TEXT NOT NULL,
    reserved_amount REAL,
    reserved_amount_reported INTEGER NOT NULL CHECK (reserved_amount_reported IN (0, 1)),
    estimated_next_funding_amount REAL,
    reserved_by TEXT,
    bill_reserve_id TEXT,
    data_mode TEXT NOT NULL DEFAULT 'actual' CHECK (data_mode IN ('actual', 'simulated')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- A reported amount IS the amount, and an unreported one is never a zero.
    CHECK ((reserved_amount_reported = 1) = (reserved_amount IS NOT NULL))
);

-- One observation per bill per capture: re-ingesting the same capture cannot manufacture a second,
-- competing history entry. The capture time is the identity, exactly as in migration 030.
CREATE UNIQUE INDEX idx_crew_bill_allocation_per_capture
    ON crew_bill_allocation_observations(provider, bill_external_id, observed_at);

-- The read path asks "the history of this bill, newest first" and "every bill's allocation in this
-- capture" (which is what the parts-sum-to-the-whole check needs).
CREATE INDEX idx_crew_bill_allocation_history
    ON crew_bill_allocation_observations(bill_external_id, provider, observed_at DESC, id DESC);
