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
    icons = _read("static/js/meridian/kit-icons.js")
    css = _read("static/css/meridian/activity.css")
    assert "m-review-glyph" in js
    # Decorative: hidden from assistive tech, because the category text is what states
    # the classification.
    assert 'glyph.setAttribute("aria-hidden", "true")' in js
    # A mask painted with currentColor, so the ring's own ink decides the glyph colour
    # (an <img> cannot inherit currentColor and would render black).
    assert "mask: var(--m-review-icon) center / contain no-repeat" in css
    assert "background-color: currentColor" in css
    # The kit path lives with the mapping it belongs to, and the row builder reaches
    # it through one helper rather than re-typing the path.
    assert "kit-2026-09-18/icons" in icons
    assert "kitIconUrl(transactionIconName(transaction))" in js
    # The ring's marker dot from the concept.
    assert ".m-review-glyph::after" in css


def test_every_referenced_kit_icon_has_a_shipped_asset():
    """A mapped name with no asset renders an EMPTY ring, not a fallback.

    `bank` was mapped in the merchant patterns and shipped nowhere, so every row it
    resolved to drew a blank circle that read as a broken icon. Nothing caught it
    because the mapping and the asset set were never compared.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const fs = await import('node:fs');
      const m = await import('./static/js/meridian/kit-icons.js');
      const dir = 'static/img/meridian/observatory/kit-2026-09-18/icons';
      const have = new Set(fs.readdirSync(dir)
        .filter((f) => f.endsWith('.svg'))
        .map((f) => f.replace(/\\.svg$/, '')));
      const wanted = [...m.ICON_NAMES.category, ...m.ICON_NAMES.action,
                      ...m.ICON_NAMES.merchant, ...m.ICON_NAMES.unknown];
      const missing = [...new Set(wanted)].filter((n) => !have.has(n)).sort();
      if (missing.length) throw new Error('mapped but not shipped: ' + missing.join(', '));
      if (!/^\\/static\\/img\\//.test(m.KIT_ICON_ROOT)) throw new Error('kit root is not a static path');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_unclassified_rows_show_their_merchant_glyph_not_a_wall_of_questions():
    """The owner's live data is entirely unclassified, so every row resolved to the
    same question glyph and all 62 kit icons stayed unused.

    The ring identifies the MERCHANT while the category line keeps saying nothing is
    known, and only an unnameable merchant falls back to the question glyph.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = """
      const { transactionIconName } = await import('./static/js/meridian/kit-icons.js');
      const check = (label, got, want) => {
        if (got !== want) throw new Error(`${label}: expected ${want}, got ${got}`);
      };
      // Real merchants from the live ledger, all carrying an explicit "uncategorized"
      // classification with no suggestion -- the exact state that produced the wall.
      const uncategorized = { category: 'uncategorized' };
      check('grocer', transactionIconName({ merchant: 'Dollar General', classification: uncategorized }), 'basket');
      check('dining', transactionIconName({ merchant: "Wendy's", classification: uncategorized }), 'fork-knife');
      check('energy', transactionIconName({ merchant: '2222 ENERGY NOR', classification: uncategorized }), 'lightning-charge');
      check('lunch', transactionIconName({ merchant: 'Lunchflow', classification: uncategorized }), 'fork-knife');
      check('keys', transactionIconName({ merchant: 'KeyMe', classification: uncategorized }), 'key');
      // A merchant the kit cannot name keeps the concept's question glyph.
      check('unnamed', transactionIconName({ merchant: 'Zz Unknown', classification: uncategorized }), 'question-circle');
      check('empty', transactionIconName({ amount: -5 }), 'question-circle');
      // The bank pattern used to name an icon the kit does not ship.
      check('bank', transactionIconName({ merchant: 'Savings Reserve', amount: -50 }), 'piggy-bank');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


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
      }), 'cash-stack');
      check('groceries', transactionIconName({ merchant: 'Corner Market', amount: -32.4 }), 'basket');
      check('transit', transactionIconName({ merchant: 'City Transit', amount: -3 }), 'bus-front');
      check('rent', transactionIconName({ merchant: 'Rent', amount: -1320 }), 'house');
      check('entertainment', transactionIconName({ merchant: 'Steam', amount: -14.99 }), 'controller');
      // Category-only rows still resolve, and unknown rows stay neutral rather than
      // borrowing a meaning they do not have.
      check('category-only', transactionIconName({
        amount: -20, classification: { category: 'Groceries' },
      }), 'basket');
      check('unknown spend', transactionIconName({ merchant: 'Zz Unknown', amount: -5 }), 'question-circle');
      check('unknown income', transactionIconName({ merchant: 'Zz Unknown', amount: 5 }), 'question-circle');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_category_icons_preserve_owner_meaning_and_unknown_state():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is unavailable")
    script = """
      const { transactionIconName, categoryIsAssigned } = await import('./static/js/meridian/kit-icons.js');
      const cases = [
        [{merchant:'Whole Foods',classification:{category:'Dining',method:'user_rule'}},'fork-knife'],
        [{classification:{category:'Phone'}},'phone'],
        [{classification:{category:'Pets'}},'heart'],
        [{classification:{category:'Refunds'},amount:10},'arrow-counterclockwise'],
        [{classification:{category:'Uncategorized'},merchant:'Unknown',amount:-5},'question-circle'],
        [{classification:{category:'Work supplies',method:'user_rule'},merchant:'Whole Foods'},'tag'],
      ];
      for (const [input,want] of cases) {
        const got = transactionIconName(input);
        if (got !== want) throw Error(`${JSON.stringify(input)} expected ${want}, got ${got}`);
      }
      for (const v of [null, '', 'Uncategorized', 'unassigned', '  Uncategorized  ']) {
        if (categoryIsAssigned(v)) throw Error(`Not a category: ${v}`);
      }
    """
    result = subprocess.run([node, "--input-type=module", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
