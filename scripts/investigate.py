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

**Read-only with respect to money and providers, and precise about it.** This script imports
no provider write path and calls no mutating method: it reads evidence with
``list_links_for_target`` and ``get_item`` and nothing else. What it DOES write is one row in
``ai_run_records`` — the audit trail I.1 requires — and no financial state, no proposal and no
provider state is touched. ``--no-record`` turns even that off. The distinction is stated
rather than glossed, because a command that describes itself as "read-only" while writing to
the database is exactly the kind of quiet inaccuracy that makes a safety claim worthless.

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
    read_content=None,
    clock: Callable[[], Any] | None = None,
) -> RoleRun:
    """Run the Investigator. Separated from argument handling so it is testable without a
    database, a network or a key: tests pass a fake repository and a fake client."""
    return Investigator(repository, read_content=read_content).run(
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
    if payload.get("recorded_id") is not None:
        lines.append(f"recorded: ai_run_records#{payload['recorded_id']}")
    lines.append("(read-only: nothing was proposed, approved or executed)")
    return "\n".join(lines)


def record_run(run: RoleRun, db_path: str) -> int:
    """Keep the run record, per I.1: "persisted so a proposal can be audited back to the
    reasoning that produced it". Returns the stored row id.

    Only the audit row is written -- no claim text, no model output, no evidence body (see
    ``meridian/ai/run_records.py``). A failure to record must NOT discard the answer the
    operator is waiting for, so the caller decides how to report it rather than this raising
    into the run.
    """
    from meridian.ai.run_records import RunRecordStore

    return RunRecordStore(db_path).record(run.record).id


def show_history(db_path: str, *, limit: int) -> str:
    """Recent runs, newest first. Read-only."""
    from meridian.ai.run_records import RunRecordStore

    runs = RunRecordStore(db_path).list_recent(limit=limit)
    if not runs:
        return "no runs recorded yet"
    lines = [f"{len(runs)} most recent run(s):"]
    for stored in runs:
        lines.append(
            f"  #{stored.id} {stored.recorded_at} {stored.role} "
            f"{stored.provider}/{stored.model} {stored.outcome} "
            f"({len(stored.evidence_ids)} evidence ref(s))"
        )
    return "\n".join(lines)


def build_client():
    """The app's own provider chain. Imported lazily so this module stays importable (and
    AST-checkable) without dragging in a network stack, and so a missing key is a runtime
    message rather than an import error."""
    from crew.advisor import build_llm_chain

    return build_llm_chain()


def build_content_reader(db_path: str):
    """A reader for stored evidence content, or ``None``.

    Built from the APP's own factory so the encryption key derivation matches production exactly
    — the same reason ``scripts/backfill_charge_evidence.py`` does it this way. ``DB_FILE`` must
    be set BEFORE ``app`` is imported, because the factory derives the evidence root from it at
    import time; setting it afterwards would read the live blobs for a different database than
    the one being investigated.

    Best-effort by design. This is the difference between a role that can explain a charge and
    one that cannot, but it is not worth failing a read-only investigation over: if the store
    cannot be built, the role runs without content and returns no claims rather than inventing
    any. The caller is told, so "no claims" is never mistaken for "the evidence says nothing".
    """
    import os

    os.environ["DB_FILE"] = db_path
    os.environ.setdefault("SESSION_COOKIE_SECURE", "0")
    try:
        import app as app_module

        factory = app_module.app.config.get("MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY")
        if factory is None:
            return None
        store = factory()
    except Exception:  # noqa: BLE001 - a missing store is a degraded mode, not a failure
        return None
    return lambda content_hash: store.read(content_hash)


def convene_council(
    *,
    repository,
    client,
    target_kind: str,
    target_id: str,
    question: str,
    read_content=None,
):
    """Run the Investigator and the Skeptic on one question.

    The two are wired together so the Skeptic is handed the Investigator's claims -- the
    council's whole reason for existing. A single shared client is used because a fake or a
    real chain treats both roles identically; a test asserts each role was called once.
    """
    from meridian.ai.council import CouncilMember, convene
    from meridian.ai.skeptic import Skeptic

    investigator = Investigator(repository, read_content=read_content)
    skeptic = Skeptic(repository)
    return convene(
        question,
        [
            CouncilMember(
                "investigator",
                lambda q, claims: investigator.run(
                    q, client=client, target_kind=target_kind, target_id=target_id
                ),
            ),
            CouncilMember(
                "skeptic",
                lambda q, claims: skeptic.run(
                    q, client=client, target_kind=target_kind, target_id=target_id, review=claims
                ),
            ),
        ],
    )


def render_council(result) -> dict[str, Any]:
    """The deliberation as data. Carries each role's own run record, and no verdict."""
    return {
        "question": result.question,
        "roles": list(result.roles()),
        "unanimous": result.is_unanimous(),
        "roles_detail": [
            {
                "role": role,
                "status": run.result.status.value,
                "detail": run.result.detail,
                "claims": [
                    {
                        "text": claim.text,
                        "evidence_ids": list(claim.evidence_ids),
                        "subject": claim.subject,
                    }
                    for claim in run.result.claims
                ],
                "record": run.record.as_dict(),
            }
            for role, run in result.runs
        ],
        "claims": [
            {
                "role": item.role,
                "text": item.claim.text,
                "evidence_ids": list(item.claim.evidence_ids),
                "subject": item.claim.subject,
            }
            for item in result.claims
        ],
        "disagreements": [
            {
                "subject": disagreement.subject,
                "roles": list(disagreement.roles),
                "positions": [
                    {"role": role, "text": claim.text}
                    for role, claim in disagreement.positions
                ],
            }
            for disagreement in result.disagreements
        ],
        "failures": [
            {"role": role, "outcome": outcome} for role, outcome in result.failures()
        ],
    }


def format_council_text(payload: dict[str, Any]) -> str:
    """A terminal rendering that does not look like a decision."""
    lines = [
        f"council: {len(payload['roles'])} role(s) on one question",
        f"question: {payload['question']}",
    ]
    for detail in payload["roles_detail"]:
        lines.append(f"  {detail['role']}: {detail['status']} ({len(detail['claims'])} claim(s))")
        if detail["detail"]:
            lines.append(f"      {detail['detail']}")
    if payload["claims"]:
        lines.append("claims, each attributed to the role that made it:")
        for claim in payload["claims"]:
            cited = ", ".join(claim["evidence_ids"]) or "NO CITATION"
            lines.append(f"  [{claim['role']}] {claim['text']}  [{cited}]")
    for disagreement in payload["disagreements"]:
        lines.append(
            f"  ! unresolved disagreement on {disagreement['subject']!r} "
            f"between {', '.join(disagreement['roles'])}:"
        )
        for position in disagreement["positions"]:
            lines.append(f"      [{position['role']}] {position['text']}")
    for failure in payload["failures"]:
        lines.append(f"  ! {failure['role']} did not run: {failure['outcome']}")
    lines.append(f"unanimous: {'yes' if payload['unanimous'] else 'no'}")
    lines.append(
        "no verdict is produced: disagreement is shown, never settled by majority vote"
    )
    lines.append("(read-only: nothing was proposed, approved or executed)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Investigate the evidence behind a target (read-only).",
    )
    parser.add_argument(
        "--target",
        help="kind:id, e.g. transaction:412 (required unless --history is used)",
    )
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--db",
        default=os.environ.get("DB_FILE", "savings_data.db"),
        help="Meridian database (read-only; default $DB_FILE or savings_data.db)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--council",
        action="store_true",
        help="also run the Skeptic and show the deliberation (still no verdict)",
    )
    parser.add_argument(
        "--no-content",
        action="store_true",
        help="do not read stored evidence content (the role then has ids only)",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="do not append an audit row (the run is still printed)",
    )
    parser.add_argument(
        "--history",
        type=int,
        metavar="N",
        help="list the N most recent runs and exit (read-only)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.history is not None:
        print(show_history(args.db, limit=args.history))
        return EXIT_OK

    if not args.target:
        print(
            "error: --target is required (kind:id, e.g. transaction:412), "
            "unless --history is used.",
            file=sys.stderr,
        )
        return EXIT_UNAVAILABLE

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

    # Content is what lets the role explain anything at all; without it the model gets evidence
    # ids and returns no claims. Its absence is announced rather than left to look like silence.
    read_content = None
    if not args.no_content:
        read_content = build_content_reader(args.db)
        if read_content is None:
            print(
                "warning: stored evidence content could not be opened, so the investigation runs "
                "without it. Any 'no claims' below means NO CONTENT WAS SUPPLIED, not that the "
                "evidence says nothing.",
                file=sys.stderr,
            )

    if args.council:
        council_result = convene_council(
            repository=repository,
            client=client,
            target_kind=target_kind,
            target_id=target_id,
            question=args.question,
            read_content=read_content,
        )
        council_payload = render_council(council_result)
        # Every role's run is recorded: a council of two roles is two runs, and collapsing
        # them into one row would lose which role said what.
        if not args.no_record:
            recorded = []
            for _role, run in council_result.runs:
                try:
                    recorded.append(record_run(run, args.db))
                except Exception as exc:  # noqa: BLE001 - same policy as a single run
                    print(
                        f"warning: a run was not recorded ({type(exc).__name__}); the audit "
                        "trail is incomplete for this council.",
                        file=sys.stderr,
                    )
            council_payload["recorded_ids"] = recorded
        print(
            json.dumps(council_payload, indent=2, sort_keys=True)
            if args.json
            else format_council_text(council_payload)
        )
        # A council where any role failed is not a clean run, and says so through the exit
        # code rather than only in the text.
        if council_result.failures():
            return EXIT_UNAVAILABLE
        return EXIT_OK

    run = investigate(
        repository=repository,
        client=client,
        target_kind=target_kind,
        target_id=target_id,
        question=args.question,
        read_content=read_content,
    )
    payload = render(run)

    # Recording is attempted AFTER the answer is in hand and never replaces it. A failed
    # audit write is reported on stderr while the investigation still reaches the operator:
    # losing the trail is bad, but swallowing the answer is worse, and neither justifies
    # pretending the run did not happen.
    if not args.no_record:
        try:
            payload["recorded_id"] = record_run(run, args.db)
        except Exception as exc:  # noqa: BLE001 - any storage failure is the same report
            print(
                f"warning: the run was not recorded ({type(exc).__name__}); the audit trail "
                "is incomplete for this run.",
                file=sys.stderr,
            )

    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else format_text(payload))
    return _EXIT_FOR_STATUS[run.result.status]


if __name__ == "__main__":
    raise SystemExit(main())
