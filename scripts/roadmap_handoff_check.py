"""Reconcile the governing order with what is actually in flight (read-only).

WHY THIS EXISTS. The owner's stated failure mode: the project has a clear original build
order, sessions routinely push in new directions, and a handoff written afterwards is
indistinguishable between "derived from the governing docs and assigned order" and "derived
from the conversation". The two must be reconciled or slices are lost. This script is the
reconciliation, so a handoff is a checked projection of the doc set rather than a summary of a
good session.

It is a CHECK, never an authority: everything it reports is already declared in the ledger or
the roadmap, and it neither reprioritises nor promotes anything.

Checks, in the order they matter:

  1. COVERAGE      — every task id the roadmap names exists in the ledger (nothing planned is lost).
  2. IN-FLIGHT     — every unfinished task declares a phase, so it belongs to a track. A high
                     priority in-progress task with no declared track is exactly how a slice drifts.
  3. GATES         — owner-gated tasks are visible, so they cannot be quietly worked around.
  4. ROADMAP GAPS  — unfinished ledger tasks the roadmap never names: legitimate (a defect found
                     in a session) but they must be visible as such rather than assumed planned.

Exit code is 0 when checks 1-2 pass, 1 otherwise, so it can gate a handoff.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROADMAP = ROOT / "docs/project/MERIDIAN_ROADMAP.md"
LEDGER = ROOT / "docs/project/MERIDIAN_OS_TASKS.json"

FINISHED = {"complete", "done"}

#: A task is "in flight" if it is not finished. Only these must declare a track.
def _in_flight(t: dict) -> bool:
    return t.get("status") not in FINISHED


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true", help="only report failures")
    args = parser.parse_args()

    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    tasks = json.loads(LEDGER.read_text(encoding="utf-8"))["tasks"]
    ledger_ids = {t["id"] for t in tasks}

    mentioned = set(re.findall(r"\bOS-\d{3}\b", roadmap_text))
    mentioned |= set(re.findall(r"\bVIRGIL-A\d\b", roadmap_text))

    failures: list[str] = []

    # 1. COVERAGE — a roadmap item absent from the ledger is planned work with no home.
    missing_from_ledger = sorted(mentioned - ledger_ids)
    if missing_from_ledger:
        failures.append(
            f"roadmap names {len(missing_from_ledger)} id(s) absent from the ledger: "
            f"{missing_from_ledger}"
        )
    if not args.quiet:
        print(f"[1] coverage      : {len(mentioned)} roadmap id(s), "
              f"{len(missing_from_ledger)} missing from the ledger")

    # 2. IN-FLIGHT — every unfinished task needs a track.
    open_tasks = [t for t in tasks if _in_flight(t)]
    undeclared = [t["id"] for t in open_tasks if not (t.get("phase") or "").strip()]
    if undeclared:
        failures.append(
            f"{len(undeclared)} unfinished task(s) declare no phase/track: {undeclared}"
        )
    if not args.quiet:
        print(f"[2] in-flight     : {len(open_tasks)} unfinished, "
              f"{len(undeclared)} with no declared track")

    # 3. GATES — surfaced, never a failure: an owner gate is a legitimate resting state.
    gated = [t["id"] for t in open_tasks if t.get("owner_decision_required")]
    if not args.quiet:
        print(f"[3] owner gates   : {len(gated)} -> {gated}")

    # 4. ROADMAP GAPS — unfinished work the roadmap does not name. Not a failure: a defect
    #    found mid-session is legitimately absent from the roadmap. It must be VISIBLE, and
    #    it must not be presented as assigned work.
    unplanned = sorted(t["id"] for t in open_tasks if t["id"] not in mentioned)
    if not args.quiet:
        print(f"[4] not in roadmap: {len(unplanned)} unfinished task(s) -> {unplanned}")
        if unplanned:
            print("    (legitimate for a session-found defect; must be labelled emergent, "
                  "not assigned, in any handoff)")

    if not args.quiet:
        print()
        for t in sorted(open_tasks, key=lambda x: x["id"]):
            track = (t.get("phase") or "(NO TRACK)").ljust(22)
            gate = "GATE" if t.get("owner_decision_required") else "    "
            print(f"    {t['id']:8s} {track} {t.get('status','?'):11s} {gate} "
                  f"{(t.get('title') or '')[:46]}")

    if failures:
        print("\nRECONCILIATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        print("\nFix the ledger/roadmap before writing a handoff: the governing order and what "
              "is declared in flight must agree.")
        return 1

    print("\nRECONCILED: every roadmap item is in the ledger, and every unfinished task "
          "declares a track.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
