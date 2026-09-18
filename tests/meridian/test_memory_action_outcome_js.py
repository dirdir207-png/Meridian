"""A09: Memory must retain failed/uncertain executions and parse action state."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_memory_management_imports_shared_action_state_interpreter():
    source = (ROOT / "static/js/meridian/memory-manage.js").read_text(encoding="utf-8")
    accounts = (ROOT / "templates/meridian/partials/accounts.html").read_text(encoding="utf-8")

    assert 'from "./action-outcome.js"' in source
    assert 'type="module" src="/static/js/meridian/memory-manage.js"' in accounts


def test_memory_execute_parses_body_and_only_removes_verified_rows():
    source = (ROOT / "static/js/meridian/memory-manage.js").read_text(encoding="utf-8")

    assert "const body = await response.json()" in source
    assert "describeActionOutcome({ routing_direct: true, action: body })" in source
    assert "if (outcome.refresh)" in source
    assert "if (row) row.remove();" in source
    assert "if (statusEl) statusEl.textContent = outcome.message;" in source

    # These were the false-success behavior: every HTTP-200 execute response was
    # called executed, removed, and followed by an unconditional memory refresh.
    assert "statusEl.textContent = 'executed'" not in source
    assert "} else if (step === 'execute') {\n                    if (statusEl)" not in source


def test_memory_execute_does_not_expose_blind_resend_after_durable_outcome():
    source = (ROOT / "static/js/meridian/memory-manage.js").read_text(encoding="utf-8")

    assert "execute.disabled = true" in source
    assert "Check Actions & Approvals" in (
        ROOT / "static/js/meridian/action-outcome.js"
    ).read_text(encoding="utf-8")
