# Independent verification — 2026-09-25

**Role.** Adversary, not reviewer. Each claim below is re-derived with an instrument the original did **not**
use, and reported CONFIRMED / FALSIFIED / COULD-NOT-CHECK with the instrument named. Claiming a row in
`AGENT_COORDINATION.md` was done first; no application code is written by this pass, scratch work lives in
`/tmp`, and no provider write is attempted anywhere.

**How to read this.** A CONFIRMED verdict means the claim survived a *different* instrument — not that the same
number was seen twice (that would be determinism, not truth). COULD-NOT-CHECK is a first-class result and is
listed first wherever it occurs, because it is where a reader's trust should stop.

---

## Claim 5 — "the orphan list is exactly one module"

**As written** (`docs/project/STATE_OF_THE_SYSTEM.md:76-80`): *"1 of 112 modules under `meridian/` are never
named by any other module, the app, a script or a test (dotted-path search). A module here is buried, not lost…
`meridian/ai/investigation_service.py`"*. Its instrument is `_orphan_modules()` in
`scripts/state_of_the_system.py:144-162`, a **text search over dotted paths**. The document itself discloses
that this instrument *"cannot follow a module loaded by file path (`spec_from_file_location`)"*.

**My instrument (different):** runtime import tracing. A rail-hardened harness imported the real application
with the socket layer denied outright, against a scratch database copy under `/tmp`, then exercised the HTTP
surface and recorded every file under `meridian/` that Python actually loaded. Text search was never performed.

**Result: COULD-NOT-CHECK for the claim as written, and one new finding confirmed.**

- **COULD-NOT-CHECK (count).** The claim is about *being named by a dotted path*; this instrument measures
  *being loaded at runtime*. Those are different questions. **The 64-of-112 figure this harness produced is a
  statement about the harness's reach and must not be quoted as an orphan count.** It is recorded here so it is
  not mistaken for one.
- **Not falsified (the named module).** `meridian/ai/investigation_service.py` was not loaded at runtime under
  this harness either, which is consistent with the claim. It does **not** confirm it: "not loaded here" is not
  "nothing calls it", and this instrument cannot see naming.
- **NEW — CONFIRMED by this instrument: the application loads exactly three files from `meridian/ai/` —
  `__init__.py`, `advisor.py`, `classifier.py` — and does not load the agent-role layer at all** (`role.py`,
  `envelope.py`, `run_records.py`, `council.py`, `investigator.py`, `skeptic.py`, `facts.py`, `evaluation.py`).
  Measured with the money surfaces executing (Today, Plan, Activity, Accounts, Dial, Transactions all returned
  200) and the advisor surfaces reached **by their real methods** (`GET /api/advisor/status` → 200,
  `POST /api/advisor/chat` → 400). This independently corroborates the audits' "built but unwired" finding with
  a different instrument, and sharpens it: **it is the agent-role layer that is unwired, not the AI subsystem** —
  the advisor and classifier paths are loaded and serving.
- **Observation, not a claim about the repository: importing `app.py` starts background workers.** A
  credit-card transaction checker thread began on import and ran against the scratch database every 30 seconds.
  Note that `scripts/state_of_the_system.py` does **not** import `app` (0 hits), so this document's generator is
  unaffected — but any tool that imports the application inherits those workers.

**Scope of my reach, stated so the numbers cannot travel without it:** 13 GET requests (6 authenticated money
surfaces returning 200, 3 redirects, 4 not-found) plus 2 advisor calls; no POST to any money route, deliberately,
because that would be a provider write. A module imported lazily inside an unexercised view would be invisible
to this instrument.

---

## Claim 1 — "17 of 17 bound to a governed action with an executor (16 with a readback verifier)"

**As written** (`docs/project/INTEGRATION_AUDIT_2026-09-25.md:68`, echoed at `STATE_OF_THE_SYSTEM.md:13-17`).
The original established it by **reading** the registries.

**Instrument (different): EXECUTION.** The real pipeline was driven against a scratch DB in `/tmp` — the real
`ActionStore`, the real `ExecutorSpec`, the real `execute_approved_action` — with four guard layers installed
before import: socket denied outright; `subprocess.run`/`Popen` replaced (both provider boundaries are
subprocesses — `crew-write` and `crew-readonly`, both Keychain-backed and both executable on this machine);
`sqlite3.connect` refused outside `/tmp`; both binaries redirected to nonexistent paths plus an argv tripwire. A
guard self-test proves the tripwire fires on the real binary path. Result: **33 subprocess calls intercepted, 0
network events, 0 real-binary touches**, and the code under test unchanged during the window.

**VERDICT: both halves CONFIRMED, each with one measured refinement. No falsification.**

- **"17 of 17" — CONFIRMED as a bijection, verified by the operations actually dispatched rather than by name.**
  17 action types → 17 distinct CLI operations, exactly one each; the dispatched set equals the runtime
  allow-list exactly (0 never sent, 0 sent-but-undeclared).
- **"16 with a readback verifier" — CONFIRMED as present AND reached on the execution path, and CONTINGENT on
  provider content rather than canned.** 16 verifier objects, 16 actually invoked, each after the write and each
  performing exactly one provider readback; the timeline is execute → write → verifier → readback for all 16.
  With a complete-but-empty synthetic readback, `archive_crew_bill` and `delete_crew_pocket` returned
  `ok=True`/VERIFIED while others returned `ok=None` with action-specific reasons; with the readback refused,
  all 16 returned `ok=None` "readback unavailable"; a crashing verifier was recorded as check
  `verifier-exception`, state `executed` — **never VERIFIED**.
- **The single action without a verifier is `top_up_crew_reserve`, and it is deliberate.** The connector payload
  carries no `billReserveId`, so a top-up cannot be attributed to the reserve it targeted
  (`docs/project/write-coverage.json` records "none" with that reason), and the pipeline has an explicit runtime
  branch producing check `no-verifier-registered`, `ok=null`. Measured safe for the properties in scope:
  executing before approval raises `IllegalTransitionError` and dispatches 0 writes (state stays `proposed`);
  one execution → `executed`, `ok=null`, and no unverified write ever reaches `verified`; re-execution with the
  SAME key and with a NEW key both raise `IllegalTransitionError` and dispatch 0 writes — **no replay, no
  auto-retry.**

### Refinement 1 — a registration count is not an every-attempt execution count

Production wiring passes `precondition=...` (`app.py:1277`), and **`update_crew_bill` is the only action type
carrying one.** With the precondition installed and **no recorded base_state**, `update_crew_bill` is refused
*before* dispatch: executor not called, verifier not reached, 0 provider calls
(`sent_to_provider: false`, error `precondition_unverifiable`), state `failed`. So on the execution path the
counts are **16/17 dispatched and 15/16 verifiers reached** in that configuration, and **17/17 and 16/16** once a
reviewed base_state is present (seeded through the real `capture_base_state`).

`STATE_OF_THE_SYSTEM.md`'s "16" is a **registration** count and reads correctly as one. It is **not** an
every-attempt execution count, and any restatement of it as "16 verifiers run on every execution attempt" is
**falsified** — 15 do, on unreviewed approvals. The refusal itself is the safe direction and is by design.

### Refinement 2 — a third name map that reproduces the D-039 phantom gap

The 17/17 above lives in the CLI-operation ↔ governed-action space, linked **by execution** (the executor
literally sends `argv[1]`). A third map exists: `crew_commands._SPECS` has 12 specs keyed on **local** names that
do not match the CLI operations — only 6 of 12 keys have any name-level match in the allow-list, and only 1 of
the 12 specs is reached during a full 17-action sweep. **A name-keyed comparison of these two maps reproduces
exactly the phantom-gap mechanism D-039 warns about.** Recorded because the next person to compare catalogues
will be tempted to do it by name.

### Instrument integrity, and one refuted hypothesis

The verification ran while this repository was being committed to by a sibling agent: HEAD moved `8923958` →
`18737b0` (this pass's own record) mid-run. The verifier checked that **no commit touched any file under
test** and that all eight files' mtimes predate the run window — which is the state discipline this repository
keeps having to relearn, applied correctly here. It also declined to import `app.py`, because that module runs
`init_db()` **and mints secrets at module level**; it read the file with `ast` only, and labelled that reading a
*precondition*, explicitly not evidence.

A refuted hypothesis, recorded because the discipline matters more than the finding: the first sweep showed
`create_autopilot_rule` never dispatched, which looked like a registered-but-unreachable operation. It was the
verifier's own defect — that executor routes through the verified formula builder, which requires snake_case
parameters, and camelCase inputs made it raise before dispatch. With fair parameters it dispatches like the
other sixteen. **A refuted hypothesis is not a finding, and it was not reported as one.**

Also confirmed as a precondition rather than a claim: all six facet methods the verifiers call
(`readback_transfers`, `readback_funding_plans`, `readback_autopilot_rules`, `readback_reassignment_rules`,
`readback_virtual_cards`, `readback_selected_spend_pocket`) exist on the real adapter; the single exception in
the injected-truth run was a gap in the verifier's own fake.

**COULD-NOT-CHECK: the provider-mutation-name level.** The connector payload contains only `{"input": {...}}`
(verified for `create_autopilot_rule`, `create_bill`, `archive_bill`); no mutation name is transmitted, and the
name→mutation mapping lives inside the connector binary, which must not be run. Mutation names are visible only
through `crew_commands.operation_name` (e.g. `DeleteBill`, `CreateSubaccount`) and could not be tied to the
connector's own names by this instrument. **`STATE_OF_THE_SYSTEM.md:43-45` already discloses this** — it states
that carrier status is recorded in `OS119_MIGRATION_BY_EVIDENCE.md` and that it "cannot be re-derived from this
tree alone". This verdict therefore confirms the document's own honesty rather than contradicting it.

---

## Claim 4 — "the allocation ordering rule" — **FALSIFIED**

**As written** (`docs/project/OS058_FUNDING_EVENT_MEASUREMENT.md`):
- `:172` — *"**Crew's `bills` array is a SORT, not a fixed list — and the key is now proven.** Order matches
  `(daysOverdue desc, reservedBy asc)` on BOTH dates, exactly"*
- `:109` — *"consistent with `daysOverdue DESC`, then `reservedBy ASC`, plus a deterministic tie-breaker"*
- `:401` — *"the ordering and the tie-break: higher `daysOverdue` → earlier `reservedBy` → **lower bill
  amount**"*

`STATE_OF_THE_SYSTEM.md` and `INTEGRATION_AUDIT_2026-09-25.md` assert **no** allocation-ordering rule (a
negative, established there by exhaustive keyword search — `:110-125` explicitly lists provider-side
attribution as unreadable).

**Instrument (different): the raw provider read.** The only raw provider material that survives is
`Simplecrew Branch/data/live_crew_snapshot.txt` (80,538 B, sha256 `138d6b7328ffd17e…`, captured
2026-09-04T18:10:19Z, `mode=read-only`, `complete=True`, `mutations_enabled=False`) — one
`accounts[0]/billReserve/bills` array, 5 bills. Its own fields were sorted by an independent script
(`/tmp/raw_derive.py`, `/tmp/raw_derive2.py`; nothing written to the repository). The author's rule came from
two owner-authorized **injected** experiments and his "09-04 column" is a transcription of the array, not an
independent re-sort.

**Four falsifications.**

- **F1 — the rule's PRIMARY sort key is unobserved on the only raw capture.** All five bills carry
  `daysOverdue` **present-but-NULL** (0 explicit zeros, 0 non-null). `daysOverdue DESC` is therefore
  indistinguishable from omitting it, and *"the key is now proven"* is not proven by any raw read that exists.
  What the raw read does prove is the **secondary** key: raw array order equals `reservedBy ASC` exactly
  (09-16, 09-16, 09-20, 09-22, 09-28), and differs from `amount` in both directions. The 09-25 array exists
  **only as a document transcription** — no raw payload for it survives in either tree — and it is not
  reproducible by any pure sort on provider fields (two bills tie on both date and amount).
- **F2 — the rule's full form misorders the credited bill on the raw read.** Derived independently over the raw
  fields, treating absent as 0 as the document does, the order is [B2, B1, B3, B4, B5]; the raw array is
  [B1, …]. B1 and B2 share the soonest `reservedBy`; B2 is the **lower** amount and holds 0.00, while B1 is the
  larger and holds the entire bucket (1 of 5 rows non-zero). The asserted tie-break — *lower amount wins an
  equal deadline* — **predicts the wrong bill** on the only natural, unfixtured raw allocation available. The
  document itself marks this contradiction **OPEN** (`:232-237`); the application's status record still relies
  on it operationally (`CURRENT_STATUS.md:25-26`: *"under the measured equal-deadline ordering the smaller
  probes outrank it"*). **A contradiction its own source calls open is being used as a live premise.**
- **F3 — absent and zero are conflated.** On this same capture `reservedAmount` is present with 4 explicit
  zeros and 1 non-zero — the repository's own distinction is directly observable — while `daysOverdue` is
  present-and-NULL for every bill. The rule folds NULL into the same term as 0, and nothing documents how a
  NULL key orders; a mechanical Python port of the rule raises `TypeError` on this exact payload.
- **F4 — the application does not implement the ordering the claim attributes to it.** `app.py:2059` sorts
  bills by `reservedBy` ascending with a `"9999-12-31"` null sentinel and **drops `daysOverdue` entirely**;
  `meridian/**` never references `daysOverdue` (it appears only in the raw GraphQL field list,
  `app.py:2002`); the single consumer of `reserved_by` is `meridian/services/dial.py:275`, which compares ONE
  bill's deadline and never an order. The only stored allocation series carries no `daysOverdue` and is 100%
  zero-or-silent (11,484 rows across 1,044 captures, 0 non-zero, 0 silent-but-... as measured).

**COULD-NOT-CHECK:** cascade/capacity behaviour, which needs a natural non-zero provider read. All non-zero
evidence in this repository is injected (owner-authorized top-ups), and the continuous store begins after the
unwind (22:30:58Z).

**CONFIRMED (narrow):** `reservedBy ASC` as the observable secondary ordering — the entire 2026-09-04
single-read state is fully described by *array = reservedBy-ascending*.

**Where the claim is asserted, and where it is not.** Asserted at
`OS058_FUNDING_EVENT_MEASUREMENT.md:109`, `:130-131`, `:172`, `:401`; carried as fact in the tasks ledger at
`MERIDIAN_OS_TASKS.json:2872` and `:1464`; reported at `CURRENT_STATUS.md:30` and `:66`. **Not** asserted in
`STATE_OF_THE_SYSTEM.md` or `INTEGRATION_AUDIT_2026-09-25.md` — both assert no ordering rule, and the former
explicitly lists "the reserve's internal attribution" among provider-side state invisible to every instrument
here. So the falsification lands on the measurement document, the ledger and the status record, not on the two
documents this pass was pointed at.

**Candidate orderings, side by side on the raw read** (bill positions only; the provider's own figures are
deliberately not reproduced here):

| candidate ordering | derived | vs raw array |
|---|---|---|
| `(daysOverdue DESC, reservedBy ASC, amount ASC)` — the asserted full rule | B2, B1, B3, B4, B5 | **DIFFERS** |
| `(daysOverdue DESC, reservedBy ASC)` — the asserted core | B1, B2, B3, B4, B5 | matches |
| `(reservedBy ASC)` — what `app.py:2059` actually does | B1, B2, B3, B4, B5 | matches |
| `(array position)` — creation/id order | B1, B2, B3, B4, B5 | matches |
| `(amount ASC, reservedBy ASC)` | B2, B5, B4, B3, B1 | DIFFERS |
| `(amount DESC, reservedBy ASC)` | B1, B3, B4, B5, B2 | DIFFERS |

**A scope limit on the confirmation, not just the falsification:** on this single read, `reservedBy ASC` and
plain array position are *indistinguishable*, so the raw material confirms the secondary key only as "deadline
ascending", and cannot separate it from the array simply being in creation order. The claim says creation order
was refuted — by the injected experiments, which are not raw material. What discriminates instead is the
**state**, and it is recorded as shares rather than amounts: exactly one bill is non-zero, it is the largest of
the array and holds the entire bucket, while the smaller of the two soonest-deadline bills holds nothing.

**Store counts** (read-only, `mode=ro`): the dated allocation series holds **11,484 rows across 1,044 captures,
0 non-zero and 0 silent**, and its schema has **no `daysOverdue` column** — so the rule's primary key has never
been captured on the app side either.

**Instrument limits, stated so nothing is over-read.** `daysOverdue` is plausibly derived from the anchor and
day-of-month and null because none of the five anchors had passed on that date — consistent with the data and
**untested by it**; no claim is made about the mechanism. A single read is also consistent with a mid-cascade
state, and a cascade needs a second read that does not exist.

**Consequence, stated without prescribing a fix:** the claim is unsupported at the primary-key level by any raw
data that exists, contradicted at the tie-break level by the one natural raw allocation, and **not implemented**
in the application — while remaining in operational use in the status record.

---

## Claim 3 — "Today and Plan publish one money rule" — **FALSIFIED, narrowly**

**As written** (`STATE_OF_THE_SYSTEM.md:106`, the guards table): *"tests/meridian/test_safe_to_spend_agreement.py
(yes) | Today and Plan publish one figure from one rule"*; also `AGENT_COORDINATION.md:150` and
`TODAY_PLAN_SPEND_ALIGNMENT_2026-09-25.md:8`. The binding instruction is D-024
(`MERIDIAN_DECISIONS.md:460`), whose rule is: `total = Σ money accounts + reserve` (SIGNED), set aside = every
active pocket except the spend pocket, positive balances only, `amount = total − set aside − max(0, reserve)`,
**never clamped**.

**Instrument (different): the app's HTTP surface.** `app.test_client()` against the real application — through
Flask routing, `@login_required`, `@_safe_read`, the repository-factory seam, query-string parsing and
`jsonify`. Scratch SQLite in `/tmp` with the app running its own migrations and invented accounts seeded through
the repository API; provider client and health service replaced with abort stubs; sockets refused on any
non-local address (zero violations, nothing left the machine). The author's evidence is a Python-function
comparison inside the unit fixture (`build_today()`/`build_plan()` over a seeded repository), which bypasses
every layer above.

**The falsification — the unobserved state.** In **4 of 21 scenarios** both endpoints returned HTTP 200 and the
same quantity diverged:

| scenario | Today `safe_to_spend.amount` | Plan `allocation.cash_total` |
|---|---|---|
| nothing observed at all | **null**, status `unavailable` | **0.0**, segments all 0.0 |
| only a credit-type account | **null** | **0.0** |
| only a reserve row, no accounts | **null** | **0.0** |
| only EUR money, figured currency USD | **null** | **0.0** |

These are the same quantity by the project's own mapping — *"the same number, same rule, same repository"* — so
this is not a shape difference. In the fourth case both surfaces **know** money exists (Today's
`available_cash.by_currency` shows EUR) while Plan still publishes a USD-shaped zero.

**Adjudication, which the verifier read afterwards and did not treat as its own instrument:** the claim's own
guard asserts this exact asymmetry — `tests/meridian/test_safe_to_spend_agreement.py:260-264` requires Today's
amount to be `None` with status `unavailable` **and** Plan's segments to be `[0.0, 0.0, 0.0]`; its docstring
(`:244-245`) states: *"Neither workspace may invent a 0.00: that would claim an observation the read did not
make. Today withholds the figure and says unavailable; Plan's partition is three zeros."* So the falsification
is of **the claim as written** and of the project's own absence rule (D-017/C01) — **not** of the author's
declared acceptance condition, which names the exception. A reader who accepts the guard's exception would call
it CONFIRMED.

**Ledger sentence, as the verifier framed it:** *"the shared rule is confirmed wherever a figure is stated, but
the pair does not publish one figure in the unobserved state — Today withholds, Plan states 0.00 — and the guard
encodes that asymmetry as intended."*

**Confirmed by the same sweep (17 of 21), including both pre-registered discriminators:** a positive reserve; a
**negative** reserve that reduces the figure and is **not clamped** (D-019 rule 2); mixed signs; an overdrawn
set-aside pocket; inactive pockets and inactive checking; investment-type accounts; a non-USD currency;
Crew-selected spend pocket (basis `crew_selection`) including where the selection contradicts the spend name.
Side check: `?as_of=2000-01-01` and `?as_of=2030-01-01` leave both figures unchanged — no `as_of` dependence in
the money figure.

### F2 — a shared-rule collapse, not a divergence: silence and a reported zero are the same number

A reserve row with `total_reserved_amount` **NULL**, **no row at all**, and a **reported 0.00** all publish the
identical pair (Today and Plan agree with each other in all three). The reserve term therefore does not
distinguish "the provider said nothing" from "the provider said zero" — the distinction this repository enforces
elsewhere (migration 031's `reported` flag) and the one F4/§Evidence-map work depends on. **Both surfaces are
wrong together**, which is why a pair-agreement test cannot see it.

### F3 — observation, not a falsification: the "Safe to Spend" name hazard, measured

With two ACTIVE pockets both named "Safe to Spend", Today reports `spend_pocket_basis: "name"`, subtracts one of
them, and Plan follows. The surfaces agree; **the arbitrary pick lives inside the shared rule**, exactly where
the owner's recorded hazard says it would.

### ⚠ Warning for any future harness: `/plan` is not isolated from live data by a scratch database

`meridian/services/plan.py:71` reads a **real local file** — `~/Library/Application
Support/SimpleCrew/live_crew_snapshot.txt` — for its `crew_ids` block, regardless of which database the app is
pointed at. An early exploratory run **surfaced a real subaccount identifier** from it (not reproduced, and not
recorded here). The verifier isolated it by pointing `plan._CREW_SNAPSHOT_PATH` at a non-existent path, and every
figure above was produced with that stub in place (the figures were unchanged by it). **A scratch DB is not
sufficient isolation for `/plan`.**

### Could not check over HTTP

Whether Plan's published `0.0` reaches the owner as a *rendered* figure: `static/js/meridian/plan.js:185` reads
`…find(s => s.label === "Available")?.amount || <fallback>`, and `0.0` is falsy, so it may fall through to a
fallback at the render layer. Not driven in a browser, so **not claimed**. The live-provider path was not driven
and must not be.

---

## Claim 2 — in flight

| # | claim | instrument prescribed | status |
|---|---|---|---|
| 2 | the ungoverned write surface is exactly the 26 declared routes | hit the routes through HTTP with the provider stubbed | in flight |

Their verdicts are appended below when they return. Each will carry its instrument, its scope, and its own
COULD-NOT-CHECK column; any falsification goes to the owner first, as instructed.
