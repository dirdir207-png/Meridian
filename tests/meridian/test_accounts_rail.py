"""Observatory slice: the Accounts connector rail (concept 04).

Concept 04 threads its account rows on a dashed rail with a small node per row, so the
medallions read as one constellation. These guards protect the details that make it read
as a deliberate rail rather than a stray border: the line stops at the end medallions, it
is excluded from rows that carry no medallion, and each node takes its row's tint.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_connector_rail_is_scoped_to_medallion_rows_only():
    """Archived rows carry no medallion, so a node beside them would mark nothing."""
    css = _read("static/css/meridian/accounts.css")
    assert ".m-account-list .m-account-row:not(.m-account-row-archived)::before" in css
    assert ".m-account-list .m-account-row:not(.m-account-row-archived)::after" in css
    # Decorative: the rail must never intercept a click on the row.
    rail_block = css.split(".m-account-list .m-account-row:not(.m-account-row-archived)::before")[1]
    assert "pointer-events: none" in rail_block.split("}")[0]


def test_connector_rail_stops_at_the_end_medallions():
    """Left to run the full row height the line dangles past the first and last
    medallions, which reads as a broken border rather than a constellation."""
    css = _read("static/css/meridian/accounts.css")
    assert ".m-account-list .m-account-row:first-child::before" in css
    assert ".m-account-list .m-account-row:last-child::before" in css
    first = css.split(".m-account-list .m-account-row:first-child::before")[1].split("}")[0]
    last = css.split(".m-account-list .m-account-row:last-child::before")[1].split("}")[0]
    assert "top: 50%" in first
    assert "bottom: 50%" in last
    # The rail has to sit left of the medallion, which means the row needs a gutter.
    assert "padding-left: 30px" in css


def test_connector_rail_nodes_inherit_the_row_tint():
    """The node colour has to come from the row, not the medallion, or the rail would
    need its own duplicated colour table."""
    js = _read("static/js/meridian/accounts.js")
    css = _read("static/css/meridian/accounts.css")
    assert "row.dataset.tint = roleTint(role)" in js
    assert "background: var(--medallion-tint, var(--m-ink-faint))" in css
    for tint in ("lilac", "mint", "apricot", "coral", "slate"):
        assert f'.m-account-row[data-tint="{tint}"]' in css, tint
