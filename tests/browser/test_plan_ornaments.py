"""The Plan income strip's ornaments must not sit on its text, and the map's hub star must
fill the circle it sits in.

Both are owner-reported on 2026-09-24, from the iPhone Air:

  * "On next paycheck the text also overlaps with the stars on the banner, as well as the
    dollar figure" -- the strip's two decorative stars were positioned at `left/right: 2px`,
    which is measured from the card's PADDING box, so a 22px star began inside the 20px
    border-image and ran over the content box. Measured before the fix: the caption
    underlapped BOTH stars 12x17px at 420px, and the date and amount 8x10 and 8x22 at desktop.
  * "Can you make the upper most star fill the circle" -- the hub's star was a 40px mark in a
    62px disc (64.5%).

A source-read guard cannot see either defect: the CSS values looked reasonable in isolation
and only their interaction with the border width and the disc size made them wrong. So this
guard measures the rendered boxes, deriving each pseudo-element's box from its own padding
box (an absolutely positioned pseudo-element offsets from its containing block's padding
edge, and the card is `position: relative`).
"""

import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(
    not APP_URL, reason="APP_URL is required for browser tests"
)

PLAN = {
    "summary": {"headline": "Synthetic ornament probe", "commitment_count": 1,
                "total_target": 100.0, "total_funded": 100.0, "unfunded": 0.0,
                "coverage_ratio": 1.0, "next_due": "2026-10-01", "first_shortfall": None},
    "allocation": {"cash_total": 1000.0, "segments": [
        {"label": "Bills", "amount": 600.0},
        {"label": "Goals", "amount": 200.0},
        {"label": "Available", "amount": 200.0}]},
    "next_paycheck": {"date": "2026-10-02", "amount": 1435.97},
    "timeline": {"start": "2026-09-24", "end": "2026-10-24", "events": [
        {"date": "2026-10-02", "amount": 1435.97, "commitment": "Paycheck",
         "commitment_id": 1, "rule_id": "1", "source": "paycheck", "explanation": []}]},
    "commitments": [],
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-24T10:00:00Z"},
}

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 1024, "height": 768},
    "mobile": {"width": 430, "height": 932},
    "mobile-small": {"width": 390, "height": 844},
    "mobile-air": {"width": 420, "height": 912},
}

MEASURE = """() => {
    const card = document.querySelector('.m-plan-funding-card');
    const cardRect = card.getBoundingClientRect();
    const border = parseFloat(getComputedStyle(card).borderLeftWidth) || 0;
    const box = (pseudo) => {
        const cs = getComputedStyle(card, pseudo);
        if (cs.content === 'none') return null;
        const w = parseFloat(cs.width);
        const h = parseFloat(cs.height);
        const left = cardRect.left + border + parseFloat(cs.left || '0');
        const top = cardRect.top + border + parseFloat(cs.top || '0');
        return {left, right: left + w, top, bottom: top + h};
    };
    const collisions = [];
    const textSelectors = {
        title: '.m-plan-next-title',
        label: '.m-plan-funding-card .m-section-label',
        date: '[data-next-paycheck-date]',
        amount: '[data-next-paycheck-amount]',
        caption: '[data-funding-caption]',
    };
    for (const pseudo of ['::before', '::after']) {
        const star = box(pseudo);
        if (!star) continue;
        for (const [name, sel] of Object.entries(textSelectors)) {
            const el = card.querySelector(sel);
            if (!el || getComputedStyle(el).display === 'none') continue;
            const rect = el.getBoundingClientRect();
            if (!rect.width && !rect.height) continue;
            const overlapX = Math.min(star.right, rect.right) - Math.max(star.left, rect.left);
            const overlapY = Math.min(star.bottom, rect.bottom) - Math.max(star.top, rect.top);
            if (overlapX > 0 && overlapY > 0) collisions.push({pseudo, name, overlapX, overlapY});
        }
    }
    const hub = document.querySelector('.m-plan-map-hub').getBoundingClientRect();
    const mark = document.querySelector('.m-plan-map-hub-mark').getBoundingClientRect();
    // The asset is taller than it is wide: its circular BEZEL spans x 2..214 of a 217x256
    // canvas, and the extra height is the north/south rivet knobs. `contain` fits the whole
    // canvas, so the drawn bezel is the box height scaled by 213/256 -- which is the number
    // that has to match the disc, not the box width. tests/meridian/test_plan_map.py
    // re-measures that 213/256 from the PNG so this constant cannot drift silently.
    const BEZEL_OF_CANVAS_HEIGHT = 213 / 256;
    const BEZEL_OF_CANVAS_WIDTH = 213 / 217;
    const bezelWidth = mark.width * BEZEL_OF_CANVAS_WIDTH;
    const centre = (r) => r.left + r.width / 2;
    return {
        collisions,
        hub: Math.round(hub.width),
        hubMark: Math.round(mark.width),
        bezel: Math.round(mark.height * BEZEL_OF_CANVAS_HEIGHT),
        bezelWidth: Math.round(bezelWidth),
        // The BOX may exceed the disc by the canvas's own transparent padding, so centring
        // is checked on the painted bezel rather than on the box.
        bezelCentred: Math.abs(centre(hub) - centre(mark)) <= 1,
        markInsideDisc: mark.left >= hub.left - 1 && mark.right <= hub.right + 1,
    };
}"""


@pytest.mark.parametrize("name", sorted(VIEWPORTS))
def test_the_income_strip_ornaments_never_touch_its_text(browser, name):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=VIEWPORTS[name])
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": "meridian-owner-2026"}),
    )
    assert response.status == 200
    page = context.new_page()
    page.route("**/api/meridian/plan*",
               lambda route: route.fulfill(status=200, content_type="application/json",
                                           body=json.dumps(PLAN)))
    page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
    page.wait_for_selector(".m-plan-funding-card")
    page.wait_for_timeout(300)

    measured = page.evaluate(MEASURE)
    assert measured["collisions"] == [], (
        f"a decorative star sits on the strip's text at {name}: {measured['collisions']}"
    )
    # The star must not be pushed outside the ticket, which would be a different defect.
    assert page.evaluate(
        "() => { const c = document.querySelector('.m-plan-funding-card').getBoundingClientRect();"
        " const s = getComputedStyle(document.querySelector('.m-plan-funding-card'), '::before');"
        " const b = parseFloat(getComputedStyle(document.querySelector('.m-plan-funding-card'))"
        ".borderLeftWidth) || 0;"
        " const left = c.left + b + parseFloat(s.left || '0');"
        " return left >= c.left - 1 && left + parseFloat(s.width) <= c.right + 1; }"
    ), "the leading ornament escaped the ticket"
    context.close()


@pytest.mark.parametrize("name", ["desktop", "mobile-air"])
def test_the_hub_star_fills_the_circle_it_sits_in(browser, name):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=VIEWPORTS[name])
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": "meridian-owner-2026"}),
    )
    assert response.status == 200
    page = context.new_page()
    page.route("**/api/meridian/plan*",
               lambda route: route.fulfill(status=200, content_type="application/json",
                                           body=json.dumps(PLAN)))
    page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
    page.wait_for_selector(".m-plan-map-hub-mark")
    page.wait_for_timeout(300)

    measured = page.evaluate(MEASURE)
    ratio = measured["bezel"] / measured["hub"]
    assert ratio >= 0.95, (
        "the hub star's bezel is meant to fill its circle, not sit small inside it: "
        f"bezel {measured['bezel']}px in disc {measured['hub']}px = {ratio:.3f}"
    )
    assert measured["bezel"] <= measured["hub"] + 1, (
        "the bezel must not read as larger than the circle it fills: "
        f"{measured['bezel']}px in {measured['hub']}px"
    )
    assert measured["bezelWidth"] <= measured["hub"] + 1, (
        "the painted bezel must not read as wider than the circle it fills: "
        f"{measured['bezelWidth']}px in {measured['hub']}px"
    )
    assert measured["bezelCentred"], (
        "the bezel must stay centred on the disc: " + str(measured)
    )
    context.close()


@pytest.mark.parametrize("name", ["desktop", "mobile-air"])
def test_the_hub_mark_overflows_its_disc_symmetrically(browser, name):
    """The star is deliberately taller than its disc, so the knob overflow is the thing to
    check -- and it must be EVEN.

    Owner, 2026-09-24: *"Top star on plan is off center ... the whole thing needs to move up in
    the circle with the edges matching, the knobs can overlap."* Measured before the fix: 0px
    of overflow above the disc and **8.9px** below on a phone (13px at desktop), because
    `place-items: center` cannot centre an item that overflows its container: the implicit grid
    row was auto-sized to the 75px mark inside the 62px disc, and the initial
    `align-content: start` pinned that oversized row to the top. Adding `align-content: center`
    splits it evenly, which is what this asserts. A one-sided overflow means the mark has
    started hanging off the circle again.
    """
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=VIEWPORTS[name])
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": "meridian-owner-2026"}),
    )
    assert response.status == 200
    page = context.new_page()
    page.route("**/api/meridian/plan*",
               lambda route: route.fulfill(status=200, content_type="application/json",
                                           body=json.dumps(PLAN)))
    page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
    page.wait_for_selector(".m-plan-map-hub-mark")
    page.wait_for_timeout(300)

    measured = page.evaluate("""() => {
        const hub = document.querySelector('.m-plan-map-hub').getBoundingClientRect();
        const mark = document.querySelector('.m-plan-map-hub-mark').getBoundingClientRect();
        return {
            above: +(hub.top - mark.top).toFixed(2),
            below: +(mark.bottom - hub.bottom).toFixed(2),
            hubH: Math.round(hub.height),
            markH: Math.round(mark.height),
            centresMatch: Math.abs((hub.top + hub.height / 2) - (mark.top + mark.height / 2)) <= 1,
        };
    }""")
    assert measured["markH"] > measured["hubH"], (
        "the mark is meant to be sized by its bezel, so it must exceed the disc: " + str(measured)
    )
    assert abs(measured["above"] - measured["below"]) <= 1, (
        "the mark must overflow its disc evenly, not hang below it: " + str(measured)
    )
    assert measured["centresMatch"], measured
    context.close()
