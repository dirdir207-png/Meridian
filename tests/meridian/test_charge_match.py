"""Tests for the charge matcher (OS-067).

The contract: match mail evidence to the CHARGE it documents, on a VERIFIABLE basis, and
record doubt rather than resolving it.
"""

from datetime import datetime, timezone

from meridian.charge_match import (
    CONFIDENCE_AMBIGUOUS,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    attach_charge_matches,
    extract_charge_signal,
    find_charge_matches,
    summarize,
)


class FakeEvidence:
    def __init__(self, eid, title, body="", sender=""):
        self.id = eid
        self.title = title
        self.body = body
        self.sender = sender


class FakeTx:
    def __init__(self, tid, amount, occurred_at):
        self.id = tid
        self.amount = amount
        self.occurred_at = occurred_at


# --- signal extraction ---------------------------------------------------------------

def test_extracts_an_amount_from_a_receipt_body():
    signal = extract_charge_signal(
        "Receipt for your payment. Total: $19.65 paid to PayPal on 2026-09-21."
    )
    assert signal is not None
    assert signal.amount == 19.65
    assert signal.stated_date == datetime(2026, 9, 21, tzinfo=timezone.utc)


def test_handles_thousands_separators():
    signal = extract_charge_signal("Amount due $1,234.56")
    assert signal is not None and signal.amount == 1234.56


def test_no_amount_means_out_of_scope_not_a_failure():
    assert extract_charge_signal("Your statement is ready to view online") is None
    assert extract_charge_signal("") is None


def test_parses_the_date_formats_real_billers_use():
    for text, expected in (
        ("charged 2026-09-18", (2026, 9, 18)),
        ("charged 09/18/2026", (2026, 9, 18)),
        ("charged Sep 18, 2026", (2026, 9, 18)),
        ("charged September 18, 2026", (2026, 9, 18)),
    ):
        signal = extract_charge_signal(f"${8}.00 " + text)
        assert signal is not None and signal.stated_date is not None, text
        assert (
            signal.stated_date.year, signal.stated_date.month, signal.stated_date.day
        ) == expected, text


# --- matching ------------------------------------------------------------------------

def test_a_single_candidate_corroborated_by_date_is_high_confidence():
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Receipt: charged $8.00 on 2026-09-18")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    assert matches[0].matched
    assert matches[0].confidence == CONFIDENCE_HIGH
    assert matches[0].days_from_stated == 0


def test_a_single_candidate_without_a_date_is_only_medium():
    """Amount alone is too weak to call a fact, so it is graded down, not hidden."""
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "You spent $8.00")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    assert matches[0].matched
    assert matches[0].confidence == CONFIDENCE_MEDIUM


def test_the_date_disambiguates_identical_amounts():
    """Two $8.00 charges: the date picks the right one and it counts as real evidence."""
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Receipt $8.00 on 2026-09-18")],
        transactions=[
            FakeTx("t1", -8.0, "2026-09-01T10:00:00Z"),
            FakeTx("t2", -8.0, "2026-09-18T10:00:00Z"),
        ],
    )
    assert matches[0].transaction_id == "t2"
    assert matches[0].confidence == CONFIDENCE_HIGH
    assert matches[0].reason == "date-disambiguated"


def test_an_unresolvable_tie_is_recorded_as_ambiguous_never_asserted():
    """Seven charges of $10.60 and no usable date: the doubt must be visible."""
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Hangzhou DeepSeek: $10.60 USD")],
        transactions=[
            FakeTx(f"t{i}", -10.60, f"2026-09-{10 + i:02d}T10:00:00Z") for i in range(7)
        ],
    )
    match = matches[0]
    assert match.confidence == CONFIDENCE_AMBIGUOUS
    assert match.candidate_count == 7
    assert match.alternatives, "the other candidates must be recorded, not discarded"
    assert "ambiguous" in match.provenance()


def test_an_amount_with_no_matching_charge_is_reported_not_linked():
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Our up to $25.00 gift to you")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    assert not matches[0].matched
    assert matches[0].reason == "no-charge-this-size"


def test_an_email_without_money_is_out_of_scope():
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Your statement is ready")],
        transactions=[],
    )
    assert not matches[0].matched
    assert matches[0].reason == "no-amount"


def test_the_body_is_searched_not_only_the_subject():
    """Real receipts carry the amount in the body; measuring subjects alone found almost
    nothing, which is why the caller may supply body text."""
    matches = find_charge_matches(
        evidence_items=[
            FakeEvidence(1, "Your OpenAI receipt", body="Total charged: $8.00 on 2026-09-18")
        ],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    assert matches[0].matched, "the amount lived in the body and must still be found"


def test_a_charge_outside_the_window_is_not_matched():
    """An unbounded window would make amount matching meaningless."""
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Receipt $8.00 on 2026-09-18")],
        transactions=[FakeTx("t1", -8.0, "2026-07-01T10:00:00Z")],
        window_days=3,
    )
    assert matches[0].matched
    assert matches[0].confidence == CONFIDENCE_MEDIUM, (
        "a far-off single candidate is amount-only: the date must not corroborate it"
    )
    assert matches[0].days_from_stated is None, (
        "an out-of-window date must not be recorded as corroboration"
    )


def test_one_bad_row_does_not_stop_the_pass():
    class Exploding:
        @property
        def id(self):
            raise RuntimeError("bad row")

    matches = find_charge_matches(
        evidence_items=[Exploding(), FakeEvidence(2, "You spent $8.00")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    assert len(matches) == 2
    assert matches[0].reason.startswith("error:")
    assert matches[1].matched, "a later good row must still be processed"


# --- attaching -----------------------------------------------------------------------

class FakeLink:
    def __init__(self, target_kind, target_id):
        self.target_kind = target_kind
        self.target_id = target_id


class FakeRepo:
    def __init__(self):
        self.links = []
        self.by_evidence = {}

    def add_link(self, *, evidence_id, target_kind, target_id, relation, provenance):
        self.links.append((evidence_id, target_kind, target_id, relation, provenance))
        self.by_evidence.setdefault(evidence_id, []).append(FakeLink(target_kind, target_id))

    def list_links(self, evidence_id):
        return self.by_evidence.get(evidence_id, [])


def test_attaching_adds_one_link_with_its_basis_recorded():
    repo = FakeRepo()
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Receipt $8.00 on 2026-09-18")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    result = attach_charge_matches(evidence_repo=repo, matches=matches)
    assert result["created"] == 1
    _eid, kind, tid, relation, provenance = repo.links[0]
    assert kind == "transaction" and tid == "t1" and relation == "documents"
    assert provenance == "mail:amount+date:high", "the BASIS must survive into the link"


def test_re_running_does_not_duplicate_a_link():
    repo = FakeRepo()
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Receipt $8.00 on 2026-09-18")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    attach_charge_matches(evidence_repo=repo, matches=matches)
    second = attach_charge_matches(evidence_repo=repo, matches=matches)
    assert second["created"] == 0 and second["skipped"] == 1
    assert len(repo.links) == 1


def test_unmatched_evidence_creates_no_link():
    repo = FakeRepo()
    matches = find_charge_matches(
        evidence_items=[FakeEvidence(1, "Our up to $25.00 gift")],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    result = attach_charge_matches(evidence_repo=repo, matches=matches)
    assert result["created"] == 0 and repo.links == []


# --- reporting -----------------------------------------------------------------------

def test_the_summary_states_the_hit_rate_and_why_items_missed():
    matches = find_charge_matches(
        evidence_items=[
            FakeEvidence(1, "Receipt $8.00 on 2026-09-18"),
            FakeEvidence(2, "Our up to $25.00 gift"),
            FakeEvidence(3, "Your statement is ready"),
        ],
        transactions=[FakeTx("t1", -8.0, "2026-09-18T10:00:00Z")],
    )
    summary = summarize(matches)
    assert summary["evidence_considered"] == 3
    assert summary["matched"] == 1
    assert summary["hit_rate"] == round(1 / 3, 3)
    assert summary["unmatched_reasons"]["no-amount"] == 1
    assert summary["unmatched_reasons"]["no-charge-this-size"] == 1


def test_a_bare_dollar_figure_is_not_treated_as_a_charge_amount():
    """A marketing "$25" with no cents is not a transaction amount. Requiring the cents
    group is what keeps promo copy out of the ledger match."""
    assert extract_charge_signal("Get up to $25 without the stress of interest") is None
    assert extract_charge_signal("25% Off Sitewide Ends Soon") is None
