"""Settle the dock-overlap gap: is the inline advisor control reachable, or truly occluded?

The rect-intersection probe could not tell occlusion from clipping, because both
produce identical geometry. This probe answers the question that actually
matters:

  * Is the control hit-testable at its own centre (elementFromPoint returns the
    control or a descendant)? If yes it is reachable, not obscured.
  * Can it be brought fully clear of the dock by scrolling? If yes, then the
    initial overlap is a transient scroll artefact rather than a permanent
    occlusion, because content passing under a sticky bar is normal.
  * Is there a scroll position at which it is visible AND hit-testable?

Read-only: synthetic preview, no provider, no credentials, no mutation.
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
  const nav = document.querySelector('nav.m-nav');
  const navRect = nav ? nav.getBoundingClientRect() : null;

  const hitTest = (el) => {
    const r = el.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2);
    const y = Math.round(r.y + r.height / 2);
    const vw = window.innerWidth, vh = window.innerHeight;
    if (x < 0 || y < 0 || x >= vw || y >= vh) {
      return { inViewport: false, x, y, topElement: null, hitsSelf: false };
    }
    const top = document.elementFromPoint(x, y);
    return {
      inViewport: true, x, y,
      topElement: top ? (top.className || top.tagName) : null,
      hitsSelf: !!(top && (el === top || el.contains(top))),
    };
  };

  const control = document.querySelector('.obs-control');
  if (!control) return { error: 'no .obs-control' };

  const initial = {
    rect: (() => { const r = control.getBoundingClientRect();
      return { y: Math.round(r.y), bottom: Math.round(r.bottom) }; })(),
    nav: navRect ? { y: Math.round(navRect.y), bottom: Math.round(navRect.bottom) } : null,
    hit: hitTest(control),
  };

  // Bring it fully into view the way a user would, then re-test.
  control.scrollIntoView({ block: 'center' });
  const afterScroll = {
    rect: (() => { const r = control.getBoundingClientRect();
      return { y: Math.round(r.y), bottom: Math.round(r.bottom) }; })(),
    nav: navRect ? { y: Math.round(navRect.y), bottom: Math.round(navRect.bottom) } : null,
    hit: hitTest(control),
    clearsDock: navRect ? (control.getBoundingClientRect().bottom <= navRect.y) : null,
  };

  return { viewport_h: window.innerHeight, initial, afterScroll };
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
