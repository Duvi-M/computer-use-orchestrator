"""Add retention and artifact metadata.

Revision ID: 0002_retention_artifacts
Revises: 0001_initial_saas_schema
Create Date: 2026-06-10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_retention_artifacts"
down_revision = "0001_initial_saas_schema"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if _has_table(table_name) and not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    if _has_table("sessions") and not _has_column("sessions", "deleted_at"):
        op.add_column("sessions", sa.Column("deleted_at", sa.Float(), nullable=True))

    if not _has_table("artifacts"):
        op.create_table(
            "artifacts",
            sa.Column("artifact_id", sa.String(length=255), primary_key=True),
            sa.Column("session_id", sa.String(length=255), nullable=True),
            sa.Column("user_id", sa.String(length=255), nullable=True),
            sa.Column("organization_id", sa.String(length=255), nullable=True),
            sa.Column("event_id", sa.Integer(), nullable=True),
            sa.Column("message_id", sa.Integer(), nullable=True),
            sa.Column("artifact_type", sa.String(length=64), nullable=True),
            sa.Column("media_type", sa.String(length=128), nullable=True),
            sa.Column("storage_path", sa.Text(), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("checksum", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.Float(), nullable=True),
            sa.Column("expires_at", sa.Float(), nullable=True),
            sa.Column("deleted_at", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        )

    _create_index_if_missing("ix_sessions_deleted_at", "sessions", ["deleted_at"])
    _create_index_if_missing("ix_artifacts_session_id", "artifacts", ["session_id"])
    _create_index_if_missing("ix_artifacts_user_id", "artifacts", ["user_id"])
    _create_index_if_missing("ix_artifacts_organization_id", "artifacts", ["organization_id"])
    _create_index_if_missing("ix_artifacts_type", "artifacts", ["artifact_type"])
    _create_index_if_missing("ix_artifacts_created_at", "artifacts", ["created_at"])
    _create_index_if_missing("ix_artifacts_expires_at", "artifacts", ["expires_at"])
    _create_index_if_missing("ix_artifacts_deleted_at", "artifacts", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_artifacts_deleted_at", table_name="artifacts")
    op.drop_index("ix_artifacts_expires_at", table_name="artifacts")
    op.drop_index("ix_artifacts_created_at", table_name="artifacts")
    op.drop_index("ix_artifacts_type", table_name="artifacts")
    op.drop_index("ix_artifacts_organization_id", table_name="artifacts")
    op.drop_index("ix_artifacts_user_id", table_name="artifacts")
    op.drop_index("ix_artifacts_session_id", table_name="artifacts")
    op.drop_index("ix_sessions_deleted_at", table_name="sessions")
    op.drop_table("artifacts")
    op.drop_column("sessions", "deleted_at")
