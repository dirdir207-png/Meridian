"""Track I.2 — the Investigator: one role, end to end, on I.1's envelope.

MERIDIAN_ROADMAP.md §6, **I.2 — One role, end to end**: *"Ship the Forecaster or
Investigator first — read-only, evidence-bound, immediately useful. Adversarial tests:
hallucinated citation, missing evidence, contradictory sources, unavailable model. Prove the
envelope before adding roles."*

**The Investigator answers a question about a charge, an event or a discrepancy from the
evidence actually linked to it, and says so when it cannot.**

Four properties make it safe, and each is checked in
``tests/meridian/test_ai_investigator.py`` rather than described here:

1. **No evidence, no answer.** If nothing is linked to the target, the run returns
   ``UNAVAILABLE`` and the model is *never called*. A model asked to explain nothing will
   produce something, so the call is not made in the first place.
2. **A hallucinated citation voids the result.** Every claim must cite evidence the task
   actually supplied; when it does not, the result is ``FAILED`` carrying **no claims at
   all**. That is the envelope's own rule -- a failed result may not carry claims -- so a
   fabricated citation cannot reach a reader even by accident.
3. **Disagreement is recorded, not settled.** Two claims about the same subject that do not
   agree are both returned, with the conflict marked. Nothing votes, scores or picks a
   winner.
4. **An unavailable model is a state, not an exception.** A failing or timing-out client
   yields ``UNAVAILABLE``; the role never raises into its caller and never retries.

**It receives a client and never builds one.** ``client`` is injected and only needs
``complete(system, messages) -> str`` -- Meridian's real chain (`crew/advisor.py::
FailoverLLMClient`) and a two-line test fake are interchangeable. A test asserts this module
contains no ``requests``, no ``api_key``, no ``os.environ`` and no ``subprocess``, so it can
never grow its own credential or start its own network call.

**This role is what I.1 was for.** It reads; it never writes. It holds no provider write
tool -- ``meridian/ai/envelope.py`` proves that for every role at import -- and its only
output is a typed result plus a run record.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from meridian.ai.envelope import (
    Claim,
    EnvelopeResult,
    EnvelopeTask,
    EvidenceRef,
    ResultStatus,
    RunRecord,
    UnsupportedClaim,
    detect_disagreements,
    permissions_for,
    validate_citations,
)

ROLE = "investigator"
PROMPT_VERSION = "investigator-v1"

_ROLE = permissions_for(ROLE)

SYSTEM_PROMPT = (
    "You are the Investigator for Meridian. You answer ONLY from the evidence supplied. "
    "Return JSON with `claims`, `assumptions`, `confidence` and `what_would_change`. "
    "Each claim is an object with `text`, `evidence_ids` (ids copied exactly from the "
    "supplied evidence) and `subject` (a short key naming the FACT the claim is about, so "
    "two claims about the same fact can be compared). Every claim MUST cite at least one "
    "supplied evidence id; never cite an id you were not given and never invent one. If "
    "the evidence does not answer the question, return no claims. Never state that an "
    "action was taken or will be taken."
)

# Models wrap JSON in a fenced block often enough that refusing to parse it would be a
# usability bug rather than a security win. Same approach as crew/advisor.py.
_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class RoleRun:
    """A role's answer AND its audit trail, which must always travel together: the roadmap
    requires the record so a proposal can be traced back to the reasoning that produced it."""

    result: EnvelopeResult
    record: RunRecord

    @property
    def status(self) -> ResultStatus:
        return self.result.status


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def humanize_age(observed_at: str, now: datetime) -> str:
    """A readable age, or ``unknown`` when the timestamp cannot be trusted.

    Returning ``unknown`` rather than a number matters: a freshness label is a claim about
    how current something is, and a broken timestamp cannot support one.
    """
    moment = _parse_iso(observed_at)
    if moment is None:
        return "unknown"
    seconds = max(0.0, (now - moment).total_seconds())
    if seconds < 90:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 86400)}d"


def _extract_json(raw: str) -> Mapping[str, Any]:
    """Parse the model's reply, tolerating a fenced block. Raises ValueError if unusable."""
    if not isinstance(raw, str):
        raise ValueError("model reply was not text")
    text = raw.strip()
    fenced = _JSON_BLOCK.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model reply was not JSON: {exc}") from None
    if not isinstance(payload, dict):
        raise ValueError("model reply was not a JSON object")
    return payload


class Investigator:
    """Find the evidence behind a charge, an event or a discrepancy. Read-only.

    ``evidence_repository`` is any object exposing ``list_links_for_target(target_kind,
    target_id)`` and ``get_item(evidence_id)`` -- the real
    ``meridian/evidence.py::EvidenceRepository`` in production.
    """

    role = ROLE
    prompt_version = PROMPT_VERSION

    def __init__(self, evidence_repository, *, prompt_version: str | None = None) -> None:
        self._repository = evidence_repository
        self.prompt_version = prompt_version or PROMPT_VERSION

    # -- evidence binding ---------------------------------------------------------------

    def bind_evidence(
        self, *, target_kind: str, target_id: str, now: datetime
    ) -> tuple[EvidenceRef, ...]:
        """The evidence linked to ``target``, as references.

        Withdrawn evidence is excluded: an item whose content was deleted or which was
        revoked is not evidence any more, and answering from it would be answering from a
        retracted record. ``confidence`` is left ``None`` because the store does not record
        one -- inventing a number here would be indistinguishable from a real measurement.
        """
        refs: list[EvidenceRef] = []
        for link in self._repository.list_links_for_target(target_kind, target_id):
            item = self._repository.get_item(link.evidence_id)
            if item is None:
                continue
            if getattr(item, "revoked_at", None) or getattr(item, "content_deleted_at", None):
                continue
            provenance = getattr(link, "provenance", None) or (
                f"{item.source_kind}:{item.source_id}"
            )
            refs.append(
                EvidenceRef(
                    id=f"evidence:{item.id}",
                    provenance=provenance,
                    observed_at=item.created_at,
                    freshness=humanize_age(item.created_at, now),
                    confidence=None,
                )
            )
        return tuple(refs)

    # -- the run -------------------------------------------------------------------------

    def run(
        self,
        question: str,
        *,
        client,
        target_kind: str,
        target_id: str,
        clock: Callable[[], datetime] | None = None,
    ) -> RoleRun:
        """Answer ``question`` from the evidence linked to the target.

        Never raises for a model, parsing or citation problem: each of those becomes a
        visible state on the result. The only exceptions that escape are programmer errors
        (an unknown role, a malformed budget), which should be loud.
        """
        tick = clock or _utcnow
        started = tick()
        refs = self.bind_evidence(target_kind=target_kind, target_id=target_id, now=started)

        if not refs:
            # No evidence, no answer -- and no model call. Asking a model to explain
            # nothing is precisely how an unsupported answer gets produced.
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.UNAVAILABLE,
                    detail=(
                        f"No evidence is linked to {target_kind}:{target_id}. "
                        "Nothing can be asserted from an empty evidence set."
                    ),
                ),
                started=started,
                tick=tick,
                evidence_ids=(),
                outcome="unavailable:no-evidence",
                client=client,
            )

        task = EnvelopeTask(
            role=self.role,
            question=question,
            evidence=refs,
            budget=_ROLE.budget,
        )

        try:
            raw = client.complete(
                SYSTEM_PROMPT,
                [{"role": "user", "content": self._prompt_payload(task)}],
            )
        except Exception as exc:  # noqa: BLE001 - any client failure is the same state
            # Deliberately broad and deliberately NOT a retry: an unavailable model is a
            # state to report. Retrying a call whose outcome is unknown is how a role
            # starts behaving like an executor.
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.UNAVAILABLE,
                    detail=f"The model is unavailable: {type(exc).__name__}.",
                ),
                started=started,
                tick=tick,
                evidence_ids=tuple(ref.id for ref in refs),
                client=client,
                outcome="unavailable:model",
            )

        try:
            result = self._build_result(raw)
        except ValueError as exc:
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.FAILED,
                    detail=f"The model reply could not be used: {exc}",
                ),
                started=started,
                tick=tick,
                evidence_ids=tuple(ref.id for ref in refs),
                client=client,
                outcome="failed:unparseable",
            )

        try:
            validate_citations(result, task)
        except UnsupportedClaim as exc:
            # The result is VOIDED rather than repaired. Dropping the bad claim would keep
            # whatever the model produced alongside it, and the reason it fabricated a
            # citation is not something this role can see.
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.FAILED,
                    detail=f"Refused: {exc}",
                ),
                started=started,
                tick=tick,
                evidence_ids=tuple(ref.id for ref in refs),
                client=client,
                outcome="failed:unsupported-citation",
            )

        return self._finish(
            result,
            started=started,
            tick=tick,
            evidence_ids=tuple(ref.id for ref in refs),
            outcome="ok",
            client=client,
        )

    # -- internals -----------------------------------------------------------------------

    def _prompt_payload(self, task: EnvelopeTask) -> str:
        """The model sees references, not bodies: it can cite only what it was given."""
        return json.dumps(
            {
                "question": task.question,
                "evidence": [
                    {
                        "id": ref.id,
                        "provenance": ref.provenance,
                        "observed_at": ref.observed_at,
                        "freshness": ref.freshness,
                    }
                    for ref in task.evidence
                ],
            },
            sort_keys=True,
        )

    def _build_result(self, raw: str) -> EnvelopeResult:
        payload = _extract_json(raw)
        claims: list[Claim] = []
        for entry in payload.get("claims") or []:
            if not isinstance(entry, dict):
                continue
            text = entry.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            ids = entry.get("evidence_ids") or []
            if not isinstance(ids, list):
                ids = []
            subject = entry.get("subject")
            claims.append(
                Claim(
                    text=text,
                    evidence_ids=tuple(item for item in ids if isinstance(item, str)),
                    subject=subject if isinstance(subject, str) and subject.strip() else None,
                )
            )

        if not claims:
            return EnvelopeResult(
                status=ResultStatus.UNAVAILABLE,
                assumptions=self._strings(payload.get("assumptions")),
                what_would_change=self._strings(payload.get("what_would_change")),
                detail="The evidence does not answer the question.",
            )

        confidence = payload.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            confidence = 0.0
        confidence = min(1.0, max(0.0, float(confidence)))

        return EnvelopeResult(
            status=ResultStatus.OK,
            claims=tuple(claims),
            assumptions=self._strings(payload.get("assumptions")),
            confidence=confidence,
            what_would_change=self._strings(payload.get("what_would_change")),
            disagreements=detect_disagreements(claims),
        )

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        return tuple(item for item in value if isinstance(item, str) and item.strip())

    def _finish(
        self,
        result: EnvelopeResult,
        *,
        started: datetime,
        tick: Callable[[], datetime],
        evidence_ids: tuple[str, ...],
        outcome: str,
        client: Any = None,
    ) -> RoleRun:
        # The record states what the client can attest to and says `unknown` otherwise. A
        # plausible-looking provider name that nothing verified would make the audit trail
        # read as authoritative while being a guess -- which is worse than admitting the gap.
        record = RunRecord(
            role=self.role,
            provider=getattr(client, "last_provider", None) or "unknown",
            model=getattr(client, "model", None) or "unknown",
            prompt_version=self.prompt_version,
            evidence_ids=evidence_ids,
            started_at=_iso(started),
            ended_at=_iso(tick()),
            outcome=outcome,
        )
        return RoleRun(result=result, record=record)
