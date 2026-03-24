"""Team model - represents an organization/team using Synkro"""
from sqlalchemy import Column, String, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TeamPlan(str, enum.Enum):
    """Team subscription plan"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Team(Base):
    """Team/Organization model"""
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    plan = Column(SQLEnum(TeamPlan), default=TeamPlan.FREE, nullable=False)
    settings = Column(JSON, default=dict)  # Team-wide settings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("User", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team {self.name}>"
