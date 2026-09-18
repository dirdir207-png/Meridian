"""Guardrail checker acceptance.

Every case runs against a synthetic repository in tmp_path: the checker never touches
the real tree, never inspects a database, and never mutates git state.

The cases are the corrected contract from the cross-review. The earlier design is
disproven here by construction: case_missing_and_new_migration asserts that a
same-HEAD edit to a shipped migration FAILS (the old version passed it) and that a
legitimate new migration PASSES (the old version rejected it).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts/check_guardrails.py"
SHIPPED = "meridian/migrations/001_init.sql"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _write_claims(root: Path, claims: list[dict[str, object]]) -> None:
    (root / "docs/project/agent-claims.json").write_text(
        json.dumps({"schema_version": 1, "claims": claims}, indent=2)
    )


def make_repo(tmp_path: Path, claims: list[dict[str, object]] | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "meridian/migrations").mkdir(parents=True)
    (root / "docs/project").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / SHIPPED).write_text("CREATE TABLE a(id INTEGER);\n")
    (root / "app.py").write_text("# app\n")
    (root / "AGENTS.md").write_text("# governing rules\n")
    (root / "scripts/thing.py").write_text("# thing\n")
    (root / "docs/project/other.md").write_text("# other\n")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "test")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "baseline")

    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    (root / "docs/project/shipped-migrations.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "frozen_at_sha": sha,
                "migrations": {SHIPPED: hashlib.sha256((root / SHIPPED).read_bytes()).hexdigest()},
            },
            indent=2,
        )
    )
    _write_claims(
        root,
        claims
        if claims is not None
        else [
            {
                "agent": "me",
                "claim_id": "me-1",
                "generation": 1,
                "files": ["scripts/thing.py"],
                "base_sha": sha,
            },
            {
                "agent": "other",
                "claim_id": "other-1",
                "generation": 1,
                "files": ["docs/project/other.md"],
                "base_sha": sha,
            },
        ],
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "manifests")
    return root


def run_checker(root: Path, agent: str = "me") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--agent", agent, "--repo-root", str(root)],
        capture_output=True,
        text=True,
    )


# 1 - unchanged baseline passes
def test_unchanged_baseline_passes(tmp_path: Path) -> None:
    result = run_checker(make_repo(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


# 2 and 3 - the two directions the earlier design got wrong
def test_same_head_shipped_migration_edit_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / SHIPPED).write_text("CREATE TABLE a(id INTEGER, extra TEXT);\n")  # no commit: HEAD unchanged
    result = run_checker(root)
    assert result.returncode == 1, result.stdout
    assert "shipped migration was modified" in result.stdout


def test_new_migration_passes_and_is_reported(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "meridian/migrations/002_next.sql").write_text("CREATE TABLE b(id INTEGER);\n")
    result = run_checker(root)
    assert result.returncode == 0, result.stdout
    assert "new migration to register" in result.stdout


# 4 - a deleted tracked file outside every claim fails
def test_missing_tracked_baseline_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "app.py").unlink()
    result = run_checker(root)
    assert result.returncode == 1, result.stdout
    assert "changed outside declared scope" in result.stdout


# 5 - a rename whose destination is out of scope fails
def test_rename_out_of_scope_destination_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    _git(root, "mv", "scripts/thing.py", "docs/moved.py")
    result = run_checker(root)
    assert result.returncode == 1, result.stdout
    assert "moved.py" in result.stdout


# 6 - another owner's legitimate dirty file is preserved, not punished
def test_other_owners_dirty_file_is_preserved(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "docs/project/other.md").write_text("# other edited\n")
    result = run_checker(root)
    assert result.returncode == 0, result.stdout
    assert "preserved" in result.stdout


# 7 - an undeclared staged addition fails
def test_undeclared_staged_addition_fails(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "undeclared.txt").write_text("nope\n")
    _git(root, "add", "undeclared.txt")
    result = run_checker(root)
    assert result.returncode == 1, result.stdout
    # A staged addition appears as "A " in porcelain, not "??", so it is caught by the
    # out-of-scope rule rather than the untracked rule. Either message is correct; what
    # matters is that it fails loudly and names the path.
    assert "undeclared.txt" in result.stdout
    assert "FAIL" in result.stdout


# 8 - a stale claim is a configuration failure, not a silent pass
def test_stale_expired_claim_fails(tmp_path: Path) -> None:
    root = make_repo(
        tmp_path,
        claims=[
            {
                "agent": "me",
                "claim_id": "me-stale",
                "generation": 1,
                "files": ["scripts/thing.py"],
                "base_sha": "0" * 40,
                "expires_at": "2020-01-01T00:00:00+00:00",
            }
        ],
    )
    result = run_checker(root)
    assert result.returncode == 2, result.stdout
    assert "stale" in result.stdout


@pytest.mark.parametrize(
    "claims",
    [
        [{"agent": "me", "claim_id": "a", "generation": 1, "files": ["x.py"]}],  # missing base_sha
        [
            {"agent": "me", "claim_id": "a", "generation": 1, "files": ["x.py"], "base_sha": "0" * 40},
            {"agent": "me", "claim_id": "b", "generation": 1, "files": ["y.py"], "base_sha": "0" * 40},
        ],  # duplicate agent
        [
            {"agent": "me", "claim_id": "a", "generation": 1, "files": [], "base_sha": "0" * 40},
        ],  # empty scope
        [
            {"agent": "me", "claim_id": "a", "generation": 1, "files": ["**"], "base_sha": "0" * 40},
        ],  # whole-repo claim
    ],
)
def test_malformed_claims_fail_loudly(tmp_path: Path, claims: list[dict[str, object]]) -> None:
    result = run_checker(make_repo(tmp_path, claims=claims))
    assert result.returncode == 2, result.stdout
    assert "CONFIG" in result.stdout


def test_undeclared_agent_fails(tmp_path: Path) -> None:
    result = run_checker(make_repo(tmp_path), agent="nobody")
    assert result.returncode == 2, result.stdout
    assert "no claim declared" in result.stdout


# 9 - capability is validated, not the interpreter's path
def test_missing_capability_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import check_guardrails  # noqa: PLC0415
    finally:
        sys.path.pop(0)

    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> object:
        if name == "playwright":
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked)
    problems = check_guardrails.check_capabilities(require_browser=True)
    assert any("playwright" in p for p in problems)

    # A non-browser run must not demand the browser capability at all.
    assert check_guardrails.check_capabilities(require_browser=False) == []


def test_checker_is_read_only(tmp_path: Path) -> None:
    """The checker must not mutate git state or the working tree."""
    root = make_repo(tmp_path)
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"], cwd=root, capture_output=True
    ).stdout
    run_checker(root)
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"], cwd=root, capture_output=True
    ).stdout
    assert before == after


def test_receipt_records_evidence_and_leaves_session_fields_null(tmp_path: Path) -> None:
    """A receipt must record what was observed and NOT invent what only a session knows."""
    root = make_repo(tmp_path)
    (root / "scripts/thing.py").write_text("# thing edited\n")
    receipt = tmp_path / "reentry.json"
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--agent",
            "me",
            "--repo-root",
            str(root),
            "--receipt",
            str(receipt),
            "--quiet",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
    document = json.loads(receipt.read_text())
    assert document["agent"] == "me"
    assert document["authorized_scope"] == ["scripts/thing.py"]
    assert document["result"] == "ok"
    assert document["changed_paths"] == {"scripts/thing.py": "in-scope"}
    assert document["constraints_digest"].get("AGENTS.md"), "governing digest must be recorded"
    # base and current may legitimately differ: the claim records where it was made.
    # Recording both is the point - a claim based on an older HEAD must be visible.
    head_now = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert document["current_head"] == head_now
    assert len(str(document["base_head"][0])) == 40
    # Unfilled by design: a packet that guesses these is worse than one that admits they are blank.
    assert document["task"] is None
    assert document["next_action"] is None
    assert document["evidence_receipts"] == []
    assert document["unresolved_outcomes"] == []
