"""One answer to "which Crew pocket is the spend pocket", and the guard that keeps it one.

Written after the owner renamed his Crew pocket ``Free to Spend`` -> ``Safe to Spend`` on
2026-09-25 and the app silently changed what Safe to Spend MEANT: ``today.py`` matched the
old English name, failed, and fell through to its ``"Cash accounts"`` branch -- a different
base -- with no error and no failing test. Five production sites matched that name, so the
rename had to be repeated in five places.

These tests pin three things: that both names are recognised, that a name which merely LOOKS
similar is NOT recognised, and that the Python list and the browser list cannot drift apart.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from meridian.services.spend_pocket import (
    SPEND_POCKET_NAMES,
    find_spend_pocket,
    is_spend_pocket_name,
)

ROOT = Path(__file__).resolve().parents[2]
ACCOUNTS_JS = ROOT / "static" / "js" / "meridian" / "accounts.js"


class _Account:
    """Stands in for an AccountRecord; only `name` is read by the rule."""

    def __init__(self, name: str) -> None:
        self.name = name


@pytest.mark.parametrize(
    "name",
    [
        "Free to Spend",  # the name the rule was originally written against
        "free to spend",
        "  FREE TO SPEND  ",
        "Safe to Spend",  # the owner's rename, 2026-09-25
        "safe to spend",
        "  Safe To Spend ",
    ],
)
def test_the_old_name_and_the_new_name_are_both_the_spend_pocket(name):
    """A rename is not an event the calculation should notice."""
    assert is_spend_pocket_name(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "Spending money",  # discretionary, but NOT the pocket rule's business
        "Christmas spend",  # earmarked -- treating it as free cash is the dangerous direction
        "Free to Spend Savings",  # a DIFFERENT pocket that merely contains the old name
        "Safe to Spend Goal",
        "Checking",
        "Bill Reserve",
        "Emergency Fund",
        "",
        None,
        123,
    ],
)
def test_a_name_that_only_looks_similar_is_not_the_spend_pocket(name):
    """This is the direction that matters. A rule loose enough to survive any rename --
    "contains 'spend'" -- would also accept an earmarked bucket and quietly count money the
    owner has set aside as free to spend. The rule is an exact list on purpose."""
    assert is_spend_pocket_name(name) is False


def test_the_pocket_is_found_and_absent_is_none_rather_than_a_guess():
    """`None` is what lets the callers say WHICH basis they used, instead of presenting a
    different figure as the same figure. Today's silent fallback is the defect this prevents."""
    accounts = [_Account("Checking"), _Account("Safe to Spend"), _Account("Free to Spend")]
    assert find_spend_pocket(accounts).name == "Safe to Spend"
    assert find_spend_pocket([_Account("Checking")]) is None
    assert find_spend_pocket([]) is None
    assert find_spend_pocket(None) is None


def test_the_browser_uses_the_same_list_as_python():
    """Two copies of a name list is how this broke. The browser has to recognise the pocket
    too -- the Accounts 'liquid' total and the bucket emblem both key off it -- so the lists
    are compared rather than trusted, and this fails the moment one is edited alone."""
    source = ACCOUNTS_JS.read_text(encoding="utf-8")
    match = re.search(
        r"const SPEND_POCKET_NAMES = \[(.*?)\];", source, re.DOTALL
    )
    assert match, "accounts.js no longer declares SPEND_POCKET_NAMES"
    browser_names = re.findall(r'"([^"]+)"', match.group(1))
    assert browser_names == list(SPEND_POCKET_NAMES), (
        "the browser's spend-pocket names and meridian/services/spend_pocket.py have drifted; "
        "a pocket renamed in Crew must not change a figure in any workspace"
    )


def test_no_module_keeps_a_private_copy_of_the_name_rule():
    """today.py and dial.py each carried a private copy of `_spend_source_account`, and the
    dial's own docstring records that the two 'had already drifted'. A third lived in plan.py.
    The rule is defined once now; this fails if a copy grows back."""
    offenders = []
    for path in (ROOT / "meridian").rglob("*.py"):
        if path.name == "spend_pocket.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "def _spend_source_account" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"private copies of the spend-pocket rule: {offenders}"
