"""Mechanism C, first application: Virgil's panel TRANSITIONS.

WHY THIS FILE EXISTS AND WHY A CAPTURE WAS NOT ENOUGH. The governed capture matrix records STATES
-- ten frames across five viewports, both themes -- and every one of them showed the panel open
and looking correct. Neither of the owner's two defects is visible in a state: the soft keyboard
appears DURING the open, and the black screen appears AFTER the close. Sixteen surface guards
passed while both were live, because a screenshot of an open panel is not evidence about what
opening it does, and nothing anywhere performed a close.

The owner's report, kept because it is the acceptance case: Virgil "summons the soft keyboard on
open and leaves a black or partially black screen" on close.

Two root causes, and the first is the reason this file asserts on FOCUS rather than only on
visibility:

1. THE KEYBOARD HAD TWO CAUSES. `advisor_fab.js` called `input.focus()` on open, AND the input
   carried `data-sheet-initial-focus`, which `shell.js` focuses on open. Removing either one alone
   leaves the keyboard appearing -- so a "fix" that had only removed the JS line would have tested
   green on a keyboard-free assertion written by the same person who removed it. The assertions
   below therefore check the OUTCOME (focus is not the composer) rather than the mechanism.

2. THE BLACK SCREEN WAS A STATE THAT OUTLIVED ITS CLOSE. `#advisor-panel` is `display: none` only
   while it lacks `[data-open]` (advisor.css:105,145), and on a phone it spans from 0.75rem to
   0.75rem with a `--m-surface` fill -- dark navy in the dark theme -- so a panel whose `data-open`
   was never removed covers the screen and looks exactly like a crash. The transition is asserted
   from the ELEMENT's computed state, not from the absence of an error.
"""
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL is required for browser tests")


def _open_panel(page):
    """Click the trigger and wait for the sheet.

    The trigger is only DISPLAYED under `body:has([data-meridian-shell])` (advisor.css:74-89), so a
    click issued before the shell initialises fails with "element is not visible" -- which is what
    the first run of this file did, at the desktop viewport, against the owner's instance. The
    navigation and the wait mirror tests/browser/test_contextual_advisor.py, which is the working
    precedent: same workspace, same trigger, same ordering.
    """
    fab = page.locator("#advisor-fab")
    fab.wait_for(state="visible", timeout=15000)
    fab.click()
    page.wait_for_timeout(200)


def _goto_and_open(page):
    page.goto(f"{APP_URL}/meridian?workspace=activity", wait_until="domcontentloaded")
    _open_panel(page)


def test_opening_does_not_focus_the_composer(browser):
    """The keyboard must not appear by itself. Focus must still move INTO the dialog."""
    from tests.browser.test_transaction_inspector import MOBILE_VIEWPORT, _authed_page

    # A PHONE viewport, not the helper's desktop default. Both defects are phone defects -- the
    # soft keyboard and the full-height sheet -- and the trigger is deliberately not rendered at
    # desktop widths. The first two runs of this file used 1440x900 and the FAB resolved to
    # HIDDEN, which is the viewport talking, not the product.
    context, page = _authed_page(browser, MOBILE_VIEWPORT)
    _goto_and_open(page)

    active_id = page.evaluate("document.activeElement ? document.activeElement.id : null")
    assert active_id != "advisor-fab-input", (
        "opening Virgil focused the composer, which summons the soft keyboard over the briefing "
        "the owner opened the panel to read"
    )
    inside = page.evaluate(
        "!!document.getElementById('advisor-panel').contains(document.activeElement)"
    )
    assert inside, "focus must still move into the dialog, or the sheet becomes a keyboard trap"
    context.close()


def test_closing_leaves_no_dark_sheet_and_no_inert_page(browser):
    """The transition itself: open, then close, then assert there is nothing left behind."""
    from tests.browser.test_transaction_inspector import MOBILE_VIEWPORT, _authed_page

    # A PHONE viewport, not the helper's desktop default. Both defects are phone defects -- the
    # soft keyboard and the full-height sheet -- and the trigger is deliberately not rendered at
    # desktop widths. The first two runs of this file used 1440x900 and the FAB resolved to
    # HIDDEN, which is the viewport talking, not the product.
    context, page = _authed_page(browser, MOBILE_VIEWPORT)
    _goto_and_open(page)
    assert page.locator("#advisor-panel[data-open]").count() == 1, "the panel did not open"

    page.locator("#advisor-panel .m-advisor-close").click()
    page.wait_for_timeout(200)

    assert page.locator("#advisor-panel[data-open]").count() == 0, "the panel kept its open state"
    display = page.evaluate(
        "getComputedStyle(document.getElementById('advisor-panel')).display"
    )
    assert display == "none", (
        f"the panel is still rendered (display: {display}) after closing, which on a phone is a "
        "near-full-screen dark sheet -- the owner's black screen"
    )
    inert = page.evaluate(
        "const m = document.getElementById('main'); return !!(m && m.inert);"
    )
    assert inert is False, "the page stayed inert after closing, so nothing is clickable"


def test_the_panel_can_be_reopened_after_closing(browser):
    """A close that leaves state behind usually breaks the SECOND open, which a single
    open-then-close assertion would never catch."""
    from tests.browser.test_transaction_inspector import MOBILE_VIEWPORT, _authed_page

    # A PHONE viewport, not the helper's desktop default. Both defects are phone defects -- the
    # soft keyboard and the full-height sheet -- and the trigger is deliberately not rendered at
    # desktop widths. The first two runs of this file used 1440x900 and the FAB resolved to
    # HIDDEN, which is the viewport talking, not the product.
    context, page = _authed_page(browser, MOBILE_VIEWPORT)
    _goto_and_open(page)
    page.locator("#advisor-panel .m-advisor-close").click()
    page.wait_for_timeout(200)
    _open_panel(page)

    assert page.locator("#advisor-panel[data-open]").count() == 1, "the panel did not reopen"
    display = page.evaluate(
        "getComputedStyle(document.getElementById('advisor-panel')).display"
    )
    assert display != "none", "the panel is marked open but is not rendered"
    context.close()
