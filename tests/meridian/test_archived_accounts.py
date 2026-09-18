"""An account a complete provider read concluded is gone must stay visible.

Handoff C02/C04 archive the row locally: it keeps its history and stops being a
current observation. Dropping it silently from the Accounts workspace re-creates
exactly the experience the owner reported as data loss, so the read model reports
it with provenance instead — and never as a current balance.

The label logic lives in ``static/js/meridian/archived-accounts.js`` so it can be
executed here, rather than only asserted as text present in a file.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from meridian.repository import FinancialRepository
from meridian.services.accounts import build_accounts

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.fixture
def repository(tmp_path):
    return FinancialRepository(str(tmp_path / "financial.db"))


def _connection(repository):
    """One provider connection, as the owner really has one Crew connection."""
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=0,
        transactions_synced=0,
        errors=0,
    )
    return run.connection_id


def _seed_account(
    repository,
    connection_id,
    external_id,
    name,
    *,
    balance=42.0,
    observed_at="2026-09-07T13:55:04.923476Z",
):
    """Seed one account as the last known observation of it."""
    return repository.upsert_account(
        provider="crew",
        external_id=external_id,
        name=name,
        account_type="pocket",
        balance=balance,
        connection_id=connection_id,
        source_updated_at=observed_at,
    )


def _archive(repository, connection_id, *, observed, absent_since):
    """Record what one complete read of this connection did and did not return."""
    return repository.mark_absent_accounts(
        provider="crew",
        connection_id=connection_id,
        observed_external_ids=observed,
        absent_since=absent_since,
    )


def _add_transaction(repository, account, external_id):
    repository.upsert_transaction(
        provider="crew",
        external_id=external_id,
        account_id=account.id,
        amount=-12.0,
        occurred_at="2026-09-06T10:00:00Z",
        description="Coffee",
        status="posted",
    )


def test_an_archived_account_is_reported_with_its_provenance(repository):
    connection_id = _connection(repository)
    account = _seed_account(repository, connection_id, "deleted-pocket", "Free to Spend")
    _add_transaction(repository, account, "historical-1")
    _add_transaction(repository, account, "historical-2")
    _archive(
        repository,
        connection_id,
        observed=(),
        absent_since="2026-09-11T14:09:37Z",
    )

    archived = build_accounts(repository)["archived"]

    assert len(archived) == 1
    entry = archived[0]
    assert entry["id"] == account.id
    assert entry["name"] == "Free to Spend"
    assert entry["provider"] == "crew"
    assert entry["account_type"] == "pocket"
    assert entry["absent_since"] == "2026-09-11T14:09:37Z"
    assert entry["last_observed_at"] == "2026-09-07T13:55:04.923476Z"
    assert entry["retained_transactions"] == 2


def test_an_archived_account_never_presents_a_balance_as_current(repository):
    """The last known figure is history, not a current balance."""
    connection_id = _connection(repository)
    _seed_account(repository, connection_id, "deleted-pocket", "Free to Spend", balance=1234.56)
    _archive(repository, connection_id, observed=(), absent_since="2026-09-11T14:09:37Z")

    entry = build_accounts(repository)["archived"][0]

    assert "balance" not in entry
    assert "available_balance" not in entry
    assert "currency" not in entry


def test_an_account_the_reader_still_returned_stays_current(repository):
    """Absence is per account: one pocket vanishing must not retire the rest."""
    connection_id = _connection(repository)
    checking = _seed_account(
        repository, connection_id, "checking", "Checking", observed_at="2026-09-11T14:00:00Z"
    )
    vanished = _seed_account(repository, connection_id, "deleted-pocket", "Free to Spend")
    _archive(
        repository,
        connection_id,
        observed=("checking",),
        absent_since="2026-09-11T14:09:37Z",
    )

    payload = build_accounts(repository)
    current_ids = [item["id"] for group in payload["groups"] for item in group["accounts"]]

    assert current_ids == [checking.id]
    # The vanished account is reported, but only through the archived list.
    assert [item["id"] for item in payload["archived"]] == [vanished.id]


def test_the_archived_list_is_newest_conclusion_first_and_bounded(repository):
    """Conclusion order, not row id order, decides what a reader sees first."""
    connection_id = _connection(repository)
    first = _seed_account(repository, connection_id, "first-pocket", "First Pocket")
    second = _seed_account(repository, connection_id, "second-pocket", "Second Pocket")
    third = _seed_account(repository, connection_id, "third-pocket", "Third Pocket")
    # The newest conclusion belongs to the oldest row, so ordering by row id
    # cannot satisfy this test.
    _archive(repository, connection_id, observed=("first-pocket", "second-pocket"),
             absent_since="2026-09-09T00:00:00Z")
    _archive(repository, connection_id, observed=("first-pocket",),
             absent_since="2026-09-10T00:00:00Z")
    _archive(repository, connection_id, observed=(), absent_since="2026-09-11T00:00:00Z")

    archived = build_accounts(repository)["archived"]

    assert [item["id"] for item in archived] == [first.id, second.id, third.id]
    assert [item["absent_since"] for item in archived] == [
        "2026-09-11T00:00:00Z",
        "2026-09-10T00:00:00Z",
        "2026-09-09T00:00:00Z",
    ]
    assert [item["name"] for item in build_accounts(repository, archived_limit=2)["archived"]] == [
        "First Pocket",
        "Second Pocket",
    ]


def test_the_archived_list_is_empty_when_nothing_was_concluded_absent(repository):
    connection_id = _connection(repository)
    _seed_account(
        repository, connection_id, "checking", "Checking", observed_at="2026-09-11T14:00:00Z"
    )

    assert build_accounts(repository)["archived"] == []


def test_the_archived_list_rejects_an_unbounded_request(repository):
    with pytest.raises(ValueError):
        build_accounts(repository, archived_limit=0)


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


def test_archived_account_labels_state_provenance_without_money():
    _run_node(
        r"""
      const { describeArchivedAccount } = await import('./static/js/meridian/archived-accounts.js');
      const check = (condition, message) => { if (!condition) throw new Error(message); };

      const view = describeArchivedAccount({
        id: 7,
        name: 'Free to Spend',
        provider: 'crew',
        account_type: 'pocket',
        absent_since: '2026-09-11T14:09:37Z',
        last_observed_at: '2026-09-07T13:55:04.923476Z',
        retained_transactions: 19,
      });

      check(view.name === 'Free to Spend', 'name');
      check(view.source === 'Crew no longer returns this account', 'provider-labelled source');
      check(view.observed === 'Last observed 2026-09-07', 'observation date');
      check(view.absent === 'Concluded absent 2026-09-11', 'conclusion date');
      check(view.history === '19 transactions kept in Activity', 'history count');
      check(!('balance' in view) && !('currency' in view), 'no amount may be presented as current');

      const single = describeArchivedAccount({
        name: 'Solo', provider: 'crew', retained_transactions: 1,
      });
      check(single.history === '1 transaction kept in Activity', 'singular history');
      check(single.observed === 'No observation is recorded', 'missing observation is explicit');

      const bare = describeArchivedAccount({ name: 'Bare' });
      check(bare.source === 'Provider no longer returns this account', 'unnamed provider degrades honestly');
      check(
        bare.history === 'No transactions are recorded for it',
        'no-history is explicit rather than a zero amount',
      );
      """
    )


def test_transaction_account_labels_mark_archived_context_only():
    _run_node(
        r"""
      const { describeTransactionAccount } = await import('./static/js/meridian/archived-accounts.js');
      const check = (condition, message) => { if (!condition) throw new Error(message); };

      const current = describeTransactionAccount({ account_name: 'Checking', account_archived: false });
      check(current.name === 'Checking', 'current name');
      check(current.archived === false, 'current is not archived');
      check(current.note === '', 'current carries no archived note');

      const archived = describeTransactionAccount({ account_name: 'Free to Spend', account_archived: true });
      check(archived.archived === true, 'archived flag');
      check(archived.note === 'no longer returned by this provider', 'archived note');

      const unnamed = describeTransactionAccount({ account_archived: true });
      check(unnamed.name === '', 'missing name stays empty');
      check(unnamed.archived === false, 'absence cannot be claimed for an account we cannot name');
      check(unnamed.note === '', 'no note without a name');
      """
    )


def test_the_accounts_workspace_has_a_place_for_archived_accounts():
    html = _read("templates/meridian/partials/accounts.html")
    assert "data-archived-accounts" in html
    assert "data-archived-account-list" in html
    assert "No longer returned" in html
    assert "nothing was deleted" in html
    # Hidden until something is actually reported, so it cannot read as a permanent
    # fixture of the workspace.
    assert 'data-archived-accounts hidden' in html


def _code_without_comments(source):
    return "\n".join(
        line.split("//")[0] for line in source.splitlines()
    )


def test_the_archived_renderer_shows_provenance_and_no_amount():
    js = _read("static/js/meridian/accounts.js")
    assert "function renderArchived" in js
    assert "renderArchived(payload.archived || [])" in js
    assert "describeArchivedAccount" in js
    body = _code_without_comments(
        js.split("function archivedAccountRow")[1].split("function renderArchived")[0]
    )
    # A last known figure is not a current balance, and there is nothing to change.
    assert "formatCurrency" not in body
    assert "balance" not in body
    assert "button" not in body
    assert "archivedAccountName" in body


def test_the_activity_ledger_labels_the_account_a_transaction_belongs_to():
    js = _read("static/js/meridian/activity.js")
    assert "describeTransactionAccount" in js
    assert "dataset.rowAccount" in js
    assert "account_archived" not in js.split("describeTransactionAccount")[0]
    # The old dead reference expected a field the API never sent.
    assert "transaction.accountName" not in js
