/* Category semantics take precedence over decorative merchant guesses. */
const TRANSACTION_ICONS = [
  [/(electric|power|utilit|energy|gas|water|sewer)/i, "lightning-charge"],
  [/(internet|wifi|broadband|fibre|fiber|wireless|phone|mobile)/i, "wifi"],
  [/(rent|mortgage|housing|landlord)/i, "house"],
  [/(grocer|food|market|restaurant|cafe|coffee)/i, "basket"],
  [/(transit|transport|bus|train|metro|commut|fuel|petrol)/i, "bus-front"],
  [/(stream|entertain|game|gaming|hobby|steam|spotify|netflix|xbox|playstation)/i, "controller"],
  [/(reserve|savings|bank|transfer)/i, "bank"],
  [/(household|family|people|connection)/i, "people"],
  [/(insurance|alert|notification)/i, "bell"],
  [/(income|paycheck|salary|payroll|deposit|interest|refund)/i, "star"],
  [/(goal|target)/i, "flag"],
];

export const CATEGORY_ICONS = Object.freeze({
  groceries: "basket", dining: "fork-knife", coffee: "cup-hot", gas: "fuel-pump",
  transport: "bus-front", shopping: "bag", entertainment: "controller", travel: "airplane",
  utilities: "lightning-charge", internet: "wifi", phone: "phone", rent: "house",
  subscriptions: "arrow-repeat", health: "heart-pulse", fitness: "activity",
  insurance: "shield-check", transfers: "arrow-left-right", "personal care": "scissors",
  home: "tools", education: "mortarboard", fees: "receipt", pets: "heart",
  gifts: "gift", charity: "balloon-heart", taxes: "receipt", income: "cash-stack",
  refunds: "arrow-counterclockwise", reimbursements: "people", savings: "piggy-bank",
  recurring: "arrow-repeat", other: "tag",
});

export const ACTION_ICONS = Object.freeze({
  confirmCategory: "check-circle", correctCategory: "pencil-square", chooseCategory: "tag",
  reviewProposal: "file-earmark-check", funding: "piggy-bank", transfer: "arrow-left-right",
  schedule: "calendar-check", permission: "shield-check", evidence: "journal-text",
  needsReview: "exclamation-triangle", awaitingVerification: "hourglass-split",
  failed: "x-circle", history: "clock-history",
});

export function categoryIsAssigned(value) {
  return typeof value === "string" && !["", "uncategorized", "unassigned"].includes(value.trim().toLowerCase());
}

export function transactionIconName(transaction) {
  const safe = transaction || {};
  const classification = safe.classification || {};
  const category = (classification.category || "").trim().toLowerCase();
  // Owner classifications always control their icon, including custom categories.
  if (categoryIsAssigned(category)) {
    if (category === "utilities" && classification.method !== "user_rule") {
      const detail = `${safe.merchant || ""} ${safe.description || ""}`;
      if (/internet|wifi|broadband|fibre|fiber/i.test(detail)) return "wifi";
    }
    return CATEGORY_ICONS[category] || "tag";
  }
  // Explicitly unknown classification must not acquire certainty from decoration.
  if (category) return "question-circle";
  if (categoryIsAssigned(safe.suggested_category)) {
    return CATEGORY_ICONS[safe.suggested_category.trim().toLowerCase()] || "tag";
  }
  // Legacy unclassified fixture rows retain semantic descriptors until classified.
  const text = [safe.merchant, safe.description].filter(v => typeof v === "string").join(" ");
  for (const [pattern, icon] of TRANSACTION_ICONS) {
    if (pattern.test(text)) return icon;
  }
  return "question-circle";
}
