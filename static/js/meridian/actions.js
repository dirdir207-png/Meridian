/* Read-only Settings action history for the Observatory surface. */

import { MeridianApiError, meridianFetch } from "./api.js";
import { renderActionReviewDetails } from "./action-review.js";
import { renderActionVerification } from "./action-verification.js";

const root = document.querySelector("[data-actions-root]");

const LABELS = {
  proposed: "Proposed",
  approved: "Approved",
  executing: "Executing",
  executed: "Executed",
  verified: "Verified",
  rejected: "Rejected",
  expired: "Expired",
  failed: "Failed",
};

function titleCase(value) {
  return String(value || "Action")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function stateLabel(state) {
  return LABELS[state] || titleCase(state);
}

function formatTimestamp(value) {
  if (!value) {
    return "—";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function render(actions) {
  const history = root.querySelector("[data-action-history]");
  const empty = root.querySelector("[data-actions-empty]");
  history.querySelectorAll("[data-action-card]").forEach((node) => node.remove());
  empty.hidden = actions.length > 0;
  for (const action of actions) {
    const card = document.createElement("article");
    card.className = "m-action-card";
    card.dataset.actionCard = action.id;
    card.dataset.state = action.state || "unknown";

    const head = document.createElement("div");
    head.className = "m-action-card-head";
    const type = document.createElement("strong");
    type.className = "m-action-type";
    type.textContent = titleCase(action.type);
    const state = document.createElement("span");
    state.className = "m-action-state";
    state.dataset.state = action.state || "unknown";
    state.textContent = stateLabel(action.state);
    head.append(type, state);

    const rationale = document.createElement("p");
    rationale.className = "m-action-rationale";
    rationale.textContent = action.rationale || "No rationale recorded.";

    const meta = document.createElement("p");
    meta.className = "m-action-meta";
    const requested = action.requested_by ? `Requested by ${action.requested_by}` : "Owner";
    const created = formatTimestamp(action.created_at);
    const decided = action.decided_at ? ` · decided ${formatTimestamp(action.decided_at)}` : "";
    meta.textContent = `${requested} · ${created}${decided}`;

    card.append(
      head,
      rationale,
      meta,
      renderActionVerification(action),
      renderActionReviewDetails(action),
    );
    history.appendChild(card);
  }
}

async function load() {
  if (!root) {
    return;
  }
  const errorBox = root.querySelector("[data-actions-error]");
  errorBox.hidden = true;
  root.setAttribute("aria-busy", "true");
  try {
    const payload = await meridianFetch("/api/meridian/actions");
    render(payload.actions || []);
  } catch (error) {
    errorBox.textContent =
      error instanceof MeridianApiError
        ? `${error.message} ${error.recoveryAction}`
        : "Action history could not be loaded.";
    errorBox.hidden = false;
  } finally {
    root.removeAttribute("aria-busy");
  }
}

root?.querySelector("[data-actions-refresh]")?.addEventListener("click", load);
load();

window.MeridianActions = { load };
