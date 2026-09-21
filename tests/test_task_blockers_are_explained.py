"""A task may be `blocked` only with a recorded, checkable reason.

THE PATTERN THIS EXISTS TO STOP. The owner has now been told roughly five times that work was
"owner gated" when it was not. It happened again in this session: VIRGIL-A0's title is "Approve
Virgil contracts and establish the compatible iOS toolchain", which READS like an owner gate, and
the ledger's own statuses -- A0 `ready`, A1 `blocked`, A5 `blocked` -- invited the inference that
A0 gates the others. Nothing in the record says any such thing. The owner's reply: "VIRGIL A0 is
NOT the gate."

Why this keeps happening, and why a rule is the right instrument:

1. An invented owner-gate is the CHEAPEST possible blocker. It sounds responsible, it cannot be
   checked by the person reading it, and it moves the work off the agent without anyone being
   accountable for the delay. Every other reason a task might be blocked (a schema, a failing
   test, an unmerged dependency) is a claim that can be falsified; "needs the owner" is not.
2. The ENABLING CONDITION IS AN EMPTY FIELD. VIRGIL-A1 and VIRGIL-A5 both carry status `blocked`
   and literally nothing else -- no reason, no dependency, no question, no progress. A reader who
   has to guess will guess, and the guess that costs the reader least is the one that blames
   someone else.
3. A TITLE IS NOT A GATE. "Approve X" describes the work; it does not establish who must act or
   whether anything is actually pending. Inferring a dependency from a title is how a task sits
   untouched for sessions while looking diligently parked.

So: a blocked task must say what blocks it, and a blocker that names the OWNER must name the
pending decision in its own field. An honest "reason not recorded" is acceptable -- guessing is
not.
"""
import json
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "docs/project/MERIDIAN_OS_TASKS.json"

#: Fields a task may use to explain a blocker. `progress` counts: a task whose progress explains
#: exactly what is stuck is not hiding anything.
REASON_FIELDS = ("blocked_reason", "blocked_by", "depends_on", "depends", "progress")

#: Phrases that ASSERT an owner dependency. Deliberately not the bare word "owner", and the
#: reason is this session's own record: the `blocked_reason` written for VIRGIL-A1..A5 explains AT
#: LENGTH that the owner is NOT the gate, and a keyword match flagged exactly that sentence. A
#: guard that cries wolf about the record is the same defect as a guard that cries wolf about a
#: layout, so this matches claims rather than vocabulary. A reason may discuss the owner freely;
#: what it may not do is assert that the owner is what it is waiting for.
OWNER_GATE_PHRASES = (
    "owner gated",
    "owner-gated",
    "waiting on the owner",
    "waiting for the owner",
    "awaiting the owner",
    "awaiting owner",
    "needs the owner",
    "needs owner",
    "requires the owner",
    "pending owner",
    "blocked on the owner",
    "waiting on your",
    "awaiting your",
    "your decision",
    "your approval",
    "owner decision is pending",
)


def _blocked_tasks() -> list[dict]:
    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    return [t for t in tasks if t.get("status") == "blocked"]


def test_every_blocked_task_states_what_blocks_it():
    """No task may be parked on a reason nobody wrote down."""
    silent = []
    for task in _blocked_tasks():
        if not any(str(task.get(field, "")).strip() for field in REASON_FIELDS):
            silent.append(task["id"])
    assert not silent, (
        "these tasks are `blocked` with NO recorded reason, so every reader has to invent one -- "
        f"and the cheapest invention blames the owner: {silent}. Record the actual blocker, or "
        "record that it is not yet known and make finding out the task."
    )


def test_a_blocker_that_names_the_owner_names_the_decision():
    """'Waiting on the owner' is only a fact if the question and its deadline exist.

    A task that genuinely needs an owner decision must carry `owner_question` -- the decision in
    one sentence -- so a reader can see whether it is still open, and so the owner can answer it
    instead of being handed a task that silently waits for him.
    """
    vague = []
    for task in _blocked_tasks():
        blob = " ".join(str(task.get(field, "")) for field in REASON_FIELDS).lower()
        if any(phrase in blob for phrase in OWNER_GATE_PHRASES) and not str(task.get("owner_question", "")).strip():
            vague.append(task["id"])
    assert not vague, (
        "these tasks attribute their block to the OWNER without naming the pending decision, "
        f"which is how a false owner-gate gets created: {vague}. Add `owner_question`, or record "
        "the real blocker -- which is usually not the owner."
    )


def test_no_task_claims_an_owner_gate_from_its_title_alone():
    """The VIRGIL-A0 failure, pinned.

    A title beginning with an approval verb describes work; it does NOT establish that anything
    is pending. If such a task is blocked, its reason must be recorded like any other -- and this
    test names the exact class of task that has been misread this way, so the next session reads
    the REASON rather than the title.
    """
    approval_verbs = ("approve", "approves", "sign off", "sign-off", "ratify", "decide")
    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    for task in tasks:
        title = str(task.get("title", "")).lower()
        if task.get("status") == "blocked" and title.startswith(approval_verbs):
            assert any(str(task.get(field, "")).strip() for field in REASON_FIELDS), (
                f"{task['id']} is blocked and its title starts with an approval verb, which is "
                "read as an owner gate -- but nothing records that the owner is actually "
                "pending. Record the real blocker."
            )
