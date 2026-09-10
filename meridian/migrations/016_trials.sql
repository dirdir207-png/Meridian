CREATE TABLE trials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL,
    account_identifier TEXT,
    plan_name TEXT,
    status TEXT NOT NULL DEFAULT 'trial' CHECK(status IN ('trial','active','canceled','unknown')),
    trial_started_at TEXT NOT NULL,
    trial_ends_at TEXT NOT NULL,
    cancel_by TEXT NOT NULL,
    buffer_days INTEGER NOT NULL DEFAULT 1 CHECK(buffer_days >= 0 AND buffer_days <= 90),
    price_after REAL,
    cadence TEXT,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    source_of_truth TEXT NOT NULL DEFAULT 'manual' CHECK(source_of_truth IN ('checkout_capture','receipt','transaction','manual','inferred')),
    confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0 AND confidence <= 1),
    allowlisted INTEGER NOT NULL DEFAULT 0 CHECK(allowlisted IN (0,1)),
    essential INTEGER NOT NULL DEFAULT 0 CHECK(essential IN (0,1)),
    autonomy_tier TEXT NOT NULL DEFAULT 'propose' CHECK(autonomy_tier IN ('direct','propose','autonomous')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX trials_cancel_by_idx ON trials(cancel_by);
CREATE INDEX trials_status_idx ON trials(status);
