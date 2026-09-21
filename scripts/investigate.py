#!/usr/bin/env python3
"""Investigate the evidence behind a target -- read-only, agent- and owner-runnable.

This is the entry point that makes Track I.2's Investigator **reachable**. The role was
built and proven in ``meridian/ai/investigator.py`` but nothing could invoke it; a role that
nothing can call is not shipped, and the roadmap's I.2 asks for a role that is *"immediately
useful"*. This is the smallest honest way to get there: a command, not a web surface.

    .venv311/bin/python scripts/investigate.py --target transaction:412 --question "What is this?"

**Why a command and not an endpoint.** The role returns model-generated commentary about the
owner's financial evidence. Putting that behind a new web surface is a product decision --
which surface, what it looks like, who may see it -- and MERIDIAN_ROADMAP.md's visual
authority does not cover it. A read-only command needs none of that settled, adds no
endpoint, and can be replaced by a surface later without changing the role.

**Read-only, and checked rather than promised.** This script imports no write path and opens
the database read-only in spirit and in practice: it calls ``list_links_for_target`` and
``get_item``, and nothing else. ``tests/test_investigate_script.py`` parses this file and
fails if it ever imports a provider write module, so the claim cannot rot.

**An unconfigured model is reported, never faked.** With no API key in the environment the
script prints that no model is configured and exits 2. It does not fall back to a canned
answer: a fabricated investigation of the owner's own transactions is worse than no
investigation, and only a real client can support a claim about real evidence.

Exit codes: 0 ok, 1 failed (unusable reply, or a refused citation), 2 unavailable (no model,
no evidence, or the model could not be reached).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from meridian.ai.envelope import ResultStatus  # noqa: E402
from meridian.ai.investigator import Investigator, RoleRun  # noqa: E402

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_UNAVAILABLE = 2

_EXIT_FOR_STATUS = {
    ResultStatus.OK: EXIT_OK,
    ResultStatus.FAILED: EXIT_FAILED,
    ResultStatus.UNAVAILABLE: EXIT_UNAVAILABLE,
}

DEFAULT_QUESTION = "What is the evidence behind this, and what does it support?"


def parse_target(raw: str) -> tuple[str, str]:
    """``kind:id`` -> ``(kind, id)``.

    The id stays a string: the evidence store keys links by ``str(target_id)``, and coercing
    to int here would silently fail to match a link stored as text.
    """
    if not isinstance(raw, str) or ":" not in raw:
        raise ValueError(f"target must look like kind:id, got {raw!r}")
    kind, _, identifier = raw.partition(":")
    kind = kind.strip()
    identifier = identifier.strip()
    if not kind or not identifier:
        raise ValueError(f"target must look like kind:id, got {raw!r}")
    return kind, identifier


def investigate(
    *,
    repository,
    client,
    target_kind: str,
    target_id: str,
    question: str,
    clock: Callable[[], Any] | None = None,
) -> RoleRun:
    """Run the Investigator. Separated from argument handling so it is testable without a
    database, a network or a key: tests pass a fake repository and a fake client."""
    return Investigator(repository).run(
        question,
        client=client,
        target_kind=target_kind,
        target_id=target_id,
        clock=clock,
    )


def render(run: RoleRun) -> dict[str, Any]:
    """The result as data, with the run record attached.

    ``disagreements`` is surfaced explicitly rather than folded into the claims: two claims
    that contradict each other are the single most important thing a reader needs to notice,
    and burying them in a list of equal-looking claims is how a conflict gets missed.
    """
    result = run.result
    return {
        "status": result.status.value,
        "claims": [
            {"text": claim.text, "evidence_ids": list(claim.evidence_ids), "subject": claim.subject}
            for claim in result.claims
        ],
        "disagreements": [
            {
                "subject": disagreement.subject,
                "claims": [claim.text for claim in disagreement.claims],
            }
            for disagreement in result.disagreements
        ],
        "assumptions": list(result.assumptions),
        "confidence": result.confidence,
        "what_would_change": list(result.what_would_change),
        "detail": result.detail,
        "run": run.record.as_dict(),
    }


def format_text(payload: dict[str, Any]) -> str:
    """A terminal rendering. Never claims an action was taken."""
    lines = [f"status: {payload['status']}"]
    if payload["detail"]:
        lines.append(f"detail: {payload['detail']}")
    for claim in payload["claims"]:
        cited = ", ".join(claim["evidence_ids"]) or "NO CITATION"
        lines.append(f"  - {claim['text']}  [{cited}]")
    for disagreement in payload["disagreements"]:
        lines.append(f"  ! unresolved disagreement on {disagreement['subject']!r}:")
        for text in disagreement["claims"]:
            lines.append(f"      {text}")
    for assumption in payload["assumptions"]:
        lines.append(f"  assumption: {assumption}")
    if payload["what_would_change"]:
        lines.append(f"  would change the answer: {'; '.join(payload['what_would_change'])}")
    record = payload["run"]
    lines.append(
        f"run: {record['role']} · {record['provider']}/{record['model']} · "
        f"{record['prompt_version']} · {record['outcome']} · "
        f"{len(record['evidence_ids'])} evidence ref(s)"
    )
    lines.append("(read-only: nothing was proposed, approved or executed)")
    return "\n".join(lines)


def build_client():
    """The app's own provider chain. Imported lazily so this module stays importable (and
    AST-checkable) without dragging in a network stack, and so a missing key is a runtime
    message rather than an import error."""
    from crew.advisor import build_llm_chain

    return build_llm_chain()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Investigate the evidence behind a target (read-only).",
    )
    parser.add_argument("--target", required=True, help="kind:id, e.g. transaction:412")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--db",
        default=os.environ.get("DB_FILE", "savings_data.db"),
        help="Meridian database (read-only; default $DB_FILE or savings_data.db)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        target_kind, target_id = parse_target(args.target)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UNAVAILABLE

    try:
        client = build_client()
    except Exception as exc:  # noqa: BLE001 - a broken client is a reportable state
        print(f"error: could not build a model client: {type(exc).__name__}", file=sys.stderr)
        return EXIT_UNAVAILABLE

    # An unconfigured model is reported BEFORE any evidence is read, and nothing is
    # fabricated in its place. `providers()` is the chain's own answer to "is anything
    # configured", so this cannot drift from the real factory.
    if not getattr(client, "providers", lambda: [])():
        print(
            "error: no AI provider is configured, so nothing can be investigated.\n"
            "       Set DEEPSEEK_API_KEY (or OPENAI_API_KEY) and try again. This script\n"
            "       will not invent an answer, and it never logs or prints the key.",
            file=sys.stderr,
        )
        return EXIT_UNAVAILABLE

    from meridian.evidence import EvidenceRepository
    from meridian.repository import FinancialRepository

    graph = FinancialRepository(args.db)
    repository = EvidenceRepository(graph.db_path)

    run = investigate(
        repository=repository,
        client=client,
        target_kind=target_kind,
        target_id=target_id,
        question=args.question,
    )
    payload = render(run)
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else format_text(payload))
    return _EXIT_FOR_STATUS[run.result.status]


if __name__ == "__main__":
    raise SystemExit(main())
