"""Settings hub structure — the 09-18 concept's grouped directory.

Governing authority: `design/observatory-extension-2026-09-18/concepts/settings.png`.
The concept shows three parchment group banners, each row an icon medallion, a title, a
subtitle and a chevron. This module is the single place that structure is declared, so the
route, the template and the tests cannot drift apart.

COUNTS ARE NOT RESTATED IN PROSE, HERE OR ANYWHERE ELSE. A restated number is a second copy
that nothing reconciles, and this docstring carried one for two sessions: it said "nine rows"
long after the concept had been recounted at eight, and a ledger note repeated the same wrong
nine. The row count IS `len(SETTINGS_HUB)`. The concept's own rows are enumerated in
tests/meridian/test_settings_hub.py, which also declares the rows added BEYOND the concept with
the authority for each, so a reader can always tell fidelity from addition. Anything needing a
count should read the declaration rather than a sentence about it.

WHY THIS IS STATIC AND NOT READ FROM THE DATABASE. Every `href` here points at a route
that ALREADY EXISTS; this slice adds none. The hub therefore holds structure only, and
each detail surface keeps reading its own state (a section whose credential is absent
still renders, and still says so). Building the hub on a repository read would make the
whole Settings page fail whenever that read failed — a regression for a page whose job is
to be reachable so the owner can fix things. Availability is stated per row by
`unavailable`, and the bar for clearing it is a real read model, not a shell.

A ROW WITH NO READ MODEL IS NOT A LINK. `unavailable=True` means the concept names a
capability that has no route, no partial and no read model today. Those rows render as
non-interactive rows stating "Planned". The build handoff is explicit: unavailable
features must "say unavailable/planned, not show working switches". A row that opened an
empty page would claim a surface that does not exist, which is the failure this flag
exists to prevent. Clearing a flag is a later slice that ships the read model with it.
"""

# The tint classes map to the concept's own medallion colours and reuse the tokens the
# rest of the Observatory already uses (lilac / mint / apricot / brass-ish slate).
SETTINGS_HUB = (
    {
        "key": "connections",
        "label": "CONNECTIONS",
        "rows": (
            {
                "key": "money-sources",
                "icon": "piggy-bank",
                "tint": "lilac",
                "label": "Money sources",
                "detail": "Accounts, freshness and access",
                "href": "/meridian/settings?section=connections",
                "section": "connections",
            },
            {
                "key": "email-calendars",
                "icon": "envelope",
                "tint": "mint",
                "label": "Email & calendars",
                "detail": "Separate accounts and permissions",
                "href": "/meridian/settings?section=connections",
                "section": "connections",
            },
            {
                # NOT IN THE CONCEPT. Added on the owner's authority, 2026-09-21: "If we are
                # missing payday and funding, its added in the same visual style."
                #
                # The concept's eight rows do not represent this section, and until this row
                # existed NOTHING IN THE PRODUCT LINKED TO IT: the partial, the route, the JS
                # module and a live endpoint (/api/meridian/trials/deadlines) all shipped, and
                # it rendered only for someone who already knew to type ?section=trials.
                # tests/test_surface_reachability.py is what found that, and it fails on the
                # orphan without this row.
                #
                # It sits in CONNECTIONS because trials and renewals are what Meridian FINDS in
                # the sources this group already lists; the concept offers no group for an
                # obligation, so the nearest honest one is where its evidence comes from.
                "key": "trials-renewals",
                "icon": "arrow-repeat",
                "tint": "mint",
                "label": "Trials & renewals",
                "detail": "Kept visible before they convert",
                "href": "/meridian/settings?section=trials",
                "section": "trials",
            },
        ),
    },
    {
        "key": "authority",
        "label": "VIRGIL & AUTHORITY",
        "rows": (
            {
                "key": "approval-boundaries",
                "icon": "shield-check",
                "tint": "apricot",
                "label": "Approval boundaries",
                "detail": "Review what Virgil may do",
                "href": "/meridian/settings?section=actions",
                "section": "actions",
            },
            {
                # No route, no partial, no read model. Stated, not stubbed.
                "key": "memory-privacy",
                "icon": "eye",
                "tint": "lilac",
                "label": "Memory & privacy",
                "detail": "Sources, retention and corrections",
                "href": None,
                "section": None,
                "unavailable": True,
            },
            {
                "key": "briefings-quiet-hours",
                "icon": "bell",
                "tint": "mint",
                "label": "Briefings & quiet hours",
                "detail": "When Meridian may speak",
                "href": None,
                "section": None,
                "unavailable": True,
            },
        ),
    },
    {
        "key": "preferences",
        "label": "PREFERENCES",
        "rows": (
            {
                # The app's theme control exists, but the concept's Appearance SURFACE
                # (per-theme preview, contrast statement) does not. Linking the row at the
                # toggle would point at a different thing than the row names.
                "key": "appearance",
                "icon": "palette",
                "tint": "apricot",
                "label": "Appearance",
                "detail": "Observatory · Dark",
                "href": None,
                "section": None,
                "unavailable": True,
            },
            {
                # BUILD_HANDOFF: "Funding schedules link to the existing Plan journey."
                # This row therefore points AT Plan and does not carry a funding surface of
                # its own -- that is the "instead of duplicating it" half of the rule. The
                # concept's own subtitle is "Manage in Plan". The existing payday settings
                # section still exists and stays reachable through the in-page link in
                # connections.html; it is simply not a hub row, because the concept draws the
                # funding row as a pointer to Plan.
                "key": "funding-schedules",
                "icon": "calendar-check",
                "tint": "lilac",
                "label": "Funding schedules",
                "detail": "Manage in Plan",
                "href": "/meridian?workspace=plan",
                "section": None,
                "external": True,
            },
            {
                "key": "security-devices",
                "icon": "key",
                "tint": "mint",
                "label": "Security & devices",
                "detail": "Sessions, devices and data",
                "href": "/meridian/settings?section=security",
                "section": "security",
            },
            {
                # NOT IN THE CONCEPT. Added on the owner's authority, 2026-09-21, the same
                # direction that added Trials & renewals above.
                #
                # The comment on Funding schedules records that payday was left out on purpose,
                # because the concept draws funding as a pointer to Plan. That reasoning held
                # for the CONCEPT and failed for the PRODUCT: it left a shipped surface
                # reachable only through a link buried inside Connections
                # (templates/meridian/partials/connections.html:16). A row here does not
                # duplicate the Plan journey -- Funding schedules still points there -- it
                # names the payday surface that already exists and had no way in.
                #
                # RENAMED 2026-09-24 (OS-104), on the owner's report that "payday and funding is
                # unnecessarily complex and suggests overlap ... Funding the way the app
                # describes separate from payday is per bill and doesn't need a separate setting
                # or section". The row said "Payday & funding" while the pane it opens carried a
                # second, two-mode copy of Plan's per-bill funding editor. That copy is gone --
                # funding a particular bill is the bill's own business and Plan owns that editor
                # with all four modes -- so this row now names the one thing the pane actually
                # is: the paycheck Crew holds and the cadence Meridian reads from it. Funding
                # keeps its own pointer row above, so nothing became unreachable.
                "key": "payday-funding",
                "icon": "cash-stack",
                "tint": "apricot",
                "label": "Payday",
                "detail": "The paycheck Crew pays you from",
                "href": "/meridian/settings?section=payday",
                "section": "payday",
            },
        ),
    },
)


def settings_hub_rows():
    """Every row across every group, in display order."""
    return [row for group in SETTINGS_HUB for row in group["rows"]]


#: The five governed Settings section routes. A hub row that points INSIDE Settings must
#: name one of these, so a typo cannot ship a dead link. A row may instead point at another
#: existing journey (Plan, for Funding schedules), and such a row declares ``external`` and
#: carries no section.
SETTINGS_SECTIONS = frozenset({"connections", "payday", "actions", "security", "trials"})

#: Routes outside Settings that a hub row may legitimately point at.
HUB_EXTERNAL_ROUTES = frozenset({"/meridian?workspace=plan"})
