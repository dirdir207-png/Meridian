CREATE TABLE trial_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id INTEGER NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK(kind IN ('7_days','3_days','1_day','deadline')),
    due_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','dismissed')),
    created_at TEXT NOT NULL,
    sent_at TEXT,
    UNIQUE(trial_id, kind)
);
CREATE INDEX trial_notifications_due_idx ON trial_notifications(status, due_at);
