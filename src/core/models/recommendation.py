"""
Recommendation and learning domain models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import Field

from src.core.models.base import Entity, BaseModel


class SkillCategory(str, Enum):
    """Skill categories for interview preparation."""
    # Interview skills
    SELF_INTRODUCTION = "self_introduction"
    MOTIVATION = "motivation"
    SITUATIONAL = "situational"
    SERVICE_MIND = "service_mind"
    TEAMWORK = "teamwork"
    STRESS_MANAGEMENT = "stress_management"

    # Language skills
    KOREAN_SPEAKING = "korean_speaking"
    ENGLISH_SPEAKING = "english_speaking"
    ENGLISH_LISTENING = "english_listening"
    SECOND_LANGUAGE = "second_language"

    # Image/Presentation
    POSTURE = "posture"
    MAKEUP = "makeup"
    GROOMING = "grooming"

    # Knowledge
    AVIATION_KNOWLEDGE = "aviation_knowledge"
    SAFETY_KNOWLEDGE = "safety_knowledge"
    SERVICE_KNOWLEDGE = "service_knowledge"
    AIRLINE_INFO = "airline_info"

    # Documents
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    DOCUMENT_PHOTO = "document_photo"


class ContentType(str, Enum):
    """Learning content types."""
    VIDEO = "video"
    ARTICLE = "article"
    QUIZ = "quiz"
    PRACTICE = "practice"
    MOCK_INTERVIEW = "mock_interview"
    TEMPLATE = "template"
    CHECKLIST = "checklist"


class DifficultyLevel(int, Enum):
    """Content difficulty levels."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class SkillScore(BaseModel):
    """Individual skill score."""
    category: SkillCategory
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1, default=0.5, description="Confidence in the score")
    last_assessed_at: Optional[datetime] = None
    assessment_count: int = Field(default=0)
    trend: float = Field(default=0, description="Score change trend")


class SkillProfile(Entity):
    """
    User skill profile.

    Tracks a user's skills and progress across different areas.
    """

    user_id: str

    # Skill scores
    skills: Dict[str, SkillScore] = Field(default_factory=dict)

    # Aggregated metrics
    overall_readiness: float = Field(default=50.0, ge=0, le=100)
    total_assessments: int = Field(default=0)
    last_assessment_at: Optional[datetime] = Field(default=None)

    # Learning stats
    total_study_time_minutes: int = Field(default=0)
    completed_content_count: int = Field(default=0)
    current_streak_days: int = Field(default=0)
    longest_streak_days: int = Field(default=0)
    last_activity_at: Optional[datetime] = Field(default=None)

    def get_skill_score(self, category: SkillCategory) -> float:
        """Get score for a specific skill."""
        if category.value in self.skills:
            return self.skills[category.value].score
        return 50.0  # Default score

    def update_skill(self, category: SkillCategory, new_score: float) -> None:
        """Update a skill score."""
        category_key = category.value

        if category_key not in self.skills:
            self.skills[category_key] = SkillScore(
                category=category,
                score=new_score,
                last_assessed_at=datetime.utcnow(),
                assessment_count=1
            )
        else:
            skill = self.skills[category_key]
            old_score = skill.score

            # Calculate weighted average with more weight on recent scores
            weight = min(0.7, 0.3 + (skill.assessment_count * 0.05))
            skill.score = (skill.score * (1 - weight)) + (new_score * weight)
            skill.trend = skill.score - old_score
            skill.assessment_count += 1
            skill.last_assessed_at = datetime.utcnow()

        self.total_assessments += 1
        self.last_assessment_at = datetime.utcnow()
        self._recalculate_readiness()
        self.touch()

    def _recalculate_readiness(self) -> None:
        """Recalculate overall readiness score."""
        if not self.skills:
            self.overall_readiness = 50.0
            return

        # Weighted average based on importance
        weights = {
            SkillCategory.SELF_INTRODUCTION.value: 0.12,
            SkillCategory.MOTIVATION.value: 0.12,
            SkillCategory.SITUATIONAL.value: 0.10,
            SkillCategory.SERVICE_MIND.value: 0.10,
            SkillCategory.ENGLISH_SPEAKING.value: 0.10,
            SkillCategory.KOREAN_SPEAKING.value: 0.08,
            SkillCategory.POSTURE.value: 0.08,
            SkillCategory.GROOMING.value: 0.06,
            SkillCategory.AVIATION_KNOWLEDGE.value: 0.06,
            SkillCategory.TEAMWORK.value: 0.06,
            SkillCategory.COVER_LETTER.value: 0.06,
            SkillCategory.STRESS_MANAGEMENT.value: 0.04,
            SkillCategory.SECOND_LANGUAGE.value: 0.02,
        }

        total_score = 0.0
        total_weight = 0.0

        for category_key, skill in self.skills.items():
            weight = weights.get(category_key, 0.05)
            total_score += skill.score * weight
            total_weight += weight

        if total_weight > 0:
            self.overall_readiness = total_score / total_weight
        else:
            self.overall_readiness = 50.0

    def get_weaknesses(self, top_n: int = 5) -> List[SkillScore]:
        """Get top weakest skills."""
        skills_list = list(self.skills.values())
        skills_list.sort(key=lambda x: x.score)
        return skills_list[:top_n]

    def get_strengths(self, top_n: int = 3) -> List[SkillScore]:
        """Get top strongest skills."""
        skills_list = list(self.skills.values())
        skills_list.sort(key=lambda x: x.score, reverse=True)
        return skills_list[:top_n]


class LearningContent(Entity):
    """
    Learning content entity.

    Represents a piece of educational content.
    """

    # Basic info
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    content_type: ContentType
    skill_category: SkillCategory
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)

    # Content details
    content_url: Optional[str] = Field(default=None)
    content_body: Optional[str] = Field(default=None, description="For articles/text content")
    duration_minutes: int = Field(default=0, ge=0)
    thumbnail_url: Optional[str] = Field(default=None)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list, description="Content IDs")
    related_content: List[str] = Field(default_factory=list, description="Related content IDs")

    # Access control
    is_premium: bool = Field(default=False)
    is_published: bool = Field(default=True)
    published_at: Optional[datetime] = Field(default=None)

    # Stats
    view_count: int = Field(default=0)
    completion_count: int = Field(default=0)
    average_rating: float = Field(default=0.0, ge=0, le=5)
    rating_count: int = Field(default=0)

    # Author
    author_id: Optional[str] = Field(default=None)
    author_name: Optional[str] = Field(default=None)

    def increment_views(self) -> None:
        """Increment view count."""
        self.view_count += 1

    def add_completion(self) -> None:
        """Record a completion."""
        self.completion_count += 1

    def add_rating(self, rating: float) -> None:
        """Add a rating."""
        if self.rating_count == 0:
            self.average_rating = rating
        else:
            total = self.average_rating * self.rating_count
            self.average_rating = (total + rating) / (self.rating_count + 1)
        self.rating_count += 1


class Recommendation(BaseModel):
    """
    Learning recommendation.

    Represents a personalized content recommendation.
    """

    content_id: str
    title: str
    content_type: ContentType
    skill_category: SkillCategory

    # Recommendation details
    reason: str = Field(description="Why this is recommended")
    priority_score: float = Field(ge=0, le=100, description="Higher = more important")
    estimated_improvement: float = Field(ge=0, description="Expected skill improvement")
    is_urgent: bool = Field(default=False)

    # Context
    current_skill_score: Optional[float] = Field(default=None)
    target_skill_score: Optional[float] = Field(default=None)

    # Generated timestamp
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class LearningActivity(BaseModel):
    """User learning activity record."""
    id: str
    user_id: str
    content_id: str
    activity_type: str = Field(description="view, complete, quiz_attempt, etc.")
    skill_category: SkillCategory

    # Results
    score: Optional[float] = Field(default=None, ge=0, le=100)
    duration_seconds: int = Field(default=0)
    completed: bool = Field(default=False)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StudyPlan(BaseModel):
    """Personalized study plan."""
    user_id: str
    target_airline: Optional[str] = Field(default=None)
    target_date: Optional[datetime] = Field(default=None, description="Target interview date")

    # Weekly plan
    weekly_goals: Dict[int, List[Recommendation]] = Field(
        default_factory=dict,
        description="Week number -> list of recommendations"
    )

    # Progress
    total_items: int = Field(default=0)
    completed_items: int = Field(default=0)

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100
