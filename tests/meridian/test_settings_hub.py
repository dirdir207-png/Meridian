"""Settings hub — the 09-18 concept's grouped directory.

Governing authority: `design/observatory-extension-2026-09-18/concepts/settings.png`, which
shows three parchment group banners (CONNECTIONS / VIRGIL & AUTHORITY / PREFERENCES) and
nine rows, each an icon medallion, a title, a subtitle and a chevron, plus a
"Capabilities appear only when available." footer.

The load-bearing guard here is the PLANNED row. The build handoff requires that unavailable
features "say unavailable/planned, not show working switches", and the failure mode is
specific and easy to reintroduce: giving one of those rows an href so it "works" like the
others, which opens an empty surface and claims a capability that does not exist. These
tests fail if that happens.
"""

from pathlib import Path

from meridian.settings_hub import (
    HUB_EXTERNAL_ROUTES,
    SETTINGS_HUB,
    SETTINGS_SECTIONS,
    settings_hub_rows,
)

ROOT = Path(__file__).resolve().parents[2]

CONCEPT = "design/observatory-extension-2026-09-18/concepts/settings.png"

#: The concept's three group labels, in the order the concept draws them.
CONCEPT_GROUPS = ("CONNECTIONS", "VIRGIL & AUTHORITY", "PREFERENCES")

#: The concept's eight rows, in the order the concept draws them. The count is EIGHT, not
#: nine: an earlier ledger note said nine and that number was carried into this slice's
#: first draft, where it produced a red test. Recounted directly from the concept twice --
#: CONNECTIONS 2, VIRGIL & AUTHORITY 3, PREFERENCES 3.
CONCEPT_ROWS = (
    "Money sources",
    "Email & calendars",
    "Approval boundaries",
    "Memory & privacy",
    "Briefings & quiet hours",
    "Appearance",
    "Funding schedules",
    "Security & devices",
)


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_the_governing_concept_exists():
    """Two records previously disagreed about whether this target existed, and one of them
    wrongly concluded the reference was unavailable. Pin the file so a future session cannot
    rebuild the hub against a missing concept."""
    assert (ROOT / CONCEPT).is_file(), f"governing concept missing: {CONCEPT}"


def test_hub_matches_the_concepts_groups_and_rows():
    assert tuple(group["label"] for group in SETTINGS_HUB) == CONCEPT_GROUPS
    labels = [row["label"] for row in settings_hub_rows()]
    # The concept draws EIGHT rows across its three groups (2 + 3 + 3). An earlier note
    # claimed nine; that number is wrong and this assertion is the record of it.
    assert len(labels) == 8, labels
    assert tuple(labels) == CONCEPT_ROWS, labels
    assert len(set(labels)) == len(labels), f"duplicate row: {labels}"


def test_every_row_carries_the_concept_parts():
    """The concept draws each row as an icon medallion + title + subtitle + chevron."""
    for row in settings_hub_rows():
        assert row["icon"], row["key"]
        assert row["tint"] in {"lilac", "mint", "apricot", "slate"}, row["key"]
        assert row["label"], row["key"]
        assert row["detail"], row["key"]


def test_row_icons_all_exist_as_shipped_kit_assets():
    """The row glyphs are the kit's own SVGs referenced as CSS masks, so a typo'd icon name
    renders an invisible box rather than failing loudly."""
    for row in settings_hub_rows():
        asset = ROOT / f"static/img/meridian/observatory/kit-2026-09-18/icons/{row['icon']}.svg"
        assert asset.is_file(), f"{row['key']} names a missing glyph: {row['icon']}"
        assert f".m-settings-icon--{row['icon']}" in _read("static/css/meridian/settings.css")


def test_a_row_with_no_read_model_is_not_a_link():
    """THE guard for this slice. A planned row must state that it is planned and must not
    navigate anywhere; a row that opened an empty page would claim a surface that does not
    exist. This fails if an href is added without the read model behind it."""
    planned = [row for row in settings_hub_rows() if row.get("unavailable")]
    assert planned, "expected at least one planned row to exist"

    template = _read("templates/meridian/partials/settings-navigation.html")
    for row in planned:
        assert row["href"] is None, f"{row['key']} is planned but carries an href"
        assert row["section"] is None, f"{row['key']} is planned but names a section"

    # The template must render non-links as a div with aria-disabled, never an anchor.
    assert 'class="m-settings-row m-settings-row-planned"' in template
    assert 'aria-disabled="true"' in template
    # And the planned row must SAY so, not merely lack a chevron.
    assert "Planned" in template
    assert "m-settings-row-tag" in _read("static/css/meridian/settings.css")


def test_available_rows_resolve_to_real_sections_only():
    """Every link on the hub must resolve somewhere real. This is what stops a dead link
    shipping, and it is why the section set is one declaration.

    A row may point inside Settings (then it names a governed section) or at another existing
    journey (then it declares `external` and names an allowed route). Anything else is a bug.
    """
    for row in settings_hub_rows():
        if row["href"] is None:
            continue
        if row.get("external"):
            assert row["section"] is None, f"{row['key']}: an external row must not claim a section"
            assert row["href"] in HUB_EXTERNAL_ROUTES, row["key"]
        else:
            assert row["section"] in SETTINGS_SECTIONS, row["key"]
            assert f"section={row['section']}" in row["href"], row["key"]


def test_funding_schedules_points_at_plan_and_does_not_duplicate_it():
    """BUILD_HANDOFF: "Funding schedules link to the existing Plan journey." The row is a
    POINTER, so it must not grow a funding surface of its own -- and this is exactly the
    mistake this slice made first, linking it to `?section=payday` (a second funding surface)
    while its own comment claimed it pointed at Plan."""
    row = next(r for r in settings_hub_rows() if r["key"] == "funding-schedules")
    assert row["href"] == "/meridian?workspace=plan"
    assert row["section"] is None, "pointing inside Settings would duplicate the Plan journey"
    assert row.get("external") is True
    assert row["detail"] == "Manage in Plan"


def test_hub_states_availability_and_carries_the_concept_furniture():
    template = _read("templates/meridian/partials/settings-navigation.html")
    # The concept's footer, verbatim.
    assert "Capabilities appear only when available." in template
    # The concept's violet wavy rule is the SAME asset Today/Activity/Accounts use, and it
    # must not be re-drawn: one asset, one meaning.
    assert "m-title-rule" in template
    assert "title-rule.svg" in _read("static/css/meridian/workspaces.css")
    css = _read("static/css/meridian/settings.css")
    # The group banners carry a star at each end, from the shipped kit.
    banner_star = css.split(".m-settings-group-banner::before", 1)[1].split("}", 1)[0]
    assert "star.svg" in banner_star
    # The banner is the kit's PARCHMENT TICKET -- the same art Today already uses for evidence.
    #
    # THIS ASSERTION WAS PREVIOUSLY ITS OPPOSITE. It pinned a MUTED low-opacity wash, on the
    # grounds that the concept's banner averages rgb(142,128,111) (a mid-tone) while its canvas
    # beside it is rgb(25,34,49), so a nine-slice parchment fill "reads as a brass bar". The
    # owner looked at the result and rejected it, 2026-09-21: the banners "looked drained and
    # inactive versus the tickets in the concept and in the rest of the app". The measurement
    # was arithmetically right and answered the wrong question -- an average cannot describe art
    # whose identity is its shaped edge, its cut corners and its rivets -- and a muted mid-tone
    # that the eye reads as a disabled control is not fidelity to a ribbon the eye reads as
    # engraved stationery.
    #
    # The authority and the date are recorded HERE, in the guard, because a guard derived from
    # a judgement is the most dangerous kind: it silently enforces a mistake and makes the
    # correct change look like a regression. Reversing one must be a deliberate, cited act.
    banner_rule = css.split(".m-settings-group-banner {", 1)[1].split("}", 1)[0]
    assert "border-image" in banner_rule
    assert "parchment-ticket.png" in banner_rule, "the banner is the kit's parchment ticket"
    assert "border-radius: 0" in banner_rule, "the shaped silhouette supplies the corners"


def test_the_hub_is_the_no_section_landing_and_adds_no_route():
    """The route renders the hub when `section` is absent and every pre-existing section
    still resolves. No route is added by this slice."""
    app_py = _read("app.py")
    assert "SETTINGS_HUB_SECTIONS" in app_py
    assert "settings_hub=SETTINGS_HUB" in app_py
    # An unknown section still lands on Connections, as it did before.
    assert "url_for('meridian_settings', section='connections')" in app_py

    settings_html = _read("templates/meridian/settings.html")
    assert "settings_hub" in settings_html or "settings-navigation.html" in settings_html


def test_planned_rows_are_not_rendered_as_enabled_controls():
    """A planned row must not look pressable: no chevron (which means "this goes
    somewhere") and a dashed border that reads as unavailable."""
    template = _read("templates/meridian/partials/settings-navigation.html")
    # The chevron is guarded by `{% if row.href %}` and the element renders a `<div>` in the
    # else-branch, so a planned row gets neither a link nor a chevron. Assert the STRUCTURE
    # rather than slicing the template: a chevron inside the guarded block, and the count of
    # `row.href` guards consistent with "link branch + chevron branch".
    assert "m-settings-row-chevron" in template
    # Three `row.href` guards: the opening element, the chevron, and the closing tag. The
    # chevron is the SECOND one, which is what keeps it off the planned branch.
    assert template.count("{% if row.href %}") == 3, "expected open-element, chevron and close guards"
    assert 'class="m-settings-row m-settings-row-planned"' in template

    planned_branch = template.split('class="m-settings-row m-settings-row-planned"', 1)[1]
    planned_branch = planned_branch.split("{% if row.href %}", 1)[0]
    assert "m-settings-row-chevron" not in planned_branch
    assert "<a class=" not in planned_branch

    css = _read("static/css/meridian/settings.css")
    planned_block = css.split(".m-settings-row-planned {")[1].split("}")[0]
    assert "cursor: default" in planned_block
    assert "dashed" in planned_block


def test_row_icon_names_are_unique_per_meaning():
    """One stable glyph per meaning: two rows sharing an icon would make them read as the
    same capability."""
    icons = [row["icon"] for row in settings_hub_rows()]
    assert len(icons) == len(set(icons)), icons


def test_hub_ink_is_defined_per_theme():
    """The banner label and the Planned tag each get their ink stated, and the rules differ.

    The banner is the kit's parchment TICKET, which is light in BOTH themes, so its label ink
    is the paper ink in both and must NOT reach for a theme-flipping token. This test asserted
    the opposite while the banner was the muted wash the ticket replaced; see the note in
    test_hub_states_availability_and_carries_the_concept_furniture for why the wash went.

    The Planned tag is a small marker sitting on the page itself, which DOES flip with the
    theme, so it keeps the per-theme token -- and that token must be defined for both themes.
    """
    css = _read("static/css/meridian/settings.css")
    assert "--m-settings-planned-ink:" in css, "the hub's attention ink must be a token"
    light = css.split('html[data-theme="light"] .m-settings-nav', 1)
    assert len(light) == 2, "the ink must be redefined for the light theme"
    assert "--m-settings-planned-ink:" in light[1].split("}", 1)[0]

    banner_rule = css.split(".m-settings-group-banner {", 1)[1].split("}", 1)[0]
    assert "var(--obs-paper-ink" in banner_rule, "the light ticket needs dark ink in both themes"
    assert "var(--m-settings-planned-ink)" not in banner_rule, "the ticket does not flip"

    tag_rule = css.split(".m-settings-row-tag {", 1)[1].split("}", 1)[0]
    assert "var(--m-settings-planned-ink)" in tag_rule

