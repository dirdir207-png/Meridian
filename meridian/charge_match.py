"""Match mail evidence to the CHARGE it documents (OS-067).

The evidence store answers "what mail do we have?". This module answers a different and
more useful question: **which real charge does this email document?**

Why a separate concern. The bill matcher (`services/plan.py::_bill_invoice_evidence`) asks
"is this a bill email?" — a JUDGEMENT that cannot be checked against anything, which is why
it needs keyword heuristics and why it has to reject card alerts ("You spent $58.25 at
Verizon") that the transaction side desperately wants. This module asks a VERIFIABLE
question instead: does the amount in this email correspond to an actual charge we can find?
That makes precision objective — a match is either supported by the ledger or it is not —
so the matcher can be tightened without starving coverage, and widened without inventing
claims.

Design rules:

  * A match needs BOTH an amount and date support. Amount alone is too weak: $8.00 appears
    on many days, so an amount-only match is a guess dressed as a fact.
  * Ambiguity is recorded, never resolved by picking one. The same amount can occur twice
    in the window (two $8.00 OpenAI charges), and choosing one would assert something the
    data does not support. Ties attach with explicit low confidence and the alternatives
    are kept in the provenance so a human can see the doubt.
  * Nothing here mutates a transaction. It only adds an evidence link, so the worst case is
    a link a human can reject, never a changed financial fact.
  * Unmatched evidence is REPORTED, not silently dropped. The hit rate is the honest measure
    of whether ingestion is broad enough, and it must be visible.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional

# A charge stated in an email. Bounded and anchored so we match real money, not "2026" or
# a stray "4.5".
_AMOUNT_RE = re.compile(r"\$\s?([\d,]+\.\d{2})")

# Dates as email headers/notifications write them. Kept deliberately narrow: ambiguity in
# date parsing would silently widen the match window and destroy the precision this module
# exists to provide.
_DATE_PATTERNS = (
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"),
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b",
        re.IGNORECASE,
    ),
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

#: Confidence vocabulary. Deliberately coarse: three levels are enough to act on, and more
#: would imply a precision the underlying data does not have.
CONFIDENCE_HIGH = "high"          # single candidate, date corroborates
CONFIDENCE_MEDIUM = "medium"      # single candidate, amount only
CONFIDENCE_AMBIGUOUS = "ambiguous"  # several candidates; ties left for a human

#: How far from the stated date a charge may sit. Posting lag is real (a card charge can
#: post a day or two after the email), but an unbounded window would make amount matching
#: meaningless, so it stays tight.
DEFAULT_WINDOW_DAYS = 3


@dataclass(frozen=True)
class ChargeSignal:
    """What an email claims: an amount, and the date it says it happened."""

    amount: float
    stated_date: Optional[datetime] = None


@dataclass
class ChargeMatch:
    """The outcome for one piece of evidence. Always returned, matched or not."""

    evidence_id: int
    signal: Optional[ChargeSignal] = None
    transaction_id: Optional[str] = None
    confidence: Optional[str] = None
    days_from_stated: Optional[int] = None
    candidate_count: int = 0
    alternatives: list[str] = field(default_factory=list)
    reason: str = ""

    @property
    def matched(self) -> bool:
        return self.transaction_id is not None

    def provenance(self) -> str:
        """A greppable audit string. Records the BASIS and the DOUBT, not just success."""
        if not self.matched:
            return f"mail:no-match:{self.reason}"
        basis = "amount+date" if self.days_from_stated is not None else "amount"
        spec = f"mail:{basis}:{self.confidence}"
        if self.confidence == CONFIDENCE_AMBIGUOUS:
            spec += f":{self.candidate_count}candidates"
        return spec


def extract_charge_signal(text: str) -> Optional[ChargeSignal]:
    """Pull the first money amount and any stated date out of ``text``.

    Returns None when there is no amount at all — an email with no money in it cannot
    document a charge, so it is out of scope rather than a failure.
    """
    if not text:
        return None
    amounts = _AMOUNT_RE.findall(text)
    if not amounts:
        return None
    try:
        amount = float(amounts[0].replace(",", ""))
    except ValueError:
        return None
    if amount <= 0:
        return None
    return ChargeSignal(amount=amount, stated_date=_first_date(text))


def _first_date(text: str) -> Optional[datetime]:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        groups = match.groups()
        try:
            if len(groups) == 3 and groups[0].isalpha():
                month = _MONTHS.get(groups[0][:3].lower())
                if month is None:
                    continue
                return datetime(int(groups[2]), month, int(groups[1]), tzinfo=timezone.utc)
            if len(groups) == 3 and len(groups[0]) == 4:
                return datetime(int(groups[0]), int(groups[1]), int(groups[2]), tzinfo=timezone.utc)
            if len(groups) == 3:
                # Ambiguous M/D vs D/M. Assume US month-first, which matches this owner's
                # provider data; if the day is impossible as a month it cannot be valid.
                month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                if not 1 <= month <= 12:
                    continue
                return datetime(year, month, day, tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


def _parse_transaction_date(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def find_charge_matches(
    *,
    evidence_items: Iterable,
    transactions: Iterable,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> list[ChargeMatch]:
    """For each evidence item, find the charge it documents. Read-only.

    Never raises for a single bad item: one unparseable row must not stop the pass, and a
    caller measuring hit-rate needs every item accounted for.
    """
    prepared: list[tuple[str, float, Optional[datetime]]] = []
    for tx in transactions:
        amount = getattr(tx, "amount", None)
        if amount is None:
            continue
        try:
            value = abs(float(amount))
        except (TypeError, ValueError):
            continue
        if value <= 0:
            continue
        prepared.append(
            (
                str(getattr(tx, "id", "")),
                value,
                _parse_transaction_date(
                    getattr(tx, "occurred_at", None) or getattr(tx, "posted_at", None)
                ),
            )
        )

    results: list[ChargeMatch] = []
    for item in evidence_items:
        try:
            text = _evidence_text(item)
            signal = extract_charge_signal(text)
            if signal is None:
                results.append(
                    ChargeMatch(evidence_id=item.id, reason="no-amount")
                )
                continue
            candidates = [c for c in prepared if abs(c[1] - signal.amount) < 0.005]
            if not candidates:
                results.append(
                    ChargeMatch(evidence_id=item.id, signal=signal, reason="no-charge-this-size")
                )
                continue
            results.append(
                _choose(item, signal, candidates, window_days)
            )
        except Exception as exc:  # noqa: BLE001 - one bad row must not stop the pass
            try:
                bad_id = getattr(item, "id", -1)
            except Exception:  # noqa: BLE001 - the row is unreadable in every respect
                bad_id = -1
            results.append(
                ChargeMatch(evidence_id=bad_id, reason=f"error:{type(exc).__name__}")
            )
    return results


def _evidence_text(item) -> str:
    """Subject, sender, and body text WHEN the caller supplied one.

    ``body`` is optional on purpose. A stored EvidenceItem carries no body, so a caller
    working from the store alone still gets subject and sender matching rather than an
    AttributeError — but the amount usually lives in the BODY of a receipt, so a caller that
    CAN supply body text (a live Gmail fetch, or a readable blob) should, and will match far
    more. Measured 2026-09-21: subject-only matching found 9 hits across 775 stored items,
    because only 23 of them carried a money amount in the subject at all.
    """
    parts = [getattr(item, "title", None) or "", getattr(item, "body", None) or ""]
    sender = getattr(item, "sender", None)
    if sender:
        parts.append(sender)
    return " ".join(parts)


def _choose(item, signal: ChargeSignal, candidates, window_days: int) -> ChargeMatch:
    """Pick a candidate, or record the tie rather than inventing a winner.

    A date only CORROBORATES a match when it falls INSIDE the window. A candidate dated
    months away is not weak support for the  it is no support, so it must not be
    able to raise confidence merely by existing. (An earlier version treated any dated
    single candidate as high confidence, which would have silently asserted a match
    between a September email and a July charge.)
    """
    within: list[tuple[int, str]] = []
    for tx_id, _amount, occurred in candidates:
        if signal.stated_date is None or occurred is None:
            continue
        delta = abs((occurred.date() - signal.stated_date.date()).days)
        if delta <= window_days:
            within.append((delta, tx_id))

    if len(candidates) == 1:
        tx_id, _amount, _occurred = candidates[0]
        if within:
            return ChargeMatch(
                evidence_id=item.id, signal=signal, transaction_id=tx_id,
                confidence=CONFIDENCE_HIGH, days_from_stated=within[0][0],
                candidate_count=1, reason="single-candidate-with-date",
            )
        return ChargeMatch(
            evidence_id=item.id, signal=signal, transaction_id=tx_id,
            confidence=CONFIDENCE_MEDIUM, candidate_count=1,
            reason="single-candidate-amount-only",
        )

    # Several charges share this amount. If exactly one is corroborated by the date, that is
    # real evidence and worth using; if none or several are, the tie is reported as such.
    if len(within) == 1:
        delta, tx_id = within[0]
        return ChargeMatch(
            evidence_id=item.id, signal=signal, transaction_id=tx_id,
            confidence=CONFIDENCE_HIGH, days_from_stated=delta,
            candidate_count=len(candidates), reason="date-disambiguated",
        )

    # No corroboration available: attach to the  but SAY it is ambiguous rather
    # than presenting a coin flip as a fact.
    if within:
        delta, tx_id = min(within)
    else:
        tx_id = candidates[0][0]
        delta = None
    return ChargeMatch(
        evidence_id=item.id, signal=signal, transaction_id=tx_id,
        confidence=CONFIDENCE_AMBIGUOUS, days_from_stated=delta,
        candidate_count=len(candidates),
        alternatives=[c[0] for c in candidates if c[0] != tx_id],
        reason="ambiguous-amount",
    )


def attach_charge_matches(
    *,
    evidence_repo,
    matches: Iterable[ChargeMatch],
    provenance_prefix: str = "mail",
) -> dict[str, int]:
    """Persist the links for matched charge evidence. Adds links only.

    Never mutates a transaction, and never removes a link. Re-running is safe: an existing
    identical link is left alone rather than duplicated.
    """
    created = 0
    skipped = 0
    failed = 0
    for match in matches:
        if not match.matched:
            continue
        try:
            existing = evidence_repo.list_links(match.evidence_id)
            already = any(
                link.target_kind == "transaction" and str(link.target_id) == str(match.transaction_id)
                for link in existing
            )
            if already:
                skipped += 1
                continue
            basis = match.provenance().split(":", 1)[1]
            evidence_repo.add_link(
                evidence_id=match.evidence_id,
                target_kind="transaction",
                target_id=str(match.transaction_id),
                relation="documents",
                provenance=f"{provenance_prefix}:{basis}",
            )
            created += 1
        except Exception:  # noqa: BLE001 - a bad link must not stop the pass
            failed += 1
    return {"created": created, "skipped": skipped, "failed": failed}


def summarize(matches: Iterable[ChargeMatch]) -> dict[str, object]:
    """Honest accounting for an operator: what matched, on what basis, and what did not."""
    rows = list(matches)
    by_confidence: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for match in rows:
        key = match.confidence or "unmatched"
        by_confidence[key] = by_confidence.get(key, 0) + 1
        if not match.matched:
            reasons[match.reason] = reasons.get(match.reason, 0) + 1
    matched = sum(1 for m in rows if m.matched)
    return {
        "evidence_considered": len(rows),
        "matched": matched,
        "unmatched": len(rows) - matched,
        "hit_rate": round(matched / len(rows), 3) if rows else 0.0,
        "by_confidence": by_confidence,
        "unmatched_reasons": reasons,
    }
