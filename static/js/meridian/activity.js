/* Activity workspace: a stable, date-grouped ledger with cursor pagination. */

import { MeridianApiError, activityBannerCopy, meridianFetch } from "./api.js";
import { describeTransactionAccount } from "./archived-accounts.js";
import { dayDividerLabel, dayKey, dayLabel, formatCurrency } from "./format.js";
import { ACTION_ICONS, categoryIsAssigned, kitIconUrl, transactionIconName } from "./kit-icons.js";

const state = {
  cursor: null,
  accountId: null,
  category: "",
  mode: "timeline",
  controller: null,
  accountsLoaded: false,
};

/* Show an explicit sign so income reads "+$" and spend reads "−$", matching the
   atlas. formatCurrency keeps the locale grouping; we only add the sign. */
/* One review control, built the same way every time: the kit's action glyph inside a
   masked span (so it inherits currentColor), the label as real text, and the data
   attribute the existing click handlers already look for. */
function reviewAction({ className, dataAttribute, icon, label }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `m-button ${className}`;
  button.dataset[dataAttribute] = "";
  const glyph = document.createElement("span");
  glyph.className = "m-review-action-icon";
  glyph.setAttribute("aria-hidden", "true");
  glyph.style.setProperty("--m-review-action-icon", kitIconUrl(icon));
  const text = document.createElement("span");
  text.textContent = label;
  button.append(glyph, text);
  return button;
}

function signedAmount(amount, currency) {
  const sign = amount < 0 ? "\u2212" : "+";
  return `${sign}${formatCurrency(Math.abs(amount), currency)}`;
}

function buildRow(transaction) {
  const row = document.createElement("div");
  row.className = "m-transaction-row";
  row.dataset.transactionRow = "";
  row.dataset.transactionId = String(transaction.id);
  row.dataset.kind = transaction.amount < 0 ? "spend" : "income";
  row.dataset.classificationCategory = transaction.classification?.category || "";
  row.setAttribute("role", "button");
  row.setAttribute("tabindex", "0");
  row.setAttribute(
    "aria-label",
    `${transaction.merchant || transaction.description}, ${formatCurrency(
      transaction.amount,
      transaction.currency
    )}. Open details.`
  );

  const left = document.createElement("span");
  left.className = "m-row-text";
  const title = document.createElement("span");
  title.className = "m-row-title";
  title.setAttribute("data-row-description", "");
  title.textContent =
    transaction.merchant || transaction.description || `Transaction ${transaction.id}`;
  const sub = document.createElement("span");
  sub.className = "m-row-sub";
  const accountView = describeTransactionAccount(transaction);
  sub.textContent =
    transaction.merchant && transaction.description
      ? transaction.description
      : (transaction.provider || "");
  if (accountView.name) {
    const account = document.createElement("span");
    account.className = "m-row-account";
    account.dataset.rowAccount = "";
    account.textContent = accountView.note
      ? `${accountView.name} \u00b7 ${accountView.note}`
      : accountView.name;
    if (sub.textContent) sub.append(" \u00b7 ");
    sub.append(account);
    row.dataset.accountArchived = accountView.archived ? "true" : "false";
  }
  left.append(title, sub);

  const category = document.createElement("span");
  category.className = "m-row-category";
  category.setAttribute("data-row-category", "");
  category.textContent =
    transaction.classification?.category || "Unassigned";

  const amount = document.createElement("span");
  amount.className = `m-row-amount ${
    transaction.amount < 0 ? "is-spend" : "is-income"
  }`;
  amount.textContent = signedAmount(transaction.amount, transaction.currency);

  row.append(left, category, amount);

  // Concept 03 closes every timeline row with a trailing chevron. It is a typographic
  // affordance -- the kit ships no chevron glyph, and a decorative mark is not artwork
  // to be engraved -- and it is hidden from assistive tech because the row already
  // announces itself as "Open details" and a second cue would only repeat that.
  if (state.mode !== "review") {
    const chevron = document.createElement("span");
    chevron.className = "m-row-chevron";
    chevron.setAttribute("aria-hidden", "true");
    chevron.textContent = "\u203a";
    row.append(chevron);
  }

  // Concept 03 frames each row's category glyph in a ring with a small marker dot.
  // Decorative: the icon is masked and hidden from assistive tech, while the real
  // category text below stays authoritative. Built in BOTH modes -- the timeline
  // previously had no glyph at all, so only the Review tab ever showed one and the
  // ledger read as unadorned text next to a concept full of kit art.
  const glyph = document.createElement("span");
  glyph.className = "m-review-glyph";
  glyph.setAttribute("aria-hidden", "true");
  const glyphIcon = document.createElement("span");
  glyphIcon.className = "m-review-glyph-icon";
  glyphIcon.style.setProperty(
    "--m-review-icon",
    kitIconUrl(transactionIconName(transaction))
  );
  glyph.appendChild(glyphIcon);
  row.prepend(glyph);

  if (state.mode === "review") {
    // Card layout: name + amount on top, merchant·date·account line, an orange
    // attention dot + category/confidence line, then two pill actions.
    row.classList.add("m-review-card");
    row.removeAttribute("role");
    row.removeAttribute("tabindex");

    // Merchant · date · account sub-line.
    const date = dayLabel(transaction.occurred_at);
    const account = accountView.note
      ? `${accountView.name} \u00b7 ${accountView.note}`
      : accountView.name;
    const meta = document.createElement("div");
    meta.className = "m-review-meta";
    meta.textContent = [
      transaction.merchant || transaction.description || "Transaction",
      date,
      account,
    ]
      .filter(Boolean)
      .join(" · ");

    // Category / confidence with an orange attention dot.
    const cat = document.createElement("div");
    cat.className = "m-review-category";
    const dot = document.createElement("span");
    dot.className = "m-review-dot";
    const confidence = transaction.classification?.confidence || 0;
    const hasCategory = categoryIsAssigned(transaction.classification?.category);
    const suggested = categoryIsAssigned(transaction.suggested_category) ? transaction.suggested_category : "";
    // Expose the smart guess to the inline editor via a data attribute.
    if (suggested) {
      row.dataset.suggestedCategory = suggested;
    }
    // Ranked category options (suggestion first + merchant history + defaults).
    if (Array.isArray(transaction.category_options) && transaction.category_options.length) {
      row.dataset.categoryOptions = JSON.stringify(transaction.category_options);
    }
    const catLabel = hasCategory
      ? transaction.classification.category
      : suggested
        ? `Suggested: ${suggested}`
        : "No category suggested yet";
    const catText = document.createElement("span");
    catText.dataset.confidenceLabel = "";
    catText.textContent = `${catLabel} · ${Math.round(confidence * 100)}% confidence`;
    cat.append(dot, catText);

    const actions = document.createElement("div");
    actions.className = "m-review-actions";
    // Concept 03 gives a row with nothing to confirm ONE filled control -- "Choose
    // category" -- and no disabled button beside it. The previous markup rendered a
    // greyed, disabled Needs-category control next to a quiet Choose-category one, so
    // the row's only available action was the least prominent thing on it and the row
    // read as broken. The concept instead makes the thing the owner CAN do the
    // primary action.
    const confirmable = hasCategory || suggested;
    if (confirmable) {
      const target = hasCategory ? transaction.classification.category : suggested;
      actions.append(
        reviewAction({
          className: "m-review-approve",
          dataAttribute: "reviewApprove",
          icon: ACTION_ICONS.confirmCategory,
          label: `Confirm ${target}`,
        }),
        reviewAction({
          className: "m-button--quiet m-review-correct",
          dataAttribute: "reviewCorrect",
          icon: ACTION_ICONS.correctCategory,
          label: "Change",
        })
      );
    } else {
      // Still `data-review-correct`, so the existing handler opens the category
      // editor exactly as before; only the emphasis changes.
      actions.append(
        reviewAction({
          className: "m-review-choose",
          dataAttribute: "reviewCorrect",
          icon: ACTION_ICONS.chooseCategory,
          label: "Choose category",
        })
      );
    }

    // Wrap the header (name + amount) for the card's top line.
    const header = document.createElement("div");
    header.className = "m-review-header";
    const select = document.createElement("label");
    select.className = "m-review-select";
    select.setAttribute("aria-label", `Review ${transaction.merchant || "transaction"}`);
    const check = document.createElement("input");
    check.type = "checkbox";
    check.dataset.reviewSelect = "";
    select.appendChild(check);
    const name = document.createElement("span");
    name.className = "m-review-name";
    name.textContent = transaction.merchant || transaction.description || `Transaction ${transaction.id}`;
    const amountEl = document.createElement("span");
    amountEl.className = `m-review-amount ${transaction.amount < 0 ? "is-spend" : "is-income"}`;
    amountEl.textContent = signedAmount(transaction.amount, transaction.currency);

    header.append(glyph, name, select, amountEl);
    name.classList.add("m-review-grow");

    row.replaceChildren(header, meta, cat, actions);
  }
  return row;
}

/* Concept 03's day divider: the day's name bound to its short date, a hairline rule
   that runs to the edge, and a four-pointed star at the rule's end. The rule and the
   star are decorative and stay out of the accessibility tree; the label carries the
   heading's meaning on its own.

   The divider's moon/sun marker is NOT built here yet: the kit ships a crescent
   (`moon.svg`) but no sunburst, and the concept puts a sunburst on every older day.
   Rather than approximate artwork the handoff forbids approximating, the marker slot is
   left for the missing asset. */
function dayHeading(isoTimestamp) {
  const heading = document.createElement("h2");
  heading.className = "m-day-heading";
  const label = document.createElement("span");
  label.className = "m-day-heading-label";
  label.textContent = dayDividerLabel(isoTimestamp);
  const rule = document.createElement("span");
  rule.className = "m-day-heading-rule";
  rule.setAttribute("aria-hidden", "true");
  const star = document.createElement("span");
  star.className = "m-day-heading-star";
  star.setAttribute("aria-hidden", "true");
  heading.append(label, rule, star);
  return heading;
}

function groupFor(ledger, isoTimestamp) {
  const key = dayKey(isoTimestamp);
  let group = ledger.querySelector(`[data-day-group][data-day-key="${key}"]`);
  if (!group) {
    group = document.createElement("section");
    group.className = "m-day-group";
    group.dataset.dayGroup = "";
    group.dataset.dayKey = key;
    const heading = dayHeading(isoTimestamp);
    const list = document.createElement("div");
    list.className = "m-day-rows";
    group.append(heading, list);

    // Insert newest day first.
    const existing = [...ledger.querySelectorAll("[data-day-group]")];
    const anchor = existing.find((candidate) => candidate.dataset.dayKey < key);
    if (anchor) {
      ledger.insertBefore(group, anchor);
    } else {
      ledger.appendChild(group);
    }
  }
  return group.querySelector(".m-day-rows");
}

function setChip(root, freshness) {
  const chip = root.querySelector("[data-freshness]");
  chip.dataset.state = freshness ? (freshness.status || "unavailable") : "unavailable";
  const labels = { fresh: "Fresh", stale: "Stale", unavailable: "Not connected" };
  chip.textContent = labels[chip.dataset.state] || chip.dataset.state;
}

/* Concept 03's parchment banner. The copy comes from `activityBannerCopy`, which
   returns null when nothing has been observed, so an unconnected ledger shows no
   headline claiming an order it has not seen. The timeline owns this surface; Review
   owns the decision strip, so the two never stack. */
function setActivityBanner(root, freshness) {
  const banner = root.querySelector("[data-activity-banner]");
  if (!banner) {
    return;
  }
  const copy = activityBannerCopy(freshness);
  if (copy) {
    const title = banner.querySelector("[data-activity-banner-title]");
    const meta = banner.querySelector("[data-activity-banner-meta]");
    if (title) title.textContent = copy.title;
    if (meta) meta.textContent = copy.meta;
  }
  banner.hidden = copy === null || state.mode !== "timeline";
}

/* The Review tab's badge and the parchment strip are ONE number, supplied by the
   API as `review_count`. It is the size of the queue the Review tab lists, so the
   figure cannot disagree with the rows beneath it. Zero hides both rather than
   inviting the owner to look for nothing. */
function setReviewCount(root, count) {
  const value = Number.isFinite(count) && count > 0 ? Math.trunc(count) : 0;
  const plural = value === 1 ? "decision" : "decisions";

  const badge = root.querySelector("[data-review-count]");
  if (badge) {
    badge.textContent = String(value);
    badge.hidden = value === 0;
    // The badge is decorative inside the tab, so the tab's own name carries the
    // figure to assistive tech instead of leaving a bare "Review 3".
    const tab = badge.closest("[data-activity-mode]");
    if (tab) {
      if (value > 0) {
        tab.setAttribute("aria-label", `Review, ${value} ${plural} to review`);
      } else {
        tab.removeAttribute("aria-label");
      }
    }
  }

  const strip = root.querySelector("[data-review-strip]");
  if (strip) {
    const figure = strip.querySelector("[data-review-strip-count]");
    const label = strip.querySelector("[data-review-strip-label]");
    if (figure) figure.textContent = String(value);
    if (label) label.textContent = `${plural} to review`;
    // The strip belongs to Review. The timeline carries the kit's own banner instead,
    // so the two do not stack into two competing parchment invitations.
    strip.hidden = value === 0 || state.mode !== "review";
  }
}

/* Collect the distinct classification categories seen so far into the filter
   select, preserving the current selection. */
function populateCategories(root, transactions) {
  const select = root.querySelector("[data-category-filter]");
  if (!select) {
    return;
  }
  const known = new Set(
    [...select.options].map((option) => option.value).filter(Boolean)
  );
  for (const transaction of transactions || []) {
    const category = transaction.classification?.category;
    if (category && !known.has(category)) {
      known.add(category);
      const option = document.createElement("option");
      option.value = category;
      option.textContent = category;
      select.appendChild(option);
    }
  }
}

/* Client-side category filter. Timeline rows carry data-classification-category;
   day groups that end up with no matching row are collapsed. Pattern cards are
   never filtered (category is a timeline notion). */
function applyCategoryFilter(root) {
  const category = state.category;
  const groups = root.querySelectorAll("[data-day-group]");
  let visibleRows = 0;
  let hasPattern = false;
  for (const group of groups) {
    if (group.hasAttribute("data-pattern-card")) {
      group.hidden = false;
      hasPattern = true;
      continue;
    }
    const rows = group.querySelectorAll("[data-transaction-row]");
    let visible = 0;
    for (const row of rows) {
      const rowCategory = row.dataset.classificationCategory || "";
      const show = !category || rowCategory === category;
      row.hidden = !show;
      if (show) {
        visible += 1;
      }
    }
    group.hidden = visible === 0;
    visibleRows += visible;
  }
  const empty = root.querySelector("[data-activity-empty]");
  if (empty) {
    empty.hidden = visibleRows > 0 || hasPattern;
  }
}

function renderPage(root, payload, { append }) {
  const ledger = root.querySelector("[data-ledger]");
  const empty = root.querySelector("[data-activity-empty]");
  const loadMore = root.querySelector("[data-load-more]");
  const errorBox = root.querySelector("[data-activity-error]");

  errorBox.hidden = true;
  if (!append) {
    ledger.replaceChildren();
  }

  const transactions = payload.transactions || [];
  if (state.mode === "patterns") {
    for (const pattern of payload.patterns || []) {
      const card = document.createElement("article");
      card.className = "m-day-group";
      card.dataset.patternCard = pattern.kind;
      const heading = document.createElement("h2");
      heading.className = "m-day-heading";
      heading.textContent = pattern.title;
        const detail = document.createElement("p");
        detail.className = "m-pattern-detail";
        detail.textContent = pattern.detail || "";
        if (detail.textContent) {
          card.append(heading, detail);
        } else {
          card.append(heading);
        }

      const evidence = document.createElement("div");
      evidence.className = "m-pattern-evidence";
      const evidenceHeader = document.createElement("p");
      evidenceHeader.className = "m-pattern-evidence-label";
      evidenceHeader.textContent = "Evidence";
      evidence.append(evidenceHeader);
      for (const row of (pattern.evidence || [])) {
        const link = document.createElement("button");
        link.type = "button";
        link.className = "m-pattern-evidence-link";
        link.dataset.transactionId = row.id;
        const amt = Number(row.amount);
        const amountText = Number.isFinite(amt)
          ? `${amt < 0 ? "−" : "+"}${formatCurrency(Math.abs(amt))}`
          : "";
        link.textContent = [row.date, row.title, amountText].filter(Boolean).join(" · ");
        link.addEventListener("click", () => {
          if (window.MeridianTransactionInspector) {
            window.MeridianTransactionInspector.open(Number(row.id), { opener: link });
          }
        });
        evidence.appendChild(link);
      }
      card.append(evidence);
      ledger.appendChild(card);
    }
  }
  for (const transaction of transactions) {
    groupFor(ledger, transaction.occurred_at).appendChild(buildRow(transaction));
  }

  empty.hidden = ledger.children.length > 0;
  state.cursor = payload.next_cursor || null;
  loadMore.hidden = !state.cursor;
  setChip(root, payload.data_freshness);
  populateCategories(root, transactions);
  applyCategoryFilter(root);
}

async function populateAccounts(select) {
  if (state.accountsLoaded) {
    return;
  }
  state.accountsLoaded = true;
  try {
    const payload = await meridianFetch("/api/meridian/accounts");
    for (const account of payload.accounts || []) {
      const option = document.createElement("option");
      option.value = String(account.id);
      option.textContent = account.name;
      select.appendChild(option);
    }
  } catch {
    /* The All-accounts view remains usable without the filter options. */
  }
}

async function loadActivity(options = {}) {
  const root = document.querySelector("[data-activity-root]");
  if (!root) {
    return;
  }
  const append = Boolean(options.cursor) && options.cursor === state.cursor;

  if (state.controller) {
    state.controller.abort();
  }
  state.controller = new AbortController();

  const params = new URLSearchParams();
  const limit = options.limit || 50;
  params.set("limit", String(limit));
  const cursor = options.cursor !== undefined ? options.cursor : null;
  if (cursor && append) {
    params.set("cursor", cursor);
  }
  const accountId =
    options.accountId !== undefined ? options.accountId : state.accountId;
  if (accountId) {
    params.set("account_id", String(accountId));
  }
  params.set("mode", state.mode);

  root.setAttribute("aria-busy", "true");
  try {
    const payload = await meridianFetch(`/api/meridian/activity?${params}`, {
      signal: state.controller.signal,
    });
    setReviewCount(root, payload.review_count);
    setActivityBanner(root, payload.data_freshness);
    renderPage(root, payload, { append: append && cursor !== null });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }
    const ledgerEmpty =
      root.querySelector("[data-ledger] [data-transaction-row]") === null;
    if (ledgerEmpty || !(error instanceof MeridianApiError)) {
      const detail =
        error instanceof MeridianApiError
          ? `${error.message} ${error.recoveryAction}`
          : "Something went wrong while loading Activity.";
      const errorBox = root.querySelector("[data-activity-error]");
      errorBox.textContent = detail;
      errorBox.hidden = false;
    }
  } finally {
    root.removeAttribute("aria-busy");
  }
}

function openAccount(accountId) {
  state.accountId = Number(accountId) || null;
  state.mode = "timeline";
  document.querySelectorAll("[data-activity-mode]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.activityMode === "timeline"));
  });
  const select = document.querySelector("[data-account-filter]");
  if (select) {
    select.value = state.accountId ? String(state.accountId) : "";
  }
  if (window.MeridianShell && window.MeridianShell.getWorkspace() === "activity") {
    loadActivity({ accountId: state.accountId, cursor: null });
  } else if (window.MeridianShell) {
    window.MeridianShell.setWorkspace("activity", { focus: true });
  }
}


window.MeridianActivity = { loadActivity, openAccount };

document.addEventListener("click", (event) => {
  const modeButton = event.target.closest("[data-activity-mode]");
  if (!modeButton) {
    return;
  }
  state.mode = modeButton.dataset.activityMode;
  document.querySelectorAll("[data-activity-mode]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button === modeButton));
  });
  loadActivity({ cursor: null });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest("[data-load-more]")) {
    return;
  }
  event.preventDefault();
  if (state.cursor) {
    loadActivity({ cursor: state.cursor });
  }
});

document.addEventListener("change", (event) => {
  const select = event.target.closest("[data-account-filter]");
  if (!select) {
    return;
  }
  const value = select.value ? Number(select.value) : null;
  state.accountId = value;
  loadActivity({ accountId: value, cursor: null });
});

document.addEventListener("change", (event) => {
  const select = event.target.closest("[data-category-filter]");
  if (!select) {
    return;
  }
  state.category = select.value || "";
  const root = document.querySelector("[data-activity-root]");
  if (root) {
    applyCategoryFilter(root);
  }
});

document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-filter-toggle]");
  if (!toggle) {
    return;
  }
  const panel = document.querySelector("[data-filter-panel]");
  const expanded = toggle.getAttribute("aria-expanded") === "true";
  toggle.setAttribute("aria-expanded", String(!expanded));
  if (panel) {
    panel.hidden = expanded;
  }
});

document.addEventListener("meridian:workspacechange", (event) => {
  if (event.detail.workspace === "activity") {
    loadActivity();
    const select = document.querySelector("[data-account-filter]");
    if (select) {
      populateAccounts(select);
    }
  }
});

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    if (window.MeridianShell && window.MeridianShell.getWorkspace() === "activity") {
      loadActivity();
      const select = document.querySelector("[data-account-filter]");
      if (select) {
        populateAccounts(select);
      }
    }
  });
} else if (
  window.MeridianShell &&
  window.MeridianShell.getWorkspace() === "activity"
) {
  loadActivity();
  const select = document.querySelector("[data-account-filter]");
  if (select) {
    populateAccounts(select);
  }
}
