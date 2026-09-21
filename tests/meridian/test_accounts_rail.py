"""Observatory slice: the Accounts connector bow and star-tipped separators (concept 04).

Finding 4 of artifacts/astra-fidelity-review-2026-09-16/README.md measured the gap and
named the construction: the concept uses "curved dashed paths bowing outward, one node
circle at each end, coloured per row (lilac -> mint -> apricot), plus dotted row
separators with a brass star at each end", and records the straight vertical dashed rail
this replaces as "the wrong construction".

These guards protect the properties that make the bow read as a deliberate constellation
rather than a stray border: it needs at least two rows to have anything to connect, it
carries exactly one node per medallion-bearing row, each node takes its row's tint, and
archived rows (which carry no medallion) get neither node nor curve.

The curve needs measured row positions, so it is generated as SVG from the same data that
lays the rows out. That generator is a PURE function of the measurements, which is what
makes the count and tint invariants checkable here without a browser.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def _run_geometry(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_connectors_layer_is_decorative_and_clipped():
    """The layer overlays the list; it must never intercept a click on a row, and it must
    not add a scroll region of its own."""
    css = _read("static/css/meridian/accounts.css")
    block = css.split(".m-account-connectors {")[1].split("}")[0]
    assert "position: absolute" in block
    assert "pointer-events: none" in block
    assert "overflow: hidden" in block
    # Behind the medallions, not over them.
    assert "z-index: 0" in block


def test_row_keeps_the_left_gutter_the_bow_lives_in():
    """The row stays the layout authority for the gutter, so the generated layer measures
    against rows that are already inset. Losing this padding would push the medallions
    into the bow."""
    css = _read("static/css/meridian/accounts.css")
    row_block = css.split("\n.m-account-row {")[1].split("}")[0]
    assert "padding" in row_block
    assert "30px" in row_block


def test_row_separator_is_dotted_and_star_tipped():
    """The concept rules each row with a fine dotted line tipped by a small brass star,
    rather than a plain muted border."""
    css = _read("static/css/meridian/accounts.css")
    assert "border-bottom: 1px dotted var(--obs-brass, #c6aa71)" in css
    star_block = css.split(".m-account-row::before {")[1].split("}")[0]
    assert "star.svg" in star_block
    assert "mask:" in star_block
    assert "pointer-events: none" in star_block
    # Decorative: no text content, so nothing is read out to a screen reader.
    assert 'content: ""' in star_block


def test_archived_rows_are_excluded_from_the_connector_chain():
    """Archived rows carry no medallion, so a node beside them would mark nothing."""
    js = _read("static/js/meridian/accounts.js")
    assert '.m-account-row:not(.m-account-row-archived)' in js


def test_the_layer_hangs_off_the_sheet_not_a_single_list():
    """A list holds one financial ROLE, and a concept-matched page holds one account in
    each, so a per-list layer sees a single row and draws nothing.

    The sheet is the PARENT of `[data-accounts-groups]`, so scoping the query under the
    groups container matches nothing -- a defect that drew no connectors at all and was
    only caught in the browser. Pin the selector to the root-scoped form."""
    js = _read("static/js/meridian/accounts.js")
    assert 'root.querySelectorAll(".m-account-list-sheet")' in js
    assert "[data-accounts-groups] .m-account-list-sheet" not in js
    css = _read("static/css/meridian/accounts.css")
    assert ".m-account-list-sheet {\n  position: relative;" in css
    # The layer is positioned against the sheet's own padding, so it must not also be
    # anchored to the list.
    assert ".m-account-list {\n  position: relative;\n}" not in css


def test_connectors_are_drawn_after_the_rows_exist():
    """The generator measures live row boxes, so it has to run after the rows are in the
    DOM. Rendering it before `renderGroups` would measure an empty sheet."""
    js = _read("static/js/meridian/accounts.js")
    groups_call = js.index("renderGroups(groups);")
    connectors_call = js.index("renderAllConnectors();", groups_call)
    assert connectors_call > groups_call


def test_a_single_row_gets_no_bow():
    """TWO nodes are required for a path. A lone row must get no arc at all -- drawing a
    fixed bow unconditionally hangs a 12px curl beside a constellation of one, which is
    the defect this guard exists to prevent."""
    out = _run_geometry("""
      const { connectorGeometry } = await import('./static/js/meridian/accounts.js');
      const one = connectorGeometry([{ centerY: 20, tint: 'lilac' }]);
      const none = connectorGeometry([]);
      console.log(JSON.stringify({ one: one === null, none: none === null }));
    """)
    result = json.loads(out)
    assert result["one"] is True, "a single row must not produce a bow"
    assert result["none"] is True, "an empty list must not produce a bow"


def test_geometry_gives_one_node_per_row_and_takes_the_bow_depth():
    out = _run_geometry("""
      const { connectorGeometry } = await import('./static/js/meridian/accounts.js');
      const rows = [
        { centerY: 30, tint: 'lilac' },
        { centerY: 90, tint: 'mint' },
        { centerY: 150, tint: 'apricot' },
      ];
      const g = connectorGeometry(rows);
      const xs = [...g.d.matchAll(/Q([-\\d.]+) /g)].map((m) => Number(m[1]));
      console.log(JSON.stringify({ nodes: g.nodes.length, tints: g.nodes.map((n) => n.tint), xs }));
    """)
    result = json.loads(out)
    assert result["nodes"] == 3, "every medallion-bearing row carries exactly one node"
    assert result["tints"] == ["lilac", "mint", "apricot"]
    # Every control point sits at nodeX - bow = 21 - 12 = 9, so the cord bows left of the
    # nodes and never reaches the row's own left edge.
    assert result["xs"] == [9, 9, 9, 9], result["xs"]


def test_geometry_uses_the_stylesheet_node_radius_match():
    """The generated node radius is a literal in JS; the stylesheet's node rules must not
    contradict it by re-introducing a stroke that changes its apparent size."""
    js = _read("static/js/meridian/accounts.js")
    css = _read("static/css/meridian/accounts.css")
    assert 'circle.setAttribute("r", "3.5")' in js
    node_block = css.split(".m-account-connector-node {")[1].split("}")[0]
    assert "stroke: none" in node_block


def test_connector_nodes_carry_the_tints_the_stylesheet_defines():
    """The node colours live in JS (they are SVG attrs) and the row tints live in CSS. If
    either table gains a colour the other lacks, a node loses its fill and renders black
    on the night canvas -- so both sides are pinned to one list here."""
    js = _read("static/js/meridian/accounts.js")
    css = _read("static/css/meridian/accounts.css")
    tint_block = js.split("const TINT_COLORS = {")[1].split("};")[0]
    js_tints = dict(re.findall(r"(\w+):\s*\"(#[0-9a-f]{6})\"", tint_block))
    assert js_tints, "TINT_COLORS not found in accounts.js"

    css_tints = {}
    for selector, body in re.findall(
        r'\.m-account-connector-node\[data-tint="(\w+)"\]\s*\{([^}]*)\}', css
    ):
        match = re.search(r"fill:\s*(#[0-9a-f]{6})", body)
        assert match, f"node rule for {selector} declares no solid fill"
        css_tints[selector] = match.group(1)

    assert css_tints == js_tints, (
        "the connector node colours in the stylesheet and in accounts.js have diverged"
    )


def test_connector_tint_colours_match_the_medallion_tint_source():
    """The node's colour and its row's medallion disk are the same ink. The medallion
    tints live in the stylesheet as `--medallion-tint`; the nodes carry the same values in
    JS. This pins the two together so a future palette change cannot make a row's node
    disagree with the row's medallion."""
    css = _read("static/css/meridian/accounts.css")
    js = _read("static/js/meridian/accounts.js")
    js_tints = dict(re.findall(
        r"(\w+):\s*\"(#[0-9a-f]{6})\"", js.split("const TINT_COLORS = {")[1].split("};")[0]
    ))
    # The medallion tint table is split across two selector families: the row selector
    # (which the icon inherits) and the icon's own direct selectors.
    medallion = dict(re.findall(
        r"\.m-account-(?:row|icon)\[data-tint=\"(\w+)\"\]\s*\{\s*--medallion-tint:\s*(#[0-9a-f]{6})",
        css,
    ))
    for tint, colour in js_tints.items():
        assert medallion.get(tint) == colour, (
            f"node tint {tint} is {colour} in JS but {medallion.get(tint)} on the medallion"
        )
