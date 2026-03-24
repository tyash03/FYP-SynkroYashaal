"""Email model - stores synced Gmail emails"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from datetime import datetime
import uuid

from app.database import Base


class Email(Base):
    """Synced email from Gmail"""
    __tablename__ = "emails"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Not globally unique — the same Gmail message can be synced by different users
    gmail_message_id = Column(String(500), nullable=False)
    subject = Column(String(1000), default="")
    sender = Column(String(500), default="")
    to = Column(String(500), default="")
    body_preview = Column(String(500), default="")
    body = Column(Text, default="")
    received_at = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)

    # AI classification (filled in Phase 3)
    ai_classification = Column(String(50), nullable=True)  # task_request, urgent, fyi, etc.
    ai_summary = Column(Text, nullable=True)

    # Relations
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    integration_id = Column(String(36), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_emails_user_received", "user_id", "received_at"),
        # Per-user deduplication: same message ID is fine across different users
        UniqueConstraint("user_id", "gmail_message_id", name="uq_emails_user_gmail_id"),
    )

    def __repr__(self):
        return f"<Email {self.subject[:40]}>"
