"""Track I.2 — the Investigator: one role end to end, on I.1's envelope.

MERIDIAN_ROADMAP.md §6, **I.2 — One role, end to end**: *"Ship the Forecaster or
Investigator first — read-only, evidence-bound, immediately useful. Adversarial tests:
hallucinated citation, missing evidence, contradictory sources, unavailable model. Prove the
envelope before adding roles."*

**The Investigator answers a question about a charge, an event or a discrepancy from the
evidence actually linked to it, and says so when it cannot.**

The four properties that make it safe are now inherited from ``meridian/ai/role.py`` and are
checked in ``tests/meridian/test_ai_investigator.py`` rather than described here:

1. **No evidence, no answer.** If nothing is linked to the target, the run returns
   ``UNAVAILABLE`` and the model is *never called*.
2. **A hallucinated citation voids the result.** Every claim must cite evidence the task
   actually supplied; when it does not, the result is ``FAILED`` carrying **no claims at
   all**, so a fabricated citation cannot reach a reader even by accident.
3. **Disagreement is recorded, not settled.** Two claims about the same subject that do not
   agree are both returned, with the conflict marked.
4. **An unavailable model is a state, not an exception.** A failing client yields
   ``UNAVAILABLE``; the role never raises into its caller and never retries.

**It receives a client and never builds one** — see ``meridian/ai/role.py``. A test asserts
this module contains no ``requests``, no ``api_key``, no ``os.environ`` and no ``subprocess``

**This role is what I.1 was for.** It reads; it never writes. It holds no provider write tool
— ``meridian/ai/envelope.py`` proves that for every role at import.
"""

from __future__ import annotations

from meridian.ai.role import (  # noqa: F401 - re-exported: callers import these from here
    EvidenceBoundRole,
    RoleRun,
    humanize_age,
)

ROLE = "investigator"
PROMPT_VERSION = "investigator-v1"

SYSTEM_PROMPT = (
    "You are the Investigator for Meridian. You answer ONLY from the evidence supplied. "
    "Return JSON with `claims`, `assumptions`, `confidence` and `what_would_change`. "
    "Each claim is an object with `text`, `evidence_ids` (ids copied exactly from the "
    "supplied evidence) and `subject` (a short key naming the FACT the claim is about, so "
    "two claims about the same fact can be compared). Every claim MUST cite at least one "
    "supplied evidence id; never cite an id you were not given and never invent one. If "
    "the evidence does not answer the question, return no claims. Never state that an "
    "action was taken or will be taken."
)


class Investigator(EvidenceBoundRole):
    """Find the evidence behind a charge, an event or a discrepancy. Read-only.

    ``evidence_repository`` is any object exposing ``list_links_for_target(target_kind,
    target_id)`` and ``get_item(evidence_id)`` -- the real
    ``meridian/evidence.py::EvidenceRepository`` in production.
    """

    role = ROLE
    prompt_version = PROMPT_VERSION

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT
