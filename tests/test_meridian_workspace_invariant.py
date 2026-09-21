"""Regression guard for the governing four-workspace shell invariant.

Both governing design records require exactly four primary workspaces
(Today, Plan, Activity, Accounts) with Settings held separate:

- ``Meridian Project Documents/01 - Product Design Specification.md``
  ("The primary navigation contains four workspaces.")
- ``design/observatory-drafts-2026-09-08/BUILD_SPEC.md`` section 3
  ("Keep four workspaces: Today, Plan, Activity, Accounts; Settings is separate.")

Commit 5ea003d added Trials as a fifth primary workspace and, in doing so,
spliced a stray ``<section`` into ``index.html`` so the Accounts workspace lost
its ``data-workspace-section`` element. These checks are pure file reads so they
run in the default (non-browser) suite.
"""

from pathlib import Path

ROOT = Path(__file__).parents[1]
INDEX = ROOT / "templates/meridian/index.html"
NAVIGATION = ROOT / "templates/meridian/partials/navigation.html"
SETTINGS = ROOT / "templates/meridian/settings.html"
SETTINGS_NAV = ROOT / "templates/meridian/partials/settings-navigation.html"
SHELL_JS = ROOT / "static/js/meridian/shell.js"
APP_PY = ROOT / "app.py"

WORKSPACES = ("today", "plan", "activity", "accounts")


def test_primary_navigation_has_exactly_four_workspaces():
    navigation = NAVIGATION.read_text()
    assert navigation.count("data-workspace=") == 4
    for workspace in WORKSPACES:
        assert f'data-workspace="{workspace}"' in navigation
    assert 'data-workspace="trials"' not in navigation


def test_shell_html_has_balanced_sections_and_four_workspace_elements():
    index = INDEX.read_text()
    assert index.count("<section") == index.count("</section>"), (
        "index.html has an unbalanced <section> tag"
    )
    assert index.count("<section") == 4
    assert index.count("data-workspace-section=") == 4
    for workspace in WORKSPACES:
        assert f'data-workspace-section="{workspace}"' in index


def test_shell_html_has_no_dangling_tag_line():
    """A multi-line `<section` is normal here; a tag opened inside a tag is not.

    The corruption repaired in this slice put `<section` on line N and
    `<section id="workspace-trials"...>` on line N+1, which the browser tokenizer
    merges into one malformed element and which pushed the Accounts workspace's
    attributes out of any element entirely.
    """
    lines = INDEX.read_text().splitlines()
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        assert not stripped.startswith("<section <"), (
            f"index.html:{number} nests a tag inside a tag"
        )
        if stripped == "<section" and number < len(lines):
            following = lines[number].strip()
            assert not following.startswith("<"), (
                f"index.html:{number} leaves a dangling `<section` tag immediately "
                f"followed by another tag on line {number + 1}"
            )


def test_javaScript_and_route_workspace_lists_match_the_governing_four():
    shell_js = SHELL_JS.read_text()
    for workspace in WORKSPACES:
        assert f'"{workspace}"' in shell_js
    assert '"trials"' not in shell_js

    app_py = APP_PY.read_text()
    assert (
        'MERIDIAN_WORKSPACES = ("today", "plan", "activity", "accounts")' in app_py
    )


def test_trials_remains_reachable_as_a_settings_section():
    """Restated 2026-09-21 for the Settings hub.

    The original asserted a `settings?section=trials` link inside the flat nav. That nav is
    now the 09-18 concept's grouped hub, whose nine rows do not include a Trials row, so the
    link is deliberately gone -- restated rather than deleted, so the removal stays visible.
    What must still hold is that the section is reachable by URL, renders, and that every
    hub link resolves to a governed section.
    """
    settings = SETTINGS.read_text()
    assert "active_settings_section == 'trials'" in settings
    assert "meridian/partials/trials.html" in settings
    assert "/static/js/meridian/trials.js" in settings

    # The governed section set now lives in ONE declaration (meridian/settings_hub.py)
    # instead of being written inline in app.py, so the hub's links and the route's
    # accepted sections cannot drift apart.
    from meridian.settings_hub import (
        HUB_EXTERNAL_ROUTES,
        SETTINGS_HUB,
        SETTINGS_SECTIONS,
    )

    assert SETTINGS_SECTIONS == {"connections", "payday", "actions", "security", "trials"}
    for group in SETTINGS_HUB:
        for row in group["rows"]:
            if row["href"] is None:
                continue
            # A row points inside Settings (a governed section) or at another existing
            # journey (declared external). Funding schedules is the latter: BUILD_HANDOFF
            # requires it to link to the Plan journey rather than duplicate it.
            if row.get("external"):
                assert row["href"] in HUB_EXTERNAL_ROUTES, row["key"]
            else:
                assert row["section"] in SETTINGS_SECTIONS, row["key"]

    assert "SETTINGS_HUB_SECTIONS" in APP_PY.read_text()


def test_trials_is_not_loaded_as_a_fifth_workspace():
    index = INDEX.read_text()
    assert "meridian/partials/trials.html" not in index
    assert "/static/js/meridian/trials.js" not in index


# --- Rendered-DOM verification ---------------------------------------------
# File-read checks cannot prove the browser parses the shell correctly. The
# 5ea003d corruption produced a DOM with a merged element and text nodes that
# leaked tag attribute syntax, so these tests parse the rendered HTML.

import os  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
from html.parser import HTMLParser  # noqa: E402

import pytest  # noqa: E402

if "app" not in sys.modules:
    os.environ["DB_FILE"] = os.path.join(
        tempfile.mkdtemp(prefix="meridian_workspace_invariant_"), "savings_data.db"
    )

import app as simplecrew  # noqa: E402


class _SectionCollector(HTMLParser):
    """Collect <section> attributes and any attribute text leaked into content."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self.leaked_attribute_text = []

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            self.sections.append(dict(attrs))

    def handle_data(self, data):
        if "data-workspace-section=" in data or 'id="workspace-accounts"' in data:
            self.leaked_attribute_text.append(data.strip())


@pytest.fixture
def shell_client(monkeypatch):
    monkeypatch.setattr(simplecrew, "_background_thread_started", True)
    monkeypatch.setattr(
        simplecrew.login_manager,
        "_user_callback",
        lambda value: simplecrew.User(value, "invariant-user", "invariant@example.com"),
    )
    client = simplecrew.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "invariant-user"
        session["_fresh"] = True
    return client


@pytest.mark.parametrize("workspace", WORKSPACES)
def test_rendered_shell_has_exactly_four_workspace_sections(shell_client, workspace):
    html = shell_client.get(f"/meridian?workspace={workspace}").get_data(as_text=True)
    collector = _SectionCollector()
    collector.feed(html)

    # Partials may legitimately contain their own <section> elements; the
    # invariant is the count of workspace wrappers.
    workspace_sections = [
        section for section in collector.sections if section.get("data-workspace-section")
    ]
    assert len(workspace_sections) == 4, (
        f"rendered shell has {len(workspace_sections)} workspace <section> "
        f"elements, expected 4"
    )
    assert {s["data-workspace-section"] for s in workspace_sections} == set(WORKSPACES)
    for section in workspace_sections:
        assert section.get("data-workspace") == section["data-workspace-section"]
    assert collector.leaked_attribute_text == [], (
        "tag attribute syntax leaked into rendered text: "
        f"{collector.leaked_attribute_text}"
    )


def test_accounts_workspace_renders_with_its_own_attributes(shell_client):
    """Regression for the 5ea003d splice, which detached these attributes."""
    html = shell_client.get("/meridian?workspace=accounts").get_data(as_text=True)
    collector = _SectionCollector()
    collector.feed(html)

    accounts = [
        section
        for section in collector.sections
        if section.get("data-workspace-section") == "accounts"
    ]
    assert len(accounts) == 1
    assert accounts[0].get("id") == "workspace-accounts"
    assert "data-memory-accounts" in accounts[0]


def test_trials_workspace_is_no_longer_routable(shell_client):
    response = shell_client.get("/meridian?workspace=trials")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/meridian")


def test_settings_renders_the_trials_section(shell_client):
    html = shell_client.get("/meridian/settings?section=trials").get_data(as_text=True)
    assert "data-trials-panel" in html
    assert "/static/js/meridian/trials.js" in html
    assert "Trials &amp; renewals" in html
