# Enhanced SimpleCrew — Current Status

Last consolidated: 2026-09-13 (C4 pocket deletion readback repair)

## C4 pocket deletion readback repair — 2026-09-13

Implemented: `delete_crew_pocket` now verifies absence from a fresh, complete Crew snapshot. Complete absence is verified; presence is provider-confirmed failure; missing, partial, stale, malformed, timeout, or exception readback remains unresolved and non-retryable. No accepted deletion is resubmitted, including after restart. Proposal → owner approval → single-attempt execution → provider verification remains intact.

Tested: focused C4/routing suites **69 passed**; `tests/meridian` **673 passed**; changed-path Ruff, `git diff --check`, and guardrail receipt passed. Synthetic fake-provider coverage proves complete absence, partial readback, and no resubmission. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: verifier-less financial operations, full mutation reachability, and live owner acceptance. Next: continue to the next low-risk operation-specific readback slice.

## C4 pocket readback repair — 2026-09-13

Implemented: `create_crew_pocket` now verifies the provider-generated pocket ID and returned identity fields against a fresh, complete Crew snapshot. Incomplete, missing, malformed, timeout, exception, or mismatched readback remains unresolved or provider-confirmed failure as appropriate; the accepted operation is non-retryable and never resubmitted. Proposal → owner approval → single-attempt execution → provider verification remains intact.

Tested: focused C4/routing suites **67 passed**; `tests/meridian` **671 passed**; changed-path Ruff, `git diff --check`, and guardrail receipt passed. Synthetic fake-provider cases cover complete confirmation, incomplete readback, and no resubmission. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: other verifier-less operations, full mutation reachability, and live owner acceptance. Next: continue to the next low-risk operation-specific readback slice.

## C4 create-bill readback repair — 2026-09-13

Implemented: `create_crew_bill` now verifies the provider-generated bill ID and requested name/amount against a fresh, complete Crew snapshot. Missing, partial, stale, malformed, timeout, exception, or mismatched readback is unresolved (`executed`, `ok: null`) unless provider truth proves a mismatch; the accepted create is never resubmitted, including after restart. The existing proposal → owner approval → single-attempt execution → provider verification pipeline is preserved.

Tested: focused C4 suite (`tests/meridian/test_crew_write_actions.py tests/crew/test_executors.py`) **53 passed**; `tests/meridian` **669 passed**; changed-path Ruff, `git diff --check`, and guardrail receipt passed. Synthetic fake-provider coverage proves complete confirmation and incomplete readback/no-resubmit. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: other verifier-less operations, full mutation reachability, and live owner acceptance. Next: review this commit.

## C4 archive readback repair — 2026-09-13

Implemented: `archive_crew_bill` now uses a fresh complete Crew snapshot verifier. A complete readback proving the bill is absent is verified; a still-present bill is a provider-confirmed failure; missing, partial, stale, malformed, timeout, exception, or otherwise inconclusive readback remains `executed` with `ok: null`, `provider_truth: false`, and `retry_allowed: false`. The accepted operation is never resubmitted, including after restart.

Tested: focused C4 suite (`tests/meridian/test_crew_write_actions.py tests/crew/test_executors.py`) **51 passed**; changed-path Ruff and `git diff --check` passed. Synthetic fake-provider coverage includes complete present/absent, partial, exception and restart/no-retry cases. No live provider, credentials, deployment, preset, migration, or unrelated path was touched.

Deployed: nothing. Verified: synthetic provider readback and isolated tests only. Remaining gaps: other verifier-less operations and full mutation reachability/live owner acceptance. Next: review and then select one further operation-specific readback.

## C4 post-execution financial verification repair — 2026-09-13

Implemented: reserve-setting writes now verify against a fresh, complete Crew snapshot rather than local commitments; missing, partial, stale, malformed, mismatched, timed-out, and exception readbacks remain explicitly unresolved (`executed`, `ok: null`, `provider_truth: false`, `retry_allowed: false`). A missing bill is no longer reported as confirmed deletion for bill updates. Verifier exceptions after provider acceptance no longer become false terminal failures. The existing proposal → owner approval → single claim/execution → provider verification pipeline remains unchanged; unresolved actions are non-claimable and never resubmitted.

Tested: RED reproduction from `scripts/verify_readiness.py probes` recorded the reserve verifier's no-local-ID false success, local-ID `AttributeError`, and partial-readback false deletion. RED→GREEN focused suite `tests/meridian/test_crew_write_actions.py tests/crew/test_executors.py` — **48 passed**; `tests/meridian` — **664 passed**; Ruff on changed paths, `git diff --check`, and `scripts/check_guardrails.py --agent builder --receipt <temp>` — clean. Synthetic cases cover complete match, missing/partial/stale/malformed/mismatched readback, timeout, verifier exception, and fresh-process restart; each asserts one provider submission and no retry. Preset identity/guard check: installed `Meridian Constitutional Builder` files at `/Users/stephenwest/.dsh/.agent-presets/meridian-constitutional-builder`, `verify_preset.py` — **33 invariants passed**. No live provider, credentials, deployment, preset modification, or migration change.

Deployed: nothing. Verified: synthetic provider/readback and isolated application tests only; no live financial acceptance or production deployment. Remaining gaps: other verifier-less operations still require future operation-specific readbacks; C4-wide mutation reachability and owner/live acceptance remain open. Next: perform one bounded operation-specific readback expansion after review.

## Expanded readiness audit — 2026-09-13

Implemented: reusable `scripts/verify_readiness.py`, safety tests, [readiness report](MERIDIAN_READINESS_AUDIT.md), prerequisite order and gameplan supplement. Tested: isolated application image **953 passed, 7 skipped, 1 failed** (machine-local Crew CLI unavailable); selected Harness suites **236 passed**; audit-tool safety checks **3 passed**. Synthetic restore passed across 21 migrations, WAL backup, failed-migration rollback, wrong-key/tamper rejection, fresh-process authenticated routes and unresolved-action non-retryability. Runtime inventory: 199 routes, 27 executors; allowed `update_crew_virtual_card` lacks executor. Static/probe evidence identifies remaining authority, verification, observation, recurrence, scenario and intake gaps. New maintainer R0 and Docker exclusions were reconciled rather than reported as unimplemented.

Deployed: nothing. Verified: synthetic recovery and stated test scope only; no fresh physical-device capture, live financial acceptance, production restore or installed-preset activation. Evidence: `artifacts/readiness-2026-09-13/`. Next: H0 custom-preset negative acceptance tests and bounded C4 financial verification repair, then C1/C2 event/observation integration. Preserve unrelated dirty files; this audit does not authorize live changes.

## Forward gameplan — 2026-09-13

Planning deliverable: [MERIDIAN_EXECUTION_GAMEPLAN.md](MERIDIAN_EXECUTION_GAMEPLAN.md), sections D1–D8 plus disagreements, one first move and unknowns. Evidence in `artifacts/gameplan-2026-09-13/`. Fresh remote listing returned only `main` and `feat/meridian-implementation`; 23 local tracking entries include 17 absent-server non-ancestor tips that must be preserved/reviewed before pruning. Ruff still reports 11 findings. Two disposable Git-fixture probes demonstrate defects in the proposed guardrail script's migration check. No cleanup, application implementation, preset installation, Harness restart, deployment or live acceptance occurred. Next proposed Harness move: H0 keyless red specification for the combined authority/re-entry gate, after owner approval of D3/D4. Full economic-OS vision remains subject to the mapped product contracts and evaluation; the plan is not a completion claim.

## Dial alignment incident fixed — 2026-09-12

**iPhone Air follow-up:** corrected an additional 18px horizontal overlap by keeping the enlarged dial inside its right grid boundary and adding a 12px gutter. WebKit and Chromium tests at 420×912 pass; **47 focused checks passed** and eight device-specific captures show zero overflow. Corrected CSS verified on the running local preview. Details and evidence are in the incident report below.

See [DIAL_ALIGNMENT_FIX_2026-09-12.md](DIAL_ALIGNMENT_FIX_2026-09-12.md). Implemented top-aligned dial, bounded scrollable callouts, full-width mobile titles/amounts, a separate date-control row and preview template auto-reload. Twelve synthetic events reproduced an 879px blank offset before the fix. **71 focused tests passed**, Ruff/diff checks passed; a 16-capture dense-data matrix reports zero overflow/page errors. Existing local preview on 8081 reloaded with the same database path/runtime configuration; login HTTP 200 and all three served UI asset hashes verified. No image publication, financial mutation, credential change or migration. Authenticated phone rendering has not been recaptured; broader visual QA remains separately tracked.

## Observatory refinement checkpoint — 2026-09-12

**Paused at owner request (usage budget).** Code/assets are saved; latest focused verification is **68 passed**, Ruff clean and diff whitespace clean. Safe-to-spend and original side-callout composition are restored, with keyboard focus fixes and a compact evidence card. The last full matrix had zero overflow/page errors but predates the compact-card adjustment; final screenshot review remains pending. Resume from the latest section in [OBSERVATORY_REFINEMENT_2026-09-12.md](OBSERVATORY_REFINEMENT_2026-09-12.md). No production deployment or live-data change.

Owner requested a focused visual correction, then emphasized prominent safe-to-spend and the original dial-left/callouts-right composition. Work is saved but not yet declared complete: [checkpoint and evidence](OBSERVATORY_REFINEMENT_2026-09-12.md). Implemented: dial artwork/layout and keyboard-focus correction, Today safe-to-spend presentation, isolated synthetic full-template preview. Latest composition browser checks: 7 passed; earlier focused suite: 36 passed. Final full Today matrix/review remains pending. No production deployment or live financial/data/credential change. Continue from this checkpoint; preserve unrelated files.

## Second roadmap review — 2026-09-11

See [MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md](MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md). This informed, single-agent review compares the first vision roadmap with governing documents and targeted source at `a20702716046f2beadfd1d6c1f3801585a9beeeb`. It proposes capability-based delivery, accounts for all 22 concepts and findings A–G, and selects V1.1 (ordinary sync → persisted observation → explained Today amount) as the next proposed bounded slice. No roadmap proposal is recorded as an accepted owner decision.

Implemented: documentation only. Tested: 45 focused policy/proactive/scenario/dial checks passed (exact command in report); isolated synthetic probes characterize observation identity/freshness/empty captures and recurrence drift. Verified after the computer interruption: report is intact; pytest and Playwright packages are installed, and the Chromium executable exists. The older Playwright-install blocker and “entire Observatory unbuilt” claim must not guide current planning. No fresh browser journey, full-suite gate, live provider acceptance, deployment or live-data change occurred. No independent review is claimed.

OS-001 links this partial audit evidence; its existing status is retained pending reconciliation of the full task contract. Next: review the second roadmap and prepare the bounded V1.1 implementation packet. Preserve the first roadmap and historical completion records; do not treat ledger closure as whole-product acceptance.

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

## Immutable observation foundation — 2026-09-10 (approved slice)

- Added additive migration `019_immutable_observations.sql` and credential-free `ObservationRepository`.
- Provider snapshots are appended as immutable actual observations with deterministic payload hashes, snapshot identity, source/update timestamps, freshness, confidence, and assumptions.
- Replays of the same observed snapshot are idempotent; partial and empty snapshots remain explicitly labeled.
- Added authenticated read-only `GET /api/meridian/observations`, exposing metadata only and never raw observation payloads.
- Verification: 542 `tests/meridian` tests passed; targeted Ruff and `git diff --check` passed. No financial mutation was added or executed.
- Added reproducible actual snapshot loading and a strictly read-only `SimulationInput` boundary; simulation inputs must reference an actual snapshot and are labeled `simulated`.
- Added authenticated read-only snapshot and simulation-preview endpoints; no actual repository or financial state is changed.
- Verification for this continuation: targeted observation tests passed; no financial mutation was added or executed.
- Next action: review and commit this bounded digital-twin continuation.

## Trial Canceler / Meridian Sentinel foundation — 2026-09-10 (committed)

A separate additive foundation was implemented and committed in this ORSC lane; it is documented in
`docs/project/TRIAL_CANCELER_HANDOFF.md` and is **not yet shipped or wired
to a UI, scheduler, browser extension, mail/transaction intake, or live Crew card
flow**. It adds `meridian/trials.py`, `meridian/cancellation/`, migrations 016–017,
and authenticated `/api/meridian/trials*` / cancellation-action routes. The state
machine requires positive billing evidence before `Billing stopped`; no merchant action
or financial mutation was executed. `tests/meridian` passed 520 tests after the change.
Parallel Observatory dirty/untracked files were not altered by this work.

## Whole-project safety continuation — 2026-09-10

- Revisited the governing product spec, implementation plan, consolidated handoff, release acceptance,
  current status, and Trial Canceler handoff; reconciled the latter's stale uncommitted label.
  Historical unchecked plan boxes are not treated as current
  status; the consolidated handoff's concrete findings drive follow-up work.
- Hardened the durable action pipeline so an approved action older than the configured 3600-second TTL
  is atomically marked `expired` during execution claim, closing the pending-list/execute race. Invalid
  approval timestamps fail closed. Added regression coverage.
- Fixed a real 390px Accounts overflow caused by the account list sheet's intrinsic min-content width;
  responsive and capability-parity browser coverage now pass (8 tests).
- Verification: full suite `730 passed, 64 skipped`; `tests/meridian` 520 passed; action-store tests
  11 passed; memory contract tests 5 passed; sync reserve regression 5 passed. Observatory browser tests
  require the running preview (`APP_URL`) and were previously verified separately. A fresh browser-suite
  attempt is unavailable in this environment because `.venv311` lacks optional `pytest-playwright`;
  this is an environment gate, not an application failure. The evidence integration expectation was
  reconciled with
  the intentionally safe HTML evidence viewer.
- Hardened the approval cleanup sweep to compare legacy naive and newer timezone-aware approval
  timestamps safely; added regression coverage for aware timestamps.
- Hardened the authenticated mutation endpoint to reject malformed JSON shapes before routing; added
  HTTP regression coverage for non-object bodies, params, and missing action types. Routing now also
  fails closed for a missing/non-string action type before provenance-specific branching.
- Docker Compose configuration validates successfully (`docker compose config -q`); the tested digest
  is still not deployed to the daily-use instance, so release remains owner-gated.
- Corrected provider synchronization to treat an explicit zero reserve as authoritative instead of
  retaining the prior local reserve; omitted reserves still preserve existing observations.


## Read-only constitution evaluator — 2026-09-10

- Added `meridian/policy.py` with typed `Constitution`, `ActionPlan`, and structured `PolicyDecision` models.
- Evaluation fails closed while inactive, reports rules/evidence/assumptions/confidence/recovery, and never approves or executes actions.
- Automatic actions without bounded limits are blocked; otherwise results remain `requires_approval`.
- Verification: `tests/meridian` passed 548 tests; Ruff and `git diff --check` passed. No policy activation or financial mutation occurred.
- Commits: `7a6c985` (implementation) and `23c03ae` (status/ledger documentation).

## Capture-contract harness — 2026-09-10

- Added pure capture metadata validation in `tests/browser/capture_contract.py` for the governed four viewport/DPR pairs, light/dark themes, and required deterministic fields.
- Added four contract tests covering the complete 8-state matrix, missing metadata, mismatched DPR/theme, and JSON-safe serialization.
- Documented harness usage in `docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md`. This changes no product behavior and does not regenerate visual baselines.
- Verification: capture-contract tests passed; Ruff and `git diff --check` passed.

## Capture-matrix runner — 2026-09-10

- Added `scripts/capture_meridian_matrix.py` to execute the full governed viewport/theme/DPR matrix and emit a validated metadata manifest.
- The runner explicitly configures reduced motion and theme, waits for network/fonts/data settlement, disables animations/transitions, and requires the fixture and frozen clock to be named.
- Existing approved baselines were not regenerated; no product behavior or financial data was changed.

## Deterministic capture-runner hardening — 2026-09-10

- The matrix runner now freezes browser `Date`, disables interval polling before application scripts load, and captures both initial viewport and full-page artifacts.
- Capture targets are restricted to isolated loopback previews, and workspace metadata maps to the governing Observatory concept filenames.
- Approved visual baselines were not regenerated; no product or financial behavior changed.

## Four-workspace invariant restored — 2026-09-10

- Removed Trials as a fifth primary workspace from `navigation.html`, `shell.js`, and `MERIDIAN_WORKSPACES` in `app.py`, restoring the governing four‑workspace invariant.
- Moved Trials into the **Settings** surface as a new `section=trials` entry, matching the precedent of Payday & Funding and Actions & Approvals.
- Repaired `index.html` structural corruption from commit `5ea003d`: removed the spliced Trials `<section>` and restored the Accounts workspace's `data-workspace-section="accounts"` element.
- Added `trials` to the Settings sections list in `app.py` and wired the partial + `trials.js` include into `settings.html`.
- The Trials capability (API, `trials.py`, `cancellation/` logic, deadline ledger) remains fully reachable at `/api/meridian/trials*` and via `/meridian/settings?section=trials`; no API surface or safety semantics changed.
- Verification: 13 checks pass in `tests/test_meridian_workspace_invariant.py`, including rendered-DOM parsing that proves the four workspace sections parse with intact attributes and no leaked tag syntax; 566 tests passed; Ruff and `git diff --check` clean.
- Negative control: reintroducing the corrupted markup fails 7 of those checks, confirming the guard has teeth.
- Commits: `dbdca2f` (code and regression tests), `7c4efab` (status record).

## Proactive financial weather slice — 2026-09-10

- Added `meridian/proactive.py`: a pure, read-only projection that groups near-term Observatory dial events and classifies a financial-weather `state` (`steady` / `tight` / `strained` / `unknown`).
- Noise control: each group is capped at three events and reports an `omitted` count; zero, duplicate, and unparseable events are suppressed and counted rather than rendered.
- Freshness behaviour fails closed: when dial freshness is not `fresh`, or the available balance is missing, the state is `unknown` at confidence 0.2 with the reason recorded as an assumption. Missing data is never treated as zero, and amounts are never added across currencies.
- Every state and group carries a plain-language explanation, and each event explains its own funding meaning.
- Exposed via read-only `GET /api/meridian/weather` (login required, `@_safe_read`), reusing `build_dial` so the dial stays the single source of dates and amounts. No UI, mutation, or authority change.
- Verification: `tests/meridian` 563 passed (12 new proactive unit tests plus API cases for auth, shape, invalid `as_of`, and zero repository writes on read); full suite 793 passed, 56 skipped, with the pre-existing `tests/test_capture_contract.py` environment gate unchanged; Ruff and `git diff --check` clean.
- Commit: `768c7e4`.

## Bill funding target respects an existing reserve — 2026-09-10

- Fixed D01 from the consolidated handoff. `meridian/funding.py::_commitment_target` returned a bill's full amount and ignored its reserve, so a bill with `amount=120.00` and `funded_amount=100.00` projected 120.00 more instead of 20.00 — over-allocating by 100.00 through `project_funding` (used by Plan and Payday).
- Bills now use the same remaining-target rule goals already used: `max(0, target - funded_amount)`, so a fully reserved bill projects nothing and an over-reserved bill can never produce a negative target or shortfall.
- `services/plan.py` keeps its separate full-target `_commitment_target` (it subtracts `funded_amount` itself) and is intentionally unchanged.
- Verification: RED->GREEN — three new tests in `tests/meridian/test_funding.py` fail against the previous behaviour and pass with the fix; `tests/meridian` 566 passed; Ruff and `git diff --check` clean.
- Commit: `44bf73b`.

## Honest Plan action-outcome rendering — 2026-09-10

- Closed A07 from the consolidated handoff. Plan previously treated every successful HTTP response as successful execution, hard-coded `data-state="ok"`, and could display `Executed (failed).` or `Deleted (failed).`.
- Added pure `static/js/meridian/action-outcome.js`; all four Plan mutation call sites now interpret the returned durable action state. `verified` is the only successful terminal outcome; `executed` / `executing` stay visibly pending verification; `failed`, `rejected`, `expired`, unknown, and uncertain outcomes fail closed with recovery guidance and no blind-resend copy.
- Destructive views refresh only after `verified`, never merely because the route was direct or HTTP returned 200. Uncertain failures preserve server detail and instruct the owner to read Crew state before trying again.
- Added the existing caution-token tone for pending action notes; no new visual component or design authority was introduced. No preview was running on port 8081, so this slice makes no browser-capture claim.
- Verification: RED->GREEN — three new tests failed before the helper/integration/style existed; Node exercises every durable state and source guards reject the old false-success copy; `tests/meridian` 569 passed; Node syntax, Ruff, and `git diff --check` clean.
- Commit: `57ba383`.

## Memory retains failed and uncertain action outcomes — 2026-09-10

- Closed A09 from the consolidated handoff. Memory management previously treated every HTTP-200 execute response as success: it wrote `executed`, removed the proposal row, hid the pending container, and refreshed Accounts without inspecting the durable action state.
- The execute response body now passes through the shared action-outcome interpreter. Only `verified` removes the row and refreshes memory. Failed, uncertain, rejected, expired, executing, executed, and malformed outcomes remain visible with honest recovery copy.
- The Execute control is disabled after a durable outcome, so failure/uncertainty cannot become a blind resend path; recovery routes through Actions & Approvals and Crew-state readback.
- Verification: RED->GREEN — three focused tests failed against the old behavior; focused source/integration coverage 11 passed; `tests/meridian` 572 passed; Node syntax, Ruff, and `git diff --check` clean.
- Commit: `72b6bc0`.

## Exact recorded action review details — 2026-09-10

- Implemented the recorded-detail half of A10 across the Settings history, Memory approvals, and the legacy account approval panel. Every surface now displays all stored operation parameters, including exact amounts, sources, destinations, memos, and nested fields.
- Added shared `action-review.js`: values are rendered with `textContent` only; secret-shaped keys are recursively replaced with `[redacted]`; no action data is inserted through `innerHTML`.
- Review truth fails closed. If a durable action does not contain reviewed before/after or preserved-field evidence, the surface says **not recorded** rather than inferring it from the rationale or requested parameters.
- Scope boundary: this does **not** close A12. Fresh base-state capture, source-version/precondition checks, conflict detection, and true before/after comparison remain separate work.
- Verification: RED->GREEN — four contract tests failed before implementation; focused action-history/memory/browser-source coverage 15 passed; `tests/meridian` 576 passed; isolated preview browser shell/smoke 18 passed; Node syntax, Ruff, and `git diff --check` clean. The temporary preview was stopped afterward.
- Commit: `f27f553`.

## Structured Crew write outcomes — 2026-09-10

- Closed the structured-outcome portion of A04. Crew connector failures no longer collapse into a generic executor exception: `blocked`, `rejected`, and `uncertain` classifications plus their sanitized messages now survive into the durable action result.
- Timeouts, unreadable connector responses, and connector-reported uncertainty are explicitly stored with `verify_state=true` and `retry_allowed=false`. The executor is invoked exactly once, no verifier runs after a failed result, and the owner-facing recovery path remains Crew-state readback before any new request.
- Scope boundary: this does not implement automated reconciliation, operation-specific provider readback, typed action input schemas, or A12 stale-base preconditions. No action authority, mutation registry, retry policy, or UI route changed.
- Verification: RED→GREEN focused connector/pipeline tests; 34 focused action/outcome tests passed; `tests/meridian` 581 passed; full suite 811 passed, 64 skipped; Ruff and `git diff --check` clean. Browser-only tests were collected but skipped without `APP_URL`; no UI changed. Independent read-only review reported no findings.

## Meridian identity on auth and first-run surfaces — 2026-09-10

Owner-reported symptom: the landing page and the installed Home Screen app showed
"SimpleCrew" again. Diagnosis found three separate causes, only one of which was in
ORSC's control:

1. **Port 8080 is not this build.** `docker ps` shows container `simplecrew`, image
   `simplecrewbranch-finance-app`, compose working directory
   `/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`, created 2026-09-06. Its
   `/login` is titled `SimpleCrew - Login`. Opening `localhost:8080` shows that other
   product, not ORSC Meridian. Stopping it is owner action outside this repository.
2. **`/login` renders `register.html` whenever the users table is empty**, so
   `register.html` *is* the first-run landing page. Commit `27db882` gave the Observatory
   treatment only to `login.html` and `index.html`, so every fresh database still landed on
   the untouched `SimpleCrew - Setup` page. This was an incomplete branding sweep, not a
   revert of earlier work.
3. **A stale cache kept the old name installed.** `static/sw.js` answered
   `/manifest.json` from a cache-first branch under an unchanged cache name
   (`simple-finance-v12`), so an installed app kept the previous product name even after
   the file was corrected.

Changes: `register.html` now uses the same approved Observatory treatment already applied
to `login.html` (identical `obs-shell`, obs tokens, card/field/button classes) with Meridian
copy; the `login.html` footer, `base.html`, and `onboarding.html` no longer carry another
product name; `static/manifest.json` is named Meridian with the Observatory background and
theme colors; `sw.js` now treats `/manifest.json` as network-first, bumps `CACHE_NAME` to
`simple-finance-v13` so existing installs drop the stale manifest, and uses Meridian push
defaults. Every register/login form id, name, autocomplete, placeholder, endpoint, payload,
and error path is preserved.

Verification: RED→GREEN — 13 guards in `tests/meridian/test_auth_branding.py` failed first
(wrong manifest name, SimpleCrew on all four templates, cache-first manifest) and pass now.
Rendered through the real first-run path with an empty database, `/login` returns
`Meridian - Setup`, `apple-mobile-web-app-title: Meridian`, **zero** `SimpleCrew` occurrences,
and `manifest.json` name `Meridian`. Full suite 826 passed, 64 skipped; Ruff,
`git diff --check`, `node --check static/sw.js`, and manifest JSON validation all clean.

Owner-visible remains:
- The running preview on port 8081 (`run_preview.py:46`, `debug=False, use_reloader=False`)
  caches Jinja templates in-process, so it will keep serving the old page until it is
  restarted. This is why the symptom persisted across previous fixes.
- An already-saved iOS Home Screen icon keeps its cached name; remove and re-add it once to
  pick up the new manifest.
- `static/js/app.js` console log strings still say SimpleCrew. They are developer-console
  text with no user-visible surface and are deliberately left out of this slice.

## Accepted is not verified for verifier-less operations — 2026-09-10

Finding A05 from the consolidated handoff: `crew/executors.py` substituted `{"ok": True}`
whenever an executor registered no verifier, so a provider acceptance was recorded as
`verified`. An audit of the live registry shows the scale of the overstatement —
**15 of 27 registered action types have no verifier at all**, including
`crew_initiate_transfer`, `top_up_crew_reserve`, `set_crew_spend_pocket`,
`create_crew_pocket`, both pocket-reassignment rules, the three paycheck-funding-plan
operations, `create_crew_virtual_card`, and the bill/pocket/rule create and archive
operations.

Change: a successful execution with no registered verifier now stays in `executed`
(verification pending) and records why, inside the durable result payload:

```
"verification": {"ok": null, "check": "no-verifier-registered", "reason": "..."}
```

Only a readback verifier may move an action to `verified`. The explicit-verifier path is
unchanged, a failing verifier still lands in `failed`, and a verifier that raises still
lands in `failed` with `verifier_exception`. `executed` remains non-claimable, so the
existing single-claim guarantee still prevents a second execution of the same action; a
regression test now pins that.

No authority, routing, retry, or mutation behaviour changed, and no new state or schema was
introduced — `executed` already existed and already rendered honestly. The UI needed no
change: `static/js/meridian/action-outcome.js` has treated `executed` as
"sent, verification pending, do not resubmit" since OS-007, and the memory/asset/contract
flows are unaffected because all six of those operations do register real verifiers.

Scope boundary: this makes the recorded outcome honest. It does **not** implement the
readback service that would later confirm these operations (handoff A15) or operation-specific
provider readback (A06), so a verifier-less action now stays `executed` until such a service
exists. That is the truthful state rather than a silent success.

Review consequence fixed in the same slice: `archive_crew_bill` is verifier-less, and its Plan
Delete control relied on `outcome.refresh` to reload the list and drop the archived row. With
that refresh now unreachable, the row would have stayed listed behind a live Delete button that
creates a **second** archive request. The bill-archive control now disables itself after a
durable outcome, exactly as the rule-delete control already did. A new guard test asserts that
every destructive Plan control refuses a second request, and a negative control (removing the
guard) makes it fail. This closes a widened resend path rather than shipping it as a side
effect of the truth fix.

Verification: RED→GREEN — 3 new executor tests plus 1 pipeline test failed before the change;
the one pre-existing expectation that a verifier-less `create_crew_pocket` reached `verified`
was corrected to `executed`. Full suite 832 passed, 64 skipped; Ruff, `git diff --check`, and
`node --check static/js/meridian/plan.js` clean.

Known follow-ups found by review, deliberately not in this slice: the recorded
`no-verifier-registered` reason is stored but not yet rendered in the Approvals history; and
`meridian/crew_write_actions.py::_verify_stored` still derives its result from local commitment
state, so the two `update_crew_bill*` types are not true provider readbacks either (handoff A06).

## Absent provider accounts are reconciled, not left frozen — 2026-09-11

Finding C02 from the consolidated handoff, with C04's rule applied: Meridian only
ever upserted the accounts a provider returned, so an account the provider stopped
returning kept `is_active = 1` and a frozen `source_updated_at` forever. Because
freshness is the oldest in-scope account observation, that single orphan pinned the
whole workspace to `stale` indefinitely while transactions stayed current. This was
not hypothetical: the owner's database holds one such row (a pocket Crew no longer
returns, last observed four days before its neighbours).

Change — reconciliation, deliberately **not** a weaker freshness rule:

- `absent_since` (migration 020) records the moment a complete read concluded an
  account is gone. The row keeps its history; it only stops being a current observation.
- `sync_provider` reconciles only when `snapshot.is_complete and errors == 0`, so a
  partial or errored read never concludes a deletion, and the scope is the reading
  provider's **own connection**, so another provider's accounts are never archived.
- `mark_absent_accounts` marks a row absent once (`absent_since` is set only where it
  is still null), so one observation cannot masquerade as a repeatedly refreshed fact.
- An account the provider returns again is reactivated and its absence evidence cleared.
- The freshness join no longer counts a concluded-absent account — in either direction:
  it can no longer pin the workspace stale, and it can no longer rescue it. A connection
  whose every account was archived therefore reports `stale`, and an unreconciled frozen
  account still pins `stale` exactly as before.
- `_reclassify_relations` no longer indexes the active-account map directly: an absent
  account keeps its row, so its historical transactions are still classified in the
  account context they were recorded under instead of aborting the sync.
- Account reads select only the columns the database actually has, mirroring the
  existing transaction-column tolerance, so a reader meeting a database that has not
  yet applied migration 020 does not fail.

No authority changed: this writes no provider state, adds no routing, retry, or mutation
path, and never deletes or restores anything. The owner's deleted pocket is **not**
recreated — its row is archived locally and its 19 historical transactions remain.

Verification: RED→GREEN — 12 tests in `tests/meridian/test_sync_reconciliation.py`
(the in-flight draft could not even collect: it had no `repository` fixture, and its
absence logic did not exist), plus 1 migration test that pins both account-column
tolerance branches on a database stopped before 020. Seven mutation checks confirm the
tests are load-bearing: removing the reconciliation call, the freshness exclusion, the
reactivation reset, the once-only guard, the completeness gate, the unmigrated-database
column filter, or the conditional absence reset each fails the tests that pin it. Full
suite 845 passed, 56 skipped, with the one pre-existing `playwright`-unavailable capture
test failing identically with this change stashed. Ruff clean on changed paths (the 7
reported findings are pre-existing, in `scripts/` and `tmp/pdfs/`), `git diff --check` clean.

Verified end to end on a **copy** of the owner's database with a live, complete,
read-only Crew snapshot (`complete: true`, `errors: 0`): Crew returned 6 accounts, one
local pocket was absent from that read, that pocket was archived with `absent_since`
while its 19 transactions stayed linked, no other account changed, and workspace
freshness moved `stale` → `fresh`. The real database was not modified and no
credential, token, or payload was logged.

Owner-visible consequence, and the next slice: `list_accounts` lists only current
accounts, so an archived account now correctly leaves the Accounts workspace and stops
counting in cash math. That is honest, but a silent disappearance is exactly the
experience the owner reported as data loss, so the archived row must be shown as
archived with its provenance rather than vanishing (OS-014).

Known follow-ups found while reviewing this slice, deliberately not fixed here:
`app.py::sync_crew_to_meridian` logs `report.accounts_upserted`, `report.transactions_upserted`
and `report.error`, none of which exist on `SyncReport`; the resulting `AttributeError` is
caught and printed as a sync failure even though the sync itself succeeded, so that path's
log is untrue. Absence reconciliation is implemented for accounts only — Crew bills and
other collections (C02's other half), C03's delete-reload, and C05's null-versus-empty
semantics are untouched.

## An archived account is reported, not silently dropped — 2026-09-11

OS-013 archived accounts a complete provider read concluded are gone, but
`list_accounts` returns only current accounts, so the owner's deleted pocket simply
left the Accounts workspace. That is correct for cash math — a withdrawn observation
must not count as current money — but a silent disappearance is the same experience
the owner reported as data loss. This slice makes the archived row visible with
provenance and, deliberately, without a current balance.

Change:

- `repository.list_archived_accounts(limit=50)` returns archived rows newest
  conclusion first, each paired with how many of its transactions survive. A
  database that has not applied migration 020 cannot have archived anything, so it
  reports none rather than failing on the new column.
- `build_accounts` reports an `archived` list (name, provider, account type,
  `absent_since`, `last_observed_at`, `retained_transactions`) **and no amount**: the
  last known figure is history, not a current balance. The list is bounded.
- `templates/meridian/partials/accounts.html` gains a "No longer returned" section
  that ships collapsed and empty, reusing the existing workspace section pattern
  (`section` + `h2` + `aria-labelledby`). It adds no interactive control at all.
- `static/js/meridian/archived-accounts.js` is a new pure module whose labels are
  executed by tests: `describeArchivedAccount` (provider no longer returns this
  account · last observed date · concluded absent date · N transactions kept in
  Activity) and `describeTransactionAccount` (the ledger label, marked when the
  account is archived).
- Activity now labels the account a transaction belongs to, in both the ledger and
  the Review card, and marks the ones whose account the provider no longer returns.
  This also removes a dead `transaction.accountName` reference that expected a field
  the API never sent. The API resolves `account_name` and `account_archived` from the
  account rows, including archived ones, so historical rows keep their account context.

No authority changed: nothing here mutates provider state, adds a control, or
introduces an approval/execution path. The archived row offers no action because there
is nothing the owner could safely change from it.

Verification: RED→GREEN — 11 tests in `tests/meridian/test_archived_accounts.py`
(6 of the 9 first-run tests failed on the missing read model, then the ordering test
was rewritten until a mutation could break it) plus 4 API/rendered-page tests in
`tests/meridian/test_api.py`. Mutation checks confirm the guards are load-bearing:
ordering by row id instead of conclusion time, rendering a balance in an archived row,
and dropping the ledger's account label each fail a test. Full suite 860 passed,
56 skipped, with the same pre-existing `playwright`-unavailable capture failure.
Ruff clean on changed paths, `git diff --check` clean, `node --check` clean on all
three touched modules.

Verified end to end on a **copy** of the owner's database with a live, complete,
read-only Crew snapshot: 6 accounts reported as current, 1 reported as archived with
`absent_since`, `last_observed_at` and **19 retained transactions**, no amount
exposed for it, its Activity label marked archived, and 0 current rows wrongly marked
archived. The real database was not modified; no credential, token, or payload was
logged, and the temporary copies were deleted.

Not verified here, and recorded rather than claimed: the browser/viewport pass for this
surface. `playwright` is unavailable in this environment, so `tests/browser/*` (including
`test_accounts.py`) skips and the pre-existing capture-contract test fails for the same
reason. The section reuses existing workspace markup and adds no interactive control, and
every label carries its meaning in text rather than by colour alone, but a real
viewport/contrast pass still has to run where the browser tooling exists.

Known follow-ups, deliberately not in this slice: an archived account's rows offer no
"view its history in Activity" control, because the Activity account filter is populated
from current accounts only and a filter entry for a non-current account would be
inconsistent; `transaction.accountName` was removed rather than aliased, so the ledger
sub-line now reads from the API's `account_name`; and absent-account reconciliation still
covers accounts only (Crew bills and other collections remain open under C02).

## The preview outage, its cause, and its repair — 2026-09-11

The preview app served 503 on every financial endpoint (Today, dial, Accounts,
memory) while `/api/actions/pending` kept returning 200. The log named the cause
exactly:

    meridian refresh failed: RuntimeError: Applied migration 020 has a name or checksum mismatch

`020_account_absence_reconciliation.sql` was edited *after* an earlier revision of it
had already been applied to the preview database `/private/tmp/gate-preview/gate.db`.
`meridian/db.py` keeps migration history append-only and refuses to run when an applied
migration's name or checksum no longer matches the file, so every `run_migrations`
call raised and every repository read failed. The guard did its job; the verification
that preceded the edit was wrong — it confirmed only that `savings_data.db` was still
at 019 and never checked the preview database, which is the one the running app uses.

Repair: `gate.db` was backed up to `gate.db.pre-020-checksum-repair`, then the recorded
checksum for 020 was reconciled to the current file **after confirming the schema effect
was identical** (`absent_since` present, `idx_financial_accounts_absent` present — the
two revisions differed only in comment text). Verified by readback: `run_migrations`
returns `[]` without raising, repository reads work, and the refresh log shows
`meridian refresh provider=crew status=complete accounts=6 transactions=100 errors=0`
with no further checksum errors. No other database carries 020 (`savings_data.db` is at
019; the 2026-08-30 production backup is unaffected).

Lesson, now a rule: **a migration file is immutable from the moment any database may
have applied it — including throwaway preview and `/tmp` databases.** Ship a new
migration instead of editing a shipped one, and when a shipped file does change, check
every database the app can reach before assuming the change is free.

Still outstanding because it needs a restart, not a code change: the preview process
started 2026-09-10 13:08 and therefore runs the code as it was before commits `9486820`,
`eef9ce0` and `0030ae9`. Until it restarts, absent-account reconciliation never runs, so
the orphan row keeps Today at `stale` pinned to 2026-09-07, and the Accounts "No longer
returned" section is not served (Jinja has the previous template cached).

Follow-up finding: the 503 body reads "Try again after your provider reconnects", which
misattributes a schema/migration failure to the provider. The message should distinguish
"we could not read your data" from "your provider is unavailable".

## A12 — an approved Crew write is refused when the reviewed state changed — 2026-09-11

The write-integrity gap from the handoff: an approved action carried only its
requested parameters, never the state the reviewer actually saw, and execution
claimed the action before comparing anything. A bill edited between approval and
execution — by another surface, an agent, or the sync cadence — would still receive
the approved write.

This slice makes the guard real for one operation, `update_crew_bill`:

- `action_requests` gains `base_state_json` (nullable, self-migrating); `propose`
  accepts a `base_state` captured by the proposal path from the same local record the
  reviewer's screen was rendered from (name and amount only, never a fabricated whole).
- `ExecutorSpec` gains an optional `precondition`, evaluated after the atomic claim and
  **before any provider call**. A mismatch refuses the action as `precondition_conflict`;
  a missing or unreadable reviewed state refuses as `precondition_unverifiable` (fail
  closed). The recorded outcome says `sent_to_provider: false`, `retry_allowed: false`,
  and `provider_truth: false` — it compares our own record, not a provider readback.
- Because `FAILED` is terminal, a refusal can never be retried or silently re-run.
- Wired to `update_crew_bill` only; the other 21 action types are untouched.

Non-goals, stated explicitly: this does **not** provide provider truth (A06 remains
open); it did **not** add a new action state (a refusal is a `failed` action with a
distinct error code); and it did not change the Plan UI, which already proposes with
the Crew bill id.

Verified RED→GREEN: 7 engine tests plus 4 wired-operation tests; neutralising the guard
turns 5 of them red (including "a changed bill is refused and never reaches Crew").
Full suite 875 passed, 56 skipped, with the same pre-existing playwright-unavailable
capture failure; Ruff and `git diff --check` clean.

## C06 — one canonical Crew connector — 2026-09-11

Handoff C06: two Crew adapters represented the same provider over the same account
id space under two connection identities. `CrewReadAdapter` (GraphQL client) wrote
connection `current-user`; `CrewWorkSnapshotAdapter` (read-only `crew-readonly` CLI)
wrote `crew-work-assistant`. If both ever ran, accounts would migrate connections and
the emptied connection would hold the whole workspace `stale`.

Decision (owner authorized): the canonical connector is the read-only CrewWorkAssistant
snapshot under `crew-work-assistant`. It is the only path that has ever produced data in
either database, and a read-only CLI fits the observe-never-mutate boundary better than a
bearer-token GraphQL client.

Change: `app.py::sync_crew_snapshot` now delegates to `meridian.live.sync_live_crew`, so
the cadence gate, the legacy `/api/savings` refresh, and the live loop all write the one
identity. The `CrewReadAdapter` and `sync_provider` module imports were removed from
`app.py` (`sync_provider` remains the sync engine inside `meridian/sync`, still used by
the snapshot adapter). `CrewReadAdapter` the class and `crew_client` the GraphQL client
are left in place — `crew_client` still serves the legacy savings read, the health check,
and session renewal; deleting them is a separate cleanup.

Verified: the routing test now asserts the legacy path calls `sync_live_crew` on the app's
DB, so a revert to the client adapter fails; the two tests that patched the removed
`sync_provider` name were repointed to the live seam. Full suite 875 passed, 56 skipped,
same pre-existing playwright-unavailable failure; Ruff and `git diff --check` clean.

## A06 — a Crew bill write is now verified against the provider, not local state — 2026-09-11

The verify leg of propose→approve→execute→verify was hollow for Crew bill writes:
`_verify_stored` re-read the *local* commitment and explicitly never failed an accepted
Crew write over local state, so "verification" could not actually verify anything.

`update_crew_bill` now verifies against a fresh Crew snapshot (`capture_crew_snapshot` →
`CrewWorkSnapshotAdapter`) and compares the requested `name` and `amount` (normalizing
cents↔dollars) against what Crew now reports:

- matched → `VERIFIED` (`provider_truth: true`);
- mismatch, or the bill is gone → `FAILED` (`verification_failed`, with `requested` and
  `observed` recorded, `provider_truth: true`);
- snapshot unreadable → stays `EXECUTED` (`verification pending`, `provider_truth: false`)
  — never VERIFIED, never FAILED, because Crew already accepted the write.

Engine: `execute_approved_action` now treats a verifier's `ok is None` as "verification
pending" via the new `ActionStore.record_verification_pending` (an in-place result note
with no state change), instead of `bool(None) → False → failed`. This generalises the
OS-012 no-verifier-registered honesty to "a readback ran but could not confirm."

Composes with A12: A12 refuses a write whose reviewed state changed *before* it runs;
A06 confirms the provider state *after* it lands. Scope is `update_crew_bill` only; every
other verifier is unchanged. A `FAILED` verification is terminal — no automatic retry.

Verified RED→GREEN: 1 engine test plus 3 wired tests (matched/mismatch/unreadable);
neutralising the `ok is None` branch turns 2 red, including "cannot be read stays
executed". Full suite 879 passed, 56 skipped, same pre-existing playwright-unavailable
failure; Ruff and `git diff --check` clean.

## C02 for bills — a complete Crew read now concludes absence for bills it stops returning — 2026-09-11

OS-013 reconciled accounts; bills were left unreconciled, so a Crew bill that disappeared
stayed a live obligation locally forever. This mirrors the account rule onto commitments.

Migration 021 adds `commitments.absent_since`. `CommitmentRepository.mark_absent_bills`
archives (and timestamps) this provider's bills that a complete read no longer returns,
scoped by `legacy_source` so another provider's commitments are never touched. The row,
its funded amount and its transactions are kept — absence is evidence about the local read
model, not a deletion.

Deliberate deviations from the account rule, both conservative:

- **An empty enumeration never concludes absence.** Unlike accounts (where an empty
  observed set archives everything in scope), a read that listed no bills at all is
  treated as an unreadable surface rather than "every bill disappeared".
- **The bill is archived, not left active.** Accounts carry `is_active`; commitments carry
  a lifecycle `status`, so absence sets `status='archived'` and `absent_since` together.
  `absent_since` is what distinguishes provider absence from the owner's own archive.

Re-observing a bill clears its absence and restores it to `active`, but only for rows that
were concluded absent — an owner-archived bill is never silently revived. Both upsert paths
are wired (`sync_live_crew` and `sync_providers`), gated on a complete, error-free read.

Verified RED→GREEN: 9 tests (repository scoping, idempotence, no-provider-identity,
reactivation, owner-archive protection, plus two end-to-end sync tests through the real
adapter); neutralising the completeness gate turns the incomplete-read test red. Full suite
888 passed, 56 skipped, same pre-existing playwright-unavailable failure; Ruff and
`git diff --check` clean. `tests/meridian/test_migrations.py` gained 021 in its expected
migration lists.

Companion slice still open: Plan-surface provenance for an absent bill (the OS-014 parallel),
so the owner can see *why* a bill they remember vanished instead of it silently leaving Plan.

## A bill the provider stops returning now stays visible in Plan — 2026-09-11

The OS-014 parallel for bills. OS-018 archives a bill a complete read no longer returns,
which meant it left Plan silently — re-creating, for bills, the exact experience the owner
reported as data loss. The read model now reports it with provenance instead.

- `CommitmentRepository.list_absent_bills(limit=50)` returns concluded-absent bills, newest
  conclusion first, bounded to 1..200 like the archived-account list.
- `build_plan` exposes `absent_bills` as `{id, name, provider, absent_since}` — deliberately
  **no amount and no funded figure**, because a last known figure is not a current obligation.
- `static/js/meridian/absent-bills.js` holds the label logic as pure functions
  (`describeAbsentBill`), so it is executed in tests rather than only asserted as text.
- `plan.js` renders a "No longer returned" section into `[data-absent-bill-list]`; the section
  is `hidden` until something is actually reported, so it cannot read as a permanent fixture,
  and the row carries no amount and no control.
- `templates/meridian/partials/plan.html` gains the section, mirroring the Accounts wording.

No backend latency cost: unlike the A06 readback verifier, this reads local rows only.

Verified: 10 Python tests (repository ordering/bounds, service payload, live-vs-absent
separation, template presence, renderer shape) plus one API-level test through the
authenticated test client, plus one Node test executing the label logic. Mutation check:
dropping the absence filter turns 2 red. Full suite 898 passed, 56 skipped, same pre-existing
playwright-unavailable failure; Ruff, `git diff --check`, `node --check plan.js` and a Jinja
parse of the partial are all clean.

**Verification gap, stated plainly:** no browser, viewport, contrast or accessibility check was
possible — `playwright` is not installed in this environment, so all 56 browser tests skip. The
section is verified at the payload, label and markup level only; it has not been seen rendered.

## C01 — an unreported reserve is no longer read as a zero reserve — 2026-09-11

`_cents_to_dollars` returned `0.0` for a missing field, so a bill whose `reservedAmount` Crew
never reported was indistinguishable from a bill whose reserve had been explicitly emptied.
Because `commitments.funded_amount` is `NOT NULL`, that conflated zero was then written on
every read — **erasing the amount Meridian last knew**. Same family of silent loss as the
deleted pocket, arriving through a different door.

Fix: a nullable `_cents_to_dollars_or_none`, used only for `reservedAmount`, so an absent field
stays `None`. Both upsert paths already handled `None` correctly (`else existing.funded_amount`
on update, `0.0` on create) and were simply never handed a `None` — so this one-line change
activates intent that was already written, rather than adding new behaviour.

Deliberately not changed: `amount` keeps the non-nullable helper. An absent `amount` still reads
as `0.0`, which local validation rejects *loudly* (bills require a positive amount) instead of
silently — and that loud failure aborts the whole refresh tick for one malformed bill. Recorded
as a follow-up rather than folded into this slice.

Also flagged, not fixed: `update_bill_reserve_settings` passes its payload straight to the
crew-write CLI and its parameter contract is **not documented** (only `TopUpReserve` is
catalogued), so I did not invent a fail-closed guard keyed on a guessed field name. The endpoint
has no UI caller today, so the risk is latent — but a guard must exist before any UI derives a
reserve value from local state.

Verified: 4 new tests (2 targeting the fix, 2 regression guards proving an explicit zero still
clears and a new bill still starts at zero) plus the existing provider tests; reverting the fix
turns the 2 target tests red. Full suite 902 passed, 56 skipped, same pre-existing
playwright-unavailable failure; Ruff and `git diff --check` clean.
