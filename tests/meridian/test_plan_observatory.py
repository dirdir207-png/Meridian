"""Observatory slice: read-only Plan scenario preview.

These source-presence tests protect the critical safety boundary: the new
scenario preview must not be wired to a mutation path. The API-level behavior
is covered in test_api.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_plan_scenario_preview_is_explicitly_read_only_in_template():
    html = _read("templates/meridian/partials/plan.html")
    assert 'data-plan-scenario' in html
    assert "Preview — no changes applied" in html
    assert "data-plan-scenario-reset" in html
    assert "/api/meridian/plan/scenario" not in html
    # Apply-to-Crew is not present in this slice; a safe preview can be
    # discarded without creating a proposal.
    assert "data-plan-scenario-apply" not in html


def test_plan_scenario_preview_uses_read_only_api_and_not_mutate():
    js = _read("static/js/meridian/plan.js")
    assert "/api/meridian/plan/scenario" in js
    assert 'method: "POST"' in js
    assert "No live values change while you preview" in _read(
        "templates/meridian/partials/plan.html"
    )
    # The scenario code must not be accidentally routed through the mutation
    # helper used by the Crew write forms.
    scenario_slice = js[js.index("function runScenarioPreview"):js.index("function setupScenarioPreview")]
    assert "meridianMutate" not in scenario_slice
    assert "meridianPropose" not in scenario_slice
