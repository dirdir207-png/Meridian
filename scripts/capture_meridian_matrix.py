"""Capture Meridian's governed visual matrix and emit validated metadata."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

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

CONCEPT_FILES = {
    "today": "01-today.png",
    "plan": "02-plan.png",
    "activity": "03-activity.png",
    "accounts": "04-accounts.png",
}

_FREEZE_SCRIPT = r"""
(value => {
  const frozen = new Date(value).valueOf();
  const NativeDate = Date;
  class FrozenDate extends NativeDate {
    constructor(...args) { super(...(args.length ? args : [frozen])); }
    static now() { return frozen; }
  }
  window.Date = FrozenDate;
  window.setInterval = () => 0;
  window.clearInterval = () => {};
})(%s);
"""


def _validate_capture_target(app_url: str, fixture: str, frozen_clock: str) -> None:
    parsed = urlparse(app_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("app_url must be an absolute HTTP(S) URL")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("capture runner only accepts an isolated loopback preview")
    if not fixture.strip():
        raise ValueError("fixture is required")
    datetime.fromisoformat(frozen_clock.replace("Z", "+00:00"))


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
    _validate_capture_target(app_url, fixture, frozen_clock)
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
                    context.add_init_script(_FREEZE_SCRIPT % json.dumps(frozen_clock))
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
                        base = output / f"{workspace}-{viewport_name}-{theme}"
                        viewport_capture = base.with_name(base.name + "-viewport.png")
                        page.screenshot(path=str(viewport_capture), full_page=False)
                        current = viewport_capture
                        artifacts = [viewport_capture]
                        if full_page:
                            full_capture = base.with_name(base.name + "-full.png")
                            page.screenshot(path=str(full_capture), full_page=True)
                            current = full_capture
                            artifacts.append(full_capture)
                        metadata = CaptureMetadata(
                            concept_path=str(concept_dir / CONCEPT_FILES[workspace]),
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
                        metadata["artifacts"] = [str(path) for path in artifacts]
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
