"""A negative reserve must reduce "free to spend" — owner-reported bug, 2026-09-21.

Today's headline and the dial both read Crew's "Free to Spend" pocket directly, on the stated
assumption that *"Crew has already separated bill/obligation money into other pockets, so no
further subtraction"*. That holds while the reserve is at or above zero and FAILS when it is
negative, because a negative reserve is an overdraft whose deficit has not yet been moved out of
the spendable pocket.

The owner's acceptance case, verbatim in shape: Free to Spend 424.90 less a -324.90 reserve is
**100.00**, and Meridian displayed 424.90. The error overstates available money, which is the
dangerous direction: a spending figure that says you have more than you do is one the owner acts on.

The owner also named the workaround: top the reserve up by hand, the pocket then reads 100, and the
display "would likely display correctly". That makes the symptom vanish while the calculation stays
wrong — so the tests below fix the CALCULATION, with the pocket balance left alone.
"""
import dataclasses

import pytest

from meridian.services.reserves import (
    ReserveDeficit,
    reserve_deficit,
    spendable_after_reserve_deficit,
)


@dataclasses.dataclass
class FakeReserve:
    total_reserved_amount: float | None
    currency: str = "USD"


@dataclasses.dataclass
class FakeAccount:
    name: str
    available_balance: float | None
    currency: str = "USD"
    is_active: bool = True
    account_type: str = "cash"
    # build_today also reads the settled balance for total_cash; not asserted here, but it must
    # exist or the fixture fails before reaching the code under test.
    balance: float | None = 0.0


# ---------------------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------------------

def test_the_owners_arithmetic_is_the_acceptance_case():
    """424.90 free-to-spend less a -324.90 reserve is 100.00."""
    deficit = reserve_deficit([FakeReserve(-324.90)])
    assert deficit.amount == pytest.approx(324.90)
    assert deficit.reserves == 1
    assert spendable_after_reserve_deficit(424.90, deficit) == pytest.approx(100.00)


def test_a_positive_reserve_changes_nothing():
    """A reserve at or above zero is already reflected in how Crew split the pockets.
    Subtracting it would DOUBLE-COUNT and understate the owner's money -- the opposite error,
    and equally wrong."""
    assert reserve_deficit([FakeReserve(500.0)]).amount == 0.0
    assert spendable_after_reserve_deficit(424.90, reserve_deficit([FakeReserve(0.0)])) == 424.90


def test_an_unreported_reserve_is_not_a_deficit():
    """``None`` means the read did not report a total. Absence is not evidence of an overdraft,
    and inventing one here would reduce the owner's spendable figure on no evidence (C01)."""
    deficit = reserve_deficit([FakeReserve(None)])
    assert deficit.amount == 0.0
    assert deficit.reserves == 0
    assert deficit.is_present is False


def test_several_negative_reserves_are_summed():
    deficit = reserve_deficit([FakeReserve(-100.0), FakeReserve(-24.90), FakeReserve(50.0)])
    assert deficit.amount == pytest.approx(124.90)
    assert deficit.reserves == 2


def test_an_overdraft_beyond_the_pocket_is_reported_as_negative_not_clamped():
    """Flooring at zero would hide an overdraft behind a plausible-looking zero. D-017 forbids
    substituting a fabricated figure for an observed one."""
    deficit = reserve_deficit([FakeReserve(-500.0)])
    assert spendable_after_reserve_deficit(424.90, deficit) == pytest.approx(-75.10)


def test_currencies_are_never_added_together():
    """An unconvertible deficit is left out rather than guessed at, matching the dial's existing
    single-currency discipline."""
    deficit = reserve_deficit([FakeReserve(-100.0, currency="EUR")], currency="USD")
    assert deficit.amount == 0.0
    assert reserve_deficit([FakeReserve(-100.0, currency="EUR")], currency="EUR").amount == 100.0


def test_the_deficit_is_reported_so_the_figure_stays_explainable():
    """A headline that silently changed because of a reserve would be as opaque as the bug."""
    payload = reserve_deficit([FakeReserve(-324.90)]).as_payload()
    assert payload["reserve_deficit"] == pytest.approx(324.90)
    assert payload["reserve_deficit_count"] == 1
    assert "overdraft" in payload["reserve_deficit_reason"]
    # And with no deficit there is no borrowed reason implying one.
    assert reserve_deficit([]).as_payload()["reserve_deficit_reason"] is None


# ---------------------------------------------------------------------------------------
# Wired into the two real surfaces, which must agree
# ---------------------------------------------------------------------------------------

class _FakeGraph:
    def __init__(self, accounts, reserves):
        self._accounts = accounts
        self._reserves = reserves

    def list_accounts(self):
        return self._accounts

    def list_bill_reserves(self):
        return self._reserves


# ---------------------------------------------------------------------------------------
# Today, against a REAL repository.
#
# A real FinancialRepository is used rather than a fake on purpose: the deficit has to be read
# through the real ``list_bill_reserves()``, which is what excludes retired reserves via
# ``absent_since IS NULL``. A fake that returns whatever the test wants would prove the
# arithmetic while leaving the filter -- the part that can silently double-count a dead reserve --
# untested.
# ---------------------------------------------------------------------------------------

def _connected_repository(tmp_path, *, available=424.90):
    from meridian.repository import FinancialRepository

    repository = FinancialRepository(str(tmp_path / "financial.db"))
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    repository.upsert_account(
        provider="crew",
        external_id="free-to-spend",
        name="Free to Spend",
        account_type="savings",
        balance=available,
        available_balance=available,
        connection_id=run.connection_id,
        source_updated_at="2026-09-21T09:00:00Z",
        synced_at="2026-09-21T09:00:00Z",
    )
    repository.finish_sync_run(
        run.id, status="complete", accounts_synced=1, transactions_synced=0, errors=0
    )
    return repository


def _seed_reserve(repository, amount, *, external_id="reserve-1"):
    repository.upsert_bill_reserve(
        provider="crew",
        external_id=external_id,
        total_reserved_amount=amount,
        observed_at="2026-09-21T09:00:00Z",
    )


def test_today_subtracts_the_deficit_and_reports_it(tmp_path):
    """The headline this bug was reported against, through the real read path."""
    from meridian.services.today import build_today

    repository = _connected_repository(tmp_path)
    _seed_reserve(repository, -324.90)

    today = build_today(repository)

    assert today["safe_to_spend"]["amount"] == pytest.approx(100.00)
    inputs = today["safe_to_spend"]["inputs"]
    assert inputs["reserve_deficit"] == pytest.approx(324.90)
    assert inputs["reserve_deficit_count"] == 1
    assert "overdraft" in inputs["reserve_deficit_reason"]


def test_today_is_unchanged_when_the_reserve_is_healthy(tmp_path):
    """The guard in the other direction: a normal positive reserve must not move the headline,
    or the fix would silently understate every owner's spending money."""
    from meridian.services.today import build_today

    repository = _connected_repository(tmp_path)
    _seed_reserve(repository, 500.0)

    today = build_today(repository)

    assert today["safe_to_spend"]["amount"] == pytest.approx(424.90)
    assert today["safe_to_spend"]["inputs"]["reserve_deficit"] == 0.0


def test_a_retired_reserve_no_longer_reduces_the_headline(tmp_path):
    """A reserve a complete read stopped returning has ``absent_since`` set. Its overdraft is
    history, not a live reduction, so counting it would understate the owner's money forever."""
    from meridian.services.today import build_today

    repository = _connected_repository(tmp_path)
    _seed_reserve(repository, -324.90)
    repository.mark_absent_bill_reserves(
        provider="crew", observed_external_ids=[], absent_since="2026-09-21T10:00:00Z"
    )

    today = build_today(repository)

    assert repository.list_bill_reserves() == []
    assert today["safe_to_spend"]["amount"] == pytest.approx(424.90)


def test_no_reserves_at_all_leaves_the_headline_alone(tmp_path):
    from meridian.services.today import build_today

    today = build_today(_connected_repository(tmp_path))

    assert today["safe_to_spend"]["amount"] == pytest.approx(424.90)
    assert today["safe_to_spend"]["inputs"]["reserve_deficit"] == 0.0


def test_today_falls_back_to_cash_and_still_applies_the_deficit(tmp_path):
    """The fallback path must not quietly skip the adjustment."""
    from meridian.repository import FinancialRepository
    from meridian.services.today import build_today

    repository = FinancialRepository(str(tmp_path / "cash-only.db"))
    run = repository.begin_sync_run(
        provider="crew", connection_external_id="crew-household", connection_name="Crew"
    )
    repository.upsert_account(
        provider="crew",
        external_id="checking",
        name="Checking",
        account_type="checking",
        balance=200.0,
        available_balance=200.0,
        connection_id=run.connection_id,
        source_updated_at="2026-09-21T09:00:00Z",
        synced_at="2026-09-21T09:00:00Z",
    )
    repository.finish_sync_run(
        run.id, status="complete", accounts_synced=1, transactions_synced=0, errors=0
    )
    _seed_reserve(repository, -150.0)

    today = build_today(repository)

    assert today["safe_to_spend"]["amount"] == pytest.approx(50.0)


def test_the_dial_and_today_agree_on_the_same_inputs(tmp_path):
    """Both surfaces carried the same wrong assumption, and they had already drifted into two
    copies of ``_spend_source_account``. They now call one shared rule, so they cannot disagree
    about how much money the owner has.

    RESTORED 2026-09-21: these two tests were dropped by an edit that used a following ``def``
    line as an anchor and did not re-emit it -- the same mechanism this file's sibling trap entry
    describes, and it caught me again while WRITING that entry. Verified by name count, not by a
    green run.
    """
    from meridian.services.dial import _available_to_spend
    from meridian.services.today import build_today

    repository = _connected_repository(tmp_path)
    _seed_reserve(repository, -324.90)

    dial = _available_to_spend(repository)
    assert dial is not None
    # The dial works in minor units; Today in dollars. Same money.
    assert dial["minor"] == 10000
    assert dial["currency"] == "USD"
    assert build_today(repository)["safe_to_spend"]["amount"] == pytest.approx(100.00)


def test_the_dial_still_returns_the_pocket_when_reserves_cannot_be_read():
    """An unreadable reserve must not blank the dial. Degrading to the pocket balance is the
    previous behaviour, which is wrong only in the overdraft case -- and a blank figure would be
    wrong always."""
    from meridian.services.dial import _available_to_spend

    class Exploding(_FakeGraph):
        def list_bill_reserves(self):
            raise RuntimeError("store down")

    dial = _available_to_spend(Exploding([FakeAccount("Free to Spend", 424.90)], []))
    assert dial is not None
    assert dial["minor"] == 42490


def test_the_breakdown_explains_the_figure_and_adds_up(tmp_path):
    """The owner asked for the figure to be explainable in the app. The SERVER builds the
    breakdown rather than leaving the client to derive it: a client that re-derived the number
    could drift from the server that computed it, which is how the figure went wrong before."""
    from meridian.services.today import build_today

    repository = _connected_repository(tmp_path)
    _seed_reserve(repository, -324.90)

    breakdown = build_today(repository)["safe_to_spend"]["breakdown"]

    assert breakdown["result"] == pytest.approx(100.00)
    labels = [line["label"] for line in breakdown["lines"]]
    # RESTATED 2026-09-25 for the owner's decided wording. The first line now names the BASIS
    # ("Available balance") rather than the pocket, and the subtraction is named after the pocket
    # it came from with the SIGN carrying the minus rather than a "Less ... " verb -- his words:
    # "I would go with Available Balance, and then - with each pocket name and their balance and -
    # Bill Reserve." The arithmetic assertions below are unchanged and still what makes this test
    # mean anything.
    assert labels == ["Available balance", "Bill reserve"]
    # The stated lines must actually produce the stated result, or the explanation is decoration.
    assert sum(line["amount"] for line in breakdown["lines"]) == pytest.approx(
        breakdown["result"]
    )
    assert "reserve is negative" in breakdown["explanation"]
    assert breakdown["currency"] == "USD"
    # The adjustment is shown as a negative line, so the reader sees a subtraction rather than
    # being told one happened.
    assert breakdown["lines"][1]["amount"] < 0


def test_the_breakdown_says_nothing_was_subtracted_when_there_is_no_deficit(tmp_path):
    """It must not imply a subtraction that did not happen -- an explanation that describes
    arithmetic the calculation never performed is worse than none."""
    from meridian.services.today import build_today

    repository = _connected_repository(tmp_path)
    _seed_reserve(repository, 500.0)

    breakdown = build_today(repository)["safe_to_spend"]["breakdown"]

    assert [line["label"] for line in breakdown["lines"]] == ["Available balance"]
    assert breakdown["result"] == pytest.approx(424.90)
    assert "nothing is subtracted" in breakdown["explanation"]
    # No adjustment line, so the breakdown cannot show a subtraction that did not happen.
    assert sum(line["amount"] for line in breakdown["lines"]) == pytest.approx(
        breakdown["result"]
    )


def test_a_healthy_reserve_deficit_is_falsely_absent_by_default():
    """Guard on the dataclass default: the zero case must mean "no deficit", never "unknown"."""
    assert ReserveDeficit().is_present is False
    assert ReserveDeficit().as_payload()["reserve_deficit"] == 0.0
