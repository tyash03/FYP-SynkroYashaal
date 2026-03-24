"""add channel_id and channel_type to messages

Revision ID: 001_add_channel_fields
Revises:
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

revision = '001_add_channel_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add channel_id and channel_type columns to messages table
    # Using batch_alter_table for SQLite compatibility in dev
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('channel_id', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('channel_type', sa.String(50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_column('channel_type')
        batch_op.drop_column('channel_id')
