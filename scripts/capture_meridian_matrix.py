"""Capture Meridian's governed visual matrix and emit validated metadata."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
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


def _validate_workspaces(workspaces: Sequence[str] | None) -> list[str]:
    """Resolve the requested workspaces against the governed set.

    Narrowing to one workspace is how Track D accepts a surface at a time; the
    default remains every governed workspace, so a full run is unchanged.
    """
    # Distinguish "not specified" (None -> every governed workspace) from an
    # explicitly empty list, which is a caller error rather than "all".
    selected = list(WORKSPACES) if workspaces is None else list(workspaces)
    # "virgil" is not a fifth workspace -- BUILD_HANDOFF.md forbids adding one -- it is
    # the advisor PANEL, which opens over Today. It is a capture target so the surface
    # can produce governed evidence (a validated manifest with overflow and console
    # checks) rather than a hand-taken screenshot that nothing verifies.
    supported = [*WORKSPACES, "settings", "virgil"]
    unknown = [name for name in selected if name not in supported]
    if unknown:
        raise ValueError(
            f"unknown workspace(s): {', '.join(unknown)}; "
            f"governed workspaces are {', '.join(supported)}"
        )
    if not selected:
        raise ValueError("at least one workspace is required")
    return selected


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
    workspaces: Sequence[str] | None = None,
    skip_login: bool = False,
    ui_state: str = "default",
    ui_state_selector: str | None = None,
    concept_file: str | None = None,
    settings_query: str = "?section=connections",
) -> list[dict]:
    """Capture the governed matrix.

    ``workspaces`` narrows the run (Track D accepts one workspace at a time);
    default is every governed workspace. ``concept_file`` overrides the concept
    filename inside ``concept_dir`` for a run whose authority is not the default
    draft set -- the 2026-09-18 extension, for instance, names its concepts
    ``timeline``/``review``/``settings``/``virgil`` rather than 01-04. Recording a
    path that does not exist would make the evidence unauditable, so the caller
    can now name the image it actually compared against. ``skip_login`` targets the ISOLATED
    SYNTHETIC preview (`scripts/preview_observatory_dial.py`), which
    deliberately has no authentication, reads no .env, holds no credentials and
    makes no provider call. That is the correct target for fidelity captures,
    because the specification requires fixtures only and forbids live bank data:
    the full runtime (`run_preview.py`) loads .env and starts a Crew sync loop, so
    it must NOT be used to produce fidelity evidence. ``settings_query`` selects WHICH
    Settings surface the ``settings`` workspace captures: `?section=...` for a detail
    section, or the empty string for the HUB, which is the no-section landing page.
    It defaults to Connections so an existing run is unchanged.
    """
    _validate_capture_target(app_url, fixture, frozen_clock)
    selected = _validate_workspaces(workspaces)
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
                    # Pin the theme authoritatively BEFORE any app script runs.
                    #
                    # Emulating `color_scheme` alone was not enough, and the resulting
                    # captures were wrong in a way that survived review: theme.js resolves
                    # localStorage first and only falls back to prefers-color-scheme, and
                    # this context is reused across every workspace in the loop below.
                    # So once the app had written `meridian-theme`, every later page load
                    # in that context kept that stored value, and the "light" pass rendered
                    # the dark theme for every workspace after the first. The images were
                    # labelled light and looked plausible side by side, so a luminance
                    # check was needed to catch it. `THEMES` is the same value the harness
                    # passes as `color_scheme`, so the two can no longer disagree.
                    context.add_init_script(
                        "try { localStorage.setItem('meridian-theme', %s); } catch (e) {}"
                        % json.dumps(theme)
                    )
                    page = context.new_page()
                    console_errors: list[str] = []
                    page.on("pageerror", lambda error: console_errors.append(str(error)))
                    if not skip_login:
                        login(page, app_url)
                    for workspace in selected:
                        console_errors.clear()
                        # The Virgil panel is an overlay, so its capture loads the
                        # workspace it opens over and then opens the panel below.
                        underlying = "today" if workspace == "virgil" else workspace
                        page.goto(
                            f"{app_url}/meridian/settings{settings_query}"
                            if workspace == "settings"
                            else f"{app_url}/meridian?workspace={underlying}"
                        )
                        page.wait_for_load_state("networkidle", timeout=15000)
                        page.evaluate("() => document.fonts && document.fonts.ready")
                        page.add_style_tag(
                            content="*{animation:none!important;transition:none!important;caret-color:transparent!important}"
                        )
                        page.wait_for_function(
                            "(ws) => !document.querySelector(ws === 'settings' ? '[data-settings-shell] [aria-busy=true]' : `[data-workspace-section='${ws}'] [aria-busy='true']`)",
                            arg="settings" if workspace == "settings" else underlying,
                            timeout=12000,
                        )
                        if workspace == "virgil":
                            # Open it the way the shell's own [data-open-advisor]
                            # buttons do, so the capture exercises the real entry
                            # point rather than a test-only hook.
                            page.evaluate(
                                "() => window.advisorSetOpen && window.advisorSetOpen(true)"
                            )
                            page.wait_for_selector("#advisor-panel[data-open]", timeout=8000)
                            page.wait_for_timeout(700)
                        # A concept may depict a non-default UI state, and comparing
                        # one state against another is meaningless. Drive the state
                        # explicitly and record what was actually captured, rather
                        # than recording a constant ":default" that can silently
                        # misdescribe the image.
                        if ui_state_selector:
                            target = page.query_selector(ui_state_selector)
                            if target is None:
                                raise ValueError(
                                    f"ui_state_selector matched nothing: {ui_state_selector}"
                                )
                            target.click()
                            page.wait_for_load_state("networkidle", timeout=15000)
                            page.wait_for_timeout(150)
                        # Horizontal overflow is the primary responsive defect signal,
                        # so it is recorded rather than inferred from the image.
                        overflow = page.evaluate(
                            "document.documentElement.scrollWidth - window.innerWidth"
                        )
                        base = output / f"{workspace}-{viewport_name}-{theme}"
                        viewport_capture = base.with_name(base.name + "-viewport.png")
                        page.screenshot(path=str(viewport_capture), full_page=False)
                        current = viewport_capture
                        artifacts = [viewport_capture]
                        if full_page:
                            full_capture = base.with_name(base.name + "-full.png")
                            # The mobile shell pins itself to one viewport and scrolls
                            # an inner canvas, so the DOCUMENT is only viewport-tall and
                            # Playwright's full_page would capture no more than the
                            # viewport. Unpin it for the full shot, then remove the
                            # override so the captured runtime CSS is untouched.
                            unpin = page.add_style_tag(
                                content=(
                                    "[data-meridian-shell]{height:auto !important;"
                                    "min-height:0 !important;overflow:visible !important}"
                                    ".m-main{overflow:visible !important}"
                                )
                            )
                            page.wait_for_timeout(120)
                            page.screenshot(path=str(full_capture), full_page=True)
                            unpin.evaluate("el => el.remove()")
                            current = full_capture
                            artifacts.append(full_capture)
                        metadata = CaptureMetadata(
                            concept_path=str(
                                concept_dir / (concept_file or CONCEPT_FILES[workspace])
                            ),
                            current_path=str(current),
                            viewport=viewport_name,
                            theme=theme,
                            fixture=fixture,
                            frozen_clock=frozen_clock,
                            ui_state=f"{workspace}:{ui_state}",
                            full_page=full_page,
                            commit=commit,
                            captured_at=datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z"),
                            dpr=viewport["dpr"],
                        ).to_dict()
                        validate_metadata(metadata)
                        metadata["artifacts"] = [str(path) for path in artifacts]
                        metadata["overflow"] = overflow
                        metadata["console_errors"] = list(console_errors)
                        metadata["ui_state_selector"] = ui_state_selector
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
    parser.add_argument(
        "--workspaces",
        nargs="+",
        default=None,
        help="workspaces to capture (default: all governed workspaces)",
    )
    parser.add_argument(
        "--ui-state",
        default="default",
        help="label recorded as the captured UI state",
    )
    parser.add_argument(
        "--ui-state-selector",
        default=None,
        help="CSS selector clicked before capture to reach a non-default state",
    )
    parser.add_argument(
        "--concept-file",
        default=None,
        help=(
            "concept filename inside --concept-dir to record as the comparison "
            "authority (default: the draft-set mapping for each workspace)"
        ),
    )
    parser.add_argument(
        "--settings-query",
        default="?section=connections",
        help=(
            "query string appended to /meridian/settings for the settings workspace; "
            "pass an empty string to capture the Settings HUB (default: ?section=connections)"
        ),
    )
    parser.add_argument(
        "--skip-login",
        action="store_true",
        help="target the isolated synthetic preview, which has no authentication",
    )
    args = parser.parse_args()
    capture_matrix(**vars(args))


if __name__ == "__main__":
    main()
