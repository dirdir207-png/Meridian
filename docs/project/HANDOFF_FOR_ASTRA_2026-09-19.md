# Handoff for Astra — funding-link rule, icon ornateness, and the visual pass

**Written:** 2026-09-19 by the Builder lane (the session that shipped `c1b415b` and `6d1668c`).
**For:** Astra.
**Base:** branch `feat/meridian-implementation`, HEAD `6d1668c`, nothing pushed, nothing deployed.
**Scope of this handoff:** four pieces of work in priority order. Task A is a correctness/owner-decision
piece; Tasks B–E are visual. **No provider mutation, no push, no deployment, no authority change is
authorized by this document.**

---

## 0. Read these before touching anything

Rules and trajectory: `AGENTS.md`; `docs/project/MERIDIAN_ROADMAP.md` (supersedes
`MERIDIAN_VISION_ROADMAP.md`, `MERIDIAN_OS_ROADMAP.md`, `MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md`);
`docs/project/MERIDIAN_DECISIONS.md`; `docs/project/CURRENT_STATUS.md`; `docs/project/AGENT_COORDINATION.md`;
`docs/project/MERIDIAN_OS_TASKS.json`.
Visual acceptance: `docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md` + `design-qa.md`.

Hard boundaries, non-negotiable:

- Work **only** in `/Users/stephenwest/Openrouter/simplecrew-latest`. Never read
  `/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch` for authority and never modify it.
- **Add a row to the claims table in `AGENT_COORDINATION.md` and to `docs/project/agent-claims.json`
  before editing**, and run `scripts/check_guardrails.py --agent <your-agent-id>` (it fails closed
  without a declared claim). Stage **by path**; never `git add -A`.
- Agents may observe, explain, simulate, forecast, draft, propose and test. Only the constrained
  executor mutates financial state, through proposal → approval → execution → provider verification.
- Never present a forecast as fact, a simulation as a real balance, or a recommendation as permission.
  Missing data is not zero. A visual redesign never closes a correctness finding.

### Reconciling the visual authority (do this first; the records genuinely conflict)

The **newest** explicit governing set is `design/observatory-extension-2026-09-18/` — it holds
`concepts/review.png`, `concepts/settings.png`, `concepts/timeline.png`, `concepts/virgil.png`,
`icons/` (61 SVGs + LICENSE), `assets/`, `tokens.css`, `icon-map.json`, `prompts.json`, `BUILD_HANDOFF.md`.

`design/observatory-drafts-2026-09-08/` (00–06, including `01-today.png` … `04-accounts.png`) is
**historical** per `HANDOFF_2026-09-19.md`. Older notes in runtime memory still describe 09-08 as the
imagery target — **the handoff is newer and wins.** Do not start from 09-08 as the target.

**But there is a real gap here, and it is not yours to paper over.** The newest bundle contains **no
page-level concept for Today, Plan, Activity or Accounts** — it has only `review`, `settings`, `timeline`
and `virgil`. The only page concepts that exist for those four pages are the **historical** 09-08 images.
So:

- For **Activity's review/timeline surfaces**, and for **Settings** and **Virgil**, the newest bundle is
  the authority — subject to the caveat below.
- For **Today / Plan / Activity (timeline) / Accounts page composition**, there is currently **no
  non-historical concept to measure against**. Before treating 09-08 as the target for those pages, get the
  owner to confirm, or record explicitly that you are using it as **intent only**, with the reasoning.
  This is exactly the "verify whether 09-08 is superseded before relying on it" condition in `AGENTS.md`,
  and it is unresolved rather than settled.

Two caveats on the newest set, both from the 09-19 handoff: **`settings.png` and `virgil.png` "never
worked"**, so they are not reliable fidelity targets. Treat them as intent, not as measurement.

---

## Task A — Per-bill funding: "funded by Veterans Home" (the owner's original complaint)

This is the visible symptom the owner reported and it is **still open**. Everything else in this handoff
is cosmetic by comparison.

### What the owner said (verbatim, `CURRENT_STATUS.md`)

> *"All the bills also display funding unknown, the funding should link to a Funding Cadence setup by the
> user. … if I make a payday that titles 'Veteran's Home', and that is what is allocated toward my
> bills/expenses, they are funded by Veterans Home."*

### What is now verified in code (do not rediscover)

- The dial reports `"fundingStatus": "unknown"` for **every** bill, deliberately, with the reason in the
  module docstring and at the branch: *"Current data does not safely link one reserve to each future
  occurrence, so do not claim reserved/partial."* See `meridian/services/dial.py` (the `"kind": "bill"`
  branch). The bill branch is **not** a bug; it is an honest report of a missing link.
- **The Crew funding plan is now persisted** (commit `c1b415b`): `crew_funding_plans` holds
  `external_id`, `bill_reserve_id`, `name`, `amount` (dollars), `cadence`, `anchor_date`, `observed_at`,
  and a soft `absent_since`. `resolve_expected_paycheck(..., plans=...)` already resolves the expected
  paycheck to exactly one current plan, with `basis="crew_plan"` and the plan id as identity.
- A plan carries `billReserveId`, i.e. **the reserve it funds**. That is the candidate link.
- The connector also exposes reserve totals keyed by reserve id
  (`CrewWorkSnapshotAdapter.readback_reserve_totals()` → `{reserve_id: totalReservedAmount}`), and each
  Crew bill arrives as a `CommitmentCandidate` with the Crew bill id, `amount`, `anchorDate`,
  `frequency` and `reservedAmount`.
- `meridian/funding.py::project_funding` already exists for per-rule projections; do not build a second
  funding engine.

### The gate: one owner decision, and it is not yours to make

The proposal document `docs/project/INCOME_SOURCE_LINKING_PROPOSAL_2026-09-19.md` names the two
unanswered questions. The first one blocks this task:

> **Allocation:** when a payday funds several bills, is the relationship "this payday covers these bills"
> a **per-bill assignment the owner maintains**, or a **derived split of the total**?

A wrong answer here asserts a false relationship between two money records, which this project forbids.
`billReserveId` *suggests* reserve membership is already the answer (a plan belongs to a reserve, and the
reserve holds the bills), but that must be **confirmed by the owner**, not inferred.

**Therefore:** ask, or surface the question with the evidence above and wait. Do **not** ship a guessed
rule, and do not replace `"unknown"` with a confident value.

### Suggested bounded shape once the rule is approved

1. Resolve each bill occurrence's funding from the reserve it belongs to and the plan(s) funding that
   reserve, using the persisted plans rather than a fresh provider read.
2. Emit the existing `fundingStatus` vocabulary honestly — funded / partial / unknown — and keep
   `reserved` as a real amount only when it is one. Never spread one reserve across every future
   occurrence (the current docstring's rule still stands unless the owner's rule supersedes it).
3. Keep the provenance: which plan, which reserve, observed when.
4. Tests first, synthetic data only. No provider write. No deployment.

### Explicit non-goals for Task A

- Do **not** build a per-bill assignment UI until the owner approves the rule.
- Do **not** touch the deferred provider-mutation work (Meridian → Crew cadence write, symmetric delete).
  Those are separate slices that must ride proposal → approval → execution → provider verification.
- Do **not** silently retire the local `paycheck.py` config (OS-048 is still unanswered).

---

## Task B — The sun icon

### Verified facts

- `static/img/meridian/observatory/kit-2026-09-18/icons/` holds **62** SVGs. The supplied Bootstrap Icons
  set is **61** of them; the 62nd is **`sun.svg`**, **authored in this repository** and therefore the one
  file **not covered by the adjacent `LICENSE`** (MIT, "Copyright (c) 2019-2024 The Bootstrap Authors").
- The governing design bundle `design/observatory-extension-2026-09-18/icons/` also has 61 SVGs — it ships
  `moon.svg` and **no sun**. So there is **no governing concept artwork to extract**: this icon must be
  *designed*, unlike `dial-plate.png` / `moon-engraving.png` which were "generated from governing concept".
- It **is** actually used, so it is not a stray file: `static/js/meridian/activity.js` sets the Activity
  day-divider marker to `moon` for Today and **`sun` for every older day**, and `static/css/meridian/activity.css`
  masks both so they inherit the divider's brass. The comments there record that the kit ships
  `bi-moon` without `bi-sun` and that **approximating the sun in CSS is forbidden** — hence a real asset.
- Current geometry (16×16 viewBox, `currentColor`, `fill="none"`, `stroke-width="1.35"`,
  `stroke-linecap="round"`, `class="bi bi-sun"`, `aria-hidden="true"`): a 2.9-radius circle plus eight
  rays drawn as `<line>` elements rotated 45° apart. The header comment states the deliberate choice to
  match the kit's **outline** weight, since the supplied `bi-moon` and `bi-star` are outline variants.

### Why this is in the handoff at all

Two reasons, and the second is the one that matters:

1. It is an in-repo authored asset with no governing concept, so it needs explicit design authority and a
   provenance note rather than being treated as part of a licensed set.
2. It sits directly in the gap the owner has now named (see Task C): the supplied set is **flat outline
   Bootstrap**, and the concepts are **ornate**.

### Deliverable

Design the sun properly against `design/observatory-extension-2026-09-18/tokens.css` and
`icon-map.json`, keep it consistent with the set it sits in, and record its provenance beside it. Note for
your own decision-making: `icon-map.json` contains only `categories` and `actions` keys — there is **no
sun/day-marker slot**, because the day marker is selected by name in `activity.js`, not by the map. If you
add ornate rays, that is a deliberate departure from the 61-icon set's uniform weight and you should say so
explicitly rather than letting it look accidental.

Related open item from the same handoff: **`file-earmark-check`** (present in both
`design/observatory-extension-2026-09-18/icons/` and `static/js/meridian/kit-icons.js`) **has never been
rendered** from `concepts/review.png`. Verify whether it is mapped but unreachable, or mapped to a path
that no payload produces.

---

## Task C — The icons are less ornate than the concept (owner-reported, 2026-09-19)

Owner, verbatim:

> *"Of note also, the icons provided so far are decidedly less ornate than the concept."*

**Take this seriously and treat it as a design finding, not a bug.** The supplied icon set is Bootstrap
Icons: a flat, uniform, single-weight outline library, MIT-licensed, 61 files. The concept images in
`design/observatory-extension-2026-09-18/concepts/` are ornamented — brass, engraving, weight variation.
Those two things cannot both be "the design" without a decision, which is why this is first on the visual
list.

What to do before changing anything:

1. **Quantify it**, don't assert it. Pick a concept crop and a rendered icon at the same optical size and
   measure something reproducible and cheap — ink coverage, mean stroke weight, or dark-pixel ratio in the
   icon's box. The project's own lesson from the dial work applies: *measure, and prove the measurement
   bites* (the ray-cast that found "building" in the wrong place needed an 8-sample run test before it was
   trustworthy; the theme captures looked plausible and were wrong until luminance was measured).
2. **Then bring the decision to the owner**, because it has consequences that are not yours to absorb
   silently: replacing a 61-icon MIT set with bespoke ornament changes licensing, provenance, review
   surface and the "do not approximate engravings with CSS" rule — real art is required, either approved
   source art or image generation (`MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md`, the artwork-rules
   passage; note the roadmap supersedes that document *for planning* while its findings stay authoritative
   as findings). The rule is already expressed in code where it bites:
   `static/css/meridian/activity.css` records that approximating the sun is forbidden, and
   `CURRENT_STATUS.md` records the same gap twice as a **missing asset** rather than something to fake.
   Options worth presenting:
   (a) keep the set and add ornament only where the concept demands a hero glyph (day markers, dial,
   section badges); (b) commission/author a bespoke ornate set and document provenance; (c) a hybrid with
   an explicit list.
3. **Do not bulk-replace all 61 icons** on your own initiative. That is an authority change, not a visual
   tweak, and it would invalidate existing captures.

Answer the simple version of the question while you are at it: **is the owner's complaint about the 61
generic category icons, or about the few hero glyphs the concepts actually ornament?** Those are different
jobs with very different costs, and the owner has not said which.

---

## Task D — Review the current preview against the concepts, then continue toward the intended style

### How to produce comparable evidence

Governed captures are the only permitted fidelity evidence:

```
.venv311/bin/python scripts/capture_meridian_matrix.py \
  --app-url http://127.0.0.1:8093 \
  --output artifacts/<name>-2026-09-XX \
  --concept-dir <see trap below> \
  --fixture "<fixture id>" \
  --frozen-clock 2026-09-18T19:50:00-04:00 \
  --workspaces today plan
```

- **`:8093` is the isolated synthetic preview and the only permitted source of fidelity evidence.**
  **`:8081` is LIVE data with no frozen clock and must never produce fidelity evidence.** `:8081` has no
  Python reloader: after any change under `meridian/` or `app.py` it serves stale code until restarted
  (`(nohup .venv311/bin/python run_preview.py > tmp/preview-8081.log 2>&1 &)`).
- Viewports, DPR and themes are fixed by `MERIDIAN_VISUAL_CAPTURE_SPEC.md`: 1440×900 and 1024×768 at DPR 1;
  430×932, 390×844 and 420×912 at DPR 3; **both** themes, always set explicitly. Never inherit the OS theme.
- A recent reference set for shape: `artifacts/observatory-money-claims-2026-09-19/` — 20 capture records
  (40 PNGs: a viewport and a full-page image per record), with `overflow: 0` and `console_errors: 0` across
  all 20. Each record carries the required metadata (`concept_path`, `current_path`, `viewport`, `theme`,
  `fixture`, `frozen_clock`, `ui_state`, `full_page`, `commit`, `captured_at`) — check that yours does too.

### ⚠ The trap that will silently poison your comparison

`scripts/capture_meridian_matrix.py` has a `CONCEPT_FILES` dict mapping `today→01-today.png`,
`plan→02-plan.png`, `activity→03-activity.png`, `accounts→04-accounts.png`. **Those four filenames exist
only in the historical `design/observatory-drafts-2026-09-08/`** (verified: it has `00`–`06` including
`03-activity.png`). The newest bundle has none of them.

So both defaults are wrong for Task D, in different ways:

- Pass `--concept-dir design/observatory-extension-2026-09-18` with no `--concept-file` and the named
  concepts **do not exist there**, so the comparison cannot be made at all.
- Leave the concept dir at 09-08 and you will silently measure against a **superseded** set and draw the
  wrong conclusions.

This class of bug has already happened once here (commit `8a6e4ef`, where Activity was mapped to a
`03-activity.png` that does not exist in the 2026-09-18 bundle). **Pass the concept file explicitly for
every workspace, and write down which concept file you used for each comparison** — that is a required
field in the capture metadata anyway (`concept_path`).

### What to produce

The owner was explicit about the shape of this work: compare **every** page (Today, Plan, Activity, Accounts,
Settings) against its concept in the Track D order **structure → typography → spacing → controls →
decoration**, change **one gap at a time**, recapture after each — and **"do not chase every difference"**:
note what matters and **produce a plan of corrections** rather than attempting to reconcile everything.

So the deliverable for this task is a **written corrections plan** (in `design-qa.md` and/or a new
`docs/project/` record), with each item carrying: the page, the concept file used, the viewport/theme, the
measured difference, the intended direction, and its cost. Not a pile of edits.

Order of review is fixed. Do not start with decoration.

Also remember two rules that are easy to violate: never compare a mobile concept to a desktop capture, and
never treat a different page length or data state as a defect.

---

## Task E — Finish the in-process visual work that is already requested

These are open, already-scoped items. None of them is a redesign, and none reopens a closed decision.

| Item | State / what to do |
|---|---|
| **Today wordmark coloured dot on the second "i"** | Requested; not done. `templates/meridian/partials/wordmark.html` + wordmark styling. |
| **Dial-to-bill connector runs** | The concept draws runs from the dial to each bill row. Partially addressed in the Today work; verify against the newest concept and record what remains. |
| **A better dial pointer** | Requested; the existing pointer was flagged as improvable. |
| **Plan coverage summary still says "funded"** | The per-row stamp now reads "Reserved" but the summary still reads "…of $1,769 funded". **Left deliberately** pending the owner's wording call — it is visible in committed captures rather than quietly changed. Do not fix it without asking; it is a copy decision. |
| **`manual` is cryptic as a source label** | The owner was offered **"Your settings"** as an interim label and has not answered. Do not choose for them. |
| **Settings workspace parity in the capture harness** | `scripts/preview_observatory_dial.py`'s controller tuple covers `("shell","today","dial","plan","activity","accounts")` — **`settings` is absent**, so governed captures of Settings are not yet possible. Add it plus a synthetic fixture if your visual pass needs Settings evidence (Task D lists Settings). |

**Do not reopen:** the dial's vertical centring (`OS-041`: owner said *"I am much less concerned with the
size of the dial, I just want it evenly placed vertically"*, implemented as `align-self: center` at ≤700px)
and the day-arc start (`OS-042`, `ARC_START` = −100 so the hand clears the observatory). Both are closed and
measured; the panel-level 24-above/228-below question is recorded as a **separate** composition question.

Also recorded as rejected — do not re-propose without new evidence: mint, a darker second orange, dark ink
on the light tab label, the disabled "Needs category" control, a 186px confirm basis, lowercase
`uncategorized` prefills, an in-row ask link, and a new `<body>` attribute in `shell.js` for the FAB.

---

## Verification instruments — measured, not guessed

```bash
.venv311/bin/python -m pytest tests --ignore=tests/browser -q   # 1340 passed, 1 skipped at 6d1668c
.venv311/bin/python -m ruff check meridian/ tests/              # selects E9, F, I
node --check static/js/meridian/<file>.js
git diff --check
```

- **Environment trap:** `~/.local/bin/uv run …` is an isolated env built from production requirements. It
  cannot import Playwright and cannot run browser/capture tests, so a browser failure under it proves
  **nothing**. Use the project venv: `.venv311/bin/python -m pytest …`. `python3` on PATH is 3.9 and cannot
  import the repo at all.
- **`tests/browser` has pre-existing failures** (`OS-049`). Do not attribute them to your change by
  assumption — reconstruct a baseline in a **git worktree** at the base commit and run the same selection
  there. That is cheap, non-destructive, and it is how the 6 dial failures were shown to be pre-existing
  (identical failures and identical assertion values on a clean `b9185e3` worktree) rather than assumed.
  Clean orphan browsers with `pkill -9 -f 'chromiumdev_[p]rofile'` (bracket a character so the pattern
  cannot match your own command line).
- **Browser checks without touching live data:** the live `:8081` holds the owner's real setup and a learning
  reset written there is a real change. To exercise a page in a browser, start a throwaway instance on a
  spare port with its own temp DB and stop it afterwards (this is exactly how the OS-051 accessibility check
  was run — real `app` module, `DB_FILE` pointed at a temp path, refresh loop disabled, port 8097, removed
  after). Never present that instance as fidelity evidence.

## Task ledger

`OS-050` and `OS-051` are **done** (see their `limits` fields for precisely what was and was not
delivered). Task A above still needs an owner answer before it can start; record the answer on the relevant
task rather than in conversation. Update `MERIDIAN_OS_TASKS.json` in the same commit as any work.

## The one-line summary

**Three questions go to the owner before anything is built** — (1) Task A: is bill funding a per-bill
assignment or a derived split of the reserve? (2) Task C: are the "less ornate" icons the 61 generic
category glyphs or the few hero glyphs? (3) Task D: which concept governs Today/Plan/Activity/Accounts, now
that the newest bundle has none for those pages? **Then:** the sun (Task B) → a written corrections plan
(Task D) → the listed in-process items (Task E), one gap at a time, with governed captures at `:8093` only.
