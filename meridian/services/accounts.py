"""Provider-neutral Accounts workspace read model."""

from meridian.repository import FinancialRepository
from meridian.services.today import data_freshness

_ROLE_ORDER = (
    "cash",
    "savings",
    "investments",
    "liabilities",
    "reimbursements",
    "other",
)
_ROLE_LABELS = {
    "cash": "Cash",
    "savings": "Savings",
    "investments": "Investments",
    "liabilities": "Cards & liabilities",
    "reimbursements": "Reimbursements",
    "other": "Other",
}


def _role(account_type: str) -> str:
    normalized = account_type.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"checking", "cash", "depository", "wallet"}:
        return "cash"
    if normalized in {"savings", "money_market", "reserve"}:
        return "savings"
    if normalized in {"investment", "brokerage", "retirement", "asset"}:
        return "investments"
    if normalized in {"credit", "credit_card", "loan", "mortgage", "liability"}:
        return "liabilities"
    if normalized in {"reimbursement", "receivable"}:
        return "reimbursements"
    return "other"


def _account_view(account) -> dict[str, object]:
    return {
        "id": account.id,
        "name": account.name,
        "account_type": account.account_type,
        "balance": account.balance,
        "available_balance": account.available_balance,
        "currency": account.currency,
        "is_active": account.is_active,
        "provider": account.provider,
        "source_updated_at": account.source_updated_at,
        "synced_at": account.synced_at,
    }


def build_accounts(
    repository: FinancialRepository, *, archived_limit: int = 50
) -> dict[str, object]:
    accounts = repository.list_accounts()
    grouped = {role: [] for role in _ROLE_ORDER}
    for account in accounts:
        grouped[_role(account.account_type)].append(_account_view(account))

    connections = []
    for connection in repository.list_connection_freshness():
        status = "healthy" if connection.status == "complete" else connection.status
        connections.append(
            {
                "provider": connection.provider,
                "status": status,
                "last_successful_at": connection.last_successful_at,
                "source_updated_at": [
                    value for value in connection.source_updated_at if value
                ],
            }
        )

    reimbursements = [
        {
            "id": item.id,
            "name": item.name,
            "amount": item.amount,
            "currency": item.currency,
            "provider": item.provider,
            "source_updated_at": item.source_updated_at,
        }
        for item in repository.list_reimbursements()
    ]
    # Accounts a complete read concluded are gone keep their rows and their
    # history. They are reported here with provenance instead of vanishing, and
    # never as a current balance.
    archived = [
        {
            "id": item.account.id,
            "name": item.account.name,
            "provider": item.account.provider,
            "account_type": item.account.account_type,
            "absent_since": item.account.absent_since,
            "last_observed_at": item.account.source_updated_at,
            "retained_transactions": item.retained_transaction_count,
        }
        for item in repository.list_archived_accounts(limit=archived_limit)
    ]

    return {
        "groups": [
            {"role": role, "label": _ROLE_LABELS[role], "accounts": grouped[role]}
            for role in _ROLE_ORDER
            if grouped[role]
        ],
        "archived": archived,
        "reimbursements": reimbursements,
        "connections": connections,
        "data_freshness": data_freshness(
            repository,
            account_ids=[account.id for account in accounts],
            include_all_connections=True,
        ),
    }
