"""Add direct_messages table

Revision ID: 003
Revises: 002
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'direct_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sender_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipient_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('slack_ts', sa.String(32), nullable=True),
    )
    op.create_index('ix_direct_messages_slack_ts', 'direct_messages', ['slack_ts'])


def downgrade() -> None:
    op.drop_index('ix_direct_messages_slack_ts')
    op.drop_table('direct_messages')
