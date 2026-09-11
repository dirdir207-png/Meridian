/**
 * Provenance labels for accounts a complete provider read concluded are gone.
 *
 * An archived account keeps its row and its history; it only stops being a
 * current observation. This module turns that record into honest labels: what
 * happened, when it was last observed, and how much history survives — and it
 * deliberately exposes no amount, because a last known balance is not a current
 * one.
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

function countTransactions(value) {
  const count = Number(value);
  return Number.isFinite(count) && count > 0 ? Math.floor(count) : 0;
}

export function describeArchivedAccount(account) {
  if (!account || typeof account !== "object") {
    throw new TypeError("describeArchivedAccount needs an archived account record");
  }
  const provider = titleCase(account.provider);
  const observed = dateOnly(account.last_observed_at);
  const concluded = dateOnly(account.absent_since);
  const transactions = countTransactions(account.retained_transactions);

  let history;
  if (transactions === 1) history = "1 transaction kept in Activity";
  else if (transactions > 1) history = `${transactions} transactions kept in Activity`;
  else history = "No transactions are recorded for it";

  return {
    name: String(account.name || "Account"),
    source: provider
      ? `${provider} no longer returns this account`
      : "Provider no longer returns this account",
    observed: observed ? `Last observed ${observed}` : "No observation is recorded",
    absent: concluded ? `Concluded absent ${concluded}` : "Concluded absent",
    history,
  };
}

/**
 * The account label for one transaction row.
 *
 * A transaction recorded under an account the provider later stopped returning
 * is history, so its row says so rather than implying the account is current.
 * An unknown account yields no label at all: absence cannot be claimed for an
 * account this build cannot name.
 */
export function describeTransactionAccount(transaction) {
  const name = String((transaction && transaction.account_name) || "").trim();
  const archived = Boolean(name) && Boolean(transaction && transaction.account_archived);
  return {
    name,
    archived,
    note: archived ? "no longer returned by this provider" : "",
  };
}
