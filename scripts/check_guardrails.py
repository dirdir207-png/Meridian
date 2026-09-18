#!/usr/bin/env python3
"""Fail loudly when a change steps outside its declared scope.

This implements the corrected contract from the cross-review, replacing an earlier
version whose migration check was disproven in both directions: it keyed on HEAD
drift, so it missed same-HEAD edits to already-shipped migrations (the exact failure
that caused an outage) while rejecting legitimate new ones.

What it enforces, and what it deliberately does not:

* Declared scope, not authorship. `git status` cannot tell who changed a file, so
  this checks each change against the scope declared in docs/project/agent-claims.json.
  A file changed by another agent is NOT this agent's violation - but it does
  invalidate admission rather than authorising an overwrite.
* Shipped migrations are frozen by path->hash in docs/project/shipped-migrations.json,
  independent of where HEAD sits. Listed files may not change or disappear. New .sql
  files are allowed and reported for registration.
* NUL-safe parsing, so renames, quoted names and deletions are handled correctly.
* Capability, not path: a valid alternative environment is acceptable, a broken one
  is not.

Read-only: it never writes to the repository, never inspects a database, and never
mutates git state. Run it against a synthetic repository in tests.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK, EXIT_VIOLATION, EXIT_CONFIG = 0, 1, 2
REQUIRED_CLAIM_KEYS = ("agent", "claim_id", "generation", "files", "base_sha")


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.decode().strip()}")
    return result.stdout


def parse_status(root: Path) -> list[dict[str, object]]:
    """NUL-delimited porcelain v1. Renames emit TWO NUL-separated names."""
    raw = git(root, "status", "--porcelain=v1", "-z").decode("utf-8", "surrogateescape")
    tokens = [t for t in raw.split("\0") if t]
    entries: list[dict[str, object]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        xy, path = token[:2], token[3:]
        entry: dict[str, object] = {"xy": xy, "path": path, "untracked": xy == "??"}
        if "R" in xy or "C" in xy:  # rename/copy: original path follows
            if index < len(tokens):
                entry["original"] = tokens[index]
                index += 1
        entries.append(entry)
    return entries


def load_json(root: Path, rel: str) -> object:
    path = root / rel
    if not path.is_file():
        _die(EXIT_CONFIG, f"missing required file: {rel}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        _die(EXIT_CONFIG, f"{rel} is not valid JSON: {exc}")


def _die(code: int, message: str) -> None:
    print(f"CONFIG  {message}")
    raise SystemExit(code)


def load_claims(root: Path, agent: str) -> list[dict[str, object]]:
    """Validate every claim, then return the caller's. Malformed input is fatal."""
    document = load_json(root, "docs/project/agent-claims.json")
    if not isinstance(document, dict) or not isinstance(document.get("claims"), list):
        _die(EXIT_CONFIG, "agent-claims.json must be an object with a 'claims' list")

    seen_agents: set[str] = set()
    seen_ids: set[str] = set()
    now = datetime.now(timezone.utc)
    for claim in document["claims"]:
        if not isinstance(claim, dict):
            _die(EXIT_CONFIG, "every claim must be an object")
        missing = [k for k in REQUIRED_CLAIM_KEYS if k not in claim]
        if missing:
            _die(EXIT_CONFIG, f"claim {claim.get('claim_id', '?')} missing keys: {missing}")
        if claim["agent"] in seen_agents:
            _die(EXIT_CONFIG, f"duplicate claim for agent {claim['agent']!r}")
        if claim["claim_id"] in seen_ids:
            _die(EXIT_CONFIG, f"duplicate claim_id {claim['claim_id']!r}")
        seen_agents.add(str(claim["agent"]))
        seen_ids.add(str(claim["claim_id"]))
        if not isinstance(claim["generation"], int) or claim["generation"] < 1:
            _die(EXIT_CONFIG, f"claim {claim['claim_id']} has an invalid generation")
        patterns = claim["files"]
        if not isinstance(patterns, list) or not patterns or not all(
            isinstance(p, str) and p.strip() for p in patterns
        ):
            _die(EXIT_CONFIG, f"claim {claim['claim_id']} must declare a non-empty file list")
        if any(p in {"*", "**", "/", "./"} for p in patterns):
            _die(EXIT_CONFIG, f"claim {claim['claim_id']} claims the whole repository")
        if expires := claim.get("expires_at"):
            try:
                if datetime.fromisoformat(str(expires).replace("Z", "+00:00")) < now:
                    _die(EXIT_CONFIG, f"claim {claim['claim_id']} is stale (expired {expires})")
            except ValueError:
                _die(EXIT_CONFIG, f"claim {claim['claim_id']} has an unparseable expires_at")

    mine = [c for c in document["claims"] if c["agent"] == agent]
    if not mine:
        _die(EXIT_CONFIG, f"no claim declared for {agent!r} - declare scope before editing")
    return mine


def matches(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatch(path, p) or fnmatch.fnmatch(path, p.rstrip("/**")) for p in patterns
    )


def check_migrations(root: Path, entries: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    manifest = load_json(root, "docs/project/shipped-migrations.json")
    if not isinstance(manifest, dict) or "migrations" not in manifest:
        _die(EXIT_CONFIG, "shipped-migrations.json must contain a 'migrations' mapping")
    shipped: dict[str, str] = manifest["migrations"]
    violations: list[str] = []
    notes: list[str] = []

    for rel, expected in shipped.items():
        path = root / rel
        if not path.is_file():
            violations.append(f"shipped migration is missing: {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            violations.append(f"shipped migration was modified: {rel} (ship a new migration)")

    for entry in entries:
        path = str(entry["path"])
        if path.startswith("meridian/migrations/") and path.endswith(".sql") and path not in shipped:
            notes.append(f"new migration to register in the frozen manifest: {path}")
    return violations, notes


def check_capabilities(require_browser: bool) -> list[str]:
    """Validate capability rather than path: a different valid environment is fine."""
    problems: list[str] = []
    if sys.version_info < (3, 11):
        problems.append(f"interpreter is {sys.version_info.major}.{sys.version_info.minor}, need >= 3.11")
    for module, needed in (("flask", True), ("playwright", require_browser)):
        if not needed:
            continue
        try:
            __import__(module)
        except ImportError:
            problems.append(f"required capability missing: cannot import {module!r}")
    return problems


def build_receipt(
    root: Path,
    agent: str,
    claims: list[dict[str, object]],
    mine: list[str],
    entries: list[dict[str, object]],
    violations: list[str],
    notes: list[str],
    other_agents: dict[str, str],
) -> dict[str, object]:
    """The re-entry packet: what a session must establish before its first mutation.

    Fields the checker can compute are filled in. The fields only a session can know -
    task, what it verified and how, what is unresolved, the single next action - are
    left explicitly null rather than guessed, so an unfilled packet is visible.
    """
    constraints: dict[str, str] = {}
    for rel in ("AGENTS.md", "docs/project/MERIDIAN_DECISIONS.md", "docs/project/MERIDIAN_ROADMAP.md"):
        path = root / rel
        if path.is_file():
            constraints[rel] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    def kind(entry: dict[str, object]) -> str:
        path = str(entry["path"])
        if entry["untracked"]:
            return "untracked"
        if matches(path, mine):
            return "in-scope"
        owner = other_agents.get(path) or next(
            (a for pat, a in other_agents.items() if fnmatch.fnmatch(path, pat)), None
        )
        # Distinguish a peer's declared work from genuinely undeclared drift.
        return f"claimed-by:{owner}" if owner else "undeclared"

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "agent": agent,
        "claim_id": [c["claim_id"] for c in claims],
        "claim_generation": [c["generation"] for c in claims],
        "repo_root": str(root),
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip(),
        "base_head": [c["base_sha"] for c in claims],
        "current_head": git(root, "rev-parse", "HEAD").decode().strip(),
        "constraints_digest": constraints,
        "authorized_scope": mine,
        "changed_paths": {str(e["path"]): kind(e) for e in entries},
        "result": "violation" if violations else "ok",
        "violations": violations,
        "notes": notes,
        # Filled in by the session, never inferred:
        "task": None,
        "last_verified_source": None,
        "evidence_receipts": [],
        "unresolved_outcomes": [],
        "next_action": None,
        "stop_reason": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agent", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-browser", action="store_true")
    parser.add_argument("--receipt", type=Path, help="write a re-entry packet to this path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()

    claims = load_claims(root, args.agent)
    mine = [p for c in claims for p in c["files"]]
    other_agents = {
        p: c["agent"]
        for c in load_json(root, "docs/project/agent-claims.json")["claims"]  # type: ignore[index]
        if c["agent"] != args.agent
        for p in c["files"]
    }

    violations: list[str] = list(check_capabilities(args.require_browser))
    notes: list[str] = []
    entries = parse_status(root)
    staged = {
        t for t in git(root, "diff", "--cached", "--name-only", "-z").decode("utf-8", "surrogateescape").split("\0") if t
    }

    for entry in entries:
        path = str(entry["path"])
        if entry["untracked"]:
            if path in staged:
                if not matches(path, mine):
                    violations.append(f"undeclared untracked addition staged: {path}")
            else:
                notes.append(f"untracked, untouched (cannot become evidence silently): {path}")
            continue
        if not matches(path, mine):
            owner = other_agents.get(path) or next(
                (a for pat, a in other_agents.items() if fnmatch.fnmatch(path, pat)), None
            )
            if owner:
                notes.append(f"changed by declared claim {owner!r} - preserved, not a violation: {path}")
            else:
                violations.append(f"changed outside declared scope and undeclared by any claim: {path}")
        if "R" in str(entry["xy"]) and entry.get("original"):
            original = str(entry["original"])
            if not matches(original, mine):
                violations.append(f"rename moves a path outside scope: {original} -> {path}")
        full = root / path
        if full.is_symlink() and not full.resolve().is_relative_to(root):
            violations.append(f"symlink escapes the repository: {path}")

    for path in staged:
        if not matches(path, mine) and path not in {str(e["path"]) for e in entries}:
            violations.append(f"staged outside declared scope: {path}")

    migration_violations, migration_notes = check_migrations(root, entries)
    violations.extend(migration_violations)
    notes.extend(migration_notes)

    if args.receipt:
        receipt = build_receipt(
            root, args.agent, claims, mine, entries, violations, notes, other_agents
        )
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"receipt written: {args.receipt}")

    # Violations always print. --quiet suppresses notes only: a mode that hides the
    # failure list would make a failing check look like a silent pass.
    if not args.quiet:
        for note in notes:
            print(f"note  {note}")
    for violation in violations:
        print(f"FAIL  {violation}")
    print(
        f"{'FAIL' if violations else 'OK'}  guardrails for {args.agent!r} "
        f"({len(mine)} scope pattern(s), {len(entries)} changed path(s))"
    )
    return EXIT_VIOLATION if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
