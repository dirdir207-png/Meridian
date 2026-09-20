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
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._cycles = 0
        self._last_report: Optional[dict] = None

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds

    @property
    def cycles_completed(self) -> int:
        return self._cycles

    @property
    def last_report(self) -> Optional[dict]:
        return self._last_report

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
) -> dict:
    """One evidence cycle: Gmail from every account, then optional iCloud.

    ``since_days`` defaults wider than the manual route's 30 so a cycle reaches mail
    the previous narrower window would have skipped; the manual route is left alone so
    its behaviour does not change as a side effect of adding polling.
    """
    from .gmail_intake import ingest_all_gmail_accounts

    summary = ingest_all_gmail_accounts(
        db_path=db_path,
        evidence_repo=evidence_repo,
        token_client=token_client,
        max_messages_per_account=max_messages_per_account,
        since_days=since_days,
        blob_store=blob_store,
    )
    report: dict = {
        "outcome": "ok",
        "since_days": since_days,
        "gmail": summary,
        "total_fetched": summary.get("total_fetched", 0),
        "total_stored": summary.get("total_stored", 0),
    }
    if icloud is not None:
        try:
            report["icloud"] = icloud()
        except Exception as exc:  # noqa: BLE001 - Gmail result must survive
            report["icloud"] = {"outcome": "error", "error": type(exc).__name__}
    return report
