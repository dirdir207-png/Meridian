"""CSS integrity guards for the Settings stylesheet.

**Why this file exists.** A textual test is not a CSS test. The scroll fix for the owner's
"I am unable to scroll on the settings page" report was guarded by a test that split the
stylesheet on the string ``"@media (max-width: 900px) {"`` and looked for declarations in the
text that followed. When a later edit left the block's closing brace in the wrong place, the
mobile rules ended up at TOP LEVEL -- applying at every width, and orphaning the rules after
them -- while the guard still passed, because the text still *looked* nested.

The real damage measured in a browser at 420px: the connections row resolved to the desktop
five-column grid, overflowed to 660px inside a 420px viewport, and clipped its own text. No
text-based assertion noticed.

So these checks parse the stylesheet's STRUCTURE -- which at-rule encloses which declaration --
and they check every stylesheet in the directory, because a stray brace is not specific to one
surface. They are cheap, and they fail on exactly the class of mistake that reads as fine.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CSS_DIR = ROOT / "static/css/meridian"
SETTINGS_CSS = CSS_DIR / "settings.css"


def _strip_comments(text: str) -> str:
    """Remove /* ... */ comments.

    Braces inside comments are invisible to a browser, so counting them makes a healthy file
    look unbalanced -- which is what a naive brace count reported here first.
    """
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _blocks(text: str):
    """Yield (enclosing_media, selector, body) for each declaration block.

    A stack-based structural walk: every at-rule entered is remembered, and each declaration
    block is reported with the at-rules that actually enclose it. This is the distinction a
    textual test cannot make -- "the declaration appears after the media query in the file"
    is not the same as "the declaration is inside the media query".
    """
    text = _strip_comments(text)
    stack: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        stop = index
        while stop < len(text) and text[stop] not in "{}":
            stop += 1
        if stop >= len(text):
            return
        head = text[index:stop].strip()
        if text[stop] == "{":
            if head.startswith("@"):
                stack.append(("at", head))
                index = stop + 1
                continue
            depth = 1
            cursor = stop + 1
            while cursor < len(text) and depth:
                if text[cursor] == "{":
                    depth += 1
                elif text[cursor] == "}":
                    depth -= 1
                cursor += 1
            enclosing = " ".join(value for kind, value in stack if kind == "at")
            yield (enclosing or None, head, text[stop + 1:cursor - 1])
            index = cursor
            continue
        if stack:
            stack.pop()
        index = stop + 1
    return


# ---------------------------------------------------------------------------------------
# Structural validity, for every stylesheet
# ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("path", sorted(CSS_DIR.glob("*.css")), ids=lambda p: p.name)
def test_stylesheet_braces_are_balanced_outside_comments(path):
    """An unbalanced brace silently changes what a browser applies, and a browser's error
    recovery is not something to rely on: it cost a real layout regression here."""
    text = _strip_comments(path.read_text(encoding="utf-8"))
    assert text.count("{") == text.count("}"), (
        f"{path.name}: {text.count('{')} opening vs {text.count('}')} closing braces"
    )
    depth = 0
    for char in text:
        if char == "{":
            depth += 1
        elif char == "}":
            assert depth > 0, f"{path.name}: a closing brace closes nothing"
            depth -= 1
    assert depth == 0, f"{path.name}: {depth} block(s) left open"


def test_no_declaration_block_is_duplicated_verbatim():
    """The specific shape of the regression.

    A selector appearing both at top level and inside a media query is NORMAL -- that is how a
    responsive override is written, and a test forbidding it would be wrong. What is not normal
    is the SAME declarations appearing twice: that is the signature of a block deleted from
    inside a media query and left behind outside it. In the measured regression,
    `.m-settings-main { ... overflow-y: auto ... }` existed twice, byte for byte, one copy at
    top level where it applied at every width.
    """
    seen: dict[tuple[str, str], int] = {}
    for _media, selector, body in _blocks(SETTINGS_CSS.read_text(encoding="utf-8")):
        normalized = re.sub(r"\s+", " ", body).strip()
        seen[(selector, normalized)] = seen.get((selector, normalized), 0) + 1
    duplicated = {
        f"{selector}": count for (selector, _body), count in seen.items() if count > 1
    }
    assert not duplicated, f"declaration blocks duplicated verbatim: {duplicated}"


# ---------------------------------------------------------------------------------------
# The two regressions this file was written for
# ---------------------------------------------------------------------------------------

def test_the_phone_scroll_fix_is_INSIDE_the_phone_media_query_and_not_at_top_level():
    """The owner's report was "I am unable to scroll on the settings page". The fix is only
    correct if it is scoped to the phone block; at top level it also overrides desktop.

    Both directions are asserted. Checking only that SOME copy is inside the media query is
    satisfied by the legitimate copy alone, so it passes on a file that also carries an
    orphaned duplicate at top level -- which is exactly the broken state measured here.
    """
    blocks = [
        (media, body)
        for media, selector, body in _blocks(SETTINGS_CSS.read_text(encoding="utf-8"))
        if selector == ".m-settings-main"
    ]
    def is_scroller(body: str) -> bool:
        return "overflow-y: auto" in body and "min-height: 0" in body

    assert any(m and "max-width: 900px" in m and is_scroller(b) for m, b in blocks), (
        "the phone scroll fix is missing from the phone media query"
    )
    orphans = [b for m, b in blocks if m is None and is_scroller(b)]
    assert not orphans, "the phone scroll fix must not exist at top level; it would hit desktop"


def test_the_connections_row_switches_to_a_phone_grid_inside_a_phone_query():
    """Measured failure at 420px: the row kept the desktop FIVE-column template, resolved to
    660px inside a 420px viewport, and clipped its own route note.

    The cause was a stray closing brace earlier in the file corrupting the parse of this very
    block -- which `test_stylesheet_braces_are_balanced_outside_comments` catches directly
    (verified: that guard fails on the pre-fix file, this one does not). So this test is not
    the falsifier; it independently pins the four properties the override must have, any of
    which a careless edit could break: it exists, it is scoped to a phone query, it is not
    ALSO declared at top level, and it is declared after the desktop template so it wins the
    cascade.
    """
    grids = [
        (media, body)
        for media, selector, body in _blocks(SETTINGS_CSS.read_text(encoding="utf-8"))
        if selector == ".m-connection-row-settings" and "grid-template-columns" in body
    ]
    assert grids, "the row has no grid-template-columns at all"
    assert any(
        media and ("max-width: 600px" in media or "max-width: 760px" in media)
        and "18px" in body
        for media, body in grids
    ), "no phone-width grid override exists for the connections row"
    # The narrow override must not ALSO be declared at top level, where it would apply at
    # desktop widths and defeat the five-column layout.
    assert not [b for media, b in grids if media is None and "18px" in b], (
        "the phone grid must not be declared at top level"
    )
    # And it must come after the desktop template in source order, or the desktop would win
    # the cascade at phone widths.
    text = _strip_comments(SETTINGS_CSS.read_text(encoding="utf-8"))
    assert text.index("minmax(0, 1fr) auto 18px") > text.index("minmax(0, 1.2fr)"), (
        "the phone grid must be declared after the desktop grid"
    )
