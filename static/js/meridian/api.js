/* Typed Meridian API access: JSON-only responses, normalized stable errors,
   caller-controlled aborts. Mutations are never sent or retried here. */

export class MeridianApiError extends Error {
  constructor({ code, message, recoveryAction, status }) {
    super(message || "The request could not be completed.");
    this.name = "MeridianApiError";
    this.code = code || "unexpected_error";
    this.recoveryAction = recoveryAction || "Try again shortly.";
    this.status = status;
  }
}

export async function meridianFetch(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET") {
    throw new MeridianApiError({
      code: "mutations_forbidden",
      message: "Meridian views never send mutations.",
      recoveryAction: "Use an approved proposal instead.",
      status: 0,
    });
  }

  let response;
  try {
    response = await fetch(path, {
      ...options,
      method: "GET",
      headers: { Accept: "application/json", ...(options.headers || {}) },
    });
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw error;
    }
    throw new MeridianApiError({
      code: "network_unreachable",
      message: "Meridian could not reach the server.",
      recoveryAction: "Check your connection and try again.",
      status: 0,
    });
  }

  return _parse(response);
}

const ALLOWED_PROPOSAL_PATHS = new Set([
  "/api/meridian/funding-rules/propose",
  "/api/meridian/crew/bills",
  "/api/meridian/crew/rules",
]);

export async function meridianPropose(path, payload) {
  /* The only write channel in the browser: it creates a pending proposal
     for owner approval. It never executes anything and never touches Crew. */
  if (!ALLOWED_PROPOSAL_PATHS.has(path)) {
    throw new MeridianApiError({
      code: "mutations_forbidden",
      message: "This endpoint is not a proposal endpoint.",
      recoveryAction: "Only approval-gated proposal endpoints accept writes.",
      status: 0,
    });
  }

  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw error;
    }
    throw new MeridianApiError({
      code: "network_unreachable",
      message: "Meridian could not reach the server.",
      recoveryAction: "Check your connection and try again.",
      status: 0,
    });
  }

  return _parse(response);
}

export async function meridianMutate(action) {
  /* Write-routing channel (POST /api/actions/mutate). The server routes the
     mutation DIRECT (owner-direct/fully-specified -> executes) or to a PROPOSAL
     (AI-interpreted/composed/low-confidence/plan-level -> awaits approval). The
     response.routing_direct tells the caller which happened, so the UI can say
     "executed" vs "proposed — approve in Pending Actions." */
  let response;
  try {
    response = await fetch("/api/actions/mutate", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(action),
    });
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw error;
    }
    throw new MeridianApiError({
      code: "network_unreachable",
      message: "Meridian could not reach the server.",
      recoveryAction: "Check your connection and try again.",
      status: 0,
    });
  }
  return _parse(response);
}

async function _parse(response) {
  const contentType = response.headers.get("content-type") || "";
  let payload = null;
  if (contentType.includes("application/json")) {
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const detail = payload && payload.error ? payload.error : {};
    throw new MeridianApiError({
      code: detail.code,
      message: detail.message,
      recoveryAction: detail.recovery_action,
      status: response.status,
    });
  }

  if (payload === null) {
    throw new MeridianApiError({
      code: "invalid_response",
      message: "The server returned an unexpected response.",
      recoveryAction: "Reload the workspace.",
      status: response.status,
    });
  }

  return payload;
}

export function freshnessText(freshness) {
  if (!freshness) {
    return { state: "unavailable", label: "Freshness unknown" };
  }
  const state = freshness.status || "unavailable";
  if (state === "fresh") {
    return { state, label: `Updated ${formatTimestamp(freshness.last_updated_at)}` };
  }
  if (state === "stale") {
    const asOf = freshness.last_updated_at
      ? ` · updated ${formatTimestamp(freshness.last_updated_at)}`
      : "";
    return { state, label: `Stale${asOf}` };
  }
  return { state, label: "Not connected yet" };
}

/* Concept 03 draws a parchment banner above the day dividers: "Your money, in order."
   with an observed stamp underneath. The stamp is composed from the same freshness
   payload the rest of the shell uses rather than from a second notion of "current".

   Two honesty rules live here rather than in the view:
   - a stale graph says so IN the line ("Not current"), because "Your money, in order."
     read alone would present stale data as current;
   - an unconnected graph gets no banner at all, because that headline claims an order
     nothing has observed yet. Callers get null and hide the surface. */
export function activityBannerCopy(freshness) {
  const state = (freshness && freshness.status) || "unavailable";
  if (state === "unavailable") {
    return null;
  }
  const stamp = formatTimestamp(freshness && freshness.last_updated_at);
  // The stamp keeps its DATE. A time-only stamp reads as "today" on a ledger whose
  // newest row may be days old, which is exactly the stale-as-current claim this
  // banner must not make. The label binds to the stamp with a non-breaking space so a
  // narrow banner breaks at the separator instead of orphaning the meridiem.
  if (state === "stale") {
    return {
      title: "Your money, in order.",
      meta: stamp
        ? `Observed activity \u00b7 Last observed\u00a0${stamp} \u00b7 Not current`
        : "Observed activity \u00b7 Not current",
    };
  }
  return {
    title: "Your money, in order.",
    meta: stamp
      ? `Observed activity \u00b7 Updated\u00a0${stamp}`
      : "Observed activity",
  };
}

export function formatTimestamp(value) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
