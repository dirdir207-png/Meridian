"""Every Crew-mutating route must go through the governed pipeline — a ratchet, not a wish.

Why this test exists (2026-09-25). An audit found that the governed pipeline is real — 17 action types, 16 with
readback verifiers, `retry_allowed: False` on every failure — while a SECOND write surface sits in `app.py`
firing raw Crew GraphQL mutations with live credentials, reachable from shipped UI, guarded only by
`@login_required`. Nothing in this repository asserted the property the constitution depends on: that every
route which can mutate the provider goes through `meridian/write_routing.py` and the constrained executor.

It is the failure mode the harness lane named on 2026-09-25: **a control off the code path is decoration**, and
**a gate you have only ever seen approve is untested**. The I.1 envelope's `tools`/`Budget` have the same shape —
declared, never consulted at execution.

WHAT THIS IS. A RATCHET, deliberately. It cannot fail today: the ungoverned routes exist and are declared below.
It fails the moment a NEW route mutates Crew without the pipeline, and it fails if one of the declared items is
fixed without updating the declaration — so the list cannot rot into a lie in either direction. That is the form
the harness lane recommended: give the gate a scale floor, design the falsifier, and make the debt visible in the
place where it is incurred.

WHAT IT IS NOT. It is not a fix. Migrating these routes, fencing them, or accepting them as risk is the owner's
decision (D-031, OS-119), and this test asserts nothing about which of those is right. It only refuses to let the
set grow silently.
"""
from __future__ import annotations

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

#: Callables in app.py that reach the provider with a raw mutation, bypassing the pipeline.
RAW_MUTATION_CALLS = {
    "move_money",                 # initiateTransfer via crew_client.execute(is_mutation=True)
    "create_bill_action",         # CreateBill
    "delete_bill_action",         # DeleteBill
    "create_pocket",              # CreateSubaccount
    "delete_subaccount_action",   # DeleteSubaccount
    "set_spend_pocket_action",    # updateVirtualDebitCard / setSpendSubaccount
}

#: Direct mutation execution: `crew_client.execute(..., is_mutation=True)`.
MUTATION_FLAG = "is_mutation"

#: THE KNOWN DEBT, declared so it cannot grow unnoticed. Each entry is a route path whose POST handler reaches a
#: raw mutation without the pipeline. Removing one of these means updating this list in the same change; adding
#: one means the ratchet fires.
KNOWN_UNGOVERNED_MUTATING_ROUTES = {
    # Surfaces found by the 2026-09-25 audit and re-verified in this lane.
    "/api/move-money",
    "/api/create-bill",
    "/api/delete-bill",
    "/api/create-pocket",
    "/api/delete-pocket",
    "/api/set-card-spend",
    "/api/account/autopilot-rules/create",
    "/api/account/autopilot-rules/update",
    "/api/account/autopilot-rules/delete",
    # FOUND BY THIS RATCHET on first run, 2026-09-25 — seventeen routes the human audit did not reach,
    # all of them connector features that call the same raw Crew helpers (`create_pocket`, `move_money`).
    # Verified not to be a false positive: `app.create_pocket` is defined once, and it reaches Crew with
    # `get_crew_headers()` plus a raw `mutation CreateSubaccount`. These predate the Meridian branch
    # (`b5aa020`, 2026-01-15), so they are inherited application code the governed pipeline never absorbed.
    "/api/lunchflow/change-account",
    "/api/lunchflow/create-pocket-with-balance",
    "/api/lunchflow/stop-tracking",
    "/api/lunchflow/sync-balance",
    "/api/manual-cc/create",
    "/api/manual-cc/remove",
    "/api/manual-cc/top-up",
    "/api/simplefin/change-account",
    "/api/simplefin/create-pocket-with-balance",
    "/api/simplefin/disconnect",
    "/api/simplefin/stop-tracking",
    "/api/simplefin/sync-balance",
    "/api/simplefin/sync-now",
    "/api/splitwise/create-pockets",
    "/api/splitwise/disconnect",
    "/api/splitwise/sync-now",
}

#: Routes that legitimately mutate through the pipeline. Presence here is not a bypass.
GOVERNED_MARKERS = {"classify_action", "route_mutation", "route_many", "execute_approved_action"}


def _route_paths(node: ast.FunctionDef) -> list[str]:
    """Every route path this function is decorated with, POST-only."""
    paths = []
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        if not (isinstance(func, ast.Attribute) and func.attr == "route"):
            continue
        if not decorator.args:
            continue
        first = decorator.args[0]
        if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
            continue
        methods = []
        for keyword in decorator.keywords:
            if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                methods = [e.value for e in keyword.value.elts if isinstance(e, ast.Constant)]
        if methods and "POST" not in methods:
            continue
        paths.append(first.value)
    return paths


def _calls_in(node: ast.AST) -> set[str]:
    """Names called anywhere inside a node, plus attribute names, plus keyword names."""
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
            for keyword in child.keywords:
                if keyword.arg:
                    names.add(keyword.arg)
    return names


def _handler_map() -> dict[str, ast.FunctionDef]:
    """Route path -> the function that serves it, plus every helper it calls anywhere in the module.

    Deliberately transitive within app.py: `move_money` is called by the route, and the mutation lives one
    level down, so a body-only scan would miss exactly the defect this guards.
    """
    tree = ast.parse(APP.read_text())
    functions = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    routes: dict[str, ast.FunctionDef] = {}
    for node in functions.values():
        for path in _route_paths(node):
            routes[path] = node
    return routes, functions


def _reaches_raw_mutation(func: ast.FunctionDef, functions: dict[str, ast.FunctionDef], seen=None) -> bool:
    seen = seen or set()
    if func.name in seen:
        return False
    seen.add(func.name)
    called = _calls_in(func)
    if MUTATION_FLAG in called:
        return True
    # The third mechanism, found by the ratchet's own blind spot rather than by design: a direct HTTP POST to
    # the provider's GraphQL endpoint carrying live credentials (`get_crew_headers()` + `requests.post`). The
    # three autopilot-rule routes use this and no `crew_client`, so a detector keyed only on `crew_client` reads
    # them as governed. Two instruments, two blind spots -- the union is what is trustworthy.
    if "get_crew_headers" in called and {"post", "execute"} & called:
        return True
    for name in called & RAW_MUTATION_CALLS:
        return True
    for name in called & set(functions):
        if _reaches_raw_mutation(functions[name], functions, seen):
            return True
    return False


def test_the_ungoverned_mutating_route_set_is_exactly_what_is_declared() -> None:
    routes, functions = _handler_map()
    found = set()
    for path, handler in routes.items():
        called = _calls_in(handler)
        if called & GOVERNED_MARKERS:
            continue
        if _reaches_raw_mutation(handler, functions):
            found.add(path)

    new = sorted(found - KNOWN_UNGOVERNED_MUTATING_ROUTES)
    fixed = sorted(KNOWN_UNGOVERNED_MUTATING_ROUTES - found)
    assert not new, (
        "these routes mutate Crew WITHOUT the governed pipeline and were not declared: "
        f"{new}. Route them through meridian/write_routing.py + the executor, or declare them here with the "
        "reason — but do not let the set grow silently (D-031, OS-119)."
    )
    assert not fixed, (
        f"these routes no longer bypass the pipeline, so the declared debt is stale: {fixed}. "
        "Update KNOWN_UNGOVERNED_MUTATING_ROUTES in the same change that fixed them."
    )


def test_the_ratchet_has_something_to_ratchet() -> None:
    """A gate that has only ever seen an empty set is untested — this proves the detector works.

    The harness lane's rule: design the falsifier, not the confirmation. If the detector silently returned
    nothing, the test above would pass forever while the bypass grew.
    """
    routes, functions = _handler_map()
    assert len(routes) > 20, f"only {len(routes)} POST routes parsed — the route finder is broken, not the app"
    hitting = [p for p, h in routes.items() if _reaches_raw_mutation(h, functions)]
    assert hitting, "the detector found no raw-mutation route at all, which cannot be true while OS-119 is open"
