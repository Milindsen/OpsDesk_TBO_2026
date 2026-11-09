from datetime import date, datetime, timedelta, timezone

from app.services.sla_engine import (
    compute_sla_due,
    compute_sla_status,
    compute_urgency_factor,
)


def test_p1_with_check_in_tomorrow() -> None:
    now = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
    check_in = now.date() + timedelta(days=1)  # Tomorrow (24h or less to midnight or 14h away)

    factor = compute_urgency_factor(check_in_date=check_in, lcd=None, now=now)
    assert factor == 0.25

    # P1 base hours = 4. 4 * 0.25 = 1.0 hour
    sla_due = compute_sla_due(
        priority="P1",
        created_at=now,
        check_in_date=check_in,
        lcd=None,
    )
    expected_due = now + timedelta(hours=1)
    assert sla_due == expected_due


def test_p2_with_no_urgency() -> None:
    now = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
    # No check-in, no LCD
    factor = compute_urgency_factor(check_in_date=None, lcd=None, now=now)
    assert factor == 1.0

    # P2 base hours = 8. 8 * 1.0 = 8 hours
    sla_due = compute_sla_due(
        priority="P2",
        created_at=now,
        check_in_date=None,
        lcd=None,
    )
    expected_due = now + timedelta(hours=8)
    assert sla_due == expected_due


def test_sla_status_states() -> None:
    created = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
    due = created + timedelta(hours=4)

    # 1. OK state: plenty of time left (3.5 hours remaining of 4h total window)
    now_ok = created + timedelta(minutes=30)
    assert compute_sla_status(sla_due=due, now=now_ok, created_at=created) == "ok"

    # 2. At Risk state: less than 1 hour remaining (e.g. 45 mins left)
    now_at_risk_1h = due - timedelta(minutes=45)
    assert compute_sla_status(sla_due=due, now=now_at_risk_1h, created_at=created) == "at_risk"

    # 3. At Risk state: <= 25% of window remaining (e.g. for a 24h window, 5h left)
    long_due = created + timedelta(hours=24)
    now_at_risk_pct = created + timedelta(hours=20)  # 4h remaining out of 24h = 16.7% <= 25%
    assert compute_sla_status(sla_due=long_due, now=now_at_risk_pct, created_at=created) == "at_risk"

    # 4. Breached state: current time past due
    now_breached = due + timedelta(minutes=1)
    assert compute_sla_status(sla_due=due, now=now_breached, created_at=created) == "breached"
