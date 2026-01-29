"""
User management endpoints.

Handles user profiles and preferences.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr

from src.api.v1.deps import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    user_service
)
from src.services.user_service import UserService
from src.core.models.user import User
from src.core.exceptions import NotFoundError, ValidationError

router = APIRouter()


# =====================
# Request/Response Schemas
# =====================

class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str]
    profile_image: Optional[str]
    target_airlines: List[str]
    subscription_tier: str
    subscription_expires_at: Optional[str]
    total_sessions: int
    interview_sessions_today: int
    interview_limit_daily: int

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    target_airlines: Optional[List[str]] = None


class UserPreferencesRequest(BaseModel):
    notification_email: Optional[bool] = None
    notification_push: Optional[bool] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class UsageStatsResponse(BaseModel):
    interview_sessions_today: int
    interview_limit_daily: int
    cover_letter_reviews_this_month: int
    cover_letter_limit_monthly: int
    mentor_sessions_this_month: int
    mentor_session_limit_monthly: int


class UserListResponse(BaseModel):
    items: List[UserProfileResponse]
    total: int
    page: int
    page_size: int


# =====================
# Endpoints
# =====================

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    user_svc: UserService = Depends(user_service)
):
    """Get current user's full profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        profile_image=current_user.profile_image,
        target_airlines=current_user.target_airlines,
        subscription_tier=current_user.subscription_tier.value,
        subscription_expires_at=current_user.subscription_expires_at.isoformat() if current_user.subscription_expires_at else None,
        total_sessions=current_user.total_sessions,
        interview_sessions_today=current_user.interview_sessions_today,
        interview_limit_daily=current_user.interview_limit_daily
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    user_svc: UserService = Depends(user_service)
):
    """Update current user's profile."""
    try:
        updates = request.model_dump(exclude_unset=True)
        updated_user = user_svc.update_profile(current_user.id, updates)
        return UserProfileResponse(
            id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            phone=updated_user.phone,
            profile_image=updated_user.profile_image,
            target_airlines=updated_user.target_airlines,
            subscription_tier=updated_user.subscription_tier.value,
            subscription_expires_at=updated_user.subscription_expires_at.isoformat() if updated_user.subscription_expires_at else None,
            total_sessions=updated_user.total_sessions,
            interview_sessions_today=updated_user.interview_sessions_today,
            interview_limit_daily=updated_user.interview_limit_daily
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me/usage", response_model=UsageStatsResponse)
async def get_my_usage(
    current_user: User = Depends(get_current_active_user),
    user_svc: UserService = Depends(user_service)
):
    """Get current user's usage statistics."""
    limits = user_svc.get_usage_limits(current_user.id)
    return UsageStatsResponse(**limits)


@router.post("/me/usage/interview")
async def record_interview_usage(
    current_user: User = Depends(get_current_active_user),
    user_svc: UserService = Depends(user_service)
):
    """Record an interview session usage."""
    try:
        user_svc.record_interview_session(current_user.id)
        return {"message": "Usage recorded"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )


@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    user_svc: UserService = Depends(user_service)
):
    """Delete current user's account."""
    user_svc.delete_user(current_user.id)
    return {"message": "Account deleted successfully"}


# =====================
# Admin Endpoints
# =====================

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    user_svc: UserService = Depends(user_service)
):
    """List all users (admin only)."""
    result = user_svc.search_users(
        query=query,
        page=page,
        page_size=page_size
    )

    items = [
        UserProfileResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            phone=u.phone,
            profile_image=u.profile_image,
            target_airlines=u.target_airlines,
            subscription_tier=u.subscription_tier.value,
            subscription_expires_at=u.subscription_expires_at.isoformat() if u.subscription_expires_at else None,
            total_sessions=u.total_sessions,
            interview_sessions_today=u.interview_sessions_today,
            interview_limit_daily=u.interview_limit_daily
        )
        for u in result["items"]
    ]

    return UserListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: str,
    admin_user: User = Depends(get_admin_user),
    user_svc: UserService = Depends(user_service)
):
    """Get specific user (admin only)."""
    try:
        user = user_svc.get_user(user_id)
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            profile_image=user.profile_image,
            target_airlines=user.target_airlines,
            subscription_tier=user.subscription_tier.value,
            subscription_expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            total_sessions=user.total_sessions,
            interview_sessions_today=user.interview_sessions_today,
            interview_limit_daily=user.interview_limit_daily
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
