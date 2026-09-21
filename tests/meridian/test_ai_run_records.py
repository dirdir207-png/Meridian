"""Persisted AI run records — the audit trail behind an answer.

Track I.1 asks for the run record to be "persisted so a proposal can be audited back to the
reasoning that produced it". These tests cover the store, the schema's deliberate refusals,
and the command's recording path.

No provider is contacted anywhere in this file.
"""
import ast
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

from meridian.ai.envelope import RunRecord
from meridian.ai.run_records import RunRecordStore

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "investigate.py"

MIGRATION = ROOT / "meridian" / "migrations" / "027_ai_run_records.sql"


def _load_script():
    spec = importlib.util.spec_from_file_location("investigate_script_rr", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["investigate_script_rr"] = module
    spec.loader.exec_module(module)
    return module


investigate_script = _load_script()


def _record(**overrides) -> RunRecord:
    base = {
        "role": "investigator",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "prompt_version": "investigator-v1",
        "evidence_ids": ("evidence:1", "evidence:2"),
        "started_at": "2026-09-08T11:42:00Z",
        "ended_at": "2026-09-08T11:42:03Z",
        "outcome": "ok",
    }
    base.update(overrides)
    return RunRecord(**base)


@pytest.fixture
def store(tmp_path):
    return RunRecordStore(str(tmp_path / "meridian.db"))


# ---------------------------------------------------------------------------------------
# The schema's deliberate refusals
# ---------------------------------------------------------------------------------------

def test_the_table_stores_no_claim_text_and_no_evidence_body(tmp_path):
    """A run record is a POINTER to the reasoning, not a copy of it.

    Storing generated prose would create a second, unversioned home for financial statements
    outside the evidence store and outside the surfaces that label provenance and freshness.
    Checked against the real schema, so an added `claims` column fails here.
    """
    db_path = str(tmp_path / "meridian.db")
    RunRecordStore(db_path)
    with sqlite3.connect(db_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(ai_run_records)")
        }
    assert columns == {
        "id", "role", "provider", "model", "prompt_version", "evidence_ids",
        "started_at", "ended_at", "outcome", "recorded_at",
    }
    for forbidden in ("claim", "text", "content", "body", "answer", "response", "summary"):
        assert not any(forbidden in column for column in columns), forbidden


def test_evidence_ids_are_not_a_foreign_key(tmp_path):
    """An audit row must survive evidence being revoked or deleted and still say what was
    consulted. A cascade would erase the row that explains why an answer was given."""
    db_path = str(tmp_path / "meridian.db")
    store = RunRecordStore(db_path)
    store.record(_record(evidence_ids=("evidence:999999",)))

    with sqlite3.connect(db_path) as connection:
        foreign_keys = list(connection.execute("PRAGMA foreign_key_list(ai_run_records)"))
    assert foreign_keys == []


def test_the_migration_grants_no_authority(tmp_path):
    """Nothing in this table can reference a provider mutation or a financial amount."""
    text = MIGRATION.read_text(encoding="utf-8")
    sql = "\n".join(line for line in text.splitlines() if not line.strip().startswith("--"))
    for forbidden in ("amount", "balance", "provider_write", "approve", "execute"):
        assert forbidden not in sql.lower(), forbidden


# ---------------------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------------------

def test_a_run_round_trips_with_everything_an_audit_needs(store):
    stored = store.record(_record())
    assert stored.id > 0
    assert stored.role == "investigator"
    assert stored.provider == "deepseek"
    assert stored.model == "deepseek-chat"
    assert stored.prompt_version == "investigator-v1"
    assert stored.evidence_ids == ("evidence:1", "evidence:2")
    assert stored.started_at == "2026-09-08T11:42:00Z"
    assert stored.ended_at == "2026-09-08T11:42:03Z"
    assert stored.outcome == "ok"
    assert stored.recorded_at


def test_records_list_newest_first_and_filter_by_role(store):
    store.record(_record(outcome="ok"), recorded_at="2026-09-08T10:00:00Z")
    store.record(_record(outcome="failed:unsupported-citation"), recorded_at="2026-09-08T12:00:00Z")
    store.record(_record(role="teacher", outcome="ok"), recorded_at="2026-09-08T11:00:00Z")

    recent = store.list_recent(limit=10)
    assert [run.recorded_at for run in recent] == [
        "2026-09-08T12:00:00Z",
        "2026-09-08T11:00:00Z",
        "2026-09-08T10:00:00Z",
    ]
    assert [run.role for run in store.list_recent(role="investigator")] == [
        "investigator",
        "investigator",
    ]
    assert store.count() == 3
    assert store.count(role="teacher") == 1


def test_the_limit_is_clamped_so_a_caller_cannot_read_the_whole_table(store):
    for index in range(5):
        store.record(_record(), recorded_at=f"2026-09-08T1{index}:00:00Z")
    assert len(store.list_recent(limit=2)) == 2
    # A nonsense or hostile limit cannot turn into "everything".
    assert len(store.list_recent(limit=0)) == 1
    assert len(store.list_recent(limit=-5)) == 1
    assert len(store.list_recent(limit=10_000)) == 5


def test_get_returns_none_rather_than_raising_for_a_missing_row(store):
    assert store.get(4321) is None


def test_a_malformed_evidence_array_does_not_hide_the_rest_of_the_trail(store, tmp_path):
    """A corrupt row must still be readable: raising here would hide every other run."""
    store.record(_record())
    with sqlite3.connect(store.db_path) as connection:
        connection.execute("UPDATE ai_run_records SET evidence_ids = ?", ("{not json",))
    runs = store.list_recent(limit=10)
    assert len(runs) == 1
    assert runs[0].evidence_ids == ()
    assert runs[0].outcome == "ok"


def test_the_store_offers_no_way_to_edit_or_delete_history(store):
    """An audit trail that can be rewritten is not an audit trail."""
    for name in ("update", "delete", "remove", "clear", "purge"):
        assert not hasattr(store, name), name


def test_the_store_imports_no_provider_write_path():
    """Recording a read-only role's run must not put a write path in reach."""
    import meridian.ai.run_records as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = ("meridian.crew_write", "meridian.crew_write_actions", "meridian.mutations")
    hit = {name for name in imported if any(name.startswith(f) for f in forbidden)}
    assert not hit, sorted(hit)


# ---------------------------------------------------------------------------------------
# The command's recording path
# ---------------------------------------------------------------------------------------

def test_the_script_records_a_run_and_reports_the_row(tmp_path):
    """The command is the store's first real writer, which is what makes persistence real
    rather than speculative infrastructure with no caller."""
    db = str(tmp_path / "meridian.db")
    record = _record()
    assert investigate_script.record_run(
        type("R", (), {"record": record})(), db
    ) == 1
    stored = RunRecordStore(db).list_recent(limit=5)
    assert len(stored) == 1
    assert stored[0].role == "investigator"


def test_history_renders_recent_runs_and_says_so_when_there_are_none(tmp_path):
    db = str(tmp_path / "meridian.db")
    RunRecordStore(db)  # create the schema
    assert "no runs recorded yet" in investigate_script.show_history(db, limit=5)

    RunRecordStore(db).record(_record(outcome="failed:unsupported-citation"))
    text = investigate_script.show_history(db, limit=5)
    assert "investigator" in text
    assert "failed:unsupported-citation" in text


def test_the_rendered_output_names_the_record_it_kept():
    payload = {
        "status": "ok", "detail": None, "claims": [], "disagreements": [],
        "assumptions": [], "confidence": 0.0, "what_would_change": [],
        "run": _record().as_dict(), "recorded_id": 7,
    }
    text = investigate_script.format_text(payload)
    assert "ai_run_records#7" in text
    # And with no record kept, no id is implied.
    payload["recorded_id"] = None
    assert "ai_run_records" not in investigate_script.format_text(payload)
