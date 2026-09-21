"""Every static asset the shipped UI references must also be IN the repository.

**Why this exists.** On 2026-09-21 the Observatory icon kit
(``static/img/meridian/observatory/kit-2026-09-18/icons/``) was found to be 61 of 62
files UNTRACKED, while shipped CSS referenced 16 of those icons as CSS masks --
``advisor.css`` (the Virgil panel), ``settings.css`` (the Settings hub),
``accounts.css`` and ``activity.css`` among them. Every one of them rendered in the
working tree, and in every governed capture, because the files were simply on disk.

**The failure mode is invisible to the rest of the gate.** A capture renders from
disk; a browser test requests from a server rooted at disk; a source-presence test
reads disk. All three pass. Only a clean clone, or anything built from git, would
have shown sixteen 404s and four surfaces rendering without their glyphs. So the
check has to be against the INDEX, which is the one view of the project that says
what is actually shipped.

**The rule.** If shipped code can request an asset at runtime, that asset must be
tracked. An asset that exists only in a working tree is not shipped, however
complete it looks locally. ``tests/meridian/test_settings_hub.py`` asserts the icon
files EXIST, which is a different question -- it passed throughout the whole period
those files were untracked, and that is exactly the gap this file closes.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: Directories whose contents are SERVED to a browser, so a reference in them is a
#: runtime request. Deliberately excludes artifacts/ (captures, not shipped code).
SCANNED_DIRS = ("static/css", "static/js", "templates", "meridian")

SOURCE_SUFFIXES = (".css", ".js", ".html")

#: Extensions a browser would fetch from /static/. A reference to one of these is a
#: runtime request; anything else in a URL is not an asset this test can adjudicate.
ASSET_SUFFIXES = (
    "svg", "png", "jpg", "jpeg", "webp", "gif", "ico",
    "woff", "woff2", "ttf", "otf", "eot", "mp3", "mp4", "webm", "pdf",
)

ASSET_REFERENCE = re.compile(
    r"""['"(]?/static/([A-Za-z0-9_./\-]+\.(?:%s))""" % "|".join(ASSET_SUFFIXES)
)


def _tracked_paths() -> set:
    """Every path in the git index, relative to the repository root.

    One `git ls-files` call rather than one per file: the index is the authoritative
    answer, and asking it 16 times is how a check like this becomes slow enough to be
    dropped from the gate.
    """
    if not shutil.which("git"):
        pytest.skip("git is not available, so the index cannot be consulted")
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {path for path in result.stdout.split("\0") if path}


def _references() -> dict:
    """Map each referenced asset path to the shipped files that request it."""
    found = {}
    for directory in SCANNED_DIRS:
        base = ROOT / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix not in SOURCE_SUFFIXES or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in ASSET_REFERENCE.findall(text):
                found.setdefault(match, set()).add(
                    str(path.relative_to(ROOT))
                )
    return found


def test_referenced_assets_exist_on_disk():
    """A reference to a file that is not there at all is a broken surface."""
    missing = {
        asset: sorted(users)
        for asset, users in _references().items()
        if not (ROOT / "static" / asset).is_file()
    }
    assert not missing, (
        "shipped code requests assets that do not exist:\n"
        + "\n".join(f"  /static/{a}  <- {', '.join(u)}" for a, u in sorted(missing.items()))
    )


def test_referenced_assets_are_tracked_in_git():
    """The gate that the untracked icon kit walked straight through.

    Asserts against the INDEX, not the working tree. A file that is present locally
    but absent from the index renders in every capture and 404s on a clean clone.
    """
    tracked = _tracked_paths()
    untracked = {
        asset: sorted(users)
        for asset, users in _references().items()
        if (ROOT / "static" / asset).is_file()
        and ("static/" + asset) not in tracked
    }
    assert not untracked, (
        "shipped code requests assets that are NOT tracked by git, so they will 404 on "
        "a clean clone or a build taken from git:\n"
        + "\n".join(
            f"  static/{a}\n      requested by: {', '.join(u)}"
            for a, u in sorted(untracked.items())
        )
    )


def test_a_third_party_asset_kit_ships_its_licence():
    """MIT requires the notice to travel with the files, so it must be tracked too.

    The Observatory icon kit is Bootstrap Icons (MIT, (c) 2019-2024 The Bootstrap
    Authors). Redistributing the icons without the licence alongside them would be a
    licence defect, and the licence was untracked for the same reason the icons were.
    """
    tracked = _tracked_paths()
    licences = [
        path
        for path in ROOT.glob("static/img/**/LICENSE*")
        if path.is_file()
    ]
    absent = [str(p.relative_to(ROOT)) for p in licences if str(p.relative_to(ROOT)) not in tracked]
    assert not absent, (
        "a third-party asset kit ships files without its licence in the index: "
        + ", ".join(sorted(absent))
    )
