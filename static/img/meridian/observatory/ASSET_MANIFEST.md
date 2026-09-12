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
| `icons/*.svg` | Standard event-kind icons | 24px | Bootstrap Icons 1.13.1, MIT; license included |

Initial placeholders were authored in-repo. New raster provenance is recorded
in `docs/project/OBSERVATORY_REFINEMENT_2026-09-12.md`. Bootstrap Icons source:
https://github.com/twbs/icons/tree/v1.13.1. Remaining placeholder assets outside
the dial are not represented as completed artwork.
