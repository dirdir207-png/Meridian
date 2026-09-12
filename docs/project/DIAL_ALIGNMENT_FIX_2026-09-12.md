# Dial alignment fix — September 12, 2026

## iPhone Air follow-up

The owner's next screenshot exposed a separate horizontal collision. At 420px, the dial wrapper ended at x=306 while the callout region began at x=288: an 18px overlap. Mobile enlargement now extends only into the left margin, with a 12px grid gutter on the right. The scroll-region height was adjusted to the resulting dial size; its titles and signed amounts retain their full callout width.

The extra 420×912/DPR 3 test target follows [Apple's layout table](https://developer.apple.com/design/human-interface-guidelines/layout). Both Chromium and Playwright WebKit pass the separate-hit-area and date-label clearance tests. **47 focused checks passed**, and eight synthetic full-template iPhone Air captures (both engines, both themes, viewport/full-page) record a 12px gap and zero page overflow. Evidence: `artifacts/dial-refinement-2026-09-12/iphone-air-gap/`. The running 8081 preview serves the corrected CSS hash; no restart, financial/data change or new deployment was required for this CSS-only follow-up. Physical-device acceptance remains owner-observed.

## Symptom and cause

Owner phone screenshots showed a large blank area above the dial, words split inside the narrow event column, and a detached minus sign. The screenshot also contained older Today header markup with the new dial styling.

The prior three-event fixture did not cover a tall event rail. A twelve-event synthetic browser reproduction at 390px placed the dial **879px below the top of its panel**. `align-items: center` centered it against the entire event list. The icon's grid column left only a narrow text column. After bounding the rail, a second assertion caught date controls overlapping it because those controls still belonged to the left column while spanning both columns.

The running preview process started September 11 at 19:57, before the September 12 template edits. Its served CSS/JS already matched the checkout, while Flask/Jinja template auto-reload was disabled. An isolated Flask test reproduced old markup remaining cached after the template file changed.

## Implemented

- Top-aligned dial and bounded, keyboard-accessible scrolling event region. All twelve records remain reachable; selecting the last one scrolls the region rather than jumping the page.
- Full callout width for titles, funding state and amounts on mobile; ordinary words and signed amounts no longer split across lines.
- Date controls occupy their own full-width grid row beneath both the dial and event region.
- The center has a wider text area and a two-line title limit; the complete title remains in the event list and evidence card. Longer amounts receive a compact text size.
- Preview-only template auto-reload is enabled without enabling the debugger or process reloader.

## Verification

Baseline: `bab906f`. Failing tests were run before the corresponding fixes:

- Twelve-event alignment test failed at both 390px and 430px.
- Controls/rail overlap assertion failed before moving controls to their own row.
- Template refresh test returned `old header` after changing the file, before enabling preview template reload.

Final command:

```sh
.venv311/bin/python -m pytest tests/browser/test_dial_fidelity.py tests/test_preview_template_refresh.py tests/meridian/test_dial_js.py tests/test_capture_contract.py tests/test_meridian_workspace_invariant.py tests/meridian/services/test_today.py -q
```

**71 passed in 18.62s**, exit 0. Ruff and `git diff --check` passed. The template test uses a stub Flask app and a temporary runner directory; it cannot import the banking app or load its `.env`.

Synthetic full-template capture matrix: `artifacts/dial-refinement-2026-09-12/alignment-dense-final/` — 16 captures covering four governed viewports and both themes, zero page overflow and zero page errors. Mobile captures were visually inspected. The records/amounts are invented; the owner's financial screenshot data was not copied into fixtures or source control.

## Running preview and limits

The existing ORSC preview on port 8081 was reloaded after passing checks, preserving its database path and existing app runtime environment. No bank operation, credential change, new image deployment, or database migration was performed by this fix. New preview PID: `33798`; `/login` returned HTTP 200. Served `dial.css`, `dial.js` and `today.js` hashes match the working tree. Backend application/migration source predates the original running process and was not changed.

Authenticated live phone rendering was not captured again; the owner can reload Today to receive the refreshed template/assets. This fixes the reported alignment incident, not every previously recorded visual-fidelity or financial-model issue.
