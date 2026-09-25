"""OS-079 acceptance: the Safe-to-Spend explanation is a real disclosure, not decoration.

Isolated and deterministic: the REAL stylesheets and the REAL today.js module, driven from a
synthetic /api/meridian/today payload. No app, no credentials, no provider, no server.

What this file is FOR. The figure is the one the owner acts on, and it was wrong once already
(D-019: 424.90 shown where the truth was 100.00). An explanation that is merely plausible is
worse than none, so these tests pin the properties that make it trustworthy rather than pretty:
it says what the SERVER said, it is reachable by keyboard and not only by hover, it does not
pretend a subtraction happened when none did, and it never renders a negative as healthy money.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "browser" / "fixtures" / "safe-to-spend-explanation.html"


def _breakdown(lines, result, explanation, *, amount=None):
    return {
        "amount": result if amount is None else amount,
        "status": "available",
        "breakdown": {
            "currency": "USD",
            "lines": [{"label": label, "amount": value} for label, value in lines],
            "result_label": "Safe to spend",
            "result": result,
            "explanation": explanation,
        },
    }


# The owner's own worked example, 2026-09-25: "If my total balance is 1000 and my bill reserve is
# 100, and I have an emergency fund of 100, my safe to spend isn't 900, it's 800."
TUCKED = _breakdown(
    [("Available balance", 1000.0), ("Bill reserve", -100.0), ("Emergency fund", -100.0)],
    800.0,
    "Everything you have set aside is subtracted. The rest is safe to spend.",
)

NOTHING_SUBTRACTED = _breakdown(
    [("Available balance", 424.90)],
    424.90,
    "Available balance is the discretionary balance Meridian reads directly. No reserve overdraft "
    "was observed, so nothing is subtracted.",
)

# A pocket holding zero must not draw a row (owner: "pockets only appear ... if they have a
# balance"). The $0.00 goal is the case that would otherwise render as "-$0.00" noise.
WITH_A_ZERO_LINE = _breakdown(
    [
        ("Available balance", 1000.0),
        ("Bill reserve", -100.0),
        ("Christmas fund", 0.0),
        ("Emergency fund", -100.0),
    ],
    800.0,
    "Everything you have set aside is subtracted. The rest is safe to spend.",
)

# The server's result deliberately does NOT equal the sum of its lines. If the client ever
# re-derives the figure instead of rendering what it was sent, this payload exposes it -- which is
# the point, because a client that re-derives can drift from the server that computed it.
SERVER_SAID_SOMETHING_ELSE = _breakdown(
    [("Available balance", 1000.0), ("Bill reserve", -100.0), ("Emergency fund", -100.0)],
    799.99,
    "Synthetic payload whose result does not equal its own lines.",
)

NEGATIVE = _breakdown(
    [("Available balance", 100.0), ("Bill reserve", -220.0)],
    -120.0,
    "The bill reserve is overdrawn.",
)


def _router(payload):
    def handler(route):
        path = urlparse(route.request.url).path
        if path == "/":
            route.fulfill(path=str(FIXTURE), content_type="text/html")
            return
        if path == "/api/meridian/today":
            # Every constant above IS the `safe_to_spend` object; the payload must wrap it, or
            # today.js reads `payload.safe_to_spend || {}` and renders the empty state silently.
            body = {
                "editorial": {},
                "forecast": {},
                "data_freshness": None,
                "safe_to_spend": payload,
            }
            route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
            return
        candidate = (ROOT / path.lstrip("/")).resolve()
        if (path.startswith("/static/") and (ROOT / "static") in candidate.parents
                and candidate.is_file()):
            route.fulfill(path=str(candidate))
        else:
            route.abort()
    return handler


@contextmanager
def open_sts(payload):
    """Yield ``(page, console_errors)`` for the fixture driven from ``payload``."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 420, "height": 912},
                                      device_scale_factor=3)
        context.add_init_script("window.setInterval = () => 0;")
        page = context.new_page()
        page.clock.install(time=1788874920000)
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("**/*", _router(payload))
        page.goto("http://today.test/")
        page.wait_for_selector("[data-sts-explain]")
        page.evaluate("document.fonts.ready")
        yield page, errors
        context.close()
        browser.close()


def _labels(page):
    return page.eval_on_selector_all(".m-sts-line-label", "els => els.map(e => e.textContent)")


def _amounts(page):
    return page.eval_on_selector_all(".m-sts-line-amount", "els => els.map(e => e.textContent)")


def test_the_explanation_is_closed_until_asked_and_the_mark_is_decoration():
    with open_sts(TUCKED) as (page, errors):
        assert page.locator("[data-sts-explanation]").is_hidden()
        assert page.get_attribute("[data-sts-explain]", "aria-expanded") == "false"
        # The engraving is art: it must not be read out as though it carried meaning.
        assert page.get_attribute(".m-sts-explain-mark", "aria-hidden") == "true"
        assert errors == [], f"the page logged errors: {errors}"


def test_it_opens_on_hover_and_on_keyboard_focus_rather_than_hover_only():
    with open_sts(TUCKED) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        assert page.locator("[data-sts-explanation]").is_visible()
        assert page.get_attribute("[data-sts-explain]", "aria-expanded") == "true"

        page.dispatch_event("[data-today-safe]", "mouseleave")
        assert page.locator("[data-sts-explanation]").is_hidden()

        # The keyboard path must work on its own: a disclosure only a pointer can reach is not one.
        page.focus("[data-sts-explain]")
        assert page.locator("[data-sts-explanation]").is_visible()
        assert page.get_attribute("[data-sts-explain]", "aria-expanded") == "true"


def test_a_deliberate_open_survives_the_pointer_leaving_and_escape_closes_it():
    with open_sts(TUCKED) as (page, _errors):
        page.click("[data-sts-explain]")
        page.dispatch_event("[data-today-safe]", "mouseleave")
        page.dispatch_event("[data-sts-explain]", "blur")
        assert page.locator("[data-sts-explanation]").is_visible(), (
            "clicking pins the explanation open; moving the pointer away must not dismiss it"
        )

        page.keyboard.press("Escape")
        assert page.locator("[data-sts-explanation]").is_hidden()
        assert page.get_attribute("[data-sts-explain]", "aria-expanded") == "false"
        assert page.evaluate(
            "document.activeElement === document.querySelector('[data-sts-explain]')"
        ), "Escape must return focus to the control rather than dropping it"


def test_it_renders_every_line_the_server_sent_named_after_its_own_pocket():
    """Completeness is the owner's requirement: 'I would still want everything included for a
    solid understanding of safe to spend without leaving things out.' The emergency fund is a
    line precisely because it was subtracted -- 1000 less 100 less 100 is 800, not 900."""
    with open_sts(TUCKED) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        assert _labels(page) == [
            "Available balance", "Bill reserve", "Emergency fund", "Safe to spend",
        ]
        assert _amounts(page) == ["$1,000.00", "-$100.00", "-$100.00", "$800.00"]


def test_it_shows_the_servers_result_and_never_re_derives_one():
    """The payload's lines sum to 800.00 and its result says 799.99. The panel must show 799.99.

    This is the D-019 rule made executable: the server assembles the breakdown BECAUSE a client
    that re-derives the number can drift from the server that computed it, 'which is how this went
    wrong in the first place'. If this test ever fails, the client has started computing.
    """
    with open_sts(SERVER_SAID_SOMETHING_ELSE) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        shown = page.locator(".m-sts-line--result .m-sts-line-amount").text_content()
        assert shown == "$799.99"
        assert shown != "$800.00"


def test_a_line_holding_zero_is_omitted_and_the_result_is_always_drawn_last():
    with open_sts(WITH_A_ZERO_LINE) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        labels = _labels(page)
        assert "Christmas fund" not in labels
        assert "-$0.00" not in _amounts(page)
        assert labels[-1] == "Safe to spend", "the result row is drawn unconditionally, and last"


def test_nothing_subtracted_renders_one_line_and_no_empty_adjustment_row():
    """An explanation that describes arithmetic the calculation never performed is worse than
    none. One line in, one line out, and the prose says so."""
    with open_sts(NOTHING_SUBTRACTED) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        assert _labels(page) == ["Available balance", "Safe to spend"]
        assert "nothing is subtracted" in page.locator(".m-sts-explain-note").text_content()


def test_a_negative_safe_to_spend_never_renders_as_healthy_money():
    """The result row carries the FIGURE's signal, not a fixed colour. A green negative would be
    the same class of lie as a green zero."""
    with open_sts(NEGATIVE) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        assert page.get_attribute("[data-sts-explanation]", "data-signal") == "negative"
        result_colour = page.eval_on_selector(
            ".m-sts-line--result .m-sts-line-amount", "el => getComputedStyle(el).color"
        )
        figure_colour = page.eval_on_selector(
            "[data-sts-figure]", "el => getComputedStyle(el).color"
        )
        assert result_colour == figure_colour, (
            f"the breakdown's result {result_colour} disagrees with the figure {figure_colour}"
        )


def test_the_strip_does_not_overflow_the_owners_viewport():
    """The owner reads Meridian at 420x912. The panel must not push the page sideways."""
    with open_sts(WITH_A_ZERO_LINE) as (page, _errors):
        page.dispatch_event("[data-sts-explain]", "mouseenter")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
