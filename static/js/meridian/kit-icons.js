/* The kit's own mapping is the authority: design/observatory-extension-2026-09-18/
   icon-map.json. Keep these tables in step with it. Only names that exist under
   KIT_ICON_ROOT may appear here -- a name without an asset renders an EMPTY ring,
   which reads as a broken icon rather than a deliberate one. `bank` was exactly
   that: mapped here, absent from the kit, and invisible wherever it resolved. */
export const KIT_ICON_ROOT =
  "/static/img/meridian/observatory/kit-2026-09-18/icons";

/* Decorative merchant hints, used only when nothing has been classified. They
   name the MERCHANT, never the category: the authoritative category line stays
   "No category suggested yet" while the ring shows a basket or a fork. Specific
   brands precede generic words so "Dollar General" is groceries, not a bank. */
const TRANSACTION_ICONS = [
  [/(electric|power|utilit|energy|gas|water|sewer)/i, "lightning-charge"],
  [/(internet|wifi|broadband|fibre|fiber|wireless|phone|mobile|verizon|at&t|t-mobile)/i, "wifi"],
  [/(rent|mortgage|housing|landlord)/i, "house"],
  [/(grocer|supermarket|market|general store|dollar general|aldi|kroger|safeway|costco|trader joe|whole foods|food lion|publix)/i, "basket"],
  [/(restaurant|cafe|coffee|diner|grill|kitchen|deli|bakery|pizza|burger|taco|sushi|noodle|lunch|wendy|mcdonald|chipotle|subway|starbucks|dunkin|doordash|grubhub|ubereats)/i, "fork-knife"],
  [/(transit|transport|bus|train|metro|commut|fuel|petrol|shell|exxon|chevron|circle k|wawa|speedway)/i, "bus-front"],
  [/(stream|entertain|game|gaming|hobby|steam|spotify|netflix|xbox|playstation|hulu|disney)/i, "controller"],
  [/(locksmith|keyme|\bkeys?\b)/i, "key"],
  [/(reserve|savings|bank|transfer|credit union)/i, "piggy-bank"],
  [/(household|family|people|connection)/i, "people"],
  [/(insurance|alert|notification)/i, "bell"],
  [/(income|paycheck|salary|payroll|deposit|interest|refund)/i, "star"],
  [/(goal|target)/i, "flag"],
];

/* What the kit draws when nothing is known yet: the concept's own scroll-with-a-
   question glyph, not a bare generic circle. */
const UNKNOWN_ICON = "question-circle";

export function kitIconUrl(name) {
  return `url("${KIT_ICON_ROOT}/${name}.svg")`;
}

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
  // A suggested category is already a category claim, so its icon follows it.
  if (categoryIsAssigned(safe.suggested_category)) {
    return CATEGORY_ICONS[safe.suggested_category.trim().toLowerCase()] || "tag";
  }
  // NOTHING is classified or suggested. The row's ring still identifies the
  // MERCHANT, which is data the payload already carries, while the category line
  // continues to state that no category is known. Only a merchant the kit cannot
  // name at all falls back to the concept's question glyph -- previously EVERY
  // unclassified row returned that glyph, so all 62 kit icons stayed unused and
  // the list read as a wall of identical question marks.
  const text = [safe.merchant, safe.description].filter(v => typeof v === "string").join(" ");
  if (text.trim()) {
    for (const [pattern, icon] of TRANSACTION_ICONS) {
      if (pattern.test(text)) return icon;
    }
  }
  return UNKNOWN_ICON;
}

/* Names the kit has no asset for render an empty ring, so the mapping is checked
   against the shipped set rather than trusted. Kept here so a test can assert it. */
export const ICON_NAMES = Object.freeze({
  category: Object.values(CATEGORY_ICONS),
  action: Object.values(ACTION_ICONS),
  merchant: TRANSACTION_ICONS.map(([, icon]) => icon),
  unknown: [UNKNOWN_ICON],
});
