"""Add ticket comments and complete archive snapshots.

Revision ID: 0002_comments_archive
Revises: 0001_initial
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "0002_comments_archive"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="internal"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_comments_ticket_id", "ticket_comments", ["ticket_id"], unique=False)
    op.create_index("ix_ticket_comments_ticket_created", "ticket_comments", ["ticket_id", "created_at"], unique=False)
    for name in ["timeline_snapshot", "links_snapshot", "side_conversations_snapshot", "routing_logs_snapshot", "themes_snapshot", "comments_snapshot"]:
        op.add_column("archived_tickets", sa.Column(name, sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("archived_tickets", sa.Column("escalation_snapshot", sa.JSON(), nullable=False, server_default="{}"))

def downgrade() -> None:
    for name in ["timeline_snapshot", "links_snapshot", "side_conversations_snapshot", "routing_logs_snapshot", "themes_snapshot", "comments_snapshot", "escalation_snapshot"]:
        op.drop_column("archived_tickets", name)
    op.drop_index("ix_ticket_comments_ticket_created", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_ticket_id", table_name="ticket_comments")
    op.drop_table("ticket_comments")
