"""OS-111: the one money rule — everything you have, minus every pocket you set aside.

Owner decisions, 2026-09-25, taken BEFORE any code was written:

1. **Pocket accounting.** *"the total amount of funds in the account and reducing it by all
   obligations where funds have been tucked away ... less bill reserve ... less goals/other not
   immediately spendable buckets"*, and on the goals term *"should be money sitting in pocket."*
2. **No clamp anywhere.** D-019 rule 2 stands; ``plan.py``'s ``max(_ZERO, ...)`` is removed.
3. **The base line is labelled for what it is** ("Total balance"), each subtraction carrying its
   own pocket's name.

The three worked examples below are the owner's own, and they are the acceptance cases. Each one
also holds under the arrangement Crew actually uses — the reserve is held at ACCOUNT level, outside
every pocket (D-015) — which is why the reserve is entered into the total SIGNED rather than
subtracted as a separate deficit term.
"""
import dataclasses

import pytest

from meridian.services.safe_to_spend import (
    RESERVE_LABEL,
    RULE_SENTENCE,
    TOTAL_LABEL,
    money_accounts,
    safe_to_spend,
    set_aside_pockets,
    spend_pocket_account,
)


@dataclasses.dataclass
class FakeAccount:
    name: str
    balance: float
    id: int | None = None
    account_type: str = "cash"
    currency: str = "USD"
    is_active: bool = True
    available_balance: float | None = None


@dataclasses.dataclass
class FakeReserve:
    total_reserved_amount: float | None
    currency: str = "USD"


def _labels(result):
    return [line["label"] for line in result.lines()]


def _amounts(result):
    return [line["amount"] for line in result.lines()]


# ---------------------------------------------------------------------------------------
# The owner's three worked examples — the acceptance cases
# ---------------------------------------------------------------------------------------

def test_the_bill_reserve_and_emergency_fund_example_is_800():
    """Owner, 2026-09-25: "If my total balance is 1000 and my bill reserve is 100, and I have an
    emergency fund of 100, my safe to spend isn't 900, it's 800."

    Total 1000 = Checking 400 + Safe to Spend 400 + Emergency Fund 100 + a 100 bill reserve held
    outside the pockets. The emergency fund draws a line of its own BECAUSE it is subtracted —
    that is the owner's completeness requirement, not decoration.
    """
    accounts = [
        FakeAccount("Checking", 400.0, id=1, account_type="checking"),
        FakeAccount("Safe to Spend", 400.0, id=2, account_type="pocket"),
        FakeAccount("Emergency Fund", 100.0, id=3, account_type="pocket"),
    ]
    result = safe_to_spend(accounts, [FakeReserve(100.0)])

    assert result.total == pytest.approx(1000.00)
    assert result.amount == pytest.approx(800.00)
    assert _labels(result) == [TOTAL_LABEL, "Emergency Fund", RESERVE_LABEL]
    assert _amounts(result) == [1000.00, -100.00, -100.00]


def test_the_owners_overdraft_case_is_100_and_needs_no_deficit_term():
    """D-019's case, and the reason the signed reserve SUBSUMES its deficit rule.

    Free to Spend 424.90 against a -324.90 reserve is 100.00. The old rule reached it by
    subtracting a deficit from the pocket; this rule reaches it because the overdraft is already
    inside the total. One term, no double-count, same number.
    """
    accounts = [FakeAccount("Safe to Spend", 424.90, id=1, account_type="pocket")]
    result = safe_to_spend(accounts, [FakeReserve(-324.90)])

    assert result.total == pytest.approx(100.00)
    assert result.amount == pytest.approx(100.00)
    # No reserve line: an overdrawn reserve has no money to set aside, and subtracting a negative
    # would ADD money back.
    assert _labels(result) == [TOTAL_LABEL]
    assert "overdrawn by $324.90" in result.explanation()


def test_a_pool_of_cash_accounts_with_an_overdraft_is_the_same_number():
    """The same 100.00 when the spendable money is a CASH-typed account rather than a pocket.

    This is the shape ``tests/meridian/services/test_reserve_deficit.py`` uses, and the reason the
    rule is written over "money accounts" rather than over pockets alone: a provider that types a
    spendable account ``savings`` must not fall outside the arithmetic.
    """
    accounts = [FakeAccount("Free to Spend", 424.90, account_type="savings")]
    result = safe_to_spend(accounts, [FakeReserve(-324.90)])

    assert result.total == pytest.approx(100.00)
    assert result.amount == pytest.approx(100.00)


# ---------------------------------------------------------------------------------------
# The arithmetic's safety properties
# ---------------------------------------------------------------------------------------

def test_nothing_is_clamped_so_a_real_overdraft_shows_as_a_negative():
    """D-019 rule 2 / D-017: never substitute a fabricated figure for an observed state."""
    accounts = [FakeAccount("Safe to Spend", -83.14, id=1, account_type="pocket")]
    result = safe_to_spend(accounts, [])

    assert result.amount == pytest.approx(-83.14)
    assert result.is_negative is True


def test_an_overdrawn_non_spend_pocket_lowers_the_figure_and_is_never_subtracted():
    """Subtracting a negative pocket would ADD money back — the dangerous direction.

    So it draws no line and stays inside the total, where it lowers the figure: 100 - 50 = 50, not
    100.
    """
    accounts = [
        FakeAccount("Safe to Spend", 100.0, id=1, account_type="pocket"),
        FakeAccount("Overspent Pocket", -50.0, id=2, account_type="pocket"),
    ]
    result = safe_to_spend(accounts, [])

    assert result.total == pytest.approx(50.00)
    assert result.amount == pytest.approx(50.00)
    assert _labels(result) == [TOTAL_LABEL]


def test_a_zero_holding_pocket_draws_no_line():
    """The owner's rule, 2026-09-25: a pocket appears only when it holds a balance."""
    accounts = [
        FakeAccount("Safe to Spend", 800.0, id=1, account_type="pocket"),
        FakeAccount("Christmas fund", 0.0, id=2, account_type="pocket"),
    ]
    result = safe_to_spend(accounts, [])

    assert "Christmas fund" not in _labels(result)
    assert result.amount == pytest.approx(800.00)


def test_the_lines_sum_to_the_result():
    """OS-079's completeness invariant, and it must hold in every arrangement — including one
    where a pocket is overdrawn, because that is the case a hand-written line set gets wrong."""
    for accounts, reserves in (
        ([FakeAccount("Safe to Spend", 400.0, id=1, account_type="pocket")], []),
        (
            [
                FakeAccount("Safe to Spend", 400.0, id=1, account_type="pocket"),
                FakeAccount("Emergency Fund", 100.0, id=2, account_type="pocket"),
            ],
            [FakeReserve(50.0)],
        ),
        ([FakeAccount("Checking", 200.0, account_type="checking")], [FakeReserve(-150.0)]),
        (
            [
                FakeAccount("Safe to Spend", 100.0, id=1, account_type="pocket"),
                FakeAccount("Overspent", -50.0, id=2, account_type="pocket"),
            ],
            [FakeReserve(25.0)],
        ),
    ):
        result = safe_to_spend(accounts, reserves)
        assert sum(line["amount"] for line in result.lines()) == pytest.approx(result.amount)


def test_a_funded_reserve_is_money_you_have_that_is_also_set_aside():
    """A positive reserve nets to zero inside the total and is reported as its own line.

    It must not be counted twice in either direction: omitting it from the total would understate
    what the owner holds, and failing to subtract it would present bill money as free.
    """
    accounts = [FakeAccount("Safe to Spend", 300.0, id=1, account_type="pocket")]
    result = safe_to_spend(accounts, [FakeReserve(200.0)])

    assert result.total == pytest.approx(500.00)
    assert result.amount == pytest.approx(300.00)
    assert _amounts(result) == [500.00, -200.00]


def test_an_unreported_reserve_is_silence_not_a_number():
    """D-019: ``None`` is not a deficit, and here it is not a holding either."""
    accounts = [FakeAccount("Safe to Spend", 300.0, id=1, account_type="pocket")]

    assert safe_to_spend(accounts, [FakeReserve(None)]).amount == pytest.approx(300.00)
    assert safe_to_spend(accounts, []).amount == pytest.approx(300.00)


def test_a_reserve_in_another_currency_is_left_out_rather_than_converted():
    accounts = [FakeAccount("Safe to Spend", 300.0, id=1, account_type="pocket")]
    result = safe_to_spend(accounts, [FakeReserve(200.0, currency="EUR")])

    assert result.reserve == 0.0
    assert result.amount == pytest.approx(300.00)


# ---------------------------------------------------------------------------------------
# Basis: which accounts count, and what happens when nothing is identifiable
# ---------------------------------------------------------------------------------------

def test_money_accounts_are_pockets_and_cash_types_only():
    """Liabilities, investments and the adapter's synthetic ``fallback`` parent rows are excluded.

    ``fallback`` carries ``balance = 0.0`` by construction (crewwork.py:552-570), so counting it
    would add nothing but would put a non-holding into the account count.
    """
    accounts = [
        FakeAccount("Checking", 100.0, account_type="checking"),
        FakeAccount("Savings", 50.0, account_type="savings"),
        FakeAccount("Pocket", 25.0, account_type="pocket"),
        FakeAccount("Card", -400.0, account_type="credit"),
        FakeAccount("Brokerage", 9000.0, account_type="investment"),
        FakeAccount("Crew account", 0.0, account_type="fallback"),
        FakeAccount("Retired", 700.0, account_type="cash", is_active=False),
    ]
    assert [a.name for a in money_accounts(accounts)] == ["Checking", "Savings", "Pocket"]


def test_pockets_are_never_treated_as_spendable_when_no_spend_pocket_is_identified():
    """The conservative direction, stated as a test.

    If the spend pocket cannot be identified — a rename Meridian does not know, or a provider that
    has no pockets — then NO pocket is exempt: every one is named as set aside. The alternative,
    counting an unknown pocket as free cash, overstates a spending figure, which is the direction
    that must never be chosen by default.
    """
    accounts = [
        FakeAccount("Checking", 200.0, account_type="checking"),
        FakeAccount("Emergency Fund", 50.0, id=9, account_type="pocket"),
    ]
    result = safe_to_spend(accounts, [])

    assert result.spend_pocket is None
    assert result.has_spend_pocket is False
    assert result.amount == pytest.approx(200.00)
    assert _labels(result) == [TOTAL_LABEL, "Emergency Fund"]
    assert "could not tell which pocket you spend from" in result.explanation()


def test_a_renamed_spend_pocket_understates_rather_than_overstates():
    """A rename must never make Meridian present earmarked money as free (OS-113's class of defect).

    Before OS-111 the failure was silent and it went the other way: the lookup returned ``None``,
    Today fell through to a different BASIS and the headline changed with no error. Here the
    failure is visible (the pocket is named as a line) and conservative.
    """
    accounts = [
        FakeAccount("Spending money", 120.0, id=1, account_type="pocket"),
        FakeAccount("Safe to Spend", 80.0, id=2, account_type="pocket"),
    ]
    result = safe_to_spend(accounts, [])

    assert result.spend_pocket == "Safe to Spend"
    assert result.amount == pytest.approx(80.00)
    assert _labels(result) == [TOTAL_LABEL, "Spending money"]


def test_an_inactive_duplicate_spend_pocket_cannot_win():
    """The owner's Crew read carries TWO "Free to Spend" pockets, one inactive since 2026-09-17.

    Identification must not depend on row order, and a retired row must not be the one treated as
    the pocket the owner spends from.
    """
    accounts = [
        FakeAccount("Free to Spend", -165.22, id=472, account_type="pocket", is_active=False),
        FakeAccount("Free to Spend", 15.45, id=2, account_type="pocket"),
        FakeAccount("Emergency Fund", 0.0, id=3, account_type="pocket"),
    ]
    result = safe_to_spend(accounts, [])

    assert result.spend_pocket == "Free to Spend"
    assert result.total == pytest.approx(15.45)
    assert result.amount == pytest.approx(15.45)


def test_spend_pocket_scan_is_restricted_to_active_accounts():
    accounts = [
        FakeAccount("Safe to Spend", 0.0, id=1, account_type="pocket", is_active=False),
        FakeAccount("Free to Spend", 5.0, id=2, account_type="pocket"),
    ]
    assert spend_pocket_account(accounts).id == 2


def test_set_aside_pockets_are_largest_first_then_by_name():
    accounts = [
        FakeAccount("Safe to Spend", 10.0, id=1, account_type="pocket"),
        FakeAccount("Fun Money", 25.0, id=2, account_type="pocket"),
        FakeAccount("Emergency Fund", 50.0, id=3, account_type="pocket"),
        FakeAccount("Travel", 25.0, id=4, account_type="pocket"),
    ]
    rows = set_aside_pockets(accounts, spend_pocket=accounts[0])
    assert [row.label for row in rows] == ["Emergency Fund", "Fun Money", "Travel"]
    assert [row.amount for row in rows] == [50.0, 25.0, 25.0]


# ---------------------------------------------------------------------------------------
# Currency and the payload the surfaces render
# ---------------------------------------------------------------------------------------

def test_accounts_in_another_currency_are_excluded_not_summed():
    accounts = [
        FakeAccount("Safe to Spend", 100.0, id=1, account_type="pocket"),
        FakeAccount("Euro pocket", 45.0, id=2, account_type="pocket", currency="EUR"),
    ]
    result = safe_to_spend(accounts, [])

    # The spend pocket sets the currency, exactly as Today published it before this rule existed,
    # and the other pocket is left out rather than converted.
    assert result.currency == "USD"
    assert result.total == pytest.approx(100.00)
    assert result.amount == pytest.approx(100.00)


def test_no_money_accounts_at_all_yields_nothing_to_say():
    assert safe_to_spend([FakeAccount("Card", -10.0, account_type="credit")], []) is None
    assert safe_to_spend([], [FakeReserve(10.0)]) is None


def test_the_payload_carries_the_lines_the_result_and_the_basis():
    """The panel renders this verbatim and may not re-derive it (OS-079 acceptance 3)."""
    accounts = [FakeAccount("Safe to Spend", 300.0, id=1, account_type="pocket")]
    payload = safe_to_spend(accounts, [FakeReserve(75.0)]).as_payload()

    assert payload["currency"] == "USD"
    assert payload["result"] == pytest.approx(300.00)
    assert payload["result_label"] == "Safe to spend"
    assert payload["lines"] == [
        {"label": TOTAL_LABEL, "amount": 375.00},
        {"label": RESERVE_LABEL, "amount": -75.00},
    ]
    assert payload["spend_pocket"] == "Safe to Spend"
    assert payload["reserve"] == pytest.approx(75.00)
    assert RULE_SENTENCE in payload["explanation"]


def test_the_explanation_never_claims_a_subtraction_that_did_not_happen():
    """OS-079 acceptance 4, carried onto the new rule."""
    accounts = [FakeAccount("Safe to Spend", 300.0, id=1, account_type="pocket")]
    explanation = safe_to_spend(accounts, []).explanation()

    assert "nothing is subtracted" in explanation
    assert "overdrawn" not in explanation
