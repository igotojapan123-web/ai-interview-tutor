"""
Learning Progress Tracker.

Tracks user learning progress and skill development.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SkillLevel(str, Enum):
    """Skill proficiency levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(str, Enum):
    """Interview skill categories."""
    SELF_INTRODUCTION = "self_introduction"
    MOTIVATION = "motivation"
    SITUATIONAL = "situational"
    SERVICE_MIND = "service_mind"
    ENGLISH = "english"
    COMMUNICATION = "communication"
    BODY_LANGUAGE = "body_language"
    TIME_MANAGEMENT = "time_management"


@dataclass
class SkillProgress:
    """Progress for a specific skill."""
    category: SkillCategory
    level: SkillLevel
    score: float  # 0-100
    practices: int
    last_practiced: Optional[datetime] = None
    trend: str = "stable"  # improving, stable, declining
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "level": self.level.value,
            "score": self.score,
            "practices": self.practices,
            "last_practiced": self.last_practiced.isoformat() if self.last_practiced else None,
            "trend": self.trend,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class LearningProgress:
    """Overall learning progress."""
    user_id: str
    overall_score: float
    overall_level: SkillLevel
    total_practice_time: int  # minutes
    total_sessions: int
    total_questions: int
    streak_days: int
    longest_streak: int
    skills: Dict[SkillCategory, SkillProgress] = field(default_factory=dict)
    badges: List[str] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)
    weekly_goal: int = 5  # sessions per week
    weekly_progress: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.value,
            "total_practice_time": self.total_practice_time,
            "total_sessions": self.total_sessions,
            "total_questions": self.total_questions,
            "streak_days": self.streak_days,
            "longest_streak": self.longest_streak,
            "skills": {k.value: v.to_dict() for k, v in self.skills.items()},
            "badges": self.badges,
            "milestones": self.milestones,
            "weekly_goal": self.weekly_goal,
            "weekly_progress": self.weekly_progress,
        }


class ProgressTracker:
    """
    Learning progress tracker.

    Features:
    - Skill-based progress tracking
    - Level calculation
    - Streak tracking
    - Achievement system
    - Personalized recommendations
    """

    # Level thresholds
    LEVEL_THRESHOLDS = {
        SkillLevel.BEGINNER: 0,
        SkillLevel.ELEMENTARY: 20,
        SkillLevel.INTERMEDIATE: 40,
        SkillLevel.UPPER_INTERMEDIATE: 60,
        SkillLevel.ADVANCED: 80,
        SkillLevel.EXPERT: 95,
    }

    # Badge definitions
    BADGES = {
        "first_interview": {"name": "첫 면접", "description": "첫 모의면접 완료", "icon": "🎯"},
        "week_warrior": {"name": "주간 전사", "description": "일주일 연속 연습", "icon": "🔥"},
        "perfect_score": {"name": "만점왕", "description": "100점 획득", "icon": "👑"},
        "speed_demon": {"name": "스피드 마스터", "description": "시간 내 완벽 답변", "icon": "⚡"},
        "polyglot": {"name": "다국어 마스터", "description": "영어 면접 완료", "icon": "🌍"},
        "consistency": {"name": "꾸준함의 힘", "description": "30일 연속 연습", "icon": "💪"},
        "mentor_star": {"name": "멘토링 스타", "description": "멘토 세션 5회 완료", "icon": "⭐"},
        "improvement": {"name": "성장의 증거", "description": "점수 20점 향상", "icon": "📈"},
    }

    def __init__(self):
        # In-memory storage (use database in production)
        self._progress_data: Dict[str, LearningProgress] = {}

    async def get_progress(self, user_id: str) -> LearningProgress:
        """Get or create user's learning progress."""
        if user_id not in self._progress_data:
            self._progress_data[user_id] = self._create_initial_progress(user_id)

        return self._progress_data[user_id]

    def _create_initial_progress(self, user_id: str) -> LearningProgress:
        """Create initial progress for new user."""
        skills = {}

        for category in SkillCategory:
            skills[category] = SkillProgress(
                category=category,
                level=SkillLevel.BEGINNER,
                score=0,
                practices=0
            )

        return LearningProgress(
            user_id=user_id,
            overall_score=0,
            overall_level=SkillLevel.BEGINNER,
            total_practice_time=0,
            total_sessions=0,
            total_questions=0,
            streak_days=0,
            longest_streak=0,
            skills=skills
        )

    async def update_progress(
        self,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> LearningProgress:
        """
        Update progress after a practice session.

        Args:
            user_id: User identifier
            session_data: Session results including:
                - interview_type: Type of interview
                - score: Overall score (0-100)
                - duration_minutes: Session duration
                - questions_answered: Number of questions
                - category_scores: Dict of category -> score
        """
        progress = await self.get_progress(user_id)

        # Update session counts
        progress.total_sessions += 1
        progress.total_questions += session_data.get("questions_answered", 0)
        progress.total_practice_time += session_data.get("duration_minutes", 0)
        progress.weekly_progress += 1
        progress.updated_at = datetime.utcnow()

        # Update skill scores
        category_scores = session_data.get("category_scores", {})
        for category_name, score in category_scores.items():
            try:
                category = SkillCategory(category_name)
                await self._update_skill(progress, category, score)
            except ValueError:
                continue

        # Update overall score
        await self._recalculate_overall(progress)

        # Update streak
        await self._update_streak(progress)

        # Check for badges
        await self._check_badges(progress, session_data)

        # Check for milestones
        await self._check_milestones(progress)

        return progress

    async def _update_skill(
        self,
        progress: LearningProgress,
        category: SkillCategory,
        new_score: float
    ) -> None:
        """Update a specific skill."""
        skill = progress.skills.get(category)
        if not skill:
            skill = SkillProgress(
                category=category,
                level=SkillLevel.BEGINNER,
                score=0,
                practices=0
            )
            progress.skills[category] = skill

        # Calculate new score (weighted average with recent score having more weight)
        old_weight = 0.7
        new_weight = 0.3

        if skill.practices == 0:
            skill.score = new_score
        else:
            skill.score = (skill.score * old_weight) + (new_score * new_weight)

        skill.practices += 1
        skill.last_practiced = datetime.utcnow()

        # Update level
        skill.level = self._calculate_level(skill.score)

        # Update trend
        skill.trend = self._calculate_trend(skill)

    def _calculate_level(self, score: float) -> SkillLevel:
        """Calculate skill level from score."""
        for level in reversed(list(SkillLevel)):
            if score >= self.LEVEL_THRESHOLDS[level]:
                return level
        return SkillLevel.BEGINNER

    def _calculate_trend(self, skill: SkillProgress) -> str:
        """Calculate skill trend."""
        # Simplified - in production, compare with historical data
        if skill.practices < 3:
            return "stable"
        # This would check recent scores vs older scores
        return "improving"

    async def _recalculate_overall(self, progress: LearningProgress) -> None:
        """Recalculate overall score and level."""
        if not progress.skills:
            return

        total_score = sum(s.score for s in progress.skills.values())
        progress.overall_score = total_score / len(progress.skills)
        progress.overall_level = self._calculate_level(progress.overall_score)

    async def _update_streak(self, progress: LearningProgress) -> None:
        """Update practice streak."""
        # Simplified streak logic
        progress.streak_days += 1

        if progress.streak_days > progress.longest_streak:
            progress.longest_streak = progress.streak_days

    async def _check_badges(
        self,
        progress: LearningProgress,
        session_data: Dict[str, Any]
    ) -> List[str]:
        """Check and award badges."""
        new_badges = []

        # First interview
        if progress.total_sessions == 1 and "first_interview" not in progress.badges:
            progress.badges.append("first_interview")
            new_badges.append("first_interview")

        # Perfect score
        if session_data.get("score", 0) >= 100 and "perfect_score" not in progress.badges:
            progress.badges.append("perfect_score")
            new_badges.append("perfect_score")

        # Week streak
        if progress.streak_days >= 7 and "week_warrior" not in progress.badges:
            progress.badges.append("week_warrior")
            new_badges.append("week_warrior")

        # Month streak
        if progress.streak_days >= 30 and "consistency" not in progress.badges:
            progress.badges.append("consistency")
            new_badges.append("consistency")

        # English interview
        if session_data.get("interview_type") == "english" and "polyglot" not in progress.badges:
            progress.badges.append("polyglot")
            new_badges.append("polyglot")

        return new_badges

    async def _check_milestones(self, progress: LearningProgress) -> List[Dict]:
        """Check and record milestones."""
        new_milestones = []

        # Session milestones
        session_milestones = [10, 25, 50, 100, 250, 500]
        for milestone in session_milestones:
            if progress.total_sessions == milestone:
                new_milestones.append({
                    "type": "sessions",
                    "value": milestone,
                    "achieved_at": datetime.utcnow().isoformat(),
                })

        # Level milestones
        level_order = list(SkillLevel)
        current_idx = level_order.index(progress.overall_level)
        if current_idx > 0:
            new_milestones.append({
                "type": "level",
                "value": progress.overall_level.value,
                "achieved_at": datetime.utcnow().isoformat(),
            })

        progress.milestones.extend(new_milestones)
        return new_milestones

    async def get_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized practice recommendations."""
        progress = await self.get_progress(user_id)

        recommendations = []

        # Find weakest skills
        sorted_skills = sorted(
            progress.skills.values(),
            key=lambda s: s.score
        )

        for skill in sorted_skills[:3]:
            if skill.score < 60:
                recommendations.append({
                    "type": "practice",
                    "category": skill.category.value,
                    "reason": f"{skill.category.value} 점수 향상 필요",
                    "priority": "high" if skill.score < 40 else "medium",
                })

        # Check for skills not practiced recently
        week_ago = datetime.utcnow() - timedelta(days=7)
        for skill in progress.skills.values():
            if skill.last_practiced and skill.last_practiced < week_ago:
                recommendations.append({
                    "type": "review",
                    "category": skill.category.value,
                    "reason": "최근 연습하지 않음",
                    "priority": "low",
                })

        # Weekly goal reminder
        if progress.weekly_progress < progress.weekly_goal:
            remaining = progress.weekly_goal - progress.weekly_progress
            recommendations.append({
                "type": "goal",
                "message": f"주간 목표까지 {remaining}회 남음",
                "priority": "medium",
            })

        return recommendations

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users leaderboard."""
        sorted_users = sorted(
            self._progress_data.values(),
            key=lambda p: (p.overall_score, p.total_sessions),
            reverse=True
        )

        return [
            {
                "rank": i + 1,
                "user_id": p.user_id,
                "score": p.overall_score,
                "level": p.overall_level.value,
                "sessions": p.total_sessions,
                "badges": len(p.badges),
            }
            for i, p in enumerate(sorted_users[:limit])
        ]

    async def get_skill_radar(self, user_id: str) -> Dict[str, float]:
        """Get skill scores for radar chart."""
        progress = await self.get_progress(user_id)

        return {
            category.value: skill.score
            for category, skill in progress.skills.items()
        }


# Singleton instance
progress_tracker = ProgressTracker()
