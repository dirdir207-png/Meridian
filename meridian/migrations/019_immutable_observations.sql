CREATE TABLE financial_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    connection_external_id TEXT NOT NULL,
    object_kind TEXT NOT NULL CHECK (object_kind IN ('account', 'transaction')),
    external_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    source_updated_at TEXT,
    freshness TEXT NOT NULL CHECK (freshness IN ('fresh', 'stale', 'partial', 'unavailable')),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    assumptions_json TEXT NOT NULL DEFAULT '[]',
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    data_mode TEXT NOT NULL DEFAULT 'actual' CHECK (data_mode IN ('actual', 'simulated')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (snapshot_id, object_kind, external_id)
);
CREATE INDEX idx_financial_observations_snapshot ON financial_observations(snapshot_id, object_kind, external_id);
CREATE INDEX idx_financial_observations_external ON financial_observations(provider, connection_external_id, object_kind, external_id, observed_at DESC);
