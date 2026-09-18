"""Visibility-aware occlusion test for the dock overlap.

Rect intersection cannot tell occlusion from clipping, because both produce
identical rects. This probe decides it properly:

  1. find the element that actually scrolls the control (its scrollable ancestor)
  2. compute the control's PAINTED portion = control rect ∩ that scroller's
     visible client box
  3. if that portion is empty, the control is simply not painted (below the fold)
     -> nothing can be occluded
  4. otherwise hit-test the centre of the painted portion; if elementFromPoint
     returns something else, the control is painted and then covered -> OCCLUDED

Run it before and after a candidate fix and compare the verdict.
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
  const scrollableAncestor = (el) => {
    let node = el.parentElement;
    while (node && node !== document.documentElement) {
      const s = getComputedStyle(node);
      if (/(auto|scroll|hidden)/.test(s.overflowY) && node.scrollHeight > node.clientHeight + 1) {
        return node;
      }
      node = node.parentElement;
    }
    return document.scrollingElement || document.documentElement;
  };

  const control = document.querySelector('[data-open-advisor].obs-control');
  if (!control) return { error: 'no [data-open-advisor].obs-control' };

  const scroller = scrollableAncestor(control);
  const cr = control.getBoundingClientRect();
  const sr = scroller.getBoundingClientRect();

  // The visible client box of the scroller, intersected with the viewport.
  const visTop = Math.max(sr.top, 0);
  const visBottom = Math.min(sr.bottom, window.innerHeight);
  const visLeft = Math.max(sr.left, 0);
  const visRight = Math.min(sr.right, window.innerWidth);

  const paintedTop = Math.max(cr.top, visTop);
  const paintedBottom = Math.min(cr.bottom, visBottom);
  const paintedLeft = Math.max(cr.left, visLeft);
  const paintedRight = Math.min(cr.right, visRight);
  const paintedPx = Math.max(0, paintedBottom - paintedTop) * Math.max(0, paintedRight - paintedLeft);

  const scrollerId = scroller === document.scrollingElement ? 'document' : (scroller.className || scroller.tagName);

  if (paintedPx <= 0) {
    return {
      scroller: scrollerId,
      control: { y: Math.round(cr.y), bottom: Math.round(cr.bottom), h: Math.round(cr.height) },
      painted_px: 0,
      verdict: 'NOT_PAINTED (below fold / clipped)',
    };
  }

  const x = Math.round((paintedLeft + paintedRight) / 2);
  const y = Math.round((paintedTop + paintedBottom) / 2);
  const top = document.elementFromPoint(x, y);
  const hitsSelf = !!(top && (control === top || control.contains(top)));

  return {
    scroller: scrollerId,
    control: { y: Math.round(cr.y), bottom: Math.round(cr.bottom), h: Math.round(cr.height) },
    painted_px: Math.round(paintedPx),
    painted: { top: Math.round(paintedTop), bottom: Math.round(paintedBottom) },
    sample: { x, y },
    topElement: top ? (top.className || top.tagName) : null,
    verdict: hitsSelf ? 'PAINTED_AND_HITTABLE (not occluded)' : 'OCCLUDED (painted then covered)',
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
        page.wait_for_selector(".obs-event-item", timeout=15000)
        page.wait_for_function("() => document.querySelectorAll('.obs-event-item').length >= 2",
                               timeout=15000)
        page.evaluate("() => document.fonts && document.fonts.ready")
        page.wait_for_timeout(400)
        results[label] = page.evaluate(PROBE)
        context.close()
    browser.close()

print(json.dumps(results, indent=2))
