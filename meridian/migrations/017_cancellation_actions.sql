CREATE TABLE cancellation_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id INTEGER NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('planned','attempted','awaiting_ack','verified','unverified','escalated','failed')),
    status_label TEXT NOT NULL DEFAULT 'Unverified',
    confirmation_reference TEXT,
    started_at TEXT,
    completed_at TEXT,
    artifact_ids TEXT NOT NULL DEFAULT '[]',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX cancellation_actions_trial_idx ON cancellation_actions(trial_id, created_at);
