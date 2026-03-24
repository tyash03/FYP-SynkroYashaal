"""Pydantic schemas for Analytics responses"""
from pydantic import BaseModel
from typing import List, Optional, Dict


class WorkloadAnalytics(BaseModel):
    """Schema for workload analytics response"""
    period_days: int
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    completion_rate: float


class TeamMemberWorkload(BaseModel):
    """Schema for individual team member workload"""
    user_id: str
    full_name: str
    email: str
    active_tasks: int
    completed_tasks_30d: int
    overdue_tasks: int
    estimated_hours_remaining: float


class TeamWorkloadResponse(BaseModel):
    """Schema for team workload response"""
    team_workload: List[TeamMemberWorkload]


class MeetingInsights(BaseModel):
    """Schema for meeting insights response"""
    period_days: int
    total_meetings: int
    completed_meetings: int
    total_action_items: int
    converted_action_items: int
    action_item_conversion_rate: float
    average_duration_minutes: Optional[float] = None


class ProductivityTrendDay(BaseModel):
    """Schema for a single day in productivity trend"""
    date: str
    created: int
    completed: int


class ProductivityTrendResponse(BaseModel):
    """Schema for productivity trend response"""
    trend: List[ProductivityTrendDay]
    period_days: int
