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

from dataclasses import dataclass
from typing import Any, Iterable, Optional

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

    This is the FALLBACK path. Prefer :func:`resolve_spend_pocket`, which uses Crew's own
    selection when a snapshot has been observed and says so when it has not.
    """
    for account in accounts or ():
        if is_spend_pocket_name(getattr(account, "name", None)):
            return account
    return None


#: Which answer the resolution actually used. A caller publishes this rather than implying that
#: every figure was derived the same way.
BASIS_CREW_SELECTION = "crew_selection"
BASIS_NAME = "name"
BASIS_NONE = "none"

#: What the snapshot said. ``unobserved`` means no snapshot has ever been read for this database;
#: ``selected`` is the only state that is usable as an answer.
STATUS_SELECTED = "selected"
STATUS_SELECTED_UNMATCHED = "selected_unmatched"
STATUS_SELECTED_INACTIVE = "selected_inactive"
STATUS_NONE = "none"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_UNOBSERVED = "unobserved"


@dataclass(frozen=True)
class SpendPocketResolution:
    """Which account is the discretionary spend pocket, and on what basis.

    ``account`` may come from either mechanism, so ``basis`` is not decoration: a reader (or a
    payload) that shows the figure must be able to say whether it rests on Crew's own selection or
    on an English name, and must be able to see when the two could not be reconciled.
    """

    account: Optional[Any]
    basis: str
    selection_status: str
    selected_external_id: Optional[str] = None
    detail: str = ""

    @property
    def uses_selection(self) -> bool:
        return self.basis == BASIS_CREW_SELECTION

    def as_evidence(self) -> dict:
        """A payload-safe description: the basis, the status, and nothing about balances."""
        return {
            "basis": self.basis,
            "selection_status": self.selection_status,
            "selected_external_id": self.selected_external_id,
            "pocket": getattr(self.account, "name", None) if self.account is not None else None,
            "detail": self.detail,
        }


def _account_external_ids(account: Any) -> tuple[str, ...]:
    """Every id an account row can be matched on, most specific first.

    ``external_id`` is Crew's own id and the one the selection carries; ``connection_id`` is a local
    integer and never matches, so it is not consulted. The tuple keeps the comparison tolerant of a
    row exposed as a plain dict (the Plan map works on provider-shaped dicts) without either caller
    having to adapt.
    """
    if isinstance(account, dict):
        return tuple(str(account.get(key)) for key in ("external_id", "id") if account.get(key))
    return tuple(
        str(value) for value in (getattr(account, "external_id", None),) if value
    )


def resolve_spend_pocket(
    accounts: Iterable[Any],
    *,
    selection: Optional[Any] = None,
    active_only: bool = True,
) -> SpendPocketResolution:
    """Answer "which pocket does the owner spend from", preferring Crew's own selection.

    Order of authority, which is the point of OS-113:

    1. **An observed selection that matches a usable account** — matched by Crew's own id, so a
       rename, a duplicate name, or a retired pocket cannot change the answer. This is the only
       basis a figure should rest on when it is available.
    2. **The explicit name allow-list** — the fallback, used when nothing was observed, when the
       snapshot said ``none`` or ``ambiguous``, or when the selected id does not match an account
       this read can use. The resolution SAYS so in ``basis``/``selection_status``: falling back is
       allowed, falling back silently is not.
    3. **Nothing** — ``basis='none'`` and the callers must then treat no pocket as spendable and
       name each one as set aside, rather than counting an earmarked pocket as free cash.

    ``selection`` is a :class:`meridian.spend_selection.SpendSelection` (or anything exposing
    ``selected_external_id``/``resolution``); ``None`` means no snapshot has been recorded, which
    resolves exactly like an unobserved one.
    """
    candidates = [account for account in (accounts or ())
                  if not active_only or getattr(account, "is_active", True)]
    pool = candidates if candidates else []

    resolution = getattr(selection, "resolution", None)
    selected_id = getattr(selection, "selected_external_id", None)
    status = STATUS_UNOBSERVED if selection is None else str(resolution or STATUS_UNOBSERVED)

    if selected_id:
        match = next(
            (account for account in pool if selected_id in _account_external_ids(account)), None
        )
        if match is not None:
            return SpendPocketResolution(
                account=match,
                basis=BASIS_CREW_SELECTION,
                selection_status=STATUS_SELECTED,
                selected_external_id=selected_id,
                detail="Crew's own selected spend pocket, matched by its id",
            )
        # The id matched nothing usable. Which "nothing" matters, because the two have different
        # repairs: an id that matches an INACTIVE row is a stale selection, and one that matches no
        # row at all means the snapshot and the account read disagree. Either way the account is not
        # usable, so the name fallback answers and the status records why.
        inactive = next(
            (account for account in (accounts or ())
             if selected_id in _account_external_ids(account)), None
        )
        if inactive is not None:
            fallback = find_spend_pocket(pool)
            return SpendPocketResolution(
                account=fallback,
                basis=BASIS_NAME if fallback is not None else BASIS_NONE,
                selection_status=STATUS_SELECTED_INACTIVE,
                selected_external_id=selected_id,
                detail="Crew's selection names a pocket this read does not hold as active",
            )
        fallback = find_spend_pocket(pool)
        return SpendPocketResolution(
            account=fallback,
            basis=BASIS_NAME if fallback is not None else BASIS_NONE,
            selection_status=STATUS_SELECTED_UNMATCHED,
            selected_external_id=selected_id,
            detail="Crew's selection does not match any pocket in this read",
        )

    if status == STATUS_AMBIGUOUS:
        fallback = find_spend_pocket(pool)
        return SpendPocketResolution(
            account=fallback,
            basis=BASIS_NAME if fallback is not None else BASIS_NONE,
            selection_status=STATUS_AMBIGUOUS,
            detail="the snapshot's cards disagreed about the selected pocket",
        )

    fallback = find_spend_pocket(pool)
    return SpendPocketResolution(
        account=fallback,
        basis=BASIS_NAME if fallback is not None else BASIS_NONE,
        selection_status=STATUS_NONE if status == STATUS_NONE else STATUS_UNOBSERVED,
        detail=(
            "the snapshot exposed no selection"
            if status == STATUS_NONE
            else "no snapshot has been observed for this database"
        ),
    )


__all__ = [
    "BASIS_CREW_SELECTION",
    "BASIS_NAME",
    "BASIS_NONE",
    "SPEND_POCKET_NAMES",
    "STATUS_AMBIGUOUS",
    "STATUS_NONE",
    "STATUS_SELECTED",
    "STATUS_SELECTED_INACTIVE",
    "STATUS_SELECTED_UNMATCHED",
    "STATUS_UNOBSERVED",
    "SpendPocketResolution",
    "find_spend_pocket",
    "is_spend_pocket_name",
    "normalize_pocket_name",
    "resolve_spend_pocket",
]
