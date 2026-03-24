"""
Tests for task endpoints.
"""
import pytest
from httpx import AsyncClient
from app.models import Task


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers, test_user):
    """Test task creation."""
    response = await client.post(
        "/api/tasks",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test task description",
            "status": "todo",
            "priority": "medium",
            "source_type": "manual"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test task description"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["team_id"] == test_user.team_id


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient, auth_headers, test_db, test_user):
    """Test getting tasks list."""
    # Create test tasks
    task1 = Task(
        title="Task 1",
        status="todo",
        priority="high",
        team_id=test_user.team_id,
        created_by_id=test_user.id,
        source_type="manual"
    )
    task2 = Task(
        title="Task 2",
        status="in_progress",
        priority="medium",
        team_id=test_user.team_id,
        created_by_id=test_user.id,
        source_type="manual"
    )
    test_db.add_all([task1, task2])
    await test_db.commit()

    response = await client.get(
        "/api/tasks",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client: AsyncClient, auth_headers, test_db, test_user):
    """Test filtering tasks by status."""
    # Create tasks with different statuses
    task1 = Task(
        title="Todo Task",
        status="todo",
        priority="medium",
        team_id=test_user.team_id,
        created_by_id=test_user.id,
        source_type="manual"
    )
    task2 = Task(
        title="Done Task",
        status="done",
        priority="medium",
        team_id=test_user.team_id,
        created_by_id=test_user.id,
        source_type="manual"
    )
    test_db.add_all([task1, task2])
    await test_db.commit()

    response = await client.get(
        "/api/tasks?status=todo",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "todo"


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers, test_db, test_user):
    """Test task update."""
    task = Task(
        title="Original Title",
        status="todo",
        priority="medium",
        team_id=test_user.team_id,
        created_by_id=test_user.id,
        source_type="manual"
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)

    response = await client.patch(
        f"/api/tasks/{task.id}",
        headers=auth_headers,
        json={
            "title": "Updated Title",
            "status": "in_progress"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers, test_db, test_user):
    """Test task deletion."""
    task = Task(
        title="Task to Delete",
        status="todo",
        priority="medium",
        team_id=test_user.team_id,
        created_by_id=test_user.id,
        source_type="manual"
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)

    response = await client.delete(
        f"/api/tasks/{task.id}",
        headers=auth_headers
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_task_stats(client: AsyncClient, auth_headers, test_db, test_user):
    """Test getting task statistics."""
    # Create tasks with different statuses
    tasks = [
        Task(title=f"Task {i}", status=status, priority="medium",
             team_id=test_user.team_id, created_by_id=test_user.id, source_type="manual")
        for i, status in enumerate(["todo", "todo", "in_progress", "done", "done", "done"])
    ]
    test_db.add_all(tasks)
    await test_db.commit()

    response = await client.get(
        "/api/tasks/stats",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 6
    assert data["todo"] == 2
    assert data["in_progress"] == 1
    assert data["done"] == 3
    assert data["completion_rate"] == 50.0
