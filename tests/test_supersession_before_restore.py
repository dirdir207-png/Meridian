"""A restore is a change with a cause: name what superseded the thing, or say nothing did.

The owner, 2026-09-25: *"if you are recovering old/deleted/revised guards/rules etc, please double check anything
that changed it/superseded it etc or ask me before reverting it back, just in case. I dont want to break parts of
the app as a result."*

Why this needs a check rather than a habit: the OS-122 retrieval pass produced five apparent losses from
`origin/main` and **every one of them was superseded**, not lost — a rule that had moved file, a helper renamed,
a function that gained a parameter, a docstring rewritten into an equivalent sentence. A restorer who trusted the
diff would have reverted four working behaviours into a broken app. Retrieved-but-superseded is the normal case,
not the exception, so it cannot be left to memory.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "project" / "MERIDIAN_OS_TASKS.json"

#: Tasks already open when this rule was written (2026-09-25). Each may only leave this list by gaining
#: `supersession_checked` or by closing.
GRANDFATHERED = {
    "OS-059": "open before the rule was written; declared, not exempt",
    "OS-061": "open before the rule was written; declared, not exempt",
    "OS-063": "open before the rule was written; declared, not exempt",
    "OS-080": "open before the rule was written; declared, not exempt",
    "OS-082": "open before the rule was written; declared, not exempt",
    "OS-097": "open before the rule was written; declared, not exempt",
}

RESTORE_VERBS = re.compile(r"\b(restor|revert|recover|reinstat|re-?introduc|bring back)", re.IGNORECASE)


def test_a_task_proposing_a_restore_declares_what_superseded_it() -> None:
    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    missing = []
    for task in tasks:
        if task["status"] in {"done", "complete", "cancelled"} or task["id"] in GRANDFATHERED:
            continue
        haystack = f"{task.get('title', '')} {task.get('detail', '')}"
        if not RESTORE_VERBS.search(haystack):
            continue
        if not task.get("supersession_checked"):
            missing.append(task["id"])
    assert not missing, (
        f"these tasks propose restoring or reverting something without saying what superseded it: {missing}. "
        "Record `supersession_checked` on the task — naming the superseding code or decision, or stating plainly "
        "that nothing superseded it — before the restore is applied. Per D-037, retrieved-but-superseded is the "
        "normal case."
    )


def test_the_grandfather_list_only_ever_gets_smaller() -> None:
    tasks = {t["id"]: t for t in json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]}
    stale = [tid for tid in GRANDFATHERED if tasks.get(tid, {}).get("status") in {"done", "complete", "cancelled"}]
    assert not stale, f"finished tasks are still grandfathered here: {stale} — remove them."
