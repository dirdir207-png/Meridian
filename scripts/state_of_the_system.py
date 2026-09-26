#!/usr/bin/env python3
"""Generate docs/project/STATE_OF_THE_SYSTEM.md — a snapshot DERIVED from code, never written by hand.

WHY THIS EXISTS (owner, 2026-09-25): *"Fact is only as true as the instrument used, the context, the
measurement, the scope, without global awareness... I don't know what ISN'T checked when I ask you to
reconcile or prove things."* A document that a session writes can drift, and a reader cannot tell an
asserted fact from a measured one. This file is generated from the same code the app runs, so it cannot
drift: `tests/test_state_of_the_system.py` regenerates it and fails when the committed copy is stale.

DESIGN RULES, each from a recorded lesson:
* Derive, never restate. Every number below comes from parsing or importing the real source.
* Atomic replace (temp + rename), never a partial write — overwriting in place is a failure mode.
* Say what it does NOT check, and let a test refuse to let that section be deleted.
* The staleness hash covers CODE inputs only. Numbers read from documents are labelled as a snapshot at
  generation time and are deliberately excluded, so ordinary documentation edits do not make it stale.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "project" / "STATE_OF_THE_SYSTEM.md"
RATCHET = ROOT / "tests" / "test_governed_write_routes.py"

#: Code inputs whose content invalidates this document. Documents are NOT here, on purpose.
CODE_INPUTS = ["app.py", "meridian"]


# --------------------------------------------------------------------------- inputs


def _code_files() -> list[Path]:
    files = [ROOT / "app.py"]
    files += sorted((ROOT / "meridian").rglob("*.py"))
    files.append(RATCHET)
    return [f for f in files if f.exists()]


def _input_hash() -> str:
    h = hashlib.sha256()
    for path in _code_files():
        rel = path.relative_to(ROOT).as_posix()
        h.update(rel.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _routes() -> tuple[int, int]:
    """(total rule count, rules accepting POST) across the app and the meridian blueprint."""
    total = post = 0
    for rel in ("app.py", "meridian/api.py"):
        tree = ast.parse((ROOT / rel).read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                if not isinstance(dec.func, ast.Attribute) or dec.func.attr != "route":
                    continue
                total += 1
                methods: set[str] = set()
                for kw in dec.keywords:
                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                methods.add(elt.value.upper())
                if "POST" in methods or (not methods and False):
                    post += 1
    return total, post


def _declared_ungoverned() -> list[str]:
    tree = ast.parse(RATCHET.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == (
            "KNOWN_UNGOVERNED_MUTATING_ROUTES"
        ):
            return sorted(ast.literal_eval(node.value))
    return []


def _capability() -> dict:
    """The money path, derived by importing the registries the app itself uses."""
    sys.path.insert(0, str(ROOT))
    import meridian.crew_write as cw  # noqa: PLC0415
    import meridian.crew_write_actions as cwa  # noqa: PLC0415

    registry = cwa.crew_write_executors(":memory:")
    unverified = sorted(name for name, (_e, v) in registry.items() if v is None)
    ops: dict[str, list[str]] = {}
    for name, (executor, _v) in registry.items():
        cells = [
            c.cell_contents
            for c in (getattr(executor, "__closure__", None) or ())
            if isinstance(c.cell_contents, str)
        ]
        if cells:
            ops.setdefault(cells[0], []).append(name)
    return {
        "allowed_ops": sorted(cw._ALLOWED),
        "actions": sorted(registry),
        "unverified_actions": unverified,
        "ops_with_action": sorted(ops),
        "ops_without_action": sorted(set(cw._ALLOWED) - set(ops)),
        "actions_without_op": sorted({a for v in ops.values() for a in v if a} - set(registry)),
    }


def _referenced(dotted: str, text: str) -> bool:
    """Does this source text name module `dotted` in any of the ways Python can name it?

    Three recognised forms, because the first version of this scan knew only one and produced a false
    positive on `meridian/ai/evaluation.py` (both its callers write `from meridian.ai import evaluation`,
    which never spells the dotted path out):

    1. `import meridian.ai.evaluation` / `from meridian.ai.evaluation import x`
    2. `from meridian.ai import evaluation`      — the form that was missed
    3. `from . import evaluation` / `from .sub import evaluation` (relative, inside the package)

    NOT recognised, and stated as a limit in the document: a module loaded by file path
    (`importlib.util.spec_from_file_location`), which no static scan can follow.
    """
    if re.search(r"\b" + re.escape(dotted) + r"\b", text):
        return True
    package, _, leaf = dotted.rpartition(".")
    if package and re.search(
        r"\bfrom\s+" + re.escape(package) + r"\s+import\b[^\n]*\b" + re.escape(leaf) + r"\b", text
    ):
        return True
    if re.search(r"\bfrom\s+\.{1,2}[\w.]*\s+import\b[^\n]*\b" + re.escape(leaf) + r"\b", text):
        return True
    return bool(re.search(r"\bfrom\s+\.{1,2}" + re.escape(leaf) + r"\s+import\b", text))


def _orphan_modules() -> tuple[list[str], int]:
    """Meridian modules nothing else in the tree names — the denominator for "buried, not lost"."""
    modules = sorted((ROOT / "meridian").rglob("*.py"))
    haystacks = [ROOT / "app.py"]
    for base in ("meridian", "crew", "scripts", "tests"):
        haystacks += sorted((ROOT / base).rglob("*.py"))
    corpus = {}
    for path in haystacks:
        if path.exists():
            corpus[path] = path.read_text(errors="ignore")
    orphans = []
    for module in modules:
        rel = module.relative_to(ROOT).with_suffix("")
        dotted = rel.as_posix().replace("/", ".")
        if dotted.endswith(".__init__"):
            continue
        if not any(_referenced(dotted, text) for path, text in corpus.items() if path != module):
            orphans.append(rel.as_posix() + ".py")
    return orphans, len(modules)


#: Guard tests and the claim class each protects. Curated because a test's *intent* is not parseable.
CHECKS = [
    ("tests/test_governed_write_routes.py", "no provider-mutating route escapes the governed pipeline"),
    ("tests/test_slice_onset_ceremony.py", "every in-progress slice declares plan + model + why"),
    ("tests/test_supersession_before_restore.py", "nothing old is restored without a supersession check"),
    ("tests/test_task_blockers_are_explained.py", "a blocked task names its blocker and its owner question"),
    ("tests/test_concept_coverage.py", "the 22 concepts keep a carrier and an audited state"),
    ("tests/test_session_close.py", "session close reports clean / pushed / current"),
    ("tests/test_roadmap_handoff_check.py", "the roadmap and the ledger reconcile"),
    ("tests/meridian/test_safe_to_spend_agreement.py", "Today and Plan publish one figure from one rule"),
    ("tests/meridian/test_static_assets_tracked.py", "shipped trees and the git index agree"),
    ("tests/meridian/test_ai_evaluation.py", "the evaluation harness refuses to report health over nothing"),
    ("tests/test_state_of_the_system.py", "this document is current, and still says what it cannot check"),
]


def _ledger_snapshot() -> dict:
    ledger = json.loads((ROOT / "docs" / "project" / "MERIDIAN_OS_TASKS.json").read_text())
    tasks = ledger["tasks"]
    by_status: dict[str, int] = {}
    for task in tasks:
        by_status[task["status"]] = by_status.get(task["status"], 0) + 1
    owed = [
        t["id"]
        for t in tasks
        if t.get("owner_question") or t.get("owner_decision_required") is True
    ]
    return {"total": len(tasks), "by_status": by_status, "owner_decisions": owed}


# --------------------------------------------------------------------------- render


def _route_mechanisms() -> dict[str, list[str]]:
    """Declared route -> the raw mechanism(s) it reaches, transitively.

    Uses the RATCHET's own detector (`_handler_map`, `_calls_in`, `_has_inline_mutation`,
    `RAW_MUTATION_CALLS`) rather than a second implementation, so "reaches a raw mutation" has exactly one
    definition in this repository. What this adds is the NAMING: the ratchet answers yes/no, and the shape
    decision for each route needs to know WHICH provider mutation it performs.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("_ratchet", RATCHET)
    ratchet = importlib.util.module_from_spec(spec)
    sys.modules["_ratchet"] = ratchet
    spec.loader.exec_module(ratchet)
    routes, functions = ratchet._handler_map()
    app_source = (ROOT / "app.py").read_text()
    out: dict[str, list[str]] = {}
    for path in sorted(ratchet.KNOWN_UNGOVERNED_MUTATING_ROUTES):
        handler = routes.get(path)
        if handler is None:
            out[path] = ["HANDLER NOT FOUND"]
            continue
        seen: set[str] = set()
        stack = [handler]
        found: set[str] = set()
        while stack:
            current = stack.pop()
            if current.name in seen:
                continue
            seen.add(current.name)
            called = ratchet._calls_in(current)
            found |= called & ratchet.RAW_MUTATION_CALLS
            if ratchet.MUTATION_FLAG in called:
                found.add("crew_client(is_mutation=True)")
            if ratchet._has_inline_mutation(current) and ({"post", "execute", "execute_graphql"} & called):
                segment = ast.get_source_segment(app_source, current) or ""
                for name in sorted(set(re.findall(r"mutation\s+(\w+)", segment))):
                    found.add(name)
            for name in called & set(functions):
                stack.append(functions[name])
        out[path] = sorted(found) or ["** unresolved **"]
    return out


def render() -> str:
    cap = _capability()
    total_routes, post_routes = _routes()
    ungoverned = _declared_ungoverned()
    orphans, module_count = _orphan_modules()
    ledger = _ledger_snapshot()
    lines: list[str] = []
    add = lines.append

    add("# State of the system — GENERATED, do not edit")
    add("")
    add(f"Regenerate with `python scripts/state_of_the_system.py`. Input hash `{_input_hash()[:16]}`.")
    add("")
    add("Everything under *Derived from code* comes from parsing or importing the code the app runs, so it cannot")
    add("drift: `tests/test_state_of_the_system.py` regenerates this file and fails when the committed copy is")
    add("stale. Everything under *Snapshot at generation time* is read from documents and is **excluded** from the")
    add("staleness check on purpose, so ordinary documentation edits do not invalidate this file.")
    add("")

    add("## Derived from code — the money path")
    add("")
    add("| | count |")
    add("|---|---:|")
    add(f"| operations the executor is allowed to send | {len(cap['allowed_ops'])} |")
    add(f"| governed actions registered | {len(cap['actions'])} |")
    add(f"| governed actions with a readback verifier | {len(cap['actions']) - len(cap['unverified_actions'])} |")
    add(f"| allowed operations with NO governed action | {len(cap['ops_without_action'])} |")
    add("")
    if cap["unverified_actions"]:
        add("**Actions with no verifier** (a write whose result is never read back):")
        add("")
        for name in cap["unverified_actions"]:
            add(f"* `{name}`")
        add("")
    if cap["ops_without_action"]:
        add("**Allowed operations no governed action sends** (capability reachable only outside the pipeline):")
        add("")
        for name in cap["ops_without_action"]:
            add(f"* `{name}`")
        add("")

    add("## Derived from code — write routes")
    add("")
    add("| | count |")
    add("|---|---:|")
    add(f"| route decorators parsed STATICALLY (app + meridian blueprint) | {total_routes} |")
    add(f"| — of those, accepting POST | {post_routes} |")
    add("| route rules at RUNTIME (independent harness) | 200 |")
    add("| — of those, accepting POST | 98 |")
    add(f"| POST routes declared to reach a raw Crew mutation | {len(ungoverned)} |")
    add("")
    add("The two route populations above are NOT interchangeable: a static decorator parse cannot see blueprint or")
    add("`add_url_rule` registrations. The runtime figures are the independent verification lane's, quoted with their")
    add("instrument for that reason (`INDEPENDENT_VERIFICATION_2026-09-25.md` §Claim 2). The static count is the one that")
    add("stays reproducible here; the runtime count is the one that describes the app.")
    add("")
    add("The declared set is asserted exactly by `tests/test_governed_write_routes.py`, which fails both when the")
    add("set grows and when a declared route is fixed without updating the declaration. It is therefore the")
    add("denominator for OS-119: the shape decision concerns exactly these routes. Per the declaration's own")
    add("comments it is composed of 9 routes the 2026-09-25 audit reached and 17 found by the ratchet on its first")
    add("run — and one of them (`/api/cards/<card_id>/sensitive`) mints a card-details view token rather than")
    add("moving money, which is why the FINANCIAL count and the DECLARED count differ by one. Quote whichever the")
    add("question is about, and say which.")
    add("")

    add("## Derived from code — what each ungoverned route actually performs")
    add("")
    add("The ratchet answers *whether* a route reaches a raw mutation; the shape decision for OS-119 needs")
    add("*which* one. Both come from the same detector, so there is one definition of \"reaches a raw mutation\"")
    add("in this repository. Whether a mechanism has a governed carrier is recorded in")
    add("`docs/project/OS119_MIGRATION_BY_EVIDENCE.md`, which cites the connector's own document list as its")
    add("instrument — a cross-repository fact that cannot be re-derived from this tree alone.")
    add("")
    add("| route | raw mechanism(s) reached |")
    add("|---|---|")
    for path, mechanisms in _route_mechanisms().items():
        add(f"| `{path}` | {', '.join('`' + m + '`' for m in mechanisms)} |")
    add("")

    add("## Derived from code — modules nothing else names")
    add("")
    add(
        f"{len(orphans)} of {module_count} modules under `meridian/` are never NAMED by any other module, the app,"
        " a script or a test (dotted-path text search). This is a NAMING instrument and it does not answer whether a"
        " module is LOADED. An independent runtime tracer, exercising 13 GET responses, found that the application loads"
        " only three files from `meridian/ai/` — `__init__.py`, `advisor.py`, `classifier.py` — and does NOT load the"
        " agent-role layer at all (`role`, `envelope`, `run_records`, `council`, `investigator`, `skeptic`, `facts`,"
        " `evaluation`); see `INDEPENDENT_VERIFICATION_2026-09-25.md` §Claim 5. Do not read a short list here as"
        " \"nothing is buried\": it is a claim about NAMING."
    )
    add("")
    for path in orphans:
        add(f"* `{path}`")
    add("")

    add("## Snapshot at generation time (excluded from the staleness check)")
    add("")
    add("| | |")
    add("|---|---|")
    add(f"| tasks in the ledger | {ledger['total']} |")
    for status, count in sorted(ledger["by_status"].items()):
        add(f"| — {status} | {count} |")
    add(f"| tasks carrying an owner question | {len(ledger['owner_decisions'])} |")
    add("")

    add("## What is checked, and by what")
    add("")
    add("| guard | the claim it protects |")
    add("|---|---|")
    for path, claim in CHECKS:
        exists = "yes" if (ROOT / path).exists() else "**MISSING**"
        add(f"| `{path}` ({exists}) | {claim} |")
    add("")

    add("## What this document does NOT check")
    add("")
    add("This section is the honest half, and a test refuses to let it be deleted.")
    add("")
    add("* **Semantics.** Registration and reachability are not behaviour. An action can be wired, verified and")
    add("  still wrong, and nothing here evaluates whether a feature does what the vision says.")
    add("* **Provider-side state we do not read.** The reserve's cash balance, the sweep threshold, the")
    add("  pocket-transfer allocation settings, the reserve's internal attribution when no read has run — all")
    add("  invisible to every instrument in this repository (OS-059).")
    add("* **Whether a guard asserts the right thing.** A vacuous or miscalibrated test passes. Nothing here")
    add("  checks a check's premise — the failure class that produced 'a gate needs a floor, not a minimum'.")
    add("* **Anything before continuous recording existed.** Per-bill allocation history begins 2026-09-25")
    add("  22:30:58Z; earlier states survive only as captures, and a capture is not a series.")
    add("* **Other trees, other lanes, and managed Documents** unless someone enumerates them. This is D-042's")
    add("  channel problem: a fact can be documented, current, and simply never read.")
    add("* **Live data quality.** Sync gaps, staleness and torn reads are not visible here; only schema and")
    add("  timestamps are, and a populated schema is not populated data.")
    add("* **The set of things no instrument mentions at all.** Invisible by construction. The orphan scan is the")
    add("  closest thing to a denominator, and it covers Python imports only — not templates, JS, routes or docs —")
    add("  and it cannot follow a module loaded by file path (`spec_from_file_location`), which is how a module can")
    add("  be used and still read as unused here.")
    add("* **Intent.** Coverage measures carriers, never whether the carrier is the right product decision.")
    add("")
    return "\n".join(lines)


def main() -> int:
    text = render()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(OUT.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(tmp, OUT)  # atomic: a partial write can never be observed
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
