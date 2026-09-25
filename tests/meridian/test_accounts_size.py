"""OS-103: the owner's four-named Accounts aesthetic, measured against concept 04.

Concept 04 (`design/observatory-drafts-2026-09-08/04-accounts.png`) is 853x1844 drawn for a
420-wide phone, i.e. 0.4924 concept px to CSS px. Read with PIL on 2026-09-24 rather than by eye:

    ticket painted face   379.6 x 183.2 CSS   (x 48..818 of 853 by median first/last parchment;
                                               183.2 down the ticket's centre column)
    engraving             ~132 x 132 CSS      (ink bbox of the drawn building)
    figure                ~40px serif, ~182 CSS of ink -- 48% of the face width
    medallion ring        ~52 CSS outer diameter, ~7 CSS ring band
    cord                  bowed ~11-12 CSS left of the nodes, tinted ALONG its length
                          (lilac -> mint -> apricot), nodes ~7 CSS across

The app at 56390c9, measured the same way in the isolated synthetic preview at 420x912 DPR 3:
ticket box 388x164 with a painted face of 357.3 x 134.3 (73% of the concept's HEIGHT), an
engraving clamped to a 92px box, a 32px figure, a 46px medallion, and one cord path drawn in
rgba(238,228,207,0.26).

After this slice, measured the same way: painted face 356.7 x 179.7 CSS -- 98.1% of the concept's
height -- with the engraving at a 136px box and the owner's own nine-character figure at ~186 CSS
of ink against the concept's ~182. The remaining 6% of WIDTH is not a layout miss and cannot be
closed by layout: the ticket's box already IS the full 388px content column, and the supplied
nine-slice carries its own transparent margins plus scalloped-edge shading, so the painted face
sits ~31px inside the box on each side. Matching the concept's 379.6 would need a ~5px frame,
which is not the frame the kit draws.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def _block(css, opener):
    return css.split(opener)[1].split("}")[0]


def test_the_ticket_interior_is_sized_for_the_concepts_height():
    """The ticket's box was already the full content column, so 'larger ticket' is all interior:
    a bigger engraving and the vertical padding that carries the face to the concept's height.
    The arithmetic is pinned rather than the outcome (a browser measures the outcome): with a
    136px engraving, `padding: 12px 4px` and the 20px nine-slice border, the box is
    136 + 24 + 40 = 200px, which paints ~185px of face against the concept's 183.2."""
    css = _read("static/css/meridian/accounts.css")
    ticket = _block(css, "\n.m-accounts-summary .m-accounts-ticket {")
    assert "padding: 12px 4px" in ticket
    assert "border: 20px solid transparent" in ticket
    assert "80 fill / 20px round" in ticket, "the kit's nine-slice must survive the resize"

    art = _block(css, "\n.m-accounts-ticket-art {")
    assert "width: clamp(124px, 40%, 200px)" in art
    # The engraving yields before the figure does: a money figure has no break opportunity, so a
    # figure that does not fit does not wrap -- it spills past the ticket's edge.
    assert "flex: 0 1 auto" in art
    assert "min-width: 88px" in art
    assert "aspect-ratio: 1" in art


def test_the_ticket_figure_takes_the_concepts_scale_and_cannot_spill():
    css = _read("static/css/meridian/accounts.css")
    figure = _block(css, "\n.m-accounts-summary .m-accounts-ticket .m-accounts-figure {")
    assert "font-size: clamp(2rem, 9.5vw, 3.4rem)" in figure
    # 9.5vw is 37.1px at the 390px `mobile-small` viewport, where the engraving takes its 124px
    # floor, so both governed phone widths are covered by the same two terms. `nowrap` is the
    # other half of that: the figure may not be the element that yields.
    assert "white-space: nowrap" in figure


def test_the_rows_sit_on_the_page_not_in_a_card():
    """Concept 04 draws the rows directly on the night canvas. The sheet is now purely the
    positioned box the connector layer hangs off, and the width authority for the rows."""
    css = _read("static/css/meridian/accounts.css")
    sheet = _block(css, "\n.m-account-list-sheet {")
    assert "width: 100%" in sheet
    for gone in ("border:", "border-radius", "background:", "box-shadow", "padding"):
        assert gone not in sheet, f"the sheet kept its {gone} chrome"
    # The connector layer measures against this box, so it must stay positioned.
    assert ".m-account-list-sheet {\n  position: relative;" in css
    # And the narrow-viewport padding override that only existed for the card is gone.
    assert ".m-account-list-sheet {\n    padding:" not in css


def test_parchment_re_inks_the_rules_the_card_used_to_carry():
    """While the rows sat on a `--m-surface` card they inherited the light theme's indigo box and
    every accent was drawn against indigo. On the parchment page the concept's brass reads
    2.03:1, so the rules are re-inked and the two accents the box was carrying are restored."""
    css = _read("static/css/meridian/accounts.css")
    observatory = _read("static/css/meridian/observatory.css")
    assert (
        'html[data-theme="light"] .obs-shell .m-account-row {\n  border-bottom-color: #8a6a33;'
        in css
    )
    assert 'html[data-theme="light"] .obs-shell .m-account-row::before {\n  background: #8a6a33;' in css
    assert (
        'html[data-theme="light"] .obs-shell .m-account-list {\n'
        "  border-top-color: rgba(32, 38, 59, 0.3);" in css
    )
    # The medallion disc: `--m-surface` is the dark disc in the dark theme and #ffffff in the
    # light one, where brass on white is 1.90:1. The concept's own disc is the night indigo.
    assert (
        'html[data-theme="light"] .obs-shell .m-account-icon {\n  background: var(--obs-bg);' in css
    )
    # The sheet leaves the theme's box enumeration, or the fill it no longer declares would be
    # painted back on by the box rule. Comments are stripped first: the enumeration carries the
    # note explaining WHY the sheet left, and a guard that reads its own explanation as a
    # selector would forbid the record it depends on.
    import re

    box_list = re.sub(
        r"/\*.*?\*/", "", observatory.split('html[data-theme="light"] .obs-shell .m-ledger-card,')[1].split("{")[0],
        flags=re.S,
    )
    assert ".m-account-list-sheet" not in box_list


def test_the_dark_theme_rules_the_concept_draws_are_untouched():
    """The concept draws the night canvas only, so nothing above may degrade the dark theme: the
    brass separator and the dark disc stay exactly as the concept and the 2026-09-23 owner
    direction have them."""
    css = _read("static/css/meridian/accounts.css")
    assert "border-bottom: 1px dotted var(--obs-brass, #c6aa71)" in css
    light_overrides = css.split('html[data-theme="light"] .obs-shell .m-account-row {')[1]
    assert "#c6aa71" not in light_overrides.split("}")[0], "the dark rule must not be re-inked"
