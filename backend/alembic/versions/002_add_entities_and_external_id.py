"""add entities and ensure external_id columns exist

Revision ID: 002_add_entities
Revises: 001_add_channel_fields
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_add_entities'
down_revision = '001_add_channel_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add entities JSON column if it doesn't exist
    # Using batch_alter_table for SQLite compatibility
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('entities', sa.JSON(), nullable=True, server_default='{}')
        )


def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_column('entities')
