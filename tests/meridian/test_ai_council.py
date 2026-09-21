"""Track I.3 — the Skeptic and the council.

The roadmap's I.3 requires multi-role deliberation where *"disagreement is recorded and
shown, never settled by majority vote"*. These tests hold that line: they fail if anyone
later adds a verdict, a score, a vote or a tie-break.

No provider is contacted: every client is a fake.
"""
import ast
import dataclasses
import json
from pathlib import Path

import pytest

from meridian.ai import council as council_module
from meridian.ai.council import (
    AttributedClaim,
    CouncilMember,
    convene,
    plain_disagreements,
)
from meridian.ai.envelope import Claim, ResultStatus
from meridian.ai.investigator import Investigator
from meridian.ai.skeptic import Skeptic

ROOT = Path(__file__).resolve().parents[2]


@dataclasses.dataclass
class FakeItem:
    id: int
    source_kind: str = "mail"
    source_id: str = "message/1"
    created_at: str = "2026-09-08T09:42:00Z"
    revoked_at: str | None = None
    content_deleted_at: str | None = None


@dataclasses.dataclass
class FakeLink:
    evidence_id: int
    provenance: str = "gmail:message/1"


class FakeRepo:
    def __init__(self, ids=(1, 2)):
        self._ids = list(ids)

    def list_links_for_target(self, target_kind, target_id):
        return [FakeLink(evidence_id=i) for i in self._ids]

    def get_item(self, evidence_id, *, include_inaccessible=False):
        return FakeItem(id=evidence_id) if evidence_id in self._ids else None


class FakeClient:
    def __init__(self, reply="{}", *, raises=None):
        self._reply = reply
        self._raises = raises
        self.last_provider = "fake-provider"
        self.model = "fake-model"
        self.calls = []

    def complete(self, system, messages):
        self.calls.append((system, messages))
        if self._raises is not None:
            raise self._raises
        return self._reply


def _reply(*claims, **extra):
    return json.dumps({"claims": list(claims), **extra})


def _inv_claim(text="The charge is 12.00.", subject="amount", evidence="evidence:1"):
    return {"text": text, "evidence_ids": [evidence], "subject": subject}


def _member(role, run):
    return CouncilMember(role, run)


def _investigator_member(client, repo=None):
    investigator = Investigator(repo or FakeRepo())
    return _member(
        "investigator",
        lambda q, claims: investigator.run(
            q, client=client, target_kind="transaction", target_id="412"
        ),
    )


def _skeptic_member(client, repo=None):
    skeptic = Skeptic(repo or FakeRepo())
    return _member(
        "skeptic",
        lambda q, claims: skeptic.run(
            q, client=client, target_kind="transaction", target_id="412", review=claims
        ),
    )


# ---------------------------------------------------------------------------------------
# The council NEVER settles
# ---------------------------------------------------------------------------------------

def test_the_council_has_no_conclusion_field():
    """Falsification of 'never settled by majority vote'. A `conclusion` field would make
    "the council's answer" the thing a caller reaches for, and the first tie-break rule
    added to compute it is the moment this stops being a council."""
    fields = {field.name for field in dataclasses.fields(council_module.CouncilResult)}
    assert "conclusion" not in fields
    assert "answer" not in fields
    assert "verdict" not in fields
    assert fields == {"question", "runs", "claims", "disagreements"}
    # And no method offers one.
    for name in ("conclude", "resolve", "decide", "vote", "winner", "consensus"):
        assert not hasattr(council_module.CouncilResult, name), name


def test_a_conflict_between_two_roles_is_shown_with_both_sides():
    investigator = FakeClient(_reply(_inv_claim("The charge is 12.00.")))
    skeptic = FakeClient(_reply(_inv_claim("The charge is 21.00.", evidence="evidence:2")))
    result = convene(
        "What is this charge?",
        [_investigator_member(investigator), _skeptic_member(skeptic)],
    )

    assert [role for role, _ in result.runs] == ["investigator", "skeptic"]
    assert len(result.claims) == 2, "a claim was dropped to resolve the conflict"
    assert len(result.disagreements) == 1
    disagreement = result.disagreements[0]
    assert disagreement.subject == "amount"
    assert disagreement.roles == ("investigator", "skeptic")
    assert {claim.text for _, claim in disagreement.positions} == {
        "The charge is 12.00.",
        "The charge is 21.00.",
    }
    assert result.is_unanimous() is False


def test_agreement_is_reported_as_agreement_and_not_as_a_resolution():
    investigator = FakeClient(_reply(_inv_claim("The charge is 12.00.")))
    skeptic = FakeClient(_reply(_inv_claim("The charge is 12.00.", evidence="evidence:2")))
    result = convene(
        "What is this charge?",
        [_investigator_member(investigator), _skeptic_member(skeptic)],
    )
    # Identical TEXT on the same subject is not a disagreement, even from two roles.
    assert result.disagreements == ()
    assert len(result.claims) == 2, "agreement must not be collapsed into one claim"
    assert result.is_unanimous() is True


def test_attribution_survives_so_nobody_can_hide_behind_a_collective():
    investigator = FakeClient(_reply(_inv_claim("A.")))
    skeptic = FakeClient(_reply(_inv_claim("B.", evidence="evidence:2")))
    result = convene("q", [_investigator_member(investigator), _skeptic_member(skeptic)])
    assert {item.role for item in result.claims} == {"investigator", "skeptic"}
    assert all(isinstance(item, AttributedClaim) for item in result.claims)


def test_the_envelope_view_keeps_both_claims_for_a_plain_reader():
    speaker = FakeClient(_reply(_inv_claim("A.")))
    critic = FakeClient(_reply(_inv_claim("B.", evidence="evidence:2")))
    result = convene("q", [_investigator_member(speaker), _skeptic_member(critic)])
    plain = plain_disagreements(result.disagreements)
    assert len(plain) == 1
    assert {claim.text for claim in plain[0].claims} == {"A.", "B."}


# ---------------------------------------------------------------------------------------
# Failures are carried, not hidden
# ---------------------------------------------------------------------------------------

def test_an_unavailable_role_is_recorded_rather_than_silently_dropped():
    """"The skeptic could not run" must never read as "the skeptic found nothing"."""
    speaker = FakeClient(_reply(_inv_claim("A.")))
    critic = FakeClient(raises=TimeoutError("down"))
    result = convene("q", [_investigator_member(speaker), _skeptic_member(critic)])

    assert len(result.runs) == 2, "the failed role was dropped from the council"
    assert result.failures() == (("skeptic", "unavailable:model"),)
    # And the council is NOT unanimous: under-participation is not agreement.
    assert result.is_unanimous() is False


def test_later_roles_receive_the_earlier_claims_as_their_subject():
    """This is what makes the Skeptic possible: it is handed the Investigator's claims."""
    speaker = FakeClient(_reply(_inv_claim("A.")))
    critic = FakeClient(_reply(_inv_claim("B.", evidence="evidence:2")))
    convene("q", [_investigator_member(speaker), _skeptic_member(critic)])

    payload = json.loads(critic.calls[0][1][0]["content"])
    assert payload["claims_under_review"][0]["text"] == "A."
    assert payload["claims_under_review"][0]["evidence_ids"] == ["evidence:1"]
    # Only the CLAIM crosses over -- never the other role's reasoning or prompt.
    assert set(payload["claims_under_review"][0]) == {"text", "evidence_ids", "subject"}
    assert "Investigator" not in critic.calls[0][0]


def test_a_role_that_fails_contributes_no_claims_to_the_pool():
    speaker = FakeClient(_reply(_inv_claim("A.")))
    critic = FakeClient(raises=RuntimeError("x"))
    result = convene("q", [_investigator_member(speaker), _skeptic_member(critic)])
    assert [item.claim.text for item in result.claims] == ["A."]


def test_convening_nobody_is_empty_rather_than_an_error():
    result = convene("q", [])
    assert result.runs == ()
    assert result.claims == ()
    assert result.is_unanimous() is False


# ---------------------------------------------------------------------------------------
# The Skeptic
# ---------------------------------------------------------------------------------------

def test_the_skeptic_refuses_to_run_with_nothing_to_review_and_calls_nothing():
    client = FakeClient(_reply(_inv_claim("Unfounded doubt.")))
    skeptic = Skeptic(FakeRepo())
    run = skeptic.run("q", client=client, target_kind="transaction", target_id="412", review=())
    assert run.result.status is ResultStatus.UNAVAILABLE
    assert client.calls == [], "the model was asked to review nothing"
    assert run.record.outcome == "unavailable:nothing-to-review"


def test_the_skeptic_carries_the_subject_so_disagreement_is_detectable():
    """A counterexample that omits the subject cannot be compared with the claim it
    addresses, so the conflict becomes invisible."""
    client = FakeClient(_reply(_inv_claim("The evidence shows a single 21.00 charge.",
                                          evidence="evidence:2")))
    skeptic = Skeptic(FakeRepo())
    run = skeptic.run(
        "q", client=client, target_kind="transaction", target_id="412",
        review=(Claim(text="The charge is 12.00.", evidence_ids=("evidence:1",), subject="amount"),),
    )
    assert run.result.status is ResultStatus.OK
    assert run.result.claims[0].subject == "amount"


def test_the_skeptic_drops_doubt_that_states_nothing():
    """A skeptic answering "this could be wrong" has added no information while appearing to
    have scrutinised. It cites valid evidence, so only this check catches it."""
    client = FakeClient(_reply(_inv_claim("The evidence could be wrong.")))
    skeptic = Skeptic(FakeRepo())
    run = skeptic.run(
        "q", client=client, target_kind="transaction", target_id="412",
        review=(Claim(text="A.", evidence_ids=("evidence:1",), subject="amount"),),
    )
    assert run.result.status is ResultStatus.UNAVAILABLE
    assert run.result.claims == ()
    assert "not contradicted" in (run.result.detail or "")


def test_the_skeptic_keeps_a_substantive_counterexample_that_mentions_uncertainty():
    """The drop rule must not silence a real counterexample that happens to hedge."""
    client = FakeClient(
        _reply(
            _inv_claim(
                "The evidence shows only one source states 12.00, while the second states 21.00, "
                "so the amount is not established.",
                evidence="evidence:2",
            )
        )
    )
    skeptic = Skeptic(FakeRepo())
    run = skeptic.run(
        "q", client=client, target_kind="transaction", target_id="412",
        review=(Claim(text="The charge is 12.00.", evidence_ids=("evidence:1",), subject="amount"),),
    )
    assert run.result.status is ResultStatus.OK
    assert len(run.result.claims) == 1


def test_the_skeptic_holds_no_write_tool_and_shares_the_role_machinery():
    from meridian.ai.envelope import provider_write_tool_names

    skeptic = Skeptic(FakeRepo())
    assert not (skeptic.permissions.tools & provider_write_tool_names())
    # It is built on the shared base, so it inherits the envelope's guarantees.
    from meridian.ai.role import EvidenceBoundRole

    assert isinstance(skeptic, EvidenceBoundRole)


def test_a_hallucinated_citation_voids_the_skeptic_too():
    """The safety property is inherited, not re-implemented per role -- checked here so a
    second role cannot quietly opt out of it."""
    client = FakeClient(_reply(_inv_claim("Invented.", evidence="evidence:999")))
    skeptic = Skeptic(FakeRepo())
    run = skeptic.run(
        "q", client=client, target_kind="transaction", target_id="412",
        review=(Claim(text="A.", evidence_ids=("evidence:1",), subject="amount"),),
    )
    assert run.result.status is ResultStatus.FAILED
    assert run.result.claims == ()
    assert run.record.outcome == "failed:unsupported-citation"


# ---------------------------------------------------------------------------------------
# The fail-closed guard, and module hygiene
# ---------------------------------------------------------------------------------------

def test_fail_closed_is_read_from_the_permissions_table_not_duplicated():
    from meridian.ai.envelope import permissions_for

    assert council_module._must_fail_closed("guardian") is True
    assert "CLOSED" in permissions_for("guardian").failure_behaviour
    for role in ("investigator", "skeptic", "forecaster", "teacher"):
        assert council_module._must_fail_closed(role) is False
    # An unknown role is not silently treated as fail-closed.
    assert council_module._must_fail_closed("nobody") is False


def test_a_fail_closed_role_stops_the_council_and_keeps_what_it_has():
    """The Guardian is not implemented yet, so this is exercised with a stand-in that
    declares the guardian's role name. It must STOP the council, not be skipped."""
    speaker = FakeClient(_reply(_inv_claim("A.")))
    guardian_client = FakeClient(raises=RuntimeError("guardian down"))
    ran = []

    def guardian_run(question, claims):
        ran.append(True)
        from meridian.ai.role import EvidenceBoundRole

        class _Guardian(EvidenceBoundRole):
            role = "guardian"

            def system_prompt(self):
                return "x"

        return _Guardian(FakeRepo()).run(
            question, client=guardian_client, target_kind="transaction", target_id="412"
        )

    result = convene(
        "q",
        [
            _investigator_member(speaker),
            _member("guardian", guardian_run),
            _member("teacher", lambda q, claims: pytest.fail("ran past a fail-closed role")),
        ],
    )
    assert ran == [True]
    assert [role for role, _ in result.runs] == ["investigator", "guardian"]
    assert result.is_unanimous() is False


def test_no_role_module_builds_its_own_client_or_reads_a_credential():
    """Inherited discipline is still discipline: checked over the AST of every role module."""
    for name in ("role.py", "investigator.py", "skeptic.py", "council.py"):
        tree = ast.parse((ROOT / "meridian" / "ai" / name).read_text(encoding="utf-8"))
        imported: set[str] = set()
        chains: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            elif isinstance(node, ast.Attribute):
                parts = []
                cursor: ast.AST = node
                while isinstance(cursor, ast.Attribute):
                    parts.append(cursor.attr)
                    cursor = cursor.value
                if isinstance(cursor, ast.Name):
                    parts.append(cursor.id)
                    chains.add(".".join(reversed(parts)))
        assert not (imported & {"requests", "subprocess", "openai", "urllib", "httpx", "socket"}), name
        assert "os.environ" not in chains, name
        assert "os.getenv" not in chains, name
