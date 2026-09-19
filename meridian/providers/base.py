"""Provider-neutral, credential-free snapshots used by Meridian syncs."""

from dataclasses import dataclass
from typing import Optional, Protocol, Tuple


@dataclass(frozen=True)
class NormalizedAccount:
    external_id: str
    name: str
    account_type: str
    balance: float
    currency: str = "USD"
    available_balance: Optional[float] = None
    is_active: bool = True
    source_updated_at: Optional[str] = None


@dataclass(frozen=True)
class NormalizedTransaction:
    external_id: str
    account_external_id: str
    amount: float
    occurred_at: str
    description: str
    status: str
    currency: str = "USD"
    posted_at: Optional[str] = None
    merchant: Optional[str] = None
    raw_description: Optional[str] = None
    source_updated_at: Optional[str] = None
    category: Optional[str] = None
    relation_hint: Optional[str] = None


@dataclass(frozen=True)
class ExpectedInflow:
    external_id: str
    name: str
    amount: float
    currency: str = "USD"
    source_updated_at: Optional[str] = None


@dataclass(frozen=True)
class CommitmentCandidate:
    external_id: str
    name: str
    amount: float
    currency: str = "USD"
    source_updated_at: Optional[str] = None
    due_date: Optional[str] = None
    recurrence: Optional[str] = None
    funded_amount: Optional[float] = None
    status: Optional[str] = None
    # The provider's own id of the bill reserve that contains this bill, as observed
    # when the bill was read. ``""`` means no membership was observed -- never
    # "belongs to no reserve" -- and the sync must not let an unobserved id overwrite
    # one that was observed. It is the join key to the funding plans the owner calls
    # their income source, and it keys on the provider's record id rather than on any
    # name the owner renames (D-010).
    bill_reserve_id: str = ""


@dataclass(frozen=True)
class FundingPlanCandidate:
    """A provider's paycheck funding plan, normalized and provider-neutral.

    The plan is the record the owner calls their "income source" / "Funding Cadence"
    (confirmed 2026-09-19). ``external_id`` is that record's identity, which is what
    lets a rename in the provider propagate here instead of the app keying on a
    deposit's merchant text.

    ``cadence`` is the plan's own schedule expressed in Meridian's vocabulary, or
    ``None`` when the provider's frequency/interval cannot be expressed exactly. It is
    never coerced to a nearby cadence: an interval Meridian cannot honour must stay
    unrecognised, exactly as the shared cadence rule refuses to default.
    """

    external_id: str
    name: str
    amount: float
    bill_reserve_id: str = ""
    cadence: Optional[str] = None
    anchor_date: Optional[str] = None
    currency: str = "USD"
    observed_at: Optional[str] = None


@dataclass(frozen=True)
class ProviderSnapshot:
    connection_external_id: str
    connection_name: str
    accounts: Tuple[NormalizedAccount, ...]
    transactions: Tuple[NormalizedTransaction, ...]
    expected_inflows: Tuple[ExpectedInflow, ...] = ()
    commitment_candidates: Tuple[CommitmentCandidate, ...] = ()
    # Tri-state on purpose: ``None`` means the provider read did not observe the
    # funding-plan surface at all, while ``()`` means it observed a genuinely empty
    # one. Absence reconciliation may only conclude from the second, so collapsing
    # them would let an unreadable read look like a deletion.
    funding_plans: Optional[Tuple[FundingPlanCandidate, ...]] = None
    is_complete: bool = True
    errors: Tuple[str, ...] = ()


class ProviderAdapter(Protocol):
    provider_name: str
    connection_external_id: str
    connection_name: str

    def fetch_snapshot(self) -> ProviderSnapshot:
        """Return a credential-free read-only source snapshot."""
