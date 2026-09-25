"""The evaluation harness's own tests — including the falsifier it needs to be worth trusting.

The harness lane's rule, 2026-09-25: *a gate you have only ever seen approve is untested; design the falsifier,
not the confirmation.* So every anomaly class this module can report is asserted with a deliberately broken
input, and the empty case is asserted to be HONEST rather than clean. If the detector silently stopped working,
`test_a_broken_run_actually_reaches_the_detector` fails.
"""
from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

import pytest

from meridian.ai import evaluation
from meridian.ai.run_records import RunRecordStore

ROOT = Path(__file__).resolve().parents[2]


@dataclasses.dataclass
class FakeRun:
    """A stand-in with the same attribute surface `evaluate_runs` reads. Deliberately not a real RunRecord:
    these tests are about the harness's reasoning, not about the writer that the run-records suite covers."""

    id: int
    role: str
    provider: str
    model: str
    prompt_version: str
    evidence_ids: tuple[str, ...]
    started_at: str
    ended_at: str
    outcome: str
    recorded_at: str = "2026-09-25T12:00:00+00:00"


def run(**overrides) -> FakeRun:
    base = dict(
        id=1, role="investigator", provider="openai", model="gpt-x", prompt_version="investigator-v1",
        evidence_ids=("charge:1",), started_at="2026-09-25T12:00:00+00:00",
        ended_at="2026-09-25T12:00:02+00:00", outcome="ok",
    )
    base.update(overrides)
    return FakeRun(**base)


# --------------------------------------------------------------------------- the honest empty case
def test_zero_runs_is_not_evidence_of_health():
    report = evaluation.evaluate_runs([])
    assert report.runs_total == 0
    assert report.measured is False
    assert report.refusal_reason is not None
    assert "NOT evidence" in report.refusal_reason
    assert report.by_role == {}


def test_a_real_empty_store_reports_measured_false_without_writing_to_it(tmp_path):
    store = RunRecordStore(str(tmp_path / "meridian.db"))
    before = store.count()
    report = evaluation.evaluate_store(store)
    assert report.measured is False
    assert store.count() == before == 0, "evaluation must not write to the store it measures"


# ------------------------------------------------------------------------------- the falsifiers
def test_a_broken_run_actually_reaches_the_detector():
    """If this fails, every other anomaly test in this file is passing for the wrong reason."""
    kinds = {a.kind for a in evaluation.evaluate_runs([run(outcome="ok", evidence_ids=())]).anomalies}
    assert "uncited_ok" in kinds


def test_an_uncited_ok_run_is_flagged_and_counted():
    report = evaluation.evaluate_runs([run(id=7, evidence_ids=())])
    assert [a.kind for a in report.anomalies] == ["uncited_ok"]
    assert report.anomalies[0].run_id == 7
    stats = report.by_role["investigator"]
    assert stats.uncited_ok_runs == [7]
    assert stats.citation_rate == 0.0


def test_an_uncited_refusal_is_NOT_an_anomaly():
    """Refusing with no evidence is the discipline working, not a defect."""
    report = evaluation.evaluate_runs([run(outcome="unavailable", evidence_ids=())])
    assert report.anomalies == []
    assert report.by_role["investigator"].refusal_rate == 1.0


def test_an_unknown_outcome_is_flagged():
    report = evaluation.evaluate_runs([run(outcome="probably-fine")])
    assert [a.kind for a in report.anomalies] == ["unknown_outcome"]
    assert report.by_role["investigator"].unknown_outcome == 1


def test_a_run_that_ended_before_it_started_is_flagged():
    report = evaluation.evaluate_runs([run(started_at="2026-09-25T12:00:05+00:00",
                                           ended_at="2026-09-25T12:00:00+00:00")])
    assert [a.kind for a in report.anomalies] == ["negative_duration"]


def test_an_unparseable_timestamp_is_flagged_rather_than_silently_dropped():
    report = evaluation.evaluate_runs([run(started_at="yesterday", ended_at="tomorrow")])
    assert [a.kind for a in report.anomalies] == ["unparseable_timestamp"]


# ------------------------------------------------------------------------------------- the floor
def test_no_verdict_below_the_floor_and_the_reason_says_so():
    report = evaluation.evaluate_runs([run(id=i) for i in range(evaluation.MIN_RUNS_FOR_A_ROLE_VERDICT - 1)])
    stats = report.by_role["investigator"]
    assert stats.has_verdict is False
    assert "insufficient data" in stats.verdict()
    assert "not evidence of health" in stats.verdict()
    assert report.roles_with_a_verdict() == []


def test_a_verdict_appears_at_the_floor_and_reports_the_distribution():
    runs = [run(id=i) for i in range(evaluation.MIN_RUNS_FOR_A_ROLE_VERDICT - 1)]
    runs.append(run(id=99, outcome="failed"))
    report = evaluation.evaluate_runs(runs)
    stats = report.by_role["investigator"]
    assert stats.has_verdict is True
    assert "4 ok / 0 unavailable / 1 failed" in stats.verdict()
    assert report.roles_with_a_verdict() == ["investigator"]


def test_a_clean_run_produces_no_anomalies_and_keeps_its_provider_and_version():
    report = evaluation.evaluate_runs([run()])
    assert report.anomalies == []
    stats = report.by_role["investigator"]
    assert stats.ok == 1 and stats.runs_citing_evidence == 1
    assert stats.providers == {"openai"} and stats.prompt_versions == {"investigator-v1"}
    assert stats.median_duration_ms == pytest.approx(2000.0)


def test_evaluation_reads_the_migration_backed_table_without_a_schema_of_its_own(tmp_path):
    """The harness must not introduce storage. It reads 027's table and nothing else."""
    db = tmp_path / "meridian.db"
    store = RunRecordStore(str(db))
    with sqlite3.connect(db) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "ai_run_records" in tables
    assert store.count() == 0


def test_the_harness_has_no_writer_by_construction():
    """A measurement system that can write to what it measures is not a measurement system."""
    source = (ROOT / "meridian" / "ai" / "evaluation.py").read_text()
    for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "commit(", "executemany("):
        assert forbidden not in source, f"evaluation.py contains {forbidden!r}"
