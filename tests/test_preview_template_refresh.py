"""Preview template refresh contract, with no banking app or local secrets loaded."""
import os
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

from flask import Flask, render_template

ROOT = Path(__file__).resolve().parents[1]


def test_preview_refreshes_changed_template_without_process_restart(tmp_path, monkeypatch):
    templates = tmp_path / "templates"
    templates.mkdir()
    template = templates / "page.html"
    template.write_text("old header")
    fake_app = Flask(__name__, template_folder=str(templates))
    with fake_app.app_context():
        assert render_template("page.html") == "old header"

    stub = SimpleNamespace(app=fake_app, ensure_meridian_refresh=lambda: None)
    monkeypatch.setitem(sys.modules, "app", stub)
    monkeypatch.setenv("DB_FILE", str(tmp_path / "unused-synthetic.db"))
    # Relocating the runner ensures its .env loader cannot read the real .env.
    runner = tmp_path / "run_preview.py"
    runner.write_text((ROOT / "run_preview.py").read_text())
    runpy.run_path(str(runner), run_name="preview_template_test")

    previous_time = template.stat().st_mtime
    template.write_text("new header")
    os.utime(template, (previous_time + 2, previous_time + 2))
    with fake_app.app_context():
        assert render_template("page.html") == "new header"
    assert not (tmp_path / "unused-synthetic.db").exists()
