"""Configurable paycheck (funding source) for per-bill funding projections.

Meridian's funding rules (fixed_per_paycheck / percent_of_paycheck) need
future paycheck inflow events to allocate money toward bills. Previously these
came only from detected recurring income transactions; the owner asked for a
way to set a simple or crew-style paycheck explicitly.

This module persists a single paycheck config (cadence, amount, next date) in
``app_config`` and generates dated inflow events that ``build_plan`` feeds into
funding projections. It is read-side planning metadata; it never moves money.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .cadence import advance as cadence_advance
from .cadence import next_occurrence_with_index

_PAYCHECK_KEY = "meridian_paycheck_config"
_VALID_CADENCE = ("weekly", "biweekly", "monthly", "semimonthly")


@dataclass(frozen=True)
class PaycheckConfig:
    cadence: str
    amount: float
    next_date: str  # ISO date of the next paycheck
    active: bool = True

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, raw: str) -> "PaycheckConfig":
        data = json.loads(raw)
        return cls(
            cadence=str(data.get("cadence") or "monthly"),
            amount=float(data.get("amount") or 0),
            next_date=str(data.get("next_date") or ""),
            active=bool(data.get("active", True)),
        )


def _now() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


class PaycheckRepository:
    """Persist the owner's paycheck config in app_config (single user)."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        return conn

    def save(self, config: PaycheckConfig) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO app_config(key, value, created_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (_PAYCHECK_KEY, config.to_json(), _now()),
            )

    def get(self) -> Optional[PaycheckConfig]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_config WHERE key=?", (_PAYCHECK_KEY,)
            ).fetchone()
        if row is None:
            return None
        try:
            return PaycheckConfig.from_json(row[0])
        except (ValueError, TypeError, KeyError):
            return None

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM app_config WHERE key=?", (_PAYCHECK_KEY,))


def _next_after(anchor: date, cadence: str) -> date:
    """Advance ``anchor`` one cadence period.

    Delegates to the shared calendar-aware rule so a monthly paycheck anchored on
    the 31st stays on the 31st and semimonthly means the 15th and month-end,
    rather than drifting under a flat +15 days. An unrecognised cadence keeps the
    previous conservative default (one week).
    """
    advanced = cadence_advance(anchor, cadence)
    if advanced is None:
        return anchor + timedelta(days=7)
    return advanced


def future_paycheck_events(
    config: PaycheckConfig,
    *,
    as_of: date,
    horizon_days: int = 90,
) -> list[tuple[date, float]]:
    """Generate dated paycheck inflow events from ``config.next_date`` onward.

    Returns ``[(date, amount), ...]`` up to ``horizon_days`` ahead, anchored so
    the first entry is the next paycheck >= ``as_of``.
    """
    if not config.active or config.amount <= 0:
        return []
    events: list[tuple[date, float]] = []
    horizon = as_of + timedelta(days=horizon_days)
    anchor = date.fromisoformat(config.next_date)
    events: list[tuple[date, float]] = []
    horizon = as_of + timedelta(days=horizon_days)
    anchor = date.fromisoformat(config.next_date)
    # Anchor-preserving, index-correct walk. Occurrence number k is
    # ``advance(anchor, cadence, k)``, and the walk reports which k it landed on,
    # so every following step is simply the next k. Deriving the next occurrence
    # from ``current`` instead would let a February clamp become the permanent day;
    # guessing the index would skip or repeat a paycheck.
    current, period = next_occurrence_with_index(anchor, config.cadence, as_of)
    while current <= horizon and period <= 400:
        events.append((current, config.amount))
        following = cadence_advance(anchor, config.cadence, period + 1)
        if following is None or following <= current:
            break
        period += 1
        current = following
    return events


def build_cash_events(
    current_cash: float,
    paycheck: Optional[PaycheckConfig],
    *,
    as_of: date,
    horizon_days: int = 90,
) -> list[tuple[date, float]]:
    """Compose the funding cash timeline: current cash + future paychecks."""
    events: list[tuple[date, float]] = []
    if current_cash > 0:
        events.append((as_of, current_cash))
    if paycheck is not None:
        events.extend(future_paycheck_events(paycheck, as_of=as_of, horizon_days=horizon_days))
    return sorted(events, key=lambda item: item[0])


_MAX_EVIDENCE_IDS = 12


@dataclass(frozen=True)
class ResolvedPaycheck:
    """A paycheck projection AND the provenance of its amount.

    Deliberately NOT part of ``PaycheckConfig``. The config is what the owner set and is
    persisted verbatim through ``PaycheckRepository``; ``basis``, ``source``, ``observed_at``
    and ``evidence_ids`` are DERIVED. Folding them into the persisted config would write
    derived provenance to the database and later read it back as though the owner had
    configured it.

    It exposes the same attribute names as ``PaycheckConfig`` (cadence/amount/next_date/
    active) so the dial's ``getattr``-based readers take either one unchanged.

    ``basis`` is not decoration: an aggregate over three observed paychecks and a single
    last-observed value are different strengths of claim, and a consumer that cannot tell
    them apart cannot report the amount honestly.

    ``plan_id`` is the identity of the Crew funding plan when one produced the figure, and
    is ``None`` for every Meridian-derived leg. It is the field that lets a consumer say
    "this is the Crew record" without re-matching on the plan's name.

    ``learning_floor`` is the owner's learning window (OS-051) when it governed a
    LEARNED leg, and ``None`` otherwise. It is provenance for the same reason ``basis``
    is: a learned figure produced from a windowed history must not look like one learned
    from everything, or a reader cannot account for the difference.
    """

    cadence: str
    amount: float
    next_date: str
    active: bool
    basis: str  # "crew_plan" | "aggregate" | "last_known" | "configured"
    source: str
    observed_at: Optional[str] = None
    evidence_ids: tuple = ()
    occurrences: int = 0
    plan_id: Optional[str] = None
    learning_floor: Optional[str] = None


def _income_transactions(transactions):
    return [
        txn
        for txn in transactions or ()
        if str(getattr(txn, "classification_kind", "") or "") == "income"
    ]


def _observed_day(txn) -> Optional[str]:
    raw = str(getattr(txn, "occurred_at", "") or "")
    return raw[:10] if len(raw) >= 10 else None


def _crew_plan_paycheck(plans) -> Optional[ResolvedPaycheck]:
    """The owner's Crew funding plan as the expected paycheck, or None.

    Owner directive, verbatim: *"Right, it SHOULD be a crew record though, the paycheck"*.
    A Crew bill-reserve funding plan IS the owner's "Funding Cadence" (confirmed
    2026-09-19), so this is the FIRST leg of the chain and Meridian's own aggregation is
    the deviation that sits below it -- not above it.

    The plan is the IDENTITY as well as the amount, which is the whole point: the owner
    renames the income source ("State of New Hampshire" -> "Veteran's Home"), so keying on
    the plan record means a rename propagates and nothing depends on the merchant text of a
    deposit, which drifts. ``plan_id`` carries that identity out of here.

    Three deliberate restraints, each a place where a guess would otherwise be reported as
    a fact:

    1. **Exactly one plan, or this leg does not apply.** A plan is money moving INTO one
       reserve, so a family with several reserves can hold several plans that are
       allocations of ONE paycheck rather than competing candidates for it. Picking one
       would understate income and picking the largest would be an invented claim, so with
       more than one observed plan resolution falls through to the observations.
    2. **The schedule is never invented.** Crew's ``frequency``/``frequencyInterval`` is not
       always expressible in Meridian's vocabulary (MONTHLY x2 is not weekly, biweekly,
       monthly, semimonthly or annually). The amount and identity remain Crew facts, but an
       unmappable cadence leaves ``cadence`` empty rather than substituted with something
       Meridian cannot honour.
    3. **No transaction is claimed as evidence.** The plan is a provider RECORD, not a
       deposit, so ``evidence_ids`` stays empty and the provenance is the plan id plus the
       provider read that observed it (``observed_at``).

    ``next_date`` mirrors the established ``last_known`` leg: one cadence period after the
    plan's own ``anchorDate``, without consulting the clock. Consumers already roll a passed
    date forward through the shared anchor-preserving rule, and doing the roll here would
    make the same plan resolve differently at different times of day.
    """
    current = [
        plan for plan in (plans or ()) if float(getattr(plan, "amount", 0) or 0.0) > 0
    ]
    if len(current) != 1:
        return None

    plan = current[0]
    cadence = str(getattr(plan, "cadence", "") or "")
    next_date = ""
    if cadence:
        anchor = str(getattr(plan, "anchor_date", "") or "")
        if anchor:
            try:
                advanced = cadence_advance(date.fromisoformat(anchor), cadence, 1)
            except ValueError:
                advanced = None
            next_date = advanced.isoformat() if advanced else ""

    return ResolvedPaycheck(
        cadence=cadence,
        amount=abs(float(getattr(plan, "amount", 0) or 0.0)),
        next_date=next_date,
        active=True,
        basis="crew_plan",
        source=str(getattr(plan, "name", "") or "") or "Crew funding plan",
        observed_at=str(getattr(plan, "observed_at", "") or "") or None,
        evidence_ids=(),
        plan_id=str(getattr(plan, "external_id", "") or "") or None,
    )


def resolve_expected_paycheck(
    transactions, configured=None, plans=None, learning_floor=None
) -> Optional[ResolvedPaycheck]:
    """The owner's approved rule (2026-09-19, verbatim in docs/project/CURRENT_STATUS.md):

        "it should default to that value and moving forward aggregate after 3"

    The rule is applied to the CURRENT income channel, not to income in general, and that
    distinction is the difference between an honest number and a wrong one. ``learn_paycheck``
    groups by merchant and returns a single source, so calling it across all history would
    happily return a three-occurrence aggregate for a channel the owner has stopped using --
    and that aggregate would then be reported as the expected income. The owner's mechanism
    just changed in exactly that way (paychecks now deposit directly into Crew, where they
    previously arrived as Cash App transfers), so:

      0. the Crew funding plan, when the sync has observed exactly one (``plans``) -- the
         provider RECORD the owner named, which outranks everything Meridian derives;
      1. identify the channel from the MOST RECENTLY observed income transaction;
      2. aggregate WITHIN that channel once it has enough occurrences (``learn_paycheck``
         returns None below ``paycheck_learning._MIN_OCCURRENCES``, so the threshold is the
         existing one rather than a second copy);
      3. otherwise use that channel's last observed value -- "default to that value" --
         but only once the channel has RECURRED (>= 2 observations), because a single
         income transaction is indistinguishable from interest or a refund;
      4. otherwise fall back to the owner's configured figure, which is the last resort.

    Leg 0 was added 2026-09-19 (OS-050) and is ADDITIVE: with no plan observed the chain
    above is exactly the behaviour it had, which is what ``plans=None`` means. It is
    placed first because the owner's model makes the Crew plan the income source itself,
    while the aggregate is explicitly Meridian's own deviation.

    ``learning_floor`` (OS-051) is an ISO date restricting LEGS 1-3, which are the ones
    learned from observations. The owner: "If I change jobs and have a different pay rate,
    or at a different cadence ... I shouldnt be including the learned pay from previous
    positions". So the window is applied BEFORE the channel is identified, which matters:
    picking the channel from the most recent observation and then windowing would let a
    pre-floor deposit still decide which history is aggregated. It never touches leg 0
    (a provider record, not an observation) or the configured figure (an assertion, not a
    learned value), and it deletes nothing -- the excluded observations remain in the
    ledger and become learnable again when the floor is cleared.

    A retired channel therefore cannot win, and two channels are never averaged together,
    because a number averaged across a retired payout route and a new one describes neither.

    Known limitation, stated rather than hidden: with fewer than three observations the AMOUNT
    is observed but the SCHEDULE is not, so the cadence and next date come from the configured
    config when there is one and otherwise from the last observed date advanced by one month.
    ``basis`` describes where the amount came from, not the schedule.
    """
    from .paycheck_learning import learn_paycheck, observations_on_or_after

    plan_resolution = _crew_plan_paycheck(plans)
    if plan_resolution is not None:
        return plan_resolution

    # The window is applied BEFORE the channel is identified, so a pre-floor deposit
    # cannot decide which history is aggregated.
    income = _income_transactions(observations_on_or_after(transactions, learning_floor))

    if income:
        latest = max(income, key=lambda txn: str(getattr(txn, "occurred_at", "") or ""))
        channel = str(getattr(latest, "merchant", "") or "")
        current = [
            txn for txn in income if str(getattr(txn, "merchant", "") or "") == channel
        ]
        learned = learn_paycheck(current)

        if learned:
            days = [day for day in (_observed_day(txn) for txn in current) if day]
            ids = tuple(
                getattr(txn, "id")
                for txn in current[:_MAX_EVIDENCE_IDS]
                if getattr(txn, "id", None) is not None
            )
            return ResolvedPaycheck(
                cadence=str(learned.get("cadence") or "monthly"),
                amount=float(learned.get("amount") or 0.0),
                next_date=str(learned.get("next_date") or ""),
                active=True,
                basis="aggregate",
                source=channel or "manual",
                observed_at=max(days) if days else None,
                evidence_ids=ids,
                occurrences=int(learned.get("occurrences") or 0),
                learning_floor=learning_floor,
            )

        # A FALLBACK ONLY FOR A RECURRING DEPOSIT. Income is not the same thing as a paycheck:
        # on the owner's live ledger the most recent income-classified transaction was a $0.46
        # "Interest paid" credit, and taking it as the "last known source" replaced an expected
        # paycheck of $1,663.00 with 46 cents -- a false statement about money, produced by
        # equating two different things. One observation cannot be told apart from interest,
        # a refund or a one-off, so it is not enough to name a paycheck source. Two is the
        # smallest evidence that a channel RECURS, and anything less falls through to the
        # configured figure, which claims nothing it cannot support.
        if len(current) < 2:
            if configured is not None:
                return ResolvedPaycheck(
                    cadence=str(getattr(configured, "cadence", "") or "monthly"),
                    amount=float(getattr(configured, "amount", 0) or 0.0),
                    next_date=str(getattr(configured, "next_date", "") or ""),
                    active=bool(getattr(configured, "active", True)),
                    basis="configured",
                    source="manual",
                    learning_floor=learning_floor,
                )
            return None

        day = _observed_day(latest)
        cadence = "monthly"
        next_date = ""
        if configured is not None:
            cadence = str(getattr(configured, "cadence", "") or cadence)
            next_date = str(getattr(configured, "next_date", "") or "")
        if not next_date and day:
            try:
                from datetime import date as _date

                advanced = cadence_advance(_date.fromisoformat(day), cadence, 1)
                next_date = advanced.isoformat() if advanced else ""
            except Exception:  # noqa: BLE001 - a malformed date must not block a read
                next_date = ""
        return ResolvedPaycheck(
            cadence=cadence,
            amount=abs(float(getattr(latest, "amount", 0) or 0.0)),
            next_date=next_date,
            active=True,
            basis="last_known",
            source=channel or "manual",
            observed_at=day,
            evidence_ids=(
                (getattr(latest, "id"),)
                if getattr(latest, "id", None) is not None
                else ()
            ),
            occurrences=len(current),
            learning_floor=learning_floor,
        )

    if configured is not None:
        return ResolvedPaycheck(
            cadence=str(getattr(configured, "cadence", "") or "monthly"),
            amount=float(getattr(configured, "amount", 0) or 0.0),
            next_date=str(getattr(configured, "next_date", "") or ""),
            active=bool(getattr(configured, "active", True)),
            basis="configured",
            source="manual",
            learning_floor=learning_floor,
        )

    return None
