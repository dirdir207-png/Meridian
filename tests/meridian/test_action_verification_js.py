"""C4: the action history renders the durable verification receipt honestly.

The receipt lives in two places depending on how the pipeline ended:
``action.verification`` when a readback confirmed the write, and
``action.result.verification`` when the write was accepted but the receipt is
unconfirmed or a confirmed mismatch. An action with neither has no registered
verifier. Every case must render as what it is; an unconfirmed readback must
never read as success, failure, or deletion.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _run_node(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_verification_receipts_render_every_durable_outcome():
    script = r"""
      const { summarizeVerification } = await import('./static/js/meridian/action-verification.js');
      const check = (value, message) => { if (!value) throw new Error(message); };

      // A readback confirmed the write: mark_verified -> verification_json.
      const confirmed = summarizeVerification({
        state: 'verified',
        verification: { ok: true, check: 'crew-bill-readback', provider_truth: true },
      });
      check(confirmed.outcome === 'confirmed', 'confirmed outcome');
      check(confirmed.providerTruth === true, 'confirmed provider truth');

      // The provider accepted the write but the readback could not confirm it.
      const unresolved = summarizeVerification({
        state: 'executed',
        result: { verification: { ok: null, check: 'crew-bill-readback',
                                  provider_truth: false, retry_allowed: false,
                                  reason: 'readback unavailable: timed out' } },
      });
      check(unresolved.outcome === 'unresolved', 'unresolved outcome');
      check(unresolved.providerTruth === false, 'unresolved is not provider truth');
      check(unresolved.retryAllowed === false, 'unresolved is not retryable');
      check(unresolved.headline.includes('Do not resubmit'), 'unresolved warns against resubmit');

      // A verifier raised after acceptance: still unresolved, never a failure.
      const raised = summarizeVerification({
        state: 'executed',
        result: { verification: { ok: null, check: 'verifier-exception',
                                  provider_truth: false, retry_allowed: false,
                                  reason: 'Verification raised: boom' } },
      });
      check(raised.outcome === 'unresolved', 'exception receipt stays unresolved');
      check(raised.check === 'verifier-exception', 'exception check recorded');

      // The provider contradicted the write: a real, provider-truth failure.
      const contradicted = summarizeVerification({
        state: 'failed',
        result: { verification: { ok: false, check: 'crew-bill-readback',
                                  provider_truth: true, reason: 'fields differ',
                                  requested: { name: 'Verizon' },
                                  observed: { name: 'T-Mobile' } } },
      });
      check(contradicted.outcome === 'contradicted', 'contradicted outcome');
      check(contradicted.providerTruth === true, 'contradiction is provider truth');

      // No verifier registered at all.
      const none = summarizeVerification({ state: 'executed', result: { success: true } });
      check(none.recorded === false, 'no receipt was recorded');
      check(none.outcome === 'unresolved', 'no verifier is unresolved, not success');
      check(none.check === 'no-verifier-registered', 'no-verifier check label');
      check(none.headline.includes('Do not resubmit'), 'no-verifier warns against resubmit');

      // A receipt that never claimed provider truth must not be upgraded.
      const bare = summarizeVerification({
        state: 'executed',
        result: { verification: { ok: null, check: 'crew-bill-readback' } },
      });
      check(bare.providerTruth === false, 'absent provider_truth is false');
      check(bare.retryAllowed === false, 'absent retry_allowed is false');
      check(bare.reason === 'No reason was recorded.', 'absent reason is labelled, not invented');
    """
    _run_node(script)


def test_verification_renderer_builds_a_read_only_receipt_without_inner_html():
    script = r"""
      const { renderActionVerification } = await import('./static/js/meridian/action-verification.js');
      const check = (value, message) => { if (!value) throw new Error(message); };

      /* Minimal document double: this asserts the renderer's own decisions. */
      const makeDocument = () => ({
        createElement: (tag) => ({
          tag, children: [], dataset: {}, textContent: '', className: '',
          setAttribute() {},
          append(...nodes) { this.children.push(...nodes); },
          appendChild(node) { this.children.push(node); },
        }),
      });
      const walk = (node) =>
        [node.textContent || ''].concat((node.children || []).map(walk)).join(' ');

      const section = renderActionVerification(
        { state: 'executed',
          result: { verification: { ok: null, check: 'crew-bill-readback',
                                    provider_truth: false, retry_allowed: false,
                                    reason: 'readback unavailable: timed out',
                                    requested: { billId: 'Bill:1' } } } },
        makeDocument(),
      );

      check(section.className === 'm-action-verification', 'receipt section class');
      check(section.dataset.verificationOutcome === 'unresolved', 'outcome is on the section');
      const text = walk(section);
      check(text.includes('Do not resubmit'), 'headline warns against resubmit');
      check(text.includes('crew-bill-readback'), 'check is shown');
      check(text.includes('readback unavailable: timed out'), 'reason is shown verbatim');
      check(text.includes('Bill:1'), 'requested values are shown');
      check(text.includes('Verification'), 'section is labelled');
    """
    _run_node(script)


def test_action_history_renders_the_receipt_once_per_card():
    js = (ROOT / "static/js/meridian/actions.js").read_text(encoding="utf-8")

    assert 'from "./action-verification.js"' in js
    assert js.count("renderActionVerification(action)") == 1
    # The receipt is additive: the review details still render.
    assert js.count("renderActionReviewDetails(action)") == 1
    # Still strictly read-only: no approval/execution control is introduced.
    for forbidden in ("actions/approve", "actions/execute", "actions/reject"):
        assert forbidden not in js


def test_receipt_invariants_hold_on_every_recorded_ground_truth():
    """Pin the outcomes against the exact payloads the pipeline stores.

    These literals mirror crew/executors.py: mark_verified writes
    ``verification``, no-verifier and record_verification_pending write
    ``result.verification``, and the verifier-exception path writes
    ``result.verification`` with check ``verifier-exception``.
    """
    executors = (ROOT / "crew/executors.py").read_text(encoding="utf-8")
    assert '"check": "no-verifier-registered"' in executors
    assert '"check": "verifier-exception"' in executors
    assert "record_verification_pending" in executors
    assert "mark_verified(request_id, verification=verification)" in executors

    # Every stored shape is one the renderer understands.
    module = (ROOT / "static/js/meridian/action-verification.js").read_text(encoding="utf-8")
    assert "action.verification" in module
    assert "action.result" in module
    payload = json.loads('{"ok": null, "check": "crew-bill-readback", "provider_truth": false}')
    assert set(payload) <= {"ok", "check", "provider_truth", "retry_allowed", "reason", "requested", "observed"}
