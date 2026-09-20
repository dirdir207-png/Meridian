"""Launcher scripts must actually be runnable.

Regression test for the 2026-09-20 defect: ``scripts/install_desktop_shortcut.command`` was
committed with mode ``100644``, so double-clicking it in Finder failed with *"you do not have
appropriate access privileges"* and the owner could not install the preview launcher at all.
The file existed, the tests passed, and review missed it -- because nothing checked that the
artifact could *run*.

Both places are checked, because they fail differently:

* the **working tree**, because that is what Finder and Terminal execute; and
* **git's index**, because that is what a fresh clone materialises on disk.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_GLOBS = ("scripts/*.command", "scripts/*.sh")


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:  # pragma: no cover - no git on PATH
        pytest.skip(f"git is unavailable: {error}")
    except subprocess.CalledProcessError as error:  # pragma: no cover - not a git checkout
        pytest.skip(f"not a usable git checkout: {error}")
    return result.stdout


def _tracked_launchers() -> list[Path]:
    return [
        REPO_ROOT / line
        for line in _git("ls-files", *LAUNCHER_GLOBS).splitlines()
        if line.strip()
    ]


def test_launcher_scripts_are_tracked():
    assert _tracked_launchers(), f"expected at least one launcher matching {LAUNCHER_GLOBS}"


def test_launcher_scripts_are_executable_in_the_working_tree():
    """Finder refuses to run a non-executable file, with a privileges error."""
    unrunnable = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_launchers()
        if not os.access(path, os.X_OK)
    ]
    assert not unrunnable, (
        "these launchers cannot be run, so double-clicking them fails with 'you do not have "
        f"appropriate access privileges': {unrunnable}. Fix with: chmod +x <path>"
    )


def test_launcher_scripts_are_executable_in_git():
    """A fresh clone takes its modes from git, not from this working tree."""
    wrong = []
    for line in _git("ls-files", "-s", *LAUNCHER_GLOBS).splitlines():
        fields = line.split(maxsplit=3)
        if len(fields) != 4:  # pragma: no cover - defensive
            continue
        mode, _sha, _stage, path = fields
        if mode != "100755":
            wrong.append(f"{path} (git mode {mode})")
    assert not wrong, (
        "these launchers are not executable in git, so a fresh clone could not run them: "
        f"{wrong}. Fix with: git update-index --chmod=+x <path>"
    )


def test_launcher_scripts_have_an_interpreter_line():
    """Without a shebang, macOS has no interpreter to hand an executable file to."""
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_launchers()
        if not path.read_bytes().startswith(b"#!")
    ]
    assert not missing, f"launchers with no shebang line: {missing}"
