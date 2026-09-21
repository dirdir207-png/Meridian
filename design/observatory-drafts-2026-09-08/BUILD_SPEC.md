# Meridian Observatory — implementation specification

## 1. Purpose and authority

Build a usable personal finance application with the visual character of a crafted observatory: indigo, parchment, engraved instruments, lilac, sea-glass, and apricot. The illustration must help navigation and understanding. This document specifies a future implementation; it does not certify existing banking behavior or authorize a live financial mutation.

The owner requested the full visual suite and an interactive dial. They strongly endorsed the Observatory direction. The exact dial behavior below is a proposed implementation contract derived from that vision, not functionality already shipped. Preserve all drafts. Do not replace the app with screenshots.

Execution repository: `/Users/stephenwest/Openrouter/simplecrew-latest`. Continue its existing branch and preserve unrelated changes. Do not implement in the historical Simplecrew checkout or the separate Chime projects. The Crew connector lives separately in `/Users/stephenwest/Applications/CrewWorkAssistantOTP`; its unrelated `auth.py` changes must remain untouched.

This checkout does not contain `AGENTS.md`, `docs/project/PROJECT_BRIEF.md`, or `docs/project/DECISIONS.md` at the time this specification was written. Read current available repository instructions/status before implementation. Do not create replacement project history from assumptions.

## 2. Visual references and interpretation

All paths below are relative to this specification:

| Reference | Purpose |
|---|---|
| `00-selected-direction.png` | Original selected Observatory visual language |
| `01-today.png` | Today composition and palette |
| `02-plan.png` | Foldout map, allocation destinations, bill rows |
| `03-activity.png` | Observation ledger and category review |
| `04-accounts.png` | Account summary ticket and linked account rows |
| `05-settings.png` | Settings grouping and appearance |
| `06-interactive-observatory-vision.png` | Primary target for the functional dial and evidence ticket |

Treat images as art direction, not executable financial specifications. Mock amounts, dates, status labels, arbitrary icon choices, chart geometry, and generated text may be inconsistent. Use real validated data in the product. Preserve visual character while correcting those defects. The drafts' tall compositions may scroll on actual phones; never shrink all text to fit one viewport.

## 3. Non-negotiable product rules

- Keep four workspaces: Today, Plan, Activity, Accounts; Settings is separate.
- Keep Flask/Jinja, existing JSON APIs, and vanilla JavaScript modules unless repository instructions require otherwise. No framework migration for this redesign.
- Every readable word, money value, date, input, and control is real HTML. Financial diagrams use SVG geometry and live data. Artwork is decorative and separate.
- Viewing, scrubbing time, opening evidence, and trying a scenario never submit a financial mutation.
- Changing Crew data continues through the established validated approval/execution service. Render its actual outcome; HTTP 200 alone is not success.
- Distinguish observed balances, projected balances, reserved funds, and available-to-spend values. Never relabel one as another.
- Keep missing/stale/partial data explicit. Do not fill gaps with fictional values or derive money from illustration dimensions.
- Artwork must not obstruct tap targets, focus, text selection, zoom, scrolling, or safe-area padding.

## 4. Visual system

Starting tokens (tune against the images and measured contrast):

```css
:root {
  --obs-bg: #172334;
  --obs-surface: #202b40;
  --obs-ink: #eee4cf;
  --obs-muted: #b7b8cb;
  --obs-lilac: #c1a9e2;
  --obs-mint: #a5d4bf;
  --obs-apricot: #f3b272;
  --obs-brass: #c6aa71;
  --obs-paper: #ead8b5;
  --obs-paper-ink: #20263b;
  --obs-danger: #f1a29a;
  --obs-space-1: 4px;
  --obs-space-2: 8px;
  --obs-space-3: 12px;
  --obs-space-4: 16px;
  --obs-space-5: 24px;
  --obs-space-6: 32px;
}
```

Use the existing licensed project serif if suitable; otherwise select and bundle a licensed readable serif and sans family. Maximum two families. Serif: wordmark, page titles, hero figures, selected editorial headings. Sans: controls, dates, source labels, dense data, validation. Use tabular numerals for money and comparisons.

Mobile sizes: body 16px, supporting labels 14px, page title 32–40px, hero amount 44–56px, ordinary row amount 20–24px. Wordmark about 28px. Never put essential information below 14px to accommodate decoration. At narrow widths reduce ornament before text.

Use cream for primary text; lilac for selected navigation and secondary emphasis; mint for confirmed funding/incoming values; apricot for primary actions and upcoming events; coral for problems. Pair every status color with text/icon. Outgoing money is not automatically an error. Verify WCAG AA contrast on both indigo and parchment, including texture overlays.

Texture is subtle, low contrast, and static. Fine brass lines and occasional stars establish the theme. Reserve elaborate illustration for a page's main object. Activity and Settings need quieter treatment than Today. Avoid uniform card grids, arbitrary gauges, excessive stars, glow effects, and marketing copy that displaces useful data.

## 5. Artwork and asset construction

Create a separate asset set under `static/img/meridian/observatory/`:

- `observatory-engraving.webp`: decorative transparent observatory/landscape.
- `moon-engraving.webp`: optional small moon illustration.
- `paper-texture.webp`, `ink-texture.webp`: seamless restrained texture tiles.
- `dial-ornament.svg` or transparent raster: ornamental engraving only, no ticks/numbers/labels/pointer.
- `map-ornament.svg` or transparent raster: decorative star-map lines only.
- `ticket-corners.svg`: reusable decorative corner treatment, or a simple CSS border treatment.

Use approved source art or image generation for detailed engravings. Do not approximate the observatory with piles of CSS shapes. Inspect transparency; a checkerboard baked into a PNG is not transparency. Do not extract text from a generated screenshot and use it as a UI label.

For tickets, keep the center stretchable and the corners fixed-size (nine-slice border image or layered corner assets). Text must reflow independently of ornament. SVG monetary geometry and pointer remain code-owned; decorative asset editing never changes calculations. Decorative images use empty alt text and `pointer-events:none`.

Keep an asset manifest with source, generation prompt/license when applicable, intended dimensions, and decorative/interactive role. Export at sufficient resolution for 2x displays, compress, and avoid shipping entire multi-megabyte mockups as backgrounds.

## 6. Shared shell and components

Extend current files under `templates/meridian/`, `static/css/meridian/`, and `static/js/meridian/`.

Create reusable primitives: ObservatoryHeader, WorkspaceNavigation, ParchmentTicket, InstrumentFrame, MoneyValue, SourceStamp, StatusLabel, EvidenceSheet, ActionReceipt, EmptyState, and VirgilNote. They may be Jinja partials plus small JS renderers, not a new component framework.

Header: Meridian wordmark, Settings; page heading below. Bottom navigation: four equal tap areas, icon + visible label, active underline plus lilac. Respect `env(safe-area-inset-bottom)` and reserve matching content padding. Desktop uses a side rail and a bounded content region, not a giant stretched mobile screen.

Every overlay needs accessible name, Escape dismissal, focus trapping while modal, focus restoration, scroll management, and explicit close. A drawer must not replace an edit form during typing. Polling may update underlying state without stealing focus or discarding drafts.

## 7. Today and the dial

### Information hierarchy

1. Date and current available-to-spend value, horizon label, source observation time.
2. Interactive time dial, selected event, and next events.
3. Evidence ticket for the selected event.
4. One useful Virgil observation and scenario entry.

The current hero stays anchored to today. Selecting a future day changes a separately labeled projected value, not the observed current balance. If projected balance is unavailable, show the dated events with no invented projection.

### Proposed view model

Adapt existing APIs into this contract; do not assume this endpoint exists:

```ts
type Money = { minor: number; currency: string }; // integer minor units
type DialEvent = {
  id: string; date: string; // YYYY-MM-DD in owner's timezone
  kind: 'bill' | 'income' | 'goal' | 'transfer';
  title: string; amount: Money;
  fundingStatus: 'reserved' | 'partial' | 'unfunded' | 'unknown';
  reserved?: Money;
  source: 'crew' | 'manual' | 'evidence' | 'inferred';
  observedAt?: string; // timestamp with offset
  evidenceIds: string[];
  detailHref?: string;
};
type DialModel = {
  timezone: string;
  today: string; horizonEnd: string;
  availableToSpend: Money | null;
  freshness: 'fresh' | 'stale' | 'partial' | 'unavailable';
  observedAt: string | null;
  events: DialEvent[];
  projections: Array<{ date: string; balance: Money | null }>;
};
```

Use integer minor units at the rendering boundary, with currency-aware conversion from the existing dollar-valued model. Do not multiply every currency by 100 blindly. Never add different currencies without an explicit conversion source; show separate totals or unavailable.

### State

```ts
type DialState = {
  selectedDate: string;
  selectedEventId: string | null;
  mode: 'today' | 'explore' | 'scenario';
  drag: null | { pointerId: number; lastAngle: number; accumulatedAngle: number };
};
```

Keep state separate from rendering and API fetching. One pure reducer handles select-date, select-event, drag-start/move/end, return-today, and replace-data. Retain selection across refresh if the event still exists; otherwise select the same day and announce the change. Never infer approval from a selected event.

### Geometry

Implement `dial.js` with pure date/angle helpers and `dial.css` for layout. Use inline SVG with a stable viewBox, e.g. `0 0 600 600`, center `(300,300)`, track radius `245`. The decorative layer sits below it. CSS controls overall size; no per-device hardcoded pixel coordinates.

Use an open 240-degree arc from -120 to +120 degrees, measured clockwise from twelve o'clock. Its gap is at the bottom. This prevents a full-circle wrap from confusing the beginning/end of the horizon. It is an intentional usability refinement of the illustrated draft.

For civil-day index `d` in a horizon of `N` days:

```text
t = clamp(d / N, 0, 1)
angle = -120 + t * 240
x = cx + r * sin(angle * PI / 180)
y = cy - r * cos(angle * PI / 180)
```

`N = max(1, civilDaysBetween(today,horizonEnd))`. Use calendar-day arithmetic in the owner's timezone, not elapsed milliseconds divided by 86400000: daylight-saving days differ in length. Missing payday: use a labeled 14-day upcoming-events horizon, never invent a paycheck. Today/payday dates derive from data.

Render a tick per day, but show labels only for today, selected day, major events, and horizon end. At longer horizons thin labels; don't squeeze them. Pointer points to selected date. Same-day events share one marker with count; selecting it opens an ordered list, never overlapping labels.

All external labels should be HTML positioned in a separate layout column/list. Connector lines may be SVG decoration. Resolve collisions with vertical spacing; when labels cannot fit, replace them with an event list beneath the dial. Never crop monetary text to preserve an illustration.

### Pointer interaction

- Start drag only on the thumb/track, not the entire panel. Keep normal page scroll available outside that small interaction region.
- Convert pointer coordinates into SVG coordinates using `getScreenCTM().inverse()`.
- Calculate angle with `atan2(x-cx, -(y-cy))`; unwrap consecutive angular differences into [-180,180] and accumulate during drag so crossing the angle discontinuity cannot jump to the opposite endpoint.
- Clamp to the arc; snap to the nearest civil day. Capture the pointer on drag start and handle pointerup, pointercancel, and lostpointercapture.
- During drag update local selection via `requestAnimationFrame`; do not fetch, write, or announce every movement. Announce selection on release.
- Tapping a marker selects its event and opens/updates the evidence ticket. Tapping a date selects the day. Provide Previous day, Next day, and Back to today controls.
- One accessible range control can drive the same date index. Label it 'Explore upcoming dates'; expose meaningful `aria-valuetext`, e.g. 'Friday September 11, Electric bill, 84 dollars, reserved'. Arrow keys move one day; Home/End select horizon boundaries.
- All interactive markers also have semantic buttons/list equivalents. The dial must be fully operable without dragging or vision. Decorative SVG is hidden from accessibility APIs when the HTML controls provide its semantics.

### Motion

Pointer settles over 160–220ms after keyboard/tap selection; no delayed tracking during drag. Ticket content transitions in 120–180ms with minimal translation. Reduced motion disables rotation animation and translation. No automatic spinning, parallax, compulsory sound, or expensive ambient animation.

### Evidence ticket

Selected bill: name, due date, bill amount, reserved amount, funding status, source and observation time, evidence links, and View bill. If evidence is missing, explicitly say so. If underfunded, show exact shortfall. Do not claim 'covered' because the source returned a success flag.

The ticket expands into an accessible detail sheet with the calculation and source records. Display documents in the established protected evidence viewer. A dated source and a current balance are different facts; retain both dates.

## 8. Plan suite

Main Plan: foldout-map art behind a real allocation summary. Bills, goals, and available money are semantic links/buttons with precise amounts. Decorative constellation distances do not encode money. Follow with upcoming commitments grouped by date, funding tracks, source labels, and Add bill/goal.

Rules tab: grouped existing rules with readable trigger → condition → effect summaries. Show schedule and paused state. Edit opens a form prefilled with every supported current field; omissions must not clear unrelated Crew configuration.

Crew tab: operation controls organized by purpose (bills, pockets, cards), not raw GraphQL names. Hide unsupported controls or explain unavailable capability honestly. No 'deferred' item next to a working duplicate control.

Scenario mode: visually persistent 'Preview — no changes applied' label. Preserve the base plan. Hypothetical input updates deterministic projections. Compare before/after and allow discard. Applying a scenario creates a reviewable proposal with exact changes; it never silently executes because a slider moved.

Bill/goal detail: name, source, amount, schedule, reserved/remaining, related evidence, edit action. Destructive actions separated from ordinary editing. Approval displays validated before/after, unchanged important fields, destination, and effect. Preserve single-attempt execution and show actual verified/uncertain outcomes.

## 9. Activity suite

Timeline: quiet observation ledger, full merchant names, right-aligned amounts, date headings and compact account/source labels. Search/filter if already supported; preserve cursor pagination and scroll position.

Review: clearly say 'Suggested category'. Confirm category and Change share one aligned action row. Change opens a real editor, optionally applying a rule to future matches. Show exactly the scope of that rule. Category approval is never phrased as payment approval.

Patterns: human-readable comparison and optional small chart, with period labels and clickable actual evidence transactions. Never expose raw evidence IDs as the explanation. No claim of spending increase without a valid comparison window.

Transaction detail sheet: merchant, raw description, amount/currency, date, account, pending/posted state, category/editor, related transfers, notes and source stamp. Artwork stays small here. Do not use oversized illustrated circles on every row if that reduces scanability.

## 10. Accounts suite

Parchment summary ticket uses actual supported totals; group currencies separately. Account rows show name, balance, available balance where meaningful, provider and source age. Tapping opens account detail and filtered activity.

The constellation is a navigational motif; ordering and connections must not imply unsupported ownership or transfer relationships. Use semantically appropriate icons: a Wi-Fi symbol does not mean bill reserve merely because it appears in the generated draft.

Connections summary must use computed freshness, not just last healthy status. Assets/documents entry opens existing memory records and evidence. Never fabricate warranty/contract counts.

## 11. Settings and remaining surfaces

Settings groups: Connections; Preferences; Security & data. Use parchment section headers with ordinary HTML rows on indigo. Include only implemented features. A backup control shown in a mock is a proposal until a verified backup/restore workflow exists.

Connection detail: provider identity, last observed/successful read, errors in plain language, reconnect/revoke controls. Credentials never appear in rendered source, screenshots, or analytics.

Login: bring Meridian wordmark, type, indigo/paper palette and a restrained observatory engraving into the existing authentication flow. Preserve passkeys, password behavior and error handling.

Virgil: contextual sheet/panel anchored to the current record, with answer, actual evidence links, and separately reviewable proposals. Avoid a floating button that obscures navigation or row controls.

Action history: show proposed, approved, executing, confirmation-needed, verified, rejected/expired, and failed states as supported by backend. Unimplemented state names must be mapped explicitly or implemented before UI claims them. Preserve unfinished actions after reload. A success receipt includes the exact applied change and readback time; unknown outcomes stay visible and do not offer blind retry.

## 12. Responsive and accessibility contract

- Test widths 320, 390, 430, 768, 1024, 1440; content can scroll vertically.
- Under 380px, event labels move below the dial; the ring can shrink, text cannot become tiny. Preserve hero and one immediately useful next event near the top.
- Tablet: dial and evidence side by side when they fit. Desktop: navigation rail, central dial/plan, side evidence panel; max content width about 1280px.
- Minimum 44px touch targets, visible focus, semantic heading order, no color-only meanings, no essential hover-only content.
- At 200% zoom, controls and labels reflow without horizontal page overflow. Keep a text event-list alternative to the instrument.
- Safe-area spacing, large-text settings, keyboard navigation, reduced motion, loading/error/empty/stale states all need visual checks.
- Loading uses quiet placeholders with no fabricated amounts. Error retains last trustworthy data and names its age. Financial difficulty uses calm explicit language and actionable detail, never cheerful claims contradicted by data.

## 13. Implementation sequence

1. Verify active checkout/runtime and existing work. Inspect these reference images directly. Inventory current routes/components/data contracts; record gaps.
2. Produce/extract clean decorative assets and create tokens/shared shell in an isolated preview using synthetic fixtures and no live mutation access.
3. Build dial date geometry and state reducer as pure functions; then SVG, HTML controls, keyboard and pointer interaction. Connect fixture data first.
4. Build Today and the evidence sheet. Verify at narrow mobile sizes before adding ornament.
5. Extend Plan, Rules, Crew controls, scenario preview, Activity modes/detail, Accounts/detail/memory, Settings/connections, login and Virgil using shared primitives.
6. Connect real read APIs via adapters. Never import server secrets into frontend. Resolve missing business logic separately; no client-side fictional fallback.
7. Connect existing approved write paths only after exact outcome/error mapping is verified. Keep financial correctness fixes from the audit in the work queue; the visual redesign does not close them.
8. Capture matching screenshots against every selected draft, inspect interactions and accessibility, correct layout, then run appropriate existing tests and deployment gates.
9. Deploy only a specifically identified tested artifact with verified data backup; inspect actual served behavior before calling the redesign delivered.

Suggested additions: `static/js/meridian/dial.js`, `static/css/meridian/observatory.css`, `static/css/meridian/dial.css`, decorative assets folder, a dial partial and evidence-ticket partial. Integrate with existing `today.js`, `plan.js`, `activity.js`, `accounts.js`, `connections.js`, `shell.js`; avoid duplicate listeners and global state hidden in DOM attributes.

## 14. Verification and acceptance

Meaningful dial tests: date↔angle round trip; endpoints; N=1; same-day events; month/year/leap-day boundaries; DST; missing payday; pointer angle discontinuity; cancellation; refresh removing selected event; no data; unavailable projection; multiple currencies. All interaction tests use synthetic data.

Browser tests: drag and keyboard select the same day; event click changes correct ticket; scrolling outside track works; focus survives refresh; Escape restores focus; 320px no label collision; zoom/reduced-motion work; no network mutation occurs during dial/scenario exploration. Confirm failed execution is never success-styled and review shows exact parameters.

Visual checks: same viewport and similar fixture data as reference, real text crisp, no clipped controls, readable paper/ink contrast, consistent nav, controlled ornament scale. Inspect screenshots, not merely their existence. Test empty, stale, error, many-event and long-name cases in every workspace. Mock-image dates/artifacts must not become source code constants.

Completion report must distinguish implemented, tested, visually verified, deployed, and owner-verified work. This specification and these PNGs alone meet none of those implementation gates.

## 15. Copy-paste instruction for another implementation agent

> Read `design/observatory-drafts-2026-09-08/BUILD_SPEC.md` and inspect all seven referenced PNGs. Implement the Meridian Observatory design in the current ORSC repository, preserving its existing stack, current branch, unrelated changes, and banking safety boundaries. Start by checking current repository instructions and runtime identity. Work in small demonstrable slices: shared visual system, accessible data-driven dial, Today/evidence, then the other workspaces. Keep all money and text live HTML and the dial geometry code-owned; use separate decorative assets. Never use the mockup as a full-screen background or substitute sample data for unavailable live values. Keep exploration read-only. Verify responsive layout, pointer/keyboard interactions, real outcome handling, and screenshots before deployment. Report remaining gaps honestly. Do not execute live financial mutations as tests.
