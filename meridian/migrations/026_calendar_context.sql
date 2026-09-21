-- Calendar context: read-only, and deliberately NOT an evidence store.
--
-- Scope decision (owner, 2026-09-21): calendar events are read-only CONTEXT. They may
-- explain a month's cash-flow pressure -- travel, appointments -- but they are never
-- matched to a transaction, never treated as an obligation, and never written to the
-- evidence store.
--
-- The schema enforces that boundary rather than relying on everyone remembering it: there
-- is NO amount column, NO commitment reference and NO transaction reference. A future
-- change cannot begin matching events to money by reaching for a column that was already
-- here, which is exactly how a read-only capability would otherwise acquire authority as a
-- side effect of a later edit.
--
-- `source` is PROVENANCE, not a category. It names the ingestion route that observed the
-- row -- the app's own connector, or a harness-mediated replay -- so any row can be traced
-- to how it arrived (D-016 guardrail 3). Two routes observing the same provider event are
-- two rows, because collapsing them would destroy that trace.
--
-- Everything here is observation. A row records what a read SAW at a moment, never what
-- Meridian decided to do.
CREATE TABLE calendar_context_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_link TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    UNIQUE(source, external_id)
);
CREATE INDEX calendar_context_events_window_idx ON calendar_context_events(starts_at);
