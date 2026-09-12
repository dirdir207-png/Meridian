# Observatory / Today visual QA — work in progress

Source: `design/observatory-drafts-2026-09-08/06-interactive-observatory-vision.png`.

Implementation: production Today template and dial/Today/shell controllers in the isolated synthetic preview at http://127.0.0.1:8093/.

Evidence: `artifacts/dial-refinement-2026-09-12/` captures and manifests. Component-only `final-compact` is superseded by the owner's instruction to restore the original page composition. `today-composition-1` is intermediate; final captures are pending.

Resolved: placeholder dial layers; center displaced by controls; keyboard focus loss; prominent safe-to-spend restored; mobile event callouts moved to the right.

Still to verify: final all-viewport/theme matrix, new moon asset in composition, light-theme foregrounds, callout amount fit, exact visual comparison and current broader focused tests. Existing passing intermediate captures are not final acceptance.

Latest checkpoint: owner requested stopping to preserve usage. Moon/theme/callout fixes were captured in `artifacts/dial-refinement-2026-09-12/today-final/` (16 images, zero overflow/page errors). A subsequent compact-card/spacing change passed the focused suite (**68 tests**) but still needs fresh visual comparison. Keyboard event/date/range focus and inline advisor open/close are covered. No full live application acceptance or production deployment is claimed. Stop here; resume with that bounded capture/review only.

final result: blocked
