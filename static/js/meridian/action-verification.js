/* Honest rendering of the durable post-execution verification receipt.
 *
 * The action pipeline stores a verification receipt in two places:
 *   - `action.verification`        when a readback verifier confirmed the write
 *                                  (state `verified`, ActionStore.mark_verified)
 *   - `action.result.verification` when the write was accepted but the receipt is
 *                                  pending, unconfirmed, or a confirmed mismatch
 *                                  (states `executed` / `failed`, result_json)
 *
 * An action with no receipt at all has no registered verifier: the provider
 * accepted the write and the resulting state is unconfirmed. That is reported as
 * such, never as a success.
 *
 * This module is presentational only. It never approves, executes, or resubmits
 * anything, and it never infers a receipt that was not recorded.
 */

const NO_VERIFIER = {
  ok: null,
  check: "no-verifier-registered",
  provider_truth: false,
  retry_allowed: false,
  reason: "No readback verifier is registered for this action type.",
};

function receiptFor(action = {}) {
  const direct = action.verification;
  if (direct && typeof direct === "object") {
    return direct;
  }
  const nested = action.result && typeof action.result === "object" ? action.result.verification : null;
  if (nested && typeof nested === "object") {
    return nested;
  }
  return null;
}

/* Describe a receipt without inventing any field it does not carry.
 *
 * `ok` is deliberately tri-state: true (confirmed), false (provider-confirmed
 * mismatch or failure), null (accepted but unconfirmed). `null` must never be
 * rendered as a success or a failure. */
export function summarizeVerification(action = {}) {
  const recorded = receiptFor(action);
  const receipt = recorded || NO_VERIFIER;
  const confirmed = receipt.ok === true;
  const contradicted = receipt.ok === false;
  const unresolved = !confirmed && !contradicted;

  let headline;
  if (confirmed) {
    headline = "Provider readback confirmed this change.";
  } else if (contradicted) {
    headline = "Provider readback contradicted this change.";
  } else if (recorded) {
    headline = "The provider accepted this change, but the readback could not confirm it. Do not resubmit it.";
  } else {
    headline = "No readback verifier is registered, so the resulting state is unconfirmed. Do not resubmit it.";
  }

  return {
    recorded: Boolean(recorded),
    outcome: confirmed ? "confirmed" : contradicted ? "contradicted" : "unresolved",
    ok: receipt.ok === undefined ? null : receipt.ok,
    check: receipt.check || "unknown",
    providerTruth: receipt.provider_truth === true,
    retryAllowed: receipt.retry_allowed === true,
    reason: receipt.reason || "No reason was recorded.",
    requested: receipt.requested,
    observed: receipt.observed,
    headline,
  };
}

function detailRows(summary) {
  const rows = [
    ["Check", summary.check],
    ["Provider truth", String(summary.providerTruth)],
    ["Retry allowed", String(summary.retryAllowed)],
    ["Reason", summary.reason],
  ];
  if (summary.requested !== undefined && summary.requested !== null) {
    rows.push(["Requested", JSON.stringify(summary.requested)]);
  }
  if (summary.observed !== undefined && summary.observed !== null) {
    rows.push(["Observed", JSON.stringify(summary.observed)]);
  }
  return rows;
}

export function renderActionVerification(action, documentRef = document) {
  const summary = summarizeVerification(action);
  const section = documentRef.createElement("section");
  section.className = "m-action-verification";
  section.dataset.verificationOutcome = summary.outcome;
  section.setAttribute("aria-label", "Post-execution verification receipt");

  const heading = documentRef.createElement("h4");
  heading.textContent = "Verification";
  section.appendChild(heading);

  const headline = documentRef.createElement("p");
  headline.className = "m-action-verification-headline";
  headline.textContent = summary.headline;
  section.appendChild(headline);

  const grid = documentRef.createElement("dl");
  grid.className = "m-action-review-grid";
  for (const [term, value] of detailRows(summary)) {
    const dt = documentRef.createElement("dt");
    dt.textContent = term;
    const dd = documentRef.createElement("dd");
    dd.textContent = value;
    grid.append(dt, dd);
  }
  section.appendChild(grid);
  return section;
}

if (typeof window !== "undefined") {
  window.MeridianActionVerification = { summarizeVerification, renderActionVerification };
}
