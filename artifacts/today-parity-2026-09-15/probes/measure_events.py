"""Measure the geometry INSIDE one Today event card on the synthetic preview.

The alignment complaint is about unused width, so measure the card and each of
its descendants rather than estimating from a screenshot. Read-only.
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
  const box = (el) => {
    const r = el.getBoundingClientRect();
    return {
      tag: el.tagName.toLowerCase(),
      cls: (typeof el.className === 'string' ? el.className : ''),
      x: Math.round(r.x), right: Math.round(r.right), w: Math.round(r.width),
      text: (el.textContent || '').trim().slice(0, 30),
    };
  };
  const list = document.querySelector('.obs-dial-events .obs-event-list')
            || document.querySelector('.obs-dial-events ul');
  const card = list ? list.querySelector('li') : null;
  const events = document.querySelector('.obs-dial-events');
  const panel = document.querySelector('[data-observatory-dial] .obs-dial-panel');
  return {
    panel: panel ? box(panel) : null,
    events_column: events ? box(events) : null,
    list: list ? box(list) : null,
    card: card ? box(card) : null,
    card_children: card ? [...card.querySelectorAll('*')].slice(0, 10).map(box) : [],
    doc_width: document.documentElement.clientWidth,
  };
}
"""

with sync_playwright() as driver:
    browser = driver.chromium.launch()
    results = {}
    for label, width, height, dpr in (("desktop", 1440, 900, 1), ("mobile", 430, 932, 3)):
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
