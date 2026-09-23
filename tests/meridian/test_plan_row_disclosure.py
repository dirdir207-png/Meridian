"""Observatory slice: the Plan bill row's disclosure and its compact mobile layout (concept 02).

The concept gives each bill a chevron rather than a permanent row of action buttons, and that
disclosure is what makes the compact row possible at all: the three buttons were what forced the
tall card. These guards protect the contract from both directions -- the expanded state lives on
the ROW so the stylesheet owns the presentation, and the control carries a real expanded state so
the collapsed actions stay reachable without depending on the chevron's rotation as the only cue.

OS-089 extended the same disclosure to carry the fact line, the funding progress bar and every
piece of evidence, so the collapsed row is one band. The guards below cover what that move must
NOT break: the row keeps exactly ONE date, the full name stays available, the status badge
survives a long name, and the evidence indicator renders only when evidence exists.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/meridian/plan.css").read_text(encoding="utf-8")
HTML = (ROOT / "templates/meridian/partials/plan.html").read_text(encoding="utf-8")

MOBILE = CSS.rsplit("@media (max-width: 600px) {", 1)[1]


def test_the_disclosure_is_a_real_button_carrying_its_own_expanded_state():
    assert "m-plan-row-toggle" in JS
    assert 'rowToggle.type = "button"' in JS
    assert 'rowToggle.setAttribute("aria-expanded", "false")' in JS
    # The click handler must update the attribute as well as the row, or the accessible state
    # and the visual state can disagree.
    assert 'rowToggle.setAttribute("aria-expanded", expanded ? "false" : "true")' in JS
    # The label names the action, so the control does not rely on the chevron's direction. The
    # wording is built from a ternary, so the assertion is on that expression rather than on the
    # two finished sentences, which never appear contiguously in the source.
    assert "Show actions for" in JS
    assert '${expanded ? "Show" : "Hide"} actions for' in JS


def test_the_expanded_state_lives_on_the_row_so_the_stylesheet_owns_presentation():
    assert 'row.dataset.expanded = "false"' in JS
    assert 'row.dataset.expanded = expanded ? "false" : "true"' in JS
    assert '.m-plan-table-row[data-expanded="true"] .m-plan-cell-action' in CSS


def test_the_toggle_is_removed_from_the_desktop_grid_entirely():
    # The desktop template is four columns. A fifth cell would either create an implicit column
    # or wrap, so the toggle is display:none above the breakpoint rather than merely hidden.
    assert ".m-plan-cell-toggle {\n  display: none;\n}" in CSS


def test_the_grid_placement_is_scoped_to_the_row_and_not_to_a_class_the_head_also_uses():
    """The desktop table HEAD's first cell carries `m-plan-cell-commitment` too.

    A bare `grid-area: name` on a grid with no such template creates an implicit named line at
    the END of the grid, so the head's "Commitment" column silently moved to the far RIGHT of
    the header row while every row stayed put. The source looked right; only the capture showed
    it. So the placement is scoped to the row, and the browser guard asserts the header order.
    """
    assert ".m-plan-table-row .m-plan-cell-commitment {\n  grid-area: name;\n}" in CSS
    assert "\n.m-plan-cell-commitment {\n  grid-area: name;\n}" not in CSS
    # The head's own cell keeps the shared box styling, which is harmless on a span.
    assert ".m-plan-cell-commitment {\n  display: grid;\n  gap: var(--m-space-1);\n}" in CSS

    """Regression guard for the actual first-attempt defect.

    `display: none` was written in the mobile layout block, and a LATER mobile rule re-declared
    `display: flex` for the same cell, so the actions stayed visible, the row measured 162px and
    the disclosure appeared to do nothing. The state rule must therefore come after the layout
    rule, which is what this asserts by position.
    """
    layout = CSS.index("Actions arrive with the disclosure")
    assert CSS.index('display: none;', layout) < CSS.index("display: flex;", layout), (
        "the collapsed state must be declared before the expanded state"
    )
    assert ".m-plan-table-row[data-expanded=\"true\"] .m-plan-cell-action" in CSS


def test_the_mobile_figures_use_the_concepts_orange():
    # 02-plan.png measures rgb(242,135,62) on all three bill amounts. The shell's --obs-apricot is
    # rgb(243,178,114), a lighter tone the concept does not use for figures.
    assert "color: #f2873e" in CSS
    assert "02-plan.png measures rgb(242,135,62)" in CSS


def test_the_bills_scroll_inside_a_fixed_band_so_the_rest_fits_underneath():
    assert "overflow-y: auto" in CSS
    assert "overscroll-behavior: contain" in CSS
    # Measured, not guessed: 170px is what keeps the income strip and the add control on one
    # 420x912 screen while the band shows two and a half rows. The svh term is what stops the
    # band crowding them on a phone whose safe areas take height a desktop preview cannot show.
    assert "max-height: min(170px, 19svh);" in CSS, (
        "the band is measured against the one-screen acceptance test, not guessed"
    )


# ---------- OS-089: the collapsed row carries ONE date, and everything else is in the panel ----------


def test_the_collapsed_row_carries_exactly_one_date():
    """The correction the owner's own concept review forced.

    The first draft of the spec moved BOTH the fact line's `due ...` fragment and the NEXT
    column into the panel, which would have left the collapsed row with no date at all -- while
    02-plan.png plainly shows `Sep11` under the bill name. One date is kept and the duplicate is
    dropped: the row renders `nextDateForCommitment` (the same value the desktop NEXT column
    uses, so the two cannot disagree) and the fact line no longer states it a second time.
    """
    assert 'dateLine.dataset.commitmentDate = ""' in JS
    assert "dateLine.textContent = nextDateForCommitment(plan, commitment)" in JS
    # The duplicate must be GONE from the fact line, not merely re-rendered elsewhere.
    assert "due ${formatShortDate(commitment.due_date)}" not in JS
    assert "nameCell.append(nameWrap, dateLine)" in JS


def test_the_rest_of_the_row_lives_in_the_disclosure_panel():
    assert 'panel.className = "m-plan-table-cell m-plan-cell-panel"' in JS
    assert "panel.appendChild(facts)" in JS
    assert "panel.appendChild(inv)" in JS
    # The funding bar is NOT in the panel. The owner corrected the spec on seeing the first
    # build ("I would still want progress bars") and the concept draws it on the row, so it is a
    # row cell now -- exactly one, so the row and the panel can never disagree about the share.
    assert "panel.appendChild(progress)" not in JS
    assert 'progressCell.className = "m-plan-table-cell m-plan-cell-progress"' in JS
    assert "row.append(medallionCell, nameCell, progressCell, fundedCell, panel, nextCell)" in JS
    # None of it is still attached to the name cell, or the collapsed row would carry it twice.
    assert "nameCell.append(nameWrap, facts)" not in JS
    assert "nameCell.append(progress)" not in JS
    assert "nameCell.appendChild(inv)" not in JS


def test_the_panel_is_hidden_until_the_row_is_expanded():
    collapsed = MOBILE.index(".m-plan-cell-panel {\n    display: none;")
    expanded = MOBILE.index('.m-plan-table-row[data-expanded="true"] .m-plan-cell-panel')
    assert collapsed < expanded, "the collapsed rule must be declared before the expanded one"
    assert "display: grid;" in MOBILE[expanded : expanded + 200]


def test_the_figure_label_sits_below_the_figure_as_the_concept_draws_it():
    """The owner reported "reserved is over the dollar amount" as crowding.

    02-plan.png draws `$84` with `Reserved` UNDER it, so the label is the `::after` of the figure
    cell now. The word itself is unchanged, and so is the reason it is "Reserved" rather than
    "Funded" -- see tests/meridian/test_plan_funding_label.py, which still guards that meaning.
    """
    assert ".m-plan-cell-funded::after {" in MOBILE
    assert 'content: "Reserved";' in MOBILE
    assert ".m-plan-cell-funded::before {" not in MOBILE


def test_the_status_badge_cannot_be_pushed_out_by_a_long_name():
    """The owner: the badge is "like it is on everything but verizon payment arrangement".

    Measured at 420px, the name column is about 144px wide. When the row WRAPPED, a long name
    pushed the badge onto a second line and out of position; when the badge shared the name's
    line as a flex item, it took 85px of that 144px and left the name about 50px -- which made
    "Verizon Payment Arrangement" and "Verizon Payment" render as the same visible string, the
    collapse the spec explicitly forbids. So the badge takes the DETAIL line beside the date,
    never shares the truncating line, and is never itself truncated.
    """
    cell = MOBILE.split(".m-plan-cell-commitment {", 1)[1].split("}", 1)[0]
    assert '"name name name"' in cell
    assert '"date .    badge"' in cell
    name_block = MOBILE.split(".m-commitment-name {", 1)[1].split("}", 1)[0]
    assert "grid-area: name;" in name_block
    assert "overflow: hidden;" in name_block
    assert "text-overflow: ellipsis;" in name_block
    assert "white-space: nowrap;" in name_block
    # The wrapper's box is spent so the name can take the whole cell; a plain div carries no
    # role, so nothing leaves the accessibility tree with it.
    assert ".m-plan-cell-name {\n    display: contents;\n  }" in MOBILE
    badge_block = MOBILE.split(".m-commitment-type,\n  .m-bill-badge {", 1)[1].split("}", 1)[0]
    assert "grid-area: badge;" in badge_block
    assert "white-space: nowrap;" in badge_block


def test_the_badge_and_the_type_tag_can_never_land_in_the_same_grid_area_together():
    """They share one area, so they must not be able to co-occur. They cannot: the script renders
    the tag only for a non-bill, and the badge only from `biller_status`, which the plan service
    sets for bills. If either of those stops being true the layout would overlap, not merely look
    odd, so both sides of the claim are asserted here."""
    assert 'if (commitment.type && commitment.type !== "bill")' in JS
    assert 'const status = commitment.biller_status;' in JS
    assert '"biller_status": _biller_status(' in (ROOT / "meridian/services/plan.py").read_text(
        encoding="utf-8"
    )
    billers = (ROOT / "meridian/billers.py").read_text(encoding="utf-8")
    assert 'if commitment.type != CommitmentType.BILL:\n        return "on_track"' in billers


def test_the_full_name_stays_available_in_the_panel_and_the_accessible_name():
    """Truncation must never make two different bills look identical.

    A CSS ellipsis is acceptable for the row, but the full text has to be reachable: it is the
    panel's heading, and the row's own accessible name already carries it. A `title` attribute
    would not do -- it is not reliably announced and never appears on touch.
    """
    assert 'panelName.className = "m-plan-panel-name"' in JS
    assert "panelName.textContent = commitment.name" in JS
    assert "aria-label\", `View ${commitment.name} rule`" in JS
    assert "title" not in JS.split("panelName.className", 1)[1].split(";", 1)[0]


def test_the_bill_type_tag_is_removed_but_a_goal_still_says_goal():
    """The §6a wrinkle, resolved rather than skipped.

    The owner confirmed the banner `Upcoming bills` against the concept, and directed that the
    word BILL be removed from the rows. But this list CAN hold a goal -- the synthetic fixture
    carries one, and so does the real payload shape -- so a bills banner over a goal row would
    state something untrue. The type tag is therefore dropped for bills and KEPT for every other
    type: a goal still says GOAL beside its name.
    """
    assert 'if (commitment.type && commitment.type !== "bill")' in JS
    assert "type.textContent = TYPE_LABELS[commitment.type] || commitment.type" in JS


def test_the_evidence_indicator_renders_only_where_evidence_exists():
    """An indicator that is always present would claim evidence the payload does not have, and a
    disabled one is the same lie in a quieter voice. It is rendered inside `if (invoices.length)`."""
    assert "let evidenceCell = null;" in JS
    assert "if (invoices.length) {" in JS
    assert 'evidenceIndicator.className = "m-evidence-indicator"' in JS
    assert 'evidenceIndicator.dataset.evidenceCount = String(invoices.length)' in JS
    # The row says nothing about evidence in text, so this icon is the only signal that content
    # exists, which makes a real accessible name mandatory rather than decorative.
    assert 'evidenceIndicator.setAttribute("aria-label", "Evidence available")' in JS
    # The invoices themselves stay the things that open an invoice.
    assert 'window.open(invoice.content_url, "_blank", "noopener")' in JS


def test_the_medallion_glyph_follows_the_type_and_never_the_name():
    """OS-088 is blocked because a commitment carries no category.

    Guessing one from the bill's name is forbidden -- a guess that is wrong about money is worse
    than no icon -- so the glyph comes from the commitment's TYPE, which is real data, and an
    unknown type falls back to the kit's question glyph.
    """
    assert "const COMMITMENT_TYPE_ICONS = {" in JS
    assert 'kitIconUrl(COMMITMENT_TYPE_ICONS[commitment.type] || "question-circle")' in JS
    assert "medallion.dataset.commitmentType" in JS
    # No name-matching, in the style of the Activity ledger's merchant hints.
    assert "commitment.name.match" not in JS
    assert "new RegExp(commitment.name" not in JS


def test_the_section_is_renamed_on_screen_AND_in_both_accessible_names():
    """A cosmetic rename that leaves `aria-label="Commitments"` behind gives screen-reader users a
    different name for the list than sighted users. There are TWO attributes, not one."""
    assert HTML.count('aria-label="Upcoming bills"') == 2
    assert 'class="m-section-label">Upcoming bills<' in HTML
    assert "Commitments</h2>" not in HTML
    assert 'aria-label="Commitments"' not in HTML


def test_the_section_order_is_bills_then_income_then_controls_then_coverage():
    """Owner-directed 2026-09-23. Asserted by POSITION, because the three blocks live in one grid
    whose desktop placement deliberately reproduces the arrangement this order replaced."""
    table = HTML.index("m-plan-table-section")
    funding = HTML.index("m-plan-funding-card")
    actions = HTML.index('class="m-plan-create-actions"')
    coverage = HTML.index("m-plan-coverage-card")
    assert table < funding < actions < coverage


def test_the_add_control_spans_the_width_on_mobile():
    actions = MOBILE.split(".m-plan-create-actions {\n    display: grid;", 1)[1].split("}", 1)[0]
    assert "grid-template-columns: minmax(0, 1fr);" in actions
    assert "width: 100%;" in MOBILE


def test_the_medallion_material_is_the_kits_existing_brass_ring():
    """OS-087. The material gap closes with an asset that is ALREADY tracked and indexed -- the
    bevelled brass ring Accounts, Settings and Activity have used since 2026-09-23 -- so no
    generation, and therefore no spend, was needed to lift every medallion at once."""
    ring = "kit-2026-09-16/medallion-frame.png"
    assert ring in CSS
    assert ".m-plan-medallion-disk::after {" in CSS
    assert ".m-plan-map-hub::after {" in CSS
    # The flat composition it replaced is gone: a CSS border under a bevelled ring reads as a
    # doubled edge.
    disk = CSS.split(".m-plan-medallion-disk {", 1)[1].split("}", 1)[0]
    assert "border: 0;" in disk
