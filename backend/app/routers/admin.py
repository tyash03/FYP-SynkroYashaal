"""Admin-only endpoints for user management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional

from app.database import get_db
from app.models import User, Team
from app.models.user import UserRole
from app.schemas.user import UserResponse
from app.dependencies import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in the system. Admin only.
    Returns all users across all teams.
    """
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return users


@router.get("/users/count")
async def get_user_count(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get total user count and breakdown by role. Admin only.
    """
    # Total count
    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar()

    # Count by role
    role_counts = {}
    for role in UserRole:
        role_result = await db.execute(
            select(func.count(User.id)).where(User.role == role)
        )
        role_counts[role.value] = role_result.scalar()

    # Active users
    active_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_count = active_result.scalar()

    # Recent users (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    )
    recent_count = recent_result.scalar()

    return {
        "total": total,
        "active": active_count,
        "inactive": total - active_count,
        "new_last_30_days": recent_count,
        "by_role": role_counts
    }


@router.get("/users/team")
async def get_team_users(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users in the admin's team with details. Admin only.
    """
    result = await db.execute(
        select(User)
        .where(User.team_id == current_admin.team_id)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return {
        "team_id": current_admin.team_id,
        "total": len(user_list),
        "users": user_list
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's role. Admin only.
    """
    valid_roles = {"admin", "project_manager", "team_lead", "senior_developer", "developer", "intern"}
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(valid_roles))}"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role_map = {
        "admin": UserRole.ADMIN,
        "project_manager": UserRole.PROJECT_MANAGER,
        "team_lead": UserRole.TEAM_LEAD,
        "senior_developer": UserRole.SENIOR_DEVELOPER,
        "developer": UserRole.DEVELOPER,
        "intern": UserRole.INTERN,
    }

    user.role = role_map[role]
    await db.commit()
    await db.refresh(user)

    return {"message": f"User role updated to {role}", "user_id": user_id, "new_role": role}


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle a user's active status. Admin only.
    Cannot deactivate yourself.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own active status"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = not user.is_active
    await db.commit()

    return {
        "message": f"User {'activated' if user.is_active else 'deactivated'}",
        "user_id": user_id,
        "is_active": user.is_active
    }


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user from the system. Admin only.
    Cannot delete yourself.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()

    return None


@router.delete("/users", status_code=status.HTTP_200_OK)
async def delete_all_users_except_admin(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all users except the requesting admin. Admin only.
    WARNING: This is a destructive operation.
    """
    result = await db.execute(
        select(User).where(User.id != current_admin.id)
    )
    users_to_delete = result.scalars().all()
    count = len(users_to_delete)

    for user in users_to_delete:
        await db.delete(user)

    await db.commit()

    return {"message": f"Deleted {count} users. Admin account preserved.", "deleted_count": count}
