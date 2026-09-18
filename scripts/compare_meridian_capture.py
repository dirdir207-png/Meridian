"""Generate side-by-side concept/capture comparison artifacts.

The capture specification requires side-by-side and, where tooling permits,
overlay/difference artifacts for every concept-fidelity comparison, and metadata
recording concept path, current path, viewport, DPR, theme, fixture, frozen clock,
UI state, fullPage, commit and capture date.

Comparisons are width-normalised and top-aligned rather than stretched to a common
height: the concept is a tall mobile composition and the capture is a full page of
different length, and the specification is explicit that a different page length is
not a design defect. Stretching to equal height would distort typography and invent
a mismatch that does not exist.

Read-only: reads PNGs and writes comparison artifacts only. No app import, no
network, no database, no credential.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

GUTTER = 24
LABEL_H = 44
BG = (24, 32, 46)


def _load_width_normalised(path: Path, width: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = width / image.width
    return image.resize((width, max(1, round(image.height * ratio))), Image.LANCZOS)


def _rel(path: Path) -> str:
    """Repository-relative label, tolerating a relative input path."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def build(concept: Path, capture: Path, out: Path, *, width: int, label: str) -> dict:
    left = _load_width_normalised(concept, width)
    right = _load_width_normalised(capture, width)
    height = max(left.height, right.height)

    canvas = Image.new(
        "RGB", (width * 2 + GUTTER, height + LABEL_H), BG
    )
    canvas.paste(left, (0, LABEL_H))
    canvas.paste(right, (width + GUTTER, LABEL_H))

    draw = ImageDraw.Draw(canvas)
    draw.text((8, 14), f"CONCEPT  {concept.name}", fill=(238, 228, 207))
    draw.text((width + GUTTER + 8, 14), f"CURRENT  {capture.name}", fill=(238, 228, 207))
    draw.text((8, height + LABEL_H - 18), label, fill=(183, 184, 203))

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return {
        "concept": _rel(concept),
        "current": _rel(capture),
        "artifact": _rel(out),
        "normalised_width": width,
        "concept_scaled": list(left.size),
        "current_scaled": list(right.size),
        "page_length_differs": left.height != right.height,
        "note": (
            "Width-normalised and top-aligned. A differing page length is expected "
            "and is not a design defect."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--width", type=int, default=560)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    record = build(args.concept, args.capture, args.out, width=args.width, label=args.label)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
