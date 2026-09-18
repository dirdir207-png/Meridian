"""A bill a complete provider read concluded is gone must stay visible in Plan.

Handoff C02 archives the row locally: it keeps its history and stops being a
current obligation. Dropping it silently from the Plan workspace re-creates
exactly the experience the owner reported as data loss, so the read model reports
it with provenance instead — and never as a live obligation.

The label logic lives in ``static/js/meridian/absent-bills.js`` so it can be
executed here, rather than only asserted as text present in a file.
"""

import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.funding_repo import FundingRuleRepository
from meridian.repository import FinancialRepository
from meridian.services.plan import build_plan

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.fixture
def env(tmp_path):
    db = str(tmp_path / "plan.db")
    return FinancialRepository(db), CommitmentRepository(db), FundingRuleRepository(db)


def _absent_bill(commitments, legacy_id="bill-gone", name="T-Mobile", amount=70.0):
    bill = commitments.create(
        type=CommitmentType.BILL,
        name=name,
        amount=amount,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id=legacy_id,
    )
    commitments.mark_absent_bills(provider="crew", observed_external_ids=("bill-kept",))
    return bill


def test_an_absent_bill_is_reported_with_its_provenance(env):
    graph, commitments, rules = env
    _absent_bill(commitments)

    plan = build_plan(graph, commitments, rules, as_of=date(2026, 9, 1))

    assert len(plan["absent_bills"]) == 1
    reported = plan["absent_bills"][0]
    assert reported["name"] == "T-Mobile"
    assert reported["provider"] == "crew"
    assert reported["absent_since"]


def test_an_absent_bill_is_never_presented_as_a_current_obligation(env):
    graph, commitments, rules = env
    _absent_bill(commitments)

    plan = build_plan(graph, commitments, rules, as_of=date(2026, 9, 1))

    reported = plan["absent_bills"][0]
    # A last known figure is not a current obligation.
    assert "amount" not in reported
    assert "funded_amount" not in reported
    assert "currency" not in reported
    # And it is gone from the live commitment list it used to sit in.
    assert plan["commitments"] == []


def test_a_bill_the_provider_still_returns_stays_current(env):
    graph, commitments, rules = env
    commitments.create(
        type=CommitmentType.BILL,
        name="Verizon",
        amount=95.0,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-kept",
    )
    _absent_bill(commitments)

    plan = build_plan(graph, commitments, rules, as_of=date(2026, 9, 1))

    assert [c["name"] for c in plan["commitments"]] == ["Verizon"]
    assert [b["name"] for b in plan["absent_bills"]] == ["T-Mobile"]


def test_the_absent_list_is_newest_conclusion_first_and_bounded(env):
    graph, commitments, rules = env
    older = commitments.create(
        type=CommitmentType.BILL,
        name="Old",
        amount=70.0,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-old",
    )
    commitments.mark_absent_bills(
        provider="crew", observed_external_ids=("x",), absent_since="2026-09-01T00:00:00Z"
    )
    commitments.create(
        type=CommitmentType.BILL,
        name="New",
        amount=10.0,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-new",
    )
    commitments.mark_absent_bills(
        provider="crew", observed_external_ids=("x",), absent_since="2026-09-10T00:00:00Z"
    )

    listed = commitments.list_absent_bills()

    assert [bill.name for bill in listed] == ["New", "Old"]
    assert len(commitments.list_absent_bills(limit=1)) == 1
    assert older.name == "Old"


def test_the_absent_list_rejects_an_unbounded_request(env):
    _, commitments, _r = env

    with pytest.raises(ValueError):
        commitments.list_absent_bills(limit=0)
    with pytest.raises(ValueError):
        commitments.list_absent_bills(limit=201)


def test_the_absent_list_is_empty_when_nothing_was_concluded_absent(env):
    graph, commitments, rules = env
    commitments.create(
        type=CommitmentType.BILL,
        name="Verizon",
        amount=95.0,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-kept",
    )

    plan = build_plan(graph, commitments, rules, as_of=date(2026, 9, 1))

    assert plan["absent_bills"] == []


def _run_node(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise AssertionError(f"node failed:\n{result.stdout}\n{result.stderr}")


def test_absent_bill_labels_state_provenance_without_money():
    _run_node(
        r"""
      const { describeAbsentBill } = await import('./static/js/meridian/absent-bills.js');
      const check = (condition, message) => { if (!condition) throw new Error(message); };

      const view = describeAbsentBill({
        id: 12,
        name: 'T-Mobile',
        provider: 'crew',
        absent_since: '2026-09-11T21:04:19.009886Z',
      });

      check(view.name === 'T-Mobile', 'name');
      check(view.source === 'Crew no longer returns this bill', 'provider-labelled source');
      check(view.absent === 'Concluded absent 2026-09-11', 'conclusion date');
      check(view.note === 'Its history is kept and no money is scheduled for it', 'note');
      check(!('amount' in view) && !('currency' in view), 'no amount may be presented as current');

      const bare = describeAbsentBill({ name: 'Bare' });
      check(bare.source === 'Provider no longer returns this bill', 'unnamed provider degrades honestly');
      check(bare.absent === 'Concluded absent', 'missing conclusion date is explicit');
      check(bare.note.length > 0, 'the note is always present');
      """
    )


def test_the_plan_workspace_has_a_place_for_absent_bills():
    html = _read("templates/meridian/partials/plan.html")
    assert "data-absent-bills" in html
    assert "data-absent-bill-list" in html
    assert "No longer returned" in html
    assert "nothing was" in html
    # Hidden until something is actually reported, so it cannot read as a
    # permanent fixture of the workspace.
    assert 'data-absent-bills hidden' in html


def _code_without_comments(source):
    return "\n".join(line.split("//")[0] for line in source.splitlines())


def test_the_absent_renderer_shows_provenance_and_no_amount():
    js = _read("static/js/meridian/plan.js")
    assert "function renderAbsentBills" in js
    assert "renderAbsentBills(root, plan)" in js
    assert "describeAbsentBill" in js
    body = _code_without_comments(
        js.split("function absentBillRow")[1].split("function renderAbsentBills")[0]
    )
    # A last known figure is not a current obligation, and there is nothing to change.
    assert "formatCurrency" not in body
    assert "funding" not in body
    assert "button" not in body
