/**
 * Provenance labels for bills a complete provider read concluded are gone.
 *
 * An absent bill keeps its row and its history; it only stops being a current
 * obligation. This module turns that record into honest labels — what happened
 * and when it was concluded — and it deliberately exposes no amount, because a
 * last known figure is not a current obligation and there is nothing here the
 * owner could change.
 *
 * Pure functions only, so the labels can be executed in tests without a browser.
 */

function titleCase(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function dateOnly(isoTimestamp) {
  const text = String(isoTimestamp || "");
  const match = text.match(/^(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : "";
}

export function describeAbsentBill(bill) {
  if (!bill || typeof bill !== "object") {
    throw new TypeError("describeAbsentBill needs an absent bill record");
  }
  const provider = titleCase(bill.provider);
  const concluded = dateOnly(bill.absent_since);

  return {
    name: String(bill.name || "Bill"),
    source: provider
      ? `${provider} no longer returns this bill`
      : "Provider no longer returns this bill",
    absent: concluded ? `Concluded absent ${concluded}` : "Concluded absent",
    note: "Its history is kept and no money is scheduled for it",
  };
}
