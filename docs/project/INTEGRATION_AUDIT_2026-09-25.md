# Integration audit — dead ends, unfinished code, and seams that should link but do not

**Task:** `OS-123` (owner request, 2026-09-25). **Status:** in progress — findings only, no fixes.
**Read at:** `e7f877d` on `feat/meridian-implementation` · **Started:** 2026-09-25 (evening session)
**Scope at HEAD:** read-only. No `app.py`, `meridian/**`, `templates/**`, `static/**`, migration, route or
existing test is edited by this audit. The repairs below are *proposed bounded slices*, and each is a decision
for the owner — appearing here promotes nothing (`AGENTS.md` §Handoffs, rule 4).

---

## 0. Why this exists, in the owner's words

> *"At some point I want a deep analysis of everything wired into the app and identify dead ends, unfinished
> code, stuff within the app that should common sense and intuitively link but isn't."*

The method is prescribed by the task itself because **the method is what failed in earlier attempts**:

1. independent instruments with different assumptions — never one lens;
2. **fresh contexts**, never forks that inherit the author's premises;
3. **exact sets** (route sets, caller sets, import graphs, table sets), never mention-greps, which generate
   hypotheses and never conclusions (D-034/D-035);
4. the **rendered screen** as evidence alongside the data, at the owner's viewport;
5. an **instrument and precondition stated on every figure**, and every negative finding preceded by a search
   of where the thing would actually live.

## 1. Instruments used, with their preconditions

| # | Instrument | Established by | Preconditions / limits |
|---|---|---|---|
| I1 | Exact-set enumeration of routes, templates, JS modules, tables, services, jobs | five fresh-context helpers, raw output in `tmp/os123/*.md` | each helper's own statement is reproduced in §3; a helper's set is only as good as its parser |
| I2 | Rendered screen, governed capture contract | `scripts/capture_meridian_matrix.py` → `artifacts/os123-integration-audit-2026-09-25/captures/` (40 records, `manifest.json` carries commit `e7f877d`, fixture `os123-synthetic-preview-e7f877d`, frozen clock `2026-09-08T13:42:00Z`, DPR, theme, `fullPage`) | the target is the **isolated synthetic preview** (`scripts/preview_observatory_dial.py`, :8093), never live data and never the owner's :8081 |
| I3 | Browser console + failed-response probe | `tmp/os123/console_probe.py` → `tmp/os123/console.json` (8 page loads: 4 workspaces × desktop 1440×900 DPR1 and mobile-air 420×912 DPR3, dark, reduced-motion) | **the preview implements a limited route set**, so a 404/501 there is NOT an app finding — see §6.1, the one trap this instrument sets |
| I4 | Import/caller sets per module | AST + literal-name search over `app.py`, `meridian/**`, `scripts/**`, `tests/**` | a name reached by `getattr`/registry/string dispatch is invisible to AST; every negative below was followed by a literal search for the name |
| I5 | Direct execution of a pure function with a production-shaped input | `.venv311/bin/python -c …` on `meridian/scenarios.py` | demonstrates the mechanism; it does not claim which values the owner's data holds |
| I6 | Served-content marker | `curl :8093/meridian?workspace=today` grepped for a HEAD-only marker (`data-sts-horizon`) | proves the **front-end served** matches HEAD even though the process started 2026-09-24 — the D-035 lesson applied to this project's own stale-preview trap |

**Synthetic-fixture caveat, and it matters for reading every finding below.** The governed preview writes its
two money figures **equal by construction** (`tests/browser/fixtures/observatory-dial.html`:
`availableToSpend:{minor:24850}`; the Today fixture's safe-to-spend is also `248.50`). A capture can therefore
never reveal a divergence between the two rules it was written to show agreeing. §3.5/S1 and §3.5/S2 are exactly that
class of divergence, and they were found in code, not in pixels.

---

## 2. Exact sets — headline counts

Each figure carries the instrument that produced it; "helper" means a fresh-context agent's instrument, and the
headline conclusions drawn from those sets were re-verified here (see §5, item 5).

| Set | Count | Instrument | Where |
|---|---|---|---|
| registered route paths | **199** in `app.py` + `meridian/api.py` (139 + 60), **+4** in `crew/broker.py` (a separate Flask app) **+1** test = 204 decorator routes | two independent decorator scans (AST and raw regex) agreeing exactly, cross-checked against a second helper's AST count — the two agree once the scope difference is named | §3.1/R1 |
| JS `/api/` literals with no matching route | **0** | route set × literal set (helper) | §3.1 |
| templates | 41 | `templates/**` enumeration (helper) | §3.2 |
| templates never rendered and never included | **18** | Jinja2 `meta.find_referenced_templates` + `ast` render-arg set (helper) | §3.2/T3 |
| JS modules | see `tmp/os123/js-templates.md` | `<script src>` + ES-import closure (helper) | §3.2 |
| JS modules loaded **only** by the legacy surface | **22** | exact src-set difference, `base.html` (24) vs `meridian/index.html` (13), overlap 2 (**re-verified here**) | §3.2/T1 |
| tables from `meridian/migrations/*.sql` | 32 from 31 files | replay into `:memory:` (helper) | §3.4/P7 |
| tables in the default DB (`savings_data.db`) | 50, schema at **025** | read-only schema (**re-verified here**) | §3.4/P6 |
| tables in the preview DB (`gate.db`) | 54, schema at **031** | read-only schema (helper) | §3.4/P6 |
| tables created outside the migration runner | **22 of 50** | set difference, migrations vs live schema (helper) | §3.4/P7 |
| tracked `meridian/**` modules with no production importer | 19 | AST import graph + literal search (helper) | §3.3/U6 |
| symbols with zero references and zero literal mentions | 16 | AST + 829-file literal search (helper) | §3.3/U1 |
| `TODO`/`FIXME`/`XXX`/`HACK`/`WIP` markers in tracked source | **0** of 549 files | marker sweep (helper) | §3.3/U5 |
| scheduled jobs / cron / apscheduler | **0** | exact search (helper) | §3.4/P9 |
| connector write operations | 17 CLI ops → 17 distinct provider mutations | connector registry + md5 (helper), **re-parsed here** | §3.6 |
| of those, executable by our pipeline | **17 of 17** | set comparison keyed on the provider mutation (**re-verified here**) | §3.6 |
| of those, bound to a governed action with an executor | **17 of 17** (16 with a readback verifier) | `crew_write_actions.py` base map (**re-verified here**) | §3.6 |
| ungoverned Crew-mutating routes (a ratchet, not a fix) | 25 | `tests/test_governed_write_routes.py` | D-031, `OS-121` |

---

## 3. Findings

Classified **dead end** (wired but unreachable, shipped but never invoked, read but never persisted),
**unfinished** (a code path whose own comments or shape admit incompleteness), or **unlinked seam** (two things
that common sense says belong together, joined nowhere — including *second paths to the same fact*).
Each finding names the concept it advances, per D-033.

### 3.1 Routes and reachability

Helper: `tmp/os123/routes.md` (548 lines; raw tables in sections 2 and 6). Its first act was to refuse an
instrument: `import app` is **not safe** — it runs `init_db()` at module level (`app.py:8826`) and mints secrets
(`:186`, `:1228`), so enumerating `app.url_map` writes to the database (§3.4/P11). It therefore built a guarded
import (shared in-memory clone seeded read-only, raise-on-write, sha256 and `git status` compared before and
after) and reported honestly that **that instrument never ran to completion** — every route finding below comes
from its static instruments (two independent decorator scans, AST and raw regex, agreeing exactly), and the
dynamic questions are recorded as undecided rather than guessed.

#### R1 — the route set, established by two agreeing instruments

**204 decorator routes**: 139 in `app.py`, 60 in the `meridian_api` blueprint (`meridian/api.py`, served under
`/api/meridian`), **4 in `crew/broker.py` — a separate Flask application**, and 1 test route. That reconciles
exactly with the other helper's independent count of **199** for `app.py` + `meridian/api.py` (139 + 60): two
instruments with different parsers agree once the scope difference is named. The route set is **closed** under
both instruments: 0 `add_url_rule` calls, 0 non-literal paths, 0 conditionally-defined routes. *Limit:* a rule
registered at runtime by any other mechanism is invisible to both.

#### R2 — `GET /meridian` is registered twice, and the second handler can never run (dead end; the one method clash in `app.py`)

**Claim.** `app.py` registers the same rule with the same method twice: `meridian` at `:3194` (which reads
`request.args.get('workspace')`, validates it against `MERIDIAN_WORKSPACES`, and renders
`meridian/index.html` with `active_workspace`) and `meridian_shell` at `:3846` (which renders the same template
with **no** argument). Werkzeug keeps both rules; the first registered wins.

**Evidence — re-verified here by a different instrument than the helper's.** An AST pass over `app.py` found
exactly four duplicate rule strings, and **only one is a method clash**:

| duplicate rule | handlers | methods | verdict |
|---|---|---|---|
| `/meridian` | `meridian` (`:3194`), `meridian_shell` (`:3846`) | GET, GET | **clash — one handler is unreachable** |
| `/api/auth/passkeys/<int:passkey_id>` | `api_delete_passkey` (`:3754`), `api_update_passkey` (`:3780`) | DELETE, PATCH | distinct methods — not a conflict |
| `/api/simplefin/sync-schedule` | `:8104`, `:8134` | GET, POST | distinct methods — not a conflict |
| `/api/simplefin/timezone` | `:8172`, `:8188` | GET, POST | distinct methods — not a conflict |

**Which handler wins was settled empirically, not by reasoning** (the helper marked this medium-confidence, so
the author built an instrument for it): a minimal in-process Flask app with two identical GET rules on Flask
3.1.3 / Werkzeug 3.1.8 returns the **first** handler. So `meridian_shell` (`app.py:3846`) is dead code, and the
live handler is the one that validates the workspace — which is why the surface works and the defect is
invisible. `/` redirects through `url_for('meridian')` (`app.py:3811`), which resolves by endpoint name and is
therefore correct either way. **Confidence: high.** *Repair:* delete the duplicate (or make it the fallback it
looks like it was).

#### R3 — the `/api/meridian/*` namespace is served from two places, and the readiness check sees only one (unlinked seam)

60 rules come from the blueprint registered at `app.py:126`; **2 more are hand-written in `app.py`** under the
same prefix: `/api/meridian/actions` (`app.py:4151`) and `/api/meridian/funding-rules/propose` (`app.py:4244`).
The consequence is not cosmetic: `/api/meridian/funding-rules/propose` is **one of the browser's three
permitted write channels** (`static/js/meridian/api.js:43-47`, `ALLOWED_PROPOSAL_PATHS`), and
`scripts/verify_readiness.py:62` AST-scans for `register_blueprint`, so any check that treats `meridian_api` as
"the Meridian API" silently misses it. The other two permitted paths were cross-checked and **do** exist
(`meridian/api.py:1713`, `:1735`) — this is the one dead-link question the helper could decide, and it decided
it in the app's favour. **Confidence: high.**

#### R4 — established as *not* defects, so they are not chased again

- `crew/broker.py` is a **second Flask app** (`:39`), reached server-to-server through `BrokerCrewTransport`
  (`app.py:829-836`) and launched from a launchd template — its 4 routes must be excluded **by design** from any
  "route set minus UI references" diff, not by ignoring misses.
- All `url_for` endpoint references resolve (`meridian` ×4, `meridian_settings` ×2, `static` ×7 — the last
  resolving to Flask's implicit static rule, which the route set deliberately excludes).
- The nine legacy URL routes (`/account`, `/cards`, `/credit`, `/family`, `/splitwise`, `/bills`, `/expenses`,
  `/goals`, `/pockets`) are **real registered routes**, not redirects. Whether their handlers merely redirect
  could not be decided (that was the unexecuted instrument).
- 16 routes have no caller at all, all reached only by dead templates (§3.2/T3, T4); a further 61 have no caller
  by literal search, but the templates helper's manual pass showed several of those *are* called through composed
  paths (`fetch(\`${path}${suffix}\`)`), so that number is an upper bound, not a finding.

#### R5 — undecided, stated as such (D-035: an absence nobody established is a hypothesis)

**Decided in the app's favour:** of 89 template `href`/`action` references plus 8 Python-built `"href"`
values, **zero** match no route (converter-aware matching); the 8 dynamic references are listed rather than
guessed, including the one `{{ row.href }}` whose values were checked separately and all resolve.

**Undecided, and the reason is worth stating:** the template/Python channel matched only **3 of 203** routes, so
no claim of "unreachable from the UI" can be made for the other 200 — the modern UI calls JSON APIs from
`static/js/**` (115 `fetch(` calls in 51 files), which this instrument did not harvest. Along with it: (a) routes
nothing in the UI can reach; (b) UI references matching no route **in the JS channel** and the dynamic cases that
cannot be decided at all; (c) routes reachable only from `tests/**` or `scripts/**`; (d) routes that redirect and
never render; and the question this task cares about most — **routes whose only guard is `@login_required` that
can reach a Crew or provider mutation**. Its Instrument E/F scripts are left in `tmp/os123/routes.md` §5–§6 to be
run rather than guessed at.

### 3.2 Templates and browser modules

Helper: `tmp/os123/js-templates.md` (323 lines; instruments: Python `ast` over 138 renderer-argument sites,
Jinja2 `meta.find_referenced_templates` for the include graph, `<script src>` extraction, comment-stripped
ES-import closure, `git log -S`/`git show` to distinguish deletion from non-addition). The headline findings
were **re-verified here**; the full 15-finding table and the helper's 8 recorded false positives are in the file.

#### T1 — the entire legacy front end is reachable only through an unlinked `/debug` (dead end; the largest one found)

**Claim.** `/debug` (`app.py:3836`, `@login_required`, renders `templates/debug.html`) has **no inbound link
anywhere in the repository**. It is the only template that extends `templates/base.html`, and `base.html` is the
only loader of a set of 22 JavaScript modules that appear nowhere in the Meridian shell. The service worker's
only registration (`static/js/app.js:65-67`) and the only Web Push path (`static/js/features/notifications.js`)
live inside that set.

**Evidence — re-verified here.** Instrument: exact script-src set difference between `templates/base.html` and
`templates/meridian/index.html`, plus a repo-wide search for links to `/debug`.
- `base.html` loads **24** scripts; `meridian/index.html` loads **13**; the overlap is **2** → **22 modules are
  loaded only by the legacy surface**: `static/js/{app.js,state.js}`, `api/{account,beacon,cards,credit,expenses,family,goals,splitwise,transactions}.js`,
  `features/{autorefresh,dragdrop,groups,notifications}.js`, `ui/{dialogs,filters,modals,navigation,rendering}.js`,
  `utils/{formatters,helpers}.js`.
- `templates/debug.html` is the only template extending `base.html` (grep over `templates/**`).
- No `href="/debug"` exists in any template or JS module. `app.py:3854` does serve `/sw.js`, and
  `tests/test_auth_branding.py` guards it.

**Classification.** Dead end. **Confidence: high** for the sets; whether the legacy surface should be *deleted*
or *linked* is a product decision for the owner, and this audit does not make it.

#### T2 — the Today forecast chart cannot render: its markup was deleted and its guard still requires it (dead end; regression, git-proven)

**Claim.** `renderForecast()` returns early unless six `[data-forecast*]` hooks exist
(`static/js/meridian/today.js:150-157`); **no template contains any of them**, so the projection chart is
unreachable — while its CSS still ships and a browser test still asserts the element.

**Evidence — re-verified here.** `grep -rn "data-forecast" templates/` → **no match**.
`git show c1d627f -- templates/meridian/partials/today.html` → **10 removed lines, 0 added** (the `<svg
class="m-forecast" data-forecast …>`, floor, shade, line, labels container and the five label spans);
`git log c1d627f..HEAD -S 'data-forecast' -- templates/` → **empty**, so it was never re-added. Calls remain at
`today.js:485`. CSS: 11 `forecast` rules still in `static/css/meridian/today.css`. The browser assertion the
helper names (`tests/browser/test_activity.py:213-216`) is skipped unless `APP_URL` is set.

**Classification.** Dead end + an untruth in a commit message (the message said the chart "remains available
through the existing data hooks"). **Confidence: high.** *Repair:* either restore the markup or delete the
renderer, the CSS and the assertion together — silently keeping all three is the shape this project calls a
guard that cannot fail.

#### T3 — 18 of 41 templates are never rendered and never included (dead end; includes a security surface)

**Evidence (helper; the count is the helper's exact render set).** The unreachable set includes
`templates/meridian/partials/views/account.html` — 1191 lines whose inline JavaScript is **the sole caller of 14
routes**: `change-password`, `webauthn/register/{options,verify}`, `account/bank-details`,
`account/webauthn/{config,update-config,test}`, `account/fcm/{update-config,test}`,
`account/autopilot-rules{,/details,/update,/delete,/create}`.

**Cross-reference, stated carefully.** This does **not** reduce the cardholder-data exposure recorded in D-038
(committed this session by a concurrent lane): those endpoints are `@login_required` and answer to anyone who
knows the URL, with or without a UI that links them. It does mean that when D-038's options are decided, the
*reachability* half is already known — the surface is URL-only, exactly the class
`tests/test_surface_reachability.py` was written for after the Settings-hub defect.

#### T4 — `templates/onboarding.html` has no route and no link (dead end)

454 lines; only `tests/test_auth_branding.py` renders it. Its write endpoints
(`/api/onboarding/{status,crew/save-token,complete}`) strand with it. **Confidence: high** (helper instrument).
`OS-117` already records the neighbouring defect (Plan's write forms resolving Crew ids from an external
snapshot); this is the same family — a surface built and never arrived at.

#### T5 — two dead DOM bindings (dead end, low)

- `static/js/meridian/review.js:172` — `closest("[data-review-approve]")` matches nothing anywhere, and
  `tests/browser/test_virgil_surface.py:155` actively forbids that attribute.
- `static/js/meridian/memory.js:60` — the `[data-current-workspace]` branch is unreachable; no template emits
  the attribute.

#### T6 — ten unreferenced JS declarations and seventeen selectors with no element (dead end, low)

Unreferenced by identifier: `static/js/api/credit.js:{changeCreditAccount, stopCreditTracking,
syncCreditBalance}`, `static/js/meridian/dial.js:{dateIndexFromPointer, fundingScheduleNote}` (both shipped in
the shell bundle), `static/js/ui/modals.js:openFamilyDetail`,
`static/js/ui/navigation.js:{handleLogout, toggleMobileMenu, toggleMobileMore, toggleUserMenu}`. Selectors with
no matching element include the whole `#mobile-drawer` / `#drawer-*` / `.drawer-nav-item` family, which exists
only in `ui/navigation.js` and its CSS. **Confidence: medium-high** — the helper records 751 selectors as
undecidable because `dial.js` builds DOM through `createElementNS`, which only a browser can settle.

#### T7 — the web-app manifest is not linked from the Meridian shell (unlinked seam, low)

`static/manifest.json` is declared in `base.html`, `register.html`, `login.html`, `onboarding.html` — and
**not** in `meridian/index.html` or `meridian/settings.html`, with no `Link` header (`app.py:103` sets only
`Cache-Control`). `templates/index.html` is never rendered (`/` redirects at `app.py:3811`).

### 3.3 Unfinished code

Helper: `tmp/os123/unfinished.md` (229 lines). Instruments: AST reference analysis over 411 tracked `.py` files,
literal-name search across 829 tracked text files, marker sweeps over 549 source files, and an explicit
framework-entry-point exclusion list so decorated handlers and dunder methods are not misreported as dead.

#### U1 — 16 symbols with zero AST references **and** zero literal mentions (dead code)

Notable members, with the reason each matters (full table in the helper's file):
- `meridian/crew_write.py:45,49` — **`CrewWriteBlocked` and `CrewWriteUncertain` are never raised**. The write
  executor's own contract names two failure modes that no code path produces, while `meridian/ai/envelope.py:74`
  refers to one of them in prose. A capability the pipeline documents but cannot signal.
- `meridian/observations.py:164,185` — `list_snapshot` and `record_provider_snapshot`: **the digital twin's
  write path has no caller**, corroborated independently by `CONCEPT_COVERAGE.md:11` and by §3.4/P4's finding
  that the app's AI-run table is never written. Concept 1 is `built-unwired` in two separate ways.
- `meridian/write_routing.py:185,242,252` — `route_many`, `reroute_direct_if_owner`, `all_provenances`.
- `crew/proposals.py:15-16` — `TransferResolver`, whose `resolve()` raises `NotImplementedError` and has no
  implementer: a stub in the proposal path.
- `crew/advisor.py:23` `MeridianAdvisorBridge`, `crew/actions.py:366` `_list_by_state`,
  `crew/renewal.py:125` `active_session_id`, `app.py:715,739,1506`,
  `meridian/ai/evaluation.py:123,205`, `meridian/paycheck.py:96`.

**Guard-integrity consequence, and it is the interesting part.** `route_many` survives only as a **string** in
`tests/test_governed_write_routes.py:89` — `GOVERNED_MARKERS = {"classify_action", "route_mutation",
"route_many", "execute_approved_action"}` (re-verified here). The ratchet's vocabulary therefore contains a
marker for a function nothing calls, so a route could satisfy the ratchet by *mentioning* a dead helper. No
route does today — the marker is permissive, not falsely passing — but the marker set should be re-derived from
the live call graph, not from a hand-kept list.

#### U2 — a bare `except` silently empties the Crew-write executor registry (unfinished; capability loss with no signal)

`app.py:1261-1272` (helper instrument): an import failure is swallowed, `crew_write_executors` degrades to `{}`,
and nothing is logged or surfaced. Every governed write then fails downstream for a reason the operator cannot
see. This belongs with D-031's write-surface work rather than with the cosmetic findings above.
**Confidence: high** (helper read the handler; the audit did not execute it).

#### U3 — a stub endpoint with no consumer, and an untruth in its own copy (dead end, low)

`app.py:7140` — `GET /api/lunchflow/last-check-time` returns `time.time()`, while `app.py:7146` describes it as
"30 seconds ago". No consumer exists anywhere in the tree. The only trace of it is a readiness artifact whose
`source_sha` is stale.

#### U4 — a shipped surface that renders "coming soon" forever (unfinished, self-admitted)

`static/js/api/family.js:142-154` — `loadChildActivity` ignores its `childId` argument and renders
"Activity coming soon"; the code says an API endpoint is still needed. Reached from `family.js:128`. This is a
child surface inside the legacy bundle (see T1), so its reachability is now `/debug`-only — which makes it
*less* urgent, not more real.

#### U5 — the marker sweep comes back essentially empty, and that is a finding too

`TODO 0, FIXME 0, XXX 0, HACK 0, WIP 0` across all 549 tracked `.py/.js/.mjs/.html/.sql/.sh` files. 278 raw
marker-shaped lines reduce to 158 claim-like after removing incidental uses (HTML `placeholder=`, SQL
`placeholders`, `tempfile`, `later` as a variable). The survivors are overwhelmingly either domain vocabulary
("not yet set aside") or **honest scope notes** of the form `meridian/settings_hub.py:95` — *"No route, no
partial, no read model. Stated, not stubbed."* In other words: this codebase does not hide incompleteness behind
markers; it records it. The unfinished work in this audit was found by reference analysis, not by reading TODOs.

#### U6 — 19 tracked `meridian/**` modules have no production importer (dead end / substrate-only)

`cancellation/{adapters,recipes,catalog,reconcile,replay,scheduler}`, `context`, `deposit_discovery`,
`documents/{reconcile,safety}`, `funding_proposals`, `migrate_legacy`, `mutations`, `policy`,
`providers/{crew,lunchflow,simplefin,splitwise}`, `services/__init__`. Two of these are named as dotted strings
in `envelope.py:86,118` (a registry), so the helper classifies them "no production importer", **not** dead —
the distinction is the point of the D-035 rule. `meridian/policy.py` and `meridian/context.py` were already
recorded in `CONCEPT_COVERAGE.md` (concepts 4/5 and 17); this adds the rest, with instruments.

#### U7 — the council: declared 5, implemented 2, called 2, and reachable only from a script

Instrument (code, not docs): `meridian/ai/envelope.py:354-395` declares five roles
(forecaster, investigator, skeptic, guardian, teacher). Two exist
(`meridian/ai/investigator.py:60`, `meridian/ai/skeptic.py:72`), and both are convened only at
`scripts/investigate.py:245-247`. No `Forecaster`/`Guardian`/`Teacher` class exists, the Guardian's fail-closed
guard (`meridian/ai/council.py:136,155`) has no subject, and **no route, template or JS module references the
council at all** — which is §3.5/S5 seen from the other side. The docs agree exactly
(`MERIDIAN_ROADMAP.md:355`). **Confidence: high.**

#### U8 — the one untracked source file inside a package

`meridian/ai/investigation_service.py` (303 lines, mode `-rw-------`) is untracked, imported by nothing, served
by no route (instrument: 199 route paths parsed; none matches "investigat"), and its design specimen
`design/investigator-medallions-2026-09-21/investigator.html` is served by nothing. Already recorded at
`AGENT_COORDINATION.md:716` and `HANDOFF.md:167`; reproduced independently here, and it is the first slice the
owner selected (`OS-076`).

### 3.4 Persistence and background work

Every finding in this section was produced by the fresh-context helper (`tmp/os123/data-jobs.md`, 702 lines) and
then **re-verified here** by the author, by reading or executing the cited line. Where a claim was only the
helper's, it says so.

#### P1 — `pocket_groups` is written by two shipped paths and **created nowhere** (dead end + a real defect)

**Claim.** Two shipped code paths write a table that no migration, no `init_db()` and no ad-hoc statement ever
creates. One of them therefore always fails while reporting HTTP 200; the other fails into a `print`, and the
cleanup it claims to perform never happens on the table the UI actually reads.

**Evidence — re-verified here.** Instrument: exact search for `pocket_groups` across every `*.py` and `*.sql`
in the tree (three hits, all statements, **no `CREATE TABLE`**), plus a read-only schema query of both live
databases.
- `app.py:5517-5539` — `POST /api/assign-group`; `:5528` `DELETE FROM pocket_groups`, `:5530`
  `INSERT OR REPLACE INTO pocket_groups`. The `except` at `:5536-5537` returns
  `jsonify({"error": str(e)})` **with no status code** — so the failure is reported in the body of an HTTP 200.
- `app.py:2853-2861` — the pocket-deletion cleanup. Its own comment claims it *"ensures the deleted pocket is
  removed from your local grouping table"*; it deletes from `pocket_groups` (which does not exist), so the
  statement raises, the handler catches at `:2859` and only prints. It **never touches `pocket_links`**, which
  is the table the grouping view actually reads at `app.py:2086`.
- Both live databases were opened read-only: neither has `pocket_groups` (both have `pocket_links` and
  `splitwise_pocket_config`).
- No frontend caller for `/api/assign-group` exists in the helper's route/JS sets.

**Consequence.** A deleted pocket continues to render inside its group from a stale `pocket_links` row, and the
assignment route cannot work at all. This is the one finding in the audit that is a plain defect rather than a
visibility question. **Confidence: high.**

#### P2 — the two launchers run **disjoint halves** of the background work (unlinked seam; deployment)

**Evidence — re-verified here.** Instrument: exhaustive caller search for `ensure_meridian_refresh` +
reading both launchers.
- `app.py:7311` defines `ensure_meridian_refresh()`; the **only** production caller is `run_preview.py:49`
  (the other two hits are the definition and a test stub).
- `run_preview.py:38-49` deliberately disables the legacy path (`a._background_thread_started = True`,
  `a.app.before_request_funcs[None] = []`) and starts the Meridian refresh loop.
- `Dockerfile:26` runs `gunicorn … app:app`, and `gunicorn.conf.py`'s `post_worker_init` calls only `init_db()`
  — so a container gets the **legacy** 30-second checker via `app.py`'s `before_request` hook and **never**
  `MeridianRefreshService` (`meridian/refresh.py:57`) or `EvidenceRefreshService`
  (`meridian/evidence_refresh.py:229`).

**Consequence.** In the container there is no provider sync and no evidence poll; in the preview there is no
legacy check. Neither launcher runs both. Partly known (`CURRENT_STATUS.md` assumes the preview), but the
Docker asymmetry is recorded nowhere. **Confidence: high.**

#### P3 — the ingest dedup guard has no production caller (dead end; the one correctness risk here)

`meridian/connection_jobs.py:111` `ResumableIncremental` is referenced only by its own definition and
`tests/meridian/test_connection_jobs.py` (re-verified here: exhaustive name search). Its sibling
`IngestionCursorStore.revoke` *is* wired (`meridian/api.py:1179`). The cursors that prevent reprocessing the
same provider message are therefore never exercised outside tests. **Confidence: high**; the product consequence
is unverified (it needs a run against a real mailbox).

#### P4 — role runs are never written by the shipped app (sharpens §3.5/S5)

`ai_run_records` (migration 027) has no writer on any code path the app can reach: the only constructor is
`meridian/ai/run_records.py:81`, constructed at `scripts/evaluate_roles.py:41` and
`scripts/investigate.py:168,175`. **0 rows** in the only database that has the table. `OS-118`'s evaluation
harness therefore measures a table that is populated only when a human runs a script — which is honest, and
worth stating next to the harness rather than discovering later. **Confidence: high** (helper instrument, plus
§3.5/S5's independent import search).

#### P5 — `classification_corrections` is written and read by nothing, and holds 71 real rows (dead end)

Single site `meridian/repository.py:847` (INSERT); zero readers in `app.py`, `meridian/**`, `scripts/**` or
`tests/**`. The project's own inventory says the exact owner of that table is unknown. A real audit trail with
no consumer. **Confidence: high** (helper instrument; not re-verified line by line here).

#### P6 — the app's **default** database is six migrations behind the newest

**Evidence — re-verified here.** `app.py:113` — `DB_FILE = os.environ.get("DB_FILE", "savings_data.db")`;
that file's `schema_migrations` stops at **025** and lacks `ai_run_records`, `calendar_context_events`,
`crew_spend_selection_observations`, `crew_bill_allocation_observations`. `run_preview.py:28-30` defaults
`DB_FILE` to `/tmp/gate-preview/gate.db` (031). So **which schema the application has depends only on the
launcher**, and the fallback is the stale one. **Confidence: high.**

#### P7 — 22 of 50 live tables are created outside the migration runner (schema authority)

Instrument (helper): replay every `meridian/migrations/*.sql` into `:memory:` and set-difference against the
live schema. `schema_migrations` is therefore **not** the schema authority, and the checksum/append-only guard
`run_migrations` enforces (`meridian/db.py:108-157`) covers only part of the schema. No migration file is
unreachable — the runner globs the directory (`meridian/db.py:56`), so all 31 are reachable. **Confidence:
high** for the split; the risk is a judgement call.

#### P8 — five provider reads have no persistence path, and the rest go into a 300-second in-process cache

Exact set (helper, derived independently of `CREW_CAPABILITY_MATRIX.md`, which was **not** adopted as the
instrument): `readback_virtual_cards` (`meridian/providers/crewwork.py:323`),
`readback_physical_cards` (`:347`), `readback_autopilot_rules` (`:443`),
`readback_reassignment_rules` (`:520`), `readback_transfers` (`:533`); no table for any of them exists in
either schema. The `app.py` equivalents (family `:2437`, autopilot rules `:4808`, cards `:2524`, `:2607`,
transfers `:2175`, detail `:1964`) read into `SimpleCache(ttl_seconds=300)` (`app.py:323`) — a plain in-process
TTL dict, so nothing survives a restart. **The helper explicitly does not claim these should be persisted**;
that is a product judgement for the owner. **Confidence: high** for the code shape.

#### P9 — nothing schedules the calendar ingest

No scheduler of any kind exists in the tree (zero `schedule`, `apscheduler`, `crontab` hits; instrument:
helper's exact search). `ingest_calendar_context` is reachable only from
`scripts/calendar_context_ingest.py:152`, and §3.5/S4 shows the read side has no caller either. Both halves are
built; neither is run or read. **Confidence: high.**

#### P10 — the broker's launchd installer defaults to an interpreter that does not exist

`scripts/install_crew_broker_launchagent.sh:8` defaults to `PROJECT_DIR/venv/bin/python`; this checkout has
`.venv/` and `.venv311/`, so the preflight at `:21` exits unless `--python` is passed. Manual-install only.
**Confidence: high** (helper instrument; not re-verified here).

#### Method note — two of the helper's own instruments were wrong, and it withdrew its own findings

Recorded because the withdrawals are the asset (D-035): its first import-reachability graph (a) ignored relative
imports (`from .sync import`, level > 0) and (b) mis-keyed its own reach set, together producing **false
"persisted but never surfaced" results for `crew_bill_allocation_observations` and `cancellation_actions`**.
Both are recorded in `tmp/os123/data-jobs.md` as **withdrawn, not findings**. It also recorded the hypotheses
that came back *empty* (no read-never-written table, no unreachable migration file) instead of stretching them.

#### P11 — **importing `app` writes to the database** (hazard for every tool, test and agent in this lane)

**Claim.** `import app` is not a read. It runs `init_db()` at module level and mints secrets if they are absent,
against whatever `DB_FILE` resolves to — which defaults to the six-migrations-behind `savings_data.db` (§3.4/P6).

**Evidence — re-verified here.**
- `app.py:8825-8826` — the comment states it plainly: *"Initialize database tables on import (needed for gunicorn
  which doesn't run `__main__`)"*, then calls `init_db()`; the file contains 72 `CREATE TABLE`/`ALTER
  TABLE`/`INSERT` sites.
- `app.py:186` — `app.secret_key = get_or_create_secret_key()`, whose body inserts a new secret into `app_config`
  when absent.
- `app.py:1228` — `local_proposer_key = get_or_create_local_key(DB_FILE)`, also an insert.

**Why it belongs in this report.** The fresh-context routes helper hit it while building its instrument and had to
guard the import (redirect `sqlite3.connect` to an in-memory clone, raise on any filesystem write, and compare
`sha256` before/after) to keep its own audit read-only. Every test run, migration rehearsal and agent that has
ever done `import app` in this lane has written schema — and, on a fresh database, a secret — as a side effect.
**Confidence: high.** *Repair (proposed):* move `init_db()` behind an explicit call in both launchers, so the
import becomes the read it looks like. Bounded, but it touches production startup and therefore needs its own
slice and test, not a drive-by.

#### P12 — the migration runner is not the schema authority, and the default database is not the previewed one

Covered above as P6 (six migrations behind on the default `DB_FILE`) and P7 (22 of 50 live tables created outside
the runner). Recorded once more here only because P11 explains how the default database drifts: it is migrated by
*imports*, and by SQL-file migrations only when something runs the runner.

---

---

### 3.5 Unlinked seams found by direct reading (the author's own lens)

#### S1 — Accounts' "Available cash" is a third rule, computed in the browser, and its own comment says it matches Today's (concept 21; contradicts D-024's ONE money rule)

**Claim.** `Accounts` shows a headline money figure computed in JavaScript by summing `balance` over
"liquid" accounts, under a label ("Available cash") that reads as the same fact Today publishes as
"Safe to spend" and Plan as "Available". It is a different computation, on a different field, with the
**`is_active` filter missing** — while the server-side rule guards against exactly that hazard.

**Evidence.**
- `static/js/meridian/accounts.js:505-521` — `summarize()`; the filter at `:511-516` accepts
  `account_type === "checking" | "cash" | "savings"` or a `pocket` whose name is in `SPEND_POCKET_NAMES`
  (`:78`), and **never consults `a.is_active`**, although the payload carries it
  (`meridian/services/accounts.py:47`).
- `static/js/meridian/accounts.js:520` — `const available = liquid.reduce((sum, a) => sum + (Number(a.balance) || 0), 0)`.
- The comment at `:507-510` states the intent verbatim: *"This matches the Today safe-to-spend convention"*.
- The server convention it claims to match is `meridian/services/safe_to_spend.py:299-342`:
  `pool_total(money) + reserve − Σ set_aside − max(0, reserve)`, over `money_accounts()` which **does**
  filter `is_active` (`:236`).
- The hazard the client still carries is written down on the server side:
  `meridian/services/safe_to_spend.py:253-261` — *"the owner's Crew read carries two pockets named 'Free to
  Spend' — one of them inactive since 2026-09-17 — so a list-order match could land on a retired row."*
- Divergences that follow, in the same currency: (a) a **retired** pocket named "Free to Spend" counts toward
  Accounts' figure and not toward Today's; (b) an **overdrawn** non-spend pocket is subtracted by the server
  rule and ignored by the client; (c) a **negative reserve** reduces the server figure and is invisible to the
  client; (d) the spend pocket is identified by **name** in the browser, where OS-113 made Crew's own
  `selectedSpendSubaccount` authoritative server-side with the name rule as a declared fallback that must say
  it fell back.

**Instrument.** I4 (exact read of both call sites and the payload field) plus the quoted server guard. **Not**
demonstrated on live data and not demonstrated by any capture — see §1's fixture caveat.

**Confidence.** High that the paths differ; **unverified** how far the figures diverge on the owner's data.

**Repair (proposed, owner's decision):** the figure belongs on the server, next to the rule that already
exists — Accounts should render `safe_to_spend()`'s result and its basis, and the browser should stop doing
money arithmetic. Whether the *label* becomes "Safe to spend" on Accounts is a **visual/authority question and
is owner-gated** (it changes a surface the owner accepted). Bounded slice, presentation + one payload field.

#### S2 — the advisor's coverage verdict is computed from the DIAL's money rule while the header shows the other one (concept 8)

**Claim.** The advisor panel can state, as a sentence with a confidence of 1.0, that "Available cash of $X
covers / does not cover near-term obligations" — where `$X` is the dial's `availableToSpend`, a rule
`meridian/services/reserves.py:36-44` explicitly records as *kept for the dial only*, superseded on Safe to
Spend and Plan by OS-111. In one session the owner can therefore read two different "available cash" numbers,
one in the header and one inside the advisor's own explanation.

**Evidence.**
- `meridian/services/dial.py:78-124` — `_available_to_spend()`: the spend pocket's `available_balance`, else
  the sum of cash-type accounts' `available_balance`, then minus the reserve deficit.
- `meridian/services/dial.py:611` — shipped as `"availableToSpend"`.
- `meridian/api.py:927` — `build_financial_weather(dial)`, i.e. the weather is built **from the dial payload**;
  it cannot see Today's `safe_to_spend` figure.
- `meridian/proactive.py:113-121` reads it; `:328-356` uses it as the coverage basis and prints it in the
  owner-visible sentence.
- `static/js/ui/advisor_fab.js:263-291` renders those events and explanations.
- `meridian/services/reserves.py:36-44` — the recorded partial supersession: *"The two rules above still govern
  the DIAL … What OS-111 replaced is the mechanism on Safe to Spend and on Plan's Available."*

**Instrument.** I4 (caller sets in both directions: who produces `availableToSpend`, who consumes it).
**Confidence.** High on the mechanism; the *magnitude* of any divergence on the owner's data is unverified.

**Repair (proposed):** the weather should take the OS-111 figure as its coverage basis (one rule, one number),
or state the basis it used. This is a **behaviour change to a user-visible verdict**, so it is a decision, not
a cleanup — and the owner's D-024 says one money rule, which argues for the first form.

#### S3 — a dead transport field that is not dead: `availableToSpend` is sent to the browser, mapped, and rendered nowhere (dead end, low)

**Claim.** `availableToSpend` reaches the client, is assigned into the dial model at
`static/js/meridian/dial.js:538`, and is referenced **nowhere else** in `static/js/**` — because OS-098 moved
the figure out of the compass. Its only remaining consumer is server-side (S2).

**Evidence.** `static/js/meridian/dial.js:17` (typedef), `:538` (assignment); the centre deliberately states the
selected event instead (`:644-676`, with the reason in the comment at `:655-663`). Instrument I4.

**Confidence.** High. **Repair:** either delete the field from the client contract, or make it visible where it
belongs. Low stakes, and it should be decided together with S2 so the two halves do not drift further.

#### S4 — calendar context is ingested, has a read method, and nothing reads it (dead end; sharpens `OS-067`)

**Claim.** The calendar half of the evidence lane writes rows and exposes `list_between()`; **no production
code calls it**. Only `liveness()` is called, from an ingestion status helper.

**Evidence.**
- `meridian/calendar_context.py:127` — `list_between()`; exact caller search over `app.py`, `meridian/**`,
  `scripts/**` returns **no production caller** (tests only).
- `meridian/services/ingestion_routes.py:76` — the one production call into the store, and it asks for
  `liveness().get("last_observed_at")`, not events.
- `calendar_context_enabled()` (`:66`) is consulted only by `meridian/calendar_context.py:201` and
  `scripts/calendar_context_ingest.py:163` — nothing in the app gates on it.
- No template or JS module renders calendar context (`calendar` in `static/js/**`/`templates/**` is date
  formatting, a connector kind, or an icon name — not this store).

**Instrument.** I4 (caller sets, then a literal search for the method names). **Confidence.** High.
**Repair:** this is `OS-067`'s calendar half — the finding is that the *read* method is the unbuilt half, so the
repair is a surface/consumer, not more ingestion.

#### S5 — role runs persist into a table no surface can see (dead end × concept 3/6; feeds `OS-076`)

**Claim.** `ai_run_records` (migration 027) is written by `scripts/investigate.py` and read by
`scripts/evaluate_roles.py`. Neither `app.py`, `meridian/api.py` nor `meridian/services/**` mentions the store
or the table, and no template or JS module mentions runs, roles, council, or the role names. The provenance the
envelope was built to guarantee is therefore **CLI-only**: it exists in the audit trail and nowhere the owner
can look.

**Evidence.** I4: `grep -rn "RunRecordStore|ai_run_records" app.py meridian/api.py meridian/services/` → no
match; the same for `ai_run|run_id|council|skeptic|forecaster|guardian|teacher` over `templates/**` and
`static/js/**` → no match. (`templates/partials/advisor_fab.html` mentions "Virgil", which is the advisor
surface, not a council role.)

**Confidence.** High. **Repair:** `OS-076`'s surface is the natural home; the finding adds that there is
**no read path at all** today, so the surface needs a read API before it needs a design.

#### S6 — alerts have no feedback path, and the coverage matrix's "no delivery channel" is now half-false (concept 8)

**Claim.** The weather IS delivered — the advisor panel renders its events and explanations
(`static/js/ui/advisor_fab.js:263-291`) — so `CONCEPT_COVERAGE.md`'s row 8 ("no delivery channel") is
**stale** and should be corrected in the same commit that accepts this report. What does not exist is any
**feedback** path: no table, no route, no field, no UI control by which the owner can say an alert was useful
or wrong.

**Evidence.** I4: `grep -rni feedback` over `app.py`, `meridian/**`, `templates/**`, `static/js/**` returns two
unrelated JS comments (`static/js/features/dragdrop.js:49` haptics, `static/js/api/cards.js:216` button state).
No migration creates a feedback table (exact set of `meridian/migrations/*.sql`).

**Confidence.** High for "no feedback path exists". **Repair:** a feedback record is the smallest thing that
would let `OS-118`'s evaluation harness measure usefulness in the product rather than in a script — but it is a
new capability and therefore an owner decision, not a cleanup.

#### S7 — the scenario preview compares two definitions of "runway", so it reports a change when nothing changed (unfinished; concept 12)

**Claim.** The Plan scenario panel renders "Runway `X → Y` days (Δ)". The base `X` is
`beacon.forecast()`'s runway, which subtracts known obligations; the scenario `Y` is recomputed by
`scenarios.run_scenario()` from `starting_cash / daily_expense`, which subtracts nothing. The delta is
therefore partly **definitional**, and with **no changes requested** it is non-zero.

**Evidence.**
- `meridian/beacon.py:137` — `runway_days = max(0, floor(max(0, starting_cash - known_obligations) / daily_expense))`.
- `meridian/scenarios.py:24` — `runway_days = floor(starting_cash / daily_expense) if daily_expense > 0 else None`.
- `meridian/scenarios.py:68-72` — `comparison["runway_days"] = scenario.runway_days - base.runway_days`.
- `static/js/meridian/plan.js:439-455` — renders `${runwayBase} → ${runwayScenario} days (${scenarioDeltaDays(delta)})`,
  **recomputing the delta in the client** (`const delta = runwayScenario - runwayBase`) instead of reading the
  server's `comparison.runway_days`.
- **Demonstrated (I5)**, a production-shaped base (`starting_cash=1000`, `daily_expense=20`,
  `runway_days=40` as beacon would compute it with 200 of near obligations, which are 200):
  `run_scenario(base, {})` → `scenario.runway_days = 50`, `comparison["runway_days"] = 10`,
  `comparison["starting_cash"] = 0.0`, `comparison["low_point"] = 0.0`, `assumptions == ()`.
  **A plan with nothing changed is shown as ten days better.**
- **And the tests cannot see it** (`tests/meridian/test_scenarios.py`): the fixture at `:8-24` sets
  `starting_cash=1000, daily_expense=20, runway_days=50` — where `1000/20 == 50` exactly, so the two formulas
  agree by construction. `test_confirmed_context_range_is_labeled_as_assumption_not_fact:63-66` asserts
  `result.scenario == _base()` for an unchanged plan and passes **only** because the fixture is degenerate for
  this property. This is the "constant-shaped assertions cannot catch a degenerate shape" lesson
  (`AGENT_COORDINATION.md`, 2026-09-25 fourteenth pass) in a second location.

**Confidence.** High (demonstrated, not inferred). **Repair (proposed):** one runway definition, owned by
`beacon`, and the scenario applies *changes* to it. Then the fixture must be a base where the two formulas
disagree, or the guard is decorative again. This is a **financial-figure behaviour change**, so it is a
decision — but it is a *displayed comparison that is not true*, which the project's own rules treat as a
defect rather than a preference.

#### S8 — `beacon.runway_days` clamps at zero and ignores the inflows its own walk includes (unfinished; concept 2)

**Claim.** Two inconsistencies in one line and its neighbour: the runway scalar is floored at zero — the class
`meridian/services/reserves.py:29-31` forbids in this project's own words (*"Flooring it at zero would hide an
overdraft behind a plausible-looking zero, which is the same class of fabrication D-017 forbids"*) — and it
ignores paycheck inflows, while the 90-day walk three lines below includes them, so "days of runway" and
`first_shortfall` can describe different futures.

**Evidence.** `meridian/beacon.py:137` (`max(0, floor(max(0, …)))`) versus `:146-158` (the walk, which adds
`paycheck_inflows` and subtracts obligations, producing a `low_point` that may be negative and a
`first_shortfall`). Consumers that render the clamped scalar: `meridian/services/today.py:270-287,337-348` and
`meridian/api.py:482`.

**Confidence.** High on the code shape; **the owner-visible consequence is a judgement call** (Today says "no
runway remains before funding" at 0, which is closer to honest than a bare "0 days"). **Repair:** decide
whether a negative runway is stated (and in what words) and whether inflows belong in the scalar. Owner-gated
because it changes a headline number's meaning.

#### S9 — the claims table's "Current claims" misreports the tree (process; advances no concept — stated plainly per D-033.3)

**Claim.** 8 of the 74 rows in `docs/project/AGENT_COORDINATION.md`'s *Current claims* table declare
`**active**`, while the working tree at `e7f877d` is clean apart from declared untracked scratch and each
named body of work is in committed history. The file's own rule 2 is *"Release on commit."* An agent that
trusts the table will believe files are held that are not.

**Evidence.** Instrument: parse of the table's rows (8 containing `**active**`) plus `git status --short` at
`e7f877d`. The stale rows include `OS-113`, `OS-111`, `OS-079`, `OS-078`, `OS-077`, and three older
`Builder (…)` rows.

**Confidence.** High for the count. **Repair:** a release pass, and — better — a guard analogous to the
`agent-claims.json` generation counter, so a claim that outlives its commit is visible rather than trusted.

---

### 3.6 Retraction — the gap `OS-125` was created to fill does not exist, and two published claims are false

This is the audit's most consequential result, and it is a retraction rather than a finding. It arrived by two
independent routes in the same session: this lane's own fresh-context retrieval helper
(`tmp/os122/prose-retrieval.md`) and an unrelated concurrent lane's commit `5c33b69`. Both reached the same
conclusion; the instrument below is this lane's, and every element of it was re-read here.

**Claim withdrawn (1).** *"Of Crew's 17 write operations, 16 are covered by our registry and the one genuine gap
is `DeleteBill`."* — published in `CREW_CAPABILITY_MATRIX.md:122-126`, in `MERIDIAN_DECISIONS.md`'s D-035 payoff
table, in the handover text recorded in `CURRENT_STATUS.md`, and still carried verbatim by two ledger tasks
(`OS-122`'s detail and `OS-125`'s detail).

**Claim withdrawn (2).** *"`updateRule` appears in neither catalogue."* — `CREW_CAPABILITY_MATRIX.md:126`.

**Instrument.** Parse the connector's **own** registry for the CLI-operation → provider-mutation mapping
(`/Users/stephenwest/Applications/CrewWorkAssistantOTP/src/crew_work_assistant/crewwrite.py:23-60`), parse our
catalogue (`meridian/crew_commands.py`, alias → `CommandSpec` → mutation document), our executor allow-list
(`meridian/crew_write.py:19-37`) and our governed action map (`meridian/crew_write_actions.py:661-705`), then
compare **provider mutation names**, never local aliases. Result: **17 connector CLI operations → 17 distinct
provider mutations → all 17 executable → all 17 bound to a governed action with an executor**, 16 of them with a
readback verifier.

| connector CLI op | provider mutation | executable | governed action |
|---|---|---|---|
| `archive_bill` | **`DeleteBill`** | yes | `archive_crew_bill` |
| `create_autopilot_rule` | `CreateAutopilotRule` | yes | `create_crew_autopilot_rule` |
| `create_bill` | `CreateBill` | yes | `create_crew_bill` |
| `create_paycheck_funding_plan` | `CreatePaycheckFundingPlan` | yes | `create_crew_paycheck_funding_plan` |
| `create_pocket_reassignment_rule` | `CreatePocketReassignmentRule` | yes | `create_crew_pocket_reassignment_rule` |
| `create_subaccount` | `CreateSubaccount` | yes | `create_crew_pocket` |
| `create_virtual_card` | `CreateVirtualDebitCard` | yes | `create_crew_virtual_card` |
| `delete_paycheck_funding_plan` | `DeletePaycheckFundingPlan` | yes | `delete_crew_paycheck_funding_plan` |
| `delete_pocket_reassignment_rule` | `DeletePocketReassignmentRule` | yes | `delete_crew_pocket_reassignment_rule` |
| `delete_rule` | `DeleteRule` | yes | `delete_crew_autopilot_rule` |
| `delete_subaccount` | `DeleteSubaccount` | yes | `delete_crew_pocket` |
| `initiate_transfer` | `InitiateTransferScottie` | yes | `crew_initiate_transfer` |
| `set_spend_pocket` | `SetActiveSpendPocketScottie` | yes | `set_crew_spend_pocket` |
| `top_up_reserve` | `TopUpReserve` | yes | `top_up_crew_reserve` |
| `update_bill` | `UpdateBill` | yes | `update_crew_bill` |
| `update_bill_reserve_settings` | `UpdateBillReserveSettings` | yes | `update_crew_bill_reserve_settings` |
| `update_paycheck_funding_plan` | `UpdatePaycheckFundingPlan` | yes | `update_crew_paycheck_funding_plan` |

**How the error was manufactured.** Our tree carries **two** catalogues, and they name the same provider
mutation differently:
- `docs/project/crew_mutations.json:10-11` — `"ArchiveBill": {"operation": "ArchiveBill"}`;
- `meridian/crew_commands.py:47-51` — `DELETE_BILL_MUTATION = """mutation DeleteBill($id: ID!) { deleteBill(input: { billId: $id }) … }""`,
  registered at `:111` as `CommandSpec("DeleteBill", …)`.

The connector names its **CLI operation** `archive_bill` while its **provider mutation** is `DeleteBill`
(`crewwrite.py:49-53`; the contract is `write_operations/archive_bill.graphql:1`). The withdrawn comparison ran
against the JSON catalogue and read our `archive_bill` as "an archive, not a delete". The error is visible
inside the sentence that published it — *"we register `create_bill`, `update_bill` and `archive_bill`, and no
delete"* — and it is the same class as D-035's four retractions: **a name-set comparison published as a
capability conclusion.**

**And the verifier `OS-125` proposed to build already exists.** `meridian/crew_write_actions.py:184-204` —
`_verify_archived_crew_bill` reads a fresh complete provider snapshot and returns `{"ok": not present, …}`
(absence **is** the proof, for a deletion), `ok: None` when the snapshot is incomplete, has no bill identity, or
the readback is unavailable, with `provider_truth` stated explicitly. That is OS-125's steps 2 and 3, in
production, tested.

**Claim (2)'s true content.** `meridian/crew_commands.py:60-64` carries
`mutation EditRoundUpRule($input: UpdateRuleInput!) { updateRule(input: $input) { … } }` and registers
`edit_autopilot_rule` at `:115-117`. So `updateRule` is documented in **our** catalogue. What is actually true is
the inverse of what was published: the **connector** has no CLI operation for it (its 17 operations contain no
update-rule — re-read here), so `meridian/crew_write.py::_ALLOWED` cannot execute it and no governed action
exists — while `/api/account/autopilot-rules/update` (`app.py:5039-5057`) performs it with raw GraphQL and live
credentials and is declared ungoverned in the ratchet (`tests/test_governed_write_routes.py:57`).
**A capability in use that no operable contract down the stack records** — the owner's own phrasing, and the
genuine half of the retrieval.

**Why "16 of 17" was believable, and where the real 16/17 lives.** `CREW_CAPABILITY_MATRIX.md:16` says *"16 of
the 17 carry readback verifiers"* — that is **correct in its own terms**: 17 registered action types, the one
without a verifier being `top_up_crew_reserve`, bound to `no_verify` at `crew_write_actions.py:686` and pinned
by `tests/meridian/test_write_coverage.py:127-153`. Two different denominators with the same-shaped number were
written as if they were one fact, and the conflation is what created `OS-125`.

**Corrections this retraction requires, in the same change** (each is a stale record, not a plan change):
`MERIDIAN_OS_TASKS.json` `OS-122.detail` and `OS-125`; `CREW_CAPABILITY_MATRIX.md:122-126`;
`MERIDIAN_DECISIONS.md`'s D-035 payoff table; the handover paragraph in `CURRENT_STATUS.md`. Per D-033 and D-035
the retraction is recorded where the claim was made, not only here.

**What survives, unchanged and still open.**
- `/api/delete-bill` (`app.py:5837-5841`) still calls the **raw** `delete_bill_action`, so the *route* is
  ungoverned while its *operation* has been governed all along. Re-pointing it is `OS-119`'s owner-gated
  decision — exactly as `OS-125`'s own step 4 said.
- `top_up_crew_reserve` is money-moving with `no_verify` (`OS-120`).
- The `updateRule` asymmetry above.
- `BILLER_CAPABILITIES.md:53` cites `CREW_MUTATION_INVENTORY.md`, which is **not tracked at HEAD** (verified:
  `git ls-files` finds no such path) — a dangling citation in a governing document.

---

## 4. What the audit did NOT find (stated so its absence is visible)

- **No secrets** in tracked files are reported here; nothing in this audit required reading `.env`, and it was
  not read. (`.env` exists at the repo root and is untracked/ignored; leave it alone.)
- **No provider mutation, no live read, no write** was performed or needed.
- **Still undecided** (named with the instrument that would settle each, never guessed): routes nothing in the UI can
  reach; UI references matching no route and their dynamic cases; routes reachable only from `tests/**` or
  `scripts/**`; routes that redirect and never render; and whether any `@login_required`-only route can reach a
  Crew provider mutation — the question this task cares about most. The scripts for all five are left in
  `tmp/os123/routes.md` §4–§6. The legacy routes' render-vs-redirect behaviour is undecided too (§3.1/R4).

## 5. Method corrections this audit earned

1. **The isolated synthetic preview cannot be the only instrument for dead ends.** Its limited route set
   returns 404/501 for real app endpoints (`/api/meridian/crew/mutations-status`,
   POST `/api/meridian/plan/scenario` — both exist at `meridian/api.py:2090` and `:365`). A capture-only audit
   would have reported two false dead ends. Instrument I3's output is therefore only usable **after** checking
   the real route set — recorded here because the next session will reach for the same probe.
2. **Fixtures written to agree cannot detect divergence.** §1's caveat: the two money figures in the governed
   fixtures are equal by construction, so S1/S2 are invisible to every capture in this repository. A guard for
   either needs a **divergent** fixture, which is the same lesson as the degenerate `run_scenario` fixture (S7).
3. **A "dead" transport field is worth following to its consumer before writing it off.** `availableToSpend`
   looked like an orphan in the client; it is load-bearing on the server (S2). The client-side absence is real;
   the field is not dead.
4. **A capability gap must be measured on the provider's own identity for the thing, never on local aliases.**
   §3.6 is the proof: two catalogues in this one repository name the same Crew mutation `ArchiveBill` and
   `DeleteBill`, and a comparison keyed on the alias manufactured a gap that launched a task (`OS-125`). The
   stable key is the mutation the provider actually receives — here, the connector's registry maps its CLI
   operation to that name and is the only local artefact that does.
5. **A second-hand finding is a hypothesis until it is re-read.** Every headline finding in this report was
   re-verified here from the cited line; two helper claims needed correction on the way in (the preview-404 trap
   in §5, item 1, and a script count that is 24 in `base.html`, not 23). The helpers' own withdrawals are recorded in
   §3.4's method note. An audit that forwards its helpers' reports unverified has the same defect as an audit
   that forwards a mention-grep.
6. **A guard's marker list is part of the guard.** `GOVERNED_MARKERS` in
   `tests/test_governed_write_routes.py:89` contains `route_many`, a function nothing calls (§3.3/U1). No route
   is wrongly passing today, but the marker set is hand-kept prose in a test and should be re-derived from the
   live call graph before it drifts into decoration.

7. **A concurrent session is not evidence about that session.** This audit's method note said the earlier retrieval
   thread "died with its session and left nothing on disk", and used it to justify requiring helpers to write to
   disk before returning. The owner corrected it on 2026-09-25: **that session never died**, its output is preserved
   there, and it is still asking him owner-gated questions. The inference was made about a session this lane cannot
   see — the same failure D-035 names, in a new place. The practice it justified is still right for the right reason:
   a report that lands only in another session is not one this lane may cite, so the retrieval was re-run rather than
   assumed lost. Recorded here because the corrections are the asset.

## 6. Repair backlog (proposals only — promotion is the owner's decision)

The ids below are **proposals**. `OS-126` and `OS-127` were created this session by a concurrent lane for
different work (cardholder exposure; the retrieved payday/funding reconciliation), and **`OS-128` was then taken
by the owner's own directive** (the Today↔Plan spend alignment review, `TODAY_PLAN_SPEND_ALIGNMENT_2026-09-25.md`),
so the ids written into this table are indicative and start one higher in the ledger. Appearing here promotes
nothing (`AGENTS.md` §Handoffs, rule 4); the owner promotes.

**Ordered by "defect with a concrete failure" first, judgement calls last.**

| # | Finding | Proposed slice | Why it is bounded | Class |
|---|---|---|---|---|
| R1 | **P1** `pocket_groups` ghost table: `POST /api/assign-group` always fails (HTTP 200), and a deleted pocket keeps rendering from a stale `pocket_links` row | **defect fix**: create the table or delete both write paths; make the deletion cleanup delete the row the UI reads | two handlers in `app.py`; no model, no route added, no authority touched | defect — no owner decision needed to *plan*, and the owner may still choose delete-vs-create |
| R2 | **U2** bare `except` silently empties `crew_write_executors` | **defect fix**: fail loudly, or degrade with a recorded reason surfaced in the UI | one handler; touches the write pipeline's failure reporting | defect (safety-adjacent, `D-031` family) |
| R3 | **P2** launcher asymmetry: the container runs no provider sync or evidence poll | **defect fix**: one launcher contract, both services started or both declared off, with a test | launcher + config only | defect (deployment) |
| R3b | **P11** `import app` writes schema and mints secrets (`app.py:8826`, `:186`, `:1228`) | **defect fix**: move `init_db()` behind an explicit launcher call so the import is the read it looks like; a test that imports `app` against a read-only DB | one call site moved, two launchers touched, one test | defect (operational; changes production startup, so it needs its own slice) |
| R4 | **P3** `ResumableIncremental` never runs, so ingest dedup is unexercised | **investigate then wire**: confirm the duplicate-ingest risk against a real mailbox before building | one class + its caller | defect (unproven) |
| R5 | **S7 + S8** two runway definitions; the scenario delta is non-zero with no changes; `beacon` clamps at 0 and ignores inflows | **new task (`OS-128`)**: one definition owned by `beacon`; scenario applies changes; a **divergent** fixture | one function + one client line + one fixture | **owner**: changes a displayed comparison and a headline figure |
| R6 | **S1** Accounts' "Available cash" is a browser-side third rule, missing the `is_active` filter its own payload carries | **new task (`OS-129`)**: render the server's figure and its basis; no label change without the owner | one payload field + one JS function | **owner**: an accepted surface's figure |
| R7 | **S2** the advisor's coverage verdict is computed from the dial's superseded rule while the header shows the other | **new task (`OS-130`)**: weather takes the OS-111 figure, or names its basis in the sentence | one call site + its tests | **owner**: a visible verdict |
| R8 | **S3** `availableToSpend` shipped to the client and rendered nowhere | decide together with R7 (one decision, two halves) | — | **owner** |
| R9 | **T1** the whole legacy front end is reachable only through an unlinked `/debug` | **owner decision (`OS-131`)**: link it, fence it, or delete it with its 22 modules and the service worker | deletion is large; linking is tiny — the options differ by 100× | **owner** (product/visual) |
| R10 | **T2** the Today forecast chart cannot render (markup deleted, guard, CSS and a browser assertion still present) | **owner decision (`OS-132`)**: restore the markup or delete all three parts | one partial, one CSS block, one test | **owner** (visual) |
| R11 | **T3/T4/T7** 18 unrendered templates, unlinked `onboarding.html`, manifest not linked from the shell | fold into **`OS-084`** (management routes) and the surface-reachability mechanism | existing mechanisms | mixed |
| R12 | **S5 / U7** role runs persist with no read path; the council is CLI-only | already **`OS-076`** (owner gate recorded) | — | owner gate exists |
| R13 | **S4 / P9** calendar context is ingested, read by nothing, and scheduled by nothing | already **`OS-067`** (calendar half) | — | owner gate exists |
| R14 | **S6** alerts have no feedback path | **earmark**: the smallest usefulness signal for `OS-118` | new capability | **owner** |
| R15 | **§3.6** the retraction, and the corrections it requires | **done in this change** — records corrected, `OS-125` closed as withdrawn | docs only | correction, not a slice |
| R16 | **§3.6** `updateRule`: in use by an ungoverned route, absent from the connector and from the executor | **new task (`OS-133`)**, but it needs a **connector** change (a write contract + CLI op), which is outside this repository | bounded here; not bounded there | **owner**: touches another tree's scope |
| R17 | **S9** eight stale `**active**` claims | **release pass now**; a guard is a separate proposal | docs only | process |
| R18 | **§3.6** `BILLER_CAPABILITIES.md:53` cites a file that is not tracked | one-line correction in the same change | docs only | correction |

**Non-goals, stated so they are not silently absorbed.** This audit does not: fix anything; persist any of the
five unpersisted provider reads (`P8` — that is a product judgement, and the helper explicitly declined to claim
it); decide D-038's cardholder question (a concurrent lane owns it); or restore anything retrieved from the
older tree (D-037 — `OS-127` holds those options).

| R19 | **R2** `GET /meridian` is registered twice and `meridian_shell` (`app.py:3846`) can never run (first-registered wins, settled empirically on Flask 3.1.3) | **defect fix**: delete the duplicate, or make it the fallback it resembles | one decorator + one function | defect (invisible while it works) |
| R20 | **R3** the `/api/meridian/*` namespace has two hand-written members in `app.py`, one of them a browser-permitted write channel, and `scripts/verify_readiness.py:62` sees only the blueprint half | **defect fix**: have the readiness scan enumerate routes rather than `register_blueprint` calls | one scan + its test | defect (a check that cannot see two routes) |

## 7. Provenance of this document

- Author: Constitutional Builder (Meridian lane), session of 2026-09-25 (evening). **Written across `e7f877d` →
  `5c33b69`**: a concurrent lane committed `5c33b69` (docs only — `HANDOFF.md`, `MERIDIAN_DECISIONS.md`,
  `MERIDIAN_OS_TASKS.json`, `RETRIEVAL_SIBLING_TREE_2026-09-25.md`) while this audit was running, and that
  commit carried this lane's in-flight ledger edit (`OS-123` → `in_progress`). No application file changed in
  either commit, so every line number in this report holds at `5c33b69`.
- Raw helper evidence (untracked, per this repository's convention that `tmp/**` and `artifacts/**` are not
  committed): `tmp/os123/routes.md`, `tmp/os123/js-templates.md`, `tmp/os123/data-jobs.md`,
  `tmp/os123/unfinished.md`, `tmp/os123/console.json`, `tmp/os123/console_probe.py`, and
  `tmp/os122/prose-retrieval.md`.
- Rendered evidence: `artifacts/os123-integration-audit-2026-09-25/captures/manifest.json` (40 governed
  records at `e7f877d`, fixture `os123-synthetic-preview-e7f877d`, frozen clock `2026-09-08T13:42:00Z`).
- Findings only. **No application file was modified by this audit.** No server was started, stopped or
  restarted; the only environment action was reading the already-running isolated preview, whose served markup
  was checked against HEAD before any capture was trusted.
