"""OS-111's acceptance test: Today and Plan publish ONE number, from ONE rule.

The owner's order, 2026-09-25: *"make Today and Plan publish one 'money you can spend' number
instead of two."* The acceptance criterion is therefore not "both call the same helper" — it is
that the two payloads, built from the SAME repository, state the SAME figure. A test that asserted
each side against its own expected constant could stay green while the two drifted apart again,
which is exactly how the product ended up with two numbers in the first place.

So every case below builds BOTH payloads from one seeded database and compares them:

* the owner's worked example (total 1000, bill reserve 100, emergency fund 100 -> 800);
* his D-019 overdraft (424.90 against a -324.90 reserve -> 100.00);
* a funded reserve, where the reserve's money is counted and then set aside;
* a goal pocket alongside a spend pocket, i.e. two different reasons to set money aside;
* no pockets at all, so nothing is set aside;
* no money accounts at all, where both must decline to state a figure rather than invent 0.00.

The Plan side also asserts its own partition: Bills + Goals + Available == its published
`cash_total`, which is what stops the map's three stations from silently ceasing to add up.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.funding_repo import FundingRuleRepository
from meridian.repository import FinancialRepository


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "agreement.db")


def _env(db):
    return (
        FinancialRepository(db),
        CommitmentRepository(db),
        FundingRuleRepository(db),
    )


def _seed_account(
    graph, run, *, external_id, name, account_type, balance, available=None, goal_target=None
):
    return graph.upsert_account(
        provider="crew",
        external_id=external_id,
        name=name,
        account_type=account_type,
        balance=balance,
        available_balance=balance if available is None else available,
        goal_target=goal_target,
        connection_id=run.connection_id,
        source_updated_at="2026-09-25T09:00:00Z",
        synced_at="2026-09-25T09:00:00Z",
    )


def _seed(db, accounts, *, reserve=None):
    """One complete provider read, so both workspaces see the same observations."""
    graph, commitments, rules = _env(db)
    run = graph.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    seeded = {}
    for spec in accounts:
        seeded[spec["name"]] = _seed_account(graph, run, **spec)
    graph.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=len(accounts),
        transactions_synced=0,
        errors=0,
    )
    if reserve is not None:
        graph.upsert_bill_reserve(
            provider="crew",
            external_id="reserve-1",
            total_reserved_amount=reserve,
            observed_at="2026-09-25T09:00:00Z",
        )
    return graph, commitments, rules, seeded


def _both(graph, commitments, rules):
    from meridian.services.plan import build_plan
    from meridian.services.today import build_today

    today = build_today(graph, commitments, rules, now=datetime.now(timezone.utc))
    plan = build_plan(graph, commitments, rules, as_of=date(2026, 9, 25))
    return today, plan


def _available(plan):
    segments = plan["allocation"]["segments"]
    return Decimal(str({s["label"]: s["amount"] for s in segments}["Available"]))


def _assert_one_number(today, plan):
    figure = today["safe_to_spend"]["amount"]
    assert figure is not None, "Today declined to state a figure; this case expects one"
    assert Decimal(str(figure)) == _available(plan), (
        "Today and Plan publish DIFFERENT money-you-can-spend numbers from the same data, which "
        "is the defect OS-111 exists to remove"
    )
    # And the stations still partition the base they are drawn against.
    segments = plan["allocation"]["segments"]
    assert sum(Decimal(str(s["amount"])) for s in segments) == Decimal(
        str(plan["allocation"]["cash_total"])
    )
    return figure


def test_the_owners_worked_example_is_one_number(db):
    """Total 1000 (checking 400 + spend pocket 400 + emergency fund 100 + a 100 reserve),
    emergency fund and reserve set aside -> 800.00 on BOTH workspaces."""
    graph, commitments, rules, _ = _seed(
        db,
        [
            {"external_id": "checking", "name": "Checking", "account_type": "checking", "balance": 400.0},
            {"external_id": "spend", "name": "Safe to Spend", "account_type": "pocket", "balance": 400.0},
            {"external_id": "emergency", "name": "Emergency Fund", "account_type": "pocket", "balance": 100.0},
        ],
        reserve=100.0,
    )

    today, plan = _both(graph, commitments, rules)

    assert _assert_one_number(today, plan) == Decimal("800.00")
    assert Decimal(str(plan["allocation"]["cash_total"])) == Decimal("1000.00")
    assert today["safe_to_spend"]["breakdown"]["lines"] == [
        {"label": "Total balance", "amount": 1000.00},
        {"label": "Emergency Fund", "amount": -100.00},
        {"label": "Bill reserve", "amount": -100.00},
    ]


def test_the_overdraft_case_is_one_number_and_still_100(db):
    """D-019's case, now falling out of the one rule: 424.90 against a -324.90 reserve is 100.00.

    Under the old split, Today said 100.00 (its own deficit term) and Plan said 0.00 (clamped).
    """
    graph, commitments, rules, _ = _seed(
        db,
        [
            {
                "external_id": "spend",
                "name": "Safe to Spend",
                "account_type": "pocket",
                "balance": 424.90,
            }
        ],
        reserve=-324.90,
    )

    today, plan = _both(graph, commitments, rules)

    assert _assert_one_number(today, plan) == Decimal("100.00")
    # The reserve is inside the total rather than a second subtraction, and the panel says so.
    assert [line["label"] for line in today["safe_to_spend"]["breakdown"]["lines"]] == [
        "Total balance"
    ]
    assert "overdrawn by $324.90" in today["safe_to_spend"]["breakdown"]["explanation"]


def test_a_funded_reserve_does_not_move_the_figure_on_either_workspace(db):
    graph, commitments, rules, _ = _seed(
        db,
        [
            {
                "external_id": "spend",
                "name": "Safe to Spend",
                "account_type": "pocket",
                "balance": 300.0,
            }
        ],
        reserve=200.0,
    )

    today, plan = _both(graph, commitments, rules)

    assert _assert_one_number(today, plan) == Decimal("300.00")
    assert Decimal(str(plan["allocation"]["cash_total"])) == Decimal("500.00")


def test_a_goal_pocket_and_a_spend_pocket_agree(db):
    """Two different reasons to set money aside, one figure: the spend pocket is exempt, the goal
    pocket is a station, and both workspaces read the same two facts."""
    graph, commitments, rules, seeded = _seed(
        db,
        [
            {"external_id": "checking", "name": "Checking", "account_type": "checking", "balance": 120.0},
            {"external_id": "spend", "name": "Safe to Spend", "account_type": "pocket", "balance": 250.0},
            # A goal target is what makes this a goal pocket; the money in it is still a balance.
            {
                "external_id": "vacation",
                "name": "Vacation",
                "account_type": "pocket",
                "balance": 500.0,
                "goal_target": 2000.0,
            },
        ],
    )
    commitments.create(
        type=CommitmentType.GOAL,
        name="Vacation",
        target_amount=2000.0,
        funded_amount=500.0,
        backing_account_id=seeded["Vacation"].id,
    )

    today, plan = _both(graph, commitments, rules)

    # 120 + 250 + 500 = 870, less the 500 set aside in the goal pocket.
    assert _assert_one_number(today, plan) == Decimal("370.00")
    by_label = {s["label"]: Decimal(str(s["amount"])) for s in plan["allocation"]["segments"]}
    assert by_label["Goals"] == Decimal("500.0")


def test_with_no_pockets_nothing_is_set_aside_and_both_say_so(db):
    graph, commitments, rules, _ = _seed(
        db,
        [
            {"external_id": "checking", "name": "Checking", "account_type": "checking", "balance": 210.0},
            {"external_id": "savings", "name": "Savings", "account_type": "savings", "balance": 90.0},
        ],
    )

    today, plan = _both(graph, commitments, rules)

    assert _assert_one_number(today, plan) == Decimal("300.00")
    assert [line["label"] for line in today["safe_to_spend"]["breakdown"]["lines"]] == [
        "Total balance"
    ]


def test_both_decline_to_state_a_figure_when_nothing_holds_money(db):
    """Neither workspace may invent a 0.00: that would claim an observation the read did not
    make. Today withholds the figure and says unavailable; Plan's partition is three zeros."""
    graph, commitments, rules, _ = _seed(
        db,
        [
            {
                "external_id": "card",
                "name": "Card",
                "account_type": "credit",
                "balance": -420.0,
            }
        ],
    )

    today, plan = _both(graph, commitments, rules)

    assert today["safe_to_spend"]["amount"] is None
    assert today["safe_to_spend"]["status"] == "unavailable"
    assert today["safe_to_spend"]["breakdown"] is None
    assert [s["amount"] for s in plan["allocation"]["segments"]] == [0.0, 0.0, 0.0]
    assert plan["allocation"]["cash_total"] == 0.0


def test_a_rename_cannot_split_the_two_workspaces(db):
    """The pocket-identity rule is shared, so a name Meridian does not know moves BOTH figures
    together. Before OS-111 a rename moved Today's basis silently and left Plan untouched."""
    graph, commitments, rules, _ = _seed(
        db,
        [
            {"external_id": "checking", "name": "Checking", "account_type": "checking", "balance": 100.0},
            {"external_id": "spend", "name": "Spending money", "account_type": "pocket", "balance": 60.0},
        ],
    )

    today, plan = _both(graph, commitments, rules)

    # Unknown name, so the pocket is set aside on both sides: 160 - 60 = 100.
    assert _assert_one_number(today, plan) == Decimal("100.00")
    assert today["safe_to_spend"]["breakdown"]["spend_pocket"] is None
