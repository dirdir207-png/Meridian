"""Verify the shell change across ALL workspaces, at the level it actually affects.

The change alters shell geometry (shell / canvas / dock), not workspace content,
so it can be verified on every workspace even though only Today has fixture data.
For each workspace: is the dock its own row (static, below the canvas), does the
canvas own scrolling, and is there any horizontal overflow?

Read-only: isolated synthetic preview, no provider, no credentials, no mutation.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8093"

PROBE = """
() => {
  const shell = document.querySelector('[data-meridian-shell]');
  const main = document.querySelector('.m-main');
  const nav = document.querySelector('nav.m-nav');
  const style = (el) => (el ? getComputedStyle(el) : null);
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { top: Math.round(r.top), bottom: Math.round(r.bottom), h: Math.round(r.height) };
  };
  const shellRect = shell ? shell.getBoundingClientRect() : null;
  return {
    shell_height: shellRect ? Math.round(shellRect.height) : null,
    viewport_h: window.innerHeight,
    shell_overflows_viewport: shellRect ? Math.round(shellRect.height) > window.innerHeight + 1 : null,
    nav_position: style(nav) ? style(nav).position : null,
    nav_box: box(nav),
    main_overflow_y: style(main) ? style(main).overflowY : null,
    main_is_scroller: main ? main.scrollHeight > main.clientHeight + 1 : null,
    document_scrolls: document.documentElement.scrollHeight > window.innerHeight + 1,
    horizontal_overflow: document.documentElement.scrollWidth - window.innerWidth,
    nav_overlaps_main: (() => {
      if (!nav || !main) return null;
      const n = nav.getBoundingClientRect(), m = main.getBoundingClientRect();
      return n.top < m.bottom - 1;
    })(),
  };
}
"""

with sync_playwright() as driver:
    browser = driver.chromium.launch()
    out = {}
    for workspace in ("today", "plan", "activity", "accounts"):
        per_vp = {}
        for label, w, h, dpr in (("mobile-air", 420, 912, 3), ("mobile", 430, 932, 3), ("mobile-small", 390, 844, 3)):
            context = browser.new_context(
                viewport={"width": w, "height": h}, device_scale_factor=dpr,
                color_scheme="dark", reduced_motion="reduce",
            )
            page = context.new_page()
            page.goto(f"{BASE}/meridian?workspace={workspace}", wait_until="networkidle")
            page.wait_for_timeout(600)
            per_vp[label] = page.evaluate(PROBE)
            context.close()
        out[workspace] = per_vp
    browser.close()

print(json.dumps(out, indent=2))
