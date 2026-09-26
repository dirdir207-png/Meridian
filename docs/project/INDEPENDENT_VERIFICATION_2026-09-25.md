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

## Claims 1–4 — in flight

| # | claim | instrument prescribed | status |
|---|---|---|---|
| 1 | capability 17/17 with carriers, 16/17 with verifiers | execute the pipeline against a scratch DB | in flight |
| 2 | the ungoverned write surface is exactly the 26 declared routes | hit the routes through HTTP with the provider stubbed | in flight |
| 3 | Today and Plan publish one money rule | the HTTP surface, not the unit fixture | in flight |
| 4 | the allocation ordering rule | the raw provider read, not the document | in flight |

Their verdicts are appended below when they return. Each will carry its instrument, its scope, and its own
COULD-NOT-CHECK column; any falsification goes to the owner first, as instructed.
