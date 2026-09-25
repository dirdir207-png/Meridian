"""One canonical Plan view model: summary, timeline, allocation, commitments."""

from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Sequence

from meridian.beacon import forecast
from meridian.cadence import next_occurrence
from meridian.funding import project_funding
from meridian.funding_repo import FundingRuleRepository
from meridian.services.spend_pocket import is_spend_pocket_name

_HORIZON_DAYS = 30

# Where the live Crew read-only snapshot is written (the opaque GraphQL ids live
# there). Overridable so tests can inject a fixture.
_CREW_SNAPSHOT_PATH = None


def _crew_ids() -> Optional[dict]:
    """Extract the Crew opaque GraphQL ids (account + spend subaccounts) for the UI.

    Reads the live Crew snapshot the sync already produces and returns the ids the
    write forms need: {account_id, checking_subaccount_id, free_to_spend_subaccount_id}.
    None when the snapshot is unavailable or not parseable (the UI then leaves the
    id fields blank and the write routes to a proposal/rejects safely).
    """
    import ast
    import os

    path = _CREW_SNAPSHOT_PATH or os.path.expanduser(
        "~/Library/Application Support/SimpleCrew/live_crew_snapshot.txt"
    )
    try:
        with open(path, encoding="utf-8") as handle:
            payload = ast.literal_eval(handle.read())
    except Exception:  # noqa: BLE001 - snapshot is best-effort context
        return None
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    accounts = None

    def find(o):
        nonlocal accounts
        if isinstance(o, dict):
            if (
                "accounts" in o
                and isinstance(o["accounts"], list)
                and o["accounts"]
                and isinstance(o["accounts"][0], dict)
                and "subaccounts" in o["accounts"][0]
            ):
                accounts = o["accounts"]
                return
            for v in o.values():
                find(v)
        elif isinstance(o, list):
            for x in o:
                find(x)

    find(data)
    result = {}
    user_id = None
    def _user_id(o):
        nonlocal user_id
        if isinstance(o, dict):
            for k, v in o.items():
                if str(k).lower() in ("user", "currentuser") and isinstance(v, dict):
                    uid = v.get("id")
                    if isinstance(uid, str) and uid.startswith("VXNlcjo"):  # User: id
                        user_id = uid
                        return True
                if _user_id(v):
                    return True
        elif isinstance(o, list):
            for x in o:
                if _user_id(x):
                    return True
        return False
    _user_id(data)
    if user_id:
        result["user_id"] = user_id
    subaccounts = []
    seen_sub = set()
    if accounts:
        for acc in accounts:
            name = (acc.get("displayName") or acc.get("name") or "").strip().lower()
            if name == "checking":
                result["account_id"] = acc.get("id")
            for sub in acc.get("subaccounts", []):
                sid = sub.get("id")
                sname = sub.get("displayName") or sub.get("name") or ""
                if name == "checking" and (sname or "").strip().lower() == "checking":
                    result["checking_subaccount_id"] = sid
                if is_spend_pocket_name(sname):
                    result["free_to_spend_subaccount_id"] = sid
                if sid and sid not in seen_sub:
                    seen_sub.add(sid)
                    subaccounts.append({"id": sid, "name": sname or "Pocket"})
    if subaccounts:
        result["subaccounts"] = subaccounts
    # Autopilot rules (id + name) so the UI can edit/delete existing rules.
    rules = []
    for word in ("rules",):
        seen = set()
        def _rules(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if str(k).lower() == word and isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict) and item.get("id"):
                                key = item.get("id")
                                if key in seen:
                                    continue
                                seen.add(key)
                                rules.append({
                                    "id": item.get("id"),
                                    "name": item.get("name") or "Untitled rule",
                                    "is_paused": bool(item.get("isPaused")),
                                    "formula": item.get("formula"),
                                })
                    _rules(v)
            elif isinstance(o, list):
                for x in o:
                    _rules(x)
        _rules(data)
        if rules:
            break
    if rules:
        result["rules"] = rules
    return result or None
_ZERO = Decimal("0")

# Generic words that can appear in a bill name or an email subject but should
# not alone match an invoice (e.g. "payment", "bill", "your"). The invoice
# matcher requires a biller-specific token, not these.
_BILLER_STOPWORDS = {
    "payment",
    "payments",
    "bill",
    "bills",
    "invoice",
    "your",
    "the",
    "for",
    "and",
    "account",
    "arrangement",
    "plan",
    "monthly",
    "due",
    "auto",
    "autopay",
}


def _money(value) -> Decimal:
    return Decimal(str(value)) if value is not None else _ZERO


def _biller_status(commitment, *, last_paid=None) -> str:
    """Subtle per-bill badge for the Plan card (R33). Lazy import avoids a
    module cycle with meridian.billers (which imports commitments + models)."""
    from meridian.billers import bill_status_for

    return bill_status_for(commitment, last_paid_amount=last_paid)


def _sender_host(sender: str | None) -> str:
    """Extract the sender's domain host (e.g. 'customer.verizon.com').

    Handles 'Name <addr@host>' display-name form and a bare 'addr@host'.
    """
    if not sender:
        return ""
    raw = (sender or "").strip()
    if "<" in raw and ">" in raw:
        raw = raw[raw.find("<") + 1 : raw.find(">")]
    raw = raw.split("@")[-1] if "@" in raw else raw
    return raw.lower().strip()


def bill_invoice_link(evidence_repository, bill_name: str) -> Optional[dict]:
    """The ONE invoice a bill's evidence points at, or None.

    This is the public face of `_bill_invoice_evidence`, and it exists because a SECOND surface
    needs the same answer: the Today dial's evidence ticket. The owner asked for its "View bill"
    control to open "the mail ingested invoice we already have attached to the same bill on plan",
    and the only correct way to do that is to ask the same matcher rather than re-implement "what
    counts as this bill's invoice" -- two implementations would drift, and the drift would show up
    as Today opening a marketing email that Plan correctly refuses to call an invoice.

    Returns the first match (the matcher already ranks bill/statement subjects first and refuses
    anything that does not read as a bill), or None when the bill genuinely has no invoice mail.
    """
    matches = _bill_invoice_evidence(evidence_repository, bill_name, limit=1)
    return matches[0] if matches else None


def _bill_invoice_evidence(evidence_repository, bill_name: str, limit: int = 4) -> list[dict]:
    """Find mail evidence that looks like an invoice for a bill (e.g. "Verizon").

    Matches by sender domain (extracted email host) first, then by biller-name
    tokens in the subject. Sender-domain matches that also read as a bill/statement
    ("bill", "statement", "invoice", "payment") rank first; plain marketing from
    the same domain still surfaces but lower. Returns invoice evidence with a
    ``sender``; the UI shows it only when a real email is found.
    """
    if evidence_repository is None or not bill_name:
        return []
    try:
        from meridian.evidence import EvidenceRepository

        if not isinstance(evidence_repository, EvidenceRepository):
            return []
        items = evidence_repository.list_items(source_kind="mail", limit=400)
    except Exception:  # noqa: BLE001 - evidence lookup is best-effort
        return []
    bill_tokens = {
        t
        for t in "".join(c.lower() if c.isalnum() else " " for c in bill_name).split()
        if t and t not in _BILLER_STOPWORDS
    }
    if not bill_tokens:
        return []
    bill_keywords = {"bill", "statement", "invoice", "payment", "autopay", "receipt"}
    matches = []
    seen_ids = set()
    for item in items:
        sender_host = _sender_host(item.sender)
        title = (item.title or "").lower()
        host_tokens = (
            {t for t in "".join(c if c.isalnum() else " " for c in sender_host).split() if t}
            if sender_host
            else set()
        )
        # Domain match: a biller token equals a host label (e.g. verizon, xfinity).
        sender_match = bool(host_tokens & bill_tokens)
        title_tokens = {
            t
            for t in "".join(c if c.isalnum() else " " for c in title).split()
            if t and t not in _BILLER_STOPWORDS
        }
        title_match = bool(bill_tokens & title_tokens)
        if not (sender_match or title_match):
            continue
        if item.id in seen_ids:
            continue
        seen_ids.add(item.id)
        # Bill-keyword detection uses the raw subject (uncensored by stopwords),
        # so "Your Verizon bill is ready" counts as a bill even though "bill" is
        # a stopword for token matching.
        raw_title_tokens = {
            t
            for t in "".join(c if c.isalnum() else " " for c in title).split()
            if t
        }
        is_bill_word = bool(bill_keywords & raw_title_tokens)
        # A subject-only match (no biller-domain signature) is only trustworthy
        # when the subject also reads as a bill/statement. Otherwise a marketing
        # promo that merely mentions the bill name (e.g. "Rent is due, are you
        # covered?") from an unrelated sender would surface as an invoice.
        if not sender_match and not is_bill_word:
            continue
        matches.append(
            {
                "id": item.id,
                "title": item.title or "Invoice",
                "sender": item.sender,
                "mime_type": item.mime_type,
                "content_url": f"/api/meridian/evidence/{item.id}/content",
                "is_bill": is_bill_word,
            }
        )
    # Only real bill/statement emails surface. A sender-domain marketing email
    # (e.g. a Verizon iPhone promo) is NOT an invoice, so it is never shown —
    # the bill simply has no invoice link until a genuine bill/statement email
    # exists in evidence.
    return [m for m in matches if m["is_bill"]][:limit]


def _project_commitment(commitment, rules, cash_events, as_of: date):
    projections = []
    for rule in rules:
        if rule.paused:
            continue
        deadline = None
        for candidate in (
            getattr(commitment, "due_date", None),
            getattr(commitment, "target_date", None),
        ):
            if isinstance(candidate, str) and candidate:
                try:
                    deadline = date.fromisoformat(candidate)
                except ValueError:
                    deadline = None
            elif isinstance(candidate, date):
                deadline = candidate
        horizon_end = rule.horizon_end or (as_of + timedelta(days=_HORIZON_DAYS))
        if deadline and deadline < horizon_end:
            horizon_end = deadline
        projection = project_funding(
            rule,
            commitment,
            cash_events,
            as_of=as_of,
        )
        projections.append((rule, projection))
    return projections


def build_plan(
    graph_repository,
    commitment_repository,
    rule_repository: FundingRuleRepository,
    *,
    as_of: date,
    cash_events: Optional[Sequence[tuple[date, Decimal]]] = None,
    last_paid_by_id: Optional[dict[int, Optional[float]]] = None,
    paycheck=None,
    evidence_repository=None,
    absent_limit: int = 50,
) -> dict:
    """Compose the canonical Plan view model from local planning data.

    Cash events default to the graph's current cash balances treated as a
    single event today (plus future paycheck inflows when a paycheck config is
    supplied); callers with richer timelines may pass them.
    """
    if cash_events is None:
        cash_events = _cash_events_from_graph(graph_repository, as_of, paycheck)

    accounts = {account.id: account for account in graph_repository.list_accounts()}
    commitments = commitment_repository.list_active()
    horizon_end = as_of + timedelta(days=_HORIZON_DAYS)

    commitment_views = []
    timeline_events = []
    shortfalls = []
    total_target = _ZERO
    total_funded = _ZERO
    next_due = None

    for commitment in commitments:
        commitment_type = commitment.type.value
        target = _commitment_target(commitment)
        funded = _money(commitment.funded_amount)
        total_target += target if commitment_type != "buffer" else _ZERO
        total_funded += min(funded, target) if commitment_type != "buffer" else _ZERO

        rules = rule_repository.list_for_commitment(commitment.id)
        projections = _project_commitment(commitment, rules, cash_events, as_of)
        projected_total = sum(
            (projection.total for _rule, projection in projections), _ZERO
        )

        due_date = _date_of(getattr(commitment, "due_date", None))
        target_date = _date_of(getattr(commitment, "target_date", None))
        # Recurring bill anchors that have passed are rolled to the next
        # occurrence so the surfaced due date is a real future date.
        due_date = _next_occurrence(due_date, getattr(commitment, "recurrence", "") or "", as_of)
        if due_date and (next_due is None or due_date < next_due):
            next_due = due_date

        for rule, projection in projections:
            for event in projection.events:
                if event.amount <= _ZERO or not (as_of <= event.date <= horizon_end):
                    continue
                timeline_events.append(
                    {
                        "date": event.date.isoformat(),
                        "amount": float(event.amount),
                        "commitment": commitment.name,
                        "commitment_id": commitment.id,
                        "rule_id": rule.id,
                        "source": event.source,
                        "explanation": list(event.explanation),
                    }
                )
            for event in projection.events:
                deficit = event.desired_amount - event.amount
                if deficit > _ZERO:
                    shortfalls.append(
                        {
                            "date": event.date.isoformat(),
                            "amount": float(deficit),
                            "cause": (
                                f"{commitment.name} wanted ${event.desired_amount} but only "
                                f"${event.amount} of cash was available"
                            ),
                            "commitment_id": commitment.id,
                        }
                    )

        backing = None
        backing_id = getattr(commitment, "backing_account_id", None)
        if backing_id is not None and backing_id in accounts:
            backing = {
                "account_id": backing_id,
                "name": accounts[backing_id].name,
            }

        commitment_views.append(
            {
                "id": commitment.id,
                "type": commitment_type,
                "name": commitment.name,
                "status": commitment.status.value,
                "priority": commitment.priority,
                "target": float(target),
                "funded": float(min(funded, target)) if commitment_type != "buffer" else float(funded),
                "unfunded": float(max(_ZERO, target - funded)),
                "due_date": due_date.isoformat() if due_date else None,
                "target_date": target_date.isoformat() if target_date else None,
                "backing": backing,
                "rule_ids": [str(rule.id) for rule in rules],
                "projected_30d": float(projected_total),
                "explanation": _coverage_explanation(target, funded, projected_total),
                # Live Crew bills expose the Crew bill id so the UI can offer a
                # proposal-gated write-back (update_crew_bill). Absent for local
                # planning records.
                "crew_bill_id": (
                    getattr(commitment, "legacy_id", None)
                    if getattr(commitment, "legacy_source", None) == "crew"
                    else None
                ),
                # R33: subtle per-bill badge (underfunded / due_soon / changed)
                # shown on the existing Plan card — no separate "monitor" page.
                # "changed" needs the last-paid charge, passed via last_paid_by_id.
                "biller_status": _biller_status(
                    commitment,
                    last_paid=(last_paid_by_id or {}).get(commitment.id),
                ),
                # Clickable invoice evidence pulled from mail (e.g. a Verizon
                # bill email) so the card surfaces the source, when it exists.
                "invoice_evidence": (
                    _bill_invoice_evidence(evidence_repository, commitment.name)
                    if commitment_type == "bill"
                    else []
                ),
            }
        )

    timeline_events.sort(key=lambda item: (item["date"], item["commitment"]))
    shortfalls.sort(key=lambda item: (item["date"], -item["amount"]))
    first_shortfall = shortfalls[0] if shortfalls else None

    cash_total = sum(
        (
            _money(account.balance)
            for account in accounts.values()
            if account.is_active and account.account_type in ("cash", "checking", "savings")
        ),
        _ZERO,
    )
    committed = sum(
        (
            min(_money(view["funded"]), _money(view["target"]))
            for view in commitment_views
            if view["type"] != "buffer"
        ),
        _ZERO,
    )
    unfunded = max(_ZERO, total_target - total_funded)
    # Crew goals are pocket targets, so their current balances are already inside
    # cash_total. When goal metadata is observed, keep the Goals station separate
    # from bill obligations and re-derive the residual instead of appending cash.
    goal_pockets = [
        account
        for account in accounts.values()
        if account.is_active
        and account.account_type == "pocket"
        and account.goal_target is not None
        and _money(account.goal_target) > _ZERO
    ]
    goals_total = sum((_money(account.balance) for account in goal_pockets), _ZERO)
    bill_purpose = committed + unfunded
    if goal_pockets:
        # Crew's provider goal pockets are distinct from the bill obligations. Their
        # balances are already in cash_total, so subtract them once as a purpose.
        available = max(_ZERO, cash_total - bill_purpose - goals_total)
    else:
        # Legacy/local planning records have no provider goal metadata; retain the
        # established commitment partition rather than guessing that a pocket is a goal.
        available = max(_ZERO, cash_total - bill_purpose)

    coverage_ratio = float(min(_money("1"), total_funded / total_target)) if total_target > _ZERO else 0.0
    if commitments:
        headline = (
            f"{len(commitments)} commitments, "
            f"{int(coverage_ratio * 100)}% funded"
        )
    else:
        headline = "No commitments yet — add one to start planning"

    freshness = _graph_freshness(graph_repository)
    beacon = forecast(
        graph_repository,
        commitment_repository,
        rule_repository,
        as_of,
        freshness=freshness["status"],
    )
    return {
        "crew_ids": _crew_ids(),
        "summary": {
            "headline": headline,
            "commitment_count": len(commitments),
            "total_target": float(total_target),
            "total_funded": float(total_funded),
            "unfunded": float(unfunded),
            "coverage_ratio": coverage_ratio,
            "next_due": next_due.isoformat() if next_due else None,
            "first_shortfall": first_shortfall,
        },
        "commitments": commitment_views,
        # Bills a complete provider read concluded are gone keep their rows and
        # their history. They are reported here with provenance instead of
        # disappearing, and never as a current obligation.
        "absent_bills": [
            {
                "id": bill.id,
                "name": bill.name,
                "provider": bill.legacy_source,
                "absent_since": bill.absent_since,
            }
            for bill in commitment_repository.list_absent_bills(limit=absent_limit)
        ],
        "timeline": {
            "start": as_of.isoformat(),
            "end": horizon_end.isoformat(),
            "events": timeline_events,
        },
        "allocation": {
            "cash_total": float(cash_total),
            "segments": [
                {"label": "Bills", "amount": float(committed + unfunded)},
                {"label": "Goals", "amount": float(goals_total)},
                {"label": "Available", "amount": float(available)},
            ],
        },
        "forecast": asdict(beacon),
        "data_freshness": freshness,
        "next_paycheck": _next_paycheck_event(paycheck, as_of),
    }


def _next_paycheck_event(paycheck, as_of):
    """Next paycheck inflow from the owner's config (date + amount).

    Surfaced directly so the Funding Schedule card is meaningful even when no
    funding rules (and therefore no projected timeline events) exist.
    """
    if paycheck is None or not getattr(paycheck, "active", False):
        return None
    amount = getattr(paycheck, "amount", 0) or 0
    next_date = getattr(paycheck, "next_date", "") or ""
    cadence = getattr(paycheck, "cadence", "monthly")
    if amount <= 0 or not next_date:
        return None
    try:
        anchor = date.fromisoformat(next_date)
        anchor = next_occurrence(anchor, cadence, as_of)
    except (TypeError, ValueError):
        return None
    return {"date": anchor.isoformat(), "amount": round(float(amount), 2), "cadence": cadence}


def _coverage_explanation(target: Decimal, funded: Decimal, projected: Decimal) -> list[str]:
    factors = []
    if funded > _ZERO:
        factors.append(f"${funded} already set aside")
    if projected > _ZERO:
        factors.append(f"${projected} projected from funding rules in the next 30 days")
    remaining = max(_ZERO, target - funded - projected)
    if target > _ZERO and remaining > _ZERO:
        factors.append(f"${remaining} still needs a plan")
    if not factors:
        factors.append("No funding activity yet")
    return factors


def _commitment_target(commitment) -> Decimal:
    commitment_type = commitment.type.value
    if commitment_type == "bill":
        return _money(commitment.amount)
    if commitment_type == "buffer":
        return _money(commitment.buffer_minimum)
    return _money(commitment.target_amount)


def _date_of(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _next_occurrence(anchor: date, recurrence: str, as_of: date) -> date:
    """Roll a recurring bill's anchor date forward to the next occurrence.

    Crew's ``anchorDate`` is the original anchor of a recurring bill (e.g.
    2026-01-16). Storing it verbatim surfaces a past date as the bill's due date.
    For a recurring bill whose anchor has passed, advance it by its cadence until
    it is >= as_of so the "next due" is a real future date. Non-recurring (or
    unknown) bills keep their anchor unchanged.
    """
    rec = (recurrence or "").lower()
    anchor = anchor if isinstance(anchor, date) else _date_of(str(anchor)) if anchor else None
    if anchor is None:
        return None
    if rec not in ("weekly", "biweekly", "monthly", "semimonthly"):
        return anchor
    # Anchor-preserving: the walk measures each step from the ORIGINAL anchor, so
    # a monthly bill on the 31st clamps in February and returns to the 31st in
    # March instead of staying on the 28th forever.
    return next_occurrence(anchor, rec, as_of)


def _cash_events_from_graph(graph_repository, as_of: date, paycheck=None) -> list[tuple[date, Decimal]]:
    from decimal import Decimal

    total = sum(
        (
            _money(account.balance)
            for account in graph_repository.list_accounts()
            if account.is_active and account.account_type in ("cash", "checking", "savings")
        ),
        _ZERO,
    )
    if paycheck is not None:
        from meridian.paycheck import build_cash_events

        events = build_cash_events(float(total), paycheck, as_of=as_of)
        return [(date, Decimal(str(amount))) for date, amount in events]
    return [(as_of, total)] if total > _ZERO else []


def _graph_freshness(graph_repository) -> dict:
    from meridian.services.today import data_freshness

    return data_freshness(graph_repository, include_all_connections=True)
