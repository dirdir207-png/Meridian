"""The dated-occurrence rule, pinned.

These tests exist because the codebase previously answered "what is the next
occurrence?" six different ways, and three of them disagreed. Each drift case
below is a measured defect that shipped:

  * monthly on the 31st stuck on the 28th forever (Feb clamp became the anchor);
  * semimonthly was a flat +15 days and walked off the calendar;
  * annual Feb 29 collapsed to Feb 28 permanently after one non-leap year;
  * payday's semimonthly branch was unreachable behind the biweekly window.

Date arithmetic only: no provider, database, credential or money is involved.
"""

from datetime import date

import pytest

from meridian.cadence import (
    MONTHLY,
    SEMIMONTHLY,
    advance,
    advance_by_periods,
    next_occurrence,
    normalize,
    supported,
)


def sequence(anchor, recurrence, periods=6):
    """The anchored sequence: the anchor, then each step measured from it.

    ``advance(..., 0)`` is deliberately None (a zero-period advance is not a
    date), so the anchor itself is prepended rather than requested as period 0.
    """
    return [anchor] + [advance(anchor, recurrence, n) for n in range(1, periods)]


# --- monthly: the clamp must not become the anchor ---------------------------


def test_monthly_anchor_on_the_31st_returns_to_the_31st():
    """The original defect: Jan 31 clamped to Feb 28 and stayed on the 28th.

    The day is a property of the anchor, not of the previous occurrence, so a
    short month clips and the next long month restores the 31st.
    """
    assert sequence(date(2026, 1, 31), MONTHLY) == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
        date(2026, 5, 31),
        date(2026, 6, 30),
    ]


def test_monthly_anchor_on_the_30th_only_clips_in_february():
    assert sequence(date(2026, 1, 30), MONTHLY) == [
        date(2026, 1, 30),
        date(2026, 2, 28),
        date(2026, 3, 30),
        date(2026, 4, 30),
        date(2026, 5, 30),
        date(2026, 6, 30),
    ]


def test_monthly_leap_february_clip_is_29_not_28():
    """2028 is a leap year, so the February clip is the 29th."""
    assert advance(date(2028, 1, 31), MONTHLY) == date(2028, 2, 29)
    # ...and the anchor is still the 31st afterwards.
    assert advance(date(2028, 1, 31), MONTHLY, 2) == date(2028, 3, 31)


def test_monthly_crosses_a_year_boundary():
    assert advance(date(2026, 12, 31), MONTHLY) == date(2027, 1, 31)
    assert advance(date(2026, 1, 15), MONTHLY, 13) == date(2027, 2, 15)


def test_monthly_mid_month_day_is_never_clipped():
    assert sequence(date(2026, 1, 15), MONTHLY) == [
        date(2026, 1, 15),
        date(2026, 2, 15),
        date(2026, 3, 15),
        date(2026, 4, 15),
        date(2026, 5, 15),
        date(2026, 6, 15),
    ]


# --- semimonthly: the 15th and the last day, not +15 days --------------------


def test_semimonthly_is_the_15th_and_the_last_day_of_the_month():
    """The original defect: a flat +15 days gave Jan 15 -> Jan 30 -> Feb 14 -> Mar 1."""
    assert sequence(date(2026, 1, 15), SEMIMONTHLY) == [
        date(2026, 1, 15),
        date(2026, 1, 31),
        date(2026, 2, 15),
        date(2026, 2, 28),
        date(2026, 3, 15),
        date(2026, 3, 31),
    ]


def test_semimonthly_from_the_last_day_moves_to_the_next_15th():
    assert advance(date(2026, 1, 31), SEMIMONTHLY) == date(2026, 2, 15)
    assert advance(date(2026, 2, 28), SEMIMONTHLY) == date(2026, 3, 15)


def test_semimonthly_never_returns_its_own_input():
    """A non-advancing step would spin every caller's roll-forward loop."""
    for day in (1, 14, 15, 16, 27, 28, 30, 31):
        anchor = date(2026, 1, min(day, 31))
        assert advance(anchor, SEMIMONTHLY) > anchor


def test_semimonthly_from_before_the_15th_lands_on_the_15th():
    assert advance(date(2026, 1, 3), SEMIMONTHLY) == date(2026, 1, 15)


def test_semimonthly_february_uses_the_real_month_end():
    assert advance(date(2026, 2, 15), SEMIMONTHLY) == date(2026, 2, 28)
    assert advance(date(2028, 2, 15), SEMIMONTHLY) == date(2028, 2, 29)


# --- annual: Feb 29 must come back ------------------------------------------


def test_annual_feb_29_recovers_in_the_next_leap_year():
    """The original defect: date(y+1, 2, 29) raised, and the fallback to Feb 28
    was permanent, so the 29th never returned."""
    assert advance(date(2024, 2, 29), "annually") == date(2025, 2, 28)
    assert advance(date(2024, 2, 29), "annually", 2) == date(2026, 2, 28)
    assert advance(date(2024, 2, 29), "annually", 4) == date(2028, 2, 29)


# --- weekly / biweekly -------------------------------------------------------


def test_weekly_and_biweekly_are_plain_day_arithmetic():
    assert advance(date(2026, 1, 15), "weekly") == date(2026, 1, 22)
    assert advance(date(2026, 1, 15), "biweekly") == date(2026, 1, 29)
    assert advance(date(2026, 1, 15), "weekly", 3) == date(2026, 2, 5)


# --- vocabulary: one spelling set, no silent default ------------------------


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("month", MONTHLY),
        ("MONTHLY", MONTHLY),
        ("  monthly  ", MONTHLY),
        ("week", "weekly"),
        ("bi-weekly", "biweekly"),
        ("fortnight", "biweekly"),
        ("twice-monthly", SEMIMONTHLY),
        ("semi-monthly", SEMIMONTHLY),
        ("yearly", "annually"),
        ("annual", "annually"),
    ],
)
def test_alias_spellings_resolve_to_one_canonical_name(alias, canonical):
    assert normalize(alias) == canonical


@pytest.mark.parametrize("value", ["", None, "hourly", "every other tuesday", 7])
def test_unknown_recurrence_is_not_silently_defaulted(value):
    """An unrecognised recurrence must be visible, never quietly become weekly."""
    assert normalize(value) is None
    assert supported(value) is False
    assert advance(date(2026, 1, 15), value) is None


def test_advance_rejects_a_non_positive_period_count():
    assert advance(date(2026, 1, 15), MONTHLY, 0) is None
    assert advance(date(2026, 1, 15), MONTHLY, -1) is None


# --- next_occurrence: anchor-preserving walk --------------------------------


def test_next_occurrence_does_not_snap_a_clamped_month_forward_permanently():
    """The regression that matters: an intervening February must not rewrite the day."""
    assert next_occurrence(date(2026, 1, 31), MONTHLY, date(2026, 4, 1)) == date(2026, 4, 30)
    assert next_occurrence(date(2026, 1, 31), MONTHLY, date(2026, 3, 1)) == date(2026, 3, 31)


def test_next_occurrence_returns_the_anchor_when_not_yet_due():
    assert next_occurrence(date(2026, 9, 1), MONTHLY, date(2026, 8, 1)) == date(2026, 9, 1)


def test_next_occurrence_returns_an_unknown_recurrence_unchanged():
    """A non-recurring date is a single literal occurrence."""
    assert next_occurrence(date(2026, 1, 5), "one-off", date(2026, 8, 1)) == date(2026, 1, 5)


def test_next_occurrence_semimonthly_rolls_through_month_ends():
    assert next_occurrence(date(2026, 1, 15), SEMIMONTHLY, date(2026, 2, 16)) == date(2026, 2, 28)
    assert next_occurrence(date(2026, 1, 15), SEMIMONTHLY, date(2026, 3, 1)) == date(2026, 3, 15)


def test_next_occurrence_handles_a_long_dormant_anchor():
    """A years-old anchor must still land on the right day, not drift."""
    rolled = next_occurrence(date(2020, 1, 31), MONTHLY, date(2026, 5, 1))
    assert rolled == date(2026, 5, 31)


# --- advance_by_periods: the interval-multiplier form -----------------------


def test_advance_by_periods_multiplies_weekly_intervals():
    assert advance_by_periods(date(2026, 1, 15), "weekly", 3) == date(2026, 2, 5)
    assert advance_by_periods(date(2026, 1, 15), "biweekly", 2) == date(2026, 2, 12)


def test_advance_by_periods_monthly_keeps_the_anchor_day():
    assert advance_by_periods(date(2026, 1, 31), MONTHLY, 2) == date(2026, 3, 31)


def test_advance_by_periods_ignores_a_multiplier_for_semimonthly():
    """Semimonthly has no integer multiplier ladder; one slot is one slot."""
    assert advance_by_periods(date(2026, 1, 15), SEMIMONTHLY, 5) == date(2026, 1, 31)


def test_advance_by_periods_treats_a_zero_interval_as_one():
    assert advance_by_periods(date(2026, 1, 15), "weekly", 0) == date(2026, 1, 22)
