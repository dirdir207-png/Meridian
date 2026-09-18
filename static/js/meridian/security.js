/* Read-only Security & Data metadata for the Observatory Settings surface. */

import { MeridianApiError, meridianFetch } from "./api.js";

const root = document.querySelector("[data-security-root]");

function formatDate(value) {
  if (!value) {
    return "Never";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function renderPasskeys(passkeys) {
  const list = root.querySelector("[data-passkey-list]");
  const empty = root.querySelector("[data-passkeys-empty]");
  list.replaceChildren();
  empty.hidden = passkeys.length > 0;
  for (const passkey of passkeys) {
    const row = document.createElement("article");
    row.className = "m-passkey-row";
    row.dataset.passkeyRow = "";
    const name = document.createElement("strong");
    name.textContent = passkey.nickname || "Passkey";
    const meta = document.createElement("span");
    meta.textContent = [
      passkey.isSynced ? "Synced" : "This device",
      `Added ${formatDate(passkey.createdAt)}`,
      passkey.lastUsedAt ? `Last used ${formatDate(passkey.lastUsedAt)}` : "Not used yet",
    ].join(" · ");
    row.append(name, meta);
    list.append(row);
  }
}

async function load() {
  if (!root) {
    return;
  }
  const errorBox = root.querySelector("[data-security-error]");
  errorBox.hidden = true;
  root.setAttribute("aria-busy", "true");
  try {
    const payload = await meridianFetch("/api/auth/passkeys");
    renderPasskeys(payload.passkeys || []);
  } catch (error) {
    errorBox.textContent =
      error instanceof MeridianApiError
        ? `${error.message} ${error.recoveryAction}`
        : "Security details could not be loaded.";
    errorBox.hidden = false;
  } finally {
    root.removeAttribute("aria-busy");
  }
}

load();

window.MeridianSecurity = { load };
