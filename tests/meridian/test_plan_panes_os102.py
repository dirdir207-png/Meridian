"""OS-102: the Plan panes say what they mean, and admit what they cannot say.

Owner, 2026-09-24, on the Rules and Crew panes: the rules view showed almost nothing, and the Crew
actions were one flat sequence with a separate "deferred" list beside it. Approved as proposed:
Rules as statements built from Crew's own formula, Crew regrouped by what each action acts on, with
each deferred capability inside its own group. Edit-a-rule stays parked as its own write slice.

These guards pin the two structural fixes (the empty note survives; nothing was lost or duplicated
when the forms moved) and the honesty rules (a rule Meridian cannot explain says so and shows Crew's
own formula; a webhook path is never rendered). The statement builder's own behaviour is EXECUTED in
tests/meridian/test_rule_statement_js.py, not grepped here.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The blank rules pane
# ---------------------------------------------------------------------------


def test_the_empty_note_is_not_inside_the_list_the_renderer_clears():
    """The defect the owner reported: `renderRules` calls `list.replaceChildren()`, and the empty
    note was a CHILD of that list -- so with zero rules the note was destroyed and the pane measured
    0px. Observed in the preview before the fix: `childElementCount: 0`, note absent from the DOM."""
    html = _read("templates/meridian/partials/plan.html")
    # Match the ELEMENT, not the attribute name: the section's own comment above it explains the fix
    # by naming `[data-rules-list]`, and an index() of the bare string would find that first.
    list_open = html.index("<div data-rules-list></div>")
    note_index = html.index("<p class=\"m-empty-note\" data-rules-empty")
    assert note_index < list_open, "the empty note must come BEFORE the list it is a sibling of"
    # ...and it must be a sibling: the list element closes before the note's container would nest it.
    section = html[html.index('aria-label="Autopilot rules"') - 200:list_open + 60]
    assert "<div data-rules-list></div>" in section
    # The renderer must not assume the note exists either: depending on markup elsewhere is how
    # this broke in the first place.
    js = _read("static/js/meridian/plan.js")
    rules_fn = js.split("function renderRules(root) {", 1)[1].split("\n}", 1)[0]
    assert "if (empty) {" in rules_fn
    assert "empty.hidden = rules.length > 0" in rules_fn


def test_the_rules_pane_says_where_the_rules_came_from():
    """A card must never read as live data without saying how old it is."""
    js = _read("static/js/meridian/plan.js")
    html = _read("templates/meridian/partials/plan.html")
    assert "data-rules-source" in html
    rules_fn = js.split("function renderRules(root) {", 1)[1].split("\n}", 1)[0]
    assert "data_rules_source" in rules_fn or "data-rules-source" in rules_fn
    assert "read from Crew" in rules_fn
    assert "observation time unavailable" in rules_fn


# ---------------------------------------------------------------------------
# The statements
# ---------------------------------------------------------------------------


def test_the_old_body_summary_that_could_not_read_crew_is_gone():
    """`ruleActionsSummary` looked for `action.type`; a real Crew formula is `{roundUpTransfer: {…}}`,
    so every genuine rule rendered an empty body. Removing it is the fix; a guard keeps it removed."""
    js = _read("static/js/meridian/plan.js")
    assert "ruleActionsSummary" not in js
    assert "a.type" not in js
    assert "ruleStatementNode" in js
    assert 'from "./rule-statement.js"' in js


def test_an_unexplained_rule_discloses_itself_and_shows_crews_own_formula():
    js = _read("static/js/meridian/plan.js")
    node_fn = js.split("function ruleStatementNode(statement) {", 1)[1].split("\n}", 1)[0]
    assert "statement.recognised" in node_fn
    assert "cannot fully explain this rule yet" in node_fn
    assert "statement.unknown.join" in node_fn
    assert "Crew's own formula" in node_fn
    assert "statement.raw" in node_fn
    # The card records the state too, so a capture or a probe can tell explained from unexplained.
    card_fn = js.split("function ruleCard(rule, statement) {", 1)[1].split("\n}", 1)[0]
    assert 'card.dataset.ruleExplained = statement.recognised ? "true" : "false"' in card_fn


def test_rules_are_grouped_by_what_they_act_on_and_a_single_group_has_no_heading():
    js = _read("static/js/meridian/plan.js")
    rules_fn = js.split("function renderRules(root) {", 1)[1].split("\n}", 1)[0]
    assert 'const order = ["money", "notify", "other"]' in rules_fn
    assert "m-rule-group-title" in rules_fn
    # One group, no taxonomy: a single rule must not be given a heading it does not need.
    assert "if (present.length > 1)" in rules_fn


def test_a_rule_statement_never_renders_a_webhook_path():
    """The builder withholds it (see the executed test); this pins that the CARD does not go looking
    for it either -- the statement's text is all that reaches the DOM."""
    js = _read("static/js/meridian/plan.js")
    node_fn = js.split("function ruleStatementNode(statement) {", 1)[1].split("\n}", 1)[0]
    assert "statement.raw" in node_fn, "the raw formula is the only place a URL may appear"
    assert "innerHTML" not in node_fn, "every value renders as text"
    assert "textContent" in node_fn


# ---------------------------------------------------------------------------
# The Crew pane: grouped, and nothing lost or duplicated in the move
# ---------------------------------------------------------------------------


def test_crew_actions_are_grouped_by_purpose_with_deferred_items_inside_their_group():
    html = _read("templates/meridian/partials/plan.html")
    section = html.split('data-crew-actions data-crew-parity>', 1)[1].split("</section>", 1)[0]
    groups = re.findall(r'<div class="m-action-group" data-action-group="([a-z]+)">', section)
    assert groups == ["pockets", "bills", "rules", "cards"], groups
    # Every deferred marker lives INSIDE one of those groups, not in a list beside them.
    for block in re.split(r'<div class="m-action-group"', section)[1:]:
        markers = re.findall(r'data-parity-deferred="([a-z_]+)"', block)
        if markers:
            assert any(key in block for key in ("Rules", "Cards")), markers
    assert "Crew capabilities (deferred)" not in section, "the separate deferred list is gone"
    # The parity contract's own browser suite asserts exactly one [data-crew-parity] element.
    assert html.count("data-crew-parity>") == 1


def test_no_crew_write_form_was_lost_or_duplicated_in_the_regrouping():
    """The forms were moved by script precisely so nothing could be retyped; this proves the set is
    unchanged, since a dropped form would be a silently removed capability."""
    html = _read("templates/meridian/partials/plan.html")
    section = html.split('data-crew-actions data-crew-parity>', 1)[1].split("</section>", 1)[0]
    found = re.findall(r'<form class="m-action-form" data-ca-([a-z-]+)>', section)
    assert sorted(found) == sorted([
        "create-pocket", "set-spend", "delete-pocket", "create-bill", "top-up",
        "delete-rule", "create-virtual-card",
    ]), found
    assert len(found) == len(set(found)), "a form appears twice"
    # And every form is inside a group rather than loose in the section.
    assert section.count("<form class=\"m-action-form\"") == sum(
        block.count("<form class=\"m-action-form\"")
        for block in re.split(r'<div class="m-action-group"', section)[1:]
    )


def test_every_deferred_marker_survives_as_plain_text():
    """tests/browser/test_capability_parity.py fails closed on drift, and it also requires each
    marker to be plain list text rather than something that looks like a control."""
    html = _read("templates/meridian/partials/plan.html")
    markers = re.findall(r'<(li|p|div|span|dd) data-parity-deferred="([a-z_]+)">', html)
    assert sorted(key for _tag, key in markers) == [
        "create_pocket_reassignment_rule", "delete_pocket_reassignment_rule",
        "edit_autopilot_rule", "update_virtual_card",
    ]
    assert all(tag == "li" for tag, _key in markers), markers
