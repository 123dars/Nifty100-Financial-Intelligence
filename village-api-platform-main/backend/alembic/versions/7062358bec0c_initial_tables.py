"""initial tables

Revision ID: 7062358bec0c
Revises: 
Create Date: 2026-09-06 22:28:23.962497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7062358bec0c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_api_keys_key'), 'api_keys', ['key'], unique=True)

    op.create_table('states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_states_code'), 'states', ['code'], unique=True)
    op.create_index(op.f('ix_states_name'), 'states', ['name'], unique=True)

    op.create_table('districts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('state_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['state_id'], ['states.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'state_id', name='uq_district_code_state'),
    )

    op.create_table('sub_districts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('district_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'district_id', name='uq_subdistrict_code_district'),
    )

    op.create_table('villages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sub_district_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['sub_district_id'], ['sub_districts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'sub_district_id', name='uq_village_code_subdistrict'),
    )


def downgrade() -> None:
    op.drop_table('villages')
    op.drop_table('sub_districts')
    op.drop_table('districts')
    op.drop_index(op.f('ix_states_name'), table_name='states')
    op.drop_index(op.f('ix_states_code'), table_name='states')
    op.drop_table('states')
    op.drop_index(op.f('ix_api_keys_key'), table_name='api_keys')
    op.drop_table('api_keys')
