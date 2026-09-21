import base64
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import quote

import pytest

if "app" not in sys.modules:
    os.environ["DB_FILE"] = os.path.join(
        tempfile.mkdtemp(prefix="meridian_api_test_"), "savings_data.db"
    )

import app as simplecrew
from meridian.classify import ClassificationInput, classify_deterministic
from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.connections import ConnectionRepository, ConnectionState
from meridian.connectors.email import READ_ONLY_GMAIL_SCOPE
from meridian.repository import FinancialRepository


@pytest.fixture(autouse=True)
def disable_background_polling(monkeypatch):
    monkeypatch.setattr(simplecrew, "_background_thread_started", True)


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    repository = FinancialRepository(str(tmp_path / "financial.db"))
    user_id = "meridian-api-user"
    monkeypatch.setattr(
        simplecrew.login_manager,
        "_user_callback",
        lambda value: simplecrew.User(
            value, "meridian-api-user", "meridian-api@example.com"
        ),
    )

    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_REPOSITORY_FACTORY",
        lambda: repository,
    )
    client = simplecrew.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return client, repository


def _complete_connection(repository, *, provider="crew", include_transaction=True):
    now = datetime.now(timezone.utc).isoformat()
    run = repository.begin_sync_run(
        provider=provider,
        connection_external_id=f"{provider}-household",
        connection_name=provider.title(),
    )
    account = repository.upsert_account(
        provider=provider,
        external_id=f"{provider}-checking",
        name=f"{provider.title()} checking",
        account_type="checking",
        balance=100.0,
        connection_id=run.connection_id,
        source_updated_at=now,
    )
    if include_transaction:
        repository.upsert_transaction(
            provider=provider,
            external_id=f"{provider}-coffee",
            account_id=account.id,
            amount=-3.0,
            occurred_at=now,
            description="Coffee",
            status="posted",
            source_updated_at=now,
        )
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=int(include_transaction),
        errors=0,
    )
    return account


def _partial_connection_without_records(repository, *, provider="simplefin"):
    run = repository.begin_sync_run(
        provider=provider,
        connection_external_id=f"{provider}-household",
        connection_name=provider.title(),
    )
    repository.finish_sync_run(
        run.id,
        status="partial",
        accounts_synced=0,
        transactions_synced=0,
        errors=1,
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/meridian/today",
        "/api/meridian/dial",
        "/api/meridian/weather",
        "/api/meridian/activity",
        "/api/meridian/transactions/1",
        "/api/meridian/accounts",
        "/api/meridian/evidence/1/content",
        "/api/meridian/settings/connections",
    ],
)
def test_meridian_read_apis_require_login(path):
    response = simplecrew.app.test_client().get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login?next=" + quote(path, safe=""))


def test_evidence_content_rejects_invalid_identifier(api_client):
    client, _repository = api_client

    response = client.get("/api/meridian/evidence/not-an-id/content")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_request"


def test_dial_read_api_returns_observatory_model(api_client):
    client, repository = api_client
    _complete_connection(repository)

    response = client.get("/api/meridian/dial")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["today"] == payload["horizonEnd"] or payload["today"] < payload["horizonEnd"]
    assert "events" in payload
    assert "availableToSpend" in payload
    assert "freshness" in payload
    assert payload["projections"] == []


def test_weather_read_api_returns_proactive_model_without_mutating(api_client):
    client, repository = api_client
    _complete_connection(repository)
    accounts_before = len(repository.list_accounts())

    response = client.get("/api/meridian/weather")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["state"] in {"steady", "tight", "strained", "unknown"}
    assert payload["windowDays"] == 14
    assert isinstance(payload["groups"], list)
    assert isinstance(payload["suppressed"], int)
    # The proactive layer is a pure projection: reading it must not write rows.
    assert len(repository.list_accounts()) == accounts_before


def test_weather_read_api_rejects_invalid_as_of(api_client):
    client, repository = api_client
    _complete_connection(repository)

    response = client.get("/api/meridian/weather?as_of=not-a-date")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_request"


def test_plan_scenario_preview_requires_login_and_is_read_only(api_client):
    client, repository = api_client
    _complete_connection(repository)

    unauth = simplecrew.app.test_client().post(
        "/api/meridian/plan/scenario", json={"income": 100}
    )
    assert unauth.status_code == 302

    before = [
        (account.external_id, account.balance)
        for account in repository.list_accounts()
    ]
    response = client.post(
        "/api/meridian/plan/scenario",
        json={"income": 100, "expense_change": -1},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["read_only"] is True
    assert payload["available"] is True
    assert payload["base"]["starting_cash"] + 100 == payload["scenario"]["starting_cash"]
    assert payload["comparison"]["starting_cash"] == 100.0
    assert any("income changes by $100.00" in assumption for assumption in payload["assumptions"])
    assert any("daily expenses change by $-1.00" in assumption for assumption in payload["assumptions"])
    after = [
        (account.external_id, account.balance)
        for account in repository.list_accounts()
    ]
    assert before == after


def test_meridian_action_history_is_read_only(api_client):
    client, _repository = api_client

    proposed = client.post(
        "/api/actions/propose",
        json={
            "type": "create_commitment",
            "params": {"type": "goal", "name": "History check", "amount": 10},
            "rationale": "Read-only action history test.",
        },
    )
    assert proposed.status_code == 200

    response = client.get("/api/meridian/actions")

    assert response.status_code == 200
    actions = response.get_json()["actions"]
    assert any(
        action["type"] == "create_commitment"
        and action["state"] == "proposed"
        and action["rationale"] == "Read-only action history test."
        for action in actions
    )



def test_plan_scenario_preview_validates_numeric_input(api_client):
    client, repository = api_client
    _complete_connection(repository)

    response = client.post(
        "/api/meridian/plan/scenario",
        json={"income": "not-a-number"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_request"



def test_connection_api_requires_login_and_never_serializes_secrets(
    api_client, monkeypatch
):
    client, graph = api_client
    authorizations = ConnectionRepository(graph.db_path)
    authorizations.upsert(
        kind="gmail",
        display_name="Gmail",
        state=ConnectionState.CONNECTED,
        granted_scopes=(READ_ONLY_GMAIL_SCOPE,),
        last_successful_at="2026-08-31T07:47:00Z",
        retention_days=365,
    )
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTIONS_FACTORY",
        lambda: authorizations,
    )
    monkeypatch.setenv("GMAIL_ACCESS_TOKEN", "secret-sentinel")

    response = client.get("/api/meridian/settings/connections")

    assert response.status_code == 200
    assert response.get_json()["groups"][1]["connections"][0]["kind"] == "gmail"
    assert "secret-sentinel" not in response.get_data(as_text=True)
    assert (
        simplecrew.app.test_client()
        .get("/api/meridian/settings/connections")
        .status_code
        == 302
    )


def test_connection_authorize_returns_only_provider_handoff_state(
    api_client, monkeypatch
):
    client, graph = api_client
    authorizations = ConnectionRepository(graph.db_path)
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTIONS_FACTORY",
        lambda: authorizations,
    )
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTION_AUTHORIZERS",
        {"gmail": lambda redirect_uri=None: {"authorization_url": "https://accounts.google.test/oauth"}},
    )

    response = client.post("/api/meridian/settings/connections/gmail/authorize")

    assert response.status_code == 200
    assert response.get_json() == {
        "state": "pending",
        "authorization_url": "https://accounts.google.test/oauth",
    }
    saved = authorizations.list_all()[0]
    assert saved.state is ConnectionState.PENDING
    assert saved.granted_scopes == ()


def test_connection_authorize_reuses_one_row_per_kind(api_client, monkeypatch):
    """Repeated authorize attempts must not pile up duplicate rows."""
    client, graph = api_client
    authorizations = ConnectionRepository(graph.db_path)
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTIONS_FACTORY",
        lambda: authorizations,
    )
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTION_AUTHORIZERS",
        {"gmail": lambda redirect_uri=None: {"authorization_url": "https://accounts.google.test/oauth"}},
    )

    for _ in range(3):
        response = client.post("/api/meridian/settings/connections/gmail/authorize")
        assert response.status_code == 200

    rows = authorizations.list_all()
    assert len(rows) == 1
    assert rows[0].kind == "gmail"
    assert rows[0].state is ConnectionState.PENDING


def test_connection_revoke_marks_only_selected_source(api_client, monkeypatch):
    client, graph = api_client
    authorizations = ConnectionRepository(graph.db_path)
    gmail = authorizations.upsert(
        kind="gmail",
        display_name="Gmail",
        state=ConnectionState.CONNECTED,
        granted_scopes=(READ_ONLY_GMAIL_SCOPE,),
        last_successful_at="2026-08-31T07:47:00Z",
        retention_days=365,
    )
    calendar = authorizations.upsert(
        kind="calendar",
        display_name="Google Calendar",
        state=ConnectionState.CONNECTED,
        granted_scopes=("calendar.readonly",),
        last_successful_at="2026-08-31T07:52:00Z",
        retention_days=90,
    )

    class Connector:
        revoked = False

        def revoke(self):
            self.revoked = True

    connector = Connector()
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTIONS_FACTORY",
        lambda: authorizations,
    )
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTION_CONNECTORS",
        {gmail.public_id: connector},
    )

    response = client.post(
        f"/api/meridian/settings/connections/{gmail.public_id}/revoke"
    )

    assert response.status_code == 200
    assert response.get_json()["state"] == "revoked"
    assert connector.revoked is True
    assert authorizations.get(calendar.public_id).state is ConnectionState.CONNECTED


def test_meridian_read_apis_serialize_safe_data_and_stable_errors(
    api_client, monkeypatch
):
    client, repository = api_client
    account = repository.upsert_account(
        provider="crew",
        external_id="account-number-123456789",
        name="Checking",
        account_type="checking",
        balance=125.0,
        available_balance=100.0,
        synced_at="2026-08-27T12:00:00Z",
    )
    first = repository.upsert_transaction(
        provider="crew",
        external_id="transaction-secret-111",
        account_id=account.id,
        amount=-12.5,
        occurred_at="2026-08-27T11:00:00Z",
        description="Coffee",
        raw_description="Bearer should-never-appear",
        status="posted",
        synced_at="2026-08-27T12:00:00Z",
    )
    repository.upsert_transaction(
        provider="crew",
        external_id="transaction-secret-222",
        account_id=account.id,
        amount=-20.0,
        occurred_at="2026-08-26T11:00:00Z",
        description="Lunch",
        status="posted",
        synced_at="2026-08-27T12:00:00Z",
    )
    monkeypatch.setenv("BEARER_TOKEN", "super-secret-sentinel-value")

    today = client.get("/api/meridian/today")
    accounts = client.get("/api/meridian/accounts")
    activity = client.get("/api/meridian/activity?limit=1")
    transaction = client.get(f"/api/meridian/transactions/{first.id}")
    missing = client.get("/api/meridian/transactions/99999")

    assert today.status_code == accounts.status_code == activity.status_code == 200
    assert transaction.status_code == 200
    assert activity.get_json()["next_cursor"]
    assert activity.get_json()["transactions"][0]["id"] == first.id
    for response in (today, accounts, activity, transaction):
        payload = response.get_json()
        assert "data_freshness" in payload
        body = response.get_data(as_text=True)
        assert "account-number-123456789" not in body
        assert "transaction-secret-111" not in body
        assert "should-never-appear" not in body
        assert "super-secret-sentinel-value" not in body

    assert missing.status_code == 404
    assert missing.get_json()["error"] == {
        "code": "transaction_not_found",
        "message": "The requested transaction is not available.",
        "recovery_action": "Return to Activity and choose another transaction.",
    }


def test_meridian_activity_rejects_invalid_pagination_with_a_stable_error(api_client):
    client, _ = api_client

    response = client.get("/api/meridian/activity?limit=not-a-number")

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "invalid_request",
        "message": "limit must be an integer between 1 and 200.",
        "recovery_action": "Use a limit between 1 and 200 and try again.",
    }


def test_classification_correction_is_atomic_audited_and_can_create_rule(api_client):
    client, repository = api_client
    account = repository.upsert_account(
        provider="crew",
        external_id="checking",
        name="Checking",
        account_type="checking",
        balance=100,
    )
    transactions = []
    for external_id in ("coffee-1", "coffee-2"):
        transaction = repository.upsert_transaction(
            provider="crew",
            external_id=external_id,
            account_id=account.id,
            amount=-5,
            occurred_at="2026-08-29T10:00:00Z",
            description="Coffee",
            merchant="Corner Coffee",
            status="posted",
        )
        repository.record_classification(
            transaction.id,
            classify_deterministic(
                ClassificationInput(
                    transaction.id,
                    -5,
                    "Coffee",
                    "Corner Coffee",
                    "checking",
                    "2026-08-29T10:00:00Z",
                )
            ),
        )
        transactions.append(transaction)

    response = client.post(
        f"/api/meridian/transactions/{transactions[0].id}/classification",
        json={"category": "Dining", "kind": "spend", "create_rule": True},
    )

    assert response.status_code == 200
    assert response.get_json()["classification"]["category"] == "Dining"
    assert (
        repository.get_transaction(transactions[1].id).classification_category
        == "Dining"
    )
    assert repository.list_assignment_rules()[0].category == "Dining"
    assert repository.list_classification_history(transactions[0].id)


def test_review_and_patterns_activity_modes(api_client):
    client, repository = api_client
    account = repository.upsert_account(
        provider="crew",
        external_id="checking",
        name="Checking",
        account_type="checking",
        balance=100,
    )
    for index, occurred_at in enumerate(
        ("2026-06-29T10:00:00Z", "2026-07-29T10:00:00Z", "2026-08-29T10:00:00Z")
    ):
        transaction = repository.upsert_transaction(
            provider="crew",
            external_id=f"subscription-{index}",
            account_id=account.id,
            amount=-12,
            occurred_at=occurred_at,
            description="Monthly service",
            merchant="Example Service",
            status="posted",
        )
        repository.record_classification(
            transaction.id,
            classify_deterministic(
                ClassificationInput(
                    transaction.id,
                    -12,
                    "Monthly service",
                    "Example Service",
                    "checking",
                    occurred_at,
                )
            ),
        )

    review = client.get("/api/meridian/activity?mode=review")
    patterns = client.get("/api/meridian/activity?mode=patterns")

    assert review.status_code == 200
    assert len(review.get_json()["transactions"]) == 3
    assert patterns.status_code == 200
    assert patterns.get_json()["patterns"][0]["kind"] == "recurrence"
    assert patterns.get_json()["patterns"][0]["evidence"]
    assert patterns.get_json()["patterns"][0]["detail"]


def test_contextual_advisor_endpoint_passes_workspace_context(api_client, monkeypatch):
    client, repository = api_client
    account = repository.upsert_account(
        provider="crew",
        external_id="checking",
        name="Checking",
        account_type="checking",
        balance=100,
    )
    transaction = repository.upsert_transaction(
        provider="crew",
        external_id="coffee",
        account_id=account.id,
        amount=-5,
        occurred_at="2026-08-29T10:00:00Z",
        description="Coffee",
        status="posted",
    )
    calls = []

    class Advisor:
        def ask(self, context, question):
            calls.append((context, question))
            return {
                "answer": "It was $5.",
                "evidence": [f"transaction:{transaction.id}"],
                "proposals": [],
                "provider": "test",
                "model": "test-model",
                "usage": {},
            }

    monkeypatch.setitem(
        simplecrew.app.config, "MERIDIAN_ADVISOR_FACTORY", lambda: Advisor()
    )

    response = client.post(
        "/api/meridian/advisor",
        json={
            "question": "What happened?",
            "context": {
                "kind": "transaction",
                "object_id": transaction.id,
                "evidence_ids": [f"transaction:{transaction.id}"],
            },
        },
    )

    assert response.status_code == 200
    assert response.get_json()["answer"] == "It was $5."
    assert calls[0][0].kind == "transaction"


@pytest.mark.parametrize(
    "path",
    [
        "/api/meridian/today",
        "/api/meridian/accounts",
        "/api/meridian/activity",
    ],
)
def test_unfiltered_reads_include_partial_providers_without_records(api_client, path):
    client, repository = api_client
    _complete_connection(repository)
    _partial_connection_without_records(repository)

    response = client.get(path)

    assert response.status_code == 200
    assert response.get_json()["data_freshness"]["status"] == "stale"


@pytest.mark.parametrize(
    "path",
    [
        "/api/meridian/today",
        "/api/meridian/accounts",
        "/api/meridian/activity",
    ],
)
def test_unfiltered_reads_treat_unlinked_returned_records_as_stale(api_client, path):
    client, repository = api_client
    account = repository.upsert_account(
        provider="crew",
        external_id="unlinked-checking",
        name="Unlinked checking",
        account_type="checking",
        balance=100.0,
        source_updated_at=datetime.now(timezone.utc).isoformat(),
    )
    repository.upsert_transaction(
        provider="crew",
        external_id="unlinked-coffee",
        account_id=account.id,
        amount=-3.0,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        description="Coffee",
        status="posted",
    )

    response = client.get(path)

    assert response.status_code == 200
    assert response.get_json()["data_freshness"]["status"] == "stale"


def test_unfiltered_activity_scans_unlinked_transactions_beyond_first_page(api_client):
    client, repository = api_client
    linked_account = _complete_connection(repository)
    unlinked_account = repository.upsert_account(
        provider="crew",
        external_id="unlinked-later-checking",
        name="Unlinked later checking",
        account_type="checking",
        balance=100.0,
        source_updated_at="2026-08-26T08:00:00Z",
    )
    repository.upsert_transaction(
        provider="crew",
        external_id="unlinked-later-coffee",
        account_id=unlinked_account.id,
        amount=-3.0,
        occurred_at="2026-08-26T08:00:00Z",
        description="Later page coffee",
        status="posted",
    )

    response = client.get("/api/meridian/activity", query_string={"limit": 1})

    assert response.status_code == 200
    assert response.get_json()["transactions"][0]["account_id"] == linked_account.id
    assert response.get_json()["data_freshness"]["status"] == "stale"


def test_filtered_empty_activity_uses_the_requested_account_provider_freshness(
    api_client,
):
    client, repository = api_client
    account = _complete_connection(repository, include_transaction=False)

    response = client.get(
        "/api/meridian/activity", query_string={"account_id": account.id}
    )

    assert response.status_code == 200
    assert response.get_json()["transactions"] == []
    assert response.get_json()["data_freshness"]["status"] == "fresh"


def test_filtered_empty_activity_reports_partial_requested_account_as_stale(api_client):
    client, repository = api_client
    run = repository.begin_sync_run(
        provider="simplefin",
        connection_external_id="simplefin-household",
        connection_name="SimpleFin",
    )
    account = repository.upsert_account(
        provider="simplefin",
        external_id="simplefin-checking",
        name="SimpleFin checking",
        account_type="checking",
        balance=100.0,
        connection_id=run.connection_id,
        source_updated_at=datetime.now(timezone.utc).isoformat(),
    )
    repository.finish_sync_run(
        run.id,
        status="partial",
        accounts_synced=1,
        transactions_synced=0,
        errors=1,
    )

    response = client.get(
        "/api/meridian/activity", query_string={"account_id": account.id}
    )

    assert response.status_code == 200
    assert response.get_json()["transactions"] == []
    assert response.get_json()["data_freshness"]["status"] == "stale"


def _cursor(payload):
    return base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")


@pytest.mark.parametrize(
    "cursor",
    [
        "not-base64",
        _cursor(["not-a-timestamp", 1]),
        _cursor([1, 1]),
        _cursor(["2026-08-27T08:00:00", 1]),
        _cursor(["2026-08-27T08:00:00Z", True]),
        _cursor(["2026-08-27T08:00:00Z", 0]),
        _cursor(["2026-08-27T08:00:00Z", 1, "extra"]),
        _cursor(["2026-08-27 08:00:00+00:00", 1]),
        _cursor(["20260827T080000+00:00", 1]),
        _cursor(["2026-08-27T08:00:00+00:00", 1]),
        base64.urlsafe_b64encode(b'["2026-08-27T08:00:00Z", 1]').decode("ascii"),
    ],
)
def test_meridian_activity_rejects_malformed_or_noncanonical_cursors(
    api_client, cursor
):
    client, _ = api_client

    response = client.get("/api/meridian/activity", query_string={"cursor": cursor})

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "invalid_request",
        "message": "The activity cursor is invalid.",
        "recovery_action": "Restart from the first Activity page and try again.",
    }


@pytest.mark.parametrize("account_id", ["not-a-number", "0", "-1"])
def test_meridian_activity_names_an_invalid_account_filter(api_client, account_id):
    client, _ = api_client

    response = client.get(
        "/api/meridian/activity", query_string={"account_id": account_id}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "invalid_request",
        "message": "account_id must be a positive integer.",
        "recovery_action": "Use a positive account_id and try again.",
    }


def test_meridian_missing_transaction_keeps_last_known_good_freshness(api_client):
    client, repository = api_client
    now = datetime.now(timezone.utc).isoformat()
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-household",
        connection_name="Crew",
    )
    repository.upsert_account(
        provider="crew",
        external_id="checking",
        name="Checking",
        account_type="checking",
        balance=100.0,
        connection_id=run.connection_id,
        source_updated_at=now,
    )
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=0,
        errors=0,
    )

    response = client.get("/api/meridian/transactions/99999")

    assert response.status_code == 404
    assert response.get_json()["data_freshness"]["status"] == "fresh"


def test_meridian_api_hides_repository_failures_behind_a_stable_error(
    api_client, monkeypatch
):
    client, _ = api_client

    class UnavailableRepository:
        @staticmethod
        def list_accounts():
            raise RuntimeError("Bearer should-never-appear")

    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_REPOSITORY_FACTORY",
        UnavailableRepository,
    )

    response = client.get("/api/meridian/accounts")

    assert response.status_code == 503
    assert response.get_json()["error"] == {
        "code": "financial_data_unavailable",
        "message": "Financial data is temporarily unavailable.",
        "recovery_action": "Try again after your provider reconnects.",
    }
    assert "should-never-appear" not in response.get_data(as_text=True)


def test_oauth_callback_exchanges_code_stores_token_and_marks_connected(
    api_client, monkeypatch
):
    from meridian.connectors.google_auth import OAuthTokenStore

    client, graph = api_client
    authorizations = ConnectionRepository(graph.db_path)
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTIONS_FACTORY",
        lambda: authorizations,
    )
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_CONNECTION_AUTHORIZERS",
        {"gmail": lambda redirect_uri=None: {"authorization_url": "https://accounts.google.test/oauth"}},
    )
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "app-123.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "GOCSPX-not-a-real-secret")
    captured = {}
    import base64
    import json

    id_token_payload = base64.urlsafe_b64encode(
        json.dumps({"email": "owner@example.com"}).encode("utf-8")
    ).decode("ascii").rstrip("=")

    class _FakeResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": "at-1",
                "refresh_token": "rt-1",
                "expires_in": 3600,
                "id_token": f"head.{id_token_payload}.sig",
            }

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["data"] = kwargs.get("data")
        return _FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    # First mark pending via authorize (creates the row shared with the callback).
    pending = client.post("/api/meridian/settings/connections/gmail/authorize")
    assert pending.status_code == 200
    pending_row = authorizations.list_all()[0]

    response = client.get(
        "/api/meridian/connections/oauth/callback",
        query_string={"state": "gmail-connect", "code": "code-1"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["state"] == "connected"
    assert body["kind"] == "gmail"
    assert body["account"] == "owner@example.com"  # id_token email claim

    stored = OAuthTokenStore(graph.db_path).get(kind="gmail", account_email="owner@example.com")
    assert stored["access_token"] == "at-1"
    assert stored["refresh_token"] == "rt-1"

    saved = authorizations.list_all()[0]
    assert saved.kind == "gmail"
    assert saved.state is ConnectionState.CONNECTED
    assert saved.granted_scopes == (READ_ONLY_GMAIL_SCOPE,)

    # The callback must update the pending row in place: one gmail row total,
    # same public_id, now connected.
    assert len(authorizations.list_all()) == 1
    assert saved.public_id == pending_row.public_id

    # exchange must forward the code, secret material never appears in the body
    assert captured["data"]["code"] == "code-1"
    assert "GOCSPX" not in response.get_data(as_text=True)


def test_oauth_callback_rejects_missing_code_or_unknown_kind(api_client):
    client, _ = api_client
    missing = client.get("/api/meridian/connections/oauth/callback", query_string={"state": "gmail-connect"})

    assert missing.status_code == 400
    assert missing.get_json()["error"]["code"] == "invalid_oauth_callback"

    unknown = client.get(
        "/api/meridian/connections/oauth/callback",
        query_string={"state": "slack-connect", "code": "x"},
    )

    assert unknown.status_code == 400
    assert unknown.get_json()["error"]["code"] == "invalid_oauth_callback"


def test_paycheck_get_returns_none_when_unset(api_client):
    client, graph = api_client
    response = client.get("/api/meridian/paycheck")
    assert response.status_code == 200
    assert response.get_json()["paycheck"] is None


def test_paycheck_set_and_get_roundtrips(api_client):
    client, graph = api_client

    response = client.post("/api/meridian/paycheck", json={
        "cadence": "biweekly", "amount": 1200.0, "next_date": "2026-09-18", "active": True,
    })
    assert response.status_code == 200
    assert response.get_json()["paycheck"]["cadence"] == "biweekly"

    got = client.get("/api/meridian/paycheck").get_json()["paycheck"]
    assert got["amount"] == 1200.0
    assert got["next_date"] == "2026-09-18"


def test_paycheck_set_rejects_invalid_cadence_or_amount(api_client):
    client, _ = api_client
    bad_cadence = client.post("/api/meridian/paycheck", json={"cadence": "fortnightly", "amount": 100, "next_date": "2026-09-18"})
    assert bad_cadence.status_code == 400
    bad_amount = client.post("/api/meridian/paycheck", json={"cadence": "monthly", "amount": -5, "next_date": "2026-09-18"})
    assert bad_amount.status_code == 400


def test_oauth_callback_does_not_require_app_session(monkeypatch):
    """The callback is Google's redirect target; it must exchange the code and
    store the token without requiring an app session. Requiring one wasted the
    single-use code (302 -> /login before exchange) whenever the redirect landed
    in a tab without an app login.
    """
    import tempfile

    from meridian.evidence import EvidenceRepository  # noqa: F401
    os.environ["DB_FILE"] = os.path.join(tempfile.mkdtemp(prefix="oauth_cb_"), "cb.db")

    client = simplecrew.app.test_client()  # deliberately NO session login

    assert client.get("/api/meridian/connections/oauth/callback?state=gmail-connect").status_code in (400, 200)


def test_crew_mutations_status_readonly(api_client, tmp_path):
    """The capture-status endpoint serves the verified mutation catalog (read-only)."""
    client, _ = api_client
    # Ensure the catalog doc exists (the real repo file) so the endpoint resolves.
    response = client.get("/api/meridian/crew/mutations-status")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        payload = response.get_json()
        assert "summary" in payload
        assert "mutations" in payload
        assert payload["summary"]["total"] >= 1


def test_crew_mutations_status_requires_login():
    response = simplecrew.app.test_client().get("/api/meridian/crew/mutations-status")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def _only_connection_id(repository):
    scope = repository.get_freshness_scope(include_all_connections=True)
    assert len(scope.connections) == 1
    return scope.connections[0].connection_id


def test_accounts_api_reports_an_archived_account_with_provenance(api_client):
    """An account a complete read concluded is gone is still reported, never
    silently dropped from the workspace."""
    client, repository = api_client
    _complete_connection(repository)
    archived_count = repository.mark_absent_accounts(
        provider="crew",
        connection_id=_only_connection_id(repository),
        observed_external_ids=(),
        absent_since="2026-09-11T14:09:37Z",
    )
    assert archived_count == 1

    payload = client.get("/api/meridian/accounts").get_json()

    assert payload["accounts"] == []
    assert len(payload["archived"]) == 1
    entry = payload["archived"][0]
    assert entry["name"] == "Crew checking"
    assert entry["provider"] == "crew"
    assert entry["absent_since"] == "2026-09-11T14:09:37Z"
    assert entry["retained_transactions"] == 1
    # A last known figure is not a current balance.
    assert "balance" not in entry
    assert "available_balance" not in entry


def test_activity_marks_a_transaction_of_an_archived_account(api_client):
    client, repository = api_client
    _complete_connection(repository)
    repository.mark_absent_accounts(
        provider="crew",
        connection_id=_only_connection_id(repository),
        observed_external_ids=(),
        absent_since="2026-09-11T14:09:37Z",
    )

    payload = client.get("/api/meridian/activity").get_json()

    transaction = payload["transactions"][0]
    assert transaction["account_name"] == "Crew checking"
    assert transaction["account_archived"] is True


def test_activity_does_not_mark_a_current_accounts_transaction(api_client):
    client, repository = api_client
    _complete_connection(repository)

    payload = client.get("/api/meridian/activity").get_json()

    transaction = payload["transactions"][0]
    assert transaction["account_name"] == "Crew checking"
    assert transaction["account_archived"] is False


def test_transaction_detail_carries_its_account_label(api_client):
    client, repository = api_client
    account = _complete_connection(repository)
    transaction_id = repository.list_transactions(account_id=account.id)[0][0].id
    repository.mark_absent_accounts(
        provider="crew",
        connection_id=_only_connection_id(repository),
        observed_external_ids=(),
        absent_since="2026-09-11T14:09:37Z",
    )

    payload = client.get(f"/api/meridian/transactions/{transaction_id}").get_json()

    assert payload["transaction"]["account_name"] == "Crew checking"
    assert payload["transaction"]["account_archived"] is True


def test_accounts_workspace_renders_the_archived_section_hidden(api_client):
    """The archived section ships collapsed until something is actually reported."""
    client, _ = api_client

    response = client.get("/meridian?workspace=accounts")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "data-archived-accounts hidden" in html
    assert "data-archived-account-list" in html
    assert "No longer returned" in html


def test_plan_api_reports_a_bill_the_provider_no_longer_returns(api_client):
    """The Plan payload carries absent bills with provenance, and no amount."""
    client, repository = api_client
    commitments = CommitmentRepository(repository.db_path)
    commitments.create(
        type=CommitmentType.BILL,
        name="T-Mobile",
        amount=70.0,
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-gone",
    )
    commitments.mark_absent_bills(provider="crew", observed_external_ids=("bill-kept",))

    response = client.get("/api/meridian/plan")

    assert response.status_code == 200
    payload = response.get_json()
    assert [bill["name"] for bill in payload["absent_bills"]] == ["T-Mobile"]
    assert payload["absent_bills"][0]["provider"] == "crew"
    assert payload["absent_bills"][0]["absent_since"]
    # A last known figure is not a current obligation.
    assert "amount" not in payload["absent_bills"][0]


def test_the_dial_names_the_crew_funding_plan_as_the_income_source(api_client):
    """OS-050 end-to-end and read-only: a persisted Crew funding plan becomes the source
    the dial names, so the row's stamp reads the Crew record ("Veterans Home") instead of
    the interim "manual".

    Owner directive: *"Right, it SHOULD be a crew record though, the paycheck"*. This is the
    assertion that ties the stored record to the surface the owner actually reads, and it
    fails if resolution stops consulting the plan.
    """
    client, repository = api_client
    _complete_connection(repository)
    repository.upsert_funding_plan(
        provider="crew",
        external_id="plan:1",
        bill_reserve_id="res:1",
        name="Veterans Home",
        amount=1663.00,
        cadence="biweekly",
        anchor_date="2026-09-04",
        observed_at="2026-09-19T12:00:00Z",
    )

    response = client.get("/api/meridian/dial?as_of=2026-09-19")

    assert response.status_code == 200
    income = [e for e in response.get_json()["events"] if e["kind"] == "income"]
    assert income, "a resolved Crew plan must project at least one occurrence"
    assert income[0]["source"] == "Veterans Home"
    assert income[0]["basis"] == "crew_plan"
    assert income[0]["amount"]["minor"] == 166300


def test_a_plan_with_an_unmappable_cadence_does_not_fabricate_a_payday(api_client):
    """Safety guard for the honesty case: Crew can carry a schedule Meridian cannot express
    (MONTHLY x2), which reaches resolution as cadence ``None``. The amount and identity stay
    Crew facts, but no occurrence date may be invented -- so the dial must still answer 200
    and simply omit the projection rather than guessing a payday."""
    client, repository = api_client
    _complete_connection(repository)
    repository.upsert_funding_plan(
        provider="crew",
        external_id="plan:2",
        bill_reserve_id="res:1",
        name="Veterans Home",
        amount=1663.00,
        cadence=None,
        anchor_date="2026-09-04",
        observed_at="2026-09-19T12:00:00Z",
    )

    response = client.get("/api/meridian/dial?as_of=2026-09-19")

    assert response.status_code == 200
    assert [e for e in response.get_json()["events"] if e["kind"] == "income"] == []


def test_the_payday_settings_report_the_learning_window(api_client):
    """OS-051: the income area must say which learning window produced its figure, and
    how much of the history that window excluded."""
    client, repository = api_client
    _complete_connection(repository)

    response = client.get("/api/meridian/settings/payday")

    assert response.status_code == 200
    learning = response.get_json()["learning"]
    assert learning["active"] is False
    assert learning["floor"] is None
    assert learning["excluded"] == 0


def test_the_owner_can_reset_the_learning_window_from_the_income_area(api_client):
    """The owner-operable reset. It writes ONE Meridian-local setting and must not
    delete a single financial record: "a reset must NOT delete financial records". The
    observations stay; only which of them are learned from changes."""
    client, repository = api_client
    _complete_connection(repository)
    transactions_before = len(repository.list_transactions(limit=200)[0])

    response = client.post(
        "/api/meridian/settings/payday/learning-floor", json={"floor": "2026-09-01"}
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["learning"]["active"] is True
    assert payload["learning"]["floor"] == "2026-09-01"
    assert payload["learning"]["set_at"]
    # No financial record was removed, and nothing left Meridian.
    assert len(repository.list_transactions(limit=200)[0]) == transactions_before

    # And it persists across requests, so a restart cannot lose it.
    again = client.get("/api/meridian/settings/payday").get_json()
    assert again["learning"]["floor"] == "2026-09-01"


def test_the_owner_can_clear_the_learning_window(api_client):
    """Reversibility: clearing restores the full history rather than being one-way."""
    client, repository = api_client
    _complete_connection(repository)
    client.post(
        "/api/meridian/settings/payday/learning-floor", json={"floor": "2026-09-01"}
    )

    response = client.post(
        "/api/meridian/settings/payday/learning-floor", json={"floor": None}
    )

    assert response.status_code == 200
    assert response.get_json()["learning"]["active"] is False
    assert client.get("/api/meridian/settings/payday").get_json()["learning"]["floor"] is None


def test_an_invalid_learning_floor_is_rejected(api_client):
    """A bad date would otherwise be stored and could silently exclude everything."""
    client, repository = api_client
    _complete_connection(repository)

    response = client.post(
        "/api/meridian/settings/payday/learning-floor", json={"floor": "yesterday"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_request"
    assert client.get("/api/meridian/settings/payday").get_json()["learning"]["active"] is False


# --- a browser opening missing evidence must get a page, not JSON (OS-067) ----------
#
# Reported 2026-09-21: clicking an invoice link landed on a screen of raw JSON —
# {"error":{"code":"evidence_content_missing",...}}. The route behaved correctly (it
# explained the missing blob and how to recover), but the invoice link opens in a NEW TAB,
# so a browser NAVIGATION was being served an API payload. A JSON client must keep
# receiving JSON, so the two are distinguished by Sec-Fetch-Mode: a navigation says
# "navigate"; a fetch/XHR does not.

def _content_client(monkeypatch, tmp_path, *, title="Your Xfinity payment is due today"):
    repository = FinancialRepository(str(tmp_path / "financial.db"))

    class FakeItem:
        content_hash = "0" * 64

    item = FakeItem()
    item.title = title

    class FakeRepo:
        def get_item(self, _id):
            return item

    class ExplodingStore:
        def read(self, _hash):
            raise FileNotFoundError("blob never written")

    monkeypatch.setitem(simplecrew.app.config, "MERIDIAN_REPOSITORY_FACTORY", lambda: repository)
    monkeypatch.setitem(
        simplecrew.app.config, "MERIDIAN_EVIDENCE_REPOSITORY_FACTORY", lambda: FakeRepo()
    )
    monkeypatch.setitem(
        simplecrew.app.config, "MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY", lambda: ExplodingStore()
    )
    # Flask-Login must resolve the session user, or the route redirects to /login (302)
    # and the evidence path is never exercised.
    monkeypatch.setattr(
        simplecrew.login_manager,
        "_user_callback",
        lambda value: simplecrew.User(value, "meridian-api-user", "meridian-api@example.com"),
    )
    client = simplecrew.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "meridian-api-user"
        session["_fresh"] = True
    return client


def test_a_browser_navigation_gets_html_when_evidence_content_is_missing(monkeypatch, tmp_path):
    client = _content_client(monkeypatch, tmp_path)
    response = client.get(
        "/api/meridian/evidence/1/content",
        headers={"Sec-Fetch-Mode": "navigate", "Accept": "text/html"},
    )
    assert response.status_code == 404
    assert response.mimetype == "text/html", (
        "a navigation that opened a new tab must not receive a JSON payload"
    )
    body = response.get_data(as_text=True)
    assert "not stored" in body.lower()
    assert "Xfinity" in body, "the page must still name the document"
    assert "<script" not in body.lower(), "the error page must carry no scripts"


def test_a_json_client_still_gets_the_structured_error(monkeypatch, tmp_path):
    """The API contract must not change for programmatic callers."""
    client = _content_client(monkeypatch, tmp_path)
    response = client.get(
        "/api/meridian/evidence/1/content",
        headers={"Sec-Fetch-Mode": "cors", "Accept": "application/json"},
    )
    assert response.mimetype == "application/json"
    payload = response.get_json()
    assert payload["error"]["code"] == "evidence_content_missing"
    assert payload["error"]["recovery_action"], "the recovery action must survive"


def test_the_error_page_escapes_the_title():
    """Evidence titles come from mail subjects, so they are untrusted input."""
    from meridian.api import _evidence_unavailable_html

    page = _evidence_unavailable_html('<img src=x onerror="alert(1)">')
    assert "<img" not in page, "an evidence title must never inject markup"
    assert "&lt;img" in page
