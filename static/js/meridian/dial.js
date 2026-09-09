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

const VIEWBOX = { w: 600, h: 600, cx: 300, cy: 300, r: 245 };
const ARC_START = -120;
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
  return new Intl.DateTimeFormat(undefined, { month: "long", day: "numeric" }).format(parsed);
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
  const events = eventsForDate(state, state.selectedDate);
  return events.find((event) => event.id === state.selectedEventId) || events[0] || null;
}

function renderInstrumentOverlay(state) {
  const overlay = document.createElement("div");
  overlay.className = "obs-dial-overlay";
  overlay.setAttribute("aria-hidden", "true");

  // Center: visible event or the available-to-spend figure, matching the
  // concept art's dark sky with real data in the middle.
  const center = document.createElement("div");
  center.className = "obs-dial-center";
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
    kicker.textContent = formatLongDate(selected.date);
    title.textContent = selected.title;
    amount.textContent = minorToDisplay(selected.amount) || "—";
    status.textContent = fundingLabel(selected.fundingStatus);
  } else if (state.model.availableToSpend && state.model.availableToSpend.minor != null) {
    kicker.textContent = "Available to spend";
    title.textContent = "";
    amount.textContent = minorToDisplay(state.model.availableToSpend) || "—";
    status.textContent = "Horizon preview";
  } else {
    kicker.textContent = formatLongDate(state.selectedDate);
    title.textContent = "No event selected";
    amount.textContent = "—";
    status.textContent = "Choose a day to explore";
  }
  center.append(kicker, title, amount, status);
  overlay.appendChild(center);

  // Engraved observatory/lunar art in the lower-left of the instrument, matching
  // the concept's decorative scene without carrying financial meaning.
  const observatory = document.createElement("div");
  observatory.className = "obs-dial-observatory obs-art";
  overlay.appendChild(observatory);


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
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 44, angle);
    const span = document.createElement("span");
    span.className = "obs-dial-day-label";
    if (date === state.model.today) span.classList.add("is-today");
    if (date === state.selectedDate) span.classList.add("is-selected");
    const parsed = parseDateKey(date);
    const dayNumber = parsed ? String(parsed.getDate()) : "";
    const weekday = parsed
      ? new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(parsed).replace(".", "")
      : "";
    span.textContent = `${dayNumber} ${weekday}`;
    span.style.left = `${((point.x / VIEWBOX.w) * 100).toFixed(2)}%`;
    span.style.top = `${((point.y / VIEWBOX.h) * 100).toFixed(2)}%`;
    labels.appendChild(span);
  }
  overlay.appendChild(labels);

  // Quiet directional copy from the concept.
  const topCaption = document.createElement("p");
  topCaption.className = "obs-dial-caption obs-dial-caption--top";
  topCaption.textContent = "Days to payday";
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

function kindCode(kind) {
  const codes = { bill: "⚡", income: "✦", goal: "◎", transfer: "⇄" };
  return codes[kind] || "•";
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

  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  const radial = document.createElementNS("http://www.w3.org/2000/svg", "radialGradient");
  radial.setAttribute("id", "obsDialGlow");
  const stop1 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
  stop1.setAttribute("offset", "0%");
  stop1.setAttribute("stop-color", "#c1a9e2");
  stop1.setAttribute("stop-opacity", "0.18");
  const stop2 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
  stop2.setAttribute("offset", "100%");
  stop2.setAttribute("stop-color", "#c1a9e2");
  stop2.setAttribute("stop-opacity", "0");
  radial.append(stop1, stop2);
  defs.appendChild(radial);

  const paper = document.createElementNS("http://www.w3.org/2000/svg", "radialGradient");
  paper.setAttribute("id", "obsDialPaper");
  const paperStop1 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
  paperStop1.setAttribute("offset", "0%");
  paperStop1.setAttribute("stop-color", "#ead8b5");
  const paperStop2 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
  paperStop2.setAttribute("offset", "78%");
  paperStop2.setAttribute("stop-color", "#dfc69c");
  const paperStop3 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
  paperStop3.setAttribute("offset", "100%");
  paperStop3.setAttribute("stop-color", "#c9a97a");
  paper.append(paperStop1, paperStop2, paperStop3);
  defs.appendChild(paper);

  svg.appendChild(defs);

  const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  glow.setAttribute("cx", String(VIEWBOX.cx));
  glow.setAttribute("cy", String(VIEWBOX.cy));
  glow.setAttribute("r", String(VIEWBOX.r + 14));
  glow.setAttribute("fill", "url(#obsDialGlow)");
  svg.appendChild(glow);

  // Parchment instrument face: a full circle behind the active horizon arc so
  // the dial reads as the engraved observatory instrument in the concept art.
  const face = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  face.setAttribute("cx", String(VIEWBOX.cx));
  face.setAttribute("cy", String(VIEWBOX.cy));
  face.setAttribute("r", String(VIEWBOX.r - 4));
  face.setAttribute("class", "obs-dial-face");
  svg.appendChild(face);

  const rim = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  rim.setAttribute("cx", String(VIEWBOX.cx));
  rim.setAttribute("cy", String(VIEWBOX.cy));
  rim.setAttribute("r", String(VIEWBOX.r - 28));
  rim.setAttribute("class", "obs-dial-rim");
  svg.appendChild(rim);

  const disk = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  disk.setAttribute("cx", String(VIEWBOX.cx));
  disk.setAttribute("cy", String(VIEWBOX.cy));
  disk.setAttribute("r", String(VIEWBOX.r - 96));
  disk.setAttribute("class", "obs-dial-disk");
  svg.appendChild(disk);

  // Starfield inside the dark sky, fixed deterministic positions (decorative).
  const stars = document.createElementNS("http://www.w3.org/2000/svg", "g");
  stars.setAttribute("class", "obs-dial-stars");
  const starPositions = [
    [300, 190], [348, 175], [260, 180], [390, 230], [230, 240],
    [370, 290], [255, 300], [420, 320], [200, 330], [340, 360],
    [270, 370], [300, 250],
  ];
  for (const [sx, sy] of starPositions) {
    const star = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    star.setAttribute("cx", String(sx));
    star.setAttribute("cy", String(sy));
    star.setAttribute("r", "1.2");
    stars.appendChild(star);
  }
  svg.appendChild(stars);


  // Brass rivets around the parchment ring, purely decorative.
  const rivets = document.createElementNS("http://www.w3.org/2000/svg", "g");
  rivets.setAttribute("class", "obs-dial-rivets");
  for (let i = 0; i < 8; i += 1) {
    const angle = -180 + i * 45;
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 14, angle);
    const rivet = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    rivet.setAttribute("cx", String(point.x.toFixed(2)));
    rivet.setAttribute("cy", String(point.y.toFixed(2)));
    rivet.setAttribute("r", "4");
    rivets.appendChild(rivet);
  }
  svg.appendChild(rivets);


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
  hit.setAttribute("r", String(VIEWBOX.r + 24));
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
    const point = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 34, angle);
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
    circle.setAttribute("fill", "rgba(32,43,64,0.94)");
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
  const pointerPoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 4, pointerAngle);
  const pointerGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  pointerGroup.setAttribute("class", "obs-dial-pointer");
  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("class", "obs-dial-pointer-line");
  line.setAttribute("x1", String(VIEWBOX.cx));
  line.setAttribute("y1", String(VIEWBOX.cy));
  line.setAttribute("x2", String(pointerPoint.x.toFixed(2)));
  line.setAttribute("y2", String(pointerPoint.y.toFixed(2)));
  const tip = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  tip.setAttribute("class", "obs-dial-pointer-tip");
  tip.setAttribute("cx", String(pointerPoint.x.toFixed(2)));
  tip.setAttribute("cy", String(pointerPoint.y.toFixed(2)));
  tip.setAttribute("r", "6");
  const centerStarPoints = [];
  for (let i = 0; i < 10; i += 1) {
    const starAngle = ((-90 + i * 36) * Math.PI) / 180;
    const starRadius = i % 2 === 0 ? 13 : 5.5;
    centerStarPoints.push(
      `${(VIEWBOX.cx + starRadius * Math.cos(starAngle)).toFixed(2)},${
        (VIEWBOX.cy + starRadius * Math.sin(starAngle)).toFixed(2)
      }`
    );
  }
  const centerStar = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  centerStar.setAttribute("class", "obs-dial-pointer-star");
  centerStar.setAttribute("points", centerStarPoints.join(" "));
  pointerGroup.append(centerStar, line, tip);
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
    return `${event.title}, ${amount || "amount unavailable"}, ${fundingLabel(event.fundingStatus)}`;
  });
  return `${dateText}, ${parts.join("; ")}`;
}

function renderEventList(state, container) {
  const wrap = document.createElement("div");
  wrap.className = "obs-dial-events";

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
    list.className = "obs-event-list";
    for (const event of upcoming) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "obs-event-item";
      button.dataset.kind = event.kind;
      if (event.id === state.selectedEventId) button.setAttribute("data-selected", "true");
      const kind = document.createElement("span");
      kind.className = "obs-event-kind";
      kind.textContent = kindCode(event.kind);
      const body = document.createElement("span");
      body.className = "obs-event-body";
      const date = document.createElement("span");
      date.className = "obs-event-date";
      date.textContent = formatShortDay(event.date);
      const title = document.createElement("span");
      title.className = "obs-event-title";
      title.textContent = event.title;
      const meta = document.createElement("span");
      meta.className = "obs-event-meta";
      meta.textContent = `${fundingLabel(event.fundingStatus)} · ${event.source}`;
      body.append(date, title, meta);
      const amount = document.createElement("strong");
      amount.className = "obs-event-amount";
      amount.dataset.direction = event.kind === "income" ? "incoming" : "outgoing";
      const displayAmount = minorToDisplay(event.amount);
      amount.textContent = displayAmount ? (event.kind === "income" ? `+${displayAmount}` : `−${displayAmount}`) : "—";
      button.append(kind, body, amount);
      button.addEventListener("click", () => {
        state.selectedEventId = event.id;
        state.selectedDate = event.date;
        state.mode = "explore";
        update(state, container);
        announce(`Selected ${event.title} on ${formatShortDay(event.date)}.`);
      });
      item.appendChild(button);
      list.appendChild(item);
    }
    wrap.appendChild(list);
  }

  // Selected evidence ticket.
  const selectedEvent = upcoming.find((event) => event.id === state.selectedEventId) || null;
  wrap.appendChild(renderEvidenceTicket(state, selectedEvent || null));
  return wrap;
}

function renderEvidenceTicket(state, event) {
  const ticket = document.createElement("article");
  ticket.className = "obs-panel obs-panel--paper obs-evidence-ticket";
  if (!event) {
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
  const amount = document.createElement("strong");
  amount.className = "obs-amount obs-amount--hero";
  const displayAmount = minorToDisplay(event.amount);
  amount.textContent = displayAmount || "—";
  header.append(headerText, amount);

  const rows = document.createElement("dl");
  rows.className = "obs-ticket-rows";
  const rowData = [
    ["Due", formatLongDate(event.date)],
    ["Funding", fundingLabel(event.fundingStatus)],
    ["Source", event.source],
  ];
  if (event.reserved && event.reserved.minor != null) {
    rowData.push(["Reserved", minorToDisplay(event.reserved)]);
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
    body.push(noEvidence);
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
    const todayEvents = eventsForDate(state, state.model.today);
    state.selectedEventId = todayEvents.length ? todayEvents[0].id : null;
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
  const pointerPoint = positionOnArc(VIEWBOX.cx, VIEWBOX.cy, VIEWBOX.r - 4, pointerAngle);
  if (pointerLine) {
    pointerLine.setAttribute("x1", String(VIEWBOX.cx));
    pointerLine.setAttribute("y1", String(VIEWBOX.cy));
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
  const newEvents = renderEventList(state, container);
  if (oldEvents) oldEvents.replaceWith(newEvents);

  const range = panel.querySelector(".obs-dial-range");
  if (range) {
    const day = dayIndexForDate(state.selectedDate, state.model.today);
    range.value = String(day);
    range.setAttribute("aria-valuetext", describeSelectedDay(state));
  }

  const oldInstrumentEvents = instrument.querySelector(".obs-dial-controls");
  const newControls = renderControls(state, () => update(state, container, rangeValue));
  if (oldInstrumentEvents) oldInstrumentEvents.replaceWith(newControls);
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
    return data.distance >= VIEWBOX.r - 46 && data.distance <= VIEWBOX.r + 30;
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
  const todayEvents = eventsForDate({ model }, model.today);
  const state = {
    model,
    selectedDate: model.today,
    selectedEventId: todayEvents.length ? todayEvents[0].id : null,
    mode: "today",
    drag: null,
  };

  container.classList.add("obs-dial");
  container.replaceChildren();

  const panel = document.createElement("div");
  panel.className = "obs-dial-panel";

  const instrument = document.createElement("section");
  instrument.className = "obs-panel obs-dial-instrument";
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
  svgWrap.appendChild(controls);
  instrument.append(svgWrap, renderLegend());
  bindPointerDrag(svg, state, container, model.totalDays);

  const eventsColumn = document.createElement("aside");
  eventsColumn.className = "obs-dial-events";
  const eventsContent = renderEventList(state, container);
  eventsColumn.appendChild(eventsContent);

  panel.append(instrument, eventsColumn);
  container.appendChild(panel);

  return function stop() {
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
