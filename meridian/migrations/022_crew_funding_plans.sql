-- 022: Persist the Crew bill-reserve funding plans the sync observes.
--
-- Why this table exists: the owner's income source IS the Crew funding plan
-- ("CONFIRMED 2026-09-19 by the owner: Crew's income source IS the bill-reserve
-- funding plan"), and the owner directive is that the expected paycheck must
-- resolve to that Crew record rather than to a locally configured figure.
--
-- The read already existed: the connector selects
-- billReserve.fundingPlans { id name amount frequency frequencyInterval anchorDate }
-- and meridian/providers/crewwork.py readback_funding_plans() parsed it -- but only
-- to verify a write, and then discarded it. The snapshot is fetched fresh per sync
-- and is never cached on disk, so a plan that is not persisted during the sync is
-- gone until the next one. This table keeps it.
--
-- Absence follows the 020/021 precedent rather than deleting: a complete provider
-- read that no longer returns a plan sets absent_since and the row keeps its
-- history, so a withdrawal is distinguishable from an unobserved facet and a
-- re-observed plan is a fresh observation of the same record.
--
-- Amounts are dollars, matching the rest of Meridian; Crew reports cents and the
-- adapter converts at the provider boundary. cadence is the plan's schedule in
-- Meridian's five-cadence vocabulary, or NULL when Crew's
-- frequency/frequencyInterval cannot be expressed exactly -- NULL means "not
-- expressed", never "monthly".
CREATE TABLE crew_funding_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    bill_reserve_id TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    cadence TEXT,
    anchor_date TEXT,
    currency TEXT NOT NULL DEFAULT 'USD',
    observed_at TEXT,
    synced_at TEXT NOT NULL,
    absent_since TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (provider, external_id)
);

-- Current plans are read by the paycheck resolution, which filters on absent_since.
CREATE INDEX idx_crew_funding_plans_current
    ON crew_funding_plans(provider, absent_since);
