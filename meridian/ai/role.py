"""Shared machinery for evidence-bound roles.

Extracted when the second role arrived (Track I.3). The Investigator and the Skeptic share
everything except their prompts, their permissions and how they read the model's reply, so
that is what a role defines -- evidence binding, the envelope wiring, the fail-soft states
and the run record all live here and are written once.

**The base class is a safety boundary, not just a convenience.** Every role built on it
inherits the same properties by construction: a hallucinated citation voids the result rather
than being repaired, an empty evidence set never reaches the model, a client failure is a
state rather than an exception, and nothing is ever retried. A role that overrode those would
have to do so deliberately and visibly, which is the point.

**A role receives a client and never builds one.** The client only needs
``complete(system, messages) -> str``, so Meridian's real chain
(``crew/advisor.py::FailoverLLMClient``) and a two-line test fake are interchangeable, and no
role can hold a credential or start a network call of its own.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

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


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def humanize_age(observed_at: str, now: datetime) -> str:
    """A readable age, or ``unknown`` when the timestamp cannot be trusted.

    Returning ``unknown`` rather than a number matters: a freshness label is a claim about
    how current something is, and a broken timestamp cannot support one.
    """
    moment = parse_iso(observed_at)
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


def extract_json(raw: str) -> Mapping[str, Any]:
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


def coerce_claims(entries: Any) -> list[Claim]:
    """Build claims from whatever the model returned, ignoring anything malformed.

    Malformed entries are DROPPED rather than repaired: a claim with no citation is exactly
    what the citation check exists to refuse, and inventing an id here would defeat it.
    """
    claims: list[Claim] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        text = entry.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        ids = entry.get("evidence_ids")
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
    return claims


def coerce_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def coerce_confidence(value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return min(1.0, max(0.0, float(value)))


class EvidenceBoundRole:
    """Base for a read-only role that answers from evidence linked to a target.

    Subclasses set ``role`` and ``prompt_version`` and implement ``system_prompt()`` and
    optionally ``context_payload()``. The run loop, the evidence binding, the citation check
    and the failure states are inherited and are not meant to be re-implemented.
    """

    role: str = ""
    prompt_version: str = ""

    def __init__(self, evidence_repository, *, prompt_version: str | None = None) -> None:
        if not self.role:
            raise ValueError("a role must declare its role name")
        # Import-time proof that this role is allowed to exist at all: an unregistered role
        # would have no permissions, and permissions are what bound it.
        self.permissions = permissions_for(self.role)
        self._repository = evidence_repository
        if prompt_version:
            self.prompt_version = prompt_version

    # -- hooks ---------------------------------------------------------------------------

    def system_prompt(self) -> str:
        raise NotImplementedError

    def context_payload(
        self, task: EnvelopeTask, review: tuple[Claim, ...]
    ) -> Mapping[str, Any]:
        """Extra material for the prompt. Default: nothing beyond the evidence."""
        return {}

    def build_result(self, payload: Mapping[str, Any]) -> EnvelopeResult:
        """Turn a parsed reply into a result. Claim parsing is shared; subclasses that need
        a different reading (the Skeptic does) override this."""
        claims = coerce_claims(payload.get("claims"))
        if not claims:
            return EnvelopeResult(
                status=ResultStatus.UNAVAILABLE,
                assumptions=coerce_strings(payload.get("assumptions")),
                what_would_change=coerce_strings(payload.get("what_would_change")),
                detail="The evidence does not answer the question.",
            )
        return EnvelopeResult(
            status=ResultStatus.OK,
            claims=tuple(claims),
            assumptions=coerce_strings(payload.get("assumptions")),
            confidence=coerce_confidence(payload.get("confidence")),
            what_would_change=coerce_strings(payload.get("what_would_change")),
            disagreements=detect_disagreements(claims),
        )

    # -- evidence binding -----------------------------------------------------------------

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
        review: Iterable[Claim] = (),
        clock: Callable[[], datetime] | None = None,
    ) -> RoleRun:
        """Answer ``question`` from the evidence linked to the target.

        ``review`` carries claims another role produced, for roles whose job is to attack
        them; a role that has no use for it ignores it.

        Never raises for a model, parsing or citation problem: each becomes a visible state
        on the result. The only exceptions that escape are programmer errors (an unknown
        role, a malformed budget), which should be loud.
        """
        tick = clock or utcnow
        started = tick()
        reviewed = tuple(review)
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
            budget=self.permissions.budget,
        )

        try:
            raw = client.complete(
                self.system_prompt(),
                [{"role": "user", "content": self._prompt_payload(task, reviewed)}],
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
                outcome="unavailable:model",
                client=client,
            )

        try:
            payload = extract_json(raw)
        except ValueError as exc:
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.FAILED,
                    detail=f"The model reply could not be used: {exc}",
                ),
                started=started,
                tick=tick,
                evidence_ids=tuple(ref.id for ref in refs),
                outcome="failed:unparseable",
                client=client,
            )

        result = self.build_result(payload)

        try:
            validate_citations(result, task)
        except UnsupportedClaim as exc:
            # The result is VOIDED rather than repaired. Dropping the bad claim would keep
            # whatever the model produced alongside it, and the reason it fabricated a
            # citation is not something a role can see.
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.FAILED,
                    detail=f"Refused: {exc}",
                ),
                started=started,
                tick=tick,
                evidence_ids=tuple(ref.id for ref in refs),
                outcome="failed:unsupported-citation",
                client=client,
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

    def _prompt_payload(self, task: EnvelopeTask, review: tuple[Claim, ...]) -> str:
        """The model sees references, not bodies: it can cite only what it was given."""
        payload: dict[str, Any] = {
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
        }
        payload.update(self.context_payload(task, review))
        return json.dumps(payload, sort_keys=True)

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
        # read as authoritative while being a guess -- worse than admitting the gap.
        record = RunRecord(
            role=self.role,
            provider=getattr(client, "last_provider", None) or "unknown",
            model=getattr(client, "model", None) or "unknown",
            prompt_version=self.prompt_version,
            evidence_ids=evidence_ids,
            started_at=to_iso(started),
            ended_at=to_iso(tick()),
            outcome=outcome,
        )
        return RoleRun(result=result, record=record)
