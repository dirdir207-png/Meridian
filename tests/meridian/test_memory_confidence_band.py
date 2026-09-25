"""The confidence band is a real mapping, so it gets a real test rather than a colour assertion.

Owner, 2026-09-25: "confidence have a range of colors based on the confidence level, from red to green".
Colour alone cannot be asserted from Python, and asserting a hex in the stylesheet would only prove a
string exists. What matters is the MAPPING -- which confidence becomes which band -- so this loads
`memory.js` in Node with the minimum DOM it touches at import time and calls the function directly. The
file already publishes itself as `window.MeridianMemory` "for testing and external triggers", which is
the seam this uses.

Two properties beyond the thresholds: a value that is not a number yields NO band (so a missing
confidence renders plain, never as a red "low"), and the boundaries are inclusive at the bottom of each
band so 85% is high and 84.9% is not.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MEMORY_JS = ROOT / "static/js/meridian/memory.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node required")


def _run(script: str):
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, timeout=60, cwd=ROOT, check=False,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return completed.stdout.strip()


def _evaluate(body: str):
    """Load memory.js with a DOM stub, then run `body` against window.MeridianMemory."""
    stub = """
        globalThis.window = globalThis;
        const noop = () => {};
        // memory.js reads the workspace out of the query string during init, so the stub needs a
        // location -- that is the only reason this is not a one-line stub.
        globalThis.location = { search: '', href: 'http://localhost/meridian' };
        globalThis.document = {
            readyState: 'complete',
            addEventListener: noop,
            removeEventListener: noop,
            querySelector: () => null,
            querySelectorAll: () => [],
            createElement: () => ({ style: {}, classList: { add: noop, remove: noop },
                                    setAttribute: noop, appendChild: noop, addEventListener: noop }),
        };
        globalThis.addEventListener = noop;
    """
    return _run(stub + MEMORY_JS.read_text(encoding="utf-8") + "\n" + body)


def test_the_confidence_bands_map_low_to_red_and_high_to_green():
    output = _evaluate("""
        const band = window.MeridianMemory.confidenceBand;
        console.log(JSON.stringify({
            1: band(1), '0.99': band(0.99), '0.85': band(0.85),
            '0.8499': band(0.8499), '0.6': band(0.6), '0.5999': band(0.5999),
            0: band(0), '0.42': band(0.42),
        }));
    """)
    bands = json.loads(output.split("\n")[-1])
    assert bands["1"] == "high"
    assert bands["0.99"] == "high"
    assert bands["0.85"] == "high", "85% is the bottom of the high band, inclusive"
    assert bands["0.8499"] == "medium", "just under 85% must not read as high"
    assert bands["0.6"] == "medium"
    assert bands["0.5999"] == "low"
    assert bands["0"] == "low"
    assert bands["0.42"] == "low"


def test_a_missing_or_non_numeric_confidence_gets_no_band():
    """No confidence must render as plain text: red would claim a judgement nobody made."""
    output = _evaluate("""
        const band = window.MeridianMemory.confidenceBand;
        console.log(JSON.stringify({
            missing: band(undefined), nil: band(null), text: band('0.9'),
            nan: band(NaN), inf: band(Infinity),
        }));
    """)
    bands = json.loads(output.split("\n")[-1])
    assert all(value is None for value in bands.values()), bands


def test_the_renderer_stamps_the_band_only_when_there_is_one():
    source = MEMORY_JS.read_text(encoding="utf-8")
    assert "confidence.dataset.confidenceBand = band;" in source
    assert "if (band) confidence.dataset.confidenceBand = band;" in source
    # The percentage stays on screen: colour must never be the only signal.
    assert "`${Math.round(item.confidence * 100)}% confidence`" in source
