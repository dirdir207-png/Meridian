# Today ↔ Plan "spend": alignment review, 2026-09-25

**Asked for by the owner, 2026-09-25:** *"review align today and plan spend session in meridian lane."*
Read-only review; nothing implemented. Every claim below carries the line that establishes it.

## Verdict in one paragraph

**Today and Plan already publish one number from one rule, and a test asserts it.** The number is not what
needs aligning. What diverges is everything around it — and most of the divergence is about **words**: three
labels carry two different computations, and one of those labels collides with itself across two surfaces.
So the slice is smaller than "make two figures agree" and sharper than a naming pass: it is *one rule, one
name, one basis line, and the two places that still do their own arithmetic*.

## The map

| Surface | Label rendered | Value shown | Source of the value | Agrees with the pair? |
|---|---|---|---|---|
| Today (headline) | **"Safe to spend"** — `templates/meridian/partials/today.html:41` | the spend figure | `safe_to_spend().amount` — `meridian/services/today.py:460`, published at `:498` | **baseline** |
| Plan (allocation station) | **"Available"** (`is-available` station, `static/js/meridian/plan.js:223,244-245`), prose *"$X remains flexible"* at `:199-201` | the same number | `safe_to_spend().amount` — `meridian/services/plan.py:536`, published as `available` at `:545-548` | **yes — same rule, same repository** |
| Today (detail row) | **"Available cash"** — `static/js/meridian/today.js:497-498` | Σ `available_balance` of cash accounts (`meridian/services/today.py:401-406`), i.e. an **input**, not the figure | server | n/a as a figure — **but the words are reused below** |
| Accounts (headline) | **"Available cash"** — `templates/meridian/partials/accounts.html:31` | Σ `balance` over "liquid" accounts + a pocket matched **by name**, **without** the `is_active` filter its own payload carries | **computed in the browser** — `static/js/meridian/accounts.js:505-521` | **NO — a third rule** |
| Advisor panel (weather) | a coverage verdict **sentence** | verdict over the spend figure | the **dial's** rule — `meridian/services/dial.py:78-124` via `meridian/api.py:927` → `meridian/proactive.py:113-121,328-356` | **NO — superseded for these surfaces** (`meridian/services/reserves.py:36-44`) |
| Plan (scenario panel) | "Runway X → Y days (Δ)" | a day count | base from `beacon.forecast()` (`meridian/beacon.py:137`), scenario recomputed at `meridian/scenarios.py:24` | **NO — two definitions** (below) |

## What is aligned, and how it is guarded

`tests/meridian/test_safe_to_spend_agreement.py` does not assert each side against its own constant — it
**builds both payloads from one seeded repository** and compares them, over six cases: the owner's worked
example (1000 − 100 − 100 → 800), the D-019 overdraft (424.90 against a −324.90 reserve → 100.00), a funded
reserve, a goal pocket beside a spend pocket, no pockets, and no money accounts (where both must decline to
state a figure rather than invent 0.00). Plan additionally asserts its own partition: Bills + Goals +
Available == its published `cash_total`. That is the right shape — a test that asserted "both call the same
helper" could stay green while the two drifted apart again.

## The four divergences that remain (all pre-existing, all evidenced)

**D1 — Accounts publishes a third rule under the pair's most dangerous label.** *"Available cash"* on
Accounts reads as the same fact as Today's headline, is computed in JavaScript from `balance` rather than the
server's rule, and omits `is_active` while the server documents exactly that hazard
(`meridian/services/safe_to_spend.py:253-261`: the owner's own Crew read carries **two pockets named "Free to
Spend", one inactive since 2026-09-17**). The JS comment claims it *"matches the Today safe-to-spend
convention"*. The governed captures cannot reveal the divergence: the fixture writes both figures equal
(248.50).

**D2 — the label collides with itself.** Today uses **"Available cash"** for an *input* row
(`today.js:497-498`, Σ `available_balance`) while Accounts uses the same two words for a *headline* computed
a third way. Two surfaces, one label, two quantities — the cheapest possible source of "wait, which number is
that?".

**D3 — the advisor's verdict is computed from the rule OS-111 retired for these surfaces.** The weather's
coverage sentence reads the dial's `_available_to_spend()` (`dial.py:78-124`, shipped at `:611`), while
`reserves.py:36-44` records that rule as *kept for the dial only* and superseded on Safe to Spend / Plan by
OS-111. So the header and the sentence beneath it can be computed two different ways. Related: the dial's
`availableToSpend` reaches the client (`dial.js:17`, assigned `:538`) and is rendered **nowhere** in
`static/js/**`; its only consumer is that server-side verdict.

**D4 — the scenario panel compares two definitions of runway, and reports a difference where there is none.**
Base: `beacon.forecast()` — obligations subtracted, clamped at 0 (`beacon.py:137`). Scenario:
`starting_cash / daily_expense` — obligations **not** subtracted (`scenarios.py:24`). Demonstrated, not
inferred: with a production-shaped base (`starting_cash=1000`, `daily_expense=20`, `runway_days=40`) and **no
changes**, `run_scenario(base, {})` returns `comparison["runway_days"] = 10` while the cash and low-point
deltas are `0.0` and `assumptions` is empty. The client then **recomputes** the delta instead of reading
`data.comparison.runway_days` (`static/js/meridian/plan.js:439-455`). The tests cannot see it because the
fixture sets `1000/20 == 50`, where both formulas agree by construction
(`tests/meridian/test_scenarios.py:8-24,63-66`).

## Options, and the recommendation

Visual and authority decisions are the owner's, so these are put as options rather than picked:

1. **Source-align Accounts only** — render the server's figure and its basis; keep the words "Available cash"
   exactly as they are. Smallest: one payload field plus one JS function, no label change, no visual review
   beyond confirming the number.
2. **Naming pass** — one name for the pair's figure (Today says "Safe to spend", Plan says "Available" and
   its prose says "remains flexible"), and decide what Today's *input* row should be called so it stops
   reading as Accounts' headline. Pure owner call; touches two templates and one JS row.
3. **Full alignment** — 1 + 2 + the advisor's basis (D3) + the scenario arithmetic (D4).

**Recommendation: 1 and 2 as one slice** (they touch the same render path and the same review), **D4 as its
own defect slice** (it changes a displayed comparison and needs a *divergent* fixture — the degenerate-fixture
lesson from the 2026-09-25 audit, where a fixture written to agree cannot detect divergence), and **D3
separately** (it changes a verdict sentence and depends on the dial's role being settled).

## What this review did not do

No application file was modified. Nothing was promoted: the slice and its options are recorded in the ledger
and await the owner's choice of scope. The numbers in this document were read, not computed by hand — the
demonstrated scenario result came from executing `run_scenario` against a synthetic base, never against live
data.
