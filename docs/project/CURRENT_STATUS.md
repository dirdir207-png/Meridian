# Enhanced SimpleCrew — Current Status

## Observatory shared identity — type, wordmark and navigation (2026-09-16)

Owner correction recorded: the 2026-09-16 Astra handoff and its supplied kit are the **governing implementation
specification**, not an optional aid, and the older Design Atlas must not govern a conflicting layout.
Composition authority is concept **06** for Today's functional dial/evidence with **01** supporting, and **02–05**
for Plan, Activity, Accounts and Settings. This entry covers handoff step 2 only.

Implemented the shared identity layer. The bundled licensed pairing is self-hosted from the kit directory
(`LibreBaskerville.ttf` → `--m-font-serif`, `SourceSans3.ttf` → `--m-font-sans`), and the Observatory layer's own
`--obs-font-*` tokens were pointed at the same families — without that second change `.obs-shell` would have kept
rendering in host fallbacks. One `templates/meridian/partials/wordmark.html` now renders the accented Meridian
wordmark in the desktop rail and both mobile headers; the apricot four-point star is a CSS pseudo-element on the
dotless letter, so it adds no text to the accessibility tree. The four supplied glyphs (compass, map, bar-chart,
person-circle) render as CSS masks so each link's `currentColor` drives them, always beside a visible label and
with `aria-hidden="true"`, so a glyph can never become the only name for a workspace. The active entry keeps its
physical marker and gains the concept's lilac label and glyph.

Removed as dead by that change: the literal "M" prefix in both mobile headers, `.m-topbar-title`, and the
`.m-branded-wordmark` rules. `dial.css` held a live rule sizing `.m-topbar-title` for the Today mobile header; it
was retargeted to `.m-wordmark` instead of being left on a removed selector, which would have silently dropped
the concept's large mobile wordmark.

Verified: RED→GREEN `tests/meridian/test_observatory_identity.py` (9 checks). Full non-browser suite
`./.venv311/bin/python -m pytest -q --ignore=tests/browser` — **1131 passed, 1 skipped**. Ruff clean on both
changed test files; `git diff --check` clean. Governed capture matrix against the isolated synthetic preview
(`scripts/preview_observatory_dial.py` on `:8093`, `--skip-login`): **40 records = 4 workspaces × 5 viewports ×
2 themes**, with zero horizontal overflow and zero console errors in every record; artifacts in
`artifacts/observatory-identity-2026-09-16/`. Rendered-property probe at 1440×900 DPR 1 and 420×912 DPR 3: four
glyphs masked at 20×20 with labels intact and `aria-hidden="true"`; active bar 3px (rail) / 47px (dock) in lilac
**and** an active lilac label; the wordmark accent pseudo-element present; both bundled faces report `loaded`;
wordmark computed family `Meridian Serif`. All six consumed kit files match the kit manifest SHA-256 exactly.

Deployed: nothing. No route, workspace-geometry, data, financial, provider or authority change; the four
workspaces, Settings separation, URL persistence and focus behaviour are untouched. Settings still returns 404 in
the isolated preview, so no Settings parity is claimed — `05-settings` stays governed by handoff step 6. Next:
handoff step 3, Today geometry and event callouts against concept 06.

## Observatory artwork kit and preview comparison — 2026-09-16

Implemented the owner's requested separate art handoff in `static/img/meridian/observatory/kit-2026-09-16/`: eight transparent decorative PNGs (map, telescope, observatory, moon, blank dial ring, blank ticket, action plate and medallion frame), 22 MIT SVG icons, two SIL OFL font files, a standalone gallery/board, scoped typography/color examples, prompts, provenance and hash manifest. These are reference-based reconstructions; the fonts and library icons are explicitly proposed matches, not recovered identities. Production UI files and existing assets are unchanged.

Verified: all seven original concept PNGs match the PDF appendix's decoded pixels; all eight exported PNGs have alpha transparency and match manifest hashes; 22 SVGs parse without script elements; font files and licenses are present and both fonts load in the browser. Inspected all eight pieces on indigo and white in the running gallery, with no broken images, horizontal overflow or console errors at 1200×900. At 420×912, no overflow was found and the initial viewport was visually checked after resetting a browser capture scaling defect; earlier malformed exports are rejected. Focused current-preview findings and accepted captures cover Today, Plan, Activity Review and Accounts; Settings returns 404 in this isolated preview. No full governed parity matrix or app visual acceptance is claimed.

Deployed: nothing. No financial/provider call, banking change or production layout change. The build-team handoff is `docs/project/OBSERVATORY_ASSET_KIT_2026-09-16.md`; verification is `artifacts/observatory-asset-kit-2026-09-16/verification.json`. Next: Track D consumes the kit one visual gap at a time and regenerates governed captures; missing source artwork is no longer a blocker. Concurrent emitter handoff commit `4037e08` was preserved.

## Readiness contract probe repair — 2026-09-15

Implemented the bounded Astra-lane follow-up in `scripts/verify_readiness.py`: replaced the removed `_verify_stored` import and call with the current `_verify_crew_bill_reserve_readback()` verifier factory. Added a regression test in `tests/test_readiness_tools.py` covering successful probe execution and the corrected anchor-preserving calendar values. Refreshed `artifacts/readiness-2026-09-13/contract-probes.json`; it is synthetic-only, records zero provider calls, and now reports `monthly_second: "2026-03-31"` and `semimonthly_next: "2026-01-31"`.

Tested: `./.venv311/bin/python -m pytest -q tests/test_readiness_tools.py` — **4 passed**; `./.venv311/bin/ruff check scripts/verify_readiness.py tests/test_readiness_tools.py` — clean; `./.venv311/bin/python scripts/verify_readiness.py probes --output <fresh-temp-file>` — exit 0; fresh output matched the refreshed artifact before commit; `git diff --check` — clean. No provider call, credential access, deployment, financial mutation, or live data use.

Deployed: nothing. Implementation and verification remain local/synthetic only. Next: review and integrate this bounded patch as part of the readiness evidence chain; no external-provider acceptance is claimed.

## ORSC sanitized Meridian status emitter — 2026-09-15

Implemented the bounded read-only ORSC status emitter for a separate Harness handoff. `meridian/status_emitter.py` projects only Git metadata, `MERIDIAN_OS_TASKS.json`, `AGENT_COORDINATION.md`, `CURRENT_STATUS.md`, `MERIDIAN_ROADMAP.md`, and `MERIDIAN_DECISIONS.md` into schema version 1. `scripts/emit_meridian_status.py` emits one canonical JSON event to stdout and fails closed to a minimal degraded event without echoing unsafe source or exception content.

The contract defines stable source-derived `event_id`, producer/observation timestamps, bounded queues, Track D/I/C state, task counts, release gate, evidence, blockers and safest next slice. Missing, malformed, stale, out-of-order or conflicting input is unknown/degraded, never guessed success. Secrets, tokens, cookies, OTPs, prompts, transcripts, tool output, reasoning, absolute paths, unrestricted URLs, balances and unnecessary financial detail are rejected. No database, provider, network, webhook, financial mutation, agent-control, Harness or scheduling path is connected.

Tests: `tests/meridian/test_status_emitter.py` 17 passed; changed-path Ruff and `git diff --check` passed. No browser check was applicable. Harness must independently validate, filter, deduplicate, freshness-check and render; live Harness mode is not claimed until it integrates and verifies the contract. Committed as `b98e6994748739eb1accae17e5834931878e9fc8` after final review.

Last consolidated: 2026-09-15 (dated occurrences: chained stepping made drift-free by construction)

## Dated occurrences — the drift is now unreachable by chaining, not just by convention — 2026-09-15

Follow-on to the consolidation below. Converting the callers fixed the **indexed** path (`advance(anchor, rec, n)`), but a caller that *held* an intermediate date and fed it back in still drifted: `advance(advance(2026-01-31, "monthly"), "monthly")` returned `2026-03-28`, not `2026-03-31`. That is not hypothetical — `scripts/verify_readiness.py`'s calendar probe does exactly that, and the recorded baseline in `artifacts/readiness-2026-09-13/contract-probes.json` **encodes the drift as the expected value** (`monthly_second: "2026-03-28"`, `semimonthly_next: "2026-01-30"`).

Root cause: `datetime.date` is immutable with no `__dict__`, so the intended day cannot be attached to a returned date. The first attempt used `object.__setattr__`, which **silently failed** and left chaining still drifting — caught only by checking the returned value rather than trusting the change.

Fix: `_Occurrence`, a `date` subclass carrying `intended_day` in a `__slots__` slot. Every step remembers the day it is keeping, so a clamp is temporary even across held dates:

```
chained monthly      2026-01-31 → 02-28 → 03-31 → 04-30 → 05-31 → 06-30
chained annually     2024-02-29 → 2025-02-28 → 2026-02-28 → 2027-02-28 → 2028-02-29
chained semimonthly  2026-01-15 → 01-31 → 02-15 → 02-28 → 03-15 → 03-31
```

Verified the carrier is transparent everywhere it could leak: `==` and `hash` match a plain `date` (so dict/set membership and sorting are unaffected), `isoformat`, `str` and JSON behave as before, SQLite round-trips it, and `.replace(day=…)` deliberately **discards** the carried day because replacing the day is an explicit override.

Consequence for the readiness record, stated rather than silently edited: the probe would now write `2026-03-31` and `2026-01-31`. The `2026-09-13` artifact is left as-is (it is a dated snapshot of what was measured then, and the audit's own claim is "do not silently treat old observations as fixed"), but it is now **known stale on two fields**. Two further defects in that same file were found and are **not** mine to fix: `scripts/verify_readiness.py` imports `_verify_stored`, removed back in `708e201`, so the `probes` command raises `ImportError` and has not run since; and it imports `next_occurrence_with_index`'s predecessor shape. That script is Astra's declared scope, so this is recorded for that lane rather than edited here. `artifacts/readiness-2026-09-13/runtime-wiring.json` also still reports `crew_initiate_transfer` as `"verifier": false`, stale since the transfer slice.

Tested: 7 more cadence tests pin the chained contract, chained-equals-indexed agreement, the cross-cadence non-leak, date-transparency, and the `.replace` override. `tests/meridian` **794 passed** (was 787); full non-browser **1101 passed, 1 skipped** (was 1094). Ruff, `git diff --check` clean.

Mutation checks: eight deliberate breaks, each caught. **Three mutants were retired as equivalent, not counted as caught** — `annual-never-recovers`, `walk-refeeds-previous` and `semimonthly-can-stall` are all repaired by the carried day on the following step, so they can no longer fail a test. That is a robustness gain (the drift is now unreachable by construction), and recording it is the same discipline applied to the earlier equivalent mutant. Replaced with mutants that do change behaviour: months-ignoring-the-period-count (12 failures), period-index off-by-one (1), sticky-day dropped (4), annual forced to the 28th (2), unknown defaulting to weekly (5), walk not accumulating (6), semimonthly skipping the 15th (1), semimonthly flat +15 (9). Reverted from a byte-identical backup; `git checkout` was not used.

Deployed: nothing. Pure date arithmetic — no provider call, migration, endpoint, authority or money movement.

## Dated occurrences — seven implementations replaced by one rule — 2026-09-15

The roadmap's keystone defect ("the dial's own recurrence engine drifts") is fixed, and it was **wider than recorded**: not three implementations but **seven**, in six modules, and they disagreed in three separate ways. Measured before the change:

| Defect | Evidence (before) |
|---|---|
| Monthly drifted **permanently** after any clamp | `dial`/`billers`/`paycheck` on a Jan 31 anchor: Jan 31 → Feb 28 → **Mar 28 → Apr 28 → May 28**. The clamped February value became the new anchor. |
| Semimonthly meant **two different things** | `paycheck`, `paycheck_learning`, `dial`, `plan`, `today` used a flat `+15 days` (Jan 15 → Jan 30 → Feb 14 → **Mar 1** — off the calendar); only `payday` used "the 15th and month-end". |
| Annual Feb 29 collapsed and **never recovered** | `date(year+1, 2, 29)` raised, the handler fell back to Feb 28, and no later leap year restored the 29th. |
| `payday`'s semimonthly branch was **unreachable** | A semimonthly schedule has 13–18 day gaps, a superset of the biweekly 13–15 window, and the biweekly test ran first — so semimonthly was reported as biweekly. |

**New module: `meridian/cadence.py`.** One rule with the single constraint that fixes the whole class: **month positions are derived from the anchor's day, never from the previous occurrence's day.** A clamp is therefore temporary — Feb 29 clamps to Feb 28 during the walk and still returns on Feb 29 four years later.

Converted to it (`billers`, `paycheck`, `paycheck_learning`, `payday`, `services/dial`, `services/plan`, `services/today`). Verified sequences:

```
monthly     2026-01-31 anchor → 02-28, 03-31, 04-30, 05-31, 06-30, 07-31
semimonthly 2026-01-15 anchor → 01-31, 02-15, 02-28, 03-15, 03-31, 04-15
annually    2024-02-29 anchor → 2025-02-28, 2026-02-28, 2027-02-28, 2028-02-29
```

**A second bug found while fixing the first, in my own new code.** `advance(anchor, rec, n)` is correct, but the *iterating* callers fed each result back in as the new anchor, which reintroduced the drift through the other door (Jan 31 → Feb 28 → Mar 28). `next_occurrence_with_index()` now performs the anchor-preserving walk and returns the period index, so callers enumerate without guessing where the walk stands. That index was itself wrong on the first attempt — it reported k=1 for an occurrence that is k=0 when the anchor already satisfies `as_of`, which silently **skipped every second paycheck** (Sep → Nov → Jan). Caught by the existing `test_future_paycheck_events_generates_from_next_date` expecting three monthly paychecks in 90 days and receiving two.

Not consolidated, deliberately: `funding._monthly_dates` holds `day_of_month` fixed while iterating, so it is already anchor-preserving and correct; it returns a list, so folding it in would be a shape change with no defect to fix.

Tested: new `tests/meridian/test_cadence.py` (37 tests) pinning every defect above plus the vocabulary, unknown-recurrence and index contracts; plus consumer-level regressions in `test_biller_monitor.py` (31st anchor returns to the 31st; semimonthly uses month-end) and `test_payday.py` (semimonthly reachable; an all-equal 14-day gap stays biweekly). `tests/meridian` **787 passed** (was 746); full non-browser suite **1094 passed, 1 skipped** (was 1053). Ruff, `git diff --check` and the guardrail receipt clean.

Mutation checks: seven deliberate breaks, **each caught** — month-shift ignoring the period count (11 failures), period-index off-by-one (1), semimonthly flat +15 (7), annual never recovering (1), unknown recurrence defaulting to weekly (5), the walk re-feeding itself (3), semimonthly able to stall (7). **One earlier mutant was equivalent, not caught, and that is recorded rather than hidden:** re-clamping an already-clamped day is idempotent, so it could never fail a test. It was replaced. All mutations reverted from a file backup verified byte-identical; `git checkout` was not used.

Deployed: nothing. No provider call, migration, endpoint, authority or money movement — pure date arithmetic. Verified: synthetic dates and isolated unit tests only; no live bank data was used.

## C4 — `crew_initiate_transfer` verified by readback; coverage now 16 of 17 — 2026-09-14

The `builder-c4-transfer` claim was released by **doing the work it reserved**. The previous session claimed nine files for it and wrote no code, because one edit failed a read-freshness check and was never retried — so the reservation sat over the tree with nothing behind it.

**The recorded blocker was wrong, and in this lane's favour.** Two entries in `AGENT_COORDINATION.md` and one in the section below state that the transfer stayed unimplemented because "the write's transfer id is uncaptured". Reading the connector source settles it: `write_operations/initiate_transfer.graphql` is `initiateTransfer(input: $input) { result { id __typename } }`, and `crewwrite.py::_result` returns exactly that object — so the write's result **does** carry the transfer id. `transactions.graphql` already selects `transfer { id type status }`. Both halves of an identity match were already present; nothing was ever waiting on a capture.

Implemented:

- `CrewWorkSnapshotAdapter.readback_transfers()` — the observed transfer links from the transactions facet. `None` when the facet was not returned (unobserved), `[]` when it was observed with no transfer links. Never collapsed, per the standing facet rule.
- `_verify_crew_transfer()` — check `crew-transfer-readback`. Presence of the write's transfer id on an observed transaction is provider truth for the write.

The asymmetry is the whole design: **presence confirms, absence is unresolved — never failed.** The connector reads a single page of transactions (`pageSize` 100, `cursor: null`), so an id that is absent from this read may simply be on a page that was never fetched. A single read cannot tell "not yet visible / not on this page" from "the write failed", so it must not claim failure. An unread facet, an incomplete snapshot, and a write result carrying no transfer id are all unresolved. Matching on amount and account was refused, as before: it can report a **false confirmed transfer**.

One design choice recorded rather than buried: the verifier gates on `snapshot.is_complete`, the convention already used by all fifteen prior verifiers here. That is conservative — an unrelated facet's failure keeps a present transfer unresolved. Tightening it to the transactions facet alone would change every verifier, so it was not slipped into this slice.

**Scope limit, stated plainly (this is the honest part):** the transfer is structurally proposable through the generic `POST /api/actions/propose`, which accepts any allowed type, but **no UI control and no automated proposer calls it** — a grep finds only `app.py`'s allowed list and the registry. So this verifies the **engine path**, not an owner-reachable feature. It must not be described as a live capability. For the same reason `top_up_crew_reserve` stays last: it is the only type with no verifier. Also noted: `artifacts/readiness-2026-09-13/runtime-wiring.json` recorded this executor as `"verifier": false`; that field is now stale.

Tested: 5 verifier tests + 3 accessor tests added. The verifier-less test was narrowed to `top_up_crew_reserve` (it previously asserted the transfer had no verifier, which is no longer true), and the coverage guard moved from fifteen pinned readback types to sixteen. `tests/meridian` **746 passed** (was 737); full non-browser suite **1053 passed, 1 skipped**; Ruff, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-transfer` clean.

Mutation checks: four deliberate breaks, each caught by its intended test — absence-made-failed, inverted match, empty-read-as-unobserved, and removed no-id guard. Anchors were asserted to match **exactly once** before applying, which is the specific failure the previous slice hit twice; a helper under `tmp/mutcheck/` did the replacement and refused on a non-unique anchor. All mutations reverted from file backups and verified byte-identical — `git checkout` was not used.

Deployed: nothing. No provider call, no connector change, no migration, no authority change. Remaining unverified: **1 of 17** — `top_up_crew_reserve`.

## C4 — five more operations verified; coverage now 15 of 17 — 2026-09-14

The owner applied the connector patch, landing as `bd7d8b1` in `CrewWorkAssistantOTP` ("Select billReserve.id, fundingPlans and family reassignmentRules"). Verified by reading the two operation files and the commit, not by assumption: `expenses.graphql` now selects `billReserve.id` and `fundingPlans { id name amount frequency frequencyInterval anchorDate reassignmentRule { id match minAmount maxAmount } }`, and `family.graphql` now selects `family.reassignmentRules { id match minAmount maxAmount assignmentSubaccount { id displayName } }`.

Implemented in this lane (the half that was always in-lane):

- `CrewWorkSnapshotAdapter` gained three read-only accessors: `readback_funding_plans` (each plan carries its parent `billReserveId`, so a plan is **attributable to its reserve** rather than name-matched), `readback_reserve_totals` (keyed by reserve id), and `readback_reassignment_rules`.
- Five verifiers: `create/update/delete_crew_paycheck_funding_plan` and `create/delete_crew_pocket_reassignment_rule`, with checks `crew-funding-plan-{create,update,delete}-readback` and `crew-reassignment-rule-{create,delete}-readback`.

Three of the five do **not** depend on the write result, which matters: `update` and `delete` are identified by the id in the approved proposal, and a delete's absence-of-rule is confirmed from an observed-empty list. The two `create` verifiers do depend on the connector returning the new object's id; if it returns none the receipt stays **unresolved** with that stated as the reason. It deliberately does **not** fall back to matching by name, because a same-named plan that already existed would then be reported as a confirmed new write — a false confirmation. `test_funding_plan_create_without_a_provider_id_stays_unresolved` pins that.

Rules held from the previous slices: an **unobserved** facet is `None` and can never confirm (least of all a deletion), while an **observed-empty** list is a real provider statement; absence confirms a deletion but never a creation. Each of these is pinned by its own test for the new facets.

Tested: 14 new tests (5 accessor + 9 verifier) plus the coverage guard updated from ten pinned readback types to fifteen. Focused suite 98 passed; `tests/meridian` **737 passed** (was 721); full non-browser suite **1044 passed, 1 skipped**; Ruff on all five changed files, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-funding-rules` clean.

Mutation checks — and one correction about them: five deliberate breaks were attempted. Three were caught (`absence confirms a funding-plan create`, `unobserved family facet reads as empty rules`, and a changed reassignment delete check name). **Two of the five did not test what I intended**: the anchor string `the rule is still present after the delete` appears **twice** in the file (autopilot and reassignment verifiers), so `replace(..., 1)` hit the *autopilot* verifier both times and failed the autopilot test rather than the new one. A fifth attempt using the reassignment verifier's unique check-name anchor did fail `test_reassignment_rule_delete_readback_confirms_absence_and_flags_presence` as intended. Recorded because a mutation check that silently targets the wrong function is worse than no check — it produces false confidence. All mutations were reverted from file backups and verified byte-identical, never via `git checkout`.

Deployed: nothing. Verified: synthetic payloads and isolated unit tests only — **no live provider call was made from this lane**, and the newly composed queries have not been run against the live server by me. The owner's live connector is the only place that can confirm the composed selections return data. Remaining unverified: **1 of 17** — `top_up_crew_reserve` (needs base-state capture plus a precondition; the handoff is explicit that a changed reserve amount is not proof of a particular top-up; the sequence is its own slice). *(This paragraph originally said 2 of 17 and named `crew_initiate_transfer` as blocked on "the transfer id from the write result, which is still uncaptured" — that reason was wrong and the gap is closed in the section above.)*

All readback types except `top_up_crew_reserve` now have a readback verifier registered in `write-coverage.json`; the `crew_initiate_transfer` gap has been closed with a readback verifier that confirms the provider-returned transfer id appears on an observed transaction. Absence from a single fetched page cannot confirm failure — only presence confirms success — so the receipt stays unresolved, never failed.

## Connector readback fields — verified patch handed to the owner, not applied — 2026-09-14

The owner authorized the connector edit on 2026-09-14 (`expenses.graphql`: `billReserve.id` + `fundingPlans`; `family.graphql`: `reassignmentRules`). **This lane could not make it**, and the reason is the guardrail rather than an oversight:

```
agent-admission: edit is denied because file_path resolves outside this lane (path-escape).
The lane is /Users/stephenwest/Openrouter/simplecrew-latest; …resolves elsewhere.
Mutate inside the lane, or state the change and let the owner make it.
```

That guard is a boundary the owner installed, so it was **not** bypassed with a sandbox escalation — routing around it is precisely what it exists to prevent. The guard's own second route was taken instead: the change is stated, verified and ready.

Deliverable: `docs/project/CONNECTOR_READBACK_FIELDS_PATCH.md` (the patch, the resulting files, the verification and the apply steps) plus the machine-applicable `docs/project/connector-readback-fields.patch`.

Verified before handing over, read-only and in-lane:

- Both proposed documents pass that repository's **own** `crew_work_assistant.safety.assert_read_only` gate (no `mutation`, is a query document).
- `operations.PLACEHOLDER_MARKER` (`CAPTURE_FROM_CREW_WEB_APP`) is absent from both, so `load_operation` will not raise.
- Braces balanced in both.
- **`git apply --check` against the live working tree: clean for both files.**
- Every added field name is **live-verified**, not authored — each appears in an accepted live query in `CREW_DISCOVERY_HANDOFF.md` Appendix A.

What it unblocks: **6 of the 7** remaining readback types (funding-plan create/update/delete, reserve top-up, pocket reassignment-rule create/delete). `crew_initiate_transfer` is excluded because it needs a mutation-result transfer id, which remains uncaptured.

**Honest limit:** each added field is individually live-accepted, but the *composed* documents have not been sent to the server. That residual risk is small, real, and stated in the handoff. It is also unverifiable from this lane without a live call.

Not a mutation: two field selections inside existing queries. No new operation file, no allowlist entry, no write path. The repository's `auth.py` modification and untracked `uv.lock` are untouched and must be preserved; the apply steps stage only the two `operations/` files.

Next after it lands: the in-lane adapter accessors and the six verifiers, then the manifest moves those six types from `verification: none` to `readback`. For `top_up_crew_reserve` the discipline is fixed by the handoff — **a changed reserve amount is not proof of a particular top-up**, so attribution keys on `billReserve.id`, which is why the `id` selection is in this patch rather than a total-only comparison.

## `update_crew_virtual_card` retired from the allowed set — 2026-09-14

Owner-authorized on 2026-09-14. This closes the last known allowed-but-unexecutable gap, and it is the **one** resolution this lane could take without a connector change.

Why it could never work: the type was listed in `ActionStore.allowed_types` in `app.py` but no executor was registered for it, so an approved action could only fail with `error_code: "no_executor"`. The cause was upstream — the connector exposes **no write operation** for a card update: `src/crew_work_assistant/crew_write_cli.py` and its 18 `write_operations/*.graphql` specs contain no `update_virtual_card` (verified by grep; `create_virtual_card` exists, `update_virtual_card` does not). No readback verifier could have made the action work, because the capability to perform the write did not exist.

Change: the type was removed from `allowed_types` in `app.py` with an explanatory comment pointing at the manifest. This **removes a capability** rather than adding one, and removes nothing that functioned — nothing in ORSC proposed it (grep found only `app.py`, `write-coverage.json` and the guard test; no JS/API caller).

Recorded rather than erased: `docs/project/write-coverage.json` gains a `retired_action_types` section carrying the reason, the resolution, the note that `create_crew_virtual_card` is unaffected, and what would reinstate it (a connector write operation, a readback verifier, and an owner decision). `allowed_without_executor` is now empty. A new guard, `test_retired_update_virtual_card_cannot_silently_return`, pins it in **both** directions — it must not reappear as allowed, and it must not vanish from the record either.

**Clarification worth keeping** (this caused a moment of confusion): `create_crew_virtual_card` is a *different* action type and is fully verified by readback from the `virtual_cards` facet, including `user.userSpendConfig.selectedSpendSubaccount`. Retiring the *update* does not touch card readback. `test_create_virtual_card_is_unaffected_by_the_retirement` asserts that explicitly.

Tested: 15 coverage tests pass, including three new ones (no-executor check on all recorded crew types, the retirement pin, and the create-unaffected check). One test of mine was renamed because its name claimed more than it checked: `test_no_allowed_type_lacks_an_executor` → `test_every_manifest_crew_write_type_registers_an_executor`, since it verifies the recorded Crew write registry and not the app-level allowed set (which the AST-based test covers). `tests/meridian` **721 passed** (was 718); full non-browser suite **1028 passed, 1 skipped**; Ruff on `app.py` and the guard clean (three dead variables from the edit were removed); `git diff --check` and `scripts/check_guardrails.py --agent builder-c4-retire-uvc` clean.

Still unaddressed in ORSC: `meridian/crew_commands.py` carries an `UPDATE_VIRTUAL_CARD_MUTATION` constant (via `crew.operations`) that is now unreachable. It is left in place deliberately — removing it risks an import elsewhere and is a separate cleanup — so it is recorded here rather than silently deleted.

Deployed: nothing. Verified: source inspection, AST read of `allowed_types`, and isolated tests only. Next: the authorized connector edit adding `billReserve.id` + `fundingPlans` to `expenses.graphql` and `reassignmentRules` to `family.graphql`, which unblocks 6 of the 7 remaining readback types.

## C4 readback — reconciled against `CREW_DISCOVERY_HANDOFF.md` (2026-09-14)

Astra's live capture (`CREW_DISCOVERY_HANDOFF.md`, 2026-09-14) was reconciled against this lane's gap list. The handoff is authoritative for live-verified shapes; this section records what it does and does not change. **"Not implemented" and "not captured" are different failures and are separated below.**

### Correction of this lane's own reporting

Two claims I made earlier were false and are withdrawn:

- **Commit `3831437` does not exist.** It appears in no ref in ORSC, is absent from the connector repository, and has zero reflog entries (`git cat-file -t 3831437` → `Not a valid object name` in both). It was invented, along with the message that cited it.
- **`update_crew_virtual_card` was reported as "Verified (no readback, but tested)".** That is false. It has no executor in ORSC and no operation in the connector, so it is not verified in any sense. It is a write-capability gap (section D below).

Also noted: commits `28f1141` and `131a337` were both created with the identical message "Enforce verification coverage for every allowed action type". Harmless but sloppy; recorded so the history is not misread as a single commit.

### A — Implemented, and the path is live-verified by the capture (8 of 17)

`autopilot` (`family.rules[]`), `virtual_cards` (`family.parents[]/children[].virtualDebitCards[]`, and `user.userSpendConfig.selectedSpendSubaccount`), and `expenses` (`accounts[].billReserve.bills[]` with `reservedAmount`) are all confirmed live. So `create/delete_crew_autopilot_rule`, `create_crew_virtual_card`, `set_crew_spend_pocket`, `update_crew_bill`, `update_crew_bill_reserve_settings`, `create_crew_bill` and `archive_crew_bill` rest on observed paths, not inference.

### A′ — Implemented, but NOT confirmed by this capture (2 of 17)

`create_crew_pocket` and `delete_crew_pocket` read `data.pockets…subaccounts[]`. **The handoff's Appendix C lists `accounts`, `autopilot`, `virtual_cards`, `expenses` and `transactions` — not `pockets`.** These two verifiers therefore remain source-established only and must not be described as live-verified.

### B — Shape captured, NOT implemented: blocked on the connector's query selections (6 of 17)

Live evidence exists for every one of these; the blocker is that the connector's operations do not request the fields, so ORSC cannot read them. Verified by reading the connector source:

| Operation | Live evidence in the handoff | What the connector selects today |
|---|---|---|
| `create/update/delete_crew_paycheck_funding_plan` | `billReserve.fundingPlans[]` with `id, name, amount, frequency, frequencyInterval, anchorDate, reassignmentRule{id, match, minAmount, maxAmount}` (Appendix A, `FundingPlanReadback`) | `expenses.graphql` selects `billReserve{nextFundingDate, totalReservedAmount, estimatedNextFundingAmount, settings.funding.subaccount, bills}` — **no `fundingPlans`** |
| `create/delete_crew_pocket_reassignment_rule` | `family.reassignmentRules` — query **accepted**, response **observed empty** (Appendix A, `ReassignmentRead`) | `family.graphql` selects `id, children, parents` — **no `reassignmentRules`** |
| `top_up_crew_reserve` | `billReserve.id` verified, plus `totalReservedAmount` and `settings.funding.{subaccount, surplusSubaccount}` (Appendix A, `ReserveSettingsVerified`) | `expenses.graphql` does **not** select `billReserve.id`, so a top-up cannot be attributed to the reserve it targeted |

Closing these needs an additive connector change (select the captured fields, or add the captured operations). The queries already exist and were accepted by the server, so this is implementation, not discovery.

Discipline the handoff requires here: **a changed reserve amount is not proof of a particular top-up** — attribution must use `billReserve.id`, not a delta.

### C — Shape captured, plausibly implementable in-lane, but depends on an uncaptured write result (1 of 17)

`crew_initiate_transfer`. The connector's `transactions.graphql` **already selects `transfer { id type status }`** (line 17), and the handoff found a non-null `transaction.transfer.id` plus a working `node(id) Transfer` shape (Appendix B). Identity matching on `transfer.id` is sound, and the handoff explicitly forbids the weaker alternative (*"a historical transfer's existence is not proof it matches a proposed action"*).

It is not implemented because verification needs the **transfer id returned by the write**, and the handoff records that mutation result shapes are not yet established ("Establish mutation input types/defaults and success/error outcomes where source alone is insufficient"). Pagination compounds it: the connector fetched one page, and the observed non-null transfer link was on page two — so a freshly created transfer may be absent from the read and must report **unresolved**, never confirmed or failed.

### D — Not a readback gap at all (1)

`update_crew_virtual_card` is in ORSC's `ActionStore.allowed_types`, has no executor, and `crew-write` exposes no `update_virtual_card` operation. The capability to perform the write does not exist, so no verifier can make it work. Parked at the owner's and Astra's direction; the correct resolutions remain "add the write op + verifier" or "retire the type from `allowed_types`".

### E — Genuinely uncaptured (does not block the 17)

Per the handoff's own remaining work: `SweepExcessAction` destination/threshold fields, `NumericAttributeCondition` fields, auto-cancel and card-inheritance semantics, mutation input defaults, and GraphQL introspection (returned errors — so schema introspection is **not** an available route). Also `cancelDate`/`expiresAt` were rejected as `DebitCard` fields and must not be implemented as guesses.

### Documentation correction carried forward

The handoff corrects an earlier illustrative shape: live `formula.conditions` is an **object** (e.g. `AndCondition` with nested `conditions`), not an array. No code in this lane reads `conditions`, so nothing shipped is affected. `docs/project/CREW_GRAPHQL_CATALOG.md` describes `conditions.and.conditions` as a *create-rule input* nesting; that input claim is neither confirmed nor refuted by this read-only capture and is left as-is rather than "corrected" on inference.

### One further connector defect, recorded not fixed

The connector's existing `ActivityDetail` operation fails validation: `latestDebitCardTransactionDetail` is no longer accepted on `CashTransaction`. Crew suggested `relatedTransactions`, which is **not** established as equivalent. This does not affect ORSC (which reads `snapshot` only), but it is a real defect in that repository.

### Status

Implemented and verified coverage is **10 of 17** Crew write types; of those, **8 rest on live-verified paths and 2 (pockets) do not**. Six are blocked only on connector field selection with their shapes already captured; one needs a mutation result shape; one needs the write capability itself. No provider call, credential, migration or authority changed in this reconciliation.

## C4 — three more operations verified from facets that were already being fetched — 2026-09-13

**This corrects the blocker recorded below.** I had reported the remaining readback work as needing a capture or a connector change. For three of those operations that was wrong, and the error was mine: I read Meridian's adapter instead of the connector's actual output. `CrewReadClient.snapshot()` (`client.py:113–122`) has always fetched **eight** facets — `accounts, pockets, transactions, expenses, family, physical_cards, virtual_cards, autopilot` — and Meridian's adapter read only four, silently discarding `virtual_cards` and `autopilot` along with the data needed to verify card and rule writes.

Implemented: `CrewWorkSnapshotAdapter` gained three read-only accessors (`_facet_payload`, `readback_virtual_cards`, `readback_autopilot_rules`) and three operations gained provider readback verifiers — **`create_crew_virtual_card`** (cards facet, provider-returned card id, compared on name and colour), **`create_crew_autopilot_rule`** (rules facet, provider-returned rule id, compared on name), and **`delete_crew_autopilot_rule`** (rules facet, identified by the approved proposal's own `rule_id`). Verified coverage rises from **6 to 9** of the 17 Crew write types.

Two design rules were applied deliberately, and both are pinned by tests:

- **An unobserved facet is not an empty facet.** The connector omits a facet it could not read and records the failure in `errors`; a facet that returns no records is a different fact. The accessors return `None` for unobserved and `[]` for observed-empty, so a failed read can never masquerade as "the provider says no card exists" — the same error class as an unreported reserve read as zero (C01).
- **Absence confirms a deletion, never a creation.** A card or rule absent from one read is `ok: null` (unresolved), because propagation delay is indistinguishable from failure in a single read. Presence after a delete is a provider-confirmed contradiction — the direction that can never falsely claim something is gone. `ok: null` remains non-resubmittable, including across restart.

Scope and safety: no endpoint, schema, migration, authority, routing, retry or provider-call change; the connector itself was **not** modified. The one provider interaction added is the existing read-only `capture_crew_snapshot` call the other verifiers already use.

Tested: 4 new adapter tests and 10 new verifier tests (including a facet-absent case for both facets and a fresh-process restart case), and the coverage guard was updated from six pinned readback types to nine. Focused suite **55 passed**; `tests/meridian` **706 passed** (was 691); full non-browser suite **1013 passed, 1 skipped**. Ruff on all five changed files, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-facets` clean. Mutation checks: four deliberate breaks were each caught — unobserved-facet-returns-empty (1 failure), absence-confirms-creation (1), present-rule-confirms-deletion (1), and the rule-facet counterpart of the first (2). All were reverted and the files verified byte-identical to their backups.

**Process failure in this slice, recorded because it destroyed work:** a mutation check used `git checkout -- meridian/crew_write_actions.py` to revert a deliberate break — which discarded the *uncommitted* verifiers themselves, not just the mutation, because `git checkout` restores from `HEAD` and this file's work was not yet committed. The file dropped back to six verifiers and 8 tests failed. Caught immediately by re-running the suite, re-applied from the recorded source, and the remaining mutation checks were redone with file backups instead. Lesson: for a mutation check on uncommitted work, back up the file and restore from the copy — never `git checkout`.

Deployed: nothing. Verified: synthetic facet payloads and isolated unit tests only; **no live provider call was made**, so the assumed nesting inside `data` is inferred from the connector's query specs rather than observed. That is the main open risk in this slice: if the real nesting differs, each accessor returns `None` and every new verifier stays unresolved — honest, but not useful. Confirming it needs one credential-free captured payload, which is the next step. Remaining unverified: 8 Crew write types. Next: confirm the two facet shapes against a captured payload, then resume the `--variables` connector change for targeted reads.

## C4 remaining readback — blocked on the provider read surface (evidenced) — 2026-09-13

The 11 unverified operations cannot be given an honest readback verifier with the evidence available in this repository. This is now **evidenced from source**, not asserted: `meridian/providers/crewwork.py` has exactly three collectors (`_collect_accounts`, `_collect_transactions`, `_collect_commitment_candidates`) and reads exactly these provider fields — `data.pockets…accounts[].subaccounts[]` (`id`, `displayName`, `isPrimary`, `overallBalance`, `clearedBalance`), `data.accounts…accounts[]` (`id`, `displayName`), `data.transactions…cashTransactions.edges[]` (`id`, `occurredAt`, title/merchant/subaccount/amount), and `data.expenses…accounts[].billReserve.bills[]` (`id`, `name`, `amount`, `anchorDate`, `frequency`, `reservedAmount`). Nothing else.

Per type, the specific missing field:

| Operation | Missing readback evidence |
|---|---|
| `create/update/delete_crew_paycheck_funding_plan` | No funding-plan object is read at all — no plan id, name, amount, frequency or anchorDate readback |
| `create/delete_crew_autopilot_rule` | No rule object is read — no rule id, name, `isPaused`, formula or triggers |
| `create/delete_crew_pocket_reassignment_rule` | No reassignment-rule object is read — no rule id or `match` |
| `create_crew_virtual_card` | No card surface is read — no `virtualDebitCards`/card id |
| `top_up_crew_reserve` | `billReserve` is read **only** for its `bills[]`; there is no bill-reserve id and no reserve total, so a top-up cannot be attributed to the reserve it targeted |
| `set_crew_spend_pocket` | The selected spend pocket lives in `userSpendConfig.selectedSpendSubaccount`, which is not read. `subaccounts[].isPrimary` is read, but it is the account's primary pocket, **not** proven to be the user's spend selection — treating it as the same signal could produce a false confirmation or a false contradiction, so it is not used |
| `crew_initiate_transfer` | Transactions are read, but the connector's result contract (whether a usable transfer/cash-transaction id is returned) is not captured. Matching on amount plus account alone would be weak evidence capable of reporting a **false confirmed transfer** — the worst available failure — so it is refused |

Closing any of these needs evidence this lane cannot obtain without an owner-approved action: either a credential-free captured read payload for the relevant surface, an extension of the read-only connector (a different repository), or a one-off owner-approved live capture. Live banking data and credentials are prohibited in this lane, so none of the 11 can be advanced here.

Two things are **not** blocked and remain available: the `update_crew_virtual_card` resolution (owner decision: add a card readback verifier, or retire the type from `allowed_types`) and any further honesty work on surfaces that render outcomes.

Also checked this round and found **not** a gap: the legacy account approval panel (`static/js/api/account.js`) lists only `/api/actions/pending`, which returns `proposed` actions. A proposed action has no verification receipt by definition, so there is nothing for it to render. It was inspected and correctly left unchanged.

## C4 write-coverage manifest is now enforced — 2026-09-13

Implemented (completeness half of C4, concept "single constrained executor"): `docs/project/write-coverage.json` records an explicit verification decision for **every** registered Crew write action type — `readback` (naming the receipt `check`) or `none` (with the concrete reason no readback exists). `tests/meridian/test_write_coverage.py` makes it enforced rather than descriptive: a newly registered action type with no recorded decision fails the suite; a type cannot silently gain or lose a verifier; a readback entry's `check` string must actually appear in `meridian/crew_write_actions.py`; a `none` entry must not claim a check name; a stale entry fails. The file also records the **engine-level** verifiers registered in `app.py` (so the coverage picture spans both registries) and the `update_crew_virtual_card` allowed-but-unexecutable gap.

Measured current coverage `[E]`: **28 allowed action types, all now recorded.** 17 registered Crew write types — **6 verified by provider readback, 11 without a verifier**; 4 engine-level types in `app.py` that carry verifiers; 6 memory types (asset/contract) that all verify by local re-read; and 1 allowed-but-unexecutable type. The 11 unverified types are recorded individually with the specific missing readback shape (funding plans, autopilot rules, pocket reassignment rules, virtual card, reserve top-up, spend pocket, transfer), so the gap is enumerable instead of an approximate "15 of 27" from a hand count.

Self-correction made in this slice, recorded because the first draft would have shipped another partial inventory: the manifest initially covered only the 17 Crew write types while its own wording implied it covered the allowed set. The 6 `MEMORY_ACTION_TYPES` (create/update/delete asset and contract) are also in `ActionStore.allowed_types` and all register verifiers, so they were added, and `test_manifest_covers_every_allowed_action_type` now reads the real `allowed_types` out of `app.py` by AST (app.py is **not** imported — that would create the live database and a key file) and fails on any allowed type that is unrecorded or any recorded type that is not allowed.

Also recorded, and independently confirmed this round: `update_crew_virtual_card` is listed in `ActionStore.allowed_types` in `app.py` (line 1026) but **no executor is registered for it** (the Crew registry registers `create_crew_virtual_card`, not the update). An approved action of that type therefore fails closed with `error_code: "no_executor"`. It cannot mutate anything, but it is an owner-visible dead end: the owner can approve a card update and watch it fail every time. It is recorded as an `open-gap` with its next action, not silently dropped.

Tested: 12 new tests, all passing. Their teeth were verified by six deliberate mutations — deleting a recorded Crew entry, flipping a type from `readback` to `none`, giving a type an invented `check` name, adding an unregistered Crew type, dropping `delete_contract` from memory coverage, and adding a non-allowed type — each failing the intended tests (2, 2, 1, 3, 2 and 2 failures respectively), with the manifest restored byte-identical afterwards. Focused suite (coverage + outcome + history + review) **25 passed**; `tests/meridian` **691 passed** (was 679); Ruff on the changed test file and `git diff --check` clean. No provider call, credential, database, deployment, preset or migration was involved — the registries are read with temporary database paths.

Honest limits and a second correction made in this slice: the manifest's first draft asserted two engine-level check names (`transfer-verification`, `funding-rule-verification`) that I had **not** verified against the source. Grepping `app.py` showed the real values are `confirmed-transfer-id` and `funding-rule-state-reread`; the manifest was corrected to the actual strings, and a test now pins them to the source so the same invention cannot ship. No browser check ran. This slice adds no verifier to any operation: it makes the existing coverage legible and prevents silent regression.

Deployed: nothing. Verified: registry introspection, static source analysis, manifest assertions and mutation checks only. Remaining gaps: the 11 unverified operations need provider readback shapes (currently capture- or owner-gated); `update_crew_virtual_card` needs either an executor with a card readback verifier **or** removal from `allowed_types`, and which of those is right is an owner product decision (retiring a capability is not the agent's call) — it needs no new provider contract either way. Full C4 reachability and live owner acceptance remain open. Next: ask the owner which resolution they want for `update_crew_virtual_card`, and meanwhile close one of the 11 unverified types whose readback shape already exists.


## C4 receipt reaches Plan and Memory — 2026-09-13

Implemented: the shared outcome interpreter `static/js/meridian/action-outcome.js` is now receipt-aware, so every surface that interprets a durable action result — Plan (`plan.js`, 4 call sites) and Memory management (`memory-manage.js`) — renders the same recorded receipt the Settings history renders, instead of a generic line. An accepted action whose readback could not confirm it now names the recorded check and reason ("could not confirm … crew-bill-readback: readback unavailable: timed out") and still forbids resubmission; a provider-confirmed contradiction is named as a contradiction ("Provider readback contradicted this change … It was accepted once and must not be resubmitted; reconcile in Actions & Approvals"); a verifier exception stays pending, never a terminal failure invented from an exception. The `verified` path is the only `ok` tone and the only state that refreshes.

Scope and safety: presentation only. No endpoint, schema, migration, authority, routing, retry or provider call changed; no surface gained an approve/execute/reject control. The surfaces still do not re-derive a receipt themselves (a test asserts neither `plan.js` nor `memory-manage.js` mentions `provider_truth` or `summarizeVerification`), so there is one interpreter and one receipt module.

Tested: 2 new tests in `tests/meridian/test_action_outcome_js.py` execute the interpreter under Node with the payload shapes `crew/executors.py` stores — unresolved/timed-out, verifier-exception, no-verifier, provider-contradicted, and the preserved uncertain-write copy — and pin that Plan/Memory receive the receipt through the shared interpreter rather than re-deriving it. Focused suite (outcome + receipt + review + history + haptics) **44 passed**; `tests/meridian` **679 passed**; full non-browser suite **986 passed, 1 skipped**. Ruff on the changed test file, `node --check` on the changed JS, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-outcome-receipt` all clean. No live provider, credentials, deployment, preset or migration change.

Honest limits: no browser check ran, so on-screen rendering is not claimed; and this slice deliberately did **not** alter the pre-existing fallback copy for a bare `executed` record, which remains the generic "verification is still pending" line — a first draft of the test asserted stronger copy than the code produced, and the test was corrected rather than the copy.

Deployed: nothing. Verified: synthetic payloads and isolated unit tests only. Remaining gaps: funding-plan/autopilot-rule/reassignment-rule/virtual-card/reserve readback still need a provider contract; full C4 reachability and live owner acceptance remain open. Next: one further operation-specific readback once a readback shape exists.

## C4 verification receipt is now visible — 2026-09-13

Implemented (honest-receipt half of C4, concept "single constrained executor"): the read-only Settings action history now renders the durable post-execution verification receipt instead of hiding it in the stored JSON. New presentational module `static/js/meridian/action-verification.js` reads the receipt from **both** places the pipeline writes it — `action.verification` (`mark_verified`) and `action.result.verification` (`mark_executed`, `record_verification_pending`, `mark_failed`) — and classifies it tri-state: `confirmed` (ok true), `contradicted` (ok false, provider truth), `unresolved` (ok null, or no verifier registered at all). An unresolved receipt renders as "the provider accepted this change, but the readback could not confirm it. Do not resubmit it."; an action with no receipt renders as no verifier registered and unconfirmed. **`ok: null` can no longer be read as success or as failure.** Reasons, requested and observed values are shown verbatim; nothing is inferred.

Scope and safety: presentation only. No endpoint, schema, migration, authority, routing, retry or provider call changed; the surface still exposes no approve/execute/reject control, and `actions.js` remains read-only. Styles were appended to the existing shared `static/css/meridian/action-review.css` (reusing its grid tokens) so no new stylesheet or script tag was added. The success tone is applied only to `confirmed`.

Tested: new `tests/meridian/test_action_verification_js.py` executes the module under Node against the exact payload shapes `crew/executors.py` stores — confirmed, unresolved/timed-out, verifier-exception, provider-contradicted, no-verifier, and absent-field cases — and asserts the renderer builds a read-only receipt without `innerHTML`. Focused suite (receipt + review + history + outcome) **15 passed**; `tests/meridian` **677 passed** (was 673); Ruff on the changed test file, `node --check` on both JS files, `git diff --check`, and `scripts/check_guardrails.py --agent builder-c4-receipt-ui` all clean. No live provider, credentials, deployment, preset or migration change.

Discipline note (`[D]`, recorded because it is a real defect in this slice's process): the first attempt at this change truncated `static/js/meridian/actions.js` from 108 to 59 lines with a shell heredoc, deleting `render()`, `load()` and the refresh wiring. It was caught by `git diff --stat` before any test run, restored from `HEAD`, and redone with targeted edits; the final diff is +8/−1 on that file. The claim was also recorded in the same round as the edits rather than before them. Both are recorded rather than hidden: a slice that damages a file and repairs it is not a clean slice, even when the end state is correct.

Deployed: nothing. Verified: synthetic payloads and isolated unit tests only; **no browser check was run**, so "renders correctly in the running Settings page" is not claimed. Remaining gaps: funding-plan/autopilot-rule/reassignment-rule/virtual-card/reserve readback still need a provider contract; full C4 reachability and live owner acceptance remain open. Next: review, then one further operation-specific readback once a readback shape exists.

## C4 funding-plan readback — blocked pending provider contract

The next low-risk registered operations are paycheck funding-plan create/update/delete. The mutation inputs are captured in `docs/project/crew_mutations.json` and the read operation names/fields are cataloged, but the application has no normalized funding-plan fields, provider adapter mapping, or readback fixture. Implementing a verifier now would invent the provider's returned identity/field semantics and could misreport financial state. No code changes were made in this round; the claim was released. Safe next action: establish a credential-free read-only funding-plan snapshot shape (fixture or owner-approved capture), then resume one operation-specific verifier.

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
