# Bounded handoff — Reserve Timeline (OS-116), for the DeepSeek Harness lane

**Authority.** Owner-directed, 2026-09-26. The owner selected **visual Option 2, "Pay-cycle Chapters"** and asked for
this bounded handoff to be given to DeepSeek Harness. Implementation is authorized **inside these boundaries only**;
anything outside them is not authorized by this file, and the owner's release gate still stands at the end (Task 5).

**Core rule, verbatim from the owner:** *"Implement a read-only child view reached from Plan. Preserve Crew's ordered
projection, same-day events, balances and provenance. Keep Current Allocation separate. Missing data stays missing;
forecasts never become observed balances. No new money model or financial write path."*

## Pinned state — read this before touching anything

| | |
|---|---|
| Meridian (ORSC) checkout | `/Users/stephenwest/Openrouter/simplecrew-latest`, branch `feat/meridian-implementation`, **pin to `dffd000`** |
| Meridian worktree warning | **6 files are modified by another lane and are NOT yours**: `docs/project/AGENT_COORDINATION.md`, `scripts/preview_observatory_dial.py`, `static/css/meridian/advisor.css`, `static/js/meridian/activity.js`, `templates/meridian/partials/accounts.html`, `templates/meridian/partials/plan.html`. Do not commit them, do not revert them, do not "tidy" them. Work from the pinned commit, and re-read a file before editing it. |
| Connector checkout | `/Users/stephenwest/Applications/CrewWorkAssistantOTP`, **pin to `bd7d8b1`** |
| Connector worktree warning | 4 modified files + `uv.lock` untracked, from another lane: `src/crew_work_assistant/auth.py`, `crewwrite.py`, `write_operations/top_up_reserve.graphql`, `tests/test_crewwrite.py`. Do not inherit, commit or revert them. |
| Shared-tree rule | `docs/project/AGENT_COORDINATION.md` — claim a row before editing, stage by path, never `git add -A`; release the claim on commit. |

## Selected visual reference (owner-gated, now decided)

- **Option 2 — Pay-cycle Chapters**: `design/reserve-timeline-2026-09-26/02-pay-cycle-chapters.png`
- Study manifest: `design/reserve-timeline-2026-09-26/manifest.json`
- Existing Timeline visual authority: `design/observatory-extension-2026-09-18/concepts/timeline.png`
- Existing visual build handoff: `design/observatory-extension-2026-09-18/BUILD_HANDOFF.md`
- Existing design tokens: `design/observatory-extension-2026-09-18/tokens.css`

**The studies are synthetic and are not screenshots of running software.** The spec's
§"Required corrections to the studies" (`docs/superpowers/specs/2026-09-26-reserve-timeline-design.md`, lines 64-73)
governs over the generated imagery, and applies verbatim to the selected option: title **Reserve Timeline** (not a
direction name); scope to one verified reserve and currency; **remove the generated "All accounts" control**; keep all
same-day events on their original dates; plot actual provider row coordinates with no smoothed line, invented dates or
even spacing implying elapsed time; render zero and negative balances accurately; internal transfers stay neutral, not
income-green; decorative moon/sun symbols must not imply day/night; shrink oversized header artwork before shrinking
body text; and all text and chart geometry must be real accessible UI, never a raster screenshot background. A
pay-cycle chapter boundary must **never be inferred from an unverified schedule**.

## Known gap — the captured projection query is NOT in any tree (resolve this first, do not invent around it)

Task 1 says: *"Inspect the actual captured `AutopilotReserveProjectionScreen` query, variable contract and units … Do not
invent a query from this plan's field inventory."* Verified 2026-09-26: **the query text exists in no readable tree.**
A workspace-wide search (`grep -rl "AutopilotReserveProjection|reserveProjection|ProjectionScreen"` across the Meridian
checkout, `/tmp`, and the read-only ChatGPT-side tree) returns only *references* — the task ledger, the generated
handoff, the plan and the spec. The connector carries **no** projection operation at all (0 hits for `projection`
anywhere in its `.graphql`/`.py`/`.md`; 15 read operations total).

What *is* recorded, and is the contract you may work from: OS-130's ledger entry — captured 2026-09-20 from the native
app (Banking → Autopilot → Plan reserve, mitmproxy with a trusted certificate reused, upstream TLS verification left
on, **no raw flows or scalar financial values saved**), independently **replayed through the Keychain-backed
connector**: HTTP 200, no GraphQL errors, `asOfDate` 2026-09-20, **452 rows to 2031-12-30**, dates nondecreasing, 132
rows with multiple events, every row amount equal to the sum of its event amounts, every balance reconciling to
opening plus cumulative row amounts, and `firstNegative` matching. The field inventory, nesting and units are recorded
there and in OS-059's evidence.

**Three permitted paths, in order of preference:**

1. **Ask for the captured document.** The owner holds it; one paste removes the risk entirely.
2. **Reconstruct and verify against the recorded replay properties.** Write the operation, replay it for the same
   `asOfDate`, and treat the recorded properties as the falsifier (452 rows, nondecreasing dates, row amount = sum of
   events, balances reconcile to opening, `firstNegative` matches). Any mismatch means **stop** and report — do not
   adjust the contract to fit the query.
3. **Proceed offline on the frozen synthetic contract.** Tasks 2, 3 and 4 can be built and tested against the synthetic
   fixture without a live feed. The plan is explicit that captured evidence can support offline contract tests but
   **cannot justify live availability**: if units or nesting cannot be established, the UI stays unavailable.

A reconstructed query that reproduces the recorded properties is evidence; a query that merely "looks right" is not.

## Files — exact, and nothing else

**Existing Meridian files the work touches or reuses** (all verified present at `dffd000`): `meridian/providers/crewwork.py`,
`meridian/sync.py`, `meridian/observations.py`, `meridian/bill_allocation.py`, `meridian/api.py`,
`templates/meridian/partials/plan.html`, `static/js/meridian/plan.js`, `static/css/meridian/plan.css`,
`scripts/preview_observatory_dial.py`.

**The plan creates** (all verified absent today): `meridian/services/reserve_timeline.py`,
`meridian/services/reserve_allocation.py`, `static/js/meridian/reserve-timeline.js`,
`static/css/meridian/reserve-timeline.css`.

**Tests to create or extend:** `tests/meridian/test_reserve_projection_ingest.py`,
`tests/meridian/test_reserve_timeline.py`, `tests/meridian/test_reserve_timeline_api.py`,
`tests/meridian/test_reserve_allocation_view.py`, `tests/meridian/fixtures/reserve_projection_synthetic.json`,
`tests/browser/test_reserve_timeline.py`.

**Existing tests to reuse while integrating:** `tests/meridian/test_bill_allocation_ingest.py`,
`tests/meridian/test_bill_allocation_store.py`, `tests/browser/test_plan.py`.

**Connector files** (`/Users/stephenwest/Applications/CrewWorkAssistantOTP`): read `WORK_PROJECT.md` and `README.md`
**first** — the connector has its own instructions and they win inside its repository. Then
`src/crew_work_assistant/client.py`, `operations.py`, `cli.py`, `tests/test_client.py`, `tests/test_operations.py`,
`operations/accounts.graphql`, `operations/autopilot.graphql`. Add a **read** operation only.

## Required reading (all verified present)

Spec, plan, the generated `HANDOFF.md`, `PROJECT_INSTRUCTIONS.md`, `CURRENT_STATUS.md`, `MERIDIAN_DECISIONS.md`,
`MERIDIAN_CONCEPTS.md`, `MERIDIAN_VISUAL_CAPTURE_SPEC.md`, and the task ledger `MERIDIAN_OS_TASKS.json` (read OS-116,
OS-059, OS-130 and OS-119). Read `AGENTS.md` at the checkout root before your first edit.

## Do not do — and do not ask for

- **No** credentials of any kind: no cookies, Crew tokens, JWTs, OTPs, `.env` files or Keychain contents.
- **No** live databases or raw financial captures; no live provider call in a test.
- **No** deployment, no production restart, no Crew mutation, no reserve top-up, no bill edit, no probe cleanup.
- **No** model-preset or routing changes, and no assumption that `rotation/auto` routes by task difficulty. Report the
  model, route and effort actually used rather than inferring them.
- **No** unrelated visual artifacts, and never the dirty worktree wholesale.
- **No** new financial authority, no local forecast standing in for a missing Crew projection, no sweep modelling, no
  observation-history or bank-cleanup change as part of OS-116.

## Evidence you must leave behind

- Commands with their **exit codes**, including skips. **A skipped browser test is never a pass** (the repo runs
  `.venv311/bin/python -m pytest`; a plain `python3 -m pytest` has no pytest installed).
- Path-scoped commits only, in the correct repository, with the task named in the message.
- For any provider-read acceptance: the installed connector version and the observation revision, **without raw
  financial values**. Synthetic acceptance is not live acceptance, and a built UI is not a working provider feed.
- What you could **not** check, stated explicitly. That section is the most valuable one you can write.

## Guards that will judge the work

`tests/test_slice_onset_ceremony.py` (an in-progress slice must declare its plan, model and why),
`tests/test_governed_write_routes.py` (no new ungoverned provider-mutating route; the declaration must be updated in the
same change), `tests/test_state_of_the_system.py` (the generated state document must be regenerated when code changes),
`tests/test_supersession_before_restore.py`, `tests/test_concept_coverage.py`, `ruff check`, and `git diff --check`.

## Stop and report rather than guess

Stop if units or nesting cannot be established, if a replay mismatches the recorded properties, if a change would need a
provider write, or if a shared file needs editing that another lane holds. Report the blocker with its instrument and
what you could not check — that is a successful outcome, not a failure. Task 5's independent review and the owner's
release gate are outside this handoff: you end at tested, committed, and evidenced.
