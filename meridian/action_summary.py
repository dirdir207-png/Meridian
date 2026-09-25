"""Human sentences for proposals, instead of machine parlance.

Owner, 2026-09-25, looking at the Assets & Contracts plate: "remove essentially user facing nonesense
text like delete_asset: Meridian delete_asset".

That string was ours, twice over. `app.py` built the stored summary as
`f"Meridian {action_type}: {params.get('name') or params.get('record_id')}"` -> "Meridian delete_asset: 6",
and the UI prefixed the action type to it -> "delete_asset: Meridian delete_asset: 6". Nothing in it
tells the reader what is about to happen, and one half of it is an internal identifier.

This module turns an action into a sentence a person can decide on:

    delete_asset, {record_id: 6}   ->  Delete the asset "Test Asset"        (name resolved from the record)
    delete_asset, {}               ->  Delete a tracked asset
    create_commitment, {name: X}   ->  Add the commitment "X"

It is pure: the optional `name_lookup` is injected by the caller, so this is testable without a database
and cannot itself read or write anything. It composes text only -- it does not decide, approve, execute
or route anything, and it deliberately never invents a name it could not resolve.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

#: action type -> (verb, singular noun). Only wording lives here; nothing about routing or authority.
ACTION_PHRASES: dict[str, tuple[str, str]] = {
    "create_asset": ("Add", "asset"),
    "update_asset": ("Update", "asset"),
    "delete_asset": ("Delete", "asset"),
    "create_contract": ("Add", "contract"),
    "update_contract": ("Update", "contract"),
    "delete_contract": ("Delete", "contract"),
    "create_commitment": ("Add", "commitment"),
    "update_commitment": ("Update", "commitment"),
    "delete_commitment": ("Delete", "commitment"),
    "update_funding_rule": ("Update", "funding rule"),
    "create_funding_rule": ("Add", "funding rule"),
}

#: Field names a caller might have already put a human label in, best first.
NAME_FIELDS = ("name", "title", "label", "summary_label")


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def human_action_summary(
    action_type: str,
    params: Mapping[str, Any] | None = None,
    name_lookup: Callable[[str, Mapping[str, Any]], str | None] | None = None,
) -> str:
    """A sentence for the proposal list. Never contains a raw type or an internal id."""
    params = dict(params or {})
    verb, noun = ACTION_PHRASES.get(action_type, (None, None))

    name = None
    for field in NAME_FIELDS:
        value = params.get(field)
        if isinstance(value, str) and value.strip():
            name = value.strip()
            break
    if name is None and name_lookup is not None:
        try:
            looked_up = name_lookup(action_type, params)
        except Exception:  # a label lookup must never block proposing
            looked_up = None
        if isinstance(looked_up, str) and looked_up.strip():
            name = looked_up.strip()

    if verb and noun:
        return f'{verb} the {noun} "{name}"' if name else f"{verb} {_article(noun)} {noun}"

    # An action type this module has no wording for yet. Read it back as words rather than as an
    # identifier -- "delete_asset" at least becomes "Delete asset" -- and never append an id.
    readable = " ".join(action_type.replace("-", "_").split("_")).strip().lower()
    readable = readable[:1].upper() + readable[1:] if readable else "Change"
    return f'{readable} "{name}"' if name else readable


def lookup_record_name(action_type: str, params: Mapping[str, Any]) -> str | None:
    """Resolve a memory record's own name for the sentence, best effort.

    Kept separate from `human_action_summary` so that function stays pure: this is the only part that
    touches the database, it is read-only, and every failure returns None rather than raising -- a
    proposal must never fail because a label could not be prettied up.
    """
    record_id = params.get("record_id")
    if record_id in (None, ""):
        return None
    try:
        import app as app_module
    except Exception:
        return None
    try:
        record_id_int = int(record_id)
    except (TypeError, ValueError):
        return None
    try:
        if "asset" in action_type:
            from meridian.assets import AssetRepository

            asset = AssetRepository(app_module.DB_FILE).get_asset(record_id_int)
            return getattr(asset, "name", None)
        if "contract" in action_type:
            from meridian.contracts import ContractRepository

            contract = ContractRepository(app_module.DB_FILE).get_contract(record_id_int)
            return getattr(contract, "name", None) or getattr(contract, "title", None)
    except Exception:
        return None
    return None
