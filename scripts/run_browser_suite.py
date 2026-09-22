#!/usr/bin/env python3
"""Run the browser suite ONE FILE PER PROCESS, and aggregate the verdict.

WHY THIS EXISTS INSTEAD OF A PLAIN `pytest tests/browser/`
---------------------------------------------------------
A single pytest process cannot run the browser directory, and it is NOT a defect in this
repository's tests. pytest-playwright's `page` fixture leaves an asyncio event loop RUNNING
after the first test that uses it -- a do-nothing test that only requests `page` reproduces
it -- so every later test that needs a fresh sync_playwright dies with "It looks like you are
using Playwright Sync API inside the asyncio loop". A directory run therefore reports a wall
of errors that say nothing about the app.

The mechanism is playwright-python's sync API, which drives its loop inside a greenlet: when
the greenlet is suspended rather than exited, the thread-local "running loop" stays set. That
is why the leak survives a version change at BOTH ends -- pytest 9.0.3 -> 8.4.2 and
pytest-playwright 0.9.0 -> 0.7.0 were each measured, and the loop leaked under all four
combinations. Do not "simplify" this script back into a single invocation, and do not expect a
pin to fix it.

Each file gets a fresh interpreter, so each starts with no loop and the whole directory is
covered. That costs a little start-up time per file and buys a verdict that means something.

Usage:
    APP_URL=http://127.0.0.1:8081 .venv311/bin/python scripts/run_browser_suite.py
    ... --verbose                 # stream each file's pytest output
    ... --tests tests/browser/test_accounts.py   # a subset
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = ROOT / "tests/browser"

#: pytest's summary line, e.g. "3 failed, 5 passed, 1 error in 7.22s".
SUMMARY = re.compile(r"^(?P<body>.*?)\s+in\s+\d+(?:\.\d+)?s", re.M)
COUNT = re.compile(r"(\d+)\s+(passed|failed|error|errors|skipped)")


def _counts(output: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for line in reversed(output.splitlines()):
        match = SUMMARY.match(line.strip())
        if not match:
            continue
        for number, kind in COUNT.findall(match.group("body")):
            key = "error" if kind.startswith("error") else kind
            totals[key] = totals.get(key, 0) + int(number)
        break
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="stream each file's output")
    parser.add_argument("--tests", nargs="*", default=None, help="specific files to run")
    args = parser.parse_args()

    if not os.environ.get("APP_URL"):
        print("APP_URL is required (e.g. APP_URL=http://127.0.0.1:8081)", file=sys.stderr)
        return 2

    files = (
        [Path(p) for p in args.tests]
        if args.tests
        else sorted(p for p in BROWSER_DIR.glob("test_*.py"))
    )
    if not files:
        print("no browser test files found", file=sys.stderr)
        return 2

    grand: dict[str, int] = {}
    failing: list[tuple[Path, str]] = []
    for path in files:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(path), "-q", "-p", "no:randomly"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        if args.verbose:
            print(output)
        counts = _counts(output)
        if result.returncode != 0:
            # The last meaningful line names the failure without dumping the whole traceback.
            tail = [ln for ln in output.splitlines() if ln.strip()][-1:] or ["(no output)"]
            failing.append((path, tail[0]))
        for key, value in counts.items():
            grand[key] = grand.get(key, 0) + value
        status = "ok  " if result.returncode == 0 else "FAIL"
        rendered = ", ".join(f"{v} {k}" for k, v in sorted(counts.items())) or "no summary"
        print(f"{status} {path.name:48} {rendered}", flush=True)

    print("-" * 72)
    print("TOTAL " + (", ".join(f"{v} {k}" for k, v in sorted(grand.items())) or "nothing ran"))
    if failing:
        print(f"\n{len(failing)} file(s) failed:")
        for path, line in failing:
            print(f"  {path.name}: {line}")
        return 1
    print("all browser files passed, each in its own process")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
