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


#: Each servable Settings section and a marker only its real partial emits. Before
#: 2026-09-21 the preview served ONE section and 404'd the rest (`if section !=
#: "connections": send_error(404)`), and only SETTINGS_CONNECTIONS existed, so four fifths
#: of the page was invisible to the capture harness -- and because the isolated preview is
#: the only permitted source of fidelity evidence, Settings parity could be neither claimed
#: nor disproved for those four. This asserts every section is servable and the HUB is the
#: no-section landing page.
SERVABLE_SECTIONS = {
    "connections": "data-connections-root",
    "payday": "data-payday-root",
    "actions": "data-actions-root",
    "security": "data-security-root",
    "trials": "data-trials-root",
}


def test_every_settings_section_is_servable_by_the_isolated_preview():
    with preview() as base:
        for section, marker in SERVABLE_SECTIONS.items():
            with urlopen(f"{base}/meridian/settings?section={section}") as response:
                html = response.read().decode()
            assert marker in html, f"section {section} did not render its root marker"
            assert "Synthetic Settings preview" in html, section


def test_the_hub_is_the_no_section_landing_page():
    with preview() as base:
        with urlopen(base + "/meridian/settings") as response:
            html = response.read().decode()
        assert "data-settings-hub" in html
        for group in ("CONNECTIONS", "VIRGIL &amp; AUTHORITY", "PREFERENCES"):
            assert group in html, group
        assert "Capabilities appear only when available." in html
        # The banner must name the hub, so a capture records which surface it shows.
        assert "Synthetic Settings preview (hub)" in html


def test_section_fixtures_are_synthetic_and_read_only():
    """Every fixture the four newly-servable sections read must be recognisably synthetic,
    so a capture can never be mistaken for live data."""
    with preview() as base:
        for path, key in (
            ("/api/meridian/settings/payday", "rules"),
            ("/api/meridian/actions", "actions"),
            ("/api/auth/passkeys", "passkeys"),
            ("/api/meridian/trials/deadlines", "deadlines"),
        ):
            with urlopen(base + path) as response:
                payload = json.load(response)
            assert key in payload, path
            blob = json.dumps(payload)
            assert "synthetic" in blob.lower(), f"{path} carries no synthetic marker"

        # Connections was the one already servable; assert it too so all five are covered.
        with urlopen(base + "/api/meridian/settings/connections") as response:
            assert "synthetic" in json.dumps(json.load(response)).lower()


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
