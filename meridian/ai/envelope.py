"""Track I.1 — the role envelope and its permissions.

MERIDIAN_ROADMAP.md §6, **I.1 — Envelope *and permissions***: *"One typed task/result
contract every role uses ... input — the question, an evidence bundle (references with
provenance, freshness, confidence), the requester's authority context, and a budget
(time/tokens). output — claims each cited to evidence IDs, explicit assumptions, a
confidence, what would change the answer, and an unavailable/failed state. run record —
model and provider, prompt version, evidence used, timing, outcome, persisted so a proposal
can be audited back to the reasoning that produced it. **Permissions ship with the envelope,
not after it** ... with a test per role proving it cannot reach a provider write path. No
role ever receives a provider write tool."*

**This module's only power is to REFUSE.** It executes nothing, calls no model, and holds
no credential. It defines the contract and the grants, and it makes the central claim —
*no role can reach a provider write path* — a property that is CHECKED rather than
asserted in prose.

**Why the grants name real callables.** ``ToolSpec.target`` is a dotted path to the function
that actually is the tool, and ``tests/meridian/test_ai_envelope.py`` imports every one of
them. A registry of names that resolve to nothing would keep passing after the write surface
was renamed or replaced, which is exactly the drift this is supposed to prevent: the guard
would still say "no role can write" while pointing at a function that no longer exists.
Import failures are therefore a test failure, not a warning.

**The invariant is enforced at import.** ``_assert_registry_is_safe()`` runs when this module
is imported and raises if any role has been granted a write tool. A future edit that widens a
grant breaks immediately and loudly, rather than shipping a permission that reads as safe.
``PROVIDER_WRITE`` is deliberately *not* a role option: it exists so that grants can be
CHECKED against it, and so that a write tool cannot be added to the registry without being
classified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

# --------------------------------------------------------------------------------------
# Tools: the real surface, classified
# --------------------------------------------------------------------------------------


class ToolKind(str, Enum):
    """What a tool can do. The ONLY kind a role may never hold is ``PROVIDER_WRITE``."""

    # Reads Meridian's own state. Cannot change anything anywhere.
    READ = "read"
    # Read-only, but its output is a PROPOSAL that a human must approve before anything
    # happens. It is a distinct kind because "produces a proposal" is a capability worth
    # seeing explicitly in a grant, while still being unable to act.
    PROPOSE = "propose"
    # Mutates financial state at the provider. No role is ever granted this.
    PROVIDER_WRITE = "provider_write"


@dataclass(frozen=True)
class ToolSpec:
    """One tool, classified, pointing at the real callable.

    ``target`` is a dotted import path resolved by the test suite (see the module
    docstring): the registry is only meaningful if the tools it names exist.
    """

    name: str
    kind: ToolKind
    target: str
    description: str


# The write entry point. `execute_crew_write` is where a financial mutation actually
# reaches Crew, and `reconcile_crew_mutation` is its post-write bookkeeping -- both are
# provider-write by construction. Note that `execute_crew_write` already reports
# `retry_allowed: False` and raises `CrewWriteUncertain` rather than retrying; the
# envelope must not add a retry around it.
_PROVIDER_WRITE_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="crew_write",
        kind=ToolKind.PROVIDER_WRITE,
        target="meridian.crew_write.execute_crew_write",
        description="Execute one approved Crew write, reaching the provider.",
    ),
    ToolSpec(
        name="crew_reconcile",
        kind=ToolKind.PROVIDER_WRITE,
        target="meridian.mutations.reconcile_crew_mutation",
        description="Reconcile local state after an approved Crew write.",
    ),
)

_READ_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="read_accounts",
        kind=ToolKind.READ,
        target="meridian.repository.FinancialRepository.list_accounts",
        description="Read the owner's accounts and their observed balances.",
    ),
    ToolSpec(
        name="read_evidence",
        kind=ToolKind.READ,
        target="meridian.evidence.EvidenceRepository.list_items",
        description="Read stored evidence items with their provenance.",
    ),
    ToolSpec(
        name="read_dial",
        kind=ToolKind.READ,
        target="meridian.services.dial.build_dial",
        description="Read the forward dial: near-term dated events and their funding.",
    ),
)

_PROPOSE_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="propose_funding",
        kind=ToolKind.PROPOSE,
        target="meridian.funding_proposals.propose_due_funding",
        description="Propose funding for due commitments. Produces proposals only.",
    ),
)

TOOL_REGISTRY: Mapping[str, ToolSpec] = {
    spec.name: spec
    for spec in (*_READ_TOOLS, *_PROPOSE_TOOLS, *_PROVIDER_WRITE_TOOLS)
}


def provider_write_tool_names() -> frozenset[str]:
    """Every tool that can reach a provider write path."""
    return frozenset(
        name for name, spec in TOOL_REGISTRY.items() if spec.kind is ToolKind.PROVIDER_WRITE
    )


# --------------------------------------------------------------------------------------
# The typed envelope
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Budget:
    """What a role may spend on one task. Bounded by construction: every field is required
    and must be positive, so an unbounded run cannot be expressed."""

    max_tokens: int
    max_seconds: int
    max_tool_calls: int

    def __post_init__(self) -> None:
        for name, value in (
            ("max_tokens", self.max_tokens),
            ("max_seconds", self.max_seconds),
            ("max_tool_calls", self.max_tool_calls),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"budget {name} must be a positive integer, got {value!r}")


@dataclass(frozen=True)
class EvidenceRef:
    """A reference to evidence, carrying the provenance a reader needs to weigh it.

    Deliberately NOT the evidence body: the envelope passes references, so a result cannot
    smuggle content that was never fetched under the role's scope.
    """

    id: str
    provenance: str
    observed_at: str
    freshness: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError("evidence id is required")
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise ValueError("evidence confidence must be a number")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")


@dataclass(frozen=True)
class EnvelopeTask:
    """The input contract: question, evidence, the requester's authority, and a budget."""

    role: str
    question: str
    evidence: tuple[EvidenceRef, ...] = ()
    authority: str = "owner"
    budget: Budget = field(
        default_factory=lambda: Budget(max_tokens=2048, max_seconds=30, max_tool_calls=4)
    )

    def __post_init__(self) -> None:
        if self.role not in ROLE_PERMISSIONS:
            raise ValueError(f"unknown role: {self.role!r}")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("question is required")
        budget = self.budget
        if not isinstance(budget, Budget):
            raise ValueError("budget must be a Budget")


@dataclass(frozen=True)
class Claim:
    """One statement in a result, cited to the evidence that supports it."""

    text: str
    evidence_ids: tuple[str, ...] = ()


class ResultStatus(str, Enum):
    """A result is never merely absent. `UNAVAILABLE` and `FAILED` are states a caller must
    be able to see and show, so a failure can never be mistaken for an empty answer."""

    OK = "ok"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True)
class EnvelopeResult:
    """The output contract. The unavailable/failed state is part of the shape, not an
    exception the caller may forget to handle."""

    status: ResultStatus
    claims: tuple[Claim, ...] = ()
    assumptions: tuple[str, ...] = ()
    confidence: float = 0.0
    what_would_change: tuple[str, ...] = ()
    proposals: tuple[Mapping[str, Any], ...] = ()
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ResultStatus):
            raise ValueError("status must be a ResultStatus")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status is ResultStatus.OK and not self.claims:
            raise ValueError("an ok result must carry at least one claim")
        if self.status is not ResultStatus.OK and self.claims:
            raise ValueError("an unavailable or failed result must not carry claims")


@dataclass(frozen=True)
class RunRecord:
    """The audit trail: which role asked what, on which evidence, with which model and
    prompt, how long it took, and how it ended. Persisted (by the caller) so a proposal can
    be traced back to the reasoning that produced it."""

    role: str
    provider: str
    model: str
    prompt_version: str
    evidence_ids: tuple[str, ...]
    started_at: str
    ended_at: str
    outcome: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "provider": self.provider,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "evidence_ids": list(self.evidence_ids),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "outcome": self.outcome,
        }


# --------------------------------------------------------------------------------------
# Permissions: shipped WITH the envelope
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RolePermissions:
    """What one role may do. ``tools`` is the whole authority surface: a role can do
    nothing that is not named here, so an omitted tool is an unavailable capability rather
    than a forgotten check."""

    role: str
    purpose: str
    tools: frozenset[str]
    evidence_scope: frozenset[str]
    failure_behaviour: str


def _read_only(tools: Sequence[str], evidence_scope: Sequence[str]) -> frozenset[str]:
    return frozenset(tools)


# The council roles named by the roadmap (I.2 ships one of them; I.3 composes them). Every
# grant below is READ or PROPOSE only -- and `_assert_registry_is_safe()` proves it rather
# than trusting this comment.
ROLE_PERMISSIONS: Mapping[str, RolePermissions] = {
    "forecaster": RolePermissions(
        role="forecaster",
        purpose="Project what is coming and what it does to the funding picture.",
        tools=frozenset({"read_accounts", "read_dial", "propose_funding"}),
        evidence_scope=frozenset({"accounts", "commitments", "charges", "dial"}),
        failure_behaviour="Report unavailable with no claims; never estimate a number.",
    ),
    "investigator": RolePermissions(
        role="investigator",
        purpose="Find the evidence behind a charge, an event or a discrepancy.",
        tools=frozenset({"read_evidence", "read_accounts"}),
        evidence_scope=frozenset({"evidence", "accounts", "charges"}),
        failure_behaviour="Report unavailable with no claims; never assert an unread record.",
    ),
    "skeptic": RolePermissions(
        role="skeptic",
        purpose="Supply counterexamples and attack a claim's evidence.",
        tools=frozenset({"read_evidence", "read_dial"}),
        evidence_scope=frozenset({"evidence", "dial", "commitments"}),
        failure_behaviour="Report unavailable; a skeptic that cannot read is silent, not agreeable.",
    ),
    "guardian": RolePermissions(
        role="guardian",
        purpose="Object on policy, authority and evidence grounds.",
        tools=frozenset({"read_evidence"}),
        evidence_scope=frozenset({"evidence", "policy"}),
        failure_behaviour="Fail CLOSED: an unavailable guardian must block the proposal it guards.",
    ),
    "teacher": RolePermissions(
        role="teacher",
        purpose="Explain a decision in plain language from the recorded evidence.",
        tools=frozenset({"read_evidence", "read_dial"}),
        evidence_scope=frozenset({"evidence", "dial", "accounts", "commitments"}),
        failure_behaviour="Report unavailable; never explain from memory rather than evidence.",
    ),
}


class RoleCannotWrite(Exception):
    """Raised when a role is found holding a provider write tool."""


def permissions_for(role: str) -> RolePermissions:
    try:
        return ROLE_PERMISSIONS[role]
    except KeyError:
        raise ValueError(f"unknown role: {role!r}") from None


def role_can_reach_provider_write(role: str) -> bool:
    """True if the role holds any provider write tool. Must be False for every role."""
    permissions = permissions_for(role)
    return bool(permissions.tools & provider_write_tool_names())


def assert_role_cannot_write(role: str) -> None:
    """Raise unless the role provably cannot reach a provider write path.

    The second clause is not redundant: a role holding a tool name that is not in the
    registry is ALSO refused, because ``tools`` is a closed set and an unknown name would
    silently grant nothing while reading as though it granted something.
    """
    permissions = permissions_for(role)
    unknown = permissions.tools - set(TOOL_REGISTRY)
    if unknown:
        raise RoleCannotWrite(f"role {role!r} holds unregistered tool(s): {sorted(unknown)}")
    if role_can_reach_provider_write(role):
        raise RoleCannotWrite(
            f"role {role!r} holds a provider write tool: "
            f"{sorted(permissions.tools & provider_write_tool_names())}"
        )


def _assert_registry_is_safe() -> None:
    """Import-time invariant. Any role granted a write tool breaks the import itself.

    This is deliberately a hard failure rather than a warning: a permission that reads as
    safe while being unsafe is worse than a module that will not load.
    """
    for role in ROLE_PERMISSIONS:
        assert_role_cannot_write(role)


# --------------------------------------------------------------------------------------
# Result validation
# --------------------------------------------------------------------------------------


class UnsupportedClaim(Exception):
    """Raised when a result claims more than its task allowed it to see."""


def validate_citations(result: EnvelopeResult, task: EnvelopeTask) -> None:
    """Every cited id must come from the task's own evidence, and every claim must cite.

    This generalises the citation check the advisor already performs
    (``meridian/ai/advisor.py``: a response citing evidence outside its context raises
    ``UnsupportedAdvisorClaim``) so that EVERY role inherits it rather than each re-deriving
    it. An uncited claim is refused too: the roadmap's contract is "claims each cited to
    evidence IDs", and a claim with no citation is precisely the unsupported assertion the
    evidence discipline exists to prevent.
    """
    allowed = {ref.id for ref in task.evidence}
    for claim in result.claims:
        if not claim.evidence_ids:
            raise UnsupportedClaim(f"claim has no evidence citation: {claim.text!r}")
        outside = set(claim.evidence_ids) - allowed
        if outside:
            raise UnsupportedClaim(
                f"claim cites evidence outside the task: {sorted(outside)}"
            )


def evidence_in_scope(role: str, evidence_ids: Sequence[str]) -> bool:
    """Whether every id is inside the role's evidence scope.

    Ids are namespaced ``<scope>:<rest>`` so a scope can be checked without reading the
    record. An id with no namespace is out of scope for every role rather than defaulting
    to allowed.
    """
    scope = permissions_for(role).evidence_scope
    for raw in evidence_ids:
        if not isinstance(raw, str) or ":" not in raw:
            return False
        if raw.split(":", 1)[0] not in scope:
            return False
    return True


_assert_registry_is_safe()
