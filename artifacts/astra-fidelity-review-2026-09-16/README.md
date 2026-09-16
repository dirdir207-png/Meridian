# Astra fidelity review — concept vs current, 2026-09-16

Handoff package for correcting the Observatory implementation against the governing concept set.
Compiled by the ORSC Builder lane at `feat/meridian-implementation` @ `8d8424e`.

## What is in here

Ten images: five workspaces × two framings.

| File | What it shows |
|---|---|
| `<workspace>-01-first-screen-concept-vs-current.png` | Concept / current light / current dark, **first screen only** (`<workspace>-mobile-air-{light,dark}-viewport.png`) |
| `<workspace>-02-full-page-concept-vs-current.png` | Same three panels, **full scrolled page** |

Workspaces: `today` (concept `01-today.png`), `plan` (`02-plan.png`), `activity` (`03-activity.png`),
`activity-review` (same concept, current Review tab active), `accounts` (`04-accounts.png`).

## Method — so the comparison can be trusted or repeated

- **Concept side:** `design/observatory-drafts-2026-09-08/0{1,2,3,4}-*.png`, used unmodified.
- **Current side:** the latest capture per workspace, from
  `artifacts/observatory-{today-connectors,plan-cta,activity-vignette,activity-glyph,accounts-assets}-2026-09-16/`.
- **All panels share one width** (560 CSS px each), so both sides sit at the **same CSS scale**. A longer
  current page is **padded, not stretched** — a different page length is explicitly not a design defect.
- Current captures: Playwright + Chromium, synthetic fixture `synthetic-observatory-2026-09-08`, frozen clock
  `2026-09-08T09:42:00Z`, viewport 420×912 at DPR 3, no polling/animation/timers, `document.fonts.ready` awaited.
- Builder: `tmp/build_comparisons.py` (untracked).

## Finding 1 — CORRECTED: the light theme works; the capture tooling was wrong *(retracted as an app defect)*

**This section originally reported a light-theme defect in the application. That was wrong, and it is retracted.**

The application is correct. Probing the live shell background returns `rgb(244, 236, 223)` (cream) for the light
scheme on **all four** workspaces, and `dial.css` has carried a correct theme-aware override all along. Anyone
reading the earlier version of this file should disregard its table and its conclusion.

What actually happened is a defect in our own capture pipeline, and it is fixed:

- `theme.js` resolves `localStorage` **before** `prefers-color-scheme`.
- `capture_meridian_matrix.py` opened one browser context per (viewport, theme) and then reused a **single page
  across every workspace** in the loop, relying only on `color_scheme` emulation.
- So once the app had written `meridian-theme`, every later page load in that context kept the stored value, and
  only the **first** workspace captured in each context got the emulated scheme.

The result was that the "light" capture for every workspace after the first was in fact a **dark** render — which
is why the comparison images in this package show what looks like no theme difference. Measured on the saved
captures: Today's two themes differed by 101.6 mean luminance while Plan, Activity and Accounts differed by
**0.1**, i.e. indistinguishable. The images were labelled light and looked plausible side by side, so comparing
the two passes showed *no* difference rather than an obvious error; only a luminance check caught it.

The fix pins `localStorage` to the same theme the harness passes as `color_scheme`, before any app script runs.
Re-verified on a fresh 80-capture matrix: deltas are now 114.7 (Today), 144.0 (Plan), 175.8 (Activity) and
159.9 (Accounts).

**Consequence for this package, and please read this before using it:** the ten PNGs shipped here were produced by
the **buggy** tooling. Their "current light" panels are dark renders for Plan, Activity and Accounts. They remain
valid for **dark-theme** fidelity review — which is the theme every concept depicts — but they are **not** valid
light-theme evidence. Corrected captures must be taken before any light-theme judgement is made.

## Finding 2 — structural differences per workspace

**Today.** Matches: dial plate, right-hand callouts with kit badges (Electric / Internet / Payday), the
`Crew · observed Sep8, 9:42 AM` provenance line, the parchment evidence ticket with `AMOUNT / RESERVED / View bill`,
the apricot primary plate, bottom nav. Differs: the concept puts the dial **first** with the figure **on the dial**;
the implementation leads with the figure at hero size and places the dial below. The concept's *"Bills reserved
$1,320"* parchment strip is absent from the first screen.

**Plan.** Matches: the folded brass map and its three medallion stations (Bills `$1,320`, Goals `$200`, Available
`$248.50`), the apricot primary plate, the tab row. Differs: the concept is map-led with an "Upcoming bills" list;
the implementation leads with the headline and adds a coverage donut, a long commitments table, a next-30-days
list and a scenario preview the concept does not depict.

**Activity.** Matches: the telescope vignette in the header's top-right station, and (in Review) the ringed
category glyphs, `Income · 95% confidence`, and the category action. Differs: **the concept's parchment
"3 categories to review" strip is absent** (see Finding 3); the concept's tabs are **underlined**, the
implementation uses pills; the concept's per-row primary action is an **apricot plate**, the implementation uses a
mint pill; the concept shows `Suggested category:` phrasing, the implementation `Approve category`.

**Accounts.** Closest of the four. Matches: the parchment summary panel with the dome engraving, the medallions in
their brass riveted rings, the dashed connector rail with per-row nodes, the closing `ASSETS & CONTRACTS` parchment
strip. Differs: the concept's summary panel is **full width**, the implementation gives it `2.1fr` beside a
Liabilities card (a deliberate trade to keep the real liabilities figure); the concept's connection row is a compact
strip, the implementation a full card.

## Finding 3 — one item deliberately not built, needs an owner decision

Concept 03's parchment **"N categories to review"** strip is **not implemented and should not be implemented by
guesswork.** The transaction payload exposes no awaiting-review field, so any count would have to be derived from an
invented confidence threshold — placing a derived figure where the concept shows a fact. It needs a decision on what
the number counts and what it says.

## Finding 4 — measured detail gaps (owner-reported, verified at pixel level)

Each of these was confirmed by sampling the concept PNGs, not inferred from memory. Values are given so the
correction does not have to re-derive them.

| # | Detail | Measurement / evidence |
|---|---|---|
| 1 | **Background is too light and too green** | Concepts average `#141b32` (20,27,50) across all four pages — Today `#161c34`, Plan `#131830`, Activity `#131b30`, Accounts `#151c34`. Ours is `--obs-bg: #172334` (23,35,52). Conversely Today's dark shell override is `#101a28`, *darker* than its concept's `#161c34`. |
| 2 | **Short lilac wavy underline under the page title** | Present on Today, Activity and Accounts; **absent on Plan**. Sits between the title and the tagline, roughly the width of the title's first third. Not implemented anywhere — a repo-wide search for a squiggle/flourish/wave motif returns nothing. |
| 3 | **Date under the wordmark** | Concept 04 shows `Tuesday, Sep8 2026` in lilac directly beneath `Meridian`. Ours has `.m-topbar-date` but it is `display: none` and only ever populated for Today. |
| 4 | **The Accounts ticket is at an angle** | The concept's panel is rotated a few degrees, with **punched semicircular notches** at the edges (a real ticket), a **fine dotted border inset** from the edge, and scattered **brass stars and a crescent** on the parchment. Ours is axis-aligned, square-cornered and plain. |
| 5 | **The Accounts connectors are curved and starry** | The concept uses **curved dashed paths** bowing outward, one **node circle at each end**, coloured per row (lilac → mint → apricot), plus **dotted row separators with a brass star at each end**. The straight vertical dashed rail we built is the wrong construction. The same curved-path-plus-node vocabulary appears on Today's dial-to-callout connectors. |
| 6 | **The tabs are a bordered bar, not pills** | Plan's row is **one rounded container with a brass border, divided into three cells by thin vertical rules**; the active cell is **parchment-filled** with a **brass star medallion at its left edge**. That container's top edge is also the separator line between the header and the tabs. Activity's row is a **ruled line with an underline** on the active label (now implemented). Two different treatments; we had one pill style for both. |
| 7 | **The medallion glyphs are richer than ours** | The concept's medallions carry detailed brass-toned glyphs (a compass rose, an engraved Wi-Fi mark). The kit's SVGs are deliberately "semantic substitutes, not exact tracings", so this is an asset decision for Astra, not a CSS fix. |
| 8 | **The Accounts engraving differs** | The concept draws a **colonnaded domed rotunda on a rocky knoll**; the kit's `observatory-landscape.png` is a different engraving. **This needs new art** — it will not be faked, and no CSS or nine-slice work can close it. |

Two further notes on colour, since "different font color" was reported: the concepts set **taglines and dates in
lilac** (not muted cream), the **wordmark and page titles in cream serif**, the **provenance line on the ticket
mixes lilac with dark navy** (`Crew` in lilac, `observed …` in navy), and the **active tab label in brass**
(`--obs-brass` is `#c6aa71`).

## Limits of this package

- **No desktop comparison exists.** Every concept is mobile-portrait (853×1844) and the capture contract forbids
  pairing a mobile concept with a desktop capture. Desktop fidelity is unreviewed here.
- First-screen panels show one screen; content further down each page appears only in the `-02-full-page-` images.
- These are DPR-3 captures against 1× design mocks, matched at equal width. Absolute vertical extents are not
  directly comparable.
- The bottom strip in some mobile captures is the synthetic preview banner overlaying content — a capture artefact,
  not a layout defect.

## Reference

Implementation record, per-slice evidence and known limits: `docs/project/CURRENT_STATUS.md`,
`docs/project/MERIDIAN_OS_TASKS.json` (OS-021…OS-034), and `design-qa.md`.

**Nothing in this package is deployed.** No route, data, financial, provider or authority behaviour was changed by
any of the work it depicts.
