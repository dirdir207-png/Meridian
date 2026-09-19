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

   `ARC_END` is unchanged, so the sweep narrows 240deg -> 220deg and the visible arc stops
   short of the roofline too. */
const ARC_START = -100;
const ARC_END = 120;
const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

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
    source: event.source || "crew",
    observedAt: event.observedAt || null,
    evidenceIds: Array.isArray(event.evidenceIds) ? event.evidenceIds : [],
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
  const selected = state.mode === "today" ? null : selectedEventForState(state);
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
    // The observed source names the bill's funder; the reservation amount stays a
    // separate question, so the status word is only shown while no source is known.
    status.textContent = fundingSourceSummary(selected) || fundingLabel(selected.fundingStatus);
  } else if (state.model.availableToSpend && state.model.availableToSpend.minor != null) {
    kicker.textContent = "Safe to spend";
    title.textContent = "";
    amount.textContent = minorToDisplay(state.model.availableToSpend) || "—";
    status.textContent = `Available until ${formatShortDay(state.model.horizonEnd)}`;
  } else {
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
  for (let day = 0; day <= state.model.totalDays; day += 1) {
    const date = addDays(state.model.today, day);
    if (!date || !specialDates.has(date)) {
      continue;
    }
    const angle = dayToAngle(day, state.model.totalDays);
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 22, angle);
    const span = document.createElement("span");
    span.className = "obs-dial-day-label";
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
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 84, angle);
    const leaderStart = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 90, angle);
    const leaderEnd = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 73, angle);
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
    circle.setAttribute("r", dayEvents.length > 1 ? "15" : "7");
    circle.setAttribute("fill", "currentColor");
    marker.appendChild(circle);
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
  const pointerPoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 84, pointerAngle);
  const pointerGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  pointerGroup.setAttribute("class", "obs-dial-pointer");
  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("class", "obs-dial-pointer-line");
  const pointerStart = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, 118, pointerAngle);
  line.setAttribute("x1", String(pointerStart.x.toFixed(2)));
  line.setAttribute("y1", String(pointerStart.y.toFixed(2)));
  line.setAttribute("x2", String(pointerPoint.x.toFixed(2)));
  line.setAttribute("y2", String(pointerPoint.y.toFixed(2)));
  const tip = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  tip.setAttribute("class", "obs-dial-pointer-tip");
  tip.setAttribute("cx", String(pointerPoint.x.toFixed(2)));
  tip.setAttribute("cy", String(pointerPoint.y.toFixed(2)));
  tip.setAttribute("r", "6");
  pointerGroup.append(line, tip);
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
    const funding = fundingSourceSummary(event) || fundingLabel(event.fundingStatus);
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
        // An observed funding source is a stronger statement than "unknown", and it
        // is a different statement: this row names the funder, the evidence ticket
        // still reports the reservation status beside it.
        meta.textContent = fundingSourceSummary(event) || fundingLabel(event.fundingStatus);
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
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 84, angle);
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
  ticket.className = "obs-panel obs-panel--paper obs-evidence-ticket";
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
  const rowData = [
    ["Amount", displayAmount || "—"],
  ];
  const sourceValue = fundingSourceValue(event);
  if (sourceValue) {
    // Identity first, then what is still unresolved about the money.
    rowData.push(["Funding source", sourceValue]);
  }
  if (event.reserved && event.reserved.minor != null) {
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

  const body = [header, rows];
  if (event.fundingStatus === "unfunded" || event.fundingStatus === "partial") {
    const shortfall = document.createElement("p");
    shortfall.className = "obs-shortfall";
    const amountMinor = event.amount.minor || 0;
    const reservedMinor = event.reserved && event.reserved.minor != null ? event.reserved.minor : 0;
    const remainingMinor = Math.max(0, amountMinor - reservedMinor);
    const strong = document.createElement("strong");
    strong.textContent = minorToDisplay({ minor: remainingMinor, currency: event.amount.currency }) || "—";
    shortfall.append("Exact shortfall: ", strong, " remains unfunded.");
    body.push(shortfall);
  }

  const actions = document.createElement("div");
  actions.className = "obs-ticket-actions";
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
  } else {
    const noEvidence = document.createElement("p");
    noEvidence.className = "obs-ticket-detail";
    noEvidence.textContent = "No evidence is attached to this event.";
    actions.appendChild(noEvidence);
  }
  if (event.detailHref) {
    const detail = document.createElement("a");
    detail.className = "obs-button";
    detail.href = event.detailHref;
    detail.textContent = event.kind === "bill" ? "View bill" : "View detail";
    actions.appendChild(detail);
  }
  body.push(actions);
  ticket.append(...body);
  return ticket;
}

function renderControls(state, onChange) {
  const controls = document.createElement("div");
  controls.className = "obs-dial-controls";

  const prev = document.createElement("button");
  prev.type = "button";
  prev.className = "obs-control";
  prev.textContent = "Previous day";
  prev.setAttribute("aria-label", "Previous day");
  prev.addEventListener("click", () => {
    const next = addDays(state.selectedDate, -1);
    if (next && next >= state.model.today) {
      state.selectedDate = next;
      state.selectedEventId = null;
      onChange();
    }
  });

  const next = document.createElement("button");
  next.type = "button";
  next.className = "obs-control";
  next.textContent = "Next day";
  next.setAttribute("aria-label", "Next day");
  next.addEventListener("click", () => {
    const nextDate = addDays(state.selectedDate, 1);
    if (nextDate && nextDate <= state.model.horizonEnd) {
      state.selectedDate = nextDate;
      state.selectedEventId = null;
      onChange();
    }
  });

  const back = document.createElement("button");
  back.type = "button";
  back.className = "obs-control";
  back.textContent = "Back to today";
  back.addEventListener("click", () => {
    state.selectedDate = state.model.today;
    state.mode = "today";
    state.selectedEventId = state.model.events.find(
      (event) => event.date >= state.model.today && event.date <= state.model.horizonEnd,
    )?.id || null;
    onChange();
  });

  const rangeWrap = document.createElement("div");
  rangeWrap.className = "obs-dial-range-wrap";
  const label = document.createElement("label");
  label.className = "obs-dial-range-label";
  label.setAttribute("for", "obs-dial-range");
  label.textContent = "Explore upcoming dates";
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
  rangeWrap.append(label, range);

  controls.append(prev, rangeWrap, next, back);
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
  const pointerLine = svg.querySelector(".obs-dial-pointer-line");
  const pointerTip = svg.querySelector(".obs-dial-pointer-tip");
  const selectedIndex = dayIndexForDate(state.selectedDate, today);
  const pointerAngle = dayToAngle(selectedIndex, totalDays);
  const pointerPoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 84, pointerAngle);
  if (pointerLine) {
    const pointerStart = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, 118, pointerAngle);
    pointerLine.setAttribute("x1", String(pointerStart.x.toFixed(2)));
    pointerLine.setAttribute("y1", String(pointerStart.y.toFixed(2)));
    pointerLine.setAttribute("x2", String(pointerPoint.x.toFixed(2)));
    pointerLine.setAttribute("y2", String(pointerPoint.y.toFixed(2)));
  }
  if (pointerTip) {
    pointerTip.setAttribute("cx", String(pointerPoint.x.toFixed(2)));
    pointerTip.setAttribute("cy", String(pointerPoint.y.toFixed(2)));
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
  const selectedRow = newEvents.querySelector('.obs-event-item[data-selected="true"]');
  if (selectedRow) {
    const rowBox = selectedRow.getBoundingClientRect();
    const railBox = newEvents.getBoundingClientRect();
    if (rowBox.top < railBox.top) newEvents.scrollTop -= railBox.top - rowBox.top;
    else if (rowBox.bottom > railBox.bottom) newEvents.scrollTop += rowBox.bottom - railBox.bottom;
  }

  const oldTicket = panel.querySelector(".obs-evidence-ticket");
  if (oldTicket) oldTicket.replaceWith(renderEvidenceTicket(state, selectedEventForState(state)));

  const range = panel.querySelector(".obs-dial-range");
  if (range) {
    const day = dayIndexForDate(state.selectedDate, state.model.today);
    range.value = String(day);
    range.setAttribute("aria-valuetext", describeSelectedDay(state));
  }

  // The event rows were just replaced, so the runs must be re-anchored to the new boxes.
  renderConnectors(state, container);

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
  const initialEvent = model.events.find(
    (event) => event.date >= model.today && event.date <= model.horizonEnd,
  ) || null;
  const state = {
    model,
    selectedDate: model.today,
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

  // Both ends of a run follow live geometry, so recompute when either side resizes.
  renderConnectors(state, container);
  const redrawConnectors = () => renderConnectors(state, container);
  const resizeObserver =
    typeof ResizeObserver !== "undefined" ? new ResizeObserver(redrawConnectors) : null;
  if (resizeObserver) resizeObserver.observe(panel);
  else window.addEventListener("resize", redrawConnectors);

  return function stop() {
    if (resizeObserver) resizeObserver.disconnect();
    else window.removeEventListener("resize", redrawConnectors);
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
