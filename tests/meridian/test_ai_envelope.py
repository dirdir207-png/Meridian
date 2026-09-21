"""Track I.1 — the role envelope and its permissions.

The roadmap demands a **test per role proving it cannot reach a provider write path**, and
that is the centre of this file. The rest guards the properties that make that proof mean
something: that the registry names tools which EXIST (otherwise the proof is about names),
that the classification is complete (a write tool cannot hide as a read tool), and that the
guard actually fires when a grant is wrong (otherwise it is a comment with a function
around it).
"""
import importlib
import json

import pytest

from meridian.ai import envelope
from meridian.ai.envelope import (
    Budget,
    Claim,
    EnvelopeResult,
    EnvelopeTask,
    EvidenceRef,
    ResultStatus,
    RoleCannotWrite,
    RunRecord,
    ToolKind,
    UnsupportedClaim,
    assert_role_cannot_write,
    evidence_in_scope,
    permissions_for,
    provider_write_tool_names,
    role_can_reach_provider_write,
    validate_citations,
)

ALL_ROLES = sorted(envelope.ROLE_PERMISSIONS)


def _ref(evidence_id: str = "evidence:1") -> EvidenceRef:
    return EvidenceRef(
        id=evidence_id,
        provenance="gmail:message/abc",
        observed_at="2026-09-08T11:42:00Z",
        freshness="2h",
        confidence=0.8,
    )


def _task(role: str = "forecaster", evidence=()) -> EnvelopeTask:
    return EnvelopeTask(role=role, question="What is coming?", evidence=tuple(evidence))


# ---------------------------------------------------------------------------------------
# THE ANTI-DRIFT CHECK: a registry of names that resolve to nothing would keep passing
# after the write surface was renamed or replaced.
# ---------------------------------------------------------------------------------------

def _resolve(dotted: str):
    """Resolve a dotted path to the object it names.

    A target may address a module-level function (``a.b.func``) or a method
    (``a.b.Class.method``), so the module boundary is not simply the last dot. Import the
    LONGEST importable prefix, then walk the remaining attributes -- and fail loudly if any
    step is missing, because a registry entry that resolves to nothing is the drift this
    check exists to catch.
    """
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        module_path = ".".join(parts[:split])
        try:
            obj = importlib.import_module(module_path)
        except ImportError:
            continue
        for attribute in parts[split:]:
            if not hasattr(obj, attribute):
                raise AssertionError(f"{dotted}: {module_path} has no attribute {attribute!r}")
            obj = getattr(obj, attribute)
        return obj
    raise AssertionError(f"{dotted}: no importable module prefix")


@pytest.mark.parametrize("tool_name", sorted(envelope.TOOL_REGISTRY))
def test_every_registered_tool_resolves_to_a_real_callable(tool_name):
    """Each ToolSpec.target must import. This test is the reason the registry is trustworthy:
    it fails if the tool it names has been renamed, moved or deleted."""
    spec = envelope.TOOL_REGISTRY[tool_name]
    assert "." in spec.target, f"{tool_name} target is not a dotted path: {spec.target!r}"
    assert callable(_resolve(spec.target)), f"{spec.target} is not callable"


def test_the_write_surface_is_actually_classified_as_write():
    """The registry's whole claim is that the write entry point is marked. If
    `execute_crew_write` were absent or misclassified, every role would 'pass' the
    no-write test while the real write path sat outside the model."""
    writes = provider_write_tool_names()
    assert "crew_write" in writes
    assert "crew_reconcile" in writes
    # And it must point at the real mutation entry point, not a copy of the name.
    assert envelope.TOOL_REGISTRY["crew_write"].target == "meridian.crew_write.execute_crew_write"


def test_no_tool_is_left_unclassified():
    """ToolKind is the only thing distinguishing a read from a write, so a missing kind
    would silently be read as harmless."""
    for name, spec in envelope.TOOL_REGISTRY.items():
        assert isinstance(spec.kind, ToolKind), name


# ---------------------------------------------------------------------------------------
# THE ROADMAP'S REQUIREMENT: one test per role
# ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("role", ALL_ROLES)
def test_role_cannot_reach_a_provider_write_path(role):
    """One case per role. This is the roadmap's I.1 acceptance condition."""
    permissions = permissions_for(role)
    assert not permissions.tools & provider_write_tool_names(), (
        f"{role} holds a provider write tool: {sorted(permissions.tools & provider_write_tool_names())}"
    )
    # And the guard agrees.
    assert_role_cannot_write(role)
    assert role_can_reach_provider_write(role) is False


@pytest.mark.parametrize("role", ALL_ROLES)
def test_every_role_is_read_or_propose_only(role):
    """Not just 'no write tool': every granted tool must be READ or PROPOSE, so a role
    cannot acquire an effect under a new kind that was never considered."""
    for tool_name in permissions_for(role).tools:
        spec = envelope.TOOL_REGISTRY[tool_name]
        assert spec.kind in {ToolKind.READ, ToolKind.PROPOSE}, (role, tool_name, spec.kind)


@pytest.mark.parametrize("role", ALL_ROLES)
def test_every_role_declares_a_failure_behaviour(role):
    """An unavailable role must have decided in advance what it does, rather than leaving a
    caller to interpret silence. The Guardian is the one that must fail CLOSED."""
    behaviour = permissions_for(role).failure_behaviour
    assert isinstance(behaviour, str) and behaviour.strip()
    if role == "guardian":
        assert "CLOSED" in behaviour.upper()


def test_the_council_roles_named_by_the_roadmap_all_exist():
    """I.2 ships one role and I.3 composes them; all five named roles must be present so a
    permission exists before the role that needs it."""
    assert set(ALL_ROLES) == {"forecaster", "investigator", "skeptic", "guardian", "teacher"}


# ---------------------------------------------------------------------------------------
# FALSIFICATION: the guard must FIRE, or it is decoration
# ---------------------------------------------------------------------------------------

def test_granting_a_role_a_write_tool_raises(monkeypatch):
    """The falsifier. If this passed without raising, the per-role tests above would prove
    nothing about the guard."""
    widened = envelope.RolePermissions(
        role="forecaster",
        purpose="widened by a careless edit",
        tools=frozenset({"read_dial", "crew_write"}),
        evidence_scope=frozenset({"dial"}),
        failure_behaviour="n/a",
    )
    monkeypatch.setitem(envelope.ROLE_PERMISSIONS, "forecaster", widened)
    with pytest.raises(RoleCannotWrite, match="provider write tool"):
        assert_role_cannot_write("forecaster")
    assert role_can_reach_provider_write("forecaster") is True


def test_granting_an_unregistered_tool_is_also_refused(monkeypatch):
    """`tools` is a CLOSED set. An unknown name would grant nothing while reading as though
    it granted something, so it is refused rather than ignored."""
    widened = envelope.RolePermissions(
        role="teacher",
        purpose="typo in the tool name",
        tools=frozenset({"read_diall"}),
        evidence_scope=frozenset({"dial"}),
        failure_behaviour="n/a",
    )
    monkeypatch.setitem(envelope.ROLE_PERMISSIONS, "teacher", widened)
    with pytest.raises(RoleCannotWrite, match="unregistered tool"):
        assert_role_cannot_write("teacher")


def test_the_import_time_invariant_is_wired(monkeypatch):
    """The module checks itself when imported, so a bad grant breaks the import rather than
    shipping a permission that only reads as safe."""
    assert hasattr(envelope, "_assert_registry_is_safe")
    monkeypatch.setitem(
        envelope.ROLE_PERMISSIONS,
        "skeptic",
        envelope.RolePermissions(
            role="skeptic",
            purpose="bad",
            tools=frozenset({"crew_reconcile"}),
            evidence_scope=frozenset({"evidence"}),
            failure_behaviour="n/a",
        ),
    )
    with pytest.raises(RoleCannotWrite):
        envelope._assert_registry_is_safe()


# ---------------------------------------------------------------------------------------
# The envelope contract
# ---------------------------------------------------------------------------------------

def test_an_unknown_role_is_refused_at_task_construction():
    with pytest.raises(ValueError, match="unknown role"):
        EnvelopeTask(role="auditor", question="hello")


def test_a_budget_cannot_be_unbounded():
    for kwargs in (
        {"max_tokens": 0, "max_seconds": 30, "max_tool_calls": 4},
        {"max_tokens": 100, "max_seconds": -1, "max_tool_calls": 4},
        {"max_tokens": 100, "max_seconds": 30, "max_tool_calls": 0},
    ):
        with pytest.raises(ValueError, match="positive integer"):
            Budget(**kwargs)


def test_evidence_confidence_is_bounded():
    for value in (-0.1, 1.1):
        with pytest.raises(ValueError, match="between 0 and 1"):
            EvidenceRef(
                id="evidence:1",
                provenance="p",
                observed_at="2026-09-08T00:00:00Z",
                freshness="1d",
                confidence=value,
            )


def test_an_ok_result_must_carry_claims_and_a_failure_must_not():
    """The unavailable/failed state is part of the shape, so a failure cannot be mistaken
    for an empty answer -- and an 'ok' cannot be empty either."""
    with pytest.raises(ValueError, match="at least one claim"):
        EnvelopeResult(status=ResultStatus.OK, claims=())
    with pytest.raises(ValueError, match="must not carry claims"):
        EnvelopeResult(status=ResultStatus.UNAVAILABLE, claims=(Claim(text="x", evidence_ids=("evidence:1",)),))
    # Both legitimate shapes construct.
    EnvelopeResult(status=ResultStatus.UNAVAILABLE, detail="model unavailable")
    EnvelopeResult(status=ResultStatus.OK, claims=(Claim(text="Rent is due", evidence_ids=("evidence:1",)),))


def test_citations_must_come_from_the_task_and_every_claim_must_cite():
    task = _task(evidence=[_ref("evidence:1")])
    validate_citations(
        EnvelopeResult(
            status=ResultStatus.OK,
            claims=(Claim(text="Rent is due", evidence_ids=("evidence:1",)),),
        ),
        task,
    )
    # A claim citing evidence the task never supplied is refused.
    with pytest.raises(UnsupportedClaim, match="outside the task"):
        validate_citations(
            EnvelopeResult(
                status=ResultStatus.OK,
                claims=(Claim(text="Invented", evidence_ids=("evidence:999",)),),
            ),
            task,
        )
    # An uncited claim is refused too: "claims each cited to evidence IDs".
    with pytest.raises(UnsupportedClaim, match="no evidence citation"):
        validate_citations(
            EnvelopeResult(status=ResultStatus.OK, claims=(Claim(text="Uncited", evidence_ids=()),)),
            task,
        )


def test_evidence_scope_is_namespaced_and_defaults_to_denied():
    assert evidence_in_scope("forecaster", ["accounts:1", "dial:2026-09-08"])
    assert not evidence_in_scope("forecaster", ["evidence:1"])  # outside the forecaster's scope
    # An unscoped id is denied rather than allowed by default.
    assert not evidence_in_scope("forecaster", ["1"])
    assert not evidence_in_scope("forecaster", [""])


def test_the_run_record_carries_what_an_audit_needs():
    """A proposal must be traceable back to the reasoning that produced it, so every field
    the roadmap names must survive serialisation."""
    record = RunRecord(
        role="forecaster",
        provider="openrouter",
        model="example/model",
        prompt_version="forecaster-v1",
        evidence_ids=("dial:2026-09-08",),
        started_at="2026-09-08T11:42:00Z",
        ended_at="2026-09-08T11:42:03Z",
        outcome="ok",
    )
    payload = json.loads(json.dumps(record.as_dict()))
    for key in (
        "role", "provider", "model", "prompt_version",
        "evidence_ids", "started_at", "ended_at", "outcome",
    ):
        assert payload[key] is not None, key
    assert payload["evidence_ids"] == ["dial:2026-09-08"]


def test_the_envelope_module_calls_no_model_and_holds_no_credential():
    """The envelope defines a contract; it must not become a second, unguarded AI path.
    Checked against the source so a future edit that reaches for a client is caught."""
    source = (envelope.__file__ or "")
    text = open(source, encoding="utf-8").read()
    for forbidden in ("requests.", "openai", "api_key", "os.environ", "subprocess"):
        assert forbidden not in text, forbidden
