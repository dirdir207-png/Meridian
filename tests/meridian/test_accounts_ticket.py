"""Observatory slice: the Accounts parchment summary panel (concept 04).

Kit README: `parchment-ticket.png` is for an "account summary" and
the Accounts page now uses a dedicated archive-building cutout rather than reusing the
Today dial building. The kit also states
the contrast rule this panel has to obey: "On parchment, use dark navy text; do not
carry pale lilac/mint text over without checking contrast."
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_accounts_command_copy_matches_the_governing_concept():
    html = (ROOT / "templates/meridian/partials/accounts.html").read_text()
    assert '<h2 class="m-editorial-headline">Accounts</h2>' in html
    assert "Your financial constellation." in html


def test_accounts_places_account_constellation_before_secondary_liabilities():
    html = (ROOT / "templates/meridian/partials/accounts.html").read_text()
    assert html.index("data-accounts-groups") < html.index("data-liabilities")


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_accounts_summary_is_the_kit_parchment_panel():
    html = _read("templates/meridian/partials/accounts.html")
    css = _read("static/css/meridian/accounts.css")
    assert "m-accounts-ticket" in html
    assert 'class="m-accounts-ticket-art obs-art" aria-hidden="true"' in html
    # The kit's own assets, the same measured nine-slice the other tickets use.
    assert "kit-2026-09-16/parchment-ticket.png" in css
    assert "80 fill / 20px round" in css
    assert "observatory/accounts-ticket-building.png" in css
    assert (ROOT / "static/img/meridian/observatory/accounts-ticket-building.png").is_file()


def test_accounts_ticket_keeps_every_figure_in_html_and_drops_nothing():
    """Restyling the summary must not quietly remove a figure from the page."""
    html = _read("templates/meridian/partials/accounts.html")
    for hook in (
        "data-available-cash",
        "data-available-note",
        "data-liabilities",
        "data-liabilities-note",
    ):
        assert hook in html, hook


def test_accounts_ticket_text_obeys_the_kit_parchment_contrast_rule():
    """The label override needs three classes on purpose: `.m-accounts-net-card
    .m-section-label` sets the muted colour at the same (0,2,0) weight and appears later
    in the file, so a two-class selector loses and the label renders pale on parchment."""
    css = _read("static/css/meridian/accounts.css")
    assert ".m-accounts-summary .m-accounts-ticket .m-section-label" in css
    assert "color: #7a5a2e;" in css
    # Dark ink on the parchment face, and the pale signal colouring suppressed: the
    # figure is a cash total, not a warning.
    assert ".m-accounts-ticket .m-accounts-figure[data-signal]" in css
    assert "color: #20263b;" in css


def test_accounts_ticket_takes_the_concepts_angle_notches_and_dotted_inset():
    """Concept 04 sets the whole ticket at an angle, punches a semicircular notch out of
    each side at mid-height, and insets a fine dotted border from the edge. Finding 4
    recorded ours as "axis-aligned, square-cornered and plain".

    The angle is measured, not guessed: two independent features inside the concept agree
    -- the ticket's own top edge (-3.7deg over 656 columns) and the brass rule under the
    amount (-3.21deg over 104 columns). The rule is the cleaner, purely internal feature,
    so the panel takes -3.2deg. The text tilts with it, because that is what the concept
    draws."""
    css = _read("static/css/meridian/accounts.css")
    ticket = css.split(".m-accounts-summary .m-accounts-ticket {", 1)[1].split("}", 1)[0]
    assert "transform: rotate(-3.2deg)" in ticket
    # The kit's nine-slice must survive: the tilt is added to that panel, not a replacement.
    assert "border-image:" in ticket
    assert "parchment-ticket.png" in ticket
    # A dotted border inset from the edge, done with an outline so it needs no third
    # pseudo-element and stays out of the accessibility tree.
    assert "outline: 1px dotted var(--obs-brass)" in ticket
    assert "outline-offset: -14px" in ticket

    # The punched notches: one per side, at mid-height, in the page background colour so
    # they read as bites rather than discs. Both are decorative and inert. They share one
    # rule, with only the side-specific offset split out below it.
    shared = css.split(
        ".m-accounts-summary .m-accounts-ticket::before,\n.m-accounts-summary .m-accounts-ticket::after {",
        1,
    )[1].split("}", 1)[0]
    assert "border-radius: 50%" in shared
    # `--m-canvas`, not `--obs-bg`. The comment above has always said "the page background
    # colour", but `--obs-bg` is the page colour of the MIDNIGHT palette only, so in the light
    # theme this rule was painting dark indigo bites into a parchment ticket -- the same "pasted
    # on" artifact as the dark-mode outline, in the other theme. `--m-canvas` is the page colour
    # in both themes, which is what the rule was always trying to say. The assertion moved with
    # the code on 2026-09-23 rather than the code moving back to satisfy it.
    assert "background: var(--m-canvas)" in shared
    assert "pointer-events: none" in shared
    assert "top: 50%" in shared
    assert "left: -38px" in css
    assert "right: -38px" in css
    # The notch is deliberately larger than the concept's own ~25px, because the kit's
    # ticket edge already carries ~10px scallops that a concept-sized bite vanishes into.
    assert "width: 36px" in shared
    assert "height: 36px" in shared
    assert "margin-top: -18px" in shared
