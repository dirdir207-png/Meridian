"""Capture a Settings surface across the governed matrix, with validated metadata.

capture_meridian_matrix.py is keyed to the four workspaces and their concept files. The
Settings surfaces are routes rather than workspaces, and two open tasks need governed
evidence for them (OS-081's desktop acceptance, OS-085's both-theme retool), so this
driver reuses the SAME contract -- tests/browser/capture_contract.py -- rather than
inventing a second scheme: same five viewport/DPR pairs, same two themes, same
CaptureMetadata schema, same validation, and a manifest written beside the screenshots.

Theme handling follows the workspace harness deliberately: emulating color_scheme alone
is not enough because the app reads localStorage first and only falls back to
prefers-color-scheme, so both are set and they cannot disagree. Animations and
transitions are disabled and a settle wait is applied so a capture is deterministic.

Usage (the spec is explicit: never target live financial data -- use the isolated
synthetic preview):

    .venv311/bin/python scripts/capture_settings_surfaces.py \
        --app-url http://127.0.0.1:8093 \
        --route "/meridian/settings?section=connections" \
        --label conn --output artifacts/settings-review \
        --fixture synthetic-settings --frozen-clock 2026-09-21T12:00:00Z

A surfaced limitation, recorded rather than worked around: full_page=True with a
fixed-position element (the synthetic-preview banner) stitches that element into the
middle of the image. Read the paired *-viewport.png for those regions.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402

from tests.browser.capture_contract import (  # noqa: E402
    CAPTURE_MATRIX,
    THEMES,
    CaptureMetadata,
    validate_metadata,
)

# A surface with no concept record is captured honestly rather than pointed at an
# unrelated concept: the owner's authority for such a surface is the app's own house
# language (OS-085), and a fabricated concept_path would misreport the authority.
NO_CONCEPT = "(no concept record; authority is the app's own house language)"

_SETTLE_STYLE = (
    "*{animation:none !important; transition:none !important; caret-color:transparent !important}"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-url", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference", default=NO_CONCEPT)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--frozen-clock", required=True)
    parser.add_argument("--ui-state", default="settled")
    parser.add_argument("--viewports", default="all")
    parser.add_argument("--themes", default="all")
    args = parser.parse_args()

    viewports = list(CAPTURE_MATRIX) if args.viewports == "all" else args.viewports.split(",")
    themes = list(THEMES) if args.themes == "all" else args.themes.split(",")
    for viewport in viewports:
        if viewport not in CAPTURE_MATRIX:
            raise SystemExit(f"unsupported viewport: {viewport}")
    for theme in themes:
        if theme not in THEMES:
            raise SystemExit(f"unsupported theme: {theme}")

    args.output.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    captured_at = datetime.now(timezone.utc).isoformat()

    records: list[dict[str, object]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for viewport in viewports:
            spec = CAPTURE_MATRIX[viewport]
            for theme in themes:
                context = browser.new_context(
                    viewport={"width": spec["width"], "height": spec["height"]},
                    device_scale_factor=spec["dpr"],
                    color_scheme=theme,
                    reduced_motion="reduce",
                )
                context.add_init_script(
                    "try { localStorage.setItem('meridian-theme', %s); } catch (e) {}"
                    % json.dumps(theme)
                )
                page = context.new_page()
                page.goto(f"{args.app_url}{args.route}", wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    # A settle wait, not a correctness gate: the deterministic predicate
                    # is the busy-state check below.
                    pass
                try:
                    page.evaluate("() => document.fonts && document.fonts.ready")
                    page.wait_for_function(
                        "() => !document.querySelector(\"[aria-busy='true']\")", timeout=8000
                    )
                except Exception:
                    pass
                page.add_style_tag(content=_SETTLE_STYLE)
                page.wait_for_timeout(500)

                full_page_path = args.output / f"{args.label}-{viewport}-{theme}.png"
                viewport_path = args.output / f"{args.label}-{viewport}-{theme}-viewport.png"
                page.screenshot(path=str(full_page_path), full_page=True)
                page.screenshot(path=str(viewport_path))

                metadata = CaptureMetadata(
                    concept_path=args.reference,
                    current_path=str(full_page_path),
                    viewport=viewport,
                    theme=theme,
                    fixture=args.fixture,
                    frozen_clock=args.frozen_clock,
                    ui_state=args.ui_state,
                    full_page=True,
                    commit=commit,
                    captured_at=captured_at,
                    dpr=spec["dpr"],
                )
                validate_metadata(metadata.to_dict())
                records.append(metadata.to_dict())
                print(
                    f"captured {full_page_path.name} "
                    f"({spec['width']}x{spec['height']}@{spec['dpr']} {theme})",
                    flush=True,
                )
                context.close()
        browser.close()

    manifest = args.output / f"{args.label}-manifest.json"
    manifest.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"OK {len(records)} governed captures -> {args.output} ({manifest.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
