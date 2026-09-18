import json

import pytest

from meridian.proactive import build_financial_weather


def _event(
    event_id,
    day,
    kind,
    amount_minor,
    *,
    title="Event",
    currency="USD",
    funding_status="reserved",
):
    return {
        "id": event_id,
        "date": day,
        "kind": kind,
        "title": title,
        "amount": {"minor": amount_minor, "currency": currency},
        "fundingStatus": funding_status,
        "reserved": None,
        "source": "crew",
        "observedAt": None,
        "evidenceIds": [],
        "detailHref": "/meridian?workspace=plan",
    }


def _dial(*, events=(), available=None, freshness="fresh", today="2026-09-10"):
    return {
        "timezone": "local",
        "today": today,
        "horizonEnd": "2026-10-10",
        "availableToSpend": available,
        "freshness": freshness,
        "observedAt": "2026-09-10T00:00:00Z",
        "events": list(events),
        "projections": [],
    }


def test_steady_when_available_covers_near_term_obligations():
    dial = _dial(
        available={"minor": 200000, "currency": "USD"},
        events=[_event("bill-1", "2026-09-12", "bill", 50000, title="Rent")],
    )
    weather = build_financial_weather(dial)

    assert weather.state == "steady"
    assert weather.confidence == 1.0
    assert [group.key for group in weather.groups] == ["due_soon"]
    due = weather.groups[0]
    assert due.severity == "attention"
    assert due.events[0].title == "Rent"


def test_tight_when_income_is_required_to_cover_obligations():
    dial = _dial(
        available={"minor": 30000, "currency": "USD"},
        events=[
            _event("bill-1", "2026-09-12", "bill", 50000, title="Rent"),
            _event("income-1", "2026-09-15", "income", 100000, title="Paycheck"),
        ],
    )
    weather = build_financial_weather(dial)

    assert weather.state == "tight"
    assert "arrive on time" in weather.explanation


def test_strained_when_obligations_exceed_cash_and_income():
    dial = _dial(
        available={"minor": 10000, "currency": "USD"},
        events=[
            _event("bill-1", "2026-09-12", "bill", 50000, title="Rent"),
            _event("income-1", "2026-09-15", "income", 10000, title="Paycheck"),
        ],
    )
    weather = build_financial_weather(dial)

    assert weather.state == "strained"
    assert weather.confidence == 1.0


def test_stale_freshness_reports_unknown_not_reassuring():
    dial = _dial(
        available={"minor": 500000, "currency": "USD"},
        freshness="stale",
    )
    weather = build_financial_weather(dial)

    assert weather.state == "unknown"
    assert weather.confidence < 1.0
    assert any("freshness" in note for note in weather.assumptions)


def test_missing_available_balance_is_unknown_not_zero():
    dial = _dial()

    weather = build_financial_weather(dial)

    assert weather.state == "unknown"
    assert "available balance is unknown" in weather.assumptions


def test_group_noise_control_caps_events_and_reports_omitted():
    events = [
        _event(f"bill-{n}", "2026-09-12", "bill", 1000, title=f"Bill {n}") for n in range(5)
    ]
    dial = _dial(available={"minor": 100000, "currency": "USD"}, events=events)

    weather = build_financial_weather(dial)

    due = next(group for group in weather.groups if group.key == "due_soon")
    assert len(due.events) == 3
    assert due.omitted == 2


def test_zero_duplicate_and_missing_amount_events_are_suppressed():
    events = [
        _event("bill-1", "2026-09-12", "bill", 0),
        _event("bill-2", "2026-09-12", "bill", 0),
        _event("bill-3", "2026-09-12", "bill", 1000),
        _event("bill-3", "2026-09-12", "bill", 1000),
        {"id": "bill-4", "date": "2026-09-12", "kind": "bill", "title": "No amount"},
    ]
    dial = _dial(available={"minor": 100000, "currency": "USD"}, events=events)

    weather = build_financial_weather(dial)

    due = next(group for group in weather.groups if group.key == "due_soon")
    assert len(due.events) == 1
    assert weather.suppressed == 4


def test_out_of_window_events_are_excluded():
    dial = _dial(
        available={"minor": 100000, "currency": "USD"},
        events=[_event("bill-far", "2026-09-30", "bill", 1000)],
    )

    weather = build_financial_weather(dial, window_days=7)

    assert weather.groups == ()
    assert weather.state == "steady"


def test_mixed_currencies_refuse_to_add():
    dial = _dial(
        available={"minor": 100000, "currency": "USD"},
        events=[_event("bill-eur", "2026-09-12", "bill", 5000, currency="EUR")],
    )

    weather = build_financial_weather(dial)

    assert weather.state == "unknown"
    assert "near-term amounts span multiple currencies" in weather.assumptions


def test_funding_gap_group_flags_unfunded_obligations():
    dial = _dial(
        available={"minor": 100000, "currency": "USD"},
        events=[
            _event(
                "bill-1",
                "2026-09-12",
                "bill",
                5000,
                title="Rent",
                funding_status="unfunded",
            )
        ],
    )

    weather = build_financial_weather(dial)

    gap = next(group for group in weather.groups if group.key == "funding_gaps")
    assert gap.severity == "attention"
    assert "no money reserved" in gap.events[0].explanation


def test_window_days_must_be_a_positive_integer():
    with pytest.raises(ValueError):
        build_financial_weather(_dial(), window_days=0)
    with pytest.raises(ValueError):
        build_financial_weather(_dial(), window_days=True)


def test_to_dict_is_json_serializable():
    dial = _dial(
        available={"minor": 200000, "currency": "USD"},
        events=[_event("bill-1", "2026-09-12", "bill", 50000, title="Rent")],
    )

    payload = build_financial_weather(dial).to_dict()

    assert json.loads(json.dumps(payload))["state"] == "steady"
    assert payload["groups"][0]["events"][0]["amount_minor"] == 50000
