"""Tests for the semi-regular evidence polling service.

The point of this service is that the owner should not have to request a backfill
by hand. Two properties are load-bearing and are pinned hardest here: it must not
stack overlapping provider calls, and it must report a VERIFIED blob delta rather
than trusting an intake summary that can say "stored" while writing no content.
"""

import threading
import time

from meridian.evidence_refresh import (
    MIN_INTERVAL_SECONDS,
    EvidenceRefreshService,
    count_stored_blobs,
    run_evidence_cycle,
)

# --- the provider-load floor ------------------------------------------------------

def test_rejects_an_interval_that_would_hammer_the_provider():
    try:
        EvidenceRefreshService(lambda: {}, interval_seconds=60)
    except ValueError:
        return
    raise AssertionError("must reject intervals under the provider-poll floor")


def test_the_floor_is_much_slower_than_the_graph_refresh():
    # A graph sync is a cheap local reconcile (15s); this makes authenticated network
    # calls to Google, so it must be materially slower.
    assert MIN_INTERVAL_SECONDS >= 300


def test_accepts_the_default_interval():
    service = EvidenceRefreshService(lambda: {}, interval_seconds=MIN_INTERVAL_SECONDS)
    assert service.interval_seconds == MIN_INTERVAL_SECONDS


# --- verified blob delta (the anti-silent-failure property) -----------------------

def test_a_cycle_reports_the_observed_blob_delta_not_the_intake_claim():
    blobs = {"n": 0}

    def run_once():
        # The intake claims two stored items but writes no blob, which is exactly the
        # live failure mode: metadata rows without content.
        blobs["n"] += 0
        return {"outcome": "ok", "total_stored": 2}

    service = EvidenceRefreshService(
        run_once, interval_seconds=MIN_INTERVAL_SECONDS, blob_count=lambda: blobs["n"]
    )
    report = service.refresh_once()
    assert report["total_stored"] == 2, "the intake's own claim is still reported"
    assert report["blobs_written"] == 0, "…but the verified write count must be 0"
    assert report["blobs_before"] == 0 and report["blobs_after"] == 0


def test_blob_delta_tracks_a_real_write():
    blobs = {"n": 5}

    def run_once():
        blobs["n"] += 3
        return {"outcome": "ok", "total_stored": 3}

    service = EvidenceRefreshService(
        run_once, interval_seconds=MIN_INTERVAL_SECONDS, blob_count=lambda: blobs["n"]
    )
    report = service.refresh_once()
    assert report["blobs_written"] == 3
    assert report["blobs_after"] == 8


def test_run_without_a_blob_counter_still_works():
    service = EvidenceRefreshService(lambda: {"outcome": "ok", "total_stored": 1},
                                     interval_seconds=MIN_INTERVAL_SECONDS)
    report = service.refresh_once()
    assert report["total_stored"] == 1
    assert "blobs_written" not in report, "no counter means no invented number"


# --- single flight -----------------------------------------------------------------

def test_a_second_cycle_is_refused_rather_than_queued():
    started = threading.Event()
    release = threading.Event()

    def slow():
        started.set()
        release.wait(2)
        return {"outcome": "ok", "total_stored": 1}

    service = EvidenceRefreshService(slow, interval_seconds=MIN_INTERVAL_SECONDS)
    first = threading.Thread(target=service.refresh_once)
    first.start()
    assert started.wait(2), "first cycle should start"

    assert service.refresh_once() is None, "a concurrent cycle must be refused"

    release.set()
    first.join(2)
    assert service.cycles_completed == 1


# --- loop resilience ---------------------------------------------------------------

def test_a_failing_cycle_is_logged_and_does_not_kill_the_loop():
    logged = []
    calls = {"n": 0}

    def boom():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("provider exploded")
        return {"outcome": "ok", "total_stored": 0}

    service = EvidenceRefreshService(
        boom, interval_seconds=MIN_INTERVAL_SECONDS, logger=logged.append
    )
    service.start()
    deadline = time.time() + 5
    while service.cycles_completed < 1 and time.time() < deadline:
        time.sleep(0.02)
    service.stop()
    assert any("failed" in line for line in logged), f"expected a failure log, got {logged}"


def test_stop_is_idempotent_and_safe_before_start():
    service = EvidenceRefreshService(lambda: {}, interval_seconds=MIN_INTERVAL_SECONDS)
    service.stop()
    service.stop()


# --- the operator line -------------------------------------------------------------

def test_the_log_line_carries_the_blob_evidence():
    line = EvidenceRefreshService._describe(
        {"total_stored": 4, "total_fetched": 9, "blobs_before": 10, "blobs_after": 14,
         "blobs_written": 4, "outcome": "ok"}
    )
    assert "stored=4" in line and "blobs_written=4" in line and "blobs_total=14" in line


def test_the_log_line_omits_figures_it_does_not_have():
    line = EvidenceRefreshService._describe({"outcome": "ok"})
    assert "stored=" not in line and "blobs_written=" not in line


# --- blob counting -----------------------------------------------------------------

def test_counting_blobs_treats_a_missing_root_as_zero(tmp_path):
    assert count_stored_blobs(tmp_path / "nope") == 0


def test_counting_blobs_counts_files_only(tmp_path):
    (tmp_path / "a").write_bytes(b"x")
    (tmp_path / "b").write_bytes(b"y")
    (tmp_path / "subdir").mkdir()
    assert count_stored_blobs(tmp_path) == 2


# --- the cycle wrapper -------------------------------------------------------------

def test_cycle_reports_an_icloud_failure_without_losing_the_gmail_result(monkeypatch):
    import meridian.gmail_intake as intake

    monkeypatch.setattr(
        intake, "ingest_all_gmail_accounts",
        lambda **kwargs: {"accounts": [], "total_fetched": 3, "total_stored": 3},
    )

    def broken_icloud():
        raise RuntimeError("icloud down")

    report = run_evidence_cycle(
        db_path=":memory:", evidence_repo=object(), token_client=object(),
        blob_store=object(), icloud=broken_icloud,
    )
    assert report["total_stored"] == 3, "a mail result must survive an iCloud failure"
    assert report["icloud"]["outcome"] == "error"


def test_cycle_passes_the_wider_window_and_the_blob_store(monkeypatch):
    import meridian.gmail_intake as intake

    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        return {"accounts": [], "total_fetched": 0, "total_stored": 0}

    monkeypatch.setattr(intake, "ingest_all_gmail_accounts", fake)
    blob_store = object()
    run_evidence_cycle(
        db_path=":memory:", evidence_repo=object(), token_client=object(),
        blob_store=blob_store, since_days=45,
    )
    assert seen["since_days"] == 45, "a cycle must reach beyond the manual route's window"
    assert seen["blob_store"] is blob_store, (
        "the blob store must reach the intake, or content is never persisted"
    )


# --- credential health (OS-067: the signal that was missing for 14 days) -----------
#
# A stored authorization saying "connected" is NOT evidence that its token works. The
# live case: the Connections UI showed Gmail "Connected" while all four Gmail refresh
# tokens had been failing with HTTP 400 for days. Polling is the only place a token is
# actually exercised, so it owns this signal.

def _service(**kwargs):
    return EvidenceRefreshService(lambda: {"outcome": "ok"}, interval_seconds=MIN_INTERVAL_SECONDS, **kwargs)


def test_no_health_is_claimed_before_any_attempt():
    # Empty until a cycle really tried a credential, so a verdict can never be invented
    # from a saved authorization record.
    assert _service().credential_health() == {}


def test_a_failure_is_recorded_as_unavailable_with_an_actionable_reason():
    service = _service()
    service.record_credential_failure("gmail", "Google token refresh failed (HTTP 400)")
    health = service.credential_health()
    assert health["gmail"]["available"] is False
    assert health["gmail"]["reason"] == "reauthorize_required"


def test_an_invalid_grant_is_also_reauthorize_required():
    service = _service()
    service.record_credential_failure("gmail", "oauth error: invalid_grant")
    assert service.credential_health()["gmail"]["reason"] == "reauthorize_required"


def test_rejected_and_unreachable_are_distinguished():
    service = _service()
    service.record_credential_failure("gmail", "HTTP 401 unauthorized")
    assert service.credential_health()["gmail"]["reason"] == "authorization_rejected"
    service.record_credential_failure("icloud", "connection timed out")
    assert service.credential_health()["icloud"]["reason"] == "provider_unreachable"


def test_an_unrecognised_failure_is_not_labelled_confidently():
    # Conservative by design: never claim a cause we cannot identify.
    service = _service()
    service.record_credential_failure("gmail", "something novel went wrong")
    assert service.credential_health()["gmail"]["reason"] == "unavailable"


def test_stored_detail_is_bounded_and_single_line():
    # Error strings can echo a provider response body, so keep the first line and cap it.
    service = _service()
    service.record_credential_failure("gmail", "line one\n" + "x" * 5000)
    detail = service.credential_health()["gmail"]["detail"]
    assert "\n" not in detail
    assert len(detail) <= 200


def test_a_successful_use_clears_the_failure():
    service = _service()
    service.record_credential_failure("gmail", "HTTP 400")
    assert "gmail" in service.credential_health()
    service.record_credential_success("gmail")
    assert "gmail" not in service.credential_health()


def test_credentials_are_tracked_independently():
    service = _service()
    service.record_credential_failure("gmail", "HTTP 400")
    service.record_credential_failure("icloud", "timed out")
    service.record_credential_success("icloud")
    health = service.credential_health()
    assert "gmail" in health and "icloud" not in health


def test_the_health_snapshot_cannot_mutate_service_state():
    service = _service()
    service.record_credential_failure("gmail", "HTTP 400")
    snapshot = service.credential_health()
    snapshot["gmail"]["reason"] = "tampered"
    snapshot["injected"] = {"kind": "injected"}
    fresh = service.credential_health()
    assert fresh["gmail"]["reason"] == "reauthorize_required"
    assert "injected" not in fresh


# --- per-account resilience (one dead token must not hide the others) ---------------

def test_one_bad_account_does_not_abort_the_others(monkeypatch):
    import meridian.connectors.google_auth as google_auth
    import meridian.gmail_intake as intake

    class _Store:
        def __init__(self, _db): pass
        def list_accounts(self, kind): return [{"account_email": "a@x"}, {"account_email": "b@x"}]
        def get(self, kind, account_email): return {"access_token": "t", "refresh_token": "r"}

    monkeypatch.setattr(google_auth, "OAuthTokenStore", _Store)
    calls = {"n": 0}

    def fake_recent(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("Google token refresh failed (HTTP 400)")
        return {"fetched": 3, "stored": 3}

    monkeypatch.setattr(intake, "ingest_gmail_recent", fake_recent)
    errors = []
    summary = intake.ingest_all_gmail_accounts(
        db_path=":memory:", evidence_repo=object(), token_client=object(),
        on_account_error=lambda email, exc: errors.append((email, str(exc))),
    )
    assert summary["accounts_unavailable"] == 1
    assert summary["total_stored"] == 3, "the healthy account must still be ingested"
    assert len(errors) == 1 and "HTTP 400" in errors[0][1]


def test_a_reporting_callback_error_does_not_break_intake(monkeypatch):
    import meridian.connectors.google_auth as google_auth
    import meridian.gmail_intake as intake

    class _Store:
        def __init__(self, _db): pass
        def list_accounts(self, kind): return [{"account_email": "a@x"}]
        def get(self, kind, account_email): return {"access_token": "t", "refresh_token": "r"}

    monkeypatch.setattr(google_auth, "OAuthTokenStore", _Store)

    def boom(**kwargs):
        raise RuntimeError("dead")

    monkeypatch.setattr(intake, "ingest_gmail_recent", boom)

    def bad_callback(_email, _exc):
        raise ValueError("callback itself is broken")

    summary = intake.ingest_all_gmail_accounts(
        db_path=":memory:", evidence_repo=object(), token_client=object(),
        on_account_error=bad_callback,
    )
    assert summary["accounts_unavailable"] == 1


# --- health must never block behind a running poll ---------------------------------
#
# Measured 2026-09-20: the Connections page rendered an EMPTY connection list while a
# poll was in flight. The poll held one lock for its whole cycle (100s+ when several
# accounts each fail a token refresh first), and credential_health() waited on that same
#  so the page request, which reads health, blocked behind the poll.
#
# These pin the fix: health has its own lock.

def test_health_can_be_read_while_a_cycle_is_still_running():
    started = threading.Event()
    release = threading.Event()

    def slow_cycle():
        started.set()
        release.wait(5)
        return {"outcome": "ok"}

    service = EvidenceRefreshService(slow_cycle, interval_seconds=MIN_INTERVAL_SECONDS)
    worker = threading.Thread(target=service.refresh_once)
    worker.start()
    assert started.wait(2), "the cycle should be running"

    # The page path. It must return promptly, not wait for the cycle to finish.
    result: list = []
    reader = threading.Thread(target=lambda: result.append(service.credential_health()))
    reader.start()
    reader.join(2)
    assert not reader.is_alive(), (
        "credential_health() must not block behind a running poll cycle"
    )
    assert result == [{}]

    release.set()
    worker.join(5)


def test_health_writes_do_not_block_behind_a_cycle_either():
    started = threading.Event()
    release = threading.Event()

    def slow_cycle():
        started.set()
        release.wait(5)
        return {"outcome": "ok"}

    service = EvidenceRefreshService(slow_cycle, interval_seconds=MIN_INTERVAL_SECONDS)
    worker = threading.Thread(target=service.refresh_once)
    worker.start()
    assert started.wait(2)

    done = threading.Event()

    def writer():
        service.record_credential_failure("gmail", "HTTP 400")
        done.set()

    writer_thread = threading.Thread(target=writer)
    writer_thread.start()
    assert done.wait(2), "recording a failure must not block behind a running cycle"
    assert service.credential_health()["gmail"]["reason"] == "reauthorize_required"

    release.set()
    worker.join(5)
