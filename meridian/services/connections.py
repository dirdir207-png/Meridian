"""Presentation-safe read models for Meridian connection settings."""

from __future__ import annotations

from typing import Protocol

from meridian.connections import (
    ConnectionRecord,
    ConnectionRepository,
    ConnectionState,
    public_connection_id,
)


class FinancialConnectionSource(Protocol):
    def list_connection_freshness(self): ...


_GROUP = {
    "crew": "money",
    "simplefin": "money",
    "lunchflow": "money",
    "splitwise": "money",
    "gmail": "evidence",
    "icloud": "evidence",
    "calendar": "time",
}

_USES = {
    "crew": ("Balances", "Transactions", "Income", "Cash flow"),
    "simplefin": ("Balances", "Transactions", "Interest"),
    "lunchflow": ("Balances", "Transactions"),
    "splitwise": ("Reimbursements", "Shared expenses"),
    "gmail": ("Bills", "Statements", "Receipts"),
    "icloud": ("Bills", "Statements", "Receipts"),
    "calendar": ("Paydays", "Due dates", "Events"),
}

_PERMISSIONS = {
    "gmail": ("Read bills, statements, and receipts",),
    "icloud": ("Read bills, statements, and receipts",),
    "calendar": ("Read payday, due-date, travel, and event timing",),
}

_GROUP_LABELS = {
    "money": "Money",
    "evidence": "Evidence",
    "time": "Time",
}


def _authorization_payload(
    record: ConnectionRecord, credential: dict | None = None
) -> dict[str, object]:
    """One connection row.

    ``state`` is the AUTHORIZATION's state and stays as stored — reporting it as
    something else would be its own lie. ``credential`` is the separate, stronger fact
    that the credential was actually exercised and failed, so a row can honestly say
    "connected, but the credential needs re-authorizing" instead of implying it works.
    """
    payload: dict[str, object] = {
        "public_id": record.public_id,
        "kind": record.kind,
        "display_name": record.display_name,
        "group": _GROUP.get(record.kind, "evidence"),
        "state": record.state.value,
        "freshness": record.last_successful_at,
        "uses": list(_USES.get(record.kind, ())),
        "read_only": True,
    }
    if credential and credential.get("available") is False:
        payload["credential"] = {
            "available": False,
            "reason": credential.get("reason") or "unavailable",
            "observed_at": credential.get("observed_at"),
            # Copy-paste-ready owner guidance, keyed by the classified reason. Never a
            # raw provider error: the owner needs the ACTION, not the stack.
            "action": _REMEDY.get(
                str(credential.get("reason")), _REMEDY["unavailable"]
            ),
        }
    return payload


_REMEDY = {
    "reauthorize_required": (
        "Re-authorize this connection from Connections. The saved permission has "
        "expired or was withdrawn, so Meridian cannot read it."
    ),
    "authorization_rejected": (
        "Google rejected the saved permission. Re-authorize this connection."
    ),
    "provider_unreachable": (
        "The provider could not be reached. Meridian will retry automatically."
    ),
    "unavailable": (
        "This connection's credential could not be used. Re-authorize it, then check "
        "Connections again."
    ),
}


def _financial_payload(connection) -> dict[str, object]:
    provider = str(connection.provider).lower()
    healthy = connection.status in {"complete", "healthy"}
    return {
        "public_id": public_connection_id(provider, connection.connection_id),
        "kind": provider,
        "display_name": provider.title(),
        "group": "money",
        "state": "connected" if healthy else "failed",
        "freshness": connection.last_successful_at,
        "uses": list(_USES.get(provider, ("Balances", "Transactions"))),
        "read_only": True,
    }


def get_connection_detail(
    authorizations: ConnectionRepository, public_id: str
) -> dict[str, object] | None:
    record = authorizations.get(public_id)
    if record is None:
        return None
    permissions = list(_PERMISSIONS.get(record.kind, ("Read connected source data",)))
    return {
        **_authorization_payload(record),
        "permissions": permissions,
        "retention_days": record.retention_days,
        "can_revoke": record.state is not ConnectionState.REVOKED,
        "safeguards": {
            "read_only": True,
            "individually_revocable": True,
            "proposal_only_financial_changes": True,
        },
        "usage_explanation": (
            "Meridian may enrich forecasts and draft proposals from this source. "
            "It cannot change the source or execute financial actions."
        ),
    }


def build_connections(
    graph: FinancialConnectionSource,
    authorizations: ConnectionRepository,
    *,
    selected_id: str | None = None,
    db_path: str | None = None,
    credential_health: dict[str, dict] | None = None,
) -> dict[str, object]:
    """Assemble the Connections view.

    ``credential_health`` carries findings from REAL credential use (the evidence poll),
    keyed by kind. It exists because a stored authorization is not evidence that its
    token still works: measured 2026-09-20, this view reported Gmail "Connected" while
    all four Gmail refresh tokens had been failing with HTTP 400 for days. When a kind
    has a recorded failure the row keeps its stored `state` (that IS the authorization's
    state, honestly reported) but gains an explicit `credential` block saying the
    credential is unusable, so the surface cannot imply a working connection.
    """
    health = credential_health or {}
    rows = [_financial_payload(item) for item in graph.list_connection_freshness()]
    rows.extend(
        _authorization_payload(item, health.get(item.kind)) for item in authorizations.list_all()
    )
    # R27: attach per-account OAuth identities (multi-account chooser data).
    oauth_accounts = {}
    if db_path:
        try:
            from meridian.connectors.google_auth import OAuthTokenStore

            store = OAuthTokenStore(db_path)
            for kind in ("gmail", "calendar"):
                oauth_accounts[kind] = store.list_accounts(kind=kind)
        except Exception:  # pragma: no cover - token store optional
            oauth_accounts = {}
    groups = []
    for kind in ("money", "evidence", "time"):
        groups.append(
            {
                "kind": kind,
                "label": _GROUP_LABELS[kind],
                "connections": [row for row in rows if row["group"] == kind],
                "oauth_accounts": oauth_accounts.get(
                    "gmail" if kind == "evidence" else ("calendar" if kind == "time" else ""), []
                ),
            }
        )
    return {
        "groups": groups,
        "selected": (
            get_connection_detail(authorizations, selected_id)
            if selected_id is not None
            else None
        ),
        "safeguards": {
            "read_only": True,
            "individually_revocable": True,
            "proposal_only_financial_changes": True,
        },
    }
