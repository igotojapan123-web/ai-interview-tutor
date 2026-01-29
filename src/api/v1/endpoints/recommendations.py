"""
Recommendation endpoints.

Handles personalized learning recommendations.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.api.v1.deps import (
    get_current_user,
    get_current_active_user,
    get_premium_user,
    recommendation_service
)
from src.services.recommendation_service import RecommendationService
from src.core.models.recommendation import (
    SkillCategory, ContentType, DifficultyLevel, LearningActivity
)
from src.core.models.user import User
from src.core.exceptions import NotFoundError

router = APIRouter()


# =====================
# Request/Response Schemas
# =====================

class SkillScoreResponse(BaseModel):
    skill: str
    score: float


class SkillSummaryResponse(BaseModel):
    readiness_score: float
    skills: dict
    weaknesses: List[SkillScoreResponse]
    strengths: List[SkillScoreResponse]
    total_study_time: int
    completed_content: int
    current_streak: int
    last_activity: Optional[str]


class RecommendationResponse(BaseModel):
    content_id: str
    title: str
    content_type: str
    skill_category: str
    reason: str
    priority_score: float
    estimated_improvement: float
    is_urgent: bool
    current_skill_score: Optional[float]


class ContentResponse(BaseModel):
    id: str
    title: str
    description: str
    content_type: str
    skill_category: str
    difficulty: str
    duration_minutes: int
    is_premium: bool
    tags: List[str]


class ContentListResponse(BaseModel):
    items: List[ContentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SkillUpdateRequest(BaseModel):
    skill: str
    score: float


class ActivityRecordRequest(BaseModel):
    skill_category: str
    content_type: str
    duration_seconds: int
    completed: bool = False
    score: Optional[float] = None


class StudyPlanResponse(BaseModel):
    user_id: str
    target_airline: Optional[str]
    weekly_goals: dict
    total_items: int
    created_at: str


# =====================
# Skill Profile Endpoints
# =====================

@router.get("/profile", response_model=SkillSummaryResponse)
async def get_skill_profile(
    current_user: User = Depends(get_current_active_user),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Get current user's skill profile summary."""
    summary = rec_svc.get_skill_summary(current_user.id)
    return SkillSummaryResponse(
        readiness_score=summary["readiness_score"],
        skills=summary["skills"],
        weaknesses=[SkillScoreResponse(**w) for w in summary["weaknesses"]],
        strengths=[SkillScoreResponse(**s) for s in summary["strengths"]],
        total_study_time=summary["total_study_time"],
        completed_content=summary["completed_content"],
        current_streak=summary["current_streak"],
        last_activity=summary["last_activity"]
    )


@router.post("/profile/skill")
async def update_skill(
    request: SkillUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Update a specific skill score."""
    try:
        skill = SkillCategory(request.skill)
        if not 0 <= request.score <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Score must be between 0 and 100"
            )
        profile = rec_svc.update_skill(current_user.id, skill, request.score)
        return {"message": "Skill updated", "new_score": request.score}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid skill category: {request.skill}"
        )


@router.post("/profile/activity")
async def record_activity(
    request: ActivityRecordRequest,
    current_user: User = Depends(get_current_active_user),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Record a learning activity."""
    try:
        activity = LearningActivity(
            user_id=current_user.id,
            skill_category=SkillCategory(request.skill_category),
            content_type=ContentType(request.content_type),
            duration_seconds=request.duration_seconds,
            completed=request.completed,
            score=request.score
        )
        profile = rec_svc.record_activity(activity)
        return {"message": "Activity recorded"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================
# Recommendation Endpoints
# =====================

@router.get("/", response_model=List[RecommendationResponse])
async def get_recommendations(
    limit: int = Query(5, ge=1, le=20),
    include_premium: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Get personalized learning recommendations."""
    # Premium content for premium users only
    if include_premium and current_user.subscription_tier.value == "free":
        include_premium = False

    recs = rec_svc.get_recommendations(
        current_user.id,
        limit=limit,
        include_premium=include_premium
    )

    return [
        RecommendationResponse(
            content_id=r.content_id,
            title=r.title,
            content_type=r.content_type.value if hasattr(r.content_type, 'value') else r.content_type,
            skill_category=r.skill_category.value if hasattr(r.skill_category, 'value') else r.skill_category,
            reason=r.reason,
            priority_score=r.priority_score,
            estimated_improvement=r.estimated_improvement,
            is_urgent=r.is_urgent,
            current_skill_score=r.current_skill_score
        )
        for r in recs
    ]


@router.get("/daily-missions", response_model=List[RecommendationResponse])
async def get_daily_missions(
    current_user: User = Depends(get_current_active_user),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Get today's learning missions."""
    missions = rec_svc.get_daily_missions(current_user.id)
    return [
        RecommendationResponse(
            content_id=m.content_id,
            title=m.title,
            content_type=m.content_type.value if hasattr(m.content_type, 'value') else m.content_type,
            skill_category=m.skill_category.value if hasattr(m.skill_category, 'value') else m.skill_category,
            reason=m.reason,
            priority_score=m.priority_score,
            estimated_improvement=m.estimated_improvement,
            is_urgent=m.is_urgent,
            current_skill_score=m.current_skill_score
        )
        for m in missions
    ]


@router.get("/study-plan", response_model=StudyPlanResponse)
async def generate_study_plan(
    weeks: int = Query(4, ge=1, le=12),
    target_airline: Optional[str] = None,
    current_user: User = Depends(get_premium_user),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Generate a personalized study plan (premium only)."""
    plan = rec_svc.generate_study_plan(
        current_user.id,
        weeks=weeks,
        target_airline=target_airline
    )

    # Convert weekly goals to serializable format
    weekly_goals = {}
    for week, recs in plan.weekly_goals.items():
        weekly_goals[str(week)] = [
            RecommendationResponse(
                content_id=r.content_id,
                title=r.title,
                content_type=r.content_type.value if hasattr(r.content_type, 'value') else r.content_type,
                skill_category=r.skill_category.value if hasattr(r.skill_category, 'value') else r.skill_category,
                reason=r.reason,
                priority_score=r.priority_score,
                estimated_improvement=r.estimated_improvement,
                is_urgent=r.is_urgent,
                current_skill_score=r.current_skill_score
            ).model_dump()
            for r in recs
        ]

    return StudyPlanResponse(
        user_id=plan.user_id,
        target_airline=plan.target_airline,
        weekly_goals=weekly_goals,
        total_items=plan.total_items,
        created_at=plan.created_at.isoformat()
    )


# =====================
# Content Endpoints
# =====================

@router.get("/content", response_model=ContentListResponse)
async def search_content(
    query: Optional[str] = None,
    skill: Optional[str] = None,
    content_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Search learning content."""
    skill_enum = SkillCategory(skill) if skill else None
    type_enum = ContentType(content_type) if content_type else None
    diff_enum = DifficultyLevel(difficulty) if difficulty else None

    result = rec_svc.search_content(
        query=query,
        skill=skill_enum,
        content_type=type_enum,
        difficulty=diff_enum,
        page=page,
        page_size=page_size
    )

    items = [
        ContentResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            content_type=c.content_type.value if hasattr(c.content_type, 'value') else c.content_type,
            skill_category=c.skill_category.value if hasattr(c.skill_category, 'value') else c.skill_category,
            difficulty=c.difficulty.value if hasattr(c.difficulty, 'value') else c.difficulty,
            duration_minutes=c.duration_minutes,
            is_premium=c.is_premium,
            tags=c.tags
        )
        for c in result["items"]
    ]

    return ContentListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    rec_svc: RecommendationService = Depends(recommendation_service)
):
    """Get learning content details."""
    content = rec_svc.get_content(content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    return ContentResponse(
        id=content.id,
        title=content.title,
        description=content.description,
        content_type=content.content_type.value if hasattr(content.content_type, 'value') else content.content_type,
        skill_category=content.skill_category.value if hasattr(content.skill_category, 'value') else content.skill_category,
        difficulty=content.difficulty.value if hasattr(content.difficulty, 'value') else content.difficulty,
        duration_minutes=content.duration_minutes,
        is_premium=content.is_premium,
        tags=content.tags
    )
