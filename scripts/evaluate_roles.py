"""What did the roles actually do, and is there enough of it to say anything? READ-ONLY.

Usage:
    .venv/bin/python scripts/evaluate_roles.py                 # every role, default DB
    .venv/bin/python scripts/evaluate_roles.py --role skeptic
    .venv/bin/python scripts/evaluate_roles.py --db path/to/gate.db --limit 200

This is the first honest version of the roadmap's I.4 (OS-118). It reads `ai_run_records` — which deliberately
holds no claim text, no model output and no evidence body — so it can measure what was RECORDED: outcome
distribution, refusal rate, citation presence, durations, provider and prompt version, and contradictions
between those. It cannot measure whether a run was USEFUL to the owner, and it says so rather than substituting
a proxy and calling it the thing.

It never reports health over an empty set, and it refuses a per-role verdict below
`evaluation.MIN_RUNS_FOR_A_ROLE_VERDICT`. It writes nothing. No score it prints may remove, weaken or gate an
approval (OS-056).
"""
from __future__ import annotations

import argparse
import collections
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meridian.ai import evaluation  # noqa: E402
from meridian.ai.run_records import RunRecordStore  # noqa: E402

DEFAULT_DB = os.environ.get("GATE_DB") or os.environ.get("DB_FILE") or "/tmp/gate-preview/gate.db"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate recorded role runs (read-only).")
    parser.add_argument("--db", default=DEFAULT_DB, help="run-record database (read-only)")
    parser.add_argument("--role", default=None, help="limit to one role")
    parser.add_argument("--limit", type=int, default=500, help="most recent N runs to read")
    args = parser.parse_args(argv)

    store = RunRecordStore(args.db)
    report = evaluation.evaluate_store(store, role=args.role, limit=args.limit)

    print(f"run records read: {report.runs_total} (db: {args.db}, most recent {args.limit})")
    if not report.measured:
        print("  NOT MEASURED — " + str(report.refusal_reason))
        print("  An empty result set is the absence of data, not the absence of failures.")
        print("  Record a real run first: .venv/bin/python scripts/investigate.py --history 5")
        return 0

    for role in sorted(report.by_role):
        stats = report.by_role[role]
        print(f"  {role}: {stats.verdict()}")
        median_ms = stats.median_duration_ms
        print(f"      median duration: {median_ms:.0f}ms" if median_ms is not None else "      median duration: unknown")
        print(f"      providers: {sorted(stats.providers)}  prompt versions: {sorted(stats.prompt_versions)}")

    if report.anomalies:
        counts = collections.Counter(a.kind for a in report.anomalies)
        print(f"  ANOMALIES: {len(report.anomalies)} — {dict(counts)}")
        for anomaly in report.anomalies[:10]:
            print(f"      [{anomaly.kind}] run {anomaly.run_id} ({anomaly.role}): {anomaly.detail}")
    else:
        print(
            f"  no contradictions in these {report.runs_total} runs — which is a statement about the recorded "
            "window, not about the roles"
        )

    print(
        "\n  not measured by this tool, and not claimed: whether any run was USEFUL to the owner. Run records "
        "hold no claim text and no model output by design, so usefulness needs a journey, not a table."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
