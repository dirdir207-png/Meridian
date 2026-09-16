/* Kit README semantic mapping, applied to a ledger row.

A row carries a merchant, a description and a category, so its framed glyph is
resolved from that text. This is presentation only: the glyph never carries meaning
the text does not, the category label beside it stays authoritative, and an
unrecognised row keeps a neutral mark.

Order matters — the first match wins — and the specific text is scanned before the
broad category. The merchant and description name the actual thing ("Internet",
"Electric") while a category is broad ("Utilities"), and the kit asks for wifi for
Internet but lightning-charge for electricity. Matching both in one pass loses that
distinction, because "Utilities" matches the electricity rule and that rule comes first.

dial.js holds the same vocabulary for Today's events and plan.js for its segments;
converging the three into this module is a worthwhile follow-up rather than part of a
bounded slice. This file deliberately has no DOM or network dependency so it can be
imported and exercised under Node.
*/

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

export function transactionIconName(transaction) {
  const safe = transaction || {};
  const text = (value) => (typeof value === "string" ? value : "");
  const passes = [
    [safe.merchant, safe.description],
    [safe.classification?.category, safe.suggested_category],
  ];
  for (const parts of passes) {
    const haystack = parts.map(text).join(" ");
    if (!haystack.trim()) continue;
    for (const [pattern, icon] of TRANSACTION_ICONS) {
      if (pattern.test(haystack)) return icon;
    }
  }
  // Money in reads as income; anything unrecognised keeps a neutral heading mark.
  return safe.amount > 0 ? "star" : "compass";
}
