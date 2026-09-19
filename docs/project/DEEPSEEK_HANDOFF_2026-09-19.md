# DeepSeek continuation — owner rulings and Activity sun

## Re-entry

Canonical checkout: `/Users/stephenwest/Openrouter/simplecrew-latest`. Branch `feat/meridian-implementation`, base HEAD `ade532d`. This checkpoint is deliberately **uncommitted**, as requested for a usage-conscious handoff. Nothing pushed or deployed; no live database touched, no Crew calls or writes. Existing unrelated untracked files were preserved (1,862 before this turn). Do not use the Documents checkout.

Read `AGENTS.md`, `PROJECT_INSTRUCTIONS.md`, the top of `CURRENT_STATUS.md`, decisions D-010–D-012, this note and the diff. The old Astra handoff now points here; its unanswered-three-questions gate and blanket demotion of September 8 are superseded. `WORK_CYCLE.md`, `PROJECT_BRIEF.md`, `DECISIONS.md` and `scripts/meridian_work.py` from the other checkout do not exist here; use this checkout's Meridian records.

No other task/session was launched. Claim: `codex-owner-rulings`; its row and exact paths are in `AGENT_COORDINATION.md` and `agent-claims.json`. That claim has since been **adopted and released by DeepSeek** — see the verification block at the end of this note. Never stage all untracked artifacts.

## Owner answers — do not ask again

1. Bills already have a funding/income source in Crew; one exists presently. Preserve Crew's relationship and cross functionality. Managing assignments in Crew is acceptable. This is not approval for a specific provider write or guessed allocation.
2. The generic icons do not match the concept; ultimately replace all. One missing sun now is acceptable to conserve usage. One generation was used.
3. September 18 fills missing pages. September 16 wins overlap; September 8 is fallback. The September 16 kit says its reconstructions do not supersede page composition and references September 8 PNGs. No separate September 16 page-concept directory was located in design/kit paths; locate any actual newer page reference before claiming fidelity to one. Timeline's September 18 sun is the reference for this bounded asset slice.
4. Stop at a clean usage-conscious checkpoint; leave uncommitted work DeepSeek can continue. Prioritize visual progress. No bulk icon generation.

## Implemented in this checkpoint

- D-010–D-012 persist the rulings; OS-048 carries the new funding decision, OS-052 tracks the sun.
- One generated ornate brass sun, outside the Bootstrap directory, with exact prompt and provenance in `design/observatory-sun-2026-09-19/`.
- `static/css/meridian/activity.css`: 24px day-marker slot; older days display the generated PNG in its native colors and alpha instead of a single-color mask. Today's moon remains supplied. No layout redesign or financial behavior change.
- `static/js/meridian/activity.js`: comment corrected only. Existing day selection and semantics remain; the previous SVG is retained, but is not a runtime fallback if the PNG fails to load.
- Full icon replacement, circular day-marker frames, broad page audit and funding implementation remain open.

## Visual pass completed after the sun checkpoint

The owner approved a focused pass with a few contained corrections. `docs/project/VISUAL_CORRECTIONS_2026-09-19.md` is the detailed record.

- The wordmark’s accent is now a round dot on the second `i`.
- Activity mobile Timeline rows stack merchant and category so long names remain readable; Review cards are unchanged.
- Settings loads the persisted theme controller and the synthetic preview now serves the real Connections template plus a synthetic read-only payload.
- Fresh captures cover Today, Plan, Accounts, Activity and Settings. Main pages and Activity have zero overflow/page errors; Settings still records a 32px overflow at the 1024×768 tablet viewport (mobile 390/420/430 were clean) and is explicitly left as follow-up.

The last direct browser check emitted eight viewport/theme records with zero Activity overflow, fitting titles, working Review render, working wordmark dot and matching Settings theme. The broader governed capture manifests remain the authoritative artifacts; inspect their overflow fields before using them as acceptance evidence.

## Funding next slice — concrete findings, not implemented

At base HEAD:
- `meridian/providers/crewwork.py::_collect_commitment_candidates` walks `account.billReserve.bills`, but discards the parent reserve ID.
- `meridian/providers/base.py::CommitmentCandidate` carries external bill ID, dates, recurrence and funded amount, but no reserve identity.
- `meridian/sync.py::sync_providers` creates/updates `CommitmentRepository` bills from those candidates.
- `meridian/commitments.py` has no bill-reserve identity field. Funding plans already persist `bill_reserve_id` in `meridian/repository.py` (OS-050).
- `meridian/services/dial.py::_commitment_events` emits unknown funding for all bill occurrences. `build_dial` is called by both `/dial` and `/weather` in `meridian/api.py`.
- `static/js/meridian/dial.js` normalizes event fields and renders funding in the center, event row, accessibility label and evidence ticket. All relevant surfaces must agree.

Recommended bounded read-side implementation: preserve the observed bill→reserve link during ingestion, join to the current Crew plan by stable IDs, expose the funding-source name/provenance separately from occurrence reservation status, and consume it in the dial UI. Use a new migration if storage changes; never modify a shipped migration. Missing/ambiguous membership must not default to the sole global plan. If several plans later share a reserve, do not invent which one funds a specific bill: report ambiguity unless a finer Crew relationship is observed. Do not allocate reserve totals across future occurrences or change weather risk based on source identity. Existing stored bills have no membership; an ordinary subsequent read sync is needed to populate it after implementation, not guessed backfill. No live sync was performed here.

Test with synthetic snapshots: persistence, rename without ID change, reserve mismatch, absent/reappearing plans, missing membership, multi-plan ambiguity, local bills untouched, and funding source not falsely setting funded/partial or reserved amounts. Follow the actual exposed Crew shape; the owner clarified semantics, not a new API field. Reuse existing funding engine for amount projection if that becomes necessary; no parallel engine.

## Verification and commands

Use `.venv311/bin/python`; no system Python or production-only uv environment for browser checks.

- Focused Activity suite: 26 passed (`test_activity_timeline_chrome.py`, `test_activity_glyph.py`, `test_activity_vignette.py`).
- `node --check static/js/meridian/activity.js`: passed.
- Asset: RGBA, alpha extrema 0–255, 1,238,578 fully transparent pixels; metadata in `asset.json`.
- Capture command: `.venv311/bin/python scripts/capture_meridian_matrix.py --app-url http://127.0.0.1:8093 --output artifacts/observatory-sun-2026-09-19 --concept-dir design/observatory-extension-2026-09-18/concepts --concept-file timeline.png --fixture observatory-synthetic --frozen-clock 2026-09-18T19:50:00-04:00 --workspaces activity --ui-state timeline --ui-state-selector '[data-activity-mode="timeline"]' --skip-login`.
- First attempt used a nonexistent `data-activity-tab` selector and failed before captures; corrected to observed `data-activity-mode`. No app change was needed for that failure.
- The capture metadata's commit is the base HEAD; these captures include the uncommitted sun/CSS change. Pair them with this diff and the asset hash; do not describe them as captures of committed `ade532d` alone.
- Final matrix: 10 records / 20 PNGs across all five required viewports and both themes; all zero overflow and zero page errors. Browser asset-load probe passed both themes. Visually inspected the mobile Air dark and desktop light viewport plus both marker close-ups. `git diff --check` and guardrails passed.
- Only the synthetic `:8093` preview was used. `:8081` was not visited, restarted or mutated. No full financial test suite or live acceptance is claimed for this presentation-only slice.
- **DeepSeek verification (adopted 2026-09-19).** Claim reconciled and adopted; `codex-owner-rulings` released. Independently reproduced: 55 focused tests passed (`test_settings_visual_preview`, `test_observatory_identity`, `test_auth_branding`, and the three Activity suites — a superset of the 42 claimed); `node --check static/js/meridian/activity.js`; Ruff clean on the changed preview/capture/test files; `git diff --check` clean; `scripts/check_guardrails.py --agent codex-owner-rulings` OK (21 scope patterns, 456 changed paths). Re-hashed the asset: sha256 `25e0aeca…` matches `asset.json`, RGBA 1254×1254, alpha 0–255, 1,238,578 fully transparent pixels. Read every manifest back: `after-main` 30 records, `after-activity` 10, `observatory-sun` 10 — all zero overflow / zero console errors; `after-settings` 10 records with exactly two 32px overflow entries, both the **1024×768 tablet** viewport (light and dark), so the "mobile overflow" wording in the earlier notes was corrected in `CURRENT_STATUS.md` and `VISUAL_CORRECTIONS_2026-09-19.md`. A vision read of the small close-ups confirms the round peach dot over the second `i` and the mobile row stacking merchant → sub-line → category with the amount in its own right column; the repeated "Corner Market" sub-line is fixture data (`merchant` and `description` are the same synthetic string), not a layout defect. No code was changed by this verification; no provider, live or authority operation.

## Files to review/stage explicitly

`docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/HANDOFF_FOR_ASTRA_2026-09-19.md`, this handoff; `static/css/meridian/activity.css`, `static/js/meridian/activity.js`, `static/img/meridian/observatory/sun-engraving-2026-09-19.png`; `design/observatory-sun-2026-09-19/{README.md,prompt.txt,asset.json}`. Captures in `artifacts/observatory-sun-2026-09-19/` remain untracked by the project's convention.

Review fresh Git status first. Complete verification noted in CURRENT_STATUS, then commit this narrow slice when appropriate. No funding code is partially implemented.
