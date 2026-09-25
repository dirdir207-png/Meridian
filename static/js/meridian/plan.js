/* Plan workspace: summary-first view model rendering, the shared-rule
   inspector, and the funding-rule editor whose only write path is an
   approval-gated proposal. */

import { MeridianApiError, meridianFetch, meridianPropose, meridianMutate } from "./api.js";
import { describeAbsentBill } from "./absent-bills.js";
import { describeActionOutcome } from "./action-outcome.js";
import { formatCurrency, parseLocalDate } from "./format.js";
import { ACTION_ICONS, kitIconUrl } from "./kit-icons.js";
import { allocationIcon, allocationMark } from "./plan-map-marks.js";
import { ruleStatement, rulePurposeLabel } from "./rule-statement.js";

let controller = null;

/* Latest plan payload + selected rule, kept so delegated interactions (row
   click → inspector, edit schedule) can reach the data without re-fetching. */
let currentPlan = null;
let currentRulesById = new Map();

const TYPE_LABELS = {
  bill: "Bill",
  goal: "Goal",
  reserve: "Reserve",
  buffer: "Buffer",
  debt: "Debt",
};

// R33: subtle bill-attention badges shown on the existing Plan card.
const BILLER_STATUS_LABELS = {
  unfunded: "Underfunded",
  due_soon: "Due soon",
  changed: "Amount changed",
};

/* The collapsed row's medallion glyph, chosen from the commitment's TYPE -- a field the
   payload really carries. It is deliberately NOT a category: a commitment has no category
   and no tint (OS-088 owns that, and it is blocked on the missing data), so the disc keeps
   the neutral tint class and this table never invents a colour by matching the bill's NAME.
   A name match that is wrong about money is worse than no icon, so an unknown type falls
   back to the kit's own question glyph rather than a confident-looking one. */
const COMMITMENT_TYPE_ICONS = {
  bill: "receipt",
  goal: "flag",
  reserve: "piggy-bank",
  buffer: "shield-check",
  debt: "bar-chart",
};

function money(value, currency = "USD") {
  return value === null || value === undefined ? "—" : formatCurrency(value, currency);
}

/* Whole-dollar figure used for the prominent atlas-style sums. */
function moneyWhole(value, currency = "USD") {
  if (value === null || value === undefined) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function isMobileViewport() {
  return window.matchMedia("(max-width: 900px)").matches;
}

function formatShortDate(value) {
  const parsed = parseLocalDate(value);
  if (!parsed) {
    return "—";
  }
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatLongDate(value) {
  const parsed = parseLocalDate(value);
  if (!parsed) {
    return "—";
  }
  return parsed.toLocaleDateString(undefined, { month: "long", day: "numeric" });
}

/* ---------- Command + coverage ---------- */

function renderSummary(root, plan) {
  // Machine-readable headline (kept for assistive tech + tests).
  root.querySelector("[data-plan-headline]").textContent = plan.summary.headline;
}

function renderCoverage(root, plan) {
  const ratio = Math.max(0, Math.min(1, plan.summary.coverage_ratio || 0));
  const percent = Math.round(ratio * 100);

  const month = new Date().toLocaleDateString(undefined, { month: "long" });
  root.querySelector("[data-coverage-label]").textContent = `${month} coverage`;

  // Coverage orbit (donut ring) with an accessible numeric alternative.
  const R = 52;
  const circumference = 2 * Math.PI * R;
  const fill = root.querySelector("[data-coverage-fill]");
  fill.style.strokeDasharray = `${circumference}`;
  fill.style.strokeDashoffset = `${circumference * (1 - ratio)}`;
  root.querySelector("[data-coverage-text]").textContent = `${percent}%`;

  const orbit = root.querySelector("[data-coverage-orbit]");
  if (orbit) {
    const funded = moneyWhole(plan.summary.total_funded);
    const target = moneyWhole(plan.summary.total_target);
    orbit.setAttribute(
      "aria-label",
      `${percent}% funded — ${funded} of ${target} total funded`
    );
  }

  root.querySelector("[data-coverage-detail]").textContent =
    `${moneyWhole(plan.summary.total_funded)} of ${moneyWhole(plan.summary.total_target)} funded`;
  root.querySelector("[data-coverage-projection]").textContent =
    coverageProjection(plan);

  root.querySelector("[data-plan-total]").textContent = money(plan.summary.total_target);
  root.querySelector("[data-plan-funded]").textContent = money(plan.summary.total_funded);
  root.querySelector("[data-plan-unfunded]").textContent = money(plan.summary.unfunded);
  root.querySelector("[data-plan-next-due]").textContent = formatShortDate(plan.summary.next_due);

  const shortfall = root.querySelector("[data-plan-shortfall]");
  const first = plan.summary.first_shortfall;
  if (first) {
    shortfall.hidden = false;
    shortfall.textContent = `Shortfall: ${formatShortDate(first.date)} — ${money(first.amount)} (${first.cause})`;
  } else {
    shortfall.hidden = true;
    shortfall.textContent = "";
  }
}

function coverageProjection(plan) {
  const unfunded = plan.summary.unfunded || 0;
  if (unfunded <= 0) {
    return "Fully funded.";
  }
  const events = plan.timeline?.events || [];
  if (!events.length) {
    return "No projected funding yet.";
  }
  let accumulated = 0;
  for (const event of events) {
    accumulated += event.amount || 0;
    if (accumulated >= unfunded) {
      return `Projected complete by ${formatShortDate(event.date)}`;
    }
  }
  return "Not fully funded in the next 30 days.";
}

/* ---------- Next paycheck ---------- */

function nextPaycheck(plan) {
  const events = plan.timeline?.events || [];
  if (!events.length) {
    return null;
  }
  const sorted = [...events].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  const date = sorted[0].date;
  const amount = sorted
    .filter((event) => event.date === date)
    .reduce((sum, event) => sum + (event.amount || 0), 0);
  return { date, amount };
}

function renderFundingCard(root, plan, activeRuleCount) {
  // Prefer the explicit next_paycheck field (surfaced from the paycheck config
  // even when no funding rules produce timeline events); fall back to the first
  // timeline funding event.
  const next = plan.next_paycheck || nextPaycheck(plan);
  root.querySelector("[data-next-paycheck-date]").textContent = next
    ? formatLongDate(next.date)
    : "—";
  root.querySelector("[data-next-paycheck-amount]").textContent = next
    ? moneyWhole(next.amount)
    : "—";

  const available =
    plan.allocation?.segments?.find((segment) => segment.label === "Available")?.amount ||
    0;
  const caption = root.querySelector("[data-funding-caption]");
  if (next) {
    if (activeRuleCount > 0) {
      // The second clause IS the figure OS-111 unified with Today's Safe to Spend, so it may not
      // be floored: `Math.max(0, available)` printed "$0 remains flexible" beside a medallion
      // showing a negative -- the prose contradicting the map. The negative branch says what a
      // negative Available means, i.e. more is set aside than exists, rather than calling a
      // shortfall "flexible". Wording chosen by the owner, 2026-09-25. The verb pluralises with
      // the noun, which the original did not ("1 rule allocate ...").
      caption.textContent =
        `${activeRuleCount} rule${activeRuleCount === 1 ? "" : "s"} ` +
        `allocate${activeRuleCount === 1 ? "s" : ""} ${moneyWhole(next.amount)}; ` +
        (available < 0
          ? `nothing remains flexible — ${moneyWhole(-available)} more is set aside than you have.`
          : `${moneyWhole(available)} remains flexible.`);
    } else {
      caption.textContent = `${moneyWhole(next.amount)} expected ${formatLongDate(next.date)}; no funding rules yet.`;
    }
  } else {
    caption.textContent = "No funding scheduled yet.";
  }
}

/* ---------- Allocation + timeline ---------- */

/* Stations on the kit's folded map. These are composition, not data: the art carries
   no money and no labels, and its constellations encode nothing, so a medallion's
   place is fixed by the concept and only its label and amount come from the plan.
   "Available" always takes the lower hub, because that is the station the concept
   reserves for the money that is left over; the other segments take left then right
   in the order the service returns them, and any further segment reuses the last
   station rather than inventing a position the concept does not define. */
const ALLOCATION_STATIONS = {
  hub: { left: 50, top: 24 },
  left: { left: 24, top: 38, modifier: "is-left" },
  right: { left: 76, top: 38, modifier: "is-right" },
  available: { left: 50, top: 74, modifier: "is-available" },
  extra: { left: 50, top: 88, modifier: "is-extra" },
};

/* The station-to-mark mapping lives in ./plan-map-marks.js so a Node round-trip can exercise
   every label case. It moved there on 2026-09-24 after a real regression: a broad /commit/
   test in this file gave the Bills station's rotunda to "Unfunded commitments" as well. Keep
   the mapping out of this file, or the only possible guard is a text match that cannot see
   two labels resolving to the same mark. */

function renderAllocation(root, plan) {
  const host = root.querySelector("[data-allocation-medallions]");
  const links = root.querySelector("[data-allocation-links]");
  if (!host) return;
  host.replaceChildren();
  if (links) links.replaceChildren();

  const segments = plan.allocation?.segments || [];
  let side = 0;
  for (const segment of segments) {
    let station;
    if (/available/i.test(segment.label)) {
      station = ALLOCATION_STATIONS.available;
    } else if (side === 0) {
      station = ALLOCATION_STATIONS.left;
      side = 1;
    } else if (side === 1) {
      station = ALLOCATION_STATIONS.right;
      side = 2;
    } else {
      station = ALLOCATION_STATIONS.extra;
    }

    if (links) {
      const rule = document.createElementNS("http://www.w3.org/2000/svg", "line");
      rule.setAttribute("x1", String(station.left));
      rule.setAttribute("y1", String(station.top));
      rule.setAttribute("x2", String(ALLOCATION_STATIONS.hub.left));
      rule.setAttribute("y2", String(ALLOCATION_STATIONS.hub.top));
      links.appendChild(rule);
    }

    const medallion = document.createElement("article");
    medallion.className = `m-plan-medallion ${station.modifier}`;
    medallion.style.left = `${station.left}%`;
    medallion.style.top = `${station.top}%`;
    medallion.dataset.segment = segment.label;

    const disk = document.createElement("span");
    disk.className = "m-plan-medallion-disk";
    disk.setAttribute("aria-hidden", "true");
    /* A generated mark is used as a background IMAGE, never as a mask: masking it to a single
       brass token would flatten exactly the raised highlight and shadow the owner asked for, and
       the asset already carries its own metal. The kit fallback stays a CSS mask, not an <img>,
       because inside an image an external SVG's currentColor resolves to black and would vanish
       on the navy medallion. */
    const glyph = document.createElement("span");
    const mark = allocationMark(segment.label);
    if (mark) {
      glyph.className = `m-plan-medallion-mark is-${mark}`;
      glyph.style.setProperty(
        "--m-mark",
        `url("/static/img/meridian/observatory/plan-map-${mark}.png")`
      );
    } else {
      glyph.className = "m-plan-medallion-glyph";
      glyph.style.setProperty(
        "--m-medallion-icon",
        `url("/static/img/meridian/observatory/kit-2026-09-16/icons/${allocationIcon(segment.label)}.svg")`
      );
    }
    disk.appendChild(glyph);

    const label = document.createElement("span");
    label.className = "m-plan-medallion-label";
    label.textContent = segment.label;
    const amount = document.createElement("strong");
    amount.className = "m-plan-medallion-amount";
    amount.textContent = money(segment.amount);

    medallion.append(disk, label, amount);
    host.appendChild(medallion);
  }

  // The map's own compass rose: a decorative north point, never a money label.
  const hub = document.createElement("span");
  hub.className = "m-plan-map-hub";
  hub.setAttribute("aria-hidden", "true");
  hub.style.left = `${ALLOCATION_STATIONS.hub.left}%`;
  hub.style.top = `${ALLOCATION_STATIONS.hub.top}%`;
  /* The hub is NOT the same mark as Available after all. A full-resolution read of 02-plan.png
     shows the top medallion as a compass with its own medium-thick solid bezel carrying rivet
     knobs at north and south, while the bottom one is smaller with shorter points and a thinner
     rim. Reusing one asset for both was the error the owner caught ("the top star is different
     than the bottom one"), so the hub gets its own generated medallion and Available keeps the
     star rose. */
  const rose = document.createElement("span");
  rose.className = "m-plan-map-hub-mark";
  rose.style.setProperty(
    "--m-mark",
    'url("/static/img/meridian/observatory/plan-map-hub-compass.png")'
  );
  hub.appendChild(rose);
  host.appendChild(hub);
}

function renderTimeline(root, plan) {
  const list = root.querySelector("[data-timeline]");
  const empty = root.querySelector("[data-timeline-empty]");
  list.replaceChildren();
  const events = plan.timeline.events || [];
  empty.hidden = events.length > 0;
  for (const event of events.slice(0, 12)) {
    const row = document.createElement("li");
    const label = document.createElement("span");
    label.textContent = `${formatShortDate(event.date)} · ${event.commitment}`;
    const amount = document.createElement("span");
    amount.className = "m-timeline-amount";
    amount.textContent = money(event.amount);
    row.append(label, amount);
    list.appendChild(row);
  }
}

/* ---------- Read-only Plan scenario preview ---------- */

let scenarioTimer = null;

function scenarioPayload(root) {
  const payload = {};
  root.querySelectorAll("[data-scenario-input]").forEach((input) => {
    const value = input.value.trim();
    if (value === "") {
      return;
    }
    const raw = input.dataset.scenarioInput === "due_date_days"
      ? Number.parseInt(value, 10)
      : Number(value);
    if (Number.isFinite(raw)) {
      payload[input.dataset.scenarioInput] = raw;
    }
  });
  return payload;
}

function scenarioDelta(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  if (value > 0) {
    return `+${money(value)}`;
  }
  return money(value);
}

function scenarioDeltaDays(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  if (value > 0) {
    return `+${value}`;
  }
  return String(value);
}

function addScenarioCompareRow(compare, label, baseValue, scenarioValue, delta) {
  const dt = document.createElement("dt");
  dt.textContent = label;
  const dd = document.createElement("dd");
  dd.textContent = `${money(baseValue)} → ${money(scenarioValue)} (${scenarioDelta(delta)})`;
  compare.append(dt, dd);
}

function runScenarioPreview(root) {
  const results = root.querySelector("[data-scenario-results]");
  const compare = root.querySelector("[data-scenario-compare]");
  const empty = root.querySelector("[data-scenario-empty]");
  const assumptions = root.querySelector("[data-scenario-assumptions]");
  if (!results || !compare) {
    return;
  }
  results.setAttribute("aria-busy", "true");
  (async () => {
    try {
      const response = await fetch("/api/meridian/plan/scenario", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify(scenarioPayload(root)),
      });
      if (!response.ok) {
        throw new MeridianApiError({
          code: "preview_rejected",
          message: "The scenario preview could not be loaded.",
          recoveryAction: "Try again or refresh Plan.",
          status: response.status,
        });
      }
      const data = await response.json();
      if (!data.available) {
        empty.hidden = false;
        empty.textContent = data.reason || "Projection unavailable.";
        compare.replaceChildren();
        assumptions.textContent = "";
        return;
      }
      empty.hidden = true;
      compare.replaceChildren();
      if (data.base && data.scenario) {
        addScenarioCompareRow(
          compare,
          "Starting cash",
          data.base.starting_cash,
          data.scenario.starting_cash,
          data.comparison.starting_cash
        );
        addScenarioCompareRow(
          compare,
          "Daily expense",
          data.base.daily_expense,
          data.scenario.daily_expense,
          data.comparison.daily_expense
        );
      }
      // Runway needs a day-specific delta helper; low point is optional.
      const runwayBase = data.base?.runway_days;
      const runwayScenario = data.scenario?.runway_days;
      if (runwayBase !== null && runwayBase !== undefined && runwayScenario !== null && runwayScenario !== undefined) {
        const delta = runwayScenario - runwayBase;
        const dt = document.createElement("dt");
        dt.textContent = "Runway";
        const dd = document.createElement("dd");
        dd.textContent = `${runwayBase} → ${runwayScenario} days (${scenarioDeltaDays(delta)})`;
        compare.append(dt, dd);
      }
      if (data.base?.low_point !== null && data.base?.low_point !== undefined && data.scenario?.low_point !== null && data.scenario?.low_point !== undefined) {
        addScenarioCompareRow(
          compare,
          "Low point",
          data.base.low_point,
          data.scenario.low_point,
          data.comparison.low_point
        );
      }
      assumptions.textContent = (data.assumptions || []).length
        ? data.assumptions.join("\n")
        : "Base plan; no changes entered.";
    } catch (error) {
      empty.hidden = false;
      empty.textContent = error instanceof MeridianApiError
        ? `${error.message} ${error.recoveryAction}`
        : "Scenario preview unavailable.";
      compare.replaceChildren();
      assumptions.textContent = "";
    } finally {
      results.removeAttribute("aria-busy");
    }
  })();
}

function scheduleScenarioPreview(root) {
  if (scenarioTimer) {
    window.clearTimeout(scenarioTimer);
  }
  scenarioTimer = window.setTimeout(() => runScenarioPreview(root), 260);
}

function setupScenarioPreview(root) {
  const panel = root.querySelector("[data-plan-scenario]");
  if (!panel) {
    return;
  }
  if (!panel.__scenarioWired) {
    panel.__scenarioWired = true;
    const form = panel.querySelector("[data-plan-scenario-form]");
    const reset = panel.querySelector("[data-plan-scenario-reset]");
    form.addEventListener("input", () => scheduleScenarioPreview(panel));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (scenarioTimer) {
        window.clearTimeout(scenarioTimer);
      }
      runScenarioPreview(panel);
    });
    reset.addEventListener("click", () => {
      form.reset();
      if (scenarioTimer) {
        window.clearTimeout(scenarioTimer);
      }
      runScenarioPreview(panel);
    });
  }
  runScenarioPreview(panel);
}


/* ---------- Commitment table ---------- */

function nextDateForCommitment(plan, commitment) {
  const events = (plan.timeline?.events || []).filter(
    (event) => event.commitment_id === commitment.id
  );
  if (events.length) {
    return formatShortDate(
      events.reduce((earliest, event) =>
        event.date < earliest.date ? event : earliest
      ).date
    );
  }
  if (commitment.due_date) {
    return formatShortDate(commitment.due_date);
  }
  if (commitment.target_date) {
    return formatShortDate(commitment.target_date);
  }
  return "—";
}

function renderCommitments(root, plan, template) {
  const list = root.querySelector("[data-commitment-list]");
  const empty = root.querySelector("[data-commitments-empty]");
  // Keep the head row; remove previously rendered body rows.
  list.querySelectorAll("[data-commitment-card]").forEach((node) => node.remove());
  const commitments = plan.commitments || [];
  empty.hidden = commitments.length > 0;

  for (const commitment of commitments) {
    const row = document.createElement("div");
    row.className = "m-plan-table-row";
    row.setAttribute("role", "row");
    row.dataset.commitmentCard = String(commitment.id);
    row.tabIndex = 0;
    row.setAttribute("aria-label", `View ${commitment.name} rule`);
    row.addEventListener("keydown", (event) => {
      if (event.target !== row) {
        return;
      }
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectedCommitment(commitment);
      }
    });

    // The concept's bill row leads with a medallion. OS-089 ships the SLOT with what the
    // payload actually holds (see COMMITMENT_TYPE_ICONS): a glyph from the commitment's type
    // on a neutral disc. It is decorative to assistive tech -- the row's own name cell
    // states the bill -- so it is hidden from the accessibility tree rather than announced
    // twice.
    const medallionCell = document.createElement("div");
    medallionCell.className = "m-plan-table-cell m-plan-cell-medallion";
    medallionCell.setAttribute("role", "cell");
    medallionCell.setAttribute("aria-hidden", "true");
    const medallion = document.createElement("span");
    medallion.className = "m-bill-medallion";
    medallion.dataset.commitmentType = commitment.type || "unknown";
    const medallionGlyph = document.createElement("span");
    medallionGlyph.className = "m-bill-medallion-glyph";
    medallionGlyph.style.setProperty(
      "--m-bill-medallion-icon",
      kitIconUrl(COMMITMENT_TYPE_ICONS[commitment.type] || "question-circle")
    );
    medallion.appendChild(medallionGlyph);
    medallionCell.appendChild(medallion);

    const nameCell = document.createElement("div");
    nameCell.className = "m-plan-table-cell m-plan-cell-commitment";
    nameCell.setAttribute("role", "cell");

    const nameWrap = document.createElement("div");
    nameWrap.className = "m-plan-cell-name";
    const name = document.createElement("span");
    name.className = "m-commitment-name";
    name.textContent = commitment.name;
    nameWrap.appendChild(name);

    // The type tag is REMOVED for a bill -- the section banner above already says what the
    // list is, and the owner directed the removal -- and KEPT for every other type. That is
    // what stops the renamed banner from misrepresenting a row: this list can hold a goal
    // (the synthetic fixture carries one), so a goal still states GOAL beside its name
    // instead of being silently filed under "Upcoming bills". It is also what frees the
    // width the status badge needs on a long bill name.
    if (commitment.type && commitment.type !== "bill") {
      const type = document.createElement("span");
      type.className = "m-commitment-type";
      type.textContent = TYPE_LABELS[commitment.type] || commitment.type;
      nameWrap.appendChild(type);
    }

    // R33: subtle per-bill badge (underfunded / due_soon) on the existing card.
    // No separate monitor page; only flags bills that need attention.
    const status = commitment.biller_status;
    if (status === "unfunded" || status === "due_soon" || status === "changed") {
      const badge = document.createElement("span");
      badge.className = `m-bill-badge m-bill-badge--${status}`;
      badge.dataset.billerStatus = status;
      badge.setAttribute("aria-label", BILLER_STATUS_LABELS[status]);
      badge.textContent = BILLER_STATUS_LABELS[status];
      nameWrap.appendChild(badge);
    }

    // ONE date, on the row, exactly where the concept puts `Sep11`. It is the same value the
    // desktop table's NEXT column renders, so the two can never disagree. The first draft of
    // the spec moved BOTH this and the NEXT cell into the disclosure, which would have left
    // the collapsed row with no date at all; the correction is to keep one and drop the
    // duplicate. The duplicate dropped is the fact line's own `due ...` fragment, and the
    // NEXT cell is not rendered on mobile (see the stylesheet), so no date is lost and none
    // is stated twice.
    const dateLine = document.createElement("span");
    dateLine.className = "m-commitment-date";
    dateLine.dataset.commitmentDate = "";
    dateLine.textContent = nextDateForCommitment(plan, commitment);

    // Everything else the collapsed row used to carry moves into the disclosure: the fact
    // line, the funding progress bar and every attached piece of evidence.
    const panel = document.createElement("div");
    panel.className = "m-plan-table-cell m-plan-cell-panel";
    panel.setAttribute("role", "cell");

    // The full name, un-truncated, inside the panel. The row's own name truncates on a narrow
    // phone, and the spec requires the FULL name to remain available in the panel and in the
    // accessible name -- a `title` attribute would not do, because it is not reliably
    // announced and never appears on touch.
    const panelName = document.createElement("h3");
    panelName.className = "m-plan-panel-name";
    panelName.textContent = commitment.name;
    panel.appendChild(panelName);

    const facts = document.createElement("p");
    facts.className = "m-commitment-facts";
    const factsParts = [`${moneyWhole(commitment.funded)} of ${moneyWhole(commitment.target)}`];
    if (commitment.backing) {
      factsParts.push(`backed by ${commitment.backing.name}`);
    }
    facts.textContent = factsParts.join(" · ");
    panel.appendChild(facts);

    // Funding progress: a low-key bar so a bill's funded share reads at a
    // glance without a chart. Width is clamped to 0..100%, hidden when unknown.
    //
    // This lives on the COLLAPSED ROW, spanning it edge to edge, because that is where the
    // governing concept draws it -- a thin hairline with an end dot along the bottom of every
    // bill row. The spec had moved it into the disclosure along with the fact line and the
    // invoices; the owner corrected that on seeing it ("I would still want progress bars"), and
    // the concept agrees with him, so it is back on the row and is NOT duplicated inside the
    // panel. It stays a real `progressbar` with its value, so the bar is not colour-only.
    const progressCell = document.createElement("div");
    progressCell.className = "m-plan-table-cell m-plan-cell-progress";
    progressCell.setAttribute("role", "cell");
    if (typeof commitment.target === "number" && commitment.target > 0) {
      const progress = document.createElement("div");
      progress.className = "m-commitment-progress";
      progress.setAttribute("role", "progressbar");
      const pct = Math.max(0, Math.min(100, (commitment.funded / commitment.target) * 100));
      progress.setAttribute("aria-valuenow", String(Math.round(pct)));
      progress.setAttribute("aria-valuemin", "0");
      progress.setAttribute("aria-valuemax", "100");
      const track = document.createElement("span");
      track.className = "m-commitment-progress-track";
      const fill = document.createElement("span");
      fill.className = "m-commitment-progress-fill";
      fill.style.width = `${pct}%`;
      track.append(fill);
      progress.append(track);
      progressCell.appendChild(progress);
    }

    // Clickable invoice evidence pulled from mail (e.g. a Verizon bill email). These are the
    // entries that actually open an invoice; the row's indicator only says one exists.
    const invoices = commitment.invoice_evidence || [];
    for (const invoice of invoices) {
      const inv = document.createElement("button");
      inv.type = "button";
      inv.className = "m-invoice-link";
      inv.dataset.invoiceId = String(invoice.id);
      inv.textContent = `Invoice · ${invoice.title || "view email"}`;
      inv.addEventListener("click", (event) => {
        event.stopPropagation();
        window.open(invoice.content_url, "_blank", "noopener");
      });
      panel.appendChild(inv);
    }

    nameCell.append(nameWrap, dateLine);

    const fundedCell = document.createElement("div");
    fundedCell.className = "m-plan-table-cell m-plan-cell-funded";
    fundedCell.setAttribute("role", "cell");
    fundedCell.textContent = moneyWhole(commitment.funded);

    const nextCell = document.createElement("div");
    nextCell.className = "m-plan-table-cell m-plan-cell-next";
    nextCell.setAttribute("role", "cell");
    nextCell.textContent = nextDateForCommitment(plan, commitment);

    const actionCell = document.createElement("div");
    actionCell.className = "m-plan-table-cell m-plan-cell-action";
    actionCell.setAttribute("role", "cell");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "m-button m-button--quiet m-button--small";
    button.textContent = "Edit funding";
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openEditor(root, commitment, template);
    });
    actionCell.appendChild(button);

    // Live Crew bills: offer an approval-gated write-back proposal.
    if (commitment.crew_bill_id) {
      const crew = document.createElement("button");
      crew.type = "button";
      crew.className = "m-button m-button--quiet m-button--small";
      crew.textContent = "Save to Crew";
      crew.addEventListener("click", (event) => {
        event.stopPropagation();
        openCrewBillEditor(root, commitment, template);
      });
      actionCell.appendChild(crew);

      // Delete/archive the live Crew bill (owner-direct executes immediately;
      // an ambiguous delete proposes for approval).
      const del = document.createElement("button");
      del.type = "button";
      del.className = "m-button m-button--quiet m-button--small m-button--danger";
      del.textContent = "Delete";
      del.setAttribute("aria-label", `Delete bill ${commitment.name}`);
      del.addEventListener("click", (event) => {
        event.stopPropagation();
        if (!window.confirm(`Delete the Crew bill "${commitment.name}"? This cannot be undone.`)) {
          return;
        }
        (async () => {
          const note = document.createElement("p");
          note.className = "m-action-note";
          note.dataset.state = "ok";
          try {
            const result = await meridianMutate({
              type: "archive_crew_bill",
              params: { bill_id: commitment.crew_bill_id },
              provenance: "owner_direct",
              rationale: `Delete the Crew bill ${commitment.name} from Meridian.`,
            });
            const outcome = describeActionOutcome(result, {
              verifiedMessage: `Bill ${commitment.name} was deleted and verified.`,
            });
            note.dataset.state = outcome.tone;
            note.textContent = outcome.message;
            // A returned action record is durable history. archive_crew_bill has
            // no readback verifier, so it stays EXECUTED and never refreshes the
            // list — without this guard the archived bill would keep an active
            // Delete control that could create a second archive request.
            del.disabled = true;
            // Refresh only after durable verification; HTTP success or an
            // intermediate EXECUTED state is not proof that Crew changed.
            if (outcome.refresh) {
              setTimeout(() => loadPlan(), 600);
            }
          } catch (error) {
            note.dataset.state = "error";
            note.textContent =
              error instanceof MeridianApiError
                ? `${error.message} ${error.recoveryAction}`
                : "The bill could not be deleted.";
          }
          actionCell.appendChild(note);
        })();
      });
      actionCell.appendChild(del);
    } else {
      // A local planning record has no Crew bill behind it, so neither "Save to Crew" nor
      // the Crew delete applies -- and until now that left the row with NO removal path at
      // all. The owner had four stuck "Journey Test Bill" rows and no way to clear them.
      // This archives locally through the same proposal/execution/verification pipeline: it
      // never contacts the provider, and the executor refuses any row that does carry a
      // Crew bill id, so the two delete controls can never both apply to one row.
      const del = document.createElement("button");
      del.type = "button";
      del.className = "m-button m-button--quiet m-button--small m-button--danger";
      del.textContent = "Delete";
      del.setAttribute("aria-label", `Delete commitment ${commitment.name}`);
      del.addEventListener("click", (event) => {
        event.stopPropagation();
        if (!window.confirm(`Delete "${commitment.name}"? This cannot be undone.`)) {
          return;
        }
        (async () => {
          const note = document.createElement("p");
          note.className = "m-action-note";
          note.dataset.state = "ok";
          try {
            const result = await meridianMutate({
              type: "archive_commitment",
              params: { commitment_id: commitment.id },
              provenance: "owner_direct",
              rationale: `Delete the local commitment ${commitment.name} from Meridian.`,
            });
            const outcome = describeActionOutcome(result, {
              verifiedMessage: `${commitment.name} was deleted and verified.`,
            });
            note.dataset.state = outcome.tone;
            note.textContent = outcome.message;
            // One archive only: the row is concluded, so leave the control dead rather
            // than allowing a second request against it.
            del.disabled = true;
            if (outcome.refresh) {
              setTimeout(() => loadPlan(), 600);
            }
          } catch (error) {
            note.dataset.state = "error";
            note.textContent =
              error instanceof MeridianApiError
                ? `${error.message} ${error.recoveryAction}`
                : "The commitment could not be deleted.";
          }
          actionCell.appendChild(note);
        })();
      });
      actionCell.appendChild(del);
    }

    // The concept's small evidence glyph: an INDICATOR that evidence exists, and a way to open
    // the disclosure that holds it. It is rendered ONLY when a real invoice exists -- never a
    // disabled icon, which would imply evidence the payload does not have -- and it is not the
    // thing that opens an invoice; the panel's entries below are. Because the collapsed row
    // says nothing about evidence in text, this icon is the only signal that content exists,
    // so it carries a real accessible name: an unlabelled icon that is the sole indicator of
    // content is a defect, and a `title` would not do (not reliably announced, never on touch).
    let evidenceCell = null;
    let evidenceIndicator = null;
    if (invoices.length) {
      evidenceCell = document.createElement("div");
      evidenceCell.className = "m-plan-table-cell m-plan-cell-evidence";
      evidenceCell.setAttribute("role", "cell");
      evidenceIndicator = document.createElement("button");
      evidenceIndicator.type = "button";
      evidenceIndicator.className = "m-evidence-indicator";
      evidenceIndicator.dataset.evidenceCount = String(invoices.length);
      // The glyph is the kit's own evidence icon, taken from the existing mapping rather than
      // a new literal, so it is covered by the guard that fails when a mapped name has no
      // shipped asset (an absent asset renders an empty ring, i.e. a broken icon).
      evidenceIndicator.style.setProperty("--m-evidence-icon", kitIconUrl(ACTION_ICONS.evidence));
      evidenceIndicator.setAttribute("aria-expanded", "false");
      evidenceIndicator.setAttribute("aria-label", "Evidence available");
      evidenceCell.appendChild(evidenceIndicator);
    }

    // The concept gives each bill a disclosure chevron rather than a permanent row of buttons:
    // the row states the bill, and the actions and the rest of its detail arrive when it is
    // opened. That disclosure is what makes the compact mobile row possible at all, because
    // the three action buttons and the fact line were what forced the tall card. The state
    // lives on the row as `data-expanded` so the stylesheet owns the presentation while this
    // owns only the state and the accessibility contract.
    //
    // The cell is `display: none` above the mobile breakpoint, which removes it from the desktop
    // grid entirely, so the four-column desktop table is untouched by its presence here.
    const toggleCell = document.createElement("div");
    toggleCell.className = "m-plan-table-cell m-plan-cell-toggle";
    toggleCell.setAttribute("role", "cell");
    const rowToggle = document.createElement("button");
    rowToggle.type = "button";
    rowToggle.className = "m-plan-row-toggle";
    rowToggle.setAttribute("aria-expanded", "false");
    rowToggle.setAttribute("aria-label", `Show actions for ${commitment.name}`);
    rowToggle.innerHTML =
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"' +
      ' focusable="false"><path d="M9 6l6 6-6 6" stroke="currentColor" stroke-width="2"' +
      ' stroke-linecap="round" stroke-linejoin="round"/></svg>';

    // ONE disclosure, two controls that open it. Keeping the state transition in one place is
    // what stops the chevron and the evidence indicator from disagreeing about whether the
    // panel is open, which two independent handlers would eventually do.
    const toggleRow = () => {
      const expanded = row.dataset.expanded === "true";
      row.dataset.expanded = expanded ? "false" : "true";
      rowToggle.setAttribute("aria-expanded", expanded ? "false" : "true");
      rowToggle.setAttribute(
        "aria-label",
        `${expanded ? "Show" : "Hide"} actions for ${commitment.name}`
      );
      if (evidenceIndicator) {
        evidenceIndicator.setAttribute("aria-expanded", expanded ? "false" : "true");
      }
    };
    rowToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleRow();
    });
    if (evidenceIndicator) {
      evidenceIndicator.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleRow();
      });
    }
    toggleCell.appendChild(rowToggle);
    row.dataset.expanded = "false";

    // The panel cell carries the disclosure's contents and is placed in its own grid row, so
    // it can take the full width on mobile while the desktop row keeps its own rhythm. The
    // progress cell sits AFTER the name so its hairline draws along the bottom of the collapsed
    // band, which is where the concept puts it and where the eye scans for it.
    row.append(medallionCell, nameCell, progressCell, fundedCell, panel, nextCell);
    if (evidenceCell) {
      row.appendChild(evidenceCell);
    }
    row.append(toggleCell, actionCell);
    list.appendChild(row);
  }

  const footer = root.querySelector("[data-plan-next-funding]");
  const nextFunding =
    plan.summary.next_due ||
    (plan.timeline?.events?.length ? plan.timeline.events[0].date : null);
  if (nextFunding) {
    footer.hidden = false;
    footer.textContent = `Next funding ${formatShortDate(nextFunding)}`;
  } else {
    footer.hidden = true;
    footer.textContent = "";
  }
}

function absentBillRow(bill) {
  const view = describeAbsentBill(bill);
  const row = document.createElement("li");
  row.className = "m-commitment-row m-commitment-row-absent";
  row.dataset.absentBill = String(bill.id);
  const name = document.createElement("strong");
  name.className = "m-commitment-name";
  name.textContent = view.name;
  const provenance = document.createElement("span");
  provenance.className = "m-commitment-meta";
  provenance.textContent = view.source + " \u00b7 " + view.absent;
  const note = document.createElement("span");
  note.className = "m-commitment-note";
  note.textContent = view.note;
  // No amount and no control: a last known figure is not a current obligation.
  row.append(name, provenance, note);
  return row;
}

function renderAbsentBills(root, plan) {
  const section = root.querySelector("[data-absent-bills]");
  const list = root.querySelector("[data-absent-bill-list]");
  if (!section || !list) {
    return;
  }
  const bills = Array.isArray(plan.absent_bills) ? plan.absent_bills : [];
  list.replaceChildren();
  if (!bills.length) {
    section.hidden = true;
    return;
  }
  for (const bill of bills) {
    list.append(absentBillRow(bill));
  }
  section.hidden = false;
}

function renderDocumentDiscrepancies(root, plan) {
  const section = root.querySelector("[data-document-discrepancies]");
  const list = root.querySelector("[data-document-discrepancy-list]");
  const document_discrepancies = plan.document_discrepancies || [];
  section.hidden = document_discrepancies.length === 0;
  list.replaceChildren();
  for (const discrepancy of document_discrepancies) {
    const item = document.createElement("li");
    item.className = "m-commitment-card";
    const message = document.createElement("p");
    message.textContent = discrepancy.message;
    const approval = document.createElement("p");
    approval.className = "m-state-line";
    approval.textContent = discrepancy.requires_approval
      ? "Any change requires approval."
      : "Review only.";
    item.append(message, approval);
    list.append(item);
  }
}

/* ---------- Shared-rule inspector (desktop rail / mobile sheet) ---------- */

const inspectorState = { open: false };

function buildInspectorPanel() {
  const panel = document.createElement("section");
  panel.className = "m-inspector-inner m-plan-inspector";
  panel.dataset.planInspector = "";
  panel.innerHTML = `
    <div class="m-inspector-head">
      <span class="m-section-label">Selected rule</span>
      <button type="button" class="m-icon-button" data-plan-inspector-close data-sheet-initial-focus aria-label="Close rule details">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
          <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <div class="m-inspector-scroll">
      <h2 class="m-inspector-title" data-plan-inspector-title tabindex="-1">Select a commitment</h2>
      <dl class="m-facts">
        <div class="m-fact" data-fact="rule-method"><dt>Method</dt><dd data-plan-rule-method>—</dd></div>
        <div class="m-fact" data-fact="rule-target"><dt>Target</dt><dd data-plan-rule-target>—</dd></div>
        <div class="m-fact" data-fact="rule-current"><dt>Current</dt><dd data-plan-rule-current>—</dd></div>
      </dl>
      <section class="m-inspector-section" aria-label="Rule guidance">
        <h3>Guidance</h3>
        <p class="m-state-line" data-plan-rule-note>Select a commitment to see its funding rule.</p>
      </section>
      <button type="button" class="m-button" data-plan-edit-schedule>Edit schedule</button>
    </div>`;
  return panel;
}

function ensureInspectorPanel() {
  const rail = document.querySelector("[data-inspector-rail]");
  if (!rail) {
    return null;
  }
  let panel = rail.querySelector("[data-plan-inspector]");
  if (!panel) {
    panel = buildInspectorPanel();
    panel.addEventListener("click", (event) => {
      if (event.target.closest("[data-plan-inspector-close]")) {
        closePlanInspector();
        return;
      }
      if (event.target.closest("[data-plan-edit-schedule]")) {
        openScheduleEditor();
      }
    });
    rail.appendChild(panel);
  }
  return { rail, panel };
}

function ruleMethodText(rule) {
  if (!rule) {
    return "No funding rule yet";
  }
  switch (rule.kind) {
    case "percent_of_paycheck":
      return `${rule.percent || 0}% of pay`;
    case "fixed_per_paycheck":
      return `${money(rule.amount)} per paycheck`;
    case "calendar":
      return `${money(rule.amount)} on a calendar cadence`;
    case "even_by_due_date":
      return "Even by due date";
    default:
      return "Manual";
  }
}

function guidanceNote(commitment, rule) {
  if (!rule) {
    return "No funding rule yet. Add one to fund this commitment.";
  }
  if (commitment.unfunded <= 0) {
    return "Fully funded. Meridian can repurpose the surplus.";
  }
  if (commitment.projected_30d > 0) {
    const months = Math.max(1, Math.ceil(commitment.unfunded / commitment.projected_30d));
    const arrives = new Date();
    arrives.setMonth(arrives.getMonth() + months);
    const label = arrives.toLocaleDateString(undefined, { month: "long", year: "numeric" });
    return `At this pace, the target arrives ${label}. Meridian can propose a faster schedule.`;
  }
  return "Underfunded. Add a funding rule to reach the target.";
}

function populateInspector(panel, commitment) {
  const rule = currentRulesById.get(String(commitment.id))?.[0] || null;
  const title = panel.querySelector("[data-plan-inspector-title]");
  title.textContent = commitment.name;
  panel.querySelector("[data-plan-rule-method]").textContent = ruleMethodText(rule);
  panel.querySelector("[data-plan-rule-target]").textContent = moneyWhole(commitment.target);
  panel.querySelector("[data-plan-rule-current]").textContent = moneyWhole(commitment.funded);
  panel.querySelector("[data-plan-rule-note]").textContent = guidanceNote(commitment, rule);
}

function openPlanInspector(commitment) {
  const ctx = ensureInspectorPanel();
  if (!ctx || !commitment) {
    return;
  }
  ctx.rail.setAttribute("data-plan-mode", "");
  populateInspector(ctx.panel, commitment);
  if (!inspectorState.open) {
    inspectorState.open = true;
    window.MeridianShell.openSheet(ctx.rail, { modal: isMobileViewport() });
  }
}

function closePlanInspector() {
  const rail = document.querySelector("[data-inspector-rail]");
  if (rail) {
    rail.removeAttribute("data-plan-mode");
  }
  if (inspectorState.open) {
    inspectorState.open = false;
    window.MeridianShell.closeSheet();
  }
}

function openScheduleEditor() {
  // "Edit schedule" behaves like the row's Edit funding control.
  if (isMobileViewport()) {
    closePlanInspector();
  }
  const root = document.querySelector("[data-plan-root]");
  const template = root.closest("main").querySelector("[data-funding-editor-template]");
  const card = root.querySelector(`[data-commitment-card="${currentInspectorCommitmentId}"]`);
  const commitment = currentPlan?.commitments?.find(
    (item) => item.id === currentInspectorCommitmentId
  );
  if (card && commitment) {
    openEditor(root, commitment, template);
    card.scrollIntoView({ block: "center" });
    card.querySelector("[data-funding-editor] input, [data-funding-editor] select")?.focus();
  }
}

let currentInspectorCommitmentId = null;

function selectedCommitment(commitment) {
  if (!commitment) {
    return;
  }
  currentInspectorCommitmentId = commitment.id;
  openPlanInspector(commitment);
}

/* ---------- Funding-rule editor ---------- */

function describeRule(kind, amount, percent) {
  switch (kind) {
    case "fixed_per_paycheck":
      return `Moves ${money(amount)} from available cash on each paycheck.`;
    case "percent_of_paycheck":
      return `Moves ${percent || 0}% of each paycheck.`;
    case "calendar":
      return `Moves ${money(amount)} on a repeating calendar cadence.`;
    case "even_by_due_date":
      return `Splits the remaining amount evenly between now and the due date.`;
    default:
      return "";
  }
}

function openEditor(root, commitment, template) {
  root.querySelectorAll("[data-funding-editor]").forEach((node) => node.remove());
  const editor = template.content.firstElementChild.cloneNode(true);
  editor.dataset.commitmentId = String(commitment.id);
  const preview = editor.querySelector("[data-editor-preview]");

  const kindSelect = editor.querySelector('select[name="kind"]');
  const amountInput = editor.querySelector('input[name="amount"]');
  const percentInput = editor.querySelector('input[name="percent"]');

  function syncFields() {
    const kind = kindSelect.value;
    editor.querySelector('[data-editor-field="amount"]').hidden = kind === "percent_of_paycheck";
    editor.querySelector('[data-editor-field="percent"]').hidden = kind !== "percent_of_paycheck";
    preview.textContent = describeRule(
      kind,
      amountInput.value ? Number(amountInput.value) : null,
      percentInput.value
    );
  }

  kindSelect.addEventListener("change", syncFields);
  amountInput.addEventListener("input", syncFields);
  percentInput.addEventListener("input", syncFields);
  editor.querySelector("[data-editor-cancel]").addEventListener("click", () => editor.remove());

  editor.addEventListener("submit", async (event) => {
    event.preventDefault();
    const note = editor.querySelector("[data-editor-note]");
    const rule = { kind: kindSelect.value };
    if (kindSelect.value === "percent_of_paycheck") {
      if (percentInput.value) {
        rule.percent = Number(percentInput.value);
      }
    } else if (amountInput.value) {
      rule.amount = Number(amountInput.value);
    }
    note.hidden = true;
    try {
      await meridianPropose("/api/meridian/funding-rules/propose", {
        commitment_id: commitment.id,
        rule,
      });
      note.hidden = false;
      note.textContent = "Proposal created — approve it in Pending Actions.";
      note.dataset.state = "ok";
    } catch (error) {
      note.hidden = false;
      note.dataset.state = "error";
      note.textContent =
        error instanceof MeridianApiError
          ? `${error.message} ${error.recoveryAction}`
          : "The proposal could not be created.";
    }
  });

  syncFields();
  root.querySelector(`[data-commitment-card="${commitment.id}"]`).appendChild(editor);
  return editor;
}

/* ---------- Live Crew bill write-back (approval-gated) ---------- */

function openCrewBillEditor(root, commitment, template) {
  root.querySelectorAll("[data-funding-editor]").forEach((node) => node.remove());
  const editor = template.content.firstElementChild.cloneNode(true);
  editor.dataset.commitmentId = String(commitment.id);
  const preview = editor.querySelector("[data-editor-preview]");
  const kindSelect = editor.querySelector('select[name="kind"]');
  const amountInput = editor.querySelector('input[name="amount"]');
  const percentInput = editor.querySelector('input[name="percent"]');
  const note = editor.querySelector("[data-editor-note]");
  const submit = editor.querySelector('button[type="submit"]');

  // Re-purpose: Create a Crew bill write-back proposal.
  kindSelect.hidden = true;
  percentInput.closest('[data-editor-field="percent"]').hidden = true;
  amountInput.value = "";
  amountInput.setAttribute("placeholder", `New amount ($) for ${commitment.name}`);
  preview.textContent = `Approve to push a ${commitment.name} change to Crew.`;
  submit.textContent = "Propose to Crew";

  // Frequency + anchor date fields (Crew contract: frequency/frequencyInterval/anchorDate).
  const freq = document.createElement("label");
  freq.className = "m-field";
  freq.innerHTML = `
    <span class="m-field-label">Repeat</span>
    <select class="m-select" name="frequency">
      <option value="MONTHLY">Monthly</option>
      <option value="WEEKLY">Weekly</option>
      <option value="YEARLY">Yearly</option>
    </select>`;
  const anchor = document.createElement("label");
  anchor.className = "m-field";
  anchor.innerHTML = `
    <span class="m-field-label">Anchor date</span>
    <input class="m-input" name="anchor-date" type="date" inputmode="numeric">`;
  // Default anchor to the commitment's due date if known, else today; frequency default monthly.
  const due = commitment.due_date || new Date().toISOString().slice(0, 10);
  anchor.querySelector('input[name="anchor-date"]').value = due;
  editor.insertBefore(freq, preview);
  editor.insertBefore(anchor, preview);

  editor.querySelector("[data-editor-cancel]").addEventListener("click", () => editor.remove());

  editor.addEventListener("submit", async (event) => {
    event.preventDefault();
    note.hidden = true;
    const amount = Number(amountInput.value);
    if (!Number.isFinite(amount) || amount <= 0) {
      note.hidden = false;
      note.dataset.state = "error";
      note.textContent = "Enter a valid amount.";
      return;
    }
    const frequency = editor.querySelector('select[name="frequency"]').value;
    const frequencyInterval = frequency === "WEEKLY" ? 1 : frequency === "MONTHLY" ? 1 : 1;
    const anchorDate = editor.querySelector('input[name="anchor-date"]').value || new Date().toISOString().slice(0, 10);
    try {
      await meridianPropose("/api/meridian/crew/bills", {
        billId: commitment.crew_bill_id,
        name: commitment.name,
        amount: Math.round(amount * 100), // dollars -> cents (Crew contract)
        frequency,
        frequencyInterval,
        anchorDate,
      });
      note.hidden = false;
      note.textContent = "Crew write-back proposed — approve it in Pending Actions.";
      note.dataset.state = "ok";
    } catch (error) {
      note.hidden = false;
      note.dataset.state = "error";
      note.textContent =
        error instanceof MeridianApiError
          ? `${error.message} ${error.recoveryAction}`
          : "The Crew write-back could not be proposed.";
    }
  });

  root.querySelector(`[data-commitment-card="${commitment.id}"]`).appendChild(editor);
  amountInput.focus();
  return editor;
}

/* ---------- New autopilot rule (approval-gated) ---------- */

function openAutopilotRuleEditor() {
  const root = document.querySelector("[data-plan-root]");
  if (!root || typeof window.MeridianShell === "undefined") return;

  const sheet = document.createElement("section");
  sheet.className = "m-sheet m-funding-editor m-autopilot-rule-editor";
  sheet.setAttribute("role", "dialog");
  sheet.setAttribute("aria-label", "New autopilot rule");
  sheet.hidden = true;
  sheet.innerHTML = `
    <form class="m-funding-editor" data-autopilot-rule-form>
      <h3 class="m-editor-title">New autopilot rule</h3>
      <label class="m-field">
        <span class="m-field-label">Rule name</span>
        <input class="m-input" name="rule-name" type="text" required maxlength="80" placeholder="e.g. Save the spare change">
      </label>
      <label class="m-field">
        <span class="m-field-label">Triggers</span>
        <select class="m-select" name="rule-trigger">
          <option value="ACCOUNT_DEPOSIT_RECEIVED">Account deposit received</option>
          <option value="DEBIT_CARD_TRANSACTION">Debit card transaction</option>
        </select>
      </label>
      <label class="m-field">
        <span class="m-field-label">Action</span>
        <select class="m-select" name="rule-action">
          <option value="roundUpTransfer">Round up spare change</option>
          <option value="targetBalanceTransfer">Move to a target balance</option>
          <option value="internalTransfer">Move a fixed amount</option>
          <option value="splitDeposit">Split a deposit by percentage</option>
          <option value="sweepExcess">Sweep excess above a floor</option>
        </select>
      </label>
      <div class="m-field" data-rule-target-balance hidden>
        <span class="m-field-label">Target balance ($)</span>
        <input class="m-input" name="rule-merchant" type="number" min="0" step="0.01" inputmode="decimal">
      </div>
      <div class="m-field" data-rule-amount hidden>
        <span class="m-field-label">Amount ($)</span>
        <input class="m-input" name="rule-amount" type="number" min="0.01" step="0.01" inputmode="decimal">
      </div>
      <div class="m-field" data-rule-to-subaccount hidden>
        <span class="m-field-label">To pocket (subaccount id)</span>
        <input class="m-input" name="rule-subaccount" type="text" placeholder="U3ViYWNjb3VudDo…">
      </div>
      <p class="m-editor-preview">Creates a Crew autopilot rule. A fully-specified owner rule executes; under-specified rules need approval.</p>
      <div class="m-editor-actions">
        <button type="submit" class="m-button">Create rule</button>
        <button type="button" class="m-button m-button--quiet" data-autopilot-rule-cancel>Cancel</button>
      </div>
      <p class="m-editor-note" data-autopilot-rule-note hidden></p>
    </form>
  `;

  const note = sheet.querySelector("[data-autopilot-rule-note]");

  // Show/hide action-specific fields.
  const actionSelect = sheet.querySelector('select[name="rule-action"]');
  const syncFields = () => {
    const action = actionSelect.value;
    sheet.querySelector("[data-rule-target-balance]").hidden = action !== "targetBalanceTransfer";
    sheet.querySelector("[data-rule-amount]").hidden =
      !(action === "internalTransfer" || action === "sweepExcess");
    sheet.querySelector("[data-rule-to-subaccount]").hidden =
      !(action === "targetBalanceTransfer" || action === "internalTransfer");
  };
  actionSelect.addEventListener("change", syncFields);
  syncFields();

  sheet.querySelector("[data-autopilot-rule-cancel]").addEventListener("click", () => {
    if (window.MeridianShell.closeSheet) window.MeridianShell.closeSheet();
  });
  sheet.querySelector("form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = sheet.querySelector("form");
    const name = form.querySelector('input[name="rule-name"]').value.trim();
    const action = form.querySelector('select[name="rule-action"]').value;
    const trigger = form.querySelector('select[name="rule-trigger"]').value;
    const toSub = form.querySelector('input[name="rule-subaccount"]').value.trim();
    note.hidden = true;
    if (!name) {
      note.hidden = false; note.dataset.state = "error";
      note.textContent = "Enter a rule name.";
      return;
    }
    // Build the verified formula action (subset of the real action union) with
    // the real Crew account/subaccount ids injected so the server never sends a
    // null accountId (which Crew rejects).
    const crewIds = (currentPlan && currentPlan.crew_ids) || {};
    const accountId = crewIds.account_id || "";
    const subaccountId = crewIds.free_to_spend_subaccount_id || "";
    const actions = [];
    if (action === "roundUpTransfer") {
      actions.push({ roundUpTransfer: { roundToNearest: 100, accountId, accountType: "ACCOUNT", subaccountId } });
    } else if (action === "sweepExcess" || action === "targetBalanceTransfer") {
      const amtField = form.querySelector('input[name="rule-merchant"]').value;
      const amount = Number(amtField) || 1;
      if (action === "sweepExcess") {
        actions.push({ sweepExcess: {
          subaccountId: subaccountId || toSub,
          amountToRemain: Math.round(amount * 100),
          sweepDestinations: [{ type: "SUBACCOUNT", percentage: 100, subaccountId: subaccountId || toSub || "" }],
        }});
      } else {
        actions.push({ targetBalanceTransfer: { target: Math.round(amount * 100), direction: "INTO", accountId, subaccountId } });
      }
    } else if (action === "internalTransfer") {
      const amt = Number(form.querySelector('input[name="rule-amount"]').value);
      actions.push({ internalTransfer: { amount: Math.round(amt * 100), memo: name, accountFromId: accountId, accountToId: subaccountId || toSub } });
    } else if (action === "splitDeposit") {
      actions.push({ splitDeposit: { destinations: [{ type: "SUBACCOUNT", percentage: 100, subaccountId: subaccountId || toSub || "" }] }});
    }
    const rule = {
      name,
      formula: {
        name,
        triggers: [trigger],
        conditions: { and: { conditions: [{ idMatch: {
          entitySchema: "SUBACCOUNTS",
          entityId: subaccountId,
        } }] } },
        actions,
      },
    };
    try {
      const result = await meridianMutate({
        type: "create_crew_autopilot_rule",
        params: { name, account_id: accountId, subaccount_id: subaccountId, formula: rule.formula },
        provenance: "owner_direct",
        rationale: `Create an autopilot rule (${action}) from Meridian.`,
      });
      const outcome = describeActionOutcome(result, {
        verifiedMessage: "Autopilot rule was created and verified.",
      });
      note.hidden = false;
      note.dataset.state = outcome.tone;
      note.textContent = outcome.message;
    } catch (error) {
      note.hidden = false; note.dataset.state = "error";
      note.textContent = error instanceof MeridianApiError
        ? `${error.message} ${error.recoveryAction}`
        : "The rule could not be created.";
    }
  });

  document.body.appendChild(sheet);
  window.MeridianShell.openSheet(sheet, { modal: true });
  requestAnimationFrame(() => {
    const initial = sheet.querySelector('input[name="rule-name"]');
    if (initial) initial.focus();
  });
}

/* ---------- New commitment (approval-gated proposal) ---------- */

function openNewCommitmentEditor() {
  const root = document.querySelector("[data-plan-root]");
  if (!root || typeof window.MeridianShell === "undefined") return;

  const sheet = document.createElement("section");
  sheet.className = "m-sheet m-funding-editor m-new-commitment-editor";
  sheet.setAttribute("role", "dialog");
  sheet.setAttribute("aria-label", "New commitment");
  sheet.hidden = true;
  sheet.innerHTML = `
    <form class="m-funding-editor" data-new-commitment-form>
      <h3 class="m-editor-title">New commitment</h3>
      <label class="m-field">
        <span class="m-field-label">Type</span>
        <select class="m-select" name="type">
          <option value="bill">Bill</option>
          <option value="goal">Goal</option>
          <option value="reserve">Reserve</option>
          <option value="buffer">Buffer</option>
          <option value="debt">Debt</option>
        </select>
      </label>
      <label class="m-field">
        <span class="m-field-label">Name</span>
        <input class="m-input" name="name" type="text" required maxlength="80" placeholder="e.g. New bill">
      </label>
      <label class="m-field">
        <span class="m-field-label">Amount</span>
        <input class="m-input" name="amount" type="number" min="0" step="0.01" inputmode="decimal" placeholder="0.00">
      </label>
      <label class="m-field">
        <span class="m-field-label">Recurrence</span>
        <select class="m-select" name="recurrence">
          <option value="one_time">One-time</option>
          <option value="monthly">Monthly</option>
          <option value="weekly">Weekly</option>
          <option value="yearly">Yearly</option>
        </select>
      </label>
      <p class="m-editor-preview">Creates a commitment proposal; approve to apply it.</p>
      <div class="m-editor-actions">
        <button type="submit" class="m-button">Propose commitment</button>
        <button type="button" class="m-button m-button--quiet" data-new-commitment-cancel>Cancel</button>
      </div>
      <p class="m-editor-note" data-new-commitment-note hidden></p>
    </form>
  `;

  const note = sheet.querySelector("[data-new-commitment-note]");
  sheet.querySelector("[data-new-commitment-cancel]").addEventListener("click", () => {
    if (window.MeridianShell.closeSheet) window.MeridianShell.closeSheet();
  });
  sheet.querySelector("form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const type = sheet.querySelector('select[name="type"]').value;
    const name = sheet.querySelector('input[name="name"]').value.trim();
    const amount = Number(sheet.querySelector('input[name="amount"]').value);
    const recurrence = sheet.querySelector('select[name="recurrence"]').value;
    note.hidden = true;
    if (!name) {
      note.hidden = false; note.dataset.state = "error";
      note.textContent = "Enter a commitment name.";
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      note.hidden = false; note.dataset.state = "error";
      note.textContent = "Enter a valid amount greater than zero.";
      return;
    }
    try {
      // Direct proposal POST (create_commitment is not on the browser allowlist,
      // so use fetch to /api/actions/propose); approval-gated, never executes.
      const response = await fetch("/api/actions/propose", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "create_commitment",
          params: { type, name, amount, currency: "USD", recurrence },
          rationale: "New commitment from Plan",
        }),
      });
      if (!response.ok) {
        let message = "The commitment could not be proposed.";
        try { const data = await response.json(); if (data?.error) message = data.error; } catch (_) {}
        throw new MeridianApiError({ code: "proposal_rejected", message, recoveryAction: "Review the form and try again.", status: response.status });
      }
      note.hidden = false; note.dataset.state = "ok";
      note.textContent = "Commitment proposed — approve it in Pending Actions.";
      sheet.querySelector('[name="name"]') && (sheet.querySelector('[name="name"]').value = "");
    } catch (error) {
      note.hidden = false; note.dataset.state = "error";
      note.textContent = error instanceof MeridianApiError
        ? `${error.message} ${error.recoveryAction}`
        : "The commitment could not be proposed.";
    }
  });

  document.body.appendChild(sheet);
  window.MeridianShell.openSheet(sheet, { modal: true });
}

/* ---------- Load + wiring ---------- */

function indexRules(rules) {
  const map = new Map();
  for (const rule of rules || []) {
    const key = String(rule.commitment_id);
    if (!map.has(key)) {
      map.set(key, []);
    }
    map.get(key).push(rule);
  }
  return map;
}

/* Switch between the Plan | Rules | Crew segmented views (keeps the page
   scannable instead of one long scroll). */
function setupPlanSegs(root) {
  const seg = root.querySelector("[data-plan-seg]");
  if (!seg) {
    return;
  }
  const panes = root.querySelectorAll("[data-plan-view-pane]");
  const tabs = seg.querySelectorAll("[data-plan-view]");
  tabs.forEach((tab) => {
    const name = tab.dataset.planView;
    const activ = tab.classList.contains("is-active");
    tab.setAttribute("aria-pressed", activ ? "true" : "false");
    tab.addEventListener("click", (event) => {
      event.stopPropagation();
      tabs.forEach((t) => {
        const on = t === tab;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-pressed", on ? "true" : "false");
      });
      panes.forEach((p) => {
        p.hidden = p.dataset.planViewPane !== name;
      });
    });
  });
}

/* OS-102: a rule is explained in words, and what cannot be explained honestly is DISCLOSED rather
   than smoothed over. The old body line looked for `action.type`; a real Crew formula carries
   `actions: [{roundUpTransfer: {...}}]`, where the action name is the KEY, so every genuine rule
   rendered with an empty body. The statement builder lives in ./rule-statement.js so it can be
   executed under Node (tests/meridian/test_rule_statement_js.py) rather than only grepped. */

function ruleNameLookup() {
  /* Crew ids are opaque. The plan payload already resolves the ones it knows -- the account and the
     pockets it can address -- so a statement can say "Free to Spend" wherever that is known, and say
     the honest thing where it is not. It never invents a name for an id it cannot resolve. */
  const names = {};
  const crew = (currentPlan && currentPlan.crew_ids) || {};
  if (crew.account_id) names[String(crew.account_id)] = "Checking";
  for (const sub of crew.subaccounts || []) {
    if (sub && sub.id) names[String(sub.id)] = sub.name || "Pocket";
  }
  return names;
}

function ruleStatementLine(label, text) {
  const row = document.createElement("p");
  row.className = "m-rule-statement-line";
  const key = document.createElement("span");
  key.className = "m-rule-statement-key";
  key.textContent = label;
  const value = document.createElement("span");
  value.className = "m-rule-statement-value";
  value.textContent = text;
  row.append(key, value);
  return row;
}

function ruleStatementNode(statement) {
  const wrap = document.createElement("div");
  wrap.className = "m-rule-statement";
  const lines = [];
  if (statement.when) {
    lines.push(["When", statement.when]);
  }
  for (const condition of statement.conditions) {
    // The statement builder owns the single "only when"; the card labels the row instead.
    lines.push(["If", condition.replace(/^only when /, "")]);
  }
  for (const effect of statement.effects) {
    lines.push(["Then", effect]);
  }
  if (!lines.length && statement.description) {
    lines.push(["Crew's description", statement.description]);
  }
  for (const [label, text] of lines) {
    wrap.append(ruleStatementLine(label, text));
  }
  if (statement.schedule) {
    wrap.append(ruleStatementLine("Schedule", statement.schedule));
  }
  if (!statement.recognised) {
    /* Not summarised away: the terms Meridian does not read are named, and Crew's own formula is
       available underneath. A rule the app cannot fully explain must not read as explained. */
    const note = document.createElement("p");
    note.className = "m-rule-unknown";
    note.textContent = `Meridian cannot fully explain this rule yet: ${statement.unknown.join("; ")}.`;
    const details = document.createElement("details");
    details.className = "m-rule-raw";
    const summary = document.createElement("summary");
    summary.textContent = "Crew's own formula";
    const pre = document.createElement("pre");
    pre.textContent = statement.raw;
    details.append(summary, pre);
    wrap.append(note, details);
  }
  return wrap;
}

function ruleCard(rule, statement) {
  const card = document.createElement("article");
  card.className = "m-rule-card";
  card.dataset.ruleId = rule.id;
  card.dataset.rulePurpose = statement.purpose;
  card.dataset.ruleExplained = statement.recognised ? "true" : "false";
  const head = document.createElement("div");
  head.className = "m-rule-card-head";
  const nameEl = document.createElement("h3");
  nameEl.className = "m-rule-card-name";
  nameEl.textContent = rule.name || "Untitled rule";
  head.appendChild(nameEl);
  if (rule.is_paused) {
    const paused = document.createElement("span");
    paused.className = "m-bill-badge m-bill-badge--due_soon";
    paused.textContent = "Paused";
    head.appendChild(paused);
  }
  const note = document.createElement("p");
  note.className = "m-action-note";
  note.hidden = true;
  const del = document.createElement("button");
  del.type = "button";
  del.className = "m-button m-button--quiet m-button--small m-button--danger";
  del.textContent = "Delete";
  del.setAttribute("aria-label", `Delete rule ${rule.name}`);
  del.addEventListener("click", () => {
    if (!window.confirm(`Delete the rule "${rule.name}"? This cannot be undone.`)) {
      return;
    }
    (async () => {
      try {
        const result = await meridianMutate({
          type: "delete_crew_autopilot_rule",
          params: { rule_id: rule.id },
          provenance: "owner_direct",
          rationale: `Delete the Crew rule ${rule.name} from Meridian.`,
        });
        const outcome = describeActionOutcome(result, {
          verifiedMessage: "Rule deleted and verified.",
        });
        note.hidden = false;
        note.dataset.state = outcome.tone;
        note.textContent = outcome.message;
        // A returned action record is durable history. Do not turn the same
        // control into a blind resend path after failure or uncertainty.
        del.disabled = true;
        if (outcome.refresh) {
          setTimeout(() => loadPlan(), 600);
        }
      } catch (error) {
        note.hidden = false;
        note.dataset.state = "error";
        note.textContent = error instanceof MeridianApiError
          ? `${error.message} ${error.recoveryAction}`
          : "The rule could not be deleted.";
      }
    })();
  });
  head.appendChild(del);
  card.appendChild(head);
  card.appendChild(note);
  card.appendChild(ruleStatementNode(statement));
  return card;
}

function renderRules(root) {
  const list = root.querySelector("[data-rules-list]");
  const empty = root.querySelector("[data-rules-empty]");
  const source = root.querySelector("[data-rules-source]");
  if (!list) {
    return;
  }
  const crew = (currentPlan && currentPlan.crew_ids) || {};
  const rules = crew.rules || [];
  const names = ruleNameLookup();
  if (empty) {
    // The note is a SIBLING of the list now, so clearing the list can no longer destroy it. The null
    // check stays anyway: depending on markup elsewhere is exactly how this broke the first time.
    empty.hidden = rules.length > 0;
  }
  if (source) {
    const freshness = (currentPlan && currentPlan.data_freshness) || null;
    const when = freshness && freshness.label ? freshness.label : "observation time unavailable";
    source.hidden = rules.length === 0;
    source.textContent = rules.length
      ? `${rules.length} rule${rules.length === 1 ? "" : "s"} read from Crew · ${when}`
      : "";
  }
  list.replaceChildren();

  /* Grouped by what each rule acts on, in the order that is useful rather than the order Crew
     returned: money movement first because it moves money, notifications after it. One group renders
     without a heading, so a single rule does not read as a taxonomy. */
  const order = ["money", "notify", "other"];
  const grouped = new Map();
  for (const rule of rules) {
    const statement = ruleStatement(rule, { names });
    if (!grouped.has(statement.purpose)) grouped.set(statement.purpose, []);
    grouped.get(statement.purpose).push({ rule, statement });
  }
  const present = order.filter((purpose) => grouped.has(purpose));
  for (const purpose of present) {
    if (present.length > 1) {
      const heading = document.createElement("h3");
      heading.className = "m-rule-group-title";
      heading.textContent = rulePurposeLabel(purpose);
      list.appendChild(heading);
    }
    for (const { rule, statement } of grouped.get(purpose)) {
      list.appendChild(ruleCard(rule, statement));
    }
  }
}

async function loadCaptureStatus(root) {
  const panel = root.querySelector("[data-capture-status]");
  if (!panel) {
    return;
  }
  const total = panel.querySelector("[data-capture-total]");
  const track = panel.querySelector("[data-capture-track]");
  const note = panel.querySelector("[data-capture-note]");
  try {
    const payload = await meridianFetch("/api/meridian/crew/mutations-status");
    const summary = payload.summary || {};
    const captured = summary.captured || 0;
    const missing = summary.missing || 0;
    const all = summary.total || 0;
    total.textContent = `${captured}/${all}`;
    const pct = all ? Math.round((captured / all) * 100) : 0;
    track.replaceChildren();
    const fill = document.createElement("span");
    fill.className = "m-capture-status-fill";
    fill.style.width = `${pct}%`;
    track.appendChild(fill);
    note.textContent = missing > 0
      ? `${captured} of ${all} verified; ${missing} not yet captured.`
      : `${captured} of ${all} verified — full covered.`;
  } catch {
    total.textContent = "—";
    note.textContent = "Capture status unavailable.";
  }
}

async function loadPlan() {
  const root = document.querySelector("[data-plan-root]");
  if (!root) {
    return;
  }
  if (controller) {
    controller.abort();
  }
  controller = new AbortController();
  const errorBox = root.querySelector("[data-plan-error]");
  errorBox.hidden = true;
  root.setAttribute("aria-busy", "true");
  try {
    const [planRes, rulesRes] = await Promise.allSettled([
      meridianFetch("/api/meridian/plan", { signal: controller.signal }),
      meridianFetch("/api/meridian/funding-rules", { signal: controller.signal }),
    ]);
    if (planRes.status === "rejected") {
      throw planRes.reason;
    }
    const plan = planRes.value;
    const rules =
      rulesRes.status === "fulfilled" ? rulesRes.value.funding_rules || [] : [];

    currentPlan = plan;
    currentRulesById = indexRules(rules);
    const template = root
      .closest("main")
      .querySelector("[data-funding-editor-template]");

    renderSummary(root, plan);
    renderCoverage(root, plan);
    renderFundingCard(root, plan, rules.length);
    renderAllocation(root, plan);
    renderTimeline(root, plan);
    renderCommitments(root, plan, template);
    renderAbsentBills(root, plan);
    renderDocumentDiscrepancies(root, plan);
    loadCaptureStatus(root);
    setupPlanSegs(root);
    setupScenarioPreview(root);
    renderRules(root);
    const ruleForm = root.querySelector("[data-ca-delete-rule]");
    if (ruleForm) {
      populateRulePicker(ruleForm);
    }
    const spendForm = root.querySelector("[data-ca-set-spend]");
    if (spendForm) {
      populatePocketPicker(spendForm);
    }
    const delPocket = root.querySelector("[data-ca-delete-pocket]");
    if (delPocket) {
      populatePocketPicker(delPocket, true);
    }
    const vcForm = root.querySelector("[data-ca-create-virtual-card]");
    if (vcForm) {
      populatePocketPicker(vcForm, true);
    }

    // Desktop shows the rail by default; mobile only on demand. Prefer a
    // commitment with a funding rule and a real target (e.g. a goal/reserve).
    if (!isMobileViewport() && plan.commitments?.length) {
      const withRule =
        plan.commitments.find(
          (item) => currentRulesById.has(String(item.id)) && item.target > 0
        ) ||
        plan.commitments.find((item) => currentRulesById.has(String(item.id))) ||
        plan.commitments[0];
      selectedCommitment(withRule);
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }
    errorBox.textContent =
      error instanceof MeridianApiError
        ? `${error.message} ${error.recoveryAction}`
        : "The plan could not be loaded.";
    errorBox.hidden = false;
  } finally {
    root.removeAttribute("aria-busy");
  }
}

window.MeridianPlan = { loadPlan };

/* Wire the Crew action panel (create pocket / create bill / top up reserve) to
   POST /api/actions/mutate, which routes owner-direct inputs straight to Crew and
   AI-composed/under-specified inputs to a proposal for approval. */
function wireCrewActions(root) {
  const attach = (form, build) => {
    if (!form || form.__wired) {
      return;
    }
    form.__wired = true;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const note = form.querySelector("[data-note]");
      const payload = build(form);
      note.hidden = true;
      try {
        const result = await meridianMutate(payload);
        const outcome = describeActionOutcome(result);
        note.hidden = false;
        note.dataset.state = outcome.tone;
        note.textContent = outcome.message;
      } catch (error) {
        note.hidden = false;
        note.dataset.state = "error";
        note.textContent =
          error instanceof MeridianApiError
            ? `${error.message} ${error.recoveryAction}`
            : "The Crew action could not be sent.";
      }
    });
  };
  attach(root.querySelector("[data-ca-create-pocket]"), (f) => {
    const crew = (currentPlan && currentPlan.crew_ids) || {};
    return {
      type: "create_crew_pocket",
      params: {
        account_id: crew.account_id || "",
        name: f.querySelector('input[name="name"]').value.trim(),
        type: "SAVINGS",
      },
      provenance: "owner_direct",
      rationale: "Create a pocket from Meridian.",
    };
  });
  attach(root.querySelector("[data-ca-create-bill]"), (f) => {
    const amount = Number(f.querySelector('input[name="amount"]').value);
    const crew = (currentPlan && currentPlan.crew_ids) || {};
    return {
      type: "create_crew_bill",
      params: {
        account_id: crew.account_id || "",
        name: f.querySelector('input[name="name"]').value.trim(),
        amount: Math.round(amount * 100),
        frequency: "MONTHLY",
        frequency_interval: 1,
        anchor_date: new Date().toISOString().slice(0, 10),
      },
      provenance: "owner_direct",
      rationale: "Create a bill from Meridian.",
    };
  });
  attach(root.querySelector("[data-ca-top-up]"), (f) => {
    const amount = f.querySelector('input[name="amount"]').value;
    const crew = (currentPlan && currentPlan.crew_ids) || {};
    const fill = f.querySelector('input[name="bill_reserve_id"]');
    if (fill && crew.bill_reserve_id && !fill.value) {
      fill.value = crew.bill_reserve_id;
    }
    return {
      type: "top_up_crew_reserve",
      params: {
        bill_reserve_id: f.querySelector('input[name="bill_reserve_id"]').value.trim(),
        amount: amount ? Math.round(Number(amount) * 100) : 0,
        subaccount_id: crew.free_to_spend_subaccount_id || "",
      },
      provenance: "owner_direct",
      rationale: "Top up the Crew bill reserve from Meridian.",
    };
  });

  // Delete an existing autopilot rule (populate the picker from crew_ids.rules).
  const ruleForm = root.querySelector("[data-ca-delete-rule]");
  if (ruleForm) {
    populateRulePicker(ruleForm);
    attach(ruleForm, (f) => ({
      type: "delete_crew_autopilot_rule",
      params: { rule_id: f.querySelector('select[name="rule_id"]').value.trim() },
      provenance: "owner_direct",
      rationale: "Delete a Crew autopilot rule from Meridian.",
    }));
  }

  // Set the active spend pocket (pick from the known spend subaccount ids).
  const spendForm = root.querySelector("[data-ca-set-spend]");
  if (spendForm) {
    populatePocketPicker(spendForm);
    attach(spendForm, (f) => {
      const crew = (currentPlan && currentPlan.crew_ids) || {};
      return {
        type: "set_crew_spend_pocket",
        params: {
          user_id: crew.account_id || "",
          subaccount_id: f.querySelector('select[name="subaccount_id"]').value.trim(),
        },
        provenance: "owner_direct",
        rationale: "Set the active spend pocket from Meridian.",
      };
    });
  }

  // Delete a pocket (pick from the full subaccount list; destructive, confirmed).
  const delPocket = root.querySelector("[data-ca-delete-pocket]");
  if (delPocket) {
    populatePocketPicker(delPocket, true);
    attach(delPocket, (f) => ({
      type: "delete_crew_pocket",
      params: { subaccount_id: f.querySelector('select[name="subaccount_id"]').value.trim() },
      provenance: "owner_direct",
      rationale: "Delete a Crew pocket from Meridian.",
    }));
  }

  // Create a virtual debit card (uses the live user + a chosen pocket).
  const vcForm = root.querySelector("[data-ca-create-virtual-card]");
  if (vcForm) {
    populatePocketPicker(vcForm, true);
    attach(vcForm, (f) => {
      const crew = (currentPlan && currentPlan.crew_ids) || {};
      return {
        type: "create_crew_virtual_card",
        params: {
          user_id: crew.user_id || "",
          name: f.querySelector('input[name="name"]').value.trim(),
          subaccount_id: f.querySelector('select[name="subaccount_id"]').value.trim() || null,
          card_color: "TEAL",
        },
        provenance: "owner_direct",
        rationale: "Create a virtual debit card from Meridian.",
      };
    });
  }
}

/* Fill a pocket picker. With `all`, list every known subaccount (for delete);
   otherwise only the spend pockets (for set-spend). */
function populatePocketPicker(form, all = false) {
  const sel = form.querySelector('select[name="subaccount_id"]');
  if (!sel) {
    return;
  }
  const crew = (currentPlan && currentPlan.crew_ids) || {};
  const pockets = all
    ? (crew.subaccounts || [])
    : [
        { id: crew.free_to_spend_subaccount_id, name: "Free to Spend" },
        { id: crew.checking_subaccount_id, name: "Checking" },
      ].filter((p) => p.id);
  sel.replaceChildren();
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select a pocket…";
  sel.appendChild(placeholder);
  for (const pocket of pockets) {
    const opt = document.createElement("option");
    opt.value = pocket.id;
    opt.textContent = pocket.name || "Pocket";
    sel.appendChild(opt);
  }
}

/* Fill the delete-rule picker from currentPlan.crew_ids.rules. Called after
   currentPlan is populated (the rules are not known at wire time). */
function populateRulePicker(ruleForm) {
  const sel = ruleForm.querySelector('select[name="rule_id"]');
  if (!sel) {
    return;
  }
  const crew = (currentPlan && currentPlan.crew_ids) || {};
  const rules = crew.rules || [];
  sel.replaceChildren();
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select a rule…";
  sel.appendChild(placeholder);
  for (const rule of rules) {
    const opt = document.createElement("option");
    opt.value = rule.id;
    opt.textContent = rule.name || "Untitled rule";
    sel.appendChild(opt);
  }
}

document.addEventListener("meridian:workspacechange", (event) => {
  if (event.detail.workspace === "plan") {
    loadPlan();
    wireCrewActions(document);
  } else {
    closePlanInspector();
  }
});

document.addEventListener("click", (event) => {
  const newButton = event.target.closest("[data-plan-new-commitment]");
  if (newButton) {
    event.preventDefault();
    openNewCommitmentEditor();
    return;
  }
  const ruleButton = event.target.closest("[data-plan-new-rule]");
  if (ruleButton) {
    event.preventDefault();
    openAutopilotRuleEditor();
    return;
  }
  const root = document.querySelector("[data-plan-root]");
  if (!root) {
    return;
  }
  if (event.target.closest("button, a, input, select, textarea, .m-funding-editor")) {
    return;
  }
  const row = event.target.closest("[data-commitment-card]");
  if (row && currentPlan) {
    const id = Number(row.dataset.commitmentCard);
    const commitment = currentPlan.commitments.find((item) => item.id === id);
    selectedCommitment(commitment);
  }
});

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    wireCrewActions(document);
    if (window.MeridianShell && window.MeridianShell.getWorkspace() === "plan") {
      loadPlan();
    }
  });
} else {
  wireCrewActions(document);
  if (window.MeridianShell && window.MeridianShell.getWorkspace() === "plan") {
    loadPlan();
  }
}
