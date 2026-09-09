"""Observatory slice: Accounts rows can open filtered Activity."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_accounts_rows_have_activity_buttons():
    js = _read("static/js/meridian/accounts.js")
    css = _read("static/css/meridian/accounts.css")
    assert "m-account-activity" in js
    assert "window.MeridianActivity.openAccount" in js
    assert ".m-account-activity" in css


def test_activity_exposes_open_account_filter():
    js = _read("static/js/meridian/activity.js")
    assert "function openAccount" in js
    assert "openAccount" in js.split("window.MeridianActivity = ")[1]
    assert "data-account-filter" in js
