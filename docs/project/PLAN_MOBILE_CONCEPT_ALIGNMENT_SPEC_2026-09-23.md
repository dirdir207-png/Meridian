# Plan (mobile) — concept alignment spec, owner-directed 2026-09-23

**Status:** approved by the owner as the next slice. **DELIVERED 2026-09-23 (OS-089)** — see
"## 10. Resolution" below, which records every point where the built result departs from this
document and why.
**Supersedes nothing.** Extends D-022 and the 2026-09-23 mobile bill-row work.
**Read with:** `design/observatory-drafts-2026-09-08/02-plan.png` (the governing Plan concept),
`MERIDIAN_DECISIONS.md` D-021 (image generation) and D-004 (newest governing visual record wins).

---

## 1. Owner direction, verbatim

> "I want the medallion work done, so everything matches the plan concept. Admittedly the app or
> preview has more info for bills. Lets make that information fit in a cohesive and visually
> appealing way. Right now reserved is over the dollar amount in the live app, and the evidence has
> really no styling at all. Lets generate a small evidence glyph that opens the evidence, bills
> with names that are too long can be intelligently truncated if need be, and underfunded/funded
> etc can be typed next to the bill name (like it is on everything but verizon payment arrangement,
> the word bill can be removed and the next date can be added to the drop down. Actually, all the
> additional info can be added to the drop down, which would then display all of the attached
> evidence. The evidence Icon can just be an indicator that evidence exists. As it sits, with all
> the extra info, the next income and add a bill don't fit on the first page and add a bill or goal
> is still short and situated next to new autopilot rule, instead of stretching the length of the
> page. September coverage can be moved under those two fields. Next paycheck can be made to look
> like the app too, with the generated icon."

Authorised spend: *"If we need to match them with runway, we can spend that"* (2026-09-23).

---

## 2. Measured current state (preview, 420x912, dark)

Measured rather than recalled. Do not re-derive these; re-verify only if the code moved.

| Fact | Value |
|---|---|
| `Add a bill or goal` width | **213px** in a 388px row, beside `New autopilot rule` (128px) |
| Section order | map → bills → `SEPTEMBER COVERAGE` + `NEXT PAYCHECK` (one grid) → create actions |
| `.m-plan-cell-funded::before` | `content: "Reserved"`, `display: block`, `margin-bottom: 4px` |
| `.m-plan-cell-name` text | `"Electric\nBILL"` — the word BILL is a separate span |
| `.m-bill-badge` | `display: inline-block; margin-left: 0.5rem` |
| section heading | DOM text `Commitments`, rendered `COMMITMENTS` by `text-transform: uppercase` |
| section/table `aria-label` | BOTH are `Commitments` — two attributes, not one |
| `.m-invoice-link` | pill whose `background` is `--m-surface-muted` and `border` is `--m-border` |
| bill row height | 113px collapsed, 162px expanded |

### The two defects are real, and both have a mechanical cause

1. **The evidence control reads as unstyled.** It *is* styled — but with
   `background: var(--m-surface-muted)` and `border: 1px solid var(--m-border)`, and inside a D-022
   dark box those resolve to `rgba(238,228,207,0.08)` and `rgba(238,228,207,0.16)`. So the pill is
   a faint wash on a dark surface and reads as plain text. This is the same class of bug D-022
   already recorded: a value chosen for one surface, kept after the surface moved.
2. **The badge disappears on long names.** `.m-bill-badge` is `inline-block` with a left margin
   inside a wrapping name row, so `Verizon Payment Arrangement` pushes it out of position. The
   owner reports it as *"like it is on everything but verizon payment arrangement"*.
3. **"Reserved" over the figure** is a crowding report, not a measured overlap: on the preview the
   label is a `display: block` line with a 4px gap above the figure, both right-aligned. Read it as
   "too tight to read as a label", and note that **the owner's own fix removes it anyway** (§3).

---

## 3. Target structure

### Collapsed row — matching the concept's density

The concept's row is **name over date** on the left, **figure over `Reserved`** on the right, then a
chevron:

```
[ medallion ]  Electric …truncated…  [status]      $84        [◈]  [>]
               Sep11                              Reserved
```

- **Medallion** — the concept's per-bill medallion (§5).
- **Name** — truncated intelligently (§4).
- **Status** — `Underfunded` / `Funded` / `Due soon` etc. typed next to the name, ALWAYS, including
  when the name is long. This is the badge, moved so it cannot be pushed out.
- **Date** — the bill's next date, under the name, exactly where the concept puts `Sep11`.
  **This is a CORRECTION to the first draft of this spec.** That draft moved both the fact line and
  the `NEXT` column into the panel, which would have left the collapsed row with no date at all —
  plainly contradicting the concept, which shows one. The app carries that date TWICE today: as
  `due …` inside the fact line, and as the `NEXT` column. The fix is to keep ONE and drop the
  duplicate, not to drop both, and do not assume which without looking.
- **Figure** — the reserved amount in the concept's orange (`#f2873e`, measured from 02-plan.png).
- **Evidence indicator** (§6) — an ICON ONLY, present only when evidence exists.
- **Chevron** — the existing disclosure (`m-plan-row-toggle`, `aria-expanded`, `data-expanded`).

### Disclosure panel — everything else

All additional information moves into the panel, which the owner explicitly wants:

- the `NEXT` column, which is the DUPLICATE of the date kept above (drop the duplicate, never the
  date itself)
- the `$X of $Y · backed by …` fact line
- the funding progress bar
- **every attached piece of evidence**, in full, each opening its invoice
- the existing actions (`Edit funding`, `Save to Crew`, `Delete`)

Consequence to verify: the collapsed row must measure SHORTER than the 113px recorded in §2 — it
loses the fact line, the progress bar and the duplicate `NEXT` block, while keeping the name, the
status, ONE date, the figure, the evidence indicator and the chevron. If it does not get shorter,
the panel did not absorb them.

---

## 4. Truncation

"Intelligently truncated if need be." A naive CSS `text-overflow: ellipsis` is acceptable for the
NAME, but:

- the **status badge must never be the thing that truncates or wraps away** — it is the signal;
- truncation must not hide a name that distinguishes two bills. `Verizon Payment Arrangement` and
  `Verizon Payment` must not collapse to the same visible string. If a simple ellipsis does that,
  prefer a slightly smaller font over a hard cut;
- the FULL name must remain available: in the disclosure panel, and in the accessible name. A
  `title` attribute alone is NOT sufficient (it is not reliably announced and never appears on
  touch). Put the full name in the panel heading.

---

## 5. Medallion work — this is OS-087, and it is the headline

Colour and structure are already unified (Accounts, Plan map, Settings, dock). What remains is
MATERIAL: the concept's medallions are rendered metal — a bevelled brass ring with highlight and
shadow, and a finely engraved glyph — while the app composes them from a flat disc, a 2px border,
inset shadows and a single-colour SVG mask.

**Do this first, in this order, because it is the owner's stated priority:**

1. Read the live Runway balance (`RUNWAY_GET_ORGANIZATION` / `RUNWAY_GET_USAGE`) and STATE the
   planned spend to the owner before generating. D-021: a generation is a SPEND.
2. The previous attempt failed with `upload_http=403 SignatureDoesNotMatch` on the presigned
   `Policy` field — a mistyped base64 character, not a model failure. Transcribe every presigned
   field exactly; `file` last.
3. Ask whether ONE generated RING asset can lift every medallion at once, before generating per
   glyph. `kit-2026-09-16/medallion-frame.png` is already real brass art used by Accounts,
   Settings, Activity and the bill rows, so the ring is the cheapest honest win.
4. Bill medallions specifically: the concept's bill rows use the **"Bill Reserve" pattern** —
   tinted disc, dark glyph — which is NOT the map's dark-disc-with-brass-glyph. Both are in the
   concept; this is a second component, not a contradiction. See OS-088 for the blocking data gap.

Generated art must ship with a design record (README + `assets.json` with kind, source_reference,
dimensions, mode, sha256 verified by recomputation), a row in `design/README.md`, and TRACKED files.

---

## 6. Evidence glyph

"Generate a small evidence glyph that opens the evidence." One new asset, the app's own scale
(20-24px, matching `[data-nav-icon]` and the settings medallions), used as:

- an INDICATOR in the collapsed row — icon only, no text, and **absent when there is no evidence**
  (never a disabled icon that implies missing evidence exists);
- the panel's evidence entries remain the places that actually open each invoice.

Accessibility: the indicator is decorative-per-row only if the collapsed row already communicates
that evidence exists in text. If it does not, the indicator needs a real accessible name
(`Evidence available`) — an unlabelled icon that is the only signal for content is a defect.

---

## 6a. Copy changes

- The section banner reads **`Commitments`** today (measured: DOM text `Commitments`, rendered
  `COMMITMENTS` by `text-transform: uppercase`); the governing concept's banner is
  **`Upcoming bills`** — the owner confirmed this against the concept artwork on 2026-09-23 with
  *"I was referring to this"* and *"It says commitments in the preview"*. Rename it to
  **Upcoming bills**.
- Remove the **`BILL`** tag beside each name (owner: *"the word bill can be removed"*). This is
  also what frees the space the status badge needs in §3.
- **One wrinkle to resolve while implementing, not to skip.** The section's own creation control
  says *"Add a bill or goal"*, so this list CAN hold a goal, while the concept's banner says bills.
  The owner's direction is that these particular rows are bills, so the heading follows the
  concept — but if a goal row can appear here, then either the heading or the creation control is
  telling the user something untrue. Decide which, make the copy agree with itself, and record the
  choice. Do not leave a heading and a button disagreeing about what the list contains.
- The section's `aria-label` must agree with the visible heading. Today the markup carries
  `aria-label="Commitments"` on the section AND `aria-label="Commitments"` on the table, so a
  renamed heading with stale labels would give screen-reader users a different name from sighted
  ones — a regression introduced by a purely cosmetic change.

## 7. Layout and order changes

1. **`Add a bill or goal` stretches full width.** Today it is 213px beside a 128px button.
2. **`New autopilot rule`** must be placed deliberately, not left as the leftover half of a
   two-up row. Decide and record: stacked under, or a quieter full-width secondary.
3. **`SEPTEMBER COVERAGE` moves UNDER those two controls.** Today the summary grid (coverage +
   next paycheck) sits BETWEEN the bills and the buttons.
4. **`NEXT PAYCHECK` should match the app**, with the generated icon (§5).
5. Consequence to verify: the owner's complaint is *"the next income and add a bill don't fit on
   the first page"*. After truncation, the panel move and the full-width button, confirm on
   420x912 that the income strip AND the add control are reachable in one screen. That is the
   acceptance test, and it is the reason for the whole slice.

---

## 8. Acceptance criteria

- A capture at 420x912 (dark and light) shows: one-line rows, the status badge beside EVERY name
  including a long one, an evidence indicator only where evidence exists, and no `BILL` tag.
- The collapsed row is measurably SHORTER than the 113px recorded in §2.
- The full name is present in the panel and in the accessible name.
- `Add a bill or goal` spans the page width.
- Section order reads: bills → next paycheck → add control(s) → September coverage → rest.
- Next income and the add control are both reachable in one screen at 420x912.
- Guards in `tests/meridian/test_plan_row_disclosure.py` are updated, not deleted, and a new guard
  covers the badge-with-long-name case and the evidence indicator's conditional render.
- `ruff` clean; full suite green; `session_close.py` exit 0; browser checks at the mobile viewports.

## 9. Non-goals

- Do not regenerate the app's 61-icon set. `HANDOFF_FOR_ASTRA_2026-09-19.md:200` forbids bulk
  replacement on initiative, and the owner's "brass everywhere" instruction was about the glyph
  treatment, which is already done.
- Do not infer a bill's category from its name (OS-088 says why).
- Do not change the desktop Plan table. The governing concepts are mobile-shaped; the desktop is
  tabled by the owner (*"The app is primarily mobile for my purposes"*).
- Do not merge to `main`. Branch only, per the owner's 2026-09-23 ruling.

## 10. Resolution (2026-09-23, OS-089)

Built on `feat/meridian-implementation`. Full detail is in D-023; this section exists so the spec
and the product cannot drift apart, and so the NEXT session reading this document does not re-file
a deliberate choice as a gap.

**Delivered as specified.** One-line collapsed bill rows (113/114px → **61/62px**); the fact line,
progress bar, invoice entries and duplicated NEXT figure moved into the existing disclosure, which
takes the full row width on mobile; the banner and both `aria-label`s read `Upcoming bills`; the
`BILL` tag is removed for bills; `Add a bill or goal` spans the width; the order is bills → next
paycheck → add controls → September coverage. The evidence indicator renders only where evidence
exists and carries the accessible name `Evidence available`.

**Four departures, each forced by a measurement and each recorded in D-023.**

1. **§3's diagram puts the status badge on the name line. It is on the DETAIL line instead.** At
   420px the name column is ~144px; an 85px badge sharing it left the name ~50px, which collapsed
   `Verizon Payment Arrangement` and `Verizon Payment` into the same visible string — the exact
   collapse §4 forbids. The name now takes the whole cell and truncates with a prefix ellipsis, and
   the badge cannot wrap away or be truncated. Two of §4's requirements were in direct conflict at
   this width; the one about distinguishable names won.
2. **The acceptance test in §8 could not be met by §7's changes alone.** The spec's three changes
   brought the add control from 1427px to 879px, and the mobile canvas ends at 826px. Two further
   mobile-only changes closed it, neither removing a control, figure or word: the `PLAN` kicker is
   dropped (it printed the word three times above the fold) with the headline down from 2.25rem to
   1.75rem, and the bills band is capped at a measured **120px**. Result: income strip fully on
   screen at 675..777px, add control top at 789px.
3. **§5's medallion work, and §7.4's "generated icon", needed no generation at all.** The kit
   already ships `medallion-frame.png` (a rendered bevelled brass ring with four rivets) and the
   income ticket is already the kit's parchment ticket flanked by compass stars. The Plan map's
   stations and hub now layer the real ring asset. **No Runway credits were spent.** What remains
   generative is the concept's engraved glyphs, which is the half worth spending on.
4. **The row medallion (OS-088's territory) ships in the app's unified disc, not the concept's
   tinted one.** The tint IS the category, and commitments still carry no category; the glyph
   therefore follows the commitment's TYPE, which is real data, and no colour is chosen by matching
   a name. OS-088 replaces the disc treatment, not the slot.

**One deliberate desktop content change**, contrary to §9's "do not change the desktop Plan table"
in letter but not in intent: `due <date>` is removed from the fact line, because the duplication it
removes is the desktop NEXT column's own. Column order, row height and row geometry are unchanged
(verified by diffing the governed desktop captures; structural difference 0.34%, entirely the map's
brass ring, the heading rename, that removed fragment, and the funding bar's move one line up).

### 10a. Second pass -- the owner's corrections after seeing the first build (2026-09-23)

He reviewed the build on his own iPhone Air and sent three corrections. D-023 point 6 carries the
full record and the measurements; the summary, so this spec is not read as final where it has been
superseded:

- **The progress bar's placement in SS3 is superseded.** *"Also I would still want progress bars"* --
  the bar is back ON the collapsed row as the concept draws it (a 2px hairline with an end dot at the
  funded share), not in the disclosure. Exactly one bar exists, so the row and the panel cannot
  disagree.
- **The `Plan` headline is removed on mobile** and `Give every dollar a destination.` carries the
  block, centred -- pre-authorised by the owner (*"if need be, I would even remove the Plan and center
  give every dollar a destination"*). The top block is compressed toward the concept's ~148px.
- **The bills band is EXTENDED, not shrunk** -- 120px to `min(170px, 19svh)`, two and a half rows. The
  height came from the income ticket (102px to 68px: label, date and figure on one line with the
  caption beneath) and from the gaps, NOT from the map, which keeps its concept size.
- **His phone is NOT too small.** The iPhone Air is 420x912 CSS, exactly the `mobile-air` capture
  viewport and exactly the concept's own scale (852x1846 at 0.494). The concept fits because its top
  block is ~148px against the app's ~250px, not because its screen is larger. Recorded because the
  question will recur.
