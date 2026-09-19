"""The isolated preview serves real Settings markup and synthetic reads only."""
import json
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from scripts.preview_observatory_dial import Handler


@contextmanager
def preview():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_settings_preview_uses_real_template_and_synthetic_connections():
    with preview() as base:
        with urlopen(base + "/meridian/settings?section=connections") as response:
            html = response.read().decode()
        assert "data-connections-root" in html
        assert "no bank connection" in html
        with urlopen(base + "/api/meridian/settings/connections") as response:
            payload = json.load(response)
        assert payload["groups"][0]["connections"][0]["public_id"].startswith("synthetic-")
        with pytest.raises(HTTPError) as error:
            urlopen(Request(base + "/api/meridian/settings/connections/gmail/authorize", data=b"{}"))
        assert error.value.code == 501
        with pytest.raises(HTTPError) as error:
            urlopen(base + "/meridian/settings?section=not-a-section")
        assert error.value.code == 404


def test_settings_respects_saved_theme_and_toggle_changes_it():
    from playwright.sync_api import sync_playwright

    with preview() as base, sync_playwright() as driver:
        browser = driver.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900}, color_scheme="light")
            page.add_init_script("localStorage.setItem('meridian-theme', 'dark')")
            page.goto(base + "/meridian/settings?section=connections")
            page.wait_for_load_state("networkidle")
            assert page.locator("html").get_attribute("data-theme") == "dark"
            page.locator("[data-theme-toggle]").click()
            assert page.locator("html").get_attribute("data-theme") == "light"
            assert page.evaluate("localStorage.getItem('meridian-theme')") == "light"
        finally:
            browser.close()
