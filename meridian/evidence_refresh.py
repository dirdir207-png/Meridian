"""Semi-regular evidence polling.

Gmail (and optionally iCloud) evidence was previously manual-only: the owner had to
POST ``/api/meridian/gmail/intake`` by hand to get anything new, which defeats the
purpose of an evidence store. This runs the same read-only intake on an interval so
evidence stays current without a harness request.

Three properties matter more than the schedule:

1. **It is read-only at the provider.** The transports only fetch messages; nothing
   here sends, labels, archives, deletes or mutates provider state. This never touches
   a financial write path and holds no approval authority.
2. **It reports what it OBSERVED, not what it attempted.** ``ingest_record`` swallows
   blob-write failures (``except Exception: pass``), so a run can report
   ``stored/duplicate`` while writing no content — which is how the live store ended up
   with 732 metadata rows and zero blobs. Every cycle therefore counts the blob store
   before and after and reports the delta, so "ingested" can never silently mean
   "metadata only".
3. **One cycle at a time.** A tick that overruns the interval must not stack up
   overlapping provider calls, so the loop waits on a stop event and re-entrancy is
   refused rather than queued.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

DEFAULT_INTERVAL_SECONDS = 1800
DEFAULT_SINCE_DAYS = 45
DEFAULT_MAX_MESSAGES = 50

# Provider polling cannot run faster than this. It is deliberately much slower than
# the Crew graph refresh (15s): a graph sync is a cheap local reconcile, whereas this
# makes real authenticated network calls to Google, and hammering it would risk
# throttling the owner's own account.
MIN_INTERVAL_SECONDS = 300


def count_stored_blobs(root: str | Path) -> int:
    """Count content blobs actually persisted under ``root``.

    Returns 0 when the root does not exist yet, which is the honest reading of "no
    content is stored" rather than an error. Counting files, not bytes, because the
    question this answers is "how many documents could the viewer open?".
    """
    try:
        return sum(1 for path in Path(root).iterdir() if path.is_file())
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
        return 0


class EvidenceRefreshService:
    """Run the read-only evidence intake loop in a background daemon thread.

    - ``run_once``: zero-arg callable returning a report dict (or None). It owns the
      provider calls, so this class never needs to know about transports or tokens.
    - ``interval_seconds``: how often to poll. Clamped to ``MIN_INTERVAL_SECONDS``.
    - ``blob_count``: zero-arg callable returning the number of stored blobs, used to
      report a VERIFIED delta per cycle instead of trusting the intake's own summary.

    Each tick is best-effort: a failure is logged and the loop continues. A failed
    cycle leaves previously stored evidence untouched.
    """

    def __init__(
        self,
        run_once: Callable[[], Optional[dict]],
        *,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        blob_count: Optional[Callable[[], int]] = None,
        logger: Optional[Callable[[str], None]] = None,
    ):
        if interval_seconds < MIN_INTERVAL_SECONDS:
            raise ValueError(
                f"evidence poll interval must be at least {MIN_INTERVAL_SECONDS} seconds"
            )
        self._run_once = run_once
        self._interval_seconds = interval_seconds
        self._blob_count = blob_count
        self._logger = logger or (lambda _: None)
        self._lock = threading.Lock()
        # Health has its OWN lock, deliberately. `_lock` guards the single-flight
        # invariant and is held for the WHOLE cycle (over 100s when several accounts must
        # each fail a token refresh before the mail fetch runs). Reading health through
        # that lock made a Connections page request block behind a running poll —
        # measured 2026-09-20, the page hung long enough to render an empty connection
        # list while a poll was in flight. Health is a small independent structure, so it
        # gets its own lock and can always be read immediately.
        self._health_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._cycles = 0
        self._last_report: Optional[dict] = None
        self._credential_health: dict[str, dict] = {}

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds

    @property
    def cycles_completed(self) -> int:
        return self._cycles

    @property
    def last_report(self) -> Optional[dict]:
        return self._last_report

    # --- credential health ---------------------------------------------------------
    # A stored authorization saying "connected" is NOT evidence that its token still
    # works. Measured 2026-09-20: the Connections UI showed Gmail "Connected" while all
    # four Gmail refresh tokens had been failing with HTTP 400 for days, because the
    # payload read the AUTHORIZATION record rather than the credential. Polling is the
    # one place that actually exercises a token, so it owns this signal.

    def record_credential_failure(self, kind: str, detail: str) -> None:
        """Record that a token could not be used, so the UI stops claiming it works."""
        with self._health_lock:
            self._credential_health[kind] = {
                "kind": kind,
                "available": False,
                "reason": self._classify_credential_error(detail),
                "detail": self._safe_detail(detail),
                "observed_at": datetime.now(timezone.utc).isoformat(),
            }

    def record_credential_success(self, kind: str) -> None:
        """A token was used successfully; clear any prior failure for that kind."""
        with self._health_lock:
            self._credential_health.pop(kind, None)

    def credential_health(self) -> dict[str, dict]:
        """Per-kind credential findings from real poll attempts.

        Returns a copy so callers cannot mutate the service's state. Uses its own
        lock, so a request can read health while a poll cycle is still running
        rather than blocking behind it.
        """
        with self._health_lock:
            return {kind: dict(value) for kind, value in self._credential_health.items()}

    @staticmethod
    def _safe_detail(detail: str) -> str:
        """Bound the stored text.

        Error strings can echo a provider response body, so keep the first line and cap
        the length rather than persisting whatever arrives.
        """
        first = (detail or "").splitlines()[0] if detail else ""
        return first[:200]

    @staticmethod
    def _classify_credential_error(detail: str) -> str:
        """Turn a provider error into a reason the owner can act on.

        Deliberately conservative: an unrecognised failure stays "unavailable" with a
        generic reason rather than being labelled as something it might not be.
        """
        text = (detail or "").lower()
        if "http 400" in text or "invalid_grant" in text:
            return "reauthorize_required"
        if "http 401" in text or "http 403" in text:
            return "authorization_rejected"
        if "timeout" in text or "timed out" in text:
            return "provider_unreachable"
        return "unavailable"

    def refresh_once(self) -> Optional[dict]:
        """Single-flight: refuse rather than queue a concurrent cycle.

        Returns the report, or None when another cycle already holds the lock. A
        queued second call would double the provider load for no gain, so the honest
        answer is "already running".
        """
        if not self._lock.acquire(blocking=False):
            self._logger("meridian evidence poll skipped: a cycle is already running")
            return None
        try:
            before = self._blob_count() if self._blob_count else None
            report = self._run_once()
            after = self._blob_count() if self._blob_count else None
            if report is not None and before is not None and after is not None:
                report = {**report, "blobs_before": before, "blobs_after": after,
                          "blobs_written": after - before}
            self._cycles += 1
            self._last_report = report
            return report
        finally:
            self._lock.release()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                report = self.refresh_once()
                if report is not None:
                    self._logger(self._describe(report))
            except Exception as exc:  # noqa: BLE001 - never kill the loop
                self._logger(
                    f"meridian evidence poll failed: {type(exc).__name__}: {exc}"
                )
            self._stop.wait(self._interval_seconds)
    @staticmethod
    def _describe(report: dict) -> str:
        """One line an operator can act on; the blob delta is the load-bearing part."""
        parts = ["meridian evidence poll"]
        if "total_stored" in report:
            parts.append(f"stored={report['total_stored']}")
        if "total_fetched" in report:
            parts.append(f"fetched={report['total_fetched']}")
        if report.get("blobs_written") is not None:
            parts.append(f"blobs_written={report['blobs_written']}")
        if report.get("blobs_after") is not None:
            parts.append(f"blobs_total={report['blobs_after']}")
        # Name the folder that was read. The inbox is the default, so without this an
        # operator cannot tell a correctly-targeted cycle from one silently reading the
        # wrong mailbox — the failure this selector exists to prevent.
        if report.get("icloud_mailbox"):
            parts.append(f"mailbox={report['icloud_mailbox']}")
        if report.get("outcome"):
            parts.append(f"outcome={report['outcome']}")
        return " ".join(parts)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="meridian-evidence-poll", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None


def run_evidence_cycle(
    *,
    db_path: str,
    evidence_repo,
    token_client,
    blob_store,
    since_days: int = DEFAULT_SINCE_DAYS,
    max_messages_per_account: int = DEFAULT_MAX_MESSAGES,
    icloud: Optional[Callable[[], dict]] = None,
    on_credential_error: Optional[Callable[[str, str], None]] = None,
    on_credential_ok: Optional[Callable[[str], None]] = None,
) -> dict:
    """One evidence cycle: Gmail from every account, then optional iCloud.

    ``since_days`` defaults wider than the manual route's 30 so a cycle reaches mail
    the previous narrower window would have skipped; the manual route is left alone so
    its behaviour does not change as a side effect of adding polling.

    ``on_credential_error(kind, detail)`` / ``on_credential_ok(kind)`` let the calling
    service turn a real auth attempt into a health signal, which is the only way the UI
    can learn that a stored token no longer works (a saved authorization always looks
    "connected" regardless).
    """
    from .gmail_intake import ingest_all_gmail_accounts

    def _account_failed(_email, exc):
        if on_credential_error is not None:
            on_credential_error("gmail", str(exc))

    summary = ingest_all_gmail_accounts(
        db_path=db_path,
        evidence_repo=evidence_repo,
        token_client=token_client,
        max_messages_per_account=max_messages_per_account,
        since_days=since_days,
        blob_store=blob_store,
        on_account_error=_account_failed,
    )
    if on_credential_ok is not None and int(summary.get("accounts_unavailable", 0)) == 0:
        # Only clear the signal when a cycle actually authenticated; a cycle with no
        # accounts at all is not evidence that a credential recovered.
        if summary.get("accounts"):
            on_credential_ok("gmail")
    report: dict = {
        "outcome": "ok" if not summary.get("accounts_unavailable") else "degraded",
        "since_days": since_days,
        "gmail": summary,
        "total_fetched": summary.get("total_fetched", 0),
        "total_stored": summary.get("total_stored", 0),
        "accounts_unavailable": summary.get("accounts_unavailable", 0),
    }
    if icloud is not None:
        try:
            report["icloud"] = icloud()
        except Exception as exc:  # noqa: BLE001 - Gmail result must survive
            report["icloud"] = {"outcome": "error", "error": type(exc).__name__}
            if on_credential_error is not None:
                on_credential_error("icloud", str(exc))
    # Fold the iCloud leg into the top-level totals. Without this the operator line read
    # "stored=0 fetched=0" on 2026-09-20 while iCloud had in fact ingested the bill that
    # was already sitting in the database — the numbers described only the Gmail leg, so a
    # WORKING cycle logged failure-shaped zeros. A summary that can say "nothing happened"
    # while something happened is worse than no summary at all.
    icloud_result = report.get("icloud")
    if isinstance(icloud_result, dict):
        for source_key, target_key in (("fetched", "total_fetched"), ("stored", "total_stored")):
            value = icloud_result.get(source_key)
            if isinstance(value, int):
                report[target_key] = int(report.get(target_key, 0)) + value
        if icloud_result.get("mailbox"):
            report["icloud_mailbox"] = icloud_result["mailbox"]
    return report
