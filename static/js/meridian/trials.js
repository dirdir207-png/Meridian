(() => {
  "use strict";
  const panel = document.querySelector("[data-trials-panel]");
  if (!panel) return;
  const list = panel.querySelector("[data-trials-list]");
  const status = panel.querySelector("[data-trials-status]");
  async function refresh() {
    status.textContent = "Loading trial deadlines…";
    try {
      const response = await fetch("/api/meridian/trials/deadlines", { credentials: "same-origin" });
      if (!response.ok) throw new Error("request failed");
      const data = await response.json();
      list.textContent = (data.deadlines || []).map((item) => `${item.service} — ${item.kind} — ${item.due_at}${item.overdue === "true" ? " — overdue" : ""}`).join("\n") || "No active trial deadlines.";
      status.textContent = "Read-only deadline view";
    } catch (_) { status.textContent = "Trial deadlines unavailable."; }
  }
  panel.querySelector("[data-trials-refresh]").addEventListener("click", refresh);
  refresh();
})();
