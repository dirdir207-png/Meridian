# Meridian Reserve Timeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development only when delegation is authorized. Steps use checkbox syntax for tracking.

**Goal:** Deliver OS-116's read-only Reserve Timeline over Crew's own projection and a separate observed-allocation view.

**Architecture:** Preserve the captured provider projection in the existing observation pipeline. A dedicated service validates and exposes immutable ordered rows; the Plan UI renders them without a second money model.

**Tech Stack:** Existing Python/Flask/SQLite, vanilla JavaScript/CSS, pytest and Playwright; no new runtime framework.

**Spec:** `docs/superpowers/specs/2026-09-26-reserve-timeline-design.md`.

**Status:** Draft planning deliverable, 2026-09-26, source inspected at `18737b0`; visual selection and implementation unapproved. Direction 1 is a recommendation, not an owner decision. No implementation tests below were run in this planning turn.

## Global Constraints

- No new financial authority.
- No local forecast may stand in for a missing Crew projection.
- Null stays null.
- Keep provider array order.
- Fixtures live only in synthetic previews/tests.
- No bank cleanup or observation-history retention change is part of OS-116.
- Scope to one verified reserve and currency.
- Use the canonical checkout/current branch and its coordination process; do not import the legacy recovery workflow. Preserve unrelated files and existing claims.

## Review Focus

1. Same-day events and repeated source IDs must survive grouping and chart selection (tasks 2, 4).
2. Missing/partial/stale snapshots must never become a zero balance or “covered” status (tasks 1–3).
3. Filtering a range or known experimental content must not leave contradictory balances (tasks 2, 4).
4. Allocation rows from different connection/reserve/capture/mode must never be merged (task 3).
5. Unknown types, HTML-like names, negative opening and disputed markers must remain honest and safe (tasks 2, 4).

## Delivery order and gates

Design selection → contract lock → connector OS-059 / mapping OS-130 → integration → browser acceptance → independent review → owner release gate.
Existing OS-130 dependency on OS-059 remains in force. Its captured-query evidence
can support offline contract tests before that gate closes, but cannot justify live
availability. Keep the sweep-threshold investigation separate; never model a sweep.
Only OS-116 planning has been requested here; do not launch agents from this document.

## Task 1 — Provider contract and immutable ingestion (OS-059/OS-130)

**Files:** inspect connector `/Users/stephenwest/Applications/CrewWorkAssistantOTP/src/crew_work_assistant/operations.py`, `client.py`, `cli.py`, `tests/test_client.py`; connector implementer must read its own instructions before edits. Meridian: modify `meridian/providers/crewwork.py`, `meridian/sync.py`; reuse `meridian/observations.py`; create `tests/meridian/test_reserve_projection_ingest.py`.

**Interfaces:** add `CrewWorkSnapshotAdapter.readback_reserve_projection() -> dict | None`. `None` means unobserved facet. Preserve a credential-free allowlisted payload as `ObservationObject(object_kind='crew_reserve_projection', external_id=reserve_id, ...)` in the existing `ActualSnapshot`. Metadata is the existing snapshot identity/time/mode, with explicit currency and reserve scope. No new mutable balance column.

- [ ] Inspect the actual captured `AutopilotReserveProjectionScreen` query, variable contract and units through OS-130's referenced evidence; record a sanitized contract table. Verify the connector method and exact facet path. Do not invent a query from this plan's field inventory.
- [ ] Write `test_missing_projection_is_unobserved`, `test_null_markers_preserved`, `test_projection_order_and_metadata_roundtrip`, `test_same_capture_is_idempotent`, and `test_partial_capture_does_not_publish_complete_projection`. Assert every field named in the spec is retained at its real nesting, null != zero, and secrets/raw envelopes never enter the stored payload.
- [ ] Run `.venv311/bin/python -m pytest -q tests/meridian/test_reserve_projection_ingest.py`; observe failures for absent behavior, not environment failures.
- [ ] Implement connector read-only operation and snapshot adapter; preserve OS-059/130 dependency boundaries. Wire both singular/plural sync paths, using the existing atomic publication boundary. Add synthetic connector transport tests in its own environment.
- [ ] Rerun focused tests plus `tests/meridian/test_bill_allocation_ingest.py`; verify exit 0 and no live connection. Review/path-stage and commit only this task's files in the appropriate repositories.

**Gate:** if captured units or nesting cannot be established, stop the connector change and keep the UI unavailable. Read-only provider acceptance is separate from synthetic tests and must record installed connector/version and observation revision without raw financial values.

## Task 2 — Projection normalization and service

**Files:** create `meridian/services/reserve_timeline.py`, `tests/meridian/test_reserve_timeline.py`, `tests/meridian/fixtures/reserve_projection_synthetic.json`.

**Interfaces:** define `normalize_projection(payload: dict, *, snapshot_id: str, reserve_id: str, connection_id: str, observed_at: str, currency: str, data_mode: str) -> dict` and `build_reserve_timeline(observation: dict | None, *, start_date: date, end_date: date, now: datetime) -> dict` in the new module. Inputs are credential-free stored data only. Output contract:

`{schema_version:1, status, provenance:'crew_estimate', data_mode, snapshot_id, reserve_id, connection_id, currency, observed_at, as_of_date, horizon_end, opening_minor, range_opening_minor, rows, low_point, first_negative, projected_nsf_date, reconciliation, issues}`.

Row: `{id, date, sequence, amount_minor, balance_minor, events}`.
Event: `{id, source_id, raw_type, kind, name, amount_minor}`.
Nullable fields stay null. Status is `available|empty|unavailable|partial|stale|invalid`;
issues carry stable codes. IDs use snapshot/row/event position, never source ID alone.

- [ ] Write the synthetic golden assertion: opening 40000; changes `[100000,-60000,-10000,-90000]`; balances exactly `[140000,80000,70000,-20000]`; second row children `[-45000,-15000]`. First three dates equal; final date later; no merge.
- [ ] Add `test_unknown_type_preserved`, `test_duplicate_source_ids_distinct`, `test_bad_group_or_balance_invalid`, `test_null_not_zero`, `test_negative_opening_not_hidden`, `test_unsupported_currency_unavailable`, `test_range_carries_preceding_balance`, `test_conflicting_markers_are_disclosed`, and `test_no_recurrence_invented_beyond_provider_horizon` with exact expected status/issue codes established in the fixture contract.
- [ ] Run `.venv311/bin/python -m pytest -q tests/meridian/test_reserve_timeline.py`; confirm the intended failures.
- [ ] Implement strict decimal conversion and validators, not forecast generation. Row/event indices preserve original order. Reuse existing freshness policy. Keep actual-input and estimate provenance distinct. Allocation estimates never enter opening balance.
- [ ] Rerun tests to exit 0; review and path-stage/commit this task only.

## Task 3 — Scoped allocation read model and authenticated APIs

**Files:** modify `meridian/bill_allocation.py`, `meridian/api.py`; create `meridian/services/reserve_allocation.py`, `tests/meridian/test_reserve_timeline_api.py`, `tests/meridian/test_reserve_allocation_view.py`.

**Interfaces:** add store `capture_allocations(*, provider: str, connection_external_id: str, bill_reserve_id: str, observed_at: str, data_mode: str='actual') -> tuple[BillAllocation,...]` without weakening existing methods. Add `build_reserve_allocation(allocations: Sequence[BillAllocation], *, reserve_total: Decimal | None, total_observed_at: str | None) -> dict` returning `{status, observed_at, reserve_total_minor, rows, reconciliation, issues}`. Each row preserves reported flag, nullable observed amount and separately labelled next-funding estimate.

GET `/api/meridian/reserve-timeline?reserve_id=...&start=YYYY-MM-DD&end=YYYY-MM-DD` and GET `/api/meridian/reserve-allocation?reserve_id=...&observed_at=...` use existing login/safe-read patterns. Resolve connection from authorized reserve identity, not a caller-supplied cross-account ID. No POST/PATCH/DELETE routes. Use latest complete scoped stored observation; no provider call on page render.

- [ ] Write API tests: unauthenticated request uses existing denial behavior; invalid dates/ranges return 400; unknown scoped reserve 404; unavailable observation returns typed unavailable without zeros; last success remains stale after refresh failure. Test a valid empty feed separately.
- [ ] Write allocation tests: two connections/reserves at the same timestamp never mix; simulated rows excluded; reported 0 survives; missing stays null; different total timestamp yields incomplete reconciliation; differing parts/whole yields discrepancy. A sum of observed parts is not an observed total when the bucket total is absent.
- [ ] Run `.venv311/bin/python -m pytest -q tests/meridian/test_reserve_timeline_api.py tests/meridian/test_reserve_allocation_view.py`; confirm intended failures.
- [ ] Implement store filtering/services/routes using a temporary DB and synthetic authenticated app fixture. Never import `app` with its default/live database: app import initializes it. Retain exact observation identity in responses; do not auto-join latest-per-bill captures.
- [ ] Rerun focused tests and `tests/meridian/test_bill_allocation_store.py` to exit 0. Review and path-stage/commit only scoped files.

## Task 4 — Selected design in Plan

**Files:** modify `templates/meridian/partials/plan.html`, `static/js/meridian/plan.js`, `static/css/meridian/plan.css`; create `static/js/meridian/reserve-timeline.js`, `static/css/meridian/reserve-timeline.css`, `tests/browser/test_reserve_timeline.py`; update `scripts/preview_observatory_dial.py` only to add matching synthetic read routes/fixtures.

**Interfaces:** `mountReserveTimeline(root, {fetchProjection, fetchAllocation}) -> {destroy()}` exported by the new module. Fetch functions consume task 3 URLs/contracts; UI never recomputes money. Render exact provider balances and parent-child totals. Escape names through textContent. Cancel stale requests on range/reserve changes and on destroy.

- [ ] Confirm the owner-selected image and written corrections; no visual choice is inferred from the recommendation.
- [ ] Add browser tests: repeat-date ordering; group disclosure exact totals; chart-to-row selection and keyboard equivalent; forecast/allocation separation; range carry-forward; selected snapshot stable during expansion; loading/empty/stale/unavailable/invalid; malicious-looking names render as text; no write requests; simulated banner and known experiment warning suppress reassurance.
- [ ] Run `.venv311/bin/python -m pytest -q tests/browser/test_reserve_timeline.py` with the documented isolated preview fixture. Confirm failures from missing UI, not missing server.
- [ ] Implement selected layout using existing tokens/assets, mobile sheet/desktop inspector and accessible disclosure controls. No enabled Meridian simulation tab or new monetary action. If experiment provenance is unavailable, disclose that clean-data verification is incomplete; do not implement a name-prefix filter.
- [ ] Rerun browser tests, `tests/browser/test_plan.py`, and service/API tests. Capture light/dark at 390×844, 420×912, 430×932 (DPR 3), 1024×768 and 1440×900 (DPR 1), fixed clock, fonts ready, no polling/animation. Verify 200% zoom, focus, no overflow/dock collision. Save exact commit/fixture/theme/state metadata and compare with selected study plus written corrections.
- [ ] Review and commit intended files only after passing gates. Test real Flask route integration as well as synthetic-preview rendering; a preview-only route is not product integration.

## Task 5 — Review, release and evidence

- [ ] Run focused suites above, repository-required lint and `git diff --check`; record commands, final exit codes and skips. Do not promote skipped browser tests to passes.
- [ ] Obtain independent high-reasoning review of identity scoping, units, provenance, partial captures and absence of provider-write access. Mark pending if no independent reviewer can run.
- [ ] Update OS-116 and OS-130 evidence separately. A built UI is not a working provider feed; synthetic acceptance is not live acceptance.
- [ ] With release authorization, deploy the tested commit through the existing launcher, verify process restart/serving revision and installed connector version, then navigate Plan → Reserve Timeline → expand group → Current allocation on the owner's actual phone path. No transfer/top-up/bill edit required.
- [ ] Record rollback to the previous tested application version; new observations remain preserved. Keep unavailable state on connector failure. Update current status, session-emergent record and generated handoff; run `scripts/roadmap_handoff_check.py`.

## Conditional DeepSeek Harness execution strategy

No Harness agents were launched in this planning turn. Installed-source inspection
alone cannot certify a healthy authenticated parallel runner; no callable Harness
dispatch connector is exposed in this session. The following is an execution plan,
not a claim that jobs are running.

After contract and visual approval, an integrator owns shared files and release:

| Lane | Bounded responsibility | Parallel boundary |
|---|---|---|
| A | Task 1 connector/ingestion | Can overlap B/C after contract lock; coordinate separate connector repo |
| B | Tasks 2–3 service, scoping and API | Own all shared `api.py`, sync/store integration via integrator |
| C | Task 4 UI against frozen synthetic contract | Own new UI files; queue shared Plan-file edits for integrator |
| Review | Task 5 review | Begins only after integrated evidence exists |

Check Harness health/auth with a harmless nonfinancial smoke, inspect supported
agent dispatch, and verify each worker's allowed paths before launching. Do not
change presets or assume `rotation/auto` routes by task difficulty. Suggested
reasoning: stable high-reasoning model for contracts/arithmetic/review; Sol/high for
UI integration per roadmap, configured available fallback for mechanical tests.
Actual route/effort and usage must be reported, not inferred. If parallel dispatch
is unavailable, execute tasks 1–5 serially with the same gates. Each worker gets
only spec, assigned task, frozen synthetic contract and exact source files—no live
payloads or credentials. Shared-tree rules prohibit concurrent edits to the same
files. No workers may deploy, change authority, mutate Crew, or clean up probes.

### Copyable Harness handoff

Read AGENTS.md and the generated HANDOFF in the canonical Meridian checkout.
Review OS-116 and OS-130 with the 2026-09-26 Reserve Timeline spec and plan.
Do not start implementation until the owner selects a displayed design and approves
the plan. Preserve OS-130's OS-059 dependency. Use Crew's captured projection feed;
keep ordered same-day events, exact group totals, provider running balances and
source age. Current allocation is a separate coherent dated observation. Missing
is not zero and estimates are not observed money. No financial write, credential
change, cleanup, deployment or model-preset change is authorized by these files.
If authorized parallel workers are available, assign nonoverlapping lanes A/B/C
only after locking the shared contract; otherwise use serial execution. Record
actual tests, commits, serving version and limits rather than declaring parity
from the presence of a chart.

## Planning self-review

Spec coverage: source contract task 1; money/provenance/range semantics task 2;
allocation/auth task 3; interaction/visual/failure states task 4; actual serving-path
acceptance task 5. All five review risks have owning tests. Shared files have one
integrator. No first-slice local forecasting or write scope. Independent review,
visual selection, connector acceptance and production verification remain open.

## Planning validation — 2026-09-26

Passed: roadmap/ledger reconciliation (`python3 scripts/roadmap_handoff_check.py`),
JSON parsing, existence of all 13 referenced existing Meridian integration/test
paths, placeholder scan, synthetic-image PNG signatures, and `git diff --check`.
The task-ledger edit was checked semantically: only OS-116's new evidence reference
changed. Written self-review corrected the adapter name to
`CrewWorkSnapshotAdapter` and recorded generated-image/date/scoping corrections.
No application suite or live acceptance was run: there is no product implementation
in this deliverable. Independent review is unperformed.
