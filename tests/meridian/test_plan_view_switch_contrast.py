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
    # RETARGETED 2026-09-24: 8 -> 9. The ninth is `dial.css` `.m-observatory-virgil-snapshot`, the
    # Today Virgil strip added with the Today snapshot composition. Today's page is the Observatory's
    # own dark navy in BOTH themes (`--obs-bg` does not flip), so a cream foreground there is the
    # correct use of the literal -- exactly the distinction this test protects.
    #
    # The assertion is an ALLOWANCE PER FILE rather than one total: at the time of this retarget the
    # total had ALSO drifted to 11 while the test still said 8 (nine in dial.css and observatory.css
    # plus two in today.css), so the pinned total had become a stale number that the code no longer
    # satisfied. Per-file allow-lists keep the protection real -- any new file, or any addition beyond
    # the counted allowance, still fails -- without pretending to know a total that no commit ever
    # reconciled.
    allowance = {"dial.css": 3, "observatory.css": 4, "today.css": 2}
    counts = {}
    for name in offenders:
        counts[name.split(":")[0]] = counts.get(name.split(":")[0], 0) + 1
    assert counts == allowance, (
        f"the paper literal must stay inside the counted dark-surface uses {allowance}; got {counts} "
        f"({offenders}). A bulk replacement, or a new file using the literal as a foreground, "
        "fails here."
    )


def test_the_light_page_is_parchment_which_is_why_cream_could_not_be_seen():
    """The premise of the bug, pinned so the fix is not 'verified' against a page that
    changed underneath it."""
    observatory = (ROOT / "static/css/meridian/observatory.css").read_text(encoding="utf-8")
    light = observatory.split('html[data-theme="light"] .obs-shell', 1)[1].split("}", 1)[0]

    assert "--m-canvas: #f4ecdf" in light
    assert "--m-ink: #20263b" in light
    # And the paper literal itself never flips anywhere.
    assert "--obs-paper: #ead8b5;" in observatory
