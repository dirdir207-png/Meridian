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
| `moon-engraving.png` | Decorative moon and orbit lines beside spendable | 1254×1254 | Generated from governing concept. **Re-derived 2026-09-24** with `scripts/key_raster_background.py --strategy colour`, because the asset shipped OPAQUE on a flat `#101a28` field that does not match Today's `#161c34` and so read as a block of a different blue (owner-reported). RGBA with real transparency: 96.7% of pixels fully transparent, all four corners zero-alpha. The opaque master, the derivation command and the tool's report are in `design/observatory-moon-2026-09-24/` |
| `title-rule.svg` | Lilac wavy rule under the workspace title (Today/Activity/Accounts; **not** Plan) | 72×12 | Drawn in-repo from measurements of concepts 01/03/04 (141×18 device px, 8.1px stroke, 10.0px peak-to-peak, lilac `#a28ec9`). Drawn at the concepts' scale-independent peak-to-stroke ratio of 1.25. Decorative: carries no theme token, so it keeps the concepts' colour on both themes |
| `accounts-ticket-building.png` | Accounts summary-ticket illustration: a colonnaded domed archive building with scrolls and an open ledger | 1254×1254 | **Owner-supplied 2026-09-18**, replacing the kit's provisional scoping of `observatory-landscape.png` (the Today dial's building) to this surface. RGBA with real transparency: 56.2% of pixels fully transparent, all four corners `(0,0,0,0)`. Displayed at `clamp(92px, 28%, 188px)` in a 1:1 box |
| `trials-sentinel-hourglass.png` | Trials & renewals command-header ornament: an engraved brass sand-timer | 607×1222 | **Generated 2026-09-23** with Runway `gpt_image_2` (D-021) and derived by `scripts/key_raster_background.py`; master, prompt and hashes in `design/trials-sentinel-2026-09-23/`. RGBA: 76.0% of pixels fully transparent, all four corners transparent, alpha 0–255. Used as a CSS `mask` with `background: var(--obs-brass)` so the engraving follows the theme, sized `clamp(104px, 13vw, 168px)` tall |
| `accounts/compass-medallion.png` | Accounts emblems: the concept's compass rose for the account named **Free to Spend** | 208×208 (4× the concept's 52 CSS disc) | **Derived 2026-09-24** by `scripts/build_account_medallions.py --write` from the owner-authorized master `design/investigator-medallions-2026-09-21/compass-medallion.png` (sha256 `2223e081…`, lilac/brass rim, indigo field, engraved compass rose). The master is 1254×1254 with the disc at only **80.0%** of the canvas (visible bbox 124,124–1126,1111), so the handoff's instruction to "match the visible disc, not the PNG canvas" is met by cropping to that bbox before resampling: 2,026,463 → **91,025 bytes**, corners `(0,0,0,0)`, delivery sha256 `547e3382…`. The masters stay the source of record and are never shipped (`test_each_concept_emblem_is_a_real_delivered_asset`) |
| `accounts/wifi-medallion.png` | Accounts emblems: the concept's Wi-Fi mark for the account named **Bill Reserve** | 208×208 | Same derivation from `design/investigator-medallions-2026-09-21/wifi-medallion.png` (sha256 `76c7b1d8…`); visible bbox 117,121–1134,1126 = **81.2%** of canvas; 2,068,417 → **92,817 bytes**, corners transparent, delivery sha256 `589f7e5b…` |
| `accounts/star-medallion.svg` | Accounts emblems: the concept's star for the account named **Emergency Fund** | 208×208 | **Drawn in-repo 2026-09-24.** The delivered package explicitly excludes the emergency-fund star ("The emergency-fund star and full 61-icon pack are outside this small artwork delivery"), and the owner's 2026-09-24 choice authorised a drawn one. Drawn to the two masters' own measured construction — an angle-averaged radial profile of each puts the brass outer rim at 0.89–1.00 R, the coloured band at 0.73–0.89, the brass inner ring at 0.70–0.73 and the field inside 0.70 — so it is a brass rim with four rivets, a **coral** band (the concept's own emergency-fund colour), a brass inner ring, an indigo field and a brass star. Vector against the other two's raster: it reads slightly flatter at 208×208 and matches at the 52px display size; a matching raster star master is the open follow-up |
| `icons/*.svg` | Standard event-kind icons | 24px | Bootstrap Icons 1.13.1, MIT; license included |

Initial placeholders were authored in-repo. New raster provenance is recorded
in `docs/project/OBSERVATORY_REFINEMENT_2026-09-12.md`. Bootstrap Icons source:
https://github.com/twbs/icons/tree/v1.13.1. Remaining placeholder assets outside
the dial are not represented as completed artwork.
