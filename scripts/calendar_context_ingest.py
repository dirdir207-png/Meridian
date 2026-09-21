#!/usr/bin/env python
"""Feed Composio-fetched calendar events into Meridian as read-only context.

Run with `.venv311/bin/python scripts/calendar_context_ingest.py --events <file.json>`.

**What this is.** The calendar's ONLY adapter is this Composio-mediated route (owner
decision, 2026-09-21). The in-app Google OAuth transport is deliberately NOT built for
calendar, so Meridian holds no Google credential for it and is not exposed to Google's
refresh-token lifetime.

**What this deliberately is NOT.** It is not a service and does not pretend to be one. It
makes no provider call itself: it reads a file of events that something else already fetched,
and it writes no rows itself -- it replays them through a transport satisfying the same
`CalendarTransport` interface the app uses and hands them to the SAME
`ingest_calendar_context` the app calls. This mirrors `scripts/backfill_charge_evidence.py`,
the worked example D-016 guardrail 3 cites, and it is what keeps this from being a
side-channel write. Provenance (`source`) is recorded on every row either way.

**Honest liveness (D-016 guardrail 4).** Whoever schedules this is responsible for its
liveness, and the store can only report what it OBSERVED: `--status` prints the newest
observed event and the count, so a daily run that has quietly stopped shows up as STALE
rather than as healthy. This script cannot and does not claim the schedule is running.

**Scope.** Read-only context: events are never matched to a transaction, never treated as an
obligation, and never written to the evidence store. No financial table is touched. No
authority is exercised or extended.

**Privacy.** Only four fields per event ever cross into the store: id, start, end, summary.
Anything else in the input -- descriptions, attendees, locations, conference links -- is
DROPPED here rather than stored, which is the same minimum-field discipline the in-repo
connector already applies and has a test for.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meridian.calendar_context import (  # noqa: E402
    CALENDAR_CONTEXT_ENABLED_ENV,
    SOURCE_COMPOSIO,
    CalendarContextDisabled,
    CalendarContextStore,
    calendar_context_enabled,
    default_window,
    ingest_calendar_context,
)

#: The only fields that may cross into the store. Everything else is dropped.
MINIMUM_FIELDS = ("id", "start", "end", "summary")


class ComposioCalendarTransport:
    """Serves staged Composio results through the app's own `CalendarTransport` interface.

    Satisfying the app's interface -- rather than writing rows -- is the whole point: the
    intake's dedupe, provenance and minimum-field rules all still apply, so external data
    cannot take a different path into the store than the app's own would.
    """

    #: The app's connector only ever configures the read-only calendar scope. Refusing
    #: anything else means a routing mistake cannot silently upgrade this to a write scope.
    _ALLOWED_SCOPES = frozenset({"https://www.googleapis.com/auth/calendar.events.readonly"})

    def __init__(self, records, *, revoked: bool = False):
        self._records = list(records)
        self._revoked = revoked
        self.scopes = None

    def configure(self, *, scopes):
        requested = set(scopes or ())
        if not requested or not requested <= self._ALLOWED_SCOPES:
            raise ValueError(
                "ComposioCalendarTransport only serves the read-only calendar scope"
            )
        self.scopes = tuple(scopes)

    def list_events(self, *, cursor, time_min, time_max):
        if self._revoked:
            return {"events": [], "next_cursor": None}
        window_start = str(time_min)[:10]
        events = []
        for record in self._records:
            start = _start_of(record)
            if not start:
                continue
            # Bounded to the requested window, so a staged file cannot smuggle in an
            # unbounded read of someone's calendar.
            if start < window_start or start >= str(time_max)[:10]:
                continue
            events.append({
                "id": str(record.get("id") or ""),
                "start": start,
                "end": _end_of(record) or start,
                # The summary is the only human-readable field that reaches the store.
                "summary": str(record.get("summary") or "Event"),
            })
        return {"events": events, "next_cursor": None}


def _start_of(record: dict) -> str:
    """Google returns `dateTime` for timed events and `date` for all-day ones."""
    start = record.get("start")
    if isinstance(start, dict):
        return str(start.get("dateTime") or start.get("date") or "")
    return str(start or "")


def _end_of(record: dict) -> str:
    end = record.get("end")
    if isinstance(end, dict):
        return str(end.get("dateTime") or end.get("date") or "")
    return str(end or "")


def _load_events(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("events") or payload.get("items") or []
    if not isinstance(payload, list):
        raise SystemExit(f"{path}: expected a JSON list of events")
    return [record for record in payload if isinstance(record, dict)]


def _dropped_fields(records: list[dict]) -> int:
    """How many fields the minimum-field rule removed. A count, never their content."""
    return sum(len([k for k in record if k not in MINIMUM_FIELDS]) for record in records)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--events", type=Path, help="JSON file of Composio-fetched calendar events")
    parser.add_argument("--db", required=True, type=Path, help="Meridian database path")
    # `--as-of` is validated below rather than declared required, because `--status` is a
    # read-only liveness report that must work without an ingest anchor.
    parser.add_argument("--as-of", help="anchor date, YYYY-MM-DD (required unless --status)")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--days-forward", type=int, default=30)
    parser.add_argument("--status", action="store_true", help="print observed liveness and exit")
    parser.add_argument(
        "--enable",
        action="store_true",
        help=f"actually ingest (otherwise this refuses); mirrors {CALENDAR_CONTEXT_ENABLED_ENV}=1",
    )
    args = parser.parse_args(argv)

    store = CalendarContextStore(str(args.db))

    if args.status:
        # Read-only, and deliberately reports OBSERVATION rather than schedule health.
        print(json.dumps(store.liveness(), indent=2))
        return 0

    if not args.events:
        parser.error("--events is required unless --status is used")
    if not args.as_of:
        parser.error("--as-of is required unless --status is used")
    if not calendar_context_enabled() and not args.enable:
        print(
            "Refusing to run: calendar context is disabled.\n"
            f"Set {CALENDAR_CONTEXT_ENABLED_ENV}=1 (or pass --enable). It reads events and\n"
            "writes observed context rows; it makes no provider call and touches no money.",
            file=sys.stderr,
        )
        return 2

    records = _load_events(args.events)
    transport = ComposioCalendarTransport(records)
    window_start, window_end = default_window(
        as_of=args.as_of, days_back=args.days_back, days_forward=args.days_forward
    )

    try:
        report = ingest_calendar_context(
            store=store,
            transport=transport,
            source=SOURCE_COMPOSIO,
            as_of=args.as_of,
            enabled=True,
        )
    except CalendarContextDisabled as exc:  # pragma: no cover - guarded above
        print(f"Refused: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        **report,
        "window": {"start": window_start, "end": window_end},
        "fields_dropped_by_minimum_field_rule": _dropped_fields(records),
        "liveness": store.liveness(),
        "note": (
            "Observed counts only. This script does not run on a schedule and cannot report "
            "the schedule's health -- see --status."
        ),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
