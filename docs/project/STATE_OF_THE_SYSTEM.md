# State of the system — GENERATED, do not edit

Regenerate with `python scripts/state_of_the_system.py`. Input hash `ac7fcbaf181e2590`.

Everything under *Derived from code* comes from parsing or importing the code the app runs, so it cannot
drift: `tests/test_state_of_the_system.py` regenerates this file and fails when the committed copy is
stale. Everything under *Snapshot at generation time* is read from documents and is **excluded** from the
staleness check on purpose, so ordinary documentation edits do not invalidate this file.

## Derived from code — the money path

| | count |
|---|---:|
| operations the executor is allowed to send | 17 |
| governed actions registered | 17 |
| governed actions with a readback verifier (a REGISTRATION count) | 16 |
| allowed operations with NO governed action | 0 |

A registration count is not an every-attempt execution count. An independent lane drove the dispatch path and
found 16/17 actions dispatched with 15/16 verifiers REACHED when an approval carries no reviewed base_state
(`update_crew_bill` is refused before dispatch), and 17/17 with 16/16 when it does — never restate the row above as
every-attempt behaviour (`INDEPENDENT_VERIFICATION_2026-09-25.md` §Claim 1).

**Actions with no verifier** (a write whose result is never read back):

* `top_up_crew_reserve`

## Derived from code — write routes

| | count |
|---|---:|
| route decorators parsed STATICALLY (app + meridian blueprint) | 140 |
| — of those, accepting POST | 74 |
| route rules at RUNTIME (independent harness) | 200 |
| — of those, accepting POST | 98 |
| POST routes declared to reach a raw Crew mutation | 26 |

The two route populations above are NOT interchangeable: a static decorator parse cannot see blueprint or
`add_url_rule` registrations. The runtime figures are the independent verification lane's, quoted with their
instrument for that reason (`INDEPENDENT_VERIFICATION_2026-09-25.md` §Claim 2). The static count is the one that
stays reproducible here; the runtime count is the one that describes the app.

The declared set is asserted exactly by `tests/test_governed_write_routes.py`, which fails both when the
set grows and when a declared route is fixed without updating the declaration. It is therefore the
denominator for OS-119: the shape decision concerns exactly these routes. Per the declaration's own
comments it is composed of 9 routes the 2026-09-25 audit reached and 17 found by the ratchet on its first
run — and one of them (`/api/cards/<card_id>/sensitive`) mints a card-details view token rather than
moving money, which is why the FINANCIAL count and the DECLARED count differ by one. Quote whichever the
question is about, and say which.

## Derived from code — what each ungoverned route actually performs

The ratchet answers *whether* a route reaches a raw mutation; the shape decision for OS-119 needs
*which* one. Both come from the same detector, so there is one definition of "reaches a raw mutation"
in this repository. Whether a mechanism has a governed carrier is recorded in
`docs/project/OS119_MIGRATION_BY_EVIDENCE.md`, which cites the connector's own document list as its
instrument — a cross-repository fact that cannot be re-derived from this tree alone.

| route | raw mechanism(s) reached |
|---|---|
| `/api/account/autopilot-rules/create` | `CreateRoundUpRule` |
| `/api/account/autopilot-rules/delete` | `DeleteRule` |
| `/api/account/autopilot-rules/update` | `EditRoundUpRule` |
| `/api/cards/<card_id>/sensitive` | `GenerateViewSadToken` |
| `/api/create-bill` | `CreateBill`, `create_bill_action` |
| `/api/create-pocket` | `CreateSubaccount`, `create_pocket` |
| `/api/delete-bill` | `DeleteBill`, `delete_bill_action` |
| `/api/delete-pocket` | `DeleteSubaccount`, `delete_subaccount_action` |
| `/api/lunchflow/change-account` | `DeleteSubaccount`, `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `delete_subaccount_action`, `move_money` |
| `/api/lunchflow/create-pocket-with-balance` | `CreateSubaccount`, `create_pocket` |
| `/api/lunchflow/stop-tracking` | `DeleteSubaccount`, `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `delete_subaccount_action`, `move_money` |
| `/api/lunchflow/sync-balance` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/manual-cc/create` | `CreateSubaccount`, `create_pocket` |
| `/api/manual-cc/remove` | `DeleteSubaccount`, `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `delete_subaccount_action`, `move_money` |
| `/api/manual-cc/top-up` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/move-money` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/set-card-spend` | `SetActiveSpendPocketScottie`, `UpdateVirtualDebitCard`, `for`, `set_spend_pocket_action` |
| `/api/simplefin/change-account` | `DeleteSubaccount`, `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `delete_subaccount_action`, `move_money` |
| `/api/simplefin/create-pocket-with-balance` | `CreateSubaccount`, `InitiateTransferScottie`, `create_pocket`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/simplefin/disconnect` | `DeleteSubaccount`, `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `delete_subaccount_action`, `move_money` |
| `/api/simplefin/stop-tracking` | `DeleteSubaccount`, `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `delete_subaccount_action`, `move_money` |
| `/api/simplefin/sync-balance` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/simplefin/sync-now` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/splitwise/create-pockets` | `CreateSubaccount`, `create_pocket` |
| `/api/splitwise/disconnect` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |
| `/api/splitwise/sync-now` | `InitiateTransferScottie`, `crew_client(is_mutation=True)`, `move_money` |

## Derived from code — modules nothing else names

1 of 112 modules under `meridian/` are never NAMED by any other module, the app, a script or a test (dotted-path text search). This is a NAMING instrument and it does not answer whether a module is LOADED. An independent runtime tracer, exercising 13 GET responses, found that the application loads only three files from `meridian/ai/` — `__init__.py`, `advisor.py`, `classifier.py` — and does NOT load the agent-role layer at all (`role`, `envelope`, `run_records`, `council`, `investigator`, `skeptic`, `facts`, `evaluation`); see `INDEPENDENT_VERIFICATION_2026-09-25.md` §Claim 5. Do not read a short list here as "nothing is buried": it is a claim about NAMING.

* `meridian/ai/investigation_service.py`

## Snapshot at generation time (excluded from the staleness check)

| | |
|---|---|
| tasks in the ledger | 137 |
| — blocked | 10 |
| — complete | 79 |
| — done | 18 |
| — in_progress | 6 |
| — open | 13 |
| — ready | 11 |
| tasks carrying an owner question | 16 |

## What is checked, and by what

| guard | the claim it protects |
|---|---|
| `tests/test_governed_write_routes.py` (yes) | no provider-mutating route escapes the governed pipeline |
| `tests/test_slice_onset_ceremony.py` (yes) | every in-progress slice declares plan + model + why |
| `tests/test_supersession_before_restore.py` (yes) | nothing old is restored without a supersession check |
| `tests/test_task_blockers_are_explained.py` (yes) | a blocked task names its blocker and its owner question |
| `tests/test_concept_coverage.py` (yes) | the 22 concepts keep a carrier and an audited state |
| `tests/test_session_close.py` (yes) | session close reports clean / pushed / current |
| `tests/test_roadmap_handoff_check.py` (yes) | the roadmap and the ledger reconcile |
| `tests/meridian/test_safe_to_spend_agreement.py` (yes) | Today and Plan publish one figure from one rule |
| `tests/meridian/test_static_assets_tracked.py` (yes) | shipped trees and the git index agree |
| `tests/meridian/test_ai_evaluation.py` (yes) | the evaluation harness refuses to report health over nothing |
| `tests/test_state_of_the_system.py` (yes) | this document is current, and still says what it cannot check |

## What this document does NOT check

This section is the honest half, and a test refuses to let it be deleted.

* **Semantics.** Registration and reachability are not behaviour. An action can be wired, verified and
  still wrong, and nothing here evaluates whether a feature does what the vision says.
* **Provider-side state we do not read.** The reserve's cash balance, the sweep threshold, the
  pocket-transfer allocation settings, the reserve's internal attribution when no read has run — all
  invisible to every instrument in this repository (OS-059).
* **Whether a guard asserts the right thing.** A vacuous or miscalibrated test passes. Nothing here
  checks a check's premise — the failure class that produced 'a gate needs a floor, not a minimum'.
* **Anything before continuous recording existed.** Per-bill allocation history begins 2026-09-25
  22:30:58Z; earlier states survive only as captures, and a capture is not a series.
* **Other trees, other lanes, and managed Documents** unless someone enumerates them. This is D-042's
  channel problem: a fact can be documented, current, and simply never read.
* **Live data quality.** Sync gaps, staleness and torn reads are not visible here; only schema and
  timestamps are, and a populated schema is not populated data.
* **The set of things no instrument mentions at all.** Invisible by construction. The orphan scan is the
  closest thing to a denominator, and it covers Python imports only — not templates, JS, routes or docs —
  and it cannot follow a module loaded by file path (`spec_from_file_location`), which is how a module can
  be used and still read as unused here.
* **Intent.** Coverage measures carriers, never whether the carrier is the right product decision.
