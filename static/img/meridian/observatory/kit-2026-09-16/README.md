# Observatory asset kit — 2026-09-16

Owner-requested standalone art handoff. Open `index.html` through a local HTTP server to inspect the files on indigo, parchment, white, and contrasting backgrounds. The existing synthetic preview serves this directory at `/static/img/meridian/observatory/kit-2026-09-16/index.html`.

## What these files are

Separate decorative reconstructions made with the built-in image-generation tool, using the exact governing reference PNGs. The seven reference PNGs were compared to the seven embedded images on PDF pages 16–22: dimensions and decoded RGB pixels match exactly. The PDF contains flattened artwork, not editable illustration layers or font metadata.

These exports remove UI labels and restore the decorative surfaces beneath them. They are not pixel-exact crops and do not supersede the reference composition. `prompts.json` records the requests; `manifest.json` records actual dimensions, hashes, alpha checks and roles. Rejected checkerboard exports are not shipping assets.

## File use

| Asset | Intended placement | Rules |
|---|---|---|
| `plan-map.png` | Plan allocation illustration | Preserve aspect ratio; put readable HTML summaries above it. Constellations do not encode money. |
| `activity-telescope.png` | Activity top-right vignette; reuse sparingly in Settings | About 130–170 CSS px wide on mobile. Do not let it squeeze the heading or touch target. |
| `observatory-landscape.png` | Lower-left Today dial layer; Accounts decorative vignette | Separate from dial geometry; no interaction. Review edge treatment on the chosen theme. |
| `moon-orbit.png` | Upper-right Today hero ornament | About 110–150 CSS px wide; no marketing text embedded; do not use it as a status indicator. |
| `parchment-ticket.png` | Evidence, account summary, compact income ticket | Blank center for HTML. Preserve corner sizes with measured nine-slice or layered fixed corners when adapting height. Never stretch the entire border arbitrarily. |
| `apricot-button.png` | Primary action plate | Use behind a real button/link. HTML label and arrow; at least 44px target. Nine-slice for variable width. |
| `medallion-frame.png` | Event and navigation badges | Decorative frame above a code-owned colored disk and semantic SVG icon. |
| `dial-annulus.png` | Optional separate ornamental ring for Today | No baked dates, ticks, pointer or financial meaning; those remain code-owned. Do not replace approved geometry solely to fit an image. |

Decorative image elements use `alt=""`, `aria-hidden="true"`, and `pointer-events:none`. The gallery uses descriptive alternatives only because inspecting the artwork itself is its purpose. Use the manifest's actual dimensions to avoid layout shift. At 2× a raster should not be displayed wider than half its native width; at 3× use one-third. Full native assets are masters; choose delivery sizes after the target slot is measured.

## Typography

`fonts/LibreBaskerville.ttf` and `fonts/SourceSans3.ttf` are bundled variable fonts with their SIL OFL notices. This is an explicit candidate match, not a claim that the generated concepts used those exact fonts. Existing production CSS uses Iowan Old Style/Baskerville/Georgia and system sans, with no bundled font files found during inspection. A CSS stack does not prove which fallback actually rendered.

Use the specimen to decide on the pairing once, then self-host it consistently. Maximum two families. Serif: wordmark, page titles, hero amounts, editorial headings. Sans: controls, dates, source stamps, dense data, errors. Body 16px, supporting labels 14px, page title 32–40px, hero amount 44–56px, row amount 20–24px. Money uses tabular lining numerals. Do not shrink text to make the tall concept fit one phone viewport.

## Color and icons

`kit.css` carries the exact starting tokens from `BUILD_SPEC.md`; it is scoped to `.obs-kit` and is not loaded by the app. Cream = primary text; lilac = secondary emphasis/selection; mint = confirmed funding/incoming; apricot = primary action/upcoming; coral = problems. On parchment, use dark navy text; do not carry pale lilac/mint text over without checking contrast. Do not equate outgoing money with an error.

The 22 SVGs in `icons/` are Bootstrap Icons v1.13.1, MIT, with the license preserved. They are semantic substitutes, not exact tracings. `compass`, `map`, `bar-chart`, `person-circle` map to the four navigation entries; `gear` to Settings. Pair the icon with a visible label. Bill badges distinguish electricity (`lightning-charge`) from Internet (`wifi`); use `bank` for reserves instead of copying the concept's semantically incorrect Wi-Fi reserve glyph. Other mappings: `house` rent, `flag` goal, `basket` groceries, `controller` entertainment, `bus-front` transit, `people` connection/household, `bell` notifications, `key` passkeys, `cloud-arrow-down` backup, `clock-history` action history. A shown icon does not make an unsupported feature available.

## Integration sequence for the build team

1. Read `design/observatory-drafts-2026-09-08/BUILD_SPEC.md`, the current decisions and `docs/project/OBSERVATORY_ASSET_KIT_2026-09-16.md`. Inspect 01 for general Today language and 06 for the functional dial/evidence target; 02–05 govern their own workspaces.
2. Settle the reproducible type pairing and token use with the owner. Restore the header and navigation hierarchy across screens.
3. Today: preserve the large left-bleeding dial, legible right callouts, prominent mint selection pointer, connectors tied to actual event coordinates, and shaped evidence ticket. The current shorter pointer exists; its prominence and relationship to the callouts need work. Do not use a new image to cover wrong layout or geometry.
4. Plan: install the map below the tabs with semantic allocation summaries and separate medallions. Activity: add the telescope and restore the quiet ledger/review styling. Accounts: use the parchment summary plus observatory vignette. Settings: reuse restrained art and parchment section strips only after its preview route is available.
5. Run the governed capture matrix against synthetic fixtures, compare matching states, and review each image. A working asset gallery is not app parity. Distinguish artistic composition differences from intentionally different fixtures or verified financial semantics.

No production template, CSS, JS, financial logic or deployment is changed by this kit. Keep existing assets until the consuming slice deliberately replaces them. Never use an entire mockup as a page background.

## Sources

- Local governing art: `design/observatory-drafts-2026-09-08/00–06` (individual filenames in manifest).
- PDF: `output/pdf/Meridian_Consolidated_Handoff_2026-09-08.pdf`, visual appendix pages 16–22.
- Fonts: https://github.com/google/fonts/tree/main/ofl/librebaskerville and https://github.com/google/fonts/tree/main/ofl/sourcesans3 (retrieved 2026-09-16, hashes in manifest).
- Icons: https://github.com/twbs/icons/tree/v1.13.1/icons.
