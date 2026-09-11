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
