"""Isolated Today design preview: production templates/controllers, synthetic reads only.

Run with .venv311/bin/python scripts/preview_observatory_dial.py.
No app import, environment loading, database, authentication, or provider access.
"""
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
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
         "due_date": "2026-09-11", "target_date": None, "backing": "bill_reserve",
         "biller_status": "reserved", "crew_bill_id": "synthetic-electric",
         "invoice_evidence": None},
        {"id": "synthetic-internet", "name": "Internet", "type": "bill",
         "target": 65.00, "funded": 65.00, "unfunded": 0.00,
         "due_date": "2026-09-14", "target_date": None, "backing": "bill_reserve",
         "biller_status": "reserved", "crew_bill_id": "synthetic-internet",
         "invoice_evidence": None},
        {"id": "synthetic-rent", "name": "Rent", "type": "bill",
         "target": 1171.00, "funded": 1171.00, "unfunded": 0.00,
         "due_date": "2026-09-16", "target_date": None, "backing": "bill_reserve",
         "biller_status": "reserved", "crew_bill_id": "synthetic-rent",
         "invoice_evidence": None},
        {"id": "synthetic-goal", "name": "Emergency fund", "type": "goal",
         "target": 200.00, "funded": 200.00, "unfunded": 0.00,
         "due_date": None, "target_date": "2027-03-01", "backing": "pocket",
         "biller_status": None, "crew_bill_id": None, "invoice_evidence": None},
    ],
    "next_paycheck": {"date": "2026-09-16", "amount": 1660.00},
    "timeline": {
        "events": [
            {"key": "synthetic-1", "date": "2026-09-11", "amount": 84.00,
             "commitment_id": "synthetic-electric", "detail": "Reserved"},
            {"key": "synthetic-2", "date": "2026-09-14", "amount": 65.00,
             "commitment_id": "synthetic-internet", "detail": "Reserved"},
            {"key": "synthetic-3", "date": "2026-09-16", "amount": 1171.00,
             "commitment_id": "synthetic-rent", "detail": "Reserved"},
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
    "accounts": [
        {"id": 1, "name": "Checking", "provider": "crew"},
        {"id": 2, "name": "Emergency fund", "provider": "crew"},
    ]
}

ACTIVITY = {
    "transactions": [
        {"id": "synthetic-tx-1", "amount": -84.00, "currency": "USD",
         "description": "Electric", "merchant": "Electric", "provider": "crew",
         "occurred_at": "2026-09-11T12:00:00Z", "classification": "bill",
         "suggested_category": "Utilities", "category_options": ["Utilities", "Home"]},
        {"id": "synthetic-tx-2", "amount": -65.00, "currency": "USD",
         "description": "Internet", "merchant": "Internet", "provider": "crew",
         "occurred_at": "2026-09-14T12:00:00Z", "classification": "bill",
         "suggested_category": "Utilities", "category_options": ["Utilities", "Home"]},
        {"id": "synthetic-tx-3", "amount": 1660.00, "currency": "USD",
         "description": "Paycheck", "merchant": "Paycheck", "provider": "crew",
         "occurred_at": "2026-09-16T12:00:00Z", "classification": "income",
         "suggested_category": "Income", "category_options": ["Income"]},
    ],
    "patterns": [],
    "next_cursor": None,
    "data_freshness": {"status": "fresh", "last_updated_at": "2026-09-08T13:42:00Z"},
}


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
    for name in ("shell", "today", "dial", "plan", "activity"):
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
