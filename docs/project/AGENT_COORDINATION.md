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
| Constitutional Builder (OS-103: the Accounts aesthetic, measured) | `static/css/meridian/accounts.css`, `static/js/meridian/accounts.js`, `static/css/meridian/observatory.css`, `tests/meridian/test_accounts_rail.py`, `tests/meridian/test_accounts_size.py` (new), `design-qa.md`, `docs/project/{MERIDIAN_OS_TASKS.json,CURRENT_STATUS.md,AGENT_COORDINATION.md,agent-claims.json,session-emergent.json,HANDOFF.md}` | 2026-09-24 | **released** at `8bc3c16`, with a follow-up docs commit for the regenerated handoff. The owner's four-named Accounts aesthetic, measured against `design/observatory-drafts-2026-09-08/04-accounts.png` before anything was drawn. Three traits are fidelity deltas and are built: the ticket's painted face 357.3x134.3 -> 356.7x179.7 CSS (73% -> 98.1% of the concept's height), the card around the rows removed in both themes with the light theme's rules re-inked for parchment, and the cord tinted along its length from each row's tint to the next. The fourth (icons) changes the glyph SYSTEM, so it is verified and proposed, not implemented. Presentation only: no route, data, financial, provider or authority change. Also repaired here: `agent-claims.json` had five claims under one agent id, which made `check_guardrails.py` die with `CONFIG duplicate claim` for ANY agent; they are consolidated into one generation-6 claim whose note names each superseded id, and no declared scope was lost. |
| Constitutional Builder (dial ticket contrast + invoice-note spacing follow-up) | `static/css/meridian/dial.css`, `static/js/meridian/dial.js`, `tests/meridian/test_dial_js.py`, `tests/browser/test_dial_fidelity.py`, `docs/project/{CURRENT_STATUS,AGENT_COORDINATION}.md` | 2026-09-24 | **released** with the row below at the 2026-09-24 (seventh pass) commit: the parchment ticket ink correction and the removal of the redundant `"Bill email attached."` line shipped together with the pointer/controls work, because both touch `dial.js` and `dial.css` and could not be separated at file level. |
| Constitutional Builder (Today control/pointer and Settings ornament follow-up) | `static/js/meridian/dial.js`, `static/css/meridian/dial.css`, `static/css/meridian/settings.css`, `tests/meridian/test_dial_js.py`, `tests/browser/test_dial_fidelity.py`, `meridian/api.py`, `meridian/services/dial.py`, `templates/meridian/partials/today.html`, `tests/meridian/services/test_dial.py`, `tests/browser/test_dial_reserved_amount.py`, `tests/meridian/test_plan_view_switch_contrast.py`, `docs/project/{CURRENT_STATUS,AGENT_COORDINATION,MERIDIAN_OS_TASKS,session-emergent}.json`, `docs/project/MERIDIAN_OS_TASKS.json` | 2026-09-24 | **released** at the 2026-09-24 (seventh pass) commit. Owner-requested read-only visual work: the stylus becomes a visible instrument hand, the duplicate day-navigation buttons are removed (the keyboard range path and `T` survive), every day number can be shown from ONE revertible constant, the arc spreads to +132°, and the decorative Settings hourglass moves to the upper-right corner and grows to 132px. No financial authority, provider, route or action-pipeline change. |
| Constitutional Builder (OS-078: negative reserve vs Safe to Spend) | `meridian/services/reserves.py` (new), `meridian/services/today.py`, `meridian/services/dial.py`, `tests/meridian/services/test_reserve_deficit.py` (new), `tests/meridian/services/test_today.py`, `docs/project/{MERIDIAN_DECISIONS.md,MERIDIAN_OS_TASKS.json,CURRENT_STATUS.md,AGENT_COORDINATION.md,agent-claims.json}` | 2026-09-21 | **active**. Owner-reported correctness fix to a headline figure; display only, no route or schema change. |
| Constitutional Builder (OS-077: evidence fact bundle) | `meridian/ai/facts.py` (new), `meridian/ai/investigator.py`, `scripts/investigate.py`, `tests/meridian/test_ai_facts.py` (new), `tests/meridian/test_ai_investigator.py`, `tests/test_investigate_script.py`, `docs/project/{MERIDIAN_OS_TASKS.json,CURRENT_STATUS.md,AGENT_COORDINATION.md,agent-claims.json}` | 2026-09-21 | **active**. Backend PREREQUISITE for OS-076, delivered under its own id so OS-076's acceptance is not redefined. Read-only: no route, template, JS or CSS in this claim, and `meridian/ai/**` stays this lane's. |
| Constitutional Builder (OS-075 defect fix: negative bill reserve) | `meridian/migrations/028_allow_negative_bill_reserve.sql` (new), `tests/meridian/test_bill_reserve_negative.py` (new), `tests/meridian/test_migrations.py`, `tests/meridian/test_bill_reserve_observations.py`, `docs/project/{MERIDIAN_DECISIONS.md,MERIDIAN_OS_TASKS.json,CURRENT_STATUS.md,AGENT_COORDINATION.md,agent-claims.json}` | 2026-09-21 | **released 2026-09-21** at `1fb530f`. See the log entry below. |
| Codex design handoff 2026-09-21 | `design/investigator-medallions-2026-09-21/**`, `docs/project/AGENT_COORDINATION.md` (own row/log only), `docs/project/{CURRENT_STATUS,MERIDIAN_DECISIONS,HANDOFF}.md`, `docs/project/{MERIDIAN_OS_TASKS,session-emergent}.json` (own additive records only) | 2026-09-21 | **released at `e62f555`**. Owner-requested medallion artwork and Investigator surface specification for DeepSeek Harness. Full icon pack and desktop Settings excluded. No runtime or Track I backend edits; preserve the active builder claim. |
| Constitutional Builder (Track I: OS-072 envelope, OS-073 Investigator, I.3 council) | `meridian/ai/**` (envelope, role, investigator, skeptic, council, run_records), `meridian/migrations/027_ai_run_records.sql`, `scripts/investigate.py`, `tests/meridian/test_ai_{envelope,investigator,council,run_records}.py`, `tests/test_investigate_script.py`, `tests/meridian/test_migrations.py`, `tests/meridian/test_bill_reserve_observations.py`, `docs/project/{MERIDIAN_OS_TASKS.json,MERIDIAN_ROADMAP.md,CURRENT_STATUS.md,AGENT_COORDINATION.md,agent-claims.json}` | 2026-09-21 | **released 2026-09-21** at `b2bc935` (OS-072 persisted run records), `0c30f9f` (OS-074 council + Skeptic), `331c28f` (handoff). Track I lane complete as scoped: the envelope, the permissions, the Investigator, the Skeptic, the council and the persisted run record all shipped, all tested, no role able to reach a provider write path. **Still open and Astra's design work per the owner 2026-09-21: OS-038's medallion glyphs and the Investigator's customer-facing surface -- which THIS LANE IMPLEMENTS when the assets/design land.** |
| Constitutional Builder (Track D closure: OS-038 remainder, OS-065, OS-071) | `static/css/meridian/accounts.css`, `static/js/meridian/accounts.js` (only if an SVG layer proves necessary), `tests/meridian/test_accounts_rail.py`, `tests/meridian/test_accounts_connectors.py` (new), `templates/meridian/settings.html`, `templates/meridian/partials/settings-navigation.html`, `static/css/meridian/settings.css`, `templates/meridian/partials/virgil.html` (new), `static/css/meridian/virgil.css` (new), `scripts/preview_observatory_dial.py`, `tests/meridian/test_settings_visual_preview.py`, `tests/meridian/test_settings_hub.py` (new), `tests/meridian/test_virgil_surface.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-21 | **released 2026-09-21** at `d60f1c9`, `25181bd`, `38328df`, `9a55413`, `56e3372` (owner-directed Track D closure: OS-065 Settings hub, the calendar read-only leg, the Settings ingestion routes, OS-071 Virgil). Visual authority is `design/observatory-extension-2026-09-18/`; the 09-08 drafts are superseded only where 09-18 does NOT cover a surface, verified this session. Presentation and read-only only: no route, data, financial, provider or authority change. Virgil ships INERT. **OS-038's medallion glyph artwork remains OPEN and is now Astra's work, not this lane's.** |
| Codex owner-rulings | `docs/project/{agent-claims.json,AGENT_COORDINATION.md,MERIDIAN_DECISIONS.md,CURRENT_STATUS.md,MERIDIAN_OS_TASKS.json,HANDOFF_FOR_ASTRA_2026-09-19.md,DEEPSEEK_HANDOFF_2026-09-19.md}`, `design/observatory-sun-2026-09-19/**`, `static/css/meridian/activity.css`, `static/js/meridian/activity.js` (comment), `static/img/meridian/observatory/sun-engraving-2026-09-19.png`, `artifacts/observatory-sun-2026-09-19/**` | 2026-09-19 | **released** at `052ab3e` (adopted and committed by DeepSeek; the adoption row was removed on release and the evidence is in the log entry of that date). Scope as declared: owner-approved visual pass. Additional scope: `artifacts/visual-pass-2026-09-19/**`, `docs/project/VISUAL_CORRECTIONS_2026-09-19.md`, `design-qa.md` (declared, unmodified), wordmark partial/shell CSS, Settings template, preview/capture scripts, `tests/meridian/test_settings_visual_preview.py`. Sun work preserved. No provider/live operation. |

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
| Builder (multi-page fidelity convergence) | `templates/meridian/index.html`, workspace partials and CSS for Today/Plan/Activity/Accounts, `static/css/meridian/{today,dial,observatory,shell}.css`, relevant workspace JS/tests, capture/comparison scripts and `artifacts/*fidelity-2026-09-16/**`, `design-qa.md`, status/coordination/task records | 2026-09-16 | **active**. Owner-approved correction after the same-scale comparisons showed structural and theme mismatches: converge Today, Plan, Activity, and Accounts on concepts 01–04 while preserving interactive evidence and every financial boundary. |
| Builder (Activity orange presentation) | `templates/meridian/partials/activity.html`, `static/css/meridian/activity.css`, `tests/meridian/test_activity_vignette.py`, `artifacts/observatory-activity-actions-2026-09-18/**` (untracked by convention), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-18 | **released** (commit in this slice). Owner-approved presentation-only slice: adopt `--obs-action: #e99a48`; orange selected tab with star and light-edition ink override; ticket-shaped confirm/correct controls with a continuous brass outline; full-bleed rules with end stars. Review fixed two real defects in this slice (chamfered-border severance, and orange text at 1.95:1 in the light edition). The unavailable review-count banner is explicitly excluded. No JS, route, data, financial, provider or authority change. |
| Builder (Activity follow-up: light green, row glyphs, review count) | `static/js/meridian/kit-icons.js`, `static/js/meridian/activity.js`, `static/css/meridian/activity.css`, `static/css/meridian/observatory.css`, `templates/meridian/partials/activity.html`, `meridian/api.py`, `scripts/preview_observatory_dial.py`, `tests/meridian/test_activity_glyph.py`, `tests/meridian/test_activity_review_count.py` (new), `tests/meridian/test_observatory_identity.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-18 | **active**. Owner review of the live preview: kit icons rendered as one question mark and never on the timeline; the retired `#202b40`/`#fffaf0` surface literals survived the OS-043 token fix as seven hard-coded rules; and the review count was authorised after being blocked. `meridian/api.py` gains a READ-ONLY `review_count` derived from the review queue the route already builds -- **no repository change, no new query, no classification, write, provider or authority change**. Delivered in this claim: the light edition's green action, the unconfirmable row's single primary with concept copy and ACTION_ICONS glyphs, and the retired surface literals. Still open: the timeline banner, day-part markers, row chevrons and the 'Ask Virgil about this activity' footer. |

| Builder (OS-056b: Crew's reported funding schedule + divergence test) | `meridian/migrations/025_crew_reported_funding_schedule.sql` (new), `docs/project/shipped-migrations.json`, `meridian/providers/base.py`, `meridian/providers/crewwork.py`, `meridian/repository.py`, `meridian/commitments.py`, `meridian/sync.py`, `meridian/live.py`, `meridian/services/dial.py`, `static/js/meridian/dial.js`, `tests/meridian/test_migrations.py`, `tests/meridian/test_bill_reserve_observations.py` (one exact migration-list assertion restated, declared rather than taken silently), `tests/meridian/test_crew_funding_schedule_ingestion.py` (new), `tests/meridian/services/test_dial_schedule.py`, `tests/meridian/test_dial_js.py`, `tests/browser/test_dial_reserved_amount.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at `ae11326`**. Handoff Decision 1B: migration 025 persists Crew's own reported funding fields (`estimatedNextFundingAmount` per bill and per reserve, `reservedBy`, `nextFundingDate`), the dial states Crew's figure when it exists (basis `crew_reported`) and the mirror otherwise (basis `crew_estimate`), and `fundingSchedule.divergence` reports any disagreement so a change in Crew's arithmetic becomes visible. Absence follows C01 in both mapping sites; the reserve-level estimate is stored but never used as a dividend. **No** provider mutation, live sync, deployment or `:8081` restart by an agent. INCIDENT: the preview already running when 025 shipped applied it to its own database on the next refresh, and its stale `BillReserveRecord` then 503'd the dial; only an owner restart clears it. See the log entry below and OS-057. |
| Builder (OS-053 handoff; two self-corrections; lint baseline re-measured) | `docs/project/HANDOFF_OS-053_2026-09-20.md` (new), `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Writes the OS-053 slice handoff (self-sufficient: verified line refs for both mapping sites, C01 absence framing, live-data evidence table, three unification options, test plan, traps, owner decisions owed). Confirms the duplication in source: sync.py:152 has no production caller while live.py:63-89 duplicates the loop in production, with create defaults `one_time` vs `monthly`, and names the decisive open question (does Crew report a frequency at all?). CORRECTS TWO OF MY OWN CLAIMS: `cadence` is a legacy unpopulated column (`recurrence` is live and reads monthly for every bill), and Rent's stored due_date 2026-09-16 CONFIRMS the owner's correction that it never moved to the 18th. Forbids "fixing" the January anchorDate values in this slice. Records OS-060 as CONDITIONALLY approved per the owner's exact words, and re-measures roadmap hazard 6 (17 errors, all in artifacts/tmp; meridian/scripts/tests clean). **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (why Jev: wakeful triage layer + its boundary) | `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Records the owner's rationale for Jev as a COST role (a cheap always-awake layer deciding whether the expensive intelligence needs to wake), not an authority role, with the boundary that keeps it safe: WHEN TO SPEND is not WHAT IS SAFE TO IGNORE; a layer that can decline to escalate is a SILENT-LOSS CHANNEL unless its decisions are logged, attributable and replayable; deterministic owner-set triggers (stipulation violation, bill exceeding its reserve, shortfall, failed verification) cannot be suppressed by it; OS-056 applied to routing (add friction only; "confidence >= .95 -> act" must never ship). Also writes down the alternative the owner left open: deterministic watchers for known/critical conditions, a cheap model for the unmodelled, the expensive intelligence woken when either says so — a LAYERED design direction, not a settled choice. ORSC-side JEV work stays ON HOLD. **Documentation only: no code, schema, provider, live or authority change.** |
| Builder (intelligence not prescription; keep the why) | `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at `7cf16a1`** — row added retroactively at the next commit, because the claim itself was recorded in `agent-claims.json` at `7cf16a1` but this coordination row was omitted; recorded here rather than silently skipped. Records the owner's constraint that outranks Track I's blueprint ("An intelligence is needed because it shouldnt be prescribed to a preordained set of variables, virgil decides what needs to be done based on my input and proposes action") with what it forbids and what authority it leaves untouched, the correction to OS-063's first-step framing (stipulation store = precondition, checker = tool), the proactive half, the inbox trust boundary (OS-064), and roadmap section 3.0's three rules for capturing vision that otherwise lives only in chats. **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (proactive half + inbox trust boundary; OS-064) | `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Records the proactive half as Track C V4 carrying the I.5 payload, with four added requirements: Meridian notices (observed deviation, not a request); solvency AND liquidity are both goals (a plan that rebuilds the reserve by starving spendable cash is the failure, not the fix); the plan names a recovery date; approval then execution with no part exempt. Records the second trigger class (inbound email/statement notice of a bill change) as OS-064, written trust-boundary-first and NOT authorised to build: read-only least privilege, no credential/token/body exposure anywhere, email content is EVIDENCE NEVER INSTRUCTIONS (injection boundary), verify the claim against the bill of record, suppression as a precondition, fail-closed. Names the real blocker: proactive.py exists but CONCEPT_COVERAGE.md records its lifecycle/dedupe as unverified, so V4 suppression precedes either trigger class. **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (CORRECTION: income timing != due date; the one-arc framing) | `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Corrects a false fact I recorded as binding: Rent's due date never moved from the 16th; what changed was the DIRECT DEPOSIT date (the owner switched direct deposit to Crew, which has no early direct deposit; his check used to arrive at Envelope Bank on Wednesday and moved via Cash App over two days), so the 18th is an INCOME-ARRIVAL date, not a due date. Two rules recorded: income arrival is modelled separately from obligation dates and funding-event timing follows income arrival; and NEVER assert causation -- state what was observed, not who caused it. This error is the rule's own proof. Also records the owner's one-arc framing (shortfall + Virgil's brief + proposals + automation are ONE thing), which puts FEATURE PARITY on the critical path (an adjustment Meridian cannot read is one it cannot propose) and makes Virgil the front door to OS-063. **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (owner's original ask → Track I.5 / OS-063; Rent date history) | `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit. CORRECTED the same day — see the newest claim row: the Rent-due-date change it describes (16th → 18th, "a Crew correction") NEVER HAPPENED; the deposit date moved, not the bill.** What stands: the original ask (Track I.5 / OS-063) with its three parts and prerequisites, the two date rules (income arrival is separate from obligation dates; never assert causation), and the payment-arrangement-as-bill-data finding. **Documentation and ledger only.** |
| Builder (owner's original ask → Track I.5 / OS-063 — superseded row kept for history) | `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Records the capability that motivated Meridian's AI features (roadmap Track I.5, ledger OS-063): unforeseen cost + goal as input, owner stipulations as standing constraints that bound the proposal space, proposals across budget/bill/autopilot as output. Recorded NOT authorised to start -- prerequisites named (I.1/I.2/I.3, Track C V2/V3, OS-059, the existing propose/approve/execute engine). Also records ~~that bill dates can move WITHOUT the owner (Rent 5th -> 16th -> 18th, the last a system correction he did not make)~~ **SUPERSEDED — the due date never moved from the 16th; the deposit date moved instead, so income arrival is a separate fact from an obligation date. See the CORRECTION row above** and that payment-arrangement bills are ordinary bills named as such (Verizon Payment Arrangement beside Verizon). **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (owner adjustments are data; stale due-date evidence) | `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Owner framing recorded as binding: permanent mechanics versus temporary owner adjustments; never encode a current arrangement as a rule, special case or guessed intent; let changed dates/amounts flow through with no stale-value assumption; never pin a temporary arrangement as the steady state. Corrects my own OS-061 clause that read as forbidding amount changes -- amounts are a first-class case (Verizon and Eversource are being adjusted in dates AND amounts now). Records the measured stale due_date/cadence evidence (Verizon 2026-01-22, Eversource 2026-01-30, both empty cadence, vs Crew's reservedBy 2026-09-22 / 2026-09-30) and raises OS-053 as likely the same root cause. **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (roadmap keystone correction; Rent arrangement; Virgil A0) | `docs/project/MERIDIAN_ROADMAP.md`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Four owner decisions plus one approved governing-doc correction. ROADMAP: the keystone "is currently drifting" claim was stale -- corrected in four places with test evidence (cadence.py clamps while preserving the anchor day; 80 tests pass), history kept struck through rather than deleted. RENT: the gap is resolved by payment, never re-targeted; the display must name where the shortfall comes from. LATENESS: explicitly NOT modelled ("meridian and crew dont need to know that"), retiring the deferred-obligation design. AI BILLS: propose-only chosen over a preapproved-automation class; OS-061 filed. VIRGIL-A0: approved, criterion 1 satisfied and toolchain already verified, criterion 2 (versioned contracts + adversarial tests) still open, signing still owner-gated. **Documentation and ledger only: no code, schema, provider, live or authority change.** |
| Builder (preview launcher, restart matrix, Tailscale verification) | `scripts/restart_preview.command` (new), `scripts/install_desktop_shortcut.command` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Desktop launcher so the owner owns the preview process (the agent-owned one dies with the agent shell, observed again today). Launcher stops only the 8081 LISTENER, starts detached, and verifies the port before claiming success; tested end to end. Restart matrix verified against run_preview.py (Python + ALTER-style migrations yes; templates/static/docs no). Phone access over Tailscale verified on loopback, LAN and the tailnet address. Standing instruction recorded: tell the owner when a restart is needed. Agent's direct write to ~/Desktop was correctly refused by the lane boundary, so the installer is versioned in the repo for the owner to run. **No application code changed; no provider mutation, live write or authority change.** |
| Builder (reserve is a one-way lock; funded != covered) | `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Two owner facts recorded as binding semantics: money cannot be transferred OUT of the reserve (so it is never a liquidity source for any action, proposal or projection), and a bill can exceed the reserve earmarked for it (pending Rent 1442.00 vs reserve 1097.10, a 344.90 gap from spendable cash) -- so "funded" must never stand in for "covered". Also records the pocket rule as the owner's liquidity guarantee and a policy knob set low while tight, and one numeric exposure observation carrying explicit uncertainty rather than a rule. Files **OS-060** (show the reserve-versus-amount gap) with five prohibitions. **Documentation only: no code, schema, provider, live or authority change.** |
| Builder (funding derivation, earmarking order, Crew Autopilot settings) | `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Owner-supplied funding derivation + earmarking order + Crew's Autopilot settings screen, recorded in D-015 with the payload-verified parts marked verified and the unreadable parts marked unreadable. Closes the model-level questions; keeps "which bill holds the reserve" open for OS-058 and files **OS-059** for the connector readback gap (autopilot settings, sweep threshold, pocket-transfer allocation). **Documentation only: no code, schema, provider, live or authority change.** |
| Builder (D-015 resolution: what the reserve-level figure means) | `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json`, `meridian/providers/base.py`, `meridian/providers/crewwork.py`, `meridian/repository.py`, `meridian/services/dial.py`, `meridian/sync.py`, `meridian/live.py` | 2026-09-20 | **released at this commit**. Owner clarification plus payload arithmetic resolved the third open question: the reserve-level `estimatedNextFundingAmount` is an ACCOUNT-TOTAL snapshot (reserve 1097.10 + subaccounts 345.28 = 1442.38, the owner's live total), not a reserve figure, and it lags the live total (it still read 1435.97, 6.41 behind). Recorded as RESOLVED in D-015 and in six source docstrings/ comments. **Comment-only code change: no behaviour, schema, provider, live or authority change**, and migration 025's own comment is deliberately left stale because a shipped migration is checksum-frozen. Dial already ignores the field. |
| Builder (OS-057: live verification of the whole slice) | `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Documentation of the real-data verification only; no code change. Restarted the preview at the owner's explicit instruction (the stuck pre-025 process was replaced), confirmed the refresh healthy with zero failures and zero 503s, then read a copy of the live database and closed OS-057: 025 applied, Crew's reported figures present for all five real bills and identical to the mirror (delta 0 cents on every row), the dial stating `basis="crew_reported"` with `divergence=null`, and the reserve row showing `next_funding_date=2026-10-02` with the reserve-level estimate stored but unused. Filed OS-058 for the 2026-10-02 measurement. **No** provider mutation, no transfer, no live-sync write, no deployment. The restart is agent-owned and can be swept; the durable home is the owner's terminal. |
| Builder (OS-056b follow-up: the schema/record alignment guard) | `tests/meridian/test_record_schema_alignment.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json`, `docs/project/MERIDIAN_OS_TASKS.json` | 2026-09-20 | **released at `7c568bf`**. Turns the measured OS-056b incident into a one-second mechanical guard: a record built as `**dict(row)` must declare exactly its table's migrated columns, proved load-bearing by a negative control (the mutation check reproduced the incident's own `estimated_next_funding_amount` mismatch). Tests and documentation only; no code, schema, provider, live or authority change. |
| Builder (OS-056: Today mirrors Crew's per-event funding math) | `meridian/funding.py`, `meridian/services/dial.py`, `static/js/meridian/dial.js`, `tests/meridian/test_funding.py`, `tests/meridian/services/test_dial_schedule.py` (new), `tests/meridian/test_dial_js.py`, `tests/meridian/services/test_dial_reserved_amount.py`, `tests/browser/test_dial_reserved_amount.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at `864130e`**. Bounded read-only slice implementing D-015: `crew_proration_cents` (Decimal ceiling, five-row oracle) + `cadence_interval_days` (exact weekly/biweekly only) in `funding.py`; an additive `fundingSchedule` on the bill's next occurrence in `dial.py`, built only from exactly one observed plan with a supported cadence and an anchor; three-length labelled copy in `dial.js`; the derived even-split branch REMOVED service-side and client-side. `fundingSource`'s pinned shape is untouched (the matched plan record is returned separately for its anchor date). **No** provider mutation, migration, live sync, deployment or `:8081` restart. `artifacts/observatory-dial-schedule-2026-09-20/**` and `artifacts/dial-schedule-review-2026-09-20/**` are capture evidence and remain untracked by the lane's convention. Ledger follow-up closing OS-055 by removal: `e6683a7`. |
| Builder (Plan: folded allocation map) | `templates/meridian/partials/plan.html`, `static/js/meridian/plan.js`, `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py` (new), `tests/browser/test_plan.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `91c09f9`. Track D Plan, first batch: the kit's folded-map allocation replaces the generic stacked bar and swatch legend and is installed below the tabs. Stations are composition, not amounts; every figure stays HTML; the mask-glyph defect and long-label wrapping both carry regression guards. **No** route, data, financial or authority change. Still open in Plan: row scale lines, the perforated income strip, the bottom CTA and the exact header/tab order. |

| Builder (Plan: next-income strip) | `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `507bd5b`. Track D Plan, batch 2: the funding card becomes concept 02's perforated parchment income strip by reusing the kit's `parchment-ticket.png` as a nine-slice with `fill`; ticket ink, decorative star ornaments, no dark hover lift. Copy unchanged. **No** route, data, financial or authority change. |

| Builder (Plan: primary action plate) | `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `8a17939`. Track D Plan, batch 3: the "New commitment" primary action carries the kit's `apricot-button.png` plate behind its real HTML label, with slice offsets measured from the asset rather than guessed. 44px target kept. **No** route, data, financial or authority change. |

| Builder (Activity: header vignette) | `templates/meridian/partials/activity.html`, `static/css/meridian/activity.css`, `tests/meridian/test_activity_vignette.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `16c769a`. Track D Activity, batch 1: the kit's `activity-telescope.png` becomes the concept's top-right vignette, and the header copy moves from hard right to the concept's left alignment. At mobile the art sits in flow rather than squeezing the heading, per the kit's own warning. **No** route, data, financial or authority change. |

| Builder (Activity: framed row glyphs) | `static/js/meridian/activity.js`, `static/js/meridian/kit-icons.js` (new), `static/css/meridian/activity.css`, `tests/meridian/test_activity_glyph.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `1c8d079`. Track D Activity, batch 2: review rows carry the concept's ringed category glyph, resolved by a DOM-free `kit-icons.js` whose two-pass scan preserves the kit's electricity-versus-Internet distinction. A Node round-trip caught both that bug and "Steam" resolving to nothing. **No** route, data, financial or authority change. |

| Builder (Accounts: parchment summary panel) | `templates/meridian/partials/accounts.html`, `static/css/meridian/accounts.css`, `tests/meridian/test_accounts_ticket.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `f368ba0`. Track D Accounts, batch 1: the cash figure moves onto the kit's parchment ticket, the asset the kit names for an account summary, with the Accounts decorative vignette beside it. The capture caught a parchment contrast failure (pale label at equal specificity) now fixed and pinned. **No** route, data, financial or authority change. |

| Builder (Accounts: account medallion) | `static/js/meridian/accounts.js`, `static/css/meridian/accounts.css`, `tests/meridian/test_accounts_medallion.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `4cdac31`. Track D Accounts, batch 2: each row carries the concept's medallion — the supplied brass ring above a code-owned tinted disk with the role icon on top, exactly the anatomy the kit specifies. The role glyph set is kept deliberately (the kit supplies no equivalent for three of five roles). **No** route, data, financial or authority change. |

| Builder (Accounts: connector rail) | `static/js/meridian/accounts.js`, `static/css/meridian/accounts.css`, `tests/meridian/test_accounts_rail.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-16 | **released** at `c73e428`. Track D Accounts, batch 3: the rows are threaded on the concept's dashed rail with a node per medallion in that row's tint, completing the constellation reading. The rail stops at the end medallions, skips rows with no medallion, and its 30px gutter was checked at mobile. **No** route, data, financial or authority change. |

| Builder (Accounts: closing strip + reconciliation) | `static/css/meridian/accounts.css`, `tests/meridian/test_accounts_assets_strip.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/MERIDIAN_ROADMAP.md`, `design-qa.md` | 2026-09-16 | **released** at `ba71bce`. Track D Accounts, batch 4: the tracked-items section closes the page as the concept's parchment strip, with no invented engraving because the kit scopes the telescope to Activity/Settings. Also reconciles the roadmap's stale visual-authority sentence and releases the lane's blanket claim. **No** route, data, financial or authority change. |

| Builder (capture theme fix + Activity ruled tabs) | `scripts/capture_meridian_matrix.py`, `static/css/meridian/activity.css`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md` | 2026-09-16 | **released** at `8d8db80`. Two fixes: the capture script pinned the theme so light captures are genuinely light (the "light" pass had been rendering dark for every workspace after the first, which invalidated part of this session's evidence and produced a wrong diagnosis of the application); and Activity's mode row became the concept's ruled-underline treatment, making green a test the other lane had left failing. **No** route, data, financial or authority change. |

| Builder (Today: lilac wavy title rule, OS-038 first item) | `static/img/meridian/observatory/title-rule.svg` (new), `static/img/meridian/observatory/ASSET_MANIFEST.md`, `static/css/meridian/workspaces.css`, `templates/meridian/partials/{today,activity,accounts}.html`, `tests/meridian/test_title_rule.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `design-qa.md` | 2026-09-17 | **released** at `525fae9`. Track D OS-038, first bounded item: the lilac wavy rule under the workspace title, measured from concepts 01/03/04 and deliberately **not** added to Plan, whose concept 02 shows none. Presentation only: **no** route, data, financial or authority change. The row also records the measured verdict on OS-035 (the instrument is already centred 29/29 in its row; the 233px below is the controls+ticket grid row). |

| Builder (Accounts: supplied archive-building asset, OS-039 close-out) | `tests/meridian/test_accounts_assets_strip.py`, `templates/meridian/partials/accounts.html`, `static/img/meridian/observatory/ASSET_MANIFEST.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md`, `artifacts/observatory-accounts-building-2026-09-18/**` | 2026-09-18 | **released at this commit**. Reconciles the owner-supplied `accounts-ticket-building.png` (committed by the parallel `builder-trackd` lane at `0b8a3ba`) and closes OS-039. That lane swapped the asset in `accounts.css` but left `test_accounts_assets_strip.py` asserting the *old* asset, so the suite was **red on `HEAD`**; this row fixes that guard while preserving its reuse-restraint intent, and corrects the stale comment and docs that still described `observatory-landscape.png` as the Accounts vignette. `accounts.css` and the asset itself are **not** touched — that lane's declared scope stands. **No** route, data, financial or authority change. |

| Builder (Today: OS-036 connector runs, and the reverted instrument centring) | `static/js/meridian/dial.js`, `static/css/meridian/dial.css`, `tests/meridian/test_dial_js.py`, `tests/browser/test_dial_fidelity.py`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md` | 2026-09-18 | **released at this commit**. Track D Today: reproduces and fixes OS-036 (connector runs drew for rows the scrollable rail does not show, leaving dashed lines cut off in mid-air) and reverts the `align-self: center` that `5c732f9` added to the instrument, which did not fix the owner's report and made the dial's position depend on the event-list length. Turns 3 of the 9 pre-existing `tests/browser` failures green. **No** route, data, financial, provider or authority change; presentation only. |

| Builder (Bottom dock: taller, with the concepts' ornate glyphs) | `static/img/meridian/observatory/nav/**` (new), `static/css/meridian/shell.css`, `static/css/meridian/observatory.css`, `tests/meridian/test_nav_dock.py` (new), `tests/meridian/test_observatory_identity.py`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md`, `artifacts/observatory-dock-2026-09-18/**` | 2026-09-18 | **released at this commit**. Owner-requested: the dock is taller and its icons more ornate, both measured against concept 01 rather than nudged (dock 65px/15.5% of width → 76px/18.1% against the concept's 17.8%; glyphs 20px → 34px against the concept's 8.4% of width). Stacks glyph over label, becomes the concept's rounded inset panel with hairline rules, moves the active marker under the label and removes the fill the concept does not draw. Four glyphs drawn in-repo; the kit's Bootstrap glyphs are superseded for the dock, **not deleted**, and the desktop rail is untouched. **No** route, data, financial, provider or authority change; presentation only. |

| Builder (Plan: the concept's bordered tab bar, OS-038 item 4) | `static/css/meridian/plan.css`, `tests/meridian/test_plan_map.py`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md`, `artifacts/observatory-plan-tabs-2026-09-18/**` | 2026-09-18 | **released at this commit**. OS-038 item 4, measured against concept 02: one brass-bordered rounded container, three equal cells divided by thin rules, the active cell parchment-filled with a brass star medallion at its left edge. Fixed two real layout defects found while verifying (cells were 148/119/119 because a zero flex basis is floored by the active cell's own medallion gutter; a `flex: 1` in the ≤600px block then re-imposed it at mobile widths). Scoped to `plan.css` — Activity keeps the ruled-underline treatment concept 03 shows. **No** route, data, financial, provider or authority change; presentation only. |

| Builder (Accounts: the tilted, notched, dotted summary ticket, OS-038 item 3) | `static/css/meridian/accounts.css`, `tests/meridian/test_accounts_ticket.py`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md`, `artifacts/observatory-accounts-ticket-2026-09-18/**` | 2026-09-18 | **released at this commit**. OS-038 item 3, closing Finding 4's "axis-aligned, square-cornered and plain". The tilt is measured from two features inside the concept ticket that agree (−3.7° / −3.21° → −3.2°); the dotted inset border uses `outline-offset` so it needs no third pseudo-element; the notches are pseudo-element circles that rotate with the panel. The kit's nine-slice, scallops and rivets are **preserved**, and a test asserts that. Notch is 36px against the concept's ~25px because the kit's edge already carries ~10px scallops — recorded, not silent. NOTE: this touches `tests/meridian/test_accounts_ticket.py`, which the parallel `builder-trackd` claim lists; that lane's work is committed and its tree is clean, and the edits are additive (one new test) rather than overwriting, so the overlap is disclosed rather than taken silently. **No** route, data, financial, provider or authority change; presentation only. |

| Builder (Today: the dial placed evenly in its band, OS-041) | `static/css/meridian/dial.css`, `tests/browser/test_dial_fidelity.py`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md`, `artifacts/observatory-dial-centring-2026-09-18/**` | 2026-09-18 | **released at this commit**. Owner: "I just want it evenly placed vertically", which also closes OS-035's composition question (placement, not size). Reverses `d0e0cd6`'s `align-self` revert, which was right that the old rule failed to fix the report and wrong about what was wanted: with `align-items: start` the dial sat 0px from the panel top with all 48px of slack beneath. Concept 01 agrees with the owner (~25px above / ~30px below). Now 24/24 inside the band. One browser guard DEMANDED the rejected arrangement ("must not vertically center the dial"); its mechanism is superseded and its reason (no drift with list length, now bounded by the rail cap) is preserved. **No** route, data, financial, provider or authority change; presentation only. |

| Builder (Today: the day arc starts clear of the building, OS-042) | `static/js/meridian/dial.js`, `tests/meridian/test_dial_js.py`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `design-qa.md`, `artifacts/observatory-dial-arc-2026-09-18/**` | 2026-09-18 | **released at this commit**. `ARC_START` −120 → −100 because day 0 sat at −120° and put the hand at (129,399), inside the kit's observatory. Measured the building by ray-casting the plate with an 8-sample run test (without it the first pass found phantom "building" on the right): it intrudes only between −140° and −110°, inward to r=150–182, against a hand running r=118–198. The r=198 tip now clears by 85 units on every day, full length throughout. The new guard READS the constant and fails below −105; proved to bite. Every day moved up to 20°, and drag clamps to the same range. **No** route, data, financial, provider or authority change. |

| Builder (OS-050 read half: Crew funding-plan ingestion + plan-first paycheck resolution) | `meridian/migrations/022_crew_funding_plans.sql` (new), `docs/project/shipped-migrations.json`, `meridian/providers/base.py`, `meridian/providers/crewwork.py`, `meridian/repository.py`, `meridian/sync.py`, `meridian/paycheck.py`, `meridian/api.py`, `tests/meridian/test_crew_funding_plans.py` (new), `tests/meridian/test_expected_income_rule.py`, `tests/meridian/providers/test_crewwork.py`, `tests/meridian/test_sync.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json` | 2026-09-19 | **active**. Owner directive: *"it SHOULD be a crew record though, the paycheck"*. The READ half of OS-050 only: persist the `billReserve.fundingPlans` the sync already fetches but discards, and resolve the expected paycheck to that Crew record first (name + id as identity, never merchant text). **No provider mutation, no deployment**: the Meridian→Crew cadence write and the symmetric delete stay deferred. Writes only Meridian's own SQLite, exactly like the existing account/transaction ingestion. |

| Builder (OS-051: governable paycheck-learning floor and nested reset) | `meridian/paycheck_learning.py`, `meridian/paycheck.py`, `meridian/payday.py`, `meridian/services/payday.py`, `meridian/api.py`, `templates/meridian/partials/payday-funding.html`, `static/js/meridian/payday.js`, `static/css/meridian/settings.css`, `tests/meridian/test_paycheck_learning.py`, `tests/meridian/test_expected_income_rule.py`, `tests/meridian/test_payday.py`, `tests/meridian/test_settings_payday.py`, `tests/meridian/services/test_payday_settings.py`, `tests/meridian/test_api.py`, `tests/browser/test_settings_payday_learning.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/agent-claims.json` | 2026-09-19 | **released at this commit**. Meridian-local derived-number governance only: the floor/reset changes which observations are learned from, deletes no financial record, mutates no provider, and is nested under Payday & Funding. The window is applied before the income channel is chosen, so a pre-floor deposit cannot select the aggregated history. Crew plan precedence and the configured figure are untouched. Browser write follows the documented `connections.js` plain-`fetch` precedent; `api.js` allowlists were not widened. **No** provider write, deployment or authority change. |

| Builder (OS-048b: the dial states a per-bill reserved amount with its basis) | `meridian/migrations/024_crew_bill_reserve_observations.sql` (new), `docs/project/shipped-migrations.json`, `meridian/providers/base.py`, `meridian/providers/crewwork.py`, `meridian/repository.py`, `meridian/commitments.py`, `meridian/sync.py`, `meridian/live.py`, `meridian/services/dial.py`, `static/js/meridian/dial.js`, `tests/meridian/test_migrations.py`, `tests/meridian/test_bill_reserve_observations.py` (new), `tests/meridian/services/test_dial_reserved_amount.py` (new), `tests/meridian/test_dial_js.py`, `tests/meridian/test_dial_income_meta.py`, `tests/browser/test_dial_reserved_amount.py` (new), `design-qa.md`, `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `artifacts/observatory-dial-reserved-2026-09-19/**` | 2026-09-19 | **released at `fec1c33`**. Owner ruling D-013, owner-chosen Option B. The audit found the handoff's premise incomplete: the reserve's set-aside total (Crew `billReserve.totalReservedAmount`) is observed by the connector but persisted nowhere, and `commitments.funded_amount` is `NOT NULL DEFAULT 0` (C01), so "Crew reported zero" and "never reported" are indistinguishable in storage. 024 persists both observed facts; the dial then applies observed → labelled derived split → unknown, carrying basis/divisor/attribution. Verifying it also found the production path (`meridian.live.sync_live_crew`) persisted neither funding plans nor reserve totals — they were written only by `sync_providers`, which OS-053 established has no production caller — so both writes were added there. `tests/meridian/test_dial_income_meta.py` is declared rather than taken silently: two of its source-presence assertions pinned the expression and the comment this slice replaced, and both were restated to the new contract while keeping their original intent (income rows render no funding status; a bill does not multiply one reserve across dates). **No provider mutation, no live sync, no guessed backfill, no deployment, no `:8081` restart.** |
| Builder (Crew funding math: the per-event formula and the `reservedBy` deadline, reverse-engineered) | `docs/project/CREW_FUNDING_MATH_2026-09-19.md` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json`, `docs/project/MERIDIAN_DECISIONS.md`, `docs/project/MERIDIAN_OS_TASKS.json` | 2026-09-20 | **released at this commit**. Documentation only, no code. One read-only connector snapshot (mode read-only, complete) against the live :8081 database proves `bill.estimatedNextFundingAmount = ceil(amount * interval_days / 30.4375)` on 5 of 5 bills, and shows the two fields Meridian discards: `reservedBy` (exactly each bill's next due date) and `nextFundingDate` (the plan's next event, 2026-10-02). Falsifies the even split, the proportional split and a nearest-due-first waterfall on real data, so OS-048b's derived branch and the divisor copy model something Crew does not do. Leaves totalReservedAmount, the earmarking rule and the reserve-level estimate explicitly OPEN with the 2026-10-02 event as the decisive free observation. **No provider mutation, no live sync, no schema or behaviour change, no deployment.** |
| Builder (OS-056 handoff for the next session) | `docs/project/HANDOFF_OS056_2026-09-20.md` (new), `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. Documentation only, no code. Writes the cold-start handoff for the next session to build OS-056: the proven Crew formula with its five-row test oracle, the two Crew fields Meridian discards (`reservedBy`, `nextFundingDate`), the falsified rules, four decisions to make before coding (compute vs ingest, horizon, next-occurrence-only unit, retirement of the `derived` branch), the expected file surface, hard non-goals, the three measurements pending at the 2026-10-02 event, and the environment traps that cost this session time (re-entry refusals, the connector CLI hanging when raced by the app's refresh, the preview being swept when the agent shell resets, and the fact that a running preview never reloads changed code). **No provider mutation, no code, no schema, no behaviour change.** |

| Builder (OS-053: unify the candidate-to-commitment mapping) | `meridian/commitments.py`, `meridian/sync.py`, `meridian/live.py`, `tests/meridian/test_commitment_candidate_mapping.py` (new), `tests/meridian/test_bill_reserve_observations.py`, `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. OS-053 closed as a **latent refactor**: one shared candidate-to-commitment mapping in `commitments.py`, both entry points rewired onto it, both duplicated loops deleted, and the two divergent recurrence fallbacks (`one_time` vs `monthly`) collapsed into one named constant `UNREPORTED_RECURRENCE_FALLBACK = "monthly"`. **Corrects the handoff's Option B:** `sync_providers` also does `upsert_reimbursement`, `reconcile()` and `_reclassify_relations()` — none of which `live.py` does — so it was rewired, **not** deleted, which would have destroyed capability. **No behaviour change** (owner-confirmed: Crew always reports a frequency; pre/post suite identical at 1421 passed / 1 skipped): no migration, no backfill, no schema change, no provider mutation, no live sync, no authority change, and **no `due_date` rewriting** — the January anchors are Crew's `anchorDate` (OS-038/OS-060). 18 new tests, falsified before trusted (repointing the fallback fails 3; re-duplicating the loop in `live.py` fails 7). Read-only check on a DB **copy**: 11 bills, 0 unreported, distinct recurrence `{'monthly'}`. |

| Builder (OS-060: read-only reserve-versus-amount exposure) | `meridian/services/today.py`, `templates/meridian/partials/today.html`, `static/js/meridian/today.js`, `static/css/meridian/observatory.css`, `tests/meridian/services/test_reserve_exposure.py` (new), `tests/meridian/test_today_exposure_js.py` (new), `docs/project/CURRENT_STATUS.md`, `docs/project/MERIDIAN_OS_TASKS.json`, `docs/project/AGENT_COORDINATION.md`, `docs/project/agent-claims.json` | 2026-09-20 | **released at this commit**. OS-060 shipped as a **read-only** display, per the owner's 2026-09-20 scope decision: a gap is shown ONLY where a bill's amount exceeds its **observed** reserved figure AND a reserved report exists. Only Rent qualifies today (1442.00 − 1097.10 = **344.90**); the four `0.00`-with-reported bills are normal funded-not-covered (D-015) and correctly show nothing. **Key finding:** Rent sits OUTSIDE the dial's event window (next occurrence 2026-10-16 vs horizon end 2026-10-04), so the exposure is window-independent — an event-loop field would have rendered nothing. Wording factual with no verb of action; "has to come from spendable cash" was rejected as bordering on implying a transfer. No other number moves (the gap was already inside known obligations). 21 new tests; suite 1460 passed / 1 skipped; falsified before trusted, which caught a defect in the author's own test (it passed for the wrong reason). **No provider mutation, no transfer, no reserve withdrawal, no authority change, no migration, no forecast, no lateness modelling, no re-targeting.** `meridian/**.py` change → preview restart needed. |
| Constitutional Builder (OS-089: Plan mobile concept alignment) | `static/js/meridian/plan.js`, `static/css/meridian/plan.css`, `templates/meridian/partials/plan.html`, `scripts/preview_observatory_dial.py` (synthetic fixture only), `tests/meridian/test_plan_row_disclosure.py`, `tests/meridian/test_plan_funding_label.py`, `tests/browser/test_plan.py`, `design-qa.md`, `docs/project/{MERIDIAN_OS_TASKS.json,MERIDIAN_DECISIONS.md,CURRENT_STATUS.md,AGENT_COORDINATION.md,agent-claims.json,PLAN_MOBILE_CONCEPT_ALIGNMENT_SPEC_2026-09-23.md,HANDOFF.md}` | 2026-09-23 | **released at this commit**. NOTE: the before/after captures live in the UNTRACKED scratch tree `artifacts/plan-mobile-concept-alignment-2026-09-23/`, per this repo's convention that nothing under `artifacts/` is committed; `design-qa.md` references them by path. Owner-directed 2026-09-23 slice per `docs/project/PLAN_MOBILE_CONCEPT_ALIGNMENT_SPEC_2026-09-23.md`: one-line bill rows, the facts/progress/evidence/NEXT move into the existing disclosure, the section becomes `Upcoming bills` with matching `aria-label`s, the `BILL` tag is removed, the add control stretches full width, and September coverage moves below the controls. **Presentation and copy only: no route, data, financial, authority, migration or provider change.** The medallion material is applied from the kit's existing brass ring (`medallion-frame.png`, already tracked and indexed), so no Runway generation occurs in this slice without a separately stated spend. |

## Log (append only — newest first)

### 2026-09-24 (twelfth pass) — OS-104 implemented: the Cadence card now reads the record that actually pays (`b`-side consolidation)

**The owner's model was already the app's model in one place, and the screen he reads used the other one.** He
said payday and funding "suggests overlap", that the payday and when it lands IS the cadence, and that per-bill
funding "doesn't need a separate setting or section". `meridian/api.py:515` has preferred Crew's paycheck record
since 2026-09-19 (*"per the owner's directive that the paycheck SHOULD be a crew record"*), but
`services/payday.py` built its `pattern` from `recognize_payday(transactions)` alone and the Cadence card rendered
from that — **which is why his screenshot could say "Not recognized" above a Crew cadence listed lower down.**

**Implemented, at the layer that decides.** `resolve_cadence()` answers in the backend's own order — Crew's
paycheck, then the observed pattern, then nothing — names its source, and reports when Crew holds several records
with differing schedules rather than letting one figure stand in for all. The payload carries `cadence` (the
resolved answer) *and* `pattern` (what Meridian has observed), because those are two different facts. The card
reads the resolved value and its source label; the per-row `Crew cadence:` line is gone.

**The duplication and the dead end both went.** The pane's own **two-mode** copy of the **four-mode**
per-commitment funding editor Plan already ships against the same repository and the same propose route is
removed — funding a bill is the bill's own business — and the hub row is renamed **Payday** ("The paycheck Crew
pays you from") while **Funding schedules** keeps its pointer to Plan. The instruction *"Add or confirm your payday
timing"* went with it: it asked for an action nothing in the product could perform (`/settings/payday` is GET-only,
its only POST sets the learning floor, and no payday write exists). Five phrasings of two facts — *"Not
recognized"*, *"Add or confirm your payday timing"*, *"Income unavailable"*, *"No run projected"*, *"not
reported"* — collapsed to one each.

**Verified** in the isolated preview at 420×912 DPR 3 in both themes in three payload states: the owner's own
screenshot state reads *"Not recognized — No paycheck record in Crew and no deposit pattern yet. Set the paycheck
in Crew, or let Meridian learn it from deposits."*; the Crew state reads *"Biweekly — Crew paycheck · State of NH
PR Payment"*; the learned state reads *"Biweekly — Learned from your deposits · 92% confidence · 12 deposits"*.
The removed controls are absent in every state, `docOverflow` 0, no console errors. 16 new tests in
`tests/meridian/test_payday_cadence_resolution.py`; the old `test_settings_payday.py` guard was **rewritten rather
than deleted** (its old assertion pinned the removed editor) so it now holds something stronger: the write goes
through the pipeline with explicit `owner_direct` provenance, reports whether the router executed it or parked it
for approval, is read back from Crew, and is never retried — plus the anti-duplication rule that keeps a second
per-bill editor out of this pane.

**Not changed:** which mechanism funds anything, any route, action, repository, migration, provider call or
authority boundary. The one write that remains (the Crew paycheck amount) is untouched and still verified by
readback. **Still owed:** the owner's decision on whether Meridian should also write FREQUENCY / DAY /
IDENTIFICATION — Crew's other paycheck sections, which his screenshot shows and Meridian neither reads in full nor
writes at all. That would be a new capability, so it is not implemented.

### 2026-09-24 (eleventh pass) — The fourth Accounts trait: the concept's three emblems, derived where they exist and drawn where they do not (`OS-103` closed)

**The trait that was not guessed at is now built, on the owner's pick.** *"More diverse icons"* changed a glyph
system, so it went to him as a choice; he chose **the concept's three emblems** — which is also the acceptance the
delivered medallion handoff demands, since that artwork may be used only *"where that visual mapping is
deliberately accepted"*.

**Derived, not invented, where the art exists.** The two masters are 1254×1254 with the disc filling only ~80% of
the canvas, so fitting the canvas into the disc box would have painted a 42px medallion. The new
`scripts/build_account_medallions.py --write` crops each to its visible disc and resamples to 208×208 = 4× the
concept's measured 52 CSS disc: **2,026,463 → 91,025 bytes** (compass, sha256 `547e3382…`) and **2,068,417 →
92,817** (Wi-Fi, `589f7e5b…`), transparent corners, both recorded in `ASSET_MANIFEST.md` with the command — the
repo's normal asset process, which is a recorded derivation rather than a hand-resized file. **Drawn where it does
not:** the delivered package explicitly excludes the emergency-fund star, so `accounts/star-medallion.svg` is
authored in-repo to the two masters' own measured construction (an angle-averaged radial profile puts the brass
rim at 0.89–1.00 R, the colour band at 0.73–0.89, the brass inner ring at 0.70–0.73, the field inside 0.70), with
the concept's coral for that bucket. It is vector against their raster — flatter at 208px, indistinguishable at
the 52px display size — and a matching raster star master is the recorded follow-up rather than a hidden gap.

**Measured in the running page, not from the source.** At 420×912 and 390×844, DPR 3, both themes, driving the
real `/api/meridian/accounts` render path with the concept's own names: `Free to Spend` → compass (lilac),
`Bill Reserve` → Wi-Fi (mint), `Emergency Fund` → star (apricot), each **52×52 with no tint border, no kit frame
and no glyph** — the art is a complete medallion and the handoff forbids stacking it over the frame. The disc went
46 → **52px** (the concept measures 103 device px of 853-wide art at the governed viewport) and the mobile row
track 44 → 52px so it cannot overhang the column gap. **`Emergency plumbing fund` → no emblem, and `Checking` →
its role medallion**: the key is the account's name matched against concept 04's three names *exactly*, so a
lookalike keeps its semantic medallion instead of wearing an emblem that would assert something untrue. The
connector's nodes and segment stops follow the emblems' tints, so the cord now carries the concept's colour
progression. `docOverflow` 0 at every width and theme, no console errors.

Five new guards in `tests/meridian/test_accounts_medallion.py` (assets real and referenced, the three-layer
construction dropped for emblems, the colour longhand that keeps emblem art alive in the light theme, the concept
sizing, the exact key with no fuzzy path, the label and `aria-hidden` retained, tints reaching the connector) and
a browser-level case in `tests/browser/test_accounts.py` that drives five names through the real payload path.
Two pre-existing guards were updated where the code legitimately moved — the tint assignment and the light theme's
disc declaration — each keeping its original intent and saying why. `OS-103` is **complete**; the traits that were
measured and deliberately not chased stay recorded in `design-qa.md`.

### 2026-09-24 (tenth pass) — OS-104: the app already agrees with the owner about payday; the screen he reads does not

**The owner's observation was checked line by line and every part of it holds.** He said payday and funding
"suggests overlap", that "payday is the funding mechanism, so the payday and when it lands is the cadence", that
"it still says no cadence detected in places", and that per-bill funding "doesn't need a separate setting or
section"; then sent Crew's own **Edit paycheck** screen (FREQUENCY `Every two weeks`, DAY `Every other Friday`,
Identification — *"Deposits matching these conditions will fund your Autopilot plan"*, DATE window, PAST MATCHING
ACTIVITY) with *"Crew has 5 sections. We have all the machinery for bidirectionality."*

**The record already agrees with him, and has since 2026-09-19.** `api.py:515-535` makes Crew's funding plan
outrank every other leg *"per the owner's directive that the paycheck SHOULD be a crew record"*, and
`providers/base.py:79-92` calls that record the owner's *"income source / Funding Cadence"*. The Settings pane
answers the same question differently: `services/payday.py:87` builds `pattern` from
`recognize_payday(transactions)` alone while Crew's plans ride in the same payload, and `payday.js:54-64`
renders the summary from `pattern` only — **so the Cadence card can read "Not recognized" on a page that lists a
Crew cadence further down, which is exactly the screenshot he sent.** Three more defects came out of the same
pass: the card's own instruction *"Add or confirm your payday timing"* has no control behind it anywhere
(`/settings/payday` is GET-only, the only POST sets the learning floor, and a repository-wide search finds no
payday write — the screen asks for something the product cannot do); Settings carries a **two-mode** copy of the
**four-mode** per-commitment funding editor Plan already ships against the same repository and the same propose
route; and the hub names funding twice (`settings_hub.py:142` and `:171`).

**His "all the machinery" claim is verified, and its extent is now on record:** `crew_write_actions.py:674-684`
already registers `create` / `update` / `delete_crew_paycheck_funding_plan`, each with a readback verifier. What
is NOT covered is the rest of the paycheck his screenshot shows — FREQUENCY, DAY, IDENTIFICATION, the DATE
window — which Meridian reads only in part and writes not at all.

Findings and the proposed correction are in `docs/project/PAYDAY_FUNDING_FINDINGS_2026-09-24.md`; the ledger
entry is `OS-104` (status `ready`, `owner_decided` true for the consolidation, because removing the duplicate
section is his own instruction). **The one decision the correction cannot make for itself is where FREQUENCY,
DAY and IDENTIFICATION are edited** — Crew owns them and Meridian only reads (no new authority, shippable now),
or Meridian grows write commands for them (a NEW capability: same pattern as the funding-plan actions, but the
authority boundary moves and it needs its own bounded slice). Nothing was implemented.

### 2026-09-24 (ninth pass) — OS-102: the owner said there was no concept for the Plan panes; the record says half of one exists

**The verification the ledger demanded came back against the premise, and that is the whole value of doing it
first.** The owner: *"the rules and crew tab of the plan page have almost no styling. I do not believe there is a
previous concept, so it is one you will have to design."* Checked all nine `design/*/` directories, their READMEs
and handoffs, and the asset manifests: **no DRAWN concept exists** for either pane (02-plan.png draws the Plan
tab; the 09-18 extension's `concepts/` holds only review, settings, timeline and virgil; nothing else mentions
them). But **a governing PROSE specification does exist and is binding** — `BUILD_SPEC.md` §8 states both panes'
requirements verbatim (Rules: grouped rules with readable trigger → condition → effect, schedule and paused
state, edit prefilled; Crew: controls organized by purpose — bills, pockets, cards — not raw GraphQL names, and
"no 'deferred' item next to a working duplicate control"), and `AGENTS.md` assigns everything the 09-18 set does
not cover to the 09-08 set, naming `plan` explicitly. So the content requirements and the honesty rules are
already governed; the job is **composition and styling against a binding checklist**, not invention — a smaller
and safer task than the instruction implied.

**Measured, not read.** Rules pane: `renderRules()` renders a name, a `Paused` badge and a `Delete` button —
no trigger, condition, effect, schedule or edit. Two defects in the empty case: `[data-rules-empty]` is a CHILD
of `[data-rules-list]` and `renderRules` calls `list.replaceChildren()`, so with zero rules the note is made
visible and detached in the same pass — **observed**: `noteInDom: false`, pane height **0px**, i.e. a blank pane
that cannot be told apart from a broken one; and (reasoned from source, explicitly NOT observed) a second pass
would evaluate `empty.hidden` on `null`. Crew pane: `.m-plan-parity` and `.m-parity-list` have **no styling in
any stylesheet**, and the 7 forms sit in one flat sequence (Create pocket, Create bill, Top up reserve, Manage
autopilot rule, Set active spend pocket, Delete pocket, Create virtual card), so §8's purpose grouping is not met.

**The Rules pane's central requirement is reachable with no backend change:** `meridian/services/plan.py:119`
already sends each rule's `formula` (the real Crew AutopilotRule payload — triggers, sixteen-supported action
types, optional conditions, often a description) and the renderer discards it.

Proposal written to `docs/project/PLAN_PANES_DESIGN_PROPOSAL_2026-09-24.md` and put to the owner, with the
ledger updating only its `evidence` — **status stays `ready`, `owner_decided` stays false, and no code was
written for either pane.** Edit-a-rule is proposed as an explicit NON-GOAL of the styling slice because it is a
new WRITE control and belongs in its own bounded slice with its own authority review.

### 2026-09-24 (eighth pass) — The Accounts aesthetic: three traits measured, the fourth asked about, and a gate that could not run at all (`OS-103`)

**The owner named four traits; three of them are differences between the app and a governing record, so they
were measured before anything moved.** Concept 04 was read with PIL (its ticket's painted face is **379.6 x
183.2** CSS at the governed 420-wide viewport) and the running page was measured in the isolated preview at
420/430/390, DPR 3, both themes. At `56390c9` the ticket's box was already the full 388px content column, so
"larger ticket" was entirely an interior problem: its painted face was **357.3 x 134.3** — 73% of the concept's
height — because the engraving was clamped to a 92px box. The engraving now takes `clamp(124px, 40%, 200px)`
(136px at 420) and the interior `12px 4px`, which lands the painted face at **356.7 x 179.7 (98.1%)** with the
figure at the concept's own scale (~186 CSS of ink for the owner's `$2,485.07` against the concept's ~182). The
card around the rows is gone in both themes, and the cord now carries one gradient per adjacent pair from each
row's tint to the next, confirmed from rendered pixels rather than from the source. **Two traps are now guarded:**
the cord's ink is an SVG *attribute*, and a CSS `stroke` declaration outranks a presentation attribute — so a
`stroke` left on `.m-account-connector` silently flattens every segment back to one colour; and a money figure has
no break opportunity, so a figure that does not fit **spills past the ticket's edge** rather than wrapping, which
is what the ledger did at 390px before the engraving became the element that yields.

**The fourth trait was NOT implemented, and that is the point of this entry.** "More diverse icons" changes a
glyph *system*: the concept draws three emblems for three purpose buckets, the payload keys a glyph on the
financial ROLE (`_role("pocket")` resolves to `other`), and the delivered
`design/investigator-medallions-2026-09-21/` artwork states its own boundary — "do not use artwork as an
account-type classifier", and place the Wi-Fi mark only where the mapping is deliberately accepted. Two forks,
different artwork, one needing the owner's acceptance: the owner picks. Recorded in `OS-103` and in
`session-emergent.json`. **Also recorded and deliberately not fixed:** the row separator's brass star sits at the
row's vertical centre while the dotted rule it is meant to tip is the row's `border-bottom`, so on a 125.5px
mobile row it floats ~30px above its rule; the owner named the *cord*, not the separator.

**A documented gate could not run at all, and it was not this slice's doing.** `docs/project/agent-claims.json`
had accumulated **five entries under the single agent id `constitutional-builder`**, and
`scripts/check_guardrails.py` validates *every* claim before it checks anything, so it died with
`CONFIG duplicate claim for agent 'constitutional-builder'` for **any** agent — the declared-scope step that
`HANDOFF_OS-053` documents as "run it and expect OK" was unpassable. The file's own lifecycle (one claim per
agent, updated in place with an incremented generation — `builder-trackd` is generation 2 under one claim_id)
says the five were superseded, so they were consolidated into one `constitutional-builder` claim at generation 6,
whose note names each superseded claim_id. **No declared scope was lost:** their file lists and verification notes
are in this table's rows and in the file's own git history, and every one of them was released with its commit.
The checker now reports `OK — 13 scope pattern(s)`.

Verified: full suite **1944 passed / 96 skipped / 1 failed** — the one failure is
`tests/test_generate_handoff.py::test_untracked_artifacts_do_not_make_the_handoff_claim_a_dirty_tree`, which
asserts the *committed* HANDOFF agrees with the working tree and therefore cannot pass while this slice is
uncommitted; it is green after the follow-up commit below. `ruff check app.py meridian/ scripts/ tests/` clean;
`check_guardrails.py --agent constitutional-builder` OK; `git diff --check` clean. Presentation only: no route,
data, financial, provider, migration or authority change.

### 2026-09-24 (seventh pass) — The pointer "missing" three times was 18px wide, and two derived estimates passed colliding geometry

**Two verification guards were asserting something other than what they claimed, and both fired only
once the slice was actually committed.** `test_session_close.py` derived its premise from
`git status --porcelain` but asserted the *script's exit code*, which also folds in `push state` and
the handoff basis — so a session that had committed its slice and simply not pushed yet **failed a
test named "an uncommitted tree is reported as unsafe" with a clean tree**. The same shape appeared in
`test_generate_handoff.py`: editing a tracked file after regenerating `HANDOFF.md` makes the handoff
under-report the tree, which is a *sequencing* consequence of committing, not a regression. **A guard
whose premise and assertion read different rows of the same table cannot distinguish the states it
names.** Both were retargeted to the row they name, and the session-close one was falsified in both
directions (dirty tree → FAIL + `NOT SAFE TO END` + paths listed; clean tree → `ok (clean)`) rather
than assumed.

**The owner's report was not a rendering mystery.** Three separate rounds went looking for a
clipping, stacking, lifecycle or bundle problem, because `OS-037` had already recorded "the pointer
moves correctly in the isolated preview, could not reproduce". A live DOM read settled it in one
call: `.obs-dial-pointer` present, `visibility: visible`, `opacity: 1`, `fill: #a5d4bf`, angle 10°,
tip at viewBox (345.5, 43.9) — everything correct except that `POINTER_INNER_UNITS = 96` and a
5.4-unit half-width painted an **18.1 x 6.4px** wedge at the governed 352.8px wrap. He was not
failing to find the pointer; there was almost nothing to find. **Measure the rendered size before
theorising about why something is invisible.**

**Two derived numbers were wrong, and the browser caught both; the estimates did not.** The
concept's pointer sits at 53% of its radius, so that is where the tip went — but the rim day numbers
are seated at a **measured 243.7 units**, so a 250-unit tip put the circle across the number ring and
the wedge under a date. Then a bounding-box overlap test "failed" on a 1.7px box corner while the
painted wedge cleared by ~3px, because the needle is a rotated path. Both were resolved by measuring
at the governed viewports, not by reasoning: the tip ends at 244, and the selected day draws no
number while every day is numbered.

**Sheet order beat a stale assertion's premise.** `BUILD_SPEC.md` §7 requires `Previous day` /
`Next day` / `Back to today`. The owner has since seen them and asked them back out; the newest
explicit record wins (D-004), and the tests were retargeted to the behaviour rather than the
widgets — the range control keeps the keyboard path and the removed "back to today" survives as `T`.
A latent trap went with them: `.obs-dial-controls .obs-control:last-child` would have silently
retargeted to `.obs-dial-range-wrap` once the buttons were gone.

**Two stale counts were found, only one of them mine.** The arc-end literal was replaced by the
relationship it protected. The paper-literal test asserted `8` while the tree actually held **11** —
it had drifted when `.m-observatory-virgil-snapshot` landed, so a passing total would have been a
coincidence; it is now a per-file allowance. And `CURRENT_STATUS` recorded that targeted tests "could
not run because the system Python has no pytest", which was a wrong premise hiding the Eversource
ticket from the gate: the repository's own `.venv311/bin/python` runs them.

**Earmarked, not started:** `OS-102` — the Plan page's **Rules and Crew tabs have almost no styling**
and, per the owner, no previous concept, so they are the first surface in this lane where a NEW
composition is authorised rather than derived. Design proposal and owner approval come before any
implementation; recorded in `session-emergent.json` as well so it cannot be lost to a compaction.

### 2026-09-24 (sixth pass) — The rail did not have to be a column, so the tradeoff was never geometric (`OS-100`)

**The lesson, and it cost two failed compositions to learn.** `OS-099` recorded a constraint as
geometric fact: *at 420px a side callout rail and an 82.5%-of-viewport dial cannot both hold*. The
owner's clarification plus his concept showed that was wrong — **the rail does not have to be a
column**. As an overlay it takes no layout width, the dial keeps the row, and each callout sits at
its own event's height, which is exactly what he meant by "follows the curved path". I had treated a
layout choice as a physical law, and the "impossible" tradeoff I surfaced was an artefact of my own
assumption. **Before reporting a tradeoff as inherent, check whether the constraint is in the medium
or only in the approach.**

**His clarification also corrects a misread that had already caused a revert.** "When I said no
overlap, I was highlighting that there still wasn't when I requested it previously" — the earlier
"no overlap to the left or under" was a complaint that the overlap was ABSENT, not an instruction
against it. Reading a terse correction as a specification, rather than asking which of two opposite
readings he meant, cost a revert and a round trip.

**Three defects in the first attempt were caught by looking at captures, not by tests:** callouts
drawn as opaque cards dropped on the artwork; a day number ghosting behind the scrim's transparent
tail; and a keep-in-view adjustment measuring rows before they were seated. **A composition change
needs a picture, not only a measurement** — the measurements were all correct while the thing looked
wrong.

**And the badge/date collision was measured rather than guessed:** same angle, so radii decide
contact; 28px of separation against ~34px needed. That is why the number had a badge sitting on it.

### 2026-09-24 (fifth pass) — I moved the callouts beneath the dial; the owner wanted them on the right (`OS-099`)

**The correction, stated plainly because the reasoning is the reusable part.** The owner asked for
"large dial with the left-and-under overlap". I implemented that as *callouts beneath the dial*, citing
`BUILD_SPEC.md §7`, which does prescribe an event list beneath the instrument **when labels cannot sit
beside it**. His screenshot showed a Today page containing only the compass, and his clarification was
"no overlap to the left or under" — the callouts belong on the **right**, scrollable. `51bebdd` is
reverted.

**The constraint that makes this a lesson rather than an accident: at 420px, a side callout rail and an
82.5%-of-viewport dial CANNOT both hold.** The enlargement was only achievable by taking the rail's
place. A governing spec clause that permits a fallback is not a mandate for it, and where two owner
requirements are geometrically exclusive, the tradeoff has to be surfaced BEFORE the change is built —
not discovered by the owner on his phone. `OS-099` records the constraint so the next attempt starts
there.

**His screenshot also settled the "double ticket" report from earlier in the session**, which I had
been unable to reproduce: the funding-schedule text runs through the perforation line between the two
ticket halves. A screenshot is a reproduction; `OS-093` now carries it. **When a visual defect cannot
be reproduced, asking for the capture is the work — not a substitute for it.**

**Two smaller corrections, both mine.** The day labels were uneven because my `OS-094` inset was per
label (a two-digit day pulled further in than a narrow one); they now share one radius sized by the
widest box, measured at a single value of 104. And the moon's block was in the ASSET, not the CSS: it
shipped opaque with no alpha channel on a flat `#101a28` field against a `#161c34` page.

**That last one needed a new keying capability, not a retuned threshold**, and the measurement is
worth keeping: a luminance key cannot separate a subject that CONTAINS its field's colour — the moon's
centre keyed to alpha 0 at floors 30, 40, 50 and 60, so the scene would have shipped as a crescent
outline. `scripts/key_raster_background.py` gained a colour-distance strategy; the default is
unchanged, and a test asserts the two strategies behave differently on the same input rather than
merely existing.

### 2026-09-24 (fourth pass) — The last two Today items were ONE defect (`OS-098`)

**"Safe-to-spend moved back outside the compass" and "moon in the upper-right" were not two
positions to nudge: they were one hidden container.** `.m-observatory-overview` carried
`m-visually-hidden`, the idiom that collapses a box to **1×1 clipped**. So the figure inside it
measured **0px wide** — populated with the real value and unreadable — and the moon overflowed that
clipped parent at the **left**. The dial's centre stated the figure instead, which meant the VISIBLE
copy was the duplicate and the canonical copy was invisible. Reading the markup once was worth more
than any amount of repositioning.

**The centre now says nothing about Safe-to-spend.** With no event selected it states the date and a
prompt. The figure belongs outside the compass; the centre belongs to the selected moment. That
deletes the duplicate rather than relocating it.

**Two guards were INVERTED, not deleted, and that is the point worth recording.** Both asserted the
old arrangement in as many words — `not [data-sts-figure].is_visible()` with the message "the
duplicate safe-to-spend block must not displace the dial", and the centre's
`kicker.textContent = "Safe to spend"`. When an owner reverses a requirement, the guard that encoded
it must be inverted with the new reason recorded, or the next session reads the old assertion as the
intent and reverts the fix. The non-zero-width assertion is deliberate: a 0px figure is exactly the
clipped state being fixed, so "visible" alone would not have caught it.

**Evidence is a captured state rather than a reconstruction:** the before images were produced by
reverting the two changed files, capturing, and restoring them.

**Attribution was re-proven for THESE files** (not borrowed from the earlier finding): reverting
`today.html` and `dial.js` gives byte-identical counts, 5 failed / 22 passed, so the shell and
activity failures remain pre-existing (`OS-097`).

**The owner's four Today items are now all delivered:** dial size (`OS-096`), dates inside the wheel
(`OS-094`), the moon's station and Safe-to-spend outside the compass (`OS-098`).

### 2026-09-24 (third pass) — The phone dial reaches the concept's size (`OS-096`), and a baseline that was wrong (`OS-097`)

**The dial was never too big to fit; it was capped by one declaration.** A later `max-width: 700px`
rule re-imposed a two-column panel with a hard 130px callout column, beating the single-column rule
declared above it because equal specificity is resolved by ORDER — the same failure mode OS-089
recorded. With the callouts moved beneath the dial (which `BUILD_SPEC.md §7` prescribes, and which is
what the owner meant by "left-and-under overlap"), the painted disc went from **55.1% to 82.7%** of a
420px viewport, against the concept's **82.5%**, with zero overflow in either state.

**Five guards encoded the old composition and were RETARGETED, not deleted.** This is the part worth
reading before touching dial geometry again: OS-035's dial-position guard became a direct invariance
(the dial's offset must not change between 12 events and 2); the hit-area guard became vertical
separation; the layout test's "larger than the callout column" comparison became the concept proportion
plus callouts-below, because **a comparison is not a requirement** (OS-049's own lesson); the
side-column 65% check became conditional so desktop keeps it; and the connector tests moved to desktop,
where runs can exist, with the phone case asserted as "no run may cross the instrument".

**My first attempt at the rail was wrong and is recorded as wrong.** I removed the rail's height cap to
give the labels room. That would have added ~700px of page on a long horizon, and the cap is what the
connector visibility rule and OS-036's fix are built on. The cap is restated (`min(340px, 40svh)`)
rather than removed, and the reason is in the CSS.

**`OS-097`: the browser suite is NOT green in this environment, and the previous status claim was
wrong.** Four failures in `test_meridian_shell.py` and one in `test_activity.py` were each checked by
reverting ONLY the file this session changed: **byte-identical counts with and without it**, so they
are pre-existing. Reverting the change is what proves attribution — a finding that merely exists at
HEAD does not, which is this repo's own attribution-trap rule. Separately, a single full-suite run
reported 49 failed / 46 errors across 14 files, including 24 errors in a file that passes 24/24 alone;
that shape is an environment/capacity artefact, and it is recorded so the number is not mistaken for a
baseline.

**Still open from the owner's four Today items:** the moon (upper-left, should be upper-right) and the
dial centre repeating the Safe-to-spend figure the header carries.

### 2026-09-24 (later) — The Today dial's labels, and a Plan regression this lane caused (`OS-094`, `OS-095`)

**Two commits, both verified before landing:** `0182e43` (fix/today — day labels anchored inside the
painted wheel) and `e882843` (fix/plan — the hub star centred, and a shortfall keeping its own glyph).

**`OS-095` is a regression I introduced and the owner caught, and the attribution was checked rather
than excused.** `git log -S` traces it to this lane's own `f5e7ef7` (OS-090): replacing an explicit
`/unfund/` test with a broad `/bill|commit/` fall-through made "Unfunded commitments" resolve to the
Bills station's rotunda. **The deeper lesson is about guard design, not regexes.** The mapping lived
inside `plan.js`, where the only possible guard was a text match on the source — and a text match
cannot express "these two DIFFERENT labels must not resolve to the SAME mark". The mapping now lives
in a DOM-free module and is exercised by calling it. That is the shape of guard that would have
caught this, and it is now in place for every label case including the service's older ones.

**A measurement corrected my own reasoning, and that is worth recording.** I had argued from the CSS
that the hub mark's geometry was symmetric. Measuring the DOM said otherwise: **0px of overflow above
the disc and 8.9px below**, because `place-items: center` cannot centre a grid item that overflows
its container — the implicit row grew to the mark and `align-content: start` pinned it to the top.
The reasoning was wrong; the measurement was right. Owner's framing was also the accurate diagnosis
before any code was read: *"the whole thing needs to move up in the circle."*

**The same discipline fixed the day labels.** They were anchored on a fixed radius, so each label's
own box decided whether it fitted; they hung 5-10px outside the painted wheel on mobile and looked
nearly right at desktop, which is exactly how a scale-dependent defect hides from a single-viewport
review. The acceptance target is now the plate's OWN painted circle read from its clip-path, not a
radius chosen by the implementer, and the negative control reproduces the defect's signature (three
mobile widths fail, desktop passes).

**Interim-state correctness is now a stated requirement in this lane.** Because Python changes need
a restart while static assets update on refresh, the app can serve OLD labels with a NEW mapping.
That state is user-visible — it is the state the owner photographed — so it is asserted by the
round-trip guard rather than treated as a transient. **The `:8081` preview still needs a restart**
before the Plan map reads Bills / Goals / Available.

**Still open from the owner's four Today items:** the dial's size (64.3% of the viewport against the
concept's 82.5%), blocked on relocating the 130px callout rail — the "left-and-under overlap" half;
the moon, currently upper-left rather than upper-right; and the dial centre repeating the
Safe-to-spend figure, which the header already carries.

### 2026-09-24 — OS-090 completed, and three owner-reported defects fixed (`OS-090`, `OS-091`, `OS-092`)

**This session's three commits, all verified before landing:**
`bf6844f` (fix/accounts — the Assets & Contracts strip no longer widens the column),
`ad57836` (fix/plan — the strip's stars clear its text, and the hub star fills its circle),
`f5e7ef7` (feat/plan — the map's second station is GOALS, OS-090).

**OS-090 is complete, not partially done.** Migration 029 carries Crew's nullable pocket `targetAmount`
through the provider, sync and repository; Plan derives Goals from goal-bearing pocket balances and
subtracts them once from the residual, so pocket cash cannot be double-counted; the unfunded figure keeps
reducing free cash even though it is no longer a station. The legacy direct-HTTP goal path in `app.py` was
left exactly as found. **The `:8081` preview needs a RESTART to show this** — `services/plan.py` is Python,
so the running process still serves "Unfunded commitments" and the rotunda until it is restarted.

**OS-091 (accounts overflow) and OS-092 (plan ornaments) were found by the owner, not by the gate, and both
are recorded rather than remembered.** OS-091's trigger was DATA: a pending memory proposal row whose
min-content is ~420px inside a 388px column. It produced **no document-level overflow** — on mobile `.m-main`
is itself a scroll container — so every existing guard passed while the page scrolled sideways and the
Execute control sat 44px off-screen. That is the lesson worth carrying: a document overflow check cannot see
overflow inside a scroll container. OS-092's two defects were likewise invisible to a source read, because
the values were reasonable in isolation and only their interaction with the border width and the disc size
made them wrong. All three now have measured browser guards proved load-bearing by negative control.

**Attribution was checked, not assumed.** `git log -S` puts the offending accounts rules at `4514a7a`
(2026-08-31) and `972a114` (2026-09-01) — pre-existing, and nothing in this session's diff had touched those
files. Reverting the stylesheets, not the agent's reasoning, is what proves a guard load-bearing.

**Still open from the owner's reports, and NOT fixed:** the Today evidence ticket's layout when a bill has
two tickets, and the "no evidence is attached to this event" line standing beside a "View bill" link that
navigates to Plan. Recorded as `OS-093` before being worked on.

### 2026-09-23 — The Plan bill row is one line, and the medallion material needed no spend (`OS-089`, `OS-087`, `D-023`)

**Second pass, same day, owner-directed from his iPhone Air.** He reported that the spacing did not work on
mobile, that the bills section was too small, and that the parchment should sit closer to the top so the bills
could be EXTENDED; he corrected the spec on the progress bar (*"Also I would still want progress bars"*) and
asked whether his phone was too small for the concept's layout. **It is not:** the iPhone Air is 420x912 CSS,
exactly the `mobile-air` capture viewport and exactly the concept's own scale (02-plan.png is 852x1846 at
0.494); the concept fits because its top block is ~148px against the app's ~250px. Changes, all mobile-only:
the funding bar moved back onto the COLLAPSED ROW as a 2px hairline with an end dot at the funded share (one
bar only, so the row and the panel cannot disagree); the `Plan` headline is removed with the subline carrying
the block centred (he pre-authorised it); the top gaps tightened to 6px; the income ticket 102px -> 68px; and
the bills band EXTENDED 120px -> `min(170px, 19svh)`. Measured after: map 191..449, band 473..643, ticket
673..741, add control 753..811 -- fully inside the canvas (68..826) -- row 69px. The `svh` term exists because
a real handset loses ~100px to the status bar and home-indicator inset that a desktop preview cannot show.
Governed desktop structural diff is now 0.34%, the extra being the funding bar's move one line up.

**Owner-directed, fully specified, and now closed on `feat/meridian-implementation`.** The governing record is
`docs/project/PLAN_MOBILE_CONCEPT_ALIGNMENT_SPEC_2026-09-23.md` and the binding decisions are D-023. The
collapsed bill row went from **113/114px** to **61/62px**: medallion, the name with its ONE date, the reserved
figure with `Reserved` beneath it, the evidence indicator where evidence exists, and the chevron. The fact
line, the progress bar, the invoice entries and the duplicated NEXT figure moved into the existing disclosure,
which takes the full row width on mobile. The banner and both `aria-label`s read `Upcoming bills`; the `BILL`
tag is gone for bills and kept for every other type, because this list can hold a goal. Order is bills → next
paycheck → add controls → September coverage, and `Add a bill or goal` spans the page.

**The finding that matters most is about spend, not pixels.** The owner authorised Runway credits for the
medallion material (*"If we need to match them with runway, we can spend that"*). Looking at the shipped kit
BEFORE opening the generation route showed `kit-2026-09-16/medallion-frame.png` is already a rendered bevelled
brass double ring with four rivets, and that the Plan map's stations and hub were the last surfaces still
composing their own flat ring from a 2px border and inset shadows. They now layer the real asset, so OS-087's
material gap closed with **zero credits**. What genuinely remains generative is the concept's engraved glyphs
against single-colour SVG masks — that is the half worth spending on, and D-021 still requires the spend to be
stated before it happens. Balance was 468 credits read read-only on 2026-09-22.

**Two defects were caught by the capture and by nothing else.** The income ticket's nine-slice was overridden
on `border-width` alone, so the layout reserved 10px while the image still drew 20px and the parchment painted
over its own title; and a bare `grid-area: name` on `m-plan-cell-commitment` — a class the desktop table's HEAD
cell also carries — created an implicit named line at the END of the head's grid, rendering `Commitment` in the
last column while every row stayed put. Both now have guards; the second is a browser guard on the RENDERED
header order, because the source read correctly in both cases.

**Third pass, same day.** *"Can we get everything a little closer together to allow three bills to show?"*
Measured: the row's height was set by the 44px disclosure toggle (kept -- it is the touch-target floor), not by
the medallion, so padding alone took it 69px -> 61/62px, the concept's own ~60px pitch. The map is SCALED to
89% rather than narrowed, because narrowing wrapped `Goals $200.00` onto two lines -- caught by the capture,
not by the numbers. All other reclaim is padding/margin only. At 420x912 the band is 200px and shows three
whole rows (193px needed of its 198px client box); the add control's bottom sits at 823px, inside the 826px
canvas. Guards added for the row pitch, the map's scale, the reclaimed paddings, and -- because CSS resolves
equal-specificity ties by order and the first attempt failed SILENTLY on exactly this -- that the third-pass
block is the LAST thing in the stylesheet.

**Verification.** Full suite **1907 passed / 83 skipped**; `ruff` clean over `app.py meridian/ scripts/ tests/`;
`git diff --check` clean; `session_close.py` exit 0; `tests/browser/test_plan.py` **8 passed** against
`APP_URL=http://127.0.0.1:8081`, including the one-screen acceptance test. Governed captures at 5 viewports ×
2 themes in `artifacts/plan-mobile-concept-alignment-2026-09-23/{before,after}`, taken against the isolated
synthetic preview, never the daily runtime. Desktop structural difference **0.24%**, entirely the map's brass
ring, the heading rename and the removed duplicate date. **No provider mutation, no transfer, no reserve
movement, no authority change, no migration, no forecast.** Left open deliberately: OS-088's tinted
per-category bill disc (still blocked on category data) and the engraved-glyph half of OS-087.

### 2026-09-21 — Safe to Spend ignored a negative reserve (`OS-078`, `D-019`, base `874b79c`)

**Owner-reported.** Free to Spend 424.90 displayed where the figure should be 100.00, reserve -324.90. Crew's own
Pockets screen shows SAFE TO SPEND 100.00 — so Crew subtracts the negative reserve and **Meridian** was the one
misreporting, by reading the raw pocket balance.

**The wrong assumption** (verbatim in `today.py`, inherited by `dial.py`): *"Crew has already separated bill/obligation
money into other pockets, so no further subtraction."* True at or above zero; false when negative, because a negative
reserve is an **overdraft** whose deficit has not been moved out of the spendable pocket yet. The error overstates
available money — the dangerous direction.

**Fix:** `meridian/services/reserves.py` holds one shared rule, and BOTH surfaces call it (they had already drifted into
two copies of `_spend_source_account`). Only negative reserves count; nothing is clamped; `None` is not a deficit; a
retired reserve no longer reduces the figure. The server also assembles `safe_to_spend.breakdown` so the figure can
explain itself — the affordance to display it is `OS-079`, with the data already shipped.

**Deliberate divergence:** Crew totals the pockets the owner SELECTED, so a positive reserve would INCREASE its Safe to
Spend; Meridian does not add a positive reserve, because earmarked bill money is not free to spend. Recorded so it is
not later mistaken for a bug.

**Bug I introduced, caught by the full suite:** the new local was first named `breakdown`, clobbering the commitments
breakdown of the same name in `build_today`; the top-level key returned safe-to-spend lines and
`test_breakdown_reports_bills_and_goals` failed with `KeyError: 'bills_total'`. Renamed `spend_breakdown`. A run of only
the new tests would have passed.

**UNCOMMITTED WIP LEFT IN THE TREE — `meridian/ai/investigation_service.py`.** The first bounded piece of `OS-076`
(validation for the Investigator's web route: question/context ceilings, strict boolean, 400 before any model call,
server-derived sources, owner-context-is-not-evidence). It is **written but UNWIRED and UNTESTED**, so it was NOT
committed — committing a service no route calls would be committing a placeholder. It is left as an untracked file for
the next session to finish or discard, and nothing in the app references it. `OS-076` remains **open**; Astra's
contract is at `design/investigator-medallions-2026-09-21/`.


### 2026-09-21 — A wrong CHECK was failing every live sync; the negative reserve is correct (`OS-075`, `D-017`, `1fb530f`)

**Defect.** `crew_bill_reserves.total_reserved_amount` carried
`CHECK (total_reserved_amount IS NULL OR total_reserved_amount >= 0)` from migration 024, on the
assumption that a reserve total is money set aside and cannot go below zero. On 2026-09-21 the owner's
live read raised `sqlite3.IntegrityError: CHECK constraint failed` on **every** sync, so no reserve row,
no funding plan and no bills were refreshed. The owner confirmed the value is correct — *"Negative reserve
is correct"*, because they deliberately left too much in Crew's "free to spend" and rent clearing took
the reserve below zero. **A reserve total is a running balance, not a quantity.**

**How it surfaced, because the route matters.** `tests/meridian/test_live.py::test_build_sync_once_is_a_callable`
went red. This lane's changes could not plausibly have caused it — and that was exactly the reasoning that
had **already been wrong twice this session**. So it was proven pre-existing by running that test in a
**clean worktree of HEAD** with none of this lane's work present (it failed there too), and then followed to
its source rather than filed as flaky. **A targeting run of `test_migrations.py` would never have found
it; only the whole-tree run did.**

**Fix.** `028_allow_negative_bill_reserve.sql` — a table rebuild, since SQLite cannot alter a CHECK in
place. Identical definition minus the clause, every row copied **verbatim** (ids included; nothing clamped,
rounded or repaired), index recreated. `NULL` keeps meaning "not reported" (C01) and stays distinguishable
from a real `0.0`. The value is stored **as reported** — clamping would present a fabricated figure as a
measured one.

**Decisive evidence is live:** `tests/meridian/test_live.py` **2 passed** — a real read against the owner's
Crew account, failing before and passing after. No financial figure is printed, logged or committed.

**Scope, deliberately narrow:** this removes the *only* non-negativity check sitting on a
**provider-reported balance**. Every other `>= 0` in the schema stays, because those are on values Meridian
or the owner **states**. `D-017` records the rule: **do not add a CHECK to a value Meridian only observes.**

**Not touched, on purpose:** `meridian/repository.py`. The upsert that raised is correct — it faithfully
tried to store a real value. The defect was the schema's assumption, so the schema is where it is fixed.
Migration 024 stays frozen.

### 2026-09-20 — OS-060 shipped read-only; the window trap that would have made it render nothing; and the vision captured

**Two owner decisions settled the slice, and one of them narrowed it.** OS-060 was conditionally approved (*"if its something you can do, and the visual display of it is easy to understand and informative, then absolutely"*). The owner chose: show a gap **only** where a bill's amount exceeds its observed reserved figure **and** a reserved report exists, worded factually with no verb of action.

**The data then decided the rest.** Only **one** live bill qualifies: **Rent — 1442.00 needed, 1097.10 set aside, 344.90 not yet covered**. The four other bills (Eversource, Verizon, Xfinity, Verizon Payment Arrangement) all read `funded_amount 0.00` **with the report flag SET** — which is **normal "funded is not covered" (D-015)**, not an exposure. The broader `reserved < amount` rule would have marked four of five bills "uncovered": arithmetic that is right and a display that would have **failed the owner's own legibility condition**. The qualifying rule is `0 < reserved < amount`.

**THE FINDING THAT CHANGED THE SHAPE OF THE SLICE: Rent is outside the dial's event window.** Rent's next occurrence is **2026-10-16**; Today's horizon ends **2026-10-04**. Adding a field inside the dial's event loop — the obvious place, beside `fundingStatus` and `reserved` — would have shipped a feature that **renders nothing on the live data**. Verified by computing `_next_occurrence` against the real stored values rather than assuming. The exposure is therefore **window-independent**: it is a statement about the bill's reserve *pool right now*, not about a dated occurrence. That is also why it needs no occurrence date and does not surface `due_date`.

**Implementation.** `_coverage_exposure()` in `meridian/services/today.py` — a pure function of the commitment list, so it is testable with no database — emits `reserve_exposure {count, items[]}` on the Today payload (name, amount, reserved, gap; ordered by gap descending). `renderReserveExposure()` in `today.js` renders one factual sentence and **stays hidden unless a gap was actually observed**, so a missing or unobserved reserve can never read as a shortfall.

**Wording, and a phrase deliberately NOT used.** Chosen: *"Rent: $1,442.00 needed · $1,097.10 set aside — $344.90 not yet covered"*. **Rejected:** *"has to come from spendable cash"* — the ledger asks the display to name where the shortfall comes from, but that phrasing borders on implying a transfer, and the reserve is a **one-way lock** that can never be tapped or topped up. Factual statement, no verb of action, no source named, no control, no link.

**No other number moves.** `known_obligations` already counts each bill's *unfunded remainder*, so the 344.90 was **already inside safe-to-spend**; the exposure names what was already counted and adds no second deduction. Pinned by test.

**Falsification caught a defect in MY OWN TEST, which is the part worth recording.** On the first attempt, removing the `reserved > 0` guard left the false-positive test **green**. Cause: that test created its bill **without** the `reserved_amount_reported` flag, so the bill was being excluded by the *other* guard — it was passing for the wrong reason and proving nothing about the rule it named. After fixing it to set `reported=True` (the live shape), removing the guard correctly fails **4** tests. Removing the reported gate fails **1**. Also recorded honestly: that gate is **defence in depth**, not load-bearing — `commitments._validate` normalises any positive `funded_amount` to `reported=True` and an unreported read stores `0.0`, so every repository-reachable state is already caught by `reserved > 0`.

**Verification.** 21 new tests; full non-browser suite **1460 passed / 1 skipped** (1439 + 21, zero regressions). Ruff clean; `git diff --check` clean; guardrails OK. Read-only re-read of a **copy** of `/tmp/gate-preview/gate.db` confirms exactly one qualifying bill.

**No migration, no backfill, no schema change, no provider mutation, no live sync, no authority change.** This is a `meridian/**.py` change, so the preview needs a restart to show it.

**OWNER DECISION CAPTURED — the OS-063 stipulation floor is a MOVING TARGET.** Owner's words: *"the stipulation floor is going to be a moving target until I catch up and get to a steady state budget."* Recorded in the OS-063 ledger row and in hot memory. It is a **time-varying** owner-set value, not an unknown-but-fixed number and **not $600**. So the store must be **append-with-validity** (a superseded floor is retained, so the system can state what the floor *was* at a past time), the checker must judge against the floor **in force at that time**, and the trend must **never** be extrapolated into an invented steady-state target. It also collides directly with OS-063's own proactive requirement to **name a recovery date** — recovery is defined against a destination, and the destination is moving, so that requirement must **fail closed** rather than invent one. The cadence half needed no owner input: income is `Veterans Home`, 1663.00, **biweekly**. Verified nothing in `meridian/` or `tests/` hardcodes a floor.

**OWNER DECISION #4 CLOSED — the unwritten vision is captured.** The recovered prior-conversation material is now **Mnemon Document `da793b36`**, *"Meridian vision recovery — the unwritten AI-replanning vision"*: the Sep 8 observe→verify philosophy, the Sep 10 "absurdly far reaching" progression (financial digital twin, agent council, constitutional autonomy, **intent compiler**, crisis mode, bounded autonomous CFO), Sep 15's Virgil as a native interface into the same persistent intelligence, Sep 19's cortex/reflexes/nervous-system event split, and the **verbatim** unexpected-expense exchange that names *Intent-to-Plan Reconfiguration*. **Provenance is marked [V] verbatim / [R] reconstructed / [O] operational corroboration and must not be flattened** — chat titles and full transcripts are not recoverable, and recovered ≠ accepted requirement. It confirms the arc the roadmap already gates (Track I.5 = OS-063; feature parity a prerequisite; Virgil the front door) and **authorises nothing**: every mutation still travels propose → approve → execute → readback.

### 2026-09-20 — OS-053 implemented: one mapping, one fallback, and the handoff's own recommendation corrected

**What the defect actually was.** The same provider read was mapped into commitments twice — `sync.py::sync_providers` and `live.py::sync_live_crew` — and the copies had diverged on exactly one visible thing: a bill reporting no frequency became `monthly` through production and `one_time` through the unused copy.

**I did not implement the handoff's recommended Option B, and this is the important part of the entry.** The handoff said "delete the duplicate; make `sync_providers` delegate or remove it". Read line by line, **`sync_providers` does three things `live.py` does not**: it persists `expected_inflows` via `upsert_reimbursement`, and it runs `reconcile()` and `_reclassify_relations()`. Deleting it, or "delegating" only the candidate loop away, would have **silently destroyed those three capabilities in production**. The function therefore **stays and is rewired**. A handoff recommendation is a hypothesis from a prior read, not an instruction to apply without reading — the same discipline that caught the `cadence`-vs-`recurrence` error the day before.

**Also corrected: "which default is nearly academic".** It is not. `plan._next_occurrence` rolls a recurrence forward only for `weekly/biweekly/monthly/semimonthly`; anything else — including `one_time` — returns the anchor **unchanged**. Crew's `anchorDate` is frequently **in the past** (four live bills anchor in January 2026), so `one_time` on a past anchor **drops the obligation out of the foreseeable future**, while `monthly` keeps it. **The expensive failure is erasing an obligation, not continuing one** — and Track I.5/OS-063 reasons over exactly that forecast. Chosen: `UNREPORTED_RECURRENCE_FALLBACK = "monthly"`, one named constant, both paths.

**Shipped.** Shared mapping in `meridian/commitments.py` (`CandidateObservation`, `observation_of_candidate`, `commitment_fields_from_candidate`, `commitment_update_fields`); both entry points rewired; duplicate loops deleted (sync.py −61, live.py −66). `commitment_update_fields` encodes C01 — an unreported field keeps the stored value, and the create fallback is deliberately **never** applied on update.

**Verification, and the falsification that makes it evidence.** 18 new tests; full non-browser suite **1439 passed / 1 skipped** (1421 baseline + 18, **zero regressions** — the refactor changed no routing). **Falsified before trusted, twice:** repointing the single fallback to `one_time` fails **3** tests; re-introducing the inline `or "monthly"` duplicate in `live.py` fails **7**. Ruff clean; `git diff --check` clean; guardrails OK. Read-only check on a **copy** of `/tmp/gate-preview/gate.db`: **11 bills, 0 without a stored recurrence, distinct values `{'monthly'}`** — nothing invented, no stored value changed.

**No migration, no backfill, no schema change, no provider mutation, no live sync, no authority change, no `:8081` restart needed by an agent** — but see the note to the owner: this is a `meridian/**.py` change, so the running preview is executing the pre-OS-053 code until it is restarted.

**Observed and deliberately not edited:** the absent-bill guard is phrased differently in the two files (`sync.py` `report.status == "complete"` vs `live.py` `snap.is_complete and not snap.errors`) but is **semantically equivalent** — `sync_provider` sets `status="complete"` only when `snapshot.is_complete` and its error counter is `0`. Left alone rather than churned.

### 2026-09-20 — The preview launcher could not run: a script that exists is not a script that runs

**The owner tried to install the Desktop preview launcher and Finder refused:** *"install_desktop_shortcut.command could not be executed because you do not have appropriate access privileges."* Cause, verified rather than guessed: the file was committed with mode **`100644`** — no executable bit — and sat on disk as `-rw-------`, so macOS will not execute it. `scripts/restart_preview.command` was fine (`100755` in git, `711` on disk).

**This is my defect, and it is precisely the failure the mission warns about.** I wrote the launcher, committed it, verified it *existed*, and told the owner to double-click it — **without ever verifying it could run.** "A script exists" was treated as "a script works", the same error class as claiming completion because a button or endpoint exists. The owner could not install the launcher at all, and both the suite and review missed it because **nothing asserted runnability**.

**Fixed in both places that matter.** `chmod 755` on both launchers, **and** `git update-index --chmod=+x` so the mode is correct **in the index** — because a fresh clone takes its modes from git, not from this working tree, so fixing only the filesystem would have left the bug in the repository.

**And pinned with a test that was falsified before it was trusted.** `tests/test_launcher_scripts.py` (4 tests) asserts every tracked `scripts/*.command` / `*.sh` is executable **in the working tree** (what Finder executes) **and in git** (what a clone materialises), and that each carries a shebang. Verification: reintroducing the bug with `chmod 644` makes the working-tree test **fail**; restoring it makes all four **pass**. A regression test never seen to fail proves nothing.

**Incident note:** an earlier diagnostic looped over every tracked file and **timed out at 300 s, resetting the persistent shell** — the second such reset in this lane. Keep those checks bounded (filter by pathspec and extension; never read every tracked file).

### 2026-09-20 — OS-053 handoff written, the duplication located in code, and two of my own prior claims corrected

The owner asked for a handoff so a fresh session can start OS-053. Written to `docs/project/HANDOFF_OS-053_2026-09-20.md` — self-sufficient, with `[E]` marks on what was verified and `[?]` on what was not — and the ledger row updated to point at it.

**The duplication is confirmed in the source, not just in the ledger.** `meridian/sync.py:152`'s `sync_providers` (plural) has **no production caller**; the production path is `meridian/live.py`, whose `sync_live_crew` calls `sync_provider` (**singular**) and then **re-implements the candidate loop itself** at `live.py:63-89`. The create branches already disagree: `recurrence=candidate.recurrence or "one_time"` in `sync.py` versus `or "monthly"` in `live.py`.

**The sharper framing, which reframes the fix.** That fallback converts *"Crew did not report a frequency"* into the **assertion** `"monthly"` — the absence-as-assertion error the project's own **C01 rule** forbids everywhere else — and the two copies make **different assertions about the same silence**. So the decision is not merely "pick a default": it is whether to keep fabricating at all, given that a fabricated recurrence feeds directly into the "foreseeable future" the owner's whole vision (Track I.5 / OS-063) reasons over.

**Two corrections to my own earlier claims, both caught while verifying for the handoff:**

1. **`cadence` is a legacy, unpopulated column — `recurrence` is the live field**, and it reads `monthly` for every bill. My earlier report of "empty cadence" for Verizon/Eversource implied no recurrence was recorded. **It did not mean that.** I drew a conclusion from the wrong column.
2. **Rent's stored `due_date` is `2026-09-16`**, which **confirms the owner's correction** that the due date never moved to the 18th — the 18th was an **income-arrival** date. So the data now supports the corrected rule rather than my original inference.

**And the January `due_date` values are not a bug to fix here.** Verizon `2026-01-22`, Eversource `2026-01-30`, Xfinity `2026-01-30`, Verizon Payment Arrangement `2026-01-16` are Crew's own `anchorDate` faithfully stored, while `reserved_by` carries the live deadline and the dial reads that. **The handoff explicitly forbids "fixing" them in this slice.**

**The decisive open question is now named** — *does Crew report a frequency at all for these bills?* — and is flagged as **unanswerable from the database**, precisely because the `or` default has already erased the difference between "Crew said monthly" and "Crew said nothing". It must be answered from the raw provider payload first.

Also: **OS-060 is recorded as CONDITIONALLY approved**, in the owner's words — *"if its something you can do, and the visual display of it is easy to understand and informative, then absolutely"* — so it ships only if plainly legible, and a design needing explanation or reading as a warning has failed the condition. And roadmap hazard 6's **stale lint baseline is corrected**: it claimed 11 errors, "five in `scripts/`"; re-measured, it is **17 errors, every one in scratch code** (`artifacts/**`, `tmp/**`), with `meridian/`, `scripts/` and `tests/` **clean** — which changes the conclusion from "clean up source first" to "exclude the scratch directories".

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

**FOLLOW-UP, same day — the owner answered the decisive question and it de-risks the slice.** Asked what Meridian should store when Crew reports no frequency, he replied: ***"There is always a frequency, so no need."*** So the `or` fallback is **dead code in practice** — no real bill reaches the create branch frequency-less — which changes OS-053 from a behaviour change into a **refactor**: **no migration, no backfill, no renegotiated semantics**, and existing `recurrence` values (Crew's own) are untouched. Two things still stand: the duplication should be unified anyway, because an undeclared assumption is precisely what hides inside "shouldn't happen" — keep **one** fallback and make it **observable**, since an unreported frequency in production would signal that the read *changed* (partial payload, new bill type, schema drift); and the **C01 principled form is explicitly out of scope** — storing "unreported" as unreported is a schema change for a case that does not occur, which is speculative infrastructure. It also **confirms** the January `due_date` values are unrelated to recurrence, leaving them squarely with OS-038/OS-060. Handoff §4/§5/§6/§11 and the ledger row were corrected to match.

**The owner explained the role he had in mind for Jev, and it reconciles something that previously looked like a contradiction.** *"Thats also why I thought Jev might be a good addition, a cheaper underlying layer than can determine if virgil is needed at all for a set of actions, and is cheaper to essentially be 'always awake and checking conditions' — although there might be better machinery."* That is a **cost** role, not an authority role: deep reasoning cannot run on every tick, so a cheap layer watches continuously and decides whether the expensive intelligence needs to wake. It fits the constitution's logic — and it is also exactly where a cheap layer can do harm, so the roadmap records the role **with** its boundary:

- **WHEN TO SPEND is not WHAT IS SAFE TO IGNORE.** Only the first power is cheap. A layer that can decline to escalate is a **silent-loss channel** — the same objection the owner raised against a model veto in memory admission — and it stays safe only if escalation decisions are **logged, attributable and replayable**, so "what did it pass over?" is always answerable.
- **Deterministic owner-set triggers cannot be suppressed by it.** A stipulation violation, a bill exceeding its reserve, a shortfall, a failed verification: these escalate **because a rule says so**. This is OS-056 applied to routing — the layer may only **add** friction, and "confidence >= .95 -> act" must never ship.
- **The alternative the owner left open is now written down.** For *known* conditions, **deterministic checks are the always-awake layer** — free, replayable, unsuppressible. For conditions **nobody wrote down**, which is exactly where "intelligence, not prescription" needs an intelligence, a cheap model is the only thing that can notice. So the likely shape is **layered**: deterministic watchers for the known and the critical, a cheap model for the unmodelled, and the expensive intelligence woken only when either says so. Recorded as a **design direction, not a settled choice**.
- **Status unchanged:** ORSC-side JEV work stays **on hold** (evaluation runs in the Harness lane). This records intent and boundary, not authorization.

Durable records added: insights `ceb04b06` (intelligence, not prescription), `955c432f` (the one-arc framing), `c3fa309f` (this Jev role and boundary), plus the earlier `6660fedc` (the original ask). No application code changed; no provider mutation; no authority change.

### 2026-09-20 — "Intelligence, not prescription", and a rule about not losing the why

**The owner's architectural constraint on Track I, recorded as outranking its blueprint.** *"An intelligence is needed because it shouldnt be prescribed to a preordained set of variables, virgil decides what needs to be done based on my input and proposes action."* Recorded at the head of Track I with what it forbids — a fixed enumeration of "things Meridian can adjust" that becomes the ceiling on what can be proposed; a lookup mapping a detected condition to a canned response; a design where a situation not in the table produces nothing — and with what it does **not** change: the intelligence **decides and proposes and never executes**, and the approval gate, provider verification, provenance, the OS-056 friction-only rule and the one-way reserve lock all still bind. Deterministic parts are explicitly kept as **tools and checks** (arithmetic, stipulation satisfaction, freshness, provenance, readback verification) that make output auditable rather than standing in for the decision. **This corrected my own framing of OS-063**, which had presented a deterministic stipulation checker as "the first safe step": the stipulation store is now recorded as a **precondition** and the checker as a **tool**, with the review test stated — *could it handle a situation nobody wrote down?*

**And the owner named the failure mode behind this whole session: the vision was never written down.** *"it has all been discussed, but in chats or with chatgpt etc, not necessary recorded in governing docs etc, it shouldnt be forgotten. The why is important."* Recorded as roadmap §3.0 with three rules: **capture at the moment of statement** (roadmap if it changes the trajectory, D-015 if binding, the ledger if it is work, plus a durable insight — the next compaction is the deadline, not a later cleanup); **record the why, not just the what**, quoting the owner where the wording carries intent, because a decision without its reason gets re-litigated or "fixed" backwards — the two errors in this lane today are the evidence; and **absence from the docs is not absence of a decision** — when the owner references prior context, treat it as authoritative and record it rather than re-deriving or guessing.

This is the mechanism by which a new session inherits the vision instead of reconstructing it: this session spent its first half deriving, piece by piece, what one recorded paragraph would have given outright.

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

### 2026-09-20 — The proactive half, and the inbox trust boundary

**The owner completed the vision: the same arc, pointed outward.** *"The later roadmap is where proactive comes in: 'I noticed you had to spend an extra 500 on ____, I propose to do these things to stay solvent without being cash starved in the meantime, and then return to steady state on this date, with your approval, I'll take care of all of it.'"* That is **Track C V4** (proactive help with a closed feedback loop, **no alert storms**) carrying the **Track I.5** payload, recorded in the roadmap with the four requirements it adds: **Meridian notices** (trigger is an observed deviation, not a request); **solvency and liquidity are both goals** — "without being cash starved in the meantime" makes the liquidity floor **integral**, so a plan that rebuilds the reserve by starving spendable cash is not a solution but the failure it was meant to prevent; **the plan names a recovery date**; and **approval then execution** — one approval authorises the whole plan, and no part of it is exempt from the gate.

**And then a second trigger class, which is the one with a trust boundary.** *"Or, I saw your bill increased by 40 dollars in your email, heres what needs to be adjusted with your approval — I approve, and all adjustments occur etc."* So triggers are **plural**, and one is **inbound notification** rather than an observed transaction. Filed as **OS-064** — recorded, **not authorised to build** — with the boundary written down first because a new data source is precisely where a credential rule gets violated: **read-only, least privilege**; **no token, cookie, OTP or message body ever logged, stored as evidence, put in a proposal, or handed to a model as instruction**; **email content is EVIDENCE, NEVER INSTRUCTIONS** (untrusted, possibly wrong, possibly hostile — it can never direct tool use or constitute authorization); **the claim is verified against the bill of record**, with Crew's readback as the authority and the email demoted to the reason the check happened; **suppression is a precondition**, since one message per bill per cycle is not an alert stream and re-reading must never re-propose; and **fail-closed** when the sender is unrecognised, the amount is unparseable, or the claim disagrees with Crew.

**One blocker named honestly:** `meridian/proactive.py` already exists and is wired, but `CONCEPT_COVERAGE.md` records its **lifecycle/dedupe as unverified** — so V4's suppression work is a **prerequisite** for either trigger class, not a detail to add later. The detection side stays under the OS-056 rule (a classifier may only add friction), and the proactive front door remains VIRGIL-A4, gated on C-V4 plus one proven I.2 role.

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

### 2026-09-20 — CORRECTION: I asserted a cause and was wrong; income timing is not a due date

**The owner corrected a fact I had written down as binding, and the mistake is worth recording in full because it is the rule's own proof.** I had recorded that Rent's due date moved `5th → 16th → 18th` and that Crew had made the second change. **Wrong.** The rent due date **never changed from the 16th**, in Meridian or in Crew. What actually changed was the **direct deposit date**: the owner switched direct deposit **to Crew**, which **does not offer early direct deposit** — previously his check arrived at **Envelope Bank on Wednesday** and he moved the money across with **Cash App over two days**. So **the 18th is an income-arrival date, not a due date.** Corrected in D-015 and `CURRENT_STATUS.md`, with OS-063 carrying the note as well.

Two durable rules come out of it. (1) **Income arrival is modelled separately from obligation dates**: a paycheck's landing day moves for reasons unrelated to any bill — deposit provider, early-deposit availability, multi-day transfer chains — and **funding-event timing follows income arrival, not the due date**. (2) **Never assert causation.** Meridian states **what it observed**, never **who caused it**. I broke that rule, wrote an inferred cause as fact, and it was false — which is exactly the failure the rule exists to prevent, now demonstrated rather than argued.

**And the owner's framing of the whole product as ONE arc, which changes ordering.** *"That's the whole point of shortfall, virgil's brief, proposals, automation. Its why almost full feature parity was so important. This was the whole point and vision all along."* Recorded in the roadmap at Track I.5 and in OS-063: **detect a shortfall honestly → analyse the foreseeable future → generate proposals across every adjustable setting while honouring stipulations → owner approves → execute → verify against the provider → automate only what was explicitly preapproved.** Two consequences recorded as ordering changes, not scope additions: **feature parity is a prerequisite** — an adjustment Meridian cannot *read* is one it cannot *propose*, which puts OS-059 on the critical path rather than beside it — and **Virgil is the front door to this arc**, in the owner's words: *"I should be able to ask virgil to analyze my financial situation and generate proposals to make all the in app adjustments I need to see me through, with any stipulations included."* So VIRGIL-A1/A3 are the interface to OS-063, and A3's negative test (speech or model output can never select direct mutation provenance) is the safety property the whole arc rests on.

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

### 2026-09-20 — The owner's original ask, recorded as Track I.5 / OS-063 — and how Rent's date actually moved

**The capability that motivated Meridian's AI features, in the owner's words:** *"I had to pay 500 dollars to repair my car, I can't cover this bill, look at the foreseeable future and make any budget/bill/autopilot adjustments necessary (proposals are then generated). I may add a stipulation like, I need at least 600 dollars free to spend each pay period, so meridian would make sure my pocket rule is for 600 dollars to free to spend."* Recorded in the roadmap as **Track I.5** — the statement of what Track I is *for* — and in the ledger as **OS-063** with its dependency chain spelled out, precisely so it is not attempted early. Three parts: an **unforeseen cost plus a goal** as input; **owner stipulations** as standing constraints that bound the proposal space (owner-set policy held in Meridian, since Crew has no equivalent — they are not a classifier and can never remove an approval, and an unsatisfiable stipulation must produce a refusal or a named shortfall rather than a silently weakened constraint); and **proposals** across budget, bill and autopilot settings as output — I.3's "one validated plan for the executor". **Recorded, not authorised to start**: it sits on V2/V3 planning above I.2 → I.3, and needs OS-059's readback gaps closed before the pocket rule can even be read. The first safe step when reached is not a planner but the stipulation store plus a read-only satisfaction checker.

**And the concrete history behind the Rent date, which produced two rules.** ~~Rent is normally due the **5th**; the owner changed it to the **16th**; then his **direct deposit switched to Crew**, which moved it to the **18th** — *"a correction I didn't make."* So a bill's date is **neither necessarily owner-set nor stable**: the system can revise it. Rule one: never assume a stored due date was the owner's choice, and never present a moved date as drift or an error to correct.~~ **CORRECTED the same day (see the newest entry above): the due date never moved from the 16th. What changed was the direct deposit date — switching direct deposit to Crew, which has no early direct deposit, moved the INCOME arrival, not the bill (his check used to arrive at Envelope Bank on Wednesday and move via Cash App over two days).** The surviving rules are: **income arrival is modelled separately from obligation dates, and funding-event timing follows income arrival, not the due date**; and **state what was observed, never who caused it** — the struck-through text above is the proof, since an inferred cause was written as fact and was false.

**And why a workaround is usually a new bill.** The owner's distinction — *"bills specifically that say payment arrangement, and normal bills"* — lives in the **bill data itself**: `Verizon Payment Arrangement` sits beside the plain `Verizon` as its own bill. So the workaround is typically a **coexisting new bill**, not an edit, which is exactly why the bill set's shape changes and reverts. Meridian must not infer a payment-arrangement type, and the earlier non-goal stands: never flag a one-time bill as an error. He restates the steady state too: once caught up it is **consistent month-to-month**, and today's manual changes are a running-behind accommodation.

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

### 2026-09-20 — A flaky security test, diagnosed instead of re-run until green

Running the non-browser suite for a docs-only slice, one test failed: `tests/crew/test_session_credentials.py::test_cipher_rejects_tampering_and_wrong_key`. It then passed 5/5 in isolation — the signature of a nondeterministic defect. **Diagnosed rather than dismissed, and the root cause was reproduced:** the test built its tampered value as `encrypted.ciphertext[:-1] + b"x"`, which *overwrites* the last byte instead of changing it. When the ciphertext already ends in `0x78` ('x'), the "tampered" bytes are **identical to the original**, decryption correctly succeeds, and the security assertion fails. A short reproduction found such a ciphertext on **attempt 14** and printed `old tamper is byte-identical to the original: True` / `decrypt(tampered) -> NO ERROR`, so the mechanism is demonstrated, not inferred. Frequency ≈ **1 run in 256**.

**Fixed** by flipping the final byte with XOR and adding an explicit `assert tampered_bytes != encrypted.ciphertext` guard, so the test can never silently become a no-op again. **Verified:** the same logic over **5000 fresh encryptions with zero failures to detect**, the test passing 8/8 consecutive runs, Ruff clean, and the full non-browser suite green at **1417 passed / 1 skipped**. Filed as OS-062 (`done`) with the evidence.

The habit this vindicates: "it failed but passes on re-run" is a finding, not an inconvenience — re-running until green was hiding a 0.4% false-alarm rate in a **security** assertion, and false alarms are how real alarms get ignored. (Distinct from OS-049, which is the separate, still-open pre-existing browser-suite baseline.)

### 2026-09-20 — "Owner adjustments are data, not law" — and the stale due-date evidence behind it

**The owner's framing correction, recorded as a binding principle.** *"Really think of it as owner made one time decisions and adjustments. Once I am not running behind, it will return to a normal state. Sometimes I just need that flexibility."* So D-015 now separates the two explicitly: the **mechanics are permanent** (reserve is one-way, pulls only from Checking, pockets claim the residual before the sweep, `funded` is not `covered`, per-bill funding mirrors Crew), while the **owner's values inside them are temporary state** (the low pocket allocation, the Rent shortfall, an adjusted date or amount, real-world lateness). Three obligations follow: never encode a current arrangement as a rule, a special case, or a guessed "intent"; let changed dates and amounts flow through with no code path, test or fixture that assumes the old value; and never pin a temporary arrangement as the steady state. The owner states the system already captures changes fluidly and applies the underlying logic — so the requirement is to keep it that way, not to add anything.

**A correction to my own work, caught by that framing.** OS-061 was written with a clause that read as *forbidding* clock amount changes ("not touch bill AMOUNTS as a side effect of a date correction"). The owner is adjusting **Verizon and Eversource dates *and* amounts** right now, so amounts are a first-class case, not an exception. The clause is rewritten: both are in scope as separate, explicitly-stated changes, and what stays forbidden is a change the owner did not ask for riding along with one he did.

**The stale due-date evidence, measured before he changes anything.** The 2026-09-20 snapshot shows exactly the problem he described:

| Bill | Meridian `amount` | Meridian `due_date` | Meridian `cadence` | Crew's own `reservedBy` |
|---|---|---|---|---|
| Verizon | `101.57` | `2026-01-22` (past) | *(empty)* | `2026-09-22` |
| Eversource | `210.00` | `2026-01-30` (past) | *(empty)* | `2026-09-30` |

So Meridian's locally-held `due_date` for these two is a stale **January** date with **no cadence recorded**, while Crew's own readback carries the live upcoming dates — which is the one-time-entry problem the owner described, visible in data rather than taken on trust. It also makes **OS-053** (the candidate-to-commitment mapping exists twice and disagrees) look like the same defect from a different angle, which raises it from tidy-up to likely root cause. These before-values are recorded so the capture can be *verified* after he makes his Crew-side changes rather than assumed.

**And the cause behind those one-time entries, which turns into a non-goal.** The owner explained why they exist: **Crew has no option for a bill with only one due date.** When a budget is exceeded and he negotiates a **payment arrangement** (his examples: Verizon `75.00` due the 22nd monthly, Eversource `210.00` due the 30th), he must either create a **new bill** for the negotiated amount on the new date, or **modify the existing bill one time** — and usually he also **redoes the original bill so the next month starts on the correct date.** His framing is itself the requirement: *"These arent things crew or meridian have to worry about, the underlying budget system still works the same, its me tinkering with it because budgets were exceeded and I needed to find a workaround."* That produced three records: an **explicit non-goal** added to the roadmap's §9 (no payment-arrangement, one-time-bill or workaround modelling — plus no lateness/deferral modelling, from the earlier decision); a **correction to OS-061**, whose first framing implied a defect to repair when these entries are deliberate workarounds, retitled to owner-requested bill *restructuring* (create / one-time-modify / restore) and forbidden from ever flagging a one-time entry as an error; and a note in D-015 that the bill set may change shape and revert, so nothing in ingestion, storage, display or tests may assume the previous bill set.

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

### 2026-09-20 — Roadmap keystone corrected, the Rent arrangement settled, and Virgil A0 approved

Four owner decisions and one approved correction, all landed together.

**1. The roadmap's keystone claim was stale, and is corrected (owner approved).** The roadmap called the dated-occurrence model the keystone and said it "is currently drifting `[T]`", with §5's first repair requiring the math be pulled into V1. That was right when written and has since been fixed: `meridian/cadence.py` clamps to the month's real length while **preserving the anchor day** (`Jan 31 → Feb 28 → Mar 31`, semimonthly = 15th + true month end), pinned at engine level by `tests/meridian/test_cadence.py`, with 80 tests passing across cadence, funding and payday. Corrected in four places: §5's repair #1 (struck through, kept as history), §6's keystone line, §6's consequence about defects reaching the rendered surface, §6's "Next move" (which had asked for work already delivered, and now starts one step later), and §7's hazard #4 (whose stale restart advice now points at the Desktop launcher and the real matrix). **Correcting the governing doc matters because the next session would otherwise have re-fixed a settled defect.**

**2. The Rent gap: resolved by payment, never by re-targeted funding.** September Rent (`1442.00`, due `2026-09-19`) is past due with `1097.10` set aside. The owner's arrangement: the gap **stays open and is resolved automatically when Rent is paid**, with the shortfall taken from spendable funds so Free to Spend falls by the gap. So no future funding is aimed at it, and "the reserve is short" is a fact to state rather than a condition to repair. OS-060 was updated accordingly, and the display must name *where* the shortfall comes from, not just its size.

**3. Real-world lateness is explicitly NOT modelled.** October Rent is funded normally — roughly half from the next paycheck, the rest from the following one, which is what Crew's own per-event proration already produces (`663.27` per biweekly event on a `1442.00` bill). In the owner's words: *"it is late in real life, meridian and crew don't need to know that."* This **retires the "deferred by owner" design** that was briefly considered: no deferred-obligation concept, no lateness flag, no owner-intent annotation for this case.

**4. AI-assisted bill maintenance is propose-only.** Some bills carry dates entered as one-time entries that should recur. The owner was offered propose-only versus designing a preapproved-automation class and chose **propose-only**: Meridian may draft the change and the owner approves each one. Reuses the existing propose → approve → execute engine; **no new authority and nothing automatic.** Filed as OS-061, with an explicit prohibition on any preapproved-automation class and a dependency note to settle OS-053 first.

**5. VIRGIL-A0 approved.** Owner: *"I approve AO."* Recorded in the gate itself, which was an empty stub: its **acceptance criterion 1** (owner accepts or amends the north star, addendum and threat-model reconciliation) is therefore **satisfied**, and its toolchain evidence was already verified on 2026-09-15 (macOS 26.4.1, Xcode 26.6, iPhoneOS/Simulator SDK 26.5, iPhone Air simulator smoke test). **Acceptance criterion 2 is NOT satisfied** — the versioned request/response/session/device-action/task/authentication/audit/error contracts and the adversarial tests are still to be authored, bounded to documentation and test harnesses only. **Signing remains owner-gated** (0 valid identities; Apple account, certificate, profile, App ID, device enrollment). And A1 does **not** unblock merely from A0: the addendum gates it on C-V1 trustworthy evidence **and** Track I.1's envelope/permissions.

Documentation and ledger only: no application code changed, no provider mutation, no authority change.

### 2026-09-20 — Preview launcher on the Desktop, the restart matrix, and verified phone access

The owner asked to be told whenever the preview needs a restart, and for a Desktop executable to call it. Both are now in place, with the parts that could be checked checked.

**The launcher.** `scripts/restart_preview.command` (repo, canonical) stops whatever listens on 8081, starts a fresh preview detached via `nohup` so closing the window does not stop it, and **verifies the port is listening before reporting success**. Tested end to end: it stopped the running PID 98854, started a new one, and reported correctly. `scripts/install_desktop_shortcut.command` writes a one-line Desktop shortcut pointing at it. **The lane boundary refused the agent's direct write to `~/Desktop` ("file_path resolves outside this lane") — correctly — so the installer is versioned in the repo and the owner runs it once.** Safety: it uses `lsof -ti tcp:8081 -sTCP:LISTEN`, so it can only ever kill the *listener* and never a client such as the owner's browser; it never contacts Crew and never moves money.

**The restart matrix, verified against `run_preview.py` rather than assumed.** A restart IS needed for Python changes (`meridian/**.py`, `app.py`, `run_preview.py`, since `use_reloader=False`) and for a migration that `ALTER`s a table whose record is built as `Model(**dict(row))` — which must be restarted *as part of shipping it*, because the running process applies the new `.sql` and then fails its reads (the 2026-09-20 dial 503). A restart is NOT needed for `templates/**` (`TEMPLATES_AUTO_RELOAD = True` and `jinja_env.auto_reload = True` are both set), for `static/**` (served from disk), or for docs. **Standing instruction recorded: state plainly, in the response, whenever a restart is needed.**

**Phone access over Tailscale, verified rather than assumed.** The app binds `0.0.0.0`, so the launcher preserves remote access: `lsof` shows `TCP *:8081 (LISTEN)`, and the same route answers `302` on loopback, on the LAN address `10.0.0.4`, and on the **tailnet address `100.118.158.2`**. Firewall is disabled. Caveats recorded: the Mac must be awake with the preview running, and `0.0.0.0` means the preview is reachable from the local network too, not only the tailnet.

**One observed fragility, confirmed empirically.** The preview was restarted by the launcher, and then a shell reset during a later command **swept it again** — `pgrep` found nothing and the port was free. That is precisely why the launch moved to the owner's Desktop: an agent-owned preview dies with the agent's shell, and a health check that only looks at the port would report it as merely "not running" rather than explaining why.

Documentation and two small scripts; no application code changed.

### 2026-09-20 — The reserve is a one-way lock, and "funded" is not "covered"

Two further owner facts, and they are the ones that change what the product may say. Plus one numeric observation that is deliberately *not* recorded as a rule.

**1. Money cannot be transferred out of the reserve.** It is one-way: bill allocations and the residual sweep move money in; nothing moves it out. So the reserve is **never a liquidity source** — not for an action, not for a proposal, not as an assumption inside a projection. Any Meridian action premised on withdrawing from the reserve is invalid by construction, and no proposal may be drafted on the idea that reserve funds can be redeployed.

**2. A bill can exceed the reserve earmarked for it.** The owner's pending Rent payment is `1442.00` against a reserve of `1097.10` — a **`344.90`** gap that must come from spendable cash at payment time. So **"funded" does not mean "covered"**, and Meridian currently shows the funded figure beside the bill amount *without* the gap, which understates real exposure: the screen says "funded" where the owner needs to know "covered". Surfacing the gap is legitimate read-only arithmetic over two observed values; **acting** on it is not — any reallocation goes through propose → approve → execute → readback, never as a side effect of a display. Filed as **OS-060** with five explicit prohibitions (no shortfall tone when EARLY FUNDING = 0 and the bill is merely not yet funded; no implication that the reserve can be tapped; no proposal or transfer triggered by the display; no forecast dressed as fact; no judgement of the owner's pocket allocation).

**Why the pocket rule exists, per the owner:** *"that's why I have the pocket rule — to ensure I have enough spendable cash, since money can't be transferred out of reserve."* It is their **liquidity guarantee** against a locked reserve, and they state its value is currently **low because they are tight** and will be **raised on a normal budget**. Meridian must treat it as a **variable policy choice it does not judge** — never a constant, never a target to optimise toward, never something to change automatically.

**An observation recorded with explicit uncertainty, NOT as a rule.** The whole account currently comes to `1442.38`, which is the Rent bill (`1442.00`) plus 38 cents; the spendable funds (`345.28` across the pockets and Checking) are the Rent gap (`344.90`) plus the same 38 cents. Those are one equation rearranged rather than two confirmations, so it is a single fact: **right now the pending Rent payment consumes essentially the entire account.** It is consistent with the owner describing themselves as very tight, and it may be coincidence or deliberate — hence the uncertainty. It is recorded because it is the sharpest available statement of current exposure, and because a display that hid the gap would hide exactly this. Meridian must not model it.

**Confirmed by the owner:** AUTOMATIC TOP-UPS = off and OPTIMIZE CASH FLOW = on — the two load-bearing toggles read from their screenshot were read correctly.

Documentation only: no code behaviour, schema, provider, live or authority change. D-015 carries the lock, the funded-versus-covered rule and the policy-knob status; the ledger gains OS-060.

### 2026-09-20 — The funding derivation, the earmarking order and Crew's Autopilot settings

The owner described how the reserve is actually funded and supplied Crew's own "Autopilot settings" screen. This closes the remaining two of the three open questions at the model level (the third — what the reserve-level figure means — was closed earlier the same day), and it changes what Meridian may say about its own screens.

**The derivation, in the owner's words and order.** Income lands in **Checking**; bills are allocated; then **pocket transfers** claim the residual; then whatever exceeds a threshold in Checking is swept into the reserve. The owner's sharpening is the load-bearing part: *if the pocket rule allocates the remaining funds to Free to Spend, those funds are no longer available to be pulled into the reserve from Checking.* The reserve is therefore the **last** claimant on a paycheck, not the first.

**What the payload independently confirms.** `billReserve.settings.funding.subaccount` = **Checking** (so "the reserve only pulls from checking" is stored, not just asserted), and a real rule named **"Sweep Excess Checking Funds"** — action `SWEEP_EXCESS`, condition matching the Checking subaccount, trigger `ACCOUNT_BALANCE_UPDATED`, not paused, not broken, prose *"removes funds over 1800 in the checking pocket"*. A second rule, **Round Ups**, exists but is `isBroken: true`.

**Crew's Autopilot settings (owner-supplied screenshot), and what each one forces.** SOURCE POCKET = Checking ("For bill adjustments and manual top-ups"); SURPLUS POCKET = Checking ("Leftover income will be sent here"); **EARLY FUNDING = 0 days** ("Ensure bills and pocket transfers are ready on their due dates"); **AUTOMATIC TOP-UPS = off** ("Keep your reserve on track by pulling from the source pocket, even if that pocket goes negative"); **OPTIMIZE CASH FLOW = on** ("Maintain a smaller reserve by funding strategically"). Three consequences that change how the product reads its own screens:

1. A bill at `0.00` reserved is **normal, not a shortfall** — with EARLY FUNDING at 0 the money is in Checking by design and Crew pulls it on the due date. The dial's "not yet set aside" wording is accurate as *state* and must not acquire a warning connotation.
2. The reserve **cannot drain Checking**, because AUTOMATIC TOP-UPS is off — which is the specific rule the owner meant by *"if that rule wasn't there, my whole paycheck would have gone into reserve"*.
3. The reserve is **deliberately smaller** than the bills' total need (OPTIMIZE CASH FLOW on), so it must never be measured against a sum of bill amounts as though a gap were a shortfall. This also explains why the reserve sits below the sum of the five per-event figures: designed behaviour, not an anomaly.

**Two things deliberately left open rather than guessed.** *Which bill is credited with holding the reserve, and by what rule* — the funding order is settled but the attribution is not, and the stored data already refutes the obvious guess (Rent holds the whole `1097.10` while its per-event need is `663.27`; the other four hold `0.00`; and the reserve is not an accumulation of bill allocations, since one event's allocations sum to `883.96`, so two events would exceed `1097.10`). Second, **two numbers Meridian cannot read at all**: the sweep **threshold** (the rule's condition object returns EMPTY, so "1800" exists only in prose and **$18.00 vs $1,800 is undetermined** — not to be picked) and the **pocket-transfer allocation** settings (pockets return balances only, `goal` is `null` on all four). Those become **OS-059**, a connector readback change in the established pattern, not a Meridian inference.

**Product consequence worth stating plainly:** Meridian models **no sweep** today, which remains the correct posture until those settings are readable. Any future projection that swept the checking remainder into the reserve *without* the pocket component would over-reserve materially — presenting money as set aside that is not, which is precisely what D-015 forbids.

Documentation only: no code behaviour, schema, provider, live or authority change. D-015 carries the full model, the settings table and the consequences.

### 2026-09-20 — RESOLVED: what Crew's reserve-level `estimatedNextFundingAmount` actually is

The owner supplied the key that closed one of the three open questions, and the provider's own payload confirmed it arithmetically. Recorded here because it changes how a stored field may be read, and because a future session must not re-open it as a mystery.

**The owner's clarification:** `1435.97` is their **total account balance**; `1097.10` is what actually sits in the **reserve**.

**The confirmation, to the cent, from the payload Meridian itself ingests:**

```
totalReservedAmount (the reserve)     1097.10
+ the four subaccount balances         345.28   (Checking -96.61, Free to Spend 441.89,
                                                 Emergency Fund 0, Fun Money/Splurge/Travel 0)
= the owner's live total              1442.38   -- exactly the figure the owner reported
```

**Two consequences, both of which constrain the code:**

1. **It is not a reserve figure at all.** Despite the name, the reserve-level `estimatedNextFundingAmount` is an *account-total* quantity — reserve **plus** spendable subaccounts. Reading it as an amount set aside would overstate the reserve by the entire spendable balance (339–345 today), which is precisely the error D-015 was written to prevent. It stays excluded from every arithmetic path: never a dividend, never presented as the reserve, and `totalReservedAmount` is never derived from it. Meridian's dial already ignores it, which this vindicates rather than changes.
2. **It is a lagged snapshot, not a live balance.** A fresh provider read on 2026-09-20 still returned `1435.97` while the account total had moved to `1442.38` — `6.41` behind — and the spendable portion it was computed against was `338.87` then versus `345.28` now. So the field records the account total as of when Crew last evaluated the reserve. It must never be presented as a current balance.

**Where this lives, and one deliberate exception.** The D-015 entry carries the RESOLVED note with the arithmetic, `CURRENT_STATUS` points at it, and the six source docstrings that called the field "unexplained" now state what it is (`providers/base.py`, `providers/crewwork.py`, `repository.py`, `services/dial.py`, `sync.py`, `live.py`). The one place it is *not* corrected is **migration 025's own comment**, which still calls the figure unexplained: a shipped migration is frozen by checksum and may never be edited (the 2026-09-11 immutability rule), so that stale comment is a known artifact rather than an oversight. The comment in `sync.py` and the docstrings above carry the correction.

**Ledger effect.** OS-058 is narrowed rather than closed: question 3 is answered, and what remains is (1) how `totalReservedAmount` is derived, (2) the earmarking rule, and now (3) when the account-total field refreshes and to what value — all still measured at the 2026-10-02 funding event, from data the refresh already stores every 15 seconds. No code behaviour changed in this entry: docstrings, decisions, status and ledger only.

### 2026-09-20 — LIVE VERIFIED: the whole slice against a real Crew read, and the incident closed

The owner restarted the preview and the slice is now confirmed on real data rather than fixtures. OS-057 is closed; OS-058 is filed for the remaining future measurement.

**The restart.** The stuck pre-025 process was replaced at the owner's explicit instruction. New process healthy: `provider=crew status=complete accounts=6 transactions=100 errors=0`, **zero** `unexpected keyword argument` failures, **zero** 503s in the new log. The dial outage is over. Durability caveat, stated because it is real: this process is a child of the agent shell and can be swept when that shell resets, so the durable home for the preview remains the owner's terminal.

**The measurement, read-only from a copy of the live database (never the live file).** All four of OS-057's checks passed:

- `schema_migrations` carries `025`, and the four columns exist.
- Crew's reported figures are populated for the **five real bills** and reproduce the reverse-engineered oracle exactly in cents: Rent 66327, Verizon Payment Arrangement 3459, Verizon 4672, Eversource 9660, Xfinity 4278, each with its stored `reservedBy`. The local-only commitments (`Journey Test Bill` x2, `Test`) store NULL -- the C01 absence rule holds on real data, so an unreported field is not written as a zero.
- **The divergence test passes on real data:** for every one of the five bills the mirror equals Crew's own reported figure with delta 0. Crew's arithmetic has not moved, so the mirror is verified against the provider's own statement rather than against itself.
- The dial payload on real stored data states `basis="crew_reported"` with `divergence=null` and Crew's own deadlines for all five bills. The reserve row carries `total_reserved_amount=1097.10` (observed, unchanged), `next_funding_date=2026-10-02` (the handoff's predicted event, now confirmed in storage), and the reserve-level `estimated_next_funding_amount=1435.97` stored but provably unused.

**One caveat recorded rather than glossed:** the payload render widened the horizon with a labelled **stub** paycheck so all five bills appear at once. The stored observations and the per-bill divergence comparison involve no stub. The owner's browser had not been reloaded when this was written, so the first 503-free dial request from their own session is still to be observed.

**What this changes about confidence.** Before today the mirrored proration rested on a reverse-engineered oracle from one snapshot, with the client tested against synthetic payloads. Now the same numbers have returned from the live provider through the real ingestion path, and the two independent statements agree to the cent. That is the strongest evidence available short of the funding event itself.

### 2026-09-20 — INCIDENT: shipping 025 under a running preview 503'd the dial (measured, then guarded)

The owner reported "my dial cant be loaded". It was not transient, and it was caused by the slice I had just committed — so it is recorded here as a defect I introduced, with the mechanism, the measured evidence and the guard that now prevents the class.

**What happened.** The preview on `:8081` (PID 28426, started 20:29:44) was running **pre-025 code**. `run_preview.py` uses `use_reloader=False`, so Python modules are fixed at start — but `FinancialRepository(...)` runs `run_migrations` on every 15-second refresh, and that constructor is reached by the refresh loop. So the running process picked up `025_crew_reported_funding_schedule.sql` off disk and applied it to `/tmp/gate-preview/gate.db` by itself (the same mechanism that applied 024 on 2026-09-19, which is why I should have anticipated this).

**Why that broke it.** 025 is an `ALTER` on `crew_bill_reserves`, and that table is read as `BillReserveRecord(**dict(row))`. The columns moved; the in-memory dataclass did not. Every reserve read then raised `TypeError: BillReserveRecord.__init__() got an unexpected keyword argument 'estimated_next_funding_amount'`, which killed the refresh tick (84 logged failures) and the dial's own read path. The measured symptom: `/api/meridian/dial` **503** while `/api/meridian/today`, `/accounts` and `/memory/today` still returned **200** — a dial-only outage, which is exactly why it reads as a front-end problem.

**Why it cannot self-heal.** The old class cannot learn the columns, and undoing an applied migration is not available (checksum frozen; history authoritative). The only repair is a **restart**, which is owner-gated; the owner chose to start it in their own terminal.

**Pre-flight, read-only on a copy of the live database** (never the live file) with the new code: `list_bill_reserves()` reads cleanly, `build_dial` succeeds with `freshness: fresh`, and the horizon's three bills carry their schedules with the proven values — Verizon `4672`, Eversource `9660`, Xfinity `4278` cents, `basis: "crew_estimate"`, `divergence: null`. So the restart does not merely clear the 503; it produces the expected payload on real data, and the first refresh after it populates the reported fields, flipping those rows to `basis: "crew_reported"` with the divergence check active.

**The guard, so this is caught in a test rather than by the owner.** New `tests/meridian/test_record_schema_alignment.py` pins the invariant mechanically: for each declared (table, record) pair whose record is built with `**dict(row)`, the table's migrated columns and the dataclass's fields must be *exactly* equal after `run_migrations`. It is proved load-bearing by a negative control — a deliberately stale class is reported, and the mutation check reproduced the incident's own mismatch (`columns the record does not declare = ['estimated_next_funding_amount', ...]`). Adding a column without extending its record now fails in ~0.1s instead of 503ing a live app. The pair map is deliberately partial and names the two tables this lane has altered; extending it is the documented prompt for the next such migration.

**The durable rule.** Shipping a migration that `ALTER`s a table whose record is built with `**dict(row)` breaks any already-running preview the moment that process applies it. Restart the preview as part of such a migration, or accept a 503 window. A migration that only creates a new table, or that adds a column to a table read column-by-column (`commitments` maps its fields explicitly), is safe by construction.

### 2026-09-20 — OS-056b: Crew's own reported funding fields are ingested, and the mirror is checked against them

Second commit of the OS-056 slice, taking the handoff's Decision 1B (*"compute first, ingest second"*) and closing the gap the first commit left: OS-056 made Today **mirror** Crew's published rule, which is Meridian applying Crew's arithmetic to data Meridian already stored — useful, but only ever Meridian's own statement.

**No connector change was needed, and that was verified rather than assumed.** `app.py`'s live `expenses` query already selects reserve-level `nextFundingDate`, `totalReservedAmount`, `estimatedNextFundingAmount`, and per bill `estimatedNextFundingAmount`, `reservedAmount`, `reservedBy`; `CrewWorkSnapshotAdapter` already walks that same `bill` dict (it reads `reservedAmount` from it today), and the adapter's own test fixture already carries `estimatedNextFundingAmount`. So this was an ingestion gap at Meridian's mapping boundary, not a provider gap — the cheapest kind of gap to close, and worth checking before writing anything.

**Migration 025** adds four NULLABLE columns: `commitments.estimated_next_funding_amount`, `commitments.reserved_by`, `crew_bill_reserves.estimated_next_funding_amount`, `crew_bill_reserves.next_funding_date`. Registered in all four places (the file, `shipped-migrations.json` with its sha256, `_LATER_MIGRATIONS`, and the exact applied-version list). **No backfill is attempted**, and that is a deliberate refusal rather than an omission: pre-025 storage cannot distinguish a reported zero from silence for these fields, so any backfilled value would manufacture provenance the provider never gave.

**Absence discipline is C01's, unchanged.** All four columns are nullable, so NULL means "this read did not report it" — never zero. Both mapping sites pass the stored value through when the candidate's field is `None`, `upsert_bill_reserve` uses the same `COALESCE`-keeps semantics it already used for the total, and tests pin both directions (a silent read never clears; a reported change does overwrite). `crewwork.py` uses the nullable cents conversion throughout, and the reserve-level pair comes from a **new** `readback_reserve_funding_schedule()` rather than a widened `readback_reserve_totals()` — the latter's shape is the contract the reserve write-verification path compares against, so widening it would have changed a verifier.

**The dial now states Crew's own figure when there is one** (`basis: "crew_reported"`, deadline from Crew's `reservedBy`, event from its reported `nextFundingDate`) and falls back to the mirror (`basis: "crew_estimate"`) otherwise. D-013's order of authority is preserved exactly — an observation outranks a derivation of it — and the client names the provenance in the copy (`· Crew's own estimate` vs `· Crew estimate`) while both readings stay labelled as estimates, never as money held.

**The divergence test is the point of the slice.** Both figures are computed whenever both exist, so a disagreement is reported as `fundingSchedule.divergence = {reportedMinor, computedMinor, deltaMinor}`. Before this, only one side of the comparison was stored, so the mirror could be wrong in the same direction forever and nothing would say so. A new test runs all five reverse-engineered oracle rows through the real ingestion path and asserts the mirror equals Crew's own reported number on every one, with no residual.

Verified: full non-browser suite **1413 passed, 1 skipped** (14 new tests in `tests/meridian/test_crew_funding_schedule_ingestion.py`); `tests/browser/test_dial_reserved_amount.py` **13 passed** across the contract's five viewports × both themes at the specified DPRs, with the measured row-geometry check still holding on the longer "Crew's own estimate" string; `node --check`; Ruff clean; `git diff --check` clean; `scripts/check_guardrails.py --agent deepseek-os056b` clean. Captures regenerated in `artifacts/observatory-dial-schedule-2026-09-20/` with review JPEGs in `artifacts/dial-schedule-review-2026-09-20/`. `tests/meridian/test_bill_reserve_observations.py` is declared rather than taken silently: one assertion pinned the exact applied-migration list, which now includes 025.

Explicitly not done and not claimed: **no provider mutation, no transfer, no Crew write, no live sync, no deployment, no `:8081` restart.** The preview on `:8081` (PID 28426) predates both OS-056 commits and a running preview loads code at process start, so **neither slice is live**; 025 will be applied by the next app start and the reported columns stay empty until a read runs under the new code. The reserve-level `$1,435.97` is now stored and still **unexplained** — it is never used as a dividend and `totalReservedAmount` is never derived from it. **OS-057** records the real-read verification and the 2026-10-02 measurement, neither of which an agent may trigger.

### 2026-09-20 — OS-056: Today states Crew's own per-event funding estimate (base `5a88cc6`)

`docs/project/HANDOFF_OS056_2026-09-20.md` front-loaded the evidence, so this session re-derived nothing: it took the handoff's Decision 1A (compute first, no migration) and Decision 4 (retire the `derived` branch), and left Decisions 2 (horizon) and 3 (unit) as written.

**The pure rule.** `meridian/funding.py` gains `crew_proration_cents(amount_cents, interval_days)` — `ceil(amount × interval ÷ 30.4375)` in `Decimal` with `ROUND_CEILING`, which reproduces Crew's own payload for all five oracle rows — and `cadence_interval_days`, which answers only for cadences Meridian expresses exactly (`weekly` 7, `biweekly` 14) and `None` otherwise. A cadence that cannot be expressed produces **no** schedule rather than a guessed interval, which is the same fail-closed choice the shared cadence rule already makes.

**The exposure.** `meridian/services/dial.py` emits an additive `fundingSchedule` on the bill's earliest occurrence in the horizon — `{eventDate, contribution, deadline, nextFundingDate, planName, basis: "crew_estimate", intervalDays}` — and only when the bill's reserve resolves to exactly one current plan whose cadence maps exactly and which carries an anchor. Later occurrences keep `null`: one reserve is still never multiplied across future due dates (D-010 as narrowed by D-013). The schedule is built from the matched plan record, which `_resolve_funding_source` now returns separately, so the `fundingSource` payload shape its own tests pin is byte-identical.

**Precedence is preserved rather than decorated.** `reserved`, `fundingStatus`, `fundingBasis` and the observed/unknown order of authority are unchanged, and the centre readout states the observed figure whenever there is one — a reported zero included. The browser test pins both directions: Internet (observed zero + schedule) shows the observed statement in the centre and the schedule in the row and ticket; Insurance (nothing observed) is the case where the centre does fall to the schedule.

**Copy in three lengths, because the capture said so.** OS-048b's lesson was that a long label at 420px wrapped into its own value, so the row gets `$29.89/event · Crew estimate`, the centre the same, and only the ticket the sentence naming the deadline and the plan. Every form says "estimate"; nothing reads as money held. Measured with a throwaway read-only probe at 1440/1024/430/390/420: the meta line wraps but its right edge lands exactly on the amount column's left edge (0px gap, no overlap) and stays well inside its own row (Internet 14.8px of a 120px row at 1440; 40.5px of 125.8px at 420), with zero horizontal overflow everywhere. A browser assertion now measures that geometry instead of assuming it.

**The retirement, in both halves.** D-015 §1 retired the even-split *model*; this removes it. `_reserve_figure` returns `observed` or `unknown` only, `_reserve_totals_by_reserve` and `_bill_counts_by_reserve` (its divisor machinery) are gone, `"observed"` is the only basis the client will state, and a legacy payload still carrying a `derived` figure renders as nothing on the row, the centre and the ticket. The "Meridian estimate, split across N bills" wording is gone from the product and a Node round-trip pins that it cannot come back. D-014 now records the retirement, so a future session does not re-propose it — and OS-055's fabrication risk is closed by removal rather than by choosing a divisor rule.

Verified: focused non-browser **136 passed** (funding oracle incl. the ceiling boundary, dial schedule, dial reserved amount, dial-JS Node round-trip); full non-browser suite **1399 passed, 1 skipped**; `tests/browser/test_dial_reserved_amount.py` **13 passed** — the contract's five viewports × both themes at the specified DPRs, zero horizontal overflow, zero console errors, plus the measured row-geometry check; `node --check static/js/meridian/dial.js`; Ruff clean; `git diff --check` clean; `scripts/check_guardrails.py --agent deepseek-os056` clean. Captures: `artifacts/observatory-dial-schedule-2026-09-20/` (10 PNGs) with 760px review JPEGs in `artifacts/dial-schedule-review-2026-09-20/`, both untracked by this lane's convention; the reasoning and the numbers are in `design-qa.md`.

Explicitly not done and not claimed: **no provider mutation, no transfer, no Crew write, no live sync, no migration, no deployment, no `:8081` restart.** The running preview loads code at process start, so nothing in this slice is live until the owner authorizes a restart. `funding_rules` still holds zero rows — this slice mirrors Crew's published rule directly rather than driving `project_funding`, which is the compute-first decision the handoff recommended. The three open questions (how `totalReservedAmount` is derived, the earmarking rule, and the reserve-level `$1,435.97`) are still unmeasured; the **2026-10-02** funding event remains the decisive free observation. The six pre-existing `tests/browser/test_dial_fidelity.py` failures (dial-wrap vs rail geometry; theme-toggle label width) are OS-049's baseline, reproduced identically and not attributable to this slice.

### 2026-09-20 — reverse-engineering Crew's funding arithmetic (documentation only, no code)

Owner asked me to discern the calculations Crew actually uses from the reserve amount and funding rules. One read-only connector snapshot (`crew-readonly snapshot`, `mode: read-only`, `complete: true`, `22:27:32Z`) against the live `:8081` database answered most of it, and the answer changes the design.

**Proven, exact on 5 of 5 bills:** `bill.estimatedNextFundingAmount = ceil(bill.amount × interval_days ÷ 30.4375)`, where `interval_days` is the funding plan's cadence in days (this plan is `frequency WEEKLY, frequencyInterval 2` = 14 days; `crewwork.py:46` already maps that to `biweekly`) and `30.4375 = 365.25/12`. The residual is positive on every bill, so it is a ceiling and not a round — rounding to nearest would miss Eversource and Rent. So Crew computes a **daily-rate proration of each monthly bill across the funding interval**; it funds every bill a little from every funding event, which is precisely the Simple/Beacon "fund it by its due date" mechanic the owner described, already running.

**What Meridian was discarding:** each bill carries **`reservedBy`** — literally the deadline the reservation is for, and observed to be exactly that bill's next due date (`2026-09-22`, `2026-09-30`, `2026-10-16`, `2026-10-16`) — and the reserve carries **`nextFundingDate`** (`2026-10-02`, the plan's own next event). Those two fields are the deterministic schedule.

**Also falsified, not just unproven:** an even split of the reserve (`109710/5 = 21942` cents is not observed), a proportional split, and a nearest-due-first waterfall (Eversource and Xfinity are due `2026-09-30` and hold nothing, while Rent is due `2026-10-16` and holds all `$1,097.10`). The even-split fallback OS-048b shipped, and the divisor copy the owner ratified, are therefore modelling something Crew does not do. D-015 records that; OS-055 and OS-056 are refined to mirror Crew's formula instead.

**Stated as open rather than guessed:** `totalReservedAmount` (the `÷ 0.46 = $2,385.00` ratio is exactly round but does *not* survive the proven formula, so it is a coincidence), how Crew chooses which bill the balance is earmarked to, and the reserve-level `estimatedNextFundingAmount` (`$1,435.97`, not the sum of the per-bill estimates). All three become measurable at the **`2026-10-02`** funding event from data `crew_bill_reserves` and `commitments` already refresh every 15 seconds — no new tooling, no code change.

Findings: `docs/project/CREW_FUNDING_MATH_2026-09-19.md`. Documentation only: no code, test, migration, schema, provider, authority or behaviour change; the snapshot is a read of data the running app already fetches every 15s.

Method note for the next agent: invoking the connector CLI *while* the app's refresh loop is also calling it makes the call hang past the shell limit. Run it detached with output to a file and it returns in seconds. The payload is the owner's real financial data — read the fields you need, never paste it around.

### 2026-09-19 — OS-048b: the dial states the per-bill reserved amount it was throwing away (committed `fec1c33`, base `2f2e833`)

D-013 permits the per-dated-occurrence reserved figure and fixes its precedence. Implementing that instruction turned up two things the audit could not find anywhere in storage, and one thing in production that neither the ruling nor the handoff anticipated.

**The dividend did not exist.** D-013's fallback is *"an even allocation of total set aside funds, split evenly across commitments"*. Crew's `billReserve.totalReservedAmount` is that total, and the connector already read it — `readback_reserve_totals` for write verification, and the preview's own expenses summary — but **nothing persisted it**: no column, no table, no row anywhere in the schema. The only reserve-scoped number that *was* stored, the funding plan's own amount (022), is the plan's per-cadence figure rather than the bucket balance, so dividing it across bills would have manufactured a number and attributed it to the owner's income source. Migration `024_crew_bill_reserve_observations.sql` adds `crew_bill_reserves`, keyed on Crew's own reserve id, with a nullable total, an observation time, and the 020/021/022 absence discipline: an unobserved facet is evidence of nothing, an unreported total is not an empty bucket, and a withdrawn reserve is retired rather than deleted.

**"Reported zero" and "never reported" were the same stored value.** `commitments.funded_amount` is `REAL NOT NULL DEFAULT 0` (005) and C01 pins that a bill whose reserve Crew never reported reads 0.0 — exactly like a bill Crew emptied. So the two copy states the handoff's test list requires ("not yet set aside" versus "Funding unknown") were not merely unimplemented; they were *unrepresentable*. The same migration adds `commitments.reserved_amount_reported`, and the backfill sets it only where `funded_amount > 0` — an implication rather than a guess, because absence writes 0.0, so a positive value can only have come from something that stated it (a Crew report, a migrated legacy balance, or the owner's own figure). A read that does not report the field never clears the flag, mirroring C01's refusal to let a silent read erase a known amount.

**Precedence lives in one function.** `_reserve_figure` returns the figure, its status, its basis, its divisor, its attribution and its observation time. Observed wins — Crew's own per-bill `reservedAmount`, attributed to Crew only when the stored row itself came from Crew, so a local bill's figure is never called Crew's. Otherwise the reserve total is divided evenly across the bills in that reserve, labelled `derived`, attributed to Meridian, and shipped with its divisor so a consumer can reconstruct the division. Otherwise nothing is stated. The figure is written to the **earliest occurrence in the horizon only**; later occurrences of the same bill keep `"unknown"`, which is D-010 as narrowed by D-013 — one share per bill is permitted, multiplying it across future dates is not.

**Labelled wherever it is stated.** D-013 §4 is not only about the ticket. The centre readout, the event row, and the accessibility text all read the figure through `fundingReserveSummary`, so a derived figure says "(Meridian estimate)" in the rail and is never attributed to Crew; the ticket adds the divisor ("Meridian estimate, split across 3 bills"). A payload carrying a reserved amount with **no** basis is not promoted into the figure line at all, and keeps its pre-slice rendering — a test pins that, because an unlabelled number can only be read as an observation.

**The finding that was not in the handoff: the production path stored neither fact.** Funding plans and reserve totals were written only by `sync_providers`, which OS-053 had already established has no production caller; `app.py` refreshes through `meridian.live.sync_live_crew`, which wrote accounts, transactions, commitments and bill absence — and neither of the two facts the dial's funding resolution reads. OS-048a's source naming and this slice's figure would both have been dead in the running app, with green tests, because every test inserted the plans and reserves directly. `sync_live_crew` now performs both writes, Meridian-local, additive, provider-read-only, under the same tri-state absence rule. That is a persistence correction, not an authority change.

**One visual defect was caught by looking, not by asserting.** The first ticket label was the full sentence "Set aside for this bill"; the 420px capture shows it wrapping onto a second line that collided with its own value. The label is now the short "Set aside" — the row grid's label column is sized for AMOUNT / FUNDING SOURCE / RESERVED — the provenance note is date-only (the ticket header already stamps the time), and the browser suite now measures the label and value boxes and fails if they overlap.

Verified: 29 new non-browser tests (new `services/test_dial_reserved_amount.py` 12, new `test_bill_reserve_observations.py` 15, +2 in `test_dial_js.py`) and the full non-browser suite **1390 passed, 1 skipped**; 13 new browser tests (new `tests/browser/test_dial_reserved_amount.py`) driving the real module and stylesheets with a deterministic synthetic model and a fixed clock across the contract's five viewports × both themes at the specified DPRs — zero horizontal overflow, zero console errors, plus the measured label/value collision check and an executed check that an unlabelled payload is never promoted; `node --check`; Ruff clean; guardrails clean for `deepseek-os048b`; `git diff --check` clean. Captures: `artifacts/observatory-dial-reserved-2026-09-19/` (10 viewport PNGs; no concept drawing of a reserved amount exists, so these are synthetic self-consistency and review artifacts, not a concept-vs-capture parity matrix).

Explicitly not done and not claimed: **no live sync, no provider call, no backfill, no deployment, no `:8081` restart.** `crew_bill_reserves` is empty in every existing database until the next ordinary read runs, so the running app still states nothing new. The six `tests/browser/test_dial_fidelity.py` failures listed as OS-049 were reproduced at pristine `2f2e833` with this diff stashed, so they are pre-existing and this slice neither caused nor fixed them. `sync_providers` and `sync_live_crew` now copy three fields twice, and a test pins the two paths equal on the reserve facts; the recurrence divergence OS-053 records is untouched and still deliberate.

Owner ratified the derived figure's divisor copy after the slice — *"Split across 3 bills is fine, I can always adjust after"* (D-014). Nothing was changed in response; the ruling is recorded so the wording is not re-opened as an open question, and it remains revisable as presentation only.

**Post-slice verification, read-only (`b1e3c81`):** the owner noted the refresh runs every 15 seconds, so the live state was inspected instead of assumed, and the assumption underneath both OS-048a and OS-048b turned out to be wrong in a way worth recording. `meridian/refresh.py` does default to 15s and `/tmp/gate-preview/gate.db` shows crew runs completing every ~15–21s. **Migration 024 is already applied there** — the running process builds `FinancialRepository(...)` on every refresh and that constructor runs pending migrations — so 024 and its backfill have been exercised against real populated data: 11 bills, exactly one with `funded_amount > 0`, and exactly that one (`Rent`, 1097.10) flagged `reserved_amount_reported = 1`. But the process serving `:8081` (`run_preview.py`, PID 60909) started **03:19:38 on 2026-09-19**, roughly 14 hours before `fec1c33`, and nothing reloads a module, so it is still running the **pre-OS-048a** `meridian/live.py`: `bill_reserve_id` is `''` on all 11 bills and `crew_funding_plans` / `crew_bill_reserves` hold 0 rows while the bills update every 15 seconds. Conclusion: **both slices take effect on an app restart, not on a read** — which is owner-gated, and is why this slice did not restart `:8081`. The handoff's "existing stored bills keep an empty membership until an ordinary read sync runs" is falsified: reads have been running every 15s throughout. Recorded in CURRENT_STATUS and OS-054; no code, test or schema change followed, because none is indicated.

**Owner authorized the restart; live verification complete (`a0062e9`).** `run_preview.py` PID 60909 was stopped and restarted with its exact original invocation (PID 30001, 17:34:51, first refresh `complete`), so both slices are running against real data for the first time. Read from a consistent SQLite backup snapshot of the live database, never by touching the live file. Both tables populated (`crew_bill_reserves`: reserve `BillReserve:8d2f3e8f-…` at 1097.10; `crew_funding_plans`: **Veterans Home**, 1663.00, `biweekly`), all five real Crew bills now carry the reserve id, and the three bills in today's horizon each emit `fundingStatus: "unfunded"`, `fundingBasis: "observed"`, `fundingAttribution: "crew"`, `reserved: null` and `fundingSource: Veterans Home` — so the fourth copy state is live and the dial now says these bills are **not yet set aside** in Crew's own terms rather than "unknown". The funded bill (Rent, next due 2026-10-16) is simply past `horizonEnd`. OS-054 closed.

**New finding from that live data, contradicting D-013's premise and recorded rather than acted on:** Crew does allocate per bill. Rent reports 1097.10 and the other four report 0.00 *explicitly* (`reserved_amount_reported = 1` on all five), and `totalReservedAmount` = 1097.10 is exactly their **sum** — not an independent pooled bucket. So the `derived` branch is dormant on this data (precedence correctly stops at `observed`, meaning the owner-approved "split across N bills" copy currently appears nowhere), and if it ever fired on a partially-reported reserve it would give an unreported bill a share of *other bills'* money. Filed as **OS-055** with three candidate rules for the owner, deliberately not changed silently: it is dormant, so nothing on Today is wrong today, and the fix changes what the dial claims about money.

### 2026-09-19 — OS-048a: the bill→reserve membership survives ingestion, and the dial names the funder (committed `8e8333c`)

Read-side slice for D-010 (*"Bills are already funded by a particular funding source or income source in Crew"*). The plan was already stored with its reserve (022); the bill side dropped the containing reserve id at ingestion (`_collect_commitment_candidates` bound `account.billReserve` and never read its `id`), so no join existed and every bill read "funding unknown".

**Recon finding worth keeping:** `sync_providers` (`meridian/sync.py:152`) has **no production caller** — only its own definition and tests. Production ingest is `meridian/live.py::sync_live_crew`, which calls `sync_provider` (singular) and duplicates the candidate→commitment loop at `live.py:63-89`. The copies have already diverged: a frequency-less bill becomes `recurrence: "monthly"` in `live.py:71` but `"one_time"` in `sync.py:197`, so the same provider read stores different data depending on the entry point. This slice copied the new field into **both** sites and deliberately did **not** touch that divergence, because changing it would change what production writes. Filed as **OS-053** for a deliberate decision.

**What changed:** `CommitmentCandidate.bill_reserve_id` (read from `account.billReserve.id`; `""` = not observed); migration `023_commitment_bill_reserve.sql` adds `commitments.bill_reserve_id`, registered in `shipped-migrations.json` and `_LATER_MIGRATIONS`; both mapping sites copy it; an unobserved id never overwrites an observed one while a different observed id replaces it; `dial.py` resolves the membership against **current** plans and exposes `fundingSource` with plan id, name, provider, cadence, observation time and reserve id — or `fundingSourceAmbiguous` with the candidate ids and **no name chosen**, or `null`. `fundingStatus` stays `unknown` and `reserved` stays `null`: source identity is not an occurrence reserved amount. `dial.js` shows the source in the centre, the event row, the accessibility label and its own evidence-ticket row beside the unresolved Funding row.

**Verification:** new `tests/meridian/test_bill_reserve_membership.py` (8 tests) and `tests/meridian/services/test_dial_funding_source.py` (9 tests), extended `test_dial_js.py` (executed under Node, not grepped) and `test_dial_income_meta.py` (updated, not deleted, to keep pinning that income rows carry no funding status); migration list and checksum registrations updated. Focused suites 98 passed; full non-browser suite passed with 1 skipped; `node --check static/js/meridian/dial.js`; Ruff clean; guardrails OK for `deepseek-os048a` (18 scope patterns); `git diff --check` clean.

**Not done, and must not be assumed done:** no live sync ran, so existing stored bills still carry an empty membership — a normal read sync is what populates them, and no backfill was guessed; the reserved amount per dated occurrence is still unknown; weather and risk are unchanged; no provider call, migration edit, deployment or authority change. The live preview on `:8081` was not restarted or mutated. Committed as `8e8333c`; the claim row was released with this entry.

### 2026-09-19 — DeepSeek adopts and commits the owner-rulings/visual checkpoint (`052ab3e`)

The Codex lane handed off the owner's 2026-09-19 rulings (`codex-owner-rulings`) as a deliberately uncommitted
checkpoint and asked DeepSeek to reconcile the claim, reproduce the evidence, and commit it. Done: `052ab3e`
("Meridian: owner rulings, generated sun marker, and the focused visual pass") — 20 paths, 386 insertions, no
push and no deployment.

**Reproduced, not accepted on description.** 55 focused tests passed under `.venv311/bin/python`
(`test_settings_visual_preview`, `test_observatory_identity`, `test_auth_branding`,
`test_activity_timeline_chrome`, `test_activity_glyph`, `test_activity_vignette` — a superset of the 42 the
handoff claimed). `node --check static/js/meridian/activity.js`, Ruff on the changed preview/capture/test
files, `git diff --check`, and `scripts/check_guardrails.py --agent codex-owner-rulings` (21 scope patterns,
456 changed paths) all clean. `sun-engraving-2026-09-19.png` was re-hashed to the `asset.json` sha256
`25e0aeca…`, with RGBA mode, 1254×1254, alpha 0–255 and 1,238,578 fully transparent pixels read back
independently.

**One measured-evidence error corrected.** The handoff, `CURRENT_STATUS.md` and
`VISUAL_CORRECTIONS_2026-09-19.md` all described the Settings 32px overflow as "mobile". The manifests say
otherwise: `after-main` 30 records, `after-activity` 10 and `observatory-sun` 10 with zero overflow and zero
console errors, and `after-settings` 10 records with exactly two nonzero entries — 32px at the **1024×768
tablet** viewport, light and dark. The 390/420/430 mobile viewports were clean. All three records now say
tablet. The lesson to keep: the claim was right about the app and wrong about which viewport, and only reading
the manifest back could tell the difference.

**Scope held.** Documentation-only adoption plus the checkpoint's own presentation change (generated sun
marker, round wordmark dot, ≤600px Activity row stack, Settings theme controller, read-only synthetic
Connections preview). No provider call, database write, migration, route authority or live-preview (`:8081`)
touch. Captures in `artifacts/observatory-sun-2026-09-19/` and `artifacts/visual-pass-2026-09-19/` stay
untracked by convention. `design-qa.md` was declared in the claim but not modified. The pre-existing untracked
set is intact — 2089 entries before the commit, 2082 after, the seven-file difference being exactly the newly
tracked files.

**Next slice, unchanged by this commit:** OS-048 read-side Crew bill→reserve funding source per D-010 and
`DEEPSEEK_HANDOFF_2026-09-19.md` — retain the observed bill→reserve link during ingestion, expose source
identity separately from occurrence reservation status, never default a missing or ambiguous link to the sole
global plan, and perform no live sync or provider mutation.

### 2026-09-18 — ⚠ A CONCURRENT WRITER IS ACTIVE IN THIS WORKING TREE

**Found while reviewing my own diff before committing OS-043.** `git diff` listed seven files I had
never opened:

    M meridian/classify.py              M static/js/meridian/activity.js
    M meridian/repository.py            M static/js/meridian/kit-icons.js
    M tests/meridian/test_activity_glyph.py    M static/js/meridian/review.js
    M tests/meridian/test_repository.py
    ?? meridian/category_catalog.py     ?? tests/meridian/test_category_expansion.py

**mtimes 11:45–11:48, interleaved with my own 11:47–11:50.** So this is live, concurrent writing into the
same directory — not a stale artifact and not a rebase.

**What it is** (read so the report is concrete, not a guess):
- a new `meridian/category_catalog.py` — 29 categories with a merchant→category lookup, imported by both
  `classify.py` and `repository.py`. It is **untracked**, so any commit of those two files alone would break
  the import.
- `kit-icons.js` rewritten around a new ornate `CATEGORY_ICONS` vocabulary — basket, fork-knife, cup-hot,
  fuel-pump, bus-front, bag, controller, airplane. **This is the "ornate icons" work the owner described
  Astra as doing**, already in flight.
- `repository.py` adds a genuine authority improvement: `if current["classification_evidence"] == "owner
  correction": return` — automated sync/AI/rule refresh can no longer undo an owner's category correction.

**What I did about it:** staged **three paths by name** for OS-043 and verified nothing else was staged.
None of the concurrent files are in that commit, and there is **no file overlap** between the two sets. I
did not revert, stash, or touch any of it.

**Two consequences to hold on to:**
1. A full-suite run and a governed capture taken in this tree are **contaminated** — they exercise that
   uncommitted work. My "1220 passed" included it, and the Activity captures may show its icons. Targeted
   tests for my own change were re-run in isolation (46 passed).
2. **Concurrent uncommitted work to core logic (`classify.py`, `repository.py`) is itself a risk** — those
   are not presentation. Classification drives what the app asserts about spending, and the pair cannot be
   committed without `category_catalog.py` riding along.

**Unresolved and needs the owner:** whether Astra's lane commits its own work, and who owns the remaining
Activity presentation work, since the ornate-icon half already exists in this tree uncommitted.

### 2026-09-18 — Builder (Today) — the hand was landing in the observatory

**Owner:** *"It defaults into the building for today and is not visually appealing. Where the hand sits per day
to say."*

**Root cause was a convention, not a widget bug.** The arc ran −120°…+120°, so day 0 (today) sat at −120° and put
the hand at (129,399) — precisely where the kit's `dial-plate.png` draws its observatory. Worth recording that
**the concept cannot arbitrate this: its dial has no building at all** (checked both lower quadrants of
01-today.png), so the observatory is the kit's addition and there is no governing answer for how a hand should
treat it. That is why this went to the owner as a decision rather than being silently "fixed".

**Measurement note worth reusing.** Ray-casting the plate from its centre found "building" on the *right* side,
where there is none: the sky's star sparkles are individually bright enough to trip a naive light-pixel test.
Requiring a run of **8 consecutive light samples** (~16px) removed them and left the real mass. A measurement
that reports structure where none exists is worse than no measurement, because it looks like data.

| | |
|---|---|
| building intrudes into the sky disc | only between −140° and −110° |
| reaches inward to | r = 150–182 |
| hand runs | r = 118–198 |
| roofline inner edge, −110° → −105° | 165 → 283 (near-vertical) |

**Fixed:** `ARC_START` −120 → **−100**, `ARC_END` unchanged. Sweep 240° → 220°, which also stops the visible rim
arc short of the roofline. The hand's r=198 tip clears the nearest building edge (r=283) by **85 units on every
day**, with a full-length hand throughout.

**Three options were measured and offered; the owner chose the shift.** Clamping the hand's outer radius at the
roofline was rejected on evidence: at 14 days only day 0 falls in the −140°…−110° band, so the hand would
visibly change length for a single day and read as a glitch. The full concept-arc rework was declined as too
large a relocation.

**The guard reads the constant rather than matching a literal.** `test_the_day_arc_starts_clear_of_the_dials_building_art`
parses `ARC_START` from the source and fails below **−105** — the measured roofline, not a preference. Proved to
bite by re-setting it to −120, which fails with the exact diagnosis.

**Visible and intended:** every day's position moved by up to 20° at the lower-left end, so the arc is now
asymmetric about the top (midpoint +10° rather than 0°). Drag input clamps to the same new range, so scrubbing
and the rendered positions cannot disagree.

**Test state:** non-browser suite 1189 passed, 1 skipped. Browser dial file unchanged at **6 failed / 13 passed**
— the same 6 pre-existing failures. Captures `artifacts/observatory-dial-arc-2026-09-18/` — 10 files, zero
console errors, zero horizontal overflow.

### 2026-09-18 — Builder (Today) — the dial placed evenly, and a revert I got wrong

**Owner:** *"I am much less concerned with the size of the dial, I just want it evenly placed vertically."*
That closes OS-035's open composition question in one sentence — placement, never size.

**I had left it at the extreme.** `d0e0cd6` reverted an `align-self: center` on the instrument. The revert was
right that the old rule did not fix the owner's report, and **wrong about what the owner wanted**: with
`align-items: start` the dial measured **0px** from the panel top with **all 48px** of its band's slack beneath
it — 0 above / 252 below. Removing the centring did not merely fail to help; it produced the worst available
arrangement for "evenly placed". Worth saying plainly rather than quietly reversing it.

**Concept 01 settles it and agrees with the owner:** its dial spans ~435px inside a band whose callouts span
~490px, i.e. roughly 25px above and 30px below. Centred, not pinned. The concept barely has slack because its
columns are near-equal height; ours had 48px because the rail cap (318px) exceeds the dial (270px).

**Fix:** `align-self: center` on the instrument at ≤700px → **24px above / 24px below inside the band**.
Unchanged at 1024/1440px, where the dial is taller than its band and centring is a no-op.

**The revert's second reason was real but is now stale.** It was that centring made the dial's position track
the event-list length because the row grew with the list. `d0e0cd6` also capped the rail, so the band height is
bounded and the offset is derived, not drifting. True against the uncapped rail; not true now.

**A guard pointed the wrong way, and this is the reusable lesson.**
`test_long_event_list_does_not_push_dial_down_or_split_amounts` asserted `dial.y - panel.y <= 8` under the
message *"The event list must not vertically center the dial"* — it **demanded the arrangement the owner has
now rejected**. Its mechanism was superseded by the owner's requirement; its *reason* (no drift with list
length) is preserved. It now asserts the dial sits at the band's centre, `abs(centred − band_slack/2) <= 2`,
which fails both on pinned-to-top (0) and pushed-down-by-the-list. When a test encodes a *mechanism* rather
than the *reason*, the owner's requirement can invert it — and the fix is to re-express the reason, not to
delete the guard.

**Stated limit:** this balances the dial in its own band. The whole panel still measures 24 above / 228 below,
because the controls row and evidence ticket sit below the band and `align-self` cannot reach them. Panel-level
equalisation needs the dial's column to span all three rows, which would crush the controls and the 130px
callout column into one strip. The concept also carries real content below its dial band, so content below is
not itself the defect.

**Test state:** non-browser suite 1189 passed, 1 skipped. Browser dial file back to **6 failed / 13 passed** —
the same 6 pre-existing failures, none dial-placement related (4 topbar theme-toggle label, 2 dial/rail
clearance). Captures `artifacts/observatory-dial-centring-2026-09-18/` — 10 files, zero console errors, zero
horizontal overflow.

### 2026-09-18 — Builder (Accounts) — the summary ticket tilted, notched and dotted

OS-038's third item, closing Finding 4's "axis-aligned, square-cornered and plain".

**The angle was measured, not chosen.** Two independent features *inside* the concept's ticket agree: its top
edge (−3.7° over 656 columns, robust fit) and the brass rule under the amount (−3.21° over 104 columns). The
rule is the cleaner purely-internal feature, so the panel takes **−3.2°**. The text tilts with the panel,
because that is what the concept draws.

**The notch size is a measured deviation, not a slip.** At the concept's own ~25px the notch was invisible as a
notch: the concept's edge is smooth, but the kit's `parchment-ticket.png` already carries ~10px scallops down
the same edge, so a concept-sized bite read as a *missing scallop*. 36px makes the gesture legible. This is
recorded in the CSS comment, the ledger and `design-qa.md` rather than left as an unexplained number.

**Two implementation choices worth keeping.** The dotted inset border is `outline: 1px dotted` with
`outline-offset: -14px` — it needs no third pseudo-element and stays out of the accessibility tree. The notches
are pseudo-element circles in `var(--obs-bg)` rather than a mask cut, so they rotate with the panel and need no
`mask-composite` support.

**Verified rather than assumed:** a rotated box is wider than the box that laid out — 388×164 at −3.2° bounds to
~397px against a 388px column. Zero horizontal overflow measured at 390/420/430px and confirmed by the governed
capture at all five viewports in both themes. The kit's nine-slice, scallops and rivets are **preserved** and a
test asserts the nine-slice survives the change.

**Scope note:** this edits `tests/meridian/test_accounts_ticket.py`, which the parallel `builder-trackd` claim
lists. That lane's work is committed, its tree is clean, and the edit is additive (one new test), so the overlap
is disclosed here rather than taken silently.

**Test state:** non-browser suite 1189 passed, 1 skipped. Captures
`artifacts/observatory-accounts-ticket-2026-09-18/` — 10 files, zero console errors, zero horizontal overflow.
`ruff` clean; `git diff --check` clean.

### 2026-09-18 — Builder (Plan) — the tabs rebuilt as the concept's bordered bar

OS-038's fourth item. Concept 02's tab row is **one rounded container with a brass border, three equal cells
divided by thin vertical rules, and a parchment-filled active cell carrying a brass star medallion at its left
edge**; the app had three pills in a muted trough. Measured before building: container ~733×82px (852px concept,
0.493 to 420px) → ~361×40px; active cell 254px = an equal third; medallion ~70px → ~34px.

**Two real bugs surfaced while verifying, and the second is the instructive one.** The cells measured
**148/119/119**: with `box-sizing: border-box` a zero flex basis is floored by the active cell's own 42px
medallion gutter, so "Plan" was wider than its siblings. A one-third percentage basis fixed that at the base
rule — and then the *existing* `@media (max-width: 600px)` block's `flex: 1` (i.e. `1 1 0%`) re-imposed the
asymmetry at exactly the widths the concept's equal cells matter. A fix that only inspected the rule being
written would have shipped the bug at every mobile width. Final measured cell widths: 118.7/118.7/118.7 at
390px, 128.7 at 420px, 132 at 430px; labels fit; zero overflow.

**Deliberate deviation, recorded:** the bar is built to 44px rather than the concept's 40px, because its cells
are buttons and 44px is the touch-target floor.

**Scoped to `plan.css`.** Activity keeps the ruled-underline treatment concept 03 shows; the two workspaces are
not meant to share one tab style.

**Test state:** non-browser suite 1188 passed, 1 skipped (+2 guards in `tests/meridian/test_plan_map.py`, one of
which strips CSS comments before asserting so it cannot fire on its own documentation). Captures
`artifacts/observatory-plan-tabs-2026-09-18/` — 10 files, Plan × five governed viewports × two themes, zero
console errors, zero horizontal overflow. `ruff` clean; `git diff --check` clean.

### 2026-09-18 — Builder (bottom dock) — taller, with the concepts' ornate glyphs

Owner-requested in the same pass as the dial work: *"Taller icon dock at the bottom I noticed as well, in the
concept. Also with more ornate icons."* Both halves were measured against concept 01 before anything changed,
and both were true.

**The concept:** panel 152px tall in an 853px frame = **17.8%** of width; a rounded panel inset 2.0% from the
screen edges, hairline rules between workspaces, each glyph **stacked above** its label, the ringed compass at
~**8.4%** of width (~34px at 420px), and the active workspace marked by a lilac rule **under** its label with
**no fill** behind the item.

**The app had:** **65px (15.5%)** full-bleed bar, **20px** Bootstrap silhouettes, **12px** labels, glyph
*beside* label, marker *above* the glyph.

**Delivered:** stacked layout (most of the height), glyphs 20→34px, labels 12→15px, item floor 56→64px, the
concept's rounded inset dock with hairline rules between workspaces, the marker moved under the label, and the
lilac active fill removed. After: **76px = 18.1%** at 420px, a ratio of **1.02** against the concept.

**Four glyphs were drawn, not borrowed:** `compass-rose.svg` (ring, inner ring, four-point star, cardinal
ticks), `charted-map.svg` (folded three-panel map, dotted route, cross, waypoint), `rising-bars.svg` (four
ascending columns on a baseline), `ringed-profile.svg` (ring, head, shoulders). They stay single-colour CSS
masks driven by `currentColor` — the concept inks the active glyph lilac and the rest muted, which is precisely
what that mechanism already does, so the theming architecture is unchanged. The kit's Bootstrap glyphs are
**superseded for the dock, not deleted**: they remain on disk and still serve surfaces that use them.

**One guard was reconciled rather than satisfied.**
`test_shell_maps_each_workspace_to_its_supplied_kit_glyph` hard-coded the kit's filenames and failed the moment
the owner's request was implemented. Its value was the invariant — one workspace, one real glyph, both mask
properties — not one file's path, so it now guards that and is renamed
`..._to_its_own_glyph_and_the_file_exists`. The path was the brittle part, not the intent.

**Scope limit, re-measured:** the desktop rail is untouched — 150px, row layout, 20px glyphs, no inset, zero
overflow.

**Recorded, not chased:** at 390px the dock is 19.5% of width against the concept's 17.8%, because the glyph and
label are fixed sizes while the viewport narrows; the concept is one fixed-width composition.

**Test state:** non-browser suite **1186 passed, 1 skipped** (+4 new guards). Captures
`artifacts/observatory-dock-2026-09-18/` — 40 files, four workspaces × five governed viewports × two themes,
zero console errors, zero horizontal overflow, light/dark luminance deltas 151–159. Note
`tests/browser/test_meridian_shell.py` cannot run against the isolated synthetic preview: its conftest registers
an owner through `/api/auth/register`, which only the full app serves, so it fails at setup (20 errors) rather
than on assertions. `ruff` clean; `git diff --check` clean.

### 2026-09-18 — Builder (Today dial) — OS-036 reproduced and fixed; the instrument centring reverted

Claimed `dial.js`, `dial.css`, the two dial test files and the docs.

**OS-036 was not a false alarm.** It was recorded as "could not reproduce; needs the owner's data", with the
long-event-list case named as the untested candidate. That candidate was the answer. `renderConnectors` drew a
run for every event in the horizon on the assumption that every row had somewhere on screen to land, but the
rail is internally scrollable: with a 14-event horizon its content is 1591px inside a 330px box, and 11 of the
14 rows sat below the visible area while still receiving a run. Those runs ran to `y=1754` and were cut off by
the connector layer's `overflow: hidden` at `y=746.9` — dashed lines to nowhere, exactly as reported.

The fix is twofold and both halves are needed: only rows whose centre is inside the rail's visible box get a
run, and the rail re-runs `renderConnectors` on scroll so the survivors keep following their rows. The scroll
listener is bound where the rail is created, so it dies with the element `update()` replaces rather than
needing its own teardown. 14 runs became 3, each exactly on its own visible row, and scrolling re-anchors to
the newly visible rows with none off-screen. The behavioural guard was checked against the unfixed code and
**fails** there (14 runs for 11 hidden rows), so it is a real guard.

**A previous "fix" in this area is reverted.** `5c732f9` added `align-self: center` to the instrument and
recorded it as balancing the dial's vertical space. Measured, it does not: the owner's 29px above / 233px
below only becomes 0/262, because the void is the **second** panel row (controls + evidence ticket), which
`align-self` cannot reach. What it does do is make the dial's vertical position a function of the event count
— at 390px a 12-event horizon centres a 240px dial in a 300px row and pushes it 30px down. Reverted. Its
removal then exposed the other half of the same guard, `rail.height <= dial.height + 48`, which the rail's
`calc(100vw - 90px)` cap overshot by 12px at every governed mobile width; the cap is now derived from the guard
(`calc(100vw - 102px)`, with the derivation written into the CSS).

**Net effect:** 3 of the 9 pre-existing `tests/browser/test_dial_fidelity.py` failures are green. The other 6
are unrelated and named rather than waved at: 4 are the topbar's theme-toggle label measuring 20.86px at
390/430px where the test wants `<= 1px`, and 2 demand 10px of clearance between the dial wrap and the rail
where the design deliberately spends the full 12px column gap — a conflict between the test's expectation and
a documented clearance decision, which needs re-deciding rather than silently satisfying.

**Test state:** non-browser suite 1182 passed, 1 skipped. `ruff` clean on tracked source; `git diff --check`
clean. No route, data, financial, provider or authority change. Not deployed.

### 2026-09-18 — Builder (Accounts) — the supplied archive-building asset, and a red suite left behind

Claimed only the reconciliation surface: the stale guard, the stale comment, the manifest row and the docs. The
parallel `builder-trackd` lane's commit `0b8a3ba` is **not** reverted, re-authored or re-staged; its `accounts.css`
and its asset are left exactly as shipped.

**What the other lane left.** `0b8a3ba` replaced `observatory-landscape.png` with
`accounts-ticket-building.png` in `.m-accounts-ticket-art` and updated `test_accounts_ticket.py` — but
`test_accounts_assets_strip.py` still asserted `"observatory-landscape.png" in css`, so the non-browser suite was
**red on `HEAD`** (1180 passed, 1 failed). That test file was inside the other lane's own declared claim
(`docs/project/agent-claims.json` → `builder-trackd-today-parity`), so it was claimed and not reconciled.

**The fix kept the intent, not the filename.** That guard exists to stop *unsanctioned reuse*, and swapping a
shared building for a dedicated one is the same restraint it protects. It now asserts all three facts: no
`activity-telescope.png`, no `observatory-landscape.png` (Today's building stays on Today), and
`accounts-ticket-building.png` present and on disk. A comment that still described the old asset in
`accounts.html`, and four stale doc references, were corrected the same way.

**Recorded rather than overclaimed.** The supplied art is a colonnaded domed archive building with scrolls and an
open ledger. It is *not* a reproduction of the concept's "colonnaded domed rotunda on a rocky knoll" — it stands on
a flat plinth among foliage — so it is recorded as the owner-supplied governing art for this surface, with no
pixel-equivalence claim. Transparency was **decoded, not assumed**: alpha range 0..255, 56.2% of pixels fully
transparent, all four corners `(0,0,0,0)`, satisfying the handoff's "real transparency" rule. One size note is
recorded and deliberately not acted on: the asset is 2.0 MB for a slot of at most 188 CSS px, within existing
precedent (`dial-plate.png` is 3.0 MB), so it ships as supplied rather than downscaling the owner's art unasked.

**Captures:** `artifacts/observatory-accounts-building-2026-09-18/` — 10 files, Accounts × five governed viewports
× two themes, zero overflow and zero console errors, light/dark luminance deltas 147–163.

**Test state:** non-browser suite **1181 passed, 1 skipped** (the previously failing guard now passes). The nine
`tests/browser` `test_dial_fidelity.py` failures remain **pre-existing and unrelated** — they reproduce on a clean
`874f61a` tree with this work absent. `ruff` clean on tracked source; `git diff --check` clean.

### 2026-09-17 — Builder (Today/Activity/Accounts) — OS-038 first item: the lilac wavy title rule

Claimed `title-rule.svg`, its manifest row, `workspaces.css`, the three partials and the new guard file.
**Released at the commit carrying this row.**

The rule was measured before it was drawn, from the governing concepts rather than by eye: concept 01's rule is
141×18 px with an 8.1px stroke and a 10.0px peak-to-peak wave, concept 03's is 130×17 with a 7.4px stroke. The
scale-independent ratio the concepts agree on is **peak-to-stroke 1.23–1.28**, and the asset draws 1.25 (a 4-unit
stroke, a 5-unit wave, a 24-unit half-period). It is held at a constant 72×12 CSS px rather than scaled with the
title, because the concepts size it as a fixed ornament — it is 0.40× Today's cap height but 1.57× Activity's.
Concept 02 (Plan) shows **no** rule, so none was added there, and a guard fails if one appears.

Two traps worth keeping from this slice, both of which cost real time:

- **A 3× capture cannot be compared to a concept by absolute pixel size.** The first version looked right in the
  capture and was wrong: its amplitude was ~1.8× the concept's *relative to its stroke*. Only the ratio
  peak-to-stroke, and the CSS-pixel size (`device px / DPR`), are comparable across the two.
- **`--` is illegal inside an XML comment.** A perfectly readable SVG comment made the asset unparseable, which the
  new guard caught before any browser saw it.

Also measured this round, and recorded rather than "fixed": **OS-035 is not a defect.** The instrument is already
centred in its own grid row at every governed mobile width (420px: 29.2px above, 29.1px below; 390px: 30.0/30.0).
The 233px the owner measured is the *second* panel row — `.obs-dial-controls` plus `.obs-evidence-ticket` — which
`align-self` cannot touch. The dial's real gap to the concept is **size**: 63.6% of viewport width against the
concept's 82.5%, because the callout column is a hard 130px floor. Closing that needs callouts relocated, which is
a composition decision, not a tweak.

**Captures:** `artifacts/observatory-title-rule-2026-09-17/` — 30 files, three workspaces × five governed viewports
× two themes, zero overflow and zero console errors, light/dark luminance deltas 147–182. An earlier attempt of the
same run passed `--app-url .../meridian` and captured **30 clean-looking 404 pages** while the manifest reported
zero console errors; the evidence was thrown away and re-captured against the root URL. Do not trust a manifest's
error fields to tell you a page rendered — inspect the image.

**Test state:** full non-browser suite **1181 passed, 1 skipped** (+4 new guards). The nine `tests/browser`
`test_dial_fidelity.py` failures are **pre-existing and unrelated**: they reproduce with this slice's tracked edits
stashed, on a clean `874f61a` tree (browser tests need `playwright`, which the uv runner cannot import, so the
non-browser baseline is the one this lane can actually compare). `ruff` is clean on tracked source; `git diff
--check` is clean.

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

- **Deleting a test makes a suite GREENER, not redder.** Three test functions were silently deleted
  across three commits by edits that used a function's `def` line as an edit anchor and did not re-emit it,
  so the `def` vanished and its body merged into the neighbouring test — where it still ran and still
  passed. Pass/fail cannot detect this, and a rising test total hides it. **Never anchor an edit on a `def`
  line without re-emitting it, and verify by NAME COUNT after editing a test file.** The audit that finds it
  compares test-function names across every revision in the session against the working tree.
- **Tools/agents in this lane can leave the tree dirty without being the cause.** Untracked deliveries
  (e.g. `design/investigator-medallions-2026-09-21/**`) are filtered out of the handoff's tree-state line by
  design, so they never make it cry wolf; a `HANDOFF.md` left uncommitted by a previous generation DOES,
  because the generator reads `git status` before it writes.
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

### 2026-09-21 — Codex design delivery: medallions and Investigator

Owner requested only OS-038 medallion artwork and the user-facing Investigator, with scope left open to relevant evidence cross-references. Delivered `design/investigator-medallions-2026-09-21/README.md`, implementation contract, synthetic interactive specimen, two newly generated transparent medallion masters and hash/prompt provenance. Full icon pack and desktop Settings excluded. OS-038 remains open pending integration; new OS-076 records the surface design and follow-on work. Source review found the current role prompt carries document metadata, not meaningful facts; the handoff explicitly routes that prerequisite to the existing evidence/backend lane, preserving yesterday's storage and matching fixes.

Verified specimen interactions and observed two viewport/theme combinations; see VERIFICATION.md for exact checks and browser limitations. JS syntax, diff whitespace and roadmap reconciliation pass. No runtime code changed, no live data/provider use, no deployment, no app preview restart. All other tracks remain untouched. This log and package are design evidence, not application acceptance.
