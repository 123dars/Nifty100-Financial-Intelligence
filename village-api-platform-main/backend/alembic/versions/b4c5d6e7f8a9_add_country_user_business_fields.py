"""Add country table, user business fields, user_state_access

Revision ID: b4c5d6e7f8a9
Revises: a1b2c3d4e5f6
Create Date: 2025-01-15 12:00:00.000000
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── countries table ──────────────────────────────────────────
    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
    )

    # ── states.country_id FK ─────────────────────────────────────
    op.add_column("states", sa.Column("country_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_states_country", "states", "countries", ["country_id"], ["id"])

    # ── user business fields ─────────────────────────────────────
    op.add_column("users", sa.Column("business_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("users", sa.Column("gst_number", sa.String(), nullable=True))
    op.add_column("users", sa.Column("status", sa.String(20), nullable=False, server_default="active"))
    op.add_column("users", sa.Column("plan", sa.String(20), nullable=False, server_default="free"))
    op.add_column("users", sa.Column("admin_notes", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("rejection_reason", sa.String(), nullable=True))
    op.create_index("ix_users_status", "users", ["status"])

    # ── user_state_access table ──────────────────────────────────
    op.create_table(
        "user_state_access",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "state_id",
            sa.Integer(),
            sa.ForeignKey("states.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "state_id", name="uq_user_state_access"),
    )


def downgrade() -> None:
    op.drop_table("user_state_access")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_column("users", "rejection_reason")
    op.drop_column("users", "rejected_at")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "admin_notes")
    op.drop_column("users", "plan")
    op.drop_column("users", "status")
    op.drop_column("users", "gst_number")
    op.drop_column("users", "phone")
    op.drop_column("users", "business_name")
    op.drop_constraint("fk_states_country", "states", type_="foreignkey")
    op.drop_column("states", "country_id")
    op.drop_table("countries")
