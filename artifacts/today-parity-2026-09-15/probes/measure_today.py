"""Measure Today's real layout geometry on the isolated synthetic preview.

Alignment work should be driven by measured boxes, not by estimating positions
from a raster. Read-only: loads the preview, queries getBoundingClientRect, no
mutation, no provider, no credentials.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

APP_URL = "http://127.0.0.1:8093/"

SELECTORS = {
    "viewport": "html",
    "left_rail": ".m-nav, .m-rail, nav",
    "today_layout": ".m-today-layout",
    "today_primary": ".m-today-primary",
    "today_brief": ".m-today-brief",
    "dial_wrap": ".m-observatory-dial-wrap",
    "dial_panel": "[data-observatory-dial] .obs-dial-panel",
    "dial_svg_wrap": ".obs-dial-svg-wrap",
    "dial_events": ".obs-dial-events",
    "event_list": ".obs-event-list--orbit, .obs-event-list",
}


def measure(page, viewport_w):
    out = {}
    for name, selector in SELECTORS.items():
        handle = page.query_selector(selector)
        if handle is None:
            out[name] = None
            continue
        box = handle.bounding_box()
        if box is None:
            out[name] = None
            continue
        out[name] = {
            "x": round(box["x"]),
            "right": round(box["x"] + box["width"]),
            "width": round(box["width"]),
        }
    # The right margin actually left over, which is the alignment complaint.
    if out.get("viewport"):
        doc_w = page.evaluate("document.documentElement.clientWidth")
        out["viewport"]["client_width"] = doc_w
        anchor = out.get("event_list") or out.get("dial_events")
        if anchor:
            out["dead_space_right_of_events"] = doc_w - anchor["right"]
    return out


with sync_playwright() as driver:
    browser = driver.chromium.launch()
    results = {}
    for label, width, height, dpr in (
        ("desktop", 1440, 900, 1),
        ("tablet", 1024, 768, 1),
        ("mobile", 430, 932, 3),
    ):
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=dpr,
            color_scheme="dark",
            reduced_motion="reduce",
        )
        page = context.new_page()
        page.goto(APP_URL, wait_until="networkidle")
        page.wait_for_selector(".obs-dial-center-amount", timeout=10000)
        results[label] = measure(page, width)
        context.close()
    browser.close()

print(json.dumps(results, indent=2))
