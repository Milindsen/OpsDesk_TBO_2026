import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.database import SessionLocal
from app.models.archive import ArchivedTicket
from app.models.ticket import Ticket
from app.models.side_conversation import SideConversation
from app.models.theme import TicketTheme

logger = logging.getLogger(__name__)

def _iso(value):
    return value.isoformat() if value else None

def _snapshot(ticket: Ticket) -> dict:
    return {
        "timeline": [{"id":str(e.id),"actor_id":str(e.actor_id) if e.actor_id else None,"actor_name":e.actor_name,"event_type":e.event_type,"payload":e.payload,"created_at":_iso(e.created_at)} for e in ticket.timeline_events],
        "links": [{"id":str(x.id),"source_id":str(x.source_id),"target_id":str(x.target_id),"link_type":x.link_type,"reason":x.reason,"score":x.score,"created_at":_iso(x.created_at)} for x in [*ticket.links_as_source,*ticket.links_as_target]],
        "side_conversations": [{"id":str(c.id),"subject":c.subject,"kind":c.kind,"created_by_id":str(c.created_by_id),"created_at":_iso(c.created_at),"recipients":[{"email":r.email,"name":r.name,"added_at":_iso(r.added_at)} for r in c.recipients],"messages":[{"author_id":str(m.author_id) if m.author_id else None,"author_name":m.author_name,"body":m.body,"kind":m.kind,"sent_at":_iso(m.sent_at)} for m in c.messages]} for c in ticket.side_conversations],
        "routing_logs": [{"id":str(r.id),"chosen_agent_id":str(r.chosen_agent_id) if r.chosen_agent_id else None,"candidate_scores":r.candidate_scores,"reason_text":r.reason_text,"routed_at":_iso(r.routed_at)} for r in ticket.routing_logs],
        "themes": [{"name":tt.theme.name,"confidence":tt.confidence} for tt in ticket.themes if tt.theme],
        "comments": [{"id":str(c.id),"author_id":str(c.author_id) if c.author_id else None,"author_name":c.author_name,"body":c.body,"visibility":c.visibility,"created_at":_iso(c.created_at)} for c in ticket.comments],
        "escalation": ({"id":str(ticket.escalation.id),"escalated_by_id":str(ticket.escalation.escalated_by_id),"escalated_to_id":str(ticket.escalation.escalated_to_id),"reason":ticket.escalation.reason,"escalated_at":_iso(ticket.escalation.escalated_at),"resolved_at":_iso(ticket.escalation.resolved_at)} if ticket.escalation else {}),
    }

def archive_closed_tickets(db: Session, days: int = 90) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (select(Ticket).where(Ticket.status == "Closed", Ticket.updated_at < cutoff)
            .options(selectinload(Ticket.timeline_events), selectinload(Ticket.links_as_source), selectinload(Ticket.links_as_target),
                     selectinload(Ticket.side_conversations).selectinload(SideConversation.recipients), selectinload(Ticket.side_conversations).selectinload(SideConversation.messages),
                     selectinload(Ticket.routing_logs), selectinload(Ticket.themes).selectinload(TicketTheme.theme), selectinload(Ticket.comments), selectinload(Ticket.escalation)))
    tickets = db.scalars(stmt).unique().all()
    count = 0
    for t in tickets:
        snap = _snapshot(t)
        archived = ArchivedTicket(id=t.id,title=t.title,description=t.description,agency_id=t.agency_id,tboh=t.tboh,priority=t.priority,
            intent=t.intent,status=t.status,assignee_id=t.assignee_id,region=t.region,check_in_date=t.check_in_date,lcd=t.lcd,product_bug_link=t.product_bug_link,
            sla_due=t.sla_due,sla_status=t.sla_status,routing_reason=t.routing_reason,contact_count=t.contact_count,
            created_at=t.created_at,updated_at=t.updated_at,archived_at=datetime.now(timezone.utc),archive_reason=f"auto_{days}d",
            timeline_snapshot=snap["timeline"],links_snapshot=snap["links"],side_conversations_snapshot=snap["side_conversations"],
            routing_logs_snapshot=snap["routing_logs"],themes_snapshot=snap["themes"],comments_snapshot=snap["comments"],escalation_snapshot=snap["escalation"])
        db.add(archived); db.delete(t); count += 1
    db.commit()
    return count

def run_archival_job() -> None:
    db = SessionLocal()
    try:
        count = archive_closed_tickets(db, days=90)
        logger.info("Archived %s closed tickets older than 90 days with case-history snapshots.", count)
    except Exception:
        logger.exception("Error during ticket archival job")
        db.rollback()
    finally:
        db.close()
