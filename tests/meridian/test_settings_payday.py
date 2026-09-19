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


def test_payday_ui_is_explicitly_an_approval_gated_proposal():
    html = _read("templates/meridian/partials/payday-funding.html")
    js = _read("static/js/meridian/payday.js")
    assert "Meridian never moves money from this screen" in html
    assert "proposal" in html.lower()
    # The payday editor creates a funding proposal; it never calls the direct
    # mutation helper used for owner-directed Crew writes.
    assert "meridianPropose" in js
    assert "meridianMutate" not in js


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
