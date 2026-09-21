"""Connections owns its editor vocabulary instead of borrowing Plan's (OS-085).

Found by comparing the vocabulary rather than hunting for dead CSS: ``connections.js`` emitted the
``m-editor-*`` classes, which are defined **only** in ``plan.css`` and nowhere else. So the
Connections editor was styled by Plan's stylesheet, and the retool this task exists for -- *"match
the style of the rest of the app"* -- could not be done by editing those rules without **silently
moving Plan**, a live surface with its own concept fidelity.

The correction gives Connections its own ``m-connection-editor-*`` rules in ``settings.css`` carrying
the **same declarations**, so the appearance is unchanged and only the coupling moves. These guards
therefore assert two things at once: that Connections no longer borrows, and that **Plan did not
move** -- because a decoupling that quietly restyled Plan would be worse than the coupling.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONNECTIONS_JS = ROOT / "static/js/meridian/connections.js"
SETTINGS_CSS = ROOT / "static/css/meridian/settings.css"
PLAN_JS = ROOT / "static/js/meridian/plan.js"
PLAN_CSS = ROOT / "static/css/meridian/plan.css"

OWNED = ("title", "preview", "actions", "note")


def test_connections_no_longer_emits_plans_editor_classes():
    js = CONNECTIONS_JS.read_text(encoding="utf-8")
    assert "m-connection-editor-" in js, "the slice is empty, so the assertion below is vacuous"
    assert "m-editor-" not in js.replace("m-connection-editor-", ""), (
        "connections.js is emitting a Plan-owned m-editor-* class again, so editing that rule to "
        "retool Connections would move Plan"
    )


def test_every_owned_class_is_defined_and_emitted():
    js = CONNECTIONS_JS.read_text(encoding="utf-8")
    css = SETTINGS_CSS.read_text(encoding="utf-8")
    for name in OWNED:
        cls = f"m-connection-editor-{name}"
        assert cls in js, f"{cls} is defined in CSS but never emitted"
        assert re.search(rf"\.{cls}\b", css), f"{cls} is emitted but has no rule in settings.css"


def test_plan_did_not_move():
    """The decoupling must be a no-op for Plan: its rules and its emitters are untouched."""
    plan_css = PLAN_CSS.read_text(encoding="utf-8")
    for name in OWNED:
        assert f".m-editor-{name} {{" in plan_css, (
            f"plan.css lost .m-editor-{name}, so Plan was restyled by a change that was supposed "
            f"only to decouple Connections"
        )
    assert "m-editor-" in PLAN_JS.read_text(encoding="utf-8"), (
        "plan.js lost its editor classes, which means Plan moved"
    )


def test_the_two_vocabularies_are_disjoint():
    """No stylesheet may define both, or the ownership question is reopened."""
    settings = SETTINGS_CSS.read_text(encoding="utf-8")
    assert not re.search(r"\.m-editor-(title|preview|actions|note)\b", settings), (
        "settings.css has taken over a Plan-owned class instead of owning its own"
    )
