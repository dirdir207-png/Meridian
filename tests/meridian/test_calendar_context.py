"""Calendar context: read-only observation through a single Composio-mediated adapter.

Scope decision (owner, 2026-09-21): calendar events are read-only CONTEXT. They are never
matched to a transaction, never treated as an obligation, and never written to the evidence
store. The calendar's ONLY adapter is the Composio route -- the in-app Google OAuth transport
is deliberately not built, so Meridian holds no Google credential for calendar and is not
exposed to Google's refresh-token lifetime.

These tests are mostly about ABSENCE, because that is what can silently erode: a later edit
that adds a matching column, a second write path, or an extra field on the way through would
all be easy to miss and would each widen what this capability can do.
"""
import json
import sqlite3
from pathlib import Path

import pytest

from meridian.calendar_context import (
    CALENDAR_CONTEXT_ENABLED_ENV,
    SOURCE_COMPOSIO,
    CalendarContextDisabled,
    CalendarContextStore,
    calendar_context_enabled,
    default_window,
    ingest_calendar_context,
)
from meridian.db import run_migrations

ROOT = Path(__file__).resolve().parents[2]


class FakeCalendarTransport:
    """Stand-in for the Composio-fed adapter: same interface, no network."""

    def __init__(self, events, *, revoked: bool = False):
        self._events = list(events)
        self._revoked = revoked
        self.scopes = None

    def configure(self, *, scopes):
        self.scopes = tuple(scopes)

    def list_events(self, *, cursor, time_min, time_max):
        if self._revoked:
            return {"events": [], "next_cursor": None}
        return {"events": self._events, "next_cursor": None}


def _event(event_id="e1", start="2026-09-10T09:00:00Z", end="2026-09-10T10:00:00Z",
           summary="Travel"):
    return {"id": event_id, "start": start, "end": end, "summary": summary}


@pytest.fixture()
def store(tmp_path):
    db_path = tmp_path / "calendar.db"
    run_migrations(str(db_path))
    return CalendarContextStore(str(db_path))


# --------------------------------------------------------------------------------------
# The capability is OFF unless explicitly enabled
# --------------------------------------------------------------------------------------

def test_capability_is_off_by_default_and_says_so_loudly():
    assert calendar_context_enabled({}) is False
    for raw in ("0", "", "no", "off", "false"):
        assert calendar_context_enabled({CALENDAR_CONTEXT_ENABLED_ENV: raw}) is False
    for raw in ("1", "true", "yes", "on", "TRUE"):
        assert calendar_context_enabled({CALENDAR_CONTEXT_ENABLED_ENV: raw}) is True


def test_ingesting_while_disabled_refuses_rather_than_silently_doing_nothing(store):
    """A caller that believes it ingested when it did not is the failure this prevents."""
    with pytest.raises(CalendarContextDisabled):
        ingest_calendar_context(
            store=store,
            transport=FakeCalendarTransport([_event()]),
            source=SOURCE_COMPOSIO,
            as_of="2026-09-10",
            enabled=False,
        )
    assert store.count() == 0


# --------------------------------------------------------------------------------------
# It observes, attributes, and dedupes
# --------------------------------------------------------------------------------------

def test_ingest_records_observed_events_with_provenance(store):
    report = ingest_calendar_context(
        store=store,
        transport=FakeCalendarTransport([_event(), _event("e2", summary="Rent due")]),
        source=SOURCE_COMPOSIO,
        as_of="2026-09-10",
        enabled=True,
        observed_at="2026-09-10T12:00:00Z",
    )
    assert report["events_read"] == 2
    assert report["inserted"] == 2
    assert report["rows_added"] == 2
    # Reports what was OBSERVED, not what was attempted.
    assert report["rows_after"] == store.count() == 2

    rows = store.list_between(start="2026-09-01", end="2026-10-01")
    assert [row["external_id"] for row in rows] == ["e1", "e2"]
    assert all(row["source"] == SOURCE_COMPOSIO for row in rows)


def test_re_observing_the_same_event_does_not_duplicate_or_look_new(store):
    payload = FakeCalendarTransport([_event()])
    first = ingest_calendar_context(store=store, transport=payload, source=SOURCE_COMPOSIO,
                                   as_of="2026-09-10", enabled=True)
    second = ingest_calendar_context(store=store, transport=payload, source=SOURCE_COMPOSIO,
                                     as_of="2026-09-10", enabled=True)
    assert first["inserted"] == 1
    assert second["unchanged"] == 1 and second["rows_added"] == 0
    assert store.count() == 1


def test_a_changed_event_updates_in_place_and_is_reported_as_updated(store):
    ingest_calendar_context(store=store, transport=FakeCalendarTransport([_event()]),
                            source=SOURCE_COMPOSIO, as_of="2026-09-10", enabled=True)
    report = ingest_calendar_context(
        store=store,
        transport=FakeCalendarTransport([_event(summary="Travel (moved)")]),
        source=SOURCE_COMPOSIO, as_of="2026-09-10", enabled=True,
    )
    assert report["updated"] == 1 and report["inserted"] == 0
    assert store.count() == 1
    assert store.list_between(start="2026-09-01", end="2026-10-01")[0]["summary"] == "Travel (moved)"


def test_two_routes_observing_one_event_stay_separable(store):
    """Provenance is preserved, not collapsed: collapsing it would destroy the trace D-016
    guardrail 3 requires."""
    for source in (SOURCE_COMPOSIO, "some_other_route"):
        ingest_calendar_context(store=store, transport=FakeCalendarTransport([_event()]),
                                source=source, as_of="2026-09-10", enabled=True)
    assert store.count() == 2
    assert store.count_by_source() == {SOURCE_COMPOSIO: 1, "some_other_route": 1}


def test_an_empty_read_is_zero_events_and_not_an_error(store):
    """A provider returning nothing is a normal outcome, not a failure.

    Note on `revoked`: that flag belongs to the CONNECTOR, not the transport, and the intake
    builds a fresh connector per run -- so a revoked-connector path is not reachable from here
    by design, and `test_calendar.py` covers it directly. What IS reachable is an empty page,
    and it must read as "observed nothing" rather than as success-with-unknown-effect.
    """
    report = ingest_calendar_context(
        store=store, transport=FakeCalendarTransport([], revoked=True),
        source=SOURCE_COMPOSIO, as_of="2026-09-10", enabled=True,
    )
    assert report["events_read"] == 0
    assert report["rows_added"] == 0
    assert report["revoked"] is False  # connector-level; a fresh connector is not revoked
    assert store.count() == 0


# --------------------------------------------------------------------------------------
# The safety boundary, asserted as ABSENCE
# --------------------------------------------------------------------------------------

def test_the_store_has_no_column_that_could_match_an_event_to_money(store):
    """The schema is the enforcement: matching cannot begin without a deliberate migration."""
    with sqlite3.connect(store.db_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(calendar_context_events)")]
    forbidden = ("amount", "commitment", "transaction", "charge", "bill", "cents", "total")
    for name in columns:
        assert not any(token in name.lower() for token in forbidden), name


def test_the_module_exposes_no_matching_or_linking_api():
    """A capability cannot acquire matching by having the function available."""
    import meridian.calendar_context as module

    surface = [name for name in dir(module) if not name.startswith("_")]
    for forbidden in ("match", "link", "exposure", "obligation", "propose"):
        assert not any(forbidden in name.lower() for name in surface), forbidden


def test_calendar_context_never_touches_the_evidence_store(store, tmp_path):
    """It writes to its own table and nothing else. If it ever wrote evidence rows, this
    would see them, because the evidence table would have to exist in the same database."""
    ingest_calendar_context(store=store, transport=FakeCalendarTransport([_event()]),
                            source=SOURCE_COMPOSIO, as_of="2026-09-10", enabled=True)
    with sqlite3.connect(store.db_path) as connection:
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    populated = set()
    for table in tables:
        if table in ("schema_migrations", "sqlite_sequence"):
            continue
        with sqlite3.connect(store.db_path) as connection:
            if connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]:
                populated.add(table)
    assert populated == {"calendar_context_events"}, populated


def test_minimum_fields_only_the_connector_drops_the_rest(store):
    """The in-repo connector already drops description/attendees; assert it survives the
    full ingest path, because that is the field discipline the lane boundary depends on."""
    transport = FakeCalendarTransport([{
        "id": "e1", "start": "2026-09-10T09:00:00Z", "end": "2026-09-10T10:00:00Z",
        "summary": "Travel", "description": "Private itinerary",
        "attendees": ["private@example.com"],
    }])
    ingest_calendar_context(store=store, transport=transport, source=SOURCE_COMPOSIO,
                            as_of="2026-09-10", enabled=True)
    with sqlite3.connect(store.db_path) as connection:
        blob = json.dumps([dict(zip(
            [d[0] for d in connection.execute("SELECT * FROM calendar_context_events").description],
            row)) for row in connection.execute("SELECT * FROM calendar_context_events")])
    assert "Private itinerary" not in blob
    assert "private@example.com" not in blob


# --------------------------------------------------------------------------------------
# Honest liveness
# --------------------------------------------------------------------------------------

def test_liveness_reports_observation_and_cannot_claim_the_scheduler_is_healthy(store):
    before = store.liveness()
    assert before["has_ever_observed"] is False and before["last_observed_at"] is None

    ingest_calendar_context(store=store, transport=FakeCalendarTransport([_event()]),
                            source=SOURCE_COMPOSIO, as_of="2026-09-10", enabled=True,
                            observed_at="2026-09-10T12:00:00Z")
    after = store.liveness()
    assert after["has_ever_observed"] is True
    assert after["last_observed_at"] == "2026-09-10T12:00:00Z"
    assert after["total_events"] == 1
    assert "schedule" not in after and "healthy" not in after


# --------------------------------------------------------------------------------------
# The Composio adapter satisfies the app's own interface
# --------------------------------------------------------------------------------------

def test_script_transport_refuses_any_scope_but_read_only():
    """A routing mistake must not be able to upgrade this to a write scope."""
    from scripts.calendar_context_ingest import ComposioCalendarTransport

    transport = ComposioCalendarTransport([])
    transport.configure(scopes=("https://www.googleapis.com/auth/calendar.events.readonly",))
    with pytest.raises(ValueError):
        ComposioCalendarTransport([]).configure(
            scopes=("https://www.googleapis.com/auth/calendar",)
        )
    with pytest.raises(ValueError):
        ComposioCalendarTransport([]).configure(scopes=())


def test_script_transport_normalises_all_day_and_timed_events_and_stays_in_window():
    """Google returns `date` for all-day and `dateTime` for timed events, and an all-day
    event has no time -- the pitfalls that make a naive read silently miss or shift events."""
    from scripts.calendar_context_ingest import ComposioCalendarTransport

    transport = ComposioCalendarTransport([
        {"id": "timed", "start": {"dateTime": "2026-09-10T09:00:00-04:00"},
         "end": {"dateTime": "2026-09-10T10:00:00-04:00"}, "summary": "Timed"},
        {"id": "allday", "start": {"date": "2026-09-12"}, "end": {"date": "2026-09-13"},
         "summary": "All day"},
        {"id": "outside", "start": {"date": "2027-01-01"}, "end": {"date": "2027-01-02"},
         "summary": "Outside the window"},
    ])
    payload = transport.list_events(cursor=None, time_min="2026-09-07", time_max="2026-10-10")
    ids = [event["id"] for event in payload["events"]]
    assert ids == ["timed", "allday"]
    assert payload["events"][1]["start"] == "2026-09-12"


def test_script_transport_passes_only_the_minimum_fields():
    from scripts.calendar_context_ingest import ComposioCalendarTransport

    transport = ComposioCalendarTransport([{
        "id": "e1", "start": {"dateTime": "2026-09-10T09:00:00Z"},
        "end": {"dateTime": "2026-09-10T10:00:00Z"}, "summary": "Travel",
        "description": "Private itinerary", "attendees": ["private@example.com"],
        "location": "Somewhere private",
    }])
    payload = transport.list_events(cursor=None, time_min="2026-09-07", time_max="2026-10-10")
    assert set(payload["events"][0]) == {"id", "start", "end", "summary"}
    assert "Private itinerary" not in json.dumps(payload)
    assert "private@example.com" not in json.dumps(payload)


def test_script_refuses_to_run_while_disabled_and_reports_status_read_only(tmp_path, capsys):
    from scripts.calendar_context_ingest import main

    db_path = tmp_path / "calendar.db"
    run_migrations(str(db_path))
    events = tmp_path / "events.json"
    events.write_text(json.dumps([_event()]), encoding="utf-8")

    code = main(["--events", str(events), "--db", str(db_path), "--as-of", "2026-09-10"])
    assert code == 2
    assert "Refusing to run" in capsys.readouterr().err
    assert CalendarContextStore(str(db_path)).count() == 0

    # --status is read-only and works regardless of the gate.
    assert main(["--status", "--db", str(db_path)]) == 0
    assert json.loads(capsys.readouterr().out)["has_ever_observed"] is False


def test_script_end_to_end_writes_observed_context(tmp_path, capsys):
    from scripts.calendar_context_ingest import main

    db_path = tmp_path / "calendar.db"
    run_migrations(str(db_path))
    events = tmp_path / "events.json"
    events.write_text(json.dumps([
        {"id": "e1", "start": {"dateTime": "2026-09-10T09:00:00Z"},
         "end": {"dateTime": "2026-09-10T10:00:00Z"}, "summary": "Travel",
         "description": "dropped"},
    ]), encoding="utf-8")

    assert main(["--events", str(events), "--db", str(db_path),
                 "--as-of", "2026-09-10", "--enable"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["inserted"] == 1 and report["rows_after"] == 1
    assert report["source"] == SOURCE_COMPOSIO
    assert report["fields_dropped_by_minimum_field_rule"] == 1
    assert CalendarContextStore(str(db_path)).count() == 1


def test_default_window_is_bounded():
    """An unbounded read of someone's calendar is the 'unnecessary data' the lane excludes."""
    start, end = default_window(as_of="2026-09-10")
    assert start == "2026-09-03" and end == "2026-10-10"
