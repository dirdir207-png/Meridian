"""Branding guard for auth and first-run surfaces (Home Screen identity).

iOS names a Home Screen web app from ``apple-mobile-web-app-title`` (falling back
to ``<title>``) and from the web manifest's ``name``/``short_name``. ``/login``
renders ``register.html`` whenever the users table is empty, so ``register.html``
*is* the first-run landing page — if it still advertises "SimpleCrew", re-saving
the icon renames the app.

These checks render the templates so a broken Jinja/markup change fails here
rather than in the browser, and they pin the auth form contract so a branding
edit cannot silently drop a field or an endpoint.
"""

from pathlib import Path

import pytest
from flask import Flask, render_template

ROOT = Path(__file__).parents[2]
TEMPLATES = ROOT / "templates"
MANIFEST = ROOT / "static/manifest.json"

BRANDING_TEMPLATES = ("base.html", "login.html", "register.html", "onboarding.html")


@pytest.fixture(scope="module")
def renderer():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES),
        static_folder=str(ROOT / "static"),
    )

    def render(name):
        with app.test_request_context():
            return render_template(name)

    return render


def test_manifest_names_the_app_meridian():
    import json

    manifest = json.loads(MANIFEST.read_text())

    assert manifest["name"] == "Meridian"
    assert manifest["short_name"] == "Meridian"


@pytest.mark.parametrize("template", BRANDING_TEMPLATES)
def test_no_home_screen_surface_still_advertises_simplecrew(renderer, template):
    html = renderer(template)

    assert "SimpleCrew" not in html, f"{template} still advertises SimpleCrew"


def test_register_page_is_a_meridian_first_run_page(renderer):
    html = renderer("register.html")

    assert '<meta name="apple-mobile-web-app-title" content="Meridian">' in html
    assert "<title>Meridian - Setup</title>" in html
    assert ">Meridian</h1>" in html


def test_login_page_is_a_meridian_page(renderer):
    html = renderer("login.html")

    assert '<meta name="apple-mobile-web-app-title" content="Meridian">' in html
    assert "<title>Meridian - Login</title>" in html
    assert ">Meridian</h1>" in html


def test_register_page_keeps_the_registration_contract(renderer):
    html = renderer("register.html")

    for element_id in ("registerForm", "username", "email", "password", "errorMessage"):
        assert f'id="{element_id}"' in html, f"register.html lost #{element_id}"
    assert "fetch('/api/auth/register'" in html
    assert "method: 'POST'" in html
    assert "JSON.stringify({ username, email, password })" in html
    assert "at least 8 characters" in html


def test_login_page_keeps_the_authentication_contract(renderer):
    html = renderer("login.html")

    for element_id in (
        "passkeyLoginSection",
        "passkeyLoginBtn",
        "showPasswordLoginBtn",
        "passwordLoginForm",
        "loginForm",
        "username",
        "password",
        "errorMessage",
    ):
        assert f'id="{element_id}"' in html, f"login.html lost #{element_id}"
    assert "/api/auth/passkeys/available" in html
    assert "/api/auth/login" in html
    assert "Sign in with Passkey" in html


def test_every_template_that_names_the_app_uses_meridian():
    names = set()
    for path in sorted(TEMPLATES.glob("*.html")):
        for line in path.read_text().splitlines():
            marker = 'name="apple-mobile-web-app-title" content="'
            if marker in line:
                names.add((path.name, line.split(marker, 1)[1].split('"', 1)[0]))

    assert names, "expected at least one template to declare the Home Screen title"
    wrong = sorted(name for name in names if name[1] != "Meridian")
    assert wrong == [], f"templates still naming another app: {wrong}"


SERVICE_WORKER = ROOT / "static/sw.js"


def test_service_worker_never_serves_a_cached_manifest():
    """The Home Screen app name is read from the manifest.

    ``static/sw.js`` used to answer ``/manifest.json`` from a cache-first branch
    under a cache name that did not change, so an installed app kept the old
    product name forever even after the file was corrected.
    """
    worker = SERVICE_WORKER.read_text()

    assert "url.pathname === '/manifest.json'" in worker, (
        "the manifest must take the network-first branch"
    )
    cache_first_branch = worker.split("// ── Everything else", 1)[1]
    assert "/manifest.json" not in cache_first_branch, (
        "the manifest must not fall through to the cache-first branch"
    )


def test_service_worker_cache_version_is_bumped_past_the_stale_manifest():
    worker = SERVICE_WORKER.read_text()
    version = int(worker.split("const CACHE_NAME = 'simple-finance-v", 1)[1].split("'", 1)[0])

    assert version >= 13, (
        "bump CACHE_NAME so existing installs drop the cached SimpleCrew manifest"
    )


def test_push_notification_defaults_are_meridian_branded():
    worker = SERVICE_WORKER.read_text()

    assert "title: 'Meridian'" in worker
    assert "title: 'SimpleCrew'" not in worker
    assert "tag: 'meridian-sync'" in worker
