# Preset guardrails — implementation design

**Status:** design only. Nothing in the Harness or the installed preset has been changed. This document exists so
the change can be reviewed, versioned and tested *before* anyone touches a live preset.

**Source:** `CONSTITUTIONAL_BUILDER_REVIEW_2026-09-12.md` (the review). This document says what implementing its
recommendations actually looks like.

The work splits cleanly. **Part A is Harness-side** — authority-bearing, outside this lane, owner-gated.
**Part B is lane-side** — buildable here today, and it is the half that needs no Harness change to be useful.

---

## Part A — Harness-side changes

Each row: the finding, the file and anchor, the change, and **the test that proves it** (a change without a test
is another prose instruction).

| # | Anchor | Change | Proof |
|---|---|---|---|
**1a** Authority capsule | `agent.cordis.yml` context-gate section (≈L123–124: `complete: true`, `includeRuntimeContext: false`) | Drop blanket complete-prompt / context suppression. Replace with an explicit allowlist of required sections. | Assemble the preset's system prompt and assert the emitted text contains `persona`, `plan:policy`, the runtime policy snapshot and the instruction capsule. Fails today. |
**1b** Instruction wording | `instruction-hint.mjs:239–242` ("not task instructions", "never depends on them") | Replace with precedence-aware wording: accepted project instructions **are** requirements under the governing precedence rules. | Assert the hint text no longer carries the disclaimer, and that a seeded session treats an AGENTS rule as binding in a fixture task. |
**2** Re-entry gate | `context-gate.mjs:156–211` | After `compaction/end` (also on resume, preset/model change, HEAD movement): do not strip instruction/context messages. Inject a **re-entry packet** and withhold write tools until its checks are satisfied. Make the instruction hint once per *epoch*, not once per session. | Synthetic compaction: assert (a) the packet is present, (b) `write`/`edit`/`bash`-mutation are absent until the packet validates, (c) a changed instruction version refreshes the hint. |
**3** Seed hygiene | `prefab-session-seed.mjs:297–315,385–400`; `template.jsonl` | Drop the foreign reminders (Windows rules, old `available_skills` block). Rebuild instruction and skill context from the current registry. Label retained examples as examples. | Render a seed for a synthetic workspace: assert no Windows reminder, no stale catalog, and that instruction text matches the current AGENTS content hash. |
**4** Boundary unification | `agent.cordis.yml:242–256` (`str_replace_editor` isolated behind `dsh-fs-local`) | Route every write-capable tool through the same filesystem/permission boundary, and add a **startup check**: workspace root must equal the configured lane and the branch must match, else refuse. | Negative tests: wrong cwd, `../` path escape, out-of-lane absolute path, stale HEAD, another writer's claim. **This is the one with a recorded real violation** (an earlier session wrote into a tree outside the lane). |
**5** Evidence-bound completion | preset bootstrap + Ralph config | One slice per cycle; declared aggregate budget (time/tokens, children included); bounded retry; no-progress stop; and a checkpoint that **cites the artifact** (path, exit code, SHA) for each claim. | A run producing confident prose with no executed command cannot reach `complete`; a non-zero exit cannot reach `complete`; an owner stop mid-slice yields a usable checkpoint. |
**6** Operating packet | preset `README.md` + persona bootstrap | Correct the preset name and scope; reference documents by exact path (`docs/project/...`) at explicit versions; add the UI data-density and device cases (long titles, large/unknown amounts, many same-day events, WebKit/Safari, the owner's iPhone Air). | Assert every referenced path resolves, and that referenced document versions match the working tree. |
**7** Recoverability | preset packaging | Version the preset source *in the canonical project*, install through a reviewed diff plus backup, never overwrite a live preset mid-session; expose a queryable version marker. | Install produces a diff artifact and a backup; the version marker is readable at startup. |

**Ordering (revised):** `1a+1b+2 together → 4 → 5 → 3 → 6 → 7`.
1 and 2 are one fix — both are "authority does not survive," one at assembly and one after compaction. Fixing
one without the other leaves the hole (validate against stripped constraints, or strip them after validating).
#4 comes next because it is the only one with a **recorded** out-of-lane write. #3 wastes context but cannot cause
an out-of-scope mutation, so it ranks below the safety items.

---

## Part B — Lane-side, buildable now

This half needs no Harness change. It is the mechanism that makes claims checkable *in this repository*.

### B1. The claims manifest — `docs/project/agent-claims.json`

Declared scope, machine-readable, one entry per active agent:

```json
{
  "claims": [
    {
      "agent": "builder",
      "files": ["docs/project/*", "tests/test_capture_contract.py"],
      "base_sha": "4bcbcc7",
      "since": "2026-09-12T21:40:00-04:00",
      "note": "docs and capture-contract only; dial/Today untouched"
    }
  ]
}
```

### B2. The checker — `scripts/check_guardrails.py`

Small, and only things it can actually enforce. It does **not** try to attribute uncommitted changes to an agent
(`git status` cannot do that); it enforces *declared scope* instead.

```python
#!/usr/bin/env python3
"""Fail loudly when a change steps outside its declared scope.

Enforces what is enforceable: declared scope, frozen migrations, staged-diff containment,
baseline hashes for undeclared files, and the verification interpreter. It deliberately does
NOT guess authorship from `git status`.
"""
from __future__ import annotations
import argparse, fnmatch, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = "meridian/migrations/"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def declared(agent: str) -> tuple[list[str], str]:
    data = json.loads((ROOT / "docs/project/agent-claims.json").read_text())
    mine = [c for c in data["claims"] if c["agent"] == agent]
    if not mine:
        sys.exit(f"no claim declared for {agent!r} - add one before editing")
    return mine[0]["files"], mine[0]["base_sha"]


def in_scope(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def changed(include_staged_only: bool = False) -> list[str]:
    args = ["diff", "--name-only", "--cached"] if include_staged_only else ["status", "--porcelain"]
    if include_staged_only:
        return [p for p in git(*args).split("\n") if p]
    out = []
    for line in git(*args).split("\n"):
        if not line.strip() or line.startswith("??"):
            continue                      # untracked files are reported, not policed (see --report-untracked)
        out.append(line[3:].strip())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--report-untracked", action="store_true")
    args = ap.parse_args()
    patterns, base_sha = declared(args.agent)
    failures: list[str] = []

    # 1. declared scope covers tracked modifications
    for path in changed():
        if not in_scope(path, patterns):
            failures.append(f"modified outside declared scope: {path}")

    # 2. migrations are frozen once shipped
    if git("rev-parse", "HEAD").strip() != base_sha:
        for path in changed():
            if path.startswith(MIGRATIONS) and Path(path).suffix == ".sql":
                failures.append(f"shipped migration modified: {path} (ship a new migration)")

    # 3. nothing staged outside scope
    for path in changed(include_staged_only=True):
        if not in_scope(path, patterns):
            failures.append(f"staged outside declared scope: {path}")

    # 4. baseline hashes: nothing undeclared drifted
    baseline = ROOT / "docs/project/guardrail-baseline.json"
    if baseline.exists():
        recorded = json.loads(baseline.read_text())
        for path, digest in recorded.items():
            if in_scope(path, patterns):
                continue                  # declared files are allowed to change
            full = ROOT / path
            if full.exists() and hashlib.sha256(full.read_bytes()).hexdigest() != digest:
                failures.append(f"undeclared drift: {path}")

    if args.report_untracked:
        for line in git("status", "--porcelain").split("\n"):
            if line.startswith("??"):
                print(f"note: untracked {line[3:].strip()}")

    for f in failures:
        print(f"FAIL  {f}")
    print(f"{'FAIL' if failures else 'OK'}  guardrails for {args.agent!r} "
          f"({len(patterns)} scope pattern(s), base {base_sha[:7]})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### B3. The re-entry packet — `docs/project/REENTRY.md`

The lane-side half of finding 2: what an agent must establish before its first mutation, and where to write it so
the next agent can check it rather than trust it.

```
repo/branch:            simplecrew-latest / feat/meridian-implementation
HEAD at entry:          <sha>
task (one line):
declared scope:         <patterns>            (mirrors agent-claims.json)
constraints version:    <sha of AGENTS.md + MERIDIAN_DECISIONS.md at entry>
last verified commit:   <sha + what was verified + how>
unresolved outcomes:    <failed/uncertain writes, open findings>
next action (exactly one):
```

### B4. Tests — `tests/test_check_guardrails.py`

Cover: in-scope change passes; out-of-scope tracked change fails; a modified `meridian/migrations/*.sql` fails;
staging outside scope fails; undeclared file drift fails; a missing claim exits with a clear message. Run in a
temp clone so the real tree is never mutated.

---

## What proves the whole thing works

The review's validation list, kept verbatim as the acceptance gate:

1. Startup/resume/compaction/preset-switch preserve current instructions and plan-mode rules **before** writes.
2. Newer instructions replace stale versions without duplicate message IDs or foreign reminders.
3. All editing paths enforce the same boundary; wrong-workspace and stale-claim cases fail.
4. Passing-looking prose without actual verification cannot complete a task.
5. Owner stop, provider quota failure and process interruption preserve a usable checkpoint.
6. On-demand tools and memory retrieval still work; no unnecessary model calls are added.
7. **One bounded, authorized real task** compares usefulness, correctness and total usage against the current
   preset before wider adoption.

Item 7 is the one that matters most, and this session is the motivating data point: an unmodified, persona-only
preset produced three over-claims and two garbled post-compaction messages while consuming a very large budget.

---

## Boundary

Part A touches `/Users/stephenwest/.dsh/.agent-presets/meridian-constitutional-builder/` and the Harness
packages — **outside this lane and outside this agent's authority**. It needs an explicit grant, and a session
whose lane that is (the review correctly changed nothing).

Part B is in-lane and unblocked. It is also the smaller half, and it is useful on its own: declared scope plus a
checker plus a re-entry packet would have caught several of tonight's failures — a stale patch left in another
agent's directory, a commit touching files outside the slice, and an unverified CSS change premised on a bad
measurement.
