"""Which Crew pocket is the discretionary spend pocket — answered in ONE place.

**Why this module exists (owner, 2026-09-25).** He renamed his Crew pocket
``Free to Spend`` -> ``Safe to Spend``, and the app silently changed what Safe to Spend
MEANS rather than what it is called. ``today.py`` identified the pocket with::

    "free to spend" in name or name == "free to spend"

``"safe to spend"`` satisfies neither test, so the lookup returned ``None`` and Today fell
through to its ``"Cash accounts"`` branch -- a DIFFERENT BASE (the sum of the cash,
checking and savings accounts) -- with no error, no warning and no failing test. On a
figure the owner acts on, that is the same class of silent basis-change D-019 was written
about after the 424.90 / 100.00 defect.

**The duplication was already known.** ``meridian/services/dial.py`` carries this in its own
docstring: *"they had already drifted into two copies of ``_spend_source_account``"*. There
were three copies of the rule in Python (``today.py``, ``dial.py``, ``plan.py``) plus two
name matches in the browser (``accounts.js``). Renaming a pocket had to be repeated in five
places, and nobody can remember five places. This module is the one place.

**What this is NOT.** Name matching is still the wrong mechanism; it is the only one
available on the read path today. ``meridian/providers/crewwork.py``
``readback_selected_spend_pocket()`` already reads Crew's OWN per-user selection
(``userSpendConfig.selectedSpendSubaccount``) and refuses to guess when it is unobserved or
ambiguous. Identifying the pocket by Crew's selection instead of by an English string
removes this whole defect class and is the same setting the OS-112 pocket-selection surface
will configure. Until that is wired into the read path, this module is the seam that makes
the current mechanism correct, explicit and changeable in one edit.
"""

from __future__ import annotations

#: Accepted names, compared case-insensitively with surrounding whitespace removed.
#:
#: Keep this list SMALL and explicit. It is a list of names, not a pattern: a pattern loose
#: enough to accept any future rename ("contains 'spend'") would also accept a pocket called
#: "Spending money" or "Christmas spend" and quietly treat an earmarked bucket as free cash,
#: which is the dangerous direction. A new name is a one-line change here, and that is the
#: point -- it should be a deliberate edit that a reviewer sees, not an inference.
SPEND_POCKET_NAMES: tuple[str, ...] = (
    "free to spend",  # the name this rule was written against
    "safe to spend",  # the owner's rename, 2026-09-25
)


def normalize_pocket_name(name: object) -> str:
    """The comparison form: a string, trimmed and case-folded. Non-strings become ``""``."""
    return str(name or "").strip().casefold()


def is_spend_pocket_name(name: object) -> bool:
    """Is this the name of the discretionary spend pocket?

    Exact match after normalization. ``"free to spend"`` and ``"safe to spend"`` are both
    accepted, so the rule is correct before, during and after the owner's rename -- a
    rename is not an event the calculation should notice.
    """
    return normalize_pocket_name(name) in SPEND_POCKET_NAMES


def find_spend_pocket(accounts):
    """The first account whose name is a spend-pocket name, or ``None``.

    Returns ``None`` rather than guessing when the pocket is absent: the callers must then
    say WHICH basis they used, rather than presenting a different figure as the same figure.
    """
    for account in accounts or ():
        if is_spend_pocket_name(getattr(account, "name", None)):
            return account
    return None


__all__ = [
    "SPEND_POCKET_NAMES",
    "find_spend_pocket",
    "is_spend_pocket_name",
    "normalize_pocket_name",
]
