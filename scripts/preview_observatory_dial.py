"""Isolated Today design preview: production templates/controllers, synthetic reads only.

Run with .venv311/bin/python scripts/preview_observatory_dial.py.
No app import, environment loading, database, authentication, or provider access.
"""
import json
import mimetypes
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
# The hub's structure is declared once in meridian.settings_hub and imported here, so the
# preview renders the SAME structure the application does. Run as a path this script does
# not get the project root on sys.path, so add it explicitly rather than duplicating the
# structure (a duplicated copy is exactly how a preview stops predicting the real page).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TODAY = {
    "safe_to_spend": {"amount": 248.50, "currency": "USD", "through_date": "2026-09-16"},
    "forecast": {"available": True, "as_of": "2026-09-08", "runway_days": 14,
                 "coverage_horizons": {}, "confidence": None},
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-08T13:42:00Z"},
    "inputs": {}, "upcoming_events": [],
    "next_inflow": {"amount": 1660, "currency": "USD", "date": "2026-09-16"},
    "beacon": {"title": "Synthetic planning example", "summary": "Preview data only.",
               "detail": "This isolated preview has no bank connection."},
}

# Plan fixture. Every field here is one that plan.js actually reads — the shape is
# derived from the consumer, never invented, because a fixture that guesses
# produces false gap reports. Values are obviously synthetic and echo the
# governing concept's own figures so a capture can be compared against it.
# Note the three segment labels: plan.js looks up `label === "Available"` by name,
# so these must match the application's allocation vocabulary.
PLAN = {
    "summary": {
        "headline": "Synthetic plan preview",
        "total": 1768.50, "total_target": 1768.50, "total_funded": 1520.00,
        "unfunded": 248.50, "coverage_ratio": 0.86,
        "captured": True, "missing": [], "next_due": "2026-09-11",
        "first_shortfall": None,
    },
    "allocation": {
        "cash_total": 1768.50,
        "segments": [
            {"label": "Bills", "amount": 1320.00},
            {"label": "Goals", "amount": 200.00},
            {"label": "Available", "amount": 248.50},
        ],
    },
    "commitments": [
        {"id": "synthetic-electric", "name": "Electric", "type": "bill",
         "target": 84.00, "funded": 84.00, "unfunded": 0.00,
         "due_date": "2026-09-11", "target_date": None, "backing": {"name": "Bill reserve"},
         "biller_status": "reserved", "crew_bill_id": "synthetic-electric",
         "invoice_evidence": None},
        {"id": "synthetic-internet", "name": "Internet", "type": "bill",
         "target": 65.00, "funded": 65.00, "unfunded": 0.00,
         "due_date": "2026-09-14", "target_date": None, "backing": {"name": "Bill reserve"},
         "biller_status": "reserved", "crew_bill_id": "synthetic-internet",
         "invoice_evidence": None},
        {"id": "synthetic-rent", "name": "Rent", "type": "bill",
         "target": 1171.00, "funded": 1171.00, "unfunded": 0.00,
         "due_date": "2026-09-16", "target_date": None, "backing": {"name": "Bill reserve"},
         "biller_status": "reserved", "crew_bill_id": "synthetic-rent",
         "invoice_evidence": None},
        {"id": "synthetic-goal", "name": "Emergency fund", "type": "goal",
         "target": 200.00, "funded": 200.00, "unfunded": 0.00,
         "due_date": None, "target_date": "2027-03-01", "backing": {"name": "Pocket"},
         "biller_status": None, "crew_bill_id": None, "invoice_evidence": None},
    ],
    "next_paycheck": {"date": "2026-09-16", "amount": 1660.00},
    "timeline": {
        "events": [
            {"key": "synthetic-1", "date": "2026-09-11", "amount": 84.00,
             "commitment_id": "synthetic-electric", "commitment": "Electric"},
            {"key": "synthetic-2", "date": "2026-09-14", "amount": 65.00,
             "commitment_id": "synthetic-internet", "commitment": "Internet"},
            {"key": "synthetic-3", "date": "2026-09-16", "amount": 1171.00,
             "commitment_id": "synthetic-rent", "commitment": "Rent"},
        ]
    },
    "absent_bills": [],
    "document_discrepancies": [],
}

FUNDING_RULES = {"funding_rules": []}

# Activity and accounts fixtures, again derived from what the controller reads.
# activity.js calls /api/meridian/activity (with query params, which the handler
# strips) and /api/meridian/accounts for its filter options.
ACCOUNTS = {
    "groups": [
        {"role": "cash", "label": "Cash", "accounts": [
            {"id": 1, "name": "Checking", "account_type": "checking",
             "balance": 248.50, "available_balance": 248.50, "currency": "USD",
             "is_active": True, "provider": "crew",
             "source_updated_at": "2026-09-08T13:42:00Z",
             "synced_at": "2026-09-08T13:42:00Z"},
        ]},
        {"role": "savings", "label": "Savings", "accounts": [
            {"id": 2, "name": "Emergency fund", "account_type": "pocket",
             "balance": 200.00, "available_balance": 200.00, "currency": "USD",
             "is_active": True, "provider": "crew",
             "source_updated_at": "2026-09-08T13:42:00Z",
             "synced_at": "2026-09-08T13:42:00Z"},
        ]},
    ],
    "archived": [],
    "reimbursements": [],
    "connections": [],
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-08T13:42:00Z"},
}

ACTIVITY_ROWS = [    {"id": "synthetic-tx-1", "amount": -84.00, "currency": "USD",
     "description": "Electric", "merchant": "Electric", "provider": "crew",
     "occurred_at": "2026-09-11T12:00:00Z", "classification": {"category": "Utilities", "confidence": 0.86},
     "suggested_category": "Utilities", "category_options": ["Utilities", "Home"]},
    {"id": "synthetic-tx-2", "amount": -65.00, "currency": "USD",
     "description": "Internet", "merchant": "Internet", "provider": "crew",
     "occurred_at": "2026-09-14T12:00:00Z", "classification": {"category": "Utilities", "confidence": 0.86},
     "suggested_category": "Utilities", "category_options": ["Utilities", "Home"]},
    {"id": "synthetic-tx-3", "amount": 1660.00, "currency": "USD",
     "description": "Paycheck", "merchant": "Paycheck", "provider": "crew",
     "occurred_at": "2026-09-16T12:00:00Z", "classification": {"category": "Income", "confidence": 0.95},
     "suggested_category": "Income", "category_options": ["Income"]},
    # Below the 0.7 review threshold, so the fixture exercises a real review queue and
    # the badge/strip have a figure the rows actually support.
    {"id": "synthetic-tx-4", "amount": -12.40, "currency": "USD",
     "description": "Unassigned purchase", "merchant": "Unassigned purchase",
     "provider": "crew", "occurred_at": "2026-09-16T09:30:00Z",
     "classification": {"category": "uncategorized", "confidence": 0.2},
     "suggested_category": None, "category_options": ["Groceries", "Dining"]},
    # Dated to the CAPTURE CLOCK's day, deliberately. The ledger's dividers and their
    # moon/sun markers are decided against the browser's clock, and governed captures
    # are taken with --frozen-clock 2026-09-18T19:50:00-04:00. Anchoring this row there
    # is what makes a capture show the concept's "Today" divider with its crescent
    # rather than a fourth sunburst. Opened without a frozen clock the same ledger just
    # reads as an older day, which is the honest result. Confidence sits above the
    # review threshold, so the review_count above is unmoved.
    {"id": "synthetic-tx-5", "amount": -23.75, "currency": "USD",
     "description": "Corner Market", "merchant": "Corner Market", "provider": "crew",
     "occurred_at": "2026-09-18T16:00:00Z", "classification": {"category": "Groceries", "confidence": 0.92},
     "suggested_category": "Groceries", "category_options": ["Groceries", "Dining"]},
]

ACTIVITY = {
    "transactions": ACTIVITY_ROWS,
    "patterns": [],
    "next_cursor": None,
    # Derived from the rows above with the server's own rule, so the fixture can never
    # advertise a count its list does not contain.
    "review_count": sum(
        1
        for row in ACTIVITY_ROWS
        if (row.get("classification") or {}).get("confidence") is not None
        and row["classification"]["confidence"] < 0.7
    ),
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-08T13:42:00Z"},
}


# Connections-only Settings fixture. No credentials, account data or write handler.
#
# The two route rows mirror what `meridian/services/ingestion_routes.py` serves for real, so
# the synthetic preview can show the rows this slice added. They are SYNTHETIC in the sense
# that matters: the fixture is written here, not observed from any account. In particular the
# Composio row shows the NOT-observed-yet state, because that is the honest state of a
# capability whose daily trigger is not wired -- a fixture that showed "Live" would let a
# capture claim a working schedule that does not exist.
SETTINGS_CONNECTIONS = {"groups": [
    {"kind": "money", "label": "Money", "connections": [{
        "public_id": "synthetic-crew", "display_name": "Example Crew connection",
        "uses": ["Balances", "Transactions", "Bills"], "state": "connected",
        "freshness": "2026-09-18T18:00:00Z",
    }]},
    {"kind": "evidence", "label": "Evidence", "connections": [{
        "public_id": "route-icloud-imap", "kind": "icloud",
        "display_name": "iCloud Mail (IMAP)",
        "uses": ["Bills", "Statements", "Receipts"], "state": "connected",
        "state_label": "Configured", "freshness": "2026-09-06T00:00:00Z",
        "freshness_label": "Mail lane last observed", "read_only": True, "route": True,
        "status_note": (
            "An iCloud mailbox is configured. Master mail reads are shared across the mail lane."
        ),
        "meaning": (
            "iCloud Mail is read over IMAP. This row reports whether a read has actually "
            "succeeded, not merely that the mailbox is configured."
        ),
    }]},
    {"kind": "time", "label": "Time", "connections": [{
        "public_id": "route-composio-calendar", "kind": "composio",
        "display_name": "Calendar via Composio",
        "uses": ["Calendar events", "Travel", "Appointments"], "state": "available",
        "state_label": "Not observed yet", "freshness": None,
        "freshness_label": "Last calendar read", "read_only": True, "route": True,
        "status_note": (
            "No calendar read has been recorded yet, so there is nothing to call current."
        ),
        "live_meaning": (
            "Live means the Composio connection is still current with the harness. "
            "The calendar is read on a daily schedule, not continuously."
        ),
    }]},
]}

# The four sections that had no fixture at all, so the isolated preview could not serve
# them and Settings parity could not be claimed OR disproved for four fifths of the page
# (`if section != "connections": send_error(404)`). Every shape below is derived from the
# consumer that reads it -- payday.js, actions.js, security.js, trials.js -- rather than
# invented, because a fixture that guesses produces false gap reports.
#
# Every value is OBVIOUSLY SYNTHETIC: the "synthetic-" id prefix convention holds, and the
# preview banner says so on the page. These reads exist to render the shells for capture;
# they are not evidence about live data and must never be presented as such.
SETTINGS_PAYDAY = {
    "pattern": {"cadence": "biweekly", "confidence": 0.92, "evidence_count": 12,
                "next_date": "2026-09-16", "typical_amount": 1660.00},
    "next_run": {"date": "2026-09-16", "total": 780.00, "contributions": [
        {"commitment": "Example bill", "amount": 480.00},
        {"commitment": "Example reserve", "amount": 300.00},
    ]},
    "rules": [{"id": "synthetic-rule-1", "commitment_id": "synthetic-commitment-1",
               "kind": "fixed_per_paycheck", "amount": 300.00,
               "commitment": "Example reserve"}],
    "learning": {"floor": "2026-01-01", "included": 12, "excluded": 3, "set_at": None},
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-08T13:42:00Z"},
}

SETTINGS_ACTIONS = {"actions": [
    {"id": "synthetic-action-1", "type": "set_rent", "state": "verified",
     "rationale": "Owner stated an exact value.", "proposed_at": "2026-09-08T13:42:00Z"},
    {"id": "synthetic-action-2", "type": "reallocate_surplus", "state": "pending",
     "rationale": "Composed from the current shortfall.", "proposed_at": "2026-09-08T13:42:00Z"},
]}

SETTINGS_PASSKEYS = {"passkeys": [
    {"id": "synthetic-passkey-1", "name": "Example device", "created_at": "2026-09-08T13:42:00Z",
     "last_used_at": "2026-09-08T13:42:00Z"},
]}

SETTINGS_TRIALS = {"deadlines": [
    {"service": "Synthetic trial", "kind": "converts_to_paid", "due_at": "2026-09-12",
     "overdue": "false"},
]}

#: Settings sections the isolated preview can serve, and the read each one needs. The hub
#: is the no-section landing page.
SETTINGS_SECTIONS = ("connections", "payday", "actions", "security", "trials")


def settings_preview_html(section=None):
    """Render Settings at `section` (None = the hub) against synthetic reads only."""
    from meridian.settings_hub import SETTINGS_HUB

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    html = env.get_template("meridian/settings.html").render(
        active_workspace="", settings_active=True, active_settings_section=section,
        settings_hub=SETTINGS_HUB,
    )
    label = section or "hub"
    banner = (
        f'<div class="design-preview-banner">Synthetic Settings preview ({label}) '
        '· no bank connection</div>'
    )
    styles = '<style>.design-preview-banner{position:fixed;z-index:1000;bottom:0;left:0;right:0;padding:4px;background:#101a28;color:#eee4cf;text-align:center;font:10px system-ui}*{animation:none!important;transition:none!important}</style>'
    return html.replace("</head>", styles + "</head>").replace("</body>", banner + "</body>")


def preview_html():
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    html = env.get_template("meridian/index.html").render(active_workspace="today", settings_active=False)
    html = re.sub(r'<script\b[^>]*>.*?</script>', "", html, flags=re.S)
    html = html.replace(' data-model-url="/api/meridian/dial"', "")
    fixture = (ROOT / "tests/browser/fixtures/observatory-dial.html").read_text()
    model_script = re.search(r'<script>(window.setInterval.*?)</script>', fixture, flags=re.S).group(1)
    scripts = f"<script>document.documentElement.dataset.theme='dark';{model_script}</script>"
    # A workspace only renders if its controller is loaded. "plan" is included so
    # the Plan workspace populates from the PLAN fixture below; without it the
    # Plan captures showed empty states and every content difference read as a
    # missing feature. plan.js pulls its own imports (api, format, absent-bills,
    # action-outcome) through ES module resolution.
    for name in ("shell", "today", "dial", "plan", "activity", "accounts"):
        scripts += f'<script type="module" src="/static/js/meridian/{name}.js"></script>'
    scripts += '<script src="/static/js/meridian/theme.js"></script><script src="/static/js/ui/advisor_fab.js"></script>'
    banner = '<div class="design-preview-banner">Synthetic Today preview · no bank connection</div>'
    styles = '<style>.design-preview-banner{position:fixed;z-index:1000;bottom:0;left:0;right:0;padding:4px;background:#101a28;color:#eee4cf;text-align:center;font:10px system-ui}*{animation:none!important;transition:none!important}</style>'
    html = html.replace("</head>", styles + "</head>").replace("</body>", banner + scripts + "</body>")

    def version_asset(match):
        asset = ROOT / match.group(2).lstrip("/")
        return f'{match.group(1)}="{match.group(2)}?v={asset.stat().st_mtime_ns}"' if asset.is_file() else match.group(0)

    return re.sub(r'(src|href)="(/static/[^"?]+)"', version_asset, html)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path in ("/", "/meridian"):
            body, mime = preview_html().encode(), "text/html; charset=utf-8"
        elif path == "/meridian/settings":
            # No section renders the HUB; a known section renders that section. An unknown
            # section is still a 404: the preview must not pretend to serve a surface it
            # has no fixture for, because a silent fallback would make a missing fixture
            # look like a working page in a capture.
            section = parse_qs(urlsplit(self.path).query).get("section", [None])[0]
            if section is not None and section not in SETTINGS_SECTIONS:
                self.send_error(404, "Unknown synthetic Settings section")
                return
            body = settings_preview_html(section).encode()
            mime = "text/html; charset=utf-8"
        elif path == "/api/meridian/settings/connections":
            body, mime = json.dumps(SETTINGS_CONNECTIONS).encode(), "application/json"
        elif path == "/api/meridian/settings/payday":
            body, mime = json.dumps(SETTINGS_PAYDAY).encode(), "application/json"
        elif path == "/api/meridian/actions":
            body, mime = json.dumps(SETTINGS_ACTIONS).encode(), "application/json"
        elif path == "/api/auth/passkeys":
            body, mime = json.dumps(SETTINGS_PASSKEYS).encode(), "application/json"
        elif path == "/api/meridian/trials/deadlines":
            body, mime = json.dumps(SETTINGS_TRIALS).encode(), "application/json"
        elif path == "/api/meridian/today":
            body, mime = json.dumps(TODAY).encode(), "application/json"
        elif path == "/api/meridian/plan":
            body, mime = json.dumps(PLAN).encode(), "application/json"
        elif path == "/api/meridian/funding-rules":
            body, mime = json.dumps(FUNDING_RULES).encode(), "application/json"
        elif path == "/api/meridian/activity":
            body, mime = json.dumps(ACTIVITY).encode(), "application/json"
        elif path == "/api/meridian/accounts":
            body, mime = json.dumps(ACCOUNTS).encode(), "application/json"
        elif path == "/api/advisor/status":
            body, mime = b'{"configured":false}', "application/json"
        elif path.startswith("/static/"):
            candidate = (ROOT / path.lstrip("/")).resolve()
            if (ROOT / "static") not in candidate.parents or not candidate.is_file():
                self.send_error(404)
                return
            body = candidate.read_bytes()
            mime = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8093), Handler).serve_forever()
