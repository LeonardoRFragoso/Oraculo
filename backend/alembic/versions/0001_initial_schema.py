"""Initial schema — users, data_sources, alerts

Revision ID: 0001
Create Date: 2025-06-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("email", sa.String(256), unique=True, nullable=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), server_default="user", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])

    # data_sources
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("connector_type", sa.String(64), nullable=False),
        sa.Column("config_encrypted", sa.Text(), server_default="{}", nullable=False),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="registered", nullable=False),
        sa.Column("datasets_json", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("domain_summary_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_data_sources_owner_id", "data_sources", ["owner_id"])
    op.create_index("ix_data_sources_status", "data_sources", ["status"])

    # alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_name", sa.String(256), nullable=False),
        sa.Column("severity", sa.String(32), server_default="info", nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("trigger", sa.String(64), server_default="system", nullable=False),
        sa.Column("acknowledged", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("acknowledged_by", sa.String(64), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerts_source_id", "alerts", ["source_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_acknowledged", "alerts", ["acknowledged"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("data_sources")
    op.drop_table("users")
