"""AI Chat interface - natural language queries about tasks and meetings"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.database import get_db
from app.models import User, Task, Meeting, TaskStatus
from app.dependencies import get_current_user
from app.services.ai_service import chat_query

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


class ChatQueryRequest(BaseModel):
    """Request schema for chat queries"""
    message: str


class ChatQueryResponse(BaseModel):
    """Response schema for chat queries"""
    response: str
    context_used: Dict[str, Any]
    suggested_actions: List[Dict[str, str]] = []


@router.post("/query", response_model=ChatQueryResponse)
async def send_chat_query(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a natural language query to the AI assistant.

    The AI can answer questions about:
    - Your tasks ("What's on my plate this week?")
    - Team workload ("Who's working on authentication?")
    - Meeting summaries ("What did we decide about the API redesign?")
    - General productivity queries

    Returns:
    - **response**: Natural language answer
    - **context_used**: Data that was used to answer
    - **suggested_actions**: Recommended next steps
    """
    query = request.message.lower()

    # Classify query type and gather relevant context
    context = await gather_context_for_query(query, current_user, db)

    # Generate response using AI
    response_text = await chat_query(request.message, context)

    # Generate suggested actions based on context
    suggested_actions = generate_suggested_actions(query, context)

    return {
        "response": response_text,
        "context_used": context,
        "suggested_actions": suggested_actions
    }


async def gather_context_for_query(
    query: str,
    user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Gather relevant data based on the query.

    Determines what data to fetch based on keywords in the query.
    """
    context = {
        "user": {
            "name": user.full_name,
            "email": user.email,
            "role": user.role.value
        }
    }

    # Keywords for different query types
    task_keywords = ["task", "plate", "working on", "assigned", "todo", "doing", "progress"]
    time_keywords = ["week", "today", "tomorrow", "overdue", "deadline", "due"]
    team_keywords = ["team", "who", "working on", "assigned to"]
    meeting_keywords = ["meeting", "decided", "discussed", "summary"]

    # Check if query is about tasks
    if any(keyword in query for keyword in task_keywords):
        tasks_data = await get_tasks_context(user, db, query, time_keywords)
        context["tasks"] = tasks_data

    # Check if query is about team
    if any(keyword in query for keyword in team_keywords):
        team_data = await get_team_context(user, db, query)
        context["team"] = team_data

    # Check if query is about meetings
    if any(keyword in query for keyword in meeting_keywords):
        meetings_data = await get_meetings_context(user, db, query)
        context["meetings"] = meetings_data

    return context


async def get_tasks_context(
    user: User,
    db: AsyncSession,
    query: str,
    time_keywords: List[str]
) -> Dict[str, Any]:
    """Get task-related context"""

    # Determine time filter
    time_filter = None
    if "today" in query:
        time_filter = datetime.utcnow().date()
    elif "week" in query or "this week" in query:
        time_filter = datetime.utcnow() + timedelta(days=7)
    elif "overdue" in query:
        time_filter = "overdue"

    # Build query
    tasks_query = select(Task).where(Task.team_id == user.team_id)

    # Check if asking about own tasks
    if "my" in query or "plate" in query:
        tasks_query = tasks_query.where(Task.assignee_id == user.id)

    # Apply time filter
    if time_filter == "overdue":
        tasks_query = tasks_query.where(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status != TaskStatus.DONE
            )
        )
    elif time_filter:
        tasks_query = tasks_query.where(Task.due_date <= time_filter)

    # Limit results
    tasks_query = tasks_query.limit(20)

    result = await db.execute(tasks_query)
    tasks = result.scalars().all()

    # Format tasks
    tasks_list = [
        {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "assignee_id": task.assignee_id
        }
        for task in tasks
    ]

    # Get task statistics
    stats_result = await db.execute(
        select(
            Task.status,
            func.count(Task.id)
        ).where(
            Task.team_id == user.team_id
        ).group_by(Task.status)
    )
    stats = {row[0].value: row[1] for row in stats_result}

    return {
        "tasks": tasks_list,
        "count": len(tasks_list),
        "statistics": stats
    }


async def get_team_context(
    user: User,
    db: AsyncSession,
    query: str
) -> Dict[str, Any]:
    """Get team-related context"""

    # Get team members
    members_result = await db.execute(
        select(User).where(User.team_id == user.team_id)
    )
    members = members_result.scalars().all()

    # Get task distribution
    task_distribution = []
    for member in members:
        task_count_result = await db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.assignee_id == member.id,
                    Task.status != TaskStatus.DONE
                )
            )
        )
        task_count = task_count_result.scalar()

        task_distribution.append({
            "user_id": member.id,
            "name": member.full_name,
            "active_tasks": task_count
        })

    return {
        "members": [
            {"id": m.id, "name": m.full_name, "email": m.email}
            for m in members
        ],
        "task_distribution": task_distribution
    }


async def get_meetings_context(
    user: User,
    db: AsyncSession,
    query: str
) -> Dict[str, Any]:
    """Get meeting-related context"""

    # Get recent completed meetings
    meetings_query = select(Meeting).where(
        and_(
            Meeting.team_id == user.team_id,
            Meeting.status == "completed"
        )
    ).order_by(Meeting.created_at.desc()).limit(5)

    result = await db.execute(meetings_query)
    meetings = result.scalars().all()

    # Search in summaries if query has specific keywords
    search_terms = [word for word in query.split() if len(word) > 3]

    relevant_meetings = []
    for meeting in meetings:
        relevance_score = 0
        if meeting.summary:
            for term in search_terms:
                if term.lower() in meeting.summary.lower():
                    relevance_score += 1

        relevant_meetings.append({
            "id": meeting.id,
            "title": meeting.title,
            "date": meeting.created_at.isoformat(),
            "summary": meeting.summary[:500] if meeting.summary else None,
            "relevance": relevance_score
        })

    # Sort by relevance
    relevant_meetings.sort(key=lambda x: x["relevance"], reverse=True)

    return {
        "recent_meetings": relevant_meetings[:3],
        "total_meetings": len(meetings)
    }


def generate_suggested_actions(
    query: str,
    context: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Generate suggested actions based on query and context"""

    suggestions = []

    # If asking about tasks
    if "tasks" in context:
        tasks_data = context["tasks"]

        if tasks_data["count"] > 0:
            suggestions.append({
                "action": "view_tasks",
                "label": f"View all {tasks_data['count']} tasks",
                "url": "/dashboard/tasks"
            })

        # Suggest creating a task if appropriate
        if any(word in query for word in ["create", "add", "new"]):
            suggestions.append({
                "action": "create_task",
                "label": "Create a new task",
                "url": "/dashboard/tasks?action=create"
            })

    # If asking about team
    if "team" in context:
        suggestions.append({
            "action": "view_team",
            "label": "View team workload",
            "url": "/dashboard/analytics"
        })

    # If asking about meetings
    if "meetings" in context:
        meetings_data = context["meetings"]

        if meetings_data.get("recent_meetings"):
            meeting_id = meetings_data["recent_meetings"][0]["id"]
            suggestions.append({
                "action": "view_meeting",
                "label": "View meeting details",
                "url": f"/dashboard/meetings/{meeting_id}"
            })

    return suggestions
