import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL is required for browser tests")


def test_review_modes_show_confidence_patterns_and_preserve_inspector(browser):
    from tests.browser.test_transaction_inspector import _authed_page, _fulfill

    context, page = _authed_page(browser)
    transaction = {
        "id": 101,
        "account_id": 11,
        "provider": "crew",
        "amount": -3,
        "currency": "USD",
        "occurred_at": "2026-08-20T18:00:00Z",
        "description": "Coffee",
        "merchant": "Blue Bottle",
        "status": "posted",
        "classification": {"category": "Dining", "kind": "spend", "confidence": 0.49, "evidence": "uncertain merchant"},
    }

    def activity_route(route):
        mode = "patterns" if "mode=patterns" in route.request.url else "review"
        payload = (
            {"patterns": [{"kind": "recurrence", "title": "Monthly coffee", "evidence_ids": [101]}], "data_freshness": {"status": "fresh"}}
            if mode == "patterns"
            else {"transactions": [transaction], "next_cursor": None, "data_freshness": {"status": "fresh"}}
        )
        route.fulfill(content_type="application/json", body=json.dumps(payload))

    page.route("**/api/meridian/activity*", activity_route)
    page.route("**/api/meridian/transactions/101", _fulfill({"transaction": transaction, "data_freshness": {"status": "fresh"}}))
    page.route("**/api/meridian/accounts", _fulfill({"accounts": [], "data_freshness": {"status": "fresh"}}))
    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    page.locator('[data-activity-mode="review"]').click()
    assert "49% confidence" in page.locator("[data-confidence-label]").inner_text()
    page.locator('[data-transaction-id="101"]').click()
    page.locator('[data-activity-mode="patterns"]').click()
    assert page.locator("[data-inspector-rail]").is_visible()
    page.wait_for_selector('[data-pattern-card="recurrence"]')
    assert page.locator('[data-pattern-card="recurrence"]').is_visible()
    context.close()


def test_a_two_word_category_can_be_typed_without_the_inspector_stealing_the_space(browser):
    """The owner: "when manually writing a category, pressing the space key brings up
    the evidence so you cannot have more than 1 word".

    The inline editor is inserted INTO the transaction row, and a document-level
    keydown listener treated Enter/Space anywhere inside a row as "activate the row",
    calling preventDefault and opening the inspector. The space never reached the
    input, so multi-word categories such as "Personal Care" were impossible to type.
    """
    from tests.browser.test_transaction_inspector import _authed_page, _fulfill

    context, page = _authed_page(browser)
    transaction = {
        "id": 303,
        "account_id": 11,
        "provider": "crew",
        "amount": -12.4,
        "currency": "USD",
        "occurred_at": "2026-08-20T18:00:00Z",
        "description": "Unassigned purchase",
        "merchant": "Unassigned purchase",
        "status": "posted",
        "classification": {
            "category": "uncategorized",
            "kind": "spend",
            "confidence": 0.2,
            "evidence": "no reliable category",
        },
        "suggested_category": None,
        "category_options": ["Personal Care", "Dining"],
    }

    page.route(
        "**/api/meridian/activity*",
        _fulfill(
            {
                "transactions": [transaction],
                "next_cursor": None,
                "review_count": 1,
                "data_freshness": {"status": "fresh"},
            }
        ),
    )
    page.route(
        "**/api/meridian/accounts",
        _fulfill({"accounts": [], "data_freshness": {"status": "fresh"}}),
    )
    # The inspector fetches the transaction detail when it opens.
    page.route(
        "**/api/meridian/transactions/303",
        _fulfill({"transaction": transaction, "data_freshness": {"status": "fresh"}}),
    )
    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    page.locator('[data-activity-mode="review"]').click()

    page.locator("[data-review-correct]").first.click()
    field = page.locator(".m-review-editor-input")
    field.click()
    field.type("Personal Care")

    # The space must reach the field rather than opening the transaction evidence.
    assert field.input_value() == "Personal Care"
    assert not page.locator("[data-inspector-rail]").is_visible()

    # The row must still activate from the keyboard, but only when the ROW itself has
    # focus. Review cards drop role/tabindex, so the focusable row is the timeline one.
    page.locator(".m-review-editor-input").press("Escape")
    page.locator('[data-activity-mode="timeline"]').click()
    # Review cards drop role/tabindex, so wait for the RE-RENDERED timeline row rather
    # than focusing the review card that is still attached under the same id.
    row = page.locator('[data-transaction-id="303"][tabindex="0"]')
    row.wait_for(state="attached")
    row.focus()
    page.keyboard.press("Space")
    # The rail opens asynchronously (it fetches the transaction), so wait for it
    # rather than sampling visibility once.
    page.wait_for_selector("[data-inspector-rail]", state="visible", timeout=5000)
    context.close()


def test_unchecking_apply_to_future_matching_toggles_the_box_instead_of_opening_evidence(browser):
    """The owner: unchecking "apply to future matching" made the evidence card consume the
    page and left the box unchanged -- the same failure the space key had.

    The row's click guard enumerated the review controls one by one, and this checkbox was
    never added to that list, so a click on it bubbled to the row and opened the inspector.
    The guard is now general: any interactive descendant owns its own events, so adding a
    control and forgetting a list can no longer reintroduce this.
    """
    from tests.browser.test_transaction_inspector import _authed_page, _fulfill

    context, page = _authed_page(browser)
    transaction = {
        "id": 303,
        "account_id": 11,
        "provider": "crew",
        "amount": -12.4,
        "currency": "USD",
        "occurred_at": "2026-08-20T18:00:00Z",
        "description": "Unassigned purchase",
        "merchant": "Unassigned purchase",
        "status": "posted",
        "classification": {
            "category": "uncategorized",
            "kind": "spend",
            "confidence": 0.2,
            "evidence": "no reliable category",
        },
        "suggested_category": None,
        "category_options": ["Personal Care", "Dining"],
    }

    page.route(
        "**/api/meridian/activity*",
        _fulfill(
            {
                "transactions": [transaction],
                "next_cursor": None,
                "review_count": 1,
                "data_freshness": {"status": "fresh"},
            }
        ),
    )
    page.route(
        "**/api/meridian/accounts",
        _fulfill({"accounts": [], "data_freshness": {"status": "fresh"}}),
    )
    page.route(
        "**/api/meridian/transactions/303",
        _fulfill({"transaction": transaction, "data_freshness": {"status": "fresh"}}),
    )

    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    page.locator('[data-activity-mode="review"]').click()
    page.locator("[data-review-correct]").first.click()

    box = page.locator(".m-review-editor-rule input[type=checkbox]")
    box.wait_for(state="visible")
    assert box.is_checked()

    # The box itself.
    box.click()
    assert not box.is_checked()
    assert not page.locator("[data-inspector-rail]").is_visible()

    # And its label, which is the other half of the same control.
    page.locator(".m-review-editor-rule").click()
    assert box.is_checked()
    assert not page.locator("[data-inspector-rail]").is_visible()
    context.close()
