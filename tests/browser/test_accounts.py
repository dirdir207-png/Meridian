import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(
    not APP_URL, reason="APP_URL is required for browser tests"
)
OWNER_PASSWORD = "meridian-owner-2026"
DESKTOP_VIEWPORT = {"width": 1440, "height": 900}


@pytest.fixture()
def authed_page(browser):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=DESKTOP_VIEWPORT)
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200
    yield context.new_page()


def test_accounts_workspace_uses_financial_roles_not_provider_workspaces(authed_page):
    authed_page.goto(f"{APP_URL}/meridian?workspace=accounts")
    authed_page.wait_for_selector("[data-accounts-group]")

    roles = authed_page.locator("[data-accounts-group]").evaluate_all(
        "nodes => nodes.map(node => node.dataset.accountsGroup)"
    )
    assert "cash" in roles
    assert authed_page.locator("[data-provider-workspace]").count() == 0
    assert authed_page.locator("[data-connections]").count() == 1


def test_accounts_rows_keep_provider_marks_secondary(authed_page):
    authed_page.goto(f"{APP_URL}/meridian?workspace=accounts")
    authed_page.wait_for_selector("[data-account-row]")

    row = authed_page.locator("[data-account-row]").first
    assert row.locator("[data-account-name]").is_visible()
    assert row.locator("[data-account-source]").count() == 1
    assert row.locator("[data-account-source]").evaluate(
        "node => parseFloat(getComputedStyle(node).fontSize)"
    ) < row.locator("[data-account-name]").evaluate(
        "node => parseFloat(getComputedStyle(node).fontSize)"
    )


def test_concept_emblems_apply_to_the_three_named_accounts_only(authed_page):
    """The owner chose concept 04's three emblems on 2026-09-24. The mapping is name-keyed and
    EXACT, so this drives the real render path with the concept's three names plus two lookalikes
    and asserts that only the three get artwork -- and that each of those rows still says what it
    is, because the emblem is decoration rather than a classifier."""
    import json as _json

    payload = {
        "groups": [
            {"role": "cash", "accounts": [
                {"id": 901, "name": "Free to Spend", "account_type": "pocket", "balance": 441.89,
                 "currency": "USD", "synced_at": "2026-09-24T13:46:00Z"},
                {"id": 902, "name": "Checking", "account_type": "checking", "balance": 1243.18,
                 "currency": "USD", "synced_at": "2026-09-24T13:46:00Z"},
            ]},
            {"role": "savings", "accounts": [
                {"id": 903, "name": "Bill Reserve", "account_type": "reserve", "balance": 1320.00,
                 "currency": "USD", "synced_at": "2026-09-24T13:46:00Z"},
                {"id": 904, "name": "Emergency Fund", "account_type": "savings", "balance": 200.00,
                 "currency": "USD", "synced_at": "2026-09-24T13:46:00Z"},
                {"id": 905, "name": "Emergency plumbing fund", "account_type": "pocket",
                 "balance": 60.00, "currency": "USD", "synced_at": "2026-09-24T13:46:00Z"},
            ]},
        ],
        "archived": [], "reimbursements": [], "connections": [],
        "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-24T13:46:00Z"},
    }
    authed_page.route(
        "**/api/meridian/accounts*",
        lambda route: route.fulfill(body=_json.dumps(payload), content_type="application/json"),
    )
    authed_page.goto(f"{APP_URL}/meridian?workspace=accounts")
    authed_page.wait_for_selector("[data-account-row]")

    emblems = authed_page.evaluate(
        """() => [...document.querySelectorAll('.m-account-row')].map((row) => ({
             name: row.querySelector('[data-account-name]').textContent,
             emblem: row.querySelector('.m-account-icon').dataset.emblem || null,
             tint: row.querySelector('.m-account-icon').dataset.tint,
             glyph: row.querySelector('.m-account-icon svg') ? 'svg' : null,
             frame: getComputedStyle(row.querySelector('.m-account-icon'), '::after').content,
             size: row.querySelector('.m-account-icon').getBoundingClientRect().width,
           }))"""
    )
    by_name = {row["name"]: row for row in emblems}
    assert by_name["Free to Spend"]["emblem"] == "compass"
    assert by_name["Bill Reserve"]["emblem"] == "wifi"
    assert by_name["Emergency Fund"]["emblem"] == "star"
    # The lookalike must NOT take the emergency fund's emblem: a decoration may not assert
    # something untrue about the owner's money.
    assert by_name["Emergency plumbing fund"]["emblem"] is None
    assert by_name["Checking"]["emblem"] is None
    # Concept tints, and the emblems carry their own ring/field/glyph, so no frame and no glyph.
    assert by_name["Emergency Fund"]["tint"] == "apricot"
    for name in ("Free to Spend", "Bill Reserve", "Emergency Fund"):
        assert by_name[name]["glyph"] is None
        assert by_name[name]["frame"] in ("none", "")
        assert by_name[name]["size"] == 52
    # The rows that did not match keep the semantic medallion, which is the fallback that makes
    # the emblem safe to grant.
    for name in ("Checking", "Emergency plumbing fund"):
        assert by_name[name]["glyph"] == "svg"
