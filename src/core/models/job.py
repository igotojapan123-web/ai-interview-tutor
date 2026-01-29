"""
Job posting domain models.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import Field, HttpUrl

from src.core.models.base import Entity, BaseModel


class JobType(str, Enum):
    """Job types."""
    CABIN_CREW = "cabin_crew"
    GROUND_STAFF = "ground_staff"
    PILOT = "pilot"
    MAINTENANCE = "maintenance"
    OFFICE = "office"
    INTERNSHIP = "internship"


class RecruitmentStatus(str, Enum):
    """Recruitment status."""
    UPCOMING = "upcoming"
    OPEN = "open"
    EXTENDED = "extended"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class AirlineRegion(str, Enum):
    """Airline regions."""
    DOMESTIC = "domestic"
    FOREIGN = "foreign"
    LCC = "lcc"
    FSC = "fsc"


class LanguageRequirement(BaseModel):
    """Language requirement specification."""
    language: str = Field(description="Language code (en, ko, zh, ja, etc.)")
    test_type: Optional[str] = Field(default=None, description="TOEIC, OPIC, HSK, etc.")
    min_score: Optional[str] = Field(default=None, description="Minimum score")
    level: Optional[str] = Field(default=None, description="Level description")
    is_required: bool = Field(default=True)


class PhysicalRequirement(BaseModel):
    """Physical requirement specification."""
    height_min_cm: Optional[int] = Field(default=None)
    height_max_cm: Optional[int] = Field(default=None)
    arm_reach_cm: Optional[int] = Field(default=None, description="Minimum arm reach")
    vision: Optional[str] = Field(default=None, description="Vision requirements")
    swimming: Optional[str] = Field(default=None, description="Swimming requirements")
    bmi_range: Optional[str] = Field(default=None)
    tattoo_policy: Optional[str] = Field(default=None)


class Airline(BaseModel):
    """Airline information."""
    code: str = Field(description="IATA airline code")
    name_ko: str = Field(description="Korean name")
    name_en: str = Field(description="English name")
    region: AirlineRegion
    country: str = Field(default="KR")
    website: Optional[str] = None
    career_page: Optional[str] = None
    logo_url: Optional[str] = None


class JobPosting(Entity):
    """
    Job posting entity.

    Represents an airline job posting with all requirements.
    """

    # Airline info
    airline_code: str
    airline_name: str

    # Basic info
    title: str = Field(min_length=1, max_length=500)
    job_type: JobType
    status: RecruitmentStatus = Field(default=RecruitmentStatus.UPCOMING)

    # Description
    description: Optional[str] = Field(default=None, max_length=10000)
    summary: Optional[str] = Field(default=None, max_length=500)

    # Dates
    announcement_date: Optional[date] = Field(default=None)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    interview_date: Optional[date] = Field(default=None)

    # Requirements
    education: Optional[str] = Field(default=None, description="Education requirements")
    experience: Optional[str] = Field(default=None, description="Experience requirements")
    age_requirement: Optional[str] = Field(default=None)
    military_requirement: Optional[str] = Field(default=None, description="For Korean males")

    # Detailed requirements
    language_requirements: List[LanguageRequirement] = Field(default_factory=list)
    physical_requirements: Optional[PhysicalRequirement] = Field(default=None)

    # Additional requirements stored as key-value
    requirements: Dict[str, str] = Field(default_factory=dict)

    # Location
    location: Optional[str] = Field(default=None)
    base_airports: List[str] = Field(default_factory=list, description="Base airport codes")

    # Compensation
    salary_info: Optional[str] = Field(default=None)
    benefits: List[str] = Field(default_factory=list)

    # Application
    application_url: Optional[str] = Field(default=None)
    application_method: Optional[str] = Field(default=None)
    required_documents: List[str] = Field(default_factory=list)

    # Source
    source_url: Optional[str] = Field(default=None)
    source_name: Optional[str] = Field(default=None, description="Where the posting was found")

    # Crawling metadata
    last_crawled_at: Optional[datetime] = Field(default=None)
    content_hash: Optional[str] = Field(default=None, description="Hash to detect changes")

    # Tags
    tags: List[str] = Field(default_factory=list)

    @property
    def is_open(self) -> bool:
        """Check if job posting is currently open."""
        return self.status in [RecruitmentStatus.OPEN, RecruitmentStatus.EXTENDED]

    @property
    def days_until_deadline(self) -> Optional[int]:
        """Calculate days until deadline."""
        if not self.end_date:
            return None
        delta = self.end_date - date.today()
        return delta.days

    @property
    def is_deadline_near(self) -> bool:
        """Check if deadline is within 7 days."""
        days = self.days_until_deadline
        return days is not None and 0 <= days <= 7

    @property
    def is_deadline_urgent(self) -> bool:
        """Check if deadline is within 3 days."""
        days = self.days_until_deadline
        return days is not None and 0 <= days <= 3

    def mark_closed(self) -> None:
        """Mark posting as closed."""
        self.status = RecruitmentStatus.CLOSED
        self.touch()

    def extend_deadline(self, new_end_date: date) -> None:
        """Extend the application deadline."""
        self.end_date = new_end_date
        self.status = RecruitmentStatus.EXTENDED
        self.touch()


class JobAlert(BaseModel):
    """User job alert preferences."""
    user_id: str
    airlines: List[str] = Field(default_factory=list, description="Interested airline codes")
    job_types: List[JobType] = Field(default_factory=list)
    regions: List[AirlineRegion] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    # Notification settings
    notify_new_posting: bool = Field(default=True)
    notify_deadline_7_days: bool = Field(default=True)
    notify_deadline_3_days: bool = Field(default=True)
    notify_deadline_1_day: bool = Field(default=True)

    # Notification channels
    email_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=True)
    kakao_enabled: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class JobSearchCriteria(BaseModel):
    """Job search criteria."""
    query: Optional[str] = None
    airline_codes: Optional[List[str]] = None
    job_types: Optional[List[JobType]] = None
    status: Optional[List[RecruitmentStatus]] = None
    regions: Optional[List[AirlineRegion]] = None
    deadline_within_days: Optional[int] = None
    posted_after: Optional[date] = None
    sort_by: str = Field(default="deadline", description="deadline, posted, airline")
    sort_order: str = Field(default="asc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
