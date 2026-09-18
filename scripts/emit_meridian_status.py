#!/usr/bin/env python3
"""Emit one sanitized Meridian status event."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meridian.status_emitter import (
    StatusEmitterError,
    build_status_event,
    canonical_event_json,
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed-at")
    args = parser.parse_args()
    try:
        sources = {
            "tasks": json.loads((ROOT / "docs/project/MERIDIAN_OS_TASKS.json").read_text()),
            "coordination": (ROOT / "docs/project/AGENT_COORDINATION.md").read_text(),
            "current_status": (ROOT / "docs/project/CURRENT_STATUS.md").read_text(),
            "roadmap": (ROOT / "docs/project/MERIDIAN_ROADMAP.md").read_text(),
            "decisions": (ROOT / "docs/project/MERIDIAN_DECISIONS.md").read_text(),
        }
        remote = _git("config", "--get", "remote.origin.url") or "ORSC"
        repository = re.sub(r"\.git$", "", remote.rsplit("/", 1)[-1].rsplit(":", 1)[-1])
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", repository):
            repository = "ORSC"
        event = build_status_event(sources=sources, git={"repository": repository, "branch": _git("branch", "--show-current"), "revision": _git("rev-parse", "HEAD")}, observed_at=args.observed_at)
        print(canonical_event_json(event))
        return 0
    except (OSError, subprocess.CalledProcessError, ValueError, StatusEmitterError):
        print(json.dumps({"schema_version": 1, "event_id": "meridian-status-unavailable", "health": "degraded", "producer": {"name": "orsc-meridian-status-emitter", "version": "1"}}, separators=(",", ":")))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
