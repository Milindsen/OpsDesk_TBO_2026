import re
from typing import Any, List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.theme import Theme, TicketTheme
from app.models.ticket import Ticket
from app.models.comment import TicketComment
from app.models.side_conversation import SideConversation, SideMessage

THEME_RULES = {
    "refund_delay": {
        "intents": ["refund"],
        "keywords": ["delay", "waiting", "not received", "pending refund", "refund status", "money back"],
    },
    "inventory_sync": {
        "intents": ["inventory_sync"],
        "keywords": ["inventory", "sync", "mismatch", "availability", "not showing", "allotment"],
    },
    "special_request": {
        "intents": ["special_request"],
        "keywords": ["wheelchair", "early check", "late check", "meal", "honeymoon", "baby cot"],
    },
    "payment_failure": {
        "intents": ["payment"],
        "keywords": ["failure", "failed", "gateway", "charged twice", "debit", "invoice error"],
    },
    "supplier_delay": {
        "intents": ["supplier_issue"],
        "keywords": ["supplier", "property", "hotel denied", "airline cancelled", "overbooked", "unresponsive"],
    },
}


def tag_themes(ticket: Any, conversation_text: str = "") -> List[Tuple[str, float]]:
    matched: List[Tuple[str, float]] = []
    text = f"{getattr(ticket, 'title', '')} {getattr(ticket, 'description', '')} {conversation_text}".lower()
    intent = (getattr(ticket, "intent", "") or "").lower()

    for theme_name, rule in THEME_RULES.items():
        score = 0.0
        if intent in rule["intents"]:
            score += 0.45

        keyword_matches = sum(
            1 for kw in rule["keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", text)
        )
        if keyword_matches > 0:
            # Conversation evidence can independently surface a theme even when
            # the manually selected ticket intent is different.
            score += min(0.65, 0.2 * keyword_matches)

        if score >= 0.5:
            matched.append((theme_name, min(1.0, round(score, 2))))

    if not matched:
        # Default fallback theme based on intent if any
        for theme_name, rule in THEME_RULES.items():
            if intent in rule["intents"]:
                matched.append((theme_name, 0.6))
                break

    return matched


def apply_theme_tags(db: Session, ticket: Ticket) -> List[TicketTheme]:
    # Use customer-facing conversation content as well as the ticket's structured
    # intent. Internal-only notes are deliberately excluded from product themes.
    public_comments = db.scalars(
        select(TicketComment.body).where(
            TicketComment.ticket_id == ticket.id,
            TicketComment.visibility == "public",
        )
    ).all()
    external_messages = db.scalars(
        select(SideMessage.body)
        .join(SideConversation, SideConversation.id == SideMessage.side_conversation_id)
        .where(SideConversation.ticket_id == ticket.id, SideMessage.kind == "external")
    ).all()
    conversation_text = " ".join([*public_comments, *external_messages])
    tags = dict(tag_themes(ticket, conversation_text))
    applied: List[TicketTheme] = []

    existing_links = db.scalars(
        select(TicketTheme).where(TicketTheme.ticket_id == ticket.id)
    ).all()
    existing_by_name = {link.theme.name: link for link in existing_links if link.theme}

    # Keep tags synchronized when intent or conversation text changes.
    for theme_name, link in existing_by_name.items():
        if theme_name not in tags:
            db.delete(link)

    for theme_name, conf in tags.items():
        theme = db.scalar(select(Theme).where(Theme.name == theme_name))
        if not theme:
            theme = Theme(
                name=theme_name,
                description=f"Automated theme category for {theme_name.replace('_', ' ')}",
            )
            db.add(theme)
            db.flush()

        existing = existing_by_name.get(theme_name)
        if existing:
            existing.confidence = conf
        else:
            tt = TicketTheme(ticket_id=ticket.id, theme_id=theme.id, confidence=conf)
            db.add(tt)
            applied.append(tt)

    return applied
