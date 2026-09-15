"""C4 completeness: the write registry cannot gain or lose verification silently.

`docs/project/write-coverage.json` is the recorded verification decision for
every registered Crew write action type. These tests make it enforced rather
than descriptive:

  * every registered type must appear in the manifest (a new operation cannot be
    added without recording whether anything verifies it);
  * every manifest entry must match the live registry (a type cannot gain or lose
    a verifier without the manifest changing too);
  * every readback entry must name a check string that actually exists in
    `meridian/crew_write_actions.py`, so the receipt's `check` field is a
    documented contract rather than free text;
  * a `none` entry must not claim a check name.

No provider call, database or credential is involved.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/project/write-coverage.json"
REGISTRY_SOURCE = ROOT / "meridian/crew_write_actions.py"
APP_SOURCE = ROOT / "app.py"

STATUSES = {"readback", "none"}


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _registry(tmp_path):
    from meridian.crew_write_actions import crew_write_executors

    return crew_write_executors(str(tmp_path / "write-coverage.db"))


def test_manifest_is_well_formed():
    manifest = _manifest()

    assert manifest["schema_version"] == 1
    assert manifest["source_of_truth"] == "meridian.crew_write_actions.crew_write_executors"
    assert set(manifest["status_vocabulary"]) == STATUSES

    entries = manifest["entries"]
    assert entries, "the manifest must record at least one action type"

    seen = set()
    for entry in entries:
        assert entry["type"], "every entry names an action type"
        assert entry["type"] not in seen, f"duplicate manifest entry: {entry['type']}"
        seen.add(entry["type"])
        assert entry["verification"] in STATUSES, f"{entry['type']} has an unknown status"
        if entry["verification"] == "readback":
            assert entry.get("check"), f"{entry['type']} must name its receipt check"
            assert entry.get("note"), f"{entry['type']} must explain what it confirms"
        else:
            assert not entry.get("check"), (
                f"{entry['type']} is unverified and must not claim a check name"
            )
            assert entry.get("reason"), (
                f"{entry['type']} must record why no readback exists"
            )


def test_every_registered_type_is_recorded(tmp_path):
    """A new write operation cannot be added without a recorded decision."""
    registry = _registry(tmp_path)
    recorded = {entry["type"] for entry in _manifest()["entries"]}

    unrecorded = sorted(set(registry) - recorded)
    assert not unrecorded, (
        "these action types are registered but have no recorded verification "
        f"decision in docs/project/write-coverage.json: {unrecorded}"
    )


def test_no_manifest_entry_is_stale(tmp_path):
    """A recorded type that is no longer registered must not linger."""
    registry = _registry(tmp_path)
    recorded = {entry["type"] for entry in _manifest()["entries"]}

    stale = sorted(recorded - set(registry))
    assert not stale, (
        "docs/project/write-coverage.json records types that are no longer "
        f"registered: {stale}"
    )


def test_recorded_status_matches_the_live_registry(tmp_path):
    """The manifest cannot drift from the code in either direction."""
    registry = _registry(tmp_path)

    for entry in _manifest()["entries"]:
        execute, verifier = registry[entry["type"]]
        assert callable(execute), f"{entry['type']} has no callable executor"
        if entry["verification"] == "readback":
            assert verifier is not None, (
                f"{entry['type']} is recorded as verified by readback but the "
                "registry registers no verifier"
            )
        else:
            assert verifier is None, (
                f"{entry['type']} is recorded as unverified but the registry "
                "registers a verifier; update the manifest"
            )


def test_readback_check_names_exist_in_the_source():
    """The receipt's `check` value is a contract, not free text."""
    source = REGISTRY_SOURCE.read_text(encoding="utf-8")

    for entry in _manifest()["entries"]:
        if entry["verification"] != "readback":
            continue
        check = entry["check"]
        assert f'"{check}"' in source, (
            f"{entry['type']} records check '{check}', which does not appear in "
            "meridian/crew_write_actions.py"
        )


def test_readback_types_are_the_six_that_were_hardened():
    """Pin the coverage this lane actually achieved, so it cannot quietly shrink."""
    verified = {
        entry["type"]
        for entry in _manifest()["entries"]
        if entry["verification"] == "readback"
    }

    assert verified == {
        "update_crew_bill",
        "update_crew_bill_reserve_settings",
        "create_crew_bill",
        "create_crew_pocket",
        "delete_crew_pocket",
        "archive_crew_bill",
    }


def test_allowed_but_unexecutable_types_are_recorded(tmp_path):
    """An allowed type with no executor must be a recorded gap, not a surprise.

    `update_crew_virtual_card` is in `ActionStore.allowed_types` and has no
    executor, so an approved action fails closed with `no_executor`. That is
    safe but it is an owner-visible dead end, and it must stay documented until
    it is either implemented or removed from the allowed set.
    """
    registry = _registry(tmp_path)
    manifest = _manifest()
    recorded_gaps = {entry["type"] for entry in manifest["allowed_without_executor"]}

    app_source = APP_SOURCE.read_text(encoding="utf-8")
    assert '"update_crew_virtual_card"' in app_source, (
        "update_crew_virtual_card is no longer listed in app.py; reconcile the "
        "recorded gap in docs/project/write-coverage.json"
    )

    # The gap is real: allowed, but absent from the Crew write registry.
    assert "update_crew_virtual_card" not in registry, (
        "an executor now exists for update_crew_virtual_card; remove it from "
        "allowed_without_executor and record its verification decision instead"
    )
    assert "update_crew_virtual_card" in recorded_gaps, (
        "the allowed-without-executor gap is no longer documented"
    )

    for gap in manifest["allowed_without_executor"]:
        assert gap.get("reason"), f"{gap['type']} must record why it is a gap"
        assert gap.get("status") in {"open-gap", "resolved"}, (
            f"{gap['type']} needs an explicit gap status"
        )
        assert gap.get("next_action"), (
            f"{gap['type']} must record what would close it"
        )


def test_engine_level_verifiers_are_recorded():
    """Verifiers registered in app.py are part of the coverage picture."""
    app_source = APP_SOURCE.read_text(encoding="utf-8")

    for entry in _manifest()["engine_level_verifiers"]:
        assert entry["verification"] in STATUSES
        assert entry.get("check"), f"{entry['type']} must name its check"
        assert f'"{entry["check"]}"' in app_source, (
            f"{entry['type']} records check '{entry['check']}', which does not "
            "appear in app.py"
        )


def test_manifest_does_not_duplicate_a_type_across_sections():
    manifest = _manifest()
    registry_types = {entry["type"] for entry in manifest["entries"]}
    engine_types = {entry["type"] for entry in manifest["engine_level_verifiers"]}
    gap_types = {entry["type"] for entry in manifest["allowed_without_executor"]}
    memory_types = {entry["type"] for entry in manifest["memory_action_types"]}

    for left, right in (
        (registry_types, engine_types),
        (registry_types, gap_types),
        (registry_types, memory_types),
        (engine_types, gap_types),
        (engine_types, memory_types),
        (gap_types, memory_types),
    ):
        assert not left & right, f"a type is recorded twice: {sorted(left & right)}"


def _allowed_types_from_source():
    """Read ActionStore.allowed_types out of app.py without importing it.

    Importing app.py would create the real database and a local key file, so the
    allowed set is read statically instead. `MEMORY_ACTION_TYPES` is resolved by
    import because that module is pure definitions and touches no database.
    """
    import ast

    from meridian.memory_actions import MEMORY_ACTION_TYPES

    tree = ast.parse(APP_SOURCE.read_text(encoding="utf-8"))
    literal: list[str] = []
    extra_names: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name != "ActionStore":
            continue
        for keyword in node.keywords:
            if keyword.arg != "allowed_types":
                continue
            value = keyword.value
            parts = []
            if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
                parts = [value.left, value.right]
            else:
                parts = [value]
            for part in parts:
                if isinstance(part, ast.Tuple):
                    for element in part.elts:
                        assert isinstance(element, ast.Constant), (
                            "allowed_types must be a literal tuple for this guard"
                        )
                        literal.append(element.value)
                elif isinstance(part, ast.Name):
                    extra_names.add(part.id)

    assert literal, "ActionStore(allowed_types=...) was not found in app.py"
    assert extra_names <= {"MEMORY_ACTION_TYPES"}, (
        f"unhandled name(s) in allowed_types: {sorted(extra_names)}"
    )
    return set(literal) | set(MEMORY_ACTION_TYPES)


def test_manifest_covers_every_allowed_action_type():
    """Every type the store will accept has a recorded verification decision.

    This is the guard that stops the manifest from becoming another partial
    inventory that merely looks complete: it compares the manifest against the
    actual `allowed_types` in app.py, including the memory action types.
    """
    manifest = _manifest()
    recorded = (
        {entry["type"] for entry in manifest["entries"]}
        | {entry["type"] for entry in manifest["engine_level_verifiers"]}
        | {entry["type"] for entry in manifest["memory_action_types"]}
        | {entry["type"] for entry in manifest["allowed_without_executor"]}
    )
    allowed = _allowed_types_from_source()

    missing = sorted(allowed - recorded)
    assert not missing, (
        "these allowed action types have no recorded verification decision: "
        f"{missing}"
    )
    unknown = sorted(recorded - allowed)
    assert not unknown, (
        f"the manifest records types that are not allowed in app.py: {unknown}"
    )


def test_memory_action_verifiers_match_their_registration(tmp_path):
    """The memory types are verified by local re-read; record and check that."""
    from meridian.memory_actions import asset_executors, contract_executors

    registered = {
        **asset_executors(str(tmp_path / "memory.db")),
        **contract_executors(str(tmp_path / "memory.db")),
    }
    recorded = {entry["type"]: entry for entry in _manifest()["memory_action_types"]}

    assert set(recorded) == set(registered), "memory coverage drifted from the registry"
    for action_type, entry in recorded.items():
        execute, verifier = registered[action_type]
        assert entry["verification"] == "readback"
        assert verifier is not None, f"{action_type} is recorded as verified but has no verifier"

    source = (ROOT / "meridian/memory_actions.py").read_text(encoding="utf-8")
    for entry in recorded.values():
        assert f'"{entry["check"]}"' in source, (
            f"{entry['type']} records check '{entry['check']}', absent from memory_actions.py"
        )


@pytest.mark.parametrize("field", ["unresolved_receipt_rule"])
def test_the_unresolved_rule_is_stated(field):
    """The safety rule the whole slice depends on must be written down."""
    manifest = _manifest()
    assert manifest[field]
    assert "never resubmitted" in manifest[field]
