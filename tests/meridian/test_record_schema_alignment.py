"""The schema and the record dataclasses must move together, or a running app breaks.

Why this guard exists — a measured incident, not a style preference (2026-09-20, OS-056b).

Migration 025 added two columns to ``crew_bill_reserves``. The dataclass for that table is
built as ``BillReserveRecord(**dict(row))``, so the running preview — whose in-memory class
predated the columns — raised
``TypeError: BillReserveRecord.__init__() got an unexpected keyword argument
'estimated_next_funding_amount'`` on every reserve read. That killed its 15-second refresh
and the dial's own read path, so ``/api/meridian/dial`` returned 503 while
``/api/meridian/today`` and ``/api/meridian/accounts`` kept returning 200: a dial-only
outage that looked like a front-end problem.

The mechanism is worth stating plainly, because it is easy to repeat: ``FinancialRepository``
runs ``run_migrations`` on every refresh, so a schema file added on disk is applied by
whatever process is ALREADY running. If that process's record class does not declare the new
columns, the next read fails. A migration that only creates a new table, or that adds a
column to a table read column-by-column (``commitments``, for example, maps its fields
explicitly in ``_from_row``), is safe by construction. A migration that ALTERs a table whose
record is built with ``**dict(row)`` is not.

So this test pins the invariant mechanically instead of relying on someone noticing a 503:
for each declared (table, record) pair, the table's live columns and the dataclass's fields
must be EXACTLY equal after every migration has run. Adding a column without extending the
record fails here — in a one-second test, before it can reach a running process.

The pair map is deliberately partial and should grow: it names the tables this lane has
actually altered. Extend it when touching another ``**dict(row)`` record rather than
inventing a heuristic that guesses the mapping.
"""

import sqlite3
from dataclasses import fields

import pytest

from meridian.db import run_migrations
from meridian.repository import BillReserveRecord, FundingPlanRecord

# (table, record class) for every record this lane has altered. Both are read as
# `Record(**dict(row))` in repository.py, so an undeclared column is an immediate TypeError
# in any process whose code predates the migration.
DECLARED_PAIRS = [
    ("crew_bill_reserves", BillReserveRecord),
    ("crew_funding_plans", FundingPlanRecord),
]


def _table_columns(db_path, table: str) -> list[str]:
    with sqlite3.connect(db_path) as connection:
        return [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]


def _record_fields(record) -> list[str]:
    return [field.name for field in fields(record)]


def _mismatch(db_path, table: str, record) -> str:
    """Empty when aligned; otherwise a description of how they differ."""
    columns = _table_columns(db_path, table)
    names = _record_fields(record)
    missing_from_record = [c for c in columns if c not in names]
    missing_from_table = [n for n in names if n not in columns]
    if not missing_from_record and not missing_from_table:
        return ""
    return (
        f"{table} vs {record.__name__}: "
        f"columns the record does not declare = {missing_from_record}; "
        f"record fields with no column = {missing_from_table}"
    )


@pytest.mark.parametrize(
    ("table", "record"),
    DECLARED_PAIRS,
    ids=[f"{table}-{record.__name__}" for table, record in DECLARED_PAIRS],
)
def test_every_migrated_column_has_a_record_field(tmp_path, table, record):
    """The 2026-09-20 dial outage, turned into a one-second assertion."""
    db_path = str(tmp_path / "financial.db")
    run_migrations(db_path)

    assert _mismatch(db_path, table, record) == ""


def test_the_guard_reports_a_stale_record(tmp_path):
    """Negative control: the check must BITE, or it proves nothing.

    A guard that passes on a deliberately out-of-sync pair would have passed on the
    incident itself. This models the table as it was BEFORE the schema moved, asserts the
    helper reports the mismatch, and then confirms the real record still aligns on the same
    database — so the control is meaningful rather than an artefact of a helper that always
    complains.
    """
    from dataclasses import make_dataclass

    db_path = str(tmp_path / "financial.db")
    run_migrations(db_path)

    stale = make_dataclass("StaleBillReserveRecord", [("id", int)])
    report = _mismatch(db_path, "crew_bill_reserves", stale)

    assert report, "a stale record must be reported"
    assert "total_reserved_amount" in report, "the report must name an undeclared column"
    assert "record fields with no column = []" in report, "the stale class has no extra fields"

    assert _mismatch(db_path, "crew_bill_reserves", BillReserveRecord) == ""


def test_the_pair_map_declares_the_tables_this_slice_altered():
    """The guard's coverage is declared, not implied.

    Migration 025 altered ``crew_bill_reserves``; 022 created ``crew_funding_plans``. Both
    are read as ``**dict(row)``, so both belong here. If a future migration alters another
    such table, this assertion is the prompt to extend the map — which is cheaper than
    discovering it from a 503.
    """
    assert {table for table, _ in DECLARED_PAIRS} == {
        "crew_bill_reserves",
        "crew_funding_plans",
    }
