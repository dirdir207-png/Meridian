"""Evaluation — what actually happened when a role ran, and whether there is enough of it to say anything.

**Why this module exists.** The roadmap names I.4 as the step that makes the intelligence measurable —
*"Measured usefulness on a real journey, refusal correctness when evidence is missing, citation accuracy, cost
per useful proposal"*. Until 2026-09-25 it existed nowhere: no module, no task id, no artifact. Correctness is
tested per role by adversarial unit tests; usefulness was measured nowhere at all. So an intelligence here could
be provably correct and never proven useful, which is the difference between *reporting* and *evaluating*.

**What it refuses to do, which is most of its value.**

* **It never reports health over an empty set.** Zero runs is `measured: False` with a stated reason, never
  "0 failures" — the empty-set trap that makes a clean dashboard lie.
* **It refuses a verdict below a floor.** `MIN_RUNS_FOR_A_ROLE_VERDICT` is a scale, not a minimum: below it the
  report says *insufficient data*, because "no failures seen in two runs" is not a finding about a role.
* **It does not infer usefulness from correctness.** Citation validity and refusal behaviour are measurable from
  what is recorded; whether a run was *useful to the owner* is not, and this module says so rather than
  substituting a proxy and calling it the thing.
* **It writes nothing.** No table, no column, no upload: it reads `ai_run_records` (which deliberately holds no
  claim text, no model output and no evidence body) and reports. Recording is not authority, and neither is
  measuring — the OS-056 rule binds here: no score from this module may remove, weaken or gate an approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import median
from typing import Iterable, Sequence

from meridian.ai.envelope import ResultStatus, RunRecord
from meridian.ai.run_records import RunRecordStore, StoredRun

#: Below this many runs, a role gets NO verdict — "insufficient data", not "healthy".
#:
#: Chosen as a scale rather than a minimum: the failure mode this guards against is not the one-run case (which
#: is obviously empty) but the five-run case that reports 5/5 ok and reads like evidence. Five is the point at
#: which a *distribution* starts to mean something and a single bad run stops being noise; it is deliberately
#: small because the alternative — a large number nobody reaches — is how a harness stops being run.
MIN_RUNS_FOR_A_ROLE_VERDICT = 5

KNOWN_OUTCOMES = {status.value for status in ResultStatus}


@dataclass(frozen=True)
class Anomaly:
    """One recorded run that contradicts the discipline the envelope claims to enforce."""

    kind: str
    run_id: int
    role: str
    detail: str


@dataclass
class RoleStats:
    role: str
    runs: int = 0
    ok: int = 0
    unavailable: int = 0
    failed: int = 0
    unknown_outcome: int = 0
    runs_citing_evidence: int = 0
    uncited_ok_runs: list[int] = field(default_factory=list)
    durations_ms: list[float] = field(default_factory=list)
    providers: set[str] = field(default_factory=set)
    prompt_versions: set[str] = field(default_factory=set)

    @property
    def refusal_rate(self) -> float | None:
        """Share of runs that ended in a non-ok state. None when there is nothing to divide by."""
        if not self.runs:
            return None
        return (self.unavailable + self.failed) / self.runs

    @property
    def citation_rate(self) -> float | None:
        """Share of runs whose recorded evidence set was non-empty."""
        if not self.runs:
            return None
        return self.runs_citing_evidence / self.runs

    @property
    def median_duration_ms(self) -> float | None:
        return median(self.durations_ms) if self.durations_ms else None

    @property
    def has_verdict(self) -> bool:
        return self.runs >= MIN_RUNS_FOR_A_ROLE_VERDICT

    def verdict(self) -> str:
        if not self.has_verdict:
            return f"insufficient data ({self.runs} of {MIN_RUNS_FOR_A_ROLE_VERDICT} runs) — not evidence of health"
        return (
            f"{self.ok} ok / {self.unavailable} unavailable / {self.failed} failed "
            f"over {self.runs} runs; refusals {self.refusal_rate:.0%}, citing evidence {self.citation_rate:.0%}"
        )


@dataclass
class Report:
    runs_total: int
    window_days: int | None
    by_role: dict[str, RoleStats] = field(default_factory=dict)
    anomalies: list[Anomaly] = field(default_factory=list)
    generated_at: str = ""

    @property
    def measured(self) -> bool:
        """Whether ANY claim about role behaviour can be made from what was recorded."""
        return self.runs_total > 0

    @property
    def refusal_reason(self) -> str | None:
        if self.measured:
            return None
        return (
            "0 runs recorded: nothing is measured here, and this is NOT evidence that the roles are healthy. "
            "An empty result set is the absence of data, not the absence of failures."
        )

    def roles_with_a_verdict(self) -> list[str]:
        return sorted(role for role, stats in self.by_role.items() if stats.has_verdict)

    def roles_without_one(self) -> list[str]:
        return sorted(role for role, stats in self.by_role.items() if not stats.has_verdict)


def _duration_ms(run: StoredRun | RunRecord) -> float | None:
    try:
        started = datetime.fromisoformat(str(run.started_at).replace("Z", "+00:00"))
        ended = datetime.fromisoformat(str(run.ended_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (ended - started).total_seconds() * 1000.0


def evaluate_runs(runs: Iterable[StoredRun | RunRecord], *, window_days: int | None = None) -> Report:
    """Summarise recorded runs. Pure: no clock beyond the stamp, no store, no writes.

    Every anomaly is a CONTRADICTION between what the envelope claims and what was recorded — an `ok` outcome
    with no cited evidence, an outcome outside the enum, a run that ended before it started. They are reported,
    never repaired, because a harness that silently fixes its input measures itself.
    """
    report = Report(
        runs_total=0,
        window_days=window_days,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    for run in runs:
        report.runs_total += 1
        role = str(run.role)
        stats = report.by_role.setdefault(role, RoleStats(role=role))
        stats.runs += 1
        stats.providers.add(str(run.provider))
        stats.prompt_versions.add(str(run.prompt_version))

        outcome = str(run.outcome)
        if outcome == ResultStatus.OK.value:
            stats.ok += 1
        elif outcome == ResultStatus.UNAVAILABLE.value:
            stats.unavailable += 1
        elif outcome == ResultStatus.FAILED.value:
            stats.failed += 1
        else:
            stats.unknown_outcome += 1
            report.anomalies.append(
                Anomaly("unknown_outcome", int(run.id), role,
                        f"outcome {outcome!r} is not one of {sorted(KNOWN_OUTCOMES)}")
            )

        cited = bool(run.evidence_ids)
        if cited:
            stats.runs_citing_evidence += 1
        elif outcome == ResultStatus.OK.value:
            # The envelope refuses an uncited claim inside the result object, so a recorded `ok` with an empty
            # evidence set means either the record or the discipline is wrong. Both are worth knowing.
            stats.uncited_ok_runs.append(int(run.id))
            report.anomalies.append(
                Anomaly("uncited_ok", int(run.id), role,
                        "outcome is ok but the run cites no evidence")
            )

        duration = _duration_ms(run)
        if duration is None:
            report.anomalies.append(
                Anomaly("unparseable_timestamp", int(run.id), role,
                        f"started_at={run.started_at!r} ended_at={run.ended_at!r}")
            )
        elif duration < 0:
            report.anomalies.append(
                Anomaly("negative_duration", int(run.id), role,
                        f"ended {abs(duration):.0f}ms before it started")
            )
        else:
            stats.durations_ms.append(duration)

    return report


def evaluate_store(store: RunRecordStore, *, role: str | None = None, limit: int = 500,
                   window_days: int | None = None) -> Report:
    """Read-only evaluation from the run-record store. The only side effect is a read."""
    return evaluate_runs(store.list_recent(role=role, limit=limit), window_days=window_days)


def same_destination(a: Sequence[str], b: Sequence[str]) -> bool:
    """Kept deliberately trivial and exported for the tests that prove the report is order-independent."""
    return sorted(a) == sorted(b)
