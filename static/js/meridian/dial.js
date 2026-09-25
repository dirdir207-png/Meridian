/* Meridian Observatory dial.
   Pure calendar/angle helpers plus a vanilla renderer for the interactive
   open 240-degree horizon.

   The dial never fetches or mutates financial data by itself; callers hand it
   a DialModel object. In the current preview slice the data is synthetic.
   Financial geometry stays code-owned; decorative art is separate and hidden
   from assistive technology.

   API:
     import { renderDial } from "./dial.js";
     const stop = renderDial(container, model);

   Model (compatible with the Observatory BUILD_SPEC view model):
     {
       timezone, today, horizonEnd,
       availableToSpend: {minor, currency} | null,
       freshness, observedAt,
       events: [{
         id, date, kind, title,
         amount: {minor, currency},
         fundingStatus, reserved?: {minor, currency},
         source, observedAt?, evidenceIds?, detailHref?
       }],
       projections: [{date, balance: {minor,currency}|null}]
     }
*/

const VIEWBOX = { w: 600, h: 600, cx: 300, cy: 300, r: 282 };
/* The day arc. `ARC_START` was -120, which put day 0 — today — in the dial's lower-left
   at (129,399), and that is exactly where the kit's `dial-plate.png` draws its observatory.
   Measured on the plate (1254px, centre 626,632): the building intrudes into the sky disc
   only between -140deg and -110deg, reaching inward to r=150-182 against a hand that runs
   r=118-198, so today's hand crossed it and read as being "into the building" (owner,
   2026-09-18). The building's inner edge jumps from 165 at -110deg to 283 at -105deg — a
   near-vertical roofline — so -100 starts the arc clear of it with ~10deg of margin while
   keeping a full-length hand for every day.

   The concept is no help on the collision itself: its dial has NO building (verified in
   both lower quadrants), so the observatory is the kit's addition and there is no authority
   for how a hand should treat it. The concept's own arc does start near the top and sweep
   clockwise, so shifting the start right is also the direction it points in.

   `ARC_END` moves to 180 (owner, 2026-09-25, reporting the defect his own screenshot showed: "there
   is a little overlap with the numbers and weekdays on the dial ... There is still plenty of room
   from where the 16th sits currently and the bottom of the dial, the obvious solution is spacing them
   out evenly, just slightly wider apart"). At the time the end sat at 132, so a 21-day horizon put 21
   labels over 232deg -- 27px of centre-to-centre arc against ~31px labels -- and the weekday
   abbreviations crossed into the neighbouring numbers on the whole right-hand side. Measured at the
   governed phone size with the owner's own horizon (today Sep 25, ending Oct 16): **7 visible
   collisions totalling 350px2 at 132**, 5/48.9 at 160, **2/25.3 at 180**, 1/11.9 at 190.

   180 is the bottom of the dial and also the CEILING, which is not a guess: a sweep to 210 was
   rendered and the last numbers (`16`, `14`, `15`) came down behind the rotunda's own engraving,
   i.e. a number painted onto the building reads as a defect rather than as a spread. So the arc now
   runs -100 -> 180 (280deg) and the numbers reach the graphic at each end, which is what the
   2026-09-24 change asked for ("the numbers extend down to the graphic on the bottom right and to
   the graphic at the top left (the rotunda image)").

   The remaining 2 collisions at 180 are ~25px2 in total -- two labels grazing a neighbour's corner,
   not text over text -- and they are LEFT VISIBLE rather than papered over: closing them entirely
   needs either a smaller weekday face or an arc past the building, and both are the owner's call.

   The numbers themselves cannot spread radially, which is worth recording because it was the
   first interpretation measured: their ring already sits at radius 243 of the painted wheel's
   280 (their outermost corner reaches 275.6), i.e. ~4 units from the edge, pinned there by
   `placeDayLabels` which keeps every label inside the wheel. Widening the ARC is the only
   spread this instrument has left. */
const ARC_START = -100;
const ARC_END = 180;
/* Where an event's marker badge sits, as a radius from the dial centre.
 *
 * This is a shared constant because TWO placements must agree: the badge itself and the run that
 * leaves it. It was the literal `VIEWBOX.r - 84` (198 units) in both places.
 *
 * It moved inward (2026-09-24, owner: "the numbers in the dial still seem very disorganized") to
 * separate the badge from the day-number label, which sits at the rim at the SAME angle. At a
 * 370px wrap the old radius put the badge's centre 28px from the label's centre, while the badge's
 * own radius (~14px) plus the label's half-diagonal (~19.6px) needs ~34px -- so the badge sat ON
 * the number. At 164 units the separation is ~49px and the two no longer touch. */
const MARKER_RADIUS_UNITS = VIEWBOX.r - 118;
/* The stylus, measured off the concept's own dial: a point at POINTER_INNER_UNITS widening to a
 * wedge POINTER_TIP_HALF_WIDTH either side at POINTER_TIP_UNITS, where its tip circle sits ON the
 * ring band (the painted disc's outer edge is ~265 units at r=282).
 *
 * RE-MEASURED 2026-09-25, FROM THE RENDERED PATH rather than from the art alone, because the
 * 2026-09-24 pass tuned these constants while the geometry was silently DEGENERATE and therefore
 * unpaintable. Owner then: "The pointer in the dial still needs considerable work ... Its so thin its
 * barely visible, a far cry from the concept."
 *
 * THE DEFECT, and it was arithmetic, not taste: the base offset was built with the MATHEMATICAL
 * perpendicular (`perpX = -sin(rad), perpY = cos(rad)`) while `positionOnArc` is a BEARING off north
 * (`x = cx + r*sin(rad)`, `y = cy - r*cos(rad)`). The two are 90 degrees apart, so the offset ran
 * ALONG the hand's axis and the three path vertices were collinear -- read off the rendered `d`,
 * |AB| 93 + |BC| 28 = |AC| 121 exactly, area ZERO. Nothing but the 0.88px dark stroke was painting.
 * That is why every previous increase in half-width changed nothing the owner could see: he was
 * looking at a stroke, and the wedge had no area to widen. It also appeared in TWO places (the first
 * render and `paintSVGSelection`, the update path that repaints on every change), and fixing one left
 * the other painting the same hairline.
 *
 * RE-MEASURED proportions, concept 06 at 853px for 420 CSS (its dial r=~271px, 1 unit = 0.588 CSS px
 * on this instrument):
 *   inner point         114.7px = 0.423 r  -> 126 units   (the wedge tapers to a point well inside)
 *   tip circle centre   144.5px = 0.533 r  -> 230 units   (on the band; the number band caps it)
 *   tip base half-width   8.1px = 0.030 r  -> 4.5 units   (the concept's blade is SLIM: ~4.8 CSS px)
 *   tip circle radius    10.4px = 0.038 r  -> 14 units    (17.6 CSS px across; the concept's is ~19)
 * The earlier 14-unit half-width came from reading the head's own width as the blade's, which would
 * have made a wedge 16.5 CSS px across at the base -- wider than the head that sits on it, i.e. the
 * opposite of the concept, where a slim blade carries a large ring.
 *
 * GEOMETRY CHECK, and these figures are MEASURED IN THE BROWSER at the governed phone widths rather
 * than derived, because two derived estimates passed geometry that actually collided:
 *   - `placeDayLabels()` seats the rim numbers' centres at radius **243.7 units** (389..432px from the
 *     dial centre at 390/420/430 CSS, DPR 3). The tip circle's far edge is 224 + 20 = 244, i.e. it ends
 *     where the numbers' own centres begin, with the whole stylus INSIDE the number ring. That bound is
 *     respected rather than relaxed: it is what keeps the hand off the day numbers.
 *   - The selected day draws no number while every day is numbered (see `renderInstrumentOverlay`),
 *     because the stylus is that day's mark and the two sit at the same angle.
 *
 * OWNER CORRECTION, 2026-09-25: "The pointer on the today page does not extend to the center of the dial
 * and is still quite small." He is looking at concept 06, and he is right -- read at full resolution, the
 * concept's stylus is a fine mint needle whose tail runs all the way to the dial's centre and widens as
 * it goes out to the ring, ending in a ring head ~50 concept px across (= 42 units, radius ~21).
 *
 * This comment used to claim the hand spanned 36.9% of the radius and that "the 53% the concept shows is
 * not reachable on this instrument". The second half of that was a measurement error, not a constraint:
 * the needle's tail is a hairline taper, and measuring only the bright part of the stroke reads the
 * thick half of it. The real constraint was always the TIP bound above, and the tail was parked at 126
 * units for no better reason than that the centre readout lives there.
 *
 * The readout is an HTML overlay and the needle is SVG BENEATH it, so extending the tail cannot cost a
 * word of legibility: the needle passes behind the centre readout exactly as the concept draws it.
 * Measured after this correction at 420x912: the needle spans 6..224 units (89% of the radius), its head
 * is 23.5 CSS px across against the concept's ~24.6, and the day-number bound is unchanged at 244.
 */
const POINTER_INNER_UNITS = 6;
const POINTER_TIP_UNITS = 224;
const POINTER_TIP_HALF_WIDTH = 5.5;
const POINTER_TIP_RADIUS = 20;
const POINTER_TIP_RING_RADIUS = 14;
const POINTER_TIP_PUPIL_RADIUS = 8;
const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

/* ── Reversible visual preview: every day number on the rim ──────────────────────────────────────
 *
 * Owner, 2026-09-24: "compare a visual state with all month numbers populated in the dial, with an
 * easy revert." This is that state, and the REVERT IS THIS ONE LINE — flip `false` back, or revert
 * the commit that changed it; nothing else in the file depends on it.
 *
 * What it does: `renderInstrumentOverlay` normally labels only the KEY days (today, the selected
 * day, every day that carries an event, and the horizon end), which is what `BUILD_SPEC.md` §7 asks
 * for ("Render a tick per day, but show labels only for today, selected day, major events, and
 * horizon end. At longer horizons thin labels; don't squeeze them."). With this true, every civil
 * day in the horizon is labelled instead.
 *
 * Two guards keep this honest while the preview is on, because a visible number must never be a
 * false claim and must never be unreadable:
 *   - The horizon is capped (`ALL_DAY_NUMBERS_MAX_DAYS`). A 31-day horizon puts 32 labels on a
 *     220deg arc, ~6.9deg apart; at the governed phone size that is ~21px of arc for a ~31px label,
 *     so labels would collide into an unreadable ring. Beyond the cap the dial falls back to key
 *     days rather than drawing a smear.
 *   - Each label still comes from `addDays(today, day)`, so every number is a real civil date in the
 *     owner's timezone and no label is ever a sample or a mock. The callout-yield and off-screen
 *     hiding in `placeDayLabels` still apply unchanged.
 *
 * The panel states which state is live via `data-day-numbers` on `.obs-dial-overlay` ("key" or
 * "all"), so a test can assert the rendered state without reaching into module internals. */
const ALL_DAY_NUMBERS = true;
const ALL_DAY_NUMBERS_MAX_DAYS = 31;

/* Where a day label may sit, measured rather than hand-tuned (owner, 2026-09-24: "dates
   aligned inside the wheel instead of clipping").

   The labels used to be anchored at a fixed `VIEWBOX.r - 22` units and centred on that point,
   which made the label's own BOX the thing that decided whether it fitted. Measured at the
   governed mobile size (a 270px wrap, so 1 unit = 0.45px): the anchor sat 117px from the
   centre while the rim is at 127px, and a 24x31px label centred there reached 132-137px —
   i.e. its corner overhung the rim by 5-10px on four of five labels. Desktop overhung less
   (620px wrap, one label by 2px), which is why this read as a mobile-only defect.

   The first fix to that made the inset per label — half each label's OWN diagonal — which
   kept every label inside the rim but put them at DIFFERENT distances from the centre, and the
   owner reported the result on 2026-09-24: "dates aren't well centered in the dial." He was
   reading a real property of that code, not a rendering artifact: a two-digit day was pulled in
   further than a narrow one, so the ring of dates was visibly uneven.

   ONE radius is now used for every label, sized by the WIDEST box present, so the dates sit
   evenly on a single circle and no label can overhang. The invariant is unchanged (the inset
   still accounts for the largest half-diagonal, converted from pixels to viewBox units with the
   wrap's MEASURED width, plus a clearance) — only the evenness differs.
   `DAY_LABEL_MAX_INSET_UNITS` is the largest such inset any governed dial needs (the biggest
   label at the smallest dial: a 31x38px box on a 240px wrap = 61 units of half-diagonal, plus
   clearance), and it seeds the pre-measurement position so nothing is ever painted overhanging.

   `DAY_LABEL_CLEARANCE_UNITS` is 10, not 6 (owner, 2026-09-25, after the arc widened: "the numbers
   and days of the week just need to move slightly interiorly so that the week days don't clip into
   the edge of the dial on the bottom left"). The label is AXIS-ALIGNED while the ring is a circle, so
   its furthest corner is a box corner at the diagonals rather than a flat edge at the top, and at the
   bottom of the dial the weekday row is the element nearest the rim. Measured at 420px: the painted
   wheel is 165.8px from the centre and the worst label corner reached 162.3 -- a **3.5px margin**,
   which is why the weekday text touched the edge. At 10 the margin is **5.9px**.

   Ten and not more, because the two constraints pull against each other: moving the labels inward
   shrinks the ring they sit on, so their spacing falls with it. Measured (worst label pair, total,
   margin): 6 -> 20.7px2, 27.7px2, 3.5px; 10 -> 24.5px2, 35.4px2, 5.9px; 12 -> 26.3px2, 39.6px2,
   7.0px; 18 -> 59.3px2 total, 10.6px. Ten is the furthest in that keeps the worst pair inside the
   browser guard's own tolerance, and it buys the margin he asked for without spending the spacing he
   called "perfect". Beyond it the honest alternative is a different form (the weekday flipping above
   the number on the lower half so the stack opens toward the centre), not a bigger inset. */
export const DAY_LABEL_CLEARANCE_UNITS = 10;
export const DAY_LABEL_MAX_INSET_UNITS = 68;

export function placeDayLabels(state, wrap) {
  if (!wrap || !state || !state.model) return [];
  const labels = [...wrap.querySelectorAll(".obs-dial-day-label")];
  const width = wrap.clientWidth;
  if (!width || width <= 0 || !labels.length) return [];
  const pxPerUnit = width / VIEWBOX.w;
  // ONE radius for all of them: sized by the widest label's half-diagonal so nothing overhangs,
  // then applied to every label so the ring reads as even (see the note above).
  let widestHalfDiagonal = 0;
  for (const span of labels) {
    widestHalfDiagonal = Math.max(
      widestHalfDiagonal,
      Math.hypot(span.offsetWidth, span.offsetHeight) / 2
    );
  }
  const insetUnits = widestHalfDiagonal / pxPerUnit + DAY_LABEL_CLEARANCE_UNITS;
  // The floor keeps a pathologically small dial from stacking labels on the centre readout.
  const radius = Math.max(VIEWBOX.r * 0.45, VIEWBOX.r - insetUnits);
  // Where each callout claims the dial. The row's FULL box counts, not only the opaque part of its
  // scrim: a day number under the transparent tail is still visibly ghosted behind the gradient
  // (caught in the review capture of this composition), which reads as the same clutter the yield
  // exists to prevent.
  const panel = wrap.closest(".obs-dial-panel");
  const opaque = panel
    ? [...panel.querySelectorAll(".obs-dial-events .obs-event-item")].map((el) => {
        const box = el.getBoundingClientRect();
        return {left: box.left, right: box.right, top: box.top, bottom: box.bottom};
      })
    : [];
  const placed = [];
  for (const span of labels) {
    const day = Number(span.dataset.day);
    if (!Number.isFinite(day)) continue;
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, radius, dayToAngle(day, state.model.totalDays));
    span.style.left = `${((point.x / VIEWBOX.w) * 100).toFixed(2)}%`;
    span.style.top = `${((point.y / VIEWBOX.h) * 100).toFixed(2)}%`;
    // A callout's opaque part WINS over a day number it lands on -- reset first, so a label a
    // previous layout hid comes back once it no longer collides. Nothing is lost by yielding: the
    // callout states that date itself ("Sep 30", "Oct 6"), and two overlapping date readings is
    // exactly the clutter the owner reported as "the numbers in the dial still seem very
    // disorganized". This only can arise at phone width, where the callouts overlap the instrument
    // by request; on desktop the rail is a column beside the dial and `opaque` is empty.
    span.style.visibility = "";
    // A label the phone's own edge would cut in half is hidden rather than shown sliced: the
    // instrument now reaches 40px past the viewport (owner, 2026-09-24), so a number at 9 or 10
    // o'clock would otherwise render as half a date.
    if (span.getBoundingClientRect().left < 0) {
      span.style.visibility = "hidden";
    }
    if (opaque.length) {
      const box = span.getBoundingClientRect();
      if (
        opaque.some(
          (entry) =>
            box.right > entry.left &&
            box.left < entry.right &&
            box.bottom > entry.top &&
            box.top < entry.bottom
        )
      ) {
        span.style.visibility = "hidden";
      }
    }
    placed.push({day, radius});
  }
  return placed;
}

/* Where a callout row sits on the dial's right side (owner, 2026-09-24, with the concept supplied:
   "The bills on the right follow the dials curved path in the concept, can there be a curved side
   rail?").

   Yes. At phone width the rail is an OVERLAY on the dial's right rather than a column beside it
   (dial.css declares that last, on purpose), and each row is placed at the height of its own
   event's marker, so the stack follows the instrument's curve the way the concept draws it. Three
   things make this more than a per-row `top`:

   1. Rows must not collide. Two events a day apart sit at nearly the same angle, so rows are
      pushed down in angular order until `CALLOUT_MIN_GAP_PX` separates the neighbours.
   2. The group must not walk off the dial. When the pushed stack ends below the dial's bottom the
      whole group is lifted to fit -- never above the dial's top.
   3. If it still does not fit, nothing is lost: the rows are absolutely positioned inside a
      scrollable rail, whose scrollable overflow includes them.

   Desktop is left completely alone: the placement applies only when the rail is actually an
   overlay, and elsewhere any inline `top` is CLEARED so a column layout cannot inherit stale
   offsets from a previous phone-width layout. */
export const CALLOUT_MIN_GAP_PX = 8;

export function placeCalloutRows(state, container) {
  const panel = container.querySelector(".obs-dial-panel");
  const rail = panel && panel.querySelector(".obs-dial-events");
  const wrap = panel && panel.querySelector(".obs-dial-svg-wrap");
  if (!panel || !rail || !wrap || !state || !state.model) return [];
  const items = [...rail.querySelectorAll(".obs-event-list--orbit > li")];
  if (!items.length) return [];
  if (getComputedStyle(rail).position !== "absolute") {
    for (const item of items) item.style.top = "";
    return [];
  }
  const wrapWidth = wrap.clientWidth;
  if (!wrapWidth) return [];
  const scale = wrapWidth / VIEWBOX.w;
  const wrapTop = wrap.offsetTop;
  // The rail stops at the TICKET'S TOP EDGE -- not at the panel's edge and not at the dial's
  // bottom. The owner, 2026-09-24: "the terminus of the scrollable bills on the right is slight
  // too low, so it clips into and overlaps the ticket, I feel the edge of the ticket should be the
  // lowest visible point, almost like the text is going behind the ticket". So the rail's scroll
  // band ends exactly where the ticket begins: a row on its way out is cut off by the ticket
  // instead of being drawn across it (the ticket also paints above, at z-index 2).
  const ticketEl = panel.querySelector(".obs-evidence-ticket");
  const ticketTop = ticketEl ? ticketEl.offsetTop : wrap.offsetTop + wrap.offsetHeight;
  rail.style.height = `${Math.round(Math.max(80, ticketTop - rail.offsetTop))}px`;
  const entries = [];
  items.forEach((item, index) => {
    const row = item.querySelector(".obs-event-item");
    const date = item.dataset.eventDate;
    if (!row || !date) return;
    const day = dayIndexForDate(date, state.model.today);
    if (!Number.isFinite(day)) return;
    const point = positionOnArc(
      VIEWBOX.cx, VIEWBOX.cy, MARKER_RADIUS_UNITS, dayToAngle(day, state.model.totalDays)
    );
    entries.push({
      item,
      index,
      id: row.dataset.eventId || null,
      target: wrapTop + point.y * scale,
      height: row.offsetHeight,
    });
  });
  if (!entries.length) return [];
  // Angular order, with document order as a stable tie-break so equal angles keep their sequence.
  entries.sort((a, b) => a.target - b.target || a.index - b.index);

  let cursor = -Infinity;
  for (const entry of entries) {
    entry.top = Math.max(entry.target, cursor + CALLOUT_MIN_GAP_PX);
    cursor = entry.top + entry.height;
  }
  const last = entries[entries.length - 1];
  const overflow = last.top + last.height - wrap.offsetHeight;
  if (overflow > 0) {
    const lift = Math.min(overflow, entries[0].top);
    for (const entry of entries) entry.top -= lift;
  }
  for (const entry of entries) entry.item.style.top = `${Math.round(entry.top)}px`;
  return entries.map((entry) => ({id: entry.id, top: Math.round(entry.top)}));
}

export function clamp(value, min, max) {
  if (Number.isNaN(value)) return min;
  return Math.min(max, Math.max(min, value));
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

export function parseDateKey(value) {
  if (value instanceof Date) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate(), 12);
  }
  if (typeof value === "string") {
    const match = DATE_ONLY.exec(value);
    if (match) {
      return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 12);
    }
  }
  const parsed = value ? new Date(value) : new Date();
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate(), 12);
}

export function dateKey(value) {
  const parsed = parseDateKey(value);
  if (!parsed) return null;
  return `${parsed.getFullYear()}-${pad2(parsed.getMonth() + 1)}-${pad2(parsed.getDate())}`;
}

export function addDays(value, amount) {
  const parsed = parseDateKey(value);
  if (!parsed) return null;
  parsed.setDate(parsed.getDate() + amount);
  return dateKey(parsed);
}

/* Calendar-day difference between date-only keys. Uses UTC date components so
   DST transitions do not make the count 23/25 hours. */
export function civilDaysBetween(from, to) {
  const a = dateKey(from);
  const b = dateKey(to);
  if (!a || !b) return 0;
  const [ay, am, ad] = a.split("-").map(Number);
  const [by, bm, bd] = b.split("-").map(Number);
  return Math.round((Date.UTC(by, bm - 1, bd) - Date.UTC(ay, am - 1, ad)) / 86400000);
}

export function dayIndexForDate(value, todayValue) {
  return Math.max(0, civilDaysBetween(todayValue, value));
}

export function dayToAngle(dayIndex, totalDays) {
  const n = Math.max(1, totalDays);
  const t = clamp(dayIndex / n, 0, 1);
  return ARC_START + t * (ARC_END - ARC_START);
}

export function angleToDay(angleDeg, totalDays) {
  const n = Math.max(1, totalDays);
  const clamped = clamp(angleDeg, ARC_START, ARC_END);
  const t = (clamped - ARC_START) / (ARC_END - ARC_START);
  return Math.round(clamp(t, 0, 1) * n);
}

export function positionOnArc(cx, cy, radius, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return {
    x: cx + radius * Math.sin(rad),
    y: cy - radius * Math.cos(rad),
  };
}

export function dateIndexFromPointer(clientX, clientY, svg, totalDays) {
  if (!svg || typeof svg.getScreenCTM !== "function") {
    return 0;
  }
  const ctm = svg.getScreenCTM();
  if (!ctm) return 0;
  const point = new DOMPoint(clientX, clientY).matrixTransform(ctm.inverse());
  const dx = point.x - VIEWBOX.cx;
  const dy = point.y - VIEWBOX.cy;
  let angle = (Math.atan2(dx, -dy) * 180) / Math.PI;
  if (angle > 180) angle -= 360;
  if (angle < -180) angle += 360;
  return angleToDay(angle, totalDays);
}

function shortestAngleDelta(from, to) {
  let delta = to - from;
  while (delta > 180) delta -= 360;
  while (delta < -180) delta += 360;
  return delta;
}

function normalizeEvent(event) {
  const amount = event.amount || {};
  const reserved = event.reserved || null;
  const source = event.fundingSource || null;
  return {
    id: event.id || `${event.date}-${event.kind || "event"}-${event.title || "event"}`,
    date: dateKey(event.date),
    kind: event.kind || "bill",
    title: event.title || "Money moment",
    amount: {
      minor: amount.minor == null ? 0 : Number(amount.minor),
      currency: amount.currency || "USD",
    },
    fundingStatus: event.fundingStatus || "unknown",
    reserved: reserved
      ? {
          minor: reserved.minor == null ? 0 : Number(reserved.minor),
          currency: reserved.currency || amount.currency || "USD",
        }
      : null,
    fundingSchedule: event.fundingSchedule || null,
    // Observed funding-source identity, kept separate from the reserved amount above.
    // A source without a provider record id is not citable, so it is dropped rather
    // than shown as an unnamed source.
    fundingSource:
      source && source.id
        ? {
            id: String(source.id),
            name: source.name || "",
            provider: source.provider || "",
            cadence: source.cadence || null,
            observedAt: source.observedAt || null,
            billReserveId: source.billReserveId || "",
          }
        : null,
    fundingSourceAmbiguous: event.fundingSourceAmbiguous === true,
    fundingSourceCandidateIds: Array.isArray(event.fundingSourceCandidateIds)
      ? event.fundingSourceCandidateIds.slice()
      : [],
    // The basis of the reserved amount above (D-013). "observed" is the ONLY basis a
    // stated figure may carry since D-015 retired the even-split model, so a payload
    // that predates this slice — including one still carrying a "derived" figure, which
    // the service can no longer produce — can never be rendered as an observation.
    fundingBasis: event.fundingBasis === "observed" ? "observed" : "unknown",
    fundingAttribution:
      event.fundingAttribution === "crew" || event.fundingAttribution === "meridian"
        ? event.fundingAttribution
        : null,
    fundingObservedAt: event.fundingObservedAt || null,
    source: event.source || "crew",
    observedAt: event.observedAt || null,
    evidenceIds: Array.isArray(event.evidenceIds) ? event.evidenceIds : [],
    // The mail-ingested invoice for this bill, resolved server-side by the SAME matcher the Plan
    // surface uses. Today's "View bill" opens it directly (owner, 2026-09-24: "View bill should
    // link to the mail ingested invoice we already have attached to the same bill on plan").
    invoice: event.invoice && event.invoice.content_url ? event.invoice : null,
    detailHref: event.detailHref || null,
  };
}

export function normalizeModel(model) {
  const nowKey = dateKey(new Date());
  const today = dateKey(model.today || nowKey);
  const horizonEnd = dateKey(model.horizonEnd || addDays(today, 14));
  const events = (model.events || [])
    .map(normalizeEvent)
    .filter((event) => event.date)
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  const projections = Array.isArray(model.projections)
    ? model.projections
        .map((entry) => ({ date: dateKey(entry.date), balance: entry.balance || null }))
        .filter((entry) => entry.date)
    : [];
  return {
    timezone: model.timezone || "local",
    today,
    horizonEnd,
    totalDays: Math.max(1, civilDaysBetween(today, horizonEnd)),
    availableToSpend: model.availableToSpend || null,
    freshness: model.freshness || "unavailable",
    observedAt: model.observedAt || null,
    events,
    projections,
  };
}

const ZERO_DECIMAL_CURRENCIES = new Set(["JPY", "KRW", "VND", "CLP", "ISK"]);

function minorToMajor(amount) {
  const currency = (amount && amount.currency) || "USD";
  const digits = ZERO_DECIMAL_CURRENCIES.has(currency.toUpperCase()) ? 0 : 2;
  return (amount ? amount.minor : 0) / (10 ** digits);
}

function minorToDisplay(amount) {
  if (!amount || amount.minor == null) return null;
  const currency = amount.currency || "USD";
  const digits = ZERO_DECIMAL_CURRENCIES.has(currency.toUpperCase()) ? 0 : 2;
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      currencyDisplay: "narrowSymbol",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(minorToMajor(amount));
  } catch (_) {
    return `${currency} ${minorToMajor(amount).toFixed(digits)}`;
  }
}

function formatLongDate(key) {
  const parsed = parseDateKey(key);
  if (!parsed) return "";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(parsed);
}

function formatShortDay(key) {
  const parsed = parseDateKey(key);
  if (!parsed) return "";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parsed);
}

function formatCenterDate(key) {
  const parsed = parseDateKey(key);
  if (!parsed) return "";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  })
    .format(parsed)
    .toUpperCase();
}


/* Date without the time of day. Used where the exact instant is already stamped
   elsewhere in the same view (the ticket header), and where repeating it costs several
   wrapped lines at the mobile viewport. */
function formatObservedDate(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(parsed);
}

function formatObservedAt(value) {
  if (!value) {
    return "Observation time unavailable";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(parsed);
}

function selectedEventForState(state) {
  if (!state.selectedEventId) return null;
  return state.model.events.find((event) => event.id === state.selectedEventId) || null;
}

function renderInstrumentOverlay(state) {
  const overlay = document.createElement("div");
  overlay.className = "obs-dial-overlay";
  overlay.setAttribute("aria-hidden", "true");

  // Center: visible event or the available-to-spend figure, matching the
  // concept art's dark sky with real data in the middle.
  const center = document.createElement("div");
  center.className = "obs-dial-center";
  // The centre states the SELECTED event in either mode. It used to be forced to null in "today"
  // mode -- a leftover from when the centre carried the safe-to-spend figure there, which OS-098
  // moved back outside the instrument. With that figure gone the gate left the centre permanently
  // empty on the page the owner opens, so the ticket named a bill while the dial said "No event
  // selected" (owner, 2026-09-24: "unless you are on the date of a bill, it says no event
  // selected, lets have it default to the next nearest event, so something populates").
  const selected = selectedEventForState(state);
  const kicker = document.createElement("p");
  kicker.className = "obs-dial-center-kicker";
  const title = document.createElement("p");
  title.className = "obs-dial-center-title";
  const amount = document.createElement("p");
  amount.className = "obs-dial-center-amount";
  const status = document.createElement("p");
  status.className = "obs-dial-center-status";
  if (selected) {
    kicker.textContent = formatCenterDate(selected.date);
    title.textContent = selected.title;
    amount.textContent = minorToDisplay(selected.amount) || "—";
    // The reserved amount, when it may honestly be stated, is the strongest thing this
    // readout can say about the selected bill; the source identity follows it, and the
    // bare status word is only shown while neither is known. The date prefix is spelled
    // out here because the centre has no adjacent date label of its own.
    status.textContent =
      fundingReserveLine(selected) ||
      fundingScheduleSummary(selected) ||
      fundingSourceSummary(selected) ||
      fundingLabel(selected.fundingStatus);
  } else {
    // No event selected: the centre states the DATE and what to do, deliberately NOT the
    // safe-to-spend figure. It used to state the figure here, which duplicated the header block
    // the owner has now made visible outside the instrument ("Safe-to-spend moved back outside
    // the compass", 2026-09-24). The figure belongs outside the compass; the centre belongs to
    // the selected moment. The copy below already existed.
    kicker.textContent = formatLongDate(state.selectedDate);
    title.textContent = "No event selected";
    amount.textContent = "—";
    status.textContent = "Choose a day to explore";
  }
  const badge = document.createElement("span");
  badge.className = "obs-dial-center-badge";
  if (selected) badge.appendChild(kindIcon(selected));
  else badge.hidden = true;
  if (amount.textContent.length > 10) amount.classList.add("obs-dial-center-amount--compact");
  center.append(kicker, badge, title, amount, status);
  overlay.appendChild(center);

  // Labels for today, selected day, events, and horizon end, positioned around
  // the instrument so they read as the engraved calendar in the concept art.
  const specialDates = new Set([state.model.today, state.model.horizonEnd, state.selectedDate]);
  for (const event of state.model.events) {
    if (event.date >= state.model.today && event.date <= state.model.horizonEnd) {
      specialDates.add(event.date);
    }
  }
  const labels = document.createElement("div");
  labels.className = "obs-dial-day-labels";
  // `ALL_DAY_NUMBERS` (see the note beside it) widens this to every civil day while the horizon is
  // short enough for the ring to stay readable; `data-day-numbers` records which state rendered, so
  // the reversible comparison is assertable without reaching into module internals.
  const showEveryDay = ALL_DAY_NUMBERS && state.model.totalDays <= ALL_DAY_NUMBERS_MAX_DAYS;
  labels.dataset.dayNumbers = showEveryDay ? "all" : "key";
  for (let day = 0; day <= state.model.totalDays; day += 1) {
    const date = addDays(state.model.today, day);
    if (!date || (!showEveryDay && !specialDates.has(date))) {
      continue;
    }
    // The SELECTED day does not get a number while every day is numbered, because the stylus is
    // that day's mark: it is drawn at the selected day's own angle, and the two were measured
    // colliding at the governed phone size (at tip 250 the wedge crosses the 206..236 unit band the
    // numbers occupy). Drawing both would be the same fact twice, the second time illegibly under a
    // mint wedge. The key-days state still labels the selection, where there is room for it.
    if (showEveryDay && date === state.selectedDate) {
      continue;
    }
    const angle = dayToAngle(day, state.model.totalDays);
    // A CONSERVATIVE first position, replaced by the measured pass once the overlay is in
    // the document. The inset is the largest any governed dial needs, so a label can never
    // be painted overhanging the rim even for one frame.
    const point = positionOnArc(
      VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - DAY_LABEL_MAX_INSET_UNITS, angle
    );
    const span = document.createElement("span");
    span.className = "obs-dial-day-label";
    // The day index is what placeDayLabels() needs to re-anchor from the wrap's MEASURED
    // width; the rendered date text would have to be parsed back into a day offset.
    span.dataset.day = String(day);
    if (date === state.model.today) span.classList.add("is-today");
    if (date === state.selectedDate) span.classList.add("is-selected");
    const parsed = parseDateKey(date);
    const dayNumber = parsed ? String(parsed.getDate()) : "";
    const weekday = parsed
      ? new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(parsed).replace(".", "")
      : "";
    const number = document.createElement("strong");
    number.textContent = dayNumber;
    const dayName = document.createElement("small");
    dayName.textContent = weekday;
    span.append(number, dayName);
    span.style.left = `${((point.x / VIEWBOX.w) * 100).toFixed(2)}%`;
    span.style.top = `${((point.y / VIEWBOX.h) * 100).toFixed(2)}%`;
    labels.appendChild(span);
  }
  overlay.appendChild(labels);

  // Quiet directional copy from the concept.
  const topCaption = document.createElement("p");
  topCaption.className = "obs-dial-caption obs-dial-caption--top";
  topCaption.textContent = "Your upcoming days";
  overlay.appendChild(topCaption);
  const bottomCaption = document.createElement("p");
  bottomCaption.className = "obs-dial-caption obs-dial-caption--bottom";
  bottomCaption.textContent = "Turn to explore your week";
  overlay.appendChild(bottomCaption);

  return overlay;
}



/* Crew's per-event estimate for one bill, in three forms so no surface has to abbreviate a
   sentence it cannot fit:

     value    "$29.89/event"        the amount and its unit, alone.
     summary  "$29.89/event · Crew estimate"
              the SHORT form for the event row and the centre. The OS-048b lesson was that
              a long label wrapped and collided with its own value at 420px, so the row
              gets a compact marker and the ticket carries the sentence.
     note     "$29.89/event · Crew estimate, due Sep 20 for Veterans Home"
              the ticket's full statement, naming the deadline it is measured against.

   Every form says "estimate" and the AUTHOR is read from the schedule's own basis, so the
   two provenances stay distinguishable: Crew reported the figure itself, or Meridian
   applied Crew's published rule to an observed plan. Either way it is an estimate, never
   money held, and it must never read as the observed `reserved` figure beside it. */

const SCHEDULE_BASES = new Set(["crew_reported", "crew_estimate"]);

function scheduleAuthor(schedule) {
  return schedule.basis === "crew_reported" ? "Crew's own estimate" : "Crew estimate";
}

export function fundingScheduleValue(event) {
  const schedule = event && event.fundingSchedule;
  if (!schedule || !SCHEDULE_BASES.has(schedule.basis) || !schedule.contribution) return "";
  const contribution = minorToDisplay(schedule.contribution);
  if (!contribution) return "";
  return `${contribution}/event`;
}

function fundingScheduleSummary(event) {
  const value = fundingScheduleValue(event);
  if (!value) return "";
  return `${value} · ${scheduleAuthor(event.fundingSchedule)}`;
}

function fundingScheduleNote(event) {
  const value = fundingScheduleValue(event);
  if (!value) return "";
  const schedule = event.fundingSchedule;
  const parts = [`${value} · ${scheduleAuthor(schedule)}`];
  if (schedule.deadline) parts.push(`due ${formatShortDay(schedule.deadline)}`);
  if (schedule.planName) parts.push(`for ${schedule.planName}`);
  return parts.join(", ");
}

function fundingLabel(status) {
  const labels = {
    reserved: "Reserved",
    partial: "Partially funded",
    unfunded: "Unfunded",
    unknown: "Funding unknown",
  };
  return labels[status] || labels.unknown;
}

/* The funding source is the Crew funding plan the owner calls their income source /
   Funding Cadence, matched to the reserve that contained the bill. It is identity and
   provenance only: it says WHO funds the bill and says nothing about how much of a
   dated occurrence is reserved, which stays `fundingStatus` and is still unknown. Two
   plans claiming one reserve is ambiguity, and the copy says so rather than naming one
   of them. Nothing is substituted for a missing link. */
export function fundingSourceValue(event) {
  const source = event && event.fundingSource;
  // A source is only citable through the provider's own record id; a name alone
  // cannot be cited or renamed safely, so it is not shown.
  if (source && source.id && typeof source.name === "string" && source.name) {
    return source.name;
  }
  if (event && event.fundingSourceAmbiguous === true) {
    return "Not determined (multiple candidates)";
  }
  return "";
}

export function fundingSourceSummary(event) {
  const value = fundingSourceValue(event);
  return value ? `Funding source: ${value}` : "";
}

/* The reserved amount, and — the part that matters — the basis it may be claimed on
   (D-013). The service emits a figure only for the earliest occurrence in the horizon,
   so the same reserve is never multiplied across future due dates (D-010), and every
   figure arrives with `fundingBasis`:

     observed  Crew reported this bill's own reservedAmount. This is the only basis.
     unknown   nothing is stated, and no figure is shown.

   D-015 retired the even-split model, so a "derived" figure no longer exists and a
   payload still carrying one is treated as unknown: an unlabelled or no-longer-supported
   number could only be read as an observation, which is what D-013 forbids. */

function isStatedFigure(event) {
  return Boolean(event) && event.fundingBasis === "observed";
}

function shortfallText(event) {
  const amountMinor = event.amount && event.amount.minor != null ? Number(event.amount.minor) : 0;
  const reservedMinor =
    event.reserved && event.reserved.minor != null ? Number(event.reserved.minor) : 0;
  // A reserve above the obligation is a surplus, never a negative shortfall.
  const remainingMinor = Math.max(0, amountMinor - reservedMinor);
  if (remainingMinor <= 0) return "";
  return minorToDisplay({ minor: remainingMinor, currency: event.amount.currency });
}

export function fundingReserveValue(event) {
  if (!event || !isStatedFigure(event)) return "";
  const amount = minorToDisplay(event.amount);
  const reserved = event.reserved && event.reserved.minor != null
    ? minorToDisplay(event.reserved)
    : null;
  if (reserved && event.reserved.minor > 0) {
    const short = shortfallText(event);
    return short ? `${reserved} of ${amount} set aside — ${short} short`
                 : `${reserved} of ${amount} set aside`;
  }
  // A stated zero: Crew reported an emptied reserve, which is a fact, unlike silence.
  if (event.fundingStatus === "unfunded") return `${amount} — not yet set aside`;
  return "";
}

export function fundingReserveSummary(event) {
  // Only an observed figure can reach here since D-015 retired the even-split model, so
  // there is no estimate marker to add: the ticket carries the observation's provenance.
  return fundingReserveValue(event);
}

/* The day-context form: the same statement, naming the occurrence it belongs to. Used
   where the date is not already the adjacent label (the centre readout and the
   accessibility text), never twice in one row. */
export function fundingReserveLine(event) {
  const summary = fundingReserveSummary(event);
  if (!summary || !event.date) return "";
  return `Next due ${formatShortDay(event.date)} · ${summary}`;
}

/* The bill-level provenance for the evidence ticket. An observed figure names the
   provider read that reported it. Since D-015 there is no derived figure to distinguish
   it from: the even-split model is retired, so a stated figure has exactly one author. */
export function fundingBasisNote(event) {
  if (!event || !isStatedFigure(event)) return "";
  const by = event.fundingAttribution === "crew" ? "observed from Crew" : "Meridian-side amount";
  // Date only: the ticket header already stamps the full observation time, and repeating
  // the time of day here wrapped the value over three extra lines at the mobile viewport.
  const observed = event.fundingObservedAt ? formatObservedDate(event.fundingObservedAt) : "";
  return observed ? `${by} · ${observed}` : by;
}

/* Kit README semantic mapping. The dial service emits only `kind` plus the
   commitment's own name, so the badge glyph is resolved from the event's own
   descriptive text and falls back to the kind default. This is presentation only:
   no financial meaning is inferred, and an unrecognised name simply keeps the kind
   glyph. Order matters — the first match wins. */
const CATEGORY_ICONS = [
  [/(electric|power|utility|energy|gas|water|sewer)/i, "lightning-charge"],
  [/(internet|wifi|broadband|fibre|fiber|wireless|phone|mobile)/i, "wifi"],
  [/(rent|mortgage|housing|landlord)/i, "house"],
  [/(grocer|food|market)/i, "basket"],
  [/(transit|bus|train|metro|commut)/i, "bus-front"],
  [/(stream|entertain|game|gaming|hobby)/i, "controller"],
  [/(reserve|savings|bank)/i, "bank"],
  [/(household|family|people|connection)/i, "people"],
  [/(insurance|alert|notification)/i, "bell"],
  [/(passkey|security|key)/i, "key"],
  [/(backup|cloud)/i, "cloud-arrow-down"],
  [/(history|action log)/i, "clock-history"],
];

/* The kit has no bullseye or arrow-left-right glyph, so goal and transfer map to
   the names it does supply (flag, arrow-right). */
const KIND_ICONS = {
  bill: "lightning-charge",
  income: "star",
  goal: "flag",
  transfer: "arrow-right",
};

export function eventIconName(event) {
  const safe = event || {};
  const kind = safe.kind || "bill";
  if (kind === "income") return "star";
  if (kind === "goal") return "flag";
  if (kind === "transfer") return "arrow-right";
  const haystack = typeof safe.title === "string" ? safe.title : "";
  for (const [pattern, icon] of CATEGORY_ICONS) {
    if (pattern.test(haystack)) return icon;
  }
  return KIND_ICONS[kind] || "lightning-charge";
}

function kindIcon(event) {
  const name = eventIconName(event);
  const icon = document.createElement("img");
  icon.src = `/static/img/meridian/observatory/kit-2026-09-16/icons/${name}.svg`;
  icon.alt = "";
  icon.width = 24;
  icon.height = 24;
  icon.dataset.eventIcon = name;
  return icon;
}

function arcPath(r) {
  const parts = [];
  const steps = 61;
  for (let i = 0; i <= steps; i += 1) {
    const angle = ARC_START + ((ARC_END - ARC_START) * i) / steps;
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, r, angle);
    parts.push(`${i === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`);
  }
  return parts.join(" ");
}

function renderDialSVG(state, container) {
  const { today, horizonEnd, totalDays, events } = state.model;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${VIEWBOX.w} ${VIEWBOX.h}`);
  svg.setAttribute("class", "obs-dial-svg");
  // Semantic date controls live in HTML (range, buttons, event list). The
  // decorative/diagram layer is hidden from assistive technology.
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");

  const arc = document.createElementNS("http://www.w3.org/2000/svg", "path");
  arc.setAttribute("d", arcPath(VIEWBOX.r));
  arc.setAttribute("class", "obs-dial-arc");
  svg.appendChild(arc);

  // Ticks, one per civil day including the horizon end.
  const tickGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const specialDays = new Set([today, horizonEnd, state.selectedDate]);
  for (let day = 0; day <= totalDays; day += 1) {
    const angle = dayToAngle(day, totalDays);
    const outer = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r + 8, angle);
    const dateForTick = addDays(today, day);
    const isSpecial = specialDays.has(dateForTick);
    const inner = positionOnArc(
      VIEWBOX.cx,
      VIEWBOX.cy,
      isSpecial ? VIEWBOX.r - 18 : VIEWBOX.r - 11,
      angle,
    );
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", String(outer.x.toFixed(2)));
    line.setAttribute("y1", String(outer.y.toFixed(2)));
    line.setAttribute("x2", String(inner.x.toFixed(2)));
    line.setAttribute("y2", String(inner.y.toFixed(2)));
    line.setAttribute("class", isSpecial ? "obs-dial-tick--major" : "obs-dial-tick");
    tickGroup.appendChild(line);
  }
  svg.appendChild(tickGroup);

  // Transparent hit track for pointer drags (full circle around the visible arc
  // plus a little padding; pointer events only begin inside the ring).
  const hit = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  hit.setAttribute("cx", String(VIEWBOX.cx));
  hit.setAttribute("cy", String(VIEWBOX.cy));
  hit.setAttribute("r", String(VIEWBOX.r + 15));
  hit.setAttribute("class", "obs-dial-track-hit");
  svg.appendChild(hit);

  // Markers grouped by date; multiple events share a marker and are resolved in
  // the HTML event list/ticket instead of overlapping inside the SVG.
  const markerGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const byDate = new Map();
  for (const event of events) {
    if (!byDate.has(event.date)) byDate.set(event.date, []);
    byDate.get(event.date).push(event);
  }
  for (const [eventDate, dayEvents] of byDate.entries()) {
    if (eventDate < today || eventDate > horizonEnd) continue;
    const day = dayIndexForDate(eventDate, today);
    const angle = dayToAngle(day, totalDays);
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, MARKER_RADIUS_UNITS, angle);
    const leaderStart = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, MARKER_RADIUS_UNITS - 6, angle);
    const leaderEnd = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, MARKER_RADIUS_UNITS + 11, angle);
    const leader = document.createElementNS("http://www.w3.org/2000/svg", "line");
    leader.setAttribute("class", "obs-dial-leader");
    leader.setAttribute("x1", String(leaderStart.x.toFixed(2)));
    leader.setAttribute("y1", String(leaderStart.y.toFixed(2)));
    leader.setAttribute("x2", String(leaderEnd.x.toFixed(2)));
    leader.setAttribute("y2", String(leaderEnd.y.toFixed(2)));
    markerGroup.appendChild(leader);
    const marker = document.createElementNS("http://www.w3.org/2000/svg", "g");
    marker.setAttribute("class", "obs-dial-marker");
    marker.setAttribute("data-date", eventDate);
    marker.setAttribute("data-count", String(dayEvents.length));
    marker.setAttribute("data-kind", dayEvents[0].kind);
    if (eventDate === state.selectedDate && dayEvents.some((event) => event.id === state.selectedEventId)) {
      marker.setAttribute("data-selected", "true");
    }
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", String(point.x.toFixed(2)));
    circle.setAttribute("cy", String(point.y.toFixed(2)));
    // A single-event marker is now big enough to CARRY its icon, and a multi-event marker keeps the
    // count: a number is more use than one of N icons, and the events behind it are listed in the panel.
    circle.setAttribute("r", dayEvents.length > 1 ? "15" : "14");
    circle.setAttribute("fill", "currentColor");
    marker.appendChild(circle);
    if (dayEvents.length === 1) {
      // Owner, 2026-09-25: "I see they have to do with the commitments, can we instead have them be
      // miniature versions of the bill icons on the right". The same `eventIconName()` the event list
      // uses, drawn as an SVG <image> on the marker's own disc, so a lightning bolt on the ring and a
      // lightning bolt in the list are literally the same asset rather than two lookalikes that can
      // drift apart. Sized to sit inside the disc with a 3-unit rim.
      const iconName = eventIconName(dayEvents[0]);
      const image = document.createElementNS("http://www.w3.org/2000/svg", "image");
      image.setAttribute("class", "obs-dial-marker-icon");
      image.setAttribute("href", `/static/img/meridian/observatory/kit-2026-09-16/icons/${iconName}.svg`);
      image.setAttribute("x", (point.x - 10).toFixed(2));
      image.setAttribute("y", (point.y - 10).toFixed(2));
      image.setAttribute("width", "20");
      image.setAttribute("height", "20");
      image.dataset.eventIcon = iconName;
      marker.appendChild(image);
    }
    if (dayEvents.length > 1) {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", String(point.x.toFixed(2)));
      text.setAttribute("y", String(point.y.toFixed(2) + 5));
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-size", "13");
      text.setAttribute("fill", "#eee4cf");
      text.setAttribute("font-weight", "700");
      text.textContent = String(dayEvents.length);
      marker.appendChild(text);
    }
    marker.addEventListener("click", () => {
      const firstId = dayEvents[0].id;
      state.selectedDate = eventDate;
      state.selectedEventId = dayEvents.some((event) => event.id === state.selectedEventId)
        ? state.selectedEventId
        : firstId;
      state.mode = "explore";
      update(state, container);
    });
    markerGroup.appendChild(marker);
  }
  svg.appendChild(markerGroup);

  // Pointer for selected day.
  const selectedIndex = dayIndexForDate(state.selectedDate, today);
  const pointerAngle = dayToAngle(selectedIndex, totalDays);
  // The stylus is a TAPERED WEDGE, not a line with a dot on the end (owner, 2026-09-24: "the
  // stylus on the dial is much more tapered on the concept"). Measured off the concept: it comes
  // to a POINT at the inner end and widens as it runs out to the ring, where the tip circle sits.
  // The pivot end is well inside the dark disc, so the wedge reads as a needle rather than a spoke.
  const pointerGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  pointerGroup.setAttribute("class", "obs-dial-pointer");
  const needlePoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, POINTER_INNER_UNITS, pointerAngle);
  const tipPoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, POINTER_TIP_UNITS, pointerAngle);
  // The perpendicular at the tip, which is the wedge's base -- derived from the TWO POINTS rather
  // than from the angle, and that derivation is the fix for a real defect found 2026-09-25.
  //
  // This read `perpX = -sin(rad) * HALF; perpY = cos(rad) * HALF`, the mathematical convention, while
  // `positionOnArc` above returns a BEARING off north (`x = cx + r*sin`, `y = cy - r*cos`). A
  // 90-degree mismatch is not a subtle tilt here: the "perpendicular" offset then ran ALONG the
  // hand's own axis, so the path's three vertices were collinear -- measured off the rendered `d`,
  // |AB| 93 + |BC| 28 = |AC| 121 exactly -- and the triangle's area was zero. What painted was a
  // 0.88px dark stroke along a degenerate outline, which is precisely what the owner reported: "Its
  // so thin its barely visible, a far cry from the concept."
  //
  // Deriving it from the points makes the base genuinely perpendicular to whatever direction the
  // hand points, so this cannot break again if the angle convention changes.
  const axisX = tipPoint.x - VIEWBOX.cx;
  const axisY = tipPoint.y - VIEWBOX.cy;
  const axisLength = Math.hypot(axisX, axisY) || 1;
  const perpX = (-axisY / axisLength) * POINTER_TIP_HALF_WIDTH;
  const perpY = (axisX / axisLength) * POINTER_TIP_HALF_WIDTH;
  const needle = document.createElementNS("http://www.w3.org/2000/svg", "path");
  needle.setAttribute("class", "obs-dial-pointer-needle");
  needle.setAttribute(
    "d",
    `M${needlePoint.x.toFixed(2)} ${needlePoint.y.toFixed(2)} ` +
      `L${(tipPoint.x + perpX).toFixed(2)} ${(tipPoint.y + perpY).toFixed(2)} ` +
      `L${(tipPoint.x - perpX).toFixed(2)} ${(tipPoint.y - perpY).toFixed(2)} Z`
  );
  // The tip circle, drawn as the concept does: a mint disc with the DARK ring INSIDE it and a mint
  // centre, rather than a cream dot (owner: "a black circle on it instead of the orange/cream one
  // ... an inner circle instead of an outer one").
  const tip = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  tip.setAttribute("class", "obs-dial-pointer-tip");
  tip.setAttribute("cx", String(tipPoint.x.toFixed(2)));
  tip.setAttribute("cy", String(tipPoint.y.toFixed(2)));
  tip.setAttribute("r", String(POINTER_TIP_RADIUS));
  const tipRing = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  tipRing.setAttribute("class", "obs-dial-pointer-tip-ring");
  tipRing.setAttribute("cx", String(tipPoint.x.toFixed(2)));
  tipRing.setAttribute("cy", String(tipPoint.y.toFixed(2)));
  tipRing.setAttribute("r", String(POINTER_TIP_RING_RADIUS));
  const tipPupil = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  tipPupil.setAttribute("class", "obs-dial-pointer-tip-pupil");
  tipPupil.setAttribute("cx", String(tipPoint.x.toFixed(2)));
  tipPupil.setAttribute("cy", String(tipPoint.y.toFixed(2)));
  tipPupil.setAttribute("r", String(POINTER_TIP_PUPIL_RADIUS));
  pointerGroup.append(needle, tip, tipRing, tipPupil);
  svg.appendChild(pointerGroup);

  return svg;
}

function renderLegend() {
  const legend = document.createElement("ul");
  legend.className = "obs-dial-legend";
  const entries = [
    ["Bill", "#c1a9e2"],
    ["Income", "#a5d4bf"],
    ["Goal", "#c6aa71"],
    ["Transfer", "#b7b8cb"],
  ];
  for (const [label, color] of entries) {
    const item = document.createElement("li");
    const dot = document.createElement("span");
    dot.className = "obs-dot";
    dot.style.background = color;
    item.append(dot, document.createTextNode(label));
    legend.appendChild(item);
  }
  return legend;
}

function eventsForDate(state, date) {
  return state.model.events.filter((event) => event.date === date);
}

function describeSelectedDay(state) {
  const events = eventsForDate(state, state.selectedDate);
  const dateText = formatLongDate(state.selectedDate);
  if (!events.length) return `${dateText}, no scheduled money moments`;
  const parts = events.map((event) => {
    const amount = minorToDisplay(event.amount);
    // The figure first — it is the answer to "how much is set aside for this one" — then
    // who funds the bill. The basis stays attached to the figure so the spoken text
    // carries the same distinction the row does.
    const funding =
      fundingReserveSummary(event) ||
      fundingSourceSummary(event) ||
      fundingLabel(event.fundingStatus);
    return `${event.title}, ${amount || "amount unavailable"}, ${funding}`;
  });
  return `${dateText}, ${parts.join("; ")}`;
}

function renderEventList(state, container) {
  const wrap = document.createElement("div");
  wrap.className = "obs-dial-events";
  wrap.tabIndex = 0;
  wrap.setAttribute("role", "region");
  wrap.setAttribute("aria-label", "Upcoming money moments; scroll for more events");
  // The rail scrolls independently of the panel, so the runs must follow it: without
  // this, scrolling left every run pointing at the position its row used to occupy.
  // This element is replaced on every update(), so the listener is discarded with it
  // and there is no separate binding to keep in sync.
  wrap.addEventListener("scroll", () => renderConnectors(state, container), { passive: true });

  const heading = document.createElement("h3");
  heading.className = "obs-dial-date-heading";
  const isToday = state.selectedDate === state.model.today;
  heading.textContent = isToday
    ? `Today · ${formatShortDay(state.selectedDate)}`
    : formatLongDate(state.selectedDate);
  wrap.appendChild(heading);

  // Show the full upcoming horizon, not only the selected day. The concept uses
  // the side rail as an orbit of all visible money moments.
  const upcoming = state.model.events.filter(
    (event) => event.date >= state.model.today && event.date <= state.model.horizonEnd
  );
  if (!upcoming.length) {
    const empty = document.createElement("p");
    empty.className = "obs-empty";
    empty.textContent = "No scheduled money moments in this horizon.";
    wrap.appendChild(empty);
  } else {
    const subheading = document.createElement("p");
    subheading.className = "obs-dial-subheading";
    subheading.textContent = "Upcoming money moments";
    wrap.appendChild(subheading);
    const list = document.createElement("ul");
    list.className = "obs-event-list obs-event-list--orbit";
    for (const event of upcoming) {
      const item = document.createElement("li");
      item.dataset.eventDate = event.date;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "obs-event-item";
      button.dataset.kind = event.kind;
      button.dataset.eventId = event.id;
      if (state.mode !== "today" && event.id === state.selectedEventId) {
        button.setAttribute("data-selected", "true");
      }
      const kind = document.createElement("span");
      kind.className = "obs-event-kind";
      kind.appendChild(kindIcon(event));
      const body = document.createElement("span");
      body.className = "obs-event-body";
      const date = document.createElement("span");
      date.className = "obs-event-date";
      date.textContent = formatShortDay(event.date);
      const title = document.createElement("span");
      title.className = "obs-event-title";
      title.textContent = event.title;
      button.setAttribute("aria-description", `Source: ${event.source}`);
      body.append(date, title);
      // Funding is a BILL concept: a bill may or may not have a reserve covering a future
      // occurrence, which is what the funder-status vocabulary is about. Income is not
      // funded, it arrives -- so a funding status on an income row is a category error, and
      // on the owner's own ledger "Funding unknown" under a Paycheck read as though the
      // amount were unknown while the row was displaying +$1,663.00. Income rows carry the
      // date, the title and the amount; nothing is claimed about funding.
      if (event.kind !== "income") {
        const meta = document.createElement("span");
        meta.className = "obs-event-meta";
        // Three different statements are joined rather than substituted for one another.
        // The source is a fact about the bill on every row; the observed figure belongs
        // to the one occurrence it was measured against; the schedule is Crew's own
        // per-event estimate toward that occurrence's deadline. Only a figure the
        // provider reported is stated as money (D-013); the schedule says "estimated by
        // Crew" in its own words, so a projection can never read as a balance.
        const reserveValue = fundingReserveSummary(event);
        const sourceSummary = fundingSourceSummary(event);
        const scheduleSummary = fundingScheduleSummary(event);
        meta.textContent = [sourceSummary, reserveValue, scheduleSummary].filter(Boolean).join(" · ")
          || fundingLabel(event.fundingStatus);
        body.append(meta);
      }
      const amount = document.createElement("strong");
      amount.className = "obs-event-amount";
      amount.dataset.direction = event.kind === "income" ? "incoming" : "outgoing";
      const displayAmount = minorToDisplay(event.amount);
      amount.textContent = displayAmount ? (event.kind === "income" ? `+${displayAmount}` : `−${displayAmount}`) : "—";
      button.append(kind, body, amount);
      button.addEventListener("click", () => {
        const restoreFocus = document.activeElement === button;
        state.selectedEventId = event.id;
        state.selectedDate = event.date;
        state.mode = "explore";
        update(state, container);
        if (restoreFocus) {
          const replacement = [...container.querySelectorAll(".obs-event-item")]
            .find((item) => item.dataset.eventId === event.id);
          replacement?.focus({ preventScroll: true });
        }
        announce(`Selected ${event.title} on ${formatShortDay(event.date)}.`);
      });
      item.appendChild(button);
      list.appendChild(item);
    }
    wrap.appendChild(list);
  }

  return wrap;
}

/* Connector runs. The concept ties each rim marker to its callout with a dashed run,
   so both ends come from real geometry: the start is the same projection
   `renderDialSVG` uses for the marker, and the end is the callout row's own box. The
   layer is decorative, clipped to the panel and never a hit target, so it adds no
   layout width and cannot move the dial or the rail. */
function renderConnectors(state, container) {
  const panel = container.querySelector(".obs-dial-panel");
  if (!panel) return;
  let layer = panel.querySelector(".obs-dial-connectors");
  if (!layer) {
    layer = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    layer.setAttribute("class", "obs-dial-connectors");
    layer.setAttribute("aria-hidden", "true");
    layer.setAttribute("focusable", "false");
    panel.appendChild(layer);
  }
  while (layer.firstChild) layer.removeChild(layer.firstChild);

  const svg = panel.querySelector(".obs-dial-svg");
  if (!svg) return;
  const panelBox = panel.getBoundingClientRect();
  const svgBox = svg.getBoundingClientRect();
  if (!panelBox.width || !svgBox.width) return;
  layer.setAttribute("viewBox", `0 0 ${panelBox.width.toFixed(1)} ${panelBox.height.toFixed(1)}`);
  layer.setAttribute("preserveAspectRatio", "none");

  const scale = svgBox.width / VIEWBOX.w;
  const originX = svgBox.left - panelBox.left;
  const originY = svgBox.top - panelBox.top;

  // The rail is internally scrollable (`max-height: calc(100vw - 90px)`), so with a long
  // horizon a row can sit in layout far below what the rail actually shows. A run to a
  // row the reader cannot see is a line to nowhere: it leaves the dial, runs down past
  // the rail, and is cut off by the layer's own `overflow: hidden` in mid-air. Only rows
  // whose centre is inside the rail's visible box get a run; the rest appear as soon as
  // the reader scrolls them into view, because the rail re-runs this on scroll.
  const rail = panel.querySelector(".obs-dial-events");
  const railBox = rail ? rail.getBoundingClientRect() : null;

  const seen = new Set();
  for (const event of state.model.events) {
    if (event.date < state.model.today || event.date > state.model.horizonEnd) continue;
    if (seen.has(event.id)) continue;
    seen.add(event.id);
    const row = panel.querySelector(`.obs-event-item[data-event-id="${event.id}"]`);
    if (!row) continue;
    const day = dayIndexForDate(event.date, state.model.today);
    const angle = dayToAngle(day, state.model.totalDays);
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, MARKER_RADIUS_UNITS, angle);
    const sx = originX + point.x * scale;
    const sy = originY + point.y * scale;
    const rowBox = row.getBoundingClientRect();
    const rowMidY = rowBox.top + rowBox.height / 2;
    if (railBox && (rowMidY < railBox.top || rowMidY > railBox.bottom)) continue;
    const tx = rowBox.left - panelBox.left - 4;
    const ty = rowBox.top - panelBox.top + rowBox.height / 2;
    // A run needs somewhere to go; skip rather than draw backwards through the dial.
    if (tx <= sx + 6) continue;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("class", "obs-dial-connector");
    path.setAttribute("data-connector-for", event.id);
    const midX = sx + (tx - sx) * 0.55;
    path.setAttribute(
      "d",
      `M${sx.toFixed(1)} ${sy.toFixed(1)} Q${midX.toFixed(1)} ${sy.toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)}`
    );
    layer.appendChild(path);
    const end = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    end.setAttribute("class", "obs-dial-connector-end");
    end.setAttribute("cx", tx.toFixed(1));
    end.setAttribute("cy", ty.toFixed(1));
    end.setAttribute("r", "3");
    layer.appendChild(end);
  }
}

function renderEvidenceTicket(state, event) {
  const ticket = document.createElement("article");
  // The ticket owns its parchment silhouette. Do not also give it the generic obs-panel--paper
  // surface: that produced a parchment box around the ticket-shaped receipt (owner, 2026-09-24:
  // "the ticket is surrounded by a parchment box, the box needs to be removed").
  ticket.className = "obs-evidence-ticket";
  if (!event) {
    // The populated ticket places its children by named grid area. The empty state has no
    // header/facts/actions children, so without this modifier they auto-place into the two
    // columns of the mobile template and render side by side on top of each other -- the
    // owner saw "No event selected" with the detail text overlapping it.
    ticket.classList.add("obs-evidence-ticket--empty");
    const title = document.createElement("h3");
    title.className = "obs-ticket-title";
    title.textContent = "No event selected";
    const detail = document.createElement("p");
    detail.className = "obs-ticket-detail";
    detail.textContent = "Choose a day or event on the dial to see its calculation and source evidence.";
    ticket.append(title, detail);
    return ticket;
  }

  const header = document.createElement("div");
  header.className = "obs-ticket-header";
  const headerText = document.createElement("div");
  const title = document.createElement("h3");
  title.className = "obs-ticket-title";
  title.textContent = event.title;
  const sourceStamp = document.createElement("span");
  sourceStamp.className = "obs-source-stamp";
  const observed = event.observedAt || state.model.observedAt || "Observation time unavailable";
  sourceStamp.textContent = `${event.source} · ${formatObservedAt(observed)}`;
  headerText.append(title, sourceStamp);
  const dateStamp = document.createElement("time");
  dateStamp.className = "obs-ticket-date";
  dateStamp.dateTime = event.date;
  dateStamp.title = formatLongDate(event.date);
  dateStamp.textContent = `${formatShortDay(event.date)}\n${event.date.slice(0, 4)}`;
  const displayAmount = minorToDisplay(event.amount);
  header.append(headerText, dateStamp);

  const rows = document.createElement("dl");
  rows.className = "obs-ticket-rows";
  // TWO FACTS. Today is a snapshot of the money, and the rest of the story is on Plan -- the
  // owner's own framing (2026-09-24): "All of the other additional information can be found on
  // plan, so we don't need it on today I feel. Today is more of a snapshot of information."
  // So the ticket states what the bill IS (its amount) and where it STANDS (reserved / stated /
  // funding status), and drops the funding source, the funding schedule and the shortfall
  // paragraph -- which is also what the concept's ticket carries ("Bill amount | Reserved").
  // Nothing is lost that the reader cannot see: the gap between the two figures IS the shortfall.
  const rowData = [
    ["Amount", displayAmount || "—"],
  ];
  if (isStatedFigure(event)) {
    // The bill-level statement. The author and the observation date that used to ride along here
    // ("$0.00 · observed from Crew · Sep 8, 2026") are Plan's detail, not the snapshot's.
    const figure = event.reserved && event.reserved.minor > 0
      ? minorToDisplay(event.reserved)
      : minorToDisplay({ minor: 0, currency: event.amount.currency });
    rowData.push(["Set aside", figure]);
  } else if (event.reserved && event.reserved.minor != null) {
    rowData.push(["Reserved", minorToDisplay(event.reserved)]);
  } else {
    rowData.push(["Funding", fundingLabel(event.fundingStatus)]);
  }
  for (const [label, value] of rowData) {
    const group = document.createElement("div");
    group.className = "obs-ticket-row";
    const dt = document.createElement("dt");
    dt.className = "obs-ticket-row-label";
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.className = "obs-ticket-row-value";
    dd.textContent = value || "—";
    group.append(dt, dd);
    rows.appendChild(group);
  }

  // The bill's icon, on the left, as the concept draws it. `.obs-ticket-kind` is sized by the
  // phone seating block; on desktop it keeps the shared event-kind styling.
  const kind = document.createElement("span");
  kind.className = "obs-ticket-kind";
  kind.appendChild(kindIcon(event));

  const body = [kind, header, rows];

  const actions = document.createElement("div");
  actions.className = "obs-ticket-actions";
  // NO second link here. "View bill" below already opens the mail-ingested invoice (owner,
  // 2026-09-24: "View bill should link to the mail ingested invoice we already have attached to the
  // same bill on plan"), and a first attempt added an "Invoice · <subject>" anchor beside it. That
  // was wrong twice over: the concept's ticket carries ONE control in this row ("View bill →"), and
  // the ticket is a named-area grid in which `facts` and `actions` share a row -- so the long
  // subject starved the facts column to 84px and its amounts ran under the action text. The
  // invoice remains available through the single View bill destination below.
  if (event.evidenceIds && event.evidenceIds.length) {
    const evidenceLink = document.createElement("a");
    evidenceLink.className = "obs-button obs-button--ghost";
    evidenceLink.href = "#";
    evidenceLink.textContent = "View evidence";
    evidenceLink.addEventListener("click", (e) => {
      e.preventDefault();
      const list = document.createElement("ul");
      list.className = "obs-event-list";
      for (const id of event.evidenceIds) {
        const item = document.createElement("li");
        item.textContent = `Evidence ${id}`;
        list.appendChild(item);
      }
      // Simple disclosure inside the ticket; full protected evidence viewer is
      // connected in the real workspace slice.
      const existing = ticket.querySelector(".obs-inline-evidence");
      if (existing) existing.remove();
      list.className += " obs-inline-evidence";
      ticket.appendChild(list);
    });
    actions.appendChild(evidenceLink);
  }
  // An invoice still determines the View bill destination below, but its status does not need a
  // second line in the shared actions row. Removing that redundant "Bill email attached" copy keeps
  // the evidence ticket's facts and single action aligned at the compact phone width.
  // "View bill" opens the bill's actual invoice when one was matched, and only falls back to the
  // Plan workspace when it was not. This is the owner's correction of 2026-09-24: the control used
  // to say "View bill" and land on the Plan page, which is not the bill.
  const billHref = event.invoice ? event.invoice.content_url : event.detailHref;
  if (billHref) {
    const detail = document.createElement("a");
    detail.className = "obs-button";
    detail.href = billHref;
    // Same tab, deliberately. Opening the evidence page in a NEW tab is what made it a one way
    // street: the page's Back control can only return the tab it lives in, and on the owner's
    // phone the app was left behind in the other tab (2026-09-24). Navigating in place means the
    // invoice's Back control lands back on Today, where the reader started.

    // The arrow says the control LEAVES this page for the bill/invoice, as the concept draws it
    // ("View bill ->"). It is part of the label rather than decoration so a screen reader reports
    // the same affordance.
    detail.textContent = event.kind === "bill" ? "View bill \u2192" : "View detail \u2192";
    actions.appendChild(detail);
  }
  body.push(actions);
  ticket.append(...body);
  return ticket;
}

function renderControls(state, onChange) {
  const controls = document.createElement("div");
  controls.className = "obs-dial-controls";

  /* No Previous day / Next day / Back to today buttons.
   *
   * `BUILD_SPEC.md` §7 asked for those three controls, and they were built. The owner has since
   * seen them on the phone and asked for them back out: "remove the redundant previous day, next
   * day, and similar dial navigation controls because navigation exists elsewhere." On Today they
   * were a second, worse copy of navigation the dial already carries -- the rim ticks and day
   * numbers select a day, the event rows select an event, dragging the ring scrubs the horizon --
   * and at 420x912 they sat in their own 44px row between the evidence ticket and "Explore my
   * plan", which pushed the ticket off the first screen for no new capability. Sheet order follows
   * the newest explicit governing record (D-004).
   *
   * Navigation is NOT lost, and that is the point of leaving the range control in place:
   * `#obs-dial-range` is the keyboard path -- Arrow keys step one day, Home/End jump to the
   * horizon ends, and its `aria-valuetext` states the date, its events and their amounts. It stays
   * visually collapsed (`.obs-dial-range-wrap` is clipped to 1px) and expands into the controls row
   * on `:focus-within`, so a keyboard or screen-reader user still reaches every day in the horizon
   * without a drag. Removing the three buttons removes a duplicate affordance, not an ability: the
   * dial's own drag, tap and marker paths and this range control cover the same state changes. */

  const rangeWrap = document.createElement("div");
  rangeWrap.className = "obs-dial-range-wrap";
  const label = document.createElement("label");
  label.className = "obs-dial-range-label";
  label.setAttribute("for", "obs-dial-range");
  label.textContent = "Explore upcoming dates. Press T to return to today.";
  const range = document.createElement("input");
  range.type = "range";
  range.id = "obs-dial-range";
  range.className = "obs-dial-range";
  range.min = "0";
  range.max = String(state.model.totalDays);
  range.step = "1";
  range.value = String(dayIndexForDate(state.selectedDate, state.model.today));
  range.setAttribute("aria-valuetext", describeSelectedDay(state));
  range.addEventListener("input", () => {
    const day = Number(range.value);
    state.selectedDate = addDays(state.model.today, day);
    state.selectedEventId = null;
    onChange();
  });
  // What the removed "Back to today" button did, kept as a keyboard path because Home/End jump to
  // the horizon's ends rather than to today. Only an event that IS today is re-selected, so the
  // needle's angle and the centre readout still agree, exactly as that button's note required.
  range.addEventListener("keydown", (event) => {
    if (event.key !== "t" && event.key !== "T") return;
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    event.preventDefault();
    state.selectedDate = state.model.today;
    state.mode = "today";
    state.selectedEventId =
      state.model.events.find((entry) => entry.date === state.model.today)?.id || null;
    onChange();
    announce(`Returned to today, ${formatLongDate(state.model.today)}.`);
  });
  rangeWrap.append(label, range);

  controls.append(rangeWrap);
  return controls;
}

function announce(message) {
  let node = document.querySelector("[data-obs-live-region]");
  if (!node) {
    node = document.createElement("p");
    node.className = "obs-visually-hidden";
    node.setAttribute("data-obs-live-region", "");
    node.setAttribute("role", "status");
    document.body.appendChild(node);
  }
  node.textContent = message;
}

function paintSVGSelection(svg, state) {
  if (!svg) return;
  const { today, totalDays } = state.model;
  const pointerNeedle = svg.querySelector(".obs-dial-pointer-needle");
  const pointerTip = svg.querySelector(".obs-dial-pointer-tip");
  const pointerRing = svg.querySelector(".obs-dial-pointer-tip-ring");
  const pointerPupil = svg.querySelector(".obs-dial-pointer-tip-pupil");
  const selectedIndex = dayIndexForDate(state.selectedDate, today);
  const pointerAngle = dayToAngle(selectedIndex, totalDays);
  const needlePoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, POINTER_INNER_UNITS, pointerAngle);
  const tipPoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, POINTER_TIP_UNITS, pointerAngle);
  /* The SAME derivation as the initial render, and this is the copy that actually paints: the pointer
     is re-drawn here on every update, so the owner's screenshot showed this path's output. It carried
     the identical convention bug (`-sin, cos` against a bearing-based `positionOnArc`), which made the
     wedge's three points collinear and its area zero -- a 0.88px hairline instead of a hand. Fixing
     only the first copy left this one painting the defect. */
  const axisX = tipPoint.x - VIEWBOX.cx;
  const axisY = tipPoint.y - VIEWBOX.cy;
  const axisLength = Math.hypot(axisX, axisY) || 1;
  const perpX = (-axisY / axisLength) * POINTER_TIP_HALF_WIDTH;
  const perpY = (axisX / axisLength) * POINTER_TIP_HALF_WIDTH;
  if (pointerNeedle) {
    pointerNeedle.setAttribute(
      "d",
      `M${needlePoint.x.toFixed(2)} ${needlePoint.y.toFixed(2)} ` +
        `L${(tipPoint.x + perpX).toFixed(2)} ${(tipPoint.y + perpY).toFixed(2)} ` +
        `L${(tipPoint.x - perpX).toFixed(2)} ${(tipPoint.y - perpY).toFixed(2)} Z`,
    );
  }
  for (const circle of [pointerTip, pointerRing, pointerPupil]) {
    if (!circle) continue;
    circle.setAttribute("cx", String(tipPoint.x.toFixed(2)));
    circle.setAttribute("cy", String(tipPoint.y.toFixed(2)));
  }
  svg.querySelectorAll(".obs-dial-marker").forEach((marker) => {
    const date = marker.getAttribute("data-date");
    if (date === state.selectedDate) marker.setAttribute("data-selected", "true");
    else marker.removeAttribute("data-selected");
  });
}

function update(state, container, rangeValue) {
  if (!container) return;
  const panel = container.querySelector(".obs-dial-panel");
  if (!panel) return;
  const instrument = panel.querySelector(".obs-dial-instrument");
  const svg = panel.querySelector(".obs-dial-svg");
  if (svg) paintSVGSelection(svg, state);

  const oldOverlay = instrument.querySelector(".obs-dial-overlay");
  const newOverlay = renderInstrumentOverlay(state);
  if (oldOverlay) oldOverlay.replaceWith(newOverlay);

  const oldEvents = panel.querySelector(".obs-dial-events");
  const previousScroll = oldEvents?.scrollTop || 0;
  const newEvents = renderEventList(state, container);
  if (oldEvents) oldEvents.replaceWith(newEvents);
  newEvents.scrollTop = previousScroll;

  const oldTicket = panel.querySelector(".obs-evidence-ticket");
  if (oldTicket) oldTicket.replaceWith(renderEvidenceTicket(state, selectedEventForState(state)));

  const range = panel.querySelector(".obs-dial-range");
  if (range) {
    const day = dayIndexForDate(state.selectedDate, state.model.today);
    range.value = String(day);
    range.setAttribute("aria-valuetext", describeSelectedDay(state));
  }

  // The event rows were just replaced, so their arc seating and the runs that follow them must
  // both be recomputed -- rows first, because a run ends at the row's box.
  placeCalloutRows(state, container);
  renderConnectors(state, container);
  // THE DAY LABELS ARE PART OF THIS UPDATE, and forgetting them here was a real defect rather than a
  // tidy-up. `renderInstrumentOverlay` above REPLACES the labels, and a freshly built label is placed
  // at the pre-measurement SEED inset, `VIEWBOX.r - DAY_LABEL_MAX_INSET_UNITS`; only `placeDayLabels`
  // moves it to the measured radius.
  //
  // Owner, 2026-09-25, reporting it from his phone: "The numbers do move based on event ... Some
  // events move the numbers so that they are hugging the inner rail, and some the opposite." Traced
  // on the shipped build by logging every `placeDayLabels` call while the selection walked the
  // horizon: it never bailed and always measured width 353 / inset ~44 units / radius 140.11px -- and
  // the rendered radius was nevertheless **125.84px**, which is exactly the seed (282 - 68 units at
  // that wrap). No placement call followed the re-render, because this function did not make one, so
  // the whole ring of numbers sat 13.5px inside its proper radius. Which radius you saw depended on
  // whether that selection happened to go through the full `renderDial` path (which does call
  // `redraw`), i.e. on the SELECTION and not on the data -- hence "some events ... and some the
  // opposite".
  placeDayLabels(state, panel.querySelector(".obs-dial-svg-wrap"));

  // Keep the selected row in view, AFTER the arc seating. It used to run where the rail was
  // replaced, which was correct while the rows were a stacked column: their order was their layout,
  // so the box measured there was final. With the rows placed along the dial's arc their positions
  // are only known once `placeCalloutRows` has run, and the earlier measurement was made against
  // rows every one of which still sat at `top: 0` -- so a long horizon left the selected row out of
  // the scrollport. On the phone seating this is also the only path that scrolls the rail at all,
  // because an absolutely placed row is revealed by scrolling the rail vertically.
  const settledRow = newEvents.querySelector('.obs-event-item[data-selected="true"]');
  if (settledRow) {
    const rowBox = settledRow.getBoundingClientRect();
    const railBox = newEvents.getBoundingClientRect();
    if (rowBox.top < railBox.top) newEvents.scrollTop -= railBox.top - rowBox.top;
    else if (rowBox.bottom > railBox.bottom) newEvents.scrollTop += rowBox.bottom - railBox.bottom;
  }

  // Keep the actual control nodes alive: replacing them drops keyboard focus
  // and interrupts native range dragging on every date change.
}

function bindPointerDrag(svg, state, container, totalDays) {
  let pointerState = container.__obsPointerState;
  if (!pointerState) {
    pointerState = { active: false, pointerId: null, lastAngle: 0, accumulatedAngle: 0 };
    container.__obsPointerState = pointerState;
  }

  function pointerData(clientX, clientY) {
    const ctm = svg.getScreenCTM();
    if (!ctm) return { angle: 0, distance: 0 };
    const point = new DOMPoint(clientX, clientY).matrixTransform(ctm.inverse());
    const dx = point.x - VIEWBOX.cx;
    const dy = point.y - VIEWBOX.cy;
    let angle = (Math.atan2(dx, -dy) * 180) / Math.PI;
    if (angle > 180) angle -= 360;
    if (angle < -180) angle += 360;
    return { angle, distance: Math.sqrt(dx * dx + dy * dy) };
  }

  function inTrack(data) {
    // The visible instrument occupies a ring around the arc; avoid starting a
    // drag from the center or far outside the dial.
    return data.distance >= VIEWBOX.r - 46 && data.distance <= VIEWBOX.r + 15;
  }

  let rafId = null;
  function scheduleUpdate() {
    if (rafId !== null) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      update(state, container);
    });
  }
  function cancelScheduledUpdate() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  svg.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 && event.pointerType === "mouse") return;
    const data = pointerData(event.clientX, event.clientY);
    if (!inTrack(data)) return;
    const raw = data.angle;
    const clamped = clamp(raw, ARC_START, ARC_END);
    pointerState.active = true;
    pointerState.pointerId = event.pointerId;
    pointerState.lastAngle = raw;
    pointerState.accumulatedAngle = clamped;
    svg.setPointerCapture?.(event.pointerId);
    event.preventDefault();
    const day = angleToDay(clamped, totalDays);
    state.selectedDate = addDays(state.model.today, day);
    state.mode = "explore";
    update(state, container);
  });

  svg.addEventListener("pointermove", (event) => {
    if (!pointerState.active || event.pointerId !== pointerState.pointerId) return;
    const data = pointerData(event.clientX, event.clientY);
    pointerState.accumulatedAngle = clamp(
      pointerState.accumulatedAngle + shortestAngleDelta(pointerState.lastAngle, data.angle),
      ARC_START,
      ARC_END,
    );
    pointerState.lastAngle = data.angle;
    const day = angleToDay(pointerState.accumulatedAngle, totalDays);
    state.selectedDate = addDays(state.model.today, day);
    state.mode = "explore";
    scheduleUpdate();
  });

  function endPointer(event) {
    if (!pointerState.active || event.pointerId !== pointerState.pointerId) return;
    pointerState.active = false;
    pointerState.pointerId = null;
    if (typeof svg.releasePointerCapture === "function") {
      try {
        svg.releasePointerCapture(event.pointerId);
      } catch (_) {
        /* no-op */
      }
    }
    cancelScheduledUpdate();
    const events = eventsForDate(state, state.selectedDate);
    state.selectedEventId = events.length ? events[0].id : null;
    const eventNames = events.length ? events.map((event) => event.title).join(", ") : "no scheduled events";
    announce(`${formatLongDate(state.selectedDate)}, ${eventNames}.`);
    update(state, container);
  }

  svg.addEventListener("pointerup", endPointer);
  svg.addEventListener("pointercancel", endPointer);
  svg.addEventListener("lostpointercapture", (event) => {
    if (pointerState.active && event.pointerId === pointerState.pointerId) {
      pointerState.active = false;
      pointerState.pointerId = null;
    }
  });
}

export function renderDial(container, inputModel) {
  if (!container) return null;
  const model = normalizeModel(inputModel);
  // The NEAREST upcoming event, so the dial, the centre readout and the evidence ticket all have
  // something to state the moment the page opens. Sorted explicitly: `find` would take whichever
  // event the model happened to list first, which is an ordering coincidence rather than "nearest".
  const upcoming = model.events
    .filter((event) => event.date >= model.today && event.date <= model.horizonEnd)
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  const initialEvent = upcoming[0] || null;
  const state = {
    model,
    // The pointer, the centre readout and the evidence ticket all state the SAME selection, so
    // opening on the nearest event moves the selected DATE to that event as well. Leaving the date
    // at today would point the stylus at today while the centre named a bill a week away.
    selectedDate: initialEvent ? initialEvent.date : model.today,
    selectedEventId: initialEvent ? initialEvent.id : null,
    mode: "today",
    drag: null,
  };

  container.classList.add("obs-dial");
  container.replaceChildren();

  const panel = document.createElement("div");
  panel.className = "obs-dial-panel";

  const instrument = document.createElement("section");
  instrument.className = "obs-dial-instrument";
  instrument.setAttribute("aria-label", "Upcoming date dial");

  const svgWrap = document.createElement("div");
  svgWrap.className = "obs-dial-svg-wrap";
  const art = document.createElement("div");
  art.className = "obs-dial-art obs-art";
  const svg = renderDialSVG(state, container);
  svgWrap.append(art, svg);
  const overlay = renderInstrumentOverlay(state);
  svgWrap.appendChild(overlay);
  const controls = renderControls(state, () => update(state, container));
  instrument.append(svgWrap, renderLegend());
  bindPointerDrag(svg, state, container, model.totalDays);

  const eventsColumn = renderEventList(state, container);
  panel.append(instrument, eventsColumn, controls, renderEvidenceTicket(state, selectedEventForState(state)));
  container.appendChild(panel);

  // Both ends of a run follow live geometry, so recompute when either side resizes. The day
  // labels are anchored from the wrap's MEASURED width, so they need the same treatment: a
  // label inset computed for one dial size would overhang the rim again after a resize
  // (rotating a phone, or any window change), because the labels' own boxes stay a fixed
  // pixel size while the radius grows or shrinks with the wrap.
  const redraw = () => {
    placeCalloutRows(state, container);
    renderConnectors(state, container);
    return placeDayLabels(state, svgWrap);
  };
  // Runs AFTER the panel is in the document, which is the first moment the wrap has a
  // measurable width; the labels were seeded with a conservative inset at build time.
  //
  // A FAILED PLACEMENT IS RETRIED, because leaving it on the seed MOVES THE WHOLE RING OF NUMBERS.
  // Owner, 2026-09-25: "The numbers do move based on event ... Some events move the numbers so that
  // they are hugging the inner rail, and some the opposite." Measured on the shipped build by walking
  // the selection across the horizon: the same dial measured a median label radius of **139.39px**
  // once a placement landed and **125.84px** when none did -- and 125.84 is exactly the seed,
  // `VIEWBOX.r - DAY_LABEL_MAX_INSET_UNITS` = 282 - 68 units at this wrap. So the ring sat 13.5px
  // inside its proper radius depending only on the TIMING of the re-render, not on the data.
  // `placeDayLabels` returns the labels it placed, and an empty array is its signature for "could not
  // measure yet" (the wrap's clientWidth is 0 in that window), so a failed attempt is retried on the
  // next frames rather than being left where the seed put it. Bounded, so a dial that is hidden
  // outright -- the Plan and Accounts workspaces keep Today's section in the DOM -- stops after a few
  // frames and is picked up by the ResizeObserver below when it becomes visible.
  const redrawUntilPlaced = (attempt = 0) => {
    const placed = redraw();
    if (placed && placed.length) return;
    if (attempt >= 5) return;
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(() => redrawUntilPlaced(attempt + 1));
    }
  };
  redrawUntilPlaced();
  const resizeObserver =
    typeof ResizeObserver !== "undefined" ? new ResizeObserver(redraw) : null;
  if (resizeObserver) resizeObserver.observe(panel);
  else window.addEventListener("resize", redraw);

  return function stop() {
    if (resizeObserver) resizeObserver.disconnect();
    else window.removeEventListener("resize", redraw);
    container.replaceChildren();
  };
}

/* Auto-start when the page provides a model:
   - `window.MeridianObservatoryDialModel` for inline/synthetic previews
   - `data-model-url` for a read-only JSON endpoint in a future live workspace
*/
function showUnableToLoad(container) {
  const fallback = window.MeridianObservatoryDialModel;
  if (fallback) {
    renderDial(container, fallback);
  } else {
    container.textContent = "The observatory dial could not be loaded. Nothing was changed.";
  }
}

function autoStart() {
  const container = document.querySelector("[data-observatory-dial]");
  if (!container) return;
  const modelUrl = container.getAttribute("data-model-url");
  if (modelUrl) {
    fetch(modelUrl, { headers: { Accept: "application/json" } })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Dial request failed with status ${response.status}`);
        }
        return response.json();
      })
      .then((model) => renderDial(container, model))
      .catch(() => showUnableToLoad(container));
    return;
  }
  if (window.MeridianObservatoryDialModel) {
    renderDial(container, window.MeridianObservatoryDialModel);
  }
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoStart);
  } else {
    autoStart();
  }
}

/* Pure helpers are exported for unit tests and future integration. */
