"""Tests for the roadmap/handoff reconciliation check.

The check exists so a handoff is a projection of the governing docs rather than a summary of a
session. These tests pin the two conditions that make it load-bearing: roadmap coverage, and
every unfinished task declaring a track.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "handoff_check", ROOT / "scripts/roadmap_handoff_check.py"
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def _write(tmp_path, roadmap_ids, tasks):
    roadmap = tmp_path / "MERIDIAN_ROADMAP.md"
    roadmap.write_text(
        "# Roadmap\n\n" + "\n".join(f"- {i} is planned." for i in roadmap_ids), encoding="utf-8"
    )
    ledger = tmp_path / "MERIDIAN_OS_TASKS.json"
    ledger.write_text(json.dumps({"tasks": tasks}), encoding="utf-8")
    return roadmap, ledger


def _task(tid, status="open", phase="track-C-V1", **extra):
    base = {"id": tid, "title": f"{tid} title", "status": status, "priority": "medium"}
    if phase is not None:
        base["phase"] = phase
    base.update(extra)
    return base


def test_passes_when_roadmap_and_ledger_agree(tmp_path, monkeypatch):
    roadmap, ledger = _write(
        tmp_path, ["OS-001", "OS-002"], [_task("OS-001"), _task("OS-002"), _task("OS-003", status="complete")]
    )
    monkeypatch.setattr(check, "ROADMAP", roadmap)
    monkeypatch.setattr(check, "LEDGER", ledger)
    monkeypatch.setattr("sys.argv", ["check", "--quiet"])
    assert check.main() == 0


def test_fails_when_a_roadmap_item_is_absent_from_the_ledger(tmp_path, monkeypatch):
    """Planned work with no home is the 'losing sight of a slice' failure, so it must fail."""
    roadmap, ledger = _write(tmp_path, ["OS-001", "OS-999"], [_task("OS-001")])
    monkeypatch.setattr(check, "ROADMAP", roadmap)
    monkeypatch.setattr(check, "LEDGER", ledger)
    monkeypatch.setattr("sys.argv", ["check", "--quiet"])
    assert check.main() == 1


def test_fails_when_a_finished_task_lacks_a_track(tmp_path, monkeypatch):
    """A finished task is history; only unfinished work must declare where it belongs."""
    roadmap, ledger = _write(tmp_path, ["OS-001"], [_task("OS-001", status="complete", phase=None)])
    monkeypatch.setattr(check, "ROADMAP", roadmap)
    monkeypatch.setattr(check, "LEDGER", ledger)
    monkeypatch.setattr("sys.argv", ["check", "--quiet"])
    assert check.main() == 0


def test_fails_when_an_unfinished_task_declares_no_track(tmp_path, monkeypatch):
    """The real regression this exists for: OS-067 was high priority, in progress, and belonged
    to no declared track -- which is precisely how a slice drifts."""
    roadmap, ledger = _write(tmp_path, ["OS-001"], [_task("OS-001", phase=None)])
    monkeypatch.setattr(check, "ROADMAP", roadmap)
    monkeypatch.setattr(check, "LEDGER", ledger)
    monkeypatch.setattr("sys.argv", ["check", "--quiet"])
    assert check.main() == 1


def test_a_blocked_task_still_needs_a_track(tmp_path, monkeypatch):
    """Blocked is in flight, not finished."""
    roadmap, ledger = _write(
        tmp_path, ["OS-001"], [_task("OS-001", status="blocked", phase=None)]
    )
    monkeypatch.setattr(check, "ROADMAP", roadmap)
    monkeypatch.setattr(check, "LEDGER", ledger)
    monkeypatch.setattr("sys.argv", ["check", "--quiet"])
    assert check.main() == 1


def test_an_unplanned_but_declared_task_does_not_fail_the_check(tmp_path, monkeypatch):
    """A defect found mid-session is legitimately absent from the roadmap. It must be VISIBLE
    (reported), not fatal -- failing here would punish honest reporting."""
    roadmap, ledger = _write(tmp_path, ["OS-001"], [_task("OS-001"), _task("OS-042")])
    monkeypatch.setattr(check, "ROADMAP", roadmap)
    monkeypatch.setattr(check, "LEDGER", ledger)
    monkeypatch.setattr("sys.argv", ["check", "--quiet"])
    assert check.main() == 0


def test_the_real_repository_reconciles():
    """The live ledger and roadmap must agree; if this fails, do not write a handoff."""
    import sys

    old = sys.argv
    sys.argv = ["check", "--quiet"]
    try:
        assert check.main() == 0
    finally:
        sys.argv = old
