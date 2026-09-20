"""OS-060: Today states a bill the observed reserve cannot cover.

The rendering rules are the load-bearing part of this slice, because the owner approved
it CONDITIONALLY on legibility: *"if its something you can do, and the visual display of
it is easy to understand and informative, then absolutely."* A line that renders a
shortfall where none was observed, or that implies the reserve can be tapped, has failed
that condition even when the arithmetic is right.

So these tests pin the two things a source read cannot prove:

* the line stays HIDDEN when no gap was observed -- including for the four live bills
  that report ``0.00`` reserved, which is normal (funded is not covered, D-015);
* the wording carries no verb of action and names no source to draw from, so it can
  never read as a proposal to move money.

The wording check is a source assertion on purpose: it is the one part of the slice that
no behavioural test can catch, and it is exactly the kind of copy that drifts later.
"""
import json
import os
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_today_template_has_the_exposure_slot_hidden_by_default():
    template = _read("templates/meridian/partials/today.html")
    assert "data-reserve-exposure" in template
    assert "m-exposure-line" in template
    # Hidden until a gap is observed: the server sends an explicit empty, and the
    # element must default to hidden so a gap can never appear before it is rendered.
    assert 'class="m-exposure-line" data-reserve-exposure hidden' in template


def test_the_exposure_is_not_a_control():
    """No action, no button, no link: nothing is being proposed.

    The reserve is a ONE-WAY LOCK, so an affordance here would imply it can be tapped or
    topped up from elsewhere. The ledger forbids that implication outright.
    """
    template = _read("templates/meridian/partials/today.html")
    start = template.index("data-reserve-exposure")
    # The element is a bare <p> with no children; check the tag that carries it.
    tag_start = template.rindex("<", 0, start)
    tag = template[tag_start:start]
    assert tag.strip() == "<p class=\"m-exposure-line\""
    for forbidden in ("button", "href", "data-open-advisor", "aria-label"):
        assert forbidden not in tag


def test_the_wording_names_no_action_and_no_source_to_draw_from():
    """The owner's chosen wording, guarded against drifting back into an imperative."""
    script = _read("static/js/meridian/today.js")
    start = script.index("function renderReserveExposure")
    end = script.index("function render(")
    body = script[start:end]

    # Factual composition: needed / set aside / not yet covered.
    assert "needed" in body
    assert "set aside" in body
    assert "not yet covered" in body
    # No verb of action, and no source named -- "has to come from spendable cash" was
    # rejected in review for bordering on implying a transfer.
    for forbidden in (
        "comes from",
        "has to come from",
        "spendable cash",
        "transfer",
        "top up",
        "tap",
        "shortfall",
        "warning",
        "uncovered!",
    ):
        assert forbidden not in body, forbidden


def test_the_css_uses_a_theme_aware_ink_token():
    """Both editions must render it; --obs-paper is dark-only, so it cannot be used."""
    css = _read("static/css/meridian/observatory.css")
    start = css.index(".obs-shell .m-exposure-line")
    block = css[start : css.index("}", start)]
    assert "var(--m-ink-muted)" in block
    assert "--obs-paper" not in block
    # The line names a bill and three figures, so it must be allowed to wrap.
    assert "overflow-wrap" in block


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not available")
def test_render_hides_the_line_when_no_gap_was_observed():
    """The false-positive guard, executed rather than inferred."""
    result = _run_node_render({"reserve_exposure": {"count": 0, "items": []}})
    assert result == {"hidden": True, "text": ""}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not available")
def test_render_hides_the_line_when_the_key_is_absent():
    """An older payload with no exposure key must not invent one."""
    result = _run_node_render({})
    assert result == {"hidden": True, "text": ""}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not available")
def test_render_states_the_rent_gap_factually():
    result = _run_node_render(
        {
            "reserve_exposure": {
                "count": 1,
                "items": [
                    {
                        "id": 1,
                        "name": "Rent",
                        "currency": "USD",
                        "amount": 1442.0,
                        "reserved": 1097.1,
                        "gap": 344.9,
                    }
                ],
            }
        }
    )
    assert result["hidden"] is False
    assert result["text"] == "Rent: $1,442.00 needed · $1,097.10 set aside — $344.90 not yet covered"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not available")
def test_render_summarises_additional_bills_without_listing_them():
    """More than one exposure stays legible: the largest leads, the rest are counted."""
    result = _run_node_render(
        {
            "reserve_exposure": {
                "count": 2,
                "items": [
                    {"name": "Rent", "currency": "USD", "amount": 1442.0, "reserved": 1097.1, "gap": 344.9},
                    {"name": "Water", "currency": "USD", "amount": 80.0, "reserved": 30.0, "gap": 50.0},
                ],
            }
        }
    )
    assert result["hidden"] is False
    assert "Rent" in result["text"]
    assert "Water" not in result["text"]
    assert result["text"].endswith("and 1 more bill")


def _run_node_render(payload):
    """Execute the real ``renderReserveExposure`` against a stub root and return its effect.

    ``today.js`` exports nothing and only self-bootstraps through the ``document`` API,
    so the renderer is driven through a generated module written beside it that
    re-exports the function **from inside its own module scope**. A relative import must
    resolve from a real path on disk (a data: URL cannot), and only an in-scope
    statement can name a module-private function. The file is removed immediately after.
    """
    node = shutil.which("node")
    source = (ROOT / "static/js/meridian/today.js").read_text(encoding="utf-8")
    probe_name = f"_os060_probe_{os.getpid()}.js"
    probe = ROOT / "static/js/meridian" / probe_name
    probe.write_text(source + "\nexport { renderReserveExposure };\n", encoding="utf-8")
    script = f"""
// today.js wires document/window listeners at module scope, so both must exist before
// the import. Node evaluates this preamble (which uses only CJS-provided globals)
// before the dynamic import below runs.
globalThis.window = {{}};
globalThis.document = {{
  readyState: "complete",
  addEventListener: () => {{}},
  querySelector: () => null,
  querySelectorAll: () => [],
}};
const mod = await import("./{probe_name}");
// A minimal DOM element: enough for render()'s other branches to run harmlessly while
// the exposure element records what the real renderer did to it.
const element = () => ({{
  hidden: null,
  textContent: null,
  dataset: {{}},
  children: [],
  classList: {{ add: () => {{}}, remove: () => {{}}, toggle: () => {{}} }},
  setAttribute() {{}},
  removeAttribute() {{}},
  appendChild() {{}},
  addEventListener() {{}},
  querySelector: () => null,
  querySelectorAll: () => [],
}});
const exposure = element();
const root = {{
  querySelector: (sel) => (sel === "[data-reserve-exposure]" ? exposure : element()),
  querySelectorAll: () => [],
  setAttribute() {{}},
}};
// Drive the real renderer directly: render() itself needs a full DOM, and this slice's
// contract is exactly what this one function does to its element.
mod.renderReserveExposure(root, {json.dumps(payload)});
console.log(JSON.stringify({{ hidden: exposure.hidden, text: exposure.textContent }}));
"""
    try:
        result = subprocess.run(
            [node, "--input-type=module", "-e", script],
            cwd=ROOT / "static/js/meridian",
            capture_output=True,
            text=True,
            timeout=60,
        )
    finally:
        probe.unlink(missing_ok=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip())
