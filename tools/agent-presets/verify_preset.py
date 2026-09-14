#!/usr/bin/env python3
"""Invariants the Meridian constitutional-builder preset must satisfy.

These are the machine-checkable half of the 2026-09-12 preset review. Each check
is a claim that was true of the *installed* preset before this revision, or a
claim the preset's own comments make about it. A change that reintroduces one of
them fails here rather than in a live session.

Run directly:  python3 tools/agent-presets/verify_preset.py [preset_dir]
Exit 0 = every invariant holds.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DEFAULT_PRESET = Path(__file__).resolve().parent / "meridian-constitutional-builder"

failures: list[str] = []
checks_run = 0


def check(condition: bool, message: str) -> None:
    global checks_run
    checks_run += 1
    if not condition:
        failures.append(message)


def main(preset: Path) -> int:
    cordis = preset / "agent.cordis.yml"
    if not cordis.exists():
        print(f"FAIL: {cordis} not found")
        return 2
    text = cordis.read_text()

    # 1. The persona must not become the whole system prompt. `complete: true`
    #    makes the assembler collapse `sections` to that one section, which
    #    silently drops `plan:policy` and every other section
    #    (packages/core/system-prompt/src/index.ts:621-626).
    check(
        not re.search(r"^\s*complete:\s*true\s*$", text, re.M),
        "persona sets `complete: true`: the assembled prompt collapses to the "
        "persona alone, dropping the plan:policy section and every other section",
    )
    check(
        not re.search(r"^\s*includeRuntimeContext:\s*false\s*$", text, re.M),
        "`includeRuntimeContext: false` empties `contexts`, dropping the runtime "
        "policy snapshot",
    )

    # 2. The instruction hint must treat accepted project instructions as
    #    binding, not as optional reference material.
    hint = (preset / "instruction-hint.mjs")
    check(hint.exists(), "instruction-hint.mjs missing")
    if hint.exists():
        hint_text = hint.read_text()
        check(
            "not task instructions" not in hint_text,
            "instruction-hint still calls the instruction files 'not task instructions'",
        )
        check(
            "never depends on them" not in hint_text,
            "instruction-hint still says the task 'never depends on them'",
        )

    # 3. The admission boundary is wired, and to this lane.
    check(
        "@deepseek-ai/dsh-agent-admission" in text,
        "the agent-admission plugin is not composed, so nothing denies a mutation "
        "before the session has revalidated",
    )
    for key in ("workspace:", "branch:", "constraints:"):
        check(key in text, f"agent-admission config is missing `{key}`")

    # 4. No foreign seed material in the prefab transcript (review finding 3).
    #    Checked by event provenance, not by keyword: the word "Windows" also
    #    appears legitimately in the bash tool's own description and in path
    #    handling, so a keyword scan reports a false positive on a clean preset.
    template = preset / "template.jsonl"
    check(template.exists(), "template.jsonl missing")
    if template.exists():
        records = [json.loads(line) for line in template.read_text().splitlines() if line.strip()]
        check(len(records) > 0, "template.jsonl is empty")
        foreign_markers = ("Windows \u6267\u884c\u89c4\u5219", "OpenCode", "available_skills",
                           "yolo", "radxa@")
        for index, record in enumerate(records, 1):
            if record.get("type") != "user/message":
                continue
            source = record["data"].get("source", {})
            text = "".join(b.get("text", "") for b in record["data"].get("content", []))
            if source.get("kind") == "agent-instructions":
                for marker in foreign_markers:
                    check(
                        marker not in text,
                        f"template.jsonl record {index} seeds a foreign instruction block "
                        f"(contains {marker!r})",
                    )
            if source.get("kind") == "skill-catalog":
                check(
                    not source.get("entries"),
                    f"template.jsonl record {index} seeds a skill catalog of "
                    f"{len(source.get('entries') or [])} entries from an unrelated registry",
                )

    # 5. Identity and inventory: the preset declares a name and every file it
    #    references exists.
    meta = preset / "preset.yml"
    check(meta.exists(), "preset.yml missing")
    referenced = set(re.findall(r"name:\s*\./([\w.-]+\.mjs)", text))
    for rel in sorted(referenced):
        check((preset / rel).exists(), f"composed hook {rel} is missing from the preset")

    print(f"checked {checks_run} invariants in {preset}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"\n{len(failures)} invariant(s) violated")
        return 1
    print("PASS: every preset invariant holds")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PRESET
    raise SystemExit(main(target))
