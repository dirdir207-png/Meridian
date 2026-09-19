"""The owner's expected-income rule, applied to the CURRENT income channel.

Verbatim: "it should default to that value and moving forward aggregate after 3", following
"Moving forward paychecks are deposited directly to crew, unlike transfers from cash app etc
previously, this was the first paycheck to hit directly".

The channel distinction is the whole point. learn_paycheck groups by merchant and returns a
single source, so aggregating across all history would return a three-occurrence aggregate for
a channel the owner has left, and report it as the expected income. These tests exist to make
that impossible to reintroduce.
"""
from meridian.paycheck import PaycheckConfig, resolve_expected_paycheck


class Tx:
    """A transaction as the dial's readers see it."""

    def __init__(self, merchant, amount, day, kind="income", txn_id=None):
        self.id = txn_id if txn_id is not None else abs(hash((merchant, day))) % 100000
        self.merchant = merchant
        self.description = merchant
        self.amount = amount
        self.occurred_at = f"{day}T12:00:00+00:00"
        self.classification_kind = kind


def _cash_app_history():
    return [
        Tx("Cash App", 980.50, "2026-07-22", txn_id=1),
        Tx("Cash App", 980.50, "2026-08-05", txn_id=2),
        Tx("Cash App", 980.50, "2026-08-19", txn_id=3),
    ]


def test_a_single_observation_does_not_name_a_paycheck_source():
    """KNOWN DEVIATION from the owner's literal rule, and the reason for it.

    The owner asked for a fallback to "the value of the last known source (the paycheck from
    yesterday)" on a new channel. Taken literally on the live ledger that reported an expected
    paycheck of $0.46 sourced from "Interest paid", because the most recent income-classified
    transaction was a 46-cent interest credit. Interest IS income; it is not a paycheck.

    One observation cannot be distinguished from interest, a refund or a one-off, so it is not
    evidence that a channel pays wages. Until the channel recurs (>= 2 observations) the
    configured figure is used, which claims nothing it cannot support.

    The gap this leaves is real and is recorded for the owner: the FIRST paycheck of a new job
    is, by definition, a single observation, so it is not yet usable as the default. What would
    close it is an explicit designation of which source is the paycheck -- the same governance
    the owner asked for in OS-051 -- rather than an inference from recency alone.
    """
    direct = Tx("Veterans Home", 1663.00, "2026-09-18", txn_id=99)
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")

    resolved = resolve_expected_paycheck([*_cash_app_history(), direct], configured=configured)

    assert resolved.basis == "configured"
    assert resolved.source == "manual"
    assert resolved.observed_at is None
    assert resolved.evidence_ids == ()


def test_a_retired_channel_cannot_win_even_with_enough_occurrences():
    """Three Cash App deposits would aggregate happily -- and would describe a route the owner
    has left. The current channel is the one with the most recent observation."""
    direct = Tx("Veterans Home", 1663.00, "2026-09-18", txn_id=99)
    resolved = resolve_expected_paycheck([*_cash_app_history(), direct])

    # Either there is no projection, or it does not come from the retired channel. It must
    # never fall back THROUGH the new channel to the old one, which would report wages the
    # owner no longer earns.
    assert resolved is None or resolved.source != "Cash App"
    assert resolved is None or resolved.amount != 980.50


def test_the_current_channel_aggregates_once_it_has_enough_occurrences():
    """'moving forward aggregate after 3' -- three of the NEW channel is what aggregates."""
    current = [
        Tx("Veterans Home", 1600.00, "2026-08-21", txn_id=11),
        Tx("Veterans Home", 1663.00, "2026-09-04", txn_id=12),
        Tx("Veterans Home", 1663.00, "2026-09-18", txn_id=13),
    ]
    resolved = resolve_expected_paycheck([*_cash_app_history(), *current])

    assert resolved.basis == "aggregate"
    assert resolved.source == "Veterans Home"
    assert resolved.occurrences == 3
    assert resolved.observed_at == "2026-09-18"
    assert set(resolved.evidence_ids) == {11, 12, 13}
    # The aggregate is a median of the observed pay periods, never a Cash App figure.
    assert resolved.amount >= 1600.00


def test_two_occurrences_is_not_yet_enough_to_aggregate():
    current = [
        Tx("Veterans Home", 1600.00, "2026-09-04", txn_id=11),
        Tx("Veterans Home", 1663.00, "2026-09-18", txn_id=12),
    ]
    resolved = resolve_expected_paycheck([*_cash_app_history(), *current])

    assert resolved.basis == "last_known"
    assert resolved.amount == 1663.00


def test_with_no_observations_the_configured_figure_is_the_last_resort():
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    resolved = resolve_expected_paycheck([], configured=configured)

    assert resolved.basis == "configured"
    assert resolved.source == "manual"
    assert resolved.amount == 1663.00
    # Nothing was observed, so nothing may be cited as evidence.
    assert resolved.observed_at is None
    assert resolved.evidence_ids == ()


def test_a_non_income_transaction_is_never_a_paycheck():
    spend = [Tx("Shell", -84.00, "2026-09-18", kind="spend")]
    assert resolve_expected_paycheck(spend) is None


def test_nothing_observed_and_nothing_configured_resolves_to_nothing():
    assert resolve_expected_paycheck([]) is None


def test_a_lone_interest_credit_cannot_become_the_expected_paycheck():
    """The live regression this rule exists to prevent.

    On the owner's ledger the most recent income-classified transaction was a $0.46 "Interest
    paid" credit. Treating "the most recently observed income" as "the last known SOURCE" turned
    an expected paycheck of $1,663.00 into 46 cents and announced the source as "Interest paid".
    Interest IS income; it is not a paycheck. One observation cannot be distinguished from
    interest, a refund or a one-off, so it must not name a paycheck source.
    """
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    interest = Tx("Interest paid", 0.46, "2026-09-01", txn_id=51)

    resolved = resolve_expected_paycheck([interest], configured=configured)

    assert resolved.basis == "configured"
    assert resolved.amount == 1663.00
    assert resolved.source == "manual"
    # And it must not cite the interest credit as evidence for a paycheck.
    assert resolved.observed_at is None
    assert resolved.evidence_ids == ()


def test_a_lone_income_credit_with_nothing_configured_projects_nothing():
    """Better no projection than a 46-cent paycheck."""
    interest = Tx("Interest paid", 0.46, "2026-09-01", txn_id=51)
    assert resolve_expected_paycheck([interest]) is None


def test_a_stray_recent_credit_does_not_resurrect_an_older_channel():
    """The conservative direction, chosen deliberately.

    The alternative -- skip the non-recurring credit and use the older recurring channel --
    reads better here but fails the case the owner named explicitly: after a job change the
    PREVIOUS position's channel is also recurring, so skipping forward would report the old
    wages. Falling back to the configured figure is the failure mode that cannot state
    something false about money.
    """
    current = [
        Tx("Veterans Home", 1600.00, "2026-09-04", txn_id=11),
        Tx("Veterans Home", 1663.00, "2026-09-18", txn_id=12),
    ]
    interest = Tx("Interest paid", 0.46, "2026-09-19", txn_id=51)
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")

    resolved = resolve_expected_paycheck([*current, interest], configured=configured)

    assert resolved.basis == "configured"
    assert resolved.amount == 1663.00
    assert resolved.source == "manual"
