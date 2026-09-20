"""R30: Crew feature-parity contract (family accounts excluded by scope).

For each legacy Crew-backed capability, assert Meridian exposes either a
REAL control (approval-gated, wired to a proposal) or an explicit, honest
`data-parity-deferred` marker. The parity list is a contract: a capability
may move from deferred to wired only by adding the real control AND removing
its deferred marker — never by deleting the marker alone.

Family accounts are explicitly OUT of scope per the owner's direction.

Checks (real backend via APP_URL, no external bank action):
  1. Wired controls render on the Plan workspace:
       - data-plan-new-commitment  (Crew bill write-back / commitment proposal)
       - data-plan-new-rule        (Create autopilot rule proposal)
  2. Every deferred capability in the contract is honestly listed with a
     data-parity-deferred marker (no capability silently dropped).
  3. Deferred items run only through legacy — nothing on the parity list is
     presented as a live Meridian Crew write control.
"""

import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL is required for browser tests")

DESKTOP = {"width": 1440, "height": 900}
OWNER_PASSWORD = "meridian-owner-2026"

# Crew-backed capabilities not yet exposed as a Meridian control. These must
# each carry an explicit deferred marker on the Plan page.
#
# OS-066: this dict used to be hand-maintained AND stale — it named
# "Set active spend pocket", "Delete pocket" and "Delete autopilot rule" as
# deferred while all three had working forms in the same pane — and because the
# only assertions below were about PRESENTATION (a marker exists and renders as
# list text), the stale contract and the stale template validated each other and
# the suite stayed green while the page told the owner he could not do three
# things he could do. Keys are now the SHIPPED COMMAND KINDS from
# meridian/crew_commands.py, and `test_deferred_set_matches_the_shipped_command_surface`
# fails closed on drift in either direction.
DEFERRED_CAPABILITIES = {
    # from meridian/crew_commands.py, reachable only via legacy Crew
    "create_pocket_reassignment_rule": "Create pocket reassignment rule",
    "delete_pocket_reassignment_rule": "Delete pocket reassignment rule",
    # The rule sheet on Plan creates a NEW rule; nothing edits an existing one.
    "edit_autopilot_rule": "Edit autopilot rule",
    # `create_virtual_card` IS wired in this pane; only the update half is not
    "update_virtual_card": "Update virtual card",
}

# Shipped command kinds deliberately NOT on the deferred list for the reason in each
# comment. Named explicitly rather than left implicit so the drift check can tell an
# intended exclusion from an oversight, and so the reason is re-verified rather than
# inherited. The rule for membership: Plan already reaches the capability by SOME
# control, so calling it "deferred" would be a false statement about the owner's
# abilities — which is the OS-066 defect. This constant is about REACHABILITY, not
# about whether a `data-ca-*` form exists, which is what WIRED_IN_THE_CREW_PANE records.
PLAN_REACHABLE_OUTSIDE_THE_CREW_PANE = {
    # Rules tab renders this as a real control: `data-plan-new-rule`.
    "create_autopilot_rule": "Create autopilot rule (Rules tab: data-plan-new-rule)",
    # Per-commitment Delete button in the commitment inspector (plan.js ~636) dispatches
    # `archive_crew_bill` and verifies the outcome, so the owner CAN delete a bill.
    "delete_bill": "Delete a commitment (inspector Delete button -> archive_crew_bill)",
}

# Wired controls that must render as real, approval-gated Meridian controls.
WIRED_PLAN_CONTROLS = {
    "data-plan-new-commitment": "New commitment (Crew bill write-back)",
    "data-plan-new-rule": "New autopilot rule",
}

# Commands with a LIVE write form in the Crew pane, mapped to the marker that proves it.
# Read from templates/meridian/partials/plan.html; the drift test fails if any of these
# is claimed as deferred, which is the OS-066 defect.
#
# `top_up_crew_reserve` is deliberately NOT here: it is an ACTION type dispatched in
# meridian/crew_write_actions.py, not a CommandSpec in meridian/crew_commands.py, so it
# is outside this contract's surface.
WIRED_IN_THE_CREW_PANE = {
    "create_pocket": "data-ca-create-pocket",
    "create_bill": "data-ca-create-bill",
    "delete_pocket": "data-ca-delete-pocket",
    "set_spend_pocket": "data-ca-set-spend",
    "delete_autopilot_rule": "data-ca-delete-rule",
    "create_virtual_card": "data-ca-create-virtual-card",
}


def _shipped_command_kinds():
    """Every command kind declared in meridian/crew_commands.py (the source of truth)."""
    source = (ROOT / "meridian" / "crew_commands.py").read_text(encoding="utf-8")
    return set(re.findall(r'^\s*"([a-z_]+)":\s*CommandSpec\(', source, flags=re.MULTILINE))


def _authed_page(context):
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200, f"owner login must succeed: {response.status}"
    return context.new_page()


def test_wired_crew_controls_render_on_plan(browser):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=DESKTOP)
    page = _authed_page(context)
    page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="networkidle")

    for data_attr, label in WIRED_PLAN_CONTROLS.items():
        control = page.locator(f"[{data_attr}]")
        assert control.count() >= 1, (
            f"R30 parity: '{label}' should expose a real Meridian control "
            f"({data_attr}), but none rendered on the Plan workspace."
        )
        assert control.first.is_visible(), (
            f"R30 parity: '{label}' rendered but is not visible."
        )
        # The control must open an approval-gated proposal, i.e. it is a button.
        assert control.first.get_attribute("aria-haspopup") in ("dialog", None), (
            f"R30 parity: '{label}' should be an action (button) that opens an "
            f"approval-gated proposal flow."
        )


def test_every_deferred_capability_has_an_honest_marker(browser):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=DESKTOP)
    page = _authed_page(context)
    page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="networkidle")
    # Deferred Crew parity is intentionally scoped to the Crew segment, which
    # keeps the main Plan surface focused while remaining discoverable.
    page.get_by_role("button", name="Crew", exact=True).click()

    for key, label in DEFERRED_CAPABILITIES.items():
        marker = page.locator(f"[data-parity-deferred='{key}']")
        assert marker.count() == 1, (
            f"R30 parity: '{label}' ({key}) must carry exactly one honest "
            f"deferred marker, but found {marker.count()}."
        )
        assert marker.first.is_visible(), (
            f"R30 parity: the deferred marker for '{label}' is present but hidden "
            f"or out of the a11y tree — it must be honest and visible."
        )


def test_deferred_set_matches_the_shipped_command_surface():
    """OS-066: the contract must be derived from reality, not hand-maintained.

    This is the assertion whose absence let the parity list go stale. It runs without a
    browser, because the defect it prevents is a template/contract mismatch rather than a
    rendering problem.
    """
    shipped = _shipped_command_kinds()
    assert shipped, "meridian/crew_commands.py must declare command kinds (parser/format drift?)"

    declared = set(DEFERRED_CAPABILITIES)
    excused = set(PLAN_REACHABLE_OUTSIDE_THE_CREW_PANE)

    unknown = declared - shipped
    assert not unknown, (
        f"deferred keys must be real shipped command kinds; unknown: {sorted(unknown)}"
    )
    # A capability with a live control in this pane must NOT be called deferred.
    wired_here = set(WIRED_IN_THE_CREW_PANE)
    wrongly_deferred = declared & wired_here
    assert not wrongly_deferred, (
        f"these are wired in the Crew pane and must not be listed as deferred: "
        f"{sorted(wrongly_deferred)}"
    )

    covered = declared | wired_here | excused
    unaccounted = shipped - covered
    assert not unaccounted, (
        f"every shipped command kind must be accounted for as deferred, wired in the "
        f"Crew pane, or excused as Plan-reachable elsewhere; unaccounted: "
        f"{sorted(unaccounted)}. Add each to the matching constant — do NOT silence this "
        f"by widening the deferred list, which is how the list went stale in OS-066."
    )

    overlap = declared & excused
    assert not overlap, (
        f"a capability cannot be both deferred and excused as Plan-reachable: {sorted(overlap)}"
    )


def test_deferred_set_matches_the_template():
    """Every declared deferred key must carry exactly one marker in plan.html."""
    template = (ROOT / "templates" / "meridian" / "partials" / "plan.html").read_text(encoding="utf-8")
    marked = set(re.findall(r'data-parity-deferred="([a-z_]+)"', template))
    declared = set(DEFERRED_CAPABILITIES)
    assert marked == declared, (
        f"plan.html deferred markers and the parity contract have drifted: "
        f"only in template: {sorted(marked - declared)}; "
        f"only in contract: {sorted(declared - marked)}"
    )


def test_deferred_items_are_not_live_crew_write_controls(browser):
    """The deferred parity list must not present any capability as a live Crew
    write control. Each deferred entry is list text, not a trigger button."""
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=DESKTOP)
    page = _authed_page(context)
    page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="networkidle")

    parity = page.locator("[data-crew-parity]")
    assert parity.count() == 1, "a single honest parity section should render"
    # No deferred entry may be an actionable control (button/link that submits).
    for item in parity.locator("[data-parity-deferred]").all():
        tag = item.evaluate("el => el.tagName")
        assert tag in ("LI", "P", "DIV", "SPAN", "DD"), (
            f"R30 parity: deferred item rendered as <{tag}>, which looks like a "
            f"control; it should be plain list text only."
        )
