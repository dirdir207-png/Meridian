"""Is the Today page stable enough for position assertions at all?

Two settled probes disagreed by ~250px on the same element. Before trusting any
position claim, sample the same values repeatedly across time in ONE navigation
and see whether they move.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

APP_URL = "http://127.0.0.1:8093/"

SAMPLE = """
() => {
  const c = document.querySelector('.obs-control');
  return {
    scrollY: Math.round(window.scrollY),
    docH: document.documentElement.scrollHeight,
    events: document.querySelectorAll('.obs-event-item').length,
    controlY: c ? Math.round(c.getBoundingClientRect().y) : null,
    isc: document.scrollingElement === document.documentElement ? 'html' : 'body',
  };
}
"""

with sync_playwright() as driver:
    browser = driver.chromium.launch()
    context = browser.new_context(
        viewport={"width": 420, "height": 912}, device_scale_factor=3,
        color_scheme="dark", reduced_motion="reduce",
    )
    page = context.new_page()
    page.goto(APP_URL, wait_until="networkidle")
    page.wait_for_selector(".obs-event-item", timeout=15000)
    page.wait_for_function("() => document.querySelectorAll('.obs-event-item').length >= 2", timeout=15000)
    page.evaluate("() => document.fonts && document.fonts.ready")

    samples = []
    for _ in range(10):
        samples.append(page.evaluate(SAMPLE))
        page.wait_for_timeout(500)
    context.close()
    browser.close()

print(json.dumps(samples, indent=2))
ys = [s["controlY"] for s in samples if s["controlY"] is not None]
print("distinct controlY:", sorted(set(ys)))
print("distinct scrollY:", sorted({s["scrollY"] for s in samples}))
print("distinct docH:", sorted({s["docH"] for s in samples}))
