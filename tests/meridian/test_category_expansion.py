"""Synthetic category coverage and false-positive/owner-correction regressions."""
import pytest

from meridian.classify import (
    AssignmentRule,
    ClassificationInput,
    classify_deterministic,
)
from meridian.repository import FinancialRepository
from meridian.services.activity import get_review_queue


def tx(merchant, amount=-9, description="Card purchase"):
    return ClassificationInput(1, amount, description, merchant, "checking", "2026-09-18T12:00:00Z")


@pytest.mark.parametrize("merchant,category", [
    ("WENDY’S #123", "Dining"), ("TST* CHIPOTLE 123", "Dining"),
    ("Trader Joe's", "Groceries"), ("ALDI #42", "Groceries"),
    ("Netflix.com", "Entertainment"), ("Spotify", "Entertainment"),
    ("KeyMe", "Home"), ("AMTRAK", "Transport"),
    ("Uber Eats", "Dining"), ("Lyft", "Transport"),
    ("Xfinity", "Internet"), ("T-Mobile", "Phone"),
    ("Planet Fitness", "Fitness"), ("Chewy", "Pets"),
])
def test_known_merchants_are_explainable_and_above_review_threshold(merchant, category):
    result = classify_deterministic(tx(merchant))
    assert result.category == category
    assert result.method == "deterministic"
    assert result.confidence >= .7
    assert result.rule_id.startswith("merchant:")
    assert result.evidence


@pytest.mark.parametrize("merchant", ["Amazon", "Walmart", "Target", "CVS", "Shell", "Unknown Shop", "Netflix Consulting", "ALDINE SERVICES", "Wendys Plumbing"])
def test_mixed_or_unrecognized_merchants_are_not_auto_confirmed(merchant):
    result = classify_deterministic(tx(merchant))
    assert result.confidence < .7


def test_description_does_not_override_present_unknown_merchant():
    assert classify_deterministic(tx("Unknown Shop", description="reimbursement for Netflix")).method == "fallback"
    assert classify_deterministic(tx(None, description="POS PURCHASE WENDYS 123")).category == "Dining"


def test_positive_merchant_amount_is_not_classified_as_spending():
    assert classify_deterministic(tx("Wendys", amount=9)).kind != "spend"
    assert classify_deterministic(tx("Wendys", amount=9, description="Refund")).kind == "refund"


def test_owner_rule_and_reconciliation_still_win():
    rule = AssignmentRule("user:test", "Work meals", "spend", merchant_pattern="wendy")
    assert classify_deterministic(tx("Wendys"), user_rules=[rule]).category == "Work meals"


def test_sync_style_reclassification_preserves_explicit_owner_correction(tmp_path):
    repo = FinancialRepository(str(tmp_path / "synthetic.db"))
    account = repo.upsert_account(provider="synthetic", external_id="a", name="Fixture", account_type="checking", balance=100)
    row = repo.upsert_transaction(provider="synthetic", external_id="t", account_id=account.id, amount=-9, occurred_at="2026-09-18T12:00:00Z", description="Card purchase", merchant="Wendys", status="posted")
    repo.record_classification(row.id, classify_deterministic(tx("Wendys")))
    assert get_review_queue(repo) == []
    repo.correct_classification(row.id, category="Work meals", kind="spend", create_rule=False)
    for _ in range(3):
        repo.record_classification(row.id, classify_deterministic(tx("Wendys")))
    reread = FinancialRepository(repo.db_path).get_transaction(row.id)
    assert reread.classification_category == "Work meals"
    assert reread.classification_evidence == "owner correction"


def test_uncategorized_history_does_not_hide_a_known_suggestion(tmp_path):
    repo = FinancialRepository(str(tmp_path / "synthetic.db"))
    account = repo.upsert_account(provider="synthetic", external_id="a", name="Fixture", account_type="checking", balance=100)
    row = repo.upsert_transaction(provider="synthetic", external_id="t", account_id=account.id, amount=-9, occurred_at="2026-09-18T12:00:00Z", description="Card purchase", merchant="Wendys", status="posted")
    repo.record_classification(row.id, classify_deterministic(tx("Unknown Shop")))
    assert repo.suggest_category(merchant="Wendys") == "Dining"
    assert "Uncategorized" not in repo.category_options(merchant="Wendys")


def test_every_curated_alias_resolves_to_its_declared_category():
    from meridian.category_catalog import MERCHANT_RULES

    for rule_id, category, aliases in MERCHANT_RULES:
        for alias in aliases:
            for merchant in (alias, alias.upper() + ' #123'):
                result = classify_deterministic(tx(merchant))
                assert (result.category, result.rule_id) == (category, 'merchant:' + rule_id)
