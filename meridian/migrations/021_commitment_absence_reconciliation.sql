-- 021: A complete provider read may conclude that a bill it used to return is
-- gone. Absence is local evidence only: the row, its funded amount and its
-- transactions are kept. The bill is archived so planning surfaces drop it,
-- and absent_since records why, distinguishing provider absence from an
-- owner's own archive.
ALTER TABLE commitments ADD COLUMN absent_since TEXT;

-- Absence is read in the reconciliation update, which filters on the owning
-- provider (legacy_source) and on absent_since.
CREATE INDEX idx_commitments_absent
    ON commitments(legacy_source, absent_since);
