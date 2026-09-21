"""The read-only investigation command.

The role is proven in tests/meridian/test_ai_investigator.py. This file tests the thing that
makes it REACHABLE, and guards the two claims a command like this can quietly lose: that it
is read-only, and that an unconfigured model is reported rather than faked.

Nothing here contacts a provider or needs a key: the client is a fake, and the only
real-code path exercised is argument handling.
"""
import ast
import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "investigate.py"


def _load():
    spec = importlib.util.spec_from_file_location("investigate_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["investigate_script"] = module
    spec.loader.exec_module(module)
    return module


investigate_script = _load()


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
    def __init__(self, ids=(1,)):
        self._ids = list(ids)

    def list_links_for_target(self, target_kind, target_id):
        return [FakeLink(evidence_id=i) for i in self._ids]

    def get_item(self, evidence_id, *, include_inaccessible=False):
        return FakeItem(id=evidence_id) if evidence_id in self._ids else None


class FakeClient:
    def __init__(self, reply="{}", *, providers=("fake",)):
        self._reply = reply
        self._providers = list(providers)
        self.last_provider = "fake"
        self.model = "fake-model"
        self.calls = []

    def providers(self):
        return list(self._providers)

    def complete(self, system, messages):
        self.calls.append((system, messages))
        return self._reply


def _reply(*claims, **extra):
    return json.dumps({"claims": list(claims), **extra})


# ---------------------------------------------------------------------------------------
# The read-only claim, checked rather than promised
# ---------------------------------------------------------------------------------------

def test_the_command_imports_no_provider_write_path():
    """Falsification of 'read-only': the script must not even have the write modules in
    reach. Checked over the parsed AST so a future edit cannot add one quietly."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)

    forbidden = {
        "meridian.crew_write",
        "meridian.crew_write_actions",
        "meridian.mutations",
        "meridian.funding_proposals",
    }
    hit = {name for name in imported if any(name.startswith(f) for f in forbidden)}
    assert not hit, f"the read-only command reaches a write path: {sorted(hit)}"


def test_the_command_writes_nothing_to_the_repository():
    """The Investigator is given a repository that RECORDS every attribute it is asked for.
    Only reads may appear -- a write would show up here rather than in production."""

    class RecordingRepo(FakeRepo):
        def __init__(self):
            super().__init__()
            self.accessed = []

        def __getattr__(self, name):
            self.accessed.append(name)
            raise AssertionError(f"the investigator reached {name!r} on its repository")

    repo = RecordingRepo()
    client = FakeClient(_reply({"text": "A subscription.", "evidence_ids": ["evidence:1"]}))
    run = investigate_script.investigate(
        repository=repo,
        client=client,
        target_kind="transaction",
        target_id="412",
        question="What is this?",
    )
    assert run.result.status.value == "ok"
    assert repo.accessed == [], repo.accessed


def test_the_rendered_output_says_nothing_was_executed():
    """The payload must not read as though an action occurred: this is a read-only command
    whose output could otherwise be mistaken for a proposal or a completed change."""
    client = FakeClient(_reply({"text": "A subscription.", "evidence_ids": ["evidence:1"]}))
    run = investigate_script.investigate(
        repository=FakeRepo(),
        client=client,
        target_kind="transaction",
        target_id="412",
        question="What is this?",
    )
    text = investigate_script.format_text(investigate_script.render(run))
    assert "read-only" in text
    assert "proposed" in text and "executed" in text


# ---------------------------------------------------------------------------------------
# An unconfigured model is reported, never faked
# ---------------------------------------------------------------------------------------

def test_no_configured_provider_exits_unavailable_without_calling_anything(monkeypatch, capsys):
    """The most important behaviour in this file. With no key, the command must refuse to
    investigate rather than fall back to a canned answer -- a fabricated investigation of
    the owner's own transactions is worse than none."""
    client = FakeClient(providers=())
    monkeypatch.setattr(investigate_script, "build_client", lambda: client)

    code = investigate_script.main(["--target", "transaction:412"])

    assert code == investigate_script.EXIT_UNAVAILABLE
    err = capsys.readouterr().err
    assert "no AI provider is configured" in err
    # The message must not leak a key, and must name the variable rather than a value.
    assert "DEEPSEEK_API_KEY" in err
    assert "sk-" not in err
    assert client.calls == [], "a model was called with no provider configured"


def test_a_broken_client_is_reported_rather_than_crashing(monkeypatch, capsys):
    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr(investigate_script, "build_client", explode)
    code = investigate_script.main(["--target", "transaction:412"])
    assert code == investigate_script.EXIT_UNAVAILABLE
    assert "could not build a model client" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    ["transaction", "", ":", "transaction:", ":412", "   :   "],
)
def test_a_malformed_target_is_rejected(raw, capsys):
    with pytest.raises(ValueError):
        investigate_script.parse_target(raw)


def test_a_valid_target_parses_kind_and_id():
    assert investigate_script.parse_target("transaction:412") == ("transaction", "412")
    # The id stays a STRING: the evidence store keys links by str(target_id), so coercing
    # to int here would silently match nothing.
    assert investigate_script.parse_target("cancellation_action:7") == ("cancellation_action", "7")


def test_a_malformed_target_exits_unavailable_without_touching_the_database(monkeypatch, capsys):
    client = FakeClient()
    monkeypatch.setattr(investigate_script, "build_client", lambda: client)
    called = []
    monkeypatch.setattr(
        investigate_script, "build_client", lambda: (called.append(1), client)[1]
    )
    code = investigate_script.main(["--target", "nonsense"])
    assert code == investigate_script.EXIT_UNAVAILABLE
    assert "kind:id" in capsys.readouterr().err
    assert client.calls == []


# ---------------------------------------------------------------------------------------
# Exit codes and disagreement rendering
# ---------------------------------------------------------------------------------------

def test_exit_codes_are_derived_from_the_result_status():
    from meridian.ai.envelope import ResultStatus

    assert investigate_script._EXIT_FOR_STATUS[ResultStatus.OK] == 0
    assert investigate_script._EXIT_FOR_STATUS[ResultStatus.FAILED] == 1
    assert investigate_script._EXIT_FOR_STATUS[ResultStatus.UNAVAILABLE] == 2


def test_a_refused_citation_renders_as_failed_with_no_claims():
    """The end-to-end shape of the safety property: a hallucinated citation must reach the
    operator as a failure with nothing to read, not as a confident sentence."""
    client = FakeClient(_reply({"text": "Invented.", "evidence_ids": ["evidence:999"]}))
    run = investigate_script.investigate(
        repository=FakeRepo(),
        client=client,
        target_kind="transaction",
        target_id="412",
        question="What is this?",
    )
    payload = investigate_script.render(run)
    assert payload["status"] == "failed"
    assert payload["claims"] == []
    assert payload["run"]["outcome"] == "failed:unsupported-citation"


def test_disagreements_are_rendered_rather_than_averaged():
    client = FakeClient(
        _reply(
            {"text": "The charge is 12.00.", "evidence_ids": ["evidence:1"], "subject": "amount"},
            {"text": "The charge is 21.00.", "evidence_ids": ["evidence:2"], "subject": "amount"},
        )
    )
    run = investigate_script.investigate(
        repository=FakeRepo(ids=(1, 2)),
        client=client,
        target_kind="transaction",
        target_id="412",
        question="What is this?",
    )
    payload = investigate_script.render(run)
    assert len(payload["claims"]) == 2
    assert len(payload["disagreements"]) == 1
    assert payload["disagreements"][0]["subject"] == "amount"
    text = investigate_script.format_text(payload)
    assert "unresolved disagreement" in text
    # Both sides are shown; neither is presented as the answer.
    assert "12.00" in text and "21.00" in text


def test_the_json_output_carries_the_run_record_for_audit():
    client = FakeClient(_reply({"text": "A subscription.", "evidence_ids": ["evidence:1"]}))
    run = investigate_script.investigate(
        repository=FakeRepo(),
        client=client,
        target_kind="transaction",
        target_id="412",
        question="What is this?",
    )
    payload = json.loads(json.dumps(investigate_script.render(run)))
    assert payload["run"]["evidence_ids"] == ["evidence:1"]
    assert payload["run"]["outcome"] == "ok"
    assert payload["run"]["prompt_version"]
