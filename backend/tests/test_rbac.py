import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.agency import Agency
from app.models.ticket import Ticket
from app.models.ticket_link import TicketLink
from app.models.comment import TicketComment
from app.models.theme import Theme, TicketTheme
from app.models.timeline import TimelineEvent
from app.models.side_conversation import SideConversation, SideRecipient
from app.models.user import User


def test_requester_cannot_access_other_agency_ticket(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    # Ticket belonging to Sunrise (Agency B)
    ticket_b = Ticket(
        id=uuid.uuid4(),
        title="Sunrise booking issue",
        description="Ticket belonging to Sunrise",
        agency_id=seed_agencies["sunrise"].id,
        tboh="TBO88888",
        priority="P3",
        intent="refund",
        status="Open",
        region="IN-East",
        contact_count=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(ticket_b)
    db_session.commit()

    # Requester A (Horizons) tries to GET Ticket B
    headers_a = auth_headers["requester_a"]
    res = test_client.get(f"/api/v1/tickets/{ticket_b.id}", headers=headers_a)
    assert res.status_code in [403, 404]

    # Requester A lists tickets - should NOT see Ticket B
    list_res = test_client.get("/api/v1/tickets", headers=headers_a)
    assert list_res.status_code == 200
    item_ids = [item["id"] for item in list_res.json()["items"]]
    assert str(ticket_b.id) not in item_ids


def test_agent_can_access_any_ticket(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(),
        title="Agency Ticket",
        description="Any agency ticket",
        agency_id=seed_agencies["sunrise"].id,
        tboh="TBO77777",
        priority="P2",
        intent="cancellation",
        status="Open",
        region="IN-East",
        contact_count=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(ticket)
    db_session.commit()

    agent_headers = auth_headers["agent1"]
    res = test_client.get(f"/api/v1/tickets/{ticket.id}", headers=agent_headers)
    assert res.status_code == 200
    assert res.json()["id"] == str(ticket.id)


def test_requester_cannot_escalate_and_agent_can(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(),
        title="Escalation Target",
        description="Testing escalation RBAC",
        agency_id=seed_agencies["horizons"].id,
        tboh="TBO33333",
        priority="P2",
        intent="supplier_issue",
        status="Open",
        region="IN-West",
        contact_count=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(ticket)
    db_session.commit()

    em = seed_users["em"]
    escalate_payload = {
        "escalation_manager_id": str(em.id),
        "reason": "Direct escalation test",
    }

    # 1. Requester attempt to escalate -> 403 Forbidden
    res_req = test_client.post(
        f"/api/v1/tickets/{ticket.id}/escalate",
        json=escalate_payload,
        headers=auth_headers["requester_a"],
    )
    assert res_req.status_code == 403

    # 2. Agent attempt to escalate -> 200 OK
    res_agent = test_client.post(
        f"/api/v1/tickets/{ticket.id}/escalate",
        json=escalate_payload,
        headers=auth_headers["agent1"],
    )
    assert res_agent.status_code == 200
    assert res_agent.json()["status"] == "Escalated"


def test_requester_cannot_read_staff_directory(
    test_client: TestClient, auth_headers: Dict[str, Dict[str, str]]
) -> None:
    response = test_client.get("/api/v1/users?role=agent", headers=auth_headers["requester_a"])
    assert response.status_code == 403


def test_staff_can_read_staff_directory(
    test_client: TestClient, auth_headers: Dict[str, Dict[str, str]]
) -> None:
    response = test_client.get("/api/v1/users?role=agent", headers=auth_headers["agent1"])
    assert response.status_code == 200
    assert all(user["role"] == "agent" for user in response.json())


def test_requester_does_not_receive_cross_agency_linked_ticket_details(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    own_ticket = Ticket(
        id=uuid.uuid4(), title="My agency refund", description="Own case",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-LINK-1",
        priority="P2", intent="refund", status="Open", region="IN-West",
        contact_count=1, created_at=now, updated_at=now,
    )
    other_ticket = Ticket(
        id=uuid.uuid4(), title="Other agency refund", description="Private case",
        agency_id=seed_agencies["sunrise"].id, tboh="TBO-LINK-1",
        priority="P2", intent="refund", status="Open", region="IN-East",
        contact_count=1, created_at=now, updated_at=now,
    )
    db_session.add_all([own_ticket, other_ticket])
    db_session.flush()
    db_session.add(TicketLink(
        id=uuid.uuid4(), source_id=own_ticket.id, target_id=other_ticket.id,
        link_type="strong", reason="Same TBOH", score=1.0, created_at=now,
    ))
    db_session.commit()

    response = test_client.get(
        f"/api/v1/tickets/{own_ticket.id}/links",
        headers=auth_headers["requester_a"],
    )
    assert response.status_code == 200
    assert response.json() == []

    requester_linked_queue = test_client.get(
        "/api/v1/tickets?has_links=true",
        headers=auth_headers["requester_a"],
    )
    assert requester_linked_queue.status_code == 200
    assert all(row["id"] != str(own_ticket.id) for row in requester_linked_queue.json()["items"])

    staff_linked_queue = test_client.get(
        "/api/v1/tickets?has_links=true",
        headers=auth_headers["agent1"],
    )
    assert staff_linked_queue.status_code == 200
    assert str(own_ticket.id) in {row["id"] for row in staff_linked_queue.json()["items"]}


def test_requester_cannot_create_internal_ticket_comment(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="Comment permissions", description="Test",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-COMMENT-1",
        priority="P3", intent="refund", status="Open", region="IN-West",
        contact_count=1, created_at=now, updated_at=now,
    )
    db_session.add(ticket)
    db_session.commit()

    response = test_client.post(
        f"/api/v1/tickets/{ticket.id}/comments",
        json={"body": "Private internal note", "visibility": "internal"},
        headers=auth_headers["requester_a"],
    )
    assert response.status_code == 403


def test_requester_only_sees_public_ticket_comments(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="Public and private comments", description="Test",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-COMMENT-2",
        priority="P3", intent="refund", status="Open", region="IN-West",
        contact_count=1, created_at=now, updated_at=now,
    )
    db_session.add(ticket)
    db_session.flush()
    db_session.add_all([
        TicketComment(ticket_id=ticket.id, author_id=seed_users["agent1"].id, author_name="Agent One", body="Public update", visibility="public", created_at=now),
        TicketComment(ticket_id=ticket.id, author_id=seed_users["agent1"].id, author_name="Agent One", body="Internal note", visibility="internal", created_at=now),
    ])
    db_session.commit()

    response = test_client.get(
        f"/api/v1/tickets/{ticket.id}/comments",
        headers=auth_headers["requester_a"],
    )
    assert response.status_code == 200
    bodies = [comment["body"] for comment in response.json()]
    assert bodies == ["Public update"]


def test_requester_timeline_hides_internal_notes_and_side_conversation_metadata(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="Timeline privacy", description="Test",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-TIMELINE-1",
        priority="P2", intent="refund", status="Open", region="IN-West",
        routing_reason="Private routing score details", product_bug_link="https://internal.example/BUG-9", contact_count=1,
        created_at=now, updated_at=now,
    )
    db_session.add(ticket)
    db_session.flush()
    db_session.add_all([
        TimelineEvent(ticket_id=ticket.id, actor_name="Agent", event_type="status_change", payload={"from": "New", "to": "Open", "note": "Private handover context"}, created_at=now),
        TimelineEvent(ticket_id=ticket.id, actor_name="Agent", event_type="ticket_comment", payload={"visibility": "internal", "preview": "confidential note"}, created_at=now),
        TimelineEvent(ticket_id=ticket.id, actor_name="Agent", event_type="side_convo", payload={"recipients": ["supplier@example.com"]}, created_at=now),
    ])
    db_session.commit()

    detail = test_client.get(f"/api/v1/tickets/{ticket.id}", headers=auth_headers["requester_a"])
    assert detail.status_code == 200
    assert detail.json()["routing_reason"] is None
    assert detail.json()["product_bug_link"] is None
    assert all(event["event_type"] == "status_change" for event in detail.json()["timeline"])
    assert all("note" not in event["payload"] for event in detail.json()["timeline"])

    timeline = test_client.get(f"/api/v1/tickets/{ticket.id}/timeline", headers=auth_headers["requester_a"])
    assert timeline.status_code == 200
    assert all(event["event_type"] == "status_change" for event in timeline.json())
    assert all("note" not in event["payload"] for event in timeline.json())


def test_intent_suggestion_requires_authentication(test_client: TestClient) -> None:
    response = test_client.post(
        "/api/v1/intent/suggest",
        json={"title": "Refund not received", "description": "Customer waiting for refund"},
    )
    assert response.status_code == 401


def test_escalation_manager_only_accesses_tickets_assigned_to_them(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="EM queue scope", description="Test",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-EM-SCOPE",
        priority="P2", intent="refund", status="Open", region="IN-West",
        assignee_id=seed_users["agent1"].id, contact_count=1,
        created_at=now, updated_at=now,
    )
    db_session.add(ticket)
    db_session.commit()

    em_headers = auth_headers["em"]
    denied = test_client.get(f"/api/v1/tickets/{ticket.id}", headers=em_headers)
    assert denied.status_code == 404

    ticket.assignee_id = seed_users["em"].id
    ticket.status = "Escalated"
    db_session.commit()
    allowed = test_client.get(f"/api/v1/tickets/{ticket.id}", headers=em_headers)
    assert allowed.status_code == 200


def test_escalation_manager_cannot_create_new_ticket(
    test_client: TestClient, auth_headers: Dict[str, Dict[str, str]]
) -> None:
    response = test_client.post(
        "/api/v1/tickets",
        json={
            "title": "New ticket", "description": "Should be blocked for EM",
            "tboh": "TBO-EM-CREATE", "priority": "P2", "intent": "refund",
            "region": "IN-West",
        },
        headers=auth_headers["em"],
    )
    assert response.status_code == 403


def test_ticket_queue_refreshes_stale_sla_status(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="Stale SLA status", description="Test queue SLA refresh",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-SLA-QUEUE",
        priority="P1", intent="refund", status="Open", region="IN-West",
        sla_due=now - timedelta(minutes=5), sla_status="ok", contact_count=1,
        created_at=now - timedelta(hours=2), updated_at=now - timedelta(hours=1),
    )
    db_session.add(ticket)
    db_session.commit()

    response = test_client.get("/api/v1/tickets", headers=auth_headers["agent1"])
    assert response.status_code == 200
    row = next(item for item in response.json()["items"] if item["id"] == str(ticket.id))
    assert row["sla_status"] == "breached"


def test_side_conversation_recipients_survive_ticket_reassignment(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="Supplier recipient preservation", description="Test",
        agency_id=seed_agencies["peak"].id, tboh="TBO-SIDE-TRANSFER",
        priority="P2", intent="supplier_issue", status="Open", region="ME",
        assignee_id=seed_users["agent2"].id, contact_count=1,
        created_at=now, updated_at=now,
    )
    db_session.add(ticket)
    db_session.flush()
    convo = SideConversation(
        id=uuid.uuid4(), ticket_id=ticket.id, subject="Supplier confirmation",
        kind="supplier", created_by_id=seed_users["agent2"].id, created_at=now,
    )
    db_session.add(convo)
    db_session.flush()
    db_session.add(SideRecipient(
        id=uuid.uuid4(), side_conversation_id=convo.id,
        email="supplier@example.com", name="Supplier Desk", added_at=now,
    ))
    db_session.commit()

    reassigned = test_client.post(
        f"/api/v1/tickets/{ticket.id}/assign",
        json={"agent_id": str(seed_users["agent1"].id)},
        headers=auth_headers["agent2"],
    )
    assert reassigned.status_code == 200

    db_session.expire_all()
    recipient = db_session.query(SideRecipient).filter_by(side_conversation_id=convo.id).one()
    assert recipient.email == "supplier@example.com"

    timeline = test_client.get(
        f"/api/v1/tickets/{ticket.id}/timeline",
        headers=auth_headers["agent1"],
    )
    assert timeline.status_code == 200
    assert any(event["event_type"] == "side_convo_recipients_preserved" for event in timeline.json())


def test_auto_linking_adds_case_link_event_to_activity_timeline(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    prior = Ticket(
        id=uuid.uuid4(), title="Prior refund case", description="Earlier contact",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-TIMELINE-LINK",
        priority="P2", intent="refund", status="Open", region="IN-West",
        contact_count=1, created_at=now - timedelta(days=1), updated_at=now,
    )
    db_session.add(prior)
    db_session.commit()

    created = test_client.post(
        "/api/v1/tickets",
        json={
            "title": "Second refund contact", "description": "Refund is still pending",
            "agency_id": str(seed_agencies["horizons"].id), "tboh": "TBO-TIMELINE-LINK",
            "priority": "P2", "intent": "refund", "region": "IN-West",
        },
        headers=auth_headers["agent1"],
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]

    timeline = test_client.get(
        f"/api/v1/tickets/{ticket_id}/timeline",
        headers=auth_headers["agent1"],
    )
    assert timeline.status_code == 200
    link_events = [event for event in timeline.json() if event["event_type"] == "ticket_link"]
    assert link_events
    assert link_events[0]["payload"]["link_type"] == "strong"


def test_agent_can_unassign_ticket_back_to_triage(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    seed_users: Dict[str, User],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="Unassign workflow", description="Test",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-UNASSIGN",
        priority="P2", intent="refund", status="Open", region="IN-West",
        assignee_id=seed_users["agent1"].id, contact_count=1,
        created_at=now, updated_at=now,
    )
    db_session.add(ticket)
    db_session.commit()

    response = test_client.post(
        f"/api/v1/tickets/{ticket.id}/unassign",
        headers=auth_headers["agent1"],
    )
    assert response.status_code == 200
    assert response.json()["assignee_id"] is None

    timeline = test_client.get(
        f"/api/v1/tickets/{ticket.id}/timeline",
        headers=auth_headers["agent1"],
    )
    assert any(event["event_type"] == "unassignment" for event in timeline.json())


def test_insights_and_export_are_lead_only(
    test_client: TestClient, auth_headers: Dict[str, Dict[str, str]]
) -> None:
    for role in ("requester_a", "agent1", "em"):
        assert test_client.get("/api/v1/insights/themes", headers=auth_headers[role]).status_code == 403
        assert test_client.get("/api/v1/export/tickets", headers=auth_headers[role]).status_code == 403

    lead_insights = test_client.get("/api/v1/insights/themes", headers=auth_headers["lead"])
    lead_export = test_client.get("/api/v1/export/tickets", headers=auth_headers["lead"])
    assert lead_insights.status_code == 200
    assert isinstance(lead_insights.json(), list)
    assert lead_export.status_code == 200
    assert lead_export.headers.get("X-Row-Count") is not None


def test_ticket_queue_priority_filter_is_applied(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    for priority in ("P1", "P3"):
        db_session.add(Ticket(
            id=uuid.uuid4(), title=f"Priority {priority}", description="Test",
            agency_id=seed_agencies["horizons"].id, tboh=f"TBO-{priority}",
            priority=priority, intent="refund", status="Open", region="IN-West",
            contact_count=1, created_at=now, updated_at=now,
        ))
    db_session.commit()
    response = test_client.get("/api/v1/tickets?priority=P1", headers=auth_headers["agent1"])
    assert response.status_code == 200
    assert response.json()["items"]
    assert all(row["priority"] == "P1" for row in response.json()["items"])


def test_insight_themes_include_public_conversation_but_exclude_internal_notes(
    test_client: TestClient,
    db_session: Session,
    seed_agencies: Dict[str, Agency],
    auth_headers: Dict[str, Dict[str, str]],
) -> None:
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        id=uuid.uuid4(), title="General booking question", description="Need help with a booking",
        agency_id=seed_agencies["horizons"].id, tboh="TBO-CONVERSATION-THEME",
        priority="P3", intent="other", status="Open", region="IN-West",
        contact_count=1, created_at=now - timedelta(days=20), updated_at=now - timedelta(days=20),
    )
    db_session.add(ticket)
    db_session.commit()
    message = "Refund delay: waiting for update; money back not received."

    internal = test_client.post(
        f"/api/v1/tickets/{ticket.id}/comments",
        json={"body": message, "visibility": "internal"},
        headers=auth_headers["agent1"],
    )
    assert internal.status_code == 201
    assert db_session.query(TicketTheme).filter_by(ticket_id=ticket.id).count() == 0

    public = test_client.post(
        f"/api/v1/tickets/{ticket.id}/comments",
        json={"body": message, "visibility": "public"},
        headers=auth_headers["requester_a"],
    )
    assert public.status_code == 201
    refund_theme = db_session.query(Theme).filter_by(name="refund_delay").one_or_none()
    assert refund_theme is not None
    assert db_session.query(TicketTheme).filter_by(ticket_id=ticket.id, theme_id=refund_theme.id).one_or_none() is not None

    weekly = test_client.get("/api/v1/insights/themes", headers=auth_headers["lead"], params={"since": (now - timedelta(days=7)).isoformat()})
    assert weekly.status_code == 200
    refund_row = next(row for row in weekly.json() if row["theme_name"] == "refund_delay")
    assert refund_row["count"] == 1
    assert refund_row["sample_tickets"][0]["id"] == str(ticket.id)
