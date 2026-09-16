"""Observatory slice: the Accounts closing parchment strip (concept 04).

Concept 04 ends the page with a compact parchment strip for tracked items. The kit names
`parchment-ticket.png` for exactly that shape of surface, and separately scopes
`activity-telescope.png` to Activity with only sparing reuse in Settings -- so these
guards protect both the reuse and the restraint.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_assets_strip_uses_the_kit_ticket_nine_slice():
    css = _read("static/css/meridian/accounts.css")
    block = css.split(".memory-management {")[1].split("}")[0]
    assert "parchment-ticket.png" in block
    assert "80 fill / 20px round" in block
    # The ticket replaces the plain block rather than sitting under it.
    assert "border-radius: 0" in block
    assert "background: none" in block


def test_assets_strip_does_not_borrow_the_activity_telescope():
    """The kit scopes the telescope to Activity with sparing reuse in Settings. Putting
    it on an Accounts strip because the concept happens to draw an engraving there would
    be an unsanctioned reuse, so the absence is asserted rather than left to chance."""
    css = _read("static/css/meridian/accounts.css")
    assert "activity-telescope.png" not in css
    assert "observatory-landscape.png" in css  # the vignette the kit DOES scope here


def test_assets_strip_label_wins_on_specificity():
    """`.obs-shell .m-section-label` sets the label colour at (0,2,0), so a two-class
    selector ties with it and the winner falls to stylesheet order -- the exact failure
    that put a pale label on the summary panel in batch 1."""
    css = _read("static/css/meridian/accounts.css")
    assert ".obs-shell .memory-management .m-section-label" in css
    assert "color: #7a5a2e;" in css
    assert ".obs-shell .memory-management .m-section-copy" in css
