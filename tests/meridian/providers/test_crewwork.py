"""Creates a read-only Meridian provider adapter from a CrewWorkAssistant
(crew-readonly MCP) snapshot. Balances and amounts are cents; the adapter
normalizes them to dollars like CrewReadAdapter."""

from meridian.providers.crewwork import CrewWorkSnapshotAdapter


def _snapshot():
    """A realistic CrewWorkAssistant snapshot payload (as produced by
    `crew-readonly snapshot` with its normalize_* helpers)."""
    return {
        "mode": "read-only",
        "source": "crew",
        "captured_at": "2026-09-01T14:00:00Z",
        "complete": True,
        "mutations_enabled": False,
        "data": {
            "accounts": {
                "data": {
                    "currentUser": {
                        "accounts": [
                            {
                                "id": "QWNjb3VudDox",
                                "displayName": "Checking",
                            }
                        ]
                    }
                }
            },
            "pockets": {
                "data": {
                    "currentUser": {
                        "accounts": [
                            {
                                "id": "QWNjb3VudDox",
                                "displayName": "Checking",
                                "subaccounts": [
                                    {
                                        "id": "U3ViYWNjb3VudDox",
                                        "displayName": "Checking",
                                        "overallBalance": 12345,
                                        "clearedBalance": 12000,
                                        "isPrimary": True,
                                        "status": "ACTIVATED",
                                    }
                                ],
                            }
                        ]
                    }
                }
            },
            "transactions": {
                "data": {
                    "account": {
                        "id": "QWNjb3VudDox",
                        "cashTransactions": {
                            "edges": [
                                {
                                    "node": {
                                        "id": "Q2FzaFRyYW5zYWN0aW9uOjE=",
                                        "amount": -459,
                                        "currencyCode": "USD",
                                        "description": "Coffee shop",
                                        "title": "Coffee shop",
                                        "occurredAt": "2026-09-01T09:00:00Z",
                                        "type": "DEBIT",
                                        "status": "CLEARED",
                                        "subaccount": {"id": "U3ViYWNjb3VudDox"},
                                        "matchingName": "Blue Bottle",
                                        "memo": "latte",
                                    }
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            },
        },
    }


def test_adapter_normalizes_snapshot_to_dollars():
    adapter = CrewWorkSnapshotAdapter(_snapshot())
    assert adapter.provider_name == "crew"
    snapshot = adapter.fetch_snapshot()

    assert snapshot.is_complete is True
    assert snapshot.errors == ()

    # One pocket account + one synthetic parent account (for account-level txns)
    assert len(snapshot.accounts) == 2
    account = snapshot.accounts[0]
    assert account.external_id == "U3ViYWNjb3VudDox"
    assert account.name == "Checking"
    assert account.account_type == "checking"
    assert account.balance == 123.45
    assert account.currency == "USD"

    # One transaction: cents -> dollars, status mapped
    assert len(snapshot.transactions) == 1
    txn = snapshot.transactions[0]
    assert txn.external_id == "Q2FzaFRyYW5zYWN0aW9uOjE="
    assert txn.amount == -4.59
    assert txn.occurred_at == "2026-09-01T09:00:00Z"
    assert txn.description == "Coffee shop"
    # Crew's clean `title` is the merchant label when present.
    assert txn.merchant == "Coffee shop"
    assert txn.status in ("posted", "pending", "cleared")
    # source_updated_at reflects when the snapshot observed the record (not the
    # transaction's own happened-at date), so provider freshness stays current.
    assert txn.source_updated_at == "2026-09-01T14:00:00Z"


def test_adapter_prefers_clean_title_over_raw_matching_name():
    """Crew returns a clean `title` (merchant name) alongside a raw processor
    `matchingName`; the adapter must surface the clean label."""
    snap = _snapshot()
    snap["data"]["transactions"]["data"]["account"]["cashTransactions"]["edges"] = [
        {
            "node": {
                "id": "Q2FzaFRyYW5zYWN0aW9uOjM=",
                "amount": -459,
                "currencyCode": "USD",
                "description": None,
                "title": "Cumberland Farms",
                "occurredAt": "2026-09-01T09:00:00Z",
                "type": "DEBIT",
                "status": "CLEARED",
                "subaccount": {"id": "U3ViYWNjb3VudDox"},
                "matchingName": "CUMBERLAND FARMS 5543 660000003542 - AUTHORIZATION CLEARING",
                "memo": None,
            }
        }
    ]
    txn = CrewWorkSnapshotAdapter(snap).fetch_snapshot().transactions[0]
    # The clean Crew `title` is the merchant label; the raw processor string
    # never becomes the label (it stays available as raw_description).
    assert txn.merchant == "Cumberland Farms"
    assert txn.raw_description == "CUMBERLAND FARMS 5543 660000003542 - AUTHORIZATION CLEARING"


def test_adapter_keeps_parent_account_transactions():
    """Transactions without a subaccount must still be retained via the
    synthetic parent account (never silently dropped by the sync engine)."""
    snap = _snapshot()
    snap["data"]["transactions"]["data"]["account"]["cashTransactions"]["edges"].append(
        {
            "node": {
                "id": "Q2FzaFRyYW5zYWN0aW9uOjI=",
                "amount": -1000,
                "currencyCode": "USD",
                "description": "Account-level transfer",
                "title": "Transfer",
                "occurredAt": "2026-09-01T10:00:00Z",
                "type": "TRANSFER",
                "status": "CLEARED",
                "subaccount": None,
                "matchingName": None,
                "memo": None,
            }
        }
    )
    snapshot = CrewWorkSnapshotAdapter(snap).fetch_snapshot()
    # The parent account id is present so the transfer transaction maps to it.
    transfer = [t for t in snapshot.transactions if t.external_id == "Q2FzaFRyYW5zYWN0aW9uOjI="]
    assert len(transfer) == 1
    assert transfer[0].account_external_id == "QWNjb3VudDox"
    # The synthetic parent account exists in the normalized accounts.
    parent_ids = {a.external_id for a in snapshot.accounts}
    assert "QWNjb3VudDox" in parent_ids


def test_adapter_marks_incomplete_when_snapshot_incomplete():
    snapshot = dict(_snapshot())
    snapshot["complete"] = False
    result = CrewWorkSnapshotAdapter(snapshot).fetch_snapshot()
    assert result.is_complete is False


def test_adapter_rejects_unsafe_source():
    # A snapshot that claims mutation authority must be rejected.
    bad = dict(_snapshot())
    bad["mutations_enabled"] = True
    try:
        CrewWorkSnapshotAdapter(bad).fetch_snapshot()
    except ValueError:
        return
    raise AssertionError("mutation-capable snapshot must be rejected")


def test_adapter_emits_live_bills_as_commitment_candidates():
    """Crew `expenses.bills` become commitment candidates (real money
    obligations), converted to dollars and keyed by the Crew bill id."""
    snap = _snapshot()
    snap["data"]["expenses"] = {
        "data": {
            "currentUser": {
                "accounts": [
                    {
                        "billReserve": {
                            "bills": [
                                {
                                    "id": "QmlsbDox",
                                    "name": "Verizon",
                                    "amount": 9541,
                                    "dayOfMonth": 22,
                                    "frequency": "MONTHLY",
                                    "estimatedNextFundingAmount": 4389,
                                    "reservedAmount": 5000,
                                    "anchorDate": "2026-09-22",
                                },
                                {
                                    "id": "QmlsbDoy",
                                    "name": "Rent",
                                    "amount": 144200,
                                    "dayOfMonth": 5,
                                    "frequency": "MONTHLY",
                                    "estimatedNextFundingAmount": 66327,
                                    "reservedAmount": 0,
                                    "anchorDate": "2026-09-16",
                                },
                            ]
                        }
                    }
                ]
            }
        }
    }
    candidates = CrewWorkSnapshotAdapter(snap).fetch_snapshot().commitment_candidates
    assert len(candidates) == 2

    verizon = next(c for c in candidates if c.external_id == "QmlsbDox")
    assert verizon.name == "Verizon"
    assert verizon.amount == 95.41  # cents -> dollars
    # R33: the anchorDate/frequency/reservedAmount must be carried through so
    # Plan shows the authoritative due date, recurrence, and funding.
    assert verizon.due_date == "2026-09-22"
    assert verizon.recurrence == "monthly"  # MONTHLY normalized to lowercase
    assert verizon.funded_amount == 50.00  # reservedAmount cents -> dollars
    rent = next(c for c in candidates if c.external_id == "QmlsbDoy")
    assert rent.amount == 1442.00
    assert rent.due_date == "2026-09-16"
    assert rent.funded_amount == 0.0


# --- C4: the virtual_cards and autopilot facets were always fetched -----------
# The connector's snapshot() has always requested eight facets; Meridian read
# only four and discarded these. Reading them needs no connector change, and the
# distinction that matters is unobserved (None) vs observed-empty ([]).


def _facets(cards=None, rules=None, complete=True, with_cards=True, with_rules=True):
    data = {}
    if with_cards:
        data["virtual_cards"] = {
            "data": {
                "currentUser": {
                    "family": {
                        "children": [
                            {"id": "user:1", "virtualDebitCards": cards or []}
                        ],
                        "parents": [],
                    }
                }
            }
        }
    if with_rules:
        data["autopilot"] = {
            "data": {"currentUser": {"family": {"rules": rules or []}}}
        }
    return {
        "mode": "read-only",
        "source": "crew",
        "captured_at": "2026-09-13T12:00:00Z",
        "complete": complete,
        "mutations_enabled": False,
        "data": data,
    }


def test_virtual_cards_readback_returns_observed_cards():
    adapter = CrewWorkSnapshotAdapter(
        _facets(cards=[{"id": "card:1", "name": "Zz Card", "color": "TEAL"}])
    )

    cards = adapter.readback_virtual_cards()

    assert [c["id"] for c in cards] == ["card:1"]
    assert cards[0]["color"] == "TEAL"


def test_an_unobserved_card_facet_is_none_not_an_empty_list():
    """A facet the connector could not read is unobserved, never 'no cards'.

    Collapsing the two would let a failed read masquerade as a provider statement
    that no card  the same error class as an unreported reserve read as 0.
    """
    adapter = CrewWorkSnapshotAdapter(_facets(with_cards=False))

    assert adapter.readback_virtual_cards() is None


def test_an_observed_but_empty_card_facet_is_an_empty_list():
    adapter = CrewWorkSnapshotAdapter(_facets(cards=[]))

    assert adapter.readback_virtual_cards() == []


def test_autopilot_rules_readback_returns_observed_rules_and_none_when_unobserved():
    adapter = CrewWorkSnapshotAdapter(
        _facets(rules=[{"id": "rule:1", "name": "Round Up", "isPaused": False}])
    )
    assert [r["id"] for r in adapter.readback_autopilot_rules()] == ["rule:1"]

    assert CrewWorkSnapshotAdapter(_facets(with_rules=False)).readback_autopilot_rules() is None
    assert CrewWorkSnapshotAdapter(_facets(rules=[])).readback_autopilot_rules() == []


def test_card_readback_deduplicates_a_card_listed_under_two_family_members():
    payload = _facets(cards=[{"id": "card:1", "name": "Zz Card"}])
    family = payload["data"]["virtual_cards"]["data"]["currentUser"]["family"]
    family["parents"] = [{"id": "user:2", "virtualDebitCards": [{"id": "card:1", "name": "Zz Card"}]}]

    cards = CrewWorkSnapshotAdapter(payload).readback_virtual_cards()

    assert [c["id"] for c in cards] == ["card:1"]


def _spend_card(selected_id, is_child=False, card_id="card:1"):
    config = {"id": "cfg:1"}
    config["selectedSpendSubaccount"] = {"id": selected_id} if selected_id else None
    return {"id": card_id, "name": "Card", "color": "TEAL",
            "user": {"id": "user:1", "isChild": is_child, "userSpendConfig": config}}


def test_selected_spend_pocket_returns_the_single_observed_selection():
    adapter = CrewWorkSnapshotAdapter(_facets(cards=[_spend_card("Sub:spend")]))

    assert adapter.readback_selected_spend_pocket() == ("Sub:spend",)


def test_selected_spend_pocket_is_none_when_the_facet_was_not_observed():
    adapter = CrewWorkSnapshotAdapter(_facets(with_cards=False))

    assert adapter.readback_selected_spend_pocket() is None


def test_selected_spend_pocket_is_empty_when_no_card_exposes_a_selection():
    adapter = CrewWorkSnapshotAdapter(_facets(cards=[_spend_card(None)]))

    assert adapter.readback_selected_spend_pocket() == ()


def test_selected_spend_pocket_reports_conflicting_selections_rather_than_picking():
    """Two different selections cannot both be current; the caller must not guess."""
    adapter = CrewWorkSnapshotAdapter(
        _facets(cards=[_spend_card("Sub:a", card_id="card:1"),
                       _spend_card("Sub:b", card_id="card:2")])
    )

    assert adapter.readback_selected_spend_pocket() == ("Sub:a", "Sub:b")


def test_selected_spend_pocket_ignores_a_childs_own_configuration():
    """SetSpendSubaccount sets the signed-in user's selection, not a child's."""
    adapter = CrewWorkSnapshotAdapter(
        _facets(cards=[_spend_card("Sub:parent", card_id="card:1"),
                       _spend_card("Sub:child", is_child=True, card_id="card:2")])
    )

    assert adapter.readback_selected_spend_pocket() == ("Sub:parent",)


# --- C4: fundingPlans and reassignmentRules (connector fields added bd7d8b1) ---


def _expenses_facet(plans=None, reserve_id="res:1", total=0, with_facet=True):
    data = {}
    if with_facet:
        data["expenses"] = {"data": {"currentUser": {"accounts": [
            {"id": "acct:1", "billReserve": {"id": reserve_id,
                                             "totalReservedAmount": total,
                                             "fundingPlans": plans or []}}]}}}
    return {"mode": "read-only", "source": "crew", "mutations_enabled": False,
            "complete": True, "captured_at": "2026-09-14T12:00:00Z", "data": data}


def _family_rules_facet(rules=None, with_facet=True):
    data = {}
    if with_facet:
        data["family"] = {"data": {"currentUser": {"family": {"reassignmentRules": rules or []}}}}
    return {"mode": "read-only", "source": "crew", "mutations_enabled": False,
            "complete": True, "captured_at": "2026-09-14T12:00:00Z", "data": data}


def test_funding_plans_readback_carries_its_reserve_identity():
    adapter = CrewWorkSnapshotAdapter(_expenses_facet(
        reserve_id="res:9", plans=[{"id": "plan:1", "name": "Cash App", "amount": 42720}]))

    plans = adapter.readback_funding_plans()

    assert [p["id"] for p in plans] == ["plan:1"]
    # The parent reserve id travels with the plan, so a plan is attributable and
    # not merely name-matched.
    assert plans[0]["billReserveId"] == "res:9"


def test_unobserved_funding_plan_facet_is_none_not_empty():
    adapter = CrewWorkSnapshotAdapter(_expenses_facet(with_facet=False))
    assert adapter.readback_funding_plans() is None


def test_observed_empty_funding_plans_is_an_empty_list():
    adapter = CrewWorkSnapshotAdapter(_expenses_facet(plans=[]))
    assert adapter.readback_funding_plans() == []


def test_reserve_totals_are_keyed_by_reserve_id():
    adapter = CrewWorkSnapshotAdapter(_expenses_facet(reserve_id="res:3", total=12345))
    assert adapter.readback_reserve_totals() == {"res:3": 12345}
    assert CrewWorkSnapshotAdapter(_expenses_facet(with_facet=False)).readback_reserve_totals() is None


def test_reassignment_rules_readback_distinguishes_empty_from_unobserved():
    adapter = CrewWorkSnapshotAdapter(_family_rules_facet(
        rules=[{"id": "rule:1", "match": "Example", "minAmount": 500}]))
    assert [r["id"] for r in adapter.readback_reassignment_rules()] == ["rule:1"]

    assert CrewWorkSnapshotAdapter(_family_rules_facet(rules=[])).readback_reassignment_rules() == []
    assert CrewWorkSnapshotAdapter(_family_rules_facet(with_facet=False)).readback_reassignment_rules() is None
