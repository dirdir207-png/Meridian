"""Is the dial clipped with no way to reach it, or simply below the fold?

The concept inspection repeatedly notes the dial's lower rim (and its day labels)
being cut by the viewport. That is only a defect if the content cannot be brought
into view. Measure the dial's box, the document height, and whether scrolling
reveals the rim.

Read-only: isolated synthetic preview, no provider, no credentials.
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
  const box = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { top: Math.round(r.top + window.scrollY), bottom: Math.round(r.bottom + window.scrollY),
             h: Math.round(r.height), w: Math.round(r.width) };
  };
  const labels = [...document.querySelectorAll('.obs-dial-day-label')].map((el) => {
    const r = el.getBoundingClientRect();
    return { text: (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 8),
             viewportY: Math.round(r.y), docY: Math.round(r.y + window.scrollY),
             inViewport: r.bottom > 0 && r.top < window.innerHeight };
  });
  return {
    viewport_h: window.innerHeight,
    scrollY: Math.round(window.scrollY),
    doc_height: document.documentElement.scrollHeight,
    scrollable: document.documentElement.scrollHeight > window.innerHeight + 1,
    dial_svg_wrap: box('.obs-dial-svg-wrap'),
    dial_instrument: box('.obs-dial-instrument'),
    labels,
  };
}
"""

with sync_playwright() as driver:
    browser = driver.chromium.launch()
    out = {}
    for label, w, h, dpr in (("desktop", 1440, 900, 1), ("mobile-air", 420, 912, 3)):
        context = browser.new_context(
            viewport={"width": w, "height": h}, device_scale_factor=dpr,
            color_scheme="dark", reduced_motion="reduce",
        )
        page = context.new_page()
        page.goto(APP_URL, wait_until="networkidle")
        page.wait_for_selector(".obs-event-item", timeout=15000)
        page.evaluate("() => document.fonts && document.fonts.ready")
        page.wait_for_timeout(400)
        top = page.evaluate(PROBE)
        # Scroll the dial fully into view and re-check the rim labels.
        page.evaluate("document.querySelector('.obs-dial-svg-wrap').scrollIntoView({block:'end'})")
        page.wait_for_timeout(300)
        scrolled = page.evaluate(PROBE)
        out[label] = {"at_top": top, "scrolled_to_dial": scrolled}
        context.close()
    browser.close()

print(json.dumps(out, indent=2))
