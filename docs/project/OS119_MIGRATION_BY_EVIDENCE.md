# OS-119 — the shape: migration by evidence, one route at a time

**Why this document exists.** OS-119 was framed as one global choice — migrate all 25-ish raw routes, fence
them, or accept them as documented risk. The owner's objection to that framing is correct and is the premise
here: *"I don't know the right answer to 119 because I don't know what's actually true."* A global choice
requires global trust, and global trust is exactly what a reader cannot have. So this shape removes the
global question. Each route moves only when **its own** evidence is complete, nothing is ever removed, and
stopping halfway loses nothing.

**The denominator is the DECLARED set, and an independent sweep has not confirmed it complete.** The independent verification lane (2026-09-26, `docs/project/INDEPENDENT_VERIFICATION_2026-09-25.md` §Claim 2) measured the RUNTIME population at **200 route rules, 98 accepting POST**, while the generated document's static parse reports 140/74 — different populations, not interchangeable — and found `/api/cards/<card_id>/sensitive` to be **GET-only at runtime** while standing in a set described as POST routes. Both verdicts are INTERIM, and an earlier sweep was gated by local database state (15 declared routes), so "0 undeclared" was stated against an incomplete denominator. Consequence: **"22 of 26 ready" is a statement about the declared set, never about the whole surface** — a hardened sweep may enlarge the queue, and nothing here claims the list is closed. The invariants, gate and queue are unaffected, because they are per-route and the queue can grow.

**Instruments used, and their limits.** The route→mechanism mapping is **generated** from this repository
(`docs/project/STATE_OF_THE_SYSTEM.md` §"what each ungoverned route actually performs", produced by
`scripts/state_of_the_system.py` using the ratchet's own detector, so "reaches a raw mutation" has one
definition here). Whether a mechanism has a governed carrier is a **cross-repository** fact and therefore
cannot be re-derived from this tree: it was read on 2026-09-26 from
`CrewWorkAssistantOTP/src/crew_work_assistant/write_operations/*.graphql` (18 documents) plus the governed
registry (`meridian/crew_write_actions.py::crew_write_executors`) and `meridian/crew_write.py::_ALLOWED`
(17 operations). Each row below names its instrument; none is an inference from a name that merely looks
similar (D-039).

## The invariants

1. **Nothing is removed, fenced or disabled to tidy up.** A route is either raw-and-declared, or
   migrated-and-declared. There is no third state, and no deletion (D-040).
2. **A route moves only onto a carrier that already exists and has been exercised.** Not "an action exists" —
   the action's own readback verifier must have run against the provider at least once, with its output
   recorded (D-016 family: uncertain writes are unknown until read back).
3. **The ratchet's declaration is updated in the same change that moves a route.** It fails both when the set
   grows and when a declared route is fixed without updating the declaration; that property is what keeps this
   shape honest rather than aspirational.
4. **No new authority.** Migration replaces a raw call with the governed pipeline. It does not add a
   capability, a parameter, or a scope (the constitution's monotonicity rule).
5. **The stored credential outlives the need for it.** The raw routes are the only remaining consumer of
   `get_crew_headers()`; as they move, the token becomes retirable — but only as a *consequence*, never as a
   precondition. Nothing about the broker is changed by this shape.

## The evidence gate — a route is READY when all five hold

| # | condition | how it is shown |
|---|---|---|
| 1 | every provider mutation the route performs is **named** | the generated table, from the route's handler, transitively |
| 2 | that mutation has a **connector document** | the document list in the connector's `write_operations/`, by mutation name |
| 3 | that document has a **governed action** with a **verifier** | `crew_write_executors()` — action, operation, verifier present |
| 4 | the verifier has **executed** at least once | recorded evidence, not a code reading |
| 5 | the route's **callers are re-pointed** (or the route is retained and re-declared) | the template/JS that calls it, cited |

## The table — all 26 declared routes, by verdict

**22 READY** (every mutation they perform already has a governed carrier, verified — only conditions 4 and 5
remain per route):

| routes | mutation(s) reached | carrier | verifier |
|---|---|---|---|
| `/api/move-money`, `/api/lunchflow/change-account`, `/api/lunchflow/stop-tracking`, `/api/lunchflow/sync-balance`, `/api/manual-cc/remove`, `/api/manual-cc/top-up`, `/api/simplefin/change-account`, `/api/simplefin/disconnect`, `/api/simplefin/stop-tracking`, `/api/simplefin/sync-balance`, `/api/simplefin/sync-now`, `/api/splitwise/disconnect`, `/api/splitwise/sync-now` | `InitiateTransferScottie` | `initiate_transfer.graphql` → `crew_initiate_transfer` | yes |
| `/api/create-pocket`, `/api/lunchflow/create-pocket-with-balance`, `/api/manual-cc/create`, `/api/splitwise/create-pockets`, `/api/simplefin/create-pocket-with-balance` | `CreateSubaccount` (+ transfer, for simplefin) | `create_subaccount.graphql` → `create_crew_pocket` | yes |
| `/api/delete-pocket`, and the delete half of the change/stop/disconnect routes above | `DeleteSubaccount` | `delete_subaccount.graphql` → `delete_crew_pocket` | yes |
| `/api/create-bill` | `CreateBill` | `create_bill.graphql` → `create_crew_bill` | yes |
| `/api/delete-bill` | `DeleteBill` | `archive_bill.graphql` → `archive_crew_bill` | yes |
| `/api/account/autopilot-rules/delete` | `DeleteRule` | `delete_rule.graphql` → `delete_crew_autopilot_rule` | yes |

**1 PARTIAL — `/api/set-card-spend`.** It performs two mutations. `SetActiveSpendPocketScottie` is carried
(`set_spend_pocket.graphql` → `set_crew_spend_pocket`, verified). **`UpdateVirtualDebitCard` has no document
in the connector at all**, so half of what this route does has no governed carrier today. It moves only when
that half has one, or when the route is split so the covered half moves first — the decision belongs to
whoever does the slice, and either way nothing is removed.

**1 NAME MISMATCH — `/api/account/autopilot-rules/create`.** The route performs `CreateRoundUpRule`; the
governed action `create_crew_autopilot_rule` sends **`CreateAutopilotRule`** (`create_autopilot_rule.graphql`).
These are different provider mutation names and **this shape does not assert they are the same operation**
(D-039: measured on the provider's own name). Resolving it needs a provider read — create one rule of each
kind and compare the resulting rule objects — or a new document for `CreateRoundUpRule`. Until then this route
stays raw-and-declared, which costs nothing.

**1 NO CONTRACT — `/api/account/autopilot-rules/update`.** It performs `EditRoundUpRule`, and **no catalogue
anywhere records it**: not the connector's 18 documents, not our `_ALLOWED`. The mutation TEXT does exist in
this repository (`meridian/crew_commands.py:61`, registered as `EditRoundUpRule` at `:116`, and inline at
`app.py:5099`), so the work is not discovery — it is adding a connector document, a CLI operation, a governed
action and a verifier. This is the one place where the shape requires new capability work.

**1 NOT A MONEY WRITE — `/api/cards/<card_id>/sensitive`.** It performs `GenerateViewSadToken`, which mints a
view token for card details. It cannot be "migrated" to a money pipeline because it does not move money; it
belongs in the declaration as a non-financial provider mutation, and it is the one row that should be
**re-declared with that reason** rather than queued.

## The queue

Slices are ordered by **evidence readiness and blast radius**, never by size:

1. **`/api/delete-bill`** — the smallest complete case: one mutation, an existing carried action
   (`archive_crew_bill`), a verifier that proves absence rather than assuming it, and one caller. This is the
   worked example that proves the shape end to end, including the ratchet declaration update.
2. **`/api/create-bill`** — same shape, opposite direction (creation readback).
3. **The pocket cluster** (`create-pocket`, `delete-pocket`, and the four connector features that create or
   delete pockets) — one carrier, five routes, verified.
4. **The transfer cluster** (13 routes sharing `InitiateTransferScottie`) — the largest blast radius and the
   one that retires the stored token's last consumers; do it after the pattern is proven twice.
5. **The two contract gaps** — `UpdateVirtualDebitCard` and `EditRoundUpRule` — each a connector document
   plus an action plus a verifier, in that order.
6. **The name mismatch** — resolved by a provider read, not by a code change.

## What this shape deliberately does not do

* It does not fence, disable or delete any route.
* It does not change any financial write semantic, or add a capability, or widen authority.
* It does not require the owner to certify a global picture: the evidence for each route is local and is
  recorded in that route's own change.
* It does not treat "migrate everything" as a goal. The goal is that no money-moving path lacks provenance;
  a route that cannot move yet is not a failure, it is a declared debt with a named missing piece.

## What the owner decides

1. **Approve this shape as OS-119's answer** — or say what to change about it.
2. **Whether slice 1 starts now** (`/api/delete-bill`). It is one route, one caller, one verifier; it removes
   nothing and its rollback is a revert.
3. **Whether the 16 connector-feature routes are in scope at all.** They are reachable only from the legacy
   surface, so migrating them is provenance work, not user-visible work — which is exactly the kind of thing
   D-040 says must not be dropped for looking unimportant, and equally the kind that must not displace a
   slice the owner actually wants next.

## Cross-references

D-030 (no option set defaults to the status quo), D-031 (this debt, first declared), D-039 (measure on the
provider's own name — the reason the name mismatch above is a finding and not a footnote), D-040 (nothing is
dropped for looking unused), D-042 (enumerate before concluding), the ratchet
`tests/test_governed_write_routes.py`, and the generated inventory `docs/project/STATE_OF_THE_SYSTEM.md`.
