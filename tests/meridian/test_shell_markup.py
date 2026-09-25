"""The shell's markup must be balanced, because the browser's recovery is SILENT and severe.

Why this file exists, in the owner's words (2026-09-25): "Activity and plan displays both broken". The
Activity page looked empty and the Accounts page showed its own content a full screen down the page.

The cause was one stray `</div>` in `partials/plan.html`, left behind by a scripted edit during OS-102.
The source template analysed as balanced-looking because the stray closer was matched against a
DIFFERENT open element, but in the rendered document it closed the plan pane, then the `<main>` itself.
The HTML parser recovered without an error anywhere: every section after that point became a child of
`<body>` instead of `<main>`, so `section#workspace-activity` and `section#workspace-accounts` were laid
out AFTER the `.m-shell` grid -- which is `min-height: 100vh` -- landing exactly one viewport down. The
dock stayed inside the shell, so a screenshot showed it mid-page with content below it.

Nothing caught it: the structural guards counted the elements they care about and never asked whether
the document still nested; the browser suites skip without APP_URL, and the preview crops inspected the
panes, not the shell. So there are two checks here, at the cause and at the effect:

  1. every partial's container tags balance on their own, with Jinja comments stripped;
  2. the RENDERED shell puts all four workspace sections inside `main#main`, with no parser recovery.
"""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PARTIALS = ROOT / "templates" / "meridian" / "partials"

#: Void elements never take an end tag.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}

#: Containers whose balance this file is about. Inline elements (`a`, `span`, `em`, `strong`, …) are
#: deliberately NOT tracked: HTML5 lets an inline element wrap blocks, so `<a><div></a></div>` is legal
#: and the parser re-parents it without leaking anything. Only a CONTAINER imbalance can move a
#: section out of `<main>`, which is the failure this file exists for. `p`/`li`/`option` may legally
#: omit their end tag and are not evidence either way.
CONTAINERS = {"div", "section", "main", "template", "form", "table", "aside", "nav", "header",
              "footer", "article", "ul", "ol", "dl", "details", "fieldset", "figure"}

JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
JINJA_BLOCK = re.compile(r"\{%.*?%\}", re.S)
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b([^>]*?)(/?)>")


def containers_in(markup: str):
    """Every open/close of a CONTAINER tag, with Jinja comments and blocks removed.

    Jinja comments are stripped because the browser never sees them: an explanatory comment here once
    contained a literal `</div>` and made a correct file look unbalanced. Control blocks are stripped
    for the same reason -- `{% if %}`/`{% endif %}` are not markup -- which means a tag inside a
    conditional is counted unconditionally. That is deliberate: the templates in this repository keep
    their containers outside their conditions, and a conditional that splits a container is itself a
    bug this check should catch.
    """
    cleaned = JINJA_COMMENT.sub("", markup)
    cleaned = JINJA_BLOCK.sub("", cleaned)
    for match in TAG.finditer(cleaned):
        closing, name, _attrs, self_closing = match.groups()
        if name.lower() not in CONTAINERS or self_closing:
            continue
        yield bool(closing), name.lower()


def balance(markup: str):
    """(unmatched closes, still-open at EOF) for the container tags in `markup`."""
    stack = []
    unmatched = []
    for closing, name in containers_in(markup):
        if not closing:
            stack.append(name)
            continue
        if name in stack:
            # Close everything opened after it: that "skip" IS the defect signature.
            index = len(stack) - 1 - stack[::-1].index(name)
            if index != len(stack) - 1:
                unmatched.append((name, list(stack[index + 1:])))
            del stack[index:]
        else:
            unmatched.append((name, []))
    return unmatched, stack


class Nesting(HTMLParser):
    """Record which container each marker opened inside, and every parser recovery."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.inside = {}
        self.recoveries = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        attrs = dict(attrs)
        marker = attrs.get("data-workspace-section")
        if tag == "main" and attrs.get("id") == "main":
            self.inside["__main__"] = list(self.stack)
        if marker:
            self.inside[marker] = list(self.stack)
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag not in self.stack:
            self.recoveries.append((tag, "close with no open match"))
            return
        index = len(self.stack) - 1 - self.stack[::-1].index(tag)
        if index != len(self.stack) - 1:
            self.recoveries.append((tag, list(self.stack[index + 1:])))
        del self.stack[index:]


@pytest.fixture(scope="module")
def rendered_shell():
    """The shell as the browser receives it, rendered by Jinja with the app's own loader."""
    import jinja2

    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT / "templates")),
        autoescape=True,
        undefined=jinja2.Undefined,
    )
    return environment.get_template("meridian/index.html").render(active_workspace="activity")


def test_every_partial_balances_on_its_own():
    """The root cause: a template that opens a container must close it.

    plan.html had 35 `<div>` opens against 36 closes after the OS-102 scripted edit. On its own that
    reads as a harmless extra closer; in the rendered shell it closed `<main>`.
    """
    problems = []
    for path in sorted(PARTIALS.glob("*.html")):
        markup = path.read_text(encoding="utf-8")
        unmatched, still_open = balance(markup)
        if unmatched:
            problems.append(f"{path.name}: end tag(s) with no matching open container: {unmatched[:3]}")
        if still_open:
            problems.append(f"{path.name}: left open at EOF: {still_open[:3]}")
    assert not problems, (
        "a partial's containers do not balance, and the browser's recovery from that is silent:\n  "
        + "\n  ".join(problems)
    )


def test_the_rendered_shell_nests_all_four_workspaces_inside_main(rendered_shell):
    """The effect: this is what 'Activity and Plan displays both broken' actually was."""
    walker = Nesting()
    walker.feed(rendered_shell)
    assert not walker.recoveries, (
        "the rendered shell needed parser recovery, so the document is not what the template says: "
        f"{walker.recoveries[:3]}"
    )
    assert not walker.stack, f"the rendered shell leaves these containers open: {walker.stack[:5]}"
    assert "__main__" in walker.inside, "the shell has no <main id='main'>"
    for workspace in ("today", "plan", "activity", "accounts"):
        assert workspace in walker.inside, f"section[data-workspace-section='{workspace}'] is missing"
        ancestry = walker.inside[workspace]
        assert "main" in ancestry, (
            f"section[data-workspace-section='{workspace}'] is not inside <main>; its ancestors are "
            f"{ancestry}. Outside the shell it is laid out after the min-height:100vh grid, i.e. one "
            "full viewport down the page -- which is exactly the owner's report"
        )
    # And they are all siblings inside the SAME main, not scattered through the body.
    assert len({tuple(walker.inside[name]) for name in
                ("today", "plan", "activity", "accounts")}) == 1, (
        "the four workspace sections do not share one common parent inside main"
    )


def test_the_plan_partial_keeps_its_three_view_panes():
    """The three panes are addressed by `data-plan-view-pane`; losing a wrapper loses the toggle.

    This is the specific line OS-102 dropped: without the crew pane's opener, the closing
    `</div><!-- /data-plan-view-pane="crew" -->` closed `m-plan` instead, which is how the extra
    closer consumed `<main>`. The panes are asserted to be SIBLINGS nested one level inside the
    partial's root, and the memory section to be their sibling too -- i.e. not swallowed by the crew
    pane, which is the other half of that mistake.
    """
    markup = JINJA_COMMENT.sub("", (PARTIALS / "plan.html").read_text(encoding="utf-8"))
    depths, depth = {}, 0
    for line in markup.split("\n"):
        for closing, name in containers_in(line):
            if closing:
                depth -= 1
            elif 'data-plan-view-pane="' in line:
                pane = re.search(r'data-plan-view-pane="([a-z]+)"', line).group(1)
                depths[pane] = depth
                depth += 1
                continue
            elif 'class="m-surface m-plan-memory"' in line:
                depths["memory"] = depth
                depth += 1
                continue
            else:
                depth += 1
    assert set(depths) == {"plan", "rules", "crew", "memory"}, f"panes found: {depths}"
    assert len(set(depths.values())) == 1, (
        f"the pane wrappers and the memory section are not siblings: {depths}"
    )
