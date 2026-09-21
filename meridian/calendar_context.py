"""Canonical intake for read-only calendar CONTEXT.

**Scope decision (owner, 2026-09-21): calendar events are read-only context.** They may
explain a month's cash-flow pressure -- travel, an appointment that moves a bill -- but they
are **never matched to a transaction**, **never treated as an obligation**, and **never
written to the evidence store**. That is the boundary this module exists to hold, and it is
held in three places rather than by convention:

1. The table (`026_calendar_context.sql`) has no amount, commitment or transaction column
   at all, so matching cannot begin without a deliberate migration.
2. This module exposes no matching, linking or exposure API. It can store an observation and
   read a window back, and that is all it can do.
3. A test asserts both facts, so a later edit that adds either has to argue with a red test.

**Why this module is the canonical intake.** D-016 guardrail 3 requires that externally
fetched data enters through the same intake the app uses, with its provenance recorded, and
forbids a side-channel write. So both ingestion routes -- the app's own connector and a
harness-mediated replay -- are just TRANSPORTS satisfying
`meridian.connectors.calendar.CalendarTransport`, and both are handed to
`ingest_calendar_context` below. Neither writes a row itself. This mirrors
`scripts/backfill_charge_evidence.py`, the worked example the decision cites.

**What the report means, and what it deliberately does NOT mean.** `ingest_calendar_context`
reports what was OBSERVED -- counts read back from the store after the write -- not what was
attempted. The evidence lane learned this the hard way: `ingest_record` swallowed blob-write
failures, so "ingested" silently meant "metadata only", and the owner was left with 732 rows
and 0 blobs. A report that counts attempts cannot be trusted to describe the store.

**Gating.** This capability is OFF unless explicitly enabled. It makes a real authenticated
call to a provider when it runs, so it must never be reachable as a side effect of importing
something.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

from meridian.connectors.calendar import (
    CalendarBatch,
    CalendarTransport,
    ReadOnlyCalendarConnector,
)

#: The env knob that enables the capability. Absent, empty, "0", "false" -- all mean OFF.
CALENDAR_CONTEXT_ENABLED_ENV = "MERIDIAN_CALENDAR_CONTEXT_ENABLED"

#: Provenance label for the Composio-mediated calendar read. This is the ONLY calendar
#: adapter by owner decision (2026-09-21): the in-app Google OAuth transport is deliberately
#: NOT built for calendar, so that Meridian holds no Google credential for it and is not
#: exposed to Google's refresh-token lifetime. Mail is unaffected -- its filters and
#: in-process path stay as they are.
SOURCE_COMPOSIO = "composio_calendar"


class CalendarContextDisabled(RuntimeError):
    """Raised when the capability is invoked without being enabled.

    Deliberately an exception rather than a silent no-op: a caller that believes it ingested
    something when it did not is the failure mode this guards against.
    """


def calendar_context_enabled(environ: Optional[dict] = None) -> bool:
    """Is the calendar-context capability enabled? OFF unless explicitly turned on."""
    source = os.environ if environ is None else environ
    raw = str(source.get(CALENDAR_CONTEXT_ENABLED_ENV, "") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class CalendarContextStore:
    """Observation store for calendar context. Cannot match, link or expose.

    Every method is either a write of ONE observed event or a read of a time window. There is
    no query that joins to money and no query that scores a match, because the capability has
    no such concept.
    """

    db_path: str

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def upsert(self, *, source: str, external_id: str, starts_at: str, ends_at: str,
               summary: str, source_link: str, observed_at: str) -> str:
        """Record one observation. Returns "inserted", "updated" or "unchanged".

        "unchanged" is a real outcome and is reported as such: re-observing an identical
        event must not look like new information.
        """
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id, starts_at, ends_at, summary, source_link"
                " FROM calendar_context_events WHERE source = ? AND external_id = ?",
                (source, external_id),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO calendar_context_events"
                    " (source, external_id, starts_at, ends_at, summary, source_link, observed_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (source, external_id, starts_at, ends_at, summary, source_link, observed_at),
                )
                return "inserted"
            if (
                existing["starts_at"] == starts_at
                and existing["ends_at"] == ends_at
                and existing["summary"] == summary
                and existing["source_link"] == source_link
            ):
                # Re-observed identically. `observed_at` is deliberately NOT bumped: it
                # records when the event was FIRST seen in this shape, and advancing it would
                # make an unchanged event look freshly confirmed.
                return "unchanged"
            connection.execute(
                "UPDATE calendar_context_events SET starts_at = ?, ends_at = ?, summary = ?,"
                " source_link = ?, observed_at = ? WHERE id = ?",
                (starts_at, ends_at, summary, source_link, observed_at, existing["id"]),
            )
            return "updated"

    def list_between(self, *, start: str, end: str) -> list[dict]:
        """Observed events whose start falls in [start, end). Ordered, fully attributed.

        Returned rows carry their `source`, so a consumer can always tell the app's own
        observation from a harness-mediated one.
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT source, external_id, starts_at, ends_at, summary, source_link, observed_at"
                " FROM calendar_context_events WHERE starts_at >= ? AND starts_at < ?"
                " ORDER BY starts_at, source, external_id",
                (start, end),
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute(
                "SELECT COUNT(*) FROM calendar_context_events"
            ).fetchone()[0])

    def count_by_source(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT source, COUNT(*) AS n FROM calendar_context_events GROUP BY source"
            ).fetchall()
        return {str(row["source"]): int(row["n"]) for row in rows}

    def liveness(self) -> dict:
        """Honest liveness for the daily cycle, derived from what was actually observed.

        D-016 guardrail 4 requires a scheduled capability to state its liveness honestly, and
        the only honest basis is observation: the newest `observed_at` this store actually
        holds, and how many events that was across. This deliberately cannot report "the
        scheduler is healthy" -- it reports the last time an event was genuinely written, so a
        poller that has been silently failing reads as STALE rather than as running.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT MAX(observed_at) AS last_observed_at, COUNT(*) AS total"
                " FROM calendar_context_events"
            ).fetchone()
        total = int(row["total"] or 0)
        return {
            "last_observed_at": row["last_observed_at"],
            "total_events": total,
            "by_source": self.count_by_source(),
            "has_ever_observed": total > 0,
        }


def _observed_at_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ingest_calendar_context(
    *,
    store: CalendarContextStore,
    transport: CalendarTransport,
    source: str,
    as_of: str,
    cursor: Optional[str] = None,
    enabled: Optional[bool] = None,
    observed_at: Optional[str] = None,
) -> dict:
    """Read one page of calendar events and record them as context observations.

    Returns a report of what was OBSERVED. `rows_after - rows_before` is the authoritative
    statement that something landed; the per-outcome counts describe how.

    Read-only in every direction: it fetches, and it writes only to the context store. It
    cannot send, mutate or delete anything at the provider, holds no approval authority, and
    has no path to the evidence store or to any financial table.
    """
    if not (calendar_context_enabled() if enabled is None else enabled):
        raise CalendarContextDisabled(
            "Calendar context is disabled. Set "
            f"{CALENDAR_CONTEXT_ENABLED_ENV}=1 to enable it; it makes a real provider call."
        )

    rows_before = store.count()
    connector = ReadOnlyCalendarConnector(transport)
    batch: CalendarBatch = connector.poll(cursor, as_of=as_of)
    stamp = observed_at or _observed_at_now()

    outcomes = {"inserted": 0, "updated": 0, "unchanged": 0}
    for event in batch.events:
        outcome = store.upsert(
            source=source,
            external_id=event.id,
            starts_at=event.start,
            ends_at=event.end,
            summary=event.summary,
            source_link=event.source_link,
            observed_at=stamp,
        )
        outcomes[outcome] += 1

    rows_after = store.count()
    return {
        "source": source,
        "observed_at": stamp,
        "as_of": as_of,
        "events_read": len(batch.events),
        "revoked": bool(batch.revoked),
        "cursor": batch.cursor,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_added": rows_after - rows_before,
        **outcomes,
    }


def default_window(*, as_of: str, days_back: int = 7, days_forward: int = 30) -> tuple[str, str]:
    """A bounded read window around `as_of`, used by the on-demand script.

    Bounded on purpose: an unbounded read of someone's calendar is exactly the kind of
    "unnecessary data" the lane boundary excludes.
    """
    from datetime import timedelta

    anchor = date.fromisoformat(as_of)
    return (
        (anchor - timedelta(days=days_back)).isoformat(),
        (anchor + timedelta(days=days_forward)).isoformat(),
    )


__all__ = [
    "CALENDAR_CONTEXT_ENABLED_ENV",
    "SOURCE_COMPOSIO",
    "CalendarContextDisabled",
    "CalendarContextStore",
    "calendar_context_enabled",
    "default_window",
    "ingest_calendar_context",
]
