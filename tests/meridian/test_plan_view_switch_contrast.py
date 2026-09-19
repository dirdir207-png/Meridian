"""The Plan view switch must not paint a fixed paper literal onto the page.

`--obs-paper` (#ead8b5) is a literal, not a theme token: it never flips. Using it as a
FOREGROUND is correct on a genuinely dark surface and wrong on the page, because the light
edition's page is parchment (#f4ecdf). The Plan view switch is transparent and sits on the
page, so its inactive labels were cream-on-parchment and "Rules" and "Crew" disappeared
until the owner reported it.

This file pins the page-relative control AND pins that the genuinely-dark-surface uses were
deliberately left alone, so a later bulk "fix" cannot silently change surfaces that were
already correct.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_CSS = ROOT / "static/css/meridian/plan.css"


def _rule(css: str, selector: str) -> str:
    return css.split(selector + " {", 1)[1].split("}", 1)[0]


def test_the_plan_view_switch_uses_the_page_ink_not_a_fixed_paper_literal():
    css = PLAN_CSS.read_text(encoding="utf-8")
    tab = _rule(css, ".m-seg-tab")

    assert "color: var(--m-ink);" in tab
    assert "color: var(--obs-paper);" not in tab
    # It really is a page-level control: transparent, so the page shows through.
    assert "background: transparent;" in tab
    # The active cell keeps the kit's parchment fill with the ticket ink on it.
    active = _rule(css, ".m-seg-tab.is-active")
    assert "background: var(--obs-paper);" in active
    assert "color: var(--obs-paper-ink);" in active


def test_the_paper_literal_survives_only_where_the_surface_is_genuinely_dark():
    """A blanket replacement of every `color: var(--obs-paper)` would have repainted
    controls that sit on dark surfaces and were already correct."""
    offenders = []
    for path in sorted((ROOT / "static/css/meridian").glob("*.css")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("color: var(--obs-paper);"):
                offenders.append(f"{path.name}:{number}")

    # The Plan view switch is fixed; the rest are dark-surface uses and stay.
    assert "plan.css:1039" not in offenders
    assert not any(name.startswith("plan.css") for name in offenders), offenders
    # The fix stayed scoped: the other users of the literal were not touched.
    assert len(offenders) == 8, offenders


def test_the_light_page_is_parchment_which_is_why_cream_could_not_be_seen():
    """The premise of the bug, pinned so the fix is not 'verified' against a page that
    changed underneath it."""
    observatory = (ROOT / "static/css/meridian/observatory.css").read_text(encoding="utf-8")
    light = observatory.split('html[data-theme="light"] .obs-shell', 1)[1].split("}", 1)[0]

    assert "--m-canvas: #f4ecdf" in light
    assert "--m-ink: #20263b" in light
    # And the paper literal itself never flips anywhere.
    assert "--obs-paper: #ead8b5;" in observatory
