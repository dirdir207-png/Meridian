"""A bill reserve may legitimately be negative — the production outage of 2026-09-21.

Migration 024 declared ``CHECK (total_reserved_amount IS NULL OR total_reserved_amount >= 0)``
on the assumption that a reserve total is money set aside and so cannot be below zero. On
2026-09-21 that assumption failed in production: the owner's live read raised

    sqlite3.IntegrityError: CHECK constraint failed:
        total_reserved_amount IS NULL OR total_reserved_amount >= 0

on every sync, because they had deliberately left too much in Crew's "free to spend" and rent
clearing left the reserve below zero. The owner confirmed the negative is correct.

A reserve total is a running balance, not a quantity, so the schema must be able to record a
negative. Migration 028 rebuilds the table without that clause.

These tests cover the three things that matter about a table rebuild: that the constraint is
genuinely gone, that NOTHING was lost or altered in the copy, and that the old behaviour is
still verifiable (so the migration is provably what fixed it).
"""
import shutil
import sqlite3

import pytest

from meridian import db as db_module
from meridian.db import run_migrations


def _migrate_up_to(tmp_path, monkeypatch, last_applied: str):
    """Apply migrations only up to (and including) ``last_applied``, return the db path."""
    staged = tmp_path / "staged-migrations"
    staged.mkdir()
    for source in sorted(db_module.MIGRATIONS_DIR.glob("*.sql")):
        if source.name > last_applied:
            continue
        shutil.copy(source, staged / source.name)
    with monkeypatch.context() as patch:
        patch.setattr(db_module, "MIGRATIONS_DIR", staged)
        db_path = str(tmp_path / "partial.db")
        applied = run_migrations(db_path)
    assert applied[-1] == last_applied
    return db_path


def _insert(db_path, **overrides):
    values = {
        "provider": "crew",
        "external_id": "reserve-1",
        "total_reserved_amount": 12.5,
        "currency": "USD",
        "observed_at": "2026-09-20T10:00:00Z",
        "synced_at": "2026-09-20T10:00:00Z",
        "created_at": "2026-09-20T10:00:00Z",
        "updated_at": "2026-09-20T10:00:00Z",
    }
    values.update(overrides)
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            f"INSERT INTO crew_bill_reserves ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )


# ---------------------------------------------------------------------------------------
# The outage itself
# ---------------------------------------------------------------------------------------

def test_a_negative_reserve_could_not_be_stored_before_028(tmp_path, monkeypatch):
    """Falsification: this is the exact failure the owner hit. If this ever stops raising,
    the migration is no longer what makes the next test pass, and something else changed."""
    db_path = _migrate_up_to(tmp_path, monkeypatch, "027_ai_run_records.sql")
    with pytest.raises(sqlite3.IntegrityError) as caught:
        _insert(db_path, total_reserved_amount=-42.0)
    assert "CHECK constraint failed" in str(caught.value)


def test_a_negative_reserve_is_stored_after_028(tmp_path):
    """The production defect, fixed: a running balance below zero is a real state, and a
    schema that refuses it does not prevent the state, it only prevents Meridian from
    knowing about it."""
    db_path = str(tmp_path / "full.db")
    run_migrations(db_path)
    _insert(db_path, total_reserved_amount=-42.0)
    with sqlite3.connect(db_path) as connection:
        stored = connection.execute(
            "SELECT total_reserved_amount FROM crew_bill_reserves"
        ).fetchone()[0]
    assert stored == -42.0
    # Not clamped, not absolutised: the reported figure is recorded as reported. Showing a
    # fabricated positive would present a simulation as a real balance.
    assert stored < 0


def test_null_still_means_not_reported(tmp_path):
    """The `>= 0` clause went; the NULL-means-unreported distinction (C01) must not follow
    it. An unreported total is not a zero and must never be stored as one."""
    db_path = str(tmp_path / "full.db")
    run_migrations(db_path)
    _insert(db_path, total_reserved_amount=None)
    with sqlite3.connect(db_path) as connection:
        stored = connection.execute(
            "SELECT total_reserved_amount FROM crew_bill_reserves"
        ).fetchone()[0]
    assert stored is None


# ---------------------------------------------------------------------------------------
# The rebuild must not lose or alter anything
# ---------------------------------------------------------------------------------------

def test_the_rebuild_preserves_every_row_value_and_id(tmp_path, monkeypatch):
    """A table rebuild is the risky part of this migration. Rows are copied verbatim, ids
    included, and nothing is clamped, rounded or repaired."""
    db_path = _migrate_up_to(tmp_path, monkeypatch, "027_ai_run_records.sql")
    _insert(db_path, external_id="a", total_reserved_amount=12.5)
    _insert(db_path, external_id="b", total_reserved_amount=None)
    _insert(db_path, external_id="c", total_reserved_amount=0.0, absent_since="2026-09-01")
    before = sorted(
        sqlite3.connect(db_path).execute(
            "SELECT id, external_id, total_reserved_amount, currency, absent_since"
            " FROM crew_bill_reserves ORDER BY id"
        ).fetchall()
    )
    assert len(before) == 3

    monkeypatch.undo()
    applied = run_migrations(db_path)
    assert applied == [
        "028_allow_negative_bill_reserve.sql",
        "029_crew_pocket_goals.sql",
        "030_crew_spend_selection.sql",
        # 031 keeps the dated per-bill allocation history (OS-114); it applies after 030 and
        # is listed here because this test enumerates every migration the database applies.
        "031_crew_bill_allocation_observations.sql",
    ]

    after = sorted(
        sqlite3.connect(db_path).execute(
            "SELECT id, external_id, total_reserved_amount, currency, absent_since"
            " FROM crew_bill_reserves ORDER BY id"
        ).fetchall()
    )
    assert after == before, "the rebuild altered or dropped rows"
    # A real zero and an unreported total stay distinguishable after the copy.
    assert [row[2] for row in after] == [12.5, None, 0.0]


def test_the_rebuild_keeps_the_schema_shape_and_index(tmp_path):
    """The rebuilt table must be indistinguishable from the one it replaces, apart from the
    removed clause -- column order included, because SELECT * and positional inserts care."""
    db_path = str(tmp_path / "full.db")
    run_migrations(db_path)
    with sqlite3.connect(db_path) as connection:
        columns = [(row[1], row[2], row[3], row[5]) for row in connection.execute(
            "PRAGMA table_info(crew_bill_reserves)"
        )]
        indexes = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='crew_bill_reserves'"
        )}
        leftovers = list(connection.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'crew_bill_reserves_rebuilt%'"
        ))

    assert [name for name, *_ in columns] == [
        "id", "provider", "external_id", "total_reserved_amount", "currency", "observed_at",
        "synced_at", "absent_since", "created_at", "updated_at",
        "estimated_next_funding_amount", "next_funding_date",
    ]
    # NOT NULL flags survive: provider/external_id/synced_at/created_at/updated_at are required.
    required = {name for name, _type, notnull, _pk in columns if notnull}
    assert required == {
        "provider", "external_id", "currency", "synced_at", "created_at", "updated_at"
    }
    assert indexes == {
        "sqlite_autoindex_crew_bill_reserves_1", "idx_crew_bill_reserves_current"
    }
    assert leftovers == [], "the rebuild left a temporary table behind"


def test_the_unique_key_on_provider_and_external_id_still_applies(tmp_path):
    """The rebuild recreated UNIQUE(provider, external_id); losing it would let one reserve
    accumulate duplicate rows and quietly break the dial's resolution."""
    db_path = str(tmp_path / "full.db")
    run_migrations(db_path)
    _insert(db_path, external_id="dup")
    with pytest.raises(sqlite3.IntegrityError):
        _insert(db_path, external_id="dup")
    # The same external id from a DIFFERENT provider is still a distinct reserve.
    _insert(db_path, provider="other", external_id="dup")


def test_025_columns_are_untouched_by_the_rebuild(tmp_path, monkeypatch):
    """025 added two columns to this table; the rebuild had to carry them, and they must
    still hold values and still have no non-negativity check of their own."""
    db_path = _migrate_up_to(tmp_path, monkeypatch, "027_ai_run_records.sql")
    _insert(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE crew_bill_reserves SET estimated_next_funding_amount = ?,"
            " next_funding_date = ?",
            (-15.0, "2026-10-02"),
        )
    monkeypatch.undo()
    run_migrations(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT estimated_next_funding_amount, next_funding_date FROM crew_bill_reserves"
        ).fetchone()
    assert row == (-15.0, "2026-10-02")
