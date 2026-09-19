"""Archiving a LOCAL commitment, and the guard that keeps Crew bills off that path.

`CommitmentRepository.archive()` has existed since the absence-reconciliation work and is
already covered in tests/meridian/test_commitments.py. What did not exist was any way to
REACH it: no action type, no executor, no control. A local planning record could therefore
be created and never removed -- the owner had four "Journey Test Bill" rows stuck that way,
because the Plan card renders Delete only when a Crew bill id exists.

These tests cover the action and its verifier. They deliberately do not re-test the
repository method.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_FILE", str(tmp_path / "app.db"))
    import app

    app.DB_FILE = str(tmp_path / "app.db")
    app.init_db()
    return app


def _local_bill(repository, name="Journey Test Bill"):
    from meridian.commitments import CommitmentType

    return repository.create(
        type=CommitmentType.BILL,
        name=name,
        amount=100.0,
        due_date="2026-10-16",
        recurrence="monthly",
    )


def _crew_bill(repository, name="Verizon"):
    from meridian.commitments import CommitmentType

    return repository.create(
        type=CommitmentType.BILL,
        name=name,
        amount=102.0,
        due_date="2026-09-22",
        recurrence="monthly",
        legacy_source="crew",
        legacy_id="bill-verizon-1",
    )


def test_a_local_commitment_is_archived_and_the_readback_confirms_it(app_module):
    from meridian.commitments import CommitmentRepository, CommitmentStatus

    repository = CommitmentRepository(app_module.DB_FILE)
    bill = _local_bill(repository)
    assert bill.id in [item.id for item in repository.list_active()]

    result = app_module._apply_archive_commitment({"commitment_id": bill.id})
    assert result["success"] is True
    assert result["status"] == "archived"

    check = app_module.verify_archive_commitment_action({"commitment_id": bill.id}, result)
    assert check["ok"] is True
    assert check["check"] == "commitment-archived-reread"

    # Gone from the surface the owner was stuck on: plan.py reads list_active().
    assert bill.id not in [item.id for item in repository.list_active()]
    # The history is kept rather than deleted, which is what makes this reversible.
    assert repository.get(bill.id).status is CommitmentStatus.ARCHIVED


def test_the_guard_and_the_ui_agree_about_which_rows_carry_a_crew_bill(app_module):
    """The rows the owner cannot delete in the UI must be exactly the rows this path accepts.

    The plan payload sets `crew_bill_id` to `legacy_id` gated on `legacy_source == "crew"`,
    and the card renders Delete only when that id is truthy. The executor refuses only a
    commitment carrying BOTH a crew source and a crew id. So the two conditions are one
    condition written twice -- which is what makes this fix reach the stuck rows instead of
    merely adding a button beside an impossible state.
    """
    from meridian.commitments import CommitmentRepository, CommitmentStatus

    repository = CommitmentRepository(app_module.DB_FILE)

    # No crew id -> no Delete control in the UI, and the local path accepts it.
    local = _local_bill(repository)
    accepted = app_module._apply_archive_commitment({"commitment_id": local.id})
    assert accepted["success"] is True
    assert repository.get(local.id).status is CommitmentStatus.ARCHIVED

    # A crew id -> Delete is offered, and that path owns the write instead.
    crew_backed = _crew_bill(repository)
    refused = app_module._apply_archive_commitment({"commitment_id": crew_backed.id})
    assert refused["success"] is False
    assert "Crew bill path" in refused["error"]
    assert repository.get(crew_backed.id).status is not CommitmentStatus.ARCHIVED

    plan = (ROOT / "meridian/services/plan.py").read_text(encoding="utf-8")
    ui = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "if (commitment.crew_bill_id) {" in ui
    assert 'getattr(commitment, "legacy_source", None) == "crew"' in plan
    assert (
        'getattr(existing, "legacy_source", None) == "crew" '
        'and getattr(existing, "legacy_id", None)' in app_source
    )


def test_the_verifier_will_not_confirm_a_row_that_is_not_archived(app_module):
    """A write is unknown until the readback says otherwise, so the verifier reports the
    stored status rather than echoing the executor's own claim of success."""
    from meridian.commitments import CommitmentRepository

    repository = CommitmentRepository(app_module.DB_FILE)
    bill = _local_bill(repository, name="Still active")

    check = app_module.verify_archive_commitment_action(
        {"commitment_id": bill.id}, {"commitment_id": bill.id, "success": True}
    )
    assert check["ok"] is False


def test_a_missing_commitment_is_refused_rather_than_assumed(app_module):
    result = app_module._apply_archive_commitment({"commitment_id": 987654})
    assert result["success"] is False
    assert "not found" in result["error"]


def test_the_plan_card_offers_a_local_delete_and_keeps_the_crew_one():
    """Two delete controls, one row each, and they must not overlap: the Crew branch keeps
    archive_crew_bill (provider-verified), the local branch uses archive_commitment."""
    ui = (ROOT / "static/js/meridian/plan.js").read_text(encoding="utf-8")

    after_guard = ui.split("if (commitment.crew_bill_id) {", 1)[1]
    crew_branch, local_branch = after_guard.split("} else {", 1)

    # The Crew bill keeps travelling its own provider-verified path.
    assert "archive_crew_bill" in crew_branch
    assert "archive_crew_bill" not in local_branch

    assert "archive_commitment" in local_branch
    assert "params: { commitment_id: commitment.id }" in local_branch
    # Owner-initiated and single, so the routing model executes it directly -- the same
    # provenance the Crew delete uses.
    assert 'provenance: "owner_direct"' in local_branch
    # A second request against a concluded row is refused at the control.
    assert "del.disabled = true;" in local_branch
