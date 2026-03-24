"""Analytics endpoints - workload, productivity, and team insights"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Task, Meeting, ActionItem, TaskStatus, TaskPriority
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/workload")
async def get_workload_analytics(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workload analytics for the team."""
    since = datetime.utcnow() - timedelta(days=days)

    # Tasks by status
    status_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(
            and_(
                Task.team_id == current_user.team_id,
                Task.created_at >= since,
            )
        )
        .group_by(Task.status)
    )
    tasks_by_status = {row[0].value: row[1] for row in status_result.all()}

    # Tasks by priority
    priority_result = await db.execute(
        select(Task.priority, func.count(Task.id))
        .where(
            and_(
                Task.team_id == current_user.team_id,
                Task.created_at >= since,
            )
        )
        .group_by(Task.priority)
    )
    tasks_by_priority = {row[0].value: row[1] for row in priority_result.all()}

    # Overdue tasks
    overdue_result = await db.execute(
        select(func.count(Task.id)).where(
            and_(
                Task.team_id == current_user.team_id,
                Task.due_date < datetime.utcnow(),
                Task.status != TaskStatus.DONE,
            )
        )
    )
    overdue_count = overdue_result.scalar() or 0

    # Tasks completed in period
    completed_result = await db.execute(
        select(func.count(Task.id)).where(
            and_(
                Task.team_id == current_user.team_id,
                Task.status == TaskStatus.DONE,
                Task.updated_at >= since,
            )
        )
    )
    completed_count = completed_result.scalar() or 0

    # Total tasks in period
    total_result = await db.execute(
        select(func.count(Task.id)).where(
            and_(
                Task.team_id == current_user.team_id,
                Task.created_at >= since,
            )
        )
    )
    total_count = total_result.scalar() or 0

    completion_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0

    return {
        "period_days": days,
        "tasks_by_status": tasks_by_status,
        "tasks_by_priority": tasks_by_priority,
        "total_tasks": total_count,
        "completed_tasks": completed_count,
        "overdue_tasks": overdue_count,
        "completion_rate": completion_rate,
    }


@router.get("/team-workload")
async def get_team_workload(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workload distribution across team members."""
    # Get team members
    members_result = await db.execute(
        select(User).where(User.team_id == current_user.team_id)
    )
    members = members_result.scalars().all()

    workload = []
    for member in members:
        # Active tasks (not done)
        active_result = await db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.assignee_id == member.id,
                    Task.status != TaskStatus.DONE,
                )
            )
        )
        active_count = active_result.scalar() or 0

        # Completed tasks (last 30 days)
        done_result = await db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.assignee_id == member.id,
                    Task.status == TaskStatus.DONE,
                    Task.updated_at >= datetime.utcnow() - timedelta(days=30),
                )
            )
        )
        done_count = done_result.scalar() or 0

        # Overdue tasks
        overdue_result = await db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.assignee_id == member.id,
                    Task.due_date < datetime.utcnow(),
                    Task.status != TaskStatus.DONE,
                )
            )
        )
        overdue_count = overdue_result.scalar() or 0

        # Estimated hours
        hours_result = await db.execute(
            select(func.sum(Task.estimated_hours)).where(
                and_(
                    Task.assignee_id == member.id,
                    Task.status != TaskStatus.DONE,
                )
            )
        )
        estimated_hours = hours_result.scalar() or 0

        workload.append({
            "user_id": member.id,
            "full_name": member.full_name,
            "email": member.email,
            "active_tasks": active_count,
            "completed_tasks_30d": done_count,
            "overdue_tasks": overdue_count,
            "estimated_hours_remaining": float(estimated_hours),
        })

    # Sort by active tasks descending
    workload.sort(key=lambda x: x["active_tasks"], reverse=True)

    return {"team_workload": workload}


@router.get("/meeting-insights")
async def get_meeting_insights(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get meeting analytics and insights."""
    since = datetime.utcnow() - timedelta(days=days)

    # Total meetings
    total_result = await db.execute(
        select(func.count(Meeting.id)).where(
            and_(
                Meeting.team_id == current_user.team_id,
                Meeting.created_at >= since,
            )
        )
    )
    total_meetings = total_result.scalar() or 0

    # Completed meetings
    completed_result = await db.execute(
        select(func.count(Meeting.id)).where(
            and_(
                Meeting.team_id == current_user.team_id,
                Meeting.status == "completed",
                Meeting.created_at >= since,
            )
        )
    )
    completed_meetings = completed_result.scalar() or 0

    # Total action items from meetings
    action_items_result = await db.execute(
        select(func.count(ActionItem.id))
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(
            and_(
                Meeting.team_id == current_user.team_id,
                Meeting.created_at >= since,
            )
        )
    )
    total_action_items = action_items_result.scalar() or 0

    # Converted action items
    converted_result = await db.execute(
        select(func.count(ActionItem.id))
        .join(Meeting, ActionItem.meeting_id == Meeting.id)
        .where(
            and_(
                Meeting.team_id == current_user.team_id,
                Meeting.created_at >= since,
                ActionItem.status == "converted",
            )
        )
    )
    converted_items = converted_result.scalar() or 0

    # Average duration
    duration_result = await db.execute(
        select(func.avg(Meeting.duration_minutes)).where(
            and_(
                Meeting.team_id == current_user.team_id,
                Meeting.created_at >= since,
                Meeting.duration_minutes.isnot(None),
            )
        )
    )
    avg_duration = duration_result.scalar()

    conversion_rate = round((converted_items / total_action_items * 100), 1) if total_action_items > 0 else 0

    return {
        "period_days": days,
        "total_meetings": total_meetings,
        "completed_meetings": completed_meetings,
        "total_action_items": total_action_items,
        "converted_action_items": converted_items,
        "action_item_conversion_rate": conversion_rate,
        "average_duration_minutes": round(float(avg_duration), 1) if avg_duration else None,
    }


@router.get("/productivity-trend")
async def get_productivity_trend(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily task completion trend."""
    since = datetime.utcnow() - timedelta(days=days)

    # Get tasks created and completed by date
    # We'll build daily buckets
    trend = []
    for i in range(days):
        day_start = (datetime.utcnow() - timedelta(days=days - 1 - i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        # Tasks created that day
        created_result = await db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.team_id == current_user.team_id,
                    Task.created_at >= day_start,
                    Task.created_at < day_end,
                )
            )
        )
        created = created_result.scalar() or 0

        # Tasks completed that day
        completed_result = await db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.team_id == current_user.team_id,
                    Task.status == TaskStatus.DONE,
                    Task.updated_at >= day_start,
                    Task.updated_at < day_end,
                )
            )
        )
        completed = completed_result.scalar() or 0

        trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "created": created,
            "completed": completed,
        })

    return {"trend": trend, "period_days": days}
