"""The Plan map's station-to-mark mapping, exercised as a round trip.

Why this test exists, in the owner's words (2026-09-24): *"The right still says unfounded
commitments and has the same icon as committed to commitments."*

That was a REAL regression, and this repo's attribution rule matters here: `git log -S` traces
it to this lane's own OS-090 commit (`f5e7ef7`), not to anything pre-existing. That commit
replaced an explicit `/unfund/` test with a broad `/bill|commit/` fall-through, so
"Unfunded commitments" -- which contains the word "commitments" -- began resolving to the Bills
station's rotunda and bank glyph.

Nothing could have caught it before it shipped. The mapping lived inside `plan.js`, whose only
possible guard was a text match on the source, and no text match can see that two DIFFERENT
labels resolve to the SAME mark. Worse, the labels and the mapping ship at different moments:
the running process kept serving the old segment labels while the new mapping was already live
in the browser, so the wrong state was a real, user-visible state rather than a transient one.

So the mapping moved to a DOM-free module and is tested by calling it. Every label below is a
case that a future edit could plausibly break.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = "static/js/meridian/plan-map-marks.js"

# label -> (mark, kit glyph). `None` for the mark means "keep the kit fallback".
CASES = {
    # The three stations the concept actually draws.
    "Bills": ("rotunda", "bank"),
    "Goals": ("mountain-flag", "flag"),
    "Available": ("star-rose", "compass"),
    # The service's PREVIOUS labels. They must stay correct on their own, because the running
    # app can serve them while a new client mapping is already live -- which is exactly the
    # state that produced the owner's report.
    "Committed to commitments": ("rotunda", "bank"),
    "Unfunded commitments": (None, "bell"),
    "Unfunded": (None, "bell"),
    # An unrecognised label must not borrow a station's meaning.
    "Something else": (None, "bell"),
}


def _node() -> str:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for the DOM-free module round trip")
    return node


def _run(script: str):
    result = subprocess.run(
        [_node(), "--input-type=module", "-e", script],
        cwd=str(ROOT), capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"node failed: {result.stderr}"
    return json.loads(result.stdout)


def test_the_mapping_is_dom_free_and_importable_on_its_own():
    """If it ever grows a DOM or app dependency, this round trip stops being possible."""
    path = ROOT / MODULE
    assert path.is_file()
    source = path.read_text()
    assert "document." not in source, "the mapping must stay DOM-free to be testable"
    assert "import " not in source, "the mapping must not depend on the app's modules"
    # plan.js must consume it rather than keeping a second copy.
    plan = (ROOT / "static/js/meridian/plan.js").read_text()
    assert 'from "./plan-map-marks.js"' in plan
    assert "function allocationMark(" not in plan, "the mapping has moved; do not re-declare it"
    assert "function allocationIcon(" not in plan


def test_every_label_resolves_to_the_concept_mark_it_means():
    cases = json.dumps(CASES)
    result = _run(f"""
      import {{ allocationMark, allocationIcon }} from './{MODULE}';
      const cases = {cases};
      const out = {{}};
      for (const [label, [mark, icon]] of Object.entries(cases)) {{
        out[label] = {{mark: allocationMark(label), icon: allocationIcon(label)}};
      }}
      console.log(JSON.stringify(out));
    """)
    for label, (mark, icon) in CASES.items():
        assert result[label]["mark"] == mark, (
            f"{label!r} resolves to mark {result[label]['mark']!r}, expected {mark!r}"
        )
        assert result[label]["icon"] == icon, (
            f"{label!r} resolves to glyph {result[label]['icon']!r}, expected {icon!r}"
        )


def test_a_shortfall_never_shares_a_station_mark():
    """The specific regression, pinned by NAME rather than by inspecting the source.

    A shortfall is not a station laid out on the map, so it must not carry a station's mark --
    and the check is that the two commitment-ish labels differ from each other, which is what
    no text match could express.
    """
    result = _run(f"""
      import {{ allocationMark, allocationIcon }} from './{MODULE}';
      console.log(JSON.stringify({{
        committed: allocationMark('Committed to commitments'),
        unfunded: allocationMark('Unfunded commitments'),
        committedIcon: allocationIcon('Committed to commitments'),
        unfundedIcon: allocationIcon('Unfunded commitments'),
      }}));
    """)
    assert result["committed"] == "rotunda"
    assert result["unfunded"] is None, (
        "an unfunded shortfall must keep the kit fallback, not the Bills station's rotunda"
    )
    assert result["committedIcon"] != result["unfundedIcon"], (
        "the two commitment-ish labels must not share a glyph"
    )
