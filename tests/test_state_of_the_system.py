"""The generated state document must be current, and must still admit what it cannot check.

Two assertions, both about drift rather than behaviour:

1. Regenerating the document today reproduces the committed bytes exactly. If a code input changed and the
   document was not regenerated, this fails — which is the whole point: a hand-maintained summary would
   simply have been wrong.
2. The "what this document does NOT check" section still exists and still lists its items. Deleting the
   honest half is the failure mode this guard is for; a coverage document that silently drops its limits is
   worse than none.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "state_of_the_system.py"
DOC = ROOT / "docs" / "project" / "STATE_OF_THE_SYSTEM.md"


def _generator():
    spec = importlib.util.spec_from_file_location("state_of_the_system", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["state_of_the_system"] = module
    spec.loader.exec_module(module)
    return module


def test_the_committed_state_document_is_current() -> None:
    module = _generator()
    assert DOC.exists(), (
        "docs/project/STATE_OF_THE_SYSTEM.md is missing. Generate it with "
        "`python scripts/state_of_the_system.py`."
    )
    assert module.render() == DOC.read_text(), (
        "docs/project/STATE_OF_THE_SYSTEM.md is STALE: a code input changed and the document was not "
        "regenerated. Run `python scripts/state_of_the_system.py` and commit the result."
    )


def test_the_document_still_states_what_it_does_not_check() -> None:
    text = DOC.read_text()
    marker = "## What this document does NOT check"
    assert marker in text, "the honesty section was removed"
    body = text.split(marker, 1)[1]
    bullets = [line for line in body.splitlines() if line.startswith("* ")]
    assert len(bullets) >= 6, (
        f"the honesty section shrank to {len(bullets)} items; the recorded failure classes it names "
        "(semantics, unread provider state, uncalibrated guards, pre-recording history, other lanes and "
        "Documents, live data quality, unmentioned things, intent) must not be quietly dropped"
    )


def test_the_ungoverned_write_count_is_a_number_not_a_vibe() -> None:
    """The denominator OS-119 depends on: exactly the routes the ratchet declares."""
    module = _generator()
    declared = module._declared_ungoverned()
    assert declared, "the ratchet declares no ungoverned routes; the denominator vanished"
    text = DOC.read_text()
    assert (
        f"| routes DECLARED to reach a raw Crew mutation (the declaration calls them POST) | {len(declared)} |"
        in text
    ), (
        "the generated document's declared-route count disagrees with the ratchet's declaration, or the row was "
        "relabelled away from 'declared' — the independent lane measured that one of these routes is GET-only at "
        "runtime, so the row must say DECLARED and not POST"
    )
