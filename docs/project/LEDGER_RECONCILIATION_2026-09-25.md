# Ledger reconciliation and the next most pressing slices (2026-09-25)

The owner asked for this directly, and the reason is a real failure on my part: when I offered him a
"what next" menu I read the ledger's **statuses** and presented them as current state. He corrected
two of them from his own use of the app — Settings has been reachable for a while, and Today's "View
bill" populates the invoice with a back button. Both corrections are right. A ledger is a record, not
a measurement, and anything I present as pressing has to be checked against the code first.

This reconciles every unfinished entry that could plausibly be next, with the evidence for its true
state, and then ranks the work that is actually open.

## 1. Corrections, each verified

| task | ledger said | verified state | evidence |
|---|---|---|---|
| **OS-093** Today: 'View bill' opens Plan, ticket never carries evidence | `in_progress` | **DONE — superseded by OS-101** | `static/js/meridian/dial.js:1444-1460` resolves the invoice and falls back only when nothing matched; commit `8ccba32` "View bill opens the bill's mail-ingested invoice, resolved by Plan's own matcher"; OS-101 is `complete`. Owner-confirmed from the app. |
| **OS-081** Settings hub unreachable + unusable at desktop | `open`, high | **DONE — both halves** | Reachable: `templates/meridian/partials/navigation.html:75-78` renders `data-settings-link → /meridian/settings` in the shell. Usable: rendered at **1440×900** and **420×912** — hub present, `.m-settings-nav` visible, 7 links laid out, `docOverflow 0`, no console errors. The Payday row reads "The paycheck Crew pays you from" (the OS-104 rename is live). |
| **OS-001** Reconcile current implementation and select first vertical slice | `ready`, critical | **SUPERSEDED** | It is the umbrella that produced this ledger; 100+ entries later it cannot be "next". Its function is served by this document. |
| **OS-082** Adopt the medallion treatment across the app | `open`, high | **PARTLY DONE, and its caution needs a resolution note** | The Settings hub rows already carry the kit medallion treatment, and the three Accounts emblems shipped 2026-09-24 (`af6f475`). OS-082's note forbids reading it as authority to spread *generated* artwork beyond the Investigator surface — correct, **but the owner's 2026-09-24 choice explicitly authorised the concept's three emblems on the Accounts rows for the three accounts concept 04 names**, which supersedes that caution for that surface and only that surface. Still open: the treatment on Today/Activity/Plan rows, and the Plan rows are blocked on category data (OS-088). |
| **OS-104** Payday/funding — write side | `ready`, `decision_owed` | **AUTHORISED, now actionable** | Owner, 2026-09-25: *"Meridian writes them too"* — write commands for FREQUENCY / DAY / IDENTIFICATION, on the funding-plan pattern (proposal where the router says so, readback verification, never auto-retried), as its own bounded slice. |
| **OS-067** Calendar daily trigger | `in_progress`, blocker recorded | **DECIDED, one piece left** | Owner, 2026-09-25: *"The harness runs it"* — a daily harness job calls Composio and feeds Meridian, so the app keeps holding no Composio credential. The app-side ingest is built, off by default, read-only, with 18 tests asserting absence (`tests/meridian/test_calendar_context.py`). What is missing is the harness-side daily job and its honest liveness reporting. |

Checked and **not** corrected, for the record:

- **OS-079** (Safe to Spend explanation) is genuinely open, and the owner's memory is right that it was
  never built: a repository-wide search for any explanation affordance on that figure returns nothing —
  the only match is a loading string in `today.js:365`. His verbatim request stands: *"I want to add a
  mouse over or clickable on safe to spend that shows how its calculated in the app- should be a cheap
  add."*
- **OS-084** is verified, not assumed: `app.py:1299-1317` `_meridian_memory_proposal_sink` calls
  `action_store.propose(...)` unconditionally and never consults `meridian/write_routing.py`, so bills,
  rules, assets and contracts **park the owner's own unambiguous edits** while `/api/actions/mutate`
  executes them. That contradicts D-020 and is friction on his own edits, not a safety hole — parking is
  the safe direction.
- **OS-074** (council mechanics): `meridian/ai/council.py` and `meridian/ai/skeptic.py` both exist, so
  more is built than "unstarted" implies — but file presence is not completeness, so this one is flagged
  for verification rather than closed.
- **OS-059** (Crew's Autopilot settings): only the *create-a-rule* path mentions `sweepExcess`
  (`plan.js:1338`), so Crew's settings — surplus pocket, early funding, automatic top-ups, optimize cash
  flow, the 1800 sweep threshold — are still not readable in Meridian.
- **OS-058** is a future-dated measurement (the 2026-10-02 funding event) and cannot be brought forward.

## 2. The next most pressing slices

Ranked by what he has actually asked for, what is verified missing, and what unblocks other work.

**S1 — Safe to Spend, explained (OS-079).** His own verbatim request, and the only one of these he has
already told me he wants: the flagship number on the first screen cannot show its working. It is also
the class of defect he found by hand (the reserve overdraft, `424.90 − 324.90 = 100.00`): with an
explanation affordance, that arithmetic is visible instead of discovered. Small, mobile-first, read-only.

**S2 — The paycheck sections Meridian may write (OS-104 write side).** He authorised it today. It
completes the mechanism end to end and is the first *new* write capability since the funding-plan
actions: owner-stated values only, routed by the existing pipeline (execute when unambiguous, propose
otherwise), readback verification, never auto-retried. It is also the mission's own test — authority
moving deliberately, in one bounded slice.

**S3 — The daily calendar observation (OS-067, harness side).** He decided who runs it. The app half is
built and inert; the remaining piece is the harness-side daily job plus liveness that says what was
*observed*. This is the evidence lane he complained about, and calendar context is read-only and never
matched to money.

**S4 — Put the management routes on the write router (OS-084).** Verified defect: his own unambiguous
edits to bills, rules, assets and contracts park for approval while the same class of edit through
`/api/actions/mutate` executes. Fixing it makes the write model one thing instead of two, and it is the
kind of inconsistency that erodes trust in what "pending" means.

**S5 — Repay the test debt (OS-097).** Five browser guards fail in this environment and all five
pre-date the current work. Not a feature, but the gates are only worth running if they can pass.

**Not yet, and why.** **OS-063** (unforeseen cost → one validated plan of proposals) is his original
motivation for Meridian's AI and remains the destination, but its prerequisites are unmet and it is
larger than a slice: it needs the constraint model (his "at least $600 free to spend each pay period"),
the proposal planner and the council. **OS-076 / the Investigator surface** and **VIRGIL-A0** both need
an approval from him before they can start (A0 asks him to approve the Virgil contracts and the iOS
toolchain). **OS-086** (image-generation tooling) is research: `GEMINI_GENERATE_IMAGE` is restricted in
this environment, and the two Figma tools export existing nodes rather than generating illustration —
which is also why a raster star master for the Accounts emblems is parked rather than promised.
**OS-058** is future-dated. **OS-069/OS-070** (unmodelled recurring charges, trial watch) are good
proactive work and are the natural companions to S1 once the numbers can explain themselves.

## 3. What this changes about how I present options

A status field is a claim, and I presented claims as facts. The rule I should have followed, and will:
before offering a menu of "what's next", verify each candidate against the code and say what the
verification was — which is what this document does, and why OS-093 and OS-081 are now closed rather
than offered.
