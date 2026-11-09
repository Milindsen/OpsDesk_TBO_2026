import uuid
from datetime import datetime, time, timezone
from types import SimpleNamespace

from app.services.routing_engine import pick_agent, score_agent


def test_region_match_scoring() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    agent = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="Agent IN-West",
        region="IN-West",
        shift_start=time(9, 0),
        shift_end=time(18, 0),
        availability=True,
    )
    ticket_match = SimpleNamespace(
        region="IN-West",
        priority="P3",
    )
    ticket_mismatch = SimpleNamespace(
        region="ME",
        priority="P3",
    )

    score_match = score_agent(agent, ticket_match, open_counts={}, now=now)
    score_mismatch = score_agent(agent, ticket_mismatch, open_counts={}, now=now)

    assert score_match["breakdown"]["region"] == 40
    assert score_mismatch["breakdown"]["region"] == 0
    assert score_match["score"] - score_mismatch["score"] == 40


def test_agent_out_of_shift_gets_zero_points() -> None:
    # 20:00 is outside 09:00 - 18:00
    now_evening = datetime(2026, 11, 6, 20, 0, tzinfo=timezone.utc)
    now_daytime = datetime(2026, 11, 6, 11, 0, tzinfo=timezone.utc)

    agent = SimpleNamespace(
        id=uuid.uuid4(),
        full_name="Agent Shifts",
        region="IN-West",
        shift_start=time(9, 0),
        shift_end=time(18, 0),
        availability=True,
    )
    ticket = SimpleNamespace(region="IN-West", priority="P3")

    score_out_of_shift = score_agent(agent, ticket, open_counts={}, now=now_evening)
    assert score_out_of_shift["breakdown"]["in_shift"] == 0

    score_in_shift = score_agent(agent, ticket, open_counts={}, now=now_daytime)
    assert score_in_shift["breakdown"]["in_shift"] == 20


def test_lowest_load_wins_tie_breaker() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    agent_a_id = uuid.uuid4()
    agent_b_id = uuid.uuid4()

    agent_a = SimpleNamespace(
        id=agent_a_id,
        full_name="Agent Busy",
        region="IN-West",
        shift_start=time(9, 0),
        shift_end=time(18, 0),
        availability=True,
    )
    agent_b = SimpleNamespace(
        id=agent_b_id,
        full_name="Agent Free",
        region="IN-West",
        shift_start=time(9, 0),
        shift_end=time(18, 0),
        availability=True,
    )

    ticket = SimpleNamespace(region="IN-West", priority="P2")

    # Agent A has 4 open tickets (load score = max(0, 25 - 4*5) = 5)
    # Agent B has 0 open tickets (load score = max(0, 25 - 0*5) = 25)
    open_counts = {
        str(agent_a_id): 4,
        str(agent_b_id): 0,
    }

    best, scored, reason = pick_agent(
        [agent_a, agent_b], ticket, open_counts, now
    )

    assert best["agent_id"] == str(agent_b_id)
    assert best["name"] == "Agent Free"
    assert best["breakdown"]["load"] == 25
    assert "low load (+25; 0 open tickets)" in reason


def test_unavailable_agents_are_excluded_and_ticket_stays_in_triage() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    unavailable = SimpleNamespace(
        id=uuid.uuid4(), full_name="Unavailable Agent", region="IN-West",
        shift_start=time(9, 0), shift_end=time(18, 0), availability=False,
    )
    ticket = SimpleNamespace(region="IN-West", priority="P1")
    best, scored, reason = pick_agent([unavailable], ticket, {}, now)
    assert best is None
    assert scored == []
    assert "remains in Triage" in reason


def test_out_of_shift_agents_are_excluded_from_assignment() -> None:
    now = datetime(2026, 11, 6, 20, 0, tzinfo=timezone.utc)
    out_of_shift = SimpleNamespace(
        id=uuid.uuid4(), full_name="Off Shift Agent", region="IN-West",
        shift_start=time(9, 0), shift_end=time(18, 0), availability=True,
    )
    ticket = SimpleNamespace(region="IN-West", priority="P1")
    best, scored, reason = pick_agent([out_of_shift], ticket, {}, now)
    assert best is None
    assert scored == []
    assert "remains in Triage" in reason


def test_database_open_ticket_counts_override_stale_cached_load() -> None:
    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    agent = SimpleNamespace(
        id=uuid.uuid4(), full_name="Agent With Stale Cache", region="IN-West",
        shift_start=time(9, 0), shift_end=time(18, 0), availability=True, current_load=12,
    )
    ticket = SimpleNamespace(region="IN-West", priority="P2")
    result = score_agent(agent, ticket, open_counts={}, now=now)
    assert result["open_load"] == 0
    assert result["breakdown"]["load"] == 25
