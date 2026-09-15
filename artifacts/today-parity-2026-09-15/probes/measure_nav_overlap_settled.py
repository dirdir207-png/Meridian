"""Re-measure the dock overlap WITH proper settling.

The first version waited only for `.obs-dial-center-amount`, which exists before
the event rail finishes rendering. The page therefore kept growing after the
measurement, and two runs disagreed by ~250px — so the earlier "reproduced gap"
was not trustworthy. Wait for the rail to be populated, fonts, and network idle
before measuring.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

APP_URL = "http://127.0.0.1:8093/"

PROBE = """
() => {
  const rect = (el) => {
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), right: Math.round(r.right),
             bottom: Math.round(r.bottom), w: Math.round(r.width), h: Math.round(r.height) };
  };
  const overlaps = (a, b) => a && b && a.x < b.right && b.x < a.right && a.y < b.bottom && b.y < a.bottom;

  const nav = document.querySelector('nav.m-nav');
  const navRect = nav ? rect(nav) : null;

  const controls = [...document.querySelectorAll('[data-open-advisor]')]
    .filter((el) => el.offsetWidth || el.offsetHeight)
    .map((el) => ({ cls: el.className, rect: rect(el) }));

  const vh = window.innerHeight;
  const onScreen = controls.filter((c) => c.rect.bottom > 0 && c.rect.y < vh);

  return {
    settled_marker: document.querySelectorAll('.obs-event-item').length,
    doc_height: document.documentElement.scrollHeight,
    viewport_h: vh,
    nav: navRect,
    nav_position: nav ? getComputedStyle(nav).position : null,
    overlaps: navRect ? onScreen.filter((c) => overlaps(c.rect, navRect)).map((c) => c.cls) : [],
    closest_gap: navRect && onScreen.length
      ? Math.min(...onScreen.map((c) => navRect.y - c.rect.bottom)) : null,
    controls,
  };
}
"""

with sync_playwright() as driver:
    browser = driver.chromium.launch()
    results = {}
    for label, width, height, dpr in (
        ("mobile-air", 420, 912, 3),
        ("mobile", 430, 932, 3),
        ("mobile-small", 390, 844, 3),
    ):
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=dpr,
            color_scheme="dark",
            reduced_motion="reduce",
        )
        page = context.new_page()
        page.goto(APP_URL, wait_until="networkidle")
        page.wait_for_selector(".obs-dial-center-amount", timeout=15000)
        # The event rail is what keeps growing after the dial centre appears.
        page.wait_for_selector(".obs-event-item", timeout=15000)
        page.wait_for_function("() => document.querySelectorAll('.obs-event-item').length >= 2",
                               timeout=15000)
        page.evaluate("() => document.fonts && document.fonts.ready")
        page.wait_for_timeout(400)
        before = page.evaluate(PROBE)
        page.wait_for_timeout(600)
        after = page.evaluate(PROBE)
        results[label] = {
            "stable": before["doc_height"] == after["doc_height"],
            "first": before,
            "second": after,
        }
        context.close()
    browser.close()

print(json.dumps(results, indent=2))
