"""Observatory slice: the Activity ledger row glyph (concept 03).

Concept 03 frames each row's category glyph in a ring with a small marker dot. The
glyph is decorative, so the guards below check two things: that it is installed as
decorative art rather than as content, and that the semantic resolver behind it is
actually correct — including the kit's own electricity-versus-Internet distinction,
which a single-pass keyword match silently loses.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_ledger_glyph_is_installed_as_decorative_kit_art():
    js = _read("static/js/meridian/activity.js")
    css = _read("static/css/meridian/activity.css")
    assert "m-review-glyph" in js
    # Decorative: hidden from assistive tech, because the category text is what states
    # the classification.
    assert 'glyph.setAttribute("aria-hidden", "true")' in js
    # A mask painted with currentColor, so the ring's own ink decides the glyph colour
    # (an <img> cannot inherit currentColor and would render black).
    assert "mask: var(--m-review-icon) center / contain no-repeat" in css
    assert "background-color: currentColor" in css
    assert "kit-2026-09-16/icons/" in js
    # The ring's marker dot from the concept.
    assert ".m-review-glyph::after" in css


def test_ledger_glyph_resolver_module_has_no_dom_or_network_dependency():
    """The resolver is extracted precisely so it can be exercised under Node."""
    js = _read("static/js/meridian/kit-icons.js")
    assert "document." not in js
    assert "window." not in js
    assert "fetch(" not in js
    assert "export function transactionIconName" in js


def test_ledger_glyph_resolver_round_trips_with_node():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const { transactionIconName } = await import('./static/js/meridian/kit-icons.js');
      const check = (label, got, want) => {
        if (got !== want) throw new Error(`${label}: expected ${want}, got ${got}`);
      };
      // The kit calls for wifi for Internet and lightning-charge for electricity, and
      // both of these carry the broad "Utilities" category in the fixture. The specific
      // name must win, or the distinction is lost.
      check('internet', transactionIconName({
        merchant: 'Internet', description: 'Internet', amount: -65,
        classification: { category: 'Utilities' }, suggested_category: 'Utilities',
      }), 'wifi');
      check('electric', transactionIconName({
        merchant: 'Electric', description: 'Electric', amount: -84,
        classification: { category: 'Utilities' }, suggested_category: 'Utilities',
      }), 'lightning-charge');
      check('income', transactionIconName({
        merchant: 'Paycheck', description: 'Paycheck', amount: 1660,
        classification: { category: 'Income' },
      }), 'star');
      check('groceries', transactionIconName({ merchant: 'Corner Market', amount: -32.4 }), 'basket');
      check('transit', transactionIconName({ merchant: 'City Transit', amount: -3 }), 'bus-front');
      check('rent', transactionIconName({ merchant: 'Rent', amount: -1320 }), 'house');
      check('entertainment', transactionIconName({ merchant: 'Steam', amount: -14.99 }), 'controller');
      // Category-only rows still resolve, and unknown rows stay neutral rather than
      // borrowing a meaning they do not have.
      check('category-only', transactionIconName({
        amount: -20, classification: { category: 'Groceries' },
      }), 'basket');
      check('unknown spend', transactionIconName({ merchant: 'Zz Unknown', amount: -5 }), 'compass');
      check('unknown income', transactionIconName({ merchant: 'Zz Unknown', amount: 5 }), 'star');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
