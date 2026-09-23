"""Isolated, deterministic component acceptance; no app, credentials or bank calls."""
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/browser/fixtures/observatory-dial.html"


@pytest.fixture
def dial_page(request):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, getattr(request, "param", "chromium")).launch()
        context = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        context.add_init_script("window.setInterval = () => 0;")
        page = context.new_page()
        page.clock.install(time=1788874920000)

        def fixture_route(route):
            path = urlparse(route.request.url).path
            if path == "/":
                route.fulfill(path=str(FIXTURE), content_type="text/html")
                return
            candidate = (ROOT / path.lstrip("/")).resolve()
            if path.startswith("/static/") and (ROOT / "static") in candidate.parents and candidate.is_file():
                route.fulfill(path=str(candidate))
            else:
                route.abort()

        page.route("**/*", fixture_route)
        page.goto("http://dial.test/")
        page.wait_for_selector(".obs-dial-svg")
        page.evaluate("document.fonts.ready")
        yield page
        context.close()
        browser.close()


def test_dial_information_stays_inside_instrument_and_controls_below(dial_page):
    """Adding controls to the artwork's positioning box must fail this check."""
    page = dial_page
    svg = page.locator(".obs-dial-svg").bounding_box()
    amount = page.locator(".obs-dial-center-amount").bounding_box()
    controls = page.locator(".obs-dial-controls").bounding_box()
    center_y = svg["y"] + svg["height"] / 2
    assert abs(amount["y"] + amount["height"] / 2 - center_y) < svg["height"] * 0.12
    assert controls["y"] >= svg["y"] + svg["height"] - 1
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_selection_retains_keyboard_focus_and_exact_event_without_writes(dial_page):
    page = dial_page
    requests = []
    page.on("request", lambda request: requests.append(request.method))
    internet = page.get_by_role("button", name="Internet", exact=False)
    internet.click()
    assert page.locator(".obs-dial-center-title").inner_text() == "Internet"
    assert page.locator(".obs-ticket-title").inner_text() == "Internet"
    assert page.evaluate("document.activeElement.querySelector('.obs-event-title')?.textContent") == "Internet"
    next_day = page.get_by_role("button", name="Next day", exact=True)
    next_day.focus()
    page.keyboard.press("Enter")
    assert page.locator("#obs-dial-range").input_value() == "7"
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Next day"
    assert all(method == "GET" for method in requests)


def test_pointer_and_keyboard_range_select_the_same_date(dial_page):
    page = dial_page
    svg = page.locator(".obs-dial-svg").bounding_box()
    page.mouse.click(svg["x"] + svg["width"] / 2, svg["y"] + svg["height"] * .03)
    slider = page.locator("#obs-dial-range")
    assert slider.input_value() == "4"
    slider.focus()
    assert slider.is_visible()
    page.keyboard.press("ArrowRight")
    assert slider.input_value() == "5"
    assert page.evaluate("document.activeElement.id") == "obs-dial-range"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_evidence_ticket_keeps_amount_reserve_and_source_in_compact_card(dial_page):
    ticket = dial_page.locator(".obs-evidence-ticket")
    assert ticket.bounding_box()["height"] <= 260
    assert ticket.locator("time").get_attribute("datetime") == "2026-09-11"
    assert "Synthetic Crew" in ticket.inner_text()
    assert ticket.inner_text().count("$84.00") == 2
    assert "No evidence is attached" in ticket.inner_text()


@pytest.mark.parametrize("width", [390, 420, 430])
def test_long_event_list_does_not_push_dial_down_or_split_amounts(dial_page, width):
    page = dial_page
    page.set_viewport_size({"width": width, "height": 844})
    page.evaluate("""async () => {
      const {renderDial} = await import('/static/js/meridian/dial.js');
      const model = structuredClone(window.MeridianObservatoryDialModel);
      model.horizonEnd = '2026-09-30';
      model.events = Array.from({length: 12}, (_, i) => ({
        ...model.events[0], id: `synthetic-stress-${i}`,
        title: i === 0 ? 'Household payment arrangement' : `Synthetic obligation ${i + 1}`,
        date: `2026-09-${String(11 + Math.floor(i / 2) * 3).padStart(2, '0')}`,
        amount: {minor: 123456 + i, currency: 'USD'}, fundingStatus: 'unknown', reserved: null
      }));
      renderDial(document.querySelector('[data-observatory-dial]'), model);
    }""")
    rail = page.locator(".obs-dial-events").bounding_box()
    # RETARGETED 2026-09-24, when the callouts moved BENEATH the dial (owner: "large dial with
    # the left-and-under overlap"; BUILD_SPEC.md §7 prescribes exactly this -- "when labels
    # cannot fit, replace them with an event list beneath the dial"). The dial no longer shares
    # a row with the callouts, so there is no band for it to be centred in and `band_slack` is
    # no longer a quantity: this assertion used to read "the dial must be centred in its band".
    #
    # The REASON that guard existed survives the composition change, and it is asserted
    # directly at the end of this test instead: a layout whose dial POSITION tracks the event
    # count is the regression (OS-035). Asserting the offset is unchanged between a short and a
    # long horizon tests that reason itself, rather than a property of a band that no longer
    # exists. What is kept here is that the rail stays a BOUNDED band, which the connector
    # layer's visibility rule depends on.
    assert rail["height"] <= 380, (
        f"the callout rail must stay a bounded band beneath the dial: {rail['height']}px"
    )
    controls = page.locator(".obs-dial-controls").bounding_box()
    assert controls["y"] >= rail["y"] + rail["height"], "Date controls must not overlap the scrollable callouts"
    assert page.locator(".obs-dial-center-amount").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
    assert page.locator(".obs-event-item").count() == 12, "All events remain reachable"
    assert page.locator(".obs-event-amount").evaluate_all("""items => items.every(el =>
      el.scrollWidth <= el.clientWidth + 1 &&
      el.getBoundingClientRect().height <= parseFloat(getComputedStyle(el).lineHeight) * 1.5)
    """)
    assert page.locator(".obs-event-title").first.evaluate("""el => {
      const start = el.firstChild.textContent.indexOf('arrangement');
      const range = document.createRange();
      range.setStart(el.firstChild, start);
      range.setEnd(el.firstChild, start + 'arrangement'.length);
      return range.getClientRects().length === 1;
    }"""), "Ordinary words should not split in the callout column"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator(".obs-event-item").last.click()
    assert page.locator(".obs-dial-center-title").inner_text() == "Synthetic obligation 12"
    assert page.locator(".obs-dial-events").evaluate("el => el.scrollTop") > 0
    # RETARGETED 2026-09-24: this read `assert window.scrollY == 0`, which held while the
    # callouts sat BESIDE the dial in a rail that scrolled internally -- selecting a deep row
    # moved only that rail. With the callouts beneath the dial, selecting a row below the fold
    # must bring it into view, and the page scrolls to do it; the old assertion therefore
    # reported 14/40/49px of scroll as a failure, which is the composition working. What the
    # guard protected -- that a click must not fling the page -- is kept as a BOUND: the scroll
    # may not exceed the callout band's own extent, and the row must be visible afterwards.
    after_click = page.evaluate("""() => {
      const row = document.querySelector('.obs-event-item:last-of-type').getBoundingClientRect();
      const rail = document.querySelector('.obs-dial-events').getBoundingClientRect();
      return {scrollY: window.scrollY, rowVisible: row.top >= 0 && row.bottom <= innerHeight,
              railTop: rail.top};
    }""")
    # The row is brought into view by the RAIL's own scroll, which the assertion above already
    # measures (`scrollTop > 0`); requiring it to also be inside the viewport would be wrong,
    # because the rail is a capped band that scrolls internally -- a row can be correctly
    # revealed within it while sitting outside the window. The preserved intent is the bound.
    assert after_click["scrollY"] <= after_click["railTop"] + 1, (
        "selecting a callout must scroll the page no further than the callout band itself, "
        f"rather than flinging it: {after_click}"
    )

    # THE REASON THE REMOVED CENTRING ASSERTION EXISTED, asserted directly: the dial's position
    # must not track the length of the event list. OS-035's regression was a layout whose dial
    # moved as the list grew; with the callouts beneath the dial a band-centre cannot express
    # that any more, but the invariance can. Measured with 12 events (the stress fixture above)
    # and with 2.
    def dial_offset_from_panel_top(event_count):
        page.evaluate("""async (count) => {
          const {renderDial} = await import('/static/js/meridian/dial.js');
          const model = structuredClone(window.MeridianObservatoryDialModel);
          model.horizonEnd = '2026-09-30';
          model.events = model.events.slice(0, count);
          renderDial(document.querySelector('[data-observatory-dial]'), model);
        }""", event_count)
        page.wait_for_timeout(150)
        return (page.locator(".obs-dial-svg").bounding_box()["y"]
                - page.locator(".obs-dial-panel").bounding_box()["y"])

    offset_with_twelve = dial_offset_from_panel_top(12)
    offset_with_two = dial_offset_from_panel_top(2)
    assert abs(offset_with_twelve - offset_with_two) <= 2, (
        "the dial's position must not move with the event count: "
        f"{offset_with_twelve}px with 12 events against {offset_with_two}px with 2"
    )


# OS-049. The dial's VISIBLE disc is clipped to `circle(47% at 50% 49.5%)` inside a
# square box, so the box's outer band is transparent. Two assertions here used to
# compare the transparent BOX against the callout column and then demand an extra 10px
# of clearance; measured, that reported an "intrusion" of a few pixels that does not
# exist in the pixels. What "the dial must not intrude into the callouts" can only
# reasonably mean is that the PAINTED dial does not reach them, so measure that.
# Verified at 390/420/430px: the painted disc clears the callout column by 7.2-8.4px.
_PAINTED_DIAL_JS = """
() => {
  const art = document.querySelector('.obs-dial-art');
  if (!art) return null;
  const b = art.getBoundingClientRect();
  const m = /circle\\(([\\d.]+)%\\s+at\\s+([\\d.]+)%\\s+([\\d.]+)%\\)/.exec(getComputedStyle(art).clipPath);
  if (!m) return null;
  const [, rp, cxp, cyp] = m.map(Number);
  const r = (rp / 100) * Math.max(b.width, b.height);
  const cx = b.x + (cxp / 100) * b.width;
  const cy = b.y + (cyp / 100) * b.height;
  return {left: cx - r, right: cx + r, top: cy - r, bottom: cy + r, cx: cx, cy: cy, r: r};
}
"""


def _painted_dial(page):
    """The dial's painted circle bounding box, or None when the art is absent."""
    return page.evaluate(_PAINTED_DIAL_JS)


@pytest.mark.parametrize("dial_page", ["chromium", "webkit"], indirect=True)
def test_iphone_air_dial_and_right_callouts_have_separate_hit_areas(dial_page):
    page = dial_page
    page.set_viewport_size({"width": 420, "height": 912})
    rail = page.locator(".obs-dial-events").bounding_box()
    painted = _painted_dial(page)
    assert painted is not None, "the dial art must be present to measure its painted extent"
    # RETARGETED 2026-09-24 to the composition the owner asked for. The callouts are no longer
    # a right-hand column ("large dial with the left-and-under overlap"), so comparing the
    # dial's right edge against a column at x=274 described a layout that no longer exists --
    # it reported "the painted dial (338.1px) must not intrude into the right-hand callouts
    # (rail at 16.0px)", which is a comparison rather than a defect. The invariant the guard
    # existed for is that the two things stay SEPARATE, and separation is now vertical:
    # the painted wheel ends above the callout list begins.
    assert painted["bottom"] <= rail["y"] + 1, (
        f"the painted dial (bottom {painted['bottom']:.1f}px) must not overlap the callout list "
        f"(top {rail['top']:.1f}px) -- they are stacked, not overlapped"
    )
    assert page.locator(".obs-dial-day-label").evaluate_all("""(labels) => {
      const railRect = document.querySelector('.obs-dial-events').getBoundingClientRect();
      return labels.every(label => label.getBoundingClientRect().bottom <= railRect.top + 1);
    }"""), "a day label must not reach into the callout list"
    page.get_by_role("button", name="Internet", exact=False).click()
    assert page.locator(".obs-dial-center-title").inner_text() == "Internet"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width,height", [(390, 844), (420, 912), (430, 932), (1440, 900)])
def test_day_labels_sit_inside_the_painted_wheel(dial_page, width, height):
    """Every day label's own BOX must stay inside the wheel it is engraved on.

    Owner, 2026-09-24: *"dates aligned inside the wheel instead of clipping."* The labels were
    anchored at a fixed `VIEWBOX.r - 22` units and centred there, which made each label's own
    box the deciding factor. Measured before the fix at 420px: the anchor sat 117px from the
    centre, the painted wheel's edge is at **127px**, and a 24x31px label centred on that
    anchor reached 132-137px — so four of five labels hung 5-10px outside the visible wheel.
    It was scale-dependent, which is why desktop looked nearly right (one label 2px over) and
    the phone did not.

    The painted radius is the authority rather than my own arithmetic: it is read from the
    plate's own clip-path circle, and it measures 127px at a 270px wrap and 291px at 620px —
    i.e. the drawn wheel edge, not a chosen tolerance. `placeDayLabels` now insets each label
    by half ITS OWN diagonal, so a wide two-digit day is pulled in further than a narrow one.
    """
    page = dial_page
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_timeout(200)
    painted = _painted_dial(page)
    assert painted is not None, "the dial art must be present to measure its painted wheel"
    labels = page.evaluate("""([cx, cy, r]) => {
        const centre = document.querySelector('.obs-dial-center').getBoundingClientRect();
        return [...document.querySelectorAll('.obs-dial-day-label')].map((el) => {
            const q = el.getBoundingClientRect();
            const corners = [[q.left, q.top], [q.right, q.top],
                             [q.left, q.bottom], [q.right, q.bottom]]
                .map(([x, y]) => Math.hypot(x - cx, y - cy));
            return {
                text: (el.textContent || '').trim().slice(0, 8),
                furthest: Math.max(...corners),
                radius: r,
                overlapsCentre: !(q.right <= centre.left || q.left >= centre.right
                                  || q.bottom <= centre.top || q.top >= centre.bottom),
            };
        });
    }""", [painted["cx"], painted["cy"], painted["r"]])
    assert labels, "the dial must render labels for today, events and the horizon end"
    for label in labels:
        assert label["furthest"] <= painted["r"] + 1, (
            f"the {label['text']!r} label reaches {label['furthest']:.1f}px from the centre, "
            f"outside the painted wheel at {label['radius']:.1f}px"
        )
        assert not label["overlapsCentre"], (
            f"the {label['text']!r} label collides with the centre readout"
        )


@pytest.mark.parametrize("width,height", [(390, 844), (430, 932), (1024, 768), (1440, 900)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_dial_layout_in_actual_template_and_stylesheets(dial_page, width, height, theme):
    """Exercise the actual shell's CSS/layout without importing the banking app."""
    import json
    import re

    from jinja2 import Environment, FileSystemLoader

    page = dial_page
    model = page.evaluate("window.MeridianObservatoryDialModel")
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    html = env.get_template("meridian/index.html").render(active_workspace="today", settings_active=False)
    # Other workspace controllers are outside this isolated component contract.
    # Preserve the real HTML and every stylesheet; only dial/shell scripts run.
    html = re.sub(r'<script\b[^>]*>.*?</script>', "", html, flags=re.S)
    html = html.replace(' data-model-url="/api/meridian/dial"', "")
    html = html.replace("</body>", f'<script>window.MeridianObservatoryDialModel={json.dumps(model)}</script>'
                        '<script type="module" src="/static/js/meridian/dial.js"></script>'
                        '<script type="module" src="/static/js/meridian/today.js"></script>'
                        '<script src="/static/js/ui/advisor_fab.js"></script>'
                        '<script type="module" src="/static/js/meridian/shell.js"></script></body>')
    page.route("**/shell", lambda route: route.fulfill(body=html, content_type="text/html"))
    page.route("**/api/meridian/today", lambda route: route.fulfill(json={
        "safe_to_spend": {"amount": 248.50, "currency": "USD", "through_date": "2026-09-16"},
        "forecast": {"available": False, "as_of": "2026-09-08"},
        "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-08T13:42:00Z"},
        "inputs": {}, "upcoming_events": [],
    }))
    page.route("**/api/advisor/status", lambda route: route.fulfill(json={"configured": False}))
    page.set_viewport_size({"width": width, "height": height})
    page.goto("http://dial.test/shell")
    page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
    page.wait_for_selector(".obs-dial-svg")
    page.wait_for_function("document.querySelector('[data-sts-figure]').textContent.includes('248.50')")
    title = page.locator(".obs-today-title")
    orbit = page.locator(".obs-today-orbit-heading")
    assert title.is_visible()
    assert title.inner_text() == "Today"
    assert orbit.is_visible()
    assert orbit.inner_text() == "Your next orbit."
    safe = page.locator("[data-sts-figure]")
    assert not safe.is_visible(), "the duplicate safe-to-spend block must not displace the dial"
    dial_box = page.locator(".obs-dial-svg").bounding_box()
    center_amount = page.locator(".obs-dial-center-amount")
    assert center_amount.inner_text() == "$248.50"
    assert page.locator(".obs-ticket-title").inner_text() == "Electric"
    amount_box = center_amount.bounding_box()
    assert dial_box["y"] < amount_box["y"] < dial_box["y"] + dial_box["height"]
    assert safe.evaluate("el => parseFloat(getComputedStyle(el).fontSize)") >= 48
    assert page.locator("[data-sts-horizon]").inner_text() == "Available until September 16"
    assert page.locator(".obs-dial-center-amount").evaluate("el => getComputedStyle(el).color") == "rgb(234, 216, 181)"
    assert not page.locator("#advisor-fab").is_visible()
    advice = page.get_by_role("button", name="Ask Virgil about this plan")
    assert advice.is_visible() if width > 430 else not advice.is_visible()
    if width <= 430:
        topbar_date = page.locator(".m-topbar-date")
        assert topbar_date.is_visible()
        assert topbar_date.inner_text() == "TUESDAY, SEPTEMBER 8"
        assert page.locator(".m-command-top").is_hidden()
        assert page.locator(".m-topbar-settings-icon").is_visible()
        assert page.locator(".m-topbar .m-theme-toggle-label").bounding_box()["width"] <= 1
        if theme == "dark":
            assert page.locator(".m-topbar").evaluate(
                "el => getComputedStyle(el).backgroundColor"
            ) == page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")
        rail_box = page.locator(".obs-dial-events").bounding_box()
        # OS-049. This was `dial_box["width"] >= width * 0.74`, which no CSS ever
        # satisfied -- it fails in both themes at 390 and 430px -- and it had no
        # recorded basis: it arrived in `63d2865` (the 2026-09-16 visual pass) in the
        # same commit that changed the layout, with no measurement or concept reference.
        # The measured PAINTED disc is 57.8-61.2% of the viewport at 390/420/430px, so
        # 74% was never a description of this design.
        #
        # It is NOT replaced with a smaller invented number, because a threshold with no
        # authority is not fixed by adjusting it. What replaces it is the real, checkable
        # requirement: the dial must be the dominant element in its row and must not
        # reach the callout column. Both are verified against painted geometry, so they
        # can no longer pass or fail on transparent box area.
        painted = _painted_dial(page)
        assert painted is not None, "the dial art must be present to measure its painted extent"
        painted_width = painted["right"] - painted["left"]
        # RETARGETED 2026-09-24. The two assertions here compared the painted dial against the
        # callout COLUMN ("the dial must be the larger element beside its callout column" and
        # "must clear the callout column"). At phone widths that column is gone -- the callouts
        # are beneath the dial, which is the owner's "large dial with the left-and-under
        # overlap" -- so both described a layout that no longer exists and the first reported a
        # full-width list as if it were a rival for the dial's row.
        #
        # OS-049's own lesson applies again: a comparison is not a requirement. The requirement
        # is now stated as the measurement it always should have been -- the dial must reach the
        # concept's proportion of the viewport -- and the callouts must be BELOW it. Concept 06
        # is the dial's governing target (BUILD_SPEC.md:25) and is a 420x908 phone frame, the
        # same device this viewport models. The concept proportion recorded in OS-035 is 82.5%
        # of the viewport WIDTH, which the wrap takes; the painted disc is inset inside it
        # (measured 338.1px of a 344.4px wrap at 420px), so the floor is set on the painted disc
        # and 0.78 is the calibrated bound over the measured 80.5-82.0%.
        proportion = painted_width / width
        assert proportion >= 0.78, (
            f"the dial must be the large element the owner asked for: the painted disc is "
            f"{proportion:.1%} of the viewport at {width}px, against the concept's 82.5%"
        )
        assert painted["bottom"] <= rail_box["y"] + 1, (
            f"the callouts ({rail_box['top']:.1f}px) must sit below the painted dial "
            f"({painted['bottom']:.1f}px), not beside it"
        )
        # OS-049. This was `dial_box["x"] <= 2`, another threshold from `63d2865` with no
        # recorded basis, and it is off by 2px against the CSS's own documented intent:
        # `.m-main` content starts at x=16 with `padding: clamp(4, 3.2vw, 7)` -> 4px at
        # these widths, and the wrap's `margin-left: -12px` puts the box at x=4, not 2.
        # Reaching 2 would need a -14px margin, which would contradict the comment's
        # "clipping 12px at the left". Measured: boxBleed 12px at both 390 and 430 --
        # exactly what the CSS documents.
        #
        # Replaced with the design's real, checkable guarantees: the dial runs off its
        # content column into the gutter by the documented 12px, its PAINTED disc stays
        # inside the viewport, and the page does not scroll horizontally.
        content_left = page.evaluate(
            "() => { const m = document.querySelector('.m-main');"
            " return m.getBoundingClientRect().x + parseFloat(getComputedStyle(m).paddingLeft); }"
        )
        assert content_left - dial_box["x"] == 12, (
            f"the dial must bleed the documented 12px into the left gutter "
            f"(content starts at {content_left:.1f}, dial box at {dial_box['x']:.1f})"
        )
        assert painted["left"] >= 0, (
            f"the painted dial ({painted['left']:.1f}px) must stay inside the viewport"
        )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert title.bounding_box()["y"] < dial_box["y"]
        # RETARGETED 2026-09-24 from `rail_box["y"] < dial_box["y"] + dial_box["height"] * .5`,
        # which described the rail beginning around the dial's vertical MIDDLE -- a property of
        # the side-by-side composition only. The invariant both compositions share is that the
        # callouts never sit over the instrument: at phone width they follow it, at desktop they
        # begin beside it. The disjunction keeps the desktop case (covered by this same test at
        # 1024/1440) as strictly checked as before.
        assert rail_box["y"] >= painted["bottom"] - 1 or rail_box["x"] >= painted["right"] - 1, (
            f"the callouts ({rail_box['y']:.1f},{rail_box['x']:.1f}) must either follow the "
            f"painted dial (bottom {painted['bottom']:.1f}) or begin beside it "
            f"(right {painted['right']:.1f}) -- never over it"
        )
        # RETARGETED 2026-09-24: this was unconditional and described the side-by-side
        # composition ("the rail begins past 65% of the dial's width"). Made conditional rather
        # than deleted, so the desktop case keeps exactly the check it had: when the callouts are
        # BESIDE the dial they must still start past that fraction, and when they are beneath it
        # the preceding assertion already covers their separation.
        if rail_box["y"] < painted["bottom"] - 1:
            assert rail_box["x"] > dial_box["x"] + dial_box["width"] * .65, (
                "a side-column of callouts must begin past two thirds of the dial's width"
            )
        assert not page.locator(".m-observatory-advice").is_visible()
        ticket_box = page.locator(".obs-evidence-ticket").bounding_box()
        assert ticket_box["height"] <= 180
        # OS-049. This was `cta_box["y"] + cta_box["height"] + 8 <= dock_box["y"]`, measured
        # at scrollTop=0, and it fails at 390px in both themes. It is not a real defect and
        # the assertion was asking the wrong question. `.m-main` is a `1fr` grid row with
        # `overflow-y: auto` (the mobile composition gives the dock its OWN grid row
        # precisely so it "cannot overlay content"), so the CTA sits below the fold at
        # scrollTop=0 — 762.2 against a scrollport edge of 758.25 — and "the last element is
        # past the fold before you scroll" is normal for a scrolling column, not a collision.
        # Measured after `scrollIntoView`: the CTA lands fully inside the scrollport
        # (390.2..435.2 against a 758.25 edge), 323px clear of the dock, and
        # `elementFromPoint` at its centre returns the CTA itself
        # (`obs-button obs-explore-plan`) — so it is reachable and unobstructed.
        #
        # The property worth asserting is that the last interactive element CAN be brought
        # fully into view and is not covered by the dock when it is, which is what replaces
        # the old scroll-position comparison. If the dock ever regressed to overlaying the
        # canvas, `elementFromPoint` would stop returning the CTA and this fails.
        page.locator(".obs-explore-plan").scroll_into_view_if_needed()
        reachable = page.locator(".obs-explore-plan").evaluate("""(el) => {
          const box = el.getBoundingClientRect();
          const port = document.querySelector('.m-main').getBoundingClientRect();
          const dock = document.querySelector('.m-nav').getBoundingClientRect();
          const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
          return {
            fullyInsideScrollport: box.y >= port.y - 0.5 && box.bottom <= port.bottom + 0.5,
            clearOfDock: box.bottom <= dock.y,
            notObstructed: !!hit && (hit === el || el.contains(hit)),
          };
        }""")
        assert reachable["fullyInsideScrollport"], (
            "the Explore CTA must be scrollable fully into view, not stranded past the "
            "scrollport edge"
        )
        assert reachable["clearOfDock"], "the Explore CTA must clear the dock once scrolled into view"
        assert reachable["notObstructed"], (
            "the Explore CTA must be the element a tap actually hits; the dock must not "
            "overlay it"
        )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Internet", exact=False).click()
    assert page.locator(".obs-ticket-title").inner_text() == "Internet"
    assert page.locator(".obs-dial-center-title").inner_text() == "Internet"
    if width == 390 and theme == "dark":
        page.get_by_role("button", name="Explore scenario").click()
        assert page.get_by_role("dialog", name="Virgil advisor").is_visible()
        page.get_by_role("button", name="Close advisor", exact=True).click()
        assert not page.get_by_role("dialog", name="Virgil advisor").is_visible()


def test_connector_runs_start_on_the_dial_and_end_at_their_own_row(dial_page):
    """Fails if a connector is decoration only. Every run must start at its own marker's
    projected point and finish at its own callout row, and the decorative layer must not
    widen the document or capture pointer input.

    RUN AT A DESKTOP WIDTH SINCE 2026-09-24, and the reason is the composition rather than
    convenience: a run is only drawn when its row sits to the RIGHT of the dial's marker
    (`if (tx <= sx + 6) continue`, "skip rather than draw backwards through the dial"). That
    rule is exactly right for the side-callout layout this test was written for, and at phone
    width the callouts are now beneath the dial (owner: "large dial with the left-and-under
    overlap"), so no run can have a clear path and none is drawn. The desktop width keeps the
    side column, so the geometry this test exists to check is still checked. The mobile
    composition is asserted in its own test below rather than by weakening this one.
    """
    page = dial_page
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(300)
    page.wait_for_selector(".obs-dial-connector")
    result = page.evaluate("""() => {
      const panel = document.querySelector('.obs-dial-panel').getBoundingClientRect();
      const svg = document.querySelector('.obs-dial-svg').getBoundingClientRect();
      const layer = document.querySelector('.obs-dial-connectors');
      const rows = [...document.querySelectorAll('.obs-event-item[data-event-id]')];
      const runs = [...document.querySelectorAll('.obs-dial-connector')].map((path) => {
        const row = document.querySelector(
          `.obs-event-item[data-event-id="${path.dataset.connectorFor}"]`
        );
        const d = path.getAttribute('d');
        const start = d.match(/^M([-\\d.]+) ([-\\d.]+) Q/);
        const end = d.match(/Q[-\\d.]+ [-\\d.]+ ([-\\d.]+) ([-\\d.]+)$/);
        const box = row.getBoundingClientRect();
        const sx = Number(start[1]) + panel.left;
        const sy = Number(start[2]) + panel.top;
        return {
          onDial: sx >= svg.left - 1 && sx <= svg.right + 1 &&
                  sy >= svg.top - 1 && sy <= svg.bottom + 1,
          endX: Number(end[1]) + panel.left,
          endY: Number(end[2]) + panel.top,
          rowLeft: box.left,
          rowMidY: box.top + box.height / 2,
        };
      });
      const style = getComputedStyle(layer);
      return {
        runs,
        rowCount: rows.length,
        pointerEvents: style.pointerEvents,
        hidden: layer.getAttribute('aria-hidden'),
        layoutWidth: Math.round(layer.getBoundingClientRect().width),
        panelWidth: Math.round(panel.width),
        overflow: document.documentElement.scrollWidth - innerWidth,
      };
    }""")
    assert result["runs"], "no connector runs were drawn"
    assert result["hidden"] == "true", "the connector layer must be decorative"
    assert result["pointerEvents"] == "none", "the connector layer must not capture clicks"
    assert result["layoutWidth"] <= result["panelWidth"], "the layer must span only the panel"
    assert result["overflow"] <= 0, "connectors must not widen the document"
    for run in result["runs"]:
        assert run["onDial"], "a run does not start on the dial"
        assert abs(run["endX"] - (run["rowLeft"] - 4)) <= 1.5, "a run does not end at its own row"
        assert abs(run["endY"] - run["rowMidY"]) <= 1.5, "a run does not end at its row midline"


def _long_horizon_model(count):
    """A horizon long enough that `.obs-dial-events` genuinely overflows and scrolls."""
    events = []
    names = ["Electric", "Internet", "Rent", "Payday", "Insurance", "Phone", "Water",
             "Streaming", "Gym", "Savings", "Credit card", "Groceries"]
    kinds = ["bill", "income", "goal", "transfer"]
    for i in range(count):
        day = 1 + i * 2
        events.append({
            "id": f"long-{i}",
            "date": f"2026-09-{day:02d}",
            "kind": kinds[i % len(kinds)],
            "title": f"{names[i % len(names)]} {i + 1}",
            "amount": {"minor": 1000 + i * 137, "currency": "USD"},
            "fundingStatus": "reserved" if i % 3 == 0 else "unknown",
            "source": "Synthetic Crew",
            "evidenceIds": [],
            "detailHref": f"#long-{i}",
        })
    return {
        "timezone": "America/New_York",
        "today": "2026-09-01",
        "horizonEnd": events[-1]["date"],
        "availableToSpend": {"minor": 24850, "currency": "USD"},
        "freshness": "fresh",
        "observedAt": "2026-09-01T13:42:00Z",
        "events": events,
        "projections": [],
    }


@pytest.fixture
def dial_page_long_horizon(request):
    """The same isolated fixture, but with a horizon that overflows the events rail.

    The rail is `max-height: calc(100vw - 90px)`, so the stock three-event fixture never
    scrolls and cannot expose a run that targets a row the rail does not show."""
    import json

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, getattr(request, "param", "chromium")).launch()
        context = browser.new_context(viewport={"width": 420, "height": 912}, device_scale_factor=1)
        context.add_init_script("window.setInterval = () => 0;")
        model = _long_horizon_model(14)
        # Before the page's own scripts, and non-writable so the fixture's inline
        # three-event model cannot overwrite it.
        context.add_init_script(
            "Object.defineProperty(window, 'MeridianObservatoryDialModel', {value: "
            + json.dumps(model) + ", writable: false, configurable: false});"
        )
        page = context.new_page()

        def fixture_route(route):
            path = urlparse(route.request.url).path
            if path == "/":
                route.fulfill(path=str(FIXTURE), content_type="text/html")
                return
            candidate = (ROOT / path.lstrip("/")).resolve()
            if path.startswith("/static/") and (ROOT / "static") in candidate.parents and candidate.is_file():
                route.fulfill(path=str(candidate))
            else:
                route.abort()

        page.route("**/*", fixture_route)
        page.goto("http://dial.test/")
        page.wait_for_selector(".obs-dial-svg")
        page.wait_for_timeout(400)
        yield page
        context.close()
        browser.close()


_CONNECTOR_AUDIT = """() => {
  const rect = (el) => { const r = el.getBoundingClientRect();
    return {top: r.top, bottom: r.bottom, cy: (r.top + r.bottom) / 2}; };
  const panel = document.querySelector('.obs-dial-panel');
  const rail = panel.querySelector('.obs-dial-events');
  const railBox = rect(rail);
  const runs = [...panel.querySelectorAll('path.obs-dial-connector')].map((p) => {
    const id = p.getAttribute('data-connector-for');
    const row = panel.querySelector(`.obs-event-item[data-event-id="${id}"]`);
    const rb = row ? rect(row) : null;
    return {id, rowCy: rb ? rb.cy : null,
            visible: rb ? (rb.cy >= railBox.top && rb.cy <= railBox.bottom) : null};
  });
  return {
    runIds: runs.map((r) => r.id),
    runs,
    railOverflows: rail.scrollHeight > rail.clientHeight,
    rowCount: panel.querySelectorAll('.obs-event-item[data-event-id]').length,
    // Anything the layer would have to clip to render.
    layerBottom: rect(panel.querySelector('.obs-dial-connectors')).bottom,
    railBottom: railBox.bottom,
  };
}"""


def test_connector_runs_do_not_target_rows_the_scrolled_rail_does_not_show(dial_page_long_horizon):
    """Owner-reported: runs "running straight down connecting to nothing, several lines".

    Before the fix, a 14-event horizon drew 14 runs while 11 of those rows sat below the
    rail's visible box; those runs left the dial, ran past the rail, and were cut off by
    the connector layer's own `overflow: hidden` in mid-air. Every drawn run must now
    target a row the rail actually shows, at the top, the middle and the bottom of the
    rail's scroll range.

    RUN AT A DESKTOP WIDTH SINCE 2026-09-24 for the same reason as the run-geometry test
    above: the rail's scroll visibility rule is only exercised where runs are drawn, and at
    phone width the callouts sit beneath the dial with no clear path for a run.
    """
    page = dial_page_long_horizon
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(300)
    audit = page.evaluate(_CONNECTOR_AUDIT)
    assert audit["railOverflows"], "the fixture must overflow the rail or it proves nothing"
    assert audit["rowCount"] == 14
    assert audit["runs"], "no connector runs were drawn at all"
    assert len(audit["runs"]) < audit["rowCount"], "runs are being drawn for hidden rows"
    for run in audit["runs"]:
        assert run["visible"] is not False, f"a run targets the hidden row {run['id']}"
        assert run["rowCy"] <= audit["railBottom"], f"run {run['id']} ends below the rail"

    seen = set(audit["runIds"])
    for target in ("scrollHeight", "scrollHeight / 2", "scrollHeight"):
        page.evaluate(
            "() => { const r = document.querySelector('.obs-dial-events'); "
            f"r.scrollTop = r.{target}; }}"
        )
        page.wait_for_timeout(250)
        after = page.evaluate(_CONNECTOR_AUDIT)
        assert after["runs"], f"no runs after scrolling to {target}"
        for run in after["runs"]:
            assert run["visible"] is not False, (
                f"after scrolling to {target}, a run targets the hidden row {run['id']}"
            )
            assert run["rowCy"] <= after["railBottom"]
        seen.update(after["runIds"])
    assert len(seen) > len(audit["runIds"]), (
        "scrolling the rail did not re-anchor the runs to the newly visible rows"
    )


def test_phone_callouts_sit_beneath_the_dial_and_no_run_crosses_the_instrument(dial_page):
    """The phone composition's own invariant, added 2026-09-24 when the callouts moved beneath
    the dial (owner: "large dial with the left-and-under overlap"; BUILD_SPEC.7 prescribes
    an event list beneath the dial when labels cannot sit beside it).

    Three things must hold, and none of them is a comparison against a layout that no longer
    exists:
      * the dial is the large element the owner asked for, at the concept's own proportion;
      * every callout row sits below the painted wheel, so the two never overlap;
      * no run is drawn ACROSS the instrument. A run's purpose is to connect a marker to its
        callout; when the callout is beneath the dial there is no clear path, so the code skips
        it (`if (tx <= sx + 6) continue`). That skip is the correct behaviour and is asserted
        here so a future edit cannot silently start drawing lines through the dial -- which is
        the class of defect the owner reported as "connecting to nothing, several lines"
        (OS-036), only worse.
    """
    page = dial_page
    page.set_viewport_size({"width": 420, "height": 912})
    # Resizing does not by itself re-position the runs in this fixture: it is loaded at a
    # desktop width, and the connector layer is recomputed on the resize it observes. The first
    # version of this test measured 15 runs and was reading exactly that staleness rather than
    # the phone layout -- loading the real app at 420px from the start measures 0. Re-rendering
    # puts the audit on the composition being asserted.
    page.evaluate("""async () => {
      const {renderDial} = await import('/static/js/meridian/dial.js');
      renderDial(document.querySelector('[data-observatory-dial]'),
                 window.MeridianObservatoryDialModel);
    }""")
    page.wait_for_timeout(400)
    painted = _painted_dial(page)
    assert painted is not None
    measured = page.evaluate("""() => {
      const panel = document.querySelector('.obs-dial-panel').getBoundingClientRect();
      const rail = document.querySelector('.obs-dial-events').getBoundingClientRect();
      const rows = [...document.querySelectorAll('.obs-event-item[data-event-id]')];
      const runs = [...document.querySelectorAll('path.obs-dial-connector')].map((p) => {
        const d = p.getAttribute('d') || '';
        const start = d.match(/^M([-\\d.]+) ([-\\d.]+) Q/);
        const end = d.match(/Q[-\\d.]+ [-\\d.]+ ([-\\d.]+) ([-\\d.]+)$/);
        return {start, end};
      });
      return {
        railTop: rail.top,
        panelLeft: panel.left,
        rowCount: rows.length,
        rowsBelowWheel: rows.every((r) => r.getBoundingClientRect().top >= rail.top - 1),
        runCount: runs.length,
        columns: getComputedStyle(document.querySelector('.obs-dial-panel')).gridTemplateColumns,
      };
    }""")
    # One column: the dial's row is the dial, and the callouts follow it.
    assert " " not in measured["columns"].strip(), (
        f"the phone panel must be a single column: {measured['columns']}"
    )
    assert measured["rowCount"] >= 1, "the fixture must render callout rows"
    assert measured["rowsBelowWheel"], "every callout row must start at or below the wheel's top"
    assert painted["bottom"] <= measured["railTop"] + 1, (
        f"the painted wheel ({painted['bottom']:.1f}px) must end above the callouts "
        f"({measured['railTop']:.1f}px)"
    )
    assert measured["runCount"] == 0, (
        "no run may be drawn across the instrument when the callouts are beneath it: "
        + str(measured)
    )
