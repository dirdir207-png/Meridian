"""The Settings page must scroll on a phone.

Owner report: "I went to check mine in Meridian, which should coincide with the paycheck in
Crew, but I am unable to scroll on the settings page." That blocked the funding-cadence setup
entirely, so it is an access bug rather than a cosmetic one.

Measured before the fix, at 430x932: the shell resolved to exactly the viewport height with
`overflow-y: hidden` and three grid rows summing to exactly that height (61 + 784 + 87), while
`.m-settings-main` held 873px of content in a 784px box with `overflow: visible`. The overflow
was clipped by the shell, the column could not scroll because it was not a scroll container,
and the document could not scroll because nothing exceeded it. Both the page and the column
were dead ends.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_CSS = ROOT / "static/css/meridian/settings.css"


def _mobile_block(css: str, selector: str) -> str:
    """The phone block that actually defines `selector`.

    This used to take the FIRST `@media (max-width: 900px)` block in the file, which silently
    assumed the shell's was the only one. OS-081 added a second phone-scoped block for the
    Settings top bar and that assumption broke: the helper returned the wrong block and the
    failure arrived as a parse error rather than as a signal about the layout. A helper that
    asserts less than it means is the same class of defect as a guard that encodes a judgement
    -- it fails confusingly at the wrong moment -- so it now finds the block that defines what
    the caller asked for, and says so when there is none.
    """
    for chunk in css.split("@media (max-width: 900px) {")[1:]:
        block = chunk.split("\n}\n", 1)[0]
        if selector in block:
            return block
    raise AssertionError(f"no phone block defines {selector}")


def _rule(block: str, selector: str) -> str:
    return block.split(selector + " {", 1)[1].split("}", 1)[0]


def test_the_settings_content_column_is_the_scroller_on_a_phone():
    block = _mobile_block(SETTINGS_CSS.read_text(encoding="utf-8"), "  .m-settings-main")

    main = _rule(block, "  .m-settings-main")
    assert "overflow-y: auto;" in main
    # A grid item's automatic minimum size would refuse to shrink, so the row could not be
    # bounded and the column would never overflow -- the property that actually makes this work.
    assert "min-height: 0;" in main

    shell = _rule(block, "  .m-settings-shell")
    # `1fr` alone refuses to shrink below its content, which is what pushed the content past
    # the shell's clip in the first place.
    #
    # RESTATED 2026-09-21 for the Settings hub: the row count went from three to four because
    # the nav is now a WIDE row on phone (it used to be `display: none`, which left Settings
    # with no way to reach any section on phone at all). The property that matters is
    # unchanged -- the CONTENT row is still `minmax(0, 1fr)`, so it can shrink and scroll --
    # but `main` is no longer the third row, so a literal row list stopped describing the
    # layout. This checks the row that belongs to `main` instead of its position.
    assert 'grid-template-areas: "topbar" "settings-nav" "main" "dock";' in shell
    rows = re.search(r"grid-template-rows:\s*([^;]+);", shell)
    assert rows, "the mobile shell must declare its rows explicitly"
    # Split on top-level whitespace only: a naive `.split()` breaks `minmax(0, 1fr)` apart.
    declared = [t.replace(" ", "") for t in re.findall(r"minmax\([^)]*\)|\S+", rows.group(1))]
    assert len(declared) == 4, rows.group(1)
    # Row 3 belongs to `main`: it must be the shrinkable one.
    assert declared[2] == "minmax(0,1fr)", rows.group(1)
    # `auto` for the nav and the dock, so neither collapses to zero height.
    assert declared[1] == "auto" and declared[3] == "auto", rows.group(1)


def test_the_desktop_settings_layout_is_untouched_by_that_fix():
    """The fix is scoped to the phone block; the four-column desktop grid keeps its own
    behaviour and must not acquire a scroll container of its own."""
    css = SETTINGS_CSS.read_text(encoding="utf-8")
    desktop = css.split(".m-settings-main {", 1)[1].split("}", 1)[0]

    assert "overflow" not in desktop
    assert "min-height" not in desktop
