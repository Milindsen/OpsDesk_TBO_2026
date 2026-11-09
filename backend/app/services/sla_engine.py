from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Union

PRIORITY_BASE_HOURS = {
    "P1": 4,
    "P2": 8,
    "P3": 24,
    "P4": 48,
}


def _to_datetime(
    val: Optional[Union[date, datetime]], ref_tz: Optional[timezone] = None
) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        if ref_tz and val.tzinfo is None:
            return val.replace(tzinfo=ref_tz)
        if ref_tz is None and val.tzinfo is not None:
            return val.replace(tzinfo=None)
        return val
    # It's a date
    tz = ref_tz
    return datetime.combine(val, time.min, tzinfo=tz)


def compute_urgency_factor(
    check_in_date: Optional[Union[date, datetime]],
    lcd: Optional[Union[date, datetime]],
    now: datetime,
) -> float:
    ref_tz = now.tzinfo
    dt_check_in = _to_datetime(check_in_date, ref_tz)
    dt_lcd = _to_datetime(lcd, ref_tz)

    candidates = [d for d in (dt_check_in, dt_lcd) if d is not None]
    if not candidates:
        return 1.0

    earliest = min(candidates)
    hours_to = (earliest - now).total_seconds() / 3600.0

    if hours_to <= 24:
        return 0.25
    elif hours_to <= 48:
        return 0.5
    elif hours_to <= 72:
        return 0.75
    else:
        return 1.0


def compute_sla_due(
    priority: str,
    created_at: datetime,
    check_in_date: Optional[Union[date, datetime]] = None,
    lcd: Optional[Union[date, datetime]] = None,
) -> datetime:
    base_hours = PRIORITY_BASE_HOURS.get(priority, 24)
    factor = compute_urgency_factor(check_in_date, lcd, created_at)
    return created_at + timedelta(hours=base_hours * factor)


def compute_sla_status(
    sla_due: Optional[datetime],
    now: datetime,
    created_at: Optional[datetime] = None,
) -> str:
    """Returns 'ok', 'at_risk', or 'breached'."""
    if sla_due is None:
        return "ok"

    # Normalize timezones
    if sla_due.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=sla_due.tzinfo)
    elif sla_due.tzinfo is None and now.tzinfo is not None:
        sla_due = sla_due.replace(tzinfo=now.tzinfo)

    if now >= sla_due:
        return "breached"

    remaining = (sla_due - now).total_seconds()

    if remaining < 3600:
        return "at_risk"

    if created_at is not None:
        if created_at.tzinfo is not None and sla_due.tzinfo is None:
            sla_due = sla_due.replace(tzinfo=created_at.tzinfo)
        elif created_at.tzinfo is None and sla_due.tzinfo is not None:
            created_at = created_at.replace(tzinfo=sla_due.tzinfo)
        total = (sla_due - created_at).total_seconds()
        if total > 0 and (remaining / total) <= 0.25:
            return "at_risk"

    return "ok"
