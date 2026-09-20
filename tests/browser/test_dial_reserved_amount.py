"""OS-048b browser check: the reserved amount renders inside the dial.

The service tests pin which basis a figure may be claimed on and the Node tests pin the
copy, but neither can see the dial. This drives the real module and stylesheets with a
deterministic synthetic model (no app, no credentials, no bank data, fixed clock) and
checks the two things only a browser can answer:

* the stated figure and its author reach the row and the evidence ticket, and a payload
  that carries a number without a basis is **not** rendered as a figure at all — that is
  the backwards-compatibility half of D-013, since an unlabelled number can only be read
  as an observation;
* the longer line still fits: at the owner's 420x912 and at desktop 1440x900, in both
  themes, the page never scrolls horizontally and the console stays clean.

Set ``MERIDIAN_CAPTURE_DIR`` to also write the two review screenshots there; the run is
deterministic, so the same command reproduces the same images.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/browser/fixtures/observatory-dial.html"

# Every event is synthetic and deliberately echoes the shapes the service emits: one
# observed per-bill figure, one reported zero beside a Crew-derived schedule, one that
# states nothing, and one legacy payload carrying a bare number with no basis.
MODEL = {
    "timezone": "America/New_York",
    "today": "2026-09-08",
    "horizonEnd": "2026-10-16",
    "availableToSpend": {"minor": 24850, "currency": "USD"},
    "freshness": "fresh",
    "observedAt": "2026-09-08T13:42:00Z",
    "events": [
        {
            "id": "synthetic-rent",
            "date": "2026-09-16",
            "kind": "bill",
            "title": "Rent",
            "amount": {"minor": 150000, "currency": "USD"},
            "fundingStatus": "partial",
            "reserved": {"minor": 120000, "currency": "USD"},
            "fundingBasis": "observed",
            "fundingBasisDivisor": None,
            "fundingAttribution": "crew",
            "fundingObservedAt": "2026-09-08T13:42:00Z",
            "fundingSource": {
                "id": "plan-1",
                "name": "Veterans Home",
                "provider": "crew",
                "cadence": "semimonthly",
                "observedAt": "2026-09-08T13:42:00Z",
                "billReserveId": "res-1",
            },
            "source": "crew",
            "observedAt": None,
            "evidenceIds": [],
            "detailHref": "#rent",
        },
        {
            "id": "synthetic-internet",
            "date": "2026-09-20",
            "kind": "bill",
            "title": "Internet",
            "amount": {"minor": 6500, "currency": "USD"},
            "fundingStatus": "unfunded",
            "reserved": None,
            "fundingBasis": "observed",
            "fundingBasisDivisor": None,
            "fundingAttribution": "crew",
            "fundingObservedAt": "2026-09-08T13:42:00Z",
            "fundingSchedule": {
                "eventDate": "2026-09-19",
                "contribution": {"minor": 2989, "currency": "USD"},
                "deadline": "2026-09-20",
                "nextFundingDate": "2026-09-19",
                "planName": "Veterans Home",
                "basis": "crew_estimate",
                "intervalDays": 14,
            },
            "fundingSource": None,
            "source": "crew",
            "observedAt": None,
            "evidenceIds": [],
            "detailHref": "#internet",
        },
        {
            "id": "synthetic-phone",
            "date": "2026-09-24",
            "kind": "bill",
            "title": "Phone",
            "amount": {"minor": 4200, "currency": "USD"},
            "fundingStatus": "unknown",
            "reserved": None,
            "fundingBasis": "unknown",
            "fundingBasisDivisor": None,
            "fundingAttribution": None,
            "fundingObservedAt": None,
            "fundingSource": None,
            "source": "crew",
            "observedAt": None,
            "evidenceIds": [],
            "detailHref": "#phone",
        },
        {
            # Nothing observed for this bill, so the schedule is the only statement there
            # is -- and the centre must be able to make it without inventing a balance.
            "id": "synthetic-insurance",
            "date": "2026-09-30",
            "kind": "bill",
            "title": "Insurance",
            "amount": {"minor": 4200, "currency": "USD"},
            "fundingStatus": "unknown",
            "reserved": None,
            "fundingBasis": "unknown",
            "fundingBasisDivisor": None,
            "fundingAttribution": None,
            "fundingObservedAt": None,
            "fundingSchedule": {
                "eventDate": "2026-09-19",
                "contribution": {"minor": 1932, "currency": "USD"},
                "deadline": "2026-09-30",
                "nextFundingDate": "2026-09-19",
                "planName": "Veterans Home",
                "basis": "crew_estimate",
                "intervalDays": 14,
            },
            "fundingSource": None,
            "source": "crew",
            "observedAt": None,
            "evidenceIds": [],
            "detailHref": "#insurance",
        },
        {
            "id": "synthetic-legacy",
            "date": "2026-09-28",
            "kind": "bill",
            "title": "Legacy",
            "amount": {"minor": 3000, "currency": "USD"},
            "fundingStatus": "reserved",
            "reserved": {"minor": 3000, "currency": "USD"},
            "source": "crew",
            "observedAt": None,
            "evidenceIds": [],
            "detailHref": "#legacy",
        },
        {
            "id": "synthetic-payday",
            "date": "2026-10-05",
            "kind": "income",
            "title": "Payday",
            "amount": {"minor": 166000, "currency": "USD"},
            "fundingStatus": "unknown",
            "source": "Synthetic schedule",
            "evidenceIds": [],
            "detailHref": "#payday",
        },
    ],
    "projections": [],
}


def _fixture_html() -> str:
    """The committed fixture page with the synthetic model swapped in."""
    html = FIXTURE.read_text(encoding="utf-8")
    start = html.index("window.MeridianObservatoryDialModel=")
    end = html.index(";</script>", start)
    return (
        html[:start]
        + "window.MeridianObservatoryDialModel="
        + json.dumps(MODEL)
        + html[end:]
    )


@pytest.fixture
def dial_page(request):
    from playwright.sync_api import sync_playwright

    # Defaults to the owner's iPhone Air when the test does not parametrize the fixture.
    width, height, theme, dpr = getattr(request, "param", (420, 912, "dark", 3))
    html = _fixture_html()
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": width, "height": height}, device_scale_factor=dpr
        )
        context.add_init_script("window.setInterval = () => 0;")
        page = context.new_page()
        page.clock.install(time=1788874920000)
        page.on("console", lambda message: errors.append(message.text)
                if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(str(error)))

        def fixture_route(route):
            path = urlparse(route.request.url).path
            if path == "/":
                route.fulfill(body=html, content_type="text/html")
                return
            candidate = (ROOT / path.lstrip("/")).resolve()
            if (
                path.startswith("/static/")
                and (ROOT / "static") in candidate.parents
                and candidate.is_file()
            ):
                route.fulfill(path=str(candidate))
            else:
                route.abort()

        page.route("**/*", fixture_route)
        page.goto("http://dial.test/")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        page.wait_for_selector(".obs-dial-svg")
        page.evaluate("document.fonts.ready")
        yield page, errors
        capture_dir = os.environ.get("MERIDIAN_CAPTURE_DIR")
        if capture_dir:
            target = Path(capture_dir)
            target.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(target / f"dial-reserved-{width}x{height}-{theme}.png"))
        context.close()
        browser.close()


def _meta_for(page, title: str) -> str:
    return page.get_by_role("button", name=title, exact=False).locator(
        ".obs-event-meta"
    ).inner_text()


def test_the_stated_reserve_renders_with_its_author_and_an_unlabelled_one_does_not(dial_page):
    page, _errors = dial_page

    rent = _meta_for(page, "Rent")
    assert "set aside" in rent
    assert "Veterans Home" in rent
    assert "$1,500.00" in rent and "$1,200.00" in rent

    # A reported zero is a fact stated in words, and the schedule beside it is Crew's own
    # per-event ESTIMATE toward the deadline -- never money held, and never "set aside".
    # The row uses the SHORT form ("$29.89/event · Crew estimate"); the sentence with the
    # deadline belongs to the ticket, because the OS-048b capture showed a long label
    # wrapping into its own value at this viewport.
    internet = _meta_for(page, "Internet")
    assert "not yet set aside" in internet
    assert "$29.89/event" in internet
    assert "Crew estimate" in internet
    assert "estimated by Crew" not in internet
    assert "Meridian estimate" not in internet

    # "not yet set aside" and "unknown" are different statements, and this model only
    # has the second: nothing was reported for Phone.
    phone = _meta_for(page, "Phone")
    assert phone == "Funding unknown"

    # A payload with no basis is a number without provenance, so no figure statement is
    # rendered for it. The older shape keeps its own pre-slice rendering in the ticket
    # (see the next test): the point here is that it is never promoted into the row's
    # stated reserve line, which is reserved for a figure that says where it came from.
    legacy = _meta_for(page, "Legacy")
    assert "set aside" not in legacy
    # Exactly the pre-slice label for that status: unchanged, and not promoted.
    assert legacy == "Reserved"


def test_the_ticket_names_the_bill_level_author_and_the_funding_schedule(dial_page):
    page, _errors = dial_page

    page.get_by_role("button", name="Rent", exact=False).click()
    ticket = page.locator(".obs-evidence-ticket")
    # The ticket labels are uppercased by CSS, so compare case-insensitively.
    rows = ticket.locator(".obs-ticket-rows").inner_text().lower()
    assert "set aside" in rows
    assert "$1,200.00" in rows
    assert "observed from crew" in rows
    assert "meridian estimate" not in rows

    # The label and its value must not collide. The first version used the full sentence
    # "Set aside for this bill", which wrapped inside the row grid and overlapped its own
    # value at 420px -- visible in the capture, invisible to every other test.
    overlap = page.evaluate(
        """() => {
          const rows = [...document.querySelectorAll('.obs-ticket-row')];
          const row = rows.find((r) =>
            (r.querySelector('dt').textContent || '').toLowerCase().includes('set aside'));
          if (!row) return 'no stated-figure row';
          const dt = row.querySelector('dt').getBoundingClientRect();
          const dd = row.querySelector('dd').getBoundingClientRect();
          const collides = !(dt.right <= dd.left + 1 || dd.right <= dt.left + 1
                             || dt.bottom <= dd.top + 1 || dd.bottom <= dt.top + 1);
          return collides ? 'label and value overlap' : '';
        }"""
    )
    assert overlap == "", overlap

    page.get_by_role("button", name="Internet", exact=False).click()
    schedule_rows = page.locator(".obs-evidence-ticket .obs-ticket-rows").inner_text().lower()
    assert "funding schedule" in schedule_rows
    assert "$29.89/event" in schedule_rows
    assert "crew estimate" in schedule_rows
    assert "due sep 20" in schedule_rows
    assert "meridian estimate" not in schedule_rows

    # The centre states the STRONGEST honest thing it can, so precedence is visible here:
    # an observed figure (even a reported zero) outranks the projection and is what the
    # centre says about Internet. The schedule is still in the row and the ticket above.
    status = page.locator(".obs-dial-center-status").inner_text()
    assert "not yet set aside" in status
    assert "estimated by Crew" not in status

    # With nothing observed there is no figure to outrank it, so the centre falls to the
    # schedule and states it as Crew's estimate against the deadline it is measured to.
    page.get_by_role("button", name="Insurance", exact=False).click()
    insurance_status = page.locator(".obs-dial-center-status").inner_text()
    assert "$19.32/event" in insurance_status
    assert "Crew estimate" in insurance_status
    assert "set aside" not in insurance_status


def test_a_payload_without_a_basis_keeps_its_own_rendering(dial_page):
    """Backwards compatibility, stated rather than assumed.

    A bill event that carries ``reserved`` but no ``fundingBasis`` predates this slice.
    Its number is not promoted into the new stated-figure line (nothing may claim a
    provenance it does not have), but the older ticket row is left exactly as it was, so
    a consumer that still sends the old shape is not silently emptied.
    """
    page, _errors = dial_page

    page.get_by_role("button", name="Legacy", exact=False).click()
    rows = page.locator(".obs-evidence-ticket .obs-ticket-rows").inner_text().lower()
    assert "reserved" in rows
    assert "set aside for this bill" not in rows
    assert "$30.00" in rows


@pytest.mark.parametrize(
    "dial_page",
    [
        # The locked capture contract in docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md:
        # DPR 1 desktop/tablet, DPR 3 mobile, both themes, animation and timers off.
        (1440, 900, "dark", 1), (1440, 900, "light", 1),
        (1024, 768, "dark", 1), (1024, 768, "light", 1),
        (430, 932, "dark", 3), (430, 932, "light", 3),
        (390, 844, "dark", 3), (390, 844, "light", 3),
        (420, 912, "dark", 3), (420, 912, "light", 3),
    ],
    indirect=True,
    ids=[
        "desktop-dark", "desktop-light", "tablet-dark", "tablet-light",
        "mobile-air-dark", "mobile-air-light", "mobile-dark", "mobile-light",
        "iphone-air-dark", "iphone-air-light",
    ],
)
def test_the_longer_reserve_line_stays_inside_the_viewport(dial_page):
    """The new line is the longest text the rail carries; it must not widen the page.

    These are viewport captures of a synthetic self-consistency check, not a
    concept-vs-capture parity matrix: there is no concept drawing of a reserved amount,
    so nothing here is compared against one.
    """
    page, errors = dial_page

    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
        "the reserved-amount line must not introduce horizontal overflow"
    )
    # The figure is present in this run, not silently dropped by a layout rule.
    assert "set aside" in _meta_for(page, "Rent")
    assert "Crew estimate" in _meta_for(page, "Internet")
    rail = page.locator(".obs-dial-events")
    assert rail.bounding_box()["width"] > 0

    # The two long rows in this model (a stated figure joined to a source, and a stated
    # zero joined to a schedule) must stay inside their own row. The 2026-09-19 capture
    # caught a wrapped ticket label colliding with its value, so the boxes are measured
    # here rather than assumed: the meta line may wrap, but it may not run under the
    # amount column or past the row's right edge.
    geometry = page.evaluate(
        """(titles) => {
          const out = [];
          for (const title of titles) {
            const button = [...document.querySelectorAll('.obs-event-item')]
              .find((b) => (b.querySelector('.obs-event-title') || {}).textContent === title);
            if (!button) { out.push({ title, error: 'row not found' }); continue; }
            const meta = button.querySelector('.obs-event-meta');
            const amount = button.querySelector('.obs-event-amount');
            const m = meta.getBoundingClientRect();
            const a = amount.getBoundingClientRect();
            const row = button.getBoundingClientRect();
            out.push({
              title,
              overlapAmount: !(m.right <= a.left + 1 || a.right <= m.left + 1
                              || m.bottom <= a.top + 1 || a.bottom <= m.top + 1),
              pastRowRight: m.right > row.right + 1,
              metaHeight: m.height,
              rowHeight: row.height,
            });
          }
          return out;
        }""",
        ["Rent", "Internet"],
    )
    for entry in geometry:
        assert "error" not in entry, entry
        assert entry["overlapAmount"] is False, entry
        assert entry["pastRowRight"] is False, entry
        assert entry["metaHeight"] < entry["rowHeight"], entry
    assert errors == [], f"console errors: {errors}"
