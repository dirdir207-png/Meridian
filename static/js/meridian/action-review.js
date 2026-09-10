/* Exact, privacy-safe review details for durable action records.

   This renders only evidence actually stored on the action. Missing reviewed
   before/after or preserved-field evidence is labelled as not recorded; it is
   never inferred from a rationale or from the requested parameters. */

const SECRET_KEY = /(?:authorization|bearer|cookie|credential|password|passcode|secret|session|token|api[_-]?key)/i;

function scalar(value) {
  if (value === null) return "null";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function flatten(value, prefix = "", output = []) {
  if (prefix && SECRET_KEY.test(prefix.split(".").at(-1))) {
    output.push({ path: prefix, value: "[redacted]" });
    return output;
  }
  if (Array.isArray(value)) {
    if (value.length === 0 && prefix) output.push({ path: prefix, value: "[]" });
    value.forEach((item, index) => flatten(item, `${prefix}[${index}]`, output));
    return output;
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value);
    if (entries.length === 0 && prefix) output.push({ path: prefix, value: "{}" });
    entries.forEach(([key, item]) => flatten(item, prefix ? `${prefix}.${key}` : key, output));
    return output;
  }
  if (prefix) output.push({ path: prefix, value: scalar(value) });
  return output;
}

function firstRecorded(...values) {
  return values.find((value) => value !== undefined && value !== null);
}

export function reviewActionDetails(action = {}) {
  const params = action.params && typeof action.params === "object" ? action.params : {};
  const {
    reviewed_before: _reviewedBefore,
    before: _before,
    reviewed_after: _reviewedAfter,
    after: _after,
    preserved_fields: _preservedFields,
    reviewed_preserved_fields: _reviewedPreservedFields,
    ...operationParams
  } = params;
  const before = firstRecorded(action.reviewed_before, action.before, params.reviewed_before, params.before);
  const after = firstRecorded(action.reviewed_after, action.after, params.reviewed_after, params.after);
  const preserved = firstRecorded(
    action.preserved_fields,
    action.reviewed_preserved_fields,
    params.preserved_fields,
    params.reviewed_preserved_fields,
  );
  const beforeRecorded = before !== undefined && after !== undefined;
  const preservedRecorded = preserved !== undefined;
  return {
    parameters: flatten(operationParams),
    before: beforeRecorded ? flatten(before) : [],
    after: beforeRecorded ? flatten(after) : [],
    preserved: preservedRecorded ? flatten(preserved) : [],
    beforeAfterStatus: beforeRecorded
      ? "Reviewed before/after evidence recorded."
      : "Reviewed before/after evidence not recorded for this action.",
    preservedStatus: preservedRecorded
      ? "Preserved-field evidence recorded."
      : "Preserved-field evidence not recorded for this action.",
  };
}

function addRows(documentRef, host, rows) {
  for (const item of rows) {
    const term = documentRef.createElement("dt");
    term.textContent = item.path;
    const detail = documentRef.createElement("dd");
    detail.textContent = item.value;
    host.append(term, detail);
  }
}

function addEvidenceSection(documentRef, host, label, rows, status) {
  const heading = documentRef.createElement("h4");
  heading.textContent = label;
  host.appendChild(heading);
  if (rows.length) {
    const grid = documentRef.createElement("dl");
    grid.className = "m-action-review-grid";
    addRows(documentRef, grid, rows);
    host.appendChild(grid);
  }
  const notice = documentRef.createElement("p");
  notice.className = "m-action-review-notice";
  notice.textContent = status;
  host.appendChild(notice);
}

export function renderActionReviewDetails(action, documentRef = document) {
  const review = reviewActionDetails(action);
  const section = documentRef.createElement("section");
  section.className = "m-action-review";
  section.setAttribute("aria-label", "Recorded action review details");

  const heading = documentRef.createElement("h3");
  heading.textContent = "Recorded request parameters";
  section.appendChild(heading);

  if (review.parameters.length) {
    const grid = documentRef.createElement("dl");
    grid.className = "m-action-review-grid";
    addRows(documentRef, grid, review.parameters);
    section.appendChild(grid);
  } else {
    const empty = documentRef.createElement("p");
    empty.className = "m-action-review-notice";
    empty.textContent = "No request parameters were recorded.";
    section.appendChild(empty);
  }

  addEvidenceSection(documentRef, section, "Reviewed before state", review.before, review.beforeAfterStatus);
  if (review.after.length) addEvidenceSection(documentRef, section, "Reviewed after state", review.after, "Reviewed after-state evidence recorded.");
  addEvidenceSection(documentRef, section, "Preserved fields", review.preserved, review.preservedStatus);
  return section;
}

if (typeof window !== "undefined") {
  window.MeridianActionReview = { reviewActionDetails, renderActionReviewDetails };
}
