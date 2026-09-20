"""OS-060: a bill the observed reserve cannot cover is stated as an exposure.

The owner's real problem, in their own data: the reserve is a ONE-WAY LOCK -- money goes
in and cannot be transferred back out -- and a bill can EXCEED the reserve earmarked for
it. Meridian showed the funded figure but never the gap, so a bill the reserve could not
cover read as "funded" when it was not *covered*. That is the whole defect: "funded" was
being presented where the owner needs "covered".

The owner approved this slice CONDITIONALLY (2026-09-20): *"if its something you can do,
and the visual display of it is easy to understand and informative, then absolutely."*
A display that reads as a warning, nags, or implies the reserve can be topped up has
failed that condition even if its arithmetic is right. The tests below therefore guard
the legibility rules as hard as the arithmetic:

* a bill reporting ``0.00`` reserved IS normal (funded is not covered, D-015) and must
  show NOTHING -- this is the false positive that would turn Today into a wall of
  "uncovered" markers, and four live bills read exactly that way;
* a bill whose reserve was never reported has no observed figure to subtract, so there
  is no gap to state and it must be excluded rather than defaulted to zero;
* an already-covered bill shows nothing;
* nothing is ever re-targeted at a gap, and no source to draw from is named.
"""

from meridian.commitments import CommitmentRepository, CommitmentType
from meridian.db import run_migrations
from meridian.repository import FinancialRepository
from meridian.services.today import _coverage_exposure, build_today


def _repositories(tmp_path):
    db = str(tmp_path / "m.db")
    run_migrations(db)
    return FinancialRepository(db), CommitmentRepository(db)


def _bill(commitments, *, name="Rent", amount=1442.0, reserved=None, reported=None):
    """A bill as the sync would have stored it.

    ``reported`` defaults to "a reserve figure was observed" (``reserved is not None``),
    because that flag is what distinguishes a reported 0 from silence and the
    ``commitments`` column is NOT NULL DEFAULT 0.
    """
    fields = {
        "type": CommitmentType.BILL,
        "name": name,
        "amount": amount,
        "currency": "USD",
        "recurrence": "monthly",
        "due_date": "2026-09-16",
    }
    if reserved is not None:
        fields["funded_amount"] = reserved
    if reported is not None:
        fields["reserved_amount_reported"] = reported
    return commitments.create(**fields)


# --------------------------------------------------------------------------------------
# The gap is stated when, and only when, it was observed.
# --------------------------------------------------------------------------------------


def test_a_bill_the_reserve_cannot_cover_states_the_gap(tmp_path):
    """The live Rent case: 1442.00 needed, 1097.10 set aside, 344.90 not covered."""
    _, commitments = _repositories(tmp_path)
    _bill(commitments, name="Rent", amount=1442.0, reserved=1097.1)

    exposure = _coverage_exposure(commitments)

    assert exposure["count"] == 1
    assert exposure["items"][0]["name"] == "Rent"
    assert exposure["items"][0]["amount"] == 1442.0
    assert exposure["items"][0]["reserved"] == 1097.1
    assert exposure["items"][0]["gap"] == 344.9


def test_a_bill_reporting_zero_reserved_is_not_an_exposure(tmp_path):
    """The false positive this slice must never produce.

    A reported ``0.00`` means "not funded yet" -- funded is not covered (D-015) -- and
    the reserve simply has not been filled. Flagging it would read as a shortfall. Four
    live bills (Eversource, Verizon, Xfinity, Verizon Payment Arrangement) read exactly
    this way, so the broader ``funded < amount`` test would mark all of them uncovered.

    ``reported=True`` is REQUIRED here and is not decoration: without it the bill is
    excluded by the *unreported* guard instead, and this test would pass while proving
    nothing about the ``reserved > 0`` rule. (Found by falsification -- removing that
    rule left this test green until the flag was set.)
    """
    _, commitments = _repositories(tmp_path)
    _bill(commitments, name="Eversource", amount=210.0, reserved=0.0, reported=True)

    exposure = _coverage_exposure(commitments)

    assert exposure["count"] == 0
    assert exposure["items"] == []


def test_a_bill_whose_reserve_was_never_reported_is_excluded(tmp_path):
    """No observed figure means no gap to state -- absence is not a report of zero."""
    _, commitments = _repositories(tmp_path)
    _bill(commitments, name="Unknown", amount=500.0, reserved=None, reported=False)

    exposure = _coverage_exposure(commitments)

    assert exposure["count"] == 0


def test_an_unreported_figure_is_never_subtracted_even_if_one_is_present():
    """The ``reserved_amount_reported`` gate, and an honest note about its reach.

    ``commitments._validate`` normalises any positive ``funded_amount`` to
    ``reserved_amount_reported=True`` and an unreported read stores ``0.0``, so every
    state reachable through the repositories is already caught by the ``reserved > 0``
    rule -- removing this gate changes nothing today, which falsification confirmed.
    It is kept as defence in depth and pinned here by handing the rule a row a future
    change could produce (a populated figure with the flag unset): the number must NOT
    be subtracted, because an unreported figure is not an observation and absence is
    never a report of zero (C01).
    """

    class _Row:
        type = CommitmentType.BILL
        id = 1
        name = "Local"
        currency = "USD"
        amount = 500.0
        target_amount = 500.0
        funded_amount = 200.0
        reserved_amount_reported = False

    class _Repo:
        @staticmethod
        def list_active():
            return [_Row()]

    assert _coverage_exposure(_Repo())["count"] == 0


def test_a_fully_covered_bill_is_excluded(tmp_path):
    _, commitments = _repositories(tmp_path)
    _bill(commitments, name="Covered", amount=100.0, reserved=100.0)
    _bill(commitments, name="Over", amount=100.0, reserved=150.0)

    exposure = _coverage_exposure(commitments)

    assert exposure["count"] == 0


def test_exactly_one_cent_uncovered_still_counts(tmp_path):
    """The boundary is strict inequality, and it is inclusive of the smallest gap."""
    _, commitments = _repositories(tmp_path)
    _bill(commitments, name="Almost", amount=100.0, reserved=99.99)

    exposure = _coverage_exposure(commitments)

    assert exposure["count"] == 1
    assert exposure["items"][0]["gap"] == 0.01


def test_only_bills_are_exposed_not_goals_or_reserves(tmp_path):
    """A goal is not backed by a bill reserve, so this rule does not apply to it."""
    _, commitments = _repositories(tmp_path)
    commitments.create(
        type=CommitmentType.GOAL,
        name="Holiday",
        target_amount=1000.0,
        amount=1000.0,
        currency="USD",
        funded_amount=10.0,
    )

    exposure = _coverage_exposure(commitments)

    assert exposure["count"] == 0


def test_the_largest_gap_is_listed_first(tmp_path):
    """Ordering is by gap descending, so the line's lead figure is the biggest exposure."""
    _, commitments = _repositories(tmp_path)
    _bill(commitments, name="Small", amount=100.0, reserved=90.0)
    _bill(commitments, name="Big", amount=1442.0, reserved=1097.1)
    _bill(commitments, name="Medium", amount=500.0, reserved=400.0)

    exposure = _coverage_exposure(commitments)

    assert [item["name"] for item in exposure["items"]] == ["Big", "Medium", "Small"]


def test_no_commitment_repository_yields_no_exposure(tmp_path):
    """A caller without commitments has nothing to state, and never a fabricated zero."""
    assert _coverage_exposure(None) is None


# --------------------------------------------------------------------------------------
# Through the real Today payload.
# --------------------------------------------------------------------------------------


def test_today_payload_carries_the_exposure(tmp_path):
    repository, commitments = _repositories(tmp_path)
    _bill(commitments, name="Rent", amount=1442.0, reserved=1097.1)
    _bill(commitments, name="Eversource", amount=210.0, reserved=0.0, reported=True)

    payload = build_today(repository, commitments, None)

    assert payload["reserve_exposure"]["count"] == 1
    item = payload["reserve_exposure"]["items"][0]
    assert item["name"] == "Rent"
    assert item["gap"] == 344.9


def test_today_payload_exposes_nothing_when_no_bill_is_short(tmp_path):
    """An explicit empty, so a consumer can never render a figure it was not given."""
    repository, commitments = _repositories(tmp_path)
    _bill(commitments, name="Eversource", amount=210.0, reserved=0.0, reported=True)

    payload = build_today(repository, commitments, None)

    assert payload["reserve_exposure"] == {"count": 0, "items": []}


def test_today_without_commitments_reports_no_exposure(tmp_path):
    repository, _ = _repositories(tmp_path)

    payload = build_today(repository)

    assert payload["reserve_exposure"] is None


def test_the_exposure_does_not_change_safe_to_spend(tmp_path):
    """A display-only slice: stating a gap must not move any other number.

    The shortfall is a fact to state, never a condition to repair -- nothing is
    re-targeted at it, and no figure is deducted or reserved because of it.
    """
    repository, commitments = _repositories(tmp_path)
    _bill(commitments, name="Eversource", amount=210.0, reserved=0.0, reported=True)
    before = build_today(repository, commitments, None)["safe_to_spend"]
    assert before["inputs"]["known_obligations"] == 210.0

    _bill(commitments, name="Rent", amount=1442.0, reserved=1097.1)
    after = build_today(repository, commitments, None)

    assert after["reserve_exposure"]["count"] == 1
    # The gap is 344.90, and known obligations move by exactly Rent's own unfunded
    # remainder (1442.00 - 1097.10), because that total counts each bill's shortfall
    # rather than its full amount. So the exposure is not a second deduction: the
    # shortfall was ALREADY inside known obligations. Stating it changes no number --
    # it only names what was already counted.
    rent_gap = 344.9
    assert after["safe_to_spend"]["inputs"]["known_obligations"] == (
        before["inputs"]["known_obligations"] + rent_gap
    )
    assert after["reserve_exposure"]["items"][0]["gap"] == rent_gap
