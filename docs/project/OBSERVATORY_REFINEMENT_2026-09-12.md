# Observatory refinement checkpoint — September 12, 2026

Status: stopped at the owner's request to preserve the remaining usage budget. Work is saved and tested, but final visual acceptance is pending. Source baseline before this pass: `474c019`; earlier recovery checkpoints: `1a27843`, `b3e27b5`. No production deployment, financial mutation, credential change or live database access.

## Latest stopping point

- Safe-to-spend, horizon and observation stamp are prominent on the actual Today template; mobile dial-left/callouts-right layout is implemented.
- Moon artwork is installed. Light-theme colors preserve ivory dial lettering and parchment tickets. Inline Virgil opens/closes; the overlapping Today FAB is hidden.
- Date buttons, native keyboard range and event buttons retain focus. The evidence card now shows each source/date/amount/reserve fact once and keeps unknown evidence/shortfall states explicit.
- Latest verification: **68 passed in 13.37s**, exit 0, using `.venv311/bin/python -m pytest tests/browser/test_dial_fidelity.py tests/meridian/test_dial_js.py tests/test_capture_contract.py tests/test_meridian_workspace_invariant.py tests/meridian/services/test_today.py -q`.
- Ruff passed for the preview script and changed test files; `git diff --check` passed.
- Last full rendered matrix: `artifacts/dial-refinement-2026-09-12/today-final/`, 16 images across all four viewports/two themes, zero horizontal overflow and no page errors. This predates the final compact-card/spacing adjustment; do not claim it verifies that last visual change.
- Preview: http://127.0.0.1:8093/. If stopped, run `.venv311/bin/python scripts/preview_observatory_dial.py` from ORSC. This is synthetic, not the daily banking runtime. Opening the raw template with `file://` is not a valid preview.
- **Resume narrowly:** recapture the compact card/full Today matrix, compare with the governing concept, finish QA and update evidence. Do not restart the roadmap audit or expand into other workspaces. Deployment still needs its own owner approval.

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
