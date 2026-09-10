"""Append-only, credential-free provider observations for the Meridian digital twin."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from .db import run_migrations
from .providers.base import ProviderSnapshot


@dataclass(frozen=True)
class ObservationRecord:
    id: int
    snapshot_id: str
    provider: str
    connection_external_id: str
    object_kind: str
    external_id: str
    observed_at: str
    source_updated_at: Optional[str]
    freshness: str
    confidence: Optional[float]
    assumptions: tuple[str, ...]
    payload_hash: str
    data_mode: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["assumptions"] = list(self.assumptions)
        return result


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _account_payload(account) -> dict[str, Any]:
    return {"external_id": account.external_id, "name": account.name, "account_type": account.account_type,
            "balance": account.balance, "currency": account.currency, "available_balance": account.available_balance,
            "is_active": account.is_active, "source_updated_at": account.source_updated_at}


def _transaction_payload(transaction) -> dict[str, Any]:
    return {"external_id": transaction.external_id, "account_external_id": transaction.account_external_id,
            "amount": transaction.amount, "occurred_at": transaction.occurred_at, "description": transaction.description,
            "status": transaction.status, "currency": transaction.currency, "posted_at": transaction.posted_at,
            "merchant": transaction.merchant, "source_updated_at": transaction.source_updated_at,
            "category": transaction.category, "relation_hint": transaction.relation_hint}


class ObservationRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        run_migrations(db_path)

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def append_snapshot(self, *, provider: str, snapshot: ProviderSnapshot, observed_at: str,
                        confidence: Optional[float] = None, assumptions: Iterable[str] = ()) -> tuple[ObservationRecord, ...]:
        if not provider or not snapshot.connection_external_id:
            raise ValueError("provider and connection are required")
        if not observed_at:
            raise ValueError("observed_at is required")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        objects = [("account", item.external_id, item.source_updated_at, _account_payload(item)) for item in snapshot.accounts]
        objects += [("transaction", item.external_id, item.source_updated_at, _transaction_payload(item)) for item in snapshot.transactions]
        snapshot_id = _digest({"provider": provider, "connection": snapshot.connection_external_id,
                               "observed_at": observed_at, "objects": [(kind, ext, payload) for kind, ext, _, payload in objects]})
        freshness = "fresh" if snapshot.is_complete else ("partial" if objects else "unavailable")
        assumptions_json = _canonical(tuple(assumptions))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for kind, external_id, source_updated_at, payload in objects:
                connection.execute("""INSERT OR IGNORE INTO financial_observations
                    (snapshot_id, provider, connection_external_id, object_kind, external_id, observed_at,
                     source_updated_at, freshness, confidence, assumptions_json, payload_json, payload_hash, data_mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'actual')""",
                    (snapshot_id, provider, snapshot.connection_external_id, kind, external_id, observed_at,
                     source_updated_at, freshness, confidence, assumptions_json, _canonical(payload), _digest(payload)))
            rows = connection.execute("SELECT * FROM financial_observations WHERE snapshot_id = ? ORDER BY object_kind, external_id", (snapshot_id,)).fetchall()
        return tuple(self._record(row) for row in rows)

    def list_snapshot(self, snapshot_id: str) -> list[ObservationRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM financial_observations WHERE snapshot_id = ? ORDER BY object_kind, external_id", (snapshot_id,)).fetchall()
        return [self._record(row) for row in rows]

    def list_recent(self, limit: int = 100) -> list[ObservationRecord]:
        if not isinstance(limit, int) or limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM financial_observations ORDER BY observed_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
        return [self._record(row) for row in rows]

    @staticmethod
    def _record(row) -> ObservationRecord:
        return ObservationRecord(id=row["id"], snapshot_id=row["snapshot_id"], provider=row["provider"],
            connection_external_id=row["connection_external_id"], object_kind=row["object_kind"], external_id=row["external_id"],
            observed_at=row["observed_at"], source_updated_at=row["source_updated_at"], freshness=row["freshness"],
            confidence=row["confidence"], assumptions=tuple(json.loads(row["assumptions_json"])), payload_hash=row["payload_hash"],
            data_mode=row["data_mode"], created_at=row["created_at"])


def record_provider_snapshot(adapter, repository: ObservationRepository, *, observed_at: str | None = None,
                             confidence: Optional[float] = None, assumptions: Iterable[str] = ()) -> tuple[ObservationRecord, ...]:
    """Fetch one read-only adapter snapshot and append it without changing the read model."""
    if repository is None:
        raise ValueError("repository is required")
    snapshot = adapter.fetch_snapshot()
    store = repository
    return store.append_snapshot(provider=adapter.provider_name, snapshot=snapshot,
                                 observed_at=observed_at or _now(), confidence=confidence,
                                 assumptions=assumptions)
