/* Readable statements for Crew's own AutopilotRule formulas (OS-102).
 *
 * WHY THIS IS A SEPARATE, PURE MODULE. The Plan pane used to print a rule's name and, for anything
 * Crew actually sends, an empty line: `ruleActionsSummary` looked for `action.type`, but a real Crew
 * formula carries `actions: [{roundUpTransfer: {...}}]` -- the action NAME is the key, not a field.
 * So every real rule rendered with no body at all. Rewriting that in place would have made the
 * honesty rules (what is understood, what is not, what is Crew's own vocabulary) impossible to test
 * except through a browser, so the statement builder lives here with no DOM and no imports, and
 * tests/meridian/test_rule_statement_js.py executes it under Node.
 *
 * THE HONESTY CONTRACT, because a summary of money rules is a claim about the owner's money:
 *
 *   1. Nothing is invented. Triggers and actions are named from a table of what Crew's schema
 *      actually contains (see meridian/crew_commands.py `_KNOWN_ACTIONS`); anything else is
 *      reported in Crew's own vocabulary and marks the statement `recognised: false`.
 *   2. Units are never guessed. `roundToNearest` is cents -- the repo's own default is 100 with the
 *      docstring "Round up transactions to the nearest dollar" -- so that one is formatted as money.
 *      Every other amount field is shown as the figure Crew reports, labelled as Crew's own, because
 *      no fixture in this repository establishes its unit and a wrong 100x on a money rule is worse
 *      than an unpolished sentence.
 *   3. A webhook URL is never printed. A webhook path routinely carries a secret; the statement
 *      shows the host and says the rest is withheld.
 *   4. What is not understood is disclosed, not summarised away: `unknown` names the terms, and the
 *      caller can show the raw formula beside the sentence.
 */

const TRIGGERS = {
  DEBIT_CARD_TRANSACTION: "a card purchase settles",
  CASH_TRANSACTION_OCCURRED: "cash moves in or out",
};

const PURPOSES = {
  money: "Money movement",
  notify: "Notifications",
  other: "Other rules",
};

const MONEY_ACTIONS = new Set([
  "roundUpTransfer",
  "targetBalanceTransfer",
  "splitDeposit",
  "splitDepositByAmount",
  "internalTransfer",
  "sweepExcess",
]);

const NOTIFY_ACTIONS = new Set(["sendNotification", "sendWebhook"]);

function actionKey(entry) {
  /* Crew's action union is `{ <actionName>: {...} }` -- one key, no `type` field. */
  if (!entry || typeof entry !== "object") return null;
  const keys = Object.keys(entry);
  if (keys.length !== 1) return null;
  return keys[0];
}

function actionBody(entry, key) {
  const body = entry[key];
  return body && typeof body === "object" ? body : {};
}

export function rulePurpose(rule) {
  const actions = ((rule && rule.formula && rule.formula.actions) || []).map(actionKey).filter(Boolean);
  if (actions.some((key) => NOTIFY_ACTIONS.has(key))) return "notify";
  if (actions.some((key) => MONEY_ACTIONS.has(key))) return "money";
  return "other";
}

export function rulePurposeLabel(purpose) {
  return PURPOSES[purpose] || PURPOSES.other;
}

function money(cents) {
  const value = Number(cents) / 100;
  const sign = value < 0 ? "-" : "";
  const [whole, fraction] = Math.abs(value).toFixed(2).split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${sign}$${grouped}.${fraction}`;
}

function crewFigure(value) {
  /* Crew's own number, said to be Crew's own number. */
  return `${value} (in Crew's own units)`;
}

function hostOf(url) {
  try {
    return new URL(String(url)).host || "an address Crew holds";
  } catch {
    return "an address Crew holds";
  }
}

function describeCondition(condition, names, unknown, depth = 0) {
  /* Returns bare FACTS about when a rule applies -- "the Teal card matches" -- never a sentence.
     The single "only when" in front of them belongs to the caller: nesting it here produced
     "only when only for the Teal card" the first time round. */
  if (!condition || typeof condition !== "object") {
    unknown.push("a condition Meridian does not read");
    return [];
  }
  if (condition.and || condition.or) {
    const wrapper = condition.and ? "and" : "or";
    const inner = ((condition.and || condition.or).conditions || []);
    const parts = [];
    for (const child of inner) {
      parts.push(...describeCondition(child, names, unknown, depth + 1));
    }
    if (!parts.length) {
      unknown.push(`a ${wrapper} condition with nothing in it`);
      return [];
    }
    return [`${parts.join(` ${wrapper} `)}`];
  }
  if (condition.idMatch) {
    const match = condition.idMatch || {};
    const schema = String(match.entitySchema || "an entity").replace(/_/g, " ").toLowerCase();
    const named = names[String(match.entityId || "")];
    // The id is Crew's opaque identifier. It is named when the snapshot names it and described
    // otherwise -- never printed as a bare id, which would be noise pretending to be information.
    return [named ? `${named} matches` : `Crew's ${schema} match holds`];
  }
  unknown.push("a condition Meridian does not read");
  return [];
}

function describeAction(entry, names, unknown) {
  const key = actionKey(entry);
  if (!key) {
    unknown.push("an action whose shape Meridian does not read");
    return [];
  }
  const body = actionBody(entry, key);
  const destination = (value) =>
    names[String(value || "")] || (value ? "a destination Crew holds" : "a destination Crew holds");
  switch (key) {
    case "roundUpTransfer": {
      const nearest = Number(body.roundToNearest);
      const target = destination(body.subaccountId);
      const rounded = Number.isFinite(nearest) && nearest > 0
        ? `round each purchase up to the nearest ${money(nearest)}`
        : "round each purchase up";
      return [`${rounded} and move the change into ${target}`];
    }
    case "targetBalanceTransfer": {
      const direction = String(body.direction || "INTO").toUpperCase() === "OUT" ? "out of" : "into";
      const account = destination(body.accountId);
      const figure = body.targetBalance !== undefined
        ? crewFigure(body.targetBalance)
        : body.amount !== undefined ? crewFigure(body.amount) : null;
      return figure
        ? [`move money ${direction} ${account} until it holds ${figure}`]
        : [`move money ${direction} ${account} until it reaches its target`];
    }
    case "splitDeposit": {
      const destinations = body.destinations || [];
      return [`split each deposit across ${destinations.length || "its"} destination${
        destinations.length === 1 ? "" : "s"}`];
    }
    case "splitDepositByAmount": {
      const destinations = body.destinations || [];
      const amounts = destinations
        .map((dest) => (dest && dest.amount !== undefined ? crewFigure(dest.amount) : null))
        .filter(Boolean);
      const sized = amounts.length ? ` -- ${amounts.join(", ")}` : "";
      return [`split each deposit by fixed amount across ${destinations.length || "its"} destination${
        destinations.length === 1 ? "" : "s"}${sized}`];
    }
    case "internalTransfer": {
      const from = destination(body.accountFromId);
      const to = destination(body.accountToId);
      const amount = body.amount !== undefined ? crewFigure(body.amount) : null;
      return [amount ? `move ${amount} from ${from} to ${to}` : `move money from ${from} to ${to}`];
    }
    case "sendNotification": {
      const message = String(body.message || "").trim();
      const method = String(body.method || "PUSH").toLowerCase();
      return [message ? `notify you by ${method}: "${message}"` : `notify you by ${method}`];
    }
    case "sendWebhook":
      // Host only. A webhook path routinely carries a secret, and this text can be captured,
      // screenshotted or shared.
      return [`call your webhook at ${hostOf(body.url)} (the rest of the address is withheld)`];
    case "sweepExcess": {
      const destinations = body.sweepDestinations || [];
      const source = destination(body.subaccountId);
      const shares = destinations
        .map((dest) => (dest && dest.percentage !== undefined ? `${dest.percentage}%` : null))
        .filter(Boolean);
      const split = shares.length ? ` (${shares.join(", ")})` : "";
      return [`sweep anything left in ${source} into ${
        destinations.length || "its"} destination${destinations.length === 1 ? "" : "s"}${split}`];
    }
    default:
      unknown.push(`the action type ${key}`);
      return [];
  }
}

export function ruleStatement(rule, options = {}) {
  const names = options.names || {};
  const formula = (rule && rule.formula) || {};
  const unknown = [];
  const triggers = Array.isArray(formula.triggers) ? formula.triggers : [];
  const whenRaw = triggers.map((trigger) =>
    typeof trigger === "string" ? trigger : JSON.stringify(trigger));
  const whenSentences = triggers.map((trigger) => {
    if (typeof trigger === "string" && TRIGGERS[trigger]) return TRIGGERS[trigger];
    unknown.push(typeof trigger === "string" ? `the trigger ${trigger}` : "a trigger Meridian does not read");
    return typeof trigger === "string" ? trigger : null;
  }).filter(Boolean);

  const conditionFacts = formula.conditions === undefined || formula.conditions === null
    ? []
    : describeCondition(formula.conditions, names, unknown);
  const conditions = conditionFacts.map((fact) => `only when ${fact}`);
  const effects = [];
  for (const entry of formula.actions || []) {
    effects.push(...describeAction(entry, names, unknown));
  }

  const schedule = formula.cadence || formula.schedule || formula.interval || null;
  const description = typeof formula.description === "string" ? formula.description.trim() : "";

  /* Nothing at all is not the same as everything understood: a rule whose formula Crew did not send
     (or sent empty) must not read as recognised, or the pane would imply it had explained a rule it
     never saw. */
  if (!whenRaw.length && !effects.length && !conditionFacts.length && !description && !unknown.length) {
    unknown.push("Crew reported no formula for this rule");
  }

  return {
    when: whenSentences.length ? whenSentences.join(", and ") : null,
    whenRaw,
    conditions,
    effects,
    description: description || null,
    schedule: schedule ? String(schedule) : null,
    purpose: rulePurpose(rule),
    unknown,
    recognised: unknown.length === 0,
    raw: JSON.stringify(formula, null, 1),
  };
}
