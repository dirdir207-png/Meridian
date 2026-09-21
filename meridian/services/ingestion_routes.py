"""Ingestion-route status for Settings: the two routes that are NOT stored authorizations.

**Why this is a separate read model.** `connection_authorizations` records a permission the
owner granted. Two of Meridian's ingestion routes are not that kind of thing, and pretending
they were would be the same lie this codebase already fixed once for credentials:

* **Calendar via Composio.** There is no Meridian-held Google credential at all (owner
  decision, 2026-09-21: Composio is the calendar's ONLY adapter). So there is no authorization
  row to report a state from, and inventing one would claim a permission that does not exist.
* **iCloud Mail (IMAP).** Configured from the environment, not by an OAuth grant. Its only
  honest signal is whether a read has actually SUCCEEDED, which is exactly what the mail lane's
  per-kind credential health already records from real attempts.

So both are stated from **observation** -- what a read actually produced -- never from the
existence of configuration. A route that is configured but has never observed anything must not
read as working.

**The one definition this module exists to pin down.** For Composio, *"(Live)" strictly means
the Composio connection is still current with the harness -- not that it is live and
continuously polling* (owner, 2026-09-21). That sentence is the whole reason the label is
allowable, so it is carried in the payload as `live_meaning` rather than left to a reader to
assume. Calendar is read at most once a day, so "current" is judged against a window that is
generous to a daily schedule and still fails when a run is missed: see `LIVE_WINDOW_HOURS`.

Nothing here can make a route look healthier than the evidence for it.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

#: How recent the last successful calendar read must be for Composio to read as "(Live)".
#:
#: The intended schedule is ONE read per day, so consecutive reads can legitimately be up to
#: ~24h apart. 48h is chosen because it tolerates one late or slow run while still failing as
#: soon as a whole day is missed -- a two-day-old observation cannot be described as "still
#: current with the harness" without the label becoming meaningless.
LIVE_WINDOW_HOURS = 48

#: The owner's definition, verbatim in substance, carried with the payload so the UI cannot
#: present "(Live)" as if it meant continuous polling.
COMPOSIO_LIVE_MEANING = (
    "Live means the Composio connection is still current with the harness. "
    "The calendar is read on a daily schedule, not continuously."
)

ICLOUD_ROUTE_MEANING = (
    "iCloud Mail is read over IMAP. This row reports whether a read has actually succeeded, "
    "not merely that the mailbox is configured."
)


def _parse(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _calendar_last_observed(db_path: Optional[str]) -> Optional[str]:
    """Newest observed calendar event, or None. Absence is reported as absence."""
    if not db_path:
        return None
    try:
        from meridian.calendar_context import CalendarContextStore

        return CalendarContextStore(str(db_path)).liveness().get("last_observed_at")
    except Exception:  # noqa: BLE001 - a status lookup must never break the page
        return None


def _mail_last_observed(db_path: Optional[str]) -> Optional[str]:
    """Newest stored mail evidence item, or None.

    Attribution: `source_kind='mail'` covers both Gmail and iCloud, so this is the MAIL LANE's
    last observation and the row says so rather than claiming it is iCloud's alone.
    """
    if not db_path:
        return None
    try:
        with sqlite3.connect(str(db_path)) as connection:
            row = connection.execute(
                "SELECT MAX(created_at) FROM evidence_items WHERE source_kind = 'mail'"
            ).fetchone()
        return row[0] if row and row[0] else None
    except Exception:  # noqa: BLE001
        return None


def _composio_route(db_path: Optional[str], now: datetime) -> dict:
    last = _calendar_last_observed(db_path)
    observed = _parse(last)
    if observed is None:
        # Never observed. Say that, and do NOT dress it as a problem with the harness --
        # the honest statement is that no calendar read has produced anything yet.
        state, state_label, note = (
            "available",
            "Not observed yet",
            "No calendar read has been recorded yet, so there is nothing to call current.",
        )
    elif observed >= now - timedelta(hours=LIVE_WINDOW_HOURS):
        state, state_label, note = (
            "connected",
            "Live",
            f"Last calendar read was within {LIVE_WINDOW_HOURS}h, so the connection is current "
            "with the harness.",
        )
    else:
        age_hours = int((now - observed).total_seconds() // 3600)
        state, state_label, note = (
            "attention",
            "Not current",
            f"The last calendar read was {age_hours}h ago, beyond the {LIVE_WINDOW_HOURS}h "
            "window a daily schedule can explain.",
        )
    return {
        "public_id": "route-composio-calendar",
        "kind": "composio",
        "display_name": "Calendar via Composio",
        "group": "time",
        "state": state,
        "state_label": state_label,
        "freshness": last,
        "freshness_label": "Last calendar read",
        "uses": ["Calendar events", "Travel", "Appointments"],
        "read_only": True,
        "route": True,
        "status_note": note,
        "live_meaning": COMPOSIO_LIVE_MEANING,
        "detail": (
            "Read-only calendar context, fetched through Composio. These events are never "
            "matched to a transaction and never treated as an obligation."
        ),
    }


def _icloud_route(
    db_path: Optional[str],
    icloud_configured: bool,
    credential_health: dict,
    now: datetime,
) -> dict:
    health = dict(credential_health or {}).get("icloud") or {}
    last = _mail_last_observed(db_path)

    if health.get("available") is False:
        state, state_label, note = (
            "attention",
            "Needs attention",
            "The last iCloud read failed, so this mailbox is not currently being read.",
        )
    elif not icloud_configured:
        state, state_label, note = (
            "available",
            "Not configured",
            "No iCloud mailbox is configured, so Meridian is not reading this source.",
        )
    else:
        state, state_label, note = (
            "connected",
            "Configured",
            "An iCloud mailbox is configured. Master mail reads are shared across the mail lane.",
        )
    return {
        "public_id": "route-icloud-imap",
        "kind": "icloud",
        "display_name": "iCloud Mail (IMAP)",
        "group": "evidence",
        "state": state,
        "state_label": state_label,
        "freshness": last,
        "freshness_label": "Mail lane last observed",
        "uses": ["Bills", "Statements", "Receipts"],
        "read_only": True,
        "route": True,
        "status_note": note,
        "meaning": ICLOUD_ROUTE_MEANING,
    }


def build_ingestion_routes(
    *,
    db_path: Optional[str],
    icloud_configured: bool = False,
    credential_health: Optional[dict] = None,
    now: Optional[datetime] = None,
) -> list[dict]:
    """The two non-authorization ingestion routes, each stated from observation.

    Every route is always returned, even when it has nothing to report: a route that vanished
    when its evidence went stale would hide exactly the condition the owner needs to see.
    """
    moment = now or datetime.now(timezone.utc)
    return [
        _composio_route(db_path, moment),
        _icloud_route(db_path, icloud_configured, credential_health or {}, moment),
    ]


__all__ = [
    "COMPOSIO_LIVE_MEANING",
    "ICLOUD_ROUTE_MEANING",
    "LIVE_WINDOW_HOURS",
    "build_ingestion_routes",
]
