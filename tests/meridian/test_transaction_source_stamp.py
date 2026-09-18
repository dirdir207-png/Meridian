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


def test_transaction_inspector_has_observation_record_kicker():
    template = _read("templates/meridian/partials/transaction-inspector.html")
    css = _read("static/css/meridian/inspector.css")
    assert "m-inspector-kicker" in template
    assert "Observation record" in template
    assert ".m-inspector-kicker" in css


def test_transaction_inspector_uses_signed_amount_and_signal_classes():
    js = _read("static/js/meridian/transaction-inspector.js")
    css = _read("static/css/meridian/inspector.css")
    assert "signedAmount(transaction.amount, transaction.currency)" in js
    assert 'classList.toggle("is-income", transaction.amount >= 0)' in js
    assert 'classList.toggle("is-spend", transaction.amount < 0)' in js
    assert ".m-fact.is-income dd" in css
    assert ".m-fact.is-spend dd" in css
