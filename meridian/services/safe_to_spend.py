"""What is safe to spend — ONE rule, in ONE place, for every workspace.

**Why this module exists (OS-111, owner-decided 2026-09-25).** The product published two
different "money you can spend" numbers. Today read one Crew pocket; Plan partitioned a
different quantity. The owner's order was to make them one number and to delete one of the
two rules rather than leave them standing beside each other.

**The rule, as the owner stated it** (verbatim, 2026-09-25): *"the safe to spend figure is
calculating by taking the total amount of funds in the account and reducing it by all
obligations where funds have been tucked away ... Available balance, or total balance, less
bill reserve (a collective expense/bill bucket) less goals/other not immediately spendable
buckets."* And on the goals term: *"should be money sitting in pocket."*

**What it replaced, and why the substitution was not cosmetic.** The first proposal was for
Today to adopt ``plan.py``'s rule, on the recorded premise that Plan already implemented the
owner's shape. Reading the artifacts falsified that premise three ways:

1. ``plan.py:448-455`` built its base from ``cash``/``checking``/``savings`` accounts only,
   while ``meridian/providers/crewwork.py:540`` types every non-primary Crew pocket as
   ``"pocket"``. The two sets are disjoint, so Plan subtracted goal-pocket money from a base
   that never contained it — and its own comment claimed the opposite ("their current
   balances are already inside cash_total"). ``tests/meridian/services/test_plan.py:236-255``
   only passes *because* the pocket sits outside the base.
2. Plan's bill term was ``committed + unfunded`` with ``committed`` defined as
   ``Σ min(funded, target)`` — which cancels exactly, so the term was arithmetically
   ``Σ target``: every bill's full amount, funded or not. It carried no funding information
   at all, and subtracted money the owner had not yet set aside.
3. Plan had no way to see the overdraft D-019 was written about. A negative reserve exists
   only in ``crew_bill_reserves.total_reserved_amount`` (that is what migration 028 permits);
   ``commitments.funded_amount`` is still ``CHECK >= 0`` and nothing copies one into the
   other.

Applying it would have moved the owner's headline to ``0.00`` while the pocket he spends from
held ``15.45``. So the rule is pocket accounting, which is also what Crew itself does (D-019
records that Crew's Safe-to-Spend totals the pockets the owner has *selected*).

**The arithmetic, and the one property that makes it honest.**

    total   = Σ money accounts (cash, checking, savings, pocket) + reserve   [reserve SIGNED]
    set aside = every active pocket EXCEPT the spend pocket, positive balances only
    amount  = total − Σ set aside − max(0, reserve)                          [never clamped]

*The reserve is signed into the total, and that is what subsumes D-019.*  Crew holds the
reserve at account level, outside every pocket — D-015's own arithmetic on the live read:
reserve ``1097.10`` + ``345.28`` across the four subaccounts = ``1442.38``, "the owner's live
total to the cent". So a pool of account rows alone would omit it entirely. Adding it signed
means an overdrawn reserve (``-324.90``) lowers the total by exactly the amount the old
deficit term subtracted, without a second term that could double-count it: the owner's
``424.90`` pocket against a ``-324.90`` reserve is ``100.00``, which is the figure D-019 was
written to produce. A reserve that HOLDS money nets to zero against the total and appears in
the breakdown as its own named line, which is the owner's worked example (``1000`` less a
``100`` bill reserve less a ``100`` emergency fund is ``800``).

**Three rules kept, deliberately.**

* **Nothing is clamped.** A negative result is reported as a negative (D-019 rule 2, D-017).
  Under this rule the only way to go negative is a genuinely negative total — a real
  overdraft — because a pocket that is overdrawn is never *subtracted*: subtracting a negative
  would add money back, so an overdrawn non-spend pocket stays inside the total where it
  belongs and lowers the figure. That is the dangerous direction guarded by construction.
* **Zero-holding pockets draw no line**, but every line that IS drawn is a real subtraction,
  and ``sum(lines) == result`` holds by construction (OS-079's completeness invariant).
* **No English name decides money state beyond pocket identity.** The one name-keyed question
  left is "which pocket is the spend pocket", which lives in ``meridian/services/spend_pocket.py``
  and is being replaced by Crew's own ``selectedSpendSubaccount`` under OS-113. When no spend
  pocket is identified, NO pocket is treated as spendable — every pocket is set aside and named
  as such — because the alternative (treating an unknown pocket as free cash) is the direction
  that overstates a spending figure.

**What this module is NOT.** It is read-only arithmetic over observed values. It moves no
money, proposes nothing, and grants no authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

from meridian.services.reserves import observed_reserve_total
from meridian.services.spend_pocket import (
    BASIS_NONE,
    STATUS_UNOBSERVED,
    find_spend_pocket,
    resolve_spend_pocket,
)

#: Account types that hold money the owner HAS. "fallback" is deliberately excluded: the Crew
#: adapter creates a synthetic parent row with ``balance = 0.0`` purely so that account-level
#: transactions keep an account to map to (``meridian/providers/crewwork.py:552-570``), so it is
#: not a second holding. Liabilities, investments and loans are not spending money either, which
#: matches the boundary ``today.py`` and ``plan.py`` already drew.
MONEY_ACCOUNT_TYPES = frozenset({"cash", "checking", "savings", "pocket"})

#: The base line's label. It names the BASIS rather than the pocket, and the basis is the
#: account's total — the owner's choice, 2026-09-25, taken because "Available balance" would
#: name a total by the wrong name on the one surface whose job is to explain the number.
#:
#: ONE label, including when no spend pocket is identified. OS-079 kept a separate "Cash
#: accounts" label there because that branch had a different BASIS (the sum of the cash-type
#: accounts' available balances). Under this rule the basis is the same quantity in both cases
#: — the account's total — and what differs is only WHICH pockets are exempt from the
#: subtraction, which the lines show by naming every pocket that was set aside. A second label
#: would now imply a basis change that no longer happens.
TOTAL_LABEL = "Total balance"

#: The bill reserve's line label. The quantity is the reserve bucket Crew actually reports, so
#: the bucket's own name is the honest one (the owner's OS-079 wording).
RESERVE_LABEL = "Bill reserve"

#: The closing clause of the explanation. It is the RULE, stated once, and it is the owner's own
#: 2026-09-25 wording — it simply became literally true when the rule changed.
RULE_SENTENCE = "The rest is safe to spend."


def _money(amount: float, currency: str) -> str:
    """A prose amount in the panel's own money format, so it never reads as a bare number.

    The panel prints every figure through ``formatCurrency``; the explanation is held to the same
    shape, because "overdrawn by 324.90" beside "$100.00" reads as a different kind of quantity.
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


@dataclass(frozen=True)
class SetAside:
    """One pocket the owner has set aside, and the money sitting in it."""

    label: str
    amount: float


@dataclass(frozen=True)
class SafeToSpend:
    """The figure, its derivation, and the facts needed to state either honestly."""

    currency: str
    total: float
    set_aside: tuple[SetAside, ...]
    reserve: float
    amount: float
    spend_pocket: Optional[str]
    accounts_counted: int
    #: Which mechanism identified the spend pocket, and what the snapshot said (OS-113). Published
    #: rather than implied: a figure that rests on Crew's own selection and one that rests on an
    #: English name are not the same claim, and falling back is only honest if it is visible.
    spend_pocket_basis: str = BASIS_NONE
    selection_status: str = STATUS_UNOBSERVED

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    @property
    def has_spend_pocket(self) -> bool:
        """Whether a spend pocket was identified, i.e. anything was treated as spendable."""
        return self.spend_pocket is not None

    def set_aside_total(self) -> float:
        return round(sum(item.amount for item in self.set_aside), 2)

    def lines(self) -> list[dict[str, Any]]:
        """The breakdown's lines, as the server publishes them to the panel.

        The base line first, then one line per set-aside pocket under the pocket's OWN name,
        then the bill reserve when it holds money. The signs carry the subtraction, so no line
        needs a "less" verb, and the lines sum to the result by construction.
        """
        lines: list[dict[str, Any]] = [{"label": self.base_label, "amount": self.total}]
        lines.extend(
            {"label": item.label, "amount": -item.amount} for item in self.set_aside
        )
        if self.reserve > 0:
            lines.append({"label": RESERVE_LABEL, "amount": -self.reserve})
        return lines

    @property
    def base_label(self) -> str:
        return TOTAL_LABEL

    def explanation(self) -> str:
        """Plain language, assembled by the SERVER so the panel cannot re-derive the figure.

        Four states, and each one says only what happened: nothing set aside; pockets set aside;
        no spend pocket identified; a reserve that is overdrawn. The old wording ("...is the
        discretionary balance Meridian reads directly") described a base that no longer exists, so
        it is gone rather than left standing beside the new rule.
        """
        if not self.set_aside and self.reserve <= 0:
            # Nothing may claim a subtraction that did not happen (OS-079 acceptance 4) — but an
            # overdrawn reserve still has to be STATED, because the total moved because of it and
            # a figure that changed silently is as opaque as the bug this rule replaced.
            parts = [
                f"{self.base_label} is every dollar Meridian can see in this currency.",
                "Nothing is set aside, so nothing is subtracted.",
            ]
        else:
            parts = [
                f"{self.base_label} is every dollar Meridian can see in this currency.",
                "Everything you have set aside is listed beneath it, and subtracted.",
            ]
            if not self.has_spend_pocket:
                parts.append(
                    "Meridian could not tell which pocket you spend from, so every pocket is set "
                    "aside above rather than counted as spendable."
                )
        if self.reserve < 0:
            parts.append(
                f"The bill reserve is overdrawn by {_money(abs(self.reserve), self.currency)}, "
                "which is already inside the total rather than subtracted a second time."
            )
        parts.append(RULE_SENTENCE)
        return " ".join(parts)

    def as_payload(self) -> dict[str, Any]:
        """The breakdown the surfaces render verbatim."""
        return {
            "currency": self.currency,
            "lines": self.lines(),
            "result_label": "Safe to spend",
            "result": round(self.amount, 2),
            "explanation": self.explanation(),
            # Basis, stated as data rather than inferred from the line labels.
            "spend_pocket": self.spend_pocket,
            "spend_pocket_basis": self.spend_pocket_basis,
            "selection_status": self.selection_status,
            "reserve": round(self.reserve, 2),
        }


def money_accounts(accounts: Iterable[Any], *, currency: Optional[str] = None) -> list[Any]:
    """Active accounts holding money the owner has, optionally in one currency."""
    selected = []
    for account in accounts or ():
        if not getattr(account, "is_active", False):
            continue
        if getattr(account, "account_type", None) not in MONEY_ACCOUNT_TYPES:
            continue
        if currency is not None and (getattr(account, "currency", None) or "USD") != currency:
            continue
        selected.append(account)
    return selected


def pool_total(accounts: Iterable[Any], *, currency: str = "USD") -> float:
    """Everything the owner holds in one currency, across pockets and cash accounts alike."""
    return round(
        sum(float(getattr(account, "balance", 0.0) or 0.0) for account in accounts), 2
    )


def spend_pocket_account(accounts: Iterable[Any]) -> Optional[Any]:
    """The spend pocket among ACTIVE accounts.

    ``spend_pocket.find_spend_pocket`` scans whatever it is given, and the owner's Crew read
    carries two pockets named "Free to Spend" — one of them inactive since 2026-09-17 — so a
    list-order match could land on a retired row. Which pocket is spendable must not depend on
    row order.
    """
    return find_spend_pocket([a for a in (accounts or ()) if getattr(a, "is_active", False)])


def set_aside_pockets(
    accounts: Sequence[Any],
    *,
    spend_pocket: Optional[Any],
    currency: str = "USD",
) -> tuple[SetAside, ...]:
    """Every active pocket that is NOT the spend pocket, holding money, in name order.

    A pocket holding zero draws no line (the owner's 2026-09-25 rule, and the panel drops zero
    lines anyway). A pocket that is OVERDRAWN is not listed either, and that is deliberate:
    subtracting a negative would ADD money back. Its deficit stays inside the total, where it
    lowers the figure, which is the conservative direction.
    """
    spend_id = getattr(spend_pocket, "id", None) if spend_pocket is not None else None
    rows = []
    for account in accounts:
        if getattr(account, "account_type", None) != "pocket":
            continue
        if not getattr(account, "is_active", False):
            continue
        if (getattr(account, "currency", None) or "USD") != currency:
            continue
        if spend_pocket is not None and (
            account is spend_pocket
            or (spend_id is not None and getattr(account, "id", None) == spend_id)
        ):
            continue
        balance = round(float(getattr(account, "balance", 0.0) or 0.0), 2)
        if balance <= 0:
            continue
        rows.append(SetAside(label=str(getattr(account, "name", "") or "Pocket"), amount=balance))
    rows.sort(key=lambda item: (-item.amount, item.label.casefold()))
    return tuple(rows)


def safe_to_spend(
    accounts: Iterable[Any],
    reserves: Iterable[Any] = (),
    *,
    currency: Optional[str] = None,
    spend_selection: Optional[Any] = None,
) -> Optional[SafeToSpend]:
    """The one rule. ``None`` only when there is no money at all to reason about.

    ``currency`` defaults to the spend pocket's own currency, which is what Today published
    before this rule existed; accounts in other currencies are excluded rather than summed, and
    the caller keeps reporting them separately so nothing is silently dropped.

    ``spend_selection`` is the newest OBSERVED Crew selection
    (:class:`meridian.spend_selection.SpendSelection`), or ``None`` when no snapshot has been
    recorded. It decides which pocket is spendable — Crew's own answer when it is usable, the
    explicit name allow-list otherwise — and the resolution's basis travels with the result so a
    surface can say which one it used (OS-113, owner-approved 2026-09-25).
    """
    accounts = list(accounts or ())
    resolution = resolve_spend_pocket(accounts, selection=spend_selection)
    spend = resolution.account
    if currency is None:
        currency = (getattr(spend, "currency", None) or "USD") if spend is not None else "USD"

    money = money_accounts(accounts, currency=currency)
    if not money:
        return None

    reserve = observed_reserve_total(reserves, currency=currency)
    total = round(pool_total(money, currency=currency) + reserve, 2)
    set_aside = set_aside_pockets(accounts, spend_pocket=spend, currency=currency)
    amount = round(total - sum(item.amount for item in set_aside) - max(0.0, reserve), 2)
    return SafeToSpend(
        currency=currency,
        total=total,
        set_aside=set_aside,
        reserve=round(reserve, 2),
        amount=amount,
        spend_pocket=(str(getattr(spend, "name", "") or "") if spend is not None else None),
        accounts_counted=len(money),
        spend_pocket_basis=resolution.basis,
        selection_status=resolution.selection_status,
    )


__all__ = [
    "MONEY_ACCOUNT_TYPES",
    "RESERVE_LABEL",
    "RULE_SENTENCE",
    "SetAside",
    "SafeToSpend",
    "TOTAL_LABEL",
    "money_accounts",
    "pool_total",
    "safe_to_spend",
    "set_aside_pockets",
    "spend_pocket_account",
]
