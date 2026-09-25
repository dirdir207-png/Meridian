"""Read-only Meridian provider adapter for a CrewWorkAssistant snapshot.

CrewWorkAssistant (the ``crew-readonly`` MCP server) produces a Credential-free
Crew dashboard snapshot exactly matching the mobile/API auth Crew supports
(JWT + Stytch session token kept in the Mac Keychain). This adapter consumes
that snapshot — it never makes Crew network calls and never touches
credentials — and normalizes it into Meridian ProviderSnapshot records.

Balances and amounts in the snapshot are cents; the adapter converts to the
dollar convention used by CrewReadAdapter (divide by 100).
"""

from typing import Any, Dict, Optional

from .base import (
    CommitmentCandidate,
    FundingPlanCandidate,
    NormalizedAccount,
    NormalizedBillReserve,
    NormalizedTransaction,
    ProviderSnapshot,
)

# Map Crew's status / type strings to the Meridian transaction status
# vocabulary used by the sync engine (see meridian/sync and CrewReadAdapter).
_STATUS_MAP = {
    "CLEARED": "posted",
    "POSTED": "posted",
    "PENDING": "pending",
    "DEBIT": "posted",
    "CREDIT": "posted",
    "UNKNOWN": "posted",
}

# Account type: primary pocket -> checking, everything else -> pocket.
_ACCOUNT_TYPE = {"ACTIVATED": "checking"}

# Crew expresses a schedule as ``frequency`` + ``frequencyInterval``, Meridian as a
# single cadence name. Only the combinations that mean EXACTLY one Meridian cadence
# are listed. Anything else (MONTHLY x2, WEEKLY x3, DAILY, a missing interval) is
# deliberately absent: coercing it to the nearest cadence would report a schedule
# Meridian cannot honour, which is the same class of error the shared cadence rule
# refuses to make when it returns None instead of defaulting to weekly.
_CADENCE_MAP = {
    ("WEEKLY", 1): "weekly",
    ("WEEKLY", 2): "biweekly",
    ("MONTHLY", 1): "monthly",
    ("SEMIMONTHLY", 1): "semimonthly",
    ("ANNUAL", 1): "annually",
    ("ANNUALLY", 1): "annually",
    ("YEARLY", 1): "annually",
}


def _meridian_cadence(frequency: Any, interval: Any) -> Optional[str]:
    """The plan's schedule in Meridian's vocabulary, or None when not exact."""
    try:
        periods = int(interval)
    except (TypeError, ValueError):
        return None
    return _CADENCE_MAP.get((str(frequency or "").strip().upper(), periods))


def _status(value: Optional[str]) -> str:
    if value is None:
        return "posted"
    return _STATUS_MAP.get(str(value).upper(), "posted")


def _clean_merchant(raw: Optional[str]) -> Optional[str]:
    """Best-effort cleanup of the raw processor string so it reads as a label:
    drop the trailing ' - AUTHORIZATION/CLEARING/...' and star/noise prefixes.
    Is conservative: returns None when nothing recognizable remains."""
    if not raw:
        return None
    text = str(raw).strip()
    # Cut everything from the first " - " (negative/dash separating suffix).
    for marker in (" - ", " -A", ":", " REFUND", " RETURN", " REVERSAL"):
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx]
            break
    text = text.strip(" -*#.").strip()
    return text or None


def _cents_to_dollars(value: Any) -> float:
    try:
        return float(value or 0) / 100
    except (TypeError, ValueError):
        return 0.0


def _cents_to_dollars_or_none(value: Any) -> Optional[float]:
    """Cents to dollars, or None when the provider did not report the field.

    An absent field is not a zero. Conflating them makes a bill whose reserve was
    never reported look like a bill whose reserve was explicitly emptied, and
    because ``funded_amount`` is NOT NULL locally that zero then erases the
    amount Meridian last knew (C01).
    """
    if value is None or value == "":
        return None
    try:
        return float(value) / 100
    except (TypeError, ValueError):
        return None


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


class CrewWorkSnapshotAdapter:
    """Translate a CrewWorkAssistant snapshot into Meridian's read-only model."""

    provider_name = "crew"
    connection_external_id = "crew-work-assistant"
    connection_name = "Crew (Work Assistant)"

    def __init__(self, snapshot: Dict[str, Any]):
        if not isinstance(snapshot, dict):
            raise ValueError("CrewWorkAssistant snapshot must be an object")
        if snapshot.get("mode") != "read-only" or snapshot.get("source") != "crew":
            raise ValueError("CrewWorkAssistant snapshot must come from the read-only Crew source")
        if snapshot.get("mutations_enabled", False) is not False:
            raise ValueError("CrewWorkAssistant snapshot cannot claim mutation authority")
        self._snapshot = snapshot

    def fetch_snapshot(self) -> ProviderSnapshot:
        captured_at = self._snapshot.get("captured_at") or ""
        complete = bool(self._snapshot.get("complete"))
        snap_errors = self._snapshot.get("errors") or {}

        accounts = self._collect_accounts(captured_at)
        transactions = self._collect_transactions(accounts)
        commitment_candidates = self._collect_commitment_candidates()
        funding_plans = self._collect_funding_plans()
        bill_reserves = self._collect_bill_reserves()
        errors = tuple(self._snapshot_errors(snap_errors))

        return ProviderSnapshot(
            connection_external_id=self.connection_external_id,
            connection_name=self.connection_name,
            accounts=tuple(accounts),
            transactions=tuple(transactions),
            commitment_candidates=tuple(commitment_candidates),
            funding_plans=None if funding_plans is None else tuple(funding_plans),
            bill_reserves=None if bill_reserves is None else tuple(bill_reserves),
            is_complete=complete and not errors,
            errors=errors,
        )

    def _collect_commitment_candidates(self) -> list[CommitmentCandidate]:
        """Map Crew bill-reserve bills to BILL commitment candidates.

        `bills` are the real recurring money obligations (Verizon, Rent, …).
        Amounts are cents; funding surface (reservedAmount) maps to dollar
        amount on the BILL record, and the Crew bill id is the stable key.

        The containing reserve's own id is read here too. It was previously bound
        and discarded, which is why the dial could only ever report funding unknown:
        the funding plans (022) already store the reserve they belong to, so the
        reserve id is the whole join. ``""`` means the id was not observed; it is
        passed through as unobserved rather than fabricated, and the sync refuses to
        let it overwrite an observed membership.
        """
        data = _as_dict(self._snapshot.get("data"))
        expenses_payload = _as_dict(data.get("expenses"))
        current_user = _as_dict(_as_dict(expenses_payload).get("data")).get("currentUser")
        accounts = _as_list(_as_dict(current_user).get("accounts"))
        result = []
        for account in accounts:
            bill_reserve = _as_dict(account.get("billReserve"))
            bill_reserve_id = str(bill_reserve.get("id") or "")
            for bill in _as_list(bill_reserve.get("bills")):
                external_id = str(bill.get("id") or "")
                name = str(bill.get("name") or "Crew bill")
                amount = _cents_to_dollars(bill.get("amount"))
                if not external_id:
                    continue
                # R33: carry Crew's real per-bill fields so the commitment in
                # Plan shows the authoritative anchorDate (due date), frequency
                # (recurrence), and reservedAmount (funded). Crew sets these per
                # bill; do not drop them.
                anchor_date = str(bill.get("anchorDate") or "") or None
                frequency = str(bill.get("frequency") or "").lower() or None
                # Use the nullable form: an unreported reserve must stay absent
                # rather than reading as an emptied one (C01).
                reserved = _cents_to_dollars_or_none(bill.get("reservedAmount"))
                # Crew states its own per-event contribution and deadline for this bill in
                # the same read (025). Both use the nullable conversion: an unreported field
                # is missing data, not a zero, and the sync refuses to let it erase a value
                # Meridian already knew.
                reported_estimate = _cents_to_dollars_or_none(
                    bill.get("estimatedNextFundingAmount")
                )
                reserved_by = str(bill.get("reservedBy") or "") or None
                result.append(
                    CommitmentCandidate(
                        external_id=external_id,
                        name=name,
                        amount=amount,
                        currency="USD",
                        due_date=anchor_date,
                        recurrence=frequency,
                        funded_amount=reserved,
                        bill_reserve_id=bill_reserve_id,
                        estimated_next_funding_amount=reported_estimate,
                        reserved_by=reserved_by,
                    )
                )
        return result

    def _collect_funding_plans(self) -> Optional[list[FundingPlanCandidate]]:
        """Normalize ``billReserve.fundingPlans`` into Meridian's own vocabulary.

        Reuses :meth:`readback_funding_plans` rather than re-walking the facet, so the
        write-verification path and the ingestion path can never disagree about where a
        plan lives or which reserve owns it. The ``None`` (not observed) versus ``()``
        (observed empty) distinction is the readback's and is preserved exactly, because
        absence reconciliation depends on it.

        Amounts are converted from Crew's cents to Meridian's dollars here, at the
        provider boundary, the same way bills are. A plan with no provider id is skipped:
        the id is the identity the whole slice rests on, and storing the plan under a
        fabricated key would make it unciteable and unlinkable.
        """
        plans = self.readback_funding_plans()
        if plans is None:
            return None
        captured_at = str(self._snapshot.get("captured_at") or "") or None
        collected = []
        for plan in plans:
            external_id = str(plan.get("id") or "")
            if not external_id:
                continue
            collected.append(
                FundingPlanCandidate(
                    external_id=external_id,
                    name=str(plan.get("name") or "Crew funding plan"),
                    amount=_cents_to_dollars(plan.get("amount")),
                    bill_reserve_id=str(plan.get("billReserveId") or ""),
                    cadence=_meridian_cadence(
                        plan.get("frequency"), plan.get("frequencyInterval")
                    ),
                    anchor_date=str(plan.get("anchorDate") or "") or None,
                    observed_at=captured_at,
                )
            )
        return collected

    def _collect_bill_reserves(self) -> Optional[list[NormalizedBillReserve]]:
        """The observed reserve totals, or None when the facet was not returned.

        Reuses :meth:`readback_reserve_totals` for the same reason the funding plans
        reuse their readback: the write-verification path and the ingestion path must
        never disagree about where a reserve's total lives. ``None`` (not observed)
        versus a dict (observed, possibly empty) is preserved exactly, because absence
        reconciliation may only conclude from the second.

        The total is nullable on purpose (C01): a reserve Crew did not report a total
        for must stay absent rather than read as an emptied bucket, so
        ``_cents_to_dollars_or_none`` is the conversion -- not the zero-defaulting one.

        The reserve's own reported funding schedule (025) is merged in from its readback:
        ``nextFundingDate`` is Crew's statement of the next funding event, and the
        reserve-level ``estimatedNextFundingAmount`` -- which D-015 resolved on 2026-09-20 to be
        an ACCOUNT-TOTAL snapshot (the reserve plus the spendable subaccounts), not a reserve
        figure -- is carried verbatim with its provenance and never treated as an amount set
        aside. Both stay ``None`` when unreported.
        """
        totals = self.readback_reserve_totals()
        if totals is None:
            return None
        schedule = self.readback_reserve_funding_schedule() or {}
        captured_at = str(self._snapshot.get("captured_at") or "") or None
        return [
            NormalizedBillReserve(
                external_id=reserve_id,
                total_reserved_amount=_cents_to_dollars_or_none(total),
                currency="USD",
                observed_at=captured_at,
                estimated_next_funding_amount=_cents_to_dollars_or_none(
                    (schedule.get(reserve_id) or {}).get("estimatedNextFundingAmount")
                ),
                next_funding_date=str(
                    (schedule.get(reserve_id) or {}).get("nextFundingDate") or ""
                ) or None,
            )
            for reserve_id, total in totals.items()
        ]

    def _snapshot_errors(self, snap_errors: Any) -> list[str]:
        if not isinstance(snap_errors, dict):
            return []
        # Error details are human-readable summaries produced by the MCP; keep
        # them as-is but never surface raw source payloads.
        values = []
        for key, message in snap_errors.items():
            values.append(f"{key}: {message}" if isinstance(message, str) else str(key))
        return values

    def _facet_payload(self, name: str) -> Optional[Dict[str, Any]]:
        """One facet's GraphQL ``data``, or None when the facet was not returned.

        The connector records a facet it could not read in ``errors`` and omits it
        from ``data`` entirely, so an absent facet means "not observed". That is
        NOT the same as a facet that returned no records, and the two must never
        be collapsed — the C01 unreported-reserve rule applies to every facet.
        """
        data = _as_dict(self._snapshot.get("data"))
        facet = data.get(name)
        if not isinstance(facet, dict):
            return None
        payload = facet.get("data")
        return payload if isinstance(payload, dict) else None

    def readback_virtual_cards(self) -> Optional[list]:
        """The virtual debit cards this snapshot observed, or None if unobserved.

        Read-only view of the ``virtual_cards`` facet, which the connector has
        always fetched and Meridian previously discarded.
        """
        payload = self._facet_payload("virtual_cards")
        if payload is None:
            return None
        family = _as_dict(_as_dict(payload.get("currentUser")).get("family"))
        cards = []
        seen = set()
        for group in ("children", "parents"):
            for member in _as_list(family.get(group)):
                for card in _as_list(_as_dict(member).get("virtualDebitCards")):
                    if not isinstance(card, dict):
                        continue
                    card_id = str(card.get("id") or "")
                    if not card_id or card_id in seen:
                        continue
                    seen.add(card_id)
                    cards.append(card)
        return cards

    def readback_physical_cards(self) -> Optional[list]:
        """The physical cards this snapshot observed, or None if unobserved.

        Added 2026-09-25 for the owner's own clarification of what the setting MEANS: *"the spend
        pocket in crew refers to what pocket the physical card drops from."* Crew carries the same
        per-user ``userSpendConfig.selectedSpendSubaccount`` on the physical card
        (``currentUser.family.parents[i].activePhysicalDebitCard.user`` — verified in the owner's real
        capture, where it names the same pocket as all three virtual cards), and until now we read
        only the virtual facet. So a physical card whose selection DIFFERED would have been invisible
        to the figure rather than reported as a disagreement.

        Card objects are collected by shape rather than by field name on purpose: the facet exposes
        them under several keys (activePhysicalDebitCard, issuingPhysicalCard, …), and what makes an
        object a card here is that it carries a user with a spend config. Child members are included
        so the caller's own child-skipping rule stays in ONE place.
        """
        payload = self._facet_payload("physical_cards")
        if payload is None:
            return None
        family = _as_dict(_as_dict(payload.get("currentUser")).get("family"))
        cards = []
        seen = set()
        for group in ("children", "parents"):
            for member in _as_list(family.get(group)):
                for value in _as_dict(member).values():
                    for card in ([value] if isinstance(value, dict) else _as_list(value)):
                        if not isinstance(card, dict):
                            continue
                        if "user" not in card and "userSpendConfig" not in card:
                            continue
                        card_id = str(card.get("id") or "")
                        if card_id and card_id in seen:
                            continue
                        if card_id:
                            seen.add(card_id)
                        cards.append(card)
        return cards

    def readback_capture_time(self) -> Optional[str]:
        """When this snapshot was captured, or ``None`` when it did not say.

        Used to IDENTIFY an observation (OS-113): one capture is one observation, so re-ingesting the
        same capture records nothing new rather than manufacturing a second, competing spend-pocket
        selection. ``None`` is passed through rather than substituted, because a fabricated capture
        time would look like an observation that was actually made.
        """
        value = self._snapshot.get("captured_at")
        return str(value) if value else None

    def readback_selected_spend_pocket(self, *, include_physical_cards: bool = False) -> Optional[tuple]:
        """The signed-in user's selected spend pocket, as observed, or None.

        The selection is carried on every card as
        ``user.userSpendConfig.selectedSpendSubaccount`` (live-verified). It is a
        per-user setting repeated per card, so this returns the DISTINCT observed
        ids and lets the caller refuse to guess:

          None     -> the cards facet was not observed at all
          ()       -> observed, but no card exposed a selection
          (one,)   -> exactly one selection; the provider's current value
          (a, b)   -> the cards disagreed; genuinely ambiguous, never resolved

        Cards belonging to a child are skipped: ``SetSpendSubaccount`` sets the
        signed-in user's selection, and a child's own spend config is theirs.

        ``include_physical_cards`` decides WHICH SURFACE the caller is asking about, and defaults to
        the virtual facet alone for a reason worth keeping (owner's clarification, 2026-09-25): the
        setting means the pocket the PHYSICAL card spends from, so the money figure must include the
        physical card — a divergence between card types is exactly the case the figure must not miss,
        and it is recorded as ``ambiguous`` rather than resolved. Write VERIFICATION asks the narrower
        question — "did the write I just made take effect on the surface it writes to?" — and reading
        a second surface there could report a failure while the physical card merely lags behind, so
        it keeps the default. Pass True from the ingest that feeds the read path.
        """
        observed = set()
        witnessed = False
        card_groups = [self.readback_virtual_cards()]
        if include_physical_cards:
            card_groups.append(self.readback_physical_cards())
        for cards in card_groups:
            if cards is None:
                continue
            witnessed = True
            for card in cards:
                user = _as_dict(card.get("user"))
                if user.get("isChild"):
                    continue
                config = _as_dict(user.get("userSpendConfig"))
                selection = _as_dict(config.get("selectedSpendSubaccount"))
                selected_id = str(selection.get("id") or "")
                if selected_id:
                    observed.add(selected_id)
        if not witnessed:
            return None
        return tuple(sorted(observed))

    def readback_autopilot_rules(self) -> Optional[list]:
        """The autopilot rules this snapshot observed, or None if unobserved."""
        payload = self._facet_payload("autopilot")
        if payload is None:
            return None
        family = _as_dict(_as_dict(payload.get("currentUser")).get("family"))
        return [rule for rule in _as_list(family.get("rules")) if isinstance(rule, dict)]

    def readback_funding_plans(self) -> Optional[list]:
        """Every bill-reserve funding plan this snapshot observed, or None.

        Read-only view of ``billReserve.fundingPlans`` on the ``expenses`` facet
        (added to the connector so this field is actually requested). Each entry
        carries the parent ``billReserve_id`` so a plan can be attributed to the
        reserve it belongs to rather than matched by name alone.
        """
        payload = self._facet_payload("expenses")
        if payload is None:
            return None
        accounts = _as_list(_as_dict(payload.get("currentUser")).get("accounts"))
        plans = []
        for account in accounts:
            reserve = _as_dict(_as_dict(account).get("billReserve"))
            reserve_id = str(reserve.get("id") or "")
            for plan in _as_list(reserve.get("fundingPlans")):
                if not isinstance(plan, dict):
                    continue
                plans.append({**plan, "billReserveId": reserve_id})
        return plans

    def readback_reserve_totals(self) -> Optional[dict]:
        """``{billReserveId: totalReservedAmount}`` observed, or None if unobserved.

        Attribution keys on the reserve id. A total on its own is not proof of a
        particular top-up, so callers must treat this as the reserve's state and
        not as evidence that a specific write landed.
        """
        payload = self._facet_payload("expenses")
        if payload is None:
            return None
        accounts = _as_list(_as_dict(payload.get("currentUser")).get("accounts"))
        totals = {}
        for account in accounts:
            reserve = _as_dict(_as_dict(account).get("billReserve"))
            reserve_id = str(reserve.get("id") or "")
            if not reserve_id:
                continue
            totals[reserve_id] = reserve.get("totalReservedAmount")
        return totals

    def readback_reserve_funding_schedule(self) -> Optional[dict]:
        """``{billReserveId: {estimatedNextFundingAmount, nextFundingDate}}`` or None.

        A separate readback rather than a wider return from
        :meth:`readback_reserve_totals`, because that method's shape is the contract the
        reserve write-verification path depends on: widening it would change what a verifier
        compares. ``None`` (facet not returned) versus a dict (observed, possibly with
        unreported fields inside) is preserved exactly, and the values are returned RAW --
        cents and the provider's own date string -- so the caller does the one conversion at
        the provider boundary, exactly as it does for the total.
        """
        payload = self._facet_payload("expenses")
        if payload is None:
            return None
        accounts = _as_list(_as_dict(payload.get("currentUser")).get("accounts"))
        schedule = {}
        for account in accounts:
            reserve = _as_dict(_as_dict(account).get("billReserve"))
            reserve_id = str(reserve.get("id") or "")
            if not reserve_id:
                continue
            schedule[reserve_id] = {
                "estimatedNextFundingAmount": reserve.get("estimatedNextFundingAmount"),
                "nextFundingDate": reserve.get("nextFundingDate"),
            }
        return schedule

    def readback_reassignment_rules(self) -> Optional[list]:
        """The pocket reassignment rules observed, or None if unobserved.

        Read-only view of ``family.reassignmentRules`` (added to the connector).
        An empty list is a real observation that no rules exist; None means the
        facet was not returned at all.
        """
        payload = self._facet_payload("family")
        if payload is None:
            return None
        family = _as_dict(_as_dict(payload.get("currentUser")).get("family"))
        return [rule for rule in _as_list(family.get("reassignmentRules")) if isinstance(rule, dict)]

    def readback_transfers(self) -> Optional[list]:
        """The observed transfer links in the transactions facet, or None if unobserved.

        Each entry is a dict: ``external_id`` (the cash transaction), ``transfer_id``,
        ``transfer_type``, ``status``, and ``subaccount_id``.

        The distinction that matters: ``None`` means the transactions facet was not
        returned at all (the connector records the failure and omits it), while ``[]``
        means it was observed but no transaction carried a transfer link. Collapsing
        the two would let a failed read masquerade as a provider statement that no
        transfer exists.

        IMPORTANT — this is deliberately a *presence* read. The connector fetches a
        single page of transactions (``pageSize`` 100, null cursor), so an id that is
        absent here may simply be on an unobserved page. Callers must therefore never
        treat absence from this list as proof that a transfer failed; only presence
        is evidence.
        """
        payload = self._facet_payload("transactions")
        if payload is None:
            return None
        account_node = _as_dict(_as_dict(payload).get("account"))
        edges = _as_list(_as_dict(_as_dict(account_node).get("cashTransactions")).get("edges"))
        transfers = []
        for edge in edges:
            node = _as_dict(_as_dict(edge).get("node"))
            external_id = str(node.get("id") or "")
            if not external_id:
                continue
            transfer = _as_dict(node.get("transfer"))
            transfer_id = str(transfer.get("id") or "")
            if not transfer_id:
                # An id-less link cannot identify a transfer; skip it rather than
                # reporting an entry no verifier could ever match.
                continue
            subaccount = _as_dict(node.get("subaccount"))
            transfers.append(
                {
                    "external_id": external_id,
                    "transfer_id": transfer_id,
                    "transfer_type": str(transfer.get("type") or ""),
                    "status": str(transfer.get("status") or ""),
                    "subaccount_id": str(subaccount.get("id") or ""),
                }
            )
        return transfers

    def _collect_accounts(self, captured_at: str = "") -> list[NormalizedAccount]:
        data = _as_dict(self._snapshot.get("data"))
        # The snapshot keeps account identity in data.accounts (id/name only)
        # and the pocket subaccounts (with balances) in data.pockets. The
        # CrewReadAdapter convention: primary pocket -> checking, else pocket.
        pockets_payload = _as_dict(data.get("pockets"))
        current_user = _as_dict(_as_dict(pockets_payload).get("data")).get("currentUser")
        source_accounts = _as_list(_as_dict(current_user).get("accounts"))
        owned = set()
        result = []
        for source in source_accounts:
            account_id = str(source.get("id") or "")
            if not account_id:
                continue
            for pocket in _as_list(source.get("subaccounts")):
                external_id = str(pocket.get("id") or "")
                if not external_id:
                    continue
                owned.add(external_id)
                name = str(pocket.get("displayName") or pocket.get("name") or "Crew account")
                is_primary = bool(pocket.get("isPrimary"))
                result.append(
                    NormalizedAccount(
                        external_id=external_id,
                        name=name,
                        account_type="checking" if is_primary else "pocket",
                        balance=_cents_to_dollars(pocket.get("overallBalance")),
                        currency="USD",
                        available_balance=_cents_to_dollars(pocket.get("clearedBalance")),
                        is_active=True,
                        source_updated_at=captured_at or None,
                    )
                )
        # Some transactions carry only the parent account (no subaccount) — e.g.
        # account-level transfers. Add a synthetic parent account so those
        # records are never dropped by the sync engine's account mapping.
        accounts_payload = _as_dict(data.get("accounts"))
        account_current_user = _as_dict(_as_dict(accounts_payload).get("data")).get("currentUser")
        for source in _as_list(_as_dict(account_current_user).get("accounts")):
            account_id = str(source.get("id") or "")
            if not account_id or account_id in owned:
                continue
            result.append(
                NormalizedAccount(
                    external_id=account_id,
                    name=str(source.get("displayName") or "Crew account"),
                    account_type="fallback",
                    balance=0.0,
                    currency="USD",
                    is_active=True,
                    source_updated_at=captured_at or None,
                )
            )
        return result

    def _collect_transactions(self, accounts: list[NormalizedAccount]) -> list[NormalizedTransaction]:
        owned = {account.external_id for account in accounts}
        transactions_payload = _as_dict(self._snapshot.get("data", {}).get("transactions"))
        account_node = _as_dict(_as_dict(transactions_payload).get("data")).get("account")
        edges = _as_list(_as_dict(_as_dict(account_node).get("cashTransactions")).get("edges"))
        observed_at = str(self._snapshot.get("captured_at") or "")

        result = []
        for edge in edges:
            node = _as_dict(edge.get("node"))
            external_id = str(node.get("id") or "")
            occurred_at = str(node.get("occurredAt") or "")
            if not external_id or not occurred_at:
                continue
            subaccount = _as_dict(node.get("subaccount"))
            pocket_id = str(subaccount.get("id") or "")
            account_external_id = pocket_id if pocket_id in owned else str(account_node.get("id") or pocket_id)
            # Crew's `title` is the clean merchant name ("Cumberland Farms",
            # "Walmart"); `matchingName` is the raw processor string
            # ("... - AUTHORIZATION CLEARING"). Prefer the clean title; fall
            # back to the cleaned matchingName; never show the raw processor
            # string as the primary label.
            clean_title = str(node.get("title") or "").strip() or None
            raw_merchant = str(node.get("matchingName") or "").strip() or None
            human_description = str(node.get("description") or "").strip() or None
            merchant = clean_title or _clean_merchant(raw_merchant) or "Crew transaction"
            result.append(
                NormalizedTransaction(
                    external_id=external_id,
                    account_external_id=account_external_id or (accounts[0].external_id if accounts else ""),
                    amount=_cents_to_dollars(node.get("amount")),
                    occurred_at=occurred_at,
                    description=human_description or clean_title or "Crew transaction",
                    status=_status(node.get("status") or node.get("type")),
                    currency=str(node.get("currencyCode") or "USD"),
                    merchant=merchant,
                    raw_description=node.get("memo") or node.get("externalMemo") or raw_merchant,
                    source_updated_at=observed_at or occurred_at,
                )
            )
        return result
