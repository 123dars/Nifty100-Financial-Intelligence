"""add users, request_logs, and api_key secret columns

Revision ID: a1b2c3d4e5f6
Revises: 7062358bec0c
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7062358bec0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('request_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=True),
        sa.Column('api_key_name', sa.String(), nullable=True),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('query_string', sa.String(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_request_logs_created_at'), 'request_logs', ['created_at'], unique=False)

    op.add_column('api_keys', sa.Column('secret_digest', sa.String(), nullable=True))
    op.add_column('api_keys', sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('api_keys', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('api_keys', 'expires_at')
    op.drop_column('api_keys', 'last_used_at')
    op.drop_column('api_keys', 'secret_digest')
    op.drop_index(op.f('ix_request_logs_created_at'), table_name='request_logs')
    op.drop_table('request_logs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')