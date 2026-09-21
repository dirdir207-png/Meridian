-- 028: a bill reserve may legitimately be NEGATIVE. Remove the CHECK that said otherwise.
--
-- WHY THIS MIGRATION EXISTS. Migration 024 declared
--     total_reserved_amount REAL CHECK (total_reserved_amount IS NULL OR total_reserved_amount >= 0)
-- on the assumption that a reserve total is a quantity of money set aside and therefore
-- cannot be below zero. That assumption is WRONG, and it was not a theoretical one: it
-- failed in production. On 2026-09-21 the owner's sync began raising
--
--     sqlite3.IntegrityError: CHECK constraint failed:
--         total_reserved_amount IS NULL OR total_reserved_amount >= 0
--
-- from meridian/repository.py's reserve upsert, so the whole live read FAILED whenever the
-- reserve was negative -- no reserve row, no funding plan, no bills refreshed. The owner
-- confirmed the negative is real and expected: they deliberately left too much in Crew's
-- "free to spend", so when rent cleared today the reserve went below zero.
--
-- A reserve total is therefore NOT a quantity of money set aside; it is a running balance
-- between what was set aside and what has cleared against it, and a balance can be negative.
-- Meridian's job is to record and show that, not to refuse it: a schema that rejects a real
-- state does not prevent the state, it only prevents Meridian from knowing about it. The
-- alternative -- clamping to zero -- would be worse still, because it would present a
-- fabricated figure as a reported one (rule: never present simulations as real balances).
--
-- `NULL` KEEPS ITS MEANING. NULL still means "the read did not report a total", which is not
-- evidence that the bucket is empty, and that distinction is untouched here (C01). Only the
-- `>= 0` clause is removed.
--
-- WHY A TABLE REBUILD. SQLite cannot drop or alter a CHECK constraint in place, so the table
-- is recreated with an identical definition minus that clause, its rows copied verbatim, and
-- the index recreated. No value is transformed: this migration only stops the schema from
-- refusing a value it was already being handed.
--
-- The runner wraps each migration in BEGIN IMMEDIATE and executes the statements in order, so
-- the drop and rename cannot be observed half-applied.
CREATE TABLE crew_bill_reserves_rebuilt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    total_reserved_amount REAL,
    currency TEXT NOT NULL DEFAULT 'USD',
    observed_at TEXT,
    synced_at TEXT NOT NULL,
    absent_since TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    estimated_next_funding_amount REAL,
    next_funding_date TEXT,
    UNIQUE (provider, external_id)
);

-- Rows are copied verbatim, ids included. Nothing is clamped, rounded or repaired: an
-- existing row that was stored under the old constraint was already non-negative, and this
-- does not silently change any value that was previously accepted.
INSERT INTO crew_bill_reserves_rebuilt (
    id, provider, external_id, total_reserved_amount, currency, observed_at, synced_at,
    absent_since, created_at, updated_at, estimated_next_funding_amount, next_funding_date
)
SELECT
    id, provider, external_id, total_reserved_amount, currency, observed_at, synced_at,
    absent_since, created_at, updated_at, estimated_next_funding_amount, next_funding_date
FROM crew_bill_reserves;

DROP TABLE crew_bill_reserves;

ALTER TABLE crew_bill_reserves_rebuilt RENAME TO crew_bill_reserves;

CREATE INDEX idx_crew_bill_reserves_current
    ON crew_bill_reserves(provider, absent_since);
