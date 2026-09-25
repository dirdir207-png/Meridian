"""Dated observations of each Crew bill's reserved amount — the reserve's internal allocation.

**Why this exists (OS-114, owner-authorised 2026-09-25).** The owner's own correction is the premise:
*"Reserve is one bucket, so I'm not sure it's possible, but you may be referring to its internal bill
allocation."* He is right about the bucket, and the arithmetic strengthens the case: in his 2026-09-04
capture the five per-bill ``reservedAmount`` values sum to the bucket's ``totalReservedAmount``
**exactly** (71098 = 71098 cents, difference 0), with only one distinct bucket total in the read — so the
per-bill figure *is* the bucket's internal allocation.

``commitments.funded_amount`` already holds that number, and ``commitments.reserved_amount_reported``
the flag that says whether Crew stated it. Both are single values **overwritten every sync**, so the same
number that answers "how is the bucket allocated right now" destroys the answer to "how did it get
that way". Observed so far — Rent holding the whole $710.98 on 09-04 while four bills held $0.00, the
bucket at $1,097.10 on 09-20, and $0.00 on 09-25 — and nothing on our side can yet distinguish a bucket
that moved because a bill was paid from one that moved because a sync dropped a value.

**The allocation is lumpy, not proportional**, which is what makes history worth keeping: one bill holds
the whole bucket at a time. OS-058's open question — which bill is credited, and by what rule — is
answerable only against a series of these rows.

**The C01 rule, and how it differs from migration 030.** A row is written whenever the BILL was
observed, even if Crew stated no amount: then ``reserved_amount`` is ``None`` and
``reserved_amount_reported`` is False, so silence can never be read as $0.00. That differs deliberately
from :mod:`meridian.spend_selection`, where an unobserved FACET writes no row at all — there the whole
read is absent, whereas here the bill itself was part of the read and only its amount was silent. It is
the same distinction ``commitments`` already draws.

Nothing here decides anything about money. It records what was seen, when, and with what provenance, so
that a later rule — or a later argument about a rule — has evidence instead of a single mutable number.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional, Sequence

#: Mirrors the vocabulary migration 030 established, so the two observation stores cannot drift apart in
#: what they mean by simulated data.
DATA_MODES = ("actual", "simulated")


@dataclass(frozen=True)
class BillAllocation:
    """One bill's observed share of the reserve, at one moment."""

    provider: str
    connection_external_id: str
    bill_external_id: str
    observed_at: str
    reserved_amount_reported: bool
    bill_name: Optional[str] = None
    reserved_amount: Optional[float] = None
    estimated_next_funding_amount: Optional[float] = None
    reserved_by: Optional[str] = None
    bill_reserve_id: Optional[str] = None
    data_mode: str = "actual"
    id: Optional[int] = None

    @property
    def is_reported(self) -> bool:
        """Did Crew state an amount for this bill in this read?

        ``False`` is not ``$0.00``: it means the read was silent, and a caller that treats the two as
        the same has reintroduced the defect C01 exists to prevent.
        """
        return bool(self.reserved_amount_reported) and self.reserved_amount is not None

    def as_evidence(self) -> dict:
        """What a payload may carry: the observed facts, with silence preserved as silence."""
        return {
            "bill_external_id": self.bill_external_id,
            "bill_name": self.bill_name,
            "observed_at": self.observed_at,
            "reserved_amount": self.reserved_amount if self.is_reported else None,
            "reserved_amount_reported": self.is_reported,
            "reserved_by": self.reserved_by,
            "data_mode": self.data_mode,
        }


class BillAllocationStore:
    """Append-only store for observed per-bill allocations."""

    def __init__(self, db_path) -> None:
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def record(
        self,
        *,
        provider: str,
        connection_external_id: str,
        bill_external_id: str,
        observed_at: str,
        reserved_amount: Optional[float],
        bill_name: Optional[str] = None,
        estimated_next_funding_amount: Optional[float] = None,
        reserved_by: Optional[str] = None,
        bill_reserve_id: Optional[str] = None,
        data_mode: str = "actual",
    ) -> Optional[BillAllocation]:
        """Record one bill's allocation from one capture. Idempotent per (bill, capture).

        ``reserved_amount=None`` means Crew did not state one for this bill, and is stored as silence
        with the flag recording it — never as ``0.0``.

        Returns the row that now exists for this capture, or ``None`` when the write could not be
        identified (no bill id): an observation nobody can attribute is not worth storing.
        """
        if not bill_external_id or not observed_at:
            return None
        if data_mode not in DATA_MODES:
            raise ValueError(f"unknown data_mode {data_mode!r}")
        reported = 1 if reserved_amount is not None else 0
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM crew_bill_allocation_observations "
                "WHERE provider = ? AND bill_external_id = ? AND observed_at = ?",
                (provider, bill_external_id, observed_at),
            ).fetchone()
            if existing is not None:
                # The first observation of a capture stands: re-ingesting one capture must not be able
                # to rewrite history, even with a different value.
                return self._row(existing)
            connection.execute(
                """INSERT INTO crew_bill_allocation_observations (
                       provider, connection_external_id, bill_external_id, bill_name, observed_at,
                       reserved_amount, reserved_amount_reported, estimated_next_funding_amount,
                       reserved_by, bill_reserve_id, data_mode
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    provider, connection_external_id, bill_external_id, bill_name, observed_at,
                    reserved_amount, reported, estimated_next_funding_amount, reserved_by,
                    bill_reserve_id, data_mode,
                ),
            )
            row = connection.execute(
                "SELECT * FROM crew_bill_allocation_observations "
                "WHERE provider = ? AND bill_external_id = ? AND observed_at = ?",
                (provider, bill_external_id, observed_at),
            ).fetchone()
        return self._row(row) if row is not None else None

    def history(
        self,
        bill_external_id: Optional[str] = None,
        *,
        provider: str = "crew",
        limit: int = 100,
    ) -> tuple[BillAllocation, ...]:
        """Observations newest first, for one bill or for every bill when no id is given."""
        query = "SELECT * FROM crew_bill_allocation_observations WHERE provider = ?"
        params: list[object] = [provider]
        if bill_external_id is not None:
            query += " AND bill_external_id = ?"
            params.append(bill_external_id)
        query += " ORDER BY observed_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 1000)))
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return tuple(self._row(row) for row in rows)

    def latest(self, bill_external_id: str, *, provider: str = "crew") -> Optional[BillAllocation]:
        history = self.history(bill_external_id, provider=provider, limit=1)
        return history[0] if history else None

    def allocations_at(self, observed_at: str, *, provider: str = "crew") -> tuple[BillAllocation, ...]:
        """Every bill's allocation within ONE capture.

        This is the shape the bucket check needs: the parts and the whole come from the same read, so a
        caller can compare them without mixing dates.
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM crew_bill_allocation_observations "
                "WHERE provider = ? AND observed_at = ? ORDER BY bill_external_id",
                (provider, observed_at),
            ).fetchall()
        return tuple(self._row(row) for row in rows)

    def capture_times(self, *, provider: str = "crew", limit: int = 50) -> tuple[str, ...]:
        """The distinct captures held, newest first — each one a point the reserve can be replayed at."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT observed_at FROM crew_bill_allocation_observations "
                "WHERE provider = ? ORDER BY observed_at DESC LIMIT ?",
                (provider, max(1, min(int(limit), 500))),
            ).fetchall()
        return tuple(str(row["observed_at"]) for row in rows)

    @staticmethod
    def _row(row) -> BillAllocation:
        return BillAllocation(
            provider=row["provider"],
            connection_external_id=row["connection_external_id"],
            bill_external_id=row["bill_external_id"],
            bill_name=row["bill_name"],
            observed_at=row["observed_at"],
            reserved_amount=row["reserved_amount"],
            reserved_amount_reported=bool(row["reserved_amount_reported"]),
            estimated_next_funding_amount=row["estimated_next_funding_amount"],
            reserved_by=row["reserved_by"],
            bill_reserve_id=row["bill_reserve_id"],
            data_mode=row["data_mode"],
            id=row["id"],
        )


def parts_equal_whole(allocations: Sequence[BillAllocation], bucket_total: Optional[float]) -> Optional[bool]:
    """Do one capture's per-bill allocations sum to the reserve's own total?

    ``None`` when the question cannot be asked honestly: no reported allocations, or no bucket total to
    compare against. A caller must not read that as agreement — the same distinction the whole module
    draws between silence and zero. This is the check that established the per-bill figure IS the
    bucket's internal allocation (71098 = 71098 cents on 2026-09-04), so it is kept as a runnable
    function rather than a claim in a comment.
    """
    if bucket_total is None:
        return None
    reported = [item for item in allocations if item.is_reported]
    if not reported:
        return None
    return abs(sum(item.reserved_amount or 0.0 for item in reported) - bucket_total) < 0.005


__all__ = [
    "DATA_MODES",
    "BillAllocation",
    "BillAllocationStore",
    "parts_equal_whole",
]
