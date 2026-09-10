"""Run Meridian preview. Legacy background threads stay disabled, but the
Meridian live-data refresh loop runs (auto-syncs CrewWorkAssistant snapshots
every MERIDIAN_REFRESH_INTERVAL seconds, default 300)."""
import os
from pathlib import Path


def _load_local_env() -> None:
    """Load local preview settings without logging secret values."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key and value and key not in os.environ:
            os.environ[key] = value


_load_local_env()

os.environ.setdefault(
    "DB_FILE",
    os.environ.get("GATE_DB", "/tmp/gate-preview/gate.db"),
)

# The private Tailscale preview is served over HTTP; allow its session cookie
# to round-trip from phones. Production defaults remain Secure in app.py.
os.environ.setdefault("SESSION_COOKIE_SECURE", "0")

# Patch out legacy background threads before importing app
import app as a

a._background_thread_started = True

# Remove the before_request hook that starts threads
a.app.before_request_funcs[None] = []

# Start the Meridian live-data refresh loop (idempotent, safe to call).
a.ensure_meridian_refresh()

if __name__ == "__main__":
    a.app.run(host="0.0.0.0", port=8081, debug=False, use_reloader=False)
