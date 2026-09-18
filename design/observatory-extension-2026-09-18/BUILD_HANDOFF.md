# Observatory extension — DeepSeek build handoff

2026-09-18. Owner-requested complementary concepts, reusable assets and deterministic category expansion. This is a design proposal and tested source change, not a production deployment or owner acceptance of every screen. The owner explicitly likes the deep orange action treatment.

## Start here

Use this canonical repository and its current `feat/meridian-implementation` branch. Read AGENTS.md, current project instructions, decisions, roadmap and visual capture spec. Preserve unrelated changes. Do not copy from historical checkouts. Read `design/observatory-drafts-2026-09-08/BUILD_SPEC.md` and the September 16 asset-kit handoff for the existing design language. This extension preserves their composition vocabulary; it does not authorize a new navigation system or financial behavior.

Open `index.html` for the four concepts, usable icon specimen and assets. `prompts.json` records built-in ImageGen prompts. `manifest.json` gives provenance, dimensions and SHA-256 hashes. SVGs are Bootstrap Icons 1.13.1, MIT, license bundled. They are semantic substitutes, not traced concept glyphs. Generated PNGs are design references or explicitly decorative assets, never executable UI.

## Interpretation

- **Timeline — what happened.** One chronological ledger for purchases, transfers, refunds, evidence and corrections. Separate observed money movement from forecast events. Date headings, compact category medallions, source/freshness and a selected-transaction inspector. No approval button on every ordinary ledger row. An internal transfer is neither spend nor income and must not inflate totals.
- **Review — what needs a decision.** Category review is local bookkeeping. One row shows the proposed category, why it was proposed and an explicit confirm/change action. Unknown is a question icon plus Choose category, not Approve Uncategorized. Category confirmation is never bank authorization. Consequential proposals get a separate queue/filter, exact before/after values and the existing financial approval flow.
- **Settings — how Meridian works for me.** Connections grouped by Money / Evidence / Time, each identity separately manageable. Preferences include appearance and quiet hours. Virgil settings expose memory sources, retention, capability availability and revocable authority boundaries. Funding schedules link to the existing Plan journey. Security, devices, backups and action history remain discoverable subpages. Never invent enabled integrations or a universal autonomous-money switch.
- **Virgil — one consistent guide.** Contextual entry opens a mobile full-height sheet or desktop right-side panel with Conversation and Tasks. Answers show evidence, source age and assumptions. A proposal has a draft/approval/execution/readback state, never an ambiguous Done. Long-running investigations preserve queued/running/needs-input/completed/failed states. Voice is an input method, not approval. The proposed iOS/voice capabilities remain capability-gated under VIRGIL-A0–A5; these mockups do not enable them. Keep the guide identity stable across approved runtime model changes. Use a lantern, not a floating character.

## Visual and responsive contract

Dark canvas #172334, surface #202b40, cream #eee4cf, muted #b7b8cb, lilac #c1a9e2, mint #a5d4bf, brass #c6aa71, parchment #ead8b5 with ink #20263b. **Deep orange #e99a48** is the proposed primary-action fill; hover #f3b272; text #20263b. Orange text/underline selects the local tab. Mint means confirmed/incoming, not unreviewed. Spending is not an error. Coral is for a real failure/problem.

Use bundled Libre Baskerville / Source Sans 3 from the September 16 kit. Body 16px, secondary 14px, title 32–40px, 44px minimum targets. Use quiet dividers, not nested cards. Limit artwork to a 120–160px header slot; reduce it before shrinking text. Category glyph 24–28px in a 48–56px medallion. Small status glyph 16–18px plus text. Do not reuse the compass except for Today navigation, or the clock except for actual history/time.

At 390/420/430px: single column, compact header and tabs, full-height detail sheet, dock safe-area padding and content clearance; no Virgil bubble overlapping the dock. At 1024px: narrow navigation and one optional inspector. At 1440px: existing rail, flexible ledger, 320–360px inspector; Virgil opens there without adding a fifth workspace. Settings uses grouped navigation left and selected details right. Review actions stay adjacent to their row. Light theme uses warm ivory surfaces and dark ink, not an inverted screenshot; verify contrast independently.

The images are scrollable art direction at roughly the 420×912 aspect ratio, not an instruction to shrink all content into one viewport. Build all words, amounts, dates, controls, counters and statuses as real HTML. Charts/geometry are data-driven. Never use a mockup as a background.

## Image corrections that the implementation MUST make

Generated art can disagree with semantics. Timeline's moon/sun markers are ornament, not evidence of day/night; use plain date headings or correct symbols. Its transfer amount should be neutral, not income-green. Review shows a count of three but two visible rows: render the actual total and paginate, never hardcode three. Its green dot on an unknown row must become an amber question/status with text. Ignore the generated owl next to Ask Virgil; use `chat-left-text` or the lantern identity. Virgil's draft state must be neutral/lilac rather than confirmed-green. Do not highlight Activity in the Virgil dock unless it is the actual originating workspace. Hide the synthetic-preview label in the real app, but never hide a real stale/unavailable state.

## Icons and category behavior

`static/js/meridian/kit-icons.js` now exports CATEGORY_ICONS, ACTION_ICONS, categoryIsAssigned and transactionIconName. `static/img/meridian/observatory/kit-2026-09-18/icons/` has 61 standalone licensed SVGs. Prefer CSS masks/currentColor as the existing implementation does; decorative icons get aria-hidden and nearby visible labels. The gallery shows the exact production category/action mapping. Do not imply capability from an icon.

Assigned category wins over merchant words. Owner custom category uses tag. Explicit Uncategorized uses question-circle. Utilities may specialize to Wi-Fi from a clear descriptor only when not owner-authored. Unknown incoming is not automatically salary. Taxes/fees and pets/health may share family resemblance but distinct labels remain authoritative. Use one stable glyph per meaning across desktop and mobile.

## Implemented source slice

`meridian/category_catalog.py`: 29 standard categories; 51 curated merchant rules / 70 aliases. Case, punctuation, apostrophes, recognized processor wrappers and store-number suffixes are normalized. Anchored identity matching prevents substring collisions. Merchant-sector classification does not claim item-level evidence. Confidence .95 is the pre-existing deterministic rule score, not a calibrated probability. Known negative purchases can clear the existing .7 review threshold. Positive merchant credits do not become spend. Owner rules and reconciled transfer/refund/reimbursement evidence retain precedence.

Mixed retailers, pharmacies, fuel/convenience stores, unfamiliar merchants and unrecognized descriptors stay reviewable. No broad keyword auto-confirmation was added. Existing editor-only heuristic suggestions remain suggestions. No tax treatment is inferred. Existing recurrence semantics were not expanded.

`meridian/repository.py`: explicit owner correction survives automated record_classification; Uncategorized history is excluded from suggestion/options. Catalog adds editor categories. `activity.js` uses the new glyph assets and cannot enable approval for an empty/Uncategorized suggestion. `review.js` checks the category again before submitting and offers the editor instead. Expanded dropdown categories remain free-text compatible.

Existing persisted fallback rows are not bulk rewritten by this work. Future normal sync can apply rules while preserving explicit corrections. If a one-time historical backfill is needed, first produce a read-only count/sample report and verified backup; scope to non-owner fallback records and audit changes. Do not open or mutate the live DB as part of asset integration. No live bank operation is needed.

## Build order and acceptance

1. Retain the tested classifier/icon changes. Inspect the concept gallery and apply the agreed orange treatment in the app in a bounded styling slice.
2. Recompose Activity Timeline/Review with the supplied assets; wire category, confidence/provenance and real source age. Keep Patterns accessible; its eventual design is observed trends with evidence links and explicit sample size, not another review queue.
3. Build Settings grouping over actual capability/read models. Unavailable features must say unavailable/planned, not show working switches.
4. Refresh Virgil's existing contextual conversation and proposal surfaces first. Add Tasks/voice/device surfaces only through their roadmap gates.
5. Test unknown, corrected, deterministic, AI-suggested, stale, empty and failed states; corrections save/reread/restart and survive sync. Check no approve-unknown path. Use synthetic fixtures exclusively.
6. Follow the locked capture matrix in MERIDIAN_VISUAL_CAPTURE_SPEC.md (both themes at 390×844, 420×912, 430×932, 1440×900, plus tablet). Verify labels, keyboard/focus, 200% zoom, no horizontal overflow and no dock/composer collision. Compare matching states. Deploy only after existing release/owner gates.

See `VERIFICATION.md` for this turn's measured checks. The new layouts and orange production styling are **not implemented or deployed** by this handoff. The classifier and review-icon source changes are implemented and tested; live-phone effects are not claimed.
