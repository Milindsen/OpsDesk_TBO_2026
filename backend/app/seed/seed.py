import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.agency import Agency
from app.models.escalation import Escalation
from app.models.routing_log import RoutingLog
from app.models.side_conversation import (
    SideConversation,
    SideMessage,
    SideRecipient,
)
from app.models.theme import Theme, TicketTheme
from app.models.ticket import Ticket
from app.models.ticket_link import TicketLink
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.services.auth_service import get_password_hash
from app.services.routing_engine import score_agent
from app.services.sla_engine import compute_sla_due, compute_sla_status

THEME_DEFS = [
    ("refund_delay", "Delays or disputes in customer refund processing"),
    ("inventory_sync", "Room or flight inventory out of sync with supplier"),
    ("special_request", "Custom passenger amenities, meals, and assistance"),
    ("payment_failure", "Failed gateway transactions and duplicate card charges"),
    ("supplier_delay", "Supplier unresponsiveness or unconfirmed bookings"),
]


def seed_database(db: Session) -> None:
    # Check if already seeded
    existing_agency = db.scalar(select(Agency).where(Agency.name == "Horizons Travel"))
    if existing_agency:
        # Keep seeded demo routing deterministic after code updates while preserving
        # all existing tickets and user activity in the persistent volume.
        for email in ("agent1@tbo.com", "agent2@tbo.com"):
            demo_agent = db.scalar(select(User).where(User.email == email))
            if demo_agent:
                demo_agent.shift_start = time(0, 0)
                demo_agent.shift_end = time(23, 59)
                demo_agent.availability = True
        # Keep the seeded "same refund, three contacts" journey truthful on an
        # already-persistent demo volume as well as on a fresh database.
        refund_cases = db.scalars(
            select(Ticket)
            .where(Ticket.tboh == "TBO12345", Ticket.intent == "refund", Ticket.agency_id == existing_agency.id)
            .order_by(Ticket.created_at.desc())
        ).all()
        total_refund_contacts = len(refund_cases)
        for index, case in enumerate(refund_cases, start=1):
            case.contact_count = total_refund_contacts - index + 1
        db.commit()
        print("Database already seeded. Preserved data; refreshed demo-agent shift settings.")
        return

    print("Seeding agencies and themes...")
    # 1. Themes
    themes_map: Dict[str, Theme] = {}
    for name, desc in THEME_DEFS:
        th = Theme(id=uuid.uuid4(), name=name, description=desc)
        db.add(th)
        themes_map[name] = th
    db.flush()

    # 2. Agencies
    agencies_data = [
        ("Horizons Travel", "IN-West"),
        ("Sunrise Tours", "IN-East"),
        ("Peak Adventures", "ME"),
    ]
    agencies_map: Dict[str, Agency] = {}
    for name, reg in agencies_data:
        ag = Agency(id=uuid.uuid4(), name=name, region=reg)
        db.add(ag)
        agencies_map[name] = ag
    db.flush()

    print("Seeding users...")
    demo_pw = get_password_hash("Demo@1234")
    users_data = [
        # Agents & Staff
        ("agent1@tbo.com", "Agent One", "agent", "IN-West", None, time(0, 0), time(23, 59)),
        ("agent2@tbo.com", "Agent Two", "agent", "IN-East", None, time(0, 0), time(23, 59)),
        ("em@tbo.com", "Escalation Manager", "escalation_manager", "IN-West", None, None, None),
        ("lead@tbo.com", "Team Lead", "lead", None, None, None, None),
        # Requesters
        ("agency_a@horizons.com", "Horizons Requester", "requester", "IN-West", agencies_map["Horizons Travel"].id, None, None),
        ("agency_b@sunrise.com", "Sunrise Requester", "requester", "IN-East", agencies_map["Sunrise Tours"].id, None, None),
        ("agency_c@peak.com", "Peak Requester", "requester", "ME", agencies_map["Peak Adventures"].id, None, None),
    ]

    users_map: Dict[str, User] = {}
    for email, name, role, reg, ag_id, s_start, s_end in users_data:
        usr = User(
            id=uuid.uuid4(),
            email=email,
            full_name=name,
            hashed_password=demo_pw,
            role=role,
            region=reg,
            agency_id=ag_id,
            shift_start=s_start,
            shift_end=s_end,
            availability=True,
            current_load=0,
        )
        db.add(usr)
        users_map[email] = usr
    db.flush()

    print("Seeding explicit tickets...")
    now = datetime.now(timezone.utc)
    today = date.today()

    horizons_id = agencies_map["Horizons Travel"].id
    sunrise_id = agencies_map["Sunrise Tours"].id
    peak_id = agencies_map["Peak Adventures"].id

    agent1 = users_map["agent1@tbo.com"]
    agent2 = users_map["agent2@tbo.com"]
    em = users_map["em@tbo.com"]

    # 1. Ticket 1: TBOH=TBO12345, agency=Horizons, intent=refund, priority=P2, status=Open, assignee=agent1, region=IN-West, check_in_date=today+1d (AT RISK SLA!)
    t1_created = now - timedelta(hours=1, minutes=45)
    t1_sla_due = t1_created + timedelta(hours=2)  # 2h total window due to urgency factor 0.25 (P2 8h * 0.25 = 2h), remaining 15m -> at_risk!
    t1 = Ticket(
        id=uuid.uuid4(),
        title="Urgent Refund Request for cancelled flight",
        description="Booking cancelled yesterday due to flight grounding. Guest requesting prompt refund.",
        agency_id=horizons_id,
        tboh="TBO12345",
        priority="P2",
        intent="refund",
        status="Open",
        assignee_id=agent1.id,
        region="IN-West",
        check_in_date=today + timedelta(days=1),
        sla_due=t1_sla_due,
        sla_status="at_risk",
        contact_count=3,
        routing_reason=f"Assigned to {agent1.full_name} (region match + shift).",
        created_at=t1_created,
        updated_at=now,
    )
    db.add(t1)
    agent1.current_load += 1

    # 2. Ticket 2: TBOH=TBO12345, agency=Horizons, intent=refund, priority=P2, status=Resolved, region=IN-West
    t2_created = now - timedelta(days=5)
    t2 = Ticket(
        id=uuid.uuid4(),
        title="Follow-up on refund TBO12345",
        description="Previous refund status query resolved by finance.",
        agency_id=horizons_id,
        tboh="TBO12345",
        priority="P2",
        intent="refund",
        status="Resolved",
        assignee_id=agent1.id,
        region="IN-West",
        contact_count=2,
        sla_due=t2_created + timedelta(hours=8),
        sla_status="ok",
        created_at=t2_created,
        updated_at=now - timedelta(days=3),
    )
    db.add(t2)

    # 3. Ticket 3: TBOH=TBO12345, agency=Horizons, intent=refund, priority=P3, status=Closed, region=IN-West (initial contact)
    t3_created = now - timedelta(days=15)
    t3 = Ticket(
        id=uuid.uuid4(),
        title="Initial refund query TBO12345",
        description="Client asked about refund policy and cancellation charges.",
        agency_id=horizons_id,
        tboh="TBO12345",
        priority="P3",
        intent="refund",
        status="Closed",
        assignee_id=agent1.id,
        region="IN-West",
        contact_count=1,
        sla_due=t3_created + timedelta(hours=24),
        sla_status="ok",
        created_at=t3_created,
        updated_at=now - timedelta(days=12),
    )
    db.add(t3)

    # 4. Ticket 4: TBOH=TBO99999, agency=Sunrise, intent=cancellation, priority=P1, status=Escalated, assignee=em, region=IN-East, lcd=today+2d (BREACHED SLA)
    t4_created = now - timedelta(hours=6)
    t4_sla_due = t4_created + timedelta(hours=2)  # P1 with urgency factor 0.5 = 2h window, created 6h ago -> breached!
    t4 = Ticket(
        id=uuid.uuid4(),
        title="Emergency VIP Cancellation - Sunrise Group",
        description="Corporate delegation cancellation needed immediately before LCD. Supplier API failing.",
        agency_id=sunrise_id,
        tboh="TBO99999",
        priority="P1",
        intent="cancellation",
        status="Escalated",
        assignee_id=em.id,
        region="IN-East",
        lcd=today + timedelta(days=2),
        sla_due=t4_sla_due,
        sla_status="breached",
        contact_count=1,
        routing_reason=f"Escalated to {em.full_name}: API failure blocking cancellation.",
        created_at=t4_created,
        updated_at=now,
    )
    db.add(t4)
    em.current_load += 1

    # Escalation record for ticket 4
    esc4 = Escalation(
        id=uuid.uuid4(),
        ticket_id=t4.id,
        escalated_by_id=agent1.id,
        escalated_to_id=em.id,
        reason="Supplier API endpoint rejecting cancellation tokens. Need EM direct override.",
        escalated_at=now - timedelta(hours=2),
    )
    db.add(esc4)

    # 5. Ticket 5: TBOH=TBO77777, agency=Peak, intent=supplier_issue, priority=P2, status=Open, region=ME, assignee=agent2
    t5_created = now - timedelta(hours=4)
    t5 = Ticket(
        id=uuid.uuid4(),
        title="Hotel denied check-in at Peak Resort Dubai",
        description="Guests arrived at property but front desk claims reservation was not received from distributor.",
        agency_id=peak_id,
        tboh="TBO77777",
        priority="P2",
        intent="supplier_issue",
        status="Open",
        assignee_id=agent2.id,
        region="ME",
        sla_due=t5_created + timedelta(hours=8),
        sla_status="ok",
        contact_count=1,
        routing_reason=f"Assigned to {agent2.full_name}. Transferred from shift handover with recipients preserved.",
        created_at=t5_created,
        updated_at=now,
    )
    db.add(t5)
    agent2.current_load += 1

    # Active supplier side conversation for ticket 5
    side_convo5 = SideConversation(
        id=uuid.uuid4(),
        ticket_id=t5.id,
        subject="Urgent Reservation Confirmation Check - TBO77777",
        kind="supplier",
        created_by_id=agent2.id,
        created_at=t5_created + timedelta(minutes=15),
    )
    db.add(side_convo5)
    db.flush()

    rec1 = SideRecipient(
        id=uuid.uuid4(),
        side_conversation_id=side_convo5.id,
        email="supplier@hotelpeak.com",
        name="Peak Resort Reservations Desk",
        added_at=t5_created + timedelta(minutes=15),
    )
    rec2 = SideRecipient(
        id=uuid.uuid4(),
        side_conversation_id=side_convo5.id,
        email="agent2@tbo.com",
        name="Agent Two",
        added_at=t5_created + timedelta(minutes=15),
    )
    db.add(rec1)
    db.add(rec2)

    msg5 = SideMessage(
        id=uuid.uuid4(),
        side_conversation_id=side_convo5.id,
        author_id=agent2.id,
        author_name=agent2.full_name,
        body="Dear Reservations Team, Our guest is present at front desk. Please locate voucher TBO77777 urgently.",
        kind="external",
        sent_at=t5_created + timedelta(minutes=20),
    )
    db.add(msg5)

    # 6. Ticket 6: TBOH=TBO55555, agency=Horizons, intent=amendment, priority=P3, status=New (unassigned)
    t6 = Ticket(
        id=uuid.uuid4(),
        title="Date amendment request for Bangkok package",
        description="Client requests moving check-in from 15th to 18th next month.",
        agency_id=horizons_id,
        tboh="TBO55555",
        priority="P3",
        intent="amendment",
        status="New",
        assignee_id=None,
        region="IN-West",
        sla_due=now + timedelta(hours=24),
        sla_status="ok",
        contact_count=1,
        routing_reason="Unassigned - Pending triage.",
        created_at=now - timedelta(minutes=30),
        updated_at=now - timedelta(minutes=30),
    )
    db.add(t6)

    # 7. Ticket 7: TBOH=TBO44444, agency=Sunrise, intent=payment, priority=P2, status=Open, assignee=agent1
    t7 = Ticket(
        id=uuid.uuid4(),
        title="Double debit on corporate card checkout",
        description="Transaction charged twice on card ending 8812. Invoice reflects duplicate charge.",
        agency_id=sunrise_id,
        tboh="TBO44444",
        priority="P2",
        intent="payment",
        status="Open",
        assignee_id=agent1.id,
        region="IN-East",
        sla_due=now + timedelta(hours=6),
        sla_status="ok",
        contact_count=1,
        routing_reason=f"Assigned to {agent1.full_name}.",
        created_at=now - timedelta(hours=2),
        updated_at=now,
    )
    db.add(t7)
    agent1.current_load += 1
    db.flush()

    # Links between tickets 1, 2, and 3
    link12 = TicketLink(
        id=uuid.uuid4(),
        source_id=t1.id,
        target_id=t2.id,
        link_type="strong",
        reason="Same TBOH: TBO12345",
        score=1.0,
        created_at=t1_created,
    )
    link13 = TicketLink(
        id=uuid.uuid4(),
        source_id=t1.id,
        target_id=t3.id,
        link_type="strong",
        reason="Same TBOH: TBO12345 (earlier refund contact)",
        score=1.0,
        created_at=t1_created,
    )
    db.add(link12)
    db.add(link13)

    # Timeline history for the Case 360 refund journey and the other seeded cases.
    seed_events = [
        TimelineEvent(ticket_id=t1.id, actor_id=None, actor_name="System", event_type="status_change", payload={"from": None, "to": "Open", "note": "Seeded refund case intake"}, created_at=t1_created),
        TimelineEvent(ticket_id=t1.id, actor_id=None, actor_name="System Routing Engine", event_type="assignment", payload={"from_assignee_id": None, "assigned_to": str(agent1.id), "agent_name": agent1.full_name, "assigned_by": "System"}, created_at=t1_created),
        TimelineEvent(ticket_id=t1.id, actor_id=None, actor_name="System Linker", event_type="ticket_link", payload={"target_ticket_id": str(t2.id), "target_title": t2.title, "link_type": "strong", "reason": "Same TBOH: TBO12345", "score": 1.0}, created_at=t1_created),
        TimelineEvent(ticket_id=t1.id, actor_id=None, actor_name="System Linker", event_type="ticket_link", payload={"target_ticket_id": str(t3.id), "target_title": t3.title, "link_type": "strong", "reason": "Same TBOH: TBO12345 (earlier refund contact)", "score": 1.0}, created_at=t1_created),
        TimelineEvent(ticket_id=t2.id, actor_id=None, actor_name="System", event_type="status_change", payload={"from": None, "to": "Resolved", "note": "Earlier refund status query resolved"}, created_at=t2_created),
        TimelineEvent(ticket_id=t3.id, actor_id=None, actor_name="System", event_type="status_change", payload={"from": None, "to": "Closed", "note": "Initial refund policy query closed"}, created_at=t3_created),
        TimelineEvent(ticket_id=t4.id, actor_id=agent1.id, actor_name=agent1.full_name, event_type="status_change", payload={"from": "Open", "to": "Escalated", "note": "Supplier API failure"}, created_at=now - timedelta(hours=2)),
        TimelineEvent(ticket_id=t4.id, actor_id=agent1.id, actor_name=agent1.full_name, event_type="escalation", payload={"escalated_to": str(em.id), "em_name": em.full_name, "reason": "Supplier API endpoint rejecting cancellation tokens. Need EM direct override."}, created_at=now - timedelta(hours=2)),
        TimelineEvent(ticket_id=t6.id, actor_id=None, actor_name="System", event_type="status_change", payload={"from": None, "to": "New", "note": "Ticket created; awaiting triage"}, created_at=now - timedelta(minutes=30)),
        TimelineEvent(ticket_id=t7.id, actor_id=None, actor_name="System", event_type="status_change", payload={"from": None, "to": "Open", "note": "Seeded payment case intake"}, created_at=now - timedelta(hours=2)),
        TimelineEvent(ticket_id=t7.id, actor_id=None, actor_name="System Routing Engine", event_type="assignment", payload={"from_assignee_id": None, "assigned_to": str(agent1.id), "agent_name": agent1.full_name, "assigned_by": "System"}, created_at=now - timedelta(hours=2)),
    ]
    db.add_all(seed_events)

    # Timeline events for ticket 5: Transfer + Recipients Preserved
    ev_create5 = TimelineEvent(
        ticket_id=t5.id,
        actor_id=agent1.id,
        actor_name=agent1.full_name,
        event_type="status_change",
        payload={"from": None, "to": "Open", "note": "Initial ticket intake"},
        created_at=t5_created,
    )
    ev_transfer5 = TimelineEvent(
        ticket_id=t5.id,
        actor_id=agent1.id,
        actor_name=agent1.full_name,
        event_type="assignment",
        payload={"from_assignee_id": str(agent1.id), "assigned_to": str(agent2.id), "agent_name": agent2.full_name, "assigned_by": agent1.full_name},
        created_at=t5_created + timedelta(hours=1),
    )
    ev_preserved5 = TimelineEvent(
        ticket_id=t5.id,
        actor_id=None,
        actor_name="System",
        event_type="recipients_preserved",
        payload={
            "action": "recipients_preserved",
            "active_side_conversations": 1,
            "preserved_recipients": ["supplier@hotelpeak.com", "agent2@tbo.com"],
            "note": "Side conversation recipient list preserved across transfer.",
        },
        created_at=t5_created + timedelta(hours=1, minutes=1),
    )
    ev_side_convo5 = TimelineEvent(
        ticket_id=t5.id,
        actor_id=agent2.id,
        actor_name=agent2.full_name,
        event_type="side_convo",
        payload={
            "conversation_id": str(side_convo5.id),
            "subject": side_convo5.subject,
            "kind": side_convo5.kind,
            "recipients": ["supplier@hotelpeak.com", "agent2@tbo.com"],
        },
        created_at=t5_created + timedelta(minutes=15),
    )
    db.add(ev_create5)
    db.add(ev_transfer5)
    db.add(ev_preserved5)
    db.add(ev_side_convo5)

    # Theme tagging for the 7 tickets
    theme_tags_explicit = [
        (t1.id, "refund_delay", 0.95),
        (t2.id, "refund_delay", 0.90),
        (t3.id, "refund_delay", 0.85),
        (t4.id, "supplier_delay", 0.95),
        (t5.id, "supplier_delay", 0.90),
        (t7.id, "payment_failure", 0.92),
    ]
    for tid, th_name, conf in theme_tags_explicit:
        if th_name in themes_map:
            db.add(TicketTheme(ticket_id=tid, theme_id=themes_map[th_name].id, confidence=conf))

    print("Generating ~93 additional realistic tickets (total ~100)...")
    intents = ["refund", "cancellation", "amendment", "voucher", "inventory_sync", "payment", "special_request", "supplier_issue", "other"]
    priorities = ["P1", "P2", "P3", "P4"]
    statuses = ["New", "Open", "Pending", "Resolved", "Closed"]
    agency_list = list(agencies_map.values())
    agent_candidates = [agent1, agent2]

    for i in range(8, 101):
        ag = random.choice(agency_list)
        p = random.choices(priorities, weights=[10, 30, 45, 15])[0]
        it = random.choice(intents)
        st = random.choices(statuses, weights=[15, 35, 15, 20, 15])[0]
        assignee = random.choice(agent_candidates) if st != "New" else None

        tboh_val = f"TBO{random.randint(10000, 89999)}"
        created_dt = now - timedelta(days=random.randint(0, 45), hours=random.randint(0, 23))

        # Check-in or LCD date occasionally
        has_dates = random.random() < 0.4
        ci_date = today + timedelta(days=random.randint(1, 30)) if has_dates else None
        lcd_date = today + timedelta(days=random.randint(1, 10)) if (has_dates and random.random() < 0.5) else None

        sla_due_dt = compute_sla_due(p, created_dt, ci_date, lcd_date)
        sla_st = compute_sla_status(sla_due_dt, now, created_dt)

        t_extra = Ticket(
            id=uuid.uuid4(),
            title=f"{it.replace('_', ' ').capitalize()} query for reservation {tboh_val}",
            description=f"Automated support request from {ag.name} regarding booking {tboh_val}.",
            agency_id=ag.id,
            tboh=tboh_val,
            priority=p,
            intent=it,
            status=st,
            assignee_id=assignee.id if assignee else None,
            region=ag.region,
            check_in_date=ci_date,
            lcd=lcd_date,
            sla_due=sla_due_dt,
            sla_status=sla_st,
            contact_count=1,
            routing_reason=f"Routed based on {ag.region} desk capacity." if assignee else "Pending triage",
            created_at=created_dt,
            updated_at=created_dt + timedelta(hours=random.randint(1, 6)),
        )
        db.add(t_extra)
        db.flush()

        if assignee and st in ["New", "Open", "Pending", "Escalated"]:
            assignee.current_load += 1

        # Add routing log if assigned
        if assignee:
            scored = [
                score_agent(a, t_extra, {str(agent1.id): agent1.current_load, str(agent2.id): agent2.current_load}, created_dt)
                for a in agent_candidates
            ]
            r_log = RoutingLog(
                ticket_id=t_extra.id,
                chosen_agent_id=assignee.id,
                candidate_scores=scored,
                reason_text=f"Assigned to {assignee.full_name} by routing engine.",
                routed_at=created_dt,
            )
            db.add(r_log)

        # Distribute themes
        theme_for_intent = {
            "refund": "refund_delay",
            "inventory_sync": "inventory_sync",
            "special_request": "special_request",
            "payment": "payment_failure",
            "supplier_issue": "supplier_delay",
        }.get(it)
        if theme_for_intent and theme_for_intent in themes_map:
            db.add(
                TicketTheme(
                    ticket_id=t_extra.id,
                    theme_id=themes_map[theme_for_intent].id,
                    confidence=round(random.uniform(0.70, 0.98), 2),
                )
            )

        # Add timeline creation event
        ev = TimelineEvent(
            ticket_id=t_extra.id,
            actor_id=assignee.id if assignee else None,
            actor_name=assignee.full_name if assignee else "System",
            event_type="status_change",
            payload={"from": None, "to": st, "note": "Initial ticket intake"},
            created_at=created_dt,
        )
        db.add(ev)

    db.commit()
    print("Database seeding completed successfully: 3 agencies, 7 users, 5 themes, ~100 tickets created.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
