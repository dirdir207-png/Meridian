"""Accounts must survive a pending memory proposal at a phone width.

Owner-reported on 2026-09-24 from his iPhone Air: "the accounts page is now larger than my
screen". Measured: no DOCUMENT overflow is reported (``documentElement.scrollWidth`` stayed
420) because the mobile shell's ``.m-main`` is itself a scroll container, so the page quietly
scrolls sideways instead of failing a document-level check. Inside it, ``[data-accounts]``
measured **497px inside a 388px column**: the Assets & Contracts strip could not shrink.

The trigger is DATA, not markup: ``memory-manage.js`` renders one ``.pending-memory-proposal``
row per pending memory action, and that row is a non-wrapping flex row (label + the review
``<dl>`` + Approve + Execute + status) whose min-content is ~420px. A grid track sized ``auto``
cannot go below its item's min-content, so the whole Accounts column widened. With no pending
proposal the same page fits, which is why every existing guard passed.

So the invariant asserted here is about the CONTAINER, not the document: the workspace's own
content box must not be wider than the workspace, and the row's controls must stay on screen.
"""

import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(
    not APP_URL, reason="APP_URL is required for browser tests"
)

# The owner's own handset, plus the narrowest governed mobile viewport.
OWNER_VIEWPORT = {"width": 420, "height": 912}
NARROW_VIEWPORT = {"width": 390, "height": 844}

# A memory proposal with the long parameter set the real pipeline records, so the review
# grid carries realistic width pressure rather than an easy one-word row.
PENDING = {
    "actions": [
        {
            "id": "act-1",
            "type": "create_asset",
            "rationale": "Track the 2021 vehicle as an asset against the auto loan",
            "params": {
                "name": "2021 Honda Accord",
                "category": "vehicle",
                "acquired_on": "2021-04-17",
                "estimated_value": 18450.0,
                "notes": "Financed; registration renewal is due each March",
            },
        }
    ]
}


def _authed_page(browser, viewport):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=viewport)
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": "meridian-owner-2026"}),
    )
    assert response.status == 200
    return context.new_page()


@pytest.mark.parametrize("viewport", [OWNER_VIEWPORT, NARROW_VIEWPORT])
def test_pending_memory_proposal_does_not_widen_the_accounts_workspace(browser, viewport):
    page = _authed_page(browser, viewport)
    page.route(
        "**/api/actions/pending*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(PENDING),
        ),
    )
    page.goto(f"{APP_URL}/meridian?workspace=accounts", wait_until="domcontentloaded")
    page.wait_for_selector("[data-testid=pending-memory-proposal]")
    page.wait_for_timeout(300)

    # The row really rendered with its controls, or the measurement proves nothing.
    assert page.locator("[data-testid=approve-proposal]").is_visible()

    measured = page.evaluate(
        """() => {
            const root = document.querySelector('[data-accounts]');
            const strip = document.querySelector('.memory-management');
            const row = document.querySelector('[data-testid=pending-memory-proposal]');
            const main = document.querySelector('.m-main');
            const buttons = [...document.querySelectorAll(
                '[data-testid=pending-memory-proposal] button'
            )];
            return {
                rootClient: root.clientWidth,
                stripWidth: strip.getBoundingClientRect().width,
                rowClient: row.clientWidth,
                rowScroll: row.scrollWidth,
                mainClient: main.clientWidth,
                mainScroll: main.scrollWidth,
                pageScroll: document.documentElement.scrollWidth,
                viewport: innerWidth,
                widestRight: Math.max(...buttons.map((b) => b.getBoundingClientRect().right)),
            };
        }"""
    )

    # Measured on the STRIP's own layout width, not on the workspace's scrollWidth: the
    # accounts summary ticket is deliberately rotated -3.2deg, so its transform-inflated
    # bounding box exceeds its column by a few px by design and is absorbed by the shell's
    # gutters. The defect was the strip's real layout width, which was 492px in a 388px
    # column and is asserted here directly.
    assert measured["stripWidth"] <= measured["rootClient"] + 1, (
        "the Assets & Contracts strip must shrink to the Accounts column, "
        f"not widen it: {measured}"
    )
    assert measured["rowScroll"] <= measured["rowClient"] + 1, (
        f"the pending-proposal row must fit its own box: {measured}"
    )
    assert measured["mainScroll"] <= measured["mainClient"] + 1, (
        f"the mobile canvas must not scroll sideways: {measured}"
    )
    assert measured["pageScroll"] <= measured["viewport"] + 1, measured
    assert measured["widestRight"] <= measured["viewport"] + 1, (
        f"a pending-proposal control sits off-screen: {measured}"
    )
