"""Live Crew snapshot collector for automatic refresh.

Provides a single ``sync_live_crew(db_path)`` callable that the
MeridianRefreshService invokes on its cadence. It shells out to the
CrewWorkAssistant ``crew-readonly snapshot`` CLI (the Keychain-backed
mobile/API auth that Crew supports) and syncs the normalized result into
the Meridian graph. Never logs or returns credential material.
"""

import ast
import subprocess
from typing import Optional

from .sync import SyncReport

# The CrewWorkAssistant connector ships with its own venv; this binary is the
# sanctioned read-only snapshot producer on this Mac.
CREW_READONLY = (
    "/Users/stephenwest/Applications/CrewWorkAssistantOTP/.venv/bin/crew-readonly"
)


def capture_crew_snapshot(binary: str = CREW_READONLY, timeout_seconds: int = 120) -> dict:
    """Run the crew-readonly snapshot CLI and parse its dashboard payload."""
    if not binary:
        # Importing here so the helper can be constructed without the binary.

        raise RuntimeError("crew-readonly binary path is not configured")
    try:
        result = subprocess.run(
            [binary, "snapshot"], capture_output=True, text=True, timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("crew-readonly snapshot timed out") from exc
    except OSError as exc:
        raise RuntimeError("crew-readonly binary is not available") from exc
    if result.returncode != 0:
        raise RuntimeError("crew-readonly snapshot failed")
    try:
        return ast.literal_eval(result.stdout)
    except (ValueError, SyntaxError) as exc:
        raise RuntimeError("crew-readonly returned an invalid snapshot") from exc


def sync_live_crew(db_path: str, *, snapshot: Optional[dict] = None, binary: str = CREW_READONLY) -> SyncReport:
    """Pull a live Crew snapshot (or accept one) and sync into ``db_path``."""
    from .commitments import (
        CommitmentRepository,
        CommitmentType,
        commitment_fields_from_candidate,
        commitment_update_fields,
        observation_of_candidate,
    )
    from .providers.crewwork import CrewWorkSnapshotAdapter
    from .repository import FinancialRepository
    from .sync import sync_provider

    dashboard = snapshot if snapshot is not None else capture_crew_snapshot(binary=binary)
    adapter = CrewWorkSnapshotAdapter(dashboard)
    repository = FinancialRepository(db_path)
    report = sync_provider(adapter, repository)
    # sync_provider (singular) persists accounts/transactions but not the
    # snapshot's commitment candidates; apply live bills so Plan shows real
    # money obligations (idempotent upsert keyed by Crew bill id). The mapping
    # itself lives in ``commitments`` (OS-053) so this path and ``sync_providers``
    # cannot drift apart again: both call the same two functions, and a newly
    # observed field is added in one place instead of two.
    snap = adapter.fetch_snapshot()
    commitment_repository = CommitmentRepository(repository.db_path)
    for candidate in snap.commitment_candidates:
        existing = commitment_repository.get_commitment_by_legacy(adapter.provider_name, candidate.external_id)
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
    # A complete, error-free read may conclude that a bill Crew no longer returns
    # is gone; the row and its history are kept.
    if snap.is_complete and not snap.errors:
        commitment_repository.mark_absent_bills(
            provider=adapter.provider_name,
            observed_external_ids=tuple(c.external_id for c in snap.commitment_candidates),
        )
    # Funding plans and reserve totals are the two stored facts the dial's funding
    # resolution reads (D-010/D-013), and they are the same two facts ``sync_providers``
    # already persisted -- but that function has no production caller (OS-053), so until
    # they are written here the app's own refresh stored neither: the funding source
    # could never resolve in production and no reserve total existed to divide. Both
    # writes are Meridian-local, additive and provider-read-only, and both follow the
    # same tri-state rule: ``None`` means the read did not observe the surface, which is
    # evidence of nothing, so absence may only be concluded from an observed read.
    if snap.funding_plans is not None:
        for plan in snap.funding_plans:
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
        if snap.is_complete and not snap.errors:
            repository.mark_absent_funding_plans(
                provider=adapter.provider_name,
                observed_external_ids=tuple(p.external_id for p in snap.funding_plans),
            )
    if snap.bill_reserves is not None:
        for reserve in snap.bill_reserves:
            repository.upsert_bill_reserve(
                provider=adapter.provider_name,
                external_id=reserve.external_id,
                total_reserved_amount=reserve.total_reserved_amount,
                currency=reserve.currency,
                observed_at=reserve.observed_at,
                # Crew's own reserve-level schedule (025): the next funding event it states,
                # and the reserve-level estimate, which D-015 resolved (2026-09-20) to be an
                # ACCOUNT-TOTAL snapshot rather than a reserve figure. Both stay None when
                # unreported, and neither is used as a dividend.
                estimated_next_funding_amount=reserve.estimated_next_funding_amount,
                next_funding_date=reserve.next_funding_date,
            )
        if snap.is_complete and not snap.errors:
            repository.mark_absent_bill_reserves(
                provider=adapter.provider_name,
                observed_external_ids=tuple(r.external_id for r in snap.bill_reserves),
            )
    return report


def build_sync_once(db_path: str, *, binary: str = CREW_READONLY):
    """Zero-arg callable for MeridianRefreshService tied to ``db_path``."""
    def sync_once() -> SyncReport:
        return sync_live_crew(db_path, binary=binary)
    return sync_once
