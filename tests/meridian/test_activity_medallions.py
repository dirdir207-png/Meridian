"""Activity category medallions (OS-082): the resolver, the geometry, and the fail-safe direction.

Authority: ``BUILD_HANDOFF.md`` line 24 (geometry: "Category glyph 24-28px in a 48-56px medallion")
and line 36 (the resolution rule: "Assigned category wins over merchant words. Owner custom category
uses tag. Explicit Uncategorized uses question-circle. Utilities may specialize to Wi-Fi from a clear
descriptor only when not owner-authored... Use one stable glyph per meaning across desktop and
mobile."). Nothing here is invented.

**The safety property this file exists to protect.** ``classification_method`` is *convention, not
schema*: migration 007 adds it as a plain ``TEXT`` column with no CHECK constraint. So a new or
malformed value must resolve to the **assigned category glyph**, never to the owner's ``tag`` -- the
glyph must never render Meridian's decision as the owner's decision. That is asserted below as an
ordering property, because it is the one thing here where being wrong is a correctness problem
rather than a cosmetic one.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "static/js/meridian/activity.js"
CSS = ROOT / "static/css/meridian/activity.css"

KIT = "/static/img/meridian/observatory/kit-2026-09-18/icons"
GLYPHS = ("basket", "fork-knife", "arrow-left-right", "arrow-counterclockwise", "receipt",
          "tag", "question-circle", "wifi")


def _resolver() -> str:
    js = JS.read_text(encoding="utf-8")
    start = js.index("function resolveMedallionGlyph")
    return js[start:js.index("\nfunction buildMedallion", start)]


def test_the_resolver_exists_and_is_wired_into_the_row():
    js = JS.read_text(encoding="utf-8")
    assert "function buildMedallion(transaction)" in js, "no medallion builder"
    assert "row.append(buildMedallion(transaction)" in js, (
        "the medallion is built but never appended to the row, so nothing renders"
    )


def test_the_owner_branch_is_gated_on_user_rule_and_the_fallthrough_is_not_the_tag():
    body = _resolver()
    assert len(body) > 200, "the resolver slice is too small to be the thing under test"
    owner = re.search(r'if \(method === "user_rule"\) return "([a-z-]+)"', body)
    assert owner, 'the owner-authored branch no longer tests classification_method === "user_rule"'
    assert owner.group(1) == "tag", f"owner-authored must take the tag, got {owner.group(1)!r}"
    tail = body[owner.end():]
    assert 'return "tag"' not in tail, (
        "the tag is reachable outside the owner-authored branch -- an unrecognised or missing "
        "classification_method could then present a Meridian assignment as the owner's own"
    )
    assert 'return "question-circle"' in tail, "explicit Uncategorized must take question-circle"


def test_every_glyph_the_resolver_can_return_has_a_rule_and_a_file():
    body = _resolver()
    returned = set(re.findall(r'return "([a-z-]+)"', body)) | set(
        re.findall(r': "([a-z-]+)",', body)
    )
    returned |= {"tag"}  # the owner branch, asserted separately above
    css = CSS.read_text(encoding="utf-8")
    for slug in sorted(returned):
        assert f'[data-category-glyph="{slug}"]' in css, f"no CSS rule for glyph {slug!r}"
        assert (ROOT / KIT.lstrip("/") / f"{slug}.svg").is_file(), (
            f"{slug}.svg is referenced but not in the kit"
        )


def test_the_geometry_stays_inside_the_specified_range():
    css = CSS.read_text(encoding="utf-8")
    disc = re.search(r"\.m-activity-medallion \{[^}]*inline-size: (\d+)px", css, re.S)
    glyph = re.search(r"\.m-activity-medallion::before \{[^}]*inline-size: (\d+)px", css, re.S)
    assert disc and glyph, "the medallion or its glyph lost its size"
    assert 48 <= int(disc.group(1)) <= 56, f"disc {disc.group(1)}px is outside 48-56px"
    assert 24 <= int(glyph.group(1)) <= 28, f"glyph {glyph.group(1)}px is outside 24-28px"
