import csv
import io
from typing import Generator, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_role
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/tickets")
def export_tickets_csv(
    status_filter: Optional[str] = Query(None, alias="status"),
    intent: Optional[str] = None,
    region: Optional[str] = None,
    priority: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    assignee_id: Optional[UUID] = None,
    agency_id: Optional[UUID] = None,
    tboh: Optional[str] = None,
    unassigned: Optional[bool] = None,
    escalated: Optional[bool] = None,
    current_user: User = Depends(require_role("lead")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    query = select(Ticket)
    if agency_id: query = query.where(Ticket.agency_id == agency_id)
    if status_filter: query = query.where(Ticket.status == status_filter)
    if intent: query = query.where(Ticket.intent == intent)
    if region: query = query.where(Ticket.region == region)
    if priority: query = query.where(Ticket.priority == priority)
    if start_date: query = query.where(Ticket.created_at >= start_date)
    if end_date: query = query.where(Ticket.created_at < end_date.fromordinal(end_date.toordinal()+1))
    if assignee_id: query = query.where(Ticket.assignee_id == assignee_id)
    if tboh: query = query.where(Ticket.tboh == tboh)
    if unassigned is True: query = query.where(Ticket.assignee_id.is_(None))
    elif unassigned is False: query = query.where(Ticket.assignee_id.is_not(None))
    if escalated is True: query = query.where(Ticket.status == "Escalated")
    query = query.order_by(Ticket.created_at.desc(), Ticket.id.asc())
    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    headers = ["id","title","description","agency_id","tboh","priority","intent","status","assignee_id","region","check_in_date","lcd","sla_due","sla_status","contact_count","product_bug_link","created_at","updated_at"]

    def generate() -> Generator[str, None, None]:
        output = io.StringIO(); writer = csv.writer(output)
        writer.writerow(headers); yield output.getvalue(); output.seek(0); output.truncate(0)
        # Keyset pagination avoids increasingly expensive OFFSET scans and avoids skipping rows on concurrent inserts.
        last_created = None; last_id = None; chunk_size = 500
        while True:
            chunk_query = query
            if last_created is not None:
                from sqlalchemy import or_, and_
                chunk_query = chunk_query.where(or_(Ticket.created_at < last_created, and_(Ticket.created_at == last_created, Ticket.id > last_id)))
            chunk = db.scalars(chunk_query.limit(chunk_size)).all()
            if not chunk: break
            for t in chunk:
                writer.writerow([str(t.id), t.title, (t.description or "").replace("\n", " "), str(t.agency_id), t.tboh, t.priority, t.intent, t.status, str(t.assignee_id) if t.assignee_id else "", t.region, str(t.check_in_date) if t.check_in_date else "", str(t.lcd) if t.lcd else "", t.sla_due.isoformat() if t.sla_due else "", t.sla_status, t.contact_count, t.product_bug_link or "", t.created_at.isoformat() if t.created_at else "", t.updated_at.isoformat() if t.updated_at else ""])
            last_created, last_id = chunk[-1].created_at, chunk[-1].id
            yield output.getvalue(); output.seek(0); output.truncate(0)
    return StreamingResponse(generate(), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=tickets_export.csv", "X-Row-Count":str(total_count), "Cache-Control":"no-store"})
