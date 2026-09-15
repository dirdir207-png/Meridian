"""A07: Plan must render durable action state, not HTTP success alone."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_action_outcome_helper_interprets_every_durable_state_with_node():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = r"""
      const { describeActionOutcome } = await import('./static/js/meridian/action-outcome.js');
      const check = (condition, message) => { if (!condition) throw new Error(message); };

      const proposed = describeActionOutcome({ routing_direct: false, action: { state: 'proposed' } });
      check(proposed.tone === 'pending', 'proposal tone');
      check(proposed.message.includes('approve'), 'proposal guidance');
      check(proposed.refresh === false, 'proposal refresh');

      const verified = describeActionOutcome(
        { routing_direct: true, action: { state: 'verified' } },
        { verifiedMessage: 'Bill deleted and verified.' },
      );
      check(verified.tone === 'ok', 'verified tone');
      check(verified.message === 'Bill deleted and verified.', 'verified message');
      check(verified.refresh === true, 'verified refresh');

      const executed = describeActionOutcome({ routing_direct: true, action: { state: 'executed' } });
      check(executed.tone === 'pending', 'executed is not success');
      check(executed.message.includes('verification is still pending'), 'executed explanation');
      check(executed.message.includes('Do not submit it again'), 'executed no-resend guidance');
      check(executed.refresh === false, 'unverified execution must not refresh as success');

      const uncertain = describeActionOutcome({
        routing_direct: true,
        action: {
          state: 'failed',
          result: { error: 'Transfer outcome is uncertain.', verify_state: true },
        },
      });
      check(uncertain.tone === 'error', 'uncertain failure tone');
      check(uncertain.message.includes('Transfer outcome is uncertain.'), 'server error retained');
      check(uncertain.message.includes('Check current Crew state before trying again'), 'uncertain recovery');
      check(uncertain.refresh === false, 'uncertain failure refresh');

      const failed = describeActionOutcome({ routing_direct: true, action: { state: 'failed' } });
      check(failed.tone === 'error', 'failed tone');
      check(failed.message.includes('Action failed'), 'failed label');
      check(failed.message.includes('Actions & Approvals'), 'failed recovery');

      const rejected = describeActionOutcome({ routing_direct: true, action: { state: 'rejected' } });
      check(rejected.tone === 'error' && rejected.message.includes('rejected'), 'rejected state');

      const expired = describeActionOutcome({ routing_direct: true, action: { state: 'expired' } });
      check(expired.tone === 'error' && expired.message.includes('expired'), 'expired state');

      const executing = describeActionOutcome({ routing_direct: true, action: { state: 'executing' } });
      check(executing.tone === 'pending' && executing.message.includes('in progress'), 'executing state');

      const unknown = describeActionOutcome({ routing_direct: true, action: {} });
      check(unknown.tone === 'error', 'unknown tone');
      check(unknown.message.includes('no trustworthy action outcome'), 'unknown explanation');
      check(unknown.refresh === false, 'unknown refresh');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_plan_uses_state_interpreter_without_false_success_copy():
    source = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")

    assert 'from "./action-outcome.js"' in source
    assert source.count("describeActionOutcome(") >= 4
    assert "Executed (${state})." not in source
    assert "Deleted (${result.action && result.action.state})." not in source
    assert 'result.routing_direct ? "Deleted." : "Proposed."' not in source


def test_plan_action_note_has_pending_tone():
    css = (ROOT / "static/css/meridian/plan.css").read_text(encoding="utf-8")

    assert '.m-action-note[data-state="pending"]' in css
    assert "color: var(--m-caution" in css


def test_outcome_interpreter_reports_the_recorded_verification_receipt():
    """C4: Plan and Memory inherit the same receipt the Settings history shows.

    The interpreter must surface *why* an accepted action is unresolved, and must
    not invite a resubmit for an action the provider already accepted.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not available in this environment")
    script = r"""
      const { describeActionOutcome } = await import('./static/js/meridian/action-outcome.js');
      const check = (condition, message) => { if (!condition) throw new Error(message); };

      // Provider accepted the write; the readback timed out. Still unresolved,
      // and the recorded reason must reach the operator instead of a generic line.
      const unresolved = describeActionOutcome({
        routing_direct: true,
        action: {
          state: 'executed',
          result: { verification: { ok: null, check: 'crew-bill-readback',
                                    provider_truth: false, retry_allowed: false,
                                    reason: 'readback unavailable: timed out' } },
        },
      });
      check(unresolved.tone === 'pending', 'unresolved keeps a pending tone');
      check(unresolved.refresh === false, 'unresolved must not refresh as success');
      check(unresolved.message.includes('could not confirm'), 'unresolved states it was unconfirmed');
      check(unresolved.message.includes('crew-bill-readback'), 'recorded check is named');
      check(unresolved.message.includes('timed out'), 'recorded reason is shown');
      check(unresolved.message.includes('Do not resubmit'), 'unresolved forbids resubmission');

      // A verifier raised after the provider accepted the write: same unresolved
      // handling, never a terminal failure invented from an exception.
      const raised = describeActionOutcome({
        routing_direct: true,
        action: {
          state: 'executed',
          result: { verification: { ok: null, check: 'verifier-exception',
                                    provider_truth: false, retry_allowed: false,
                                    reason: 'Verification raised: boom' } },
        },
      });
      check(raised.tone === 'pending', 'exception receipt is pending, not error');
      check(raised.message.includes('verifier-exception'), 'exception check is named');

      // No verifier registered: unconfirmed, and never a success.
      const none = describeActionOutcome({
        routing_direct: true,
        action: { state: 'executed', result: { success: true } },
      });
      check(none.tone === 'pending', 'no-verifier outcome is pending');
      check(none.refresh === false, 'no-verifier outcome must not refresh as success');
      check(none.message.includes('verification is still pending'), 'no-verifier outcome stays pending');
      check(none.message.includes('Do not submit it again'), 'no-verifier outcome forbids resubmission');
      check(!none.message.includes('verified'), 'no-verifier outcome never claims verification');

      // Provider readback contradicted the change: a real, provider-truth
      // failure, and still not an invitation to send it again.
      const contradicted = describeActionOutcome({
        routing_direct: true,
        action: {
          state: 'failed',
          result: { error: 'Post-execution verification failed',
                    verification: { ok: false, check: 'crew-bill-readback',
                                    provider_truth: true,
                                    reason: 'bill fields differ: amount' } },
        },
      });
      check(contradicted.tone === 'error', 'contradiction is an error tone');
      check(contradicted.message.includes('contradicted'), 'contradiction is named as such');
      check(contradicted.message.includes('amount'), 'recorded reason is shown');
      check(contradicted.message.includes('must not be resubmitted'), 'contradiction forbids resubmission');
      check(contradicted.refresh === false, 'contradiction must not refresh as success');

      // An uncertain write with no receipt keeps its original recovery copy.
      const uncertain = describeActionOutcome({
        routing_direct: true,
        action: { state: 'failed', result: { error: 'Transfer outcome is uncertain.', verify_state: true } },
      });
      check(uncertain.message.includes('Check current Crew state before trying again'),
            'uncertain-write recovery copy is preserved');
    """
    result = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_plan_and_memory_receive_the_receipt_through_the_shared_interpreter():
    """Both surfaces must go through the one receipt-aware interpreter."""
    outcome = (ROOT / "static/js/meridian/action-outcome.js").read_text(encoding="utf-8")
    plan = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")
    memory = (ROOT / "static/js/meridian/memory-manage.js").read_text(encoding="utf-8")

    assert 'from "./action-verification.js"' in outcome, "the interpreter must read the recorded receipt"
    assert 'from "./action-outcome.js"' in plan
    assert 'from "./action-outcome.js"' in memory
    # The surfaces must not re-derive a receipt themselves.
    for source in (plan, memory):
        assert "provider_truth" not in source
        assert "summarizeVerification" not in source


def test_every_destructive_plan_control_refuses_a_second_request():
    """A durable action record must not leave the same control live.

    Verifier-less operations stay EXECUTED and never refresh the list, so a
    destructive control that relied on that refresh to disappear would stay
    clickable and create a second mutation request.
    """
    source = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")

    for action_type in ("archive_crew_bill", "delete_crew_autopilot_rule"):
        assert f'type: "{action_type}"' in source, f"{action_type} call site missing"
        handler = source.split(f'type: "{action_type}"', 1)[1].split("} catch (error)", 1)[0]
        assert "del.disabled = true" in handler, (
            f"the {action_type} control can be clicked again after a durable outcome"
        )
