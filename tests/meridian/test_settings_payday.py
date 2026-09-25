"""Observatory slice: Settings Payday & Funding is reachable and proposal-only."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_settings_template_includes_payday_workspace_and_script():
    settings = _read("templates/meridian/settings.html")
    assert "active_settings_section == 'payday'" in settings
    assert "partials/payday-funding.html" in settings
    assert "static/js/meridian/payday.js" in settings


def test_payday_ui_writes_only_through_the_pipeline_and_says_so():
    """OS-104 rewrote this guard, and it is stronger than the one it replaced.

    The pane used to carry its own per-commitment funding editor, which created a funding
    PROPOSAL. That editor is gone (Plan owns per-bill funding, with all four modes), so the
    old assertion -- "Meridian never moves money from this screen" -- no longer described the
    surface: the one remaining write is the Crew paycheck amount, and a fully-specified owner
    edit there is ROUTED by the pipeline, which may execute it directly. What must hold now is
    that the write goes through the pipeline with explicit owner provenance, that the surface
    reports which routing happened instead of assuming success, and that an uncertain mutation
    is never repeated.
    """
    html = _read("templates/meridian/partials/payday-funding.html")
    js = _read("static/js/meridian/payday.js")

    # The pipeline, with provenance stated at the call site rather than hidden in a helper.
    assert 'fetch("/api/actions/mutate"' in js
    assert 'provenance: "owner_direct"' in js
    assert "meridianMutate" not in js
    # The outcome is reported, not assumed: direct execution and pending approval both surface.
    assert "routing_direct" in js
    assert "Pending Actions" in js
    assert "reads Crew back" in js
    # Never retried.
    for forbidden in ("retry", "setTimeout", "while ("):
        assert forbidden not in js, forbidden
    # And the surface is honest about what happens next, in the owner's words rather than ours.
    assert "reads Crew back" in js.replace("\n", " ")
    assert "proposal until you explicitly approve it" in html


def test_payday_pane_does_not_re_duplicate_per_bill_funding():
    """The owner, 2026-09-24: "Funding the way the app describes separate from payday is per
    bill and doesn't need a separate setting or section." Plan already ships the four-mode
    per-commitment editor against the same repository and the same propose route, so this pane
    must not grow a second one -- and it must say where that control lives."""
    html = _read("templates/meridian/partials/payday-funding.html")
    js = _read("static/js/meridian/payday.js")
    # The two-mode copy's controls are gone.
    for gone in ("data-payday-commitment", "data-payday-kind", "data-payday-amount",
                 "data-review-schedule"):
        assert gone not in html, gone
        assert gone not in js, gone
    # And this pane no longer proposes funding rules; Plan does, through its own editor.
    assert "funding-rules/propose" not in js
    # The funding pointer in the hub still exists, so the capability stayed reachable.
    hub = _read("meridian/settings_hub.py")
    assert '"Funding schedules"' in hub and '"Manage in Plan"' in hub


def test_payday_settings_styles_exist():
    css = _read("static/css/meridian/settings.css")
    assert ".m-payday-settings" in css
    assert ".m-payday-summary" in css
    assert ".m-payday-layout" in css


# ---------------------------------------------------------------------------
# OS-051: the learning window must be an operable control NESTED in the income
# area, not a top-level setting. Owner: "There needs to be a nested owner
# operable setting to reset the learning."
# ---------------------------------------------------------------------------


def test_the_learning_control_is_nested_inside_the_payday_area():
    html = _read("templates/meridian/partials/payday-funding.html")
    # Inside the Payday & Funding partial, which is the income area...
    assert "data-learning-floor" in html
    # ...and never promoted to a page-level section of its own.
    settings = _read("templates/meridian/settings.html")
    assert "data-learning-floor" not in settings


def test_the_learning_control_is_labelled_and_operable():
    """A date the owner picks, plus a way to go back to the full history. Both need
    accessible names, and the result must be announced rather than only coloured."""
    html = _read("templates/meridian/partials/payday-funding.html")

    assert 'data-learning-floor-input' in html
    assert 'type="date"' in html
    assert "<label" in html
    assert "Include all history" in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html


def test_the_learning_control_explains_it_deletes_nothing():
    """The owner's constraint: "a reset must NOT delete financial records, only
    change which observations Meridian aggregates". The surface must say so."""
    html = _read("templates/meridian/partials/payday-funding.html").lower()
    assert "no records are deleted" in html or "deletes no" in html


def test_the_learning_control_writes_only_a_local_setting():
    """It is a Meridian-local setting, so it must not ride the proposal pipeline (which
    exists for financial proposals) nor the Crew mutation helper."""
    js = _read("static/js/meridian/payday.js")

    assert "/api/meridian/settings/payday/learning-floor" in js
    assert "meridianMutate" not in js
    # The floor is a local setting, not a financial proposal, so it is posted with plain
    # fetch rather than through the proposal channel.
    assert 'fetch("/api/meridian/settings/payday/learning-floor"' in js
