"""Observatory slice: Settings has a read-only action history surface."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_settings_navigation_and_template_include_actions():
    """Restated 2026-09-21 for the Settings hub.

    The flat nav's row label WAS "Actions & approvals". The 09-18 concept's grouped hub
    names the same route "Approval boundaries" (subtitle "Review what Virgil may do"), so the
    label and the href now live in one place: meridian/settings_hub.py. Restated rather than
    deleted so the rename is visible.
    """
    from meridian.settings_hub import settings_hub_rows

    row = next(r for r in settings_hub_rows() if r["key"] == "approval-boundaries")
    assert row["href"] == "/meridian/settings?section=actions"
    assert row["label"] == "Approval boundaries"
    assert row["section"] == "actions"

    settings = _read("templates/meridian/settings.html")
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
