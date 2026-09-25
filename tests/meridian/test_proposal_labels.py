"""Proposal labels must read as sentences, not as internal parlance.

Owner, 2026-09-25: "remove essentially user facing nonesense text like delete_asset: Meridian
delete_asset". Two producers made that string: `app.py`'s sink wrote "Meridian delete_asset: 6" as the
summary, and `memory-manage.js` prefixed the action type to it. Both are fixed here, and the display also
recognises strings already stored, because rows that were proposed before today are not migrated.

The mapping itself is pure and lives in `meridian/action_summary.py`; the display half is asserted in
`tests/browser/test_assets_paper_theme.py` against the real pending list on a running app.
"""
from pathlib import Path

import pytest

from meridian.action_summary import human_action_summary

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("action_type,params,lookup,expected", [
    ("delete_asset", {"record_id": "6"}, "Test Asset", 'Delete the asset "Test Asset"'),
    ("delete_asset", {"record_id": "6"}, None, "Delete an asset"),
    ("update_asset", {"name": "Bike"}, None, 'Update the asset "Bike"'),
    ("create_contract", {"name": "Renters"}, None, 'Add the contract "Renters"'),
    ("create_commitment", {"name": "Xfinity"}, None, 'Add the commitment "Xfinity"'),
])
def test_a_proposal_reads_as_a_sentence(action_type, params, lookup, expected):
    name_lookup = (lambda action, payload: lookup) if lookup else None
    assert human_action_summary(action_type, params, name_lookup=name_lookup) == expected


def test_a_sentence_never_carries_an_internal_id():
    """The id is what made the old label unreadable; it must not reappear through a fallback."""
    for action_type in ("delete_asset", "update_contract", "delete_commitment", "unheard_of_action"):
        for params in ({"record_id": 6}, {"record_id": "6"}, {}):
            sentence = human_action_summary(action_type, params)
            assert "_" not in sentence, sentence
            assert ":" not in sentence, sentence
            assert "6" not in sentence, sentence


def test_an_unknown_action_type_is_read_back_as_words():
    assert human_action_summary("banish_widget", {}) == "Banish widget"
    assert human_action_summary("banish_widget", {"name": "Gizmo"}) == 'Banish widget "Gizmo"'


def test_a_lookup_that_raises_cannot_block_the_label():
    def exploding(action_type, params):
        raise RuntimeError("database is away")

    assert human_action_summary("delete_asset", {"record_id": 1}, name_lookup=exploding) == "Delete an asset"


def test_the_sink_no_longer_writes_the_machine_summary():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'summary = f"Meridian {action_type}: {params.get(\'name\') or params.get(\'record_id\')}"' not in source
    assert "human_action_summary(action_type, params, name_lookup=lookup_record_name)" in source


def test_the_ui_no_longer_prefixes_the_action_type():
    source = (ROOT / "static/js/meridian/memory-manage.js").read_text(encoding="utf-8")
    assert "label.textContent = `${action.type}: ${action.rationale || action.id}`" not in source
    assert "label.textContent = this.proposalSentence(action);" in source
    # The raw identifiers survive as data attributes rather than being destroyed.
    assert "row.dataset.actionType = action.type;" in source
    assert "row.dataset.actionId = action.id;" in source
