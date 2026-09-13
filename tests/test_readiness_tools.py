"""Safety checks for the isolated audit tooling, using invented files only."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("readiness", Path(__file__).resolve().parents[1] / "scripts/verify_readiness.py")
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


def test_context_excludes_sensitive_and_untracked_inputs(monkeypatch, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    files = {"app.py": "pass", "cookies.txt": "synthetic-cookie", ".env": "synthetic-secret", "data/live.db": "synthetic-db", "scripts/verify_readiness.py": "pass", "untracked.py": "pass", "config/com.simplecrew.crew-broker.plist.template": "synthetic-template"}
    for name, text in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    monkeypatch.setattr(readiness, "ROOT", source)
    monkeypatch.setattr(readiness, "git", lambda *args: "\0".join(k for k in files if k != "untracked.py") if args[0] == "ls-files" else "synthetic-sha")
    monkeypatch.setattr(readiness.importlib.metadata, "distributions", lambda: [])
    context = tmp_path / "context"
    context.mkdir()
    monkeypatch.setattr(readiness.tempfile, "mkdtemp", lambda **kwargs: str(context))
    manifest = readiness.prepare_context()
    assert {item["path"] for item in manifest["files"]} == {"app.py", "scripts/verify_readiness.py", "config/com.simplecrew.crew-broker.plist.template"}
    assert json.loads((context / "readiness-source.json").read_text())["source_sha"] == "synthetic-sha"


def test_existing_evidence_is_not_overwritten(monkeypatch, tmp_path):
    output = tmp_path / "receipt.json"
    output.write_text("original")
    monkeypatch.setattr(readiness.sys, "argv", ["audit", "inventory", "--output", str(output)])
    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        readiness.main()
    assert output.read_text() == "original"


def test_restore_requires_explicit_isolated_environment(monkeypatch):
    monkeypatch.delenv("READINESS_NETWORK_NONE", raising=False)
    with pytest.raises(RuntimeError, match="network-isolated"):
        readiness.restore_rehearsal()
