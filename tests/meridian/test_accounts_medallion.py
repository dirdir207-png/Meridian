"""Observatory slice: the Accounts account medallion (concept 04).

Kit README: `medallion-frame.png` is a "Decorative frame above a code-owned colored
disk and semantic SVG icon." That sentence is the whole contract, so these guards check
all three layers are present and that the semantic layer was not traded away for a
prettier one.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_account_medallion_layers_the_kit_frame_over_a_code_owned_disk():
    js = _read("static/js/meridian/accounts.js")
    css = _read("static/css/meridian/accounts.css")
    # The supplied frame, layered above the disk rather than replacing it.
    assert "kit-2026-09-16/medallion-frame.png" in css
    assert ".m-account-icon::after" in css
    # A code-owned coloured disk: the tint is chosen in JS, not baked into the art.
    assert "border-radius: 50%" in css
    assert "ROLE_TINTS" in js
    assert "icon.dataset.tint = roleTint(role)" in js
    # The three tints the concept shows, plus a quieter default for the rest. In JS the
    # tint is a value in ROLE_TINTS ("cash: 'lilac'"), in CSS it selects the disk colour.
    for tint in ("lilac", "mint", "apricot"):
        assert f'data-tint="{tint}"' in css
        assert f'"{tint}"' in js


def test_account_medallion_keeps_the_semantic_role_icons():
    """The kit supplies no equivalent for liabilities or reimbursements, so the existing
    role line-icons stay. Swapping them for the kit set would lose meaning, not gain
    fidelity -- the kit's own vocabulary prescribes `bank` for reserves and nothing for
    the other roles."""
    js = _read("static/js/meridian/accounts.js")
    for role in ("cash", "savings", "investments", "liabilities", "reimbursements"):
        assert f"{role}: `<svg" in js, role
    # The glyph is decorative alongside a visible label, so it stays out of the a11y tree.
    assert 'icon.setAttribute("aria-hidden", "true")' in js


def test_account_medallion_does_not_use_a_plain_square_tile():
    """Regression guard: the concept's medallion is round, and the previous treatment was
    a rounded square that would silently satisfy any weaker assertion."""
    css = _read("static/css/meridian/accounts.css")
    icon_block = css.split(".m-account-icon {")[1].split("}")[0]
    assert "border-radius: 50%" in icon_block
    assert "--m-radius-md" not in icon_block
