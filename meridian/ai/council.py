"""Track I.3 — council mechanics: several roles, one bounded question, no verdict.

MERIDIAN_ROADMAP.md §6, **I.3**: *"multi-role deliberation on one bounded question ... 
Disagreement is recorded and shown, never settled by majority vote. Every conclusion states
its evidence and its uncertainty."*

**What this module refuses to do is the whole point.** It does not produce a single answer,
does not score roles, does not vote, and does not rank one role's claim above another's. It
convenes roles, keeps every claim attributed to the role that made it, and hands the reader
the disagreements intact. A council that quietly resolves into one voice is worse than no
council, because the resolution would look like agreement.

**Roles run in the order given, and later roles may see earlier claims.** That is what makes
the Skeptic possible: it is handed the Investigator's claims as its subject matter. The
claims passed on are the *claims* -- text and citations, never another role's reasoning,
prompt or model output (see ``Skeptic.context_payload``). A role must be able to disagree
with what was said, not with how it was said.

**A failure is carried, not hidden.** If one role is unavailable, the council still returns
every other role's work and records the failure as a run outcome. Silently dropping an
unavailable role would turn "the skeptic could not run" into "the skeptic found nothing",
which is precisely the confusion that makes a council untrustworthy.

**One rule this module does NOT implement yet, on purpose.** The Guardian's obligation is to
fail CLOSED -- an unavailable guardian must block what it guards. That needs the Guardian
role and something to guard, so it is left for the slice that adds them rather than
half-built here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from meridian.ai.envelope import Claim, Disagreement, ResultStatus
from meridian.ai.role import RoleRun


@dataclass(frozen=True)
class AttributedClaim:
    """A claim, with the role that made it.

    Attribution is not decoration: an unattributed pile of claims is how a disagreement
    becomes invisible, because nothing shows that two conflicting statements came from two
    different roles rather than from one role contradicting itself.
    """

    role: str
    claim: Claim


@dataclass(frozen=True)
class AttributedDisagreement:
    """A disagreement, with the roles on each side. Still no verdict."""

    subject: str
    positions: tuple[tuple[str, Claim], ...]

    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(role for role, _ in self.positions)


@dataclass(frozen=True)
class CouncilMember:
    """One participant. ``run`` receives the question and the claims gathered so far and
    returns a RoleRun, so a member is any role (or any collaborator) with that shape."""

    role: str
    run: Callable[[str, tuple[Claim, ...]], RoleRun]


@dataclass(frozen=True)
class CouncilResult:
    """Every role's work, kept whole.

    There is deliberately no ``conclusion`` field. Adding one would make "the council's
    answer" the thing a caller reaches for, and the first tie-break rule added to compute it
    is the moment this stops being a council.
    """

    question: str
    runs: tuple[tuple[str, RoleRun], ...]
    claims: tuple[AttributedClaim, ...]
    disagreements: tuple[AttributedDisagreement, ...]

    def roles(self) -> tuple[str, ...]:
        return tuple(role for role, _ in self.runs)

    def failures(self) -> tuple[tuple[str, str], ...]:
        """Roles that did not return an ok result, with their outcome. Surfaced rather than
        dropped, so an unavailable role cannot read as a silent one."""
        return tuple(
            (role, run.record.outcome)
            for role, run in self.runs
            if run.result.status is not ResultStatus.OK
        )

    def is_unanimous(self) -> bool:
        """True only when every role returned ok AND nothing conflicts.

        An EMPTY council is not unanimous, and neither is one where a role returned
        UNAVAILABLE. Both would otherwise report agreement on the strength of nobody having
        disagreed -- the same error as reading a skeptic that could not run as a skeptic that
        found nothing.
        """
        if not self.runs:
            return False
        if self.failures():
            return False
        return not self.disagreements


def convene(
    question: str,
    members: Iterable[CouncilMember],
    *,
    respect_fail_closed: bool = True,
) -> CouncilResult:
    """Run every member on one question and keep everything they said.

    ``respect_fail_closed`` short-circuits the council when a member whose permissions say it
    must fail CLOSED returns a non-ok result. It defaults to True so that the rule is applied
    by default rather than remembered by each caller; no role currently declares that
    behaviour except the Guardian, which is not yet implemented, so today this is a guard
    waiting for its subject rather than dead code pretending to be one.
    """
    collected: list[tuple[str, RoleRun]] = []
    accumulated: list[Claim] = []

    for member in members:
        run = member.run(question, tuple(accumulated))
        collected.append((member.role, run))
        if run.result.status is ResultStatus.OK:
            accumulated.extend(run.result.claims)
        elif respect_fail_closed and _must_fail_closed(member.role):
            # Stop here and return what we have. Continuing would produce a conclusion the
            # guardian was supposed to veto, and dropping the guardian instead would hide
            # that the check never ran.
            break

    attributed = tuple(
        AttributedClaim(role=role, claim=claim)
        for role, run in collected
        for claim in run.result.claims
    )
    return CouncilResult(
        question=question,
        runs=tuple(collected),
        claims=attributed,
        disagreements=_disagreements(attributed),
    )


def _must_fail_closed(role: str) -> bool:
    """Whether the role's declared failure behaviour is to block. Read from the permissions
    table rather than duplicated here, so the two cannot drift."""
    from meridian.ai.envelope import permissions_for

    try:
        behaviour = permissions_for(role).failure_behaviour
    except ValueError:
        return False
    return "CLOSED" in behaviour.upper()


def _disagreements(
    claims: Sequence[AttributedClaim],
) -> tuple[AttributedDisagreement, ...]:
    """Group attributed claims by subject and keep the subjects where they conflict.

    Deterministic, and no verdict: the order is the order the claims arrived, and nothing is
    scored. ``detect_disagreements`` does the same grouping on bare claims; this keeps the
    role attribution that a council needs in order to show WHO disagrees with WHOM.
    """
    by_subject: dict[str, list[tuple[str, Claim]]] = {}
    for item in claims:
        if item.claim.subject:
            by_subject.setdefault(item.claim.subject, []).append((item.role, item.claim))

    disagreements: list[AttributedDisagreement] = []
    for subject, positions in by_subject.items():
        if len({claim.text for _, claim in positions}) > 1:
            disagreements.append(
                AttributedDisagreement(subject=subject, positions=tuple(positions))
            )
    return tuple(disagreements)


def plain_disagreements(
    disagreements: Sequence[AttributedDisagreement],
) -> tuple[Disagreement, ...]:
    """The envelope's own Disagreement view, for callers that do not need attribution."""
    return tuple(
        Disagreement(subject=item.subject, claims=tuple(claim for _, claim in item.positions))
        for item in disagreements
    )
