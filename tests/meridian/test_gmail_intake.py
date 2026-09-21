"""Tests for the Gmail -> evidence intake runner (R28/29 pilot).

Uses a fake transport (no live Gmail) so the pipeline is proven deterministic.
The real Gmail transport is separately covered by connector tests; here we
verify that fetched messages become evidence items via the document intake,
respect dedup, and quarantine empty/oversized bodies.
"""

import pytest

from meridian.connectors.gmail_read import GmailEvidence
from meridian.evidence import EvidenceRepository
from meridian.gmail_intake import ingest_gmail_recent


@pytest.fixture
def evidence_repo(tmp_path):
    return EvidenceRepository(str(tmp_path / "evidence.db"))


class FakeTransport:
    def __init__(self, messages):
        self._messages = messages

    def fetch_recent(self, *, max_results=20, since=None):
        return self._messages[:max_results]


def _msg(mid, subject, body, sender="bill@merchant.com", received="2026-09-05T12:00:00Z"):
    return GmailEvidence(
        message_id=mid, subject=subject, sender=sender,
        received_at=received, body_text=body, thread_id=None,
    )


def _ingest_store(tmp_path, name="evidence-blobs"):
    """The intake now refuses to run without a blob store (a row whose content cannot be
    kept is the bug that left 729 items unopenable), so tests must supply one."""
    from meridian.storage import DerivedKeyProvider, EncryptedBlobStore

    return EncryptedBlobStore(
        str(tmp_path / name),
        DerivedKeyProvider(b"test-secret-key-00000000000000000000000000"),
    )


def test_ingest_gmail_stores_messages_as_mail_evidence(evidence_repo, tmp_path):
    transport = FakeTransport([_msg("m1", "Your Eversource bill", "Amount due: $210.00 by Sep 20")])
    summary = ingest_gmail_recent(transport=transport, evidence_repo=evidence_repo, max_messages=5, blob_store=_ingest_store(tmp_path))

    assert summary["fetched"] == 1
    assert summary["stored"] == 1
    # The stored item is retrievable by its content hash (dedup key).
    import hashlib
    body = "Amount due: $210.00 by Sep 20"
    stored_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert evidence_repo.get_by_content_hash(stored_hash) is not None
    assert summary["items"][0]["subject"] == "Your Eversource bill"


def test_ingest_gmail_dedups_on_duplicate(evidence_repo, tmp_path):
    transport = FakeTransport([_msg("m1", "Duplicate", "same body text content")])
    first = ingest_gmail_recent(transport=transport, evidence_repo=evidence_repo, blob_store=_ingest_store(tmp_path))
    second = ingest_gmail_recent(transport=transport, evidence_repo=evidence_repo, blob_store=_ingest_store(tmp_path))

    assert first["stored"] == 1
    assert second["duplicate"] == 1 and second["stored"] == 0


def test_ingest_gmail_quarantines_empty_body(evidence_repo, tmp_path):
    transport = FakeTransport([_msg("m1", "Empty", "   ")])
    summary = ingest_gmail_recent(transport=transport, evidence_repo=evidence_repo, blob_store=_ingest_store(tmp_path))
    assert summary["quarantined"] == 1
    assert summary["stored"] == 0


def test_ingest_gmail_handles_mixed_batch_and_never_leaks_body(evidence_repo, tmp_path):
    transport = FakeTransport(
        [
            _msg("m1", "Bill A", "Amount due $50"),
            _msg("m2", "", ""),  # empty -> quarantine
            _msg("m3", "Bill B", "Statement attached"),
        ]
    )
    summary = ingest_gmail_recent(transport=transport, evidence_repo=evidence_repo, blob_store=_ingest_store(tmp_path))

    assert summary["stored"] == 2
    assert summary["quarantined"] == 1
    # Only sanitized fields are exposed in the summary, never the body.
    assert all("body" not in item and "body_text" not in item for item in summary["items"])


def test_ingest_all_gmail_accounts_iterates_each_token(tmp_path, monkeypatch):
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_all_gmail_accounts

    db = str(tmp_path / "multi.db")
    # Store two fake gmail tokens.
    import sqlite3
    conn = sqlite3.connect(db)
    conn.execute("""CREATE TABLE IF NOT EXISTS oauth_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
        account_email TEXT NOT NULL, access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL, expires_at TEXT, created_at TEXT NOT NULL,
        UNIQUE (kind, account_email))""")
    conn.execute("INSERT INTO oauth_tokens(kind,account_email,access_token,refresh_token,created_at) VALUES('gmail','a@gmail.com','at-a','rt-a','2026-01-01')")
    conn.execute("INSERT INTO oauth_tokens(kind,account_email,access_token,refresh_token,created_at) VALUES('gmail','b@gmail.com','at-b','rt-b','2026-01-01')")
    conn.commit(); conn.close()

    class FakeClient:
        def refresh(self, rt):
            return {"access_token": "fresh-" + rt}

    # Monkeypatch GmailTransport.fetch_recent to avoid live network.
    from meridian import gmail_intake as gi
    from meridian.connectors.gmail_read import GmailEvidence
    calls = []
    def fake_fetch(self, *, max_results=20, since=None):
        calls.append(self._access_token)
        return [GmailEvidence(message_id=f"m-{self._access_token}", subject=f"Subject {self._access_token}", sender="x@y.z", received_at="2026-09-05T00:00:00Z", body_text=f"Bill amount due $50 for {self._access_token}")]
    monkeypatch.setattr(gi.GmailTransport, "fetch_recent", fake_fetch)

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    summary = ingest_all_gmail_accounts(db_path=db, evidence_repo=repo, token_client=FakeClient(), max_messages_per_account=5, blob_store=_ingest_store(tmp_path))

    assert summary["total_stored"] == 2
    assert len(summary["accounts"]) == 2
    assert calls == ["at-a", "at-b"]  # stored token used; refresh fires only on 401


def test_link_mail_evidence_matches_transaction_by_amount(tmp_path):
    import sqlite3

    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import link_mail_evidence_to_transactions

    db = str(tmp_path / "link.db")
    # A transaction with amount -92.75.
    conn = sqlite3.connect(db)
    conn.execute("""CREATE TABLE financial_transactions (
        id INTEGER PRIMARY KEY, amount REAL, merchant TEXT, description TEXT,
        account_id INTEGER, provider TEXT, external_id TEXT, currency TEXT,
        occurred_at TEXT, posted_at TEXT, status TEXT, raw_description TEXT,
        source_updated_at TEXT, classification_category TEXT, classification_kind TEXT,
        classification_confidence REAL, classification_rule_id TEXT, classification_evidence TEXT,
        classification_method TEXT, classification_provider TEXT, classification_model TEXT,
        classification_version INTEGER, synced_at TEXT, created_at TEXT, updated_at TEXT,
        occurred_at_valid INTEGER DEFAULT 1)""")
    conn.execute("INSERT INTO financial_transactions(id, amount) VALUES (40, -92.75)")
    conn.commit(); conn.close()

    class Tx:
        def __init__(self, id, amount, occurred_at=None):
            self.id = id; self.amount = amount; self.occurred_at = occurred_at

    repo = EvidenceRepository(str(tmp_path / "ev.db"))
    repo.add_item(source_kind="mail", source_id="m1", content_hash="a"*64, mime_type="text/plain", size_bytes=10, title="Urgent: $92.75 charged")

    # The date is now REQUIRED: amount alone cannot discriminate on a real ledger, so the
    # subject must state when the charge happened.
    created = link_mail_evidence_to_transactions(
        evidence_repo=repo,
        transactions=[Tx(40, -92.75, "2026-09-18T09:00:00Z")],
        evidence_id=1,
        subject="Urgent: $92.75 charged on 2026-09-18 but no order confirmation",
    )

    assert created == 1
    assert len(repo.list_links_for_target("transaction", "40")) == 1


def test_link_mail_evidence_no_match_returns_zero(tmp_path):
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import link_mail_evidence_to_transactions

    class Tx:
        def __init__(self, id, amount): self.id = id; self.amount = amount

    repo = EvidenceRepository(str(tmp_path / "ev.db"))
    repo.add_item(source_kind="mail", source_id="m1", content_hash="b"*64, mime_type="text/plain", size_bytes=10, title="Welcome")

    created = link_mail_evidence_to_transactions(
        evidence_repo=repo, transactions=[Tx(40, -92.75)], evidence_id=1,
        subject="Welcome to Waypoint Budget",
    )
    assert created == 0


def test_ingest_icloud_recent_stores_mail_evidence(tmp_path):
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            return [
                IcloudMailMessage(
                    message_id="<ic1@icloud.com>", subject="Your iCloud bill",
                    sender="billing@x.com", received_at="Fri, 05 Sep 2026 12:00:00 +0000",
                    body_text="Amount due $75.00", thread_id="<ic1@icloud.com>",
                )
            ]

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    summary = ingest_icloud_recent(transport=FakeTransport(), evidence_repo=repo, max_messages=5, blob_store=_ingest_store(tmp_path))

    assert summary["stored"] == 1
    assert summary["items"][0]["subject"] == "Your iCloud bill"
    assert repo.get_by_content_hash(__import__("hashlib").sha256(b"Amount due $75.00").hexdigest()) is not None


def test_ingest_icloud_links_use_icloud_provenance(tmp_path):
    """iCloud links must be labeled icloud (not gmail), and must carry their BASIS.

    The provenance used to be a bare "icloud:amount-match". Amount alone cannot discriminate
    on a real ledger — one run over 45 receipts produced 270 links because common amounts
    recur (12 OpenAI charges of exactly $8.00) — so the basis and its confidence are recorded.
    """
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            return [
                IcloudMailMessage(
                    message_id="<ic2@icloud.com>", subject="Your charge",
                    sender="billing@x.com", received_at="Fri, 05 Sep 2026 12:00:00 +0000",
                    body_text="Amount $92.75 charged on 2026-09-05", thread_id="<ic2@icloud.com>",
                )
            ]

    class Tx:
        def __init__(self, txid, amount, occurred_at=None):
            self.id = txid
            self.amount = amount
            self.occurred_at = occurred_at

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    summary = ingest_icloud_recent(
        transport=FakeTransport(), evidence_repo=repo, max_messages=5,
        transactions=[Tx(40, -92.75, "2026-09-05T10:00:00Z")],
        blob_store=_ingest_store(tmp_path),
    )

    assert summary["linked"] == 1
    links = repo.list_links(int(summary["items"][0]["id"]))
    assert links, "expected at least one linked evidence link"
    assert all(link.provenance.startswith("icloud:") for link in links), (
        "the iCloud leg must stay distinguishable from the Gmail leg"
    )
    assert all(link.provenance == "icloud:amount+date:high" for link in links), (
        "the BASIS must be recorded, and this receipt's date corroborates the charge"
    )


def test_a_common_amount_does_not_link_to_every_matching_charge(tmp_path):
    """The regression that mattered: 45 receipts once produced 270 links.

    One receipt must produce at most ONE link, and a tie must be recorded as doubt.
    """
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            return [
                IcloudMailMessage(
                    message_id="<one@icloud.com>", subject="Receipt",
                    sender="billing@x.com", received_at="Mon, 15 Sep 2026 12:00:00 +0000",
                    body_text="Charged $8.00 on 2026-09-15", thread_id="<one@icloud.com>",
                )
            ]

    class Tx:
        def __init__(self, txid, amount, occurred_at):
            self.id = txid
            self.amount = amount
            self.occurred_at = occurred_at

    # Seven charges of $8.00 on the receipt's own day — genuinely indistinguishable — plus
    # one far in the past that must never be chosen.
    transactions = [Tx(i, -8.0, "2026-09-15T09:00:00Z") for i in range(7)]
    transactions.append(Tx(99, -8.0, "2026-06-01T09:00:00Z"))

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    summary = ingest_icloud_recent(
        transport=FakeTransport(), evidence_repo=repo, max_messages=5,
        transactions=transactions, blob_store=_ingest_store(tmp_path),
    )

    links = repo.list_links(int(summary["items"][0]["id"]))
    assert links == [], (
        "seven indistinguishable $8.00 charges must produce NO link: linking one would assert "
        "a fact the data does not support, and linking all seven is what produced 270 links "
        "from 45 receipts"
    )


def test_a_receipt_whose_date_contradicts_every_charge_creates_no_link(tmp_path):
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            return [
                IcloudMailMessage(
                    message_id="<far@icloud.com>", subject="Receipt",
                    sender="billing@x.com", received_at="Wed, 16 Sep 2026 12:00:00 +0000",
                    body_text="Charged $50.00 on 2026-09-16", thread_id="<far@icloud.com>",
                )
            ]

    class Tx:
        def __init__(self):
            self.id = "old"
            self.amount = -50.0
            self.occurred_at = "2026-01-05T09:00:00Z"

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    summary = ingest_icloud_recent(
        transport=FakeTransport(), evidence_repo=repo, max_messages=5,
        transactions=[Tx()], blob_store=_ingest_store(tmp_path),
    )
    links = repo.list_links(int(summary["items"][0]["id"])) if summary["items"] else []
    assert not links, "a charge eight months away is not evidence for this receipt"


# --- OS-067: forwarded-mail provenance --------------------------------------------
#
# MEASURED against a real forwarded Eversource bill (2026-09-20): Gmail forwarding
# REPLACES the From header with the forwarding account, so a forwarded bill arrives
# `from: gmail.com`. The forwarded copy carried 44 headers and NONE held the original
#  return-path was rewritten and there is no Resent-From / X-Forwarded-For /
# X-Original-From. The original sender survives ONLY in the forwarded body, where the
# mail client quotes the original headers. Without recovering it, the bill matcher
# (which keys on the sender's DOMAIN) misses every forwarded bill.

_REAL_FORWARD = (
    "\r\n---------- Forwarded message ---------\r\n"
    "From: Eversource <notifications@notifications.eversource.com>\r\n"
    "Date: Sat, 20 Sep 2026\r\n"
    "Subject: Your Eversource bill is ready\r\n"
    "To: owner@gmail.com\r\n\r\nYour amount due is $210.00\r\n"
)


def test_a_forwarded_body_yields_the_original_sender_domain():
    from meridian.gmail_intake import forwarded_sender_domains

    assert forwarded_sender_domains(_REAL_FORWARD) == ["notifications.eversource.com"]


def test_a_non_forwarded_message_contributes_nothing():
    from meridian.gmail_intake import forwarded_sender_domains

    assert forwarded_sender_domains("Your Verizon bill is ready. Amount due $101.57") == []


def test_the_scan_is_bounded_so_a_huge_body_cannot_flood_the_matcher():
    from meridian.gmail_intake import forwarded_sender_domains

    huge = "\n".join(f"From: x{i}@spam{i}.example.com" for i in range(5000))
    found = forwarded_sender_domains(huge)
    assert len(found) == 3, "candidate count must be capped"
    assert found[0] == "spam0.example.com", "the first quoted From is the real sender"


def test_missing_body_is_handled():
    from meridian.gmail_intake import forwarded_sender_domains

    assert forwarded_sender_domains("") == []
    assert forwarded_sender_domains(None) == []


def test_the_title_carries_recovered_provenance_and_labels_it_as_recovered():
    from meridian.gmail_intake import evidence_title

    title = evidence_title("Fwd: Your Eversource bill is ready", _REAL_FORWARD, "iCloud Mail message")
    assert "notifications.eversource.com" in title
    # It was RECOVERED from quoted text, not observed as an authenticated sender, so the
    # record must not present it as if it had arrived that way.
    assert "forwarded from" in title.lower()


def test_a_plain_subject_is_left_alone():
    from meridian.gmail_intake import evidence_title

    assert evidence_title("Your Verizon bill is ready", "no headers here", "Gmail message") == (
        "Your Verizon bill is ready"
    )


def test_a_forwarded_bill_links_to_its_bill_end_to_end(tmp_path):
    """The property that actually matters: forwarded mail reaches the right bill."""
    import hashlib

    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import evidence_title
    from meridian.services.plan import _bill_invoice_evidence

    repo = EvidenceRepository(str(tmp_path / "ev.db"))

    def store(source_id, text, title, sender):
        data = text.encode()
        return repo.add_item(
            source_kind="mail", source_id=source_id, mime_type="text/plain",
            content_hash=hashlib.sha256(data).hexdigest(), size_bytes=len(data),
            title=title, sender=sender,
        )

    forwarded = store(
        "m-forwarded", _REAL_FORWARD,
        evidence_title("Fwd: Your Eversource bill is ready", _REAL_FORWARD, "iCloud Mail message"),
        "Some Owner <owner@gmail.com>",
    )

    found = _bill_invoice_evidence(repo, "Eversource")
    assert found, "the forwarded Eversource bill must resolve to its evidence item"
    assert found[0]["id"] == forwarded.id
    # The stored sender still reports what actually  no synthetic sender.
    assert found[0]["sender"] == "Some Owner <owner@gmail.com>"

    # And it must not start matching bills it has nothing to do with.
    for unrelated in ("Xfinity", "Rent"):
        assert _bill_invoice_evidence(repo, unrelated) == [], (
            f"a forwarded Eversource bill must not surface on {unrelated}"
        )


def test_the_marketing_guard_still_holds(tmp_path):
    """A promo quoting a biller domain must NOT become an invoice.

    The is_bill keyword guard is deliberately strict; recovery must not weaken it.
    """
    import hashlib

    from meridian.evidence import EvidenceRepository
    from meridian.services.plan import _bill_invoice_evidence

    repo = EvidenceRepository(str(tmp_path / "ev.db"))
    promo = "Fwd: Big sale this week (forwarded from notifications.eversource.com)"
    data = promo.encode()
    repo.add_item(
        source_kind="mail", source_id="m-promo", mime_type="text/plain",
        content_hash=hashlib.sha256(data).hexdigest(), size_bytes=len(data),
        title=promo, sender="Some Owner <owner@gmail.com>",
    )
    assert _bill_invoice_evidence(repo, "Eversource") == [], (
        "no bill/statement wording means it is not an invoice, whatever domain it quotes"
    )


def test_icloud_intake_stores_the_recovered_forwarded_sender(tmp_path):
    """The WIRING, not just the helper: a forwarded message arriving over iCloud must
    be stored with the recovered provenance in its title.

    This is the test the end-to-end matcher test cannot be: the matcher test calls
    `evidence_title` in its own setup, so it keeps passing even if the intake stops
    calling it. Verified by  disabling the helper left the matcher test
    green and only this one red.
    """
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            return [
                IcloudMailMessage(
                    message_id="<fwd1@icloud.com>",
                    subject="Fwd: Your Eversource bill is ready",
                    # Gmail forwarding replaced the sender with the owner's account.
                    sender="Some Owner <owner@gmail.com>",
                    received_at="Sat, 20 Sep 2026 12:00:00 +0000",
                    body_text=_REAL_FORWARD,
                    thread_id="<fwd1@icloud.com>",
                )
            ]

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    summary = ingest_icloud_recent(transport=FakeTransport(), evidence_repo=repo, max_messages=5, blob_store=_ingest_store(tmp_path))
    assert summary["stored"] == 1

    items = repo.list_items(source_kind="mail", limit=10)
    assert len(items) == 1
    assert "notifications.eversource.com" in (items[0].title or ""), (
        "the intake must carry recovered forwarded provenance into the stored title, or "
        "a forwarded bill can never find its bill"
    )


def test_icloud_intake_leaves_a_normal_subject_unchanged(tmp_path):
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            return [
                IcloudMailMessage(
                    message_id="<plain1@icloud.com>", subject="Your Verizon bill is ready",
                    sender="Verizon <billing@verizon.com>",
                    received_at="Sat, 20 Sep 2026 12:00:00 +0000",
                    body_text="Amount due $101.57", thread_id="<plain1@icloud.com>",
                )
            ]

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    ingest_icloud_recent(transport=FakeTransport(), evidence_repo=repo, max_messages=5, blob_store=_ingest_store(tmp_path))
    assert repo.list_items(source_kind="mail", limit=10)[0].title == "Your Verizon bill is ready"


# --- iCloud IMAP must be time-bounded (OS-067) -------------------------------------
#
# Measured 2026-09-20: the evidence poll produced NO log line and wrote NO blobs for
# 7+ minutes. imaplib.IMAP4_SSL() with no timeout leaves the socket open forever, and the
# poll runs on a daemon thread whose hang is  so a stalled mail server became
# a silent, permanent failure rather than a visible one.

def test_the_icloud_transport_defaults_to_a_bounded_socket_timeout():
    from meridian.connectors.icloud_mail import (
        IMAP_TIMEOUT_SECONDS,
        IcloudMailTransport,
    )

    assert IMAP_TIMEOUT_SECONDS > 0, "an unbounded IMAP timeout is what caused the silent hang"
    transport = IcloudMailTransport(username="a@example.com", app_password="x")
    assert transport._socket_timeout == IMAP_TIMEOUT_SECONDS


def test_the_timeout_is_actually_passed_to_imaplib():
    """The default must reach IMAP4_SSL, not just exist as an attribute."""
    from meridian.connectors.icloud_mail import IcloudMailTransport

    calls = {}

    class FakeIMAP:
        def __init__(self, host, port, timeout=None):
            calls["host"], calls["port"], calls["timeout"] = host, port, timeout

        def login(self, user, password):
            return "OK"

    transport = IcloudMailTransport(username="a@example.com", app_password="x")
    transport._imaplib = type("M", (), {"IMAP4_SSL": FakeIMAP})
    transport._connect()
    assert calls.get("timeout"), "IMAP4_SSL must receive a timeout, or a stall hangs forever"


def test_an_unreachable_mail_host_fails_instead_of_hanging():
    """A short timeout must produce a failure, not an indefinite wait."""
    import time

    from meridian.connectors.icloud_mail import IcloudMailReadError, IcloudMailTransport

    # A SHORT explicit timeout on purpose: using the 60s default made this test block
    # for a minute on some networks, which is worse than the bug it guards.
    transport = IcloudMailTransport(
        username="a@example.com", app_password="x",
        host="10.255.255.1", port=993, socket_timeout=2,
    )
    start = time.monotonic()
    try:
        transport._connect()
    except IcloudMailReadError:
        pass
    else:
        raise AssertionError("an unreachable host must not appear to connect")
    elapsed = time.monotonic() - start
    # Generous relative to a 2s socket timeout, but still bounded: the point is that it
    # FINISHES rather than hanging indefinitely.
    assert elapsed < 30, f"the attempt must be bounded by the timeout (took {elapsed:.1f}s)"


# --- the mailbox selector (OS-067) --------------------------------------------------
#
# The inbox is the wrong place to read once mail is FORWARDED in: measured 2026-09-20 it
# held 28,393 messages from 127 distinct senders, and the intake stores every message
# with a body as evidence, so personal mail became Meridian evidence and diluted the
# bill matcher.

def test_the_icloud_intake_defaults_to_the_inbox_for_backward_compatibility():
    import inspect

    from meridian.connectors.icloud_mail import IcloudMailTransport

    sig = inspect.signature(IcloudMailTransport.fetch_recent)
    assert sig.parameters["mailbox"].default == "INBOX"


def test_an_explicit_mailbox_is_the_one_selected():
    """The chosen folder must reach IMAP select(), not be ignored."""
    from meridian.connectors.icloud_mail import IcloudMailTransport

    selected: list[tuple] = []

    class FakeConn:
        def select(self, mailbox, readonly=False):
            selected.append((mailbox, readonly))
            return "OK", [b"0"]

        def search(self, charset, criteria):
            return "OK", [b""]

        def close(self):
            return "OK", []

        def logout(self):
            return "OK", []

    transport = IcloudMailTransport(username="a@example.com", app_password="x")
    transport._connect = lambda: FakeConn()
    transport.fetch_recent(max_results=5, mailbox="Bills")
    assert selected, "select() must be called"
    assert selected[0][0] == "Bills", f"expected the Bills folder, got {selected[0][0]!r}"
    assert selected[0][1] is True, "the folder must be opened READ-ONLY, never mutating"


def test_a_missing_folder_raises_rather_than_silently_reading_the_inbox():
    """Failing loudly is the point: silently falling back to INBOX would ingest personal
    mail, which is the exact outcome this selector exists to prevent."""
    from meridian.connectors.icloud_mail import IcloudMailReadError, IcloudMailTransport

    class FakeConn:
        def select(self, mailbox, readonly=False):
            return "NO", [b"Mailbox does not exist"]

    transport = IcloudMailTransport(username="a@example.com", app_password="x")
    transport._connect = lambda: FakeConn()
    try:
        transport.fetch_recent(max_results=5, mailbox="Nonexistent")
    except IcloudMailReadError as exc:
        assert "Nonexistent" in str(exc)
    else:
        raise AssertionError("a missing folder must raise, not fall back to the inbox")


def test_the_intake_threads_the_mailbox_to_the_transport(tmp_path):
    from meridian.connectors.icloud_mail import IcloudMailMessage
    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent

    seen = {}

    class FakeTransport:
        def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
            seen["mailbox"] = mailbox
            return [
                IcloudMailMessage(
                    message_id="<b1@icloud.com>", subject="Your Xfinity bill is ready",
                    sender="Xfinity <billing@xfinity.com>",
                    received_at="Sat, 20 Sep 2026 12:00:00 +0000",
                    body_text="Amount due $93.00", thread_id="<b1@icloud.com>",
                )
            ]

    repo = EvidenceRepository(str(tmp_path / "evidence.db"))
    ingest_icloud_recent(
        transport=FakeTransport(), evidence_repo=repo, max_messages=5, mailbox="Bills"
    )
    assert seen.get("mailbox") == "Bills", "the intake must pass the mailbox through"


# --- read-only enforcement (OS-067) -------------------------------------------------
#
# The connector always selected with readonly=True, but on 2026-09-20 an ad-hoc probe
# bypassed the class, used raw imaplib with write access, and appended a sieve rule INTO
# the owner's INBOX as a real message. The class was never the weak point; the weak point
# was that nothing made the read-only expectation explicit and checkable.

def test_mutating_imap_commands_are_refused():
    from meridian.connectors.icloud_mail import IcloudMailReadError, IcloudMailTransport

    for command in ("APPEND", "store", "create", "expunge", "copy", "move", "rename"):
        try:
            IcloudMailTransport.assert_read_only_command(command)
        except IcloudMailReadError:
            continue
        raise AssertionError(f"{command!r} must be refused: this transport is read-only")


def test_read_commands_are_allowed():
    from meridian.connectors.icloud_mail import IcloudMailTransport

    for command in ("SELECT", "SEARCH", "FETCH", "LIST", "NOOP", "CLOSE", "LOGOUT"):
        IcloudMailTransport.assert_read_only_command(command)


def test_the_read_only_command_list_covers_every_mutating_verb():
    from meridian.connectors.icloud_mail import IcloudMailTransport

    # APPEND is the one that actually caused the damage, so it is pinned explicitly.
    assert "append" in IcloudMailTransport.IMAP_READ_ONLY_COMMANDS
    assert "store" in IcloudMailTransport.IMAP_READ_ONLY_COMMANDS
    assert "expunge" in IcloudMailTransport.IMAP_READ_ONLY_COMMANDS


def test_a_real_fetch_issues_only_read_only_imap_operations():
    """Behavioral, not textual: run a full fetch against a recording fake and assert no
    mutating IMAP verb was ever issued.

    An earlier version of this test grepped the module source for ".append(" and failed on
    the module's own docstring and on ordinary list appends — a brittle check that proved
    nothing about what happens on the wire. This drives the code instead.
    """
    from meridian.connectors.icloud_mail import IcloudMailTransport

    issued: list[str] = []

    raw = (
        b"Message-ID: <ro@example.com>\r\n"
        b"Subject: Your Xfinity bill is ready\r\n"
        b"From: Xfinity <billing@xfinity.com>\r\n"
        b"Date: Sat, 20 Sep 2026 12:00:00 +0000\r\n"
        b"Content-Type: text/plain\r\n\r\nAmount due $93.00\r\n"
    )

    class FakeConn:
        def select(self, mailbox, readonly=False):
            issued.append("select")
            assert readonly is True, "select must be read-only"
            return "OK", [b"1"]

        def search(self, charset, criteria):
            issued.append("search")
            return "OK", [b"1"]

        def fetch(self, num, spec):
            issued.append("fetch")
            return "OK", [(b"1 (RFC822 {1})", raw)]

        def close(self):
            issued.append("close")
            return "OK", []

        def logout(self):
            issued.append("logout")
            return "OK", []

        # Any mutating verb is recorded and fails loudly.
        def append(self, *a, **k):
            issued.append("append")
            raise AssertionError("the transport must never APPEND")

        def store(self, *a, **k):
            issued.append("store")
            raise AssertionError("the transport must never STORE flags")

        def expunge(self, *a, **k):
            issued.append("expunge")
            raise AssertionError("the transport must never EXPUNGE")

        def create(self, *a, **k):
            issued.append("create")
            raise AssertionError("the transport must never CREATE mailboxes")

    transport = IcloudMailTransport(username="a@example.com", app_password="x")
    transport._connect = lambda: FakeConn()
    messages = transport.fetch_recent(max_results=5, mailbox="Bills")

    assert len(messages) == 1, "the read path should still work"
    mutating = set(issued) & IcloudMailTransport.IMAP_READ_ONLY_COMMANDS
    assert not mutating, f"mutating IMAP commands were issued: {sorted(mutating)}"
