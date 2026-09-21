"""Observatory slice: Settings Security & Data is read-only metadata."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_settings_navigation_and_template_include_security():
    """Restated 2026-09-21 for the Settings hub.

    The flat nav's row label WAS "Security & data". The 09-18 concept's grouped hub names the
    same route "Security & devices" (subtitle "Sessions, devices and data"), so label, href
    and section now live in one place: meridian/settings_hub.py. The security PARTIAL still
    identifies itself as "Security & Data" in its own heading, which is where that wording
    remains accurate. Restated rather than deleted so the rename is visible.
    """
    from meridian.settings_hub import settings_hub_rows

    row = next(r for r in settings_hub_rows() if r["key"] == "security-devices")
    assert row["href"] == "/meridian/settings?section=security"
    assert row["label"] == "Security & devices"
    assert row["section"] == "security"

    settings = _read("templates/meridian/settings.html")
    assert "active_settings_section == 'security'" in settings
    assert "partials/security.html" in settings
    assert "static/js/meridian/security.js" in settings


def test_security_ui_never_renders_credential_material():
    html = _read("templates/meridian/partials/security.html")
    js = _read("static/js/meridian/security.js")
    assert "Credential IDs and token material are intentionally not rendered here" in html
    assert "credentialId" not in js
    assert "credential_id" not in html.lower()
    assert "meridianFetch(\"/api/auth/passkeys\")" in js


def test_security_safeguards_are_explicit():
    html = _read("templates/meridian/partials/security.html")
    for phrase in (
        "Crew credentials stay server-side",
        "Connections are read-only by design",
        "Financial changes require explicit approval",
        "Meridian never retries an uncertain financial write",
    ):
        assert phrase in html
