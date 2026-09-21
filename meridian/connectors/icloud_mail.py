"""Read-only iCloud Mail transport for evidence intake.

Fetches recent iCloud Mail messages over IMAP using the owner's app-specific
password. iCloud Mail does not use OAuth (unlike Gmail), so this uses the
standard IMAP path the owner enables via Apple's app-specific-password flow
(Apple ID -> Sign-In & Security -> App-Specific Passwords).

READ-ONLY: only SELECTs the inbox, fetches headers + body text, and closes
without logout-mutation. Never sends, deletes, moves, or flags a message.

Credential: ICLOUD_MAIL_USERNAME (the iCloud mailbox, e.g. emilyparker — NOT the
full @icloud.com address) + ICLOUD_MAIL_APP_PASSWORD (the xxxx-xxxx-xxxx-xxxx
app-specific password). Never logged or returned.
"""

from __future__ import annotations

import email
import os
from dataclasses import dataclass
from email.header import decode_header, make_header
from typing import Optional

IMAP_HOST = "imap.mail.me.com"
IMAP_PORT = 993
# Every network operation on the mail socket is bounded by this. Short enough that a
# stalled poll fails visibly within one cycle, long enough for a slow IMAP response.
IMAP_TIMEOUT_SECONDS = 60

DEFAULT_USERNAME = ""  # owner-set via env; never guessed
DEFAULT_APP_PASSWORD = ""


class IcloudMailReadError(RuntimeError):
    """An iCloud Mail read failed; callers decide whether to quarantine or skip."""


@dataclass(frozen=True)
class IcloudMailMessage:
    message_id: str
    subject: str
    sender: str
    received_at: str
    body_text: str
    thread_id: Optional[str] = None


def _decode_header_value(raw: str) -> str:
    """Decode RFC 2047 encoded header text (e.g. '=?UTF-8?Q?...?=')."""
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:  # noqa: BLE001 - header decoding is best-effort
        return raw


def _decode_body(payload: bytes, content_type: str = "text/plain") -> str:
    """Decode a message body (best-effort) to UTF-8 text."""
    try:
        charset = "utf-8"
        # Prefer a charset hint if present.
        return payload.decode(charset, errors="replace")
    except Exception:  # noqa: BLE001
        return payload.decode("utf-8", errors="replace")


def _imap_date(value: str) -> str:
    """Convert an ISO ``YYYY-MM-DD`` date to IMAP ``SINCE`` form ``DD-Mon-YYYY``.

    IMAP SINCE (RFC 3501) expects a day-month-year date like ``07-Aug-2026``;
    passing an ISO date string is rejected by iCloud with an Invalid date format
    error. Falls back to the raw value if it cannot be parsed.
    """
    try:
        from datetime import date

        return date.fromisoformat(value).strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return value


class IcloudMailTransport:
    """Minimal read-only iCloud Mail transport (IMAP, app-specific password).

    READ-ONLY BY CONSTRUCTION, not by convention. The connector only ever selects a
    mailbox with ``readonly=True`` and closes rather than expunges — but on 2026-09-20 an
    ad-hoc probe script bypassed this class, used raw imaplib with write access, and
    appended a sieve rule INTO the owner's INBOX as a real message (later found and
    deleted). The class is not the weak point; the weak point was that nothing stopped a
    caller from reaching the account beyond the class. ``IMAP_READ_ONLY_COMMANDS`` names
    the command family this connector must never issue, and
    ``assert_read_only_command`` exists so a future caller can check itself rather than
    rely on remembering.
    """

    #: IMAP commands that would mutate the mailbox. Reads are EXIMINE/SELECT(readonly),
    #: SEARCH, FETCH, LIST, NOOP, CLOSE, LOGOUT — none of these appear here.
    IMAP_READ_ONLY_COMMANDS = frozenset(
        {"append", "copy", "create", "delete", "expunge", "move", "rename", "store",
         "subscribe", "unsubscribe"}
    )

    def __init__(
        self,
        *,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
        host: str = IMAP_HOST,
        port: int = IMAP_PORT,
        socket_timeout: float = IMAP_TIMEOUT_SECONDS,
    ):
        import imaplib

        self._imaplib = imaplib
        self._username = username or os.environ.get("ICLOUD_MAIL_USERNAME", DEFAULT_USERNAME)
        self._app_password = app_password or os.environ.get(
            "ICLOUD_MAIL_APP_PASSWORD", DEFAULT_APP_PASSWORD
        )
        self._host = host
        self._port = port
        self._socket_timeout = socket_timeout
        if not self._username or not self._app_password:
            raise IcloudMailReadError(
                "iCloud Mail is not configured (set ICLOUD_MAIL_USERNAME and ICLOUD_MAIL_APP_PASSWORD)."
            )

    def _connect(self):
        try:
            # The timeout is not optional: without it a stalled server leaves this socket
            # open forever, and the evidence poll runs on a daemon thread whose hang is
            # invisible — measured 2026-09-20, the poll produced NO log line and wrote NO
            # blobs for 7+ minutes because the connection blocked with no deadline.
            connection = self._imaplib.IMAP4_SSL(
                self._host, self._port, timeout=self._socket_timeout
            )
            connection.login(self._username, self._app_password)
            return connection
        except Exception as exc:  # noqa: BLE001 - login failures are read-blocking
            raise IcloudMailReadError(f"iCloud Mail login failed: {type(exc).__name__}") from exc

    @classmethod
    def assert_read_only_command(cls, command: str) -> None:
        """Refuse a mutating IMAP command before it is issued.

        A guard for CALLERS (probes, scripts) that reach the account directly. It cannot
        police raw imaplib, but it makes the expectation explicit and testable, so the
        "read-only" promise is enforced somewhere rather than assumed everywhere.
        """
        if command.strip().lower() in cls.IMAP_READ_ONLY_COMMANDS:
            raise IcloudMailReadError(
                f"refusing mutating IMAP command {command!r}: this connector is read-only"
            )

    def fetch_recent(
        self,
        *,
        max_results: int = 20,
        since: str | None = None,
        mailbox: str = "INBOX",
    ) -> list[IcloudMailMessage]:
        """Fetch a bounded number of recent messages from ``mailbox`` (read-only).

        When ``since`` (an ISO ``YYYY-MM-DD`` date) is given, restrict the IMAP
        search to messages received on/after that date (``SINCE``), so a backfill
        can pull ~30 days without scanning the whole mailbox. Uses the
        app-specific password; selects the mailbox read-only and closes without any
        mutation.

        ``mailbox`` exists because reading the INBOX was the wrong default once mail
        starts being FORWARDED in. Measured 2026-09-20: the INBOX held 28,393 messages
        from 127 distinct senders — MoneyLion, Spotify, GitHub, marketing — and the
        intake stores each message with a body as evidence, so personal mail became
        Meridian evidence and diluted the bill matcher. Pointing this at a dedicated
        folder (populated by a mail rule) keeps the evidence store to bills.
        """
        connection = self._connect()
        results: list[IcloudMailMessage] = []
        try:
            # SELECT the mailbox in read-only (EXAMINE) to guarantee no mutation.
            status, _data = connection.select(mailbox, readonly=True)
            if status != "OK":
                raise IcloudMailReadError(
                    f"iCloud Mail could not open the mailbox {mailbox!r}"
                )

            search_criteria = f"ALL SINCE {_imap_date(since)}" if since else "ALL"
            status, data = connection.search(None, search_criteria)
            if status != "OK":
                raise IcloudMailReadError(
                    f"iCloud Mail could not search the mailbox {mailbox!r}"
                )
            message_nums = data[0].split() if data and data[0] else []
            # Keep only the most recent max_results (the oldest are dropped).
            recent_nums = message_nums[-max_results:]

            for num in reversed(recent_nums):
                try:
                    status, msg_data = connection.fetch(num, "(RFC822)")
                except Exception as exc:  # noqa: BLE001 - skip unreadable message
                    raise IcloudMailReadError(f"iCloud Mail fetch failed: {type(exc).__name__}") from exc
                if status != "OK" or not msg_data:
                    continue
                for part in msg_data:
                    if not isinstance(part, tuple):
                        continue
                    raw = part[1]
                    message = email.message_from_bytes(raw)
                    subject = _decode_header_value(str(message.get("Subject", "")))
                    sender = _decode_header_value(str(message.get("From", "")))
                    received = str(message.get("Date", ""))
                    body = self._extract_body(message)
                    results.append(
                        IcloudMailMessage(
                            message_id=str(message.get("Message-ID", "")),
                            subject=subject,
                            sender=sender,
                            received_at=received,
                            body_text=body,
                            thread_id=str(message.get("Message-ID", "")),
                        )
                    )
        finally:
            try:
                connection.close()
            except Exception:  # noqa: BLE001 - close is best-effort
                pass
            try:
                connection.logout()
            except Exception:  # noqa: BLE001 - logout is best-effort (no mutation)
                pass
        return results

    @staticmethod
    def _extract_body(message) -> str:
        """Best-effort plain-text body extraction from an email.message."""
        if message.is_multipart():
            chunks = []
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True) or b""
                    chunks.append(_decode_body(payload))
            return "\n".join(chunks) if chunks else ""
        payload = message.get_payload(decode=True) or b""
        return _decode_body(payload)
