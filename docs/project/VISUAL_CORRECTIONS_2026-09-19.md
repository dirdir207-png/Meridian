# Visual corrections — 2026-09-19

This pass used fresh synthetic captures from `:8093`. Authority follows the owner’s rule: September 16 assets and findings for overlapping work, September 18 for the added Timeline surface, and September 8 page compositions where no newer page concept exists. Activity carries two references under that rule: `design/observatory-drafts-2026-09-08/03-activity.png` still governs the Activity *page* composition (September 16 ships no page concept), while `design/observatory-extension-2026-09-18/concepts/timeline.png` governs the added Timeline surface and supplies the sun reference; the Activity captures in this pass are compared against the September 18 Timeline concept at the match that matters for this slice. The captures are evidence of the current synthetic fixture, not live-data acceptance.

## Implemented

1. **Wordmark dot** — replaced the four-point accent above the dotless second `i` with the requested round apricot dot. The shared partial and shell CSS remain the single implementation for the rail and mobile headers.
2. **Activity mobile rows** — at widths ≤600px, timeline rows use a merchant/category stack with the amount in a separate right column. Long names such as “Unassigned purchase” remain readable. Review cards keep their existing layout.
3. **Settings theme parity** — Settings now loads the same persisted theme controller as the main workspace. The synthetic preview serves the real Connections template and a read-only synthetic payload so this surface can be captured.

## Measured verification

- 42 focused tests passed: Settings preview/theme checks, identity checks, Activity timeline/glyph/vignette checks.
- `ruff` passed for the changed preview/capture/test files; `node --check` passed earlier for Activity JavaScript; `git diff --check` and guardrails passed.
- Browser matrix: 8 direct checks across 390, 420, 430 and 1440 CSS pixels in both themes. Activity had zero horizontal overflow and no page errors; all five timeline titles fit without truncation; Review still rendered; Settings applied the requested saved theme.
- Governed captures: `artifacts/visual-pass-2026-09-19/after-main/` (30 records for Today/Plan/Accounts), `after-activity/` (10 records), and `after-settings/` (10 records). Main pages and Activity had zero overflow and zero page errors. Settings has a 32px overflow in the two 1024×768 tablet captures (light and dark) caused by the existing settings shell and remains a follow-up; the 390/420/430 mobile viewports were clean. The screenshot is visually usable but is not called clean responsive parity.

## Findings left for the next slice

- Today, Plan and Accounts still differ structurally from the September 8 compositions. The biggest gaps are the smaller/current dial treatment on Today, the compact commitment-card stack on Plan, and the summary-card/list hierarchy on Accounts. They need separate one-gap-at-a-time corrections.
- Activity’s current Timeline is structurally closer, but its compact controls and parchment banner remain denser/different from the September 18 Timeline concept. The generated sun is now concept-matched at the day-divider scale.
- Settings now has a capture route, but the 32px tablet (1024×768) overflow should be traced before calling it parity. Do not hide it by changing capture metadata.
- Full icon replacement remains intentionally deferred. The owner wants the eventual set to match the concepts; this pass only generated and used the missing sun.
