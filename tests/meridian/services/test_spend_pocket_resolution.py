"""Which pocket is the spend pocket: Crew's own selection first, the name allow-list as a NAMED fallback.

The evidence this file is written against is real rather than hypothetical (OS-113, 2026-09-25):

  * ``gate.db`` holds TWO pockets the name allow-list matches — ``'Safe to Spend'`` (active) and
    ``'Free to Spend'`` (inactive since 2026-09-17);
  * ``savings_data.db`` holds TWO ACTIVE pockets BOTH named ``'Free to Spend'``
    (``Subaccount:99adf76a...`` and ``Subaccount:edc8cb88...``), which no name-based rule can tell
    apart at all — only Crew's own selection can;
  * Crew's selection, read from the owner's real capture by the shipped
    ``readback_selected_spend_pocket()``, is ``Subaccount:edc8cb88-...`` — the second of those two.

So the central test here is not "does the resolver prefer the selection" in the abstract; it is
"given two identically named active pockets, does the figure come from the one Crew says he spends
from".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from meridian.services.spend_pocket import (
    BASIS_CREW_SELECTION,
    BASIS_NAME,
    BASIS_NONE,
    STATUS_AMBIGUOUS,
    STATUS_NONE,
    STATUS_SELECTED,
    STATUS_SELECTED_INACTIVE,
    STATUS_SELECTED_UNMATCHED,
    STATUS_UNOBSERVED,
    resolve_spend_pocket,
)

# Crew's own ids, exactly as financial_accounts.external_id stores them.
SELECTED = "U3ViYWNjb3VudDplZGM4Y2I4OC1mMjM0LTQzMjEtOGEzYi1kMjc5MGU5ODFhN2E="
TWIN = "U3ViYWNjb3VudDo5OWFkZjc2YS0wZjIyLTQ0ZjctOTg5YS0xNzEwODIyZTY2M2E="


@dataclass
class Row:
    """An account row, shaped like the repository's own records."""

    external_id: str
    name: str
    is_active: bool = True
    balance: float = 0.0


@dataclass
class Selection:
    """A stored observation, shaped like meridian.spend_selection.SpendSelection."""

    resolution: str
    selected_external_id: Optional[str] = None


def test_crew_selection_beats_two_identically_named_active_pockets():
    # The savings_data.db situation that no name rule can resolve: both active, both "Free to Spend".
    twin_first = Row(TWIN, "Free to Spend", balance=-165.22)
    selected_second = Row(SELECTED, "Free to Spend", balance=-83.14)
    resolution = resolve_spend_pocket(
        [twin_first, selected_second], selection=Selection("selected", SELECTED)
    )
    assert resolution.account is selected_second
    assert resolution.basis == BASIS_CREW_SELECTION
    assert resolution.selection_status == STATUS_SELECTED
    assert resolution.uses_selection

    # And it is not an artefact of list order: reversed, the same pocket still wins.
    reversed_resolution = resolve_spend_pocket(
        [selected_second, twin_first], selection=Selection("selected", SELECTED)
    )
    assert reversed_resolution.account is selected_second


def test_the_selection_survives_a_rename_because_it_matches_by_id():
    renamed = Row(SELECTED, "Pocket 7")  # a name neither mechanism's list contains
    resolution = resolve_spend_pocket([renamed], selection=Selection("selected", SELECTED))
    assert resolution.account is renamed
    assert resolution.basis == BASIS_CREW_SELECTION, (
        "renaming a pocket must not change the figure -- that is the 2026-09-25 defect"
    )


def test_an_inactive_selected_pocket_falls_back_and_says_so():
    # gate.db's shape: the allow-list also matches a retired 'Free to Spend' row.
    retired = Row(SELECTED, "Free to Spend", is_active=False)
    live = Row(TWIN, "Safe to Spend", is_active=True)
    resolution = resolve_spend_pocket([retired, live], selection=Selection("selected", SELECTED))
    assert resolution.basis == BASIS_NAME, "an inactive selection is not usable as an answer"
    assert resolution.selection_status == STATUS_SELECTED_INACTIVE
    assert resolution.account is live
    assert resolution.selected_external_id == SELECTED
    assert "active" in resolution.detail


def test_a_selection_matching_no_account_falls_back_and_says_so():
    other = Row(TWIN, "Safe to Spend")
    resolution = resolve_spend_pocket([other], selection=Selection("selected", "Subaccount:unknown"))
    assert resolution.basis == BASIS_NAME
    assert resolution.selection_status == STATUS_SELECTED_UNMATCHED
    assert resolution.account is other


def test_an_observed_absence_falls_back_to_the_explicit_names():
    pocket = Row(TWIN, "Safe to Spend")
    resolution = resolve_spend_pocket([pocket], selection=Selection("none"))
    assert resolution.account is pocket
    assert resolution.basis == BASIS_NAME
    assert resolution.selection_status == STATUS_NONE
    assert "no selection" in resolution.detail


def test_disagreeing_cards_fall_back_too_and_the_status_records_the_disagreement():
    pocket = Row(TWIN, "Safe to Spend")
    resolution = resolve_spend_pocket([pocket], selection=Selection("ambiguous"))
    assert resolution.basis == BASIS_NAME
    assert resolution.selection_status == STATUS_AMBIGUOUS


def test_with_no_observation_at_all_the_name_rule_still_answers_but_says_it_is_unobserved():
    pocket = Row(TWIN, "Safe to Spend")
    resolution = resolve_spend_pocket([pocket])
    assert resolution.account is pocket
    assert resolution.basis == BASIS_NAME
    assert resolution.selection_status == STATUS_UNOBSERVED


def test_when_neither_mechanism_finds_a_pocket_none_is_named_and_nothing_is_claimed():
    resolution = resolve_spend_pocket(
        [Row(TWIN, "Envelope"), Row("Subaccount:x", "Emergency Fund")],
        selection=Selection("selected", SELECTED),
    )
    assert resolution.account is None
    assert resolution.basis == BASIS_NONE
    assert resolution.selection_status == STATUS_SELECTED_UNMATCHED


def test_an_inactive_pocket_is_never_selected_by_name():
    # The retired 'Free to Spend' in gate.db must not answer just because it is in the list.
    resolution = resolve_spend_pocket([Row(TWIN, "Free to Spend", is_active=False)])
    assert resolution.account is None
    assert resolution.basis == BASIS_NONE


def test_the_resolution_carries_only_what_a_payload_may_show():
    pocket = Row(SELECTED, "Safe to Spend", balance=15.45)
    evidence = resolve_spend_pocket(
        [pocket], selection=Selection("selected", SELECTED)
    ).as_evidence()
    assert evidence == {
        "basis": BASIS_CREW_SELECTION,
        "selection_status": STATUS_SELECTED,
        "selected_external_id": SELECTED,
        "pocket": "Safe to Spend",
        "detail": "Crew's own selected spend pocket, matched by its id",
    }
    assert "balance" not in evidence
