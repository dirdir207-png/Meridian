import { freshnessText, meridianFetch } from "./api.js";
import { formatCurrency } from "./format.js";

const root = document.querySelector("[data-payday-root]");
let currentPayload = null;

function humanDate(value) {
  if (!value) return "—";
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { month: "long", day: "numeric" }).format(parsed);
}

function titleCase(value) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isoDay(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function yesterday() {
  /* The owner asked for the reset to start "at yesterday", so that is the default the
     control offers rather than an unset field. */
  const value = new Date();
  value.setDate(value.getDate() - 1);
  return isoDay(value);
}

function renderLearning(learning) {
  const summary = root.querySelector("[data-learning-floor-summary]");
  const input = root.querySelector("[data-learning-floor-input]");
  const status = root.querySelector("[data-learning-floor-status]");
  if (!summary) return;

  const active = Boolean(learning?.active);
  if (active) {
    summary.textContent =
      `Learning from ${humanDate(learning.floor)} onward · ${learning.included} deposits in use` +
      ` · ${learning.excluded} earlier excluded.`;
  } else {
    summary.textContent = "Learning from all of your income history.";
  }
  // Never clobber what the owner is currently typing.
  if (input && !input.value) input.value = learning?.floor || yesterday();
  if (status && active && learning.set_at) {
    status.textContent = `Set ${new Date(learning.set_at).toLocaleString()}. No records were deleted.`;
  }
}

function cadenceSourceText(cadence) {
  /* Where the cadence came from, said plainly. Before OS-104 the card reported the observed
     pattern alone, so a Crew-held paycheck left it reading "Not recognized" while the same page
     listed that paycheck's cadence further down. When Crew holds more than one record the label
     names the one it used and admits the others: a single figure must not silently stand in for
     several. */
  if (!cadence || !cadence.value) {
    return "No paycheck record in Crew and no deposit pattern yet. Set the paycheck in Crew, or let Meridian learn it from deposits.";
  }
  if (cadence.source === "crew") {
    const named = cadence.plan_name ? ` · ${cadence.plan_name}` : "";
    const others =
      cadence.distinct_cadences > 1
        ? ` (one of ${cadence.distinct_cadences} records)`
        : "";
    return `${cadence.source_label}${named}${others}`;
  }
  return `${cadence.source_label} · ${Math.round((cadence.confidence || 0) * 100)}% confidence · ${
    cadence.deposits || 0
  } deposits`;
}

function render(payload) {
  currentPayload = payload;
  const pattern = payload.pattern;
  const cadence = payload.cadence || { value: null };
  root.querySelector("[data-payday-pattern]").textContent = cadence.value
    ? titleCase(cadence.value)
    : "Not recognized";
  root.querySelector("[data-cadence-source]").textContent = cadenceSourceText(cadence);
  root.querySelector("[data-next-payday]").textContent = humanDate(pattern?.next_date);
  root.querySelector("[data-typical-income]").textContent = pattern
    ? `${formatCurrency(pattern.typical_amount, "USD")} typical income`
    : "Not projected from your deposits yet";

  const nextRun = payload.next_run;
  root.querySelector("[data-next-run-total]").textContent = nextRun
    ? formatCurrency(nextRun.total, "USD")
    : "—";
  root.querySelector("[data-next-run-date]").textContent = nextRun
    ? `${humanDate(nextRun.date)} · proposal only`
    : "Nothing to propose yet";

  const freshness = freshnessText(payload.data_freshness);
  const freshnessNode = root.querySelector("[data-payday-freshness]");
  freshnessNode.dataset.state = freshness.state;
  freshnessNode.textContent = freshness.label;

  /* OS-104 removed this pane's own per-commitment funding editor: it was a two-mode copy of the
     four-mode editor Plan already ships against the same repository and the same propose route, and
     funding a particular bill is per bill. The rules still ride in the payload -- the projection
     below uses them -- and nothing about funding behaviour changed. */

  const contributions = root.querySelector("[data-payday-contributions]");
  contributions.replaceChildren();
  for (const item of nextRun?.contributions || []) {
    const row = document.createElement("div");
    row.className = "m-payday-contribution";
    const name = document.createElement("span");
    name.textContent = item.commitment;
    const amount = document.createElement("strong");
    amount.textContent = formatCurrency(item.amount, "USD");
    row.append(name, amount);
    contributions.append(row);
  }
  if (!nextRun?.contributions?.length) {
    const empty = document.createElement("p");
    empty.className = "m-settings-empty";
    empty.textContent = "No funding contribution is projected yet.";
    contributions.append(empty);
  }

  renderLearning(payload.learning);
}

async function setLearningFloor(floor) {
  /* The learning window is a Meridian-LOCAL setting: it moves no money, deletes no
     record, and never reaches Crew. So it is posted with plain fetch, the same way the
     owner-initiated connection authorize call is, rather than through the proposal
     channel (which exists for financial proposals) or the Crew mutation helper. */
  const status = root.querySelector("[data-learning-floor-status]");
  const setButton = root.querySelector("[data-learning-floor-set]");
  const clearButton = root.querySelector("[data-learning-floor-clear]");
  setButton.disabled = true;
  clearButton.disabled = true;
  try {
    const response = await fetch("/api/meridian/settings/payday/learning-floor", {
      method: "POST",
      credentials: "same-origin",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ floor }),
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok || !payload) {
      const detail = (payload && payload.error) || {};
      status.textContent = `${detail.message || "The learning window could not be changed."} ${
        detail.recovery_action || ""
      }`.trim();
      return;
    }
    renderLearning(payload.learning);
    status.textContent = floor
      ? "Learning re-based. No records were deleted and nothing was sent to Crew."
      : "Learning from all of your income history again. No records were deleted.";
    // Re-read so the recognised schedule and its counts reflect the new window.
    render(await meridianFetch("/api/meridian/settings/payday"));
    status.textContent = floor
      ? "Learning re-based. No records were deleted and nothing was sent to Crew."
      : "Learning from all of your income history again. No records were deleted.";
  } catch (error) {
    status.textContent = `${error.message} ${error.recoveryAction || ""}`.trim();
  } finally {
    setButton.disabled = false;
    clearButton.disabled = false;
  }
}

function renderFundingPlans(payload) {
  /* Crew's funding plans, so a plan can be ADDRESSED by its id. Names come from a provider, so
     every value renders through textContent -- never innerHTML. */
  const list = root?.querySelector("[data-funding-plans]");
  if (!list) return;
  const plans = Array.isArray(payload?.funding_plans) ? payload.funding_plans : [];
  list.replaceChildren();
  if (!plans.length) {
    const empty = document.createElement("p");
    empty.className = "m-payday-note";
    empty.textContent =
      "Crew is not reporting a funding plan right now, so there is no payday cadence to set. " +
      "Meridian will offer this as soon as Crew returns one.";
    list.append(empty);
    return;
  }
  for (const plan of plans) {
    const row = document.createElement("div");
    row.className = "m-funding-plan-row";

    const identity = document.createElement("div");
    identity.className = "m-funding-plan-identity";
    const name = document.createElement("strong");
    name.textContent = plan.name || "Unnamed plan";
    /* No per-row cadence line any more. The summary card owns the cadence, resolved in the app's
       own precedence and naming the record it came from; two cadence displays from two sources was
       the inconsistency the owner reported (OS-104). This row says which record it is and what it
       pays, which is what its control needs. */
    identity.append(name);

    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.className = "m-funding-plan-amount";
    input.dataset.fundingPlanAmount = "";
    input.value = plan.amount === null || plan.amount === undefined ? "" : String(plan.amount);
    input.setAttribute("aria-label", `Payday amount for ${plan.name || "this plan"}`);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "m-primary-button";
    button.dataset.fundingPlanSet = plan.id || "";
    button.textContent = "Set in Crew";

    button.addEventListener("click", () => setFundingPlan(plan.id, input.value, button));

    row.append(identity, input, button);
    list.append(row);
  }
}

async function setFundingPlan(planId, rawAmount, button) {
  /* A real Crew write, so it goes through the existing action pipeline rather than a bespoke
     route: POST /api/actions/mutate with provenance owner_direct. The ROUTER decides what happens
     -- a direct, fully-specified owner edit executes; anything interpreted, composed or
     low-confidence becomes a proposal -- so this reports whichever actually occurred instead of
     assuming success. Never retried: an uncertain financial mutation must not be repeated. */
  const status = root.querySelector("[data-funding-plan-status]");
  const amount = Number(String(rawAmount ?? "").trim());
  if (!planId) {
    status.textContent = "That plan has no Crew id, so it cannot be set.";
    return;
  }
  if (!Number.isFinite(amount) || amount <= 0) {
    status.textContent = "Enter the payday amount as a number greater than zero.";
    return;
  }
  button.disabled = true;
  try {
    const response = await fetch("/api/actions/mutate", {
      method: "POST",
      credentials: "same-origin",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "update_crew_paycheck_funding_plan",
        params: { fundingPlanId: planId, amount },
        provenance: "owner_direct",
        rationale: "owner set the payday amount directly in Settings",
      }),
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok || !payload) {
      const detail = (payload && payload.error) || {};
      status.textContent = `${
        detail.message || "The payday amount could not be set."
      } ${detail.recovery_action || ""}`.trim();
      return;
    }
    if (payload.routing_direct) {
      status.textContent =
        "Set in Crew. Meridian reads Crew back before treating it as confirmed, so this may show " +
        "as pending until that read completes.";
    } else {
      status.textContent =
        "That change needs your approval, so it is waiting in Pending Actions. Nothing has " +
        "reached Crew yet.";
    }
    renderFundingPlans(await meridianFetch("/api/meridian/settings/payday"));
  } catch (error) {
    status.textContent = `${error.message} ${error.recoveryAction || ""}`.trim();
  } finally {
    button.disabled = false;
  }
}

async function load() {
  if (!root) return;
  try {
    const payload = await meridianFetch("/api/meridian/settings/payday");
    render(payload);
    renderFundingPlans(payload);
  } catch (error) {
    const errorBox = root.querySelector("[data-payday-error]");
    errorBox.textContent = `${error.message} ${error.recoveryAction || ""}`.trim();
    errorBox.hidden = false;
  }
}

root?.querySelector("[data-learning-floor-set]")?.addEventListener("click", () => {
  const input = root.querySelector("[data-learning-floor-input]");
  const value = input?.value || "";
  if (!value) {
    root.querySelector("[data-learning-floor-status]").textContent =
      "Choose the date your new pay history starts.";
    return;
  }
  setLearningFloor(value);
});
root?.querySelector("[data-learning-floor-clear]")?.addEventListener("click", () => {
  setLearningFloor(null);
});
load();
