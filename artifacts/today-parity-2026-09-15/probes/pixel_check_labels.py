"""Objective pixel check of the dial day labels in the captured PNGs.

The vision reading said '8 TUE' was still washed out after the CSS change, while
the computed style said rgb(91,61,22). Those cannot both be right, so measure the
pixels: for each label region, report the darkest pixel (the glyph ink) and the
modal background, and the luminance ratio between them.

This is a diagnostic on the ARTEFACT, not the acceptance method.
"""

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

LABELS = {
    "8 Tue (is-today)": (350, 790),
    "11 Fri (is-selected)": (448, 423),
    "14 Mon": (815, 522),
    "16 Wed": (815, 790),
}


def luminance(rgb):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def analyse(path, box=26):
    image = Image.open(path).convert("RGB")
    out = {}
    for name, (cx, cy) in LABELS.items():
        pixels = [
            image.getpixel((x, y))
            for x in range(max(0, cx - box), min(image.width, cx + box))
            for y in range(max(0, cy - box), min(image.height, cy + box))
        ]
        if not pixels:
            out[name] = None
            continue
        darkest = min(pixels, key=luminance)
        lightest = max(pixels, key=luminance)
        # The glyph ink is the extreme that is NOT the background; background is
        # the most common value in the patch.
        common = max(set(pixels), key=pixels.count)
        ink = darkest if luminance(common) > 0.5 else lightest
        out[name] = {
            "background_modal": common,
            "ink_extreme": ink,
            "ratio": round(ratio(ink, common), 2),
        }
    return out


for theme in ("light", "dark"):
    for tag, directory in (
        ("baseline", "artifacts/today-parity-2026-09-15"),
        ("after-fix", "artifacts/today-labels-fix-2026-09-15"),
    ):
        path = ROOT / directory / f"today-desktop-{theme}-viewport.png"
        if not path.is_file():
            continue
        print(f"=== {theme} / {tag} ===")
        for name, data in analyse(path).items():
            if data is None:
                print(f"  {name:22} (no pixels)")
                continue
            print(
                f"  {name:22} bg={data['background_modal']} ink={data['ink_extreme']} "
                f"contrast={data['ratio']}"
            )
        print()
