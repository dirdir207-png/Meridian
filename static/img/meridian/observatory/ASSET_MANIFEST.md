# Meridian Observatory asset manifest

The initial SVG/WEBP decorations remain preserved. The September 12 refinement
uses the generated raster dial plate and moon below. Decorative assets never
carry financial meaning: dates, amounts, ticks, selection and pointer remain
code-owned. The generated dial source is RGB, not alpha-transparent; the CSS
circular clip excludes the exterior checkerboard.

| File | Role | Intended size | Status |
|---|---|---|---|
| `observatory-engraving.svg` | Decorative observatory/landscape | ~1200x720 @2x | placeholder |
| `dial-ornament.svg` | Ornament under the interactive dial, no ticks/pointer | ~1200x1200 @2x | placeholder |
| `map-ornament.svg` | Decorative star-map lines for Plan | ~1200x520 @2x | placeholder |
| `ticket-corners.svg` | Nine-slice corner treatment reference for tickets | ~400x400 @2x | CSS may supersede |
| `paper-texture.webp` | Restrained seamless parchment grain | 256x256 tile | generated placeholder |
| `ink-texture.webp` | Restrained seamless indigo grain | 256x256 tile | generated placeholder |
| `moon-engraving.webp` | Optional small moon illustration | TBD | not yet produced |
| `dial-plate.png` | Parchment/brass ring, starfield, observatory landscape | 1254×1254 | Generated from governing concept; circular CSS clip required |
| `moon-engraving.png` | Decorative moon and orbit lines beside spendable | 1254×1254 | Generated from governing concept; navy backdrop |
| `title-rule.svg` | Lilac wavy rule under the workspace title (Today/Activity/Accounts; **not** Plan) | 72×12 | Drawn in-repo from measurements of concepts 01/03/04 (141×18 device px, 8.1px stroke, 10.0px peak-to-peak, lilac `#a28ec9`). Drawn at the concepts' scale-independent peak-to-stroke ratio of 1.25. Decorative: carries no theme token, so it keeps the concepts' colour on both themes |
| `accounts-ticket-building.png` | Accounts summary-ticket illustration: a colonnaded domed archive building with scrolls and an open ledger | 1254×1254 | **Owner-supplied 2026-09-18**, replacing the kit's provisional scoping of `observatory-landscape.png` (the Today dial's building) to this surface. RGBA with real transparency: 56.2% of pixels fully transparent, all four corners `(0,0,0,0)`. Displayed at `clamp(92px, 28%, 188px)` in a 1:1 box |
| `trials-sentinel-hourglass.png` | Trials & renewals command-header ornament: an engraved brass sand-timer | 607×1222 | **Generated 2026-09-23** with Runway `gpt_image_2` (D-021) and derived by `scripts/key_raster_background.py`; master, prompt and hashes in `design/trials-sentinel-2026-09-23/`. RGBA: 76.0% of pixels fully transparent, all four corners transparent, alpha 0–255. Used as a CSS `mask` with `background: var(--obs-brass)` so the engraving follows the theme, sized `clamp(104px, 13vw, 168px)` tall |
| `icons/*.svg` | Standard event-kind icons | 24px | Bootstrap Icons 1.13.1, MIT; license included |

Initial placeholders were authored in-repo. New raster provenance is recorded
in `docs/project/OBSERVATORY_REFINEMENT_2026-09-12.md`. Bootstrap Icons source:
https://github.com/twbs/icons/tree/v1.13.1. Remaining placeholder assets outside
the dial are not represented as completed artwork.
