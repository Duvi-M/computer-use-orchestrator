"""Initial SaaS schema.

Revision ID: 0001_initial_saas_schema
Revises:
Create Date: 2026-06-10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_saas_schema"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if _has_table(table_name) and not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    if not _has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column("created_at", sa.Float(), nullable=True),
        )
    if not _has_table("organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column("created_at", sa.Float(), nullable=True),
        )
    if not _has_table("organization_memberships"):
        op.create_table(
            "organization_memberships",
            sa.Column("user_id", sa.String(length=255), nullable=False),
            sa.Column("organization_id", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=64), server_default="member", nullable=True),
            sa.Column("created_at", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "organization_id"),
        )
    if not _has_table("sessions"):
        op.create_table(
            "sessions",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column("user_id", sa.String(length=255), nullable=True),
            sa.Column("organization_id", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.Float(), nullable=True),
            sa.Column("last_activity", sa.Float(), nullable=True),
            sa.Column("status", sa.String(length=64), server_default="created", nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("stop_reason", sa.String(length=255), nullable=True),
            sa.Column("completed_at", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        )
    if not _has_table("messages"):
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(length=255), nullable=True),
            sa.Column("role", sa.String(length=64), nullable=True),
            sa.Column("text", sa.Text(), nullable=True),
            sa.Column("ts", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        )
    if not _has_table("events"):
        op.create_table(
            "events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(length=255), nullable=True),
            sa.Column("event", sa.String(length=255), nullable=True),
            sa.Column("data", sa.JSON(), nullable=True),
            sa.Column("ts", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        )

    _create_index_if_missing("ix_sessions_user_id", "sessions", ["user_id"])
    _create_index_if_missing("ix_sessions_organization_id", "sessions", ["organization_id"])
    _create_index_if_missing("ix_sessions_status", "sessions", ["status"])
    _create_index_if_missing("ix_sessions_created_at", "sessions", ["created_at"])
    _create_index_if_missing("ix_messages_session_id", "messages", ["session_id"])
    _create_index_if_missing("ix_events_session_id", "events", ["session_id"])
    _create_index_if_missing("ix_events_event", "events", ["event"])
    _create_index_if_missing("ix_events_created_at", "events", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_events_created_at", table_name="events")
    op.drop_index("ix_events_event", table_name="events")
    op.drop_index("ix_events_session_id", table_name="events")
    op.drop_index("ix_messages_session_id", table_name="messages")
    op.drop_index("ix_sessions_created_at", table_name="sessions")
    op.drop_index("ix_sessions_status", table_name="sessions")
    op.drop_index("ix_sessions_organization_id", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("events")
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    op.drop_table("users")
