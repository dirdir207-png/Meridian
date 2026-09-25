"""Tests for the generated handoff.

The handoff is the artifact the owner relies on when context runs out, so its guarantees must be
pinned: it is DERIVED from the governing docs, it names its basis by hash, it keeps session
momentum visibly separate from assigned work, and it detects its own staleness.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "gen_handoff", ROOT / "scripts/generate_handoff.py"
)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _run(*args):
    return subprocess.run(
        [sys.executable, "scripts/generate_handoff.py", *args],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_the_generated_handoff_exists_and_names_its_basis():
    text = (ROOT / "docs/project/HANDOFF.md").read_text(encoding="utf-8")
    # A handoff that cannot name the docs it came from is a session summary.
    for source in ("AGENTS.md", "MERIDIAN_ROADMAP.md", "MERIDIAN_DECISIONS.md", "MERIDIAN_OS_TASKS.json"):
        assert source in text, f"basis must name {source}"
    assert "sha256" in text or "| `" in text, "the basis must carry hashes so staleness is visible"


def test_the_handoff_quotes_the_roadmaps_own_next_move():
    text = (ROOT / "docs/project/HANDOFF.md").read_text(encoding="utf-8")
    assert "THE ASSIGNED ORDER" in text
    # Quoted, not paraphrased: the roadmap's own words must appear.
    assert "Track I.1" in text, "the assigned order must carry the roadmap's actual next move"


def test_session_emergent_items_are_separated_from_assigned_work():
    """The core safety property: a session idea must never sit in the same list as planned work."""
    text = (ROOT / "docs/project/HANDOFF.md").read_text(encoding="utf-8")
    assert "SESSION-EMERGENT" in text
    assert "promotes nothing" in text
    # The emergent section must come after the assigned/flight sections, never inside them.
    assert text.index("IN FLIGHT") < text.index("SESSION-EMERGENT")


def test_hand_editing_is_explicitly_forbidden():
    text = (ROOT / "docs/project/HANDOFF.md").read_text(encoding="utf-8")
    assert "Do not edit by" in text


def test_untracked_artifacts_do_not_make_the_handoff_claim_a_dirty_tree():
    """~440 untracked artifacts/** and tmp/** paths are scratch by convention; a handoff that
    cries wolf gets ignored."""
    changed = [l for l in gen.git("status", "--porcelain").splitlines() if not l.startswith("??")]
    text = (ROOT / "docs/project/HANDOFF.md").read_text(encoding="utf-8")
    if not changed:
        assert "working tree clean" in text
    else:
        assert "tracked path(s) modified" in text


def test_check_reports_current_for_the_committed_state():
    """Against the committed handoff, --check must pass, or CI can never be green."""
    result = _run("--check")
    if result.returncode != 0:
        # A stale file is a legitimate failure mode, but then it must say so clearly.
        assert "STALE" in result.stdout
    else:
        assert "current" in result.stdout


def test_a_mutated_governing_doc_makes_the_handoff_stale(tmp_path, monkeypatch, capsys):
    """Falsification: change the ledger, and the handoff must show the change.

    RETARGETED 2026-09-25. This mutated `tasks[0]` and asserted its title appeared in the handoff.
    That held only while `tasks[0]` happened to be unfinished: the handoff lists OPEN work only
    (`open_tasks`), and the ledger reconciliation of 2026-09-25 closed `tasks[0]` (OS-001, the old
    umbrella), so the mutation stopped being visible -- the test failed for a fixture assumption, not
    because the property broke. It now mutates a task the generator actually prints, and asserts that
    such a task exists, so the falsification cannot silently degrade into a no-op.
    """
    ledger = json.loads(gen.LEDGER.read_text(encoding="utf-8"))
    fake = tmp_path / "MERIDIAN_OS_TASKS.json"
    open_tasks = [t for t in ledger["tasks"] if t.get("status") not in gen.FINISHED]
    assert open_tasks, "the ledger has no unfinished task for this falsification to mutate"
    open_tasks[0]["title"] = "mutated for the staleness test"
    fake.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    monkeypatch.setattr(gen, "LEDGER", fake)
    monkeypatch.setattr(gen, "OUT", tmp_path / "HANDOFF.md")
    monkeypatch.setattr("sys.argv", ["gen", "--stdout"])
    assert gen.main() == 0
    printed = capsys.readouterr().out
    assert "mutated for the staleness test" in printed


def test_the_emergent_file_cannot_promote_anything_by_itself():
    """Each emergent entry either names a ledger id the owner granted, or says it is unpromoted."""
    data = json.loads((ROOT / "docs/project/session-emergent.json").read_text(encoding="utf-8"))
    ledger_ids = {
        t["id"] for t in json.loads(gen.LEDGER.read_text(encoding="utf-8"))["tasks"]
    }
    assert "emergent" in data
    for entry in data["emergent"]:
        assert entry.get("summary"), "every emergent entry needs a summary"
        assert entry.get("arose"), "every emergent entry needs a date"
        if "promoted_to" in entry:
            assert entry["promoted_to"] in ledger_ids, (
                f"{entry['promoted_to']} claims promotion but is not in the ledger"
            )
