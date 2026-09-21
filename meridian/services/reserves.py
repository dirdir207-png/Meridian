"""The reserve deficit: why a negative reserve must reduce "free to spend".

**The bug this module fixes, reported by the owner 2026-09-21.** Today's headline and the dial
both read Crew's "Free to Spend" pocket balance DIRECTLY, on a stated assumption (today.py, verbatim):

    "Crew has already separated bill/obligation money into other pockets, so no further
     subtraction."

That assumption holds while the reserve is at or above zero. **It fails when the reserve is
negative, and a negative reserve is a real, owner-confirmed state** (D-017; rent cleared against
an intentionally over-stated "free to spend"). A negative reserve is an **overdraft**: the reserve
has consumed more than it held, and that deficit has not yet been moved out of the spendable
pocket. So the pocket balance OVERSTATES what is genuinely free to spend, by exactly the deficit.

The owner's own arithmetic: Free to Spend 424.90, reserve -324.90, true free to spend **100.00**.
Meridian displayed 424.90.

**The error is in the dangerous direction.** A spending figure that says you have more money than
you do is worse than one that understates it, because the owner acts on it. The owner also noted
the workaround: topping the reserve up by hand moves the money in Crew, the pocket then reads 100,
and the display "would likely display correctly" — the symptom disappears while the calculation
stays wrong. That is a hole, not a fix.

**Two rules, kept narrow on purpose.**

1. **Only NEGATIVE reserves count.** A reserve at or above zero is already reflected in how Crew
   split the pockets, so subtracting it would double-count and understate the owner's money — the
   opposite error, and equally wrong.
2. **Nothing is clamped.** If the deficit exceeds the pocket, free-to-spend is genuinely NEGATIVE
   and is reported that way. Flooring it at zero would hide an overdraft behind a plausible-looking
   zero, which is the same class of fabrication D-017 forbids.

``total_reserved_amount`` is ``None`` when the read did not report it, which is not evidence of a
deficit, so an unreported reserve contributes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ReserveDeficit:
    """How much the spendable figure is overstated by a negative reserve."""

    amount: float = 0.0
    reserves: int = 0
    currency: str = "USD"

    @property
    def is_present(self) -> bool:
        return self.amount > 0

    def as_payload(self) -> dict[str, Any]:
        """Reported alongside the figure it adjusts, so the number stays explainable.

        A headline that silently changed because of a reserve would be as opaque as the bug
        this fixes, so the deficit is stated as an input with the count of reserves behind it.
        """
        return {
            "reserve_deficit": round(self.amount, 2),
            "reserve_deficit_count": self.reserves,
            "reserve_deficit_currency": self.currency,
            "reserve_deficit_reason": (
                "A negative bill reserve is an overdraft: it has consumed more than it held and "
                "the deficit has not yet been moved out of the spendable pocket, so it reduces "
                "what is genuinely free to spend."
                if self.is_present
                else None
            ),
        }


def reserve_deficit(reserves: Iterable[Any], *, currency: str = "USD") -> ReserveDeficit:
    """Sum the overdraft across the reserves currently observed.

    ``reserves`` is ``FinancialRepository.list_bill_reserves()`` -- current reserves only, since
    that method already excludes retired ones. A reserve whose total was never reported
    contributes nothing: absence is not a deficit.
    """
    total = 0.0
    count = 0
    for record in reserves:
        amount = getattr(record, "total_reserved_amount", None)
        if amount is None or amount >= 0:
            continue
        if (getattr(record, "currency", None) or "USD") != currency:
            # Never add across currencies; an unconvertible deficit is left out rather than
            # guessed at, matching the dial's existing single-currency discipline.
            continue
        total += -amount
        count += 1
    return ReserveDeficit(amount=total, reserves=count, currency=currency)


def spendable_after_reserve_deficit(available: float, deficit: ReserveDeficit) -> float:
    """The genuinely free figure. Not clamped: an overdraft shows as a negative number."""
    return available - deficit.amount


__all__ = [
    "ReserveDeficit",
    "reserve_deficit",
    "spendable_after_reserve_deficit",
]
