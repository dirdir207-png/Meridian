import sqlite3

import pytest

from crew.session_credentials import (
    CredentialDecryptionError,
    SessionCipher,
    SessionCredential,
    SessionCredentialStore,
)


class StaticKeyProvider:
    def __init__(self, key=b"k" * 32):
        self.key = key

    def get_or_create_key(self):
        return self.key


def credential():
    return SessionCredential(
        cookies=(
            {"name": "crew_session", "value": "opaque-secret", "domain": ".trycrew.com", "path": "/"},
        ),
        expires_at="2026-09-01T00:00:00Z",
    )


def test_cipher_round_trip_and_unique_nonces():
    cipher = SessionCipher(StaticKeyProvider())
    first = cipher.encrypt(credential())
    second = cipher.encrypt(credential())
    assert first.nonce != second.nonce
    assert cipher.decrypt(first) == credential()
    assert cipher.decrypt(second) == credential()


def test_cipher_rejects_tampering_and_wrong_key():
    encrypted = SessionCipher(StaticKeyProvider()).encrypt(credential())
    # Flip the final byte rather than overwriting it. The previous form appended b"x", which is a
    # no-op whenever the ciphertext already ended in 0x78 -- the "tampered" value was then
    # byte-identical to the original, decryption correctly succeeded, and this security test
    # failed roughly one run in 256. Verified by reproduction before the fix.
    flipped = bytes([encrypted.ciphertext[-1] ^ 0x01])
    tampered_bytes = encrypted.ciphertext[:-1] + flipped
    assert tampered_bytes != encrypted.ciphertext, "the tamper must actually change a byte"
    tampered = encrypted.__class__(encrypted.version, encrypted.nonce, tampered_bytes)
    with pytest.raises(CredentialDecryptionError):
        SessionCipher(StaticKeyProvider()).decrypt(tampered)
    with pytest.raises(CredentialDecryptionError):
        SessionCipher(StaticKeyProvider(b"z" * 32)).decrypt(encrypted)


def test_store_persists_ciphertext_not_plaintext(tmp_path):
    db = tmp_path / "credentials.db"
    store = SessionCredentialStore(str(db), SessionCipher(StaticKeyProvider()))
    assert store.load() is None
    store.save(credential())
    assert store.load() == credential()
    raw = db.read_bytes()
    assert b"opaque-secret" not in raw
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT kind, version, nonce, ciphertext FROM crew_credentials").fetchone()
    assert row[0:2] == ("session_v1", 1)
    assert row[2] and row[3]
