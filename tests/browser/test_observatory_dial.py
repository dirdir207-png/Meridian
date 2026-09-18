"""Browser checks for the concept-focused Observatory dial.

These tests are skipped unless APP_URL is supplied. They exercise synthetic
selection only and never approve, execute, or submit a financial mutation.
"""
import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(APP_URL is None, reason="APP_URL is required for browser tests")
OWNER_PASSWORD = "meridian-owner-2026"


def _authenticated_page(browser, viewport):
    context = browser.new_context(viewport=viewport)
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200
    return context, context.new_page()


def test_event_selection_updates_dial_center_and_ticket_without_post():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as browser_driver:
        browser = browser_driver.chromium.launch()
        context, page = _authenticated_page(browser, {"width": 1440, "height": 900})
        try:
            page.goto(f"{APP_URL}/meridian?workspace=today", wait_until="networkidle")
            page.wait_for_selector("[data-observatory-dial] .obs-dial-panel")
            page.wait_for_timeout(500)
            requests = []
            page.on("request", lambda request: requests.append(request))

            first = page.locator("[data-observatory-dial] .obs-event-item").first
            first_title = first.locator(".obs-event-title").inner_text()
            first.click()
            page.wait_for_timeout(300)

            assert page.locator(".obs-dial-center-title").inner_text() == first_title
            assert page.locator(".obs-evidence-ticket .obs-ticket-title").inner_text() == first_title
            assert page.locator('.obs-event-item[data-selected="true"]').count() == 1
            assert not any(request.method != "GET" for request in requests)
        finally:
            context.close()
        browser.close()


def test_dial_mobile_has_no_horizontal_overflow():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as browser_driver:
        browser = browser_driver.chromium.launch()
        context, page = _authenticated_page(browser, {"width": 390, "height": 844})
        try:
            page.goto(f"{APP_URL}/meridian?workspace=today", wait_until="networkidle")
            page.wait_for_selector("[data-observatory-dial] .obs-dial-panel")
            overflow = page.evaluate(
                "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            assert overflow <= 1
        finally:
            context.close()
        browser.close()
