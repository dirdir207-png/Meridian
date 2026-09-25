"""OS-104: the cadence is resolved once, in the app's own precedence.

Owner, 2026-09-24: *"payday is the funding mechanism, so the payday and when it lands is the cadence,
this isn't consistent. It still says no cadence detected in places."* The inconsistency was real and
it was a precedence split: `meridian/api.py::_paycheck_config` prefers Crew's funding plan (owner's
directive, 2026-09-19: the paycheck "SHOULD be a crew record"), while the Settings payload reported
the OBSERVED pattern alone, so the Cadence card could read "Not recognized" beside a Crew cadence
listed lower on the same page. These tests pin the resolution and its honesty.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from meridian.services.payday import resolve_cadence


class _Pattern:
    """The shape `recognize_payday` returns, as a payload leg rather than a live recogniser."""

    cadence = "semimonthly"
    next_date = date(2026, 10, 1)
    typical_amount = Decimal("2485.07")
    confidence = 0.86
    evidence_ids = ["a", "b", "c"]


def test_crew_paycheck_outranks_the_observed_pattern():
    """The owner's directive and the backend resolver agree; the card must too."""
    resolved = resolve_cadence(_Pattern(), [{"id": "plan-1", "name": "Paycheck", "cadence": "biweekly"}])
    assert resolved["value"] == "biweekly"
    assert resolved["source"] == "crew"
    assert resolved["plan_id"] == "plan-1"
    assert resolved["plan_name"] == "Paycheck"


def test_the_observed_pattern_is_used_only_when_crew_reports_nothing():
    for plans in ([], [{"id": "p", "name": "Paycheck", "cadence": None}], [{"id": "p", "name": "x"}]):
        resolved = resolve_cadence(_Pattern(), plans)
        assert resolved["source"] == "observed", plans
        assert resolved["value"] == "semimonthly"
        assert resolved["deposits"] == 3
        assert resolved["confidence"] == 0.86


def test_nothing_known_is_reported_as_nothing_rather_than_a_guess():
    resolved = resolve_cadence(None, [])
    assert resolved["value"] is None
    assert resolved["source"] is None
    assert resolved["source_label"] is None
    # An interval Meridian cannot express exactly arrives as None and must stay unrecognised: the
    # shared cadence rule refuses to coerce a provider interval to a nearby one.
    unresolved = resolve_cadence(None, [{"id": "p", "name": "Odd", "cadence": None}])
    assert unresolved["value"] is None


def test_several_crew_records_are_named_rather_than_averaged_away():
    """A single figure must not silently stand in for several records with different schedules."""
    same = resolve_cadence(None, [
        {"id": "p1", "name": "First", "cadence": "biweekly"},
        {"id": "p2", "name": "Second", "cadence": "biweekly"},
    ])
    assert same["conflict"] is False
    assert same["distinct_cadences"] == 1
    assert same["other_records"] == 1

    differing = resolve_cadence(None, [
        {"id": "p1", "name": "First", "cadence": "biweekly"},
        {"id": "p2", "name": "Second", "cadence": "monthly"},
    ])
    assert differing["conflict"] is True
    assert differing["distinct_cadences"] == 2
    assert differing["plan_name"] == "First", "the governing record must be named"


def test_the_payload_carries_one_resolved_cadence_and_the_pattern_separately():
    """Both facts still ship, because "what Crew says" and "what Meridian has seen" differ; only the
    CARD stops choosing the wrong one."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[2] / "meridian/services/payday.py").read_text(
        encoding="utf-8"
    )
    assert '"cadence": resolve_cadence(pattern, funding_plans)' in source
    # And the settings payload builder is the only place that decides it.
    assert source.count("resolve_cadence(") == 2, "one definition, one call site"


def test_the_card_reads_the_resolved_cadence_and_names_its_source():
    """The UI guard: the card binds to the resolved value, and the phrase that asked for an action
    no control could perform is gone for good."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    js = (root / "static/js/meridian/payday.js").read_text(encoding="utf-8")
    html = (root / "templates/meridian/partials/payday-funding.html").read_text(encoding="utf-8")

    assert "payload.cadence" in js
    assert "data-cadence-source" in js and "data-cadence-source" in html
    assert "cadenceSourceText" in js
    # The dead-end instruction is gone, in both the markup and the script.
    for gone in ("Add or confirm your payday timing", "data-pattern-confidence"):
        assert gone not in js, gone
        assert gone not in html, gone
    # Five phrasings of two facts collapse to one each: no stale copy survives anywhere.
    for stale in ("Income unavailable", "No run projected", "not reported"):
        assert stale not in js, stale
