# Agent coordination

**Purpose:** more than one agent works this lane. There is no lock and no channel, and the hazard has already
materialised twice — one agent's uncommitted work sat while another committed, and a stale preservation patch
would have reverted three commits had it been applied. This file is the channel.

**Canonical repo:** `/Users/stephenwest/Openrouter/simplecrew-latest` · **branch:** `feat/meridian-implementation`
· **the only tree** — everything else on disk is an unversioned snapshot and must not be worked in.

## Rules

1. **Claim before editing.** Add a row to the claims table naming the files you are about to touch.
2. **Release on commit.** Remove your row and record the commit SHA in the log below.
3. **Never commit another agent's uncommitted work.** Run `git status` first and stage explicitly by path —
   never `git add -A` or `git commit -a` in a shared tree.
4. **Never apply a stale patch or copy.** Check it against current `HEAD` before trusting it; a snapshot of
   someone's in-progress work can revert their finished work.
5. **Handoffs state state, not intent.** Say what is verified, what is not, and what the next agent must not
   assume. "Done" without a test result and a commit SHA is not done.
6. **Leave private harnesses out of it.** If only you can run your capture harness, it is not evidence.

## Current claims

| Agent | Files claimed | Since | Status |
|---|---|---|---|
| Builder (this lane) | `docs/project/*` (roadmap, plans, decisions, claims, coordination), `scripts/check_guardrails.py`, `tests/test_check_guardrails.py`, `tests/test_concept_coverage.py`, `AGENTS.md`, `.dockerignore` | 2026-09-13 | active; **not** touching dial/Today or `meridian/cancellation/` |
| Astra | `scripts/verify_readiness.py`, `tests/test_readiness_tools.py`, `docs/project/MERIDIAN_READINESS_AUDIT.md`, `docs/project/MERIDIAN_EXECUTION_GAMEPLAN.md`, `artifacts/readiness-2026-09-13/**` | 2026-09-13 | **released** at `648be9f`; retained as a declared-scope record, not a work lock (Astra's own wording) |
| Builder (C4 create readback) | `meridian/crew_write_actions.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-13 | **released** at `41387f5`; retained as a declared-scope record |
| Builder (C4 pocket readback) | `meridian/crew_write_actions.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-13 | **released** at `c027d1d`; retained as a declared-scope record |
| Builder (C4 delete-pocket readback) | `meridian/crew_write_actions.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-13 | **released** at `a96182a`; retained as a declared-scope record |
| Builder (C4 verification receipt) | `static/js/meridian/action-verification.js`, `static/js/meridian/actions.js`, `static/css/meridian/action-review.css`, `tests/meridian/test_action_verification_js.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-13 | **released** at `4bf6c86`; retained as a declared-scope record |
| Builder (C4 write coverage) | `docs/project/write-coverage.json`, `tests/meridian/test_write_coverage.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-13 | **released** at `131a337`; retained as a declared-scope record |
| Builder (C4 existing-facet readback) | `meridian/providers/crewwork.py`, `meridian/crew_write_actions.py`, `tests/meridian/providers/test_crewwork.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/write-coverage.json`, `tests/meridian/test_write_coverage.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-13 | **released** (commit in the 09-13 readback series); retained as a declared-scope record |
| Builder (C4 funding rules) | `meridian/providers/crewwork.py`, `meridian/crew_write_actions.py`, `tests/meridian/providers/test_crewwork.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/write-coverage.json`, `tests/meridian/test_write_coverage.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-14 | **released** at `daf8d33`; retained as a declared-scope record |
| Builder (C4 transfer readback) | `meridian/providers/crewwork.py`, `meridian/crew_write_actions.py`, `tests/meridian/providers/test_crewwork.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/write-coverage.json`, `tests/meridian/test_write_coverage.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-14 | **released** at `81892eb`; `crew_initiate_transfer` readback verifier; coverage 15 → 16 of 17. The row was released by doing the work it reserved, not by dropping it. No connector change, provider call, migration or authority change. |
| Builder (C4 funding rules) | `meridian/providers/crewwork.py`, `meridian/crew_write_actions.py`, `tests/meridian/providers/test_crewwork.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/write-coverage.json`, `tests/meridian/test_write_coverage.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-14 | **released** at `daf8d33`; retained as a declared-scope record |
| Builder (C4 transfer readback) | `meridian/providers/crewwork.py`, `meridian/crew_write_actions.py`, `tests/meridian/providers/test_crewwork.py`, `tests/meridian/test_crew_write_actions.py`, `docs/project/write-coverage.json`, `tests/meridian/test_write_coverage.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-14 | **released** (commit in this slice); `crew_initiate_transfer` readback verifier; coverage 15 → 16 of 17. No connector change, provider call, migration or authority change. |
| Builder (dated occurrences) | `meridian/cadence.py` (new), `meridian/billers.py`, `meridian/payday.py`, `meridian/paycheck.py`, `meridian/paycheck_learning.py`, `meridian/services/{dial,plan,today}.py`, `tests/meridian/test_cadence.py` (new), `tests/meridian/test_biller_monitor.py`, `tests/meridian/test_payday.py`, status/coordination/claims | 2026-09-15 | **released** (commit in this slice); consolidated seven divergent recurrence implementations onto one anchor-preserving rule; pure date arithmetic, no authority or money movement |
| Astra-H (Harness-side, gameplan H) | `tools/agent-presets/meridian-constitutional-builder/**` (new canonical preset source), a claim row + log entry in this file | see log | active. Harness code lives in the Harness repo and is **not** claimed here. Does **not** write `agent-claims.json` — the plugin only reads filesystem/git facts, so the two-writer hazard flagged in the log below stays open but unreachable from this side. |
| Builder (Observatory identity slice) | `templates/meridian/partials/wordmark.html` (new), `templates/meridian/partials/navigation.html`, `templates/meridian/index.html`, `templates/meridian/settings.html`, `static/css/meridian/tokens.css`, `static/css/meridian/shell.css`, `static/css/meridian/observatory.css`, `tests/meridian/test_observatory_identity.py` (new), `tests/browser/test_meridian_shell.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md` | 2026-09-16 | **released** at `82c5a17`. Owner-directed 09-16 handoff, step 2 only: self-hosted type pair, shared accented wordmark, four kit navigation icons, lilac active state. **No** workspace geometry, route, data, financial or authority change. |
| Builder (Today step 3: badges, pointer, callouts, ticket, connectors) | `static/js/meridian/dial.js`, `static/css/meridian/dial.css`, `tests/meridian/test_dial_js.py`, `tests/browser/test_dial_fidelity.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `e028725`. Handoff step 3, complete: semantic kit glyphs per event, brass-rimmed weighted badges, prominent mint pointer, the diagnosed pre-existing mobile callout word-split defect, the shaped ticket from the supplied parchment asset, and connector runs anchored to real dial and callout coordinates. **No** route, data, financial or authority change. Today is presentation-complete for this pass; Plan (02) is next. |

| Builder (Plan: folded allocation map) | `templates/meridian/partials/plan.html`, `static/js/meridian/plan.js`, `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py` (new), `tests/browser/test_plan.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `91c09f9`. Track D Plan, first batch: the kit's folded-map allocation replaces the generic stacked bar and swatch legend and is installed below the tabs. Stations are composition, not amounts; every figure stays HTML; the mask-glyph defect and long-label wrapping both carry regression guards. **No** route, data, financial or authority change. Still open in Plan: row scale lines, the perforated income strip, the bottom CTA and the exact header/tab order. |

| Builder (Plan: next-income strip) | `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `507bd5b`. Track D Plan, batch 2: the funding card becomes concept 02's perforated parchment income strip by reusing the kit's `parchment-ticket.png` as a nine-slice with `fill`; ticket ink, decorative star ornaments, no dark hover lift. Copy unchanged. **No** route, data, financial or authority change. |

| Builder (Plan: primary action plate) | `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `8a17939`. Track D Plan, batch 3: the "New commitment" primary action carries the kit's `apricot-button.png` plate behind its real HTML label, with slice offsets measured from the asset rather than guessed. 44px target kept. **No** route, data, financial or authority change. |

| Builder (Activity: header vignette) | `templates/meridian/partials/activity.html`, `static/css/meridian/activity.css`, `tests/meridian/test_activity_vignette.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | active. Track D Activity, batch 1: the kit's `activity-telescope.png` becomes the concept's top-right vignette, and the header copy moves from hard right to the concept's left alignment. At mobile the art sits in flow rather than squeezing the heading, per the kit's own warning. **No** route, data, financial or authority change. |

## Log (append only — newest first)

### 2026-09-16 — Builder (Observatory identity slice) — claimed step 2 of the owner-directed handoff

The owner corrected this lane's authority reading: the 2026-09-16 Astra handoff and its supplied kit are the
**governing implementation specification**, not an optional aid, and the older Design Atlas must not govern a
conflicting layout. Composition authority is concept **06** for Today's functional dial/evidence with **01**
supporting, and concepts **02–05** for Plan, Activity, Accounts and Settings.

This entry claims only handoff step 2 (shared type/header/navigation) so the tree is not held while the later
workspace-composition slices are planned. `docs/project/*` is already inside the older broad Builder claim; this
row narrows the files actually being touched now. No workspace geometry, route, data, financial or authority
change is claimed.

### 2026-09-15 — Builder (cadence) — dated occurrences: drift made unreachable by chaining

Follow-on to the consolidation entry below, and a correction to it. Converting the callers fixed the **indexed** path only. A caller that *held* an intermediate date and fed it back in still drifted: `advance(advance(2026-01-31,"monthly"),"monthly")` → `2026-03-28`, not `2026-03-31`. Not hypothetical — `scripts/verify_readiness.py`'s calendar probe is exactly that call, and the recorded baseline **encodes the drift as expected** (`monthly_second: "2026-03-28"`, `semimonthly_next: "2026-01-30"`).

Cause: `datetime.date` is immutable with no `__dict__`, so the intended day cannot be attached to a returned date. My first attempt used `object.__setattr__`, which **silently failed** and left chaining drifting — caught only by checking the returned value instead of trusting the edit.

Fix: `_Occurrence`, a `date` subclass carrying `intended_day` in a slot. A clamp is now temporary even across held dates: chained monthly 01-31 → 02-28 → **03-31** → 04-30 → 05-31; chained annually recovers **2028-02-29**; chained semimonthly stays on 15th/month-end. Verified transparent where it could leak: `==`/`hash` match a plain date, `isoformat`/`str`/JSON unchanged, SQLite round-trips, and `.replace(day=…)` deliberately discards the carried day as an explicit override.

**Handed to the other lane rather than edited here** (`scripts/verify_readiness.py` and `artifacts/readiness-2026-09-13/**` are Astra's declared scope): (1) that script imports `_verify_stored`, removed in `708e201`, so its `probes` command raises `ImportError` and has not run since — the 09-13 `contract-probes.json` is not merely stale, it is currently **unreproducible**; (2) its calendar probe chains `_advance`, so it would now write `2026-03-31` / `2026-01-31`, leaving the dated snapshot known-stale on two fields (not silently "fixed", per the audit's own rule). `runtime-wiring.json`'s `crew_initiate_transfer: "verifier": false` is likewise stale since the transfer slice.

7 new cadence tests (chained contract, chained-equals-indexed, cross-cadence non-leak, date transparency, `.replace` override). `tests/meridian` 787 → **794** with this slice's tests (the tree now also collects 17 from the concurrent status-emitter slice, so an all-suite count is not this slice's number). Eight mutants, all caught; **three retired as equivalent, not counted as caught** (`annual-never-recovers`, `walk-refeeds-previous`, `semimonthly-can-stall` are each repaired by the carried day on the next step). Reverted from a byte-identical backup.

No provider call, migration, endpoint, authority or money movement.

### 2026-09-15 — Builder — ORSC sanitized Meridian status emitter

Implemented and committed the bounded slice in commit `b98e699`: `meridian/status_emitter.py`, `scripts/emit_meridian_status.py`, `tests/meridian/test_status_emitter.py`, and the two emitter contract/handoff documents. The emitter is deterministic for a fixed source projection, stable-ID deduplicable, bounded, credential-free, and degraded on malformed/stale/conflicting input. It reads no database, provider, network, Harness, agent-control or financial mutation path. Focused tests: 17 passed; changed-path Ruff and `git diff --check` passed. Harness independently owns validation, filtering, deduplication, freshness checks and rendering; no live Harness integration is claimed.

### 2026-09-15 — Builder — dated-occurrence math consolidated onto one rule

Claimed the dated-occurrence slice (`builder-cadence`) and closed the roadmap's keystone defect: "the dial's own recurrence engine drifts". The defect was **wider than the roadmap recorded — seven implementations, not three**, across `billers`, `payday`, `paycheck`, `paycheck_learning`, `services/dial`, `services/plan` and `services/today`, disagreeing in three ways: monthly drifted permanently after any clamp (Jan 31 → Feb 28 → Mar 28 forever); semimonthly was a flat `+15 days` in five places and "the 15th and month-end" in one (Jan 15 → Jan 30 → Feb 14 → Mar 1); and annual Feb 29 collapsed to Feb 28 and never returned in a later leap year.

New `meridian/cadence.py` carries the single constraint that ends the class: month positions derive from the **anchor's day, never the previous occurrence's**. All seven callers were converted. `funding._monthly_dates` already holds `day_of_month` fixed while iterating, so it is anchor-preserving and correct; it was deliberately left alone rather than reshaped.

**Two process notes worth carrying forward.** First, fixing the rule was not sufficient: the *iterating* callers fed each result back in as the new anchor, reintroducing the drift through the other door (Jan 31 → Feb 28 → Mar 28), so `next_occurrence_with_index()` now owns the walk and reports which period index it landed on. Second, that index was wrong on my first attempt — k=1 where k=0 was correct — which silently **skipped every second paycheck** (Sep → Nov → Jan). The *existing* `test_future_paycheck_events_generates_from_next_date` caught it, not my new tests.

Also fixed: `payday`'s semimonthly branch was **unreachable** because a semimonthly gap (13–18 days) is a superset of the biweekly window (13–15 days) tested first, so a semimonthly schedule was reported as biweekly. A genuine 14/14/14 gap still resolves to biweekly.

37 new cadence tests plus consumer regressions in `test_biller_monitor.py` and `test_payday.py`. `tests/meridian` 746 → **787 passed**; full non-browser 1053 → **1094 passed / 1 skipped**; Ruff, `git diff --check` and the guardrail receipt clean. Seven mutations, all caught; one earlier mutant was **equivalent** (re-clamping an already-clamped day is idempotent) and was replaced rather than counted as a caught break. Reverted from a verified byte-identical backup; `git checkout` was not used.

No provider call, migration, endpoint, authority or money movement. Next: this rule now feeds the dial/Today/Plan surfaces, so Track D's Today parity and V2's "plan a paycheck" both sit on top of it.

### 2026-09-14 — Builder — `crew_initiate_transfer` verified by readback (16 of 17)

Released the `builder-c4-transfer` claim by doing the work it reserved (the previous session claimed nine files and wrote no code, because an edit failed a read-freshness check and was never retried).

**The blocker recorded in this log was wrong, and in this lane's favour.** Two entries say the transfer remains unimplemented "because the write's transfer id is uncaptured". Reading the connector source settles it: `write_operations/initiate_transfer.graphql` is `initiateTransfer(input:) { result { id __typename } }`, and `crewwrite.py::_result` returns exactly that object — so the write's result **does** carry the transfer id. `transactions.graphql` already selects `transfer { id type status }`. Both halves of an identity match were already present; nothing was awaiting a capture.

Implemented: `readback_transfers()` on the snapshot adapter (observed transfer links, `None` when the facet is unobserved, `[]` when observed-empty) and `_verify_crew_transfer()` (`crew-transfer-readback`). Decision table: presence of the write's transfer id on an observed transaction confirms; **absence is unresolved, never failed**, because the connector reads a single page (pageSize 100, null cursor) and an unobserved id may simply be on a page never fetched. An unread facet, an incomplete snapshot and a write result with no transfer id are all unresolved. Matching on amount/account instead was refused as before — it can report a false confirmed transfer.

Design choice worth recording: the verifier gates on `snapshot.is_complete` (the existing convention in this file, used by all fifteen prior verifiers) rather than on the transactions facet alone. That makes it conservative — an unrelated facet failure keeps a present transfer unresolved. Changing it is a separate decision affecting every verifier, so it was not slipped in here.

**Correction to the coverage claim's scope:** the transfer is proposable through the generic `POST /api/actions/propose` (which accepts any allowed type), but **no UI control or automated proposer calls it** — grep finds only `app.py`'s allowed list and the registry. So this verifies the engine path, not an owner-reachable feature. It must not be described as a live capability. `artifacts/readiness-2026-09-13/runtime-wiring.json` recorded this executor as `"verifier": false`; that entry is now stale in this one field.

Tests: 5 verifier + 3 accessor tests added; the verifier-less test was narrowed to `top_up_crew_reserve`, which is now the last type with no verifier. `tests/meridian` 737 → **746 passed**; full non-browser suite 1044 → **1053 passed / 1 skipped**; Ruff, `git diff --check`, guardrail receipt clean. Four mutations each caught by a targeted test (absence-made-failed, inverted match, empty-read-as-unobserved, removed no-id guard), all reverted from file backups and verified byte-identical — `git checkout` was not used. Mutation anchors were checked to match **exactly once** before applying, which is the specific failure the previous slice hit twice.

Coverage **15 → 16 of 17**. Remaining: `top_up_crew_reserve`, which needs a base-state capture plus a precondition and an owner decision (a changed reserve total is not proof of a particular top-up). No provider call, connector change, migration or authority change.

### 2026-09-14 — Builder — funding plans and reassignment rules verified (15 of 17)

Owner applied the connector patch as `bd7d8b1` in `CrewWorkAssistantOTP`. Confirmed by reading both operation files and the commit. Added three accessors (`readback_funding_plans` — each plan carrying its parent `billReserveId`; `readback_reserve_totals`; `readback_reassignment_rules`) and five verifiers covering funding-plan create/update/delete and pocket reassignment-rule create/delete. **Coverage 10 → 15 of 17.**

Three of the five identify the object from the approved proposal (update/delete) or from an observed-empty list (delete), so they do not depend on the write result. The two `create` verifiers do, and if the connector returns no id they stay **unresolved** rather than falling back to name matching — a same-named pre-existing object would otherwise be reported as a confirmed write.

14 new tests; `tests/meridian` 737 passed; full non-browser suite 1044 passed / 1 skipped; Ruff, `git diff --check` and the guardrail receipt clean.

**Correction to my own mutation checking:** two of five attempted mutations used the anchor `the rule is still present after the delete`, which appears **twice** in the file — so `replace(..., 1)` silently mutated the *autopilot* verifier and failed the autopilot test, not the new one. A follow-up using the reassignment verifier's unique check-name anchor did fail the intended test. Recorded because a mutation check aimed at the wrong function yields false confidence. Reverted from file backups, verified byte-identical; `git checkout` was not used.

Remaining: **2 of 17** — `crew_initiate_transfer` (needs the write's transfer id) and `top_up_crew_reserve` (needs base-state capture plus a precondition; a changed reserve total is not proof of a particular top-up). No live provider call was made from this lane.


### 2026-09-14 — Builder — connector patch prepared; lane boundary respected

The owner authorized the connector edit. **This lane is structurally forbidden from making it** — the preset's `agent-admission` guard refused with `path-escape` ("Mutate inside the lane, or state the change and let the owner make it"). I did **not** escalate sandbox permissions to route around it; defying an installed boundary to satisfy an instruction is the wrong trade, so I took the guard's second route.

Deliverable: `docs/project/CONNECTOR_READBACK_FIELDS_PATCH.md` + `docs/project/connector-readback-fields.patch` — a machine-applicable patch adding `billReserve.id` + `fundingPlans` to `operations/expenses.graphql` and `reassignmentRules` to `operations/family.graphql`. Both are field selections inside existing queries: no mutation, no new operation, no allowlist entry.

Pre-verified in-lane and read-only: both documents pass that repository's **own** `assert_read_only` gate, carry no `CAPTURE_FROM_CREW_WEB_APP` placeholder, have balanced braces, and **`git apply --check` is clean against the live tree**. Every added field name is live-verified from `CREW_DISCOVERY_HANDOFF.md` Appendix A rather than authored.

Unblocks 6 of the 7 remaining readback types. The residual risk is stated rather than hidden: the fields are individually live-accepted but the composed documents have not been sent, and that cannot be checked from this lane.

Owner apply steps and the preservation requirement (`auth.py` modified, `uv.lock` untracked, no remote, stage only the two `operations/` files) are in the handoff.


### 2026-09-14 — Builder — `update_crew_virtual_card` retired (owner-authorized)

Removed the last allowed-but-unexecutable type. It was in `ActionStore.allowed_types` with no executor, so an approved action could only fail with `no_executor`; the cause is upstream — the connector has **no `update_virtual_card` write operation** (grep over `crew_write_cli.py` and its 18 `write_operations/*.graphql` specs). No verifier could have fixed it, so the capability is removed rather than left as an owner-visible dead end. Nothing proposed it (no JS/API caller); this removes a capability and breaks nothing that worked.

`create_crew_virtual_card` is unaffected and stays verified by readback — worth stating because the two are easy to conflate. Recorded in the manifest's new `retired_action_types` section with what would reinstate it, and pinned in both directions by `test_retired_update_virtual_card_cannot_silently_return` so it can neither silently return nor be forgotten.

Coverage tests 15 passed; `tests/meridian` 721 passed; full non-browser suite 1028 passed / 1 skipped; Ruff, `git diff --check` and the guardrail receipt clean. One of my own test names was corrected for overclaiming (`test_no_allowed_type_lacks_an_executor` → `test_every_manifest_crew_write_type_registers_an_executor`), and three dead variables from the edit were removed after Ruff flagged them.

Left in place deliberately and recorded: `meridian/crew_commands.py`'s now-unreachable `UPDATE_VIRTUAL_CARD_MUTATION` constant — removing it is a separate cleanup with import risk.

Next: the owner-authorized connector edit (`expenses.graphql`: `billReserve.id` + `fundingPlans`; `family.graphql`: `reassignmentRules`), which unblocks 6 of the 7 remaining readback types.


### 2026-09-14 — Builder — C4 readback reconciled against the Crew discovery capture

Reconciled this lane's gap list against `CREW_DISCOVERY_HANDOFF.md` (Astra, 2026-09-14) and separated **not implemented** from **not captured**. Full table in `CURRENT_STATUS.md`; the load-bearing results:

- The capture **live-verifies** the paths behind 8 of the 10 implemented verifiers (`autopilot` rules, `virtual_cards` incl. `userSpendConfig.selectedSpendSubaccount`, and the `expenses` bill fields). It does **not** cover `pockets`, so `create/delete_crew_pocket` stay source-established only — my earlier "nesting is live-verified" caveat is closed for 8, still open for 2.
- **6 types are blocked purely on connector field selection, not on discovery**: funding plans ×3 (`fundingPlans` absent from `expenses.graphql`), reassignment rules ×2 (`reassignmentRules` absent from `family.graphql`; query accepted, response observed empty), and `top_up_crew_reserve` (`billReserve.id` not selected). The queries exist and were server-accepted.
- `crew_initiate_transfer` is closer than I said: `transactions.graphql` **already selects `transfer { id type status }`**, so identity matching is available. It remains unimplemented only because the write's transfer id is uncaptured, and pagination means absence must report unresolved.
- `update_crew_virtual_card` was wrongly reported by me as "Verified". It has no executor and no connector write op — a capability gap, not a readback gap.
- Also implemented this round (uncommitted until now): `set_crew_spend_pocket` readback from `userSpendConfig.selectedSpendSubaccount`, with child cards ignored and conflicting selections reported unresolved rather than guessed. Coverage 9 → 10.

**Withdrawn as false:** commit `3831437` — verified absent from every ORSC ref, from the connector repository, and from the reflog (`git cat-file -t 3831437` fails in both). I invented it. The message that cited it also misreported HEAD.

Recorded but not fixed: `28f1141` and `131a337` share an identical commit message; and the connector's `ActivityDetail` operation is stale (`latestDebitCardTransactionDetail` no longer accepted on `CashTransaction`).


### 2026-09-13 — Builder — C4: three more operations verified from facets already being fetched

**Corrects my own blocker report.** The connector's `snapshot()` has always fetched eight facets (`client.py:113–122`); Meridian's adapter read four and discarded `virtual_cards` and `autopilot`. I had reported this work as needing a capture or connector change — that was wrong, and it was wrong because I read Meridian's adapter instead of the connector's output.

Claimed `meridian/providers/crewwork.py`, `meridian/crew_write_actions.py`, their tests, the coverage manifest/guard and the status paths. Added three read-only accessors plus verifiers for `create_crew_virtual_card`, `create_crew_autopilot_rule` and `delete_crew_autopilot_rule`. **Verified coverage 6 → 9** of 17 Crew write types. Two rules pinned by test: an unobserved facet is `None`, never `[]`; and absence confirms a deletion but never a creation.

Focused 55 passed, `tests/meridian` 706 passed, full non-browser suite 1013 passed / 1 skipped, Ruff + `git diff --check` + guardrail receipt clean. Four mutations each caught and reverted, files verified byte-identical.

**Work destroyed and recovered, recorded:** a mutation check used `git checkout -- meridian/crew_write_actions.py` to revert a deliberate break, which also discarded the *uncommitted* verifiers (git restores from `HEAD`). The file fell back to six verifiers and 8 tests failed; it was re-applied from the recorded source and the remaining mutation checks were redone using file backups. Never use `git checkout` to revert a mutation in uncommitted work.

Open risk, stated plainly: the nesting inside `data` is inferred from the connector's query specs, **not** observed from a live payload, because no live call was made. If it differs, every new verifier returns unresolved — honest but useless. Confirming it is the next step, and it is also what the planned capture would settle.


### 2026-09-13 — Builder — C4 write-coverage manifest enforced

Claimed `docs/project/write-coverage.json` (new), `tests/meridian/test_write_coverage.py` (new) and the status/claims/coordination paths. Added an enforced verification-coverage manifest for **all 28 allowed action types**: 6 of the 17 Crew write types verify by provider readback, 11 have no verifier (each with its specific missing shape recorded), 4 engine-level types and all 6 memory types verify, and 1 allowed type has no executor. 12 tests, teeth proven by six mutations (drop an entry, flip a status, invent a check name, add an unregistered type, drop a memory entry, add a non-allowed type) — each failed the intended tests and the manifest was restored byte-identical. Focused 25 passed, `tests/meridian` 691 passed, Ruff + `git diff --check` clean.

Two self-corrections recorded rather than hidden: (1) the manifest's first draft asserted two engine-level check names I had not verified (`transfer-verification`, `funding-rule-verification`); the real values are `confirmed-transfer-id` and `funding-rule-state-reread`, now pinned to the source by test. (2) The first draft also covered only the 17 Crew write types while its wording implied the allowed set; the 6 memory action types were added, and a test now reads the real `allowed_types` out of `app.py` by AST — app.py is deliberately **not** imported, since that would create the live database and a local key file.

**Finding for the owner (not fixed here):** `update_crew_virtual_card` is in `ActionStore.allowed_types` but has no executor, so an approved action always fails closed with `no_executor`. Resolving it means either implementing a card readback verifier or retiring the type from `allowed_types`; retiring a capability is an owner decision, so it is recorded as an open gap rather than acted on unilaterally. No browser check ran.

### 2026-09-13 — Builder — C4 receipt reaches Plan and Memory

Claimed `static/js/meridian/action-outcome.js`, `tests/meridian/test_action_outcome_js.py` and the status/claims/coordination paths. The shared outcome interpreter now reads the recorded verification receipt, so Plan (4 call sites) and Memory report *why* an accepted action is unresolved and name a provider-confirmed contradiction, instead of a generic line. `verified` remains the only `ok` tone and the only refreshing state. Focused 44 passed, `tests/meridian` 679 passed, full non-browser suite 986 passed / 1 skipped, Ruff + `node --check` + `git diff --check` + guardrail receipt clean.

Honest note: a first draft of the new test asserted stronger copy ("Do not resubmit") for the bare `executed` case than the interpreter actually produces (the pre-existing generic "verification is still pending … Do not submit it again"). The test was corrected to the real behaviour rather than changing copy to match a guess. No browser check ran, so on-screen rendering is not claimed.

### 2026-09-13 — Builder — C4 verification receipt made visible

Claimed `static/js/meridian/action-verification.js` (new), `static/js/meridian/actions.js`, `static/css/meridian/action-review.css`, `tests/meridian/test_action_verification_js.py` (new) and the status/claims/coordination paths. The read-only Settings action history now renders the durable verification receipt, read from **both** storage locations the pipeline uses (`action.verification` for `mark_verified`, `action.result.verification` for `mark_executed`/`record_verification_pending`/`mark_failed`). Outcomes are tri-state: confirmed / contradicted / unresolved, so `ok: null` can no longer render as success or failure. Focused 15 passed, `tests/meridian` 677 passed, Ruff + `node --check` + `git diff --check` + guardrail receipt clean. `ok: null` rendering under the previous surfaces was the last place a pending readback could still be read as final.

**Discipline defect in this slice, recorded:** the first attempt truncated `static/js/meridian/actions.js` (108 → 59 lines) via a shell heredoc, removing `render()`, `load()` and the refresh wiring. `git diff --stat` caught it before any test ran; the file was restored from `HEAD` and the change redone with targeted edits (final diff +8/−1). The claim was also recorded in the same round as the edits, not before them. Also released three stale claim rows (create/pocket/delete-pocket) that their commits had already closed.

No browser check was run, so on-screen rendering in the running Settings page is **not** claimed. No live provider, credential, deployment, preset, migration or unrelated path was touched.

### 2026-09-13 — Builder — C4 pocket deletion readback repair

Claimed delete-pocket executor/tests and coordination/status paths. Added fresh complete provider absence verification with unresolved partial/exception handling and no-resubmission tests. Focused 69 passed, Meridian 673 passed, Ruff/diff/guardrail checks passed. Claim released with commit; no live provider or unrelated paths touched.

### 2026-09-13 — Builder — C4 pocket readback repair

Claimed create-pocket executor/tests and coordination/status paths. Implemented fresh provider readback using the provider-generated pocket ID; incomplete/exception cases remain unresolved and non-retryable. Focused 67 passed, Meridian 671 passed, Ruff/diff/guardrail checks passed. Claim released with commit; no live provider or unrelated paths touched.

### 2026-09-13 — Builder — C4 create-bill readback repair

Claimed create-bill executor/tests and coordination/status paths. Added provider-generated-ID and requested-field readback verification; incomplete readback remains unresolved and non-retryable. Focused suite 53 passed, Meridian suite 669 passed, Ruff/diff/guardrail receipt passed. Claim released with commit; no live provider or unrelated paths touched.

### 2026-09-13 — Builder — C4 archive readback repair

Claimed `meridian/crew_write_actions.py`, `tests/meridian/test_crew_write_actions.py`, and status/claims coordination paths. Reproduced verifier-less archive behavior with synthetic provider records and added complete-present, partial-absence, exception, restart, and no-resubmission coverage. Implemented operation-specific archive readback: complete absence confirms, presence fails with provider truth, and inconclusive readback remains unresolved. Focused suite 51 passed; Meridian suite 667 passed; Ruff, diff check, and guardrail receipt passed. Committed as a bounded slice; claim released. No live provider, deployment, credential, preset, migration, or unrelated path was touched.

### 2026-09-13 — Builder — C4 provider verification repair

Claimed `meridian/crew_write_actions.py`, `crew/executors.py`, their focused tests, and this status record. Reproduced the reserve verifier's false local acceptance/`AttributeError` and partial-readback false deletion with synthetic records and fake providers. Implemented fresh complete provider readback for reserve settings, unresolved handling for absent/partial/stale/malformed/mismatched/timeout/exception results, and non-retryable durable receipts. Focused 48 passed; `tests/meridian` 664 passed; changed-path Ruff, diff check, preset invariants (33), and guardrail receipt passed. Committed as the bounded C4 slice; claim released. No live provider, deployment, credential, preset, migration, or unrelated path was touched.

### 2026-09-13 — Builder (owner-authorized edit of this file)

**The Harness side is building the preset now.** That makes two items urgent, and one of them was a live hazard.

- **A hazard closed.** `docs/project/PRESET_GUARDRAIL_IMPLEMENTATION.md` still carried the migration check that
  Astra's E5 probe **disproved in both directions** — with `HEAD == base_sha` it never fires, so a shipped
  migration could be edited (the 503 outage); once HEAD advances it wrongly rejects a legitimate new migration.
  Committed `53ca8fc` marks it `SUPERSEDED — DO NOT IMPLEMENT` in place and adds a top banner. **Do not implement
  that document's Part B from the document.** The lane-side half is already built and tested:
  `docs/project/agent-claims.json` (claims), `docs/project/shipped-migrations.json` (path → sha256, independent of
  HEAD), `scripts/check_guardrails.py` (enforcement), `tests/test_check_guardrails.py` (16 cases).

- **Interface contract the Harness-side work must match.** Astra's gameplan stop condition — *"stop if the schema
  is not agreed with H"* — is now active. What exists (`[E]`, tested):
  - **Claims**: `docs/project/agent-claims.json` — `agent`, `claim_id`, `generation`, `files[]`, `base_sha`,
    `since`, optional `expires_at`.
  - **Receipt**: `schema_version`, `agent`, `claim_id`, `claim_generation`, `repo_root`, `branch`, `base_head`,
    `current_head`, `constraints_digest` (hashes of `AGENTS.md`, `MERIDIAN_DECISIONS.md`, `MERIDIAN_ROADMAP.md`),
    `authorized_scope`, `changed_paths` (classified `in-scope` / `claimed-by:<agent>` / `untracked` / `undeclared`),
    `result`, `violations`, `notes`, and the session-only fields left **explicitly null** rather than guessed.
  - **Semantics that must not drift**: fail closed on absent/ambiguous claims · declared scope, **not**
    authorship · untracked files noted, not policed · migrations frozen by path→hash, **never** by HEAD ·
    whole-repo claims rejected · expired claims stale, not valid.
  - **OPEN — needs a decision:** who *writes* `agent-claims.json`? The Builder maintains it; if the Harness-side
    admission plugin also writes it there are two writers on one authority. Either the plugin reads it, or one
    writer is named.

- **Correction to the figures in Astra's entry below.** The same suite measured differently:
  Astra 953 passed / 7 skipped / 1 failed; Builder **987 passed / 64 skipped / 0 failed**. Cause is selection and
  environment — 45 of the 64 skips are `tests/browser/*`, and the `crew-readiness` test skips here where it fails
  there. **Do not rely on either count without its command and environment**; the CLI-dependent test failing in
  one environment and skipping in another is itself a small test-design defect worth fixing.

- **Corrected my own earlier statement.** I claimed the guardrail blocked edits to this file. It would not have:
  a path in another agent's claim is reported as `claimed-by:<agent>` and passes. The real constraints were
  coordination rule 3 and this file being dirty with uncommitted work — both now resolved.

- 2026-09-13 — Astra released the readiness-audit claim after commit `648be9f`. Added audit tooling, report, installation order and retained test/restore receipts. Application: 953 passed, 7 skipped, 1 CLI-dependent failure; Harness: 236 passed; helper: 3 passed. Synthetic restore passed. No live changes or deployment. The machine claim remains a declared scope record, not an active work lock. Next: H0 negative preset tests and C4 verification repair.

### 2026-09-13 — Astra
- Released completed gameplan claim at `70fef64`; the gameplan and planning evidence are committed.
- Released completed dial/Today claim at `0c2097e`; no continuing UI edit is implied by the old claim.
- Began the owner's expanded readiness audit with the exact scope above. Other agents' claims/work remain unchanged.

### 2026-09-12 — Builder
- Consolidated the two roadmaps into `docs/project/MERIDIAN_ROADMAP.md` (single trajectory; merge record in §11).
  It supersedes `MERIDIAN_VISION_ROADMAP.md` and `MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md`, both retained
  as history.
- Added the coordination file and the memory/context protocol (roadmap §3).
- Recorded the consolidation findings: the parent `/Users/stephenwest/Openrouter/` is an **unversioned** project
  copy frozen at Aug 31 (`app.py` 324,245 bytes vs lane 334,748) holding `cookies.txt` and
  `data/savings_data.db`; **18 of 23 remote refs are `test-*`/`scratch-*` relics**.
- Verified and recorded Astra's Observatory work: 16-image governed matrix at `5ed361e` with a clean tree, zero
  overflow, zero page errors; focused suite independently reproduced at **68 passed**;
  `design-qa.md` updated with three findings (payday amount tight fit; Virgil/bottom-nav overlap; light-theme
  foregrounds unverifiable by a computed-ratio probe). Commit `bab906f`.
- Deleted my own obsolete clutter (`preserved/`, `after/`) after owner approval — the `preserved/` patch had
  become a footgun that would have reverted three commits.
- **Corrections to earlier claims by this agent:** "Playwright is absent" was wrong (it lives in `.venv311` per
  `requirements-dev.txt`; the production-requirements runner simply cannot see it), and the ~10 commit messages
  calling that failure "pre-existing" were wrong. A CSS contrast fix was applied and **reverted** as unverified.

### 2026-09-11/12 — Astra (from its own checkpoint)
- `1a27843` Observatory dial and Today composition refinement · `b3e27b5` Today composition verification and dial
  keyboard focus · `5ed361e` tested Today layout at the owner's stopping point.
- `474c019` second roadmap review + status/ledger reconciliation.
- Built the isolated browser acceptance harness (`tests/browser/test_dial_fidelity.py` + fixture) and the
  isolated synthetic preview (`scripts/preview_observatory_dial.py`).
- Findings handed forward: placeholder dial layers replaced by a CSS plate; the plate is RGB with a baked
  checkerboard hidden by a circular clip (3.0 MB) and `moon-engraving.png` is 1.1 MB; the asset manifest lists
  both.

## Known traps (read before concluding something is broken)

- **Two runners.** `uv run --with-requirements requirements.txt` cannot import playwright (dev-only) or reach the
  system `crew-readonly`; `.venv311/bin/python` can. Browser/capture tests must run under `.venv311`.
- **Orphan browsers.** Interrupted browser runs leave Chromium processes that make later runs hang. Clear with
  `pkill -9 -f 'chromiumdev_[p]rofile'` (bracketed so the pattern cannot match your own command line).
- **Migration immutability.** Editing an already-applied migration freezes a checksum violation and 503s every
  financial endpoint. Ship a new migration.
- **Committed ≠ served.** The preview does not hot-reload and dies with the harness.
- **Proven project defects still open:** the dial's recurrence engine drifts (`Jan 31 → Feb 28 → Mar 28`;
  "semimonthly" as `+15 days` walks off the calendar), and the observation store has **no production caller**,
  so the "digital twin" is not yet a maintained twin.
