"""Observatory slice: Accounts connection freshness uses computed data.

The Accounts workspace gets the backend's computed data freshness rather than
inferring health only from per-connection status. These source-presence tests
guard that the chip and summary read the canonical value.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_accounts_uses_computed_data_freshness():
    js = _read("static/js/meridian/accounts.js")
    assert "payload.data_freshness" in js
    assert "dataFreshness" in js
    assert "computedState" in js
    assert 'fresh: "All sources current"' in js
    assert 'stale: "Some sources are stale"' in js
    assert 'partial: "Some sources need attention"' in js


def test_accounts_freshness_chip_can_render_partial_state():
    js = _read("static/js/meridian/accounts.js")
    # A partial sync is not silently labelled Current or Stale.
    assert "partial: \"Partial\"" in js
    assert "freshness.dataset.state = computedState" in js


def test_accounts_command_uses_decorative_constellation():
    css = _read("static/css/meridian/observatory.css")
    assert ".obs-shell .m-accounts-command::before" in css
    assert "map-ornament.svg" in css
    assert "pointer-events: none" in css
