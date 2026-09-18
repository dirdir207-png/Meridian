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
