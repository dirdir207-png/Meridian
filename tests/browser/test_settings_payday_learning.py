"""OS-051 browser check: the learning window control is operable and accessible.

Requires a running isolated synthetic preview (APP_URL, e.g. http://127.0.0.1:8093).
This is a FUNCTIONAL/accessibility check, not fidelity evidence: it asserts the nested
control exists, is labelled, is keyboard reachable, and that operating it changes what
the income area reports. The preview is synthetic, never live bank data.
"""

import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL is required")

DESKTOP = {"width": 1440, "height": 900}
OWNER_PASSWORD = "meridian-owner-2026"


def _page(browser, viewport=DESKTOP):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=viewport, color_scheme="light")
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200
    page = context.new_page()
    # The floor is durable state, so each test clears it through the owner's own control
    # rather than assuming the database happens to be pristine.
    cleared = context.request.post(
        f"{APP_URL}/api/meridian/settings/payday/learning-floor",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"floor": None}),
    )
    assert cleared.status == 200
    assert cleared.json()["learning"]["active"] is False
    return context, page


def test_the_learning_window_control_is_nested_labelled_and_operable(browser):
    context, page = _page(browser)
    try:
        page.goto(f"{APP_URL}/meridian/settings?section=payday")
        page.wait_for_load_state("networkidle")

        section = page.locator("[data-learning-floor]")
        assert section.count() == 1
        assert section.is_visible()

        # The date field carries an accessible name from its <label>, and the buttons
        # have readable names rather than icon-only affordances.
        date_input = page.get_by_label("Start learning from")
        assert date_input.count() == 1
        assert date_input.get_attribute("type") == "date"

        start = page.get_by_role("button", name="Start fresh from this date")
        clear = page.get_by_role("button", name="Include all history")
        assert start.is_visible()
        assert clear.is_visible()

        # A live region announces the result rather than relying on colour alone.
        summary = page.locator("[data-learning-floor-summary]")
        assert summary.get_attribute("aria-live") == "polite"
        assert "all of your income history" in summary.inner_text().lower()

        # Keyboard reachable, which is the accessibility claim that matters here.
        date_input.focus()
        assert page.evaluate("document.activeElement.tagName") == "INPUT"
    finally:
        context.close()


def test_setting_and_clearing_the_window_updates_what_the_area_reports(browser):
    context, page = _page(browser)
    try:
        page.goto(f"{APP_URL}/meridian/settings?section=payday")
        page.wait_for_load_state("networkidle")

        date_input = page.get_by_label("Start learning from")
        date_input.fill("2026-09-01")
        page.get_by_role("button", name="Start fresh from this date").click()
        # The summary switches from the all-history wording to the windowed wording, and
        # reports the excluded count rather than only showing the date.
        page.wait_for_function(
            "() => document.querySelector('[data-learning-floor-summary]')"
            ".textContent.toLowerCase().includes('onward')",
            timeout=10000,
        )
        summary = page.locator("[data-learning-floor-summary]").inner_text()
        assert "onward" in summary.lower()
        assert "excluded" in summary.lower()

        # Server state agrees with the control, so the reset is real and persisted.
        state = page.evaluate(
            "() => fetch('/api/meridian/settings/payday', {credentials: 'same-origin'})"
            ".then((r) => r.json()).then((d) => d.learning)"
        )
        assert state["active"] is True
        assert state["floor"] == "2026-09-01"

        page.get_by_role("button", name="Include all history").click()
        page.wait_for_function(
            "() => document.querySelector('[data-learning-floor-summary]')"
            ".textContent.toLowerCase().includes('all of your income history')",
            timeout=10000,
        )
        cleared = page.evaluate(
            "() => fetch('/api/meridian/settings/payday', {credentials: 'same-origin'})"
            ".then((r) => r.json()).then((d) => d.learning)"
        )
        assert cleared["active"] is False
    finally:
        context.close()
