"""Pydantic schemas package."""
from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, UserResponse,
    Token, TokenRefresh, TokenPayload,
)
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStats
from app.schemas.meeting import (
    MeetingCreate, MeetingUpdate, MeetingResponse,
    MeetingUploadResponse, ActionItemResponse,
)
from app.schemas.integration import IntegrationResponse, IntegrationSyncResponse
from app.schemas.chat import ChatQuerySchema, ChatResponseSchema
from app.schemas.analytics import (
    WorkloadAnalytics, TeamWorkloadResponse, MeetingInsights,
    ProductivityTrendResponse,
)

__all__ = [
    "UserCreate", "UserLogin", "UserUpdate", "UserResponse",
    "Token", "TokenRefresh", "TokenPayload",
    "TaskCreate", "TaskUpdate", "TaskResponse", "TaskStats",
    "MeetingCreate", "MeetingUpdate", "MeetingResponse",
    "MeetingUploadResponse", "ActionItemResponse",
    "IntegrationResponse", "IntegrationSyncResponse",
    "ChatQuerySchema", "ChatResponseSchema",
    "WorkloadAnalytics", "TeamWorkloadResponse", "MeetingInsights",
    "ProductivityTrendResponse",
]
