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


def preview_html():
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    html = env.get_template("meridian/index.html").render(active_workspace="today", settings_active=False)
    html = re.sub(r'<script\b[^>]*>.*?</script>', "", html, flags=re.S)
    html = html.replace(' data-model-url="/api/meridian/dial"', "")
    fixture = (ROOT / "tests/browser/fixtures/observatory-dial.html").read_text()
    model_script = re.search(r'<script>(window.setInterval.*?)</script>', fixture, flags=re.S).group(1)
    scripts = f"<script>document.documentElement.dataset.theme='dark';{model_script}</script>"
    for name in ("shell", "today", "dial"):
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
