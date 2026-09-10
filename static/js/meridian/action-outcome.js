/* Honest presentation of the durable action pipeline.

   HTTP success only means the server returned an action record. The record's
   state decides whether the UI may claim success. In particular, `executed`
   still awaits verification, and `failed` can carry an uncertain-write marker
   that must never invite a blind resend. */

function resultMessage(action) {
  const result = action && action.result;
  return result && typeof result.error === "string" && result.error.trim()
    ? result.error.trim()
    : "";
}

export function describeActionOutcome(response, options = {}) {
  const action = response && response.action && typeof response.action === "object"
    ? response.action
    : {};
  const state = typeof action.state === "string" ? action.state : "unknown";

  if (!response || response.routing_direct !== true) {
    return {
      state: state === "unknown" ? "proposed" : state,
      tone: "pending",
      message: options.proposalMessage || "Proposed — approve it in Actions & Approvals.",
      refresh: false,
    };
  }

  if (state === "verified") {
    return {
      state,
      tone: "ok",
      message: options.verifiedMessage || "Action completed and was verified.",
      refresh: true,
    };
  }

  if (state === "executed") {
    return {
      state,
      tone: "pending",
      message: "The action was sent, but verification is still pending. Do not submit it again; check Actions & Approvals for the final outcome.",
      refresh: false,
    };
  }

  if (state === "executing") {
    return {
      state,
      tone: "pending",
      message: "The action is in progress. Do not submit it again; check Actions & Approvals for the final outcome.",
      refresh: false,
    };
  }

  if (state === "proposed" || state === "approved") {
    return {
      state,
      tone: "pending",
      message: state === "approved"
        ? "Approved and awaiting execution in Actions & Approvals."
        : "Proposed — approve it in Actions & Approvals.",
      refresh: false,
    };
  }

  if (state === "failed") {
    const detail = resultMessage(action) || "Action failed.";
    const uncertain = Boolean(action.result && action.result.verify_state);
    return {
      state,
      tone: "error",
      message: uncertain
        ? `${detail} Check current Crew state before trying again.`
        : `${detail} Review Actions & Approvals before deciding whether to try again.`,
      refresh: false,
    };
  }

  if (state === "rejected") {
    return {
      state,
      tone: "error",
      message: "The action was rejected and did not run. Review Actions & Approvals before creating another request.",
      refresh: false,
    };
  }

  if (state === "expired") {
    return {
      state,
      tone: "error",
      message: "The approval expired and the action did not run. Review current state before creating another request.",
      refresh: false,
    };
  }

  return {
    state,
    tone: "error",
    message: "The server returned no trustworthy action outcome. Check Actions & Approvals and do not submit it again yet.",
    refresh: false,
  };
}
