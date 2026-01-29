"""
Recommendation service.

Business logic for personalized learning recommendations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from src.core.models.recommendation import (
    SkillCategory, SkillProfile, SkillScore,
    LearningContent, ContentType, DifficultyLevel,
    Recommendation, LearningActivity, StudyPlan
)
from src.repositories.base import JSONRepository

logger = logging.getLogger(__name__)


class SkillProfileRepository(JSONRepository[SkillProfile]):
    """Repository for skill profiles."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="skill_profiles.json",
            entity_class=SkillProfile,
            id_field="user_id"
        )


class LearningContentRepository(JSONRepository[LearningContent]):
    """Repository for learning content."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="learning_content.json",
            entity_class=LearningContent
        )

    def get_by_skill(self, skill: SkillCategory) -> List[LearningContent]:
        return self.find(skill_category=skill.value)

    def get_by_type(self, content_type: ContentType) -> List[LearningContent]:
        return self.find(content_type=content_type.value)


class RecommendationService:
    """Personalized learning recommendation service."""

    # Skill weights for interview preparation
    SKILL_WEIGHTS = {
        SkillCategory.SELF_INTRODUCTION: 0.12,
        SkillCategory.MOTIVATION: 0.12,
        SkillCategory.SITUATIONAL: 0.10,
        SkillCategory.SERVICE_MIND: 0.10,
        SkillCategory.ENGLISH_SPEAKING: 0.10,
        SkillCategory.KOREAN_SPEAKING: 0.08,
        SkillCategory.POSTURE: 0.08,
        SkillCategory.GROOMING: 0.06,
        SkillCategory.AVIATION_KNOWLEDGE: 0.06,
        SkillCategory.TEAMWORK: 0.06,
        SkillCategory.COVER_LETTER: 0.06,
        SkillCategory.STRESS_MANAGEMENT: 0.04,
        SkillCategory.SECOND_LANGUAGE: 0.02,
    }

    SKILL_NAMES = {
        SkillCategory.SELF_INTRODUCTION: "자기소개",
        SkillCategory.MOTIVATION: "지원동기",
        SkillCategory.SITUATIONAL: "상황대처",
        SkillCategory.SERVICE_MIND: "서비스 마인드",
        SkillCategory.TEAMWORK: "팀워크",
        SkillCategory.STRESS_MANAGEMENT: "스트레스 관리",
        SkillCategory.KOREAN_SPEAKING: "한국어 스피킹",
        SkillCategory.ENGLISH_SPEAKING: "영어 스피킹",
        SkillCategory.ENGLISH_LISTENING: "영어 리스닝",
        SkillCategory.SECOND_LANGUAGE: "제2외국어",
        SkillCategory.POSTURE: "자세/워킹",
        SkillCategory.MAKEUP: "메이크업",
        SkillCategory.GROOMING: "그루밍",
        SkillCategory.AVIATION_KNOWLEDGE: "항공상식",
        SkillCategory.SAFETY_KNOWLEDGE: "안전지식",
        SkillCategory.SERVICE_KNOWLEDGE: "서비스지식",
        SkillCategory.AIRLINE_INFO: "항공사 정보",
        SkillCategory.RESUME: "이력서",
        SkillCategory.COVER_LETTER: "자기소개서",
        SkillCategory.DOCUMENT_PHOTO: "사진",
    }

    def __init__(
        self,
        profile_repository: Optional[SkillProfileRepository] = None,
        content_repository: Optional[LearningContentRepository] = None
    ):
        self.profile_repo = profile_repository or SkillProfileRepository()
        self.content_repo = content_repository or LearningContentRepository()

    # =====================
    # Skill Profile
    # =====================

    def get_or_create_profile(self, user_id: str) -> SkillProfile:
        """Get or create skill profile for user."""
        profile = self.profile_repo.find_one(user_id=user_id)
        if not profile:
            profile = SkillProfile(user_id=user_id)
            # Initialize with default scores
            for category in SkillCategory:
                profile.skills[category.value] = SkillScore(
                    category=category,
                    score=50.0
                )
            profile = self.profile_repo.create(profile)
        return profile

    def update_skill(self, user_id: str, skill: SkillCategory, score: float) -> SkillProfile:
        """Update a skill score."""
        profile = self.get_or_create_profile(user_id)
        profile.update_skill(skill, score)
        return self.profile_repo.save(profile)

    def record_activity(self, activity: LearningActivity) -> SkillProfile:
        """Record a learning activity and update profile."""
        profile = self.get_or_create_profile(activity.user_id)

        # Update skill if score provided
        if activity.score is not None:
            profile.update_skill(activity.skill_category, activity.score)

        # Update study time
        profile.total_study_time_minutes += activity.duration_seconds // 60

        # Update completion count
        if activity.completed:
            profile.completed_content_count += 1

        profile.last_activity_at = datetime.utcnow()

        return self.profile_repo.save(profile)

    def get_skill_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive skill summary."""
        profile = self.get_or_create_profile(user_id)

        # Convert skills to readable format
        skills_readable = {}
        for cat_key, skill_score in profile.skills.items():
            try:
                category = SkillCategory(cat_key)
                skill_name = self.SKILL_NAMES.get(category, cat_key)
                skills_readable[skill_name] = skill_score.score
            except ValueError:
                skills_readable[cat_key] = skill_score.score if isinstance(skill_score, SkillScore) else skill_score

        # Get weaknesses and strengths
        weaknesses = profile.get_weaknesses(3)
        strengths = profile.get_strengths(3)

        return {
            "readiness_score": profile.overall_readiness,
            "skills": skills_readable,
            "weaknesses": [
                {
                    "skill": self.SKILL_NAMES.get(w.category, str(w.category)),
                    "score": w.score
                }
                for w in weaknesses
            ],
            "strengths": [
                {
                    "skill": self.SKILL_NAMES.get(s.category, str(s.category)),
                    "score": s.score
                }
                for s in strengths
            ],
            "total_study_time": profile.total_study_time_minutes,
            "completed_content": profile.completed_content_count,
            "current_streak": profile.current_streak_days,
            "last_activity": profile.last_activity_at.isoformat() if profile.last_activity_at else None
        }

    # =====================
    # Recommendations
    # =====================

    def get_recommendations(
        self,
        user_id: str,
        limit: int = 5,
        include_premium: bool = False
    ) -> List[Recommendation]:
        """Generate personalized recommendations."""
        profile = self.get_or_create_profile(user_id)
        recommendations = []

        # Get weakest skills
        weaknesses = profile.get_weaknesses(3)

        for weakness in weaknesses:
            # Get content for this skill
            contents = self.content_repo.get_by_skill(weakness.category)

            for content in contents:
                if not include_premium and content.is_premium:
                    continue

                skill_name = self.SKILL_NAMES.get(weakness.category, str(weakness.category))

                rec = Recommendation(
                    content_id=content.id,
                    title=content.title,
                    content_type=content.content_type,
                    skill_category=weakness.category,
                    reason=f"'{skill_name}' 점수가 {weakness.score:.0f}점으로 보완이 필요합니다",
                    priority_score=100 - weakness.score,
                    estimated_improvement=min(15, (100 - weakness.score) * 0.2),
                    is_urgent=weakness.score < 40,
                    current_skill_score=weakness.score
                )
                recommendations.append(rec)

        # Sort by priority
        recommendations.sort(key=lambda r: (r.is_urgent, r.priority_score), reverse=True)

        # Remove duplicates by content_id
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec.content_id not in seen:
                seen.add(rec.content_id)
                unique_recs.append(rec)

        return unique_recs[:limit]

    def get_daily_missions(self, user_id: str) -> List[Recommendation]:
        """Get today's learning missions."""
        recommendations = self.get_recommendations(user_id, limit=3)

        # Try to include variety of content types
        content_types_used = set()
        missions = []

        for rec in recommendations:
            if rec.content_type not in content_types_used or len(missions) < 3:
                missions.append(rec)
                content_types_used.add(rec.content_type)

        return missions

    def generate_study_plan(
        self,
        user_id: str,
        weeks: int = 4,
        target_airline: Optional[str] = None
    ) -> StudyPlan:
        """Generate a personalized study plan."""
        profile = self.get_or_create_profile(user_id)
        weaknesses = profile.get_weaknesses(10)

        weekly_goals = {}
        used_content = set()

        for week in range(1, weeks + 1):
            week_recs = []
            target_difficulty = min(3, (week + 1) // 2)

            for weakness in weaknesses:
                contents = self.content_repo.get_by_skill(weakness.category)

                for content in contents:
                    if content.id in used_content:
                        continue
                    if content.difficulty.value > target_difficulty:
                        continue

                    skill_name = self.SKILL_NAMES.get(weakness.category, str(weakness.category))

                    rec = Recommendation(
                        content_id=content.id,
                        title=content.title,
                        content_type=content.content_type,
                        skill_category=weakness.category,
                        reason=f"{week}주차: '{skill_name}' 강화",
                        priority_score=100 - weakness.score,
                        estimated_improvement=10,
                        is_urgent=False
                    )
                    week_recs.append(rec)
                    used_content.add(content.id)

                    if len(week_recs) >= 5:
                        break

                if len(week_recs) >= 5:
                    break

            weekly_goals[week] = week_recs

        plan = StudyPlan(
            user_id=user_id,
            target_airline=target_airline,
            weekly_goals=weekly_goals,
            total_items=sum(len(recs) for recs in weekly_goals.values())
        )

        return plan

    # =====================
    # Content Management
    # =====================

    def get_content(self, content_id: str) -> Optional[LearningContent]:
        """Get learning content by ID."""
        return self.content_repo.get_by_id(content_id)

    def search_content(
        self,
        query: Optional[str] = None,
        skill: Optional[SkillCategory] = None,
        content_type: Optional[ContentType] = None,
        difficulty: Optional[DifficultyLevel] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search learning content."""
        criteria = {}

        if skill:
            criteria["skill_category"] = skill.value
        if content_type:
            criteria["content_type"] = content_type.value
        if difficulty:
            criteria["difficulty"] = difficulty.value

        contents = self.content_repo.find(**criteria)

        # Apply text search
        if query:
            query_lower = query.lower()
            contents = [
                c for c in contents
                if query_lower in c.title.lower()
                or query_lower in c.description.lower()
                or any(query_lower in tag.lower() for tag in c.tags)
            ]

        # Paginate
        total = len(contents)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "items": contents[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
