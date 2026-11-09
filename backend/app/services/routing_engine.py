from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.user import User

REGION_TZ = {"IN-West": ZoneInfo("Asia/Kolkata"), "IN-East": ZoneInfo("Asia/Kolkata"), "ME": ZoneInfo("Asia/Dubai")}
OPEN_STATUSES = ["New", "Open", "Pending", "Escalated"]

def is_in_shift(agent: Any, now: datetime) -> bool:
    start, end = getattr(agent, "shift_start", None), getattr(agent, "shift_end", None)
    if not start or not end:
        return True  # no configured shift means no shift restriction
    tz = REGION_TZ.get(getattr(agent, "region", None), ZoneInfo("Asia/Kolkata"))
    local_time = now.astimezone(tz).time().replace(tzinfo=None) if now.tzinfo else now.time()
    if start <= end:
        return start <= local_time <= end
    return local_time >= start or local_time <= end  # overnight shift

def is_eligible(agent: Any, now: datetime) -> bool:
    return bool(getattr(agent, "availability", True)) and is_in_shift(agent, now)

def score_agent(agent: Any, ticket: Any, open_counts: Dict[str, int], now: datetime) -> Dict[str, Any]:
    breakdown = {"region": 40 if agent.region and ticket.region and agent.region == ticket.region else 0,
                 "priority": {"P1": 30, "P2": 20, "P3": 10, "P4": 5}.get(ticket.priority, 10),
                 "in_shift": 20 if is_in_shift(agent, now) else 0,
                 "available": 15 if getattr(agent, "availability", True) else 0}
    load = open_counts.get(str(agent.id), 0)
    breakdown["load"] = max(0, 25 - (load * 5))
    score = sum(breakdown.values())
    return {"agent_id": str(agent.id), "name": getattr(agent, "full_name", ""), "score": score,
            "breakdown": breakdown, "open_load": load}

def build_reason_text(best: Dict[str, Any]) -> str:
    bd = best.get("breakdown", {})
    parts = []
    if bd.get("region"): parts.append("region match (+40)")
    if bd.get("in_shift"): parts.append("within local shift (+20)")
    if bd.get("available"): parts.append("available (+15)")
    if bd.get("priority"): parts.append(f"priority weight (+{bd['priority']})")
    parts.append(f"low load (+{bd.get('load', 0)}; {best.get('open_load', 0)} open tickets)")
    return f"Assigned to {best.get('name', 'agent')} ({best.get('score', 0)} pts): " + ", ".join(parts) + "."

def pick_agent(agents: List[Any], ticket: Any, open_counts: Dict[str, int], now: datetime):
    eligible = [a for a in agents if is_eligible(a, now)]
    if not eligible:
        return None, [], "No eligible agent is currently available and within their configured local shift; ticket remains in Triage."
    scored = [score_agent(a, ticket, open_counts, now) for a in eligible]
    best = min(scored, key=lambda x: (-x["score"], x["open_load"], x["name"].lower()))
    return best, scored, build_reason_text(best)

def route_ticket(db: Session, ticket: Ticket, now: Optional[datetime] = None) -> Tuple[Optional[User], List[Dict[str, Any]], str]:
    now = now or datetime.now(timezone.utc)
    agents = db.scalars(select(User).where(User.role.in_(["agent", "lead"]))).all()
    counts_query = (select(Ticket.assignee_id, func.count(Ticket.id))
                    .where(Ticket.assignee_id.is_not(None), Ticket.status.in_(OPEN_STATUSES))
                    .group_by(Ticket.assignee_id))
    open_counts = {str(row[0]): row[1] for row in db.execute(counts_query).all() if row[0] is not None}
    best, scored, reason = pick_agent(agents, ticket, open_counts, now)
    if not best:
        return None, scored, reason
    chosen = next((a for a in agents if str(a.id) == best["agent_id"]), None)
    return chosen, scored, reason
