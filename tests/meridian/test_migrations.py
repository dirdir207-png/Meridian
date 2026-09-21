import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from threading import Event

import pytest

from meridian import db as db_module
from meridian.db import run_migrations
from meridian.repository import FinancialRepository

_LATER_MIGRATIONS = [
    "004_canonical_transaction_timestamps.sql",
    "005_commitments.sql",
    "006_funding_rules.sql",
    "007_transaction_classification.sql",
    "008_ai_classification_audit.sql",
    "009_review_rules.sql",
    "010_provider_reimbursements.sql",
    "011_evidence_graph.sql",
    "012_context_signals.sql",
    "013_assets_contracts.sql",
    "014_connection_authorizations.sql",
    "015_evidence_sender.sql",
    "016_trials.sql",
    "017_cancellation_actions.sql",
    "018_trial_notifications.sql",
    "019_immutable_observations.sql",
    "020_account_absence_reconciliation.sql",
    "021_commitment_absence_reconciliation.sql",
    "022_crew_funding_plans.sql",
    "023_commitment_bill_reserve.sql",
    "024_crew_bill_reserve_observations.sql",
    "025_crew_reported_funding_schedule.sql",
    "026_calendar_context.sql",
    "027_ai_run_records.sql",
]


def _create_pre_timestamp_migration_database(
    db_path: Path, migrations_dir: Path, monkeypatch
) -> None:
    legacy_migrations = migrations_dir / "legacy-migrations"
    legacy_migrations.mkdir()
    for source in sorted(db_module.MIGRATIONS_DIR.glob("00[1-3]_*.sql")):
        shutil.copy(source, legacy_migrations / source.name)
    with monkeypatch.context() as migration_patch:
        migration_patch.setattr(db_module, "MIGRATIONS_DIR", legacy_migrations)
        run_migrations(str(db_path))


def _seed_legacy_transaction(
    db_path: Path,
    *,
    occurred_at: str,
    source_updated_at: str = "2026-08-27T08:00:00Z#legacy",
) -> int:
    with sqlite3.connect(db_path) as connection:
        account_id = connection.execute(
            """
            INSERT INTO financial_accounts (
                provider, external_id, name, account_type, balance, currency,
                synced_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "crew",
                "legacy-account",
                "Legacy account",
                "checking",
                100.0,
                "USD",
                "2026-08-27T08:00:00Z",
                "2026-08-27T08:00:00Z",
                "2026-08-27T08:00:00Z",
            ),
        ).lastrowid
        return connection.execute(
            """
            INSERT INTO financial_transactions (
                account_id, provider, external_id, amount, currency,
                occurred_at, description, status, source_updated_at, synced_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                "crew",
                "legacy-transaction",
                -1.0,
                "USD",
                occurred_at,
                "Legacy",
                "posted",
                source_updated_at,
                "2026-08-27T08:00:00Z",
                "2026-08-27T08:00:00Z",
                "2026-08-27T08:00:00Z",
            ),
        ).lastrowid


def test_migrations_are_idempotent_and_preserve_legacy_rows(tmp_path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE history (date TEXT PRIMARY KEY, balance REAL)")
        connection.execute(
            "INSERT INTO history (date, balance) VALUES (?, ?)",
            ("2026-08-26", 1234.56),
        )

    assert run_migrations(str(db_path))[-len(_LATER_MIGRATIONS) :] == _LATER_MIGRATIONS
    assert run_migrations(str(db_path)) == []

    with sqlite3.connect(db_path) as connection:
        migrations = connection.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
        legacy_row = connection.execute("SELECT date, balance FROM history").fetchone()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert migrations == [
        ("001", "001_financial_graph.sql"),
        ("002", "002_financial_integrity.sql"),
        ("003", "003_provider_sync_runs.sql"),
        ("004", "004_canonical_transaction_timestamps.sql"),
        ("005", "005_commitments.sql"),
        ("006", "006_funding_rules.sql"),
        ("007", "007_transaction_classification.sql"),
        ("008", "008_ai_classification_audit.sql"),
        ("009", "009_review_rules.sql"),
        ("010", "010_provider_reimbursements.sql"),
        ("011", "011_evidence_graph.sql"),
        ("012", "012_context_signals.sql"),
        ("013", "013_assets_contracts.sql"),
        ("014", "014_connection_authorizations.sql"),
        ("015", "015_evidence_sender.sql"),
        ("016", "016_trials.sql"),
        ("017", "017_cancellation_actions.sql"),
        ("018", "018_trial_notifications.sql"),
        ("019", "019_immutable_observations.sql"),
        ("020", "020_account_absence_reconciliation.sql"),
        ("021", "021_commitment_absence_reconciliation.sql"),
        ("022", "022_crew_funding_plans.sql"),
        ("023", "023_commitment_bill_reserve.sql"),
        ("024", "024_crew_bill_reserve_observations.sql"),
        ("025", "025_crew_reported_funding_schedule.sql"),
        ("026", "026_calendar_context.sql"),
        ("027", "027_ai_run_records.sql"),
    ]
    assert legacy_row == ("2026-08-26", 1234.56)
    assert {
        "provider_connections",
        "financial_accounts",
        "financial_transactions",
        "transaction_relations",
        "provider_sync_runs",
    } <= tables


def test_financial_graph_schema_tracks_relation_freshness_and_provider_ownership(
    tmp_path,
):
    db_path = tmp_path / "financial.db"
    run_migrations(str(db_path))

    with sqlite3.connect(db_path) as connection:
        relation_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(transaction_relations)")
        }
        connection.execute(
            """
            INSERT INTO financial_accounts (
                provider, external_id, name, account_type, balance, currency,
                synced_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "crew",
                "account-1",
                "Everyday",
                "checking",
                1.0,
                "USD",
                "2026-08-26T10:00:00Z",
                "2026-08-26T10:00:00Z",
                "2026-08-26T10:00:00Z",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError, match="provider must match"):
            connection.execute(
                """
                INSERT INTO financial_transactions (
                    account_id, provider, external_id, amount, currency,
                    occurred_at, description, status, synced_at, created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    "simplefin",
                    "transaction-1",
                    -1.0,
                    "USD",
                    "2026-08-26T10:00:00Z",
                    "Lunch",
                    "posted",
                    "2026-08-26T10:00:00Z",
                    "2026-08-26T10:00:00Z",
                    "2026-08-26T10:00:00Z",
                ),
            )

    assert {"source_updated_at", "synced_at"} <= relation_columns


def test_failed_migration_rolls_back_and_can_resume(tmp_path, monkeypatch):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_first.sql").write_text(
        "CREATE TABLE first_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    failing_path = migrations_dir / "002_recovery.sql"
    failing_path.write_text(
        "CREATE TABLE partial_table (id INTEGER PRIMARY KEY);\n"
        "INSERT INTO table_that_does_not_exist (id) VALUES (1);\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(db_module, "MIGRATIONS_DIR", migrations_dir)
    db_path = tmp_path / "resumable.db"

    with pytest.raises(sqlite3.OperationalError):
        run_migrations(str(db_path))

    with sqlite3.connect(db_path) as connection:
        applied = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        partial_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("partial_table",),
        ).fetchone()

    assert applied == [("001",)]
    assert partial_exists is None

    failing_path.write_text(
        "CREATE TABLE recovered_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )

    assert run_migrations(str(db_path)) == ["002_recovery.sql"]
    with sqlite3.connect(db_path) as connection:
        applied = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        recovered_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("recovered_table",),
        ).fetchone()

    assert applied == [("001",), ("002",)]
    assert recovered_exists == (1,)


def test_applied_migration_checksum_drift_is_rejected(tmp_path, monkeypatch):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    migration_path = migrations_dir / "001_example.sql"
    migration_path.write_text(
        "CREATE TABLE example (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(db_module, "MIGRATIONS_DIR", migrations_dir)
    db_path = tmp_path / "checksum.db"

    run_migrations(str(db_path))
    migration_path.write_text(
        "CREATE TABLE example (id INTEGER PRIMARY KEY, name TEXT);\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="checksum"):
        run_migrations(str(db_path))


def test_missing_applied_migration_file_is_rejected(tmp_path, monkeypatch):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    first_path = migrations_dir / "001_first.sql"
    first_path.write_text(
        "CREATE TABLE first_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    (migrations_dir / "002_second.sql").write_text(
        "CREATE TABLE second_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(db_module, "MIGRATIONS_DIR", migrations_dir)
    db_path = tmp_path / "missing-file.db"

    run_migrations(str(db_path))
    first_path.unlink()

    with pytest.raises(RuntimeError, match="missing from migrations directory"):
        run_migrations(str(db_path))


def test_retroactive_migration_insertion_is_rejected(tmp_path, monkeypatch):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "002_second.sql").write_text(
        "CREATE TABLE second_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(db_module, "MIGRATIONS_DIR", migrations_dir)
    db_path = tmp_path / "retroactive.db"

    assert run_migrations(str(db_path)) == ["002_second.sql"]
    (migrations_dir / "001_first.sql").write_text(
        "CREATE TABLE first_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="append-only"):
        run_migrations(str(db_path))


def test_timestamp_migration_is_recorded_once_and_preserves_provenance(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "timestamp-upgrade.db"
    _create_pre_timestamp_migration_database(db_path, tmp_path, monkeypatch)
    transaction_id = _seed_legacy_transaction(
        db_path,
        occurred_at="2026-08-27T04:00:00.11-04:00",
    )

    applied = run_migrations(str(db_path))
    assert applied[-len(_LATER_MIGRATIONS[1:]) :] == _LATER_MIGRATIONS[1:]
    assert run_migrations(str(db_path)) == []

    with sqlite3.connect(db_path) as connection:
        migration = connection.execute(
            "SELECT version, name FROM schema_migrations WHERE version = '004'"
        ).fetchone()
        transaction = connection.execute(
            """
            SELECT occurred_at, occurred_at_valid, source_updated_at
            FROM financial_transactions WHERE id = ?
            """,
            (transaction_id,),
        ).fetchone()

    assert migration == ("004", "004_canonical_transaction_timestamps.sql")
    assert transaction == (
        "2026-08-27T08:00:00.110000Z",
        1,
        "2026-08-27T08:00:00Z#legacy",
    )


def test_timestamp_migration_failure_rolls_back_and_resumes(tmp_path, monkeypatch):
    db_path = tmp_path / "timestamp-resume.db"
    _create_pre_timestamp_migration_database(db_path, tmp_path, monkeypatch)
    transaction_id = _seed_legacy_transaction(
        db_path,
        occurred_at="2026-08-27T04:00:00.1-04:00",
    )
    migration_name = "004_canonical_transaction_timestamps.sql"
    real_hook = db_module._MIGRATION_HOOKS[migration_name]

    def fail_after_conversion(connection):
        real_hook(connection)
        raise RuntimeError("interrupted timestamp migration")

    monkeypatch.setitem(
        db_module._MIGRATION_HOOKS, migration_name, fail_after_conversion
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        run_migrations(str(db_path))

    with sqlite3.connect(db_path) as connection:
        migration = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = '004'"
        ).fetchone()
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(financial_transactions)")
        }
        occurred_at = connection.execute(
            "SELECT occurred_at FROM financial_transactions WHERE id = ?",
            (transaction_id,),
        ).fetchone()[0]

    assert migration is None
    assert "occurred_at_valid" not in columns
    assert occurred_at == "2026-08-27T04:00:00.1-04:00"

    monkeypatch.setitem(db_module._MIGRATION_HOOKS, migration_name, real_hook)
    applied = run_migrations(str(db_path))
    assert applied[-len(_LATER_MIGRATIONS) :] == _LATER_MIGRATIONS


def test_timestamp_migration_locks_before_read_and_does_not_lose_concurrent_write(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "timestamp-concurrency.db"
    _create_pre_timestamp_migration_database(db_path, tmp_path, monkeypatch)
    _seed_legacy_transaction(
        db_path,
        occurred_at="2026-08-27T08:00:00Z",
        source_updated_at="2026-08-27T08:00:00Z",
    )
    repository = object.__new__(FinancialRepository)
    repository._db_path = str(db_path)
    migration_name = "004_canonical_transaction_timestamps.sql"
    real_hook = db_module._MIGRATION_HOOKS[migration_name]
    migration_read = Event()
    allow_migration = Event()
    writer_started = Event()

    def pause_after_read(connection):
        assert (
            connection.execute(
                "SELECT occurred_at FROM financial_transactions"
            ).fetchone()[0]
            == "2026-08-27T08:00:00Z"
        )
        migration_read.set()
        assert allow_migration.wait(timeout=5)
        real_hook(connection)

    monkeypatch.setitem(db_module._MIGRATION_HOOKS, migration_name, pause_after_read)

    def write_newer_value():
        writer_started.set()
        account_id = repository.list_accounts()[0].id
        return repository.upsert_transaction(
            provider="crew",
            external_id="legacy-transaction",
            account_id=account_id,
            amount=-2.0,
            occurred_at="2026-08-27T09:00:00Z",
            description="Newer",
            status="posted",
            source_updated_at="2026-08-27T09:00:00Z",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        migrating = executor.submit(run_migrations, str(db_path))
        assert migration_read.wait(timeout=5)
        writing = executor.submit(write_newer_value)
        assert writer_started.wait(timeout=5)
        with pytest.raises(TimeoutError):
            writing.result(timeout=0.1)
        allow_migration.set()
        applied = migrating.result(timeout=5)
        assert applied[-len(_LATER_MIGRATIONS) :] == _LATER_MIGRATIONS
        written = writing.result(timeout=5)

    assert written.occurred_at == "2026-08-27T09:00:00.000000Z"
    assert written.description == "Newer"


def test_invalid_legacy_timestamp_is_quarantined_without_blocking_reads(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "invalid-timestamp.db"
    _create_pre_timestamp_migration_database(db_path, tmp_path, monkeypatch)
    transaction_id = _seed_legacy_transaction(
        db_path,
        occurred_at="legacy-not-a-time",
    )

    repository = FinancialRepository(str(db_path))

    assert repository.list_transactions() == ([], None)
    assert repository.get_transaction(transaction_id) is None
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT occurred_at, occurred_at_valid, source_updated_at
            FROM financial_transactions WHERE id = ?
            """,
            (transaction_id,),
        ).fetchone()
        migration = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = '004'"
        ).fetchone()

    assert row == ("legacy-not-a-time", 0, "2026-08-27T08:00:00Z#legacy")
    assert migration == (1,)


@pytest.mark.parametrize(
    "legacy_timestamp",
    [
        "2026-08-27t08:00:00.1234567+00:00",
        "2026-08-27X08:00:00.1234567+00:00",
    ],
)
def test_timestamp_migration_quarantines_unsupported_high_precision_separators(
    tmp_path, monkeypatch, legacy_timestamp
):
    db_path = tmp_path / "unsupported-precision-timestamp.db"
    _create_pre_timestamp_migration_database(db_path, tmp_path, monkeypatch)
    transaction_id = _seed_legacy_transaction(
        db_path,
        occurred_at=legacy_timestamp,
        source_updated_at="2026-08-27T08:00:00Z#unsupported-precision",
    )

    applied = run_migrations(str(db_path))
    assert applied[-len(_LATER_MIGRATIONS[1:]) :] == _LATER_MIGRATIONS[1:]

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT occurred_at, occurred_at_valid, source_updated_at
            FROM financial_transactions WHERE id = ?
            """,
            (transaction_id,),
        ).fetchone()

    assert row == (legacy_timestamp, 0, "2026-08-27T08:00:00Z#unsupported-precision")


def test_account_writes_and_reads_tolerate_a_database_before_absence_migration(
    tmp_path, monkeypatch
):
    """A reader meeting an unmigrated database must not fail on a later column.

    Meridian can read a database another process has not finished migrating, so
    an account column added by migration 020 is used only when it exists.
    """
    db_path = tmp_path / "pre-absence.db"
    legacy_migrations = tmp_path / "legacy-migrations"
    legacy_migrations.mkdir()
    for source in sorted(db_module.MIGRATIONS_DIR.glob("0*.sql")):
        if source.name < "020_account_absence_reconciliation.sql":
            shutil.copy(source, legacy_migrations / source.name)
    with monkeypatch.context() as migration_patch:
        migration_patch.setattr(db_module, "MIGRATIONS_DIR", legacy_migrations)
        applied = run_migrations(str(db_path))
    assert "020_account_absence_reconciliation.sql" not in applied

    repository = object.__new__(FinancialRepository)
    repository._db_path = str(db_path)
    account = repository.upsert_account(
        provider="crew",
        external_id="legacy-pocket",
        name="Legacy Pocket",
        account_type="pocket",
        balance=12.0,
        source_updated_at="2026-09-01T00:00:00Z",
    )

    assert account.absent_since is None
    assert [item.id for item in repository.list_accounts()] == [account.id]
    assert repository.get_account(account.id).external_id == "legacy-pocket"

    merged = repository.upsert_account(
        provider="crew",
        external_id="legacy-pocket",
        name="Legacy Pocket",
        account_type="pocket",
        balance=20.0,
        source_updated_at="2026-09-02T00:00:00Z",
    )
    assert merged.id == account.id
    assert merged.balance == 20.0
