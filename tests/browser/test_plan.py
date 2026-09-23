import json
import os

import pytest

APP_URL = os.getenv("APP_URL")
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL is required for browser tests")

DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}
OWNER_PASSWORD = "meridian-owner-2026"


def _authed_page(browser, viewport=DESKTOP_VIEWPORT):
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=viewport)
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200
    return context, context.new_page()


def _fulfill(payload, status=200):
    body = json.dumps(payload)

    def handler(route):
        route.fulfill(status=status, content_type="application/json", body=body)

    return handler


PLAN_PAYLOAD = {
    "summary": {
        "headline": "2 commitments, 25% funded",
        "commitment_count": 2,
        "total_target": 1080.0,
        "total_funded": 250.0,
        "unfunded": 830.0,
        "coverage_ratio": 0.23,
        "next_due": "2026-10-01",
        "first_shortfall": {
            "date": "2026-09-05",
            "amount": 50.0,
            "cause": "Vacation wanted $150.00 but only $100.00 of cash was available",
        },
    },
    "commitments": [
        {
            "id": 1,
            "type": "goal",
            "name": "Vacation",
            "status": "active",
            "priority": 3,
            "target": 1000.0,
            "funded": 250.0,
            "unfunded": 750.0,
            "due_date": None,
            "target_date": None,
            "backing": {"account_id": 3, "name": "Vacation pocket"},
            "rule_ids": ["1"],
            "projected_30d": 50.0,
            "explanation": ["$250.00 already set aside"],
        },
        {
            "id": 2,
            "type": "bill",
            "name": "Internet",
            "status": "active",
            "priority": 3,
            "target": 80.0,
            "funded": 0.0,
            "unfunded": 80.0,
            "due_date": "2026-10-01",
            "target_date": None,
            "backing": None,
            "rule_ids": [],
            "projected_30d": 0.0,
            "explanation": ["No funding activity yet"],
        },
    ],
    "timeline": {
        "start": "2026-09-01",
        "end": "2026-10-01",
        "events": [
            {
                "date": "2026-09-04",
                "amount": 50.0,
                "commitment": "Vacation",
                "commitment_id": 1,
                "rule_id": "1",
                "source": "paycheck",
                "explanation": [],
            }
        ],
    },
    "allocation": {
        "cash_total": 1500.0,
        "segments": [
            {"label": "Bills", "amount": 1000.0},
            {"label": "Goals", "amount": 0.0},
            {"label": "Available", "amount": 500.0},
        ],
    },
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-08-27T12:00:00Z"},
}


def _install_routes(page, plan_payload=PLAN_PAYLOAD):
    page.route("**/api/meridian/plan*", _fulfill(plan_payload))


def test_plan_renders_command_timeline_and_allocation():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _authed_page(browser)
        _install_routes(page)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(250)

        root = page.locator("[data-plan-root]")
        assert root.is_visible()
        assert "2 commitments" in page.locator("[data-plan-headline]").inner_text()
        assert "%" in page.locator("[data-coverage-text]").inner_text()
        assert page.locator("[data-plan-total]").inner_text() != "—"
        assert page.locator("[data-plan-shortfall]").is_visible()

        timeline_rows = page.locator("[data-timeline] li")
        assert timeline_rows.count() == 1
        assert "Vacation" in timeline_rows.nth(0).inner_text()

        # Concept 02 renders the allocation as medallions on the kit's folded map, so
        # each payload segment must reach a station with its own label and amount, and
        # the decorative art and rules must stay out of the accessibility tree.
        medallions = page.locator("[data-allocation-medallions] .m-plan-medallion")
        assert medallions.count() == 3
        assert "Bills" in medallions.nth(0).inner_text()
        assert "1,000" in medallions.nth(0).inner_text()
        assert "Goals" in medallions.nth(1).inner_text()
        assert "Available" in medallions.nth(2).inner_text()
        assert "500" in medallions.nth(2).inner_text()
        assert page.locator("[data-allocation-links]").get_attribute("aria-hidden") == "true"
        assert page.locator("[data-allocation-map] .m-plan-map-hub").get_attribute("aria-hidden") == "true"

        cards = page.locator("[data-commitment-card]")
        assert cards.count() == 2
        assert "backed by Vacation pocket" in cards.nth(0).inner_text()
        browser.close()


def test_funding_editor_saves_changes_as_a_proposal():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _authed_page(browser)
        _install_routes(page)

        proposals = []

        def capture(route):
            proposals.append(json.loads(route.request.post_data))
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"proposal": {"id": "abc123"}}),
            )

        page.route("**/api/meridian/funding-rules/propose", capture)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(250)

        card = page.locator('[data-commitment-card="1"]')
        card.get_by_role("button", name="Edit funding").click()

        editor = card.locator("[data-funding-editor]")
        assert editor.is_visible()
        assert "Fixed per paycheck" in editor.inner_text()

        editor.locator('input[name="amount"]').fill("75")
        assert "75" in editor.locator("[data-editor-preview]").inner_text()

        editor.get_by_role("button", name="Save as proposal").click()
        page.wait_for_timeout(200)

        assert len(proposals) == 1
        assert proposals[0]["commitment_id"] == 1
        assert proposals[0]["rule"]["kind"] == "fixed_per_paycheck"
        assert proposals[0]["rule"]["amount"] == 75
        assert "Pending Actions" in editor.locator("[data-editor-note]").inner_text()
        browser.close()


def test_plan_is_reachable_and_readable_on_mobile():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _authed_page(browser, MOBILE_VIEWPORT)
        _install_routes(page)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(250)

        assert page.locator("[data-plan-root]").is_visible()
        overflow = page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )
        assert overflow <= 0
        assert page.locator("[data-plan-shortfall]").is_visible()
        browser.close()


# ---------- OS-089: the collapsed row, and the one-screen acceptance test ----------

OWNER_VIEWPORT = {"width": 420, "height": 912}

# Deliberately contains the three cases the concept's own three rows cannot exercise:
# a bill long enough to truncate, a status badge beside it, evidence on some rows and not
# others, and a goal in a list whose banner reads "Upcoming bills".
ROW_PAYLOAD = {
    "summary": {
        "headline": "Synthetic row probe",
        "commitment_count": 4,
        "total_target": 1448.0,
        "total_funded": 1350.0,
        "unfunded": 98.0,
        "coverage_ratio": 0.93,
        "next_due": "2026-09-11",
        "first_shortfall": None,
    },
    "allocation": {
        "cash_total": 1500.0,
        "segments": [
            {"label": "Bills", "amount": 1300.0},
            {"label": "Goals", "amount": 200.0},
            {"label": "Available", "amount": 0.0},
        ],
    },
    "commitments": [
        {"id": 1, "type": "bill", "name": "Electric", "status": "active",
         "target": 84.0, "funded": 84.0, "unfunded": 0.0, "due_date": "2026-09-11",
         "backing": {"name": "Bill reserve"}, "biller_status": "reserved",
         "invoice_evidence": None},
        {"id": 2, "type": "bill", "name": "Internet", "status": "active",
         "target": 65.0, "funded": 65.0, "unfunded": 0.0, "due_date": "2026-09-14",
         "backing": {"name": "Bill reserve"}, "biller_status": "reserved",
         "invoice_evidence": [
             {"id": "inv-2", "title": "September statement",
              "content_url": "https://example.invalid/statement"}
         ]},
        {"id": 3, "type": "bill", "name": "Verizon Payment Arrangement", "status": "active",
         "target": 99.0, "funded": 1.0, "unfunded": 98.0, "due_date": "2026-09-18",
         "backing": {"name": "Bill reserve"}, "biller_status": "unfunded",
         "invoice_evidence": [
             {"id": "inv-3", "title": "August statement",
              "content_url": "https://example.invalid/august"},
             {"id": "inv-4", "title": "July statement",
              "content_url": "https://example.invalid/july"},
         ]},
        {"id": 4, "type": "goal", "name": "Emergency fund", "status": "active",
         "target": 200.0, "funded": 200.0, "unfunded": 0.0, "target_date": "2027-03-01",
         "backing": {"name": "Pocket"}, "biller_status": None, "invoice_evidence": None},
    ],
    "next_paycheck": {"date": "2026-09-16", "amount": 1660.0},
    "timeline": {"events": [
        {"key": "e1", "date": "2026-09-11", "amount": 84.0, "commitment_id": 1,
         "commitment": "Electric"},
        {"key": "e2", "date": "2026-09-14", "amount": 65.0, "commitment_id": 2,
         "commitment": "Internet"},
        {"key": "e3", "date": "2026-09-18", "amount": 99.0, "commitment_id": 3,
         "commitment": "Verizon Payment Arrangement"},
    ]},
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-08-27T12:00:00Z"},
}


def _owner_screen_page(browser):
    """The owner's device: 420x912, the viewport the acceptance test names."""
    from tests.browser.conftest import ensure_owner

    ensure_owner()
    context = browser.new_context(viewport=OWNER_VIEWPORT, device_scale_factor=3)
    response = context.request.post(
        f"{APP_URL}/api/auth/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": "owner", "password": OWNER_PASSWORD}),
    )
    assert response.status == 200
    return context, context.new_page()


def test_the_bill_row_is_one_band_that_states_its_date_once():
    """OS-089. The collapsed row is one line: medallion, name with its ONE date, figure with
    `Reserved` beneath it, the evidence indicator where evidence exists, and the chevron.
    Everything else is behind the disclosure."""
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _owner_screen_page(browser)
        _install_routes(page, ROW_PAYLOAD)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(400)

        rows = page.locator("[data-commitment-card]")
        assert rows.count() == 4

        for index in range(4):
            row = rows.nth(index)
            # The recorded collapsed height was 113px; the row must be measurably shorter.
            assert row.evaluate("el => el.getBoundingClientRect().height") < 113

            # ONE date, on the row. `due ...` is gone from the fact line, and the desktop NEXT
            # cell is not rendered into the mobile grid.
            assert row.locator("[data-commitment-date]").count() == 1
            assert "due " not in row.inner_text()
            assert row.locator(".m-plan-cell-next").evaluate(
                "el => getComputedStyle(el).display"
            ) == "none"

            # The label reads BELOW the figure now, and nothing re-adds it above.
            funded = row.locator(".m-plan-cell-funded")
            assert funded.evaluate("el => getComputedStyle(el, '::after').content") == '"Reserved"'
            assert funded.evaluate("el => getComputedStyle(el, '::before').content") == "none"

            # The panel is closed, and the full name is already inside it.
            assert row.locator(".m-plan-cell-panel").evaluate(
                "el => getComputedStyle(el).display"
            ) == "none"
            assert row.locator("[data-commitment-date]").inner_text().strip() != ""

            # The funding bar is on the COLLAPSED row, exactly one of it, and it is NOT inside
            # the disclosure. The owner corrected the spec on this point ("I would still want
            # progress bars") and the concept draws it along the bottom of every bill row.
            assert row.locator(".m-commitment-progress").count() == 1
            assert row.locator(".m-commitment-progress").first.is_visible()
            assert row.locator(".m-plan-cell-panel .m-commitment-progress").count() == 0
            assert row.locator(".m-commitment-progress").first.get_attribute("role") == (
                "progressbar"
            )
            assert row.locator(".m-commitment-progress").first.get_attribute(
                "aria-valuenow"
            ) is not None

        # The `BILL` tag is gone; a goal still says GOAL, so the "Upcoming bills" banner never
        # silently files a goal under bills.
        names = page.locator(".m-commitment-name")
        types = page.locator(".m-commitment-type")
        assert types.count() == 1
        assert types.nth(0).inner_text().strip().lower() == "goal"
        assert names.nth(3).inner_text().strip() == "Emergency fund"
        browser.close()


def test_the_badge_stays_beside_a_long_name_and_the_name_truncates_instead():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _owner_screen_page(browser)
        _install_routes(page, ROW_PAYLOAD)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(400)

        long_row = page.locator('[data-commitment-card="3"]')
        name = long_row.locator(".m-commitment-name")
        badge = long_row.locator(".m-bill-badge")

        assert badge.count() == 1
        assert badge.inner_text().strip() == "Underfunded"
        # The NAME is what truncates here; the badge never shares that line, so it cannot be
        # pushed out of position by a long name. Measured at 420px the name column is ~144px,
        # and a badge sharing it left about 50px -- enough to collapse two different bills into
        # the same visible string.
        assert name.evaluate("el => el.scrollWidth > el.clientWidth + 1"), (
            "the long name should ellipsise rather than overflow"
        )
        name_box = name.bounding_box()
        badge_box = badge.bounding_box()
        assert badge_box["y"] >= name_box["y"] + name_box["height"] - 1, (
            "the badge must sit on the detail line, below the truncating name"
        )
        # The badge itself is never truncated...
        assert badge.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        # ...and it is not clipped by the row.
        row_box = long_row.bounding_box()
        assert badge_box["x"] + badge_box["width"] <= row_box["x"] + row_box["width"]
        assert name_box["x"] + name_box["width"] <= row_box["x"] + row_box["width"]

        # Truncation never loses the name: it is in the panel heading and in the accessible name.
        assert long_row.locator(".m-plan-panel-name").inner_text().strip() == (
            "Verizon Payment Arrangement"
        )
        assert "Verizon Payment Arrangement" in long_row.get_attribute("aria-label")
        browser.close()


def test_the_evidence_indicator_exists_only_where_evidence_does_and_opens_the_panel():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _owner_screen_page(browser)
        _install_routes(page, ROW_PAYLOAD)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(400)

        # Rows 2 and 3 carry invoices; rows 1 and 4 do not, so their indicator is ABSENT rather
        # than present-and-disabled -- a disabled icon would imply evidence that is not there.
        assert page.locator('[data-commitment-card="1"] .m-evidence-indicator').count() == 0
        assert page.locator('[data-commitment-card="4"] .m-evidence-indicator').count() == 0
        assert page.locator('[data-commitment-card="2"] .m-evidence-indicator').count() == 1
        indicator = page.locator('[data-commitment-card="3"] .m-evidence-indicator')
        assert indicator.count() == 1
        # The collapsed row says nothing about evidence in text, so this icon is the only
        # signal that content exists: it must carry a real accessible name.
        assert indicator.get_attribute("aria-label") == "Evidence available"
        assert indicator.get_attribute("data-evidence-count") == "2"

        row = page.locator('[data-commitment-card="3"]')
        assert row.locator(".m-plan-cell-panel").evaluate(
            "el => getComputedStyle(el).display"
        ) == "none"
        indicator.click()
        page.wait_for_timeout(200)
        assert row.locator(".m-plan-cell-panel").evaluate(
            "el => getComputedStyle(el).display"
        ) != "none"
        # The invoices themselves remain the things that open an invoice.
        assert row.locator(".m-invoice-link").count() == 2
        assert row.locator(".m-commitment-progress").count() == 1
        assert row.locator(".m-commitment-facts").inner_text().strip() != ""
        assert indicator.get_attribute("aria-expanded") == "true"
        browser.close()


def test_the_next_income_and_the_add_control_are_on_the_first_screen_at_420x912():
    """The acceptance test this slice exists for, measured rather than asserted by eye.

    The shell is one viewport tall and `.m-main` owns the scrolling, so "one screen" is the
    canvas rectangle -- top bar height to dock top -- and not `window.innerHeight`. The income
    strip must be entirely inside it, and the add control must be inside it too, without any
    scrolling of that canvas.
    """
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _owner_screen_page(browser)
        _install_routes(page, ROW_PAYLOAD)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(400)

        canvas = page.evaluate(
            """() => {
              const main = document.querySelector('.m-main');
              const r = main.getBoundingClientRect();
              return {top: r.top, bottom: r.bottom, scrollTop: main.scrollTop};
            }"""
        )
        assert canvas["scrollTop"] == 0, "the canvas must be measured unscrolled"
        assert canvas["bottom"] > canvas["top"]

        income = page.locator(".m-plan-funding-card").bounding_box()
        assert income["y"] >= canvas["top"]
        assert income["y"] + income["height"] <= canvas["bottom"] + 1, (
            "the next income strip must be fully on the first screen"
        )

        add = page.locator("[data-plan-new-commitment]").bounding_box()
        assert add["y"] <= canvas["bottom"], (
            "the add control must be reachable on the first screen without scrolling"
        )
        # And the primary really spans the page width on mobile.
        assert add["width"] > 0.9 * 388
        browser.close()


def test_the_desktop_column_headers_keep_their_left_to_right_order():
    """Regression guard for a defect only the capture caught.

    The disclosure's grid placement was written as a bare `grid-area: name` on
    `m-plan-cell-commitment` -- the class the HEAD's first cell also carries. On the head's grid
    there is no `name` template, so the custom ident created an implicit named line at the END of
    the grid and the "Commitment" header was rendered in the LAST column, reading
    "RESERVED | NEXT | COMMITMENT" above a row that had not moved. The source read correctly, so
    this asserts the rendered order instead.
    """
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _authed_page(browser, DESKTOP_VIEWPORT)
        _install_routes(page, ROW_PAYLOAD)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(400)

        headers = page.locator(".m-plan-table-head [role='columnheader']")
        assert headers.count() == 3
        boxes = [headers.nth(i).bounding_box() for i in range(3)]
        assert boxes[0]["x"] < boxes[1]["x"] < boxes[2]["x"], (
            "the desktop headers must read Commitment, Reserved, Next from left to right"
        )
        # ...and they must line up with the columns the rows actually use.
        row = page.locator('[data-commitment-card="1"]')
        # The head is rendered uppercase by the shared section-label treatment.
        assert page.locator(".m-plan-table-head .m-plan-cell-commitment").inner_text().strip().lower() == (
            "commitment"
        )
        assert row.locator(".m-commitment-name").inner_text().strip() == "Electric"
        # The medallion and the evidence indicator belong to the mobile row and must not appear
        # in the four-column desktop grid at all.
        assert row.locator(".m-plan-cell-medallion").evaluate(
            "el => getComputedStyle(el).display"
        ) == "none"
        # The panel's facts are still visible on desktop, where there is no disclosure.
        assert row.locator(".m-commitment-facts").is_visible()
        assert row.locator(".m-plan-cell-next").evaluate(
            "el => getComputedStyle(el).display"
        ) != "none"
        browser.close()


def test_three_bills_are_fully_visible_and_no_map_figure_wraps():
    """Owner, third pass: "Can we get everything a little closer together to allow three bills
    to show?"

    Three rows must fit the band WHOLE -- a third row cut off at the knee is not three bills --
    and the add control must still be on the screen, because the band and the control are the
    two things this slice trades against each other. The map assertion is the regression guard
    for a fix that read as correct in the numbers: narrowing the map's box shrank the type's
    container but not the type, so `$200.00` wrapped onto a second line. A range rect count is
    the honest measure of wrapping -- a block's own height can stay one line's worth while the
    text inside breaks.
    """
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as pw:
        browser = pw.chromium.launch()
        context, page = _authed_page(browser, OWNER_VIEWPORT)
        _install_routes(page, ROW_PAYLOAD)
        page.goto(f"{APP_URL}/meridian?workspace=plan", wait_until="domcontentloaded")
        page.wait_for_timeout(500)

        band = page.locator(".m-plan-table").first
        band_box = band.bounding_box()
        rows = page.locator("[data-commitment-card]")
        assert rows.count() >= 3, "the fixture must carry at least three bills"

        for i in range(3):
            box = rows.nth(i).bounding_box()
            assert box["y"] >= band_box["y"] - 1
            assert box["y"] + box["height"] <= band_box["y"] + band_box["height"] + 1, (
                f"bill {i + 1} is cut off by the band: its bottom "
                f"{box['y'] + box['height']:.0f} exceeds {band_box['y'] + band_box['height']:.0f}"
            )

        # The money on the map must each render on ONE line.
        wrapped = page.evaluate(
            """() => {
              const out = [];
              for (const el of document.querySelectorAll('.m-plan-medallion-amount, .m-plan-medallion-label')) {
                const r = document.createRange();
                r.selectNodeContents(el);
                const lines = r.getClientRects().length;
                if (lines > 1) out.push([el.textContent, lines]);
              }
              return out;
            }"""
        )
        assert wrapped == [], f"map figures wrapped onto extra lines: {wrapped}"

        # ...and the add control is still inside the canvas the shell scrolls.
        canvas = page.evaluate(
            "() => { const m = document.querySelector('.m-main'); const r = m.getBoundingClientRect();"
            " return {top: r.top, bottom: r.bottom}; }"
        )
        add = page.locator("[data-plan-new-commitment]").first.bounding_box()
        assert add["y"] + add["height"] <= canvas["bottom"] + 1, (
            "the add control must stay on the first screen: its bottom "
            f"{add['y'] + add['height']:.0f} exceeds the canvas bottom {canvas['bottom']:.0f}"
        )
        browser.close()
