"""Track I.3 — the Skeptic: supplies counterexamples and attacks a claim's evidence.

MERIDIAN_ROADMAP.md §6, **I.3 — Council mechanics**: *"Forecaster proposes, Skeptic supplies
counterexamples, Guardian objects on policy/evidence, Investigator brings causal evidence,
Teacher explains. Disagreement is recorded and shown, never settled by majority vote."*

**The Skeptic is the role that makes disagreement possible.** It is given the claims another
role produced and the same evidence, and its job is to find what those claims do NOT
establish — a claim the evidence does not support, a fact supported by only one source, or a
reading the evidence contradicts. It is built before the council runner because a council of
roles that all agree is not a council.

**It cannot "win", because it is not asked to.** The Skeptic never returns a verdict, a score
or a majority. It returns its own claims, each cited, with the same subjects as the claims it
examined — which is exactly what lets ``detect_disagreements`` put the two side by side and
leave the conflict standing. Nothing in this module ranks one role above another.

**Failing to find a counterexample is a real answer.** Unlike a role that answers a question,
a skeptic that finds nothing to attack returns ``UNAVAILABLE`` with no claims. That is
deliberately not an "ok": silence from the skeptic must not read as agreement, and the
envelope forbids an ``ok`` with no claims.

**A missing claim set is refused.** ``review`` is the Skeptic's entire subject matter; running
it with nothing to review would produce an attack on nothing, so it returns ``UNAVAILABLE``
without calling the model.
"""

from __future__ import annotations

from typing import Any, Mapping

from meridian.ai.envelope import Claim, EnvelopeResult, EnvelopeTask, ResultStatus
from meridian.ai.role import (
    EvidenceBoundRole,
    RoleRun,
    coerce_claims,
    coerce_strings,
    utcnow,
)

ROLE = "skeptic"
PROMPT_VERSION = "skeptic-v1"

SYSTEM_PROMPT = (
    "You are the Skeptic for Meridian. You are given CLAIMS produced by another role and the "
    "EVIDENCE available. Your job is to find what those claims do NOT establish: a claim the "
    "evidence does not support, a fact resting on a single source, or a reading the evidence "
    "contradicts. Return JSON with `claims`, `assumptions`, `confidence` and "
    "`what_would_change`. Each claim is an object with `text`, `evidence_ids` (ids copied "
    "exactly from the supplied evidence) and `subject` (the SAME subject key as the claim you "
    "are addressing, so the two can be compared). Every claim MUST cite at least one supplied "
    "evidence id; never cite an id you were not given and never invent one. Use the same "
    "subject for a counterexample, but state it as what the evidence shows -- do not "
    "paraphrase the claim you are attacking. If the claims are soundly supported, return NO "
    "claims rather than inventing doubt. Never state that an action was taken or will be taken."
)

# Phrases a skeptic reaching for doubt rather than evidence tends to use. This is NOT a
# correctness filter -- a real counterexample always cites evidence, and the citation check
# is what enforces that. It exists to catch the specific failure of attacking a claim
# without saying anything, which cites valid evidence and would otherwise pass.
_EMPTY_ATTACK_MARKERS = (
    "could be wrong",
    "might be wrong",
    "may be wrong",
    "not sure",
    "cannot be sure",
    "insufficient information",
)


class Skeptic(EvidenceBoundRole):
    """Attack another role's claims from the evidence. Read-only, like every role."""

    role = ROLE
    prompt_version = PROMPT_VERSION

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def context_payload(
        self, task: EnvelopeTask, review: tuple[Claim, ...]
    ) -> Mapping[str, Any]:
        """The claims under review, as text plus the evidence they cited.

        Only the claim TEXT and its citations cross over -- never another role's reasoning,
        prompt or model output. The Skeptic must be able to disagree with the claim that was
        made, not with how it was made.
        """
        return {
            "claims_under_review": [
                {"text": claim.text, "evidence_ids": list(claim.evidence_ids),
                 "subject": claim.subject}
                for claim in review
            ]
        }

    def run(self, question, *, client, target_kind, target_id, review=(), clock=None) -> RoleRun:
        """Refuse to run with nothing to review.

        An attack on nothing is not skepticism, and a model asked to review an empty list
        will produce something. This check happens before the model is called, so the call is
        never made -- the same rule as "no evidence, no answer".
        """
        reviewed = tuple(review)
        if not reviewed:
            tick = clock or utcnow
            started = tick()
            return self._finish(
                EnvelopeResult(
                    status=ResultStatus.UNAVAILABLE,
                    detail="No claims were supplied to review, so there is nothing to attack.",
                ),
                started=started,
                tick=tick,
                evidence_ids=(),
                outcome="unavailable:nothing-to-review",
                client=client,
            )
        return super().run(
            question,
            client=client,
            target_kind=target_kind,
            target_id=target_id,
            review=reviewed,
            clock=clock,
        )

    def build_result(self, payload: Mapping[str, Any]) -> EnvelopeResult:
        """Read the reply, dropping claims that assert doubt without saying anything.

        A skeptic that answers "this could be wrong" has added no information and cited
        nothing useful; keeping it would inflate the appearance of scrutiny without
        providing any. Claims that survive are the ones that state what the evidence shows.
        """
        claims = [
            claim
            for claim in coerce_claims(payload.get("claims"))
            if not _is_empty_attack(claim.text)
        ]
        if not claims:
            return EnvelopeResult(
                status=ResultStatus.UNAVAILABLE,
                assumptions=coerce_strings(payload.get("assumptions")),
                what_would_change=coerce_strings(payload.get("what_would_change")),
                detail="No counterexample was found; the claims are not contradicted here.",
            )
        return EnvelopeResult(
            status=ResultStatus.OK,
            claims=tuple(claims),
            assumptions=coerce_strings(payload.get("assumptions")),
            confidence=0.0,
            what_would_change=coerce_strings(payload.get("what_would_change")),
        )


def _is_empty_attack(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _EMPTY_ATTACK_MARKERS) and len(lowered.split()) < 14
