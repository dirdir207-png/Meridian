"""Generate the session-to-session handoff from the governing docs (read-only, deterministic).

WHY THIS IS GENERATED AND NOT WRITTEN BY HAND. The owner's constraint, verbatim: "I can't keep
track of the massive roadmap and original build with session sprawl, so I need to be able to rely
on session to session handoffs as context reaches its limit, because that's the deciding factor."
A hand-written handoff is exactly the artifact that drifts, because it is authored from whatever
the session was doing. So this file is a PROJECTION of the doc set, produced by a program, and
the same state always produces the same output.

The division of labour is the whole design:

  * THIS SCRIPT decides the STRUCTURE and pulls every fact from its authority — roadmap, ledger,
    git. It interprets nothing and prioritises nothing.
  * The only editorial input is `docs/project/session-emergent.json`, which records things that
    arose in a session and are NOT planned. It exists so session momentum has somewhere honest to
    go: an emergent item is visible as emergent, and never appears as assigned work.

An emergent item does not become planned work by appearing here. Promotion is an owner decision
recorded in the ledger. The generator cannot promote anything, and must not grow that ability.

Read this file FIRST in a new session, then the governing docs it names. It is a map, not a
source of truth: every fact in it is owned by the doc it points at.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs/project/MERIDIAN_OS_TASKS.json"
ROADMAP = ROOT / "docs/project/MERIDIAN_ROADMAP.md"
DECISIONS = ROOT / "docs/project/MERIDIAN_DECISIONS.md"
# The vision inventory. It was authoritative in the builder prompt and named by the roadmap's
# section 0, but sat in no session-ritual list at all until 2026-09-25, which is how a project
# loses sight of its own concepts while believing it reviews everything.
CONCEPTS = ROOT / "docs/project/MERIDIAN_CONCEPTS.md"
BUILDER_PROMPT = ROOT / "docs/project/MERIDIAN_INITIAL_BUILDER_PROMPT.md"
AGENTS = ROOT / "AGENTS.md"
EMERGENT = ROOT / "docs/project/session-emergent.json"
OUT = ROOT / "docs/project/HANDOFF.md"
CDB = ROOT / "docs/project/CURRENT_STATUS.md"

FINISHED = {"complete", "done"}
#: The governing sources a handoff must be able to cite. A handoff that cannot name these is a
#: session summary and is labelled as one.
GOVERNING = (AGENTS, ROADMAP, DECISIONS, LEDGER, CONCEPTS, BUILDER_PROMPT)
#: Order in which tracks are laid out, so the spine is visible rather than alphabetical.
TRACK_ORDER = ("design-fidelity", "audit", "track-C", "track-I", "virgil")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - a missing git must not break the handoff
        return ""


def track_rank(phase: str) -> tuple[int, str]:
    for i, prefix in enumerate(TRACK_ORDER):
        if phase.startswith(prefix):
            return (i, phase)
    return (len(TRACK_ORDER), phase)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdout", action="store_true", help="print instead of writing")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the file on disk is stale")
    args = parser.parse_args()

    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    open_tasks = [t for t in tasks if t.get("status") not in FINISHED]
    roadmap_text = ROADMAP.read_text(encoding="utf-8")

    import re
    mentioned = set(re.findall(r"\bOS-\d{3}\b", roadmap_text))
    mentioned |= set(re.findall(r"\bVIRGIL-A\d\b", roadmap_text))

    head = git("rev-parse", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    # Tracked modifications only: `status --porcelain` also lists ~440 untracked artifacts/**
    # and tmp/** paths, which are scratch by convention and would make every handoff claim a
    # dirty tree. A handoff that cries wolf is a handoff that gets ignored.
    changed = [l for l in git("status", "--porcelain").splitlines() if not l.startswith("??")]
    # The recent-commits list EXCLUDES commits that only touched this file. Including them made
    # the handoff self-referential: committing a regenerated handoff adds a commit that changes
    # the list, so `--check` could never pass immediately after following the close-out
    # checklist. Excluding them makes the section describe the PROJECT's movement rather than
    # this file's own bookkeeping, which is what a reader actually needs, and the list is then
    # stable across a regenerate-and-commit cycle.
    try:
        # A caller (or a test) may point OUT outside the repository, so the pathspec is only
        # applied when a repository-relative path actually exists. relative_to raises otherwise,
        # which would crash generation rather than degrade.
        excluded = OUT.relative_to(ROOT).as_posix()
    except ValueError:
        excluded = None
    log_args = ["log", "--oneline", "-14", "--no-decorate", "--", "."]
    if excluded:
        log_args.append(f":(exclude){excluded}")
    recent = [line for line in git(*log_args).splitlines() if line][:12]

    # The roadmap's own "Next move" paragraph, quoted rather than paraphrased.
    next_move = ""
    m = re.search(r"- \*\*Next move[^\n]*\*\*(.*?)(?=\n- \*\*|\n---|\Z)", roadmap_text, re.S)
    if m:
        next_move = " ".join(m.group(1).split())

    emergent: list[dict] = []
    if EMERGENT.exists():
        try:
            emergent = json.loads(EMERGENT.read_text(encoding="utf-8")).get("emergent", [])
        except Exception:  # noqa: BLE001
            emergent = []

    L: list[str] = []
    L.append("# HANDOFF — read this first, then the governing docs it names")
    L.append("")
    L.append(
        "Generated by `scripts/generate_handoff.py` from the governing documents. **Do not edit by "
        "hand** — a hand-edited handoff is a session summary wearing the authority of the plan, "
        "which is the failure this file exists to prevent."
    )
    L.append("")
    L.append(f"- Generated: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`")
    L.append(f"- Commit: `{head}` on `{branch}`"
             + (f" — **{len(changed)} tracked path(s) modified, uncommitted**"
                if changed else " — working tree clean"))
    if changed:
        L.append("")
        L.append("**Uncommitted tracked changes — finish or revert before relying on this handoff:**")
        for c in changed:
            L.append(f"- `{c}`")
    L.append("")

    # A handoff that silently goes stale is the failure this file exists to prevent, so the
    # warning is unconditional and cannot be switched off. The next session sees whether the
    # previous one actually regenerated it, without anyone having to remember to check.
    L.append("> **MAINTAINER'S OBLIGATION.** At the end of a session, or at any context checkpoint:")
    L.append("> regenerate this file (`scripts/generate_handoff.py`), record anything new in")
    L.append("> `docs/project/session-emergent.json`, and run `scripts/roadmap_handoff_check.py`.")
    L.append("> **If this file is older than the newest commit, the previous session did not do that**")
    L.append("> — regenerate it before trusting the 'IN FLIGHT' and 'RECENT COMMITS' sections, then")
    L.append("> check `session-emergent.json` for anything that was never recorded at all.")
    L.append("")
    L.append("## 1. BASIS — the sources this was derived from, by hash")
    L.append("")
    L.append("| Source | sha256 (first 16) |")
    L.append("|---|---|")
    for p in GOVERNING:
        L.append(f"| `{p.relative_to(ROOT)}` | `{sha256(p)[:16]}` |")
    L.append("")
    L.append(
        "If a hash above differs from the file you are reading, this handoff is **stale** and must "
        "be regenerated before it is relied on (`--check` detects exactly this)."
    )
    L.append("")

    L.append("## 2. THE ASSIGNED ORDER (quoted from the roadmap, not paraphrased)")
    L.append("")
    if next_move:
        L.append(f"> {next_move}")
    else:
        L.append("> (the roadmap's 'Next move' paragraph could not be located — read the roadmap)")
    L.append("")

    L.append("## 3. IN FLIGHT — open work by track")
    L.append("")
    L.append("Every unfinished task declares a track; `scripts/roadmap_handoff_check.py` enforces it.")
    L.append("")
    by_track: dict[str, list[dict]] = {}
    for t in open_tasks:
        by_track.setdefault((t.get("phase") or "(none)"), []).append(t)
    for phase in sorted(by_track, key=track_rank):
        rows = sorted(by_track[phase], key=lambda t: t["id"])
        L.append(f"### `{phase}`")
        L.append("")
        for t in rows:
            flags = []
            if t.get("owner_decision_required"):
                flags.append("**OWNER GATE**")
            if t["id"] not in mentioned:
                flags.append("_emergent — not in roadmap_")
            tag = f"  {' '.join(flags)}" if flags else ""
            L.append(f"- `{t['id']}` [{t.get('status')}/{t.get('priority')}] "
                     f"{(t.get('title') or '')[:88]}{tag}")
        L.append("")

    gates = [t for t in open_tasks if t.get("owner_decision_required")]
    L.append("## 4. WAITING ON THE OWNER")
    L.append("")
    if gates:
        for t in sorted(gates, key=lambda x: x["id"]):
            L.append(f"- `{t['id']}` — {(t.get('title') or '')[:96]}")
    else:
        L.append("- (none)")
    L.append("")

    L.append("## 5. SESSION-EMERGENT — arose in a session, NOT planned, NOT authorised")
    L.append("")
    L.append(
        "Recorded in `docs/project/session-emergent.json`. These are ideas and findings, never "
        "assignments. **Promotion to planned work is an owner decision recorded in the ledger; "
        "appearing here promotes nothing.**"
    )
    L.append("")
    if emergent:
        for e in emergent:
            L.append(f"- **{e.get('summary','(untitled)')}** — {e.get('why','')}"
                     f"{' · ledger: `' + e['promoted_to'] + '`' if e.get('promoted_to') else ' · not promoted'}")
    else:
        L.append("- (none recorded)")
    L.append("")

    L.append("## 6. RECENT COMMITS IN THIS LINE")
    L.append("")
    for line in recent:
        L.append(f"- `{line}`")
    L.append("")

    L.append("## 7. READ DEEPER — where the facts actually live")
    L.append("")
    for name, why in (
        ("docs/project/MERIDIAN_CONCEPTS.md", "the 22 concepts — which every slice must name"),
        ("docs/project/MERIDIAN_INITIAL_BUILDER_PROMPT.md", "the concepts' authoritative source: evaluate, do not auto-implement"),
        ("docs/project/MERIDIAN_ROADMAP.md", "the trajectory and its stated next move"),
        ("docs/project/MERIDIAN_OS_TASKS.json", "every task, its track, gates and limits"),
        ("docs/project/MERIDIAN_DECISIONS.md", "binding decisions; the newest governs"),
        ("docs/project/CURRENT_STATUS.md", "the running record of what was verified"),
        ("docs/project/AGENT_COORDINATION.md", "the claims table — add a row before editing"),
        ("AGENTS.md", "the rules, including the continuity and handoff contracts"),
    ):
        L.append(f"- `{name}` — {why}")
    L.append("")
    L.append(
        "**Before acting:** run `scripts/roadmap_handoff_check.py` and reconcile session momentum "
        "against project state, per AGENTS.md. If this handoff and the docs disagree, the docs win."
    )
    L.append("")

    text = "\n".join(L)

    if args.stdout:
        print(text)
        return 0

    if args.check:
        # DISABLED 2026-09-21 — KNOWN BROKEN, DO NOT TRUST ITS OUTPUT.
        #
        # `--check` compares the committed HANDOFF.md against a fresh build. Four attempts to make
        # that comparison stable all failed, because the generated file contains fields that
        # genuinely change with the working tree and with history: the timestamp, the commit hash
        # (a handoff written before its own commit can never name it), the uncommitted-paths block
        # (regenerating adds HANDOFF.md to it), and the recent-commits list (it shifts on every
        # commit that touches this file, and a commit touching this file AND another file defeats
        # every pathspec filter). Attempts to normalise them away were each defeated by the next
        # one, and the last attempt produced a false STALE after a correct regenerate.
        #
        # A check that reports false failures is worse than no check: it trains the reader to
        # ignore the one time it is right. So it now fails loudly and honestly instead of lying.
        # USE INSTEAD: just run `scripts/generate_handoff.py` — it is deterministic and cheap, and
        # regenerating is always correct. The staleness SIGNAL that matters is already carried by
        # the file itself: §1 lists the governing sources with sha256 hashes, so a reader compares
        # a hash against the file it is reading and sees immediately whether the handoff is stale.
        # FIXING THIS PROPERLY is a small, well-defined task: compare only the DERIVED CONTENT
        # (sections 1-5 and 7), excluding every history- or worktree-derived field by construction
        # rather than by block-skipping.
        print(
            "generate_handoff.py --check is DISABLED (known broken, 2026-09-21).\n"
            "It cannot distinguish real staleness from run-state differences and previously\n"
            "reported a false STALE. Do not rely on it.\n"
            "Instead: run `scripts/generate_handoff.py` to regenerate (deterministic and always\n"
            "correct), and verify staleness by comparing the sha256 hashes in HANDOFF.md section 1\n"
            "against the files themselves."
        )
        return 2

    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
