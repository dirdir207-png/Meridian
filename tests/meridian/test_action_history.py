"""Observatory slice: Settings has a read-only action history surface."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_settings_navigation_and_template_include_actions():
    nav = _read("templates/meridian/partials/settings-navigation.html")
    settings = _read("templates/meridian/settings.html")
    assert 'href="/meridian/settings?section=actions"' in nav
    assert "Actions &amp; approvals" in nav
    assert "active_settings_section == 'actions'" in settings
    assert "partials/actions.html" in settings
    assert "static/js/meridian/actions.js" in settings


def test_action_history_is_read_only_presentational():
    html = _read("templates/meridian/partials/actions.html")
    js = _read("static/js/meridian/actions.js")
    assert "read-only" in html.lower()
    assert "data-actions-refresh" in html
    assert "meridianFetch(\"/api/meridian/actions\")" in js
    # This surface must not expose approve/execute mutation controls.
    assert "actions/approve" not in js
    assert "actions/execute" not in js
    assert "actions/reject" not in js


def test_action_history_states_are_mapped():
    js = _read("static/js/meridian/actions.js")
    for state in ("proposed", "approved", "executing", "executed", "verified", "rejected", "expired", "failed"):
        assert f"{state}: " in js or f"{state}:" in js
