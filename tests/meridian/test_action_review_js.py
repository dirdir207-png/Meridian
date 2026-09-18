"""A10: approval surfaces show exact recorded parameters without exposing secrets."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_review_formatter_redacts_recursively_and_labels_missing_evidence():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = r"""
      const { reviewActionDetails } = await import('./static/js/meridian/action-review.js');
      const check = (value, message) => { if (!value) throw new Error(message); };
      const review = reviewActionDetails({
        type: 'move_money',
        params: {
          amount: 1250,
          currency: 'USD',
          source_account: 'checking-1',
          destination_account: 'safe-2',
          memo: 'Rent reserve',
          api_token: 'do-not-show',
          nested: { session_cookie: 'also-secret', preserved: true },
        },
      });
      const byPath = Object.fromEntries(review.parameters.map((item) => [item.path, item.value]));
      check(byPath.amount === '1250', 'exact amount');
      check(byPath.currency === 'USD', 'currency');
      check(byPath.source_account === 'checking-1', 'source');
      check(byPath.destination_account === 'safe-2', 'destination');
      check(byPath.memo === 'Rent reserve', 'memo');
      check(byPath.api_token === '[redacted]', 'top-level secret redaction');
      check(byPath['nested.session_cookie'] === '[redacted]', 'nested secret redaction');
      check(byPath['nested.preserved'] === 'true', 'nested value');
      check(review.beforeAfterStatus.includes('not recorded'), 'missing before/after label');
      check(review.preservedStatus.includes('not recorded'), 'missing preserved label');
      check(!JSON.stringify(review).includes('do-not-show'), 'secret absent');
      check(!JSON.stringify(review).includes('also-secret'), 'nested secret absent');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_all_review_surfaces_use_shared_details_renderer():
    actions = (ROOT / "static/js/meridian/actions.js").read_text(encoding="utf-8")
    memory = (ROOT / "static/js/meridian/memory-manage.js").read_text(encoding="utf-8")
    account = (ROOT / "static/js/api/account.js").read_text(encoding="utf-8")

    assert actions.count("renderActionReviewDetails(") >= 1
    assert memory.count("renderActionReviewDetails(") >= 1
    assert "loadActionReviewModule()" in account
    assert "review.renderActionReviewDetails(action)" in account


def test_templates_load_review_formatter_before_consumers():
    shell = (ROOT / "templates/meridian/index.html").read_text(encoding="utf-8")
    settings = (ROOT / "templates/meridian/settings.html").read_text(encoding="utf-8")
    base = (ROOT / "templates/base.html").read_text(encoding="utf-8")

    assert shell.index("action-review.css") < shell.index("action-review.js") < shell.index("plan.js")
    assert settings.index("action-review.css") < settings.index("action-review.js") < settings.index("actions.js")
    assert base.index("action-review.css") < base.index("action-review.js") < base.index("api/account.js")


def test_shared_css_supports_review_details_without_inline_secrets():
    css = (ROOT / "static/css/meridian/action-review.css").read_text(encoding="utf-8")

    assert ".m-action-review" in css
    assert ".m-action-review-grid" in css
    assert ".m-action-review-notice" in css
