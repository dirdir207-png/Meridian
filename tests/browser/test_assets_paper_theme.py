"""A paper plate's interior is ink on paper in BOTH themes.

Owner, 2026-09-25: "on dar[k] theme assets and contracts is using the light theme dark blue fill and the
text below is unreadable". The plate is the kit's parchment ticket, so the page's theme is a lie inside
it: the interior must read as ink on paper whatever the page behind is doing -- the same rule
`observatory.css` already applies in mirror image to dark BOXES.

MEASURED BEFORE THE FIX, in dark theme: `.memory-item` kept `--m-surface: #141b32` (navy cards on
parchment), the review text under them inherited `--m-ink: #eee4cf`, and because `.memory-item` paints
itself with `color-mix(in srgb, var(--m-surface) 82%, var(--m-canvas))` while `--m-canvas` stayed the
page's navy, the cards came out grey-blue rgb(204,198,192) instead of the light theme's rgb(244,236,223).

This asserts the PROPERTY (paper inks, and text that clears the contrast floor on them) rather than the
declarations, and it asserts it twice, because the defect was theme-specific: a guard that only checked
one theme would have passed while the owner was looking at the other one. Read-only: it navigates and
measures, and submits nothing.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("APP_URL"), reason="APP_URL required")

PLAYWRIGHT = pytest.importorskip("playwright.sync_api")

PAPER_INK = (32, 38, 59)          # #20263b
PAPER_SURFACE = (244, 236, 223)   # #f4ecdf
#: The very paper the ticket frame is cut from, sampled from the art's centre (#f5d8b3). Each row is
#: printed on this now that a row IS a ticket.
PAPER_PLATE_RGB = (245, 216, 179)

PROBE = r"""
() => {
  const section = document.querySelector(".memory-management");
  if (!section) return null;
  const cs = getComputedStyle(section);
  const parseRgb = (value) => {
    const match = value.match(/-?\d+(?:\.\d+)?/g);
    if (!match) return null;
    const [r, g, b] = match.slice(0, 3).map(Number);
    return match.length > 3 && Number(match[3]) === 0 ? null : [r, g, b];
  };
  const card = section.querySelector(".memory-item");
  const cardCs = card ? getComputedStyle(card) : null;
  const copy = section.querySelector(".m-section-copy");
  // Owner, 2026-09-25: "separate the tickets per items". Each ROW is now the paper, so the property is
  // no longer "nothing inside a ticket is filled" -- it is "the only fills on a ticket are the ticket's
  // own paper and the kit's apricot plates". A row filled with the PAGE's surface would be the white box
  // he rejected; a row filled with the ticket's paper is the fix.
  const filled = [...section.querySelectorAll(".memory-item, .memory-item *, .pending-memory-proposal, .pending-memory-proposal *")]
    .filter((el) => {
      const bg = getComputedStyle(el).backgroundColor;
      return bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent";
    })
    .map((el) => ({
      tag: el.tagName.toLowerCase(),
      cls: (typeof el.className === "string" ? el.className : "").trim().slice(0, 40),
      background: getComputedStyle(el).backgroundColor,
      isPlate: getComputedStyle(el).borderImageSource.indexOf("apricot-button.png") !== -1,
      isRow: el.classList.contains("memory-item") || el.classList.contains("pending-memory-proposal"),
    }));
  return {
    theme: document.documentElement.dataset.theme,
    // The ink scope lives on each TICKET now, not on the section: the section is a stack on the page,
    // and the paper is the row. Reading the tokens from the section would read the page's inks.
    tokens: {
      ink: cardCs.getPropertyValue("--m-ink").trim(),
      surface: cardCs.getPropertyValue("--m-surface").trim(),
      canvas: cardCs.getPropertyValue("--m-canvas").trim(),
      border: cardCs.getPropertyValue("--m-border").trim(),
    },
    sectionColor: cs.color,
    sectionBackgroundImage: cs.backgroundImage.slice(0, 40),
    copyColor: copy ? getComputedStyle(copy).color : null,
    cardColor: cardCs ? cardCs.color : null,
    cardBackground: cardCs ? cardCs.backgroundColor : null,
    cardCount: section.querySelectorAll(".memory-item").length,
    filledOnPaper: filled,
  };
}
"""


def _login(page, url):
    page.goto(f"{url}/login")
    page.fill('input[name="username"]', "owner")
    page.fill('input[name="password"]', "meridian-owner-2026")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{url}/meridian*")


def _channels(value):
    """RGB channels from either `rgb()/rgba()` (0-255) or `color(srgb ...)` (0-1).

    Chromium reports a `color-mix()` result as `color(srgb 0.956863 0.92549 0.87451)`, i.e. components
    in 0-1. Reading those as 0-255 made a cream card measure as if it were black and produced a bogus
    1.39:1 contrast failure -- caught by this guard failing on a correct page, which is why the parsing
    is explicit here rather than assumed.
    """
    text = (value or "").strip()
    numbers = [float(part) for part in __import__("re").findall(r"\d*\.?\d+", text)]
    if len(numbers) < 3:
        return None
    alpha = numbers[3] if len(numbers) >= 4 else None
    if alpha == 0:
        return None
    channels = numbers[:3]
    if text.startswith("color(") and max(channels) <= 1.0:
        channels = [part * 255 for part in channels]
    return channels


def _luminance(rgb):
    def channel(value):
        value = value / 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(part) for part in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(foreground, background):
    light, dark = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_the_assets_plate_is_ink_on_paper_in_both_themes(browser, theme):
    url = os.environ["APP_URL"]
    context = browser.new_context(viewport={"width": 420, "height": 912}, device_scale_factor=3)
    context.add_init_script(f"try{{localStorage.setItem('meridian-theme','{theme}')}}catch(e){{}}")
    page = context.new_page()
    _login(page, url)
    page.goto(f"{url}/meridian?workspace=accounts")
    page.wait_for_selector(".memory-management")
    page.wait_for_timeout(400)
    measured = page.evaluate(PROBE)
    context.close()

    assert measured is not None, "the Assets & Contracts plate is missing"
    assert measured["theme"] == theme, f"the page did not take the {theme} theme"
    inks = measured["tokens"]
    assert inks["ink"] == f"#{PAPER_INK[0]:02x}{PAPER_INK[1]:02x}{PAPER_INK[2]:02x}", (
        f"in {theme} theme the plate's ink token is {inks['ink']}, so text inside the parchment takes "
        "the page's ink instead of paper's"
    )
    for token in ("surface", "canvas"):
        assert inks[token] == f"#{PAPER_SURFACE[0]:02x}{PAPER_SURFACE[1]:02x}{PAPER_SURFACE[2]:02x}", (
            f"in {theme} theme the plate's --m-{token} is {inks[token]}; `.memory-item` mixes "
            "`--m-surface` with `--m-canvas`, so a page-coloured canvas greys the cards on parchment"
        )

    # The ticket's own text on the ticket's own paper -- the readability property, measured where the
    # words actually are. (The section's heading and copy sit on the PAGE now: they are no longer printed
    # on parchment, so comparing them with paper would be measuring the wrong surface.)
    ticket_ink = _channels(measured["cardColor"])
    assert ticket_ink is not None, "the ticket's text colour could not be read"
    ticket_ratio = _contrast(ticket_ink, PAPER_PLATE_RGB)
    assert ticket_ratio >= 4.5, (
        f"in {theme} theme text on a ticket measures {ticket_ratio:.2f}:1 against the ticket paper "
        f"({measured['cardColor']} on rgb{PAPER_PLATE_RGB}); this is the unreadable text the owner reported"
    )

    card_color = _channels(measured["cardColor"])
    card_background = _channels(measured["cardBackground"])
    if card_color and card_background:
        card_ratio = _contrast(card_color, card_background)
        assert card_ratio >= 4.5, (
            f"in {theme} theme an asset card measures {card_ratio:.2f}:1 "
            f"({measured['cardColor']} on {measured['cardBackground']})"
        )

    # The fills ON a ticket. Owner, 2026-09-25, in the order he reported it: "they have white boxes in the
    # parchment tickets", then, on the approach that only re-tinted them, "no where else is this the
    # design", then "Can we also separate the tickets per items". So each row IS paper now, and the rule
    # is: the paper fill on a row must be the PAPER colour, never the page's surface, and anything else
    # filled on a ticket must be the kit's apricot button plate.
    fills = measured["filledOnPaper"]
    row_fills = [entry for entry in fills if entry["isRow"]]
    assert row_fills, "no asset row painted a paper surface, so the tickets are not rendering"
    for entry in row_fills:
        channels = _channels(entry["background"])
        assert channels == list(PAPER_PLATE_RGB), (
            f"in {theme} theme a row's paper is {entry['background']}, not the ticket paper "
            f"rgb{PAPER_PLATE_RGB}; a row painted with the page's surface is the white box on paper"
        )
    for entry in fills:
        if entry["isRow"] or entry["isPlate"]:
            continue
        raise AssertionError(
            f"in {theme} theme {entry['tag']}.{entry['cls']} paints {entry['background']} inside a "
            "ticket; on parchment the only fills are the paper and the kit's apricot plates"
        )


PROPOSAL_LABELS = r"""
() => {
  const rows = [...document.querySelectorAll("[data-testid=pending-memory-proposal]")];
  return rows.map((row) => ({
    label: (row.querySelector("span") || {}).textContent || "",
    type: row.dataset.actionType || null,
    id: row.dataset.actionId || null,
    hasExecute: !!row.querySelector("[data-testid=execute-proposal]"),
  }));
}
"""


def test_the_pending_proposal_labels_are_sentences_not_action_ids(browser):
    """The owner reads this line before deciding, so it must not be `delete_asset: Meridian delete_asset`.

    Two producers wrote that string (the app's summary generator and the UI's prefix) and both are
    fixed -- but rows proposed BEFORE the fix are still in the store, so this asserts the rendered label
    on the real pending list, which is the only place that covers stored rows as well as new ones.
    Read-only: it opens the Accounts workspace and reads labels; it approves nothing.

    The raw type and id must remain reachable on the row, so the fix removes noise without destroying
    provenance.
    """
    url = os.environ["APP_URL"]
    context = browser.new_context(viewport={"width": 420, "height": 912}, device_scale_factor=3)
    page = context.new_page()
    _login(page, url)
    page.goto(f"{url}/meridian?workspace=accounts")
    page.wait_for_selector(".memory-management")
    page.wait_for_timeout(600)
    rows = page.evaluate(PROPOSAL_LABELS)
    context.close()

    assert rows, "no pending proposals were rendered, so this guard proved nothing"
    for row in rows:
        label = row["label"].strip()
        assert label, f"a proposal rendered with no label: {row}"
        assert "_" not in label, f"label shows an internal action type: {label!r}"
        assert "Meridian " not in label, f"label still carries the old machine prefix: {label!r}"
        assert ":" not in label.rstrip("."), f"label still reads as `type: id`: {label!r}"
        assert len(label) > 8, f"label is too short to be a sentence: {label!r}"
        # Provenance survives on the row itself.
        assert row["type"], f"the row lost its action type: {row}"
        assert row["id"], f"the row lost its action id: {row}"
