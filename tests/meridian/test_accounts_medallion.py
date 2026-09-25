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
    # Since 2026-09-24 a tint can also come from a concept emblem (the owner's three named
    # accounts). It is still resolved in code and still written to the icon -- the role path is
    # unchanged, and test_emblem_tints_follow_the_concept_and_reach_the_connector pins the
    # emblem path, so this assertion keeps its original intent without naming one branch.
    assert "icon.dataset.tint = tint" in js
    assert "roleTint(role)" in js
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


# ---------------------------------------------------------------------------
# Concept 04's three named emblems (owner-selected 2026-09-24).
#
# The concept draws a compass rose for Free to Spend, a Wi-Fi mark for Bill Reserve and a star
# for Emergency Fund. The owner chose those three emblems over a type-keyed glyph set, which is
# the acceptance the delivered medallion handoff requires -- it permits that artwork only "where
# that visual mapping is deliberately accepted". These guards hold the permission to its terms:
# the key stays exact and name-based, the emblem never replaces the row's own label, and the
# whole-medallion replacement is the handoff's instruction rather than a shortcut.
# ---------------------------------------------------------------------------

EMBLEM_ART = {
    "compass": "accounts/compass-medallion.png",
    "wifi": "accounts/wifi-medallion.png",
    "star": "accounts/star-medallion.svg",
}


def _css_rule(css, selector):
    """The declaration block for one selector, with comments stripped."""
    import re

    stripped = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    marker = f"{selector} {{"
    assert marker in stripped, f"{selector} is missing"
    return stripped.split(marker, 1)[1].split("}", 1)[0]


def test_each_concept_emblem_is_a_real_delivered_asset():
    css = _read("static/css/meridian/accounts.css")
    for emblem, relative in EMBLEM_ART.items():
        asset = ROOT / "static/img/meridian/observatory" / relative
        assert asset.exists(), f"{relative} is not on disk"
        assert asset.stat().st_size > 2000, f"{relative} looks like a placeholder"
        assert f'.m-account-icon[data-emblem="{emblem}"]' in css
        assert relative in css, emblem
    # The 1254px design masters are sources, never shipped style: a derivative that quietly
    # pointed back at `design/` would ship 2 MB per row on a phone.
    assert "design/investigator-medallions" not in css


def test_the_emblem_variant_drops_the_three_layer_construction():
    """The handoff: "Replace the whole decorative medallion ... do not stack them over the
    existing frame or recolor them with a CSS mask." The art carries its own ring, field and
    glyph, so the frame, the tint border and the code-owned disk must all stand down."""
    css = _read("static/css/meridian/accounts.css")
    block = _css_rule(css, ".m-account-icon[data-emblem]")
    assert "border: 0" in block
    assert "background: none" in block
    assert "background-size: contain" in block
    # The kit frame is drawn by ::after on the base class; the emblem variant must cancel it.
    assert "content: none" in _css_rule(css, ".m-account-icon[data-emblem]::after")
    # And in the light theme the disc rule must not paint a square indigo block behind round art.
    light = _css_rule(css, 'html[data-theme="light"] .obs-shell .m-account-icon[data-emblem]')
    assert "background-color: transparent" in light


def test_the_concept_emblem_sizing_matches_the_concept_and_the_mobile_track():
    """Concept 04's medallion is ~52 CSS px on the governed 420-wide viewport (103 device px of
    853-wide art at 420/853). The mobile row track has to match it, or the disc overhangs the
    column gap -- which is what a 44px track did."""
    css = _read("static/css/meridian/accounts.css")
    icon = _css_rule(css, ".m-account-icon")
    assert "width: 52px" in icon and "height: 52px" in icon
    assert "width: 46px" not in icon
    mobile = css.split("@media (max-width: 600px)")[1]
    assert "grid-template-columns: 52px minmax(0, 1fr) auto" in mobile


def test_the_bucket_key_is_exact_and_name_based():
    """A rule that fired on a prefix would relabel "Emergency plumbing fund" with the emergency
    fund's own emblem -- a decoration asserting something untrue about the owner's money. So:
    the three concept names, matched exactly, and nothing else."""
    js = _read("static/js/meridian/accounts.js")
    table = js.split("const BUCKET_EMBLEMS = {", 1)[1].split("};", 1)[0]
    assert '"free to spend": "compass"' in table
    assert '"bill reserve": "wifi"' in table
    assert '"emergency fund": "star"' in table
    assert table.count(":") == 3, "the key table must hold concept 04's three names and no more"
    resolver = js.split("export function bucketEmblem(name) {", 1)[1].split("}", 1)[0]
    assert "BUCKET_EMBLEMS[normalizeAccountName(name)]" in resolver
    # No fuzzy path: no substring test, no regex, no prefix matching anywhere in the resolver.
    for forbidden in ("includes(", "startsWith(", "match(", "indexOf(", "/.*/"):
        assert forbidden not in resolver, forbidden


def test_an_emblem_row_still_carries_its_label_and_stays_out_of_the_a11y_tree():
    """The artwork is decoration. The row's own name is the classifier, which is why the emblem
    is allowed at all."""
    js = _read("static/js/meridian/accounts.js")
    row = js.split("function accountRow(account, role) {", 1)[1].split("\n}", 1)[0]
    # The emblem branch adds the art and does NOT also draw a glyph...
    emblem_branch = row.split("if (emblem) {", 1)[1].split("} else {", 1)[0]
    assert "dataset.emblem = emblem" in emblem_branch
    assert "innerHTML" not in emblem_branch
    # ...the role medallion keeps its semantics for every other account...
    assert "icon.innerHTML = roleIcon(role)" in row
    # ...and either way the visible name label is present and the icon is hidden from a11y.
    assert 'textNode("h3", "m-account-name", account.name)' in row
    assert 'icon.setAttribute("aria-hidden", "true")' in row


def test_emblem_tints_follow_the_concept_and_reach_the_connector():
    """The concept's cord takes its colour from the medallion it leaves, so an emblem row hands
    its own tint to the node and to the segment; the two must not read from separate tables."""
    js = _read("static/js/meridian/accounts.js")
    tints = js.split("const EMBLEM_TINTS = {", 1)[1].split("};", 1)[0]
    assert 'compass: "lilac"' in tints
    assert 'wifi: "mint"' in tints
    assert 'star: "apricot"' in tints
    row = js.split("function accountRow(account, role) {", 1)[1].split("\n}", 1)[0]
    assert "const tint = emblem ? emblemTint(emblem) : roleTint(role)" in row
    assert "row.dataset.tint = tint" in row
