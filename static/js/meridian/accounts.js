import { meridianFetch } from "./api.js";
import { describeArchivedAccount } from "./archived-accounts.js";
import { formatCurrency } from "./format.js";

/* Guarded so the module can be imported where there is no DOM (Node, for the pure
   connector-geometry tests) exactly as dial.js is. Everything below is a no-op without
   a root. */
const root = typeof document === "undefined"
  ? null
  : document.querySelector("[data-accounts]");

/* ---------- Inline icon system (line set, stroke = currentColor) ---------- */

const ROLE_ICONS = {
  cash: `<svg viewBox="0 0 24 24" fill="none" focusable="false" aria-hidden="true"><path d="M3 10.5 12 4l9 6.5M5 10v7h14v-7M9.5 17v-4h5v4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  savings: `<svg viewBox="0 0 24 24" fill="none" focusable="false" aria-hidden="true"><path d="M5 9.5h.5V7.5a1 1 0 0 1 1-1h4.5a1 1 0 0 1 .4.09A5.5 5.5 0 0 1 20 12v2.5a1 1 0 0 1-1 1h-1.3a5 5 0 0 1-4.3 3h-4.2a1 1 0 0 1-.4-.09L5 14.5a1 1 0 0 1-.5-.87V9.5Z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 11h.01" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>`,
  investments: `<svg viewBox="0 0 24 24" fill="none" focusable="false" aria-hidden="true"><path d="M4 19V5M4 19h16M7 15l3-4 2.5 2 3.5-5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  liabilities: `<svg viewBox="0 0 24 24" fill="none" focusable="false" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="2" stroke="currentColor" stroke-width="1.7"/><path d="M3 10h18M6.5 14.5h4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>`,
  reimbursements: `<svg viewBox="0 0 24 24" fill="none" focusable="false" aria-hidden="true"><path d="M12 4v10M8 10l4 4 4-4M5 19h14" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  other: `<svg viewBox="0 0 24 24" fill="none" focusable="false" aria-hidden="true"><circle cx="12" cy="12" r="8.5" stroke="currentColor" stroke-width="1.7"/><path d="M9 9.5h.01M15 9.5h.01" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>`,
};

function roleIcon(role) {
  return ROLE_ICONS[role] || ROLE_ICONS.other;
}

/* Concept 04's account medallion. The kit's medallion-frame.png is a brass double ring
   with four rivets, which the kit specifies as a "decorative frame above a code-owned
   colored disk and semantic SVG icon" -- so the disk tint is ours to choose while the
   frame is the supplied art. The three tints the concept shows map to cash, savings and
   investments; the remaining roles take a quieter slate because the concept does not
   show them and inventing a signal colour would say something the data does not.

   The glyphs stay the existing role line-icons. The kit's vocabulary prescribes `bank`
   for reserves but supplies no equivalent for liabilities or reimbursements, so
   swapping the set would lose meaning rather than gain fidelity. */
const ROLE_TINTS = {
  cash: "lilac",
  savings: "mint",
  investments: "apricot",
  liabilities: "coral",
  reimbursements: "mint",
  other: "slate",
};

function roleTint(role) {
  return ROLE_TINTS[role] || "slate";
}

/* Concept 04 draws three DIFFERENT emblems on three named accounts: a compass rose for Free to
   Spend, a Wi-Fi mark for Bill Reserve, and a star for Emergency Fund. The app draws one glyph
   per financial ROLE instead, and both of the owner's first two accounts are pockets that
   resolve to `other` -- so they came out as two identical houses, which is what he reported as
   "more diverse icons" on 2026-09-24.

   The owner chose the concept's own three emblems, and the delivered medallion handoff permits
   that artwork only "where that visual mapping is deliberately accepted" -- it does, and he
   accepted it on 2026-09-24. Three things keep that permission narrow rather than a licence:

     1. The key is the account's NAME, matched against concept 04's own three names after
        normalisation, and matched EXACTLY. There is no substring or fuzzy matching, because a
        rule that fires on "Emergency" would relabel "Emergency plumbing fund" with an emblem
        that means something else. His rows carry the three names verbatim.
     2. Anything that does not match keeps its semantic role medallion, so the emblem is never
        the only thing distinguishing two accounts -- and every row still carries its own name
        label, which the handoff requires it to keep.
     3. The artwork is never a classifier: it is decoration on a row that already says what it
        is, `aria-hidden`, exactly as the role glyph was.

   Tints follow the concept too: the compass is lilac, the Wi-Fi mint, the star the concept's
   apricot. The connector node inherits the SAME tint, because the concept's cord takes its
   colour from the medallion it leaves. */
/* The discretionary spend pocket. These names are the SAME set as
   meridian/services/spend_pocket.py, and they are kept as an explicit list rather than a
   pattern on purpose: /to spend/ would also match an earmarked bucket and quietly count it
   as free cash. Kept in step because a pocket renamed in Crew must not change a figure in
   any workspace -- the owner renamed his on 2026-09-25 and Today silently changed basis. */
const SPEND_POCKET_NAMES = ["free to spend", "safe to spend"];

const BUCKET_EMBLEMS = {
  "free to spend": "compass",
  "bill reserve": "wifi",
  "emergency fund": "star",
};

const EMBLEM_TINTS = { compass: "lilac", wifi: "mint", star: "apricot" };

/* The spend pocket's emblem, resolved by ROLE so the owner's 2026-09-25 rename cannot cost
   the pocket its compass. Derived from SPEND_POCKET_NAMES rather than written twice, and
   keyed by EXACT name like the concept table above -- a prefix rule here would relabel
   "Emergency plumbing fund" with the emergency fund's own emblem, which is a decoration
   asserting something untrue about the owner's money. */
const BUCKET_EMBLEM_ALIASES = Object.fromEntries(
  SPEND_POCKET_NAMES.map((name) => [name, "compass"]),
);

function normalizeAccountName(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function bucketEmblem(name) {
  return (
    BUCKET_EMBLEMS[normalizeAccountName(name)] ||
    BUCKET_EMBLEM_ALIASES[normalizeAccountName(name)] ||
    null
  );
}

export function emblemTint(emblem) {
  return EMBLEM_TINTS[emblem] || "slate";
}

/* The same tints the medallions carry, as colour values, so the connector nodes can
   take their row's ink without the stylesheet repeating a second colour table. Kept
   beside ROLE_TINTS so the two cannot drift apart unnoticed. */
const TINT_COLORS = {
  lilac: "#c1a9e2",
  mint: "#a5d4bf",
  apricot: "#f3b272",
  coral: "#e8a48c",
  slate: "#b9c2d2",
};

/* ---------- Connector geometry (concept 04) ---------- */

const SVG_NS = "http://www.w3.org/2000/svg";

/* Concept 04 does not thread its account rows on a straight rail. The dashed line is a
   BOW: it leaves one row's node, curves left into the gutter, and returns to the next
   row's node, so the medallions read as one constellation strung on a slack cord. The
   earlier build used a straight vertical border, which is the wrong construction
   (artifacts/astra-fidelity-review-2026-09-16/README.md, Finding 4 item 5).

   The geometry is a pure function of measured positions, so it can be reasoned about and
   tested without a browser. One property matters more than the shape: with fewer than two
   rows there is nothing to string together, so no path is emitted at all. A lone row gets
   no arc -- a constellation of one is not a thing, and drawing a fixed bow unconditionally
   is how that defect reaches the page.

   The bow is built as a string of quadratic segments through the two gaps ADJACENT to each
   node rather than one continuous path, so a row that leaves the list cannot drag the
   curve through a row it no longer touches.

   Each segment also carries the TWO tints it runs between, because the concept tints the
   cord ALONG its length: the dashes leaving a row's node are that row's colour and they
   arrive at the next node as that row's colour. Read off concept 04 -- lilac dashes leave
   the lilac node and turn mint as they reach the mint node, and apricot dashes leave the
   mint node and turn orange at the third. Rendering that needs the pair, not just the path
   string, so the geometry reports both.

   `rows` are the node-carrying rows in visual order, each measured to its centre in
   list-relative coordinates. */
export function connectorGeometry(rows, options = {}) {
  const nodeX = options.nodeX ?? 21;
  const bow = options.bow ?? 12;
  if (!Array.isArray(rows) || rows.length < 2) return null;

  const centres = rows.map((row) => row.centerY);
  const tintOf = (row) =>
    Object.prototype.hasOwnProperty.call(TINT_COLORS, row.tint) ? row.tint : "slate";
  const minX = nodeX - bow;
  const segments = [];
  const links = [];
  for (let index = 0; index < rows.length; index += 1) {
    // Upward curve to the row above, bulging left across that gap.
    if (index > 0) {
      const midY = (centres[index - 1] + centres[index]) / 2;
      segments.push(
        `M${nodeX} ${centres[index].toFixed(1)}`
        + ` Q${minX.toFixed(1)} ${midY.toFixed(1)} ${nodeX} ${centres[index - 1].toFixed(1)}`
      );
    }
    // Downward curve to the row below, so every adjacent pair has its own segment and a
    // hidden row simply drops out of the chain.
    if (index < rows.length - 1) {
      const midY = (centres[index] + centres[index + 1]) / 2;
      segments.push(
        `M${nodeX} ${centres[index].toFixed(1)}`
        + ` Q${minX.toFixed(1)} ${midY.toFixed(1)} ${nodeX} ${centres[index + 1].toFixed(1)}`
      );
    }
  }
  // One paintable entry per ADJACENT PAIR, in visual order. The list above draws each pair
  // from both ends (so a hidden row drops out of the chain); painting the pair twice would
  // double a translucent stroke's alpha, so the paint list is its own list.
  for (let index = 0; index < rows.length - 1; index += 1) {
    const midY = (centres[index] + centres[index + 1]) / 2;
    links.push({
      d: `M${nodeX} ${centres[index].toFixed(1)}`
        + ` Q${minX.toFixed(1)} ${midY.toFixed(1)} ${nodeX} ${centres[index + 1].toFixed(1)}`,
      fromTint: tintOf(rows[index]),
      toTint: tintOf(rows[index + 1]),
      fromY: centres[index],
      toY: centres[index + 1],
    });
  }

  return {
    d: segments.join(" "),
    nodes: rows.map((row) => ({
      x: nodeX,
      y: row.centerY,
      tint: tintOf(row),
    })),
    links,
    nodeX,
  };
}

/* ---------- Connector rendering ---------- */

/* The layer is decorative and is never a hit target. It carries one NODE per row that
   owns a medallion; archived rows carry no medallion, so they get neither node nor curve.

   It hangs off the account SHEET, not off one `.m-account-list`. The sheet is the
   constellation: grouping splits accounts into a list per financial role, and a preview
   holds one account per group, so a per-list layer would see a single row in each and
   draw nothing at all -- which is exactly what the first capture of this slice showed.
   Mounting on the sheet strings every medallion-bearing row on the page in visual order,
   which is what the concept draws. The sheet also shares its left edge with the rows
   (only the rows add their own gutter), so one node x serves every row.

   Archived rows live in a separate section, outside `[data-accounts-groups]`, so they are
   never measured and never join the chain. */
function renderConnectors(sheet) {
  if (!sheet) return;
  let layer = sheet.querySelector(".m-account-connectors");
  const rows = [...sheet.querySelectorAll(".m-account-row:not(.m-account-row-archived)")];
  const sheetBox = sheet.getBoundingClientRect();
  const measured = rows
    .map((row) => {
      const box = row.getBoundingClientRect();
      return {
        centerY: box.top - sheetBox.top + box.height / 2,
        tint: row.dataset.tint || "slate",
      };
    })
    .filter((row) => Number.isFinite(row.centerY));
  const geometry = connectorGeometry(measured);
  if (!geometry) {
    // Nothing to string together; drop any layer rather than leave a stale curve behind
    // on a sheet that has since collapsed to a single row.
    if (layer) layer.remove();
    return;
  }
  if (!layer) {
    layer = document.createElementNS(SVG_NS, "svg");
    layer.setAttribute("class", "m-account-connectors");
    layer.setAttribute("aria-hidden", "true");
    layer.setAttribute("focusable", "false");
    sheet.append(layer);
  }
  while (layer.firstChild) layer.removeChild(layer.firstChild);

  // One gradient per adjacent pair, painted along the segment's own vertical run: the colour
  // leaving a row is that row's, and it arrives as the next row's. The stops are the same
  // values as the row's node and medallion, so a segment can never disagree with the two
  // things it joins.
  const defs = document.createElementNS(SVG_NS, "defs");
  layer.append(defs);
  geometry.links.forEach((link, index) => {
    const gradientId = `m-account-connector-tint-${index}`;
    const gradient = document.createElementNS(SVG_NS, "linearGradient");
    gradient.setAttribute("id", gradientId);
    gradient.setAttribute("gradientUnits", "userSpaceOnUse");
    gradient.setAttribute("x1", String(geometry.nodeX));
    gradient.setAttribute("y1", link.fromY.toFixed(1));
    gradient.setAttribute("x2", String(geometry.nodeX));
    gradient.setAttribute("y2", link.toY.toFixed(1));
    for (const [offset, tint] of [[0, link.fromTint], [1, link.toTint]]) {
      const stop = document.createElementNS(SVG_NS, "stop");
      stop.setAttribute("offset", String(offset));
      stop.setAttribute("stop-color", TINT_COLORS[tint] || TINT_COLORS.slate);
      gradient.append(stop);
    }
    defs.append(gradient);

    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("class", "m-account-connector");
    path.setAttribute("data-from-tint", link.fromTint);
    path.setAttribute("data-to-tint", link.toTint);
    path.setAttribute("d", link.d);
    // The segment's ink is a REFERENCE, so it has to arrive as an attribute -- and the
    // stylesheet must not also declare `stroke` on this class, because a CSS declaration
    // outranks a presentation attribute and would flatten every segment back to one colour.
    path.setAttribute("stroke", `url(#${gradientId})`);
    layer.append(path);
  });
  for (const node of geometry.nodes) {
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("class", "m-account-connector-node");
    circle.setAttribute("data-tint", node.tint);
    circle.setAttribute("cx", node.x.toFixed(1));
    circle.setAttribute("cy", node.y.toFixed(1));
    circle.setAttribute("r", "3.5");
    layer.append(circle);
  }
}

function renderAllConnectors() {
  if (!root) return;
  // The sheet is the PARENT of `[data-accounts-groups]`, not a descendant of it, so this
  // selects from the root. Scoping it under the groups container matched nothing and
  // silently drew no connectors at all.
  for (const sheet of root.querySelectorAll(".m-account-list-sheet")) {
    renderConnectors(sheet);
  }
}

/* ---------- Formatting helpers ---------- */

function textNode(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

function prettyType(accountType) {
  const map = {
    checking: "Chequing",
    cash: "Chequing",
    depository: "Chequing",
    wallet: "Chequing",
    savings: "High-Savings",
    money_market: "High-Savings",
    reserve: "High-Savings",
    credit: "Credit",
    credit_card: "Credit",
    loan: "Credit",
    mortgage: "Credit",
    liability: "Credit",
    investment: "Investment",
    brokerage: "Investment",
    retirement: "Investment",
    asset: "Investment",
    reimbursement: "Reimbursement",
    receivable: "Reimbursement",
  };
  const key = String(accountType || "").trim().toLowerCase().replace(/-/g, "_").replace(/ /g, "_");
  return map[key] || (accountType ? accountType.charAt(0).toUpperCase() + accountType.slice(1) : "Account");
}

function relativeAge(isoTimestamp) {
  if (!isoTimestamp) return "never synced";
  const parsed = new Date(isoTimestamp);
  if (Number.isNaN(parsed.getTime())) return "recently synced";
  const diffMs = Date.now() - parsed.getTime();
  if (diffMs < 0) return "just now";
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return days < 365 ? `${Math.round(days / 30)}mo ago` : `${Math.round(days / 365)}y ago`;
}

function providerList(accounts, role) {
  const names = [
    ...new Set(accounts
      .filter((a) => role === undefined || a.role === role)
      .map((a) => a.provider)
      .filter(Boolean)),
  ];
  if (!names.length) return "No sources";
  if (names.length === 1) return names[0].charAt(0).toUpperCase() + names[0].slice(1);
  return names.slice(0, -1).map((n) => n.charAt(0).toUpperCase() + n.slice(1)).join(", ")
    + `, and ${names[names.length - 1].charAt(0).toUpperCase() + names[names.length - 1].slice(1)}`;
}

/* ---------- Account identity rows (provider-neutral) ---------- */

function accountRow(account, role) {
  const row = document.createElement("article");
  row.className = "m-account-row";
  row.dataset.accountRow = "";
  // The tint lives on the row as well as the medallion so the connector rail's node can
  // inherit the same colour without the two reading from separate sources. A concept emblem
  // brings the concept's own colour with it, so the node follows the medallion either way.
  const emblem = bucketEmblem(account.name);
  const tint = emblem ? emblemTint(emblem) : roleTint(role);
  row.dataset.tint = tint;

  const icon = document.createElement("span");
  icon.className = "m-account-icon";
  icon.dataset.accountIcon = role;
  icon.dataset.tint = tint;
  if (emblem) {
    // A delivered medallion is COMPLETE -- ring, field and centre glyph in one image -- so the
    // whole mark is replaced rather than the frame being stacked over a code-owned disk and a
    // semantic glyph. The handoff is explicit: "Replace the whole decorative medallion in the
    // chosen location; do not stack them over the existing frame or recolor them with a CSS
    // mask." The stylesheet paints the art off this attribute, and the row keeps its visible
    // name, so nothing here carries meaning on its own.
    icon.dataset.emblem = emblem;
  } else {
    icon.innerHTML = roleIcon(role);
  }
  icon.setAttribute("aria-hidden", "true");

  const identity = document.createElement("div");
  identity.className = "m-account-identity";
  const name = textNode("h3", "m-account-name", account.name);
  name.dataset.accountName = "";
  const source = textNode(
    "p",
    "m-account-source",
    `${prettyType(account.account_type)} · ${relativeAge(account.synced_at)}`
  );
  source.dataset.accountSource = "";
  identity.append(name, source);
  const activity = document.createElement("button");
  activity.type = "button";
  activity.className = "m-account-activity";
  activity.dataset.accountActivity = String(account.id);
  activity.setAttribute("aria-label", `View ${account.name} activity`);
  activity.textContent = "Activity";
  activity.addEventListener("click", (event) => {
    event.stopPropagation();
    if (window.MeridianActivity && window.MeridianActivity.openAccount) {
      window.MeridianActivity.openAccount(account.id);
    }
  });
  row.append(
    icon,
    identity,
    textNode("strong", "m-account-balance", formatCurrency(account.balance, account.currency)),
    activity
  );
  return row;
}

function renderGroups(groups) {
  const target = root.querySelector("[data-accounts-groups]");
  target.replaceChildren();

  // Provider-neutral grouping by financial role (never provider-led).
  const roles = [...new Set(groups.map((g) => g.role))];
  for (const role of roles) {
    const groupAccounts = groups.filter((g) => g.role === role).flatMap((g) => g.accounts);
    const group = groups.find((g) => g.role === role);
    const section = document.createElement("section");
    section.className = "m-account-group";
    section.dataset.accountsGroup = role;

    if (groupAccounts.length > 1 || roles.length > 1) {
      const heading = textNode("h2", "m-section-label", group.label);
      heading.dataset.accountsGroupLabel = role;
      section.append(heading);
    }

    const list = document.createElement("div");
    list.className = "m-account-list";
    for (const account of groupAccounts) list.append(accountRow(account, role));
    section.append(list);
    target.append(section);
  }
  if (!roles.length) target.append(textNode("p", "m-empty-note", "No accounts are connected yet."));
}

/* ---------- Accounts no longer returned by a provider ---------- */

function archivedAccountRow(item) {
  const view = describeArchivedAccount(item);
  const row = document.createElement("article");
  row.className = "m-account-row m-account-row-archived";
  row.dataset.archivedAccount = String(item.id);
  const identity = document.createElement("div");
  identity.className = "m-account-identity";
  const name = textNode("h3", "m-account-name", view.name);
  name.dataset.archivedAccountName = "";
  const source = textNode("p", "m-account-source", view.source + " \u00b7 " + view.observed);
  source.dataset.archivedAccountSource = "";
  const history = textNode(
    "p",
    "m-account-history",
    view.absent + " \u00b7 " + view.history
  );
  history.dataset.archivedAccountHistory = "";
  identity.append(name, source, history);
  // No amount and no control: a last known figure is not a current balance, and
  // there is nothing here the owner could change.
  row.append(identity);
  return row;
}

function renderArchived(items) {
  const section = root.querySelector("[data-archived-accounts]");
  const list = root.querySelector("[data-archived-account-list]");
  if (!section || !list) return;
  list.replaceChildren();
  const archived = Array.isArray(items) ? items : [];
  for (const item of archived) list.append(archivedAccountRow(item));
  section.hidden = archived.length === 0;
}

/* ---------- Net-position summary ---------- */

function summarize(groups) {
  const all = groups.flatMap((g) => g.accounts.map((a) => ({ ...a, role: g.role })));
  // Liquid = real cash-typed accounts (cash/checking/savings) plus the spendable
  // "Free to Spend" pocket, which is where Crew keeps discretionary money. This
  // matches the Today safe-to-spend convention (the pockets are the actual
  // spendable liquid money, not an "other" bucket).
  const liquid = all.filter((a) => {
    if (a.account_type === "checking" || a.account_type === "cash" || a.account_type === "savings") {
      return true;
    }
    return a.account_type === "pocket" && SPEND_POCKET_NAMES.includes(normalizeAccountName(a.name));
  });
  // Liabilities = accounts carrying a negative balance (debt/cards owe money).
  const liabilities = all.filter((a) => (Number(a.balance) || 0) < 0);

  const available = liquid.reduce((sum, a) => sum + (Number(a.balance) || 0), 0);
  const liabilityTotal = liabilities.reduce((sum, a) => sum + Math.abs(Number(a.balance) || 0), 0);

  return {
    available,
    liabilities: liabilityTotal,
    availableNote: `Across ${providerList(all)} · synced ${relativeAge(liquid.length ? liquid[0].synced_at : null)}`,
    liabilitiesNote: liabilities.length
      ? `${liabilities.length} ${liabilities.length === 1 ? "card" : "cards"} · ${providerList(liabilities)}`
      : "No outstanding balances",
  };
}

function renderSummary(summary) {
  const available = root.querySelector("[data-available-cash]");
  const liabilities = root.querySelector("[data-liabilities]");
  const availableNote = root.querySelector("[data-available-note]");
  const liabilitiesNote = root.querySelector("[data-liabilities-note]");
  if (available) available.textContent = formatCurrency(summary.available, "USD");
  if (liabilities) liabilities.textContent = formatCurrency(summary.liabilities, "USD");
  if (availableNote) availableNote.textContent = summary.availableNote;
  if (liabilitiesNote) liabilitiesNote.textContent = summary.liabilitiesNote;

  // Value-aware figure color: a $0 or negative balance should never render in
  // the "good" green (it reads as healthy money). Green only for positive
  // available; red for negative; neutral for zero.
  if (available) {
    available.dataset.signal =
      summary.available > 0 ? "positive" : summary.available < 0 ? "negative" : "neutral";
  }
  if (liabilities) {
    // No debt (0) is good; any liability deserves attention.
    liabilities.dataset.signal =
      summary.liabilities > 0 ? "attention" : "neutral";
  }
}

/* ---------- Reimbursements ---------- */

function renderReimbursements(items) {
  const section = root.querySelector("[data-reimbursements]");
  section.hidden = !items.length;
  const list = root.querySelector("[data-reimbursement-list]");
  list.replaceChildren();
  for (const item of items) {
    list.append(accountRow({ ...item, account_type: "reimbursement", balance: item.amount }, "reimbursements"));
  }
}

/* ---------- Connection-health rail ---------- */

function renderConnections(items, dataFreshness) {
  const list = root.querySelector("[data-connections-list]");
  const status = root.querySelector("[data-connection-status]");
  const freshness = root.querySelector("[data-accounts-freshness]");
  const lastMaterial = root.querySelector("[data-connection-last]");
  list.replaceChildren();
  if (lastMaterial && dataFreshness && dataFreshness.last_updated_at) {
    lastMaterial.textContent = `Last material data · ${relativeAge(dataFreshness.last_updated_at)}`;
  }
  const computedState = (dataFreshness && dataFreshness.status) || "unavailable";
  if (!items.length) {
    list.append(textNode("p", "m-empty-note", "No provider connections are configured."));
    if (status) status.textContent = "No connected sources";
    if (freshness) {
      freshness.dataset.state = "unavailable";
      freshness.textContent = "No sources";
    }
    return;
  }
  for (const item of items) {
    const row = document.createElement("article");
    row.className = "m-connection-row";
    row.dataset.connectionRow = "";
    const provider = textNode("strong", "m-account-name", item.provider.charAt(0).toUpperCase() + item.provider.slice(1));
    provider.dataset.connectionProvider = "";
    const detail = textNode(
      "span",
      "m-connection-age",
      item.status === "healthy" ? relativeAge(item.last_successful_at) : item.status
    );
    detail.dataset.connectionAge = "";
    row.append(provider, detail);
    list.append(row);
  }
  if (status) {
    const labels = {
      fresh: "All sources current",
      stale: "Some sources are stale",
      partial: "Some sources need attention",
      unavailable: "Sources need attention",
    };
    status.textContent = labels[computedState] || "Sources need attention";
  }
  if (freshness) {
    const chipLabels = {
      fresh: "Current",
      stale: "Stale",
      partial: "Partial",
      unavailable: "Unavailable",
    };
    freshness.dataset.state = computedState;
    freshness.textContent = chipLabels[computedState] || "Unavailable";
  }
}

/* ---------- Boot ---------- */

async function loadAccounts() {
  if (!root) return;
  root.setAttribute("aria-busy", "true");
  const error = root.querySelector("[data-accounts-error]");
  error.hidden = true;
  try {
    const payload = await meridianFetch("/api/meridian/accounts");
    const groups = payload.groups || [];
    renderGroups(groups);
    renderAllConnectors();
    renderSummary(summarize(groups));
    renderArchived(payload.archived || []);
    renderReimbursements(payload.reimbursements || []);
    renderConnections(payload.connections || [], payload.data_freshness);
  } catch (failure) {
    error.textContent = `${failure.message} ${failure.recoveryAction || ""}`.trim();
    error.hidden = false;
  } finally {
    root.setAttribute("aria-busy", "false");
  }
}

if (!root) {
  // No Accounts surface on this page (or no DOM at all); nothing to boot.
} else {
  loadAccounts();

  /* The connector layer is measured from live row boxes, so a rotation or a resize moves
     the medallions and the curve has to follow them. Redrawn only, never re-fetched. */
  let connectorFrame = 0;
  window.addEventListener("resize", () => {
    window.cancelAnimationFrame(connectorFrame);
    connectorFrame = window.requestAnimationFrame(renderAllConnectors);
  });

  /* ---------- Refresh now (live-data trigger) ---------- */

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-connections-refresh]");
    if (!button) return;
    event.preventDefault();
    button.setAttribute("aria-busy", "true");
    button.disabled = true;
    button.textContent = "Refreshing…";
    try {
      const result = await meridianFetch("/api/meridian/sync");
      if (result && result.success) {
        button.textContent = "Updated";
        await loadAccounts();
        window.setTimeout(() => { button.textContent = "Refresh now"; }, 1500);
      } else {
        button.textContent = "Retry";
      }
    } catch (_) {
      button.textContent = "Retry";
    } finally {
      button.removeAttribute("aria-busy");
      button.disabled = false;
    }
  });
}
