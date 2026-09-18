"""The Activity review count: the figure behind the Review badge and the strip.

The owner asked for "an orange number indicator for the quantity of reviewable
transactions". The number did not exist anywhere -- not in the Activity payload,
not in the repository, not in the UI -- which is why the strip was blocked in the
earlier slice. The owner then authorised building it.

The contract that matters is that the badge, the strip and the Review list all
report the SAME queue. A count computed by a second, parallel definition could
drift and show "3 decisions to review" above five rows, so the route derives the
figure from the very list it returns.
"""
import os
import sys
import tempfile

import pytest

if "app" not in sys.modules:
    os.environ["DB_FILE"] = os.path.join(
        tempfile.mkdtemp(prefix="meridian_review_count_"), "savings_data.db"
    )

import app as simplecrew
from meridian.classify import Classification
from meridian.repository import FinancialRepository

WORKSPACE = "templates/meridian/partials/activity.html"
SCRIPT = "static/js/meridian/activity.js"
STYLE = "static/css/meridian/activity.css"


def _read(relative):
    from pathlib import Path

    return (Path(__file__).resolve().parents[2] / relative).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def disable_background_polling(monkeypatch):
    monkeypatch.setattr(simplecrew, "_background_thread_started", True)


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    repository = FinancialRepository(str(tmp_path / "financial.db"))
    monkeypatch.setattr(
        simplecrew.login_manager,
        "_user_callback",
        lambda value: simplecrew.User(
            value, "meridian-review-count", "review-count@example.com"
        ),
    )
    monkeypatch.setitem(
        simplecrew.app.config,
        "MERIDIAN_REPOSITORY_FACTORY",
        lambda: repository,
    )
    client = simplecrew.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "meridian-review-count"
        session["_fresh"] = True
    return client, repository


def _seed(repository, *, uncertain, certain):
    """Two transactions below the review threshold and one comfortably above it.

    `get_review_queue` includes a transaction only when its confidence is BOTH set
    and below 0.7, so a row that is merely unclassified is not in the queue.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    run = repository.begin_sync_run(
        provider="crew",
        connection_external_id="crew-review-count",
        connection_name="Crew",
    )
    account = repository.upsert_account(
        provider="crew",
        external_id="crew-review-count-checking",
        name="Crew checking",
        account_type="checking",
        balance=100.0,
        connection_id=run.connection_id,
        source_updated_at=now,
    )
    ids = []
    for index in range(uncertain + certain):
        record = repository.upsert_transaction(
            provider="crew",
            external_id=f"crew-review-count-{index}",
            account_id=account.id,
            amount=-3.0 - index,
            occurred_at=now,
            description=f"Coffee {index}",
            status="posted",
            source_updated_at=now,
        )
        repository.record_classification(
            record.id,
            Classification(
                category="Dining",
                kind="spend",
                confidence=0.2 if index < uncertain else 0.95,
                rule_id="",
                evidence="",
                method="deterministic",
            ),
        )
        ids.append(record.id)
    repository.finish_sync_run(
        run.id,
        status="complete",
        accounts_synced=1,
        transactions_synced=len(ids),
        errors=0,
    )
    return ids


def test_review_count_equals_the_rows_the_review_tab_lists(api_client):
    client, repository = api_client
    _seed(repository, uncertain=2, certain=1)

    payload = client.get("/api/meridian/activity?mode=review").get_json()

    assert payload["review_count"] == 2
    # The figure and the list are the same queue, so they cannot disagree.
    assert payload["review_count"] == len(payload["transactions"])


def test_every_mode_reports_the_count_because_the_badge_is_always_visible(api_client):
    client, repository = api_client
    _seed(repository, uncertain=2, certain=1)

    timeline = client.get("/api/meridian/activity?mode=timeline").get_json()
    patterns = client.get("/api/meridian/activity?mode=patterns").get_json()

    assert timeline["review_count"] == 2
    assert patterns["review_count"] == 2


def test_review_count_is_zero_rather_than_absent_when_nothing_awaits_review(api_client):
    client, repository = api_client
    _seed(repository, uncertain=0, certain=2)

    payload = client.get("/api/meridian/activity?mode=review").get_json()

    assert payload["review_count"] == 0
    assert payload["transactions"] == []


def test_workspace_carries_the_badge_and_the_strip_as_decorative_furniture():
    html = _read(WORKSPACE)
    script = _read(SCRIPT)
    css = _read(STYLE)

    assert 'data-review-count' in html
    assert 'data-review-strip' in html
    # The strip reports the figure in words as well as digits, so it still reads
    # without colour.
    assert "decisions to review" in html
    # The badge must not enlarge the tab's accessible name into "Review 3".
    assert 'badge.hidden = value === 0' in script
    assert "aria-label" in script
    assert "payload.review_count" in script
    # A `display` declaration outranks the UA `[hidden]` rule, so both surfaces
    # need an explicit hidden state or an empty count would render as a lone "0".
    assert ".m-activity-tab-count[hidden]" in css
    assert ".m-review-strip[hidden]" in css
    # The strip belongs to Review; the timeline carries the kit's own banner.
    assert 'state.mode !== "review"' in script
