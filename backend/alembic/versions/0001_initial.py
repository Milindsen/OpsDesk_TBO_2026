"""Initial migration with all tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agencies
    op.create_table(
        "agencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("agency_id", sa.Uuid(), nullable=True),
        sa.Column("shift_start", sa.Time(), nullable=True),
        sa.Column("shift_end", sa.Time(), nullable=True),
        sa.Column("availability", sa.Boolean(), nullable=False, default=True),
        sa.Column("current_load", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_agency_id"), "users", ["agency_id"], unique=False)

    # 3. tickets
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("tboh", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False, default="P3"),
        sa.Column("intent", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, default="New"),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=True),
        sa.Column("lcd", sa.Date(), nullable=True),
        sa.Column("sla_due", sa.DateTime(), nullable=True),
        sa.Column("sla_status", sa.String(length=20), nullable=False, default="ok"),
        sa.Column("routing_reason", sa.Text(), nullable=True),
        sa.Column("contact_count", sa.Integer(), nullable=False, default=1),
        sa.Column("product_bug_link", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_agency_id", "tickets", ["agency_id"], unique=False)
    op.create_index("ix_tickets_assignee_id", "tickets", ["assignee_id"], unique=False)
    op.create_index("ix_tickets_intent", "tickets", ["intent"], unique=False)
    op.create_index("ix_tickets_region", "tickets", ["region"], unique=False)
    op.create_index("ix_tickets_sla_due", "tickets", ["sla_due"], unique=False)
    op.create_index("ix_tickets_status", "tickets", ["status"], unique=False)
    op.create_index("ix_tickets_tboh", "tickets", ["tboh"], unique=False)

    # 4. ticket_links
    op.create_table(
        "ticket_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("link_type", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_links_source_target", "ticket_links", ["source_id", "target_id"], unique=False)
    op.create_index(op.f("ix_ticket_links_source_id"), "ticket_links", ["source_id"], unique=False)
    op.create_index(op.f("ix_ticket_links_target_id"), "ticket_links", ["target_id"], unique=False)

    # 5. timeline_events
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_name", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_timeline_events_ticket_created", "timeline_events", ["ticket_id", "created_at"], unique=False)
    op.create_index(op.f("ix_timeline_events_actor_id"), "timeline_events", ["actor_id"], unique=False)
    op.create_index(op.f("ix_timeline_events_ticket_id"), "timeline_events", ["ticket_id"], unique=False)

    # 6. routing_log
    op.create_table(
        "routing_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("chosen_agent_id", sa.Uuid(), nullable=True),
        sa.Column("candidate_scores", sa.JSON(), nullable=False),
        sa.Column("reason_text", sa.String(length=500), nullable=False),
        sa.Column("routed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chosen_agent_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routing_log_ticket_routed", "routing_log", ["ticket_id", "routed_at"], unique=False)
    op.create_index(op.f("ix_routing_log_chosen_agent_id"), "routing_log", ["chosen_agent_id"], unique=False)
    op.create_index(op.f("ix_routing_log_ticket_id"), "routing_log", ["ticket_id"], unique=False)

    # 7. side_conversations
    op.create_table(
        "side_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, default="supplier"),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_side_conversations_created_by_id"), "side_conversations", ["created_by_id"], unique=False)
    op.create_index(op.f("ix_side_conversations_ticket_id"), "side_conversations", ["ticket_id"], unique=False)

    # 8. side_recipients
    op.create_table(
        "side_recipients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("side_conversation_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["side_conversation_id"], ["side_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_side_recipients_side_conversation_id"), "side_recipients", ["side_conversation_id"], unique=False)

    # 9. side_messages
    op.create_table(
        "side_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("side_conversation_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, default="external"),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["side_conversation_id"], ["side_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_side_messages_convo_sent", "side_messages", ["side_conversation_id", "sent_at"], unique=False)
    op.create_index(op.f("ix_side_messages_side_conversation_id"), "side_messages", ["side_conversation_id"], unique=False)

    # 10. themes
    op.create_table(
        "themes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 11. ticket_themes
    op.create_table(
        "ticket_themes",
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("theme_id", sa.Uuid(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, default=1.0),
        sa.ForeignKeyConstraint(["theme_id"], ["themes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ticket_id", "theme_id"),
    )
    op.create_index("ix_ticket_themes_theme_id", "ticket_themes", ["theme_id"], unique=False)

    # 12. escalations
    op.create_table(
        "escalations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("escalated_by_id", sa.Uuid(), nullable=False),
        sa.Column("escalated_to_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("escalated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["escalated_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["escalated_to_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )
    op.create_index("ix_escalations_escalated_to", "escalations", ["escalated_to_id"], unique=False)
    op.create_index("ix_escalations_ticket_id", "escalations", ["ticket_id"], unique=False)

    # 13. archived_tickets
    op.create_table(
        "archived_tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("tboh", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("intent", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=True),
        sa.Column("lcd", sa.Date(), nullable=True),
        sa.Column("sla_due", sa.DateTime(), nullable=True),
        sa.Column("sla_status", sa.String(length=20), nullable=False),
        sa.Column("routing_reason", sa.Text(), nullable=True),
        sa.Column("contact_count", sa.Integer(), nullable=False, default=1),
        sa.Column("product_bug_link", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=False),
        sa.Column("archive_reason", sa.String(length=100), nullable=False, default="auto_90d"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_archived_tickets_archived_at", "archived_tickets", ["archived_at"], unique=False)
    op.create_index("ix_archived_tickets_tboh", "archived_tickets", ["tboh"], unique=False)



def downgrade() -> None:
    op.drop_table("archived_tickets")
    op.drop_table("escalations")
    op.drop_table("ticket_themes")
    op.drop_table("themes")
    op.drop_table("side_messages")
    op.drop_table("side_recipients")
    op.drop_table("side_conversations")
    op.drop_table("routing_log")
    op.drop_table("timeline_events")
    op.drop_table("ticket_links")
    op.drop_table("tickets")
    op.drop_table("users")
    op.drop_table("agencies")
