# Observatory refinement checkpoint — September 12, 2026

Status: work in progress, saved at the owner's request. Source baseline before this pass: `474c019`. No production deployment, financial mutation, credential change or live database access.

## Owner direction

Match the original Observatory concept more closely with focused changes. The owner subsequently clarified that safe-to-spend must remain prominent on Today and that the original layout itself matters: large dial on the left, event callouts on the right, evidence underneath. This supersedes the interim mobile layout with all event cards below the dial. Continue here, not on the proposed roadmap's V1.1 backend slice.

## Implemented so far

- New raster parchment/observatory dial plate and moon asset, based on `design/observatory-drafts-2026-09-08/06-interactive-observatory-vision.png`.
- Existing diagram/date math retained, with visual radius and pointer placement adjusted to the artwork. Controls no longer distort the absolute-positioned label layer.
- Keyboard controls survive date changes without losing focus. Event selection updates center and evidence ticket.
- Real HTML text/date labels, local Bootstrap Icons 1.13.1 assets (MIT license included), larger typography and unboxed event rail.
- Real Today template and controller retain API-provided safe-to-spend, now prominent with separate horizon/source lines. Missing horizon stays unavailable.
- Mobile composition restored to dial-left / callouts-right. Inline Today advisor control replaces the overlapping floating trigger on this workspace.
- Isolated `scripts/preview_observatory_dial.py` renders the actual templates/styles with synthetic Today data and Today/dial/shell controllers. It never imports `app.py`, loads credentials or accesses a database/provider. Loopback URL: http://127.0.0.1:8093/.

## Evidence and limitations

- Initial browser repro: center amount was 96px below dial center at 390px; keyboard focus was lost after Next day. Both tests failed before the correction and passed afterward.
- Intermediate focused suite: 36 passed (dial geometry/source checks, isolated browser checks, capture contract).
- Latest owner-directed composition: `tests/browser/test_dial_fidelity.py`: **7 passed in 7.73s**. Full relevant suite and new final capture matrix still need rerunning after this checkpoint.
- Multiple 16-image matrices (four viewports, two themes, viewport/full page) under `artifacts/dial-refinement-2026-09-12/`. `final-compact` is the superseded component-only composition; `today-composition-1` is an intermediate full Today capture, with small overflow since addressed by widening the event rail. Neither is final acceptance.
- A generated image initially contained a checkerboard outside its silhouette. The dial plate is displayed through a circular CSS clip; it is not advertised as an alpha-transparent source asset. A subsequent background-correction generation hit a usage limit; the separate moon generation later succeeded.
- No new live served-app acceptance, full application test suite, or independent review claimed. Code/template-only files opened through `file://` are not the rendered preview.

## Next actions

1. Reopen the isolated preview URL and recapture the current full Today composition in both themes/all governed viewports.
2. Check light-theme text contrast, long/empty values and mobile callout fit. Inspect both source and implementation together.
3. Run focused Today/dial tests, browser interaction checks, Ruff and diff checks; update `design-qa.md` honestly.
4. Record final evidence and commit only intended changes. Production deployment remains a separate owner gate.

## Generated asset provenance

Built-in ImageGen was used, with the governing concept attached. No external user data was sent; reference numbers are concept/fixture values.

- `static/img/meridian/observatory/dial-plate.png`: generated parchment/brass ring, dark starfield and lower-left copperplate observatory. Prompt requested no labels, dates, ticks, pointer or UI; functional geometry and text remain code-owned. The delivered RGB image uses CSS clipping to exclude its outer checkerboard.
- `static/img/meridian/observatory/moon-engraving.png`: engraved crescent moon, ivory/brass highlights, sparse celestial orbit lines/stars, uniform `#101a28` background, no text/numerals/UI/transparency.
- Standard icons: https://github.com/twbs/icons/tree/v1.13.1, local files and MIT license in `static/img/meridian/observatory/icons/`.
