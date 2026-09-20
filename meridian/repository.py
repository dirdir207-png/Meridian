"""Provider-neutral writes and stable reads for Meridian financial records."""

import base64
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence

from .category_catalog import CATEGORIES as _DEFAULT_CATEGORIES
from .db import run_migrations
from .models import AccountRecord, ArchivedAccountRecord, TransactionRecord
from .timestamps import canonical_occurred_at


@dataclass(frozen=True)
class SyncRun:
    id: int
    connection_id: int


@dataclass(frozen=True)
class ProviderConnectionFreshness:
    """The complete-sync state and source timestamps behind a read model."""

    connection_id: int
    provider: str
    status: str
    last_successful_at: Optional[str]
    source_updated_at: tuple[Optional[str], ...]


@dataclass(frozen=True)
class ProviderFreshnessScope:
    """Credential-free provider state and linkage completeness for one read."""

    connections: tuple[ProviderConnectionFreshness, ...]
    has_unlinked_records: bool


@dataclass(frozen=True)
class TransactionRelationRecord:
    id: int
    provider: str
    external_id: str
    source_transaction_id: int
    related_transaction_id: int
    relation_type: str
    confidence: Optional[float]


@dataclass(frozen=True)
class StoredAssignmentRule:
    id: int
    category: str
    kind: str
    merchant_pattern: Optional[str]
    description_pattern: Optional[str]


@dataclass(frozen=True)
class FundingPlanRecord:
    """A Crew bill-reserve funding plan: the owner's income source / Funding Cadence.

    ``external_id`` is Crew's own plan id and is the identity of the record — the owner
    renames the plan ("State of New Hampshire" -> "Veteran's Home"), so anything keyed on
    the plan's *name* or on a deposit's merchant text would break on the next rename.

    ``cadence`` is ``None`` when Crew's frequency/interval has no exact Meridian
    equivalent. ``observed_at`` is the provider read that observed the plan; ``absent_since``
    records that a later complete read no longer returned it, so the row documents a
    withdrawal without being deleted.
    """

    id: int
    provider: str
    external_id: str
    bill_reserve_id: str
    name: str
    amount: float
    cadence: Optional[str]
    anchor_date: Optional[str]
    currency: str
    observed_at: Optional[str]
    synced_at: str
    absent_since: Optional[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class BillReserveRecord:
    """One Crew bill reserve's observed state: the bucket the bills sit in.

    ``external_id`` is Crew's own reserve id -- the same value the ingested bill carries
    as ``commitments.bill_reserve_id``, which is the whole join. The owner renames
    reserves in Crew, so nothing may key on the name.

    ``total_reserved_amount`` is the reserve's total set-aside funds in dollars, or
    ``None`` when Crew did not report it. It is the dividend D-013's even-split fallback
    divides across the reserve's bills; ``None`` means "not reported", never "empty".
    """

    id: int
    provider: str
    external_id: str
    total_reserved_amount: Optional[float]
    currency: str
    observed_at: Optional[str]
    synced_at: str
    absent_since: Optional[str]
    created_at: str
    updated_at: str
    # Crew's own reserve-level ``estimatedNextFundingAmount`` (025), or ``None`` when this
    # read did not report it. RESOLVED 2026-09-20 (D-015): an ACCOUNT-TOTAL snapshot, not a
    # reserve figure -- it is the reserve plus the spendable subaccounts, and it lags the live
    # total. Kept out of every arithmetic path: ``total_reserved_amount`` is observed and must
    # never be derived from it. Stored because it is an observation with provenance, and
    # because the 2026-10-02 event will show when it refreshes.
    estimated_next_funding_amount: Optional[float] = None
    # Crew's own ``nextFundingDate`` (025): the plan's next funding event, stored verbatim so
    # a malformed value stays visible as malformed rather than becoming silence.
    next_funding_date: Optional[str] = None


@dataclass(frozen=True)
class ReimbursementRecord:
    id: int
    provider: str
    external_id: str
    name: str
    amount: float
    currency: str
    source_updated_at: Optional[str]
    synced_at: str
    created_at: str
    updated_at: str


_COMPATIBLE_CURSOR_OCCURRED_AT = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


_ACCOUNT_COLUMNS = (
    "id, provider, external_id, name, account_type, balance, currency, "
    "available_balance, is_active, source_updated_at, synced_at, created_at, "
    "updated_at, absent_since"
)
_TRANSACTION_COLUMNS = (
    "id, provider, external_id, account_id, amount, currency, occurred_at, "
    "posted_at, description, merchant, status, raw_description, "
    "source_updated_at, classification_category, classification_kind, "
    "classification_confidence, classification_rule_id, classification_evidence, "
    "classification_method, classification_provider, classification_model, "
    "classification_version, synced_at, created_at, updated_at"
)


def _available_transaction_columns(connection: sqlite3.Connection) -> str:
    available = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(financial_transactions)")
    }
    return ", ".join(
        name.strip()
        for name in _TRANSACTION_COLUMNS.split(",")
        if name.strip() in available
    )


def _available_account_columns(connection: sqlite3.Connection) -> str:
    """The account columns this database actually has.

    A reader can meet a database another process has not finished migrating, so
    a column added by a later migration is selected only when it exists;
    ``AccountRecord`` defaults the ones that are missing.
    """
    available = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(financial_accounts)")
    }
    return ", ".join(
        name.strip() for name in _ACCOUNT_COLUMNS.split(",") if name.strip() in available
    )


def _reconciles_absence(connection: sqlite3.Connection) -> bool:
    """Whether this database can record account absence yet (migration 020)."""
    return any(
        row["name"] == "absent_since"
        for row in connection.execute("PRAGMA table_info(financial_accounts)")
    )


_ACCOUNT_FRESHNESS_CONDITION = """
    financial_accounts.source_updated_at IS NULL
    OR (
        excluded.source_updated_at IS NOT NULL
        AND excluded.source_updated_at > financial_accounts.source_updated_at
    )
"""
_TRANSACTION_FRESHNESS_CONDITION = """
    financial_transactions.source_updated_at IS NULL
    OR (
        excluded.source_updated_at IS NOT NULL
        AND excluded.source_updated_at > financial_transactions.source_updated_at
    )
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _encode_cursor(occurred_at: str, record_id: int) -> str:
    payload = json.dumps([occurred_at, record_id], separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[str, int]:
    try:
        encoded = cursor.encode("ascii")
        payload = base64.b64decode(encoded, altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(payload) != encoded:
            raise ValueError
        occurred_at, record_id = json.loads(payload.decode("utf-8"))
        if (
            not isinstance(occurred_at, str)
            or type(record_id) is not int
            or record_id < 1
            or _COMPATIBLE_CURSOR_OCCURRED_AT.fullmatch(occurred_at) is None
        ):
            raise ValueError
        canonical_occurred_at_value = canonical_occurred_at(occurred_at)
        canonical_payload = json.dumps(
            [occurred_at, record_id], separators=(",", ":")
        ).encode("utf-8")
        if payload != canonical_payload:
            raise ValueError
    except (UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid transaction cursor") from exc
    return canonical_occurred_at_value, record_id


class FinancialRepository:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self.db_path = db_path
        run_migrations(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def upsert_account(
        self,
        *,
        provider: str,
        external_id: str,
        name: str,
        account_type: str,
        balance: float,
        currency: str = "USD",
        available_balance: Optional[float] = None,
        is_active: bool = True,
        connection_id: Optional[int] = None,
        source_updated_at: Optional[str] = None,
        synced_at: Optional[str] = None,
    ) -> AccountRecord:
        timestamp = synced_at or _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            absence_reset = (
                """
                    -- A returned account is present again: absence evidence from a
                    -- previous complete read cannot outlive the observation that
                    -- contradicts it.
                    absent_since = NULL,"""
                if _reconciles_absence(connection)
                else ""
            )
            connection.execute(
                f"""
                INSERT INTO financial_accounts (
                    provider, external_id, name, account_type, balance,
                    connection_id, available_balance, currency, is_active, source_updated_at,
                    synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    connection_id = COALESCE(excluded.connection_id, financial_accounts.connection_id),
                    name = CASE WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.name ELSE financial_accounts.name END,
                    account_type = CASE WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.account_type ELSE financial_accounts.account_type END,
                    balance = CASE WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.balance ELSE financial_accounts.balance END,
                    available_balance = CASE WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.available_balance
                        ELSE financial_accounts.available_balance END,
                    currency = CASE WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.currency ELSE financial_accounts.currency END,{absence_reset}
                    is_active = CASE WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.is_active ELSE financial_accounts.is_active END,
                    source_updated_at = CASE
                        WHEN excluded.source_updated_at IS NOT NULL
                            AND {_ACCOUNT_FRESHNESS_CONDITION}
                        THEN excluded.source_updated_at
                        ELSE financial_accounts.source_updated_at
                    END,
                    synced_at = CASE WHEN excluded.synced_at > financial_accounts.synced_at
                        THEN excluded.synced_at ELSE financial_accounts.synced_at END,
                    updated_at = CASE
                        WHEN {_ACCOUNT_FRESHNESS_CONDITION}
                            OR excluded.synced_at > financial_accounts.synced_at
                        THEN excluded.updated_at
                        ELSE financial_accounts.updated_at
                    END
                """,
                (
                    provider,
                    external_id,
                    name,
                    account_type,
                    balance,
                    connection_id,
                    available_balance,
                    currency,
                    int(is_active),
                    source_updated_at,
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
            row = connection.execute(
                f"SELECT {_available_account_columns(connection)} FROM financial_accounts "
                "WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        assert row is not None
        return self._account_from_row(row)

    def mark_absent_accounts(
        self,
        *,
        provider: str,
        connection_id: int,
        observed_external_ids: Sequence[str],
        absent_since: Optional[str] = None,
    ) -> int:
        """Record that a complete provider read no longer returns these accounts.

        Absence is evidence about the local read model only: the row keeps its
        history and is never deleted, it simply stops being a current
        observation. Rows already concluded absent are left untouched, so one
        observation cannot masquerade as a repeatedly refreshed fact, and the
        scope is the provider's own connection, so another provider's accounts
        are never archived by this read.
        """
        timestamp = absent_since or _now()
        observed = tuple(observed_external_ids)
        unobserved_condition = ""
        parameters: tuple[object, ...] = (timestamp, timestamp, provider, connection_id)
        if observed:
            placeholders = ", ".join("?" for _ in observed)
            unobserved_condition = f" AND external_id NOT IN ({placeholders})"
            parameters += observed
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                f"""
                UPDATE financial_accounts
                SET is_active = 0, absent_since = ?, updated_at = ?
                WHERE provider = ? AND connection_id = ?
                    AND absent_since IS NULL
                    {unobserved_condition}
                """,
                parameters,
            )
            return cursor.rowcount

    def upsert_transaction(
        self,
        *,
        provider: str,
        external_id: str,
        account_id: int,
        amount: float,
        occurred_at: str,
        description: str,
        status: str,
        currency: str = "USD",
        posted_at: Optional[str] = None,
        merchant: Optional[str] = None,
        raw_description: Optional[str] = None,
        source_updated_at: Optional[str] = None,
        synced_at: Optional[str] = None,
    ) -> TransactionRecord:
        occurred_at = canonical_occurred_at(occurred_at)
        timestamp = synced_at or _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            matching_account = connection.execute(
                "SELECT 1 FROM financial_accounts WHERE id = ? AND provider = ?",
                (account_id, provider),
            ).fetchone()
            if matching_account is None:
                raise ValueError("Transaction provider must match account provider")
            connection.execute(
                f"""
                INSERT INTO financial_transactions (
                    provider, external_id, account_id, amount, currency,
                    occurred_at, posted_at, description, merchant, status,
                    raw_description, source_updated_at, synced_at, created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    account_id = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.account_id ELSE financial_transactions.account_id END,
                    amount = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.amount ELSE financial_transactions.amount END,
                    currency = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.currency ELSE financial_transactions.currency END,
                    occurred_at = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.occurred_at ELSE financial_transactions.occurred_at END,
                    occurred_at_valid = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN 1 ELSE financial_transactions.occurred_at_valid END,
                    posted_at = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.posted_at ELSE financial_transactions.posted_at END,
                    description = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.description ELSE financial_transactions.description END,
                    merchant = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.merchant ELSE financial_transactions.merchant END,
                    status = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.status ELSE financial_transactions.status END,
                    raw_description = CASE WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.raw_description
                        ELSE financial_transactions.raw_description END,
                    source_updated_at = CASE
                        WHEN excluded.source_updated_at IS NOT NULL
                            AND {_TRANSACTION_FRESHNESS_CONDITION}
                        THEN excluded.source_updated_at
                        ELSE financial_transactions.source_updated_at
                    END,
                    synced_at = CASE
                        WHEN excluded.synced_at > financial_transactions.synced_at
                        THEN excluded.synced_at ELSE financial_transactions.synced_at
                    END,
                    updated_at = CASE
                        WHEN {_TRANSACTION_FRESHNESS_CONDITION}
                            OR excluded.synced_at > financial_transactions.synced_at
                        THEN excluded.updated_at
                        ELSE financial_transactions.updated_at
                    END
                """,
                (
                    provider,
                    external_id,
                    account_id,
                    amount,
                    currency,
                    occurred_at,
                    posted_at,
                    description,
                    merchant,
                    status,
                    raw_description,
                    source_updated_at,
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
            row = connection.execute(
                f"SELECT {_available_transaction_columns(connection)} FROM financial_transactions "
                "WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        assert row is not None
        return self._transaction_from_row(row)

    def begin_sync_run(
        self,
        *,
        provider: str,
        connection_external_id: str,
        connection_name: str,
    ) -> SyncRun:
        """Record an attempted provider read without advancing freshness."""
        timestamp = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO provider_connections (
                    provider, external_id, display_name, status, last_attempted_at
                ) VALUES (?, ?, ?, 'syncing', ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    status = 'syncing',
                    last_attempted_at = excluded.last_attempted_at,
                    updated_at = excluded.last_attempted_at
                """,
                (provider, connection_external_id, connection_name, timestamp),
            )
            connection_row = connection.execute(
                "SELECT id FROM provider_connections WHERE provider = ? AND external_id = ?",
                (provider, connection_external_id),
            ).fetchone()
            assert connection_row is not None
            cursor = connection.execute(
                """
                INSERT INTO provider_sync_runs (connection_id, provider, status, started_at)
                VALUES (?, ?, 'running', ?)
                """,
                (connection_row["id"], provider, timestamp),
            )
        return SyncRun(id=int(cursor.lastrowid), connection_id=int(connection_row["id"]))

    def finish_sync_run(
        self,
        run_id: int,
        *,
        status: str,
        accounts_synced: int,
        transactions_synced: int,
        errors: int,
    ) -> None:
        """Finalize a run and advance connection freshness only when complete."""
        if status not in {"complete", "partial", "failed"}:
            raise ValueError("Invalid sync status")
        timestamp = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute(
                "SELECT connection_id FROM provider_sync_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
            if run is None:
                raise ValueError("Unknown sync run")
            connection.execute(
                """
                UPDATE provider_sync_runs
                SET status = ?, completed_at = ?, accounts_synced = ?,
                    transactions_synced = ?, errors = ?
                WHERE id = ?
                """,
                (status, timestamp, accounts_synced, transactions_synced, errors, run_id),
            )
            if status == "complete":
                connection.execute(
                    """
                    UPDATE provider_connections
                    SET status = 'healthy', last_successful_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (timestamp, timestamp, run["connection_id"]),
                )
            else:
                connection.execute(
                    "UPDATE provider_connections SET status = ?, updated_at = ? WHERE id = ?",
                    (status, timestamp, run["connection_id"]),
                )

    def upsert_transaction_relation(
        self,
        *,
        provider: str,
        external_id: str,
        source_transaction_id: int,
        related_transaction_id: int,
        relation_type: str,
        confidence: Optional[float] = None,
    ) -> int:
        timestamp = _now()
        with self._connect() as connection:
            existed = connection.execute(
                "SELECT 1 FROM transaction_relations WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone() is not None
            connection.execute(
                """
                INSERT INTO transaction_relations (
                    provider, external_id, source_transaction_id,
                    related_transaction_id, relation_type, confidence,
                    synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    source_transaction_id = excluded.source_transaction_id,
                    related_transaction_id = excluded.related_transaction_id,
                    relation_type = excluded.relation_type,
                    confidence = excluded.confidence,
                    synced_at = excluded.synced_at,
                    updated_at = excluded.updated_at
                """,
                (
                    provider,
                    external_id,
                    source_transaction_id,
                    related_transaction_id,
                    relation_type,
                    confidence,
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
        return 0 if existed else 1

    def list_transaction_relations(self) -> list[TransactionRelationRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, provider, external_id, source_transaction_id,
                       related_transaction_id, relation_type, confidence
                FROM transaction_relations ORDER BY id
                """
            ).fetchall()
        return [TransactionRelationRecord(**dict(row)) for row in rows]

    def record_classification(self, transaction_id: int, classification) -> None:
        timestamp = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                """
                SELECT classification_category, classification_kind,
                       classification_confidence, classification_rule_id,
                       classification_evidence, classification_method,
                       classification_provider, classification_model,
                       classification_version
                FROM financial_transactions WHERE id = ?
                """,
                (transaction_id,),
            ).fetchone()
            if current is None:
                raise ValueError("transaction not found")
            current_values = (
                current["classification_category"],
                current["classification_kind"],
                current["classification_confidence"],
                current["classification_rule_id"],
                current["classification_evidence"],
                current["classification_method"],
                current["classification_provider"],
                current["classification_model"],
            )
            incoming_values = (
                classification.category,
                classification.kind,
                classification.confidence,
                classification.rule_id,
                classification.evidence,
                classification.method,
                getattr(classification, "provider", None),
                getattr(classification, "model", None),
            )
            # Explicit per-transaction corrections are written by correct_classification.
            # Automated sync/AI/rule refresh must never undo that owner decision.
            if current["classification_evidence"] == "owner correction":
                return
            if current_values == incoming_values:
                return
            if current["classification_category"] is not None:
                connection.execute(
                    """
                    INSERT INTO transaction_classification_history (
                        transaction_id, category, kind, confidence, rule_id,
                        evidence, method, version, replaced_at
                        , provider, model
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transaction_id,
                        current["classification_category"],
                        current["classification_kind"],
                        current["classification_confidence"],
                        current["classification_rule_id"],
                        current["classification_evidence"],
                        current["classification_method"],
                        current["classification_version"],
                        timestamp,
                        current["classification_provider"],
                        current["classification_model"],
                    ),
                )
            version = int(current["classification_version"] or 0) + 1
            connection.execute(
                """
                UPDATE financial_transactions
                SET classification_category = ?, classification_kind = ?,
                    classification_confidence = ?, classification_rule_id = ?,
                    classification_evidence = ?, classification_method = ?,
                    classification_provider = ?, classification_model = ?,
                    classification_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    classification.category,
                    classification.kind,
                    classification.confidence,
                    classification.rule_id,
                    classification.evidence,
                    classification.method,
                    getattr(classification, "provider", None),
                    getattr(classification, "model", None),
                    version,
                    timestamp,
                    transaction_id,
                ),
            )

    def list_classification_history(self, transaction_id: int) -> list[sqlite3.Row]:
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT category, kind, confidence, rule_id, evidence, method,
                       provider, model, version, replaced_at
                FROM transaction_classification_history
                WHERE transaction_id = ? ORDER BY id
                """,
                (transaction_id,),
            ).fetchall()

    def correct_classification(
        self,
        transaction_id: int,
        *,
        category: str,
        kind: str,
        create_rule: bool = False,
    ) -> TransactionRecord:
        if not isinstance(category, str) or not category.strip():
            raise ValueError("category is required")
        if kind not in {"income", "spend", "transfer", "refund", "fee", "reimbursement"}:
            raise ValueError("kind is invalid")
        timestamp = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            transaction = connection.execute(
                f"SELECT {_TRANSACTION_COLUMNS} FROM financial_transactions WHERE id = ?",
                (transaction_id,),
            ).fetchone()
            if transaction is None:
                raise ValueError("transaction not found")
            rule_id = None
            if create_rule:
                merchant_pattern = (
                    transaction["merchant"].strip().casefold()
                    if transaction["merchant"]
                    else None
                )
                description_pattern = (
                    None if merchant_pattern else transaction["description"].strip().casefold()
                )
                cursor = connection.execute(
                    """
                    INSERT INTO assignment_rules (
                        category, kind, merchant_pattern, description_pattern,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (category.strip(), kind, merchant_pattern, description_pattern, timestamp, timestamp),
                )
                rule_id = int(cursor.lastrowid)
            targets = [transaction]
            if rule_id is not None:
                if transaction["merchant"]:
                    targets = connection.execute(
                        f"SELECT {_TRANSACTION_COLUMNS} FROM financial_transactions "
                        "WHERE lower(merchant) = lower(?) AND classification_confidence < 0.7",
                        (transaction["merchant"],),
                    ).fetchall()
                if all(target["id"] != transaction_id for target in targets):
                    targets = [*targets, transaction]
                else:
                    targets = connection.execute(
                        f"SELECT {_TRANSACTION_COLUMNS} FROM financial_transactions "
                        "WHERE lower(description) = lower(?) AND classification_confidence < 0.7",
                        (transaction["description"],),
                    ).fetchall()
            audit_rule_id = f"user:{rule_id}" if rule_id is not None else "user:correction"
            for target in targets:
                if target["classification_category"] is not None:
                    connection.execute(
                        """
                        INSERT INTO transaction_classification_history (
                            transaction_id, category, kind, confidence, rule_id,
                            evidence, method, version, replaced_at, provider, model
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            target["id"],
                            target["classification_category"],
                            target["classification_kind"],
                            target["classification_confidence"],
                            target["classification_rule_id"],
                            target["classification_evidence"],
                            target["classification_method"],
                            target["classification_version"],
                            timestamp,
                            target["classification_provider"],
                            target["classification_model"],
                        ),
                    )
                connection.execute(
                    """
                    UPDATE financial_transactions
                    SET classification_category = ?, classification_kind = ?,
                        classification_confidence = 1.0,
                        classification_rule_id = ?,
                        classification_evidence = ?, classification_method = 'user_rule',
                        classification_provider = NULL, classification_model = NULL,
                        classification_version = classification_version + 1,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        category.strip(),
                        kind,
                        audit_rule_id,
                        "owner correction",
                        timestamp,
                        target["id"],
                    ),
                )
            connection.execute(
                """
                INSERT INTO classification_corrections (
                    transaction_id, category, kind, assignment_rule_id, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (transaction_id, category.strip(), kind, rule_id, timestamp),
            )
        result = self.get_transaction(transaction_id)
        assert result is not None
        return result

    def suggest_category(self, *, merchant: str | None, description: str | None = None) -> str | None:
        """Smart category guess for a merchant, drawn from the data.

        Prefers the most-frequent category already assigned to the same merchant
        (a real signal of how the owner categorises it), then an assignment rule
        that matches the merchant/description, then a "smart" keyword map. Returns
        None when nothing looks confident, so the editor stays a free-typed field.
        """
        from collections import Counter

        if not merchant and not description:
            return None
        merchant_key = (merchant or "").strip().casefold()
        lower_merchant = merchant_key or None
        with self._connect() as connection:
            # 1) Most-common category across this merchant's classified rows.
            if lower_merchant:
                rows = connection.execute(
                    "SELECT classification_category FROM financial_transactions "
                    "WHERE lower(merchant) = ? AND classification_category IS NOT NULL "
                    "AND classification_category != '' AND lower(classification_category) != 'uncategorized' "
                    "ORDER BY classification_confidence DESC, updated_at DESC",
                    (lower_merchant,),
                ).fetchall()
                counts = Counter(r["classification_category"] for r in rows)
                if counts:
                    return counts.most_common(1)[0][0]
            # 2) Assignment rule match (merchant or description pattern).
            description_key = (description or "").strip().casefold() or None
            for rule in self.list_assignment_rules():
                pat = (rule.merchant_pattern or rule.description_pattern or "").strip().casefold()
                if pat and ((lower_merchant and pat == lower_merchant) or (description_key and pat == description_key)):
                    return rule.category
        # 3) Keyword heuristic for recognizable merchants.
        return _keyword_category_guess(merchant or description or "")

    def category_options(self, *, merchant: str | None, description: str | None = None, limit: int = 10) -> list[str]:
        """Ranked category options for a merchant's editor dropdown.

        The suggested category is first (the smart guess), then the merchant's
        historically-assigned categories (by frequency), then the standard pool.
        The UI still lets the owner type anything — this only orders suggestions.
        """
        from collections import Counter

        suggestion = self.suggest_category(merchant=merchant, description=description)
        ordered: list[str] = []
        if suggestion:
            ordered.append(suggestion)
        lower_merchant = (merchant or "").strip().casefold() or None
        if lower_merchant:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT classification_category FROM financial_transactions "
                    "WHERE lower(merchant) = ? AND classification_category IS NOT NULL "
                    "AND classification_category != '' AND lower(classification_category) != 'uncategorized'",
                    (lower_merchant,),
                ).fetchall()
            for category, _count in Counter(r["classification_category"] for r in rows).most_common():
                if category not in ordered:
                    ordered.append(category)
        for category in _DEFAULT_CATEGORIES:
            if category not in ordered:
                ordered.append(category)
        return ordered[:limit]

    def list_assignment_rules(self) -> list[StoredAssignmentRule]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, category, kind, merchant_pattern, description_pattern
                FROM assignment_rules ORDER BY id
                """
            ).fetchall()
        return [StoredAssignmentRule(**dict(row)) for row in rows]

    def upsert_reimbursement(
        self,
        *,
        provider: str,
        external_id: str,
        name: str,
        amount: float,
        currency: str,
        source_updated_at: Optional[str] = None,
    ) -> ReimbursementRecord:
        timestamp = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO provider_reimbursements (
                    provider, external_id, name, amount, currency,
                    source_updated_at, synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    name = CASE WHEN provider_reimbursements.source_updated_at IS NULL
                        OR (excluded.source_updated_at IS NOT NULL AND excluded.source_updated_at >= provider_reimbursements.source_updated_at)
                        THEN excluded.name ELSE provider_reimbursements.name END,
                    amount = CASE WHEN provider_reimbursements.source_updated_at IS NULL
                        OR (excluded.source_updated_at IS NOT NULL AND excluded.source_updated_at >= provider_reimbursements.source_updated_at)
                        THEN excluded.amount ELSE provider_reimbursements.amount END,
                    currency = CASE WHEN provider_reimbursements.source_updated_at IS NULL
                        OR (excluded.source_updated_at IS NOT NULL AND excluded.source_updated_at >= provider_reimbursements.source_updated_at)
                        THEN excluded.currency ELSE provider_reimbursements.currency END,
                    source_updated_at = CASE WHEN provider_reimbursements.source_updated_at IS NULL
                        OR (excluded.source_updated_at IS NOT NULL AND excluded.source_updated_at >= provider_reimbursements.source_updated_at)
                        THEN excluded.source_updated_at ELSE provider_reimbursements.source_updated_at END,
                    synced_at = excluded.synced_at,
                    updated_at = excluded.updated_at
                """,
                (
                    provider,
                    external_id,
                    name,
                    amount,
                    currency,
                    source_updated_at,
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
            row = connection.execute(
                "SELECT * FROM provider_reimbursements WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        assert row is not None
        return ReimbursementRecord(**dict(row))

    def list_reimbursements(self) -> list[ReimbursementRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM provider_reimbursements ORDER BY name COLLATE NOCASE, id"
            ).fetchall()
        return [ReimbursementRecord(**dict(row)) for row in rows]

    def upsert_funding_plan(
        self,
        *,
        provider: str,
        external_id: str,
        bill_reserve_id: str,
        name: str,
        amount: float,
        cadence: Optional[str] = None,
        anchor_date: Optional[str] = None,
        currency: str = "USD",
        observed_at: Optional[str] = None,
    ) -> FundingPlanRecord:
        """Store the Crew funding plan this provider read observed.

        Keyed on Crew's own plan id, so a rename updates the record the app already
        cites instead of creating a second one. Re-observing a plan that a previous
        complete read retired clears ``absent_since``: the row was kept precisely so a
        re-created cadence stays the same record rather than orphaning its history.
        """
        timestamp = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO crew_funding_plans (
                    provider, external_id, bill_reserve_id, name, amount, cadence,
                    anchor_date, currency, observed_at, synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    bill_reserve_id = excluded.bill_reserve_id,
                    name = excluded.name,
                    amount = excluded.amount,
                    cadence = excluded.cadence,
                    anchor_date = excluded.anchor_date,
                    currency = excluded.currency,
                    observed_at = excluded.observed_at,
                    synced_at = excluded.synced_at,
                    absent_since = NULL,
                    updated_at = excluded.updated_at
                """,
                (
                    provider,
                    external_id,
                    bill_reserve_id,
                    name,
                    amount,
                    cadence,
                    anchor_date,
                    currency,
                    observed_at,
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
            row = connection.execute(
                "SELECT * FROM crew_funding_plans WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        assert row is not None
        return FundingPlanRecord(**dict(row))

    def list_funding_plans(self) -> list[FundingPlanRecord]:
        """The funding plans currently observed, newest observed first.

        Retired plans are excluded rather than deleted: resolution must not treat a
        withdrawn cadence as an income source, while the row still documents that the
        plan existed and when it stopped being returned.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM crew_funding_plans
                WHERE absent_since IS NULL
                ORDER BY observed_at DESC, id DESC
                """
            ).fetchall()
        return [FundingPlanRecord(**dict(row)) for row in rows]

    def get_funding_plan(self, provider: str, external_id: str) -> Optional[FundingPlanRecord]:
        """One stored plan whether current or retired, or None."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM crew_funding_plans WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        return FundingPlanRecord(**dict(row)) if row is not None else None

    def mark_absent_funding_plans(
        self,
        *,
        provider: str,
        observed_external_ids: Sequence[str],
        absent_since: Optional[str] = None,
    ) -> int:
        """Record that a complete read no longer returns these funding plans.

        Same discipline as the account and bill absence rules: only a complete,
        error-free read may reach here (the caller enforces that), the row is never
        deleted, and a plan already concluded absent is left untouched so one
        observation cannot masquerade as a repeatedly refreshed fact.
        """
        timestamp = absent_since or _now()
        observed = tuple(observed_external_ids)
        unobserved_condition = ""
        parameters: tuple[object, ...] = (timestamp, timestamp, provider)
        if observed:
            placeholders = ", ".join("?" for _ in observed)
            unobserved_condition = f" AND external_id NOT IN ({placeholders})"
            parameters += observed
        with self._connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE crew_funding_plans
                SET absent_since = ?, updated_at = ?
                WHERE provider = ?
                    AND absent_since IS NULL
                    {unobserved_condition}
                """,
                parameters,
            )
            return cursor.rowcount

    def upsert_bill_reserve(
        self,
        *,
        provider: str,
        external_id: str,
        total_reserved_amount: Optional[float],
        currency: str = "USD",
        observed_at: Optional[str] = None,
        estimated_next_funding_amount: Optional[float] = None,
        next_funding_date: Optional[str] = None,
    ) -> BillReserveRecord:
        """Store the reserve state this provider read observed.

        Keyed on Crew's own reserve id so a rename updates the record the app already
        cites rather than creating a second one, and re-observing a reserve a previous
        complete read retired clears ``absent_since``.

        ``None`` means the read did not report the total, which is not evidence that the
        bucket is empty, so it never overwrites a total Meridian already knew -- the same
        rule C01 applies to a single bill's reserve. A reported ``0.0`` does overwrite,
        because an emptied bucket is a real observation.

        The reserve's own reported funding schedule (025) follows the identical rule: a
        read that omits either field keeps the stored value rather than clearing it, and a
        reported value replaces it. ``reservedAt``-style provenance is not invented here --
        ``observed_at`` moves only when the read actually reported something.
        """
        timestamp = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO crew_bill_reserves (
                    provider, external_id, total_reserved_amount, currency,
                    observed_at, synced_at, created_at, updated_at,
                    estimated_next_funding_amount, next_funding_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    total_reserved_amount = COALESCE(
                        excluded.total_reserved_amount,
                        crew_bill_reserves.total_reserved_amount
                    ),
                    currency = excluded.currency,
                    observed_at = CASE
                        WHEN excluded.total_reserved_amount IS NULL
                        THEN crew_bill_reserves.observed_at
                        ELSE excluded.observed_at
                    END,
                    synced_at = excluded.synced_at,
                    absent_since = NULL,
                    updated_at = excluded.updated_at,
                    -- Same C01 rule for the reported schedule (025): an unreported field is
                    -- evidence of nothing, so it keeps whatever Meridian already knew.
                    estimated_next_funding_amount = COALESCE(
                        excluded.estimated_next_funding_amount,
                        crew_bill_reserves.estimated_next_funding_amount
                    ),
                    next_funding_date = COALESCE(
                        excluded.next_funding_date,
                        crew_bill_reserves.next_funding_date
                    )
                """,
                (
                    provider,
                    external_id,
                    total_reserved_amount,
                    currency,
                    observed_at,
                    timestamp,
                    timestamp,
                    timestamp,
                    estimated_next_funding_amount,
                    next_funding_date,
                ),
            )
            row = connection.execute(
                "SELECT * FROM crew_bill_reserves WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        assert row is not None
        return BillReserveRecord(**dict(row))

    def get_bill_reserve(self, provider: str, external_id: str) -> Optional[BillReserveRecord]:
        """One stored reserve whether current or retired, or None."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM crew_bill_reserves WHERE provider = ? AND external_id = ?",
                (provider, external_id),
            ).fetchone()
        return BillReserveRecord(**dict(row)) if row is not None else None

    def list_bill_reserves(self) -> list[BillReserveRecord]:
        """The reserves currently observed.

        Retired reserves are excluded rather than deleted: resolution must not divide a
        withdrawn bucket, while the row still documents that the reserve existed and when
        it stopped being returned.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM crew_bill_reserves
                WHERE absent_since IS NULL
                ORDER BY observed_at DESC, id DESC
                """
            ).fetchall()
        return [BillReserveRecord(**dict(row)) for row in rows]

    def mark_absent_bill_reserves(
        self,
        *,
        provider: str,
        observed_external_ids: Sequence[str],
        absent_since: Optional[str] = None,
    ) -> int:
        """Record that a complete read no longer returns these reserves.

        Same discipline as the account, bill and funding-plan absence rules: only a
        complete, error-free read may reach here (the caller enforces that), the row is
        never deleted, and a reserve already concluded absent is left untouched.
        """
        timestamp = absent_since or _now()
        observed = tuple(observed_external_ids)
        unobserved_condition = ""
        parameters: tuple[object, ...] = (timestamp, timestamp, provider)
        if observed:
            placeholders = ", ".join("?" for _ in observed)
            unobserved_condition = f" AND external_id NOT IN ({placeholders})"
            parameters += observed
        with self._connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE crew_bill_reserves
                SET absent_since = ?, updated_at = ?
                WHERE provider = ?
                    AND absent_since IS NULL
                    {unobserved_condition}
                """,
                parameters,
            )
            return cursor.rowcount

    def list_accounts(self) -> list[AccountRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT {_available_account_columns(connection)} FROM financial_accounts "
                "WHERE is_active = 1 ORDER BY name COLLATE NOCASE ASC, id ASC"
            ).fetchall()
        return [self._account_from_row(row) for row in rows]

    def list_archived_accounts(self, *, limit: int = 50) -> list[ArchivedAccountRecord]:
        """Accounts a complete read concluded are gone, newest conclusion first.

        A database that has not applied migration 020 cannot have archived an
        account, so it reports none rather than failing on the new column.
        """
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        with self._connect() as connection:
            if not _reconciles_absence(connection):
                return []
            rows = connection.execute(
                f"""
                SELECT {_available_account_columns(connection)}, (
                    SELECT COUNT(*)
                    FROM financial_transactions AS financial_transaction
                    WHERE financial_transaction.account_id = financial_accounts.id
                ) AS retained_transaction_count
                FROM financial_accounts
                WHERE absent_since IS NOT NULL
                ORDER BY absent_since DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        archived: list[ArchivedAccountRecord] = []
        for row in rows:
            values = dict(row)
            retained = int(values.pop("retained_transaction_count", 0) or 0)
            archived.append(
                ArchivedAccountRecord(
                    account=self._account_from_row(values),
                    retained_transaction_count=retained,
                )
            )
        return archived

    def get_account(self, account_id: int) -> Optional[AccountRecord]:
        """Return one account row, including one no longer returned by a provider."""
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT {_available_account_columns(connection)} FROM financial_accounts "
                "WHERE id = ?",
                (account_id,),
            ).fetchone()
        return self._account_from_row(row) if row is not None else None

    def list_transactions(
        self,
        *,
        limit: int = 50,
        cursor: Optional[str] = None,
        account_id: Optional[int] = None,
    ) -> tuple[list[TransactionRecord], Optional[str]]:
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")

        conditions: list[str] = ["occurred_at_valid = 1"]
        parameters: list[object] = []
        if account_id is not None:
            conditions.append("account_id = ?")
            parameters.append(account_id)
        if cursor is not None:
            occurred_at, record_id = _decode_cursor(cursor)
            conditions.append("(occurred_at < ? OR (occurred_at = ? AND id < ?))")
            parameters.extend((occurred_at, occurred_at, record_id))

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        parameters.append(limit + 1)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT {_TRANSACTION_COLUMNS} FROM financial_transactions"
                f"{where} ORDER BY occurred_at DESC, id DESC LIMIT ?",
                tuple(parameters),
            ).fetchall()

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        records = [self._transaction_from_row(row) for row in page_rows]
        next_cursor = None
        if has_more and records:
            last = records[-1]
            next_cursor = _encode_cursor(last.occurred_at, last.id)
        return records, next_cursor

    def get_transaction(self, transaction_id: int) -> Optional[TransactionRecord]:
        """Return one normalized transaction by its local, opaque Meridian id."""
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT {_TRANSACTION_COLUMNS} FROM financial_transactions "
                "WHERE id = ? AND occurred_at_valid = 1",
                (transaction_id,),
            ).fetchone()
        return self._transaction_from_row(row) if row is not None else None

    def get_freshness_scope(
        self,
        *,
        account_ids: Optional[Sequence[int]] = None,
        transaction_ids: Optional[Sequence[int]] = None,
        include_all_connections: bool = False,
        include_all_transaction_links: bool = False,
    ) -> ProviderFreshnessScope:
        """Return provider state and whether selected records lack a connection."""
        if account_ids is not None and transaction_ids is not None:
            raise ValueError("Specify account_ids or transaction_ids, not both")
        selected_ids = tuple(account_ids or transaction_ids or ())
        selected_records = account_ids is not None or transaction_ids is not None
        parameters: tuple[object, ...] = tuple(selected_ids)
        if account_ids is not None and selected_ids:
            placeholders = ", ".join("?" for _ in account_ids)
            selected_connections_sql = (
                "SELECT connection_id FROM financial_accounts "
                f"WHERE id IN ({placeholders})"
            )
        elif transaction_ids is not None and include_all_transaction_links:
            selected_connections_sql = (
                "SELECT account.connection_id "
                "FROM financial_transactions AS financial_transaction "
                "JOIN financial_accounts AS account "
                "ON account.id = financial_transaction.account_id"
            )
            parameters = ()
        elif transaction_ids is not None and selected_ids:
            placeholders = ", ".join("?" for _ in transaction_ids)
            selected_connections_sql = (
                "SELECT account.connection_id FROM financial_transactions AS financial_transaction "
                "JOIN financial_accounts AS account ON account.id = financial_transaction.account_id "
                f"WHERE financial_transaction.id IN ({placeholders})"
            )
        else:
            selected_connections_sql = None

        with self._connect() as connection:
            connection_ids: set[int] = set()
            has_unlinked_records = False
            if selected_connections_sql is not None:
                selected_rows = connection.execute(
                    selected_connections_sql, parameters
                ).fetchall()
                has_unlinked_records = any(
                    row["connection_id"] is None for row in selected_rows
                )
                connection_ids.update(
                    int(row["connection_id"])
                    for row in selected_rows
                    if row["connection_id"] is not None
                )
            if include_all_connections or not selected_records:
                connection_ids.update(
                    int(row["id"])
                    for row in connection.execute(
                        "SELECT id FROM provider_connections"
                    ).fetchall()
                )
            if not connection_ids:
                return ProviderFreshnessScope(
                    connections=(), has_unlinked_records=has_unlinked_records
                )
            placeholders = ", ".join("?" for _ in connection_ids)
            rows = connection.execute(
                f"""
                SELECT connection.id, connection.provider, connection.status,
                       connection.last_successful_at, account.source_updated_at
                FROM provider_connections AS connection
                -- An account a complete read concluded is gone is no longer a
                -- current observation, so it must not pin or rescue freshness.
                LEFT JOIN financial_accounts AS account
                    ON account.connection_id = connection.id
                    AND account.absent_since IS NULL
                WHERE connection.id IN ({placeholders})
                ORDER BY connection.id ASC, account.id ASC
                """,
                tuple(sorted(connection_ids)),
            ).fetchall()

        grouped: dict[int, dict[str, object]] = {}
        for row in rows:
            connection_id = int(row["id"])
            current = grouped.setdefault(
                connection_id,
                {
                    "provider": row["provider"],
                    "status": row["status"],
                    "last_successful_at": row["last_successful_at"],
                    "source_updated_at": [],
                },
            )
            current["source_updated_at"].append(row["source_updated_at"])
        return ProviderFreshnessScope(
            connections=tuple(
                ProviderConnectionFreshness(
                    connection_id=connection_id,
                    provider=values["provider"],
                    status=values["status"],
                    last_successful_at=values["last_successful_at"],
                    source_updated_at=tuple(values["source_updated_at"]),
                )
                for connection_id, values in grouped.items()
            ),
            has_unlinked_records=has_unlinked_records,
        )

    def list_connection_freshness(
        self,
        *,
        account_ids: Optional[Sequence[int]] = None,
        transaction_ids: Optional[Sequence[int]] = None,
    ) -> list[ProviderConnectionFreshness]:
        """Return provider freshness records for the requested record scope."""
        return list(
            self.get_freshness_scope(
                account_ids=account_ids,
                transaction_ids=transaction_ids,
            ).connections
        )

    @staticmethod
    def _account_from_row(row: sqlite3.Row) -> AccountRecord:
        values = dict(row)
        values["is_active"] = bool(values["is_active"])
        return AccountRecord(**values)

    @staticmethod
    def _transaction_from_row(row: sqlite3.Row) -> TransactionRecord:
        values = dict(row)
        for field in (
            "classification_category",
            "classification_kind",
            "classification_confidence",
            "classification_rule_id",
            "classification_evidence",
            "classification_method",
            "classification_provider",
            "classification_model",
        ):
            values.setdefault(field, None)
        values.setdefault("classification_version", 0)
        return TransactionRecord(**values)


def _keyword_category_guess(text: str) -> str | None:
    """Heuristic category for obvious merchant keywords (best-effort)."""
    from .category_catalog import known_merchant_category

    known = known_merchant_category(text)
    if known:
        return known[0]
    t = (text or "").lower()
    table = [
        (("starbucks", "chipotle", "mcdonald", "dunkin", "wendy", "taco bell", "kfc", "restaurant", "cafe", "coffee", "grill", "pizza", "subway", "bistro"), "Dining"),
        (("walmart", "target", "costco", "shop", "amazon", "best buy", "store", "mall", "ikea", "ebay"), "Shopping"),
        (("shell", "chevron", "exxon", "bp ", "sunoco", "gas", "fuel"), "Gas"),
        (("verizon", "att", "at&t", "tmobile", "t-mobile", "xfinity", "comcast", "spectrum", "internet", "phone"), "Utilities"),
        (("netflix", "spotify", "hulu", "disney", "hbo", "paramount", "youtube", "google play", "app store", "apple", "steam"), "Entertainment"),
        (("uber", "lyft", "transit", "metro", "airline", "delta", "united", "southwest", "amtrak"), "Transport"),
        (("cvs", "walgreens", "pharmacy", "clinic", "doctor", "hospital", "dental"), "Health"),
        (("rent", "landlord", "lease", "mortgage", "realty"), "Rent"),
        (("gym", "fitness", "training", "equinox", "planet fitness"), "Health"),
    ]
    for keywords, category in table:
        if any(k in t for k in keywords):
            return category
    return None
