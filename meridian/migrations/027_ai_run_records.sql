-- AI run records: the audit trail behind an AI answer.
--
-- Track I.1 (MERIDIAN_ROADMAP.md §6) requires a run record -- "model and provider, prompt
-- version, evidence used, timing, outcome, persisted so a proposal can be audited back to
-- the reasoning that produced it". Until now the record was CARRIED (RunRecord.as_dict) and
-- printed, but never kept, so the audit trail existed only for as long as the terminal did.
--
-- WHAT THIS TABLE IS NOT, and the schema enforces it. There is NO claim text, NO model
-- output and NO evidence body here. A run record says WHICH model, on WHICH evidence, with
-- WHICH prompt version, and how it ended -- it is a pointer to the reasoning, not a copy of
-- it. Storing generated prose would create a second, unversioned place where financial
-- statements live, outside the evidence store and outside the surfaces that know how to
-- label freshness and provenance. The requirement is to be able to AUDIT back to the
-- reasoning; it is not to keep a transcript.
--
-- `evidence_ids` is a JSON array of reference ids, deliberately NOT a foreign key: evidence
-- can be revoked or have its content deleted (see meridian/evidence.py), and an audit record
-- must survive that and still say what was consulted. A cascade would erase the row that
-- explains why an answer was given.
--
-- `outcome` is one of ok / unavailable:* / failed:* (meridian/ai/investigator.py), stored as
-- text rather than an enum so a new failure mode does not need a migration to be recordable.
--
-- NO AUTHORITY. Rows here record what a READ-ONLY role did. Nothing in this table grants,
-- approves or executes anything, and no column can reference a provider mutation.
CREATE TABLE IF NOT EXISTS ai_run_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    outcome TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

-- The two questions a reader actually asks: "what did this role do recently" and "what
-- produced this outcome". Both are covered here rather than needing a table scan.
CREATE INDEX IF NOT EXISTS idx_ai_run_records_recorded_at
    ON ai_run_records (recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_run_records_role
    ON ai_run_records (role, recorded_at DESC);
