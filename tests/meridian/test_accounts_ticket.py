"""Observatory slice: the Accounts parchment summary panel (concept 04).

Kit README: `parchment-ticket.png` is for an "account summary" and
`observatory-landscape.png` for the "Accounts decorative vignette". The kit also states
the contrast rule this panel has to obey: "On parchment, use dark navy text; do not
carry pale lilac/mint text over without checking contrast."
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
    assert "kit-2026-09-16/observatory-landscape.png" in css


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
