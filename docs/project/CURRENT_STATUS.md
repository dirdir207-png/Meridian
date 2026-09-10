# Enhanced SimpleCrew — Current Status

Last consolidated: 2026-09-10 (Observatory dial continuation)

## Canonical sources

> This copy of the project is the **separate OpenRouter build** living on
> `dirdir207-png/ORSC`. It does not touch the preexisting SimpleCrew repository
> (`dirdir207-png/SimpleCrew`), its branches, or the upstream project, which
> continue independently. All work here stays on ORSC.

- Repository: `dirdir207-png/ORSC` (separate Meridian build)
- Default branch: `main` (unchanged; this build is developed on a branch)
- Implementation branch: `feat/meridian-implementation` (on ORSC)
- SimpleCrew-side branches (`ox-alpha/meridian-overhaul` and others) are owned by the other project and are not used by this build
- Approved design: `docs/superpowers/specs/2026-08-26-meridian-product-overhaul-design.md`
- Implementation plan: `docs/superpowers/plans/2026-08-26-meridian-overhaul-implementation.md`
- Model strategy: `docs/superpowers/plans/2026-08-26-meridian-model-and-token-strategy.md`
- Codex CLI handoff: `docs/project/CODEX_CLI_HANDOFF.md`
- Approved specifications override informal chat history when they conflict.

## Architecture and safety decisions

- Enhanced SimpleCrew runs on the always-on Mac.
- Crew GraphQL is the primary banking-data path.
- Crew credentials and bearer/session tokens remain server-side/local and must never be exposed to browser or Base44 frontend code.
- Tailscale is the intended private remote-access path (`docs/REMOTE_ACCESS.md`).
- Existing SimpleCrew authentication/passkey protection remains in place.
- Financial mutations must never be retried automatically; uncertain transfer outcomes surface as `uncertain_write` / verify-state.

## Milestone status

### Slice 1 — Trustworthy foundation and shell: COMPLETE ✅

Tasks 1–8 fully implemented, tested, and pushed to `feat/meridian-implementation`:
- Production config, CI, Docker, browser-smoke gates (Task 1)
- Atomic/idempotent action execution with EXECUTING claim state (Task 2)
- Versioned migrations (001–004), normalized financial read model (Task 3)
- Crew data adapter → Meridian graph (Task 4)
- `/api/meridian/*` read APIs (Task 5)
- Editorial Wealth design tokens, responsive shell (Task 6)
- Today workspace, Activity ledger with cursor pagination (Task 7)
- Transaction inspector (Task 8)
- **Slice 1 Docker gate passed: 204 tests, Ruff clean, meridian:slice1 image verified**

### Slice 2 — Commitments and funding: COMPLETE ✅

Tasks 9–12 fully implemented, tested, and pushed to `feat/meridian-implementation`:
- Unified Meridian Commitments with dataclass + repository (Task 9)
- Funding calculus with 7 rule kinds, DST-immune, carry-forward (Task 10)
- Idempotent scheduled funding proposals with dedup (Task 11)
- Plan workspace: service, API, UI (Task 12)
- **Slice 2 Docker gate passed: 259 tests + 28 browser skips, Ruff clean, meridian:slice2 image verified**

### Crew Session Broker — COMPLETE ✅ (merged to main)

- AES-256-GCM encrypted credential storage, macOS Keychain adapter
- Loopback broker API with capability authentication
- Cookie-aware transport, Docker-side broker transport
- Renewal endpoints, LaunchAgent installer, Docker Compose template
- **150 broker-focused tests passing** (2 pre-existing Meridian advisor failures unrelated)

### Slice 3 — Unified providers and transaction intelligence: COMPLETE IN CURRENT BRANCH ✅

- Tasks 13–16 (providers, reconciliation hardening) are consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 4 — Advanced intelligence and consolidation: COMPLETE IN CURRENT BRANCH ✅

- Tasks 17–20 are consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 5 — Document Intelligence: COMPLETE IN CURRENT BRANCH ✅

- Tasks 21–23 are consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 6 — Life Context: COMPLETE IN CURRENT BRANCH ✅

- Task 24 is consolidated in the ORSC `feat/meridian-implementation` branch.

### Slice 7 — Asset and Contract Memory: COMPLETE (Task 26 done in current branch)

- Task 25 is consolidated in the ORSC `feat/meridian-implementation` branch.
- Task 26 (evidence memory across workspaces + asset/contract management) is complete in
  `feat/meridian-implementation` per `docs/superpowers/specs/2026-08-31-task26-evidence-memory-design.md`
  and `docs/superpowers/plans/2026-08-31-task26-evidence-memory.md`:
  - Four memory endpoints: `GET /api/meridian/memory/{today|plan|activity|accounts}`.
  - Six pipeline action types: `create/update/delete_asset`, `create/update/delete_contract`
    (propose→approve→execute; executors/verifiers in `meridian/memory_actions.py`).
  - Management proposal API: `POST/PATCH/DELETE /api/meridian/assets` and `/contracts`.
  - Evidence content resolves end-to-end (`MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY` configured;
    `DerivedKeyProvider` in `meridian/storage.py`).
  - Frontend: per-workspace memory regions, Assets & Contracts management UI, pending
    memory-proposal approval rendering.

> Historical per-task commit SHAs (`726e00e`…`a092c4a`) were local-only and never
> existed on GitHub; this build tracks the ORSC branch tip instead.

## Current test suite

- Fresh gate run on `feat/meridian-implementation` (2026-09-06):
  - Ruff clean (`ruff check app.py crew meridian tests` — import-sort/warnings fixed,
    including removal of the dead `build_command_payload` / `reconcile_crew_mutation`
    imports in `app.py`).
  - Full unit suite: **535 passed, 60 skipped** (skips are the Playwright browser
    tests that require a running `APP_URL`).
  - `pip-audit -r requirements.txt`: **no known vulnerabilities**.
  - Browser suite (against the live preview): `test_capability_parity.py` (3),
    `test_plan.py` + `test_meridian_shell.py` (18), plus the R30 parity contract —
    see docs/project/PRIVATE_RELEASE_ACCEPTANCE.md §1/§5.
- Historical Slice-2 / 445-test counts are superseded by the 2026-09-06 gate above.

### R32 (private daily-use release) — 2026-09-06

See `docs/project/PRIVATE_RELEASE_ACCEPTANCE.md` for the full record. Summary:
- Tested image digest `sha256:6ac1fac8f1c1…`; `docker-compose.yml` pinned to
  `meridian:r32-test` (no more `build: .`).
- 2 fresh read-only Crew captures (6 accounts / 100 txns each); app + collector
  restart, last-good offline recovery, and unchanged-tab refresh verified.
- **Two recorded non-green items (not release-blocking, but explicit):**
  1. The active daily-use instance is the local preview (port 8081) running from
     source, not the tested Docker digest — compose target matches digest, the
     daily instance does not.
  2. Autopilot query schema drift (`Cannot query field "entities" on type "Rule"`)
     leaves every sync `status=partial` (errors=1, autopilot null). The query spec
     lives in WorkAssistant (`operations/*.graphql`, owner-gated), **not** ORSC;
     benign to accounts/transactions/commitments.


### Observatory implementation — 2026-09-08 (ongoing small slices)

- Branch: `feat/meridian-implementation`; ahead of origin by 41 commits after this session.
- Slice 1 (already on branch): Observatory visual tokens/layer, decorative SVG placeholder
  asset set, and a fixture-driven accessible dial (`static/css/meridian/observatory.css`,
  `static/css/meridian/dial.css`, `static/js/meridian/dial.js`,
  `static/meridian-observatory-preview.html`).
- Slice 2 (commits `fc83417`, `c825358`): read-only data-driven dial API and view model
  (`meridian/services/dial.py`, `GET /api/meridian/dial`), Today partial wiring, evidence
  ticket, currency/minor-unit safety, and Observatory shell remapping for the Meridian
  main and Settings templates.
- Slice 3 (commit `27db882`): Observatory login/application-shell slice.
  - `templates/login.html` now uses the Meridian wordmark, indigo/paper palette, and the
    decorative engraving while preserving passkey/password controls, API calls, and error
    handling.
  - `static/css/meridian/observatory.css` adds `[data-meridian-shell] { background: transparent; }`
    so the body’s indigo radial atmosphere shows through the app shell.
- Slice 4 (commit `865c3dc`): read-only Plan scenario preview.
  - New authenticated `POST /api/meridian/plan/scenario` calls the existing pure
    `meridian.scenarios.run_scenario` service. It returns `read_only: true`, validates
    numeric inputs, and does not update the repository.
  - Plan UI adds an Observatory-styled “Scenario preview” card with before/after projection
    rows and an explicit “Preview — no changes applied” note. No apply/approval control is
    wired yet.
- Slice 5 (commit `d258aa4`): Accounts connection freshness.
  - The Accounts connection rail now consumes the backend’s computed `data_freshness` instead
    of inferring freshness only from per-connection health, adding an explicit partial state.
- Slice 6 (commit `397d835`): Settings Payday & Funding workspace.
  - The existing payday partial and proposal-only controller are now reachable from Settings.
  - Added readable Meridian/Observatory styling for the payday summary, editor, and preview.
  - The only payday write path remains the existing funding-rule proposal endpoint.
- Slice 7 (commit `622c705`): Accounts-to-Activity filtered navigation.
  - Account rows now expose an “Activity” action that switches to the Activity workspace in
    timeline mode and applies that account filter through `MeridianActivity.openAccount`.
- Slice 8 (commit `c6614cc`): Activity pattern comparisons.
  - Pattern cards now include human-readable detail lines for recurring cadence, category
    shifts, merchant trends, and cash-flow changes, while preserving clickable evidence rows.
- Slice 9 (commit `5550425`): Settings action history.
  - Added `ActionStore.list_recent` and `GET /api/meridian/actions`.
  - Added a read-only Settings “Actions & approvals” section listing proposed, approved,
    executing, executed, verified, rejected, expired, and failed states. No approve/execute
    controls are duplicated in this slice.
- Slice 10 (commit `fcdcea2`): Today dial hierarchy.
  - Moved the read-only Observatory dial into the primary Today column, directly under the
    command header, so it is no longer below the fold on mobile.
- Slice 11 (commit `c1d627f`): Today compact safe-to-spend strip.
  - The safe-to-spend label/figure now appears as a quiet strip above the dial, matching the
    reference hierarchy rather than a large forecast card leading the page.
- Slice 12 (commit `a6a9eea`): Settings Security & Data.
  - Added a read-only Security & Data section listing passkey metadata and explicit
    safeguards. It never renders credential IDs, tokens, or secret material.
- Slice 13 (commit `6b63abd`): Accounts decorative constellation.
  - Added the same restrained map ornament to the Accounts command header without encoding
    account relationships or amounts.
- Slice 14 (commit `e1e0606`): Accessible Add Connection overlay.
  - The connection chooser now traps Tab/Shift+Tab focus in addition to Escape and focus
    restoration.
- Slice 15 (commit `ad06c50`): Transaction source stamp.
  - The transaction detail sheet now shows a quiet “Source observation” line using the
    existing freshness timestamp, keeping dated source and balance distinct.
- Dial concept-focus pass (commits `c81d776` through `1c04dba`):
  - Solid parchment instrument face, engraved rim/rivets, dark sky disk, starfield,
    observatory engraving, golden star-centered pointer, and compact real-data center.
  - Day labels around the instrument, upcoming-money event orbit cards with kind icons,
    “Days to payday →”, “Turn to explore your week”, and “Explore my plan” CTA.
  - Fixed dial selection so clicking an event or marker updates the center and evidence ticket.
  - Dial now defaults to the first upcoming money moment, so the instrument is populated on load.
  - Added orbit leader lines, kind-colored markers, and a stronger observatory/lunar engraving.
  - Added engraved ticket corners to the selected-event evidence ticket.
  - Added full-width desktop Today staging so the dial/event rail is concept-scale rather than compressed beside Virgil.
  - Added Today command hierarchy: Today title, truthful orbit subtitle, and a real Crew observation stamp.
  - Added deterministic paper/ink WEBP textures to the decorative asset set.
   - Added a readable orbit bridge between desktop event cards and the dial, while hiding
     decorative connectors on mobile where the rail stacks below the instrument.

  - Added `tests/browser/test_observatory_dial.py`: Playwright verifies event selection updates
    the center/ticket, no non-GET request occurs during selection, and 390px has no horizontal
    overflow. Local run: 2 passed against the source preview.
- Verified in this session:
  - `tests/meridian` — 520 passed, including the formerly date-sensitive dial fixture with a
    frozen clock and explicit `build_dial(..., now=...)` value.
  - `tests/meridian/test_dial_js.py tests/meridian/services/test_dial.py` — 26 passed.
  - `APP_URL=http://127.0.0.1:8081 pytest tests/browser/test_observatory_dial.py -q` — 2 passed.
  - `ruff check app.py crew meridian tests` — clean.
  - Full non-browser baseline — 651 passed, 1 skipped, 1 pre-existing isolated failure in
    `tests/test_app_evidence_integration.py::test_evidence_content_resolves` (unrelated to
    Observatory; the test’s `app` fixture is not authenticated/configured in this run).
- Safety: no live financial mutation was executed or added in these slices. The dial and
  plan-scenario endpoints are read-only, scenario apply is intentionally not wired, and the
  payday/action-history surfaces are proposal-only or read-only.
- Next action: continue Observatory visual parity with activity detail sheet polish, Accounts
  constellation/detail, Settings security & data, Virgil/action-approval controls, accessible
  overlay/keyboard/safe-area/reduced-motion checks, then browser visual compares against
  `design/observatory-drafts-2026-09-08/`.

## Current blockers

- **Daily instance from source, not the tested digest:** the running preview on
  port 8081 is `run_preview_local.sh`; the Docker port-8080 slot is occupied by a
  pre-existing deployment from another project directory. "Deployed==tested" is
  met for the compose target only. (Autopilot schema drift was resolved 2026-09-06
  in WorkAssistant `a96f2d5` — snapshot now `complete: true, errors: {}`, sync
  `status=complete`.)
- TokenX routing unavailable: sub-agent spawning is blocked in this session, so parallel execution must occur in a verified Codex CLI environment or run sequentially in the parent.
- AI providers: owner's OpenAI key has no credits (429); OpenRouter free-tier quota tight
- Verification workflow: Playwright screenshot harness against isolated instance gates all UI changes

## Codex CLI handoff

A corrected handoff document has been created at `docs/project/CODEX_CLI_HANDOFF.md` containing:
- All project document references
- Current repository state
- Git evidence that Tasks 13–25 are implemented
- Task 26 scope and file locations
- Parallel agent lanes with disjoint write scopes
- TDD workflow requirements
- Model routing strategy
- Safety rules and commit conventions
- Final automated and owner-only acceptance gates

## Next action

- Task 26 and R30/R31 are complete in `feat/meridian-implementation`; the branch is pushed to
  `dirdir207-png/ORSC`. No merge to `main` (separate build by design).
- R32 acceptance recorded (see PRIVATE_RELEASE_ACCEPTANCE.md). Not yet a fully
  green formal release while the two gaps above stand; local daily use is safe.
- Remaining owner-gated tracks: R32 autopilot schema fix (WorkAssistant), R33/R34
  connected billers (depend on R32, partner-gated), and the R25 credential source.

Remaining gate (desktop / owner): reconcile the autopilot query in WorkAssistant and
optionally move the daily-use instance onto the tested Docker digest, then re-run
the §5 live acceptance to clear the two non-green items.

## Trial Canceler / Meridian Sentinel foundation — 2026-09-10 (uncommitted)

A separate additive foundation was implemented in this ORSC lane; it is documented in
`docs/project/TRIAL_CANCELER_HANDOFF.md` and is **not yet committed, shipped, or wired
to a UI, scheduler, browser extension, mail/transaction intake, or live Crew card
flow**. It adds `meridian/trials.py`, `meridian/cancellation/`, migrations 016–017,
and authenticated `/api/meridian/trials*` / cancellation-action routes. The state
machine requires positive billing evidence before `Billing stopped`; no merchant action
or financial mutation was executed. `tests/meridian` passed 520 tests after the change.
Parallel Observatory dirty/untracked files were not altered by this work.
