"""Isolated, deterministic component acceptance; no app, credentials or bank calls."""
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/browser/fixtures/observatory-dial.html"


@pytest.fixture
def dial_page():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
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
    safe = page.locator("[data-sts-figure]")
    assert safe.is_visible()
    assert safe.bounding_box()["y"] < page.locator(".obs-dial-svg").bounding_box()["y"]
    assert safe.evaluate("el => parseFloat(getComputedStyle(el).fontSize)") >= 48
    assert page.locator("[data-sts-horizon]").inner_text() == "Available until September 16"
    assert page.locator(".obs-dial-center-amount").evaluate("el => getComputedStyle(el).color") == "rgb(234, 216, 181)"
    assert not page.locator("#advisor-fab").is_visible()
    assert page.get_by_role("button", name="Ask Virgil about this plan").is_visible()
    if width <= 430:
        dial_box = page.locator(".obs-dial-svg").bounding_box()
        rail_box = page.locator(".obs-dial-events").bounding_box()
        assert rail_box["y"] < dial_box["y"] + dial_box["height"] * .5
        assert rail_box["x"] > dial_box["x"] + dial_box["width"] * .65
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Internet", exact=False).click()
    assert page.locator(".obs-ticket-title").inner_text() == "Internet"
    assert page.locator(".obs-dial-center-title").inner_text() == "Internet"
    if width == 390 and theme == "dark":
        page.get_by_role("button", name="Ask Virgil about this plan").click()
        assert page.get_by_role("dialog", name="Virgil advisor").is_visible()
        page.get_by_role("button", name="Close advisor", exact=True).click()
        assert not page.get_by_role("dialog", name="Virgil advisor").is_visible()
