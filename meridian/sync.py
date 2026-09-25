"""Idempotent synchronization of provider snapshots into Meridian."""

from dataclasses import dataclass
from datetime import datetime, timezone

from .ai.classifier import classify_with_ai_fallback
from .bill_allocation import BillAllocationStore
from .classify import AssignmentRule, ClassificationInput, classify_deterministic
from .commitments import (
    CommitmentRepository,
    CommitmentType,
    commitment_fields_from_candidate,
    commitment_update_fields,
    observation_of_candidate,
)
from .providers.base import ProviderAdapter
from .reconcile import reconcile
from .spend_selection import SpendSelectionStore


def _now_iso() -> str:
    """The observation time, used only when a capture carries no timestamp of its own."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SyncReport:
    provider: str
    status: str
    accounts_synced: int
    transactions_synced: int
    errors: int


def _record_bill_allocations(adapter, repository, snapshot) -> int:
    """Record each observed bill's share of the reserve, as THIS capture saw it (OS-114).

    The money ``sync_providers`` writes into ``commitments.funded_amount`` is the same number, but that
    column is overwritten on every sync, so this is the only place the value survives as history. Runs
    for every provider whose candidates carry a per-bill reserved amount; a provider that never states
    one records silence rather than zero.

    Returns the number of rows written, for the sync report and for tests. Failures are swallowed for
    the same reason as the spend-selection hook: provenance must never cost the owner a reconciled run.
    """
    try:
        captured_at = _capture_time(adapter)
        store = BillAllocationStore(repository.db_path)
        written = 0
        for candidate in getattr(snapshot, "commitment_candidates", ()) or ():
            recorded = store.record(
                provider=adapter.provider_name,
                connection_external_id=adapter.connection_external_id,
                bill_external_id=candidate.external_id,
                bill_name=candidate.name,
                observed_at=captured_at,
                # `funded_amount` is Crew's per-bill `reservedAmount` (C01). None means the read was
                # silent about this bill, which is stored as silence, never as 0.0.
                reserved_amount=candidate.funded_amount,
                estimated_next_funding_amount=candidate.estimated_next_funding_amount,
                reserved_by=candidate.reserved_by,
                bill_reserve_id=candidate.bill_reserve_id or None,
            )
            if recorded is not None:
                written += 1
        return written
    except Exception:  # noqa: BLE001 - provenance must never fail a sync
        return 0


def _capture_time(adapter) -> str:
    """This capture's own timestamp, or the moment of this attempt when it carries none.

    One capture is one observation, and the capture's timestamp is what identifies it: using it as the
    observation key is what makes re-ingesting the same capture add nothing, instead of manufacturing a
    second history entry for the same moment.
    """
    reader = getattr(adapter, "readback_capture_time", None)
    if callable(reader):
        try:
            captured_at = reader()
        except Exception:  # noqa: BLE001 - a broken timestamp must not stop the ingest
            captured_at = None
        if captured_at:
            return str(captured_at)
    return _now_iso()


def _record_spend_selection(adapter, repository, snapshot) -> None:
    """Record WHICH pocket Crew says the owner spends from, as this snapshot observed it (OS-113).

    This is the ingest half of OS-113. Crew publishes the setting as
    ``userSpendConfig.selectedSpendSubaccount`` per user, repeated on every card, and the connector
    has always fetched that facet while Meridian discarded it. Recording it here is what lets the
    read path answer "which pocket is spendable" by Crew's own id instead of an English name — a
    name that is measurably ambiguous in the owner's real data (two ACTIVE pockets both called
    "Free to Spend" in one readable database).

    Three deliberate behaviours, each of which is a rule rather than a detail:

    * **An adapter that cannot answer records NOTHING.** Only Crew exposes
      ``readback_selected_spend_pocket``; other providers are skipped, and their absence is not a
      claim that the owner has no spend pocket.
    * **An unobserved facet records nothing.** The provider method returns ``None`` for "I did not
      see that facet", and ``SpendSelectionStore.record`` maps that to no row at all, so a failed
      read can never be stored as "no selection" (the C01 unreported-is-not-zero rule).
    * **A failure here never fails the sync.** The money that was reconciled is the point of the
      run; losing a provenance row must not cost the owner the accounts, so any error is swallowed
      — and, because nothing is recorded, the read path goes on saying "unobserved" rather than
      inventing an answer.
    """
    reader = getattr(adapter, "readback_selected_spend_pocket", None)
    if not callable(reader):
        return
    try:
        # Read BOTH card surfaces for the ingest (owner's clarification, 2026-09-25: Crew's "spend
        # pocket" is the pocket the PHYSICAL card drops from, so a physical card that disagreed with
        # the virtual ones must be visible as a disagreement rather than silently ignored). The
        # narrower default stays for write verification, which only asks whether the surface it wrote
        # to changed.
        try:
            observed = reader(include_physical_cards=True)
        except TypeError:
            # An adapter whose signature predates the flag: still an observation, just narrower.
            observed = reader()
        captured_at = _capture_time(adapter)
        store = SpendSelectionStore(repository.db_path)
        store.record(
            provider=adapter.provider_name,
            connection_external_id=adapter.connection_external_id,
            # The CAPTURE identifies the observation, so re-syncing one capture cannot manufacture a
            # second selection; a capture that carries no timestamp falls back to this run's own
            # identity, which is still unique per attempt.
            snapshot_id=f"{adapter.provider_name}:{captured_at}",
            observed=observed,
            observed_at=captured_at,
            freshness="fresh" if getattr(snapshot, "is_complete", False) else "partial",
            assumptions=(
                "read from the cards facet; the parent user's own config, children excluded",
            ),
        )
    except Exception:  # noqa: BLE001 - provenance must never fail a sync
        return


def sync_provider(adapter: ProviderAdapter, repository, *, ai_classifier=None) -> SyncReport:
    """Persist one read-only provider snapshot without deleting prior facts."""
    run = repository.begin_sync_run(
        provider=adapter.provider_name,
        connection_external_id=adapter.connection_external_id,
        connection_name=adapter.connection_name,
    )
    try:
        snapshot = adapter.fetch_snapshot()
    except Exception:
        repository.finish_sync_run(
            run.id,
            status="failed",
            accounts_synced=0,
            transactions_synced=0,
            errors=1,
        )
        return SyncReport(adapter.provider_name, "failed", 0, 0, 1)
    accounts_by_external_id = {}
    _record_spend_selection(adapter, repository, snapshot)
    user_rules = tuple(
        AssignmentRule(
            id=f"user:{rule.id}",
            category=rule.category,
            kind=rule.kind,
            merchant_pattern=rule.merchant_pattern,
            description_pattern=rule.description_pattern,
        )
        for rule in repository.list_assignment_rules()
    )
    errors = len(snapshot.errors)
    for account in snapshot.accounts:
        try:
            accounts_by_external_id[account.external_id] = repository.upsert_account(
                provider=adapter.provider_name,
                external_id=account.external_id,
                name=account.name,
                account_type=account.account_type,
                balance=account.balance,
                connection_id=run.connection_id,
                currency=account.currency,
                available_balance=account.available_balance,
                goal_target=account.goal_target,
                is_active=account.is_active,
                source_updated_at=account.source_updated_at,
            )
        except Exception:
            errors += 1

    transactions_synced = 0
    for transaction in snapshot.transactions:
        account = accounts_by_external_id.get(transaction.account_external_id)
        if account is None:
            errors += 1
            continue
        try:
            stored_transaction = repository.upsert_transaction(
                provider=adapter.provider_name,
                external_id=transaction.external_id,
                account_id=account.id,
                amount=transaction.amount,
                currency=transaction.currency,
                occurred_at=transaction.occurred_at,
                posted_at=transaction.posted_at,
                description=transaction.description,
                merchant=transaction.merchant,
                status=transaction.status,
                raw_description=transaction.raw_description,
                source_updated_at=transaction.source_updated_at,
            )
            source_account = next(
                (
                    item
                    for item in snapshot.accounts
                    if item.external_id == transaction.account_external_id
                ),
                None,
            )
            classification_input = ClassificationInput(
                    id=stored_transaction.id,
                    amount=transaction.amount,
                    description=transaction.description,
                    merchant=transaction.merchant,
                    account_type=(
                        source_account.account_type if source_account else "unknown"
                    ),
                    occurred_at=transaction.occurred_at,
                    relation_type=(
                        _relation_type_for_hint(transaction.relation_hint)
                    ),
                )
            classification = classify_deterministic(
                classification_input,
                user_rules=user_rules,
            )
            if ai_classifier is not None:
                classification = classify_with_ai_fallback(
                    classification_input,
                    classification,
                    ai_classifier,
                )
            repository.record_classification(stored_transaction.id, classification)
        except Exception:
            errors += 1
            continue
        transactions_synced += 1

    status = "complete" if snapshot.is_complete and errors == 0 else "partial"
    if snapshot.is_complete and errors == 0:
        # Only a complete, error-free read of this provider's own connection may
        # conclude that an account it used to return is gone. The conclusion is
        # recorded on the row; no history is deleted here.
        repository.mark_absent_accounts(
            provider=adapter.provider_name,
            connection_id=run.connection_id,
            observed_external_ids=tuple(accounts_by_external_id),
        )
    repository.finish_sync_run(
        run.id,
        status=status,
        accounts_synced=len(accounts_by_external_id),
        transactions_synced=transactions_synced,
        errors=errors,
    )
    return SyncReport(
        provider=adapter.provider_name,
        status=status,
        accounts_synced=len(accounts_by_external_id),
        transactions_synced=transactions_synced,
        errors=errors,
    )


def sync_providers(adapters, repository) -> tuple[SyncReport, ...]:
    """Synchronize read-only providers and reconcile their local evidence."""
    reports = []
    commitment_repository = CommitmentRepository(repository.db_path)
    for adapter in adapters:
        try:
            snapshot = adapter.fetch_snapshot()
        except Exception as error:
            class FailedAdapter:
                provider_name = adapter.provider_name
                connection_external_id = adapter.connection_external_id
                connection_name = adapter.connection_name

                def __init__(self, failure):
                    self._failure = failure

                def fetch_snapshot(self):
                    raise self._failure

            reports.append(sync_provider(FailedAdapter(error), repository))
            continue

        class SnapshotAdapter:
            provider_name = adapter.provider_name
            connection_external_id = adapter.connection_external_id
            connection_name = adapter.connection_name

            @staticmethod
            def fetch_snapshot():
                return snapshot

        report = sync_provider(SnapshotAdapter(), repository)
        reports.append(report)
        if report.status == "failed":
            continue
        # Both observation hooks run HERE, with the REAL adapter, because this path holds the candidate
        # objects while its local wrapper carries none of the readback methods `sync_provider` looks
        # for. Recording the selection here too closes a gap the singular path could not see: an ingest
        # through `sync_providers` used to leave the spend pocket unobserved entirely.
        _record_spend_selection(adapter, repository, snapshot)
        _record_bill_allocations(adapter, repository, snapshot)
        for candidate in snapshot.commitment_candidates:
            existing = commitment_repository.get_commitment_by_legacy(
                adapter.provider_name, candidate.external_id
            )
            observation = observation_of_candidate(candidate)
            if existing is None:
                commitment_repository.create(
                    type=CommitmentType.BILL,
                    legacy_source=adapter.provider_name,
                    legacy_id=candidate.external_id,
                    **commitment_fields_from_candidate(observation),
                )
            else:
                commitment_repository.update(
                    existing.id,
                    **commitment_update_fields(observation, existing),
                )
        if report.status == "complete":
            # Only a complete, error-free read of this provider may conclude that a
            # bill it used to return is gone.
            commitment_repository.mark_absent_bills(
                provider=adapter.provider_name,
                observed_external_ids=tuple(
                    candidate.external_id for candidate in snapshot.commitment_candidates
                ),
            )
        for expected_inflow in snapshot.expected_inflows:
            repository.upsert_reimbursement(
                provider=adapter.provider_name,
                external_id=expected_inflow.external_id,
                name=expected_inflow.name,
                amount=expected_inflow.amount,
                currency=expected_inflow.currency,
                source_updated_at=expected_inflow.source_updated_at,
            )
        # Crew funding plans are the owner's income source / Funding Cadence, and the
        # snapshot carrying them is fetched fresh and never cached, so this is the only
        # moment they can be kept. `None` means the read did not observe the surface at
        # all, which is not evidence of anything -- in particular not of a deletion --
        # so absence is only ever concluded from an observed-but-empty or a changed
        # complete read, never from an unobserved facet.
        if snapshot.funding_plans is not None:
            for plan in snapshot.funding_plans:
                repository.upsert_funding_plan(
                    provider=adapter.provider_name,
                    external_id=plan.external_id,
                    bill_reserve_id=plan.bill_reserve_id,
                    name=plan.name,
                    amount=plan.amount,
                    cadence=plan.cadence,
                    anchor_date=plan.anchor_date,
                    currency=plan.currency,
                    observed_at=plan.observed_at,
                )
            if report.status == "complete":
                repository.mark_absent_funding_plans(
                    provider=adapter.provider_name,
                    observed_external_ids=tuple(
                        plan.external_id for plan in snapshot.funding_plans
                    ),
                )
        # The reserve's own total set-aside funds is the dividend D-013's even-split
        # fallback divides across the reserve's bills (024). Same tri-state discipline
        # as the funding plans above: an unobserved facet is evidence of nothing, and an
        # unreported total is stored as NULL rather than as an emptied bucket.
        if snapshot.bill_reserves is not None:
            for reserve in snapshot.bill_reserves:
                repository.upsert_bill_reserve(
                    provider=adapter.provider_name,
                    external_id=reserve.external_id,
                    total_reserved_amount=reserve.total_reserved_amount,
                    currency=reserve.currency,
                    observed_at=reserve.observed_at,
                    # Crew's own reserve-level schedule (025), NULL when unreported; the
                    # reserve-level estimate is an ACCOUNT-TOTAL snapshot, not a reserve
                    # figure (D-015, resolved 2026-09-20), so it is never used as a
                    # dividend for any per-bill figure.
                    estimated_next_funding_amount=reserve.estimated_next_funding_amount,
                    next_funding_date=reserve.next_funding_date,
                )
            if report.status == "complete":
                repository.mark_absent_bill_reserves(
                    provider=adapter.provider_name,
                    observed_external_ids=tuple(
                        reserve.external_id for reserve in snapshot.bill_reserves
                    ),
                )
        reconcile(snapshot, repository)
        _reclassify_relations(repository)
    return tuple(reports)


def _relation_type_for_hint(relation_hint):
    if not relation_hint:
        return None
    if relation_hint.startswith(("crew-transfer:", "simplefin-transfer:", "owned:")):
        return "owned_transfer"
    if relation_hint.startswith(("splitwise-expense:", "lunchflow-shared:")):
        return "reimbursement"
    return None


def _reclassify_relations(repository) -> None:
    accounts = {account.id: account for account in repository.list_accounts()}
    user_rules = tuple(
        AssignmentRule(
            id=f"user:{rule.id}",
            category=rule.category,
            kind=rule.kind,
            merchant_pattern=rule.merchant_pattern,
            description_pattern=rule.description_pattern,
        )
        for rule in repository.list_assignment_rules()
    )
    for relation in repository.list_transaction_relations():
        for transaction_id in (
            relation.source_transaction_id,
            relation.related_transaction_id,
        ):
            transaction = repository.get_transaction(transaction_id)
            if transaction is None:
                continue
            account = accounts.get(transaction.account_id)
            if account is None:
                # An absent account keeps its row, so its historical
                # transactions can still be classified with the account context
                # they were recorded under; only currentness was withdrawn.
                account = repository.get_account(transaction.account_id)
            if account is None:
                continue
            classification = classify_deterministic(
                ClassificationInput(
                    id=transaction.id,
                    amount=transaction.amount,
                    description=transaction.description,
                    merchant=transaction.merchant,
                    account_type=account.account_type,
                    occurred_at=transaction.occurred_at,
                    relation_type=relation.relation_type,
                ),
                user_rules=user_rules,
            )
            repository.record_classification(transaction.id, classification)
