# Observatory / Today visual QA

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

**Fix (a) was attempted and reverted — but the honest reason is narrower than "it did not work".** The change
made the mobile shell `height: 100svh` (instead of `min-height`) with `overflow: hidden`, gave `.m-main`
`overflow-y: auto`, and dropped the dock's `position: sticky` to `static`. The measured overlap did not move
(−41/−23/−79, identical) — because a bounding-box probe cannot see clipping: occlusion behind an opaque bar and
clipping at the same coordinate produce identical rects. So the correct statement is that **the fix's effect is
unverified, not that it was ineffective**; the revert decision was also taken on the racy measurement above,
which weakens it further.

To settle it properly, the next attempt must be visibility-aware: intersect the control's rect with the
scrolling container's visible box and hit-test (`document.elementFromPoint`) only that intersection. If the
intersection is empty after the change, the control is simply below the fold and nothing is occluded.

What IS established independently of the fix question: after `scrollIntoView({block:'center'})` the control is
fully clear of the dock (`clearsDock: true`) and hit-tests to itself (`hitsSelf: true`) at 420, 430 and 390. So
the defect is an **at-rest** occlusion of one control in the initial viewport — the control is reachable, just
partly hidden on first paint. That is a cosmetic/UX judgement, which is why it is raised for owner acceptance
rather than fixed unilaterally, especially as the concept contains no inline advisory control in that position.

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
