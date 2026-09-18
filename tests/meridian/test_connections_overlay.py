"""Observatory slice: connection chooser is keyboard-trapped."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_connection_chooser_traps_tab_focus():
    js = _read("static/js/meridian/connections.js")
    assert 'event.key === "Escape"' in js
    assert 'event.key !== "Tab"' in js
    assert "focusable[0]" in js
    assert "focusable[focusable.length - 1]" in js
    assert "event.preventDefault()" in js
    assert "closeSheet()" in js
