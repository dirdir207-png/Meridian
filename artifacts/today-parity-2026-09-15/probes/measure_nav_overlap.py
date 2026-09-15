"""Test the mobile Virgil/nav overlap properly.

The earlier attempt used the wrong nav selector and found nothing, which is not
evidence. The nav is `nav.m-nav` and is `position: fixed` at mobile, so the test
must also consider the scrolled state, where a fixed bar overlays flow content.

Read-only: synthetic preview, no provider, no mutation.
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
  const navPos = nav ? getComputedStyle(nav).position : null;

  const controls = [...document.querySelectorAll('[data-open-advisor]')].map((el) => ({
    cls: el.className,
    rect: rect(el),
    visible: !!(el.offsetWidth || el.offsetHeight),
  }));

  const vh = window.innerHeight;
  const onScreen = controls.filter((c) => c.visible && c.rect.bottom > 0 && c.rect.y < vh);

  return {
    viewport_h: vh,
    nav: navRect,
    nav_position: navPos,
    nav_overlays_content: navPos === 'fixed',
    overlaps: navRect ? onScreen.filter((c) => overlaps(c.rect, navRect)).map((c) => c.cls) : [],
    closest_gap: navRect && onScreen.length
      ? Math.min(...onScreen.map((c) => navRect.y - c.rect.bottom))
      : null,
    controls: controls.filter((c) => c.visible),
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
        entry = {"top": page.evaluate(PROBE)}
        # Scrolled to the bottom is where a fixed bar most often collides.
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(250)
        entry["bottom"] = page.evaluate(PROBE)
        results[label] = entry
        context.close()
    browser.close()

print(json.dumps(results, indent=2))
