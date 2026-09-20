# OS-049 — browser-suite baseline: measured, explained, and bounded (2026-09-20)

**Slice:** OS-049 — *"Environment: browser-suite baseline is not green and is unexplained."*
**Verdict:** the baseline is now **measured and explained**. One **real defect** was found and fixed. The
remaining failures are **not** environment drift: they are **three acceptance assertions from the 2026-09-16
ChatGPT-lane visual pass (`63d2865`) that the CSS never satisfied**, two of which **directly contradict a
documented, deliberate design decision**. They need an owner/visual-authority ruling, not a code tweak.

**No app, provider, live-sync or authority change.** Measurement only, plus one CSS floor fix.

---

## 1. What the ledger said, and what is actually true

| | Recorded in OS-049 | Measured 2026-09-20 |
|---|---|---|
| Failed | 43 | **6** |
| Passed | ~21 | **33** |
| Errors | 28 | **0** |
| Skipped | — | 70 |

The environment has **materially improved** since that entry was written — 43 failed/28 errors is now 6
failed/0 errors. `--ignore=tests/browser` is what the lane's standing command excludes, so the browser suite
had simply not been re-measured; that is the whole of the "unexplained" part.

Raw: `.venv311/bin/python -m pytest -q tests/browser` → **6 failed, 33 passed, 70 skipped** (31–36 s).

---

## 2. The one real defect — found, proven, and FIXED

### `.m-theme-toggle-label` kept its full box because a `min-width` floor was never overridden

Both mobile "hide the label" rules set `width: 1px` — but the base rule sets a **`min-width` floor**, and
**a min-width beats a width**. The label therefore remained **20.875px wide**, hidden from *sight* only by
`clip-path`, while still occupying layout and remaining a real focus/hit target.

Measured in the isolated harness (`templates/meridian/index.html` + the real stylesheets + the real dial model),
at 390px and 430px:

| Property | Before | After |
|---|---|---|
| `computedWidth` | `20.8594px` | **`1px`** |
| `computedMinWidth` | **`20.875px`** | **`0px`** |
| `clip-path` | `inset(50%)` | `inset(50%)` |
| `position` | `absolute` | `absolute` |

**Proof it was the floor, not a selector problem.** The CSSOM probe confirms **both** hiding rules **matched**:

```
shell.css  (max-width: 900px)  .m-topbar .m-theme-toggle-label
           → position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%)
dial.css   (max-width: 700px)  .obs-shell:has([data-workspace-section="today"]:not([hidden])) .m-theme-toggle-label
           → position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%)
shell.css  (no media)          .m-theme-toggle-label
           → min-width: 3.5ch; text-align: left          ← the floor: 3.5ch at 16px = ~20.9px
```

Specificity is not the issue: the `(0,2,0)` and `(0,4,0)` rules both beat the `(0,1,0)` base rule, so
`position` and `clip-path` apply as written. But **no rule ever overrode `min-width`**, so the used width was
floored at `3.5ch` regardless of `width: 1px`.

**Fix** (`static/css/meridian/shell.css`, `static/css/meridian/dial.css`): add `min-width: 0` to both hiding
rules, with a comment recording why. The rule *intends the label gone*, not merely invisible, so overriding the
floor is correct — and the floor itself stays, because it exists for a good reason in the visible case (it stops
the toggle shifting when the theme flips).

**Effect:** the `bounding_box()["width"] <= 1` assertion now **passes**, and the layout genuinely collapses
rather than relying on clipping.

---

## 3. The three remaining assertions — unmet acceptance criteria, not environment drift

Both surviving failure classes share **one mechanism**, and both were introduced by the **same commit** that
also added 78 lines to `dial.css`:

```
assert dial["x"] + dial["width"] + 10 <= rail["x"]   # → (4 + 270) + 10 <= 274  → FALSE
assert dial_box["width"] >= width * 0.74             # → 280 >= 318.2          → FALSE
```

### Mechanism: the dial's deliberate 24px right-bleed

`dial.css` (~line 942, mobile block):

```css
.obs-dial-svg-wrap {
  width: calc(100% + 24px);
  max-width: none;
  margin: 0 0 0 -12px;   /* 12px of the bleed is taken on the LEFT */
  justify-self: start;
}
```

`width: 100% + 24px` combined with a **left-only** −12px margin means the extra 12px goes to the **right**,
into the events-rail column. At 430px the bleed **overshoots**: measured `x=4`, `width=280` → right edge
**284**, while the events rail starts at **274**.

So the dial intrudes ~10px past the rail container's left edge — and that same overshoot is what holds the dial
to **65.1%** of viewport where the test wants **74%**.

### Why this is a ruling, not a bug to patch

The CSS documents this as **deliberate and load-bearing**:

> *"Visible dial goes from 246px (unclipped track width) to 258px, clipping 12px at the left. Buying more size
> means overlapping callout text and needs a scrim behind it -- **a deliberate design decision, not a tweak, so
> do not raise this value casually.**"*

That is an explicit instruction **not** to resize the dial casually, and it predicts exactly the symptom the
tests report. Meanwhile:

- **The `74%` threshold has no recorded basis.** It appears only in `63d2865` (2026-09-16) — introduced in the
  same commit that changed the CSS — with no measurement, concept reference, or rationale. It fails in **both
  themes and both mobile widths**, so it was never satisfied.
- **This is the owner's approved visual territory.** The Observatory geometry is governed by the 2026-09-16
  Astra handoff and concept artwork; `design-qa.md` is the visual acceptance record.

**Therefore the honest options — all requiring a decision, none safe to take silently:**

1. **Fix the CSS** to respect the rail (e.g. take the bleed on the left only, or clip the panel) — this is a
   **mobile dial geometry change** in the owner's approved visual territory, and the CSS explicitly warns
   against doing it casually.
2. **Re-baseline the thresholds** to measured truth (`~0.65`, intrusion `~10px`) — but that would **delete an
   acceptance criterion** on the strength of a measurement alone, which is exactly the "make the test fit the
   code" move this project forbids.
3. **Leave both and record them** as known-red with the tension surfaced — which is what this document does.

**A correction worth stating plainly:** it is tempting to describe these as "stale tests". They are not stale —
they are **unmet acceptance criteria whose thresholds contradict a documented design decision**. The
distinction matters because "stale" invites deletion, and the correct resolution may well be the CSS.

---

## 4. What is now safe to say

- **The suite is understood.** Its state is measured, each failure is attributed to a specific cause, and none
  is environment drift or flakiness.
- **One real defect was fixed** (the `min-width` floor), verified by measurement before and after.
- **Three assertions remain red, for a design reason** that predates this slice and is *not* attributable to any
  recent OS-04x/OS-05x/OS-06x work — consistent with OS-049's original finding that the failures were
  independent of the presentation work.
- **The dial-width questions belong to Track D's visual authority**, with `design-qa.md` as the acceptance
  record. They are not OS-049 environment issues.

## 5. Reproduction

```
.venv311/bin/python -m pytest -q tests/browser           # 6 failed, 33 passed, 70 skipped
.venv311/bin/python tmp/os049_probe.py 390               # the min-width defect (now 1px/0px)
.venv311/bin/python tmp/os049_probe3.py 430              # same, rendering the real template + model
.venv311/bin/python tmp/os049_dial_probe2.py 430         # panel/wrap/rail geometry
```

Probes are untracked scratch (`tmp/**` by lane convention) and make **no** provider call; they render the real
templates and stylesheets against the fixture model only.
