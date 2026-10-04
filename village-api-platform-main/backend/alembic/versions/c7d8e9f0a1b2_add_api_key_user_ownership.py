"""Add user ownership to API keys.

Revision ID: c7d8e9f0a1b2
Revises: b4c5d6e7f8a9
Create Date: 2026-09-16 18:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_api_keys_user_id",
        "api_keys",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_api_keys_user_id",
        "api_keys",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_api_keys_user_id", "api_keys", type_="foreignkey")
    op.drop_index("ix_api_keys_user_id", table_name="api_keys")
    op.drop_column("api_keys", "user_id")
