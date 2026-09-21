"""Mechanism C, first application: Virgil's panel TRANSITIONS.

WHY THIS FILE EXISTS AND WHY A CAPTURE WAS NOT ENOUGH. The governed capture matrix records STATES
-- ten frames across five viewports, both themes -- and every one of them showed the panel open
and looking correct. Neither defect the owner reported is visible in a state: the soft keyboard
appears DURING the open, and the black screen appears AFTER the close. Sixteen surface guards and
all ten frames passed while both were live, because a screenshot of an open panel is not evidence
about what opening it does, and nothing anywhere performed a close.

The owner's report, kept because it is the acceptance case: Virgil "summons the soft keyboard on
open and leaves a black or partially black screen" on close.

TWO ROOT CAUSES, and the first is why the assertions check the OUTCOME rather than the mechanism:

1. THE KEYBOARD HAD TWO CAUSES. advisor_fab.js called input.focus() on open, AND the input carried
   data-sheet-initial-focus, which shell.js focuses on open. Removing either one alone leaves the
   keyboard appearing -- so a fix that had removed only the obvious JS line would have tested green
   against an assertion written by the same person who removed it.

2. THE BLACK SCREEN WAS A STATE THAT OUTLIVED ITS CLOSE. #advisor-panel is display:none only while
   it lacks [data-open] (advisor.css:105,145), and on a phone it spans 0.75rem to 0.75rem with a
   --m-surface fill -- dark navy in the dark theme -- so a panel whose data-open was never removed
   covers the screen and looks exactly like a crash.

WHY IT RUNS AT 420x912 AT DPR 3 IN BOTH THEMES. OS-080's own acceptance criterion 4 says so: the
verification must be by REAL INPUT at the owner's device viewport, in both themes, and explicitly
"not by a capture of the panel already open". The shared _authed_page helper takes a viewport but
no device_scale_factor and no theme, which is why this file builds its own context.

FIVE THINGS WENT WRONG BEFORE IT RAN GREEN, and each was a real cause worth keeping: no visibility
wait; the Today workspace, where the trigger is hidden BY DESIGN (dial.css:1038); the viewport,
which was never the issue; missing API fixtures; and finally that a display:none element cannot be
clicked even with force=True, so the trigger's own handler is dispatched directly. The file also
caught a FALSE DEFECT IN ITSELF: selecting a transaction first opens the transaction inspector,
which is itself a modal sheet, so #main is CORRECTLY inert while it is open, and an earlier version
asserted against that and reported residue that was not there.
"""
import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL is required for browser tests")

#: The owner's device, and the viewport OS-080's criterion 4 names.
OWNER_DEVICE = {"width": 420, "height": 912}

#: Both themes, because light-theme regressions do not surface from dark captures alone.
THEMES = ("dark", "light")


def _owner_device_page(browser, theme):
    """An authenticated context at the owner's device, in one theme.

    Built here rather than reusing _authed_page because that helper offers no device_scale_factor
    and no theme, and criterion 4 requires both.
    """
    from tests.browser.conftest import ensure_owner
    from tests.browser.test_transaction_inspector import OWNER_PASSWORD

    ensure_owner()
    context = browser.new_context(
        viewport=OWNER_DEVICE, device_scale_factor=3, color_scheme=theme
    )
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200, f"login failed with {response.status}"
    return context, context.new_page()


def _open_panel(page):
    """Dispatch the trigger's own handler.

    The trigger's VISIBILITY is governed by rules unrelated to the transition under test -- most
    sharply dial.css:1038, which hides it on the Today workspace by design -- and a display:none
    element has no bounding box, so neither a normal nor a force=True click can reach it (both were
    tried). el.click() runs the app's real open path unchanged; only the pointer's ability to reach
    a hidden button is skipped.
    """
    fab = page.locator("#advisor-fab")
    fab.wait_for(state="attached", timeout=15000)
    fab.evaluate("el => el.click()")
    page.wait_for_timeout(250)


def _goto_and_open(page):
    """Navigate and open Virgil, with NOTHING ELSE OPEN.

    Activity rather than Today, because the trigger is hidden on Today by design. It deliberately
    does NOT select a transaction first: selecting one opens the transaction inspector, itself a
    modal sheet, which correctly leaves #main inert while it is open and would masquerade as
    residue from Virgil.
    """
    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    _open_panel(page)


def _resting_state(page):
    """What the page looked like before Virgil was opened, for differential assertions."""
    return page.evaluate(
        """() => {
          const fab = document.getElementById('advisor-fab');
          return {
            fabDisplay: fab ? getComputedStyle(fab).display : null,
            bodyOverflow: getComputedStyle(document.body).overflow,
            scrollLocked:
              document.body.classList.contains('is-locked') ||
              document.body.classList.contains('m-scroll-lock') ||
              document.documentElement.classList.contains('is-locked'),
          };
        }"""
    )


@pytest.mark.parametrize("theme", THEMES)
def test_opening_does_not_focus_the_composer(browser, theme):
    """Criterion 1 and 2: no keyboard, but focus is not stranded either."""
    context, page = _owner_device_page(browser, theme)
    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    _open_panel(page)

    active_id = page.evaluate("document.activeElement ? document.activeElement.id : null")
    assert active_id != "advisor-fab-input", (
        "opening Virgil focused the composer, which summons the soft keyboard over the briefing "
        "the owner opened the panel to read"
    )
    inside = page.evaluate(
        "!!document.getElementById('advisor-panel').contains(document.activeElement)"
    )
    assert inside, "focus must still move into the dialog, or the sheet becomes a keyboard trap"

    # Criterion 2's second clause: the composer and the close control must still be REACHABLE by
    # Tab, or a keyboard user is locked out of the surface that just declined to focus them.
    reachable = page.evaluate(
        """() => {
          const ids = ['advisor-fab-input', 'advisor-close'];
          return ids.every((id) => {
            const el = document.getElementById(id);
            return !!el && el.tabIndex >= 0 && !el.disabled;
          });
        }"""
    )
    assert reachable, "the composer or the close control is not reachable by Tab after opening"
    context.close()


@pytest.mark.parametrize("theme", THEMES)
def test_closing_leaves_no_residue_of_any_kind(browser, theme):
    """Criterion 3, all three clauses: no overlay, no scroll lock, trigger restored."""
    context, page = _owner_device_page(browser, theme)
    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    before = _resting_state(page)
    _open_panel(page)
    assert page.locator("#advisor-panel[data-open]").count() == 1, "the panel did not open"

    page.locator("#advisor-close").click()
    page.wait_for_timeout(250)

    assert page.locator("#advisor-panel[data-open]").count() == 0, "the panel kept its open state"
    display = page.evaluate("getComputedStyle(document.getElementById('advisor-panel')).display")
    assert display == "none", (
        f"the panel is still rendered (display: {display}) after closing, which on a phone is a "
        "near-full-screen dark sheet -- the owner's black screen"
    )
    inert = page.evaluate(
        "() => { const m = document.getElementById('main'); return !!(m && m.inert); }"
    )
    assert inert is False, "the page stayed inert after closing, so nothing is clickable"

    after = _resting_state(page)
    assert after["scrollLocked"] == before["scrollLocked"], (
        f"closing changed the page's scroll-lock state: {before} -> {after}"
    )
    assert after["bodyOverflow"] == before["bodyOverflow"], (
        f"closing left the body overflow changed: {before} -> {after}"
    )
    assert after["fabDisplay"] == before["fabDisplay"], (
        "closing did not restore the trigger to the state it was in before opening: "
        f"{before['fabDisplay']} -> {after['fabDisplay']}"
    )
    context.close()


@pytest.mark.parametrize("theme", THEMES)
def test_the_panel_can_be_reopened_after_closing(browser, theme):
    """A close that leaves state behind usually breaks the SECOND open, which a single
    open-then-close assertion would never catch."""
    context, page = _owner_device_page(browser, theme)
    _goto_and_open(page)
    page.locator("#advisor-close").click()
    page.wait_for_timeout(250)
    _open_panel(page)

    assert page.locator("#advisor-panel[data-open]").count() == 1, "the panel did not reopen"
    display = page.evaluate("getComputedStyle(document.getElementById('advisor-panel')).display")
    assert display != "none", "the panel is marked open but is not rendered"
    context.close()
