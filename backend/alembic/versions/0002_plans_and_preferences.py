"""Add plan/quota columns to users and create user_preferences table

Revision ID: 0002
Create Date: 2025-07-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add plan/quota columns to users
    op.add_column("users", sa.Column("plan", sa.String(32), server_default="free", nullable=False))
    op.add_column("users", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("llm_quota_monthly", sa.Integer(), server_default="100", nullable=False))
    op.add_column("users", sa.Column("llm_quota_used", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("quota_reset_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_users_plan", "users", ["plan"])

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("active_provider", sa.String(32), server_default="auto", nullable=False),
        sa.Column("active_model", sa.String(128), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_index("ix_users_plan", table_name="users")
    op.drop_column("users", "quota_reset_at")
    op.drop_column("users", "llm_quota_used")
    op.drop_column("users", "llm_quota_monthly")
    op.drop_column("users", "plan_expires_at")
    op.drop_column("users", "plan")
