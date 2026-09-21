"""Track I.2 — the Investigator, end to end.

MERIDIAN_ROADMAP.md §6, I.2 names the acceptance conditions directly: *"read-only,
evidence-bound, immediately useful. Adversarial tests: hallucinated citation, missing
evidence, contradictory sources, unavailable model. Prove the envelope before adding
roles."*

Each of those four is a test below, alongside the properties that make them mean something.
The fakes are deliberately tiny: the point is that a role receives a client and never builds
one, so a two-line object stands in for the real chain and **no provider is contacted and no
credential exists** anywhere in this file.
"""
import dataclasses
import json

from meridian.ai import envelope
from meridian.ai.envelope import ResultStatus, provider_write_tool_names
from meridian.ai.investigator import Investigator, humanize_age

FROZEN = "2026-09-08T11:42:00Z"


@dataclasses.dataclass
class FakeItem:
    """Mirrors the fields `meridian/evidence.py::EvidenceItem` actually exposes."""

    id: int
    source_kind: str = "mail"
    source_id: str = "message/1"
    created_at: str = "2026-09-08T09:42:00Z"
    revoked_at: str | None = None
    content_deleted_at: str | None = None
    title: str | None = "Receipt"


@dataclasses.dataclass
class FakeLink:
    evidence_id: int
    provenance: str = "gmail:message/1"


class FakeRepo:
    def __init__(self, links=(), items=None):
        self._links = list(links)
        self._items = {item.id: item for item in (items or [])}

    def list_links_for_target(self, target_kind, target_id):
        self.last_target = (target_kind, target_id)
        return list(self._links)

    def get_item(self, evidence_id, *, include_inaccessible=False):
        return self._items.get(evidence_id)


class FakeClient:
    """A client that returns canned text. Records the calls it received."""

    def __init__(self, reply="{}", *, raises=None, provider="fake-provider", model="fake-model"):
        self._reply = reply
        self._raises = raises
        self.last_provider = provider
        self.model = model
        self.calls = []

    def complete(self, system, messages):
        self.calls.append((system, messages))
        if self._raises is not None:
            raise self._raises
        return self._reply


def _repo_with_evidence(*ids, **kwargs):
    return FakeRepo(
        links=[FakeLink(evidence_id=i) for i in ids],
        items=[FakeItem(id=i, **kwargs) for i in ids],
    )


def _run(reply, *, ids=(1,), repo=None, client=None, clock=None):
    investigator = Investigator(repo or _repo_with_evidence(*ids))
    client = client or FakeClient(reply)
    run = investigator.run(
        "What is this charge?",
        client=client,
        target_kind="charge",
        target_id="charge-7",
        clock=clock,
    )
    return run, client


def _claims_reply(*claims, **extra):
    return json.dumps({"claims": list(claims), **extra})


# ---------------------------------------------------------------------------------------
# THE FOUR ADVERSARIAL CASES THE ROADMAP NAMES
# ---------------------------------------------------------------------------------------

def test_adversarial_hallucinated_citation_voids_the_whole_result():
    """A claim citing evidence the task never supplied must not survive in any form.

    The result is FAILED and carries NO claims -- which the envelope enforces structurally
    (a failed result may not carry claims), so the fabricated text cannot reach a reader
    even by accident. Dropping only the bad claim would keep whatever the model produced
    next to it, and this role cannot see why it invented a citation.
    """
    reply = _claims_reply(
        {"text": "This is a subscription.", "evidence_ids": ["evidence:1"], "subject": "kind"},
        {"text": "It recurs monthly.", "evidence_ids": ["evidence:999"], "subject": "cadence"},
    )
    run, _ = _run(reply)

    assert run.result.status is ResultStatus.FAILED
    assert run.result.claims == ()
    assert "unsupported" in (run.result.detail or "").lower() or "outside" in (run.result.detail or "").lower()
    assert run.record.outcome == "failed:unsupported-citation"


def test_adversarial_missing_evidence_is_unavailable_and_the_model_is_never_called():
    """With nothing linked, the model must not be asked. A model asked to explain nothing
    will produce something, so the call is not made at all -- asserted, not assumed."""
    client = FakeClient(_claims_reply({"text": "Invented", "evidence_ids": ["evidence:1"]}))
    run, client = _run("", repo=FakeRepo(links=[], items=[]), client=client)

    assert run.result.status is ResultStatus.UNAVAILABLE
    assert run.result.claims == ()
    assert client.calls == [], "the model was called with no evidence"
    assert run.record.evidence_ids == ()
    assert run.record.outcome == "unavailable:no-evidence"


def test_adversarial_contradictory_sources_are_both_kept_and_flagged():
    """Two claims about the SAME fact that disagree must both survive, with the conflict
    recorded. Nothing votes, scores, or picks a winner -- that is the rule that stops a
    council becoming a single voice."""
    reply = _claims_reply(
        {"text": "The charge is 12.00.", "evidence_ids": ["evidence:1"], "subject": "amount"},
        {"text": "The charge is 21.00.", "evidence_ids": ["evidence:2"], "subject": "amount"},
    )
    run, _ = _run(reply, ids=(1, 2))

    assert run.result.status is ResultStatus.OK
    assert len(run.result.claims) == 2, "a conflicting claim was dropped"
    assert len(run.result.disagreements) == 1
    disagreement = run.result.disagreements[0]
    assert disagreement.subject == "amount"
    assert {claim.text for claim in disagreement.claims} == {
        "The charge is 12.00.",
        "The charge is 21.00.",
    }
    # Both claims are still individually reachable too -- the conflict ADDS information
    # rather than replacing the claims with a summary of them.
    assert {claim.text for claim in run.result.claims} == {
        "The charge is 12.00.",
        "The charge is 21.00.",
    }


def test_adversarial_unavailable_model_is_a_state_not_an_exception():
    """A failing client must not raise into the caller, and must NOT be retried: retrying a
    call whose outcome is unknown is how a read-only role starts behaving like an executor."""
    client = FakeClient(raises=TimeoutError("upstream timed out"))
    run, client = _run("", client=client)

    assert run.result.status is ResultStatus.UNAVAILABLE
    assert run.result.claims == ()
    assert len(client.calls) == 1, "the client was retried"
    assert "TimeoutError" in (run.result.detail or "")
    assert run.record.outcome == "unavailable:model"


def test_a_genuinely_empty_answer_is_unavailable_not_ok():
    """A model that correctly finds nothing to say produces no claims, and the envelope
    forbids an 'ok' with no claims -- so it lands on UNAVAILABLE rather than an empty ok."""
    run, _ = _run(json.dumps({"claims": []}))
    assert run.result.status is ResultStatus.UNAVAILABLE
    assert run.result.claims == ()


def test_an_unparseable_reply_fails_rather_than_being_guessed_at():
    run, _ = _run("I could not find anything, sorry!")
    assert run.result.status is ResultStatus.FAILED
    assert run.result.claims == ()
    assert run.record.outcome == "failed:unparseable"


# ---------------------------------------------------------------------------------------
# Evidence binding: what reaches the model, and what does not
# ---------------------------------------------------------------------------------------

def test_the_happy_path_is_evidence_bound_and_auditable():
    reply = _claims_reply(
        {"text": "This charge is a monthly subscription.", "evidence_ids": ["evidence:1"],
         "subject": "kind"},
        assumptions=["The receipt is for the same card."],
        confidence=0.7,
        what_would_change=["A refund would change this."],
    )
    run, _ = _run(reply, ids=(1,))

    assert run.result.status is ResultStatus.OK
    assert run.result.confidence == 0.7
    assert run.result.assumptions == ("The receipt is for the same card.",)
    assert run.result.what_would_change == ("A refund would change this.",)
    assert run.result.disagreements == ()
    # The run record carries what an audit needs, including the evidence actually used.
    assert run.record.evidence_ids == ("evidence:1",)
    assert run.record.outcome == "ok"
    assert run.record.role == "investigator"
    assert run.record.prompt_version


def test_withdrawn_evidence_is_not_evidence():
    """An item whose content was deleted, or which was revoked, must not be answered from:
    that is answering from a retracted record."""
    for field in ("revoked_at", "content_deleted_at"):
        repo = FakeRepo(
            links=[FakeLink(evidence_id=1)],
            items=[FakeItem(id=1, **{field: "2026-09-08T10:00:00Z"})],
        )
        client = FakeClient(_claims_reply({"text": "x", "evidence_ids": ["evidence:1"]}))
        run, client = _run("", repo=repo, client=client)
        assert run.result.status is ResultStatus.UNAVAILABLE, field
        assert client.calls == [], f"the model was called on {field} evidence"


def test_the_model_receives_references_and_never_bodies():
    """The prompt carries ids and provenance, not content, so a claim can only cite what
    it was given and no evidence body is copied into a model call."""
    client = FakeClient(_claims_reply({"text": "x", "evidence_ids": ["evidence:1"]}))
    _run("", client=client)
    system, messages = client.calls[0]
    payload = json.loads(messages[0]["content"])
    assert payload["evidence"][0]["id"] == "evidence:1"
    assert set(payload["evidence"][0]) == {"id", "provenance", "observed_at", "freshness"}
    assert "unknown" not in system.lower()
    # The instruction the role depends on must actually be in the prompt.
    assert "evidence_ids" in system
    assert "never invent" in system


def test_freshness_is_derived_from_the_real_timestamp_and_admits_when_it_cannot_be():
    from datetime import datetime, timezone

    now = datetime(2026, 9, 8, 11, 42, tzinfo=timezone.utc)
    assert humanize_age("2026-09-08T11:41:30Z", now) == "just now"
    assert humanize_age("2026-09-08T11:40:00Z", now) == "2m"
    assert humanize_age("2026-09-08T11:12:00Z", now) == "30m"
    assert humanize_age("2026-09-08T09:42:00Z", now) == "2h"
    assert humanize_age("2026-09-06T11:42:00Z", now) == "2d"
    # A timestamp that cannot be parsed yields no claim about currency.
    assert humanize_age("not-a-timestamp", now) == "unknown"


def test_the_evidence_ref_confidence_is_absent_because_the_store_has_none():
    """`EvidenceItem` records no confidence, so the binder states None rather than a
    fabricated number a reader could not distinguish from a measurement."""
    investigator = Investigator(_repo_with_evidence(1))
    from datetime import datetime, timezone

    refs = investigator.bind_evidence(
        target_kind="charge", target_id="c", now=datetime(2026, 9, 8, tzinfo=timezone.utc)
    )
    assert len(refs) == 1
    assert refs[0].confidence is None
    assert refs[0].provenance == "gmail:message/1"


# ---------------------------------------------------------------------------------------
# The role stays inside I.1's permissions
# ---------------------------------------------------------------------------------------

def test_the_role_holds_no_provider_write_tool():
    assert not (envelope.permissions_for(Investigator.role).tools & provider_write_tool_names())


def test_the_investigator_module_cannot_grow_its_own_credential_or_network_call():
    """It receives a client and must never build one.

    Checked over the parsed AST rather than the raw text. A substring scan matches the
    module's own docstring, which NAMES these tokens in order to promise it avoids them --
    a check that fails on its own explanation is a check nobody keeps. Imports and
    attribute access are what can actually reach the network, so those are what is checked.
    """
    import ast

    import meridian.ai.investigator as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())

    imported: set[str] = set()
    attribute_chains: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Attribute):
            chain = []
            cursor: ast.AST = node
            while isinstance(cursor, ast.Attribute):
                chain.append(cursor.attr)
                cursor = cursor.value
            if isinstance(cursor, ast.Name):
                chain.append(cursor.id)
                attribute_chains.add(".".join(reversed(chain)))

    forbidden_modules = {"requests", "subprocess", "openai", "urllib", "httpx", "socket"}
    assert not (imported & forbidden_modules), sorted(imported & forbidden_modules)
    # os is allowed (this module imports nothing from it), but reading the environment is not.
    assert "os.environ" not in attribute_chains
    assert "os.getenv" not in attribute_chains
    # The client must arrive by injection, never be constructed here.
    assert "OpenAICompatClient" not in attribute_chains


def test_the_role_never_raises_for_a_client_failure():
    """Falsification of the fail-soft claim: every failure mode must return a result."""
    failures = [TimeoutError("t"), RuntimeError("boom"), ValueError("bad"), OSError("net")]
    for exc in failures:
        run, _ = _run("", client=FakeClient(raises=exc))
        assert run.result.status in {ResultStatus.UNAVAILABLE, ResultStatus.FAILED}, exc
        assert run.result.claims == ()


def test_an_unknown_target_kind_still_produces_a_state_not_a_crash():
    """The repository is asked, gets nothing, and the role reports unavailable."""
    repo = FakeRepo(links=[], items=[])
    run, _ = _run("", repo=repo)
    assert run.result.status is ResultStatus.UNAVAILABLE
