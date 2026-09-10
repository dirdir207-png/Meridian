# Trial Canceler / Meridian Sentinel — handoff

**Lane:** ORSC (`/Users/stephenwest/Openrouter/simplecrew-latest`)
**Branch:** `feat/meridian-implementation`
**Status:** implemented foundation, **committed but not yet shipped**
**Scope:** local-only trial ledger and cancellation workflow primitives

## What is valid and tested

This work is additive to Meridian's existing Flask/SQLite architecture. It does not
replace commitments, Crew writes, evidence, funding, or the existing proposal engine.
The Meridian API blueprint is already registered by `app.py`, so the new authenticated
routes are reachable when the running app uses this branch.

- `meridian/trials.py` — validated trial records, ISO-8601/timezone-aware terms,
  derived `cancel_by`, and deterministic T−7/T−3/T−1/deadline events.
- `meridian/cancellation/workflow.py` — pure state machine and routing guardrails.
  A click/request cannot become `Billing stopped`; that requires positive evidence.
- `meridian/cancellation/repository.py` — durable cancellation attempts in the same
  SQLite database, with legal transitions and evidence/status fields.
- `meridian/cancellation/recipes/catalog.py` — normalized merchant matching. Recipes
  without a valid `last_verified` date are non-executable.
- `meridian/migrations/016_trials.sql` and `017_cancellation_actions.sql` — append-only
  schema migrations.
- `meridian/api.py` — authenticated CRUD for trials and cancellation-action creation,
  listing, and state transitions.

Verification at handoff: `tests/meridian` **520 passed**; the repository suite currently
passes **728 tests with 64 skips**; targeted trial/cancellation, recipe, migration, and API
tests pass; Ruff passes for the new/changed code.

## What is *not* plugged in yet

Do not describe this as an autonomous canceler shipped to production. The following
remain intentionally absent:

1. No browser extension or local bridge; no merchant website is driven. The cancellation brief is now available as a read-only API response.
2. No scheduler invokes deadline events or creates cancellation actions automatically; `/trials/deadlines` is read-only.
3. No Gmail/Plaid/transaction ingestion creates trials automatically. The capture endpoint accepts explicit parsed terms only; it does not parse mail or browser traffic.
4. No recipe files are enabled for real merchants. Escalation planning is read-only and owner-led.
5. No evidence-ledger attachment adapter is wired to cancellation artifacts yet.
6. No UI surface has been added for trials/actions. Cancellation-action evidence can now link into the existing evidence ledger via the API.
7. No Crew virtual-card prevention flow is connected; no card mutation was executed. Post-deadline reconciliation now provides a conservative `billing_stopped` signal only when the sync window is explicitly complete.
8. The state machine records provider observations but does not itself verify a merchant.

## Integration contract for the next session

Use the existing repository factory/database path. Optional test injection points are:

- `MERIDIAN_TRIALS_FACTORY`
- `MERIDIAN_CANCELLATION_FACTORY`

Routes are under the existing `/api/meridian` prefix:

- `GET/POST /trials`
- `POST /trials/capture` (strict explicit-term capture; no inferred dates)
- `GET /trials/deadlines` (read-only deadline projection)
- `GET /trials/<id>/cancellation-brief` (read-only human handoff brief)
- `GET /trials/<id>/escalation-plan` (read-only owner-review channel ladder)
- `GET/POST /cancellation-actions/<id>/evidence` (existing evidence-ledger links)
- `GET/PATCH /trials/<id>`
- `GET/POST /trials/<id>/cancellation-actions`
- `POST /cancellation-actions/<id>/transition`

A transition to `verified` must include `billing_stopped` or `card_closed` evidence;
confirmation-reference evidence only yields `Acknowledged`. Keep this distinction when
adding UI, schedulers, browser adapters, or evidence links.

## Ownership / safety notes

This is a new domain alongside existing Meridian work, not a rewrite of another agent's
changes. Do not modify `/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`.
Before committing, inspect the dirty tree: the Observatory dial files and other
untracked design artifacts may belong to parallel work. Commit only the trial-canceler
files plus intentionally updated migration expectations and this handoff.
