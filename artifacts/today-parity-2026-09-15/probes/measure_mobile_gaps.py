"""Measure the two mobile gaps the roadmap lists for Today.

1. "payday amount is a tight fit in the callout at mobile" -> does the amount
   text overflow its container (scrollWidth > clientWidth), or clip?
2. "the inline Virgil control overlaps the bottom navigation on mobile" -> do the
   two bounding boxes intersect?

Measured, not estimated. Read-only: synthetic preview, no provider, no mutation.
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
  const overlaps = (a, b) =>
    a && b && a.x < b.right && b.x < a.right && a.y < b.bottom && b.y < a.bottom;

  // 1. every event amount: does its text overflow the box that holds it?
  const amounts = [...document.querySelectorAll('.obs-event-amount')].map((el) => ({
    text: el.textContent.trim(),
    clientWidth: el.clientWidth,
    scrollWidth: el.scrollWidth,
    overflowPx: el.scrollWidth - el.clientWidth,
    rect: rect(el),
  }));

  // 2. the inline Virgil controls vs the bottom navigation.
  const nav = document.querySelector('.m-bottom-nav, [data-bottom-nav], .m-nav-bottom, nav.m-tabbar');
  const virgils = [...document.querySelectorAll('[data-open-advisor]')]
    .map((el) => ({ cls: el.className, rect: rect(el) }));

  const navRect = nav ? rect(nav) : null;
  const collisions = navRect
    ? virgils.filter((v) => overlaps(v.rect, navRect)).map((v) => v.cls)
    : [];

  return {
    doc_width: document.documentElement.clientWidth,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    amounts,
    nav: navRect,
    virgil_controls: virgils,
    colliding_with_nav: collisions,
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
        results[label] = page.evaluate(PROBE)
        context.close()
    browser.close()

print(json.dumps(results, indent=2))
