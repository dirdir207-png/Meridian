"""Observatory slice: the Accounts closing parchment strip (concept 04).

Concept 04 ends the page with a compact parchment strip for tracked items. The kit names
`parchment-ticket.png` for exactly that shape of surface, and separately scopes
`activity-telescope.png` to Activity with only sparing reuse in Settings -- so these
guards protect both the reuse and the restraint.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_assets_strip_uses_the_kit_ticket_nine_slice():
    """The strip wears the kit's ticket art -- on the ROWS, not on the section.

    RETARGETED 2026-09-25. This asserted the nine-slice on `.memory-management` itself, i.e. one tall
    plate. The owner then asked for "one ticket per item", and that change also fixed a real defect: the
    kit's ticket is drawn for a one-row ticket, so a 1000px plate made the browser tile its interior and
    drew seams through the row text. The property is unchanged -- the strip is the kit's ticket, not a
    plain block -- so this asserts it on the rule that now carries it, and asserts the section is not a
    plate again. The `fill` keyword is deliberately not required: filling a long surface is what drew the
    seams, and a row-sized ticket does not need it.
    """
    css = _read("static/css/meridian/accounts.css")
    # Comments first: these rules carry long explanations that NAME the art when describing what they
    # used to do, and a guard that reads prose fails on a correct stylesheet.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    section = css.split(".memory-management {")[1].split("}")[0]
    assert "parchment-ticket.png" not in section, "the section must not be one tall plate again"
    frames = [block for block in re.findall(
        r"\.obs-shell \.memory-management \.memory-item,\s*\n"
        r"\.obs-shell \.memory-management \.pending-memory-proposal \{(.*?)\n\}", css, re.S)
        if "border-image" in block]
    assert frames, "the kit ticket must be worn by the rows"
    block = frames[0]
    assert "parchment-ticket.png" in block
    assert "80 / 20px round" in block, "the frame keeps the measured nine-slice"
    # The ticket replaces the plain block rather than sitting under it.
    assert "border-radius: 0" in block
    assert "background-image" in block, "the row's field is the tileable paper"


def test_assets_strip_does_not_borrow_the_activity_telescope():
    """The kit scopes the telescope to Activity with only sparing reuse in Settings, so
    its absence from Accounts is asserted rather than left to chance.

    The second assertion changed authority on 2026-09-18: the kit provisionally scoped
    `observatory-landscape.png` (the Today dial's hilltop observatory) to the "Accounts
    decorative vignette", but the owner supplied a dedicated Accounts cutout --
    `accounts-ticket-building.png`, a colonnaded domed archive building with scrolls and
    an open ledger. Reusing the Today dial's building on Accounts was the same class of
    unsanctioned reuse this test exists to prevent, so the dedicated asset is now the one
    asserted: Accounts carries its own art, not Today's and not Activity's."""
    css = _read("static/css/meridian/accounts.css")
    assert "activity-telescope.png" not in css
    assert "observatory-landscape.png" not in css  # Today's building stays on Today
    assert "accounts-ticket-building.png" in css  # the dedicated Accounts asset
    assert (ROOT / "static/img/meridian/observatory/accounts-ticket-building.png").is_file()


def test_assets_strip_label_wins_on_specificity():
    """The heading keeps a three-class selector, so it cannot lose to `.obs-shell .m-section-label`.

    RETARGETED 2026-09-25. This also asserted the label's PAPER ink (`color: #7a5a2e`), which was right
    while the section itself was parchment. The owner then moved the paper down to the rows ("separate the
    tickets per items"), so the heading prints on the page and must take the page's ink -- the paper rule
    would now paint brown on navy. The specificity property is what this test is for, and it survives:
    three classes beat the two-class base rule by specificity rather than by source order.
    """
    css = _read("static/css/meridian/accounts.css")
    assert ".obs-shell .memory-management .m-section-label" in css
    block = css.split(".obs-shell .memory-management .m-section-label {")[1].split("}")[0]
    assert "font-family: var(--m-font-serif)" in block, "the heading's own type survives the move"
    assert "color:" not in block, (
        "the heading sits on the page now: a paper ink here would print brown on navy"
    )
