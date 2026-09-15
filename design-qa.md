# Observatory / Today visual QA

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
| Inline Virgil control vs bottom nav | **Real, cosmetic, at rest.** `OCCLUDED` at 420 (`m-nav-item`) and 430 (`m-nav`); reachable by scrolling. |
| Light-theme foregrounds | **Inspected; one new finding.** Primary text is legible. But in the light theme the small grey dial labels have marginal contrast, and the lower dial rim labels (`8 / TUE` and `16 / WED`) are partially obscured by the observatory artwork and the bottom viewport crop. See below. |

**The one open defect.** The "Ask Virgil about this plan" control is painted and then covered by the dock in the
initial mobile viewport. Measured occlusion: 7046 px² covered at 420, 7046 px² at 430. It is **not** a dead
control — after scrolling it clears the dock and hit-tests to itself — so this is an at-rest occlusion of one
control, and the governing concept contains no inline advisory control in that position at all.

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

The vision reading still described "8 TUE" as washed out *after* the fix, and the pixel data says the cream text
is gone — so the most likely explanation is that the dial **artwork plate carries its own baked day marker**, and
the model was describing that rather than the HTML label. That is unfixed and is the next thing to check: if the
art plate contains baked day text, no CSS change will remove it, and it must be corrected in the artwork or
masked. Recorded as an open question rather than a conclusion.

Evidence: `artifacts/today-labels-fix-2026-09-15/` (10 captures, zero overflow, zero console errors).

A process note worth keeping: the light-theme row of this table first read "verified, no problems" before the
capture had actually been inspected. It was rewritten only after reading the image. That is the exact failure
mode the roadmap warns about — a clean-looking row that was never looked at.

**A validated fix exists but is not shipped, and the reason is a decision only you can make.** Making the mobile
shell `height: 100svh` with the canvas as its own scroll container flips the measured verdict from `OCCLUDED` to
`PAINTED_AND_HITTABLE` at 420 and 430 and `NOT_PAINTED` at 390 — it demonstrably works on Today. It is withheld
because it changes the scroll container for **every** workspace while only Today can currently be captured (see
the blocker below), so it cannot be verified across the app. Options: (a) accept the change and let the other
workspaces be verified as their capture support lands, (b) relocate or drop the inline advisory control at
mobile — smaller, and raises fidelity since the concept has no such control, but it removes a control, or
(c) accept Today as-is with the defect recorded.

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
