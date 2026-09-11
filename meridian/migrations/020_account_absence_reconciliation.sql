ALTER TABLE financial_accounts ADD COLUMN absent_since TEXT;

-- Absence is read in two places: the freshness join and the reconciliation
-- update. Both filter on the owning connection and on absent_since.
CREATE INDEX idx_financial_accounts_absent
    ON financial_accounts(connection_id, absent_since);
