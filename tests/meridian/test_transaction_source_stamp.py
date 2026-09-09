"""Observatory slice: transaction detail shows an observation source stamp."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_transaction_inspector_has_source_stamp():
    template = _read("templates/meridian/partials/transaction-inspector.html")
    js = _read("static/js/meridian/transaction-inspector.js")
    css = _read("static/css/meridian/inspector.css")
    assert "m-inspector-source-stamp" in template
    assert "data-inspector-observed" in template
    assert "formatTimestamp" in js
    assert '"[data-inspector-observed]"' in js
    assert ".m-inspector-source-stamp" in css
