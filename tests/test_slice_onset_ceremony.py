"""A slice must declare, at onset, what it is and what should build it — enforced, not remembered.

The owner, 2026-09-25: *"Lately we completely (almost) did away with our entire formalized handoff procedure,
slice breakdown at onset, recommended model per slice, all of that."* He is right, and the reason it lapsed is
structural rather than personal: the model matrix is documented in `MERIDIAN_ROADMAP.md` and named in
`PROJECT_INSTRUCTIONS.md`, but **nothing checked it**, so in practice it was optional and eventually skipped. The
handoff ritual survived precisely because a script regenerates it and a test notices staleness.

So this file is the check. Two properties:

1. **A slice in progress declares its onset plan and its recommended model** — the steps, the model, and why.
2. **The matrix the ceremony draws on still exists**, so the input cannot be quietly deleted.

Existing work is grandfathered explicitly, with a reason, in the same spirit as the write-route ratchet: the debt
is declared where it is incurred, so it can neither grow silently nor be hidden by a list nobody reads.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "project" / "MERIDIAN_OS_TASKS.json"
ROADMAP = ROOT / "docs" / "project" / "MERIDIAN_ROADMAP.md"

#: Slices already under way when the ceremony was restored. Each keeps a reason, and the list can only shrink by
#: a slice gaining its fields or closing — never grow, because a new slice must carry the ceremony from the start.
GRANDFATHERED = {
    "OS-058": "in progress before the ceremony was restored (2026-09-25); declared, not exempt",
    "OS-076": "in progress before the ceremony was restored (2026-09-25); declared, not exempt",
    "OS-080": "in progress before the ceremony was restored (2026-09-25); declared, not exempt",
    "OS-118": "in progress before the ceremony was restored (2026-09-25); declared, not exempt",
    "OS-121": "in progress before the ceremony was restored (2026-09-25); declared, not exempt",
    "OS-122": "in progress before the ceremony was restored (2026-09-25); declared, not exempt",
}

REQUIRED_FIELDS = ("onset_plan", "recommended_model", "model_why")


def test_every_ungrandfathered_slice_in_progress_declares_its_onset_ceremony() -> None:
    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    missing = []
    for task in tasks:
        if task["status"] != "in_progress":
            continue
        if task["id"] in GRANDFATHERED:
            continue
        absent = [field for field in REQUIRED_FIELDS if not task.get(field)]
        if absent:
            missing.append((task["id"], absent))
    assert not missing, (
        "these slices are in progress without an onset ceremony (breakdown at onset + recommended model + why): "
        f"{missing}. Record them on the task before starting work, per D-036 — or grandfather the task with a "
        "stated reason in this file. Both are acceptable; proceeding silently is not."
    )


def test_the_grandfathered_list_does_not_outlive_its_reason() -> None:
    """A grandfather entry for a closed task is a stale exemption, not a policy."""
    tasks = {t["id"]: t for t in json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]}
    stale = [tid for tid in GRANDFATHERED if tasks.get(tid, {}).get("status") in {"done", "complete"}]
    assert not stale, (
        f"these tasks are finished but still grandfathered: {stale}. Remove them so the exemption list keeps "
        "meaning something."
    )


def test_the_model_matrix_the_ceremony_depends_on_still_exists() -> None:
    """The ceremony's input, guarded so it cannot be deleted while the ceremony is still required."""
    text = ROADMAP.read_text(encoding="utf-8")
    assert "Recommended model / effort" in text, "the model matrix vanished from the roadmap; D-036 depends on it"
    assert "| Roadmap section | Recommended model / effort | Fallback | Why |" in text, (
        "the matrix's columns changed shape; the ceremony reads this table and must be updated with it"
    )
