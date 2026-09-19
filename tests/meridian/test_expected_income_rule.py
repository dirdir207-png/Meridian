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


class Plan:
    """A persisted Crew funding plan, as resolution reads it.

    Resolution reads Meridian's OWN record of the plan, never a live provider
    payload, so a read path cannot depend on a network call.
    """

    def __init__(self, name, amount, cadence=None, anchor_date=None,
                 external_id="plan:1", bill_reserve_id="res:1",
                 observed_at="2026-09-19T12:00:00Z"):
        self.external_id = external_id
        self.bill_reserve_id = bill_reserve_id
        self.name = name
        self.amount = amount
        self.cadence = cadence
        self.anchor_date = anchor_date
        self.observed_at = observed_at


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


# ---------------------------------------------------------------------------
# OS-050: the paycheck must resolve to the Crew record the owner named.
#
# Owner directive, verbatim: "Right, it SHOULD be a crew record though, the
# paycheck". The Crew bill-reserve funding plan IS the owner's "Funding
# Cadence", so it outranks every Meridian-derived leg.
#
# What these tests protect: the Crew record is the identity, so a rename in
# Crew reaches Meridian and nothing keys on the merchant text of a deposit.
# ---------------------------------------------------------------------------


def test_the_crew_funding_plan_outranks_every_meridian_derived_leg():
    """The Crew record wins even when Meridian has an aggregate to offer.

    Aggregation is Meridian's own deviation -- the owner: "The only deviation for
    Meridian is most likely the aggregation". A deviation must never displace the
    authoritative provider record.
    """
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    observed = [
        Tx("Cash App", 980.50, "2026-08-05", txn_id=1),
        Tx("Cash App", 980.50, "2026-08-19", txn_id=2),
        Tx("Cash App", 980.50, "2026-09-02", txn_id=3),
    ]
    plan = Plan("Veterans Home", 1663.00, cadence="biweekly", anchor_date="2026-09-04")

    resolved = resolve_expected_paycheck(observed, configured=configured, plans=[plan])

    assert resolved.basis == "crew_plan"
    assert resolved.source == "Veterans Home"
    assert resolved.amount == 1663.00
    assert resolved.plan_id == "plan:1"


def test_the_plan_is_the_identity_so_a_crew_rename_reaches_meridian():
    """The owner renames the income source ("State of New Hampshire" ->
    "Veteran's Home"). Keying on the plan record means the rename propagates;
    keying on a deposit's merchant text would break the next time it changes."""
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    # The deposits still carry the OLD merchant text.
    observed = [Tx("State Of New Hampshire", 1663.00, "2026-09-18", txn_id=7)]
    plan = Plan("Veteran's Home", 1663.00, cadence="biweekly", anchor_date="2026-09-04")

    resolved = resolve_expected_paycheck(observed, configured=configured, plans=[plan])

    assert resolved.source == "Veteran's Home"
    assert resolved.plan_id == "plan:1"


def test_a_plan_cites_its_own_record_and_claims_no_transaction_as_evidence():
    """The plan is a provider RECORD, not a transaction. Its provenance is the
    provider read that observed it, so `evidence_ids` (transaction ids) must stay
    empty rather than borrowing a deposit that merely looks related."""
    plan = Plan("Veterans Home", 1663.00, cadence="biweekly", anchor_date="2026-09-04",
                observed_at="2026-09-19T12:00:00Z")

    resolved = resolve_expected_paycheck([], plans=[plan])

    assert resolved.plan_id == "plan:1"
    assert resolved.observed_at == "2026-09-19T12:00:00Z"
    assert resolved.evidence_ids == ()


def test_the_plan_supplies_the_cadence_it_reports():
    """Crew carries frequency + frequencyInterval + anchorDate, so the schedule is
    not re-derived locally and does not need the configured figure."""
    plan = Plan("Veterans Home", 1663.00, cadence="biweekly", anchor_date="2026-09-04")

    resolved = resolve_expected_paycheck([], plans=[plan])

    assert resolved.cadence == "biweekly"
    assert resolved.next_date == "2026-09-18"


def test_an_unmappable_crew_cadence_is_not_invented():
    """Crew's interval is not always expressible in Meridian's vocabulary (e.g.
    MONTHLY x2 is not weekly/biweekly/monthly/semimonthly/annually). The AMOUNT and
    the IDENTITY are still Crew facts, but the schedule must not be fabricated into
    a cadence Meridian cannot honour."""
    plan = Plan("Veterans Home", 1663.00, cadence=None, anchor_date="2026-09-04")

    resolved = resolve_expected_paycheck([], plans=[plan])

    assert resolved.basis == "crew_plan"
    assert resolved.amount == 1663.00
    assert resolved.cadence == ""
    assert resolved.next_date == ""


def test_several_plans_do_not_silently_pick_one():
    """A reserve's funding plan is money moving INTO that reserve, so a family with
    several reserves can hold several plans that are allocations of ONE paycheck --
    not competing candidates for it. Choosing one would understate income; picking
    the largest would be a guess presented as a fact. So with more than one plan the
    Crew leg does not apply, and resolution falls through to the honest legs."""
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    plans = [
        Plan("Veterans Home", 1000.00, cadence="biweekly", anchor_date="2026-09-04",
             external_id="plan:1", bill_reserve_id="res:1"),
        Plan("Veterans Home", 663.00, cadence="biweekly", anchor_date="2026-09-04",
             external_id="plan:2", bill_reserve_id="res:2"),
    ]

    resolved = resolve_expected_paycheck([], configured=configured, plans=plans)

    assert resolved.basis == "configured"
    assert resolved.plan_id is None


def test_a_zero_amount_plan_is_not_an_expected_paycheck():
    """A cadence that funds nothing does not describe income."""
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")
    plan = Plan("Veterans Home", 0.0, cadence="biweekly", anchor_date="2026-09-04")

    resolved = resolve_expected_paycheck([], configured=configured, plans=[plan])

    assert resolved.basis == "configured"
    assert resolved.plan_id is None


def test_no_plan_leaves_the_approved_chain_untouched():
    """Regression guard: the plan leg must be additive. With no plan observed, the
    owner's approved rule (aggregate, else last known, else configured) is exactly
    what it was."""
    current = [
        Tx("Veterans Home", 1600.00, "2026-08-21", txn_id=11),
        Tx("Veterans Home", 1663.00, "2026-09-04", txn_id=12),
        Tx("Veterans Home", 1663.00, "2026-09-18", txn_id=13),
    ]

    for plans in (None, []):
        resolved = resolve_expected_paycheck(current, plans=plans)
        assert resolved.basis == "aggregate"
        assert resolved.plan_id is None


# ---------------------------------------------------------------------------
# OS-051: the learning floor governs LEARNED legs only.
#
# The floor changes which observations are learned from. It must not touch the
# Crew plan (a provider record) or the owner's configured figure (an assertion),
# and it must never delete anything.
# ---------------------------------------------------------------------------


def _old_job():
    return [
        Tx("Old Employer", 1200.0, "2026-06-05", txn_id=1),
        Tx("Old Employer", 1200.0, "2026-06-19", txn_id=2),
        Tx("Old Employer", 1200.0, "2026-07-03", txn_id=3),
    ]


def test_the_floor_excludes_a_previous_positions_pay_from_the_aggregate():
    """The owner's stated reason: "I shouldnt be including the learned pay from
    previous positions". Without the floor the old job aggregates; with it, nothing
    about that job may be reported."""
    configured = PaycheckConfig(cadence="biweekly", amount=2500.00, next_date="2026-10-16")

    without = resolve_expected_paycheck(_old_job(), configured=configured)
    with_floor = resolve_expected_paycheck(
        _old_job(), configured=configured, learning_floor="2026-09-01"
    )

    assert without.basis == "aggregate"
    assert without.amount == 1200.0
    # The old job is no longer learnable, so the honest answer is the configured figure.
    assert with_floor.basis == "configured"
    assert with_floor.amount == 2500.00
    assert with_floor.learning_floor == "2026-09-01"


def test_the_floor_carries_its_provenance_on_the_resolution():
    """A learned figure produced under a floor must say so, or a reader cannot tell
    why the amount differs from the raw history."""
    resolved = resolve_expected_paycheck(
        _old_job(),
        configured=PaycheckConfig(cadence="monthly", amount=100.0, next_date="2026-10-01"),
        learning_floor="2026-09-01",
    )

    assert resolved.learning_floor == "2026-09-01"


def test_a_post_floor_channel_still_learns_once_it_recurs():
    """The floor re-bases learning; it does not disable it."""
    new_job = [
        Tx("New Employer", 2500.0, "2026-09-18", txn_id=11),
        Tx("New Employer", 2500.0, "2026-10-02", txn_id=12),
    ]

    resolved = resolve_expected_paycheck(
        [*_old_job(), *new_job], learning_floor="2026-09-01"
    )

    assert resolved.basis == "last_known"
    assert resolved.source == "New Employer"
    assert resolved.amount == 2500.0
    # Only observations inside the window may be cited as evidence.
    assert set(resolved.evidence_ids) <= {11, 12}


def test_the_floor_never_displaces_the_crew_record():
    """The Crew plan is a provider RECORD, not an observation, so a learning window
    cannot invalidate it. Priority 1 stays priority 1."""
    plan = Plan("Veterans Home", 1663.00, cadence="biweekly", anchor_date="2026-09-04")

    resolved = resolve_expected_paycheck(
        _old_job(), plans=[plan], learning_floor="2026-09-01"
    )

    assert resolved.basis == "crew_plan"
    assert resolved.amount == 1663.00
    assert resolved.plan_id == "plan:1"


def test_the_floor_never_removes_the_owners_configured_figure():
    """A learning reset is not a configuration reset. Clearing the learned window must
    leave the owner's explicit amount intact and usable."""
    configured = PaycheckConfig(cadence="biweekly", amount=1663.00, next_date="2026-10-02")

    resolved = resolve_expected_paycheck(
        [], configured=configured, learning_floor="2026-09-19"
    )

    assert resolved.basis == "configured"
    assert resolved.amount == 1663.00
    assert resolved.source == "manual"


def test_no_floor_leaves_resolution_unchanged():
    """Regression guard: the floor is additive. Absent a floor nothing changes."""
    resolved = resolve_expected_paycheck(_old_job())

    assert resolved.basis == "aggregate"
    assert resolved.learning_floor is None
