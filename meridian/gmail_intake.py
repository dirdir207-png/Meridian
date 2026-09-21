"""Gmail -> evidence intake runner (R28/29 pilot).

Fetches a bounded set of recent Gmail messages via the owner's OAuth token and
stores each as an evidence item (source_kind='mail') through the document-intake
pipeline. Read-only: never mutates Gmail; only stores the message body text as
evidence with sane size limits.

This is a pilot: it reads a small, recent slice and records how Gmail data
populates the evidence layer. It is intentionally conservative (no attachment
download, bounded count, quarantine on oversized/empty).
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from .connectors.gmail_read import GmailEvidence, GmailTransport
from .evidence import EvidenceRepository
from .ingest import IntakeRecord, QuarantineError, ingest_record


def _date_days_ago(days: int) -> str:
    """ISO date ``days`` before today (UTC), used as the email backfill cutoff."""
    return (date.today() - timedelta(days=days)).isoformat()


# --- forwarded-mail provenance (OS-067) -------------------------------------------
#
# MEASURED, not assumed (2026-09-20, a real forwarded Eversource bill): Gmail
# forwarding REPLACES the From header with the forwarding account, so a forwarded bill
# arrives `from: gmail.com`. The forwarded copy carried 44 headers and NONE of them held
# the original sender -- `return-path` was rewritten, and there is no Resent-From /
# X-Forwarded-For / X-Original-From. So a header-based recovery is impossible.
#
# The original sender survives only in the forwarded BODY, where the mail client quotes
# the original headers ("From: Eversource <...@notifications.eversource.com>"). Without
# recovering it, the bill-invoice matcher (which keys on the sender's DOMAIN) fails for
# every forwarded bill, and the subject fallback is deliberately strict, so forwarded
# invoices simply stop appearing on their bills.
#
# The recovered domain is appended to the evidence TITLE rather than injected as a
# synthetic sender, so the matcher's existing token logic uses it unchanged and the
# stored `sender` keeps reporting what actually arrived -- the evidence record does not
# start claiming a sender it did not observe.

_FORWARDED_FROM = re.compile(r"^\s*From:\s*(.+)$", re.MULTILINE)
_EMAIL_DOMAIN = re.compile(r"@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_FORWARDED_BODY_SCAN_BYTES = 20000
_FORWARDED_CANDIDATE_LIMIT = 3


def forwarded_sender_domains(body_text: str | None) -> list[str]:
    """Original sender domains quoted inside a forwarded body.

    Bounded on both axes on purpose: only the head of the body is scanned, and only a
    few candidates are returned, so a large or hostile message cannot make this slow or
    flood the matcher with domains. Order is preserved, so the first entry is the mail
    client's own quoted ``From:`` -- the true original sender.
    """
    if not body_text:
        return []
    head = body_text[:_FORWARDED_BODY_SCAN_BYTES]
    found: list[str] = []
    for match in _FORWARDED_FROM.finditer(head):
        for domain in _EMAIL_DOMAIN.findall(match.group(1)):
            lowered = domain.lower()
            if lowered not in found:
                found.append(lowered)
            if len(found) >= _FORWARDED_CANDIDATE_LIMIT:
                return found
    return found


def evidence_title(subject: str | None, body_text: str | None, fallback: str) -> str:
    """Title for a stored mail item, carrying recovered forwarded provenance.

    A plain subject when the message was not forwarded; otherwise the subject plus the
    original sender domain, which is what lets a forwarded bill still find its bill.
    """
    title = subject or fallback
    domains = forwarded_sender_domains(body_text)
    if not domains:
        return title
    # Deliberately labelled: this domain was RECOVERED from quoted text, not observed as
    # an authenticated sender, and the title should not hide that distinction.
    return f"{title} (forwarded from {', '.join(domains)})"


def ingest_gmail_recent(
    *,
    transport: GmailTransport,
    evidence_repo: EvidenceRepository,
    max_messages: int = 20,
    since_days: int = 30,
    transactions=None,
    blob_store=None,
) -> dict[str, object]:
    """Fetch recent Gmail messages and store each as evidence.

    ``since_days`` bounds the backfill to roughly that many days by filtering the
    inbox query to messages after the cutoff (default 30). When ``transactions``
    is supplied, stored mail evidence is linked to a matching transaction by
    amount (documented charge receipts). Returns a sanitized summary: counts
    stored/duplicate/quarantined/error/linked, plus the subject + source_id of
    each stored item (never the body).
    """
    stored: list[dict[str, str]] = []
    duplicate = 0
    quarantined = 0
    errors = 0
    linked = 0

    since = _date_days_ago(since_days)
    messages: list[GmailEvidence] = transport.fetch_recent(
        max_results=max_messages, since=since
    )
    for msg in messages:
        if not msg.body_text.strip():
            quarantined += 1
            continue
        record = IntakeRecord(
            source_kind="mail",
            source_id=msg.message_id,
            blob=msg.body_text.encode("utf-8"),
            mime_type="text/plain",
            title=evidence_title(msg.subject, msg.body_text, "Gmail message"),
            sender=msg.sender or None,
        )
        try:
            result = ingest_record(record, evidence_repo=evidence_repo, blob_store=blob_store)
        except QuarantineError:
            quarantined += 1
            continue
        except Exception:  # noqa: BLE001 - a single bad message must not stop the batch
            errors += 1
            continue
        if result.duplicate:
            duplicate += 1
            continue
        if transactions:
            created = link_mail_evidence_to_transactions(
                evidence_repo=evidence_repo,
                transactions=transactions,
                evidence_id=result.item_id,
                subject=msg.subject or "",
                body=msg.body_text,
            )
            linked += created
        stored.append(
            {
                "id": str(result.item_id),
                "subject": msg.subject or "",
                "sender": msg.sender or "",
                "received_at": msg.received_at or "",
            }
        )

    return {
        "fetched": len(messages),
        "stored": len(stored),
        "duplicate": duplicate,
        "quarantined": quarantined,
        "errors": errors,
        "linked": linked,
        "items": stored,
    }


def ingest_all_gmail_accounts(
    *,
    db_path: str,
    evidence_repo: EvidenceRepository,
    token_client,
    max_messages_per_account: int = 10,
    since_days: int = 30,
    blob_store=None,
    on_account_error=None,
) -> dict[str, object]:
    """Ingest recent Gmail from every connected Gmail account.

    Enumerates all stored Gmail OAuth tokens (multi-account), builds a transport
    for each, and stores each account's recent messages as evidence. Read-only
    Gmail; no mutation. Returns a per-account summary plus a total.

    One account failing must not hide the others: a token that cannot be refreshed is
    reported through ``on_account_error(email, exception)`` and the run continues with
    the remaining accounts. Before this, the first dead token raised out of the whole
    call, so a single expired credential looked like a total Gmail outage.
    """
    from .connectors.google_auth import OAuthTokenStore

    store = OAuthTokenStore(db_path)
    accounts = store.list_accounts(kind="gmail")
    total_fetched = 0
    total_stored = 0
    failed = 0
    per_account: list[dict[str, object]] = []
    for acct in accounts:
        email = str(acct.get("account_email") or "")
        token = store.get(kind="gmail", account_email=email)
        if not token:
            continue

        def _refresh(_tok=token):
            return token_client.refresh(_tok["refresh_token"])

        transport = GmailTransport(access_token=token["access_token"], refresh=_refresh)
        try:
            summary = ingest_gmail_recent(
                transport=transport,
                evidence_repo=evidence_repo,
                max_messages=max_messages_per_account,
                since_days=since_days,
                blob_store=blob_store,
            )
        except Exception as exc:  # noqa: BLE001 - one dead token must not stop the rest
            failed += 1
            if on_account_error is not None:
                try:
                    on_account_error(email, exc)
                except Exception:  # noqa: BLE001 - reporting must never break intake
                    pass
            per_account.append({"account_email": email, "state": "unavailable",
                                "error": type(exc).__name__})
            continue
        per_account.append({"account_email": email, **summary})
        total_fetched += int(summary["fetched"])
        total_stored += int(summary["stored"])

    return {
        "accounts": per_account,
        "total_fetched": total_fetched,
        "total_stored": total_stored,
        "accounts_unavailable": failed,
    }


def link_mail_evidence_to_transactions(
    *,
    evidence_repo,
    transactions,
    evidence_id: int,
    subject: str,
    body: str | None = None,
    provenance: str = "gmail:amount-match",
) -> int:
    """Link a mail evidence item to the CHARGE it documents.

    Best-effort and read-only: never mutates a transaction, only adds an evidence link so a
    receipt can be traced to the charge.

    THIS USED TO MATCH ON AMOUNT ALONE, and that was actively harmful. A bare amount has no
    discriminating power on a real ledger: one run over 45 receipts created 270 links,
    because a $50.00 receipt matched every $50.00 charge, and common amounts like $8.00 recur
    (12 OpenAI charges of exactly $8.00). Those links are not evidence — they are noise
    wearing the shape of evidence.

    Now only a DATE-CORROBORATED match is linked, which means:

      * one receipt produces AT MOST ONE link;
      * a receipt whose date contradicts every candidate produces NONE, because "the amount
        matched but no charge happened near it" is not evidence for any of them;
      * an unresolvable tie produces none either, since linking one of several identical
        charges asserts a fact the data does not support.

    Adding a link is the only mutation, and it never touches a transaction.
    """
    from .charge_match import (
        CONFIDENCE_HIGH,
        attach_charge_matches,
        find_charge_matches,
    )

    class _Signal:
        __slots__ = ("id", "title", "body", "sender")

        def __init__(self):
            self.id = evidence_id
            self.title = subject or ""
            self.body = body or ""
            self.sender = ""

    matches = find_charge_matches(
        evidence_items=[_Signal()], transactions=transactions
    )
    usable = [m for m in matches if m.matched and m.confidence == CONFIDENCE_HIGH]
    if not usable:
        return 0
    result = attach_charge_matches(
        evidence_repo=evidence_repo,
        matches=usable,
        provenance_prefix=provenance.split(":", 1)[0],
    )
    return result["created"]


def ingest_icloud_recent(
    *,
    transport,
    evidence_repo,
    max_messages: int = 20,
    since_days: int = 30,
    transactions=None,
    blob_store=None,
    mailbox: str = "INBOX",
) -> dict[str, object]:
    """Ingest recent iCloud Mail messages as evidence (reuses the intake).

    ``since_days`` bounds the backfill to roughly that many days via an IMAP
    SINCE search (default 30). Read-only: never mutates iCloud. Stored items
    are source_kind='mail' (the same evidence surface as Gmail). When
    ``transactions`` is supplied, stored evidence is linked to matching
    transactions by amount.

    ``mailbox`` selects which folder is read. It defaults to INBOX for backward
    compatibility, but the inbox is the wrong choice once mail is FORWARDED in:
    measured 2026-09-20 the inbox held 28,393 messages from 127 distinct senders —
    MoneyLion, Spotify, GitHub, marketing — and the intake stores every message with a
    body as evidence, so personal mail became Meridian evidence and diluted the bill
    matcher. Point this at a dedicated folder to keep the store to bills.
    """
    stored: list[dict[str, str]] = []
    duplicate = 0
    quarantined = 0
    errors = 0
    linked = 0

    messages = transport.fetch_recent(
        max_results=max_messages, since=_date_days_ago(since_days), mailbox=mailbox
    )
    for msg in messages:
        if not msg.body_text.strip():
            quarantined += 1
            continue
        record = IntakeRecord(
            source_kind="mail",
            source_id=msg.message_id,
            blob=msg.body_text.encode("utf-8"),
            mime_type="text/plain",
            title=evidence_title(msg.subject, msg.body_text, "iCloud Mail message"),
            sender=msg.sender or None,
        )
        try:
            result = ingest_record(record, evidence_repo=evidence_repo, blob_store=blob_store)
        except QuarantineError:
            quarantined += 1
            continue
        except Exception:  # noqa: BLE001 - a single bad message must not stop the batch
            errors += 1
            continue
        if result.duplicate:
            duplicate += 1
            continue
        if transactions:
            created = link_mail_evidence_to_transactions(
                evidence_repo=evidence_repo,
                transactions=transactions,
                evidence_id=result.item_id,
                subject=msg.subject or "",
                body=msg.body_text,
                provenance="icloud:amount-match",
            )
            linked += created
        stored.append(
            {
                "id": str(result.item_id),
                "subject": msg.subject or "",
                "sender": msg.sender or "",
                "received_at": msg.received_at or "",
            }
        )

    return {
        "fetched": len(messages),
        "stored": len(stored),
        "duplicate": duplicate,
        "quarantined": quarantined,
        "errors": errors,
        "linked": linked,
        "items": stored,
    }
