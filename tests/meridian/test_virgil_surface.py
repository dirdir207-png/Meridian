"""OS-071 — the Virgil surface, built to the governing 09-18 concept.

The concept is ``design/observatory-extension-2026-09-18/concepts/virgil.png``: a large
serif "Virgil" over a violet wavy rule, the tagline "Clarity, with evidence.", a
"Read-only session" status line, Conversation / Tasks tabs divided by star-tipped brass
rules, a suggested-question chip, a parchment evidence card, a draft review card, a
"Sources & assumptions" disclosure, a row stating "Voice & iPhone actions — planned /
Not available in this session.", and a composer with a violet send control.

**What these tests are actually for.** OS-071's limits are the risk here, not the
styling: VISUAL AND READ-ONLY ONLY, no A1–A5 capability implemented, enabled or *implied*.
The dangerous failure is not a missing ornament — it is a surface that LOOKS like it can
do something it cannot, or a card that shows a number the data does not support. So most
of these assertions are about restraint: no new endpoint, no mutation added, a count that
comes from the data, and an unavailable capability that says so.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates/partials/advisor_fab.html"
JS = ROOT / "static/js/ui/advisor_fab.js"
CSS = ROOT / "static/css/meridian/advisor.css"
CONCEPT = ROOT / "design/observatory-extension-2026-09-18/concepts/virgil.png"


def _template() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _template_rendered() -> str:
    """The template with its {# ... #} commentary removed.

    The comments deliberately NAME the strings they explain -- including the ones that
    must not be rendered, such as the concept's hardcoded count and its synthetic-preview
    label. Asserting absence against raw source would fail on its own explanation, so the
    assertions run against what actually reaches the browser.
    """
    return re.sub(r"\{#.*?#\}", "", _template(), flags=re.S)


def _js() -> str:
    return JS.read_text(encoding="utf-8")


def _css() -> str:
    return CSS.read_text(encoding="utf-8")


def _css_without_comments() -> str:
    """CSS with /* ... */ removed, for the same reason: a comment that says "not green"
    must not be read as the declaration being green."""
    return re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)


def test_the_governing_concept_still_exists():
    """The visual authority for this surface. If it moves, the fidelity claim is void."""
    assert CONCEPT.is_file()


# ---------------------------------------------------------------------------------------
# The concept's blocks are present
# ---------------------------------------------------------------------------------------

def test_the_concept_identity_is_present():
    html = _template()
    assert "Clarity, with evidence." in html
    assert "Read-only session" in html
    # The shell's shared wavy-rule primitive, not a second copy of the ornament.
    assert "m-title-rule" in html


def test_the_tabs_and_the_suggested_question_are_present():
    html = _template()
    assert "Conversation" in html and "Tasks" in html
    assert "What needs my attention this week?" in html


def test_the_sources_disclosure_and_planned_row_match_the_concept():
    html = _template()
    assert "Sources &amp; assumptions" in html
    # The concept's own wording, verbatim: it is the pattern the whole slice follows.
    assert "Voice &amp; iPhone actions — planned" in html
    assert "Not available in this session." in html


# ---------------------------------------------------------------------------------------
# THE COUNT IS DATA, NOT DECORATION
# ---------------------------------------------------------------------------------------

def test_the_evidence_title_is_never_hardcoded_in_the_template():
    """The concept's card reads "Two things worth a look". That is a COUNT, and a fixed
    count becomes a lie at one item or at three — the same defect BUILD_HANDOFF.md names
    for the Review concept ("render the actual total, never hardcode three")."""
    html = _template_rendered()
    assert "Two things worth a look" not in html
    # The title element ships empty and is filled from the payload.
    assert "data-virgil-evidence-title" in html
    assert not re.search(r'data-virgil-evidence-title[^>]*>\s*\w', html), "title ships pre-filled"


def test_the_count_word_follows_the_real_number():
    """The JS must singularise at one and fall back to digits beyond its word list, so no
    count can silently render the wrong word."""
    js = _js()
    assert "ADVISOR_COUNT_WORDS" in js
    assert "thing worth a look" in js and "things worth a look" in js
    # 1 is special-cased, and an unmapped count falls back to the numeral.
    assert "items.length === 1" in js
    assert "ADVISOR_COUNT_WORDS[n] || String(n)" in js


def test_an_empty_briefing_hides_the_card_rather_than_showing_an_empty_one():
    """The concept draws a filled card because it is a mock with mock data. With nothing
    to report, an empty card would imply Meridian has something to say when it does not."""
    js = _js()
    assert "card.hidden = true" in js
    assert "if (!items.length)" in js


# ---------------------------------------------------------------------------------------
# RESTRAINT: no capability, no new route, no mutation
# ---------------------------------------------------------------------------------------

def test_the_briefing_adds_no_endpoint_and_no_mutation():
    """The surface must READ what already exists. The one POST in this file is the
    pre-existing advisor send, which this redesign deliberately does not touch — so the
    assertion is that the new briefing code adds no other call and no other verb."""
    js = _js()
    briefing = js.split("async function advisorLoadBriefing", 1)[1].split("\nfunction ", 1)[0]
    called = set(re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", briefing))
    assert called == {"/api/meridian/weather", "/api/actions/pending"}, called
    # Read-only: the briefing passes no method, so fetch defaults to GET.
    assert "method" not in briefing, "the briefing must issue plain GETs"

    # Exactly one mutation in the whole file, and it is the pre-existing advisor send.
    assert js.count("method: 'POST'") == 1, "a second POST was introduced"
    post_owner = js.split("method: 'POST'", 1)[0].rsplit("fetch(", 1)[1]
    assert "/api/meridian/advisor" in post_owner or "/api/advisor/chat" in post_owner, post_owner


def test_the_tasks_tab_does_not_pretend_to_work():
    """OS-071 forbids a task runner, and the concept does not state that the tab is
    unavailable — so the surface must state it rather than open an empty shell."""
    html = _template()
    tasks_block = html.split('id="virgil-view-tasks"', 1)[1].split("</div>", 1)[0]
    assert "Planned" in tasks_block
    assert "not available in this session" in tasks_block.lower()


def test_the_surface_adds_no_approval_or_execution_affordance():
    """The surface may propose; it may never approve. The only action that leaves it is
    navigation into the existing review surface."""
    html = _template()
    for forbidden in ("data-review-approve", "data-approve", "data-execute", "data-mutate"):
        assert forbidden not in html, forbidden
    # "Open review" navigates; it does not approve.
    assert 'href="/meridian/settings?section=actions"' in html


def test_no_voice_or_device_capability_is_wired():
    """Voice is an INPUT method and the iOS path is capability-gated; neither may be
    wired by drawing it."""
    html = _template()
    assert "getUserMedia" not in html
    assert "webkitSpeechRecognition" not in html.replace("SpeechRecognition", "")
    for token in ("getUserMedia", "SpeechRecognition", "mediaDevices", "/voice"):
        assert token not in _js(), token


# ---------------------------------------------------------------------------------------
# FIDELITY DEPARTURES: deliberate, and each one is recorded
# ---------------------------------------------------------------------------------------

def test_the_draft_dot_is_neutral_lilac_not_the_concepts_confirmed_green():
    """BUILD_HANDOFF.md: "Virgil's draft state must be neutral/lilac rather than
    confirmed-green." A draft that has taken no action must not read as a success."""
    dot = _css_without_comments().split(".m-virgil-dot {", 1)[1].split("}", 1)[0]
    assert "var(--obs-lilac)" in dot
    # Neither the success colour nor a raw green may appear in the dot itself.
    assert "--obs-mint" not in dot
    for green in ("#4f9d69", "#7fbf8f", "green"):
        assert green not in dot, green


def test_the_synthetic_preview_label_is_not_shown_but_real_state_still_is():
    """BUILD_HANDOFF.md: "Hide the synthetic-preview label in the real app, but never hide
    a real stale/unavailable state." Hence the decorative line keeps only its first half
    and the real status element survives."""
    html = _template_rendered()
    assert "Synthetic preview" not in html
    assert "Read-only session" in html
    assert 'id="advisor-fab-status"' in html


def test_the_review_card_declares_the_fixed_state_the_concept_shows():
    """A pending action HAS taken no action, so this line is honest as fixed copy — and it
    is the phrasing that keeps the card from implying something already happened."""
    html = _template()
    assert "Draft · No action taken" in html


def test_the_content_region_scrolls_so_nothing_is_unreachable():
    """The defect this guards, measured before the fix: the panel was capped at
    min(70svh, 28rem) = 448px with `overflow: hidden`, so once the briefing existed the
    header sat 74px ABOVE the viewport and the composer 394px below the panel's own box.
    Both were clipped with no way to scroll to them.

    The fix is structural: the panel clips, the VIEW scrolls, and the transcript inside it
    must not open a second scroller that would strand the briefing above it."""
    css = _css_without_comments()
    view = re.search(r"^\.m-virgil-view \{[^}]*\}", css, re.M)
    assert view, "no .m-virgil-view rule"
    assert "overflow-y: auto" in view.group(0), "the content region must scroll"
    assert "min-height: 0" in view.group(0), "a flex child needs min-height:0 to scroll"

    # The log keeps its own scroller for the legacy/no-briefing layout, but INSIDE the
    # view it must be plain flow.
    nested = re.search(
        r"#advisor-panel \.m-virgil-view \.m-advisor-log \{[^}]*\}", css, re.M
    )
    assert nested, "no rule neutralising the nested log scroller"
    assert "overflow: visible" in nested.group(0)
    assert "flex: 0 0 auto" in nested.group(0)


def test_mobile_is_a_full_height_sheet_not_a_clipped_card():
    """BUILD_HANDOFF.md: "Contextual entry opens a mobile full-height sheet" and "At
    390/420/430px: single column, compact header and tabs, full-height detail sheet".
    The panel used to be a compact card on mobile."""
    css = _css_without_comments()
    # Two `max-width: 900px` blocks exist in this file, so match the one that actually
    # carries the panel rule rather than the first occurrence.
    mobile = re.search(
        r"@media \(max-width: 900px\) \{\s*#advisor-panel\.m-advisor \{([^}]*)\}", css
    )
    assert mobile, "no mobile rule for the panel"
    panel = mobile.group(1)
    # Full height: anchored to BOTH insets, with the cap removed.
    assert "bottom:" in panel, "the sheet must be anchored to the bottom inset"
    assert "max-height: none" in panel, "the mobile cap must be lifted"

    """The violet send control, as an OVERRIDE that lands after the base composer rule.

    Order is part of the assertion: the base rule and the override share one selector
    (`#advisor-panel .m-advisor-send`), so the override only wins because it comes later.
    A later edit moving it above the base would silently restore the old colour.
    """
    css = _css_without_comments()
    base = re.search(r"^#advisor-panel \.m-advisor-send \{", css, re.M)
    assert base, "the base composer rule is missing"
    violet = re.search(
        r"^#advisor-panel \.m-advisor-send \{[^}]*var\(--obs-lilac\)", css, re.M
    )
    assert violet, "no violet send-control rule"
    assert violet.start() > base.start(), (
        "the violet override must come after the base composer rule"
    )
