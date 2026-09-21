"""Mechanism A -- nothing ships unreachable.

FALSIFIED BY THE SETTINGS HUB (OS-065). It rendered, passed twelve guard tests, carried ten
governed captures in both themes, and was marked complete -- while NO control in the product
linked to it, because every Settings entry point deep-linked PAST it into a section. The owner
could not see five sessions of work and said so. Every check at the time proved that a route
renders; not one asked whether a user could ARRIVE at it, and the capture harness supplies the
URL while a user follows a link. Asking the second question is the whole of this file.

The invariant, stated once: **a surface that exists only as a URL you must already know is not
shipped.** Two consequences are checked here, plus the specific regression that caused the
defect:

1. every declared settings surface -- the hub and each section -- is the target of a link
2. every declared workspace is the target of a link
3. a control whose label means "Settings" opens the DIRECTORY, not a section

Deliberately NOT checked here: whether every href resolves. That is a different class of defect
(dead links), it needs route-parameter handling to avoid false positives, and a guard that
cries wolf is worse than no guard. It is recorded as the next step of this mechanism instead.

These are static file reads, so they run in the default suite with no app import, no browser and
no database -- the same reasoning as tests/test_meridian_workspace_invariant.py.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SETTINGS_HUB = ROOT / "meridian/settings_hub.py"
APP_PY = ROOT / "app.py"

SETTINGS_PATH = "/meridian/settings"


def _hrefs() -> list[tuple[Path, str]]:
    """Every href the product can follow, with the file that declares it.

    Two sources, because links are not all literals in templates. The hub's row hrefs are DATA
    -- `"href": "/meridian/settings?section=security"` in meridian/settings_hub.py, rendered as
    `{{ row.href }}` -- so scanning templates alone reported `security` as unlinked when it is
    in fact linked from the hub. A reachability guard that cannot see data-driven links would
    have produced a false orphan and, worse, taught the next session to distrust it.
    """
    found: list[tuple[Path, str]] = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        found.extend((path, href) for href in re.findall(r'href="([^"]+)"', path.read_text(encoding="utf-8")))
    found.extend((SETTINGS_HUB, href) for href in re.findall(r'"href":\s*"([^"]+)"', SETTINGS_HUB.read_text(encoding="utf-8")))
    return found


def _path_of(href: str) -> str:
    return href.split("#", 1)[0].split("?", 1)[0]


def _declared_settings_sections() -> frozenset[str]:
    text = SETTINGS_HUB.read_text(encoding="utf-8")
    match = re.search(r"SETTINGS_SECTIONS\s*=\s*frozenset\((\{[^}]*\})\)", text)
    assert match, "SETTINGS_SECTIONS must stay a single declaration in meridian/settings_hub.py"
    return frozenset(re.findall(r'"([a-z]+)"', match.group(1)))


def _declared_workspaces() -> tuple[str, ...]:
    match = re.search(r"MERIDIAN_WORKSPACES\s*=\s*\(([^)]*)\)", APP_PY.read_text(encoding="utf-8"))
    assert match, "MERIDIAN_WORKSPACES must stay a single declaration in app.py"
    return tuple(re.findall(r'"([a-z]+)"', match.group(1)))


def test_the_settings_hub_itself_is_linked():
    """The exact defect. A hub is only a hub if something points at it."""
    bare = [
        href
        for _, href in _hrefs()
        if _path_of(href) == SETTINGS_PATH and "section=" not in href
    ]
    assert bare, (
        "no control links to the Settings hub itself -- every Settings link deep-links past it "
        "into a section, so the hub is reachable only by typing the URL (OS-081)"
    )


def test_every_settings_section_is_linked():
    """A section reachable only by typing `?section=<name>` is invisible in the product.

    This is `?section=trials` exactly: the partial, the route, the JS and the API endpoint all
    exist, and no template anywhere links to it.
    """
    hrefs = [href for _, href in _hrefs()]
    missing = sorted(s for s in _declared_settings_sections() if not any(f"section={s}" in h for h in hrefs))
    assert not missing, f"settings sections linked from nowhere (URL-only): {missing}"


def test_every_workspace_is_linked():
    """The same rule one level up: a workspace with no link is not a workspace."""
    hrefs = [href for _, href in _hrefs()]
    missing = [w for w in _declared_workspaces() if not any(f"workspace={w}" in h for h in hrefs)]
    assert not missing, f"workspaces linked from nowhere (URL-only): {missing}"


def _entry_point_href(template: str, marker: str) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    match = re.search(rf'<a[^>]*{marker}[^>]*href="([^"]+)"', text) or re.search(
        rf'<a[^>]*href="([^"]+)"[^>]*{marker}', text
    )
    assert match, f"{template}: could not find the {marker} entry point"
    return match.group(1)


def test_settings_controls_open_the_directory_not_a_section():
    """The regression, pinned at both entry points.

    `Connect account` and `View connections` in accounts.html are NOT this check's business:
    they name a specific surface, so they rightly target the Connections SECTION. A control
    whose whole job is to mean "Settings" must open the hub.
    """
    assert _entry_point_href("meridian/index.html", "data-settings-link") == SETTINGS_PATH
    assert _entry_point_href("meridian/partials/navigation.html", "data-settings-link") == SETTINGS_PATH
