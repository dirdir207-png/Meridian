"""OS-085: the Connections group headings share the hub's banner treatment.

The divergence this closes was that Connections headed its groups (Money / Evidence / Time)
with bare lilac text while the Settings hub used parchment ribbon banners. The fix shares ONE
declaration block between the two selectors rather than copying the rules, so the two cannot
drift apart later.

The guards read the SHARED BLOCK, not either selector alone: asserting only that
".m-connection-group > .m-section-label" appears somewhere would still pass if someone split the
rules into two copies, which is the drift worth preventing. Non-vacuity is covered by the last
test, which fails if the markup these rules style stops being emitted.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_CSS = ROOT / "static/css/meridian/settings.css"
CONNECTIONS_JS = ROOT / "static/js/meridian/connections.js"

BANNER_SELECTOR = ".m-settings-group-banner"
CONNECTIONS_SELECTOR = ".m-connection-group > .m-section-label"


def _selector_list_for_block_containing(needle: str) -> str:
    """Return the selector list of the declaration block that holds `needle`.

    Index-based rather than regex-based on purpose: an earlier version of this guard used a
    regex and raised "unterminated subpattern", so it failed for the wrong reason and proved
    nothing. Walking the braces cannot misfire that way.

    Note the needle is not required to be unique: `star.svg` is referenced twice inside the
    single ornament block (once for -webkit-mask and once for mask), so demanding a single
    occurrence would fail on a correct file. Uniqueness is asserted explicitly where it means
    something -- see test_the_banner_block_is_shared_with_the_connections_group_heading.
    """
    css = SETTINGS_CSS.read_text(encoding="utf-8")
    assert needle in css, f"{needle!r} must appear in settings.css"
    inside = css.index(needle)
    open_brace = css.rindex("{", 0, inside)
    previous_close = css.rindex("}", 0, open_brace)
    return css[previous_close + 1 : open_brace]


def test_the_banner_block_is_shared_with_the_connections_group_heading():
    # The treatment is shared precisely because there is ONE block carrying it; a second copy
    # is the drift this guards against.
    assert SETTINGS_CSS.read_text(encoding="utf-8").count("parchment-ticket.png") == 1, (
        "exactly one block may carry the parchment banner treatment"
    )
    selectors = _selector_list_for_block_containing("parchment-ticket.png")
    assert BANNER_SELECTOR in selectors, "the hub banner must keep the parchment treatment"
    assert CONNECTIONS_SELECTOR in selectors, (
        "the Connections group heading must be styled by the SAME block as the hub banner; "
        "if this fails the treatment was copied or dropped rather than shared"
    )


def test_the_banner_ornaments_are_shared_too():
    selectors = _selector_list_for_block_containing("star.svg")
    for selector in (
        f"{BANNER_SELECTOR}::before",
        f"{BANNER_SELECTOR}::after",
        f"{CONNECTIONS_SELECTOR}::before",
        f"{CONNECTIONS_SELECTOR}::after",
    ):
        assert selector in selectors, f"{selector} must come from the shared ornament block"


def test_connections_still_emit_the_heading_they_style():
    """Non-vacuity: the shared selector must still match markup that is really emitted."""
    js = CONNECTIONS_JS.read_text(encoding="utf-8")
    assert '"m-connection-group"' in js, "the section class must still be emitted"
    assert '"m-section-label"' in js, "the heading class must still be emitted"
