# Crew capability matrix — what already exists, verified 2026-09-25

**Why this exists.** The owner asked: *"Please also review the roadmap for anything requiring read/write paths
and verify it isnt already built."* The question was prompted by being right twice — autopilot rules and the
paycheck funding plan both had machinery assumed absent. This is the exhaustive answer, from a read-only audit
of `meridian/providers/crewwork.py` (CW), `meridian/crew_write_actions.py` (CWA), `meridian/crew_write.py`
(CWR) and `meridian/write_routing.py` (WR), with the headline claims re-verified by this lane.

## 1. THERE ARE TWO WRITE SURFACES, NOT ONE — and one of them is ungoverned

This is the finding that changes decisions, and it is why a "does a write path exist?" answer that counts only
the pipeline is wrong.

**Surface A — the governed pipeline.** `meridian/crew_write_actions.py` holds **17 registered action types**,
each mapping to a `crew-write <operation>` invocation (`CWR:81`), each name allow-listed (`CWR:19-37`), and
**16 of the 17 carry readback verifiers** (`CWA:656-705`). Every failure path returns `retry_allowed: False`
(`CWR:90-133`) — no auto-retry anywhere. Routing is `meridian/write_routing.py`: `classify_action` (`WR:64-136`)
sends under-specified, low-confidence, multi-op, plan-level and scheduled work to a proposal, and only
`Provenance.OWNER_DIRECT` executes immediately (`WR:110-115`).

**Surface B — direct Crew GraphQL from the Flask app, live and reachable from shipped UI.** Verified by this
lane, not relayed:

| Route | Anchor | What it does |
|---|---|---|
| `POST /api/move-money` | `app.py:5794` → `move_money` `app.py:2395` | fires `initiateTransfer` as a raw mutation through `crew_client.execute(..., is_mutation=True)` |
| `POST /api/create-bill` / `delete-bill` | `app.py:5844` / `5837` | `CreateBill` / `DeleteBill` |
| `POST /api/create-pocket` / `delete-pocket` | `app.py:5807` / `5800` | `CreateSubaccount` / `DeleteSubaccount` |
| `POST /api/set-card-spend` | `app.py:5541` → `updateVirtualDebitCard` `app.py:2995` | the capability **retired from the pipeline** for lack of a connector write op |
| `POST /api/account/autopilot-rules/create` / `update` / `delete` | `app.py:5179` / `5039` / `5141` | rule create/update/delete |

Shipped front-end code calls them: `static/js/ui/modals.js:152,289,306,416`, `static/js/api/cards.js:228`,
`goals.js:199`, `expenses.js:89`, `templates/partials/views/account.html:1055,1091,1155`. **The only guard is
`@login_required`** (`app.py:5790`) — authentication, not governance. **No router, no proposal, no readback
verification, no retry guard, no audit record.** No feature flag gates them.

**Two consequences worth naming precisely.**
1. `update_virtual_card` was deliberately removed from `ActionStore.allowed_types` (`app.py:1219-1223`) because
   the connector has no write op for it — yet the same provider mutation is alive on this surface. A capability
   retired in one place is reachable in another.
2. `POST /api/actions/mutate` defaults its provenance: `data.get('provenance', 'owner_direct')` (`app.py:4226`).
   A caller that omits provenance is therefore treated as the owner acting directly and executes immediately —
   which is the opposite of the router's stated intent that *"the AI/UI cannot send an ambiguous plan down the
   direct path"* (`WR:17-18`).

**Neither surface is a defect for existing.** An owner editing his own app *should* execute rather than
propose (D-020). The defect is that Surface B skips provenance classification, the single executor, provider
verification and the no-retry bound — the four things the constitution says never get bypassed.

## 2. Capability × read × write × persisted × verified

| Capability | Read | Write | Persisted | Verified |
|---|---|---|---|---|
| **autopilot rules** | YES (`CW:443`; `app.py:4798`, `:4974`) | create + delete via pipeline (`CWA:668,687`); **edit has no action type** — the only reachable edit is the ungoverned route | **NO table anywhere** | pipeline create/delete: yes by readback; legacy routes: **no** |
| **bill reserve settings** | totals/schedule yes (`CW:473`, `CW:493`); the settings sub-facet only at `app.py:2912`, as a display name, with the error path returning `"Checking"` | yes — `update_crew_bill_reserve_settings` (`CWA:664`) + `top_up_crew_reserve` (`CWA:686`) | yes — `crew_bill_reserves` (024/028), 025 columns, `crew_funding_plans` (022) | settings write: **compares BILL fields only, never the settings** (see §3C); top-up: **none** |
| **paycheck / funding plans** | yes (`CW:451`) | create/update/delete (`CWA:674,678,682`) | yes — `crew_funding_plans`, written by `live.py:100-117` | yes — readback for all three |
| **bills** | yes (`CW:158`) | create/update/archive (`CWA:669,663,670`); also ungoverned `app.py:5844`, `:5837` | yes — `commitments` + 021/023/024/025 columns + 031 history | pipeline yes; legacy **no** |
| **cards** | yes (`CW:323`, `CW:347`) | partial — create virtual card (`CWA:700`); update retired but reachable via `app.py:5541`; **no delete** | **NO** | create yes by readback; legacy **no** |
| **accounts / pockets** | yes (`CW:580`) | create/delete (`CWA:671,672`); ungoverned `5807/5800/5794` | yes — `financial_accounts`; **`goal_target` (029) never written in production** | pipeline yes; legacy **no** |
| **transactions** | yes (`CW:635`); transfer links `CW:533` | `crew_initiate_transfer` (`CWA:673`); ungoverned `5794` | yes — `financial_transactions`; **transfer links no** | yes, but **presence-only**: absence is always unresolvable (`CWA:638-643`) |
| **spend-pocket selection** | yes (`CW:396`, four-state contract) | `set_crew_spend_pocket` (`CWA:696`); ungoverned `5541` | yes — `crew_spend_selection_observations` (030) | yes; empty and conflicting are unresolved, a different id is contradicted |
| **per-bill reserve allocation** | yes (`CW:194`; 024 flag; 031 dated history) | yes — reserve settings carrying `reservedAmount`, plus a reserve-level top-up | yes — `funded_amount` + 024 flag + 031 history | yes for the per-bill write; the top-up itself **unverified** |
| **family members** | yes (`app.py:2433` via `/api/family:5278`) | **none found** | **no** | n/a |
| **digital twin** (`financial_observations`, 019) | readers exist (`meridian/api.py:272,283,297`) | **no writer**: `record_provider_snapshot` has zero callers | schema exists, nothing writes it | n/a |

**Facets read on demand and persisted nowhere:** cards · autopilot rules · pocket reassignment rules ·
transfers · `billReserve.settings.funding.subaccount` · family members · pocket goal (`goal_target` column
unused) · `financial_observations`.

## 3. Verification asymmetries (the ones that matter)

- **A. One write with no verification at all:** `top_up_crew_reserve` (`CWA:686`, `no_verify` at `:661`). Its
  recorded reason (`docs/project/write-coverage.json:54-57`, dated 2026-09-19 02:49) says the provider exposes
  no `billReserveId` — but migration **023** added `commitments.bill_reserve_id` at 16:25 *the same day*, and
  `CW:179/212` now emit it. **The reason is stale; the identity a verifier needs exists.**
- **B. Six route families with no verification and no proposal** — §1.
- **C. A verifier checking the wrong object:** `update_crew_bill_reserve_settings` compares bill fields — name,
  amount, `reservedAmount` (`CWA:68,87-89`) — read from `commitment_candidates` (bills). It never reads
  `billReserve.settings`, so **a settings-only change that silently failed is undetectable by it**. Its
  parameter is also named `billReserveId` while carrying a **bill** id (`meridian/api.py:1731`; tests pass
  `"Bill:1"`).
- **D. A shipped command with no executor:** `edit_autopilot_rule` has a `CommandSpec` and a validated payload
  builder (`meridian/crew_commands.py:115-117`, `:60-64`, `:250-255`) but no action type, executor or verifier;
  `CWA:29-37`'s edit branch is unreachable and `CWR:19-37` has no edit op. **Rule editing exists only on the
  ungoverned surface.**
- **E. Absence-as-proof is used only for deletions.** Deletions and archives return `ok=True` on observed
  absence; creations never do (absence is always `ok=None`). `crew_initiate_transfer` cannot use absence at all
  — a single page cannot prove a transfer is absent.
- **F. Tri-state asymmetry in the adapter:** funding plans, reserves, cards, rules and transfers distinguish
  unobserved (`None`) from observed-empty (`[]`/`()`); accounts, transactions and commitment candidates do not
  (`unobserved ⇒ []`) and rely on `is_complete` (`CW:154`).

## 4. What this lane resolved from the audit's open questions

- **Which sync entry point is live:** the audit could not determine whether commitments, funding plans and
  reserve totals are persisted, since `scripts/meridian_sync_live.py:40` calls `sync_provider` only. Resolved by
  direct observation: `crew_funding_plans` holds three rows with fresh `observed_at`, and `crew_bill_reserves`
  is current, so the **app's refresh loop** (`run_preview.py` → `ensure_meridian_refresh()`, persisting through
  `meridian/live.py:70-137`) is the live writer, not the script.
- **Still open, stated as open:** whether the live connector returns all eight facets it is claimed to fetch
  (`docs/project/CONNECTOR_READBACK_FIELDS_PATCH.md` is marked "not applied" as of 2026-09-14), and whether
  `financial_observations` holds any rows at all.

## 5. What this document is not

It is a record of what exists, taken by reading code. It is **not** a decision: whether Surface B is migrated
onto the pipeline, fenced, or documented is the owner's call, and it is recorded as such in D-031. Nothing here
was changed by the audit, and no route was disabled.

## 6. Archaeology — what was already recorded (owner's rule, D-034)

Executed 2026-09-25 with the instrument stated, because a figure without its instrument is an anecdote.

- **Crew's own operation catalogue** (`CrewWorkAssistantOTP/operations/`, 15 files): `accounts`, `autopilot`,
  `autopilot_rule_detail`, `card_detail`, `expenses`, `family`, `family_subaccounts`, `physical_cards`,
  `pocket_transactions`, `pockets`, `profile`, `subaccounts`, `transaction_detail`, `transactions`,
  `virtual_cards`. **All 15 appear in our code**, by filename-stem grep across `meridian/` and `app.py` — a
  positive signal and not a proof; a stem can match a comment.
- **A prior parity plan exists** (`SIMPLECREW_PARITY.md`) with a safety boundary per capability, and it records
  the same two rules this project rediscovered independently: money transfers as a *separately gated* executor
  with exact approval, fresh preflight, one submission and no third-party transfer; and Safe-to-Spend that
  *"never infer[s] silently when unavailable"* — C01 in another document's words.
- **A richer retired tree exists**: `origin/main` carries **38** source files mentioning
  autopilot/calendar/family/evaluation, against **1** file on each of `main`,
  `origin/docs/enhanced-simplecrew-project-control`, `origin/fix/review-blockers` and `origin/scratch-a`. It has
  not been mined (`OS-122`).
- **The sibling tree is older, not richer**: its `meridian/` lacks `reserves.py`, `safe_to_spend.py`,
  `spend_pocket.py` and `dial.py`.

**Conclusion: the gap is not Crew shapes.** Every shape the connector can perform is reachable, and the gating
design was recorded before this branch existed. What is missing is the machinery that **persists and uses** them —
and, above all, the evaluation harness that would prove any of it useful.
