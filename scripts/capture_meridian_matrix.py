"""Capture Meridian's governed visual matrix and emit validated metadata."""
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

from playwright.sync_api import sync_playwright

from tests.browser.capture_contract import (
    CAPTURE_MATRIX,
    THEMES,
    CaptureMetadata,
    validate_metadata,
)
from tests.browser.conftest import WORKSPACES, login


def _git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def capture_matrix(
    *,
    app_url: str,
    output: Path,
    concept_dir: Path,
    fixture: str,
    frozen_clock: str,
    full_page: bool = True,
) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    records = []
    commit = _git_commit()
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        try:
            for viewport_name, viewport in CAPTURE_MATRIX.items():
                for theme in THEMES:
                    context = browser.new_context(
                        viewport={
                            "width": viewport["width"],
                            "height": viewport["height"],
                        },
                        device_scale_factor=viewport["dpr"],
                        color_scheme=theme,
                        reduced_motion="reduce",
                    )
                    page = context.new_page()
                    login(page, app_url)
                    for workspace in WORKSPACES:
                        page.goto(f"{app_url}/meridian?workspace={workspace}")
                        page.wait_for_load_state("networkidle", timeout=15000)
                        page.evaluate("() => document.fonts && document.fonts.ready")
                        page.add_style_tag(
                            content="*{animation:none!important;transition:none!important;caret-color:transparent!important}"
                        )
                        page.wait_for_function(
                            "(ws) => !document.querySelector(`[data-workspace-section='${ws}'] [aria-busy='true']`)",
                            arg=workspace,
                            timeout=12000,
                        )
                        current = output / f"{workspace}-{viewport_name}-{theme}.png"
                        page.screenshot(path=str(current), full_page=full_page)
                        metadata = CaptureMetadata(
                            concept_path=str(concept_dir / f"{workspace}.png"),
                            current_path=str(current),
                            viewport=viewport_name,
                            theme=theme,
                            fixture=fixture,
                            frozen_clock=frozen_clock,
                            ui_state=f"{workspace}:default",
                            full_page=full_page,
                            commit=commit,
                            captured_at=datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z"),
                            dpr=viewport["dpr"],
                        ).to_dict()
                        validate_metadata(metadata)
                        records.append(metadata)
                    context.close()
        finally:
            browser.close()
    manifest = output / "manifest.json"
    manifest.write_text(json.dumps({"captures": records}, indent=2) + "\n")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concept-dir", type=Path, required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--frozen-clock", required=True)
    args = parser.parse_args()
    capture_matrix(**vars(args))


if __name__ == "__main__":
    main()
