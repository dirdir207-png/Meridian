"""Tests for the session-close verdict.

The owner's formulation: "the trick is ending sessions and determining (if it isn't a clean
pre-defined slice) -- does this need to continue right now in the new session, or can it be
earmarked, be added to a new addendum to the roadmap file, at a certain checkpoint to be worked
on." The verdict must be derived from recorded state, not from whoever is reading next.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("session_close", ROOT / "scripts/session_close.py")
close = importlib.util.module_from_spec(spec)
spec.loader.exec_module(close)


def _run(*args):
    return subprocess.run(
        [sys.executable, "scripts/session_close.py", *args],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_the_close_report_names_the_damage_state_checks():
    out = _run().stdout
    for check in ("uncommitted tracked changes", "commits not pushed", "handoff current"):
        assert check in out, f"the damage-state table must carry {check}"


def test_the_report_never_promotes_or_assigns():
    out = _run().stdout
    assert "promotes nothing" in out
    assert "NOT SAFE TO END" in out or "CLEAN STOP" in out or "CONTINUE" in out


def test_an_uncommitted_tree_is_reported_as_unsafe():
    """Falsification of the core rule: a half-finished slice must never be handed over."""
    result = _run()
    dirty = [l for l in close.git("status", "--porcelain").splitlines() if not l.startswith("??")]
    if dirty:
        assert result.returncode == 1
        assert "NOT SAFE TO END" in result.stdout
    else:
        assert result.returncode == 0, result.stdout


def test_parked_items_must_name_a_checkpoint_or_a_ledger_id():
    """Every emergent item needs a landable home; otherwise it is an orphaned intention."""
    ledger_ids = {t["id"] for t in json.loads(close.LEDGER.read_text(encoding="utf-8"))["tasks"]}
    data = json.loads(close.EMERGENT.read_text(encoding="utf-8"))
    for e in data["emergent"]:
        assert "promoted_to" in e or "parked_in" in e, (
            f"{e.get('summary')!r} has no ledger id and no named checkpoint"
        )
        if "promoted_to" in e:
            assert e["promoted_to"] in ledger_ids


def test_the_addendum_section_is_emitted_without_heading_residue():
    """A split on the marker can leave the em dash attached; emitting that as a bullet once read
    as a broken heading, so the residue must be dropped."""
    out = _run().stdout
    assert "THE ADDENDUM" in out
    for line in out.splitlines():
        assert not line.strip().startswith("—"), f"heading residue leaked into the report: {line!r}"


def test_the_addendum_and_the_ledger_agree_about_parked_work():
    """A roadmap entry claiming to be parked must not also claim to be scheduled."""
    text = (ROOT / "docs/project/MERIDIAN_ROADMAP.md").read_text(encoding="utf-8")
    assert "## 12. Addendum" in text
    marker = text.split("## 12. Addendum", 1)[1]
    assert "Nothing here is assigned" in marker, (
        "the Addendum must state that parking is not authorisation"
    )


# --- the parking-lot trigger: parked work must SURFACE when its checkpoint arrives ----------
#
# Parked work has to work BOTH ways: the roadmap must not be forgotten, and neither must the
# park. Parking against a checkpoint is only half a mechanism, and noticing the checkpoint
# arrived is the other half.


def _task(tid, status="open", phase="track-C-V1"):
    return {"id": tid, "title": tid, "status": status, "priority": "medium", "phase": phase}


def test_parked_work_is_not_due_while_its_predecessor_is_open():
    emergent = [{"summary": "parked", "due_check": {"kind": "task", "value": "OS-100"}}]
    due, later = close.due_now(emergent, [_task("OS-100", status="open")])
    assert due == []
    assert later and later[0]["summary"] == "parked"


def test_parked_work_becomes_due_when_its_predecessor_finishes():
    """The other half of the mechanism: a reached checkpoint must be impossible to miss."""
    emergent = [{"summary": "parked", "due_check": {"kind": "task", "value": "OS-100"}}]
    for status in ("complete", "done"):
        due, later = close.due_now(emergent, [_task("OS-100", status=status)])
        assert due and due[0]["summary"] == "parked", f"{status} must make it due"
        assert later == []


def test_a_parked_item_is_not_counted_as_open_work_for_phase_completion():
    """Otherwise a parked item sitting in its own checkpoint phase makes that phase permanently
    incomplete, so it never comes due — the very silent loss the parking lot exists to prevent."""
    emergent = [{"summary": "parked", "promoted_to": "OS-200",
                 "due_check": {"kind": "phase", "value": "track-C-V9"}}]
    tasks = [_task("OS-200", status="open", phase="track-C-V9")]
    due, _later = close.due_now(emergent, tasks)
    assert due, "the phase counts as reached once only parked work remains in it"


def test_an_empty_phase_is_not_a_reached_checkpoint():
    """A phase with no work at all is simply not started. Firing here is the false positive this
    check produced in practice, which is why OS-070 was re-pointed at a real task."""
    emergent = [{"summary": "p", "promoted_to": "OS-300",
                 "due_check": {"kind": "phase", "value": "track-C-V8"}}]
    due, _ = close.due_now(emergent, [])
    assert due == [], "an empty phase is not a reached checkpoint"


def test_an_unknown_trigger_fails_closed():
    """A typo in a checkpoint reference must never fire, because firing wrongly wastes an owner
    decision while failing to fire loses the work — and of the two, failing closed is safer."""
    unknown_task = [{"summary": "p", "due_check": {"kind": "task", "value": "OS-999"}}]
    due, later = close.due_now(unknown_task, [_task("OS-100")])
    assert due == [] and later
    bogus_kind = [{"summary": "q", "due_check": {"kind": "nonsense", "value": "x"}}]
    assert close.due_now(bogus_kind, [_task("OS-100")])[0] == []


def test_due_work_is_reported_above_the_damage_state():
    """A reached checkpoint is the loudest thing in the report, because it is what gets lost."""
    out = _run().stdout
    assert "DUE AT THIS CHECKPOINT" in out
    assert out.index("DUE AT THIS CHECKPOINT") < out.index("DAMAGE STATE")
