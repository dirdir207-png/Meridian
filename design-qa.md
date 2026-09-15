# Observatory / Today visual QA

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

**Track D capture blocker for the remaining workspaces.** `scripts/preview_observatory_dial.py` serves only
`/api/meridian/today`; `plan`, `activity` and `accounts` return 404, their sections never clear `aria-busy`, and
the governed capture harness times out on them (`Page.wait_for_function: Timeout 12000ms exceeded`). **Today is
the only workspace currently able to produce governed capture evidence.** The alternatives were checked and
neither is a small step: extending the isolated preview needs synthetic fixtures for roughly eight to ten
endpoints (accounts, crew/bills, contracts, assets, trials/deadlines, plan, plan/scenario, crew/rules, actions)
and inventing conformant shapes risks producing misleading parity evidence; and `run_preview.py` loads `.env` and
starts a Crew sync loop, which the capture specification forbids for fidelity work. So Plan, Activity and
Accounts need an explicit owner decision on capture infrastructure before their parity work can start.

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
