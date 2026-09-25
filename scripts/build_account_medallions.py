#!/usr/bin/env python3
"""Derive Accounts bucket medallions from the delivered Investigator masters (OS-103, trait 2).

WHY A SCRIPT AND NOT A ONE-OFF EDIT. `design/investigator-medallions-2026-09-21/README.md` says the two
masters are complete medallions -- rings, field and centre glyph -- and instructs: "Keep the masters; create
measured delivery derivatives during integration using the project's normal asset process." The normal
process in this repo is a recorded derivation: `key_raster_background.py` did it for the moon and the
hourglass, and `ASSET_MANIFEST.md` carries the command. So this derives, and reports numbers the manifest can
quote, rather than shipping a hand-resized file nobody can reproduce.

WHAT IT CHANGES AND WHY IT IS NEEDED. Each master is 1254x1254 with the medallion occupying only ~80% of the
canvas, i.e. ~10% of transparent padding a side. The handoff is explicit: "Match the VISIBLE DISC size, not
the PNG canvas: these masters include transparent padding." Compositing the canvas into a 52px box would
paint a 42px medallion. So this crops to the visible disc bbox and resamples to the delivery size, which also
takes a 2.0 MB master down to a phone-sized file.

Size: 208x208 = 4x the 52 CSS-pixel disc measured on concept 04, so the art stays sharp on the owner's
DPR-3 phone and on any 2x display, and nothing upscales.

Usage: ./.venv/bin/python scripts/build_account_medallions.py [--write]
Without --write it only reports, which is the default so a stray run cannot rewrite shipped art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "design/investigator-medallions-2026-09-21"
OUT_DIR = ROOT / "static/img/meridian/observatory/accounts"
DELIVERY_PX = 208  # 4x the concept's 52 CSS disc
ALPHA_FLOOR = 12  # the same floor the repo's other raster audits use

# The three buckets concept 04 names, and the delivered master each one takes.
DELIVERED = {
    "compass": SOURCE / "compass-medallion.png",
    "wifi": SOURCE / "wifi-medallion.png",
}


def visible_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    """The disc's own bbox: the transparent padding is not part of the medallion."""
    alpha = image.split()[-1]
    width, height = image.size
    pixels = alpha.load()
    xs = [x for x in range(width) for y in range(0, height, 2) if pixels[x, y] > ALPHA_FLOOR]
    ys = [y for y in range(height) for x in range(0, width, 2) if pixels[x, y] > ALPHA_FLOOR]
    return min(xs), min(ys), max(xs), max(ys)


def report(name: str, source_name: str, before: Image.Image, after: Image.Image, box, dest: Path) -> dict:
    alpha = after.split()[-1]
    total = after.width * after.height
    # histogram bucket 0 is the exact count of fully transparent pixels; a per-pixel sum over the image is
    # both slower and deprecated in current Pillow.
    transparent = alpha.histogram()[0]
    corners = [alpha.getpixel(c) for c in ((0, 0), (after.width - 1, 0), (0, after.height - 1),
                                           (after.width - 1, after.height - 1))]
    digest = hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None
    return {
        "name": name,
        "source": source_name,
        "source_size": list(before.size),
        "visible_bbox": list(box),
        "visible_pct_of_canvas": round((box[2] - box[0] + 1) / before.width * 100, 1),
        "delivery_size": list(after.size),
        "delivery_px_vs_concept": f"{DELIVERY_PX}px = 4x the 52 CSS disc measured on concept 04",
        "transparent_pct": round(transparent / total * 100, 1),
        "corners_alpha": corners,
        "bytes": dest.stat().st_size if dest.exists() else None,
        "sha256": digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the derived files (default: report only)")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, source in DELIVERED.items():
        master = Image.open(source).convert("RGBA")
        box = visible_bbox(master)
        cropped = master.crop((box[0], box[1], box[2] + 1, box[3] + 1))
        # Square it exactly, so a 1.01 aspect master cannot shift the disc off-centre.
        side = max(cropped.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
        delivered = square.resize((DELIVERY_PX, DELIVERY_PX), Image.LANCZOS)
        dest = OUT_DIR / f"{name}-medallion.png"
        if args.write:
            delivered.save(dest, "PNG", optimize=True)
        rows.append(report(name, str(source.relative_to(ROOT)), master, delivered, box, dest))

    print(json.dumps(rows, indent=1))
    if not args.write:
        print("\nreport only -- nothing written. Pass --write to derive the files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
