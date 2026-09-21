"""Ingestion-route status in Settings: calendar via Composio, and iCloud over IMAP.

These two are NOT stored authorizations, and the whole point of this read model is that it
never pretends they are. The load-bearing rule, stated by the owner on 2026-09-21:

    "For Composio (Live) will strictly mean the composio connection is still current with the
    harness, not that it is live and continuously polling."

The failure this guards against is a status label that outlives its definition: "(Live)" read
by anyone who assumes it means continuous polling would overstate what Meridian is doing. So
the definition travels with the payload, and these tests fail if a label is present without it.
"""
from datetime import datetime, timedelta, timezone

from meridian.services.ingestion_routes import (
    COMPOSIO_LIVE_MEANING,
    LIVE_WINDOW_HOURS,
    build_ingestion_routes,
)

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)


def _routes(*, db_path=None, icloud_configured=False, credential_health=None, now=NOW):
    return {
        route["kind"]: route
        for route in build_ingestion_routes(
            db_path=db_path,
            icloud_configured=icloud_configured,
            credential_health=credential_health,
            now=now,
        )
    }


def test_both_routes_are_always_reported():
    """A route that vanished when its evidence went stale would hide exactly the condition
    the owner needs to see."""
    routes = _routes()
    assert set(routes) == {"composio", "icloud"}


def test_composio_is_not_called_live_when_nothing_has_ever_been_observed():
    route = _routes()["composio"]
    assert route["state"] != "connected"
    assert route["state_label"] == "Not observed yet"
    assert route["freshness"] is None
    assert "nothing to call current" in route["status_note"]


def test_composio_is_live_only_within_the_daily_schedule_window(tmp_path):
    from meridian.calendar_context import CalendarContextStore
    from meridian.db import run_migrations

    db = tmp_path / "m.db"
    run_migrations(str(db))
    store = CalendarContextStore(str(db))

    # A read 6 hours ago: a daily schedule explains this, so it is current.
    recent = (NOW - timedelta(hours=6)).isoformat().replace("+00:00", "Z")
    store.upsert(source="composio_calendar", external_id="e1", starts_at="2026-09-22",
                 ends_at="2026-09-22", summary="Travel", source_link="calendar://event/e1",
                 observed_at=recent)
    live = _routes(db_path=str(db))["composio"]
    assert live["state"] == "connected" and live["state_label"] == "Live"
    assert live["freshness"] == recent

    # A read older than the window: a whole day's run was missed, so it is NOT current.
    stale = (NOW - timedelta(hours=LIVE_WINDOW_HOURS + 24)).isoformat().replace("+00:00", "Z")
    store.upsert(source="composio_calendar", external_id="e1", starts_at="2026-09-22",
                 ends_at="2026-09-22", summary="Travel (moved)", source_link="calendar://event/e1",
                 observed_at=stale)
    late = _routes(db_path=str(db))["composio"]
    assert late["state"] == "attention" and late["state_label"] == "Not current"
    assert "beyond the" in late["status_note"]


def test_the_live_window_tolerates_one_missed_run_but_not_two():
    """The window is derived from the intended DAILY schedule, not chosen for looks."""
    assert LIVE_WINDOW_HOURS == 48
    # A daily poll can legitimately be ~24h apart; 48h is one missed run. Anything longer and
    # "still current with the harness" would stop meaning anything.
    assert 24 < LIVE_WINDOW_HOURS <= 48


def test_the_live_definition_always_travels_with_the_label():
    """THE guard for this slice. If a route can render the word 'Live' without the sentence
    that scopes it, the label is free to be misread as continuous polling."""
    routes = _routes()
    composio = routes["composio"]
    assert composio["live_meaning"] == COMPOSIO_LIVE_MEANING
    assert "still current with the harness" in composio["live_meaning"]
    assert "not continuously" in composio["live_meaning"]
    for route in routes.values():
        # Every route carries some pinned definition or note; none is a bare label.
        assert route.get("live_meaning") or route.get("meaning") or route.get("status_note")


def test_routes_declare_they_are_not_authorizations():
    for route in _routes().values():
        assert route["route"] is True
        assert route["read_only"] is True
        # A route must not carry fields that only a stored authorization has, or the view
        # would start treating it as one.
        assert "credential" not in route


def test_icloud_reports_configuration_and_never_claims_a_successful_read():
    unconfigured = _routes(icloud_configured=False)["icloud"]
    assert unconfigured["state_label"] == "Not configured"
    assert "not reading this source" in unconfigured["status_note"]

    configured = _routes(icloud_configured=True)["icloud"]
    assert configured["state_label"] == "Configured"
    # Configuration is not proof of a read; the note must say the freshness is the MAIL LANE's.
    assert configured["freshness_label"] == "Mail lane last observed"


def test_icloud_credential_failure_outranks_configuration():
    """A configured mailbox whose read is failing must not read as fine -- this is the same
    class of lie as a green 'Connected' over a dead token."""
    route = _routes(
        icloud_configured=True,
        credential_health={"icloud": {"available": False, "reason": "reauthorize_required"}},
    )["icloud"]
    assert route["state"] == "attention"
    assert route["state_label"] == "Needs attention"
    assert "failed" in route["status_note"]


def test_route_lookups_fail_soft_so_settings_cannot_be_broken_by_them():
    """A status lookup must never take the page down; a bad path reports absence."""
    routes = _routes(db_path="/nonexistent/definitely/not/a/db.sqlite")
    assert routes["composio"]["state_label"] == "Not observed yet"
    assert routes["icloud"]["freshness"] is None


def test_routes_join_the_connections_view_in_their_own_groups():
    from meridian.services.connections import _GROUP

    assert _GROUP["composio"] == "time"
    assert _GROUP["icloud"] == "evidence"


def test_the_connections_endpoint_actually_serves_both_routes(monkeypatch, tmp_path):
    """Integration, not unit: the read model can be perfect and still not be wired up.

    This exercises the real route so a wiring mistake (a config key never registered, a
    service never called) fails here rather than silently shipping an absent row.
    """
    import os
    import sys

    if "app" not in sys.modules:
        os.environ.setdefault("DB_FILE", str(tmp_path / "savings_data.db"))
    import app as simplecrew

    monkeypatch.setattr(simplecrew, "_background_thread_started", True)
    monkeypatch.setattr(
        simplecrew.login_manager,
        "_user_callback",
        lambda value: simplecrew.User(value, "route-user", "route@example.com"),
    )
    client = simplecrew.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "route-user"
        session["_fresh"] = True

    response = client.get("/api/meridian/settings/connections")
    assert response.status_code == 200
    payload = response.get_json()

    by_kind = {row["kind"]: row for group in payload["groups"] for row in group["connections"]}
    assert "composio" in by_kind, by_kind.keys()
    assert "icloud" in by_kind, by_kind.keys()

    # The label is never served without the sentence that defines it.
    assert by_kind["composio"]["live_meaning"] == COMPOSIO_LIVE_MEANING
    assert by_kind["composio"]["state_label"]
    assert by_kind["composio"]["route"] is True
    # And they land in the right groups, so they appear where the owner expects them.
    groups = {
        group["kind"]: {row["kind"] for row in group["connections"]}
        for group in payload["groups"]
    }
    assert "composio" in groups["time"]
    assert "icloud" in groups["evidence"]

