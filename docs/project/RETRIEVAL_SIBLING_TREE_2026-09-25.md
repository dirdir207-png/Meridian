# Retrieval from the older tree — payday, funding, and the rules we do not carry (2026-09-25)

**Why this document exists.** The owner said twice that older SimpleCrew/Meridian work held real knowledge our
tree lacks, and that this lane had disregarded it without thorough research. He was right. A first pass by this
lane measured the wrong thing — `origin/main` **of our own repository**, an older snapshot of the same lineage —
and concluded there was nothing to retrieve. This pass read the actual older tree
(`/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`, branch `ox-alpha/meridian-overhaul`, HEAD `5b390b9`,
2026-09-11) and the connector application, with the instrument stated for every claim.

**Two premises of the first pass were wrong, and the correction matters.**

* The older tree's `feat/meridian-implementation` is at `49b65f1` (2026-08-28) — an **ancestor-era branch**, not
  ours. Its HEAD is `ox-alpha/meridian-overhaul`. Comparing branch names across two repositories is how the
  first pass went wrong.
* The `codex/turn-diffs/...` entries are **refs** under `refs/codex/turn-diffs/checkpoints/`, not branches
  (instrument: `git for-each-ref`; 20 refs: 4 local heads, 4 remotes, 9 checkpoints, 1 stash).

**Both directions are true.** The older tree is richer on payday/funding in the four ways below; it is *missing*
things we have — semimonthly-aware `meridian/cadence.py`, `meridian/paycheck_learning.py`, and the entire
`crew_write*.py` readback-verifier layer (it has **no** `crew_write*.py` at all).

## 1. Four things the older tree has that we do not

### A1 — A saved, owner-stated payday schedule, with an action and a readback verifier

* `docs/project/DECISIONS.md:20` (its D12): *"Manual payday schedules populate immediately, then observed
  deposits refine them automatically… Store manual values as an explicit fallback; promote verified recurring
  deposits only after evidence thresholds; show source/confidence and never replace a manual schedule
  silently."*
* `POST /settings/payday` (`meridian/api.py:514-549`): cadence ∈ {weekly, biweekly, semimonthly, monthly}
  (line 522), positive-amount validation (525), writes `app_config` keys `payday_cadence`/`payday_amount`/
  `payday_source`/`payday_anchor`/`payday_minimum`/`payday_maximum`, and deletes `payday_amount` when blank (531).
* Action type `update_payday_settings` with executor `_apply_payday_settings` and verifier
  `verify_payday_settings_action` (`app.py:941-968`), whose readback check is `payday-settings-reread` with
  `ok = cadence AND anchor equal`.
* `meridian/services/plan.py:78-88, 295-320` `_saved_payday_events`: *"A saved payday is itself a forecastable
  funding event"* — source "saved payday schedule", explanation "projected from the saved payday cadence and
  anchor date".

**Why this is the archaeology answer.** Our own `docs/project/PAYDAY_FUNDING_FINDINGS_2026-09-24.md:45-50` states
*"(b) The instruction is unactionable — there is no write path for a payday at all"*, and that a repo-wide search
for `set_payday`/`confirm_payday`/`payday_pattern`/`income_pattern` returns nothing. **The older tree had one.**
Verified absent from ours: `update_payday_settings` has 0 hits across our tree (all paths) and 0 commits in our
history (`git log -S`, empty).

**Classification per D-037:** the *architecture* is superseded — our D-010/D-015 and migration 022 make **Crew's
funding plan the authority**, so a second, manually-saved payday schedule would be a rival authority. But the
**pattern** is knowledge worth holding: an owner-stated fallback, promoted only after evidence thresholds, never
silently replaced, with an action plus a readback verifier. If a manual override is ever wanted, this is a
worked precedent rather than a proposal.

### A2 — A named funding-schedule model with persisted runs, CAS revisions and idempotency

Migrations we do not possess: `015_funding_schedules.sql` (`funding_sources`, `funding_schedules` with
`recurrence_json` and `revision`, indices), `016_funding_rule_metadata.sql` (`funding_rules.funding_source`,
`notes`), `017_funding_runs.sql` (`funding_runs` keyed `UNIQUE(schedule_id, occurrence_key)`, with
`total_cents`, `shortfall_cents`, `status`). Plus `meridian/schedules.py` (`validate_schedule` rejects unknown
cadence, requires an ISO anchor; `next_occurrences` supports a semimonthly `days` list with month-end clamp and
dedupes), `meridian/schedule_repo.py:38-47` (`update` raises *"schedule revision is stale"* on an
`expected_revision` mismatch), and `meridian/funding_runs.py:13-17` (`record` is idempotent via
`INSERT OR IGNORE` and returns the **first** row even when a later write offers different totals — pinned by
`tests/meridian/test_funding_runs.py:8-11`).

**Classification:** superseded architecture (Crew is the authority), but three transferable patterns — a
compare-and-swap revision guard, an idempotency key that survives a second write, and a persisted run history
with a distinct `status` vocabulary. Our tree has none of the three under these names.

### A3 — A different allocation algorithm, pinned by tests we do not have

* `meridian/planning.py:6-12` `required_contribution_cents` = `(remaining + events - 1) // events` — the ceiling
  of remaining ÷ eligible pay events.
* `build_funding_preview` (`:15-53`): greedy priority-then-id order, one shared cash pool decayed line by line,
  per-run `run_cap_cents`, `run_cap_reached` reported distinctly from `minimum_unmet`, a
  `managed_by_crew_autopilot` exclusion, and `shortfall_cents = max(0, requested - allocated)`.
* Provenance in its `docs/project/DECISIONS.md`: D13 (*"Default paycheck funding is distributed across upcoming
  bills; priority waterfall is opt-in… essentials-first behavior must be an explicit schedule strategy"*) and D14
  (*"Required contribution is derived from remaining target ÷ eligible pay events before the bill's due date…
  Equal splitting is only the fallback when requirements are otherwise equivalent"*).
* Tests with no counterpart in ours: `tests/meridian/test_planning.py:23-45` (shortfall arithmetic; `run_cap 0`
  yields `run_cap_reached`, not `minimum_unmet`; `required_per_event_cents == 3334` for 10000/3) and
  `tests/meridian/test_funding_execution.py:60-69` (a crew-autopilot rule yields `allocated 0` with exception
  `managed_by_crew_autopilot`).

Our `meridian/funding.py` is rule-per-commitment: no shared pool, no run cap, no requested/allocated split, no
`required_per_event`. **Classification: a genuine open question, not a regression.** These are design decisions
our tree never made, so they belong in front of the owner with the arithmetic and the trade-offs.

**A defect recorded so it is not inherited:** `planning.py:36` reads `rule.get("min_contribution_cents")` while
nothing in that tree writes the key (2 hits, both in `planning.py`), and its
`MERIDIAN_PRINCIPAL_AUDIT_2026-09-08.md:86` F07 says so: *"planning.py prioritizes full needs, lacks per-rule
maximum handling; Plan caller omits funding_source, so crew_autopilot guard cannot protect this production path."*

### A4 — A funding-source and account-buffer definition we do not record

`docs/project/PROJECT_BRIEF.md:11` (a file absent from our tree): *"Funding uses named schedules, not a payday
attached to one bill. A schedule has optional expected income, recurrence/anchor date, funding account, trigger,
active/paused state, and multiple independent bill allocations. **Min/max contribution limits and account buffers
have distinct meanings.**"* Its DECISIONS D04 adds that a funding source is *"an account plus an income/trigger
definition, not merely a dropdown label"*. Verified absent from ours: `account buffer` → 0 files;
`source_buffer_cents` → 0 files.

## 2. Rules in the older tree that our tree does not state

1. **A precedence rule** (its `DECISIONS.md:5`): *"Current explicit owner instructions → accepted later product
   decisions → approved original specifications → implementation plans → status claims. A newer completion claim
   does not change a requirement. **Code/tests show current behavior, not desired behavior.**"* Our tree has
   precedence for *visual* authority and for the roadmap, but not this chain.
2. **A cap rule** (`PROJECT_BRIEF.md:29`): *"Zero maximum contribution means an actual zero cap; absent maximum
   means no cap. The UI must not serialize an empty max as zero."* Our `meridian/funding.py:162-171
   _clamp_to_caps` implements exactly this distinction, and no document states it — the behaviour is real, the
   rule is unrecorded.
3. **A preservation list** (`MERIDIAN_PRINCIPAL_AUDIT_2026-09-08.md:168-178`, "Things that should NOT be
   changed"), including *"Owner-accepted direct local edits; do not add approval ceremony to ordinary metadata
   saves"* and *"Durable action claiming and uncertainty/no-resend semantics"*.
4. **A consistency rule** (`CREW_MUTATION_INVENTORY.md`): *"Any operation that changes Crew state must be
   available through Meridian's explain → approve → execute once → verify → reconcile pipeline. Meridian-local
   planning metadata may remain local, but the UI must label that boundary."* Plus a readback envelope
   `{"state": "reconciled | pending_reconciliation", "verify_state": true}` and *"The original Crew mutation is
   never retried. If the mutation is confirmed but the read-back fails, Meridian shows pending verification and
   does not present the normalized graph as current."* Our `meridian/mutations.py:26-52` implements that
   vocabulary; the per-capability inventory table has no counterpart in ours.
5. **A working-cycle discipline** (`WORK_CYCLE.md`): refresh the context packet *"after compaction, agent/model
   handoff, a schema/API change, an owner correction, two failed hypotheses, or approximately 30 minutes of
   work"*; *"A compact checkpoint should fit within 600 words"*; *"Refuse to hide red tests or modify old fixtures
   merely to make the numbers green. A specification change can update a test only with a recorded rationale and
   replacement coverage"*; and *"Do not invent counters from transcript length or claim API-dollar estimates equal
   subscription usage."*

**Careful, and the agent verified it:** that 17-finding audit's own scope line names **our** tree at `73197bd`
(2026-09-08), so several findings are about an older state of our own repository. Four were re-tested against
current HEAD and are **withdrawn**: F03 (transfer verification on id alone) is superseded by
`crew_write_actions.py:581 _verify_crew_transfer`, which is three-state and documents *"ABSENCE is UNRESOLVED,
never failed"*; F04/F05's `ScheduleRepository` and payday-form model no longer exist; F01/F02's second write
surface is already our D-031.

## 3. The connector's prose rules that our tree does not hold

1. **Money and nulls** (`BASE44_INTEGRATION_CONTRACT.md:34-35`): *"Money is always represented as integer cents.
   Dates are ISO 8601 strings. Missing values remain `null`; Base44 must not replace them with zero."* We state
   *"Amounts are dollars"* (022) and enforce absence at the storage layer (020/021/024) but never as a
   cross-boundary serialization rule.
2. **Freshness as a precondition of action** (`:82, :107-111`): snapshots expire (recommended five minutes);
   *"Reject snapshots older than five minutes for action previewing"*; *"Disable action approval when a proposal
   is expired or the snapshot is stale"*; show the capture timestamp beside every balance. We report freshness;
   we do not disable approval on it.
3. **A seven-state proposal machine** (`:92-94`): `preview`, `submitting`, `submitted_unverified`, `cancelled`,
   `expired`, `completed`, `failed`, with `execution_enabled` defaulting to **false**. Our `crew/actions.py:25-44`
   has a different eight-value vocabulary and no `submitted_unverified` (0 files). The *semantics* exist — we set
   `verify_state: True` in exactly that case — but the name and the UI contract do not.
4. **Per-proposal binding fields** (`:52-62`): `proposal_id`, **`idempotency_key`**, exact action and parameters,
   `created_at`/`expires_at`, `execution_enabled=false`, `requires_exact_approval`,
   `requires_fresh_crew_snapshot`, `requires_final_crew_review`. Our ActionStore has no `expires_at` and no
   idempotency key — we have `dedup_key`, which collapses repeated *proposals*, a different concept from
   identifying one *submission*.
5. **The transfer gate's binding list** (`WORK_PROJECT.md:32-35`): exact amount, source, destination, **expected
   pre/post balances**, approval text, expiry and idempotency key; revalidate fresh balances before a single
   submission; *"An ambiguous response is never retried automatically"*; and (`:114-115`) show a prominent
   *"check Crew; do not retry"* state. Our readback deliberately refuses amount matching
   (`crew_write_actions.py:581-600`) for a stated evidential reason — **the two systems disagree on purpose, and
   neither document records the other's argument.** That is worth an explicit decision rather than silence.
6. **A per-row safety-boundary artefact** (`SIMPLECREW_PARITY.md:9-44`): a *Capability | connector | Base44 |
   **Safety boundary*** table, with *"Proposals expire, bind exact parameters, require a fresh Crew snapshot, and
   have `execution_enabled=false`. Only `move_money` has an executor… All other write surfaces remain
   non-executable."* Our nearest equivalents (`CREW_CAPABILITY_MATRIX.md`, `BILLER_CAPABILITIES.md`) are not
   per-row safety boundaries.
7. **Credential lifecycle and the retry asymmetry** (OTP design spec): masked credential handling; the JWT and
   Stytch session token captured from response headers and persisted **immediately**; secrets passed to Keychain
   on stdin rather than as arguments; *"never logs request variables or credentials"*; rotation headers checked
   after **every** response *"including GraphQL-error responses"* and persisted **before** parsing the body;
   **an HTTP 401 triggers one `logged_in` refresh, after which a read-only request may repeat exactly once, a
   second 401 requires interactive login, and authentication endpoints and money-moving mutations are never
   automatically retried**; *"A rotated credential that cannot be written to Keychain stops the workflow"*;
   *"The transfer process may consume a current token and persist rotation, but it never launches login, repeats
   a transfer after 401, or retries an ambiguous submission"*; auth mutations are structurally excluded from the
   general read allow-list. **Our flat "never auto-retry financial mutations" lacks the bounded read-only retry
   budget and does not name authentication as a second no-retry class.**
8. **Write-layer validation** (`WRITE_LAYER.md:18-25`): each document is validated as *"the exact reviewed
   mutation (single `mutation`, pinned name/call)"* before sending; `CrewWriteRejected` (Crew said no) and
   `CrewWriteUncertain` (outcome unknown — verify, do not retry) are distinct; variables are never logged; and a
   four-value return-code contract (`0` ok, `2` blocked/invalid, `3` rejected, `4` uncertain). Note the document
   itself is **stale**: it lists 4 of the 18 write contracts that exist on disk.
9. **Explicit non-goals**: *"Sensitive card reveal | Intentionally excluded | Never expose PAN/CVV to ChatGPT or
   Base44"*; no PAN/CVV for physical cards; no API keys in Base44; *"no financial detail in notification text"*;
   *"No AI recategorization writes"*; and (`BASE44_INTEGRATION_CONTRACT.md:108`) *"Do not store PAN, CVV,
   cookies, authorization headers, or bank account numbers."*

## 4. Observational data in the older tree (aggregate only)

Instrument for all figures: `sqlite3 "file:<path>?mode=ro&immutable=1"` — read in place, nothing writable, no
copy. No amounts, balances, account identifiers, names or tokens were printed.

* `data/savings_data.db` (1.35 MB, 46 tables, migrations 001–017 stamped 2026-09-04/05): `funding_sources` 8 rows
  (all `kind='paycheck'`, `status='active'`, 7 of 8 stating an expected amount — the column is nullable, so
  "not stated" is representable); `funding_schedules` 8 rows whose `recurrence_json` carries **exactly** the two
  keys `anchor_date` and `cadence`, one distinct cadence, all anchors inside a single calendar month (day-of-month
  span 05–16) — i.e. a biweekly mid-month paycheck; **`funding_runs` 0 rows**, so the run-history model was built,
  given a schema and never exercised; `provider_sync_runs` **4,662 rows** spanning 2026-09-04 → 2026-09-26 with
  4,618 complete / 26 failed / 23 partial — **a measured ~0.56% failure rate our tree does not have at this
  resolution**; income observations 10 rows on 10 distinct amounts whose intervals (2,1,1,0,13,1,2,0,0) are **not
  any cadence**, which is why recognition returns `None` despite meeting the four-evidence threshold.
* Our `artifacts/os058-observations/gate-observation-20260925T230432Z.db`: only 4 income rows (09-01, 09-21,
  09-22 ×2), below the threshold once the same-day cluster is considered — so **the "Not recognized" state has a
  data cause as well as the code cause OS-104 found**, and rewiring the Cadence card to Crew's plan will not
  populate the learned leg on this data. Its 52,560 sync runs are a 15-second-poll artefact, not reliability.
* **Cautions.** The provenance of those 8 funding schedules is **unverified** — no script in that tree seeds
  them (`seed_preview.py` does not create the tables), so whether they are the owner's manual entries or a
  service artefact is unknown. And `acceptance/2026-08-30/*` plus `backups/owner-acceptance-2026-08-30/*` exist
  in **our** tree too, so their provenance must not be attributed to the older tree alone.

## 5. Two findings that bear on authority, both verified

1. **Our tree routes cardholder and bank-account data to the browser, and no rule in our tree governs it.**
   `app.py:4308 api_account_bank_details` queries `spendAccount.accountNumber` and `institution.routingNumber`
   and returns routing numbers (`:4328/4334/4361/4363`); `app.py:5375 api_card_sensitive` mints a
   `generateViewSadToken` and fetches `https://cde.trycrew.com/wally/debit_card`, returning `{"pan", "cvv"}`
   (`:5416-5417`). Both are `@login_required` and nothing else — **no passkey gate exists** (0 hits for a
   required-passkey rule), and **no cardholder-data rule exists anywhere in our tree** (`no PAN` → 0 files). The
   only two places the rule was ever written are the connector's non-goals and that 2026-09-08 audit's F11, and
   neither is ours. Recorded as **D-038** with the options, for the owner.
2. **The payday "Not recognized" state has a data cause as well as the code cause** — see §4.

## 6. Not retrieved, stated as gaps

* The nine `refs/codex/turn-diffs/checkpoints/*` refs were enumerated but **their trees were never resolved** —
  the one unexplored region of the older tree's history.
* The older tree's other branches (`feat/meridian-implementation` at `49b65f1`, `design/meridian-product-overhaul`)
  were not diffed against its HEAD, so an implementation living only on one of those refs would be invisible here.
* Whether its semimonthly `days`-list recurrence was ever reachable from a UI — no template or JS posting
  `recurrence.days` was found.
* Which of the connector's credential rules our Meridian-side handling (`crew/session_credentials.py`,
  `crew/mac_secrets.py`) already implements.
* No test suite was run in either tree; the one behavioural check was a standalone transcription of both payday
  interval rules, which agreed on all four legacy cases including the month-end monthly sequence.

**And the instruction that governs all of it (D-037):** retrieving is not restoring. Each item above is
classified — superseded architecture, transferable pattern, unrecorded rule, or genuine open question — and
nothing here may be put back without naming what superseded the old form, or asking.
