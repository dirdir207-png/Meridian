"""Idempotent synchronization of provider snapshots into Meridian."""

from dataclasses import dataclass

from .ai.classifier import classify_with_ai_fallback
from .classify import AssignmentRule, ClassificationInput, classify_deterministic
from .commitments import CommitmentRepository, CommitmentType
from .providers.base import ProviderAdapter
from .reconcile import reconcile


@dataclass(frozen=True)
class SyncReport:
    provider: str
    status: str
    accounts_synced: int
    transactions_synced: int
    errors: int


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
        for candidate in snapshot.commitment_candidates:
            existing = commitment_repository.get_commitment_by_legacy(
                adapter.provider_name, candidate.external_id
            )
            if existing is None:
                commitment_repository.create(
                    type=CommitmentType.BILL,
                    name=candidate.name,
                    amount=candidate.amount,
                    currency=candidate.currency,
                    recurrence=candidate.recurrence or "one_time",
                    due_date=candidate.due_date,
                    target_amount=candidate.amount,
                    funded_amount=(candidate.funded_amount if candidate.funded_amount is not None else 0.0),
                    legacy_source=adapter.provider_name,
                    legacy_id=candidate.external_id,
                    bill_reserve_id=candidate.bill_reserve_id,
                    # Only a reported reserveAmount sets this (C01/024): a silent read
                    # stores 0.0 and must not read as "Crew said the reserve is empty".
                    reserved_amount_reported=candidate.funded_amount is not None,
                    # Crew's own per-event estimate and deadline (025), NULL when the read
                    # did not report them: a missing figure is not a zero.
                    estimated_next_funding_amount=candidate.estimated_next_funding_amount,
                    reserved_by=candidate.reserved_by,
                )
            else:
                commitment_repository.update(
                    existing.id,
                    name=candidate.name,
                    amount=candidate.amount,
                    currency=candidate.currency,
                    due_date=candidate.due_date or existing.due_date,
                    recurrence=candidate.recurrence or existing.recurrence,
                    funded_amount=(
                        candidate.funded_amount
                        if candidate.funded_amount is not None
                        else existing.funded_amount
                    ),
                    # An unobserved reserve id ("" from the adapter) is not evidence
                    # that the bill left its reserve, so it never overwrites an
                    # observed membership. A different observed id does replace it,
                    # which is how a bill moved between reserves is picked up.
                    bill_reserve_id=candidate.bill_reserve_id or existing.bill_reserve_id,
                    # Symmetric with the membership: a read that did not report the
                    # amount is not a report of nothing, so the flag it already had
                    # stands rather than being cleared.
                    reserved_amount_reported=(
                        True
                        if candidate.funded_amount is not None
                        else existing.reserved_amount_reported
                    ),
                    # C01 for the reported schedule (025): an unreported figure keeps the
                    # stored value rather than clearing it.
                    estimated_next_funding_amount=(
                        candidate.estimated_next_funding_amount
                        if candidate.estimated_next_funding_amount is not None
                        else existing.estimated_next_funding_amount
                    ),
                    reserved_by=(
                        candidate.reserved_by
                        if candidate.reserved_by is not None
                        else existing.reserved_by
                    ),
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
