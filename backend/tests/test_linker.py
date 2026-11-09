import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.ticket_linker import find_links


def test_same_tboh_produces_strong_link() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()

    new_ticket = SimpleNamespace(
        id=t1_id,
        tboh="TBO12345",
        agency_id=uuid.uuid4(),
        intent="refund",
        created_at=now,
    )
    existing_ticket = SimpleNamespace(
        id=t2_id,
        tboh="TBO12345",
        agency_id=uuid.uuid4(),  # Even if different agency, same TBOH is strong
        intent="amendment",
        created_at=now - timedelta(days=2),
    )

    links = find_links(new_ticket, [existing_ticket])
    assert len(links) == 1
    assert links[0].target_id == t2_id
    assert links[0].link_type == "strong"
    assert links[0].score == 1.0
    assert "TBO12345" in links[0].reason


def test_same_agency_and_intent_within_30_days_medium_link() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    agency_id = uuid.uuid4()
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()

    new_ticket = SimpleNamespace(
        id=t1_id,
        tboh="TBO11111",
        agency_id=agency_id,
        intent="refund",
        created_at=now,
    )
    existing_ticket = SimpleNamespace(
        id=t2_id,
        tboh="TBO22222",  # Different TBOH
        agency_id=agency_id,
        intent="refund",  # Same intent
        created_at=now - timedelta(days=15),  # 15 days <= 30 days
    )

    links = find_links(new_ticket, [existing_ticket])
    assert len(links) == 1
    assert links[0].target_id == t2_id
    assert links[0].link_type == "medium"
    assert links[0].score == 0.7


def test_different_agency_produces_no_link() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()

    new_ticket = SimpleNamespace(
        id=t1_id,
        tboh="TBO11111",
        agency_id=uuid.uuid4(),
        intent="refund",
        created_at=now,
    )
    existing_ticket = SimpleNamespace(
        id=t2_id,
        tboh="TBO22222",
        agency_id=uuid.uuid4(),  # Different agency
        intent="refund",
        created_at=now - timedelta(days=2),
    )

    links = find_links(new_ticket, [existing_ticket])
    assert len(links) == 0
