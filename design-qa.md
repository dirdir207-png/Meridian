# Observatory / Today visual QA

## Reviewing the captures in chat (how to show images to the owner)

The owner reviews away from the machine, so evidence that requires opening a local directory is not reviewable
when it matters. The DSH web GUI renders an image when a message contains markdown image syntax with an
**absolute POSIX path**; the client rewrites it to the GUI's own same-origin `/api/file?path=…` endpoint, which
re-validates policy host-side and requires the session cookie. Because it is same-origin, the image also loads
when the GUI is reached remotely, with no extra server or tunnel.

```
![Today mobile dark](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/trackd-review/today-mobile-dark.jpg)
```

Rules that matter, taken from the client's own tests:

- The path **must be absolute** and POSIX. A relative path (`comparison.png`) and a Windows path are deliberately
  inert, and no image renders.
- Non-HTTP transports are inert, so this only works through the GUI.
- `/api/file` returns **401** without the session cookie — expected, and the reason a bare `curl` cannot verify it.

`artifacts/trackd-review/` holds every comparison downscaled to 760px wide as **progressive JPEG at quality 86**:
17 files, 71–191 KB each, 2.0 MB total. The originals are 1.2–1.7 MB PNGs, which is too heavy to load on a phone
and was the practical reason review stalled. Keep the full-resolution PNGs as the archival evidence and reference
these for review; do not treat the JPEG as the acceptance artifact, since it is lossy.

## Today — connector runs (2026-09-16, step 3 batch 3)

![Today mobile-air dark, connector runs](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-connectors-2026-09-16/today-mobile-air-dark-viewport.png)

![Today desktop dark, connector runs](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-connectors-2026-09-16/today-desktop-dark-viewport.png)

Read against concept **06**: each rim marker now carries a dashed brass run across to its own callout, ending in a
small brass stud at the row's left edge. Both ends are live geometry — the start is the marker's own projection,
the end is that event's row box — so the runs follow the data and re-anchor when the rows are replaced or either
side resizes. **Accepted as matching.** Previously the only decoration was a fixed dashed rule pinned to the list
item's midline that read no dial coordinate, and it was off at ≤900px where the concepts place these runs.

This completes the three Today items the handoff names — shaped ticket, prominent pointer, connectors tied to
actual coordinates — together with the semantic badge work its `Nuances` section requires. **Today is
presentation-complete for this pass**; remaining Track D work is Plan (02), then Activity (03), Accounts (04) and
Settings (05), and Settings is still absent from the isolated preview so no Settings parity can be claimed yet.

Evidence: `artifacts/observatory-today-connectors-2026-09-16/` (4 viewports × 2 themes), with the geometry proved
by `tests/browser/test_dial_fidelity.py::test_connector_runs_start_on_the_dial_and_end_at_their_own_row`.

## Today — shaped evidence ticket (2026-09-16, step 3 batch 2)

![Today mobile-air light, shaped ticket](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-ticket-2026-09-16/today-mobile-air-light-viewport.png)

![Today desktop light, shaped ticket, full page](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-ticket-2026-09-16/today-desktop-light-full.png)

Read against concept **06**: the ticket now carries the shaped silhouette the nuance names — scalloped side rails,
cut corners, four corner rivets and fibrous paper — supplied by the kit's `parchment-ticket.png` as a nine-slice
border image with `fill`, so the corner features stay fixed as the text reflows and the centre stays blank for
real words and money. At desktop full page the slice tiles without a seam. **Accepted as matching** for the
ticket. The previous `ticket-corners.svg` drew only four brass brackets, which is why the card read as a
rectangle before.

**Still open** in step 3: the dashed connector runs tying each rim marker to its callout. No connector geometry
exists at any width today — the existing decoration is a fixed 25px dashed rule pinned to the list item's own
midline, reading no dial coordinate, and it is switched off at ≤900px, which is exactly where concepts 01/06
place the runs.

Evidence: `artifacts/observatory-today-ticket-2026-09-16/` (4 viewports × 2 themes, plus full-page artifacts).
Sizing was measured before widening, because the fidelity suite caps the ticket at 260px: the mobile ticket was
193.6px, leaving 66.4px of headroom.

## Today — badges, pointer and callout legibility (2026-09-16, step 3 batch 1)

![Today mobile-air light, step 3 batch 1](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-step3-2026-09-16/today-mobile-air-light-viewport.png)

![Today macOS desktop dark, step 3 batch 1](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-step3-2026-09-16/today-desktop-dark-viewport.png)

Read against concept **06** in the review order: the callout column now distinguishes its events by glyph
(Electric keeps the lightning bolt, Internet resolves to the wifi glyph, Payday to the star on its mint disk)
instead of repeating one icon; each badge carries the concept's weighted anatomy — coloured disk, brass rim,
rivets; the mint selection pointer reads as a needle with a rimmed tip rather than another engraved tick; and
the callout titles are single-line at 390–430px instead of splitting mid-word.

**Accepted as matching** for badges, pointer and callout legibility. **Still open** in step 3, and deliberately
not claimed here: the dashed connector runs that tie a rim marker to its callout (no connector geometry exists
yet at any width), and the shaped evidence ticket, which still renders as a rectangular parchment card with
bracket corners rather than the supplied scalloped, riveted, fibrous silhouette.

Evidence: full-resolution captures at 4 viewports × 2 themes in `artifacts/observatory-today-step3-2026-09-16/`.
The kit's `medallion-frame.png` was measured and deliberately not used at badge scale: its 48px native stroke
collapses to ≈1.7px at a 44px badge, so the double rim cannot survive there.

## Observatory shared identity — first handoff slice (2026-09-16)

Authority corrected by the owner: the 2026-09-16 handoff and kit are the implementation specification, and the
older Design Atlas does not govern a conflicting layout. Today's composition authority is **06** (functional
dial/evidence) with **01** supporting; **02–05** govern Plan, Activity, Accounts and Settings.

This slice is handoff step 2 — shared type/header/navigation — reviewed against the shared chrome those concepts
show.

![Today mobile-air light](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-identity-2026-09-16/today-mobile-air-light-viewport.png)

![Today desktop dark](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-identity-2026-09-16/today-desktop-dark-viewport.png)

Read against the concepts in the required order (structure → typography → spacing → controls → decoration): the
wordmark now carries its apricot accent and renders in the bundled serif; the dock pairs each of the four entries
with its supplied glyph and a visible label; the current entry is lilac with a physical bar rather than colour
alone. **Accepted as matching at this review level.** No workspace geometry was in scope, so the dial, callout and
ticket differences recorded further down stay open for step 3 and are deliberately not counted as this slice's
gaps.

Evidence: `artifacts/observatory-identity-2026-09-16/manifest.json` holds the 40 governed records with the
contract metadata (concept path, viewport, DPR, theme, fixture, frozen clock, ui state, fullPage, commit);
full-resolution PNGs sit beside it; `identity-evidence.json` records the consumed kit hashes and the consuming
revision. No JPEG review copies were generated — the PNGs are retained locally and the owner reviews through the
GUI, so a lossy second copy would add weight without adding evidence.

## Track D — consolidated position and the decisions it needs (2026-09-15)

All four workspaces now have valid, informative, complete evidence, and all four have been assessed against their
governing concepts. This section states the whole position in one place, because the detail below is per-workspace
and the decisions are cross-cutting.

### Evidence infrastructure (all four workspaces)

| Capability | Status |
|---|---|
| Fixtures serving each workspace's real endpoint shapes | ✅ all four |
| Controllers loaded so a workspace actually renders | ✅ all four |
| Governed capture: 5 viewports × 2 themes, DPR-correct | ✅ 10 combinations each |
| Full-page capture | ✅ (fixed — had silently degraded to viewport-height at mobile) |
| Side-by-side concept/capture artifacts | ✅ 16 in total |
| Non-default UI state drivable and recorded | ✅ `--ui-state` / `--ui-state-selector` |
| Overflow and console errors recorded per capture | ✅ zero across every combination |

### Findings per workspace

| Workspace | Apparent gaps investigated | Real defects found | Outcome |
|---|---|---|---|
| **Today** | right-side alignment; payday amount at mobile; rim-label crop; dock occlusion; dial label contrast | **2** — dial `is-today` ink was cream-on-parchment; the dock occluded the inline advisor control | Both fixed and verified. Today has no outstanding measured defect. |
| **Plan** | "backed by undefined"; "undefined" timeline; missing allocation diagram; missing bills/income | **0** — the two `undefined` texts were my fixture's shape bugs; the allocation and bills elements exist and render | Differences are wording and diagram geometry, which the build spec classes as art direction. |
| **Activity** | four tabs vs three; no category review | **0** — the segmented control matches exactly and review rows exist; the comparison was state-mismatched | Valid comparison shows the sides correspond; differences are wording. |
| **Accounts** | missing Bill Reserve row; missing asset counts | **0** — both were the fixture's content, not the product's | Structures correspond; content comparison is limited by fixture authorship. |

**Consolidated result: two real defects, both on Today, both fixed — and no missing capability in any workspace.**
Every other apparent gap dissolved as one of four artifact classes, each of which is a way a comparison can lie:

1. **Label-grep absence** — the segmented control that "didn't exist" lived in JavaScript.
2. **State mismatch** — Activity's concept depicts the Review mode; the capture was the default Timeline mode.
3. **Fixture-shape bug** — three separate instances (`backing` as a string not an object; `commitment` vs
   `commitment_id`; `classification` as a string not an object). Each rendered literal "undefined" in a capture.
4. **Fixture-content limitation** — a fixture's accounts and assets set the ceiling on what a comparison may claim.

Rules now recorded so the remaining work does not re-learn them: read the **render site** for every fixture field
(names are not shapes); check the **state** before comparing; verify an apparent gap is not a fixture artifact
before reporting it; and never compare content the fixture itself supplied.

### What still needs you

1. **Today acceptance.** Track D's gate is owner-visible acceptance. The record is above; comparison images are in
   `artifacts/today-dock-fix-2026-09-15/`. On sign-off, Track D advances to Plan.
2. **Which art-direction differences to match.** Across Plan, Activity and Accounts the remaining differences are
   copy (headlines, button labels), diagram geometry (map vs bar), and composition — all named by the build
   specification as art direction that "may be inconsistent". Matching them is a product decision, not a fidelity
   fix, and doing it unilaterally would be inventing product language from a mock.
3. **Accounts content comparison** — aligning the fixture to the concept's accounts and asset counts would make the
   comparison show a match, but only because I authored the fixture to match. That is circular and is deliberately
   not done. Structure and styling are what this comparison can legitimately support.
4. **Emitter semantics** (separate thread, not Track D): deviations 2–3 in
   `MERIDIAN_STATUS_EMITTER_VERIFICATION.md` — whether `queues`/`phase`/`tracks` should carry real values or the
   contract doc should be narrowed to what the emitter does.


## Accounts — the comparison is CONTENT-confounded (Track D, 2026-09-15)

Reading `comparison-accounts-mobile-dark.png`, several apparent gaps turn out to be **the fixture's content, not the
product's**, and this is a distinct failure mode from the label-grep and state-mismatch ones already recorded.

The concept shows three account rows — Free to Spend $248.50, Bill Reserve $1,320.00, Emergency Fund $2,200.00 —
and an "Assets & documents" ticket reading "2 warranties · 1 contract". The capture shows two accounts (Checking,
Emergency fund) and no asset counts. The obvious reading is "the product lacks Bill Reserve and asset counts".

That reading is false. The Accounts fixture supplies **two** accounts and **no** assets, so the number and names of
rows, and any asset count, are determined by the fixture rather than by the product. Verified directly against the
served payload: `groups` = Cash[Checking], Savings[Emergency fund]; no assets. **A fixture's content sets the
ceiling on what a comparison may claim**, and row counts and item labels are exactly the things it controls.

Fixture-independent differences, which are the only ones this comparison can legitimately support:

| Concept | Current |
|---|---|
| "Accounts" · "Your financial constellation." | "Structure without provider clutter." · longer explanatory subline |
| One paper-ticket summary — "Cash across accounts $3,768.50" | Two separate cards — AVAILABLE CASH $248.50 and LIABILITIES $0.00 |
| Per-row chevron and illustrated circular icon | Per-row "Activity" action |
| A status strip: Crew · Connected · Updated 9:42 AM · Refresh | CONNECTION HEALTH card with Refresh now and View connections |

Both sides do carry account rows with provider and balance, a refresh affordance, and an assets/documents section,
so the structures correspond; the differences above are composition and affordance, not missing capability.

**To compare content at all, the fixture must be authored to mirror the concept's data** — the same accounts and the
same asset/contract counts. Doing that with values that are obviously synthetic is legitimate; using them to claim
product parity without that alignment is not. Until then, Accounts parity is assessable for structure and styling
only, and the honest statement is narrower than "the concept has three rows and the product has two".

## Activity — the captured comparison is state-mismatched, so it is INVALID (Track D, 2026-09-15)

Reading `comparison-activity-mobile-dark.png`, the concept and the current implementation looked
structurally different: the concept shows category review (per-row "Suggested category: Groceries",
"Confirm category", "Change"), the capture shows a plain ledger with "Unassigned" and no actions. Two
apparent gaps were checked against source, and **both dissolved**:

- **"The current has four tabs, the concept three."** False. The segmented control is exactly
  `Timeline | Review | Patterns` — the concept's three. "Filter" is a separate toggle button
  (`data-filter-toggle`) that happens to sit beside the segmented control, and the reading conflated them.
- **"The current has no category review."** False. `activity.js` renders review rows with
  `m-review-category`, an orange attention dot, the suggested category, ranked `category_options` and a
  classification confidence — the concept's exact content. It is reachable via
  `data-activity-mode="review"`.

**The real problem is the comparison itself.** `activity.js` defaults to `mode: "timeline"`, and the
capture harness records a fixed `ui_state` of `"<workspace>:default"` and never drives a workspace's own
modes or tabs. So every Activity capture is the Timeline mode while the governing concept depicts the
**Review** mode. The two columns are different states of the same product, and the specification is
explicit that only matching state may be compared.

That makes the Activity comparison **evidence of nothing** — not evidence of a gap, and not evidence of
parity. The same risk applies to any workspace whose concept depicts a non-default mode, so this is a
pipeline defect rather than an Activity defect.

The fix is bounded: let the harness drive a named UI state before capture (for Activity, select
`[data-activity-mode="review"]`), and record the state actually captured instead of the constant
`"<workspace>:default"`.

**That fix is now implemented and the valid comparison exists.** `capture_meridian_matrix.py` takes
`--ui-state` (the label recorded) and `--ui-state-selector` (a selector clicked before capture, which raises
if it matches nothing), and it records `ui_state` and `ui_state_selector` per capture. Activity re-captured as
`activity:review` into `artifacts/activity-review-parity-2026-09-15/` with
`comparison-activity-review-mobile-dark.png`.

Reading the matched comparison, **the two sides correspond**: both show a review card per transaction carrying
merchant, amount, the category suggestion, a confidence figure, and an approve/change action pair. The
remaining differences are wording and density, not structure:

| Concept | Current |
|---|---|
| "Suggested category: Groceries" as an explicit line | "Income · 95% confidence" on one line |
| "Crew • Free to Spend" account/budget meta per row | not shown in the review row |
| "Confirm category" · "Change" | "Approve category" · "Correct" |
| "3 categories to review" count header | no count; batch checkbox instead |

So Activity is **not** missing the review capability, and the earlier apparent gap was entirely an artifact of
comparing two different states. The remaining differences are again wording, which the build specification
classes as art direction.

**A third fixture-shape bug was found and fixed in the process.** The first Review capture showed "0%
confidence" and no category because the fixture set `classification` as a string while `activity.js` reads
`transaction.classification?.category` and `?.confidence` — an object. After the fix the capture reads
"Income · 95% confidence". That is the same mistake, in the same session, after I had already written the rule
against it, which is a fair measure of how easy the mistake is: **read the render site, not a sample of names.**


## Plan — gap assessment against `02-plan.png`, decision-ready (Track D, 2026-09-15)

Plan evidence is now valid on both axes that were missing: **informative** (fixtures serve data and the
controller loads) and **complete** (full-page capture works, mobile full page 1290×8427). The gap list below is
therefore read from rendered content, not from empty states or a truncated page.

Three apparent defects found in the capture were investigated and **none is a product defect**:

| Apparent defect | Verdict |
|---|---|
| "backed by **undefined**" on all four commitment cards | **My fixture's bug.** `plan.js:484` renders `commitment.backing.name`, so `backing` is an object; the fixture passed a string. Fixed. |
| "**undefined**" as the destination on every NEXT 30 DAYS row | **My fixture's bug.** `plan.js:226` renders `event.commitment`; the fixture supplied `commitment_id` and `detail`. Fixed. |
| "Next funding Sep 11" footer | **Intended.** `plan.js:616` renders `summary.next_due`. Not a defect. |
| "The scenario preview could not be loaded" | **Harness gap.** `plan.js` posts to `/api/meridian/plan/scenario`, which the isolated preview does not serve. Needs a scenario fixture before that section can be assessed. |

After the fixture fix the full-page capture contains the literal text "undefined" **nowhere**, which is the check
that confirms the first two.

What remains is a set of **design differences, not defects**:

| Concept (art direction) | Current implementation |
|---|---|
| "Give every dollar a destination." | "Every dollar has a next job." |
| Orange "Add a bill or goal →" | "+ New commitment" (plus a secondary "New autopilot rule") |
| **Unfolded-map** allocation diagram | Horizontal allocation **bar** + text legend — labels and amounts match exactly (Bills $1,320 · Goals $200 · Available $248.50) |
| "Upcoming bills" panel | "COMMITMENTS" cards with FUNDED/NEXT columns and row actions |
| "Next income" ticket | "FUNDING SCHEDULE · Next paycheck" |
| — | Extra sections: September coverage, Scenario preview, Plan memory |

**Why these need a direction rather than a fix.** The build specification says of the drafts: *"Treat images as
art direction, not executable financial specifications. Mock amounts, dates, status labels, arbitrary icon
choices, chart geometry, and generated text may be inconsistent."* Headline copy, button labels and diagram
geometry are named in that list. So "make the headline match" or "replace the bar with a map" is a **product and
design decision**, not a fidelity defect — and doing it unilaterally would be inventing product language from art
direction, which is the same class of error as the false gaps recorded above.

What is actionable without that direction, in the review order, is the **allocation presentation**: the concept
makes the allocation the centrepiece directly under the tabs, while the implementation places "Where the money
sits" fifth, after coverage, funding schedule and four commitment cards (roughly 5,000px down at mobile). Its
labels and amounts already match the concept exactly, so the remaining difference is prominence and placement —
layout, the first item in the review order, with no copy change and no data change.

## Plan — preliminary analysis, capture-gated (Track D, 2026-09-15)

Recorded so Plan parity can start immediately once its capture path exists. **This is source inspection, not
capture evidence**, and it is explicitly weaker: it can establish what markup and controllers exist, and nothing
about how the surface renders.

Reading the governing concept `02-plan.png`: tall portrait composition — wordmark and Settings; a "Plan" heading
with the subtitle *"Give every dollar a destination."*; a three-tab segmented control (Plan | Rules | Crew); a
central **unfolded-map allocation diagram** with three destinations (Bills $1,320 Reserved · Goals $200 Reserved ·
Available $248.50 Available to plan); an **Upcoming bills** panel with three reserved rows; a ticket-shaped **Next
income** card; a large orange **Add a bill or goal** button; and the four-item dock with Plan selected.

What the current implementation actually contains:

- the segmented control **exists and matches** — `plan.js` `setupPlanSegs()` drives
  `data-plan-seg` / `data-plan-view` / `data-plan-view-pane`, and the template renders exactly `Plan`, `Rules`,
  `Crew`;
- a "New commitment" primary action with a `+` icon where the concept has "Add a bill or goal" with `→`;
- an editorial headline **"Every dollar has a next job."** where the concept has "Give every dollar a
  destination.";
- twelve labelled sections (Coverage, Funding schedule, Commitments, Where the money sits, Next 30 days,
  Scenario preview, Document review, No longer returned, Crew capabilities, Crew actions, Crew mutation coverage,
  Plan memory) against the concept's focused four-block composition.

**A false-gap trap worth recording, because I fell into it first.** Grepping the concept's labels against the
template, `plan.js` and `plan.css` returned zero hits for "Give every dollar a destination", "Upcoming bills",
"Next income", "Add a bill or goal", "Available to plan" and "Reserved" — which reads as six missing elements. It
is not. The segmented control, which the same method reported absent, **exists** but lives in JavaScript rather
than the template; and the concept's "Upcoming bills" and "Next income" may well be the implementation's
"Commitments" and "Next 30 days" under different names. **Label-level absence is not feature absence**, so this
records the shape of the difference and nothing more. Whether it is a parity gap is a capture-and-compare
question, and it stays open until Plan can be captured.

That also sets the scope expectation honestly: Plan's differences look like **naming and presentation** across a
much denser layout, not a missing architecture — but that claim is exactly the kind this project refuses to make
without a capture, so it is recorded as the hypothesis to test, not as a finding.

**Plan captures are now informative — the fixture prerequisite is DONE.** The isolated preview gained a Plan
fixture and, critically, loads `plan.js`. Both halves were needed and the second was the one that mattered: the
endpoints alone changed nothing, because a workspace renders only if its controller is loaded, and the preview
had been injecting only `shell`, `today` and `dial`. With `plan` added, the previously-empty capture now shows
real rendered content:

```
SEPTEMBER COVERAGE 86% · $1,520 of $1,769 funded · Projected complete by Sep 16
FUNDING SCHEDULE · Next paycheck · September 16 · $1,660
COMMITMENTS · Electric BILL · ...
```

"Nothing funded yet." and "No funding scheduled yet." are gone. Evidence:
`artifacts/plan-parity-fixtured-2026-09-15/` — 10 combinations, zero overflow, zero console errors.

So Plan parity analysis can now run against rendered content rather than empty states, which is what the previous
round established was necessary. The fixture is derived field-by-field from what `plan.js` reads (see the shape
recorded below), and its values echo the governing concept's own figures so a capture can be compared to
`02-plan.png` directly.

The generalisable lesson, now demonstrated twice: **a workspace capture is evidence only if the workspace's
controller is loaded and its data is served.** Empty states in a capture are indistinguishable from missing
features, and both are indistinguishable from an unloaded controller.

Reading the mobile capture against the concept exposed a trap of the same family as the label-grep: the capture
shows **COVERAGE**, **FUNDING SCHEDULE**, **COMMITMENTS** and **WHERE THE MONEY SITS**, all rendering *empty*
states ("Nothing funded yet.", "No funding scheduled yet."), because the preview serves no data for Plan. The
concept's unfolded-map allocation diagram, its bills panel and its next-income card therefore look absent, when
in fact `templates/meridian/partials/plan.html` **has** the allocation element (`m-allocation-bar` +
`m-allocation-legend`) and the timeline — they are simply unpopulated. **Absence in a no-data capture is not
absence of a feature**, exactly as a label miss is not a missing feature. Any gap list read off these captures
today would send the work at things that already exist.

So Plan's real prerequisite is fixture data in the isolated preview. The shape is small and derivable from the
consumer rather than invented — `plan.js` requires `/api/meridian/plan` and treats
`/api/meridian/funding-rules` as optional, and reads exactly these top-level keys:

`summary` (`headline`, `total`, `total_target`, `total_funded`, `unfunded`, `coverage_ratio`, `captured`,
`missing`, `next_due`, `first_shortfall`) · `allocation` (`cash_total`, `segments: [{label, amount}]`) ·
`commitments: [{id, name, type, target, funded, unfunded, due_date, target_date, backing, biller_status,
crew_bill_id, invoice_evidence}]` · `next_paycheck` · `timeline` · `absent_bills` · `document_discrepancies`.

Two endpoints, not the eight-to-ten previously estimated — that estimate was for every workspace at once. Note
also that only the Plan capture is affected this way; Today's captures are unaffected because the preview serves
Today data.

The construction rule for those fixtures: derive every field from what the consumer reads, never invent a shape
the UI does not consume, and keep the values clearly synthetic. A fixture that satisfies the consumer is
evidence; a fixture that guesses is a new source of false gaps.

## Today — acceptance summary (Track D, 2026-09-15)

**Status: awaiting owner acceptance.** Everything below is measured from the live DOM or captured under the
governed matrix; nothing here is inferred from an image.

**Captured evidence.** `artifacts/today-parity-2026-09-15/` — 10 captures, all five governed viewports (1440×900
DPR 1, 1024×768 DPR 1, 430×932 DPR 3, 390×844 DPR 3, 420×912 DPR 3) × light and dark, 20 screenshots, at
`commit 2c7af918`, concept `01-today.png`, fixture `synthetic-electric-internet-payday`, frozen clock
`2026-09-08T13:42:00Z`. **Zero horizontal overflow and zero console errors in all ten combinations.**

**Gaps from the roadmap, re-tested:**

| Roadmap item | Verdict |
|---|---|
| Right-side alignment | **Not reproducible.** Layout box 251–1339 in 1440 → 101px each side, symmetric. The single-column desktop stage is deliberate and documented in `observatory.css`. |
| Payday amount tight at mobile | **Not reproducible.** clientWidth 110 / scrollWidth 110 at 420, 430 and 390. |
| Inline Virgil control vs bottom nav | **Fixed.** Was `OCCLUDED` at 420 (`m-nav-item`) and 430 (`m-nav`); after the shell change the verdict is `PAINTED_AND_HITTABLE` at both, and `NOT_PAINTED` at 390. |
| Light-theme foregrounds | **Inspected; today-marker defect found and fixed.** Primary text legible. The `is-today` day label was cream on parchment and is now dark ink (pixel-verified). The accompanying "lower rim labels obscured by artwork/crop" claim was **measured and not reproduced**. |

**The defect that was open, now closed.** The "Ask Virgil about this plan" control was painted and then covered
by the dock in the initial mobile viewport — 7046 px² covered at 420 and at 430. It was never a dead control
(after scrolling it cleared the dock and hit-tested to itself), and the governing concept contains no inline
advisory control in that position at all. The shell change described above removes the occlusion; the verdict is
now `PAINTED_AND_HITTABLE` at 420 and 430 and `NOT_PAINTED` at 390.

A second finding, from inspecting the light-theme capture directly (which the roadmap requires, because a
computed-ratio probe is not valid over gradient and parchment backgrounds). Primary light-theme text is legible,
but two things are marginal: the small grey dial labels sit at low contrast against the parchment, and the lower
dial rim labels (`8 / TUE`, `16 / WED`) are partially obscured by the observatory artwork and by the bottom
viewport crop. This is distinct from the dock overlap and was not previously on the roadmap's list.

**Fix applied for the today marker, and the verification disagreed with itself — recorded as such.** The
`is-today` day label was cream (`#eee4cf`) with a dark text-shadow, set by a later concept-fidelity pass, while
its neighbours were `rgba(32,38,59,0.82)`. The dial rim is parchment in *both* themes, so cream was wrong in
both. It now uses the dark engraved ink `#5b3d16`, which also restores the emphasis the earlier rule
(`color: #5b3d16`, size 13px) had intended.

Verifying it exposed two traps worth keeping:

1. **A theme selector that never applies.** The first attempt used
   `html[data-theme="light"] .obs-dial-day-label.is-today`, which verified clean in a probe because the probe set
   `document.documentElement.dataset.theme` by hand. At capture time the attribute is whatever `theme.js` derives
   from `prefers-color-scheme`, so the rule silently did nothing. Verified fixing the *base* rule instead, which
   is theme-independent because the rim is parchment either way.
2. **The vision reading and the computed style contradicted each other**, so neither was treated as truth. The
   pixels settled it: in the label region, cream pixels went **27 → 0** and dark-ink pixels **466 → 529** between
   baseline and after-fix captures. The cream glyph is genuinely gone.

The vision reading still described "8 TUE" as washed out *after* the fix, so the obvious explanation was that the
dial artwork plate carries its own baked day marker. **That was tested and disproven:** `.obs-dial-art` is
`static/img/meridian/observatory/dial-plate.png` (1254×1254), and it contains no text, numerals or weekday
abbreviations at all — only decorative celestial texture and tick marks. So the residual reading is almost
certainly a limitation of reading 10px type from a raster (the model itself recorded that it could not
confidently transcribe the characters), not an outstanding defect. The measured state is: the cream glyph is
gone, dark ink sits on parchment, and the label region has no cream pixels left. Left as a low-confidence item
for the owner's eye rather than reclassified as fixed or as still-broken.

Evidence: `artifacts/today-labels-fix-2026-09-15/` (10 captures, zero overflow, zero console errors).

**The "lower rim labels are cropped" claim was measured and does not reproduce.** All four day labels are inside
the viewport at desktop and at 420: `8 TUE` and `16 WED` sit at viewport y=771 in a 900px viewport, and every
label reports `inViewport: true`. The page scrolls (document height 2521 at desktop, 1927 at 420), so the dial's
lower 66px, which extends below the desktop fold, is reachable — content below the fold in a scrollable page is
not a defect, and the build specification explicitly allows the tall compositions to scroll on real devices.

This makes **two vision readings on this dial that measurement contradicted** (the "8 TUE" wash-out after the fix,
and now the cropped rim labels). Both are recorded rather than silently dropped, and they set the working rule for
this surface: the raster readings of 10px dial type are unreliable in both directions, so a dial-label claim
needs pixel or computed-style confirmation before it is acted on — and equally before it is dismissed.

A process note worth keeping: the light-theme row of this table first read "verified, no problems" before the
capture had actually been inspected. It was rewritten only after reading the image. That is the exact failure
mode the roadmap warns about — a clean-looking row that was never looked at.

**A validated fix exists and is now SHIPPED, with one honest limit.** Making the mobile shell `height: 100svh`
with the canvas as its own scroll container flips the measured verdict from `OCCLUDED` to
`PAINTED_AND_HITTABLE` at 420 and 430 and `NOT_PAINTED` at 390. It was withheld twice while only Today could be
captured; the blocker was worked around by verifying the level the change actually affects. The change alters
**shell geometry** (shell / canvas / dock), not workspace content, so it can be measured on every workspace even
without their fixture data:

| Workspace | nav position | shell height | doc scrolls | horizontal overflow | dock overlaps canvas |
|---|---|---|---|---|---|
| today | static | = viewport | no | 0 | no |
| plan | static | = viewport | no | 0 | no |
| activity | static | = viewport | no | 0 | no |
| accounts | static | = viewport | no | 0 | no |

All three mobile viewports (420/912, 430/932, 390/844), every workspace: the dock is a static grid row at the
viewport foot, the canvas owns scrolling, `nav_overlaps_main` is false, and horizontal overflow is zero. Nothing
in the Meridian client listens for `window` scroll, and `scrollIntoView()` walks up to the nearest scrollable
ancestor, so the scroll-container change has no other client dependency.

**What gates this change, and what could not be run.** The browser suite was run for the first time against this
work: `tests/browser` gives **24 passed, 63 skipped**, and every skip is the same environmental gate —
`APP_URL is required for browser tests`. `tests/browser/test_meridian_shell.py` and
`tests/browser/test_responsive_parity.py` are both entirely in that skipped set, and they are precisely the tests
that would cover a shell change. They authenticate through `/api/auth/login`, so they cannot be pointed at the
isolated synthetic preview, which deliberately has no auth.

The relevant one is worth naming exactly: `test_responsive_parity.py` parametrises 390×844 and 430×932 and asserts
that accounts has no horizontal overflow. That is the same property this shell change could have broken, and it
could not be executed. It is covered instead by direct measurement — horizontal overflow 0 across all four
workspaces at 420, 430 and 390 — which is the same assertion made by a different route. The desktop shell tests
would not have exercised the change in any case, since it lives inside `@media (max-width: 900px)`.

So the change rests on: geometry measurement across 4 workspaces × 3 mobile viewports, a governed Today capture
with zero overflow and zero console errors, the full non-browser suite (1119 passed, 1 skipped), and the browser
suite's 24 runnable tests. The one suite that would gate it directly needs a live authenticated app, which is an
environmental limitation rather than a gap in this change.

**Track D capture status — the earlier "Today only" claim was WRONG and is corrected here.** An earlier version of
this document stated that Today was the only workspace able to produce governed capture evidence from the isolated
preview. That was inferred from a timed-out four-workspace run and never tested per workspace. Tested individually:

| Workspace | Result |
|---|---|
| today | captures (10 combinations) |
| plan | **captures** — 10 combinations, `02-plan.png` |
| activity | **captures** — 10 combinations, `03-activity.png` |
| accounts | **does not settle** — 0 captures |

The timeout came from **accounts alone**, and the cause is specific: `templates/meridian/partials/accounts.html`
hardcodes `aria-busy="true"` on its root, and the preview injects only `shell`, `today` and `dial` modules, so the
accounts controller that would clear it is never loaded. Plan and Activity set `aria-busy` programmatically in
their controllers and clear it in a `finally` block, and neither depends on a template-level busy attribute, so
they settle even though the preview serves no data for them.

Governed evidence for the two newly-capturable workspaces is in `artifacts/plan-activity-parity-2026-09-15/` —
20 captures, both concepts mapped correctly, all five viewports, **zero horizontal overflow and zero console
errors**. The lesson is recorded rather than the fix alone: a claim about what a harness can do is itself a
claim that needs testing, and inferring "impossible" from one aggregate timeout cost several rounds of work that
was available all along.


## September 15 governed regeneration and measurement pass (Track D)

The previous matrix (`artifacts/dial-refinement-2026-09-12/today-final-2/`) was captured at `5ed361e`. The
capture specification says existing screenshots are historical unless regenerated, and the tree has since
gained the cadence consolidation, the transfer-readback verifier and the status emitter, so the evidence was
regenerated rather than reused.

**Fresh governed matrix: `artifacts/today-parity-2026-09-15/`** — 10 captures (all five governed viewports ×
light and dark), 20 screenshots, recorded at `commit 2c7af918` with `concept_path` `01-today.png`, fixture
`synthetic-electric-internet-payday` and frozen clock `2026-09-08T13:42:00Z`. **Zero horizontal overflow and
zero console errors in every one of the ten combinations.** Capture now also records `overflow` and
`console_errors` per capture, because horizontal overflow is the primary responsive defect signal and should
be measured rather than inferred from an image.

Producing this required a tooling fix, recorded because it was a real blocker: the governed capture script
called `login()`, but the isolated synthetic preview deliberately has no `/login` route, and it always
captured all four workspaces while that preview renders Today only. The only target that has a login is
`run_preview.py`, which loads `.env` and starts a Crew sync loop — unusable for fidelity work, because the
specification requires fixtures only and forbids live bank data. The script now takes `--skip-login`
(isolated synthetic preview: no auth, no credentials, no provider call) and `--workspaces`.

### Measured gaps (probes in `artifacts/today-parity-2026-09-15/probes/`)

Geometry was measured from the live DOM rather than estimated from pixels, because the pixel estimate
disagreed with the DOM.

| Roadmap gap | Measurement | Status |
|---|---|---|
| Right-side alignment on Today | Layout box 251–1339 in a 1440 viewport: **101px each side, symmetric**. The single-column desktop stage is deliberate (`observatory.css` documents it: "Today becomes a single Observatory stage on wide screens"). Each event card is 384px and its body reaches the right edge (326px). | **Not reproducible as a gross defect.** The residual is that the card's compact left-aligned stack (which matches the concept) leaves unused width inside a 384px card. |
| Payday amount tight fit at mobile | `+$1,660.00` measures `clientWidth 110 / scrollWidth 110` — **no overflow** — at 420, 430 and 390. | **Not reproducible.** |
| Inline Virgil control overlaps bottom nav at mobile | `obs-control` bottom vs sticky `nav.m-nav` top: **−41px at 420**, **−23px at 430**, **−79px at 390**. | **Reproduced.** The control sits behind the dock on first paint at every mobile viewport. |

A caution recorded for the next pass: the concept's callouts stack date/name/amount/status **left-aligned**,
and the vision reading of `01-today.png` confirms the amounts are deliberately *not* right-aligned. So
"fixing" the unused card width by right-aligning amounts would move the implementation **away** from the
governing concept — the trap Track D's review order exists to avoid.

Outstanding decision, not taken unilaterally: the dock overlap is structural. The dock is a `position: sticky`
grid row pinned to the viewport bottom, so mid-scroll content passes beneath it by design; the inline advisory
control is an addition the concept does not contain. Candidate fixes are (a) make the canvas the scroll
container so the dock reserves its own row and never overlays, or (b) drop the inline advisory control at
mobile. (a) touches the shell and therefore every workspace; (b) is small but removes a control. Both are
owner-visible choices, so the measurement is recorded rather than a fix improvised.

**A measurement error in this pass was found and corrected, and it matters.** The first overlap probe waited
only for `.obs-dial-center-amount`, which exists *before* the dial's event rail finishes rendering. The page
kept growing after the measurement, so two runs of the same probe disagreed by ~250px on the same element
(y=566 vs y=814 at 390 wide). The "reproduced" figure was therefore not trustworthy when first reported.
`probes/measure_nav_overlap_settled.py` waits for the rail to be populated (`.obs-event-item`), for
`document.fonts.ready`, and then samples twice 600ms apart, asserting the document height is unchanged. With
that gate the collision reproduces reliably — **−41px at 420, −23px at 430, −79px at 390**, `stable: true`,
3 events rendered — and is recorded in `measurements-nav-overlap-settled.json`.

**The occlusion question is now settled definitively, and it is a real defect.** `probes/probe_visibility.py`
computes the control's *painted* portion (its rect ∩ the scrolling container's visible box) and hit-tests only
that portion with `document.elementFromPoint`. Baseline verdict at all three viewports is
**`OCCLUDED (painted then covered)`** — the element returned at the painted centre is the dock, not the control:

| Viewport | control y | painted | element actually on top |
|---|---|---|---|
| 420 | 844–888 | 7046 px² | `m-nav-item` |
| 430 | 846–890 | 7046 px² | `m-nav` |
| 390 | 814–858 | 4869 px² | `design-preview-banner` |

Two traps were hit and are recorded so they are not repeated. First, `.obs-control` is **not unique**: the dial
renders three more of them ("Previous day", "Next day", "Back to today") at y=596, so an early
`querySelector('.obs-control')` measured the wrong element and produced a false "not occluded". The advisor
control must be selected as `[data-open-advisor].obs-control`. Second, at 390 the occluder is the
`design-preview-banner` — a harness artefact, not the product — so only the 420 and 430 results describe real
product behaviour.

**Fix (a) demonstrably removes the occlusion on Today, and is still not shipped.** Re-applied and re-measured
with the visibility probe, the verdict changes from `OCCLUDED` to `PAINTED_AND_HITTABLE (not occluded)` at 420
(painted 545 px², scroller now `m-main`, top element `obs-control`) and at 430 (3415 px²), and to
`NOT_PAINTED (below fold)` at 390. So the earlier "no measurable improvement" reading was an artefact of a
rect-only probe, exactly as suspected.

It is nevertheless reverted, for a reason that is itself a Track D finding: **the change is cross-cutting and
cannot be verified on the other three workspaces.** `scripts/preview_observatory_dial.py` serves only
`/api/meridian/today`; `plan`, `activity` and `accounts` return **404**, so those workspace sections never clear
`aria-busy` and the governed capture harness times out on them (`Page.wait_for_function: Timeout 12000ms
exceeded`). Altering the mobile scroll container for every workspace while being able to test only one of them
is not a defensible trade for a cosmetic at-rest occlusion, so the fix is recorded as validated-on-Today and
pending verification elsewhere.

What remains true regardless: after `scrollIntoView({block:'center'})` the control clears the dock
(`clearsDock: true`) and hit-tests to itself, so it is **reachable** — the defect is at-rest occlusion on first
paint, not a dead control.

**Blocker for the rest of Track D, recorded now:** Plan, Activity and Accounts cannot produce governed capture
evidence from the isolated synthetic preview until that preview serves their data (or a different
fixture-only target is built). Today is the only workspace currently capturable.

## September 12 phone alignment correction

The three-event baseline below missed the tall-list case. The owner's reported blank space was reproduced with twelve invented events and corrected: dial top alignment, bounded keyboard-scrollable callouts, full-width mobile text/amounts, and controls in a separate row. Regression and preview-template refresh checks pass within a **71-test** focused run. `artifacts/dial-refinement-2026-09-12/alignment-dense-final/` contains the fresh 16-image matrix, with zero page overflow/errors; mobile images were inspected. The local preview was reloaded and its served assets verified. See `docs/project/DIAL_ALIGNMENT_FIX_2026-09-12.md` for scope and runtime evidence. Older broad-fidelity observations below are retained, not silently treated as fixed by this incident correction.

Source: `design/observatory-drafts-2026-09-08/06-interactive-observatory-vision.png`.

Implementation: production Today template and dial/Today/shell controllers in the isolated synthetic preview
(`.venv311/bin/python scripts/preview_observatory_dial.py`, http://127.0.0.1:8093/). Synthetic data only —
never the daily banking runtime, never credentials, never a database.

## Verified this pass (2026-09-12, at commit `5ed361e`)

- **Fresh governed matrix: `artifacts/dial-refinement-2026-09-12/today-final-2/`** — 16 captures, four
  viewports × two themes × viewport/full-page, **zero horizontal overflow, zero page errors**, recorded at
  `commit 5ed361e` with `source_dirty: false`. This is the first matrix taken *after* the compact-card/spacing
  adjustment, so it supersedes `today-final/` for that change.
- **Composition matches the owner's direction**: large dial on the left, event callouts on the right, evidence
  ticket underneath; **safe-to-spend prominent** with separate horizon ("Available until September 16") and
  source ("Crew · observed Sep 8, 9:42 AM") lines.
- **Moon asset is in the composition** — `moon-engraving.png`, applied through `.m-observatory-moon` in
  `dial.css`, with the runway line ("You have about 14 days of runway."). It is a CSS background rather than an
  `<img>`, so an image-tag scan reports it missing; it is present and rendered.
- **Focused suite independently reproduced: 68 passed** — `test_dial_fidelity` 12, `test_dial_js` 22,
  `test_capture_contract` 7, `test_meridian_workspace_invariant` + `services/test_today` 27. Ruff clean;
  `git diff --check` clean.

## Remaining gaps (measured, unresolved)

1. **Payday amount is a tight fit in the callout.** `+$1,660.00` sits in a 79px box and reports
   `scrollWidth > clientWidth` at `mobile` and `mobile-small`, in **both themes**. Not visibly truncated today
   (overflow is not hidden), but it is the longest value that currently fits, and the one to watch as amounts
   grow. This is the "callout amount fit" item.
2. **Inline Virgil control overlaps the bottom navigation on mobile.** Visual pass records
   `Ask Virgil about this plan` partially truncated by the bottom navigation panel. No current test covers this.
3. **Light-theme foregrounds: not verified — and not verifiable by the computed-ratio method used here.**
   A contrast probe reported 19–24 "low contrast" elements in light theme. Inspection showed the figure is an
   artifact on both sides: text inside `[hidden]` other-workspace partials was being measured, and the backdrop
   walker cannot see `linear-gradient` or parchment backgrounds, so the nav's ivory-on-dark and the ticket's
   navy-on-parchment — correct, readable pairings — were reported at ~1.1:1. The light/dark asymmetry is a
   by-product of which elements happen to sit on gradients. **Resolve this by inspecting the capture, not by a
   computed ratio.** A candidate fix (mapping the two light-theme small-caps label rules onto `--m-ink-muted`)
   was applied and then reverted as unverified.

## Environment note

Browser verification can silently stall in two ways, both worth knowing before concluding a test has failed:

- `playwright` and its Chromium build live in `.venv311` (declared in `requirements-dev.txt`), **not** in the
  uv-isolated environment built from `requirements.txt`. A production-requirements runner cannot execute the
  browser or capture tests at all.
- An interrupted browser run leaves orphan Chromium processes behind, and later runs then hang. Clear them with
  `pkill -9 -f 'chromiumdev_[p]rofile'` (bracket the pattern so it cannot match your own command line).

## Status

Focused suite green and the post-adjustment matrix captured; composition verified against the owner's stated
direction. **Not claimed:** light-theme contrast verification, broader application acceptance, live served-app
acceptance, or any deployment. Remaining bounded work: resolve or explicitly accept the two measured gaps
above, and inspect light-theme foregrounds visually.
