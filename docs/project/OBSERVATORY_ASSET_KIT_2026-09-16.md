# Observatory artwork handoff and preview findings — 2026-09-16

Owner request: convert the artwork in the September 8 consolidated handoff into individual assets for the Meridian build team, and identify the visual nuances missing from the current preview.

## Deliverable and scope

Kit: `static/img/meridian/observatory/kit-2026-09-16/`. Start with `index.html` and `README.md`. It includes individually named decorative PNGs, licensed SVG icons, two licensed font files, a scoped CSS specimen, provenance/dimensions/hashes, and generation prompts. These are reference-based reconstructions, not original layered exports. The gallery is a standalone inspection surface and is not loaded by the production app.

The concept artwork is usable source art. Verified with `pypdf` and decoded RGB comparison: PDF pages 16–22 each contain one raster image, and all seven are pixel-identical to the corresponding `design/observatory-drafts-2026-09-08/00–06` PNGs. Using the original PNGs therefore preserves the PDF's image quality. Text and font identities are not recoverable as editable layers from these images.

## Current-preview evidence

Inspected the running synthetic preview on `127.0.0.1:8093` at source HEAD `d90b2398cf24ecdef173dc95ec1a2952e002ade1`. Its footer explicitly says no bank connection; source `scripts/preview_observatory_dial.py` serves synthetic fixtures and production templates. Screenshots are in `artifacts/observatory-asset-kit-2026-09-16/evidence/`.

Accepted captures use 420×912 CSS viewport, requested DPR 3, dark theme, initial viewport. Files ending `-dpr3.png` are the accepted images. Earlier captures without that suffix showed a browser capture scaling defect (content occupies only half the exported canvas) and are rejected, retained for traceability. This is a focused visual inspection, not the complete governed parity matrix: the clock, polling and animations were not comprehensively frozen; fixture states differ from the concepts. No pixel-difference score or financial/content equivalence is claimed.

| Step | Surface / evidence | Finding and consequence |
|---|---|---|
| 1 | Today / `01-today-dpr3.png` | Existing ring, observatory and moon establish some of the language. Header is compact; wordmark has no concept accent. Pointer exists but is a short thin line with small tip, rather than the prominent mint needle/hub. Right-side event list is internally scrollable; connector runs are absent. Internet and Electric share the lightning badge. The rectangular ticket loses scalloped silhouette/rivets. Bottom navigation is text-only. |
| 2 | Plan / `02-plan-dpr3.png` | Generic coverage donut and rounded cards occupy the main slot; the governing folded map is absent. Long introductory heading/copy and early controls displace the art-led hierarchy. This needs layout work as well as a new image. |
| 3 | Activity, Review selected / `03-activity-review-dpr3.png` | Real review controls are available. Telescope vignette, parchment review summary and large framed category glyphs are absent. Do not score differences in merchants, counts or amounts against the concept: the fixture is different. |
| 4 | Accounts / `04-accounts-dpr3.png` | Rounded summary cards replace the large parchment/observatory ticket and illustrated account constellation. Fixture balances differ; the comparison concerns presentation, not correctness of amounts. |
| 5 | Settings link | `/meridian/settings?section=connections` returns 404 on this preview. No rendered Settings audit is claimed; use 05 as art reference and add preview support before parity assessment. |

Production CSS currently declares `"Iowan Old Style", Baskerville, Georgia, "Times New Roman", serif` and system sans; no font files were found under `static/`. Computed style confirms the declared stack, not the actual fallback used. The kit offers Libre Baskerville + Source Sans 3 as a reproducible candidate with bundled licenses. Owner comparison of the specimen remains necessary before calling typography matched.

## Nuances to preserve

- `BUILD_SPEC.md` explicitly assigns 01 to Today composition/palette and 06 to functional dial/evidence. Do not discard either, and do not treat the old nonfunctional instrument's exact geometry as a financial contract.
- Preserve the oversized left-bleeding dial and the rhythm between its markers, connecting lines and right-side labels. A uniformly scaled miniature cannot preserve this hierarchy.
- The concept uses cream editorial serif lettering, lilac dates, mint incoming/confirmed values, apricot action/event emphasis, thin brass rules and indigo paper grain. Follow the governed starting tokens, then inspect texture-adjusted contrast.
- Badges have visual weight: colored disk, double brass rim, rivets and a legible semantic icon. Tiny plain circles and duplicated lightning icons lose that distinction.
- Tickets use shaped silhouettes, layered hairline borders and subtle fibrous paper. Keep all money and words in HTML, separate from art; corners remain fixed-size as text reflows.
- The small wordmark accent, navigation compass/map/chart/person glyphs and active lilac treatment must be explicit implementation items. They are not optional merely because the data routes work.
- Reuse decorative assets sparingly. Settings and Activity remain quieter than Today. Do not repeat a telescope in every row.

## Build-team next slice

Read the kit README and inspect the gallery, then integrate one bounded visual gap at a time in the existing Track D lane. Start with shared type/header/navigation, then Today geometry and event callouts, then Plan map, Activity and Accounts. Carry the kit's file hashes and exact consuming code revision into fresh governed capture evidence. The owner still accepts the visual journey; this asset handoff does not certify app parity or deploy anything.

## Verification record

Asset-level checks and gallery results are recorded in `artifacts/observatory-asset-kit-2026-09-16/verification.json`. This is an artwork/documentation handoff: no banking test, financial mutation or production release is part of it. Existing builder-owned templates, CSS, JavaScript and original art are preserved.
