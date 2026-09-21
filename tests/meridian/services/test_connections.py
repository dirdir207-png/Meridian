import json

from meridian.connections import ConnectionRepository, ConnectionState
from meridian.connectors.calendar import READ_ONLY_CALENDAR_SCOPE
from meridian.connectors.email import READ_ONLY_GMAIL_SCOPE
from meridian.repository import FinancialRepository
from meridian.services.connections import build_connections, get_connection_detail


def _financial_connection(graph: FinancialRepository) -> None:
    run = graph.begin_sync_run(
        provider="crew",
        connection_external_id="private-household-id",
        connection_name="Crew",
    )
    graph.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=0,
        transactions_synced=0,
        errors=0,
    )


def test_connections_group_money_evidence_and_time_without_secret_fields(tmp_path):
    graph = FinancialRepository(str(tmp_path / "financial.db"))
    authorizations = ConnectionRepository(graph.db_path)
    _financial_connection(graph)
    gmail = authorizations.upsert(
        kind="gmail",
        display_name="Gmail",
        state=ConnectionState.CONNECTED,
        granted_scopes=(READ_ONLY_GMAIL_SCOPE,),
        last_successful_at="2026-08-31T07:47:00Z",
        retention_days=365,
    )
    authorizations.upsert(
        kind="calendar",
        display_name="Google Calendar",
        state=ConnectionState.CONNECTED,
        granted_scopes=(READ_ONLY_CALENDAR_SCOPE,),
        last_successful_at="2026-08-31T07:52:00Z",
        retention_days=90,
    )

    payload = build_connections(graph, authorizations, selected_id=gmail.public_id)

    assert [group["kind"] for group in payload["groups"]] == [
        "money",
        "evidence",
        "time",
    ]
    assert payload["selected"]["public_id"] == gmail.public_id
    assert payload["selected"]["permissions"] == [
        "Read bills, statements, and receipts"
    ]
    assert payload["selected"]["safeguards"]["read_only"] is True
    serialized = json.dumps(payload)
    assert "private-household-id" not in serialized
    assert "access_token" not in serialized
    assert "external_id" not in serialized


def test_connection_detail_is_absent_for_unknown_public_id(tmp_path):
    graph = FinancialRepository(str(tmp_path / "financial.db"))
    authorizations = ConnectionRepository(graph.db_path)

    assert get_connection_detail(authorizations, "gmail_missing") is None


# --- OS-067: a stored authorization is not proof the credential works --------------
#
# The live failure this guards: the Connections view reported Gmail "Connected" while
# all four Gmail refresh tokens had been rejected with HTTP 400 for days, so nothing
# told the owner to act. `state` is the AUTHORIZATION's state and must stay honest;
# `credential` is the separate, stronger fact from actually exercising the credential.

def _conn_record():
    from meridian.connections import ConnectionRecord

    return ConnectionRecord(
        public_id="gmail-dead", kind="gmail", display_name="Gmail",
        state=ConnectionState.CONNECTED, granted_scopes=(),
        last_successful_at="2026-09-06", retention_days=365,
        created_at="2026-09-06", updated_at="2026-09-06",
    )


def test_a_connection_with_no_observed_credential_use_claims_nothing():
    from meridian.services.connections import _authorization_payload

    payload = _authorization_payload(_conn_record(), None)
    assert payload["state"] == ConnectionState.CONNECTED.value
    assert "credential" not in payload, (
        "no credential has been exercised, so no health verdict may be invented"
    )


def test_a_dead_credential_is_surfaced_and_keeps_the_honest_authorization_state():
    from meridian.services.connections import _authorization_payload

    payload = _authorization_payload(
        _conn_record(),
        {"available": False, "reason": "reauthorize_required",
         "detail": "Google token refresh failed (HTTP 400)",
         "observed_at": "2026-09-20T00:00:00Z"},
    )
    assert payload["state"] == ConnectionState.CONNECTED.value, (
        "the authorization is still connected; reporting otherwise would be a second lie"
    )
    assert payload["credential"]["available"] is False
    assert payload["credential"]["reason"] == "reauthorize_required"


def test_the_remedy_is_actionable_and_never_leaks_the_raw_provider_error():
    from meridian.services.connections import _authorization_payload

    payload = _authorization_payload(
        _conn_record(),
        {"available": False, "reason": "reauthorize_required",
         "detail": "Google token refresh failed (HTTP 400)"},
    )
    action = payload["credential"]["action"]
    assert "Re-authorize" in action
    assert "detail" not in payload["credential"], "raw provider text must not reach the UI"


def test_an_unrecognised_reason_still_gives_the_owner_something_to_do():
    from meridian.services.connections import _authorization_payload

    payload = _authorization_payload(_conn_record(), {"available": False, "reason": "novel"})
    assert payload["credential"]["action"], "every failure must come with a next step"


def test_a_working_credential_raises_no_warning():
    from meridian.services.connections import _authorization_payload

    payload = _authorization_payload(_conn_record(), {"available": True})
    assert "credential" not in payload


def test_build_connections_threads_health_into_the_rows(tmp_path):
    from meridian.connections import ConnectionRepository
    from meridian.repository import FinancialRepository

    graph = FinancialRepository(str(tmp_path / "graph.db"))
    repo = ConnectionRepository(graph.db_path if hasattr(graph, "db_path") else str(tmp_path / "graph.db"))
    repo.upsert(
        kind="gmail", display_name="Gmail", state=ConnectionState.CONNECTED,
        granted_scopes=(), last_successful_at="2026-09-06", retention_days=365,
    )
    without = build_connections(graph, repo)
    assert not any("credential" in row for group in without["groups"] for row in group["connections"])

    with_health = build_connections(
        graph, repo, credential_health={"gmail": {"available": False, "reason": "reauthorize_required"}}
    )
    rows = [row for group in with_health["groups"] for row in group["connections"]]
    assert any(row.get("credential", {}).get("available") is False for row in rows), (
        "a recorded credential failure must reach the row the owner reads"
    )
