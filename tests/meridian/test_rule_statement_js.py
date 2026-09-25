"""OS-102: the rule statement builder is EXECUTED, not grepped.

Every claim a summary of a money rule makes is a claim about the owner's money, so these tests run the
real module under Node and assert the sentences. The two that matter most: an unknown shape is
disclosed rather than smoothed over, and a webhook URL is never printed (a webhook path routinely
carries a secret, and this text can be captured, screenshotted and shared).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: A rule built the way meridian/crew_commands.py builds one, including the action union's real
#: shape: `{roundUpTransfer: {...}}`, where the action NAME is the key and there is no `type` field.
ROUND_UP = {
    "name": "Round Up",
    "description": "Round up transactions to the nearest dollar",
    "triggers": ["CASH_TRANSACTION_OCCURRED"],
    "actions": [{"roundUpTransfer": {"accountId": "acc-1", "roundToNearest": 100, "accountType": "ACCOUNT"}}],
}
CARD_ROUND_UP = {
    "name": "Card round up",
    "triggers": ["DEBIT_CARD_TRANSACTION"],
    "conditions": {"and": {"conditions": [
        {"idMatch": {"entityId": "card-9", "entitySchema": "DEBIT_CARDS"}},
    ]}},
    "actions": [{"roundUpTransfer": {"subaccountId": "sub-2", "roundToNearest": 500}}],
}
SPLIT = {
    "name": "Split my pay",
    "triggers": ["CASH_TRANSACTION_OCCURRED"],
    "actions": [{"splitDeposit": {"destinations": [{"subaccountId": "sub-2"}, {"subaccountId": "sub-3"}]}}],
}
NOTIFY = {
    "name": "Tell me",
    "triggers": ["CASH_TRANSACTION_OCCURRED"],
    "actions": [{"sendNotification": {"message": "Payday landed", "method": "PUSH"}}],
}
WEBHOOK = {
    "name": "Hook",
    "triggers": ["CASH_TRANSACTION_OCCURRED"],
    "actions": [{"sendWebhook": {"url": "https://hooks.example.com/services/T00/B11/secret-token-xyz"}}],
}
UNKNOWN = {
    "name": "Mystery",
    "triggers": ["SOMETHING_NEW_ENTIRELY"],
    "actions": [{"inventedAction": {"whatever": 1}}],
}


def _run(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _statement(formula, names=None):
    """Wrap the formula the way meridian/services/plan.py delivers it: a rule with a `formula`."""
    rule = {"id": "rule-1", "name": formula.get("name", "Rule"), "is_paused": False, "formula": formula}
    script = f"""
      const {{ ruleStatement, rulePurpose, rulePurposeLabel }} = await import('./static/js/meridian/rule-statement.js');
      const rule = {json.dumps(rule)};
      const out = ruleStatement(rule, {{ names: {json.dumps(names or {})} }});
      out.purposeLabel = rulePurposeLabel(rulePurpose(rule));
      console.log(JSON.stringify(out));
    """
    return json.loads(_run(script))


def test_a_real_crew_formula_renders_a_statement_rather_than_nothing():
    """The bug this replaces: the old summary looked for `action.type`, which a real Crew formula
    does not carry, so every genuine rule printed an empty body."""
    out = _statement(ROUND_UP)
    assert out["recognised"] is True
    assert out["unknown"] == []
    assert out["when"] == "cash moves in or out"
    assert out["whenRaw"] == ["CASH_TRANSACTION_OCCURRED"]
    assert out["effects"] == ["round each purchase up to the nearest $1.00 and move the change into a destination Crew holds"]


def test_cents_are_formatted_for_the_one_field_the_repo_proves_is_cents():
    out = _statement(CARD_ROUND_UP, names={"card-9": "the Teal card", "sub-2": "Free to Spend"})
    assert "the nearest $5.00" in out["effects"][0]
    assert "Free to Spend" in out["effects"][0]
    assert out["conditions"] == ["only when the Teal card matches"]


def test_an_unresolvable_id_is_described_rather_than_printed():
    out = _statement(CARD_ROUND_UP)
    # No bare opaque id, and no invented card name.
    assert out["conditions"] == ["only when Crew's debit cards match holds"]
    assert "card-9" not in json.dumps(out["conditions"])


def test_an_amount_whose_unit_is_not_established_is_labelled_as_crews_own():
    """A wrong 100x on a money rule is worse than an unpolished sentence, so the figure is reported
    as Crew's own rather than converted on a guess."""
    rule = {
        "name": "Target",
        "triggers": ["CASH_TRANSACTION_OCCURRED"],
        "actions": [{"targetBalanceTransfer": {"accountId": "acc-1", "targetBalance": 50000, "direction": "INTO"}}],
    }
    out = _statement(rule)
    assert out["effects"] == ["move money into a destination Crew holds until it holds 50000 (in Crew's own units)"]
    assert "$500.00" not in json.dumps(out)


def test_a_webhook_url_is_never_printed():
    out = _statement(WEBHOOK)
    rendered = json.dumps(out["effects"])
    assert "hooks.example.com" in rendered
    assert "secret-token-xyz" not in rendered, "a webhook path must not be rendered anywhere"
    assert "withheld" in rendered
    # The raw formula is the caller's disclosure and is allowed to hold it; the SENTENCE is not.
    assert "secret-token-xyz" in out["raw"]


def test_an_unrecognised_shape_is_disclosed_in_crews_own_vocabulary():
    out = _statement(UNKNOWN)
    assert out["recognised"] is False
    assert "SOMETHING_NEW_ENTIRELY" in out["whenRaw"]
    assert out["when"] == "SOMETHING_NEW_ENTIRELY", "unknown triggers stay in Crew's own words"
    assert "the action type inventedAction" in out["unknown"]
    assert out["effects"] == []
    assert json.loads(out["raw"])["name"] == "Mystery"


def test_purpose_groups_money_movement_apart_from_notifications():
    assert _statement(SPLIT)["purpose"] == "money"
    assert _statement(SPLIT)["purposeLabel"] == "Money movement"
    assert _statement(NOTIFY)["purpose"] == "notify"
    assert _statement(UNKNOWN)["purpose"] == "other"
    assert _statement(NOTIFY)["effects"] == ['notify you by push: "Payday landed"']


def test_a_rule_with_no_formula_does_not_throw():
    out = _statement({"name": "Empty"})
    assert out["when"] is None
    assert out["effects"] == []
    assert out["recognised"] is False
    assert json.loads(out["raw"]) == {"name": "Empty"}
