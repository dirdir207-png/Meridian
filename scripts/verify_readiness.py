"""Repeatable Meridian readiness evidence; never reads the live database or .env.

The inventory subcommand parses source without importing the application.
Additional isolated rehearsal commands are documented in the readiness report.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return dotted(node.func) + "()"
    return ""


def literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def inventory() -> dict:
    paths = sorted({ROOT / "app.py", ROOT / "assistant.py", *ROOT.glob("meridian/**/*.py"), *ROOT.glob("crew/**/*.py")})
    modules = {}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        name = rel.removesuffix(".py").replace("/", ".").removesuffix(".__init__")
        modules[name] = {"path": rel, "tree": ast.parse(path.read_text(), filename=rel), "is_package": path.name == "__init__.py"}
    graph = {name: set() for name in modules}
    mounts = {}
    for item in modules.values():
        for node in ast.walk(item["tree"]):
            if isinstance(node, ast.Call) and dotted(node.func).endswith(".register_blueprint") and node.args:
                prefix = next((literal(k.value) for k in node.keywords if k.arg == "url_prefix"), "")
                if isinstance(prefix, str):
                    mounts[dotted(node.args[0])] = prefix
    routes, calls, declarations, dynamic = [], [], [], []
    for name, item in modules.items():
        tree = item["tree"]
        package = name if item["is_package"] else name.rpartition(".")[0]
        aliases = {}
        blueprint_prefixes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name] = alias.name
                    if alias.name in modules:
                        graph[name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                target = node.module or ""
                if node.level:
                    target = importlib.util.resolve_name("." * node.level + target, package)
                for alias in node.names:
                    candidate = f"{target}.{alias.name}"
                    aliases[alias.asname or alias.name] = candidate
                    dependency = candidate if candidate in modules else target
                    if dependency in modules:
                        graph[name].add(dependency)
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and dotted(node.value.func) == "Blueprint":
                prefix = next((literal(k.value) for k in node.value.keywords if k.arg == "url_prefix"), "")
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        blueprint_prefixes[target.id] = prefix or ""

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.scope = []

            def visit_ClassDef(self, node):
                self.scope.append(node.name)
                self.generic_visit(node)
                self.scope.pop()

            def visit_FunctionDef(self, node):
                qualified = ".".join([name, *self.scope, node.name])
                decorators = [dotted(d.func if isinstance(d, ast.Call) else d) for d in node.decorator_list]
                declarations.append({"symbol": qualified, "file": item["path"], "line": node.lineno})
                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                        continue
                    method = decorator.func.attr
                    if method not in {"route", "get", "post", "put", "patch", "delete"} or not decorator.args:
                        continue
                    path = literal(decorator.args[0])
                    if not isinstance(path, str):
                        continue
                    owner = dotted(decorator.func.value)
                    methods = next((literal(k.value) for k in decorator.keywords if k.arg == "methods"), None)
                    routes.append({"path": mounts.get(owner, "") + blueprint_prefixes.get(owner, "") + path, "methods": methods or ["GET" if method == "route" else method.upper()],
                                   "function": qualified, "file": item["path"], "line": node.lineno,
                                   "decorators": decorators, "login_decorator": any(d.endswith("login_required") for d in decorators)})
                self.scope.append(node.name)
                self.generic_visit(node)
                self.scope.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node):
                target = dotted(node.func)
                prefix, _, remainder = target.partition(".")
                resolved = aliases.get(prefix, prefix) + ("." + remainder if remainder else "")
                calls.append({"caller": ".".join([name, *self.scope]) or name, "target": target, "import_resolved": resolved, "file": item["path"], "line": node.lineno})
                if target.endswith("import_module") or target == "__import__":
                    dynamic.append({"file": item["path"], "line": node.lineno, "literal_target": literal(node.args[0]) if node.args else None})
                self.generic_visit(node)

        Visitor().visit(tree)
    for dependencies in graph.values():
        for dependency in list(dependencies):
            parts = dependency.split(".")
            dependencies.update(".".join(parts[:n]) for n in range(1, len(parts)) if ".".join(parts[:n]) in modules)
    reachable = set()
    queue = deque(["app", "assistant"])
    while queue:
        name = queue.popleft()
        if name in reachable:
            continue
        reachable.add(name)
        queue.extend(graph.get(name, ()))
    js = []
    for path in sorted((ROOT / "static/js/meridian").glob("*.js")):
        text = path.read_text()
        endpoints = sorted({m.group(1).split("?")[0] for m in re.finditer(r"['\"`](/api/[^'\"`\s]+)", text)})
        js.append({"file": str(path.relative_to(ROOT)), "api_literals": endpoints})
    migrations = []
    for path in sorted((ROOT / "meridian/migrations").glob("*.sql")):
        text = path.read_text()
        migrations.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(text.encode()).hexdigest(),
                           "tables_created": re.findall(r"CREATE TABLE(?: IF NOT EXISTS)?\s+([\w]+)", text, re.I)})
    return {"source_sha": git("rev-parse", "HEAD"), "method": "AST import/call/route inventory; static reachability is not runtime feature acceptance",
            "module_count": len(modules), "route_count": len(routes),
            "modules": [{"name": name, "file": item["path"], "imports": sorted(graph[name]), "potentially_import_reachable": name in reachable} for name, item in modules.items()],
            "routes": routes, "declarations": declarations, "calls": calls, "dynamic_imports": dynamic,
            "frontend_api_literals": js, "migrations": migrations}


def prepare_context() -> dict:
    """Build an allowlisted disposable source context, never the dirty checkout."""
    context = Path(tempfile.mkdtemp(prefix="meridian-readiness-context-"))
    allowed_roots = {"crew", "meridian", "templates", "static", "tests", "scripts", "docs"}
    allowed_suffixes = {".py", ".sh", ".sql", ".html", ".css", ".js", ".mjs", ".md", ".txt", ".svg", ".png", ".webp", ".jpg", ".ico", ".woff", ".woff2", ".ttf", ".json", ".yml", ".yaml"}
    files = git("ls-files", "-z").split("\0")
    files.append("scripts/verify_readiness.py")
    copied, excluded, suspicious = [], [], []
    secret_pattern = re.compile(rb"(?:sk-(?:proj-|or-v1-)[A-Za-z0-9_-]{20,}|Bearer [A-Za-z0-9_.-]{30,}|[?&]token=[A-Za-z0-9_-]{30,})")
    for rel in sorted(set(files)):
        if not rel:
            continue
        path = ROOT / rel
        parts = Path(rel).parts
        denied = (path.is_symlink() or not path.is_file() or any(part.startswith((".env", ".credentials", ".dsh")) for part in parts)
                  or path.name == "cookies.txt" or path.suffix in {".db", ".pem", ".key", ".zstd"}
                  or rel == "docs/project/crew_mutations.json" or "captures" in parts)
        selected = ((len(parts) == 1 and (path.suffix == ".py" or path.name in {"Dockerfile", "requirements.txt", "requirements-dev.txt", "pytest.ini"}))
                    or rel == "config/com.simplecrew.crew-broker.plist.template"
                    or (parts[0] in allowed_roots and path.suffix in allowed_suffixes))
        if denied or not selected:
            excluded.append(rel)
            continue
        data = path.read_bytes()
        if path.suffix not in {".png", ".jpg", ".webp", ".ico", ".woff", ".woff2", ".ttf"} and secret_pattern.search(data):
            suspicious.append(rel)
            continue
        target = context / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copied.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest()})
    constraints = sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions() if d.metadata.get("Name")})
    (context / "readiness-constraints.txt").write_text("\n".join(constraints) + "\n")
    dockerfile = """FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-dev.txt readiness-constraints.txt /tmp/
RUN python -m pip install --no-cache-dir -c /tmp/readiness-constraints.txt -r /tmp/requirements.txt -r /tmp/requirements-dev.txt
COPY . /app
ENV PYTHONPATH=/app DB_FILE=/tmp/meridian-synthetic/app.db
LABEL meridian.readiness.synthetic="true"
CMD ["python", "scripts/verify_readiness.py", "restore", "--output", "/evidence/restore.json"]
"""
    (context / "Dockerfile.readiness").write_text(dockerfile)
    manifest = {"source_sha": git("rev-parse", "HEAD"), "context_dir": str(context), "files": copied,
                "excluded_paths": excluded, "secret_pattern_paths_excluded": suspicious,
                "note": "Only allowlisted tracked source plus this audit tool; no live data/config copied. Heuristic source scan is not a comprehensive secret audit."}
    (context / "readiness-source.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def database_digest(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return hashlib.sha256("\n".join(connection.iterdump()).encode()).hexdigest()


def contract_probes() -> dict:
    """Characterize disputed paths with invented records and mocked transport only."""
    import io
    from datetime import date
    from unittest.mock import patch

    from pypdf import PdfReader, PdfWriter

    from meridian.beacon import Forecast
    from meridian.commitments import CommitmentRepository, CommitmentType
    from meridian.crew_write_actions import _verify_crew_bill_readback, _verify_stored
    from meridian.evidence import EvidenceRepository
    from meridian.ingest import IntakeRecord, QuarantineError, ingest_record
    from meridian.live import sync_live_crew
    from meridian.providers.crewwork import CrewWorkSnapshotAdapter
    from meridian.scenarios import run_scenario
    from meridian.services.dial import _advance

    results = {"source_sha": git("rev-parse", "HEAD"), "synthetic_only": True, "provider_calls": 0}
    with tempfile.TemporaryDirectory(prefix="meridian-contract-probes-") as directory:
        db = str(Path(directory) / "synthetic.db")
        evidence = EvidenceRepository(db)
        pdf = PdfWriter()
        pdf.add_blank_page(width=100, height=100)
        stream = io.BytesIO()
        pdf.write(stream)
        content = stream.getvalue()
        assert not PdfReader(io.BytesIO(content)).is_encrypted
        try:
            ingest_record(IntakeRecord("upload", "synthetic-pdf", content, "application/pdf"), evidence_repo=evidence)
        except QuarantineError as exc:
            results["unencrypted_pdf"] = {"accepted": False, "reason": str(exc)}
        else:
            results["unencrypted_pdf"] = {"accepted": True}

        class FailedBlobStore:
            def put(self, *_args, **_kwargs):
                raise OSError("synthetic disk failure")

        intake = ingest_record(IntakeRecord("upload", "synthetic-text", b"Synthetic bill: $20.00", "text/plain"), evidence_repo=evidence, blob_store=FailedBlobStore())
        results["blob_write_failure"] = {"returned_quarantined": intake.quarantined, "metadata_persisted": evidence.get_item(intake.item_id) is not None}
        verifier = _verify_stored(db, "name")
        results["reserve_settings_no_local_id"] = verifier({"name": "Synthetic"}, {"success": True})
        commitments = CommitmentRepository(db)
        bill = commitments.create(type=CommitmentType.BILL, name="Synthetic bill", amount=20, recurrence="monthly", legacy_source="crew", legacy_id="synthetic-bill")
        try:
            verifier({"commitment_id": bill.id, "name": "Synthetic bill"}, {"success": True})
        except Exception as exc:
            results["reserve_settings_with_local_id"] = {"exception": type(exc).__name__, "message": str(exc)}
        partial = {"mode": "read-only", "source": "crew", "mutations_enabled": False, "complete": False, "data": {}}
        with patch("meridian.live.capture_crew_snapshot", return_value=partial):
            results["partial_readback_missing_bill"] = _verify_crew_bill_readback()({"billId": "synthetic-bill", "name": "Synthetic bill"}, {})
        malformed_complete = {**partial, "complete": True}
        normalized = CrewWorkSnapshotAdapter(malformed_complete).fetch_snapshot()
        sync_live_crew(db, snapshot=malformed_complete)
        results["missing_facets_complete_flag"] = {"normalized_complete": normalized.is_complete, "existing_bill_marked_absent": commitments.get(bill.id).absent_since is not None}

    results["calendar"] = {"monthly_second": _advance(_advance(date(2026, 1, 31), "monthly"), "monthly").isoformat(), "semimonthly_next": _advance(date(2026, 1, 15), "semimonthly").isoformat()}
    base = Forecast(available=True, reason=None, as_of=date(2026, 9, 1), starting_cash=1000, daily_expense=20,
                    daily_expense_range=(15, 25), runway_days=50, low_point=400, low_point_date=date(2026, 10, 1),
                    first_shortfall=None, coverage_horizons={"7d": 860, "30d": 400}, factors=(), confidence=.8, freshness="fresh")
    scenario = run_scenario(base, {"income": 100}).scenario
    results["scenario"] = {"starting_cash_changed": scenario.starting_cash != base.starting_cash, "coverage_horizons_unchanged": scenario.coverage_horizons == base.coverage_horizons}
    return results


def assert_fixture(root: Path) -> dict:
    marker = root / "synthetic-readiness.json"
    if not marker.is_file():
        raise RuntimeError("Refusing a database without the synthetic-rehearsal marker")
    data = json.loads(marker.read_text())
    if data.get("synthetic") is not True or data.get("kind") != "meridian-readiness":
        raise RuntimeError("Invalid synthetic-rehearsal marker")
    return data


def verify_restored(root: Path) -> dict:
    """Fresh-process verification of only a marked synthetic restore directory."""
    expected = assert_fixture(root)
    path = root / "app.db"
    if database_digest(path) != expected["database_digest"]:
        raise RuntimeError("Restored database does not match its logical snapshot")
    os.environ["DB_FILE"] = str(path)
    from crew.actions import ActionStore, IllegalTransitionError
    from meridian.repository import FinancialRepository

    graph = FinancialRepository(str(path))
    account = graph.get_account(expected["account_id"])
    assert account.balance == 1234.56 and account.available_balance == 1200.00
    store = ActionStore(str(path), allowed_types=("synthetic_transfer",))
    assert store.get(expected["action_id"])["state"] == "executed"
    try:
        store.claim_for_execution(expected["action_id"], "must-not-resubmit")
    except IllegalTransitionError:
        pass
    else:
        raise AssertionError("An unresolved restored action became eligible for resubmission")

    import app as application
    application._background_thread_started = True
    # Test-only process: actual route/auth decorators remain, background effects do not run.
    application.app.before_request_funcs[None] = []
    blob_store = application.app.config["MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY"]()
    assert blob_store.read(expected["blob_hash"]) == b"Synthetic readiness evidence; no real account data."
    client = application.app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "1"
        session["_fresh"] = True
    statuses = {}
    for route in ("/meridian", "/api/meridian/accounts", "/api/meridian/today", f"/api/meridian/evidence/{expected['evidence_id']}/content"):
        response = client.get(route)
        statuses[route] = response.status_code
        assert response.status_code == 200, (route, response.status_code)
    assert b"Synthetic readiness evidence" in response.data
    return {"fresh_process": True, "account_restored": True, "unresolved_action_nonretryable": True,
            "encrypted_evidence_readable": True, "authenticated_route_statuses": statuses}


def restore_rehearsal() -> dict:
    """Generate, back up, damage and restore disposable synthetic application state."""
    if not Path("/.dockerenv").exists() or os.environ.get("READINESS_NETWORK_NONE") != "1":
        raise RuntimeError("Run restore only in the documented network-isolated rehearsal container")
    with tempfile.TemporaryDirectory(prefix="meridian-restore-synthetic-") as directory:
        root = Path(directory)
        original = root / "original"
        original.mkdir()
        path = original / "app.db"
        os.environ["DB_FILE"] = str(path)
        import app as application
        from crew.actions import ActionStore
        from meridian import db as db_module
        from meridian.evidence import EvidenceRepository
        from meridian.repository import FinancialRepository
        from meridian.storage import (
            BlobDecryptionError,
            DerivedKeyProvider,
            EncryptedBlobStore,
        )

        application._background_thread_started = True
        application.app.before_request_funcs[None] = []
        graph = FinancialRepository(str(path))
        account = graph.upsert_account(provider="synthetic", external_id="synthetic-readiness-account", name="Synthetic account",
                                       account_type="checking", balance=1234.56, available_balance=1200.00,
                                       source_updated_at="2026-09-13T12:00:00Z")
        blob_store = application.app.config["MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY"]()
        blob = blob_store.put(b"Synthetic readiness evidence; no real account data.", mime_type="text/plain")
        evidence = EvidenceRepository(str(path)).add_item(source_kind="manual", source_id="synthetic-readiness",
                    content_hash=blob.content_hash, mime_type="text/plain", size_bytes=blob.size_bytes, title="Synthetic evidence")
        store = ActionStore(str(path), allowed_types=("synthetic_transfer",))
        action = store.propose("synthetic_transfer", {"amount": 1}, "Synthetic uncertain action, never submitted", "synthetic-owner")
        store.approve(action["id"], "synthetic-owner")
        store.claim_for_execution(action["id"], "synthetic-claim")
        store.mark_executed(action["id"], {"accepted": True, "synthetic": True})
        store.record_verification_pending(action["id"], {"ok": False, "reason": "synthetic readback unavailable"})
        with sqlite3.connect(path) as connection:
            connection.execute("INSERT INTO users(id,username,email,password_hash) VALUES (1,?,?,?)",
                               ("synthetic-owner", "synthetic@example.invalid", "not-a-real-password-hash"))

        backup = root / "backup"
        backup.mkdir()
        source_connection = sqlite3.connect(path)
        source_connection.execute("PRAGMA journal_mode=WAL")
        source_connection.execute("PRAGMA wal_autocheckpoint=0")
        source_connection.execute("CREATE TABLE readiness_wal_probe(value TEXT)")
        source_connection.execute("INSERT INTO readiness_wal_probe VALUES ('synthetic committed WAL row')")
        source_connection.commit()
        destination = sqlite3.connect(backup / "app.db")
        source_connection.backup(destination)
        destination.close()
        source_connection.close()
        shutil.copytree(original / "evidence", backup / "evidence")
        digest = database_digest(path)
        assert database_digest(backup / "app.db") == digest
        with sqlite3.connect(backup / "app.db") as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert connection.execute("SELECT value FROM readiness_wal_probe").fetchone()[0] == "synthetic committed WAL row"
            migration_count = connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0]

        expected = {"synthetic": True, "kind": "meridian-readiness", "database_digest": digest,
                    "account_id": account.id, "action_id": action["id"], "blob_hash": blob.content_hash, "evidence_id": evidence.id}
        (backup / "synthetic-readiness.json").write_text(json.dumps(expected))
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE financial_accounts SET balance=999 WHERE id=?", (account.id,))
        Path(blob.path).write_bytes(b"synthetic damage")
        assert database_digest(path) != digest

        migration_copy = root / "migrations"
        shutil.copytree(db_module.MIGRATIONS_DIR, migration_copy)
        (migration_copy / "022_synthetic_failure.sql").write_text("CREATE TABLE synthetic_failed_migration(id INTEGER);\nINSERT INTO missing_synthetic_table VALUES (1);\n")
        previous = db_module.MIGRATIONS_DIR
        db_module.MIGRATIONS_DIR = migration_copy
        try:
            try:
                db_module.run_migrations(str(path))
            except sqlite3.OperationalError:
                pass
            else:
                raise AssertionError("Broken synthetic migration was accepted")
        finally:
            db_module.MIGRATIONS_DIR = previous
        with sqlite3.connect(path) as connection:
            assert connection.execute("SELECT count(*) FROM sqlite_master WHERE name='synthetic_failed_migration'").fetchone()[0] == 0

        restored = root / "restored"
        shutil.copytree(backup, restored)
        wrong_key = EncryptedBlobStore(restored / "evidence", DerivedKeyProvider(b"synthetic-wrong-key"))
        try:
            wrong_key.read(blob.content_hash)
        except BlobDecryptionError:
            pass
        else:
            raise AssertionError("Wrong evidence key was accepted")
        bad = root / "bad-restore"
        shutil.copytree(backup, bad)
        with sqlite3.connect(bad / "app.db") as connection:
            connection.execute("DELETE FROM financial_accounts")
        try:
            verify_restored(bad)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Altered backup was accepted")

        child = subprocess.run([sys.executable, str(Path(__file__).resolve()), "verify-fixture", "--fixture", str(restored)],
                               text=True, capture_output=True, timeout=45)
        if child.returncode:
            raise RuntimeError(f"Fresh-process restore verification failed: {child.stderr[-4000:]}")
        verification = json.loads(child.stdout.splitlines()[-1])
        return {"synthetic_only": True, "source_image": os.environ.get("READINESS_IMAGE_ID"), "source_sha": json.loads((ROOT / "readiness-source.json").read_text())["source_sha"],
                "migration_count": migration_count, "database_snapshot_digest": digest, "sqlite_online_backup_includes_wal": True,
                "failed_migration_rolled_back": True, "wrong_evidence_key_rejected": True, "altered_backup_rejected": True,
                "restore": verification, "limitations": "Synthetic matched-source-image/data restore; no production backup, Keychain migration or live acceptance."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory", "prepare-context", "restore", "verify-fixture", "probes"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    if args.command == "verify-fixture":
        if not Path("/.dockerenv").exists() or args.fixture is None:
            raise SystemExit("Fixture verification requires the isolated container and marked fixture")
        print(json.dumps(verify_restored(args.fixture)))
        return
    if args.output is None:
        parser.error("--output is required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit("Refusing to overwrite an existing evidence artifact")
    result = {"inventory": inventory, "prepare-context": prepare_context, "restore": restore_rehearsal, "probes": contract_probes}[args.command]()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "command": args.command, "exit_code": 0,
                      **({"context_dir": result["context_dir"], "files": len(result["files"]), "excluded_sensitive_pattern_files": result["secret_pattern_paths_excluded"]} if args.command == "prepare-context" else {})}))


if __name__ == "__main__":
    main()
