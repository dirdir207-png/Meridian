"""Close a session with an explicit verdict: continue, continue-elsewhere, earmark, or done.

WHY THIS EXISTS. The owner's formulation of the real problem, verbatim: "The blueprint certainly
had a set order originally, thoughtfully composed and gated based on features and import, the
trick is ending sessions and determining (if it isn't a clean pre-defined slice) -- does this
need to continue right now in the new session, or can it be ear marked, be added to a new
addendum to the roadmap file, at a certain checkpoint to be worked on."

That is a decision, and it should not rest on whoever happens to be reading next. Two facts
decide it, and both are checkable rather than matters of judgment:

  1. DAMAGE STATE — is this a safe place to stop? Uncommitted work, an unpushed commit, a stale
     handoff, or a green-gate claim that was never recorded means NO. This is not a priority
     question and it is not negotiable: a session may not end in an unsafe state.
  2. WORK-SHAPE — once safe, is the assigned slice finished? Finished work can be parked with a
     clear conscience. Unfinished work needs to say whether it continues next session or is
     earmarked, and an earmark needs a landable home or it is just an orphaned intention.

This script only REPORTS the verdict and never writes anything. The verdict is a classification
of facts already recorded in git and the ledger, so it cannot invent an assignment, and it never
promotes or prioritises: only the owner decides that work continues.

Exit code is 0 when the session is in a safe state to end, 1 when it is not.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs/project/MERIDIAN_OS_TASKS.json"
HANDOFF = ROOT / "docs/project/HANDOFF.md"
EMERGENT = ROOT / "docs/project/session-emergent.json"
ROADMAP = ROOT / "docs/project/MERIDIAN_ROADMAP.md"
OUT = ROOT / "docs/project/SESSION_CLOSE.md"

FINISHED = {"complete", "done"}


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def due_now(emergent: list[dict], tasks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split parked work into (due at this checkpoint, not yet due).

    THE POINT OF THIS FUNCTION. Parking work against a checkpoint is only half a mechanism — the
    other half is noticing when the checkpoint ARRIVES, or the item is lost exactly like the
    work the parking lot was built to protect. So the trigger is DETECTED from the ledger rather
    than remembered:

      * ``{"kind": "task", "value": "OS-067"}`` — due once that task's status is finished.
      * ``{"kind": "phase", "value": "track-C-V4"}`` — due once no OPEN work remains in it.

    A parked item is deliberately NOT counted as open work for phase completion. It is on hold,
    not in flight; counting it would make its own phase permanently incomplete, and it would
    never come due at all.

    Preferring a predecessor TASK over a phase is the safer default, because a parked item
    usually lives in the very phase its checkpoint names.
    """
    finished = {"complete", "done"}
    by_id = {t["id"]: t for t in tasks}
    # A parked item is on hold, not in flight, so it is excluded when asking whether a phase has
    # open work left. Counting it would make its own phase permanently incomplete.
    parked_ids = {e.get("promoted_to") for e in emergent if e.get("promoted_to")}

    def is_due(check: dict) -> bool:
        kind, value = check.get("kind"), check.get("value")
        if kind == "task":
            t = by_id.get(value)
            return t is not None and t.get("status") in finished
        if kind == "phase":
            rows = [t for t in tasks if (t.get("phase") or "") == value]
            open_rows = [
                t for t in rows
                if t["id"] not in parked_ids and t.get("status") not in finished
            ]
            # A phase with no work at all is not "reached"; it is simply not started.
            return bool(rows) and not open_rows
        return False

    due = [e for e in emergent if e.get("due_check") and is_due(e["due_check"])]
    later = [e for e in emergent if e.get("due_check") and not is_due(e["due_check"])]
    return due, later


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="also write docs/project/SESSION_CLOSE.md")
    args = parser.parse_args()

    dirty = [l for l in git("status", "--porcelain").splitlines() if not l.startswith("??")]
    unpushed = git("log", "--oneline", "@{u}..HEAD")
    handoff_current = subprocess.run(
        [str(ROOT / ".venv311/bin/python"), "scripts/generate_handoff.py", "--check"],
        cwd=ROOT, capture_output=True, text=True,
    ).returncode == 0

    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    in_progress = [t for t in tasks if t.get("status") == "in_progress"]

    emergent = []
    if EMERGENT.exists():
        try:
            emergent = json.loads(EMERGENT.read_text(encoding="utf-8")).get("emergent", [])
        except Exception:  # noqa: BLE001
            emergent = []
    # "Needs a home" means: not promoted into the ledger, AND not parked against a named
    # checkpoint in the roadmap Addendum. An item that has neither is the orphaned intention
    # this whole mechanism exists to prevent.
    unpromoted = [
        e for e in emergent if not e.get("promoted_to") and not e.get("parked_in")
    ]
    decisions_owed = [e for e in emergent if e.get("decision_owed")]

    L: list[str] = []
    L.append("# SESSION CLOSE — the verdict for ending this session")
    L.append("")
    L.append("Generated by `scripts/session_close.py`. Reports only; promotes nothing.")
    L.append("")

    safe = not dirty and not unpushed and handoff_current

    due, later = due_now(emergent, tasks)

    # DUE-NOW COMES FIRST, above even the damage state. A parked item whose checkpoint has been
    # reached is exactly the thing that gets lost, so it is the loudest line in the report and it
    # cannot be reached by reading further down.
    L.append("## 0. DUE AT THIS CHECKPOINT — parked work whose trigger has fired")
    L.append("")
    if due:
        L.append("**The following was parked and its checkpoint has now been reached. It is NOT "
                 "an assignment — an owner decision is still required to schedule it — but it "
                 "must not be silently passed over.**")
        L.append("")
        for e in due:
            dc = e["due_check"]
            trig = (f"task `{dc['value']}` finished" if dc["kind"] == "task"
                    else f"phase `{dc['value']}` has no open work")
            who = e.get("promoted_to") or "(no ledger id)"
            L.append(f"- **{e.get('summary', '(untitled)')}** — {who}")
            L.append(f"  - trigger: {trig}")
            if dc.get("note"):
                L.append(f"  - why then: {dc['note']}")
    else:
        L.append("- (no parked work has come due)")
        if later:
            L.append("")
            L.append("Still waiting on their checkpoint:")
            for e in later:
                dc = e["due_check"]
                want = (f"task `{dc['value']}`" if dc["kind"] == "task"
                        else f"phase `{dc['value']}` with no open work")
                L.append(f"- {e.get('summary', '(untitled)')} — waiting on {want}")
    L.append("")

    L.append("## 1. DAMAGE STATE — may this session end safely?")
    L.append("")
    L.append("| Check | State |")
    L.append("|---|---|")
    L.append(f"| uncommitted tracked changes | {'**FAIL** — ' + str(len(dirty)) + ' path(s)' if dirty else 'ok (clean)'} |")
    L.append(f"| commits not pushed | {'**FAIL** — ' + str(len(unpushed.splitlines())) + ' commit(s)' if unpushed else 'ok (pushed)'} |")
    L.append(f"| handoff current | {'ok' if handoff_current else '**FAIL** — regenerate it'} |")
    L.append("")
    if dirty:
        L.append("Uncommitted paths (finish or revert — a half-finished slice is the one state "
                 "that must never be handed over):")
        for d in dirty:
            L.append(f"- `{d}`")
        L.append("")

    L.append("## 2. THE VERDICT")
    L.append("")
    if not safe:
        L.append("**NOT SAFE TO END.** Resolve the failures above first. This is not a judgement "
                 "call about priority — an uncommitted or unpushed state is simply not a place a "
                 "handoff can be trusted from.")
        verdict = "finish-the-slice"
    elif in_progress:
        ids = ", ".join(f"`{t['id']}`" for t in in_progress)
        L.append(f"**CONTINUE, in this or the next session.** {ids} is still `in_progress`. "
                 "The slice is committed and green, so it may be parked, but the task is not "
                 "finished. Read `progress` on that task to resume at the exact cursor — do not "
                 "restart the slice from the top.")
        verdict = "continue"
    else:
        L.append("**CLEAN STOP.** Nothing is in progress. The next session takes the assigned "
                 "order from `HANDOFF.md` §2; no continuation is owed.")
        verdict = "clean-stop"
        if unpromoted:
            L.append("")
            L.append("Earmarked items exist and are recorded (see §4) — they are NOT assignments "
                     "and do not owe a continuation.")
    L.append("")

    L.append("## 3. WORK-SHAPE — how the unfinished part should land")
    L.append("")
    if verdict == "continue":
        L.append("- **continues:** the `in_progress` task above, same slice, same cursor.")
    if unpromoted:
        L.append(f"- **needs a home ({len(unpromoted)}):** no ledger id and no named checkpoint. "
                 "Each needs one or the other, or it should be dropped — a parking lot that only "
                 "grows becomes the sprawl it was built to prevent.")
        for e in unpromoted:
            L.append(f"  - {e.get('summary', '(untitled)')} ({e.get('arose', '?')})")
    if decisions_owed:
        L.append(f"- **owner decision owed ({len(decisions_owed)}):** cannot move either way "
                 "without an explicit decision, because acting unilaterally would violate C01.")
        for e in decisions_owed:
            L.append(f"  - {e.get('summary', '(untitled)')}")
    if not unpromoted and not decisions_owed and verdict != "continue":
        L.append("- (nothing unfinished and nothing needing a home)")
    L.append("")

    addendum_lines: list[str] = []
    if ROADMAP.exists():
        text = ROADMAP.read_text(encoding="utf-8")
        marker = "## 12. Addendum"
        if marker in text:
            tail = text.split(marker, 1)[1].splitlines()
            # Drop any leading heading residue rather than assuming the split lands cleanly on a
            # line boundary: the em dash and the rest of the heading can remain attached to the
            # first fragment, and emitting "— parked work, and the checkpoint…" as a bullet read
            # as a broken heading. Only the FIRST line can be residue, so only it is dropped.
            for i, line in enumerate(tail):
                if line.strip() in ("", "---") or line.lstrip().startswith(("—", "-", "#")):
                    continue
                addendum_lines = tail[i:]
                break
    L.append("## 4. THE ADDENDUM — where parked work lands")
    L.append("")
    if addendum_lines:
        L.append("Earmarked work lives in `MERIDIAN_ROADMAP.md` §12 Addendum, each entry naming "
                 "the checkpoint it belongs to rather than floating free:")
        L.append("")
        L.extend(addendum_lines)
    else:
        L.append("- the roadmap has no Addendum section yet")
    L.append("")

    L.append("## 5. THE CLOSE-OUT CHECKLIST")
    L.append("")
    L.append("In this order, and the last two cannot be skipped:")
    L.append("")
    L.append("1. Commit or revert every tracked change; push.")
    L.append("2. Run the gates on your scope: `pytest`, `ruff`, `git diff --check`.")
    L.append("3. Record anything session-emergent in `docs/project/session-emergent.json`.")
    L.append("4. Regenerate the handoff: `scripts/generate_handoff.py`.")
    L.append("5. Commit the handoff **as the final commit of the session**, so it describes the "
             "state it was committed in and `--check` returns current.")
    L.append("6. Re-run `scripts/session_close.py` — it must report a safe state.")
    L.append("")

    text = "\n".join(L) + "\n"
    print(text)
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"(written to {OUT.relative_to(ROOT)})")
    return 0 if safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
