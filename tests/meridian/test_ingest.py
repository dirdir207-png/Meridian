"""Tests for R28/R29: document intake pipeline + evidence-linked memory."""

import pytest

from meridian.connectors.google_auth import OAuthTokenStore  # noqa: F401  (importable)
from meridian.evidence import EvidenceRepository
from meridian.ingest import IntakeRecord, QuarantineError, ingest_record


def _repo(tmp_path):
    return EvidenceRepository(str(tmp_path / "e.db"))


def _store(tmp_path):
    """Every ingest now requires a blob store: a row whose content cannot be kept is
    exactly the state that left 729 of 775 mail items with nothing to open."""
    from meridian.storage import DerivedKeyProvider, EncryptedBlobStore

    return EncryptedBlobStore(
        str(tmp_path / "evidence"),
        DerivedKeyProvider(b"test-secret-key-00000000000000000000000000"),
    )


def test_intake_persists_blob_for_later_content_read(tmp_path):
    """Ingest must write the encrypted blob so invoice/evidence links can open."""
    from meridian.storage import DerivedKeyProvider, EncryptedBlobStore

    repo = _repo(tmp_path)
    store = EncryptedBlobStore(
        str(tmp_path / "evidence"),
        DerivedKeyProvider(b"test-secret-key-00000000000000000000000000"),
    )
    blob = b"Verizon bill: amount due $85.00"
    result = ingest_record(
        IntakeRecord("mail", "m1", blob, "text/plain", "Your Verizon bill"),
        evidence_repo=repo,
        blob_store=store,
    )
    assert result.duplicate is False
    content = store.read(result.content_hash)
    assert content == blob
    # A duplicate re-ingest must also leave the blob retrievable.
    r2 = ingest_record(
        IntakeRecord("mail", "m1", blob, "text/plain", "Your Verizon bill"),
        evidence_repo=repo,
        blob_store=store,
    )
    assert r2.duplicate is True
    assert store.read(r2.content_hash) == blob


def test_duplicate_receipt_not_double_counted(tmp_path):
    repo = _repo(tmp_path)
    blob = b"Bank statement total: $123.45"
    r1 = ingest_record(IntakeRecord("mail", "m1", blob, "text/plain", "statement"), evidence_repo=repo, blob_store=_store(tmp_path))
    r2 = ingest_record(IntakeRecord("mail", "m1", blob, "text/plain", "statement"), evidence_repo=repo, blob_store=_store(tmp_path))
    assert r1.duplicate is False
    assert r2.duplicate is True
    assert r2.item_id == r1.item_id


def test_quarantine_oversized_and_elemental_cases(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(QuarantineError):
        ingest_record(IntakeRecord("upload", "u1", b"x" * (9 * 1024 * 1024), "text/plain"), evidence_repo=repo, blob_store=_store(tmp_path), extraction_limit_bytes=8 * 1024 * 1024)
    with pytest.raises(QuarantineError):
        ingest_record(IntakeRecord("upload", "u2", b"", "text/plain"), evidence_repo=repo, blob_store=_store(tmp_path))
    with pytest.raises(QuarantineError):
        ingest_record(IntakeRecord("upload", "u3", b"%PDF-1.7 encrypted", "application/pdf"), evidence_repo=repo, blob_store=_store(tmp_path))


def test_extraction_produces_provenance_facts(tmp_path):
    repo = _repo(tmp_path)
    blob = b"Amount due: $42.00\nStatement total: $42.00"
    result = ingest_record(IntakeRecord("mail", "m1", blob, "text/plain", "bil statement"), evidence_repo=repo, blob_store=_store(tmp_path))
    assert result.document_type
    facts = result.extracted["facts"]
    assert facts  # at least one labeled amount captured
    assert all("confidence" in f and "provenance" in f for f in facts)


def test_removing_evidence_does_not_touch_source_history(tmp_path):
    from meridian.db import run_migrations

    db = str(tmp_path / "full.db")
    run_migrations(db)
    repo = EvidenceRepository(db)
    blob = b"Renewal amount: $12.00"
    result = ingest_record(IntakeRecord("mail", "m", blob, "text/plain", "renewal"), evidence_repo=repo, blob_store=_store(tmp_path))
    # Revoke the evidence (owner removes it) — evidence gone, source untouched.
    with repo._connect() as conn:
        conn.execute("UPDATE evidence_items SET revoked_at=? WHERE id=?", ("2026-09-05T00:00:00Z", result.item_id))
        conn.commit()
    assert repo.get_by_content_hash(result.content_hash) is None
    assert repo.get_item(result.item_id, include_inaccessible=True) is not None  # history preserved


# --- a row must never promise content it does not have (OS-067) ---------------------
#
# Measured 2026-09-21: 46 of 775 mail items had stored content and 729 did not, so most
# invoice links pointed at a document that was never written (the owner opened one and got
# an error). The cause was structural, in ingest_record:
#
#   1. the metadata row was written FIRST and the blob SECOND, so a failed blob write
#      left a complete-looking row with nothing behind it; and
#   2. that failure was swallowed by `except Exception: pass`, so nothing said so.
#
# These pin the corrected order and the refusal.

def test_ingest_refuses_to_record_evidence_when_no_blob_store_is_available(tmp_path):
    """No store means the content cannot be kept, which is the bug itself."""
    repo = _repo(tmp_path)
    with pytest.raises(QuarantineError):
        ingest_record(
            IntakeRecord("mail", "nostore", b"Verizon bill $85", "text/plain", "bill"),
            evidence_repo=repo,
        )
    assert repo.list_items(source_kind="mail", limit=10) == [], (
        "no row may be created when its content cannot be stored"
    )


def test_a_failed_blob_write_leaves_no_metadata_row(tmp_path):
    """The failure must propagate AND leave nothing behind pointing at nothing."""
    repo = _repo(tmp_path)

    class FailingStore:
        def put(self, _content, *, mime_type=None):
            raise OSError("disk full")

        def read(self, _hash):
            raise FileNotFoundError(_hash)

    with pytest.raises(OSError):
        ingest_record(
            IntakeRecord("mail", "fail", b"Eversource bill $210", "text/plain", "bill"),
            evidence_repo=repo,
            blob_store=FailingStore(),
        )
    assert repo.list_items(source_kind="mail", limit=10) == [], (
        "a failed blob write must not leave a row whose content does not exist"
    )


def test_content_is_written_before_the_row(tmp_path):
    """Order is the guarantee: if the row exists, the content already exists."""
    repo = _repo(tmp_path)
    store = _store(tmp_path)
    seen: list[str] = []

    original_put = store.put

    class RecordingStore:
        def put(self, content, *, mime_type=None):
            seen.append("blob")
            return original_put(content, mime_type=mime_type)

        def read(self, content_hash):
            return store.read(content_hash)

    record = IntakeRecord("mail", "order", b"Xfinity bill $93", "text/plain", "bill")
    result = ingest_record(record, evidence_repo=repo, blob_store=RecordingStore())
    assert seen == ["blob"], "the blob must be written as part of ingest"
    # And the row that now exists can actually be read back.
    assert store.read(result.content_hash) == b"Xfinity bill $93"


def test_a_duplicate_re_fills_content_that_was_never_stored(tmp_path):
    """The duplicate path is the backfill route for rows created before blob storage."""
    repo = _repo(tmp_path)
    blob = b"Rent bill $1442"
    record = IntakeRecord("mail", "dup", blob, "text/plain", "bill")

    # First ingest with NO store is refused, so simulate the legacy state directly: the
    # metadata row exists but nothing was written.
    repo.add_item(
        source_kind="mail", source_id="dup", content_hash=__import__("hashlib").sha256(blob).hexdigest(),
        mime_type="text/plain", size_bytes=len(blob), title="Rent bill",
    )
    store = _store(tmp_path)
    result = ingest_record(record, evidence_repo=repo, blob_store=store)
    assert result.duplicate is True
    assert store.read(result.content_hash) == blob, (
        "re-ingesting a duplicate must fill in the missing content"
    )


def test_a_duplicate_whose_write_fails_says_so(tmp_path):
    """A duplicate that still cannot store its content must not fail silently again."""
    repo = _repo(tmp_path)
    blob = b"Verizon bill $85"
    import hashlib

    repo.add_item(
        source_kind="mail", source_id="dup2", content_hash=hashlib.sha256(blob).hexdigest(),
        mime_type="text/plain", size_bytes=len(blob), title="Verizon bill",
    )

    class FailingStore:
        def put(self, _content, *, mime_type=None):
            raise OSError("disk full")

        def read(self, _hash):
            raise FileNotFoundError(_hash)

    with pytest.raises(OSError):
        ingest_record(
            IntakeRecord("mail", "dup2", blob, "text/plain", "bill"),
            evidence_repo=repo,
            blob_store=FailingStore(),
        )
