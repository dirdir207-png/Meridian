-- 030: record Crew's OWN selected spend pocket, as observed, with provenance.
--
-- WHY (OS-113, owner-approved 2026-09-25). "Which pocket is the spend pocket" decides what Safe to
-- Spend MEANS: it is the one pocket the figure exempts from "everything set aside". The mechanism was
-- an English name, and that is measurably ambiguous rather than merely inelegant -- verified against
-- the two readable databases:
--   * gate.db matches TWO rows for the allow-list: 'Safe to Spend' (active) and 'Free to Spend'
--     (inactive since 2026-09-17), so a list-order match can land on a retired pocket;
--   * savings_data.db matches TWO ACTIVE pockets BOTH named 'Free to Spend' (external_ids
--     Subaccount:99adf76a... and Subaccount:edc8cb88...), which no name-based rule can tell apart.
-- Crew publishes the answer itself as `userSpendConfig.selectedSpendSubaccount` per user, repeated on
-- every virtual/physical card, and the connector has always fetched that facet -- Meridian discarded
-- it. Run over the owner's real historical capture, the shipped
-- `readback_selected_spend_pocket()` returns exactly one id, `Subaccount:edc8cb88-f234-4321-8a3b-
-- d2790e981a7a`, which is byte-identical to `financial_accounts.external_id` for the pocket now named
-- 'Safe to Spend' (and named 'Free to Spend' before the owner renamed it). No guessing is required.
--
-- WHAT THIS TABLE IS NOT. It never stores a resolution this read did not make. `resolution` separates
-- the three things a snapshot can say -- one selection, an observed absence, or cards that disagree --
-- so an unobserved facet is the ABSENCE OF A ROW rather than a row that says "none" (the C01
-- unreported-is-not-zero rule, applied here). Rows are append-only and carry their own snapshot id,
-- timestamp, freshness and confidence, so the read path can date the claim it is using and can never
-- present a stale selection as the current one.
CREATE TABLE crew_spend_selection_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    connection_external_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    resolution TEXT NOT NULL CHECK (resolution IN ('selected', 'none', 'ambiguous')),
    selected_external_id TEXT,
    observed_external_ids_json TEXT NOT NULL DEFAULT '[]',
    freshness TEXT NOT NULL CHECK (freshness IN ('fresh', 'stale', 'partial', 'unavailable')),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    assumptions_json TEXT NOT NULL DEFAULT '[]',
    data_mode TEXT NOT NULL DEFAULT 'actual' CHECK (data_mode IN ('actual', 'simulated')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- A 'selected' resolution must carry the id it selected, and nothing else may carry one: this is
    -- the same relationship `financial_observations` enforces between a payload and its hash.
    CHECK ((resolution = 'selected') = (selected_external_id IS NOT NULL)),
    -- One observation per snapshot per provider: re-ingesting the same snapshot cannot manufacture a
    -- second, competing selection.
    UNIQUE (snapshot_id, provider)
);

CREATE INDEX idx_crew_spend_selection_latest
    ON crew_spend_selection_observations(provider, connection_external_id, observed_at DESC, id DESC);
