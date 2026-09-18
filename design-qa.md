# Observatory / Today visual QA

## Reviewing the captures in chat (how to show images to the owner)

The owner reviews away from the machine, so evidence that requires opening a local directory is not reviewable
when it matters. The DSH web GUI renders an image when a message contains markdown image syntax with an
**absolute POSIX path**; the client rewrites it to the GUI's own same-origin `/api/file?path=…` endpoint, which
re-validates policy host-side and requires the session cookie. Because it is same-origin, the image also loads
when the GUI is reached remotely, with no extra server or tunnel.

```
![Today mobile dark](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/trackd-review/today-mobile-dark.jpg)
```

Rules that matter, taken from the client's own tests:

- The path **must be absolute** and POSIX. A relative path (`comparison.png`) and a Windows path are deliberately
  inert, and no image renders.
- Non-HTTP transports are inert, so this only works through the GUI.
- `/api/file` returns **401** without the session cookie — expected, and the reason a bare `curl` cannot verify it.

`artifacts/trackd-review/` holds every comparison downscaled to 760px wide as **progressive JPEG at quality 86**:
17 files, 71–191 KB each, 2.0 MB total. The originals are 1.2–1.7 MB PNGs, which is too heavy to load on a phone
and was the practical reason review stalled. Keep the full-resolution PNGs as the archival evidence and reference
these for review; do not treat the JPEG as the acceptance artifact, since it is lossy.

## Today — the day arc starts clear of the building (2026-09-18)

![Today mobile-air dark, the hand stopping clear of the observatory](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-dial-arc-2026-09-18/today-mobile-air-dark-viewport.png)

**Owner:** *"Can we modify the dial so that the lowest point on the left hand side is still above the building
imagery? It defaults into the building for today and is not visually appealing."*

**Root cause.** The arc ran −120°…+120°, so **today sat at −120°** and put the hand at (129,399) — exactly where
the kit's `dial-plate.png` draws the observatory. **The concept can't arbitrate this: its dial has no building**,
so this is the kit's addition.

**Measured the building by ray-casting the plate**, requiring an 8-sample run of light pixels so the sky's star
sparkles aren't mistaken for structure — without that run test, the first pass reported building on the *right*
side where there is none. The building intrudes into the sky disc **only between −140° and −110°**, reaching
inward to r=150–182 against a hand running r=118–198, with a near-vertical roofline (inner edge 165 at −110° →
283 at −105°).

**After:** `ARC_START` −120 → **−100**. The hand's r=198 tip clears the nearest building edge (r=283) by
**85 units on every day**, with a full-length hand throughout. **Accepted as matching** the requirement.

**Why not the alternatives.** Clamping the hand at the roofline would make it visibly change length for the 1–2
days in that band — a glitch, not a design. The full concept-arc rework moves every day much further and was
declined.

**Visible and intended:** every day moved by up to 20° at the lower-left, so the arc is now asymmetric about the
top (midpoint +10° rather than 0°). Drag clamps to the same range, so scrubbing and the rendered positions
cannot disagree.

## Today — the dial placed evenly in its band (2026-09-18)

![Today mobile-air dark, the dial centred in its band](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-dial-centring-2026-09-18/today-mobile-air-dark-viewport.png)

**Owner:** *"I am much less concerned with the size of the dial, I just want it evenly placed vertically."* That
resolves OS-035: the complaint was placement, never size.

**Before:** 0px above the dial, 252px below. `d0e0cd6`'s revert of `align-self: center` was correct that the old
rule failed to fix the report and wrong about what was wanted — with `align-items: start` the dial sat flush
against the panel's top with all 48px of its band's slack beneath it.

**The concept is the authority and agrees with you:** in concept 01 the dial spans ~435px inside a band whose
callouts span ~490px — roughly **25px above, 30px below**. Centred, not pinned.

**After:** **24px above / 24px below** inside the band. **Accepted as matching.** Unchanged at 1024px and
1440px, where the dial is taller than its band and there is no slack to distribute.

**The guard pointed the wrong way.** The test asserted `dial.y - panel.y <= 8` under the message *"The event list
must not vertically center the dial"* — it demanded the arrangement you rejected. It now asserts the dial sits at
the band's centre, which fails on both pinned-to-top and pushed-down-by-the-list.

**What this does not do:** balance space above and below across the *whole panel*, which is still 24 above / 228
below because the controls row and the evidence ticket sit below the band. Equalising that needs the dial's
column to span all three rows, which would crush the controls and the callout column into one strip. The concept
also carries substantial content below its dial band, so content below is not itself the defect.

## Accounts — the summary ticket tilted, notched and dotted (2026-09-18)

![Accounts mobile-air dark, the tilted ticket with punched notches and the dotted inset](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-accounts-ticket-2026-09-18/accounts-mobile-air-dark-viewport.png)

Read against concept **04**. Finding 4 had recorded this panel as "axis-aligned, square-cornered and plain"; the
concept sets it at an angle, punches a semicircular notch out of each side at mid-height, and insets a fine
dotted brass border.

**The angle is measured from two features inside the concept's own ticket**, which agree: its top edge (−3.7°
over 656 columns) and the brass rule under the amount (−3.21° over 104 columns). The panel takes **−3.2°**, the
cleaner purely-internal measurement. The text tilts with it, as the concept draws. **Accepted as matching** for
the tilt, the notches and the dotted inset.

**The notch is 36px against the concept's ~25px, deliberately, and the reason is measurable.** The concept's edge
is smooth, so a concept-sized bite reads at once; the kit's `parchment-ticket.png` already carries ~10px scallops
along that same edge, and at 22px the notch read as a *missing scallop* rather than a punched hole. The
enlargement is what makes the concept's gesture legible on the kit's edge.

**What was preserved:** the kit's nine-slice, its scalloped perforations and its corner rivets. These treatments
are **added to** the sanctioned panel, not a replacement for it, and a test asserts the nine-slice survives.

**Checked, not assumed:** a rotated box is wider than the box that laid out — 388×164 at −3.2° bounds to ~397px
against a 388px column. Zero horizontal overflow at 390/420/430px and at all five governed viewports in both
themes.

## Plan — the tabs as the concept's bordered bar (2026-09-18)

![Plan mobile-air dark, the bordered tab bar with its parchment active cell](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-plan-tabs-2026-09-18/plan-mobile-air-dark-viewport.png)

Read against concept **02**. The row of three pills in a muted trough was a **different construction**, not a
different shade: the concept draws **one rounded container with a brass border, divided into three equal cells by
thin vertical rules**, whose **active cell is parchment-filled with a brass star medallion at its left edge**.

Measured on the concept (852px wide, 0.493 to a 420px viewport): container ~733×82px → ~361×40px; active cell
254px = an equal third; medallion ~70px → ~34px. **Accepted as matching** for the construction, the cell division,
the active treatment and the medallion.

**Built to 44px, not the concept's 40px,** because the cells are buttons and 44px is the touch-target floor. A 4px
deviation recorded rather than a target quietly missed.

**Two real bugs surfaced during verification, and both had the same root.** The cells measured **148/119/119**,
not equal thirds: with `box-sizing: border-box` a zero flex basis is floored by the active cell's own 42px
medallion gutter. A one-third basis fixed it at the base rule — and then the existing `@media (max-width: 600px)`
block's `flex: 1` re-imposed `1 1 0%` **at exactly the widths the concept's equal cells matter**. Final measured
widths: 118.7/118.7/118.7 at 390px, 128.7 at 420px, 132 at 430px, labels fitting, no overflow.

**Deliberately different from Activity.** Activity keeps the ruled-underline treatment concept 03 shows; the two
workspaces are not meant to share one tab style, which is why this is scoped to `plan.css`.

## Bottom dock — taller, with the concepts' ornate glyphs (2026-09-18)

![Today mobile-air dark, the rebuilt bottom dock](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-dock-2026-09-18/today-mobile-air-dark-viewport.png)

Read against concept **01**'s dock. The owner asked for it to be *taller* with *more ornate icons*, and both
were true. Measured on the concept: the panel is **152px** tall in an 853px-wide frame (**17.8%** of width), a
rounded inset panel with hairline rules between workspaces, each glyph **stacked above** its label, the ringed
compass at ~**8.4%** of width (~34px at 420px), and the active workspace marked by a lilac rule **under** its
label with **no fill** behind the item. The app had a **65px (15.5%)** full-bleed bar, **20px** Bootstrap
silhouettes, **12px** labels, glyph *beside* label, and the marker *above* the glyph.

After: **76px = 18.1%** at 420px (ratio 1.02 against the concept), glyphs **34px**, labels **15px**, stacked,
rounded and inset, with the marker under the label and the fill removed. **Accepted as matching** for the dock's
height, structure, icon weight and active treatment.

**The four glyphs are in-repo engravings, drawn to the concept:** a ringed compass rose with cardinal ticks, a
folded three-panel map carrying a dotted route and a cross, four ascending columns on a baseline, and a ringed
profile. They stay single-colour CSS masks driven by `currentColor` — the concept inks the active glyph lilac and
the rest muted, which is exactly what that mechanism does, so nothing about the theming changed.

**Superseded, not deleted.** The kit's `compass/map/bar-chart/person-circle` Bootstrap glyphs no longer serve the
dock, but they remain on disk and still serve the surfaces that use them (the Activity row glyphs). One guard
hard-coded those filenames and was reconciled to check the invariant instead — one workspace, one real glyph, both
mask properties — because the path was the brittle part, not the intent.

**Not touched:** the desktop rail. Re-measured at 1440px: 150px wide, row layout, 20px glyphs, no inset, zero
overflow.

## Today dial — the runs to nowhere, and the centring that was reverted (2026-09-18)

**The owner's connector report is confirmed, and it only appears once the horizon is long enough to scroll
the rail.** With 14 events the rail's content is **1591px** in a **330px** box; before the fix all 14 rows got
a run and **11** of them were below the rail's visible area, so those runs left the dial, ran past the rail to
`y=1754`, and were sliced off by the connector layer's own `overflow: hidden` at `y=746.9`. Visually: dashed
lines descending from the dial and simply stopping. That is *"connecting to nothing, several lines"*.

A run is now drawn only when its own row's centre is inside the rail's visible box, and the rail re-anchors
the runs on scroll. 14 runs became **3**, each ending exactly on its visible row, and scrolling re-anchors to
the newly visible rows (`ev-7/8/9` mid, `ev-11/12/13` at the bottom) with none left off-screen.

**The centring added on 2026-09-16 is reverted.** It balanced the dial *within its grid row*, which is not
what the owner reported: the void is the second panel row (controls + evidence ticket), which no `align-self`
can reach. Worse, it tied the dial's vertical position to the event count — at 390px a 12-event horizon
pushes a 240px dial 30px down a 300px row — so the layout moved as the list grew. The dial sits at its row's
top again, and the rail's cap is now derived from the guard `rail.height <= dial.height + 48`
(`calc(100vw - 102px)`) instead of the 12px-overshooting `calc(100vw - 90px)`.

**What is NOT claimed:** the large void under the dial is still there and is a composition question — the
dial is 63.6% of viewport width against the concept's 82.5%, and the callout column is a hard 130px floor.
Fixing it means relocating the callouts, which is the owner's decision, not a tweak. 3 of the 9 pre-existing
browser failures went green with this work; the other 6 are unrelated (4 are the topbar theme-toggle label,
2 are a dial/rail clearance expectation that conflicts with the documented clearance decision).

## Accounts — the supplied archive-building illustration (2026-09-18)

![Accounts mobile-air dark, the supplied archive-building ticket illustration](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-accounts-building-2026-09-18/accounts-mobile-air-dark-viewport.png)

**The missing Accounts asset arrived.** This closes **OS-039**, which was recorded as blocked because it could not
be closed by effort: the concept draws a colonnaded domed building on the Accounts surface, the kit's only fit was
`observatory-landscape.png` — the *Today dial's* hilltop observatory — and presenting that as a match would have
been the same class of unsanctioned reuse the Accounts-strip guard exists to prevent.

The owner supplied `accounts-ticket-building.png`: a colonnaded domed archive building with an arched entrance, a
gilt dome, scrolls, a wax-sealed document and an open ledger. It is the Accounts page's own document-and-structure
motif, and it replaces the provisional reuse of Today's building on this surface. **Accepted as the Accounts
illustration.**

**What it is, recorded precisely.** It is *not* a reproduction of the concept's "colonnaded domed rotunda on a
rocky knoll" — this building stands on a flat plinth among foliage and scrolls. It is recorded as the owner-supplied
governing art for this surface, and no pixel-equivalence with the concept engraving is claimed.

**Verified, not assumed.** Decoding the PNG confirms genuine transparency rather than a baked-in backing: alpha
range 0..255, **56.2%** of pixels fully transparent, all four corners `(0,0,0,0)` — the handoff's "real
transparency" rule. Rendered at 420×912 DPR 3 in the isolated synthetic preview, the art box measures **92×92**
(its `clamp(92px, 28%, 188px)` minimum) in a **1:1** box, the resolved background image is the new asset, and the
engraving reads cleanly on the parchment with the parchment showing through.

**A red suite was left behind, and is now green.** The parallel lane swapped the asset and updated
`test_accounts_ticket.py`, but `test_accounts_assets_strip.py` still asserted the old asset was present, so the
suite failed on `HEAD`. Its intent was restraint, not a specific filename, so the guard was reconciled to assert
*both* restraints — Accounts borrows neither the Activity telescope *nor* Today's `observatory-landscape.png` — and
that its own asset is present and on disk.

**A size note, recorded rather than acted on.** The asset is **2.0 MB** for a display slot of at most 188 CSS px.
That sits within the project's existing precedent (`dial-plate.png` is 3.0 MB, `accounts-ticket-building.png` is
second at 2.0 MB) and its alpha is correct, so it ships as supplied; downscaling the owner's art is an optional
follow-up rather than something to do unasked.

## Accounts — closing parchment strip (2026-09-16, batch 4)

![Accounts mobile-air light, closing Assets & Contracts parchment strip](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-accounts-assets-2026-09-16/accounts-mobile-air-light-full.png)

Read against concept **04**: the page now closes with the concept's compact parchment strip for tracked items, so
the ticket material frames both ends of the page — the summary figure at the top and the tracked items at the
bottom. **Accepted as matching** for the strip's material, placement and hierarchy.

**One deliberate omission.** The concept draws an engraving on this strip, and the kit has no counterpart for it:
the only engraving that would fit is the telescope, which the kit scopes to Activity with sparing reuse in
Settings. Rather than an unsanctioned reuse, the strip carries the ticket material and hierarchy with no
illustration, and a test asserts the telescope stays out of `accounts.css` so a later pass cannot quietly add it.

The label again needed a three-class selector — `.obs-shell .m-section-label` sets that colour at the same (0,2,0)
weight the summary panel tripped over in batch 1. Both sites now carry the rationale and a guard.

## Accounts — connector rail (2026-09-16, batch 3)

![Accounts desktop dark, dashed connector rail with per-row nodes](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-accounts-rail-2026-09-16/accounts-desktop-dark-viewport.png)

Read against concept **04**: the account rows are now threaded on the concept's dashed rail, with a small node
beside each medallion in that row's own tint. **Accepted as matching** for the rail's placement and the
constellation reading — the medallions belong to one structure rather than floating as separate tiles.

The rail stops at the first and last medallion centres instead of running the full row height, and rows without a
medallion (archived) are excluded rather than given a node that marks nothing. Its 30px left gutter costs real
width, so mobile was checked explicitly: zero overflow at all five viewports.

Still open in Accounts, and not claimed: the connection strip and the "Assets & documents" ticket.

## Accounts — account medallions (2026-09-16, batch 2)

![Accounts desktop light, account medallions with the kit ring](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-accounts-medallion-2026-09-16/accounts-desktop-light-viewport.png)

Read against concept **04**: each account row now carries the concept's medallion — a coloured disk inside the
kit's brass double ring with its four rivets. **Accepted as matching** for the medallion's anatomy and the row's
colour rhythm (lilac for cash, mint for savings).

The kit states the anatomy as a contract — "Decorative frame above a code-owned colored disk and semantic SVG
icon" — and all three layers are present: supplied ring, tinted disk, role icon. The glyphs were deliberately
*not* swapped for the kit set: the kit prescribes `bank` for reserves and has no equivalent for liabilities,
investments or reimbursements, so the existing role icons carry more meaning than the kit vocabulary would.

Still open in Accounts, and not claimed: the concept's connector rail linking the medallions, the connection
strip, and the "Assets & documents" ticket. Note the row beneath the preview banner in the mobile capture is
partly covered by that fixed banner — a capture artefact, not a clipped medallion.

## Accounts — parchment summary panel (2026-09-16, batch 1)

![Accounts mobile-air light, parchment summary panel](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-accounts-ticket-2026-09-16/accounts-mobile-air-light-viewport.png)

Read against concept **04**: the cash figure now sits on the concept's parchment panel, with the kit's dome
engraving — `observatory-landscape.png`, the asset whose name does not say "dome" — set beside it. Scalloped
ticket ends and corner rivets come from `parchment-ticket.png`; the figure and its provenance note stay
code-owned HTML. **Accepted as matching** for the panel's material, silhouette and figure hierarchy.

*Superseded 2026-09-18:* that dome engraving was the **Today dial's** building, borrowed onto Accounts pending
dedicated art. The owner has since supplied `accounts-ticket-building.png`, which this surface now uses, so
`observatory-landscape.png` no longer appears on Accounts at all. The panel's material, silhouette and hierarchy
still hold; only the illustration changed. See the section at the top of this file.

**The capture caught what the CSS did not.** The first render put "AVAILABLE CASH" in pale lilac on the
parchment — exactly the contrast failure the kit names — because my two-class override tied on specificity with a
later rule of equal weight. The selector is now three classes, with the reason recorded in a comment and pinned
by a test. The figure's signal colouring is suppressed on the parchment too: a cash total is not a warning, and
pale mint would not have survived the paper.

Still open in Accounts, and deliberately not claimed: the concept's large coloured account medallions with their
connector rail, the connection strip, and the "Assets & documents" ticket. The concept's panel is full width;
here it takes 2.1fr beside the Liabilities card so no existing figure is dropped — a layout adaptation, recorded
rather than presented as parity.

## Activity — orange ruled tabs and ticket actions (2026-09-18)

![Activity mobile-air dark, orange Review tab and filled/open ticket actions](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-activity-actions-2026-09-18/activity-mobile-air-dark-viewport.png)

![Activity desktop light, full-width starred rule and paired ticket actions](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-activity-actions-2026-09-18/activity-desktop-light-viewport.png)

Read against the newer `design/observatory-extension-2026-09-18/concepts/review.png`, not the historical
2026-09-08 draft. **Accepted as matching for this bounded presentation slice:** Review is selected in Astra's one
action orange (`#e99a48`), a decorative star sits above the selected label, one brass rule spans the tab row with
stars at both ends, and the two category controls share a clipped ticket silhouette. The confirmation control is
filled orange with dark action ink; correction is transparent over a page-coloured face with a continuous brass
ticket edge. Mint remains a status colour rather than an action colour.

At 420 and 430 CSS px the controls remain paired; at 390px they wrap deliberately so the longer existing
"Approve category" label stays legible. Every measured control is at least 44px high and no governed viewport has
horizontal overflow. Keyboard traversal reaches **both** controls with `:focus-visible` true, and each ring is a
3px inset stroke chosen to contrast with its own face — `--obs-action-ink` over the orange fill (**6.55:1**) and
`--m-ink` over the correction face (**13.5:1** dark / **12.78:1** light). The generated stars are decorative CSS
content, so they do not alter the accessible names or the pressed state.

**Two review findings were fixed here, and are recorded rather than quietly corrected.** First, `clip-path` severs
a normal border at every chamfer, so the first correction control rendered as detached strokes; it now uses two
stacked clipped polygons (brass edge, 1px-inset page-coloured face) for one unbroken outline. Second, orange text
cannot carry the selected tab in the light edition: `#e99a48` measures only **1.95:1** there, below the 3:1
large-text floor. The light edition paints the label in the handoff's own `--obs-action-ink` (**12.78:1**) while
the star and underline stay orange, and dark keeps the orange label (**7.45:1**). **The orange cue itself stays
1.95:1 in light** — the same order as the pre-existing brass hairline — so the readable selection state is carried
by the label, not by the star. Introducing a second, darker orange to chase 3:1 was rejected: the handoff's
one-action-orange rule forbids it.

Evidence: `artifacts/observatory-activity-actions-2026-09-18/` contains viewport and full-page images for
1440×900, 1024×768, 430×932, 390×844 and 420×912 in both themes. The ten manifest records have zero console
errors and zero horizontal overflow. An explicit UI-toggle probe produced a dark/light luminance split of
36.84/207.52 and computed the confirmation fill as `rgb(233, 154, 72)` over a brass edge
`rgb(198, 170, 113)`.

**Not claimed:** the "N categories to review" banner, because there is no pending-count source; or the copy change
to "Confirm category", because that text is generated by `activity.js` outside this presentation-only slice.
Review remains local category bookkeeping and never bank authorization.

## Activity — framed category glyphs (2026-09-16, batch 2)

![Activity mobile-air dark, framed category glyphs in review mode](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-activity-glyph-2026-09-16/activity-mobile-air-dark-full.png)

Read against concept **03**: each review row now carries its category glyph inside a thin ring with the concept's
small marker dot. **Accepted as matching** for the ring motif and the glyph placement.

The screenshot is the evidence for a bug this batch fixed: **Internet** and **Electric** both carry the category
"Utilities" in the fixture, so the first one-pass resolver painted a lightning bolt on the Internet row — the
precise confusion the kit's mapping warns about. Scanning the specific merchant text before the broad category
restores `wifi` for Internet and `lightning-charge` for electricity, and a Node round-trip pins both. That same
test caught "Steam", the concept's own example, resolving to nothing.

**Not claimed:** concept 03's parchment "N categories to review" strip. The payload has no "awaiting review"
field, so the count would have to come from a confidence threshold — a classification policy I will not invent,
and a derived figure that would sit where the concept shows a fact. It needs an owner decision.

The action plate and ruled-tab treatment were open in this 2026-09-16 batch; the 2026-09-18 Activity section
above records their later bounded delivery.

## Activity — the header vignette (2026-09-16, batch 1)

![Activity desktop dark, telescope vignette top-right](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-activity-vignette-2026-09-16/activity-desktop-dark-viewport.png)

![Activity mobile-air dark, telescope vignette in flow](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-activity-vignette-2026-09-16/activity-mobile-air-dark-viewport.png)

Read against concept **03**: the header copy is now left-aligned and the kit's telescope takes the top-right
station, matching the concept's composition and filling a left half that measurement showed was entirely empty
before this slice. **Accepted as matching** for the header structure and the art's station at desktop.

**One deliberate difference at mobile.** Below 601px the concept's one-word "Activity" heading becomes our
owner-accepted full sentence, so the free right column the concept relies on does not exist; an absolute vignette
there would overlap the heading or squeeze it, which the kit forbids in as many words. The art therefore moves
into the flow above the Filter button at 148px — inside the kit's 130–170px mobile band — keeping the heading's
full measure. This is recorded as a reasoned deviation, not presented as parity.

Still open from this 2026-09-16 batch was the parchment "N categories to review" strip. The later sections above
record delivery of the framed glyphs and ruled-tab treatment; the strip remains excluded because no pending-count
data source exists.

Evidence: `artifacts/observatory-activity-vignette-2026-09-16/` (5 viewports × 2 themes, full-page included) and
a header geometry probe at 1440/1024/420/390 confirming the copy's new left alignment, the unchanged desktop
header height and zero overflow.

## Plan — the primary action plate (2026-09-16, batch 3)

![Plan mobile-air light, primary action plate](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-plan-cta-2026-09-16/plan-mobile-air-light-viewport.png)

Read against concept **02**: the primary action now uses the kit's apricot action plate — chamfered corners,
triple edge lines, four rivets and fibrous apricot — behind the real "New commitment" button, whose label and
plus glyph stay HTML on the plate's blank centre. **Accepted as matching** for the action's material and
silhouette.

The slice offsets were measured from the asset rather than assumed: the plate occupies only y 171–515 of a 724px
canvas behind ~170px of transparent padding, so a uniform slice would have pushed the chamfer and rivets into the
tiled middle band and repeated them. The measured ~230px end caps became `190 230 190 230 fill / 10px 34px round`,
giving a 222×58 control at both viewports — above the kit's 44px target — with zero overflow.

Still open in Plan, and deliberately not claimed: row-level scale lines and chevrons on the commitment rows, and
the exact header/tab order. The concept places this plate as a full-width bottom CTA; it stays in the command
header here, which is a layout decision rather than a material gap.

## Plan — the next-income strip (2026-09-16, batch 2)

![Plan desktop light, next-income strip in place](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-plan-income-2026-09-16/plan-desktop-light-full.png)

Read against concept **02**: the next income is now the concept's perforated parchment strip rather than a dark
surface panel, reusing `parchment-ticket.png` — the kit's own stated role for it is "Evidence, account summary,
compact income ticket". Scalloped ends, cut corners and corner rivets come from the asset; the date, amount and
caption stay code-owned HTML on the ticket's blank centre, in ticket ink rather than the shell's cream.
**Accepted as matching** for the strip's material, silhouette and typography rhythm.

Still open in Plan, and deliberately not claimed: row-level scale lines and chevrons on the commitment rows, the
bottom apricot CTA (`apricot-button.png`, which the kit specifies for exactly that), and the exact header/tab
order. Copy is unchanged by design — the owner accepts the live wording, so the label reads "Next paycheck"
rather than the concept's "Next income".

Evidence: `artifacts/observatory-plan-income-2026-09-16/` (5 viewports × 2 themes, full-page included), plus a
computed-style probe confirming the nine-slice, the two masked ornaments, the HTML amount and zero overflow at
both 420px and 1440px.

## Plan — the folded allocation map (2026-09-16)

![Plan mobile-air dark, folded allocation map](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-plan-map-2026-09-16/plan-mobile-air-dark-viewport.png)

![Plan desktop dark, folded allocation map](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-plan-map-2026-09-16/plan-desktop-dark-viewport.png)

Read against concept **02**: the allocation is now the folded parchment map from the kit, installed below the tabs
and ahead of the coverage/funding summary, carrying one medallion per segment — Bills on the left station, Goals
on the right, Available pinned to the lower hub — joined to a decorative compass rose by brass rules. Every
figure is HTML: the art holds no money and no labels, and the stations are fixed by the concept rather than sized
by the amounts, so the map never claims to encode the split the way the removed stacked bar did.

**Accepted as matching** for the allocation map: art, silhouette, stations, medallion anatomy, rules and typography
hierarchy. Two defects were caught by inspecting the capture rather than the tests — a bank glyph on the Goals
medallion (the handoff maps goals to `flag`) and invisible glyphs on the navy medallion (an `<img>` cannot inherit
`currentColor`, so the glyphs are now CSS masks). Both are fixed and visible in the image above.

**Still open in Plan**, and deliberately not claimed: the concept's per-medallion status tags such as "Reserved"
(the service exposes no per-segment status, and inventing one would present inference as fact), the row-level
scale lines and chevrons on the commitment rows, the perforated "Next income" strip, the bottom apricot CTA, and
the exact header/tab order. The coverage donut remains where the concept has none — a later batch decision, since
removing it would drop a real funding figure.

Evidence: `artifacts/observatory-plan-map-2026-09-16/` (4 viewports × 2 themes, full-page included).

## Today — connector runs (2026-09-16, step 3 batch 3)

![Today mobile-air dark, connector runs](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-connectors-2026-09-16/today-mobile-air-dark-viewport.png)

![Today desktop dark, connector runs](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-connectors-2026-09-16/today-desktop-dark-viewport.png)

Read against concept **06**: each rim marker now carries a dashed brass run across to its own callout, ending in a
small brass stud at the row's left edge. Both ends are live geometry — the start is the marker's own projection,
the end is that event's row box — so the runs follow the data and re-anchor when the rows are replaced or either
side resizes. **Accepted as matching.** Previously the only decoration was a fixed dashed rule pinned to the list
item's midline that read no dial coordinate, and it was off at ≤900px where the concepts place these runs.

This completes the three Today items the handoff names — shaped ticket, prominent pointer, connectors tied to
actual coordinates — together with the semantic badge work its `Nuances` section requires. **Today is
presentation-complete for this pass**; remaining Track D work is Plan (02), then Activity (03), Accounts (04) and
Settings (05), and Settings is still absent from the isolated preview so no Settings parity can be claimed yet.

Evidence: `artifacts/observatory-today-connectors-2026-09-16/` (4 viewports × 2 themes), with the geometry proved
by `tests/browser/test_dial_fidelity.py::test_connector_runs_start_on_the_dial_and_end_at_their_own_row`.

## Today — shaped evidence ticket (2026-09-16, step 3 batch 2)

![Today mobile-air light, shaped ticket](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-ticket-2026-09-16/today-mobile-air-light-viewport.png)

![Today desktop light, shaped ticket, full page](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-ticket-2026-09-16/today-desktop-light-full.png)

Read against concept **06**: the ticket now carries the shaped silhouette the nuance names — scalloped side rails,
cut corners, four corner rivets and fibrous paper — supplied by the kit's `parchment-ticket.png` as a nine-slice
border image with `fill`, so the corner features stay fixed as the text reflows and the centre stays blank for
real words and money. At desktop full page the slice tiles without a seam. **Accepted as matching** for the
ticket. The previous `ticket-corners.svg` drew only four brass brackets, which is why the card read as a
rectangle before.

**Still open** in step 3: the dashed connector runs tying each rim marker to its callout. No connector geometry
exists at any width today — the existing decoration is a fixed 25px dashed rule pinned to the list item's own
midline, reading no dial coordinate, and it is switched off at ≤900px, which is exactly where concepts 01/06
place the runs.

Evidence: `artifacts/observatory-today-ticket-2026-09-16/` (4 viewports × 2 themes, plus full-page artifacts).
Sizing was measured before widening, because the fidelity suite caps the ticket at 260px: the mobile ticket was
193.6px, leaving 66.4px of headroom.

## Today — badges, pointer and callout legibility (2026-09-16, step 3 batch 1)

![Today mobile-air light, step 3 batch 1](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-step3-2026-09-16/today-mobile-air-light-viewport.png)

![Today macOS desktop dark, step 3 batch 1](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-today-step3-2026-09-16/today-desktop-dark-viewport.png)

Read against concept **06** in the review order: the callout column now distinguishes its events by glyph
(Electric keeps the lightning bolt, Internet resolves to the wifi glyph, Payday to the star on its mint disk)
instead of repeating one icon; each badge carries the concept's weighted anatomy — coloured disk, brass rim,
rivets; the mint selection pointer reads as a needle with a rimmed tip rather than another engraved tick; and
the callout titles are single-line at 390–430px instead of splitting mid-word.

**Accepted as matching** for badges, pointer and callout legibility. **Still open** in step 3, and deliberately
not claimed here: the dashed connector runs that tie a rim marker to its callout (no connector geometry exists
yet at any width), and the shaped evidence ticket, which still renders as a rectangular parchment card with
bracket corners rather than the supplied scalloped, riveted, fibrous silhouette.

Evidence: full-resolution captures at 4 viewports × 2 themes in `artifacts/observatory-today-step3-2026-09-16/`.
The kit's `medallion-frame.png` was measured and deliberately not used at badge scale: its 48px native stroke
collapses to ≈1.7px at a 44px badge, so the double rim cannot survive there.

## Observatory shared identity — first handoff slice (2026-09-16)

Authority corrected by the owner: the 2026-09-16 handoff and kit are the implementation specification, and the
older Design Atlas does not govern a conflicting layout. Today's composition authority is **06** (functional
dial/evidence) with **01** supporting; **02–05** govern Plan, Activity, Accounts and Settings.

This slice is handoff step 2 — shared type/header/navigation — reviewed against the shared chrome those concepts
show.

![Today mobile-air light](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-identity-2026-09-16/today-mobile-air-light-viewport.png)

![Today desktop dark](/Users/stephenwest/Openrouter/simplecrew-latest/artifacts/observatory-identity-2026-09-16/today-desktop-dark-viewport.png)

Read against the concepts in the required order (structure → typography → spacing → controls → decoration): the
wordmark now carries its apricot accent and renders in the bundled serif; the dock pairs each of the four entries
with its supplied glyph and a visible label; the current entry is lilac with a physical bar rather than colour
alone. **Accepted as matching at this review level.** No workspace geometry was in scope, so the dial, callout and
ticket differences recorded further down stay open for step 3 and are deliberately not counted as this slice's
gaps.

Evidence: `artifacts/observatory-identity-2026-09-16/manifest.json` holds the 40 governed records with the
contract metadata (concept path, viewport, DPR, theme, fixture, frozen clock, ui state, fullPage, commit);
full-resolution PNGs sit beside it; `identity-evidence.json` records the consumed kit hashes and the consuming
revision. No JPEG review copies were generated — the PNGs are retained locally and the owner reviews through the
GUI, so a lossy second copy would add weight without adding evidence.

## Track D — consolidated position and the decisions it needs (2026-09-15)

All four workspaces now have valid, informative, complete evidence, and all four have been assessed against their
governing concepts. This section states the whole position in one place, because the detail below is per-workspace
and the decisions are cross-cutting.

### Evidence infrastructure (all four workspaces)

| Capability | Status |
|---|---|
| Fixtures serving each workspace's real endpoint shapes | ✅ all four |
| Controllers loaded so a workspace actually renders | ✅ all four |
| Governed capture: 5 viewports × 2 themes, DPR-correct | ✅ 10 combinations each |
| Full-page capture | ✅ (fixed — had silently degraded to viewport-height at mobile) |
| Side-by-side concept/capture artifacts | ✅ 16 in total |
| Non-default UI state drivable and recorded | ✅ `--ui-state` / `--ui-state-selector` |
| Overflow and console errors recorded per capture | ✅ zero across every combination |

### Findings per workspace

| Workspace | Apparent gaps investigated | Real defects found | Outcome |
|---|---|---|---|
| **Today** | right-side alignment; payday amount at mobile; rim-label crop; dock occlusion; dial label contrast | **2** — dial `is-today` ink was cream-on-parchment; the dock occluded the inline advisor control | Both fixed and verified. Today has no outstanding measured defect. |
| **Plan** | "backed by undefined"; "undefined" timeline; missing allocation diagram; missing bills/income | **0** — the two `undefined` texts were my fixture's shape bugs; the allocation and bills elements exist and render | Differences are wording and diagram geometry, which the build spec classes as art direction. |
| **Activity** | four tabs vs three; no category review | **0** — the segmented control matches exactly and review rows exist; the comparison was state-mismatched | Valid comparison shows the sides correspond; differences are wording. |
| **Accounts** | missing Bill Reserve row; missing asset counts | **0** — both were the fixture's content, not the product's | Structures correspond; content comparison is limited by fixture authorship. |

**Consolidated result: two real defects, both on Today, both fixed — and no missing capability in any workspace.**
Every other apparent gap dissolved as one of four artifact classes, each of which is a way a comparison can lie:

1. **Label-grep absence** — the segmented control that "didn't exist" lived in JavaScript.
2. **State mismatch** — Activity's concept depicts the Review mode; the capture was the default Timeline mode.
3. **Fixture-shape bug** — three separate instances (`backing` as a string not an object; `commitment` vs
   `commitment_id`; `classification` as a string not an object). Each rendered literal "undefined" in a capture.
4. **Fixture-content limitation** — a fixture's accounts and assets set the ceiling on what a comparison may claim.

Rules now recorded so the remaining work does not re-learn them: read the **render site** for every fixture field
(names are not shapes); check the **state** before comparing; verify an apparent gap is not a fixture artifact
before reporting it; and never compare content the fixture itself supplied.

### What still needs you

1. **Today acceptance.** Track D's gate is owner-visible acceptance. The record is above; comparison images are in
   `artifacts/today-dock-fix-2026-09-15/`. On sign-off, Track D advances to Plan.
2. **Which art-direction differences to match.** Across Plan, Activity and Accounts the remaining differences are
   copy (headlines, button labels), diagram geometry (map vs bar), and composition — all named by the build
   specification as art direction that "may be inconsistent". Matching them is a product decision, not a fidelity
   fix, and doing it unilaterally would be inventing product language from a mock.
3. **Accounts content comparison** — aligning the fixture to the concept's accounts and asset counts would make the
   comparison show a match, but only because I authored the fixture to match. That is circular and is deliberately
   not done. Structure and styling are what this comparison can legitimately support.
4. **Emitter semantics** (separate thread, not Track D): deviations 2–3 in
   `MERIDIAN_STATUS_EMITTER_VERIFICATION.md` — whether `queues`/`phase`/`tracks` should carry real values or the
   contract doc should be narrowed to what the emitter does.


## Accounts — the comparison is CONTENT-confounded (Track D, 2026-09-15)

Reading `comparison-accounts-mobile-dark.png`, several apparent gaps turn out to be **the fixture's content, not the
product's**, and this is a distinct failure mode from the label-grep and state-mismatch ones already recorded.

The concept shows three account rows — Free to Spend $248.50, Bill Reserve $1,320.00, Emergency Fund $2,200.00 —
and an "Assets & documents" ticket reading "2 warranties · 1 contract". The capture shows two accounts (Checking,
Emergency fund) and no asset counts. The obvious reading is "the product lacks Bill Reserve and asset counts".

That reading is false. The Accounts fixture supplies **two** accounts and **no** assets, so the number and names of
rows, and any asset count, are determined by the fixture rather than by the product. Verified directly against the
served payload: `groups` = Cash[Checking], Savings[Emergency fund]; no assets. **A fixture's content sets the
ceiling on what a comparison may claim**, and row counts and item labels are exactly the things it controls.

Fixture-independent differences, which are the only ones this comparison can legitimately support:

| Concept | Current |
|---|---|
| "Accounts" · "Your financial constellation." | "Structure without provider clutter." · longer explanatory subline |
| One paper-ticket summary — "Cash across accounts $3,768.50" | Two separate cards — AVAILABLE CASH $248.50 and LIABILITIES $0.00 |
| Per-row chevron and illustrated circular icon | Per-row "Activity" action |
| A status strip: Crew · Connected · Updated 9:42 AM · Refresh | CONNECTION HEALTH card with Refresh now and View connections |

Both sides do carry account rows with provider and balance, a refresh affordance, and an assets/documents section,
so the structures correspond; the differences above are composition and affordance, not missing capability.

**To compare content at all, the fixture must be authored to mirror the concept's data** — the same accounts and the
same asset/contract counts. Doing that with values that are obviously synthetic is legitimate; using them to claim
product parity without that alignment is not. Until then, Accounts parity is assessable for structure and styling
only, and the honest statement is narrower than "the concept has three rows and the product has two".

## Activity — the captured comparison is state-mismatched, so it is INVALID (Track D, 2026-09-15)

Reading `comparison-activity-mobile-dark.png`, the concept and the current implementation looked
structurally different: the concept shows category review (per-row "Suggested category: Groceries",
"Confirm category", "Change"), the capture shows a plain ledger with "Unassigned" and no actions. Two
apparent gaps were checked against source, and **both dissolved**:

- **"The current has four tabs, the concept three."** False. The segmented control is exactly
  `Timeline | Review | Patterns` — the concept's three. "Filter" is a separate toggle button
  (`data-filter-toggle`) that happens to sit beside the segmented control, and the reading conflated them.
- **"The current has no category review."** False. `activity.js` renders review rows with
  `m-review-category`, an orange attention dot, the suggested category, ranked `category_options` and a
  classification confidence — the concept's exact content. It is reachable via
  `data-activity-mode="review"`.

**The real problem is the comparison itself.** `activity.js` defaults to `mode: "timeline"`, and the
capture harness records a fixed `ui_state` of `"<workspace>:default"` and never drives a workspace's own
modes or tabs. So every Activity capture is the Timeline mode while the governing concept depicts the
**Review** mode. The two columns are different states of the same product, and the specification is
explicit that only matching state may be compared.

That makes the Activity comparison **evidence of nothing** — not evidence of a gap, and not evidence of
parity. The same risk applies to any workspace whose concept depicts a non-default mode, so this is a
pipeline defect rather than an Activity defect.

The fix is bounded: let the harness drive a named UI state before capture (for Activity, select
`[data-activity-mode="review"]`), and record the state actually captured instead of the constant
`"<workspace>:default"`.

**That fix is now implemented and the valid comparison exists.** `capture_meridian_matrix.py` takes
`--ui-state` (the label recorded) and `--ui-state-selector` (a selector clicked before capture, which raises
if it matches nothing), and it records `ui_state` and `ui_state_selector` per capture. Activity re-captured as
`activity:review` into `artifacts/activity-review-parity-2026-09-15/` with
`comparison-activity-review-mobile-dark.png`.

Reading the matched comparison, **the two sides correspond**: both show a review card per transaction carrying
merchant, amount, the category suggestion, a confidence figure, and an approve/change action pair. The
remaining differences are wording and density, not structure:

| Concept | Current |
|---|---|
| "Suggested category: Groceries" as an explicit line | "Income · 95% confidence" on one line |
| "Crew • Free to Spend" account/budget meta per row | not shown in the review row |
| "Confirm category" · "Change" | "Approve category" · "Correct" |
| "3 categories to review" count header | no count; batch checkbox instead |

So Activity is **not** missing the review capability, and the earlier apparent gap was entirely an artifact of
comparing two different states. The remaining differences are again wording, which the build specification
classes as art direction.

**A third fixture-shape bug was found and fixed in the process.** The first Review capture showed "0%
confidence" and no category because the fixture set `classification` as a string while `activity.js` reads
`transaction.classification?.category` and `?.confidence` — an object. After the fix the capture reads
"Income · 95% confidence". That is the same mistake, in the same session, after I had already written the rule
against it, which is a fair measure of how easy the mistake is: **read the render site, not a sample of names.**


## Plan — gap assessment against `02-plan.png`, decision-ready (Track D, 2026-09-15)

Plan evidence is now valid on both axes that were missing: **informative** (fixtures serve data and the
controller loads) and **complete** (full-page capture works, mobile full page 1290×8427). The gap list below is
therefore read from rendered content, not from empty states or a truncated page.

Three apparent defects found in the capture were investigated and **none is a product defect**:

| Apparent defect | Verdict |
|---|---|
| "backed by **undefined**" on all four commitment cards | **My fixture's bug.** `plan.js:484` renders `commitment.backing.name`, so `backing` is an object; the fixture passed a string. Fixed. |
| "**undefined**" as the destination on every NEXT 30 DAYS row | **My fixture's bug.** `plan.js:226` renders `event.commitment`; the fixture supplied `commitment_id` and `detail`. Fixed. |
| "Next funding Sep 11" footer | **Intended.** `plan.js:616` renders `summary.next_due`. Not a defect. |
| "The scenario preview could not be loaded" | **Harness gap.** `plan.js` posts to `/api/meridian/plan/scenario`, which the isolated preview does not serve. Needs a scenario fixture before that section can be assessed. |

After the fixture fix the full-page capture contains the literal text "undefined" **nowhere**, which is the check
that confirms the first two.

What remains is a set of **design differences, not defects**:

| Concept (art direction) | Current implementation |
|---|---|
| "Give every dollar a destination." | "Every dollar has a next job." |
| Orange "Add a bill or goal →" | "+ New commitment" (plus a secondary "New autopilot rule") |
| **Unfolded-map** allocation diagram | Horizontal allocation **bar** + text legend — labels and amounts match exactly (Bills $1,320 · Goals $200 · Available $248.50) |
| "Upcoming bills" panel | "COMMITMENTS" cards with FUNDED/NEXT columns and row actions |
| "Next income" ticket | "FUNDING SCHEDULE · Next paycheck" |
| — | Extra sections: September coverage, Scenario preview, Plan memory |

**Why these need a direction rather than a fix.** The build specification says of the drafts: *"Treat images as
art direction, not executable financial specifications. Mock amounts, dates, status labels, arbitrary icon
choices, chart geometry, and generated text may be inconsistent."* Headline copy, button labels and diagram
geometry are named in that list. So "make the headline match" or "replace the bar with a map" is a **product and
design decision**, not a fidelity defect — and doing it unilaterally would be inventing product language from art
direction, which is the same class of error as the false gaps recorded above.

What is actionable without that direction, in the review order, is the **allocation presentation**: the concept
makes the allocation the centrepiece directly under the tabs, while the implementation places "Where the money
sits" fifth, after coverage, funding schedule and four commitment cards (roughly 5,000px down at mobile). Its
labels and amounts already match the concept exactly, so the remaining difference is prominence and placement —
layout, the first item in the review order, with no copy change and no data change.

## Plan — preliminary analysis, capture-gated (Track D, 2026-09-15)

Recorded so Plan parity can start immediately once its capture path exists. **This is source inspection, not
capture evidence**, and it is explicitly weaker: it can establish what markup and controllers exist, and nothing
about how the surface renders.

Reading the governing concept `02-plan.png`: tall portrait composition — wordmark and Settings; a "Plan" heading
with the subtitle *"Give every dollar a destination."*; a three-tab segmented control (Plan | Rules | Crew); a
central **unfolded-map allocation diagram** with three destinations (Bills $1,320 Reserved · Goals $200 Reserved ·
Available $248.50 Available to plan); an **Upcoming bills** panel with three reserved rows; a ticket-shaped **Next
income** card; a large orange **Add a bill or goal** button; and the four-item dock with Plan selected.

What the current implementation actually contains:

- the segmented control **exists and matches** — `plan.js` `setupPlanSegs()` drives
  `data-plan-seg` / `data-plan-view` / `data-plan-view-pane`, and the template renders exactly `Plan`, `Rules`,
  `Crew`;
- a "New commitment" primary action with a `+` icon where the concept has "Add a bill or goal" with `→`;
- an editorial headline **"Every dollar has a next job."** where the concept has "Give every dollar a
  destination.";
- twelve labelled sections (Coverage, Funding schedule, Commitments, Where the money sits, Next 30 days,
  Scenario preview, Document review, No longer returned, Crew capabilities, Crew actions, Crew mutation coverage,
  Plan memory) against the concept's focused four-block composition.

**A false-gap trap worth recording, because I fell into it first.** Grepping the concept's labels against the
template, `plan.js` and `plan.css` returned zero hits for "Give every dollar a destination", "Upcoming bills",
"Next income", "Add a bill or goal", "Available to plan" and "Reserved" — which reads as six missing elements. It
is not. The segmented control, which the same method reported absent, **exists** but lives in JavaScript rather
than the template; and the concept's "Upcoming bills" and "Next income" may well be the implementation's
"Commitments" and "Next 30 days" under different names. **Label-level absence is not feature absence**, so this
records the shape of the difference and nothing more. Whether it is a parity gap is a capture-and-compare
question, and it stays open until Plan can be captured.

That also sets the scope expectation honestly: Plan's differences look like **naming and presentation** across a
much denser layout, not a missing architecture — but that claim is exactly the kind this project refuses to make
without a capture, so it is recorded as the hypothesis to test, not as a finding.

**Plan captures are now informative — the fixture prerequisite is DONE.** The isolated preview gained a Plan
fixture and, critically, loads `plan.js`. Both halves were needed and the second was the one that mattered: the
endpoints alone changed nothing, because a workspace renders only if its controller is loaded, and the preview
had been injecting only `shell`, `today` and `dial`. With `plan` added, the previously-empty capture now shows
real rendered content:

```
SEPTEMBER COVERAGE 86% · $1,520 of $1,769 funded · Projected complete by Sep 16
FUNDING SCHEDULE · Next paycheck · September 16 · $1,660
COMMITMENTS · Electric BILL · ...
```

"Nothing funded yet." and "No funding scheduled yet." are gone. Evidence:
`artifacts/plan-parity-fixtured-2026-09-15/` — 10 combinations, zero overflow, zero console errors.

So Plan parity analysis can now run against rendered content rather than empty states, which is what the previous
round established was necessary. The fixture is derived field-by-field from what `plan.js` reads (see the shape
recorded below), and its values echo the governing concept's own figures so a capture can be compared to
`02-plan.png` directly.

The generalisable lesson, now demonstrated twice: **a workspace capture is evidence only if the workspace's
controller is loaded and its data is served.** Empty states in a capture are indistinguishable from missing
features, and both are indistinguishable from an unloaded controller.

Reading the mobile capture against the concept exposed a trap of the same family as the label-grep: the capture
shows **COVERAGE**, **FUNDING SCHEDULE**, **COMMITMENTS** and **WHERE THE MONEY SITS**, all rendering *empty*
states ("Nothing funded yet.", "No funding scheduled yet."), because the preview serves no data for Plan. The
concept's unfolded-map allocation diagram, its bills panel and its next-income card therefore look absent, when
in fact `templates/meridian/partials/plan.html` **has** the allocation element (`m-allocation-bar` +
`m-allocation-legend`) and the timeline — they are simply unpopulated. **Absence in a no-data capture is not
absence of a feature**, exactly as a label miss is not a missing feature. Any gap list read off these captures
today would send the work at things that already exist.

So Plan's real prerequisite is fixture data in the isolated preview. The shape is small and derivable from the
consumer rather than invented — `plan.js` requires `/api/meridian/plan` and treats
`/api/meridian/funding-rules` as optional, and reads exactly these top-level keys:

`summary` (`headline`, `total`, `total_target`, `total_funded`, `unfunded`, `coverage_ratio`, `captured`,
`missing`, `next_due`, `first_shortfall`) · `allocation` (`cash_total`, `segments: [{label, amount}]`) ·
`commitments: [{id, name, type, target, funded, unfunded, due_date, target_date, backing, biller_status,
crew_bill_id, invoice_evidence}]` · `next_paycheck` · `timeline` · `absent_bills` · `document_discrepancies`.

Two endpoints, not the eight-to-ten previously estimated — that estimate was for every workspace at once. Note
also that only the Plan capture is affected this way; Today's captures are unaffected because the preview serves
Today data.

The construction rule for those fixtures: derive every field from what the consumer reads, never invent a shape
the UI does not consume, and keep the values clearly synthetic. A fixture that satisfies the consumer is
evidence; a fixture that guesses is a new source of false gaps.

## Today — acceptance summary (Track D, 2026-09-15)

**Status: awaiting owner acceptance.** Everything below is measured from the live DOM or captured under the
governed matrix; nothing here is inferred from an image.

**Captured evidence.** `artifacts/today-parity-2026-09-15/` — 10 captures, all five governed viewports (1440×900
DPR 1, 1024×768 DPR 1, 430×932 DPR 3, 390×844 DPR 3, 420×912 DPR 3) × light and dark, 20 screenshots, at
`commit 2c7af918`, concept `01-today.png`, fixture `synthetic-electric-internet-payday`, frozen clock
`2026-09-08T13:42:00Z`. **Zero horizontal overflow and zero console errors in all ten combinations.**

**Gaps from the roadmap, re-tested:**

| Roadmap item | Verdict |
|---|---|
| Right-side alignment | **Not reproducible.** Layout box 251–1339 in 1440 → 101px each side, symmetric. The single-column desktop stage is deliberate and documented in `observatory.css`. |
| Payday amount tight at mobile | **Not reproducible.** clientWidth 110 / scrollWidth 110 at 420, 430 and 390. |
| Inline Virgil control vs bottom nav | **Fixed.** Was `OCCLUDED` at 420 (`m-nav-item`) and 430 (`m-nav`); after the shell change the verdict is `PAINTED_AND_HITTABLE` at both, and `NOT_PAINTED` at 390. |
| Light-theme foregrounds | **Inspected; today-marker defect found and fixed.** Primary text legible. The `is-today` day label was cream on parchment and is now dark ink (pixel-verified). The accompanying "lower rim labels obscured by artwork/crop" claim was **measured and not reproduced**. |

**The defect that was open, now closed.** The "Ask Virgil about this plan" control was painted and then covered
by the dock in the initial mobile viewport — 7046 px² covered at 420 and at 430. It was never a dead control
(after scrolling it cleared the dock and hit-tested to itself), and the governing concept contains no inline
advisory control in that position at all. The shell change described above removes the occlusion; the verdict is
now `PAINTED_AND_HITTABLE` at 420 and 430 and `NOT_PAINTED` at 390.

A second finding, from inspecting the light-theme capture directly (which the roadmap requires, because a
computed-ratio probe is not valid over gradient and parchment backgrounds). Primary light-theme text is legible,
but two things are marginal: the small grey dial labels sit at low contrast against the parchment, and the lower
dial rim labels (`8 / TUE`, `16 / WED`) are partially obscured by the observatory artwork and by the bottom
viewport crop. This is distinct from the dock overlap and was not previously on the roadmap's list.

**Fix applied for the today marker, and the verification disagreed with itself — recorded as such.** The
`is-today` day label was cream (`#eee4cf`) with a dark text-shadow, set by a later concept-fidelity pass, while
its neighbours were `rgba(32,38,59,0.82)`. The dial rim is parchment in *both* themes, so cream was wrong in
both. It now uses the dark engraved ink `#5b3d16`, which also restores the emphasis the earlier rule
(`color: #5b3d16`, size 13px) had intended.

Verifying it exposed two traps worth keeping:

1. **A theme selector that never applies.** The first attempt used
   `html[data-theme="light"] .obs-dial-day-label.is-today`, which verified clean in a probe because the probe set
   `document.documentElement.dataset.theme` by hand. At capture time the attribute is whatever `theme.js` derives
   from `prefers-color-scheme`, so the rule silently did nothing. Verified fixing the *base* rule instead, which
   is theme-independent because the rim is parchment either way.
2. **The vision reading and the computed style contradicted each other**, so neither was treated as truth. The
   pixels settled it: in the label region, cream pixels went **27 → 0** and dark-ink pixels **466 → 529** between
   baseline and after-fix captures. The cream glyph is genuinely gone.

The vision reading still described "8 TUE" as washed out *after* the fix, so the obvious explanation was that the
dial artwork plate carries its own baked day marker. **That was tested and disproven:** `.obs-dial-art` is
`static/img/meridian/observatory/dial-plate.png` (1254×1254), and it contains no text, numerals or weekday
abbreviations at all — only decorative celestial texture and tick marks. So the residual reading is almost
certainly a limitation of reading 10px type from a raster (the model itself recorded that it could not
confidently transcribe the characters), not an outstanding defect. The measured state is: the cream glyph is
gone, dark ink sits on parchment, and the label region has no cream pixels left. Left as a low-confidence item
for the owner's eye rather than reclassified as fixed or as still-broken.

Evidence: `artifacts/today-labels-fix-2026-09-15/` (10 captures, zero overflow, zero console errors).

**The "lower rim labels are cropped" claim was measured and does not reproduce.** All four day labels are inside
the viewport at desktop and at 420: `8 TUE` and `16 WED` sit at viewport y=771 in a 900px viewport, and every
label reports `inViewport: true`. The page scrolls (document height 2521 at desktop, 1927 at 420), so the dial's
lower 66px, which extends below the desktop fold, is reachable — content below the fold in a scrollable page is
not a defect, and the build specification explicitly allows the tall compositions to scroll on real devices.

This makes **two vision readings on this dial that measurement contradicted** (the "8 TUE" wash-out after the fix,
and now the cropped rim labels). Both are recorded rather than silently dropped, and they set the working rule for
this surface: the raster readings of 10px dial type are unreliable in both directions, so a dial-label claim
needs pixel or computed-style confirmation before it is acted on — and equally before it is dismissed.

A process note worth keeping: the light-theme row of this table first read "verified, no problems" before the
capture had actually been inspected. It was rewritten only after reading the image. That is the exact failure
mode the roadmap warns about — a clean-looking row that was never looked at.

**A validated fix exists and is now SHIPPED, with one honest limit.** Making the mobile shell `height: 100svh`
with the canvas as its own scroll container flips the measured verdict from `OCCLUDED` to
`PAINTED_AND_HITTABLE` at 420 and 430 and `NOT_PAINTED` at 390. It was withheld twice while only Today could be
captured; the blocker was worked around by verifying the level the change actually affects. The change alters
**shell geometry** (shell / canvas / dock), not workspace content, so it can be measured on every workspace even
without their fixture data:

| Workspace | nav position | shell height | doc scrolls | horizontal overflow | dock overlaps canvas |
|---|---|---|---|---|---|
| today | static | = viewport | no | 0 | no |
| plan | static | = viewport | no | 0 | no |
| activity | static | = viewport | no | 0 | no |
| accounts | static | = viewport | no | 0 | no |

All three mobile viewports (420/912, 430/932, 390/844), every workspace: the dock is a static grid row at the
viewport foot, the canvas owns scrolling, `nav_overlaps_main` is false, and horizontal overflow is zero. Nothing
in the Meridian client listens for `window` scroll, and `scrollIntoView()` walks up to the nearest scrollable
ancestor, so the scroll-container change has no other client dependency.

**What gates this change, and what could not be run.** The browser suite was run for the first time against this
work: `tests/browser` gives **24 passed, 63 skipped**, and every skip is the same environmental gate —
`APP_URL is required for browser tests`. `tests/browser/test_meridian_shell.py` and
`tests/browser/test_responsive_parity.py` are both entirely in that skipped set, and they are precisely the tests
that would cover a shell change. They authenticate through `/api/auth/login`, so they cannot be pointed at the
isolated synthetic preview, which deliberately has no auth.

The relevant one is worth naming exactly: `test_responsive_parity.py` parametrises 390×844 and 430×932 and asserts
that accounts has no horizontal overflow. That is the same property this shell change could have broken, and it
could not be executed. It is covered instead by direct measurement — horizontal overflow 0 across all four
workspaces at 420, 430 and 390 — which is the same assertion made by a different route. The desktop shell tests
would not have exercised the change in any case, since it lives inside `@media (max-width: 900px)`.

So the change rests on: geometry measurement across 4 workspaces × 3 mobile viewports, a governed Today capture
with zero overflow and zero console errors, the full non-browser suite (1119 passed, 1 skipped), and the browser
suite's 24 runnable tests. The one suite that would gate it directly needs a live authenticated app, which is an
environmental limitation rather than a gap in this change.

**Track D capture status — the earlier "Today only" claim was WRONG and is corrected here.** An earlier version of
this document stated that Today was the only workspace able to produce governed capture evidence from the isolated
preview. That was inferred from a timed-out four-workspace run and never tested per workspace. Tested individually:

| Workspace | Result |
|---|---|
| today | captures (10 combinations) |
| plan | **captures** — 10 combinations, `02-plan.png` |
| activity | **captures** — 10 combinations, `03-activity.png` |
| accounts | **does not settle** — 0 captures |

The timeout came from **accounts alone**, and the cause is specific: `templates/meridian/partials/accounts.html`
hardcodes `aria-busy="true"` on its root, and the preview injects only `shell`, `today` and `dial` modules, so the
accounts controller that would clear it is never loaded. Plan and Activity set `aria-busy` programmatically in
their controllers and clear it in a `finally` block, and neither depends on a template-level busy attribute, so
they settle even though the preview serves no data for them.

Governed evidence for the two newly-capturable workspaces is in `artifacts/plan-activity-parity-2026-09-15/` —
20 captures, both concepts mapped correctly, all five viewports, **zero horizontal overflow and zero console
errors**. The lesson is recorded rather than the fix alone: a claim about what a harness can do is itself a
claim that needs testing, and inferring "impossible" from one aggregate timeout cost several rounds of work that
was available all along.


## September 15 governed regeneration and measurement pass (Track D)

The previous matrix (`artifacts/dial-refinement-2026-09-12/today-final-2/`) was captured at `5ed361e`. The
capture specification says existing screenshots are historical unless regenerated, and the tree has since
gained the cadence consolidation, the transfer-readback verifier and the status emitter, so the evidence was
regenerated rather than reused.

**Fresh governed matrix: `artifacts/today-parity-2026-09-15/`** — 10 captures (all five governed viewports ×
light and dark), 20 screenshots, recorded at `commit 2c7af918` with `concept_path` `01-today.png`, fixture
`synthetic-electric-internet-payday` and frozen clock `2026-09-08T13:42:00Z`. **Zero horizontal overflow and
zero console errors in every one of the ten combinations.** Capture now also records `overflow` and
`console_errors` per capture, because horizontal overflow is the primary responsive defect signal and should
be measured rather than inferred from an image.

Producing this required a tooling fix, recorded because it was a real blocker: the governed capture script
called `login()`, but the isolated synthetic preview deliberately has no `/login` route, and it always
captured all four workspaces while that preview renders Today only. The only target that has a login is
`run_preview.py`, which loads `.env` and starts a Crew sync loop — unusable for fidelity work, because the
specification requires fixtures only and forbids live bank data. The script now takes `--skip-login`
(isolated synthetic preview: no auth, no credentials, no provider call) and `--workspaces`.

### Measured gaps (probes in `artifacts/today-parity-2026-09-15/probes/`)

Geometry was measured from the live DOM rather than estimated from pixels, because the pixel estimate
disagreed with the DOM.

| Roadmap gap | Measurement | Status |
|---|---|---|
| Right-side alignment on Today | Layout box 251–1339 in a 1440 viewport: **101px each side, symmetric**. The single-column desktop stage is deliberate (`observatory.css` documents it: "Today becomes a single Observatory stage on wide screens"). Each event card is 384px and its body reaches the right edge (326px). | **Not reproducible as a gross defect.** The residual is that the card's compact left-aligned stack (which matches the concept) leaves unused width inside a 384px card. |
| Payday amount tight fit at mobile | `+$1,660.00` measures `clientWidth 110 / scrollWidth 110` — **no overflow** — at 420, 430 and 390. | **Not reproducible.** |
| Inline Virgil control overlaps bottom nav at mobile | `obs-control` bottom vs sticky `nav.m-nav` top: **−41px at 420**, **−23px at 430**, **−79px at 390**. | **Reproduced.** The control sits behind the dock on first paint at every mobile viewport. |

A caution recorded for the next pass: the concept's callouts stack date/name/amount/status **left-aligned**,
and the vision reading of `01-today.png` confirms the amounts are deliberately *not* right-aligned. So
"fixing" the unused card width by right-aligning amounts would move the implementation **away** from the
governing concept — the trap Track D's review order exists to avoid.

Outstanding decision, not taken unilaterally: the dock overlap is structural. The dock is a `position: sticky`
grid row pinned to the viewport bottom, so mid-scroll content passes beneath it by design; the inline advisory
control is an addition the concept does not contain. Candidate fixes are (a) make the canvas the scroll
container so the dock reserves its own row and never overlays, or (b) drop the inline advisory control at
mobile. (a) touches the shell and therefore every workspace; (b) is small but removes a control. Both are
owner-visible choices, so the measurement is recorded rather than a fix improvised.

**A measurement error in this pass was found and corrected, and it matters.** The first overlap probe waited
only for `.obs-dial-center-amount`, which exists *before* the dial's event rail finishes rendering. The page
kept growing after the measurement, so two runs of the same probe disagreed by ~250px on the same element
(y=566 vs y=814 at 390 wide). The "reproduced" figure was therefore not trustworthy when first reported.
`probes/measure_nav_overlap_settled.py` waits for the rail to be populated (`.obs-event-item`), for
`document.fonts.ready`, and then samples twice 600ms apart, asserting the document height is unchanged. With
that gate the collision reproduces reliably — **−41px at 420, −23px at 430, −79px at 390**, `stable: true`,
3 events rendered — and is recorded in `measurements-nav-overlap-settled.json`.

**The occlusion question is now settled definitively, and it is a real defect.** `probes/probe_visibility.py`
computes the control's *painted* portion (its rect ∩ the scrolling container's visible box) and hit-tests only
that portion with `document.elementFromPoint`. Baseline verdict at all three viewports is
**`OCCLUDED (painted then covered)`** — the element returned at the painted centre is the dock, not the control:

| Viewport | control y | painted | element actually on top |
|---|---|---|---|
| 420 | 844–888 | 7046 px² | `m-nav-item` |
| 430 | 846–890 | 7046 px² | `m-nav` |
| 390 | 814–858 | 4869 px² | `design-preview-banner` |

Two traps were hit and are recorded so they are not repeated. First, `.obs-control` is **not unique**: the dial
renders three more of them ("Previous day", "Next day", "Back to today") at y=596, so an early
`querySelector('.obs-control')` measured the wrong element and produced a false "not occluded". The advisor
control must be selected as `[data-open-advisor].obs-control`. Second, at 390 the occluder is the
`design-preview-banner` — a harness artefact, not the product — so only the 420 and 430 results describe real
product behaviour.

**Fix (a) demonstrably removes the occlusion on Today, and is still not shipped.** Re-applied and re-measured
with the visibility probe, the verdict changes from `OCCLUDED` to `PAINTED_AND_HITTABLE (not occluded)` at 420
(painted 545 px², scroller now `m-main`, top element `obs-control`) and at 430 (3415 px²), and to
`NOT_PAINTED (below fold)` at 390. So the earlier "no measurable improvement" reading was an artefact of a
rect-only probe, exactly as suspected.

It is nevertheless reverted, for a reason that is itself a Track D finding: **the change is cross-cutting and
cannot be verified on the other three workspaces.** `scripts/preview_observatory_dial.py` serves only
`/api/meridian/today`; `plan`, `activity` and `accounts` return **404**, so those workspace sections never clear
`aria-busy` and the governed capture harness times out on them (`Page.wait_for_function: Timeout 12000ms
exceeded`). Altering the mobile scroll container for every workspace while being able to test only one of them
is not a defensible trade for a cosmetic at-rest occlusion, so the fix is recorded as validated-on-Today and
pending verification elsewhere.

What remains true regardless: after `scrollIntoView({block:'center'})` the control clears the dock
(`clearsDock: true`) and hit-tests to itself, so it is **reachable** — the defect is at-rest occlusion on first
paint, not a dead control.

**Blocker for the rest of Track D, recorded now:** Plan, Activity and Accounts cannot produce governed capture
evidence from the isolated synthetic preview until that preview serves their data (or a different
fixture-only target is built). Today is the only workspace currently capturable.

## September 12 phone alignment correction

The three-event baseline below missed the tall-list case. The owner's reported blank space was reproduced with twelve invented events and corrected: dial top alignment, bounded keyboard-scrollable callouts, full-width mobile text/amounts, and controls in a separate row. Regression and preview-template refresh checks pass within a **71-test** focused run. `artifacts/dial-refinement-2026-09-12/alignment-dense-final/` contains the fresh 16-image matrix, with zero page overflow/errors; mobile images were inspected. The local preview was reloaded and its served assets verified. See `docs/project/DIAL_ALIGNMENT_FIX_2026-09-12.md` for scope and runtime evidence. Older broad-fidelity observations below are retained, not silently treated as fixed by this incident correction.

Source: `design/observatory-drafts-2026-09-08/06-interactive-observatory-vision.png`.

Implementation: production Today template and dial/Today/shell controllers in the isolated synthetic preview
(`.venv311/bin/python scripts/preview_observatory_dial.py`, http://127.0.0.1:8093/). Synthetic data only —
never the daily banking runtime, never credentials, never a database.

## Verified this pass (2026-09-12, at commit `5ed361e`)

- **Fresh governed matrix: `artifacts/dial-refinement-2026-09-12/today-final-2/`** — 16 captures, four
  viewports × two themes × viewport/full-page, **zero horizontal overflow, zero page errors**, recorded at
  `commit 5ed361e` with `source_dirty: false`. This is the first matrix taken *after* the compact-card/spacing
  adjustment, so it supersedes `today-final/` for that change.
- **Composition matches the owner's direction**: large dial on the left, event callouts on the right, evidence
  ticket underneath; **safe-to-spend prominent** with separate horizon ("Available until September 16") and
  source ("Crew · observed Sep 8, 9:42 AM") lines.
- **Moon asset is in the composition** — `moon-engraving.png`, applied through `.m-observatory-moon` in
  `dial.css`, with the runway line ("You have about 14 days of runway."). It is a CSS background rather than an
  `<img>`, so an image-tag scan reports it missing; it is present and rendered.
- **Focused suite independently reproduced: 68 passed** — `test_dial_fidelity` 12, `test_dial_js` 22,
  `test_capture_contract` 7, `test_meridian_workspace_invariant` + `services/test_today` 27. Ruff clean;
  `git diff --check` clean.

## Remaining gaps (measured, unresolved)

1. **Payday amount is a tight fit in the callout.** `+$1,660.00` sits in a 79px box and reports
   `scrollWidth > clientWidth` at `mobile` and `mobile-small`, in **both themes**. Not visibly truncated today
   (overflow is not hidden), but it is the longest value that currently fits, and the one to watch as amounts
   grow. This is the "callout amount fit" item.
2. **Inline Virgil control overlaps the bottom navigation on mobile.** Visual pass records
   `Ask Virgil about this plan` partially truncated by the bottom navigation panel. No current test covers this.
3. **Light-theme foregrounds: not verified — and not verifiable by the computed-ratio method used here.**
   A contrast probe reported 19–24 "low contrast" elements in light theme. Inspection showed the figure is an
   artifact on both sides: text inside `[hidden]` other-workspace partials was being measured, and the backdrop
   walker cannot see `linear-gradient` or parchment backgrounds, so the nav's ivory-on-dark and the ticket's
   navy-on-parchment — correct, readable pairings — were reported at ~1.1:1. The light/dark asymmetry is a
   by-product of which elements happen to sit on gradients. **Resolve this by inspecting the capture, not by a
   computed ratio.** A candidate fix (mapping the two light-theme small-caps label rules onto `--m-ink-muted`)
   was applied and then reverted as unverified.

## Environment note

Browser verification can silently stall in two ways, both worth knowing before concluding a test has failed:

- `playwright` and its Chromium build live in `.venv311` (declared in `requirements-dev.txt`), **not** in the
  uv-isolated environment built from `requirements.txt`. A production-requirements runner cannot execute the
  browser or capture tests at all.
- An interrupted browser run leaves orphan Chromium processes behind, and later runs then hang. Clear them with
  `pkill -9 -f 'chromiumdev_[p]rofile'` (bracket the pattern so it cannot match your own command line).

## Status

Focused suite green and the post-adjustment matrix captured; composition verified against the owner's stated
direction. **Not claimed:** light-theme contrast verification, broader application acceptance, live served-app
acceptance, or any deployment. Remaining bounded work: resolve or explicitly accept the two measured gaps
above, and inspect light-theme foregrounds visually.
