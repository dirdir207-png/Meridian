import sqlite3

from meridian.observations import ObservationRepository
from meridian.providers.base import (
    NormalizedAccount,
    NormalizedTransaction,
    ProviderSnapshot,
)


def snapshot(*, complete=True):
    return ProviderSnapshot(
        connection_external_id="conn-1", connection_name="Crew",
        accounts=(NormalizedAccount("acct-1", "Checking", "checking", 100.0, source_updated_at="2026-09-10T10:00:00Z"),),
        transactions=(NormalizedTransaction("txn-1", "acct-1", -5.0, "2026-09-10T09:00:00Z", "Coffee", "posted", source_updated_at="2026-09-10T09:01:00Z"),),
        is_complete=complete,
    )


def test_observations_are_append_only_and_replay_is_idempotent(tmp_path):
    repo = ObservationRepository(str(tmp_path / "obs.db"))
    first = repo.append_snapshot(provider="crew", snapshot=snapshot(), observed_at="2026-09-10T10:02:00Z", confidence=.8, assumptions=["source complete"])
    second = repo.append_snapshot(provider="crew", snapshot=snapshot(), observed_at="2026-09-10T10:02:00Z", confidence=.8, assumptions=["source complete"])
    assert [item.id for item in second] == [item.id for item in first]
    assert all(item.data_mode == "actual" and item.payload_hash for item in first)
    with sqlite3.connect(tmp_path / "obs.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM financial_observations").fetchone()[0] == 2


def test_partial_snapshot_is_explicit_and_provenance_is_preserved(tmp_path):
    repo = ObservationRepository(str(tmp_path / "obs.db"))
    records = repo.append_snapshot(provider="crew", snapshot=snapshot(complete=False), observed_at="2026-09-10T10:02:00Z")
    assert {record.freshness for record in records} == {"partial"}
    assert records[0].source_updated_at == "2026-09-10T10:00:00Z"
    assert records[0].assumptions == ()


def test_snapshot_identity_changes_when_observed_data_changes(tmp_path):
    repo = ObservationRepository(str(tmp_path / "obs.db"))
    first = repo.append_snapshot(provider="crew", snapshot=snapshot(), observed_at="2026-09-10T10:02:00Z")
    changed = snapshot()
    changed = ProviderSnapshot(changed.connection_external_id, changed.connection_name, changed.accounts, (
        NormalizedTransaction("txn-1", "acct-1", -6.0, "2026-09-10T09:00:00Z", "Coffee", "posted"),), is_complete=True)
    second = repo.append_snapshot(provider="crew", snapshot=changed, observed_at="2026-09-10T10:03:00Z")
    assert first[0].snapshot_id != second[0].snapshot_id

import os
import sys
import tempfile

import pytest

if "app" not in sys.modules:
    os.environ["DB_FILE"] = os.path.join(tempfile.mkdtemp(prefix="meridian_observations_api_"), "savings_data.db")
import app as simplecrew


@pytest.fixture
def observation_api_client(monkeypatch, tmp_path):
    repository = ObservationRepository(str(tmp_path / "financial.db"))
    monkeypatch.setitem(simplecrew.app.config, "MERIDIAN_REPOSITORY_FACTORY", lambda: repository)
    monkeypatch.setattr(simplecrew.login_manager, "_user_callback", lambda value: simplecrew.User(value, "obs-user", "obs@example.com"))
    client = simplecrew.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "obs-user"
        session["_fresh"] = True
    return client, repository


def test_observation_api_requires_authentication(observation_api_client):
    client, _ = observation_api_client
    with client.session_transaction() as session:
        session.clear()
    assert client.get("/api/meridian/observations").status_code in (302, 401)


def test_observation_api_returns_metadata_without_payload(observation_api_client):
    client, repository = observation_api_client
    records = repository.append_snapshot(provider="crew", snapshot=snapshot(), observed_at="2026-09-10T10:02:00Z")
    response = client.get("/api/meridian/observations")
    assert response.status_code == 200
    body = response.get_json()
    assert body["data_mode"] == "actual"
    assert body["observations"][0]["snapshot_id"] == records[0].snapshot_id
    assert "payload" not in body["observations"][0]
