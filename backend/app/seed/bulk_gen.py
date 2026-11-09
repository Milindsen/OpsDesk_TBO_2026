import argparse
import os
import random
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.agency import Agency
from app.models.ticket import Ticket
from app.models.user import User
from app.services.sla_engine import compute_sla_due, compute_sla_status

INTENTS = [
    "refund",
    "cancellation",
    "amendment",
    "voucher",
    "inventory_sync",
    "payment",
    "special_request",
    "supplier_issue",
    "other",
]
PRIORITIES = ["P1", "P2", "P3", "P4"]
PRIORITY_WEIGHTS = [10, 25, 45, 20]
STATUSES = ["New", "Open", "Pending", "Resolved", "Closed"]
STATUS_WEIGHTS = [20, 40, 15, 15, 10]


def generate_bulk_tickets(db: Session, count: int = 50000, batch_size: int = 5000, start_index: int = 1) -> None:
    print(f"Starting bulk generation of {count} tickets...")
    start_time = time.time()

    agencies = db.scalars(select(Agency)).all()
    if not agencies:
        print("No agencies found. Please run seed.py first.")
        return

    agents = db.scalars(select(User).where(User.role.in_(["agent", "lead"]))).all()
    agent_ids = [a.id for a in agents] if agents else [None]

    now = datetime.now(timezone.utc)
    today = date.today()

    total_inserted = 0
    batch: List[Dict[str, Any]] = []

    for i in range(start_index, start_index + count):
        ag = random.choice(agencies)
        priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0]
        intent = random.choice(INTENTS)
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        assignee_id = random.choice(agent_ids) if status != "New" else None

        created_at = now - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        has_ci = random.random() < 0.35
        ci_date = today + timedelta(days=random.randint(1, 45)) if has_ci else None
        lcd_date = today + timedelta(days=random.randint(1, 15)) if (has_ci and random.random() < 0.4) else None

        sla_due = compute_sla_due(priority, created_at, ci_date, lcd_date)
        sla_st = compute_sla_status(sla_due, now, created_at)

        tboh_num = random.randint(10000, 99999)
        ticket_dict = {
            "id": uuid.uuid4(),
            "title": f"Bulk ticket {i}: {intent.replace('_', ' ').capitalize()} for TBO{tboh_num}",
            "description": f"Bulk generated ticket #{i} for agency {ag.name}. Automated load testing dataset.",
            "agency_id": ag.id,
            "tboh": f"TBO{tboh_num}",
            "priority": priority,
            "intent": intent,
            "status": status,
            "assignee_id": assignee_id,
            "region": ag.region,
            "check_in_date": ci_date,
            "lcd": lcd_date,
            "sla_due": sla_due,
            "sla_status": sla_st,
            "routing_reason": "Bulk generator pre-allocated" if assignee_id else None,
            "contact_count": 1,
            "created_at": created_at,
            "updated_at": created_at + timedelta(minutes=random.randint(10, 180)),
        }
        batch.append(ticket_dict)

        if len(batch) >= batch_size:
            db.execute(insert(Ticket), batch)
            db.commit()
            total_inserted += len(batch)
            elapsed = time.time() - start_time
            rate = total_inserted / elapsed if elapsed > 0 else 0
            print(f"Inserted {total_inserted}/{count} tickets ({rate:.0f} tickets/sec)...")
            batch = []

    if batch:
        db.execute(insert(Ticket), batch)
        db.commit()
        total_inserted += len(batch)

    total_time = time.time() - start_time
    rate = total_inserted / total_time if total_time > 0 else 0
    print(f"Bulk generation finished! Total: {total_inserted} tickets in {total_time:.2f} seconds ({rate:.0f} tickets/sec).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk ticket generator for OpsDesk")
    parser.add_argument("--count", type=int, default=None, help="Number of tickets to generate (explicit opt-in when SEED_BULK is false)")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch insert size")
    args = parser.parse_args()

    bulk_enabled = os.getenv("SEED_BULK", "false").lower() in ("true", "1", "yes")
    if bulk_enabled:
        count = 50000
    elif args.count is None:
        print("SEED_BULK is disabled; skipping bulk ticket generation.")
        return
    else:
        count = args.count

    db = SessionLocal()
    try:
        if bulk_enabled:
            existing = db.scalar(
                select(func.count()).select_from(Ticket).where(Ticket.title.like("Bulk ticket %"))
            ) or 0
            remaining = max(0, count - existing)
            if remaining == 0:
                print(f"Bulk dataset already contains {existing} tickets; skipping duplicate generation.")
                return
            print(f"Bulk dataset contains {existing}/{count}; generating remaining {remaining}.")
            generate_bulk_tickets(db, count=remaining, batch_size=args.batch_size, start_index=existing + 1)
        else:
            generate_bulk_tickets(db, count=count, batch_size=args.batch_size)
    finally:
        db.close()


if __name__ == "__main__":
    main()
