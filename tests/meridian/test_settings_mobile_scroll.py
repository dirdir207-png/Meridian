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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_CSS = ROOT / "static/css/meridian/settings.css"


def _mobile_block(css: str) -> str:
    return css.split("@media (max-width: 900px) {", 1)[1].split("\n}\n", 1)[0]


def _rule(block: str, selector: str) -> str:
    return block.split(selector + " {", 1)[1].split("}", 1)[0]


def test_the_settings_content_column_is_the_scroller_on_a_phone():
    block = _mobile_block(SETTINGS_CSS.read_text(encoding="utf-8"))

    main = _rule(block, "  .m-settings-main")
    assert "overflow-y: auto;" in main
    # A grid item's automatic minimum size would refuse to shrink, so the row could not be
    # bounded and the column would never overflow -- the property that actually makes this work.
    assert "min-height: 0;" in main

    shell = _rule(block, "  .m-settings-shell")
    # `1fr` alone refuses to shrink below its content, which is what pushed the content past
    # the shell's clip in the first place.
    assert "grid-template-rows: auto minmax(0, 1fr) auto;" in shell


def test_the_desktop_settings_layout_is_untouched_by_that_fix():
    """The fix is scoped to the phone block; the four-column desktop grid keeps its own
    behaviour and must not acquire a scroll container of its own."""
    css = SETTINGS_CSS.read_text(encoding="utf-8")
    desktop = css.split(".m-settings-main {", 1)[1].split("}", 1)[0]

    assert "overflow" not in desktop
    assert "min-height" not in desktop
