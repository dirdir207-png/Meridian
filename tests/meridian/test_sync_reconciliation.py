"""Absent provider records must be reconciled with explicit completeness evidence.

A record the provider stops returning used to stay ``is_active = 1`` forever with
a frozen ``source_updated_at`` (handoff finding C02). Because workspace freshness
is ``min(source_updated_at)`` over in-scope accounts, that single orphan pinned
the whole app to ``stale`` indefinitely while transactions stayed current.

The fix is reconciliation, **not** a weaker freshness rule: only a complete,
error-free provider read may conclude that a record is gone, and the conclusion
is recorded as explicit evidence on the row.
"""

from datetime import datetime, timedelta, timezone

import pytest

from meridian.providers.base import NormalizedAccount, ProviderSnapshot
from meridian.repository import FinancialRepository
from meridian.services.today import data_freshness
from meridian.sync import sync_provider


@pytest.fixture
def repository(tmp_path):
    return FinancialRepository(str(tmp_path / "financial.db"))


class SnapshotAdapter:
    provider_name = "crew"
    connection_external_id = "crew-household"
    connection_name = "Crew"

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def fetch_snapshot(self):
        return self._snapshot


def _account(external_id, observed_at):
    return NormalizedAccount(
        external_id=external_id,
        name=external_id,
        account_type="pocket",
        balance=1.0,
        source_updated_at=observed_at,
    )


def _snapshot(account_ids, observed_at, *, is_complete=True, errors=()):
    return ProviderSnapshot(
        connection_external_id="crew-household",
        connection_name="Crew",
        accounts=tuple(_account(item, observed_at) for item in account_ids),
        transactions=(),
        is_complete=is_complete,
        errors=tuple(errors),
    )


def _observed_at(now):
    return now.isoformat().replace("+00:00", "Z")


def _seed_account(repository, external_id, source_updated_at):
    """Seed one account as the last known observation of it."""
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    account = repository.upsert_account(
        provider="crew",
        external_id=external_id,
        name=external_id,
        account_type="pocket",
        balance=0.0,
        connection_id=run.connection_id,
        source_updated_at=source_updated_at,
    )
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=0,
        errors=0,
    )
    return account, run.connection_id


def test_a_complete_sync_marks_a_vanished_account_absent(repository):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    account, _ = _seed_account(
        repository, "deleted-pocket", _observed_at(now - timedelta(days=4))
    )

    sync_provider(
        SnapshotAdapter(_snapshot(["checking"], _observed_at(now))),
        repository,
    )

    reconciled = repository.get_account(account.id)
    assert reconciled.is_active is False
    assert reconciled.absent_since is not None


def test_a_vanished_account_keeps_its_history(repository):
    """Reconciliation archives the row; it must not delete evidence."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    account, connection_id = _seed_account(
        repository, "deleted-pocket", _observed_at(now - timedelta(days=4))
    )
    repository.upsert_transaction(
        provider="crew",
        external_id="historical-1",
        account_id=account.id,
        amount=-12.0,
        occurred_at=_observed_at(now - timedelta(days=5)),
        description="Coffee",
        status="posted",
    )

    sync_provider(
        SnapshotAdapter(_snapshot(["checking"], _observed_at(now))),
        repository,
    )

    assert repository.get_account(account.id) is not None
    stored, _ = repository.list_transactions(account_id=account.id)
    assert [item.external_id for item in stored] == ["historical-1"]
    assert stored[0].account_id == account.id


def test_an_incomplete_sync_does_not_conclude_an_account_is_gone(repository):
    """Absence alone is not deletion: partial reads must not archive."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    account, _ = _seed_account(
        repository, "deleted-pocket", _observed_at(now - timedelta(days=4))
    )

    sync_provider(
        SnapshotAdapter(
            _snapshot(
                ["checking"],
                _observed_at(now),
                is_complete=False,
                errors=("transaction page unavailable",),
            )
        ),
        repository,
    )

    assert repository.get_account(account.id).is_active is True
    assert repository.get_account(account.id).absent_since is None


def test_reconciliation_is_scoped_to_the_providers_own_connection(repository):
    """A different provider's account must never be archived by this read."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    other = repository.begin_sync_run(
        provider="simplefin",
        connection_external_id="simplefin-household",
        connection_name="SimpleFIN",
    )
    untouched = repository.upsert_account(
        provider="simplefin",
        external_id="other-bank-account",
        name="Other",
        account_type="checking",
        balance=5.0,
        connection_id=other.connection_id,
        source_updated_at=_observed_at(now - timedelta(days=30)),
    )
    repository.finish_sync_run(
        other.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=0,
        errors=0,
    )
    _seed_account(repository, "deleted-pocket", _observed_at(now - timedelta(days=4)))

    sync_provider(
        SnapshotAdapter(_snapshot(["checking"], _observed_at(now))),
        repository,
    )

    assert repository.get_account(untouched.id).is_active is True
    assert repository.get_account(untouched.id).absent_since is None


def test_a_quiet_account_the_provider_still_returns_stays_active(repository):
    """An unchanged account is not an absent account."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    quiet, _ = _seed_account(
        repository, "quiet-pocket", _observed_at(now - timedelta(days=40))
    )

    sync_provider(
        SnapshotAdapter(_snapshot(["quiet-pocket"], _observed_at(now))),
        repository,
    )

    assert repository.get_account(quiet.id).is_active is True
    assert repository.get_account(quiet.id).absent_since is None


def test_a_reappearing_account_is_reactivated(repository):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    account, _ = _seed_account(
        repository, "deleted-pocket", _observed_at(now - timedelta(days=4))
    )
    sync_provider(
        SnapshotAdapter(_snapshot(["checking"], _observed_at(now))),
        repository,
    )
    assert repository.get_account(account.id).is_active is False

    sync_provider(
        SnapshotAdapter(
            _snapshot(["checking", "deleted-pocket"], _observed_at(now))
        ),
        repository,
    )

    restored = repository.get_account(account.id)
    assert restored.is_active is True
    assert restored.absent_since is None


def test_an_absent_account_no_longer_pins_the_workspace_to_stale(repository):
    """The reported symptom: one orphaned row forced ``stale`` forever."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _seed_account(repository, "deleted-pocket", _observed_at(now - timedelta(days=4)))

    sync_provider(
        SnapshotAdapter(_snapshot(["checking"], _observed_at(now))),
        repository,
    )

    freshness = data_freshness(repository, now=now + timedelta(minutes=1))

    assert freshness["status"] == "fresh"


def test_freshness_is_still_stale_when_the_sync_stops_succeeding(repository):
    """The safety rule must still catch a view we cannot vouch for."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    sync_provider(
        SnapshotAdapter(_snapshot(["checking"], _observed_at(now))),
        repository,
    )

    freshness = data_freshness(repository, now=now + timedelta(hours=25))

    assert freshness["status"] == "stale"


def test_freshness_is_still_stale_while_an_account_remains_unreconciled(repository):
    """Before any complete read concludes absence, the row still pins status."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _seed_account(repository, "deleted-pocket", _observed_at(now - timedelta(days=4)))

    freshness = data_freshness(repository, now=now + timedelta(minutes=1))

    assert freshness["status"] == "stale"


def test_an_errored_read_does_not_conclude_an_account_is_gone(repository):
    """A read that reported errors is not complete evidence, whatever it claims."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    account, _ = _seed_account(
        repository, "deleted-pocket", _observed_at(now - timedelta(days=4))
    )

    sync_provider(
        SnapshotAdapter(
            _snapshot(
                ["checking"],
                _observed_at(now),
                is_complete=True,
                errors=("accounts page truncated",),
            )
        ),
        repository,
    )

    assert repository.get_account(account.id).is_active is True
    assert repository.get_account(account.id).absent_since is None


def test_reconciliation_records_absence_once(repository):
    """Absence is evidence of one observation, not a value refreshed every read."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    account, _ = _seed_account(
        repository, "deleted-pocket", _observed_at(now - timedelta(days=4))
    )
    adapter = SnapshotAdapter(_snapshot(["checking"], _observed_at(now)))

    sync_provider(adapter, repository)
    first = repository.get_account(account.id).absent_since
    assert first is not None

    sync_provider(adapter, repository)

    assert repository.get_account(account.id).absent_since == first


def test_a_connection_with_no_observed_accounts_is_not_fresh(repository):
    """Archiving everything must not manufacture a current view."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    _seed_account(repository, "deleted-pocket", _observed_at(now - timedelta(days=4)))

    sync_provider(
        SnapshotAdapter(_snapshot([], _observed_at(now))),
        repository,
    )

    freshness = data_freshness(repository, now=now + timedelta(minutes=1))

    assert freshness["status"] == "stale"
