"""The desktop Settings navigation must be sized to hold its own content (OS-081).

The desktop treatment is SPECIFIED, not invented. ``BUILD_HANDOFF.md`` line 24: *"At 1440px:
existing rail, flexible ledger, 320-360px inspector; Virgil opens there without adding a fifth
workspace. Settings uses grouped navigation left and selected details right."*

The grouped navigation is the hub's rows and group banners, and they were sitting in a **210px**
column, where every label and subtitle wrapped onto four or five lines while the details column sat
almost empty. The correction sizes the navigation column to what it contains.

**What this pins and what it does not.** It pins the WIDTH, which is the defect: the column must be
wide enough for the rows and must not have gone back to 210px. It does NOT verify the appearance.
The capture matrix in the build handoff requires BOTH THEMES at 390x844, 420x912, 430x932 and
1440x900 plus tablet, with separate checks for 200% zoom, horizontal overflow and dock/composer
collision -- none of which a stylesheet assertion can stand in for.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "static/css/meridian/settings.css"


def _desktop_block() -> str:
    """The ``min-width: 901px`` block, which is where the desktop grid is decided."""
    css = CSS.read_text(encoding="utf-8")
    match = re.search(r"@media \(min-width: 901px\) \{(.*?)\n\}", css, re.S)
    assert match, "the >=901px desktop block is gone from settings.css"
    return match.group(1)


def test_the_desktop_navigation_column_is_wide_enough_to_hold_its_rows():
    block = _desktop_block()
    match = re.search(r"grid-template-columns:\s*([^;]+);", block)
    assert match, (
        "the desktop block no longer sets the shell grid, so the 210px column stands unreplaced"
    )
    columns = match.group(1)
    assert "210px" not in columns, (
        "the grouped navigation is back in a 210px column, which wraps every label and subtitle "
        f"onto four or five lines: {columns}"
    )
    widths = [int(n) for n in re.findall(r"(\d+)px", columns)]
    assert max(widths) >= 300, (
        f"no column is wide enough for the grouped navigation to hold its rows: {columns}"
    )


def test_the_block_under_test_really_is_the_shell_grid():
    """Guards the guard: an emptied or relocated block would make the check above vacuous."""
    css = CSS.read_text(encoding="utf-8")
    assert "grid-template-areas" in css, "the settings shell is no longer a grid"
    assert "settings-nav" in css, "the navigation column no longer exists in the shell"
    assert "m-settings-row" in css, "the grouped navigation rows no longer exist"
