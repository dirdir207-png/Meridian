"""OS-083: the payday control routes the owner's own edit through the ACTION PIPELINE.

The owner's rule, restated 2026-09-21: "actions directly made by me in the app circumvent the need
for proposal, I can directly execute." This pins that the payday control USES the general path
rather than growing a parallel one, and that it reports what actually happened.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "static/js/meridian/payday.js"
TEMPLATE = ROOT / "templates/meridian/partials/payday-funding.html"


def _write_block():
    js = JS.read_text(encoding="utf-8")
    return js[js.index("async function setFundingPlan"):js.index("async function load()")]


def test_control_posts_to_the_action_pipeline_with_owner_direct_provenance():
    js = JS.read_text(encoding="utf-8")
    assert '"/api/actions/mutate"' in js, "the control must use the existing general endpoint"
    assert '"update_crew_paycheck_funding_plan"' in js
    assert 'provenance: "owner_direct"' in js, "a direct owner edit is not a proposal"
    assert "fundingPlanId: planId" in js, "the plan id is the identity the readback verifier needs"


def test_control_does_not_go_through_the_proposal_channel():
    assert "meridianPropose" not in _write_block(), (
        "the payday control proposed by default, which parks the owner's own unambiguous edit"
    )


def test_the_message_branches_on_what_actually_happened():
    """A message that always said 'set' would lie whenever the router proposed instead."""
    block = _write_block()
    assert "routing_direct" in block
    assert "Pending Actions" in block


def test_the_write_is_never_retried():
    assert _write_block().count("await fetch(") == 1, (
        "an uncertain financial mutation must not be issued twice"
    )


def test_the_surface_exposes_where_plans_render_and_status_is_announced():
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "data-funding-plans" in template
    assert "data-funding-plan-status" in template
    assert 'aria-live="polite"' in template


def test_the_write_block_is_actually_the_one_under_test():
    """Guards the guards: a `not in` assertion against an EMPTY slice passes vacuously, so the
    slice itself has to be shown to be the real function before the others mean anything."""
    block = _write_block()
    assert "await fetch(" in block, "the slice is not the write function"
    assert len(block) > 400, f"the slice is only {len(block)} chars, so it is not the function"
