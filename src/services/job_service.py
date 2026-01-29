"""
Job posting service.

Business logic for job postings and alerts.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
import logging
import hashlib

from src.core.models.job import (
    JobPosting, JobType, RecruitmentStatus, JobAlert, JobSearchCriteria
)
from src.core.exceptions import NotFoundError
from src.repositories.job_repository import JobRepository, JobAlertRepository

logger = logging.getLogger(__name__)


class JobService:
    """Job posting and alert service."""

    AIRLINE_NAMES = {
        "KE": "대한항공", "OZ": "아시아나항공", "7C": "제주항공",
        "LJ": "진에어", "TW": "티웨이항공", "BX": "에어부산",
        "RS": "에어서울", "ZE": "이스타항공",
        "EK": "에미레이트항공", "SQ": "싱가포르항공",
        "CX": "캐세이퍼시픽", "QR": "카타르항공", "EY": "에티하드항공",
        "NH": "전일본공수", "JL": "일본항공"
    }

    def __init__(
        self,
        job_repository: Optional[JobRepository] = None,
        alert_repository: Optional[JobAlertRepository] = None
    ):
        self.job_repo = job_repository or JobRepository()
        self.alert_repo = alert_repository or JobAlertRepository()

    # =====================
    # Job Postings
    # =====================

    def get_job(self, job_id: str) -> JobPosting:
        """Get job posting by ID."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("JobPosting", job_id)
        return job

    def get_open_jobs(self) -> List[JobPosting]:
        """Get all open job postings."""
        return self.job_repo.get_open_jobs()

    def get_jobs_by_airline(self, airline_code: str) -> List[JobPosting]:
        """Get job postings for a specific airline."""
        return self.job_repo.get_by_airline(airline_code)

    def get_upcoming_deadlines(self, days: int = 7) -> List[JobPosting]:
        """Get jobs with deadlines within N days."""
        return self.job_repo.get_upcoming_deadlines(days)

    def search_jobs(self, criteria: JobSearchCriteria) -> Dict[str, Any]:
        """Search job postings."""
        return self.job_repo.search(criteria)

    def create_job(self, job_data: Dict[str, Any]) -> JobPosting:
        """Create a new job posting (admin/crawler)."""
        # Generate content hash for deduplication
        hash_content = f"{job_data.get('airline_code')}_{job_data.get('title')}_{job_data.get('end_date')}"
        content_hash = hashlib.md5(hash_content.encode()).hexdigest()

        # Check for duplicate
        existing = self.job_repo.get_by_content_hash(content_hash)
        if existing:
            logger.debug(f"Duplicate job posting found: {existing.id}")
            return existing

        job = JobPosting(
            **job_data,
            content_hash=content_hash,
            last_crawled_at=datetime.utcnow()
        )

        job = self.job_repo.create(job)
        logger.info(f"Job posting created: {job.id}")

        # Notify interested users
        self._notify_new_job(job)

        return job

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> JobPosting:
        """Update job posting."""
        job = self.get_job(job_id)
        for key, value in updates.items():
            if hasattr(job, key) and value is not None:
                setattr(job, key, value)
        job.last_crawled_at = datetime.utcnow()
        return self.job_repo.update(job)

    def close_expired_jobs(self) -> int:
        """Close expired job postings."""
        count = self.job_repo.mark_closed_if_expired()
        if count > 0:
            logger.info(f"Closed {count} expired job postings")
        return count

    def _notify_new_job(self, job: JobPosting) -> None:
        """Notify users interested in this job."""
        interested = self.alert_repo.get_users_for_new_posting(
            job.airline_code,
            JobType(job.job_type) if isinstance(job.job_type, str) else job.job_type
        )
        if interested:
            logger.info(f"Notifying {len(interested)} users about new job: {job.title}")
            # In production, send notifications via notification service

    # =====================
    # Job Alerts
    # =====================

    def get_user_alert(self, user_id: str) -> Optional[JobAlert]:
        """Get user's job alert preferences."""
        return self.alert_repo.get_by_user(user_id)

    def save_user_alert(self, user_id: str, alert_data: Dict[str, Any]) -> JobAlert:
        """Save user's job alert preferences."""
        existing = self.alert_repo.get_by_user(user_id)

        if existing:
            for key, value in alert_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            return self.alert_repo.save(existing)

        alert = JobAlert(user_id=user_id, **alert_data)
        return self.alert_repo.create(alert)

    def get_users_for_deadline_alert(self, days: int) -> List[JobAlert]:
        """Get users who want deadline alerts."""
        return self.alert_repo.get_users_for_deadline_notification(days)

    def process_deadline_alerts(self) -> Dict[str, int]:
        """Process and send deadline alerts."""
        results = {"7_day": 0, "3_day": 0, "1_day": 0}

        for days, key in [(7, "7_day"), (3, "3_day"), (1, "1_day")]:
            jobs = self.job_repo.get_upcoming_deadlines(days)
            if not jobs:
                continue

            users = self.alert_repo.get_users_for_deadline_notification(days)
            for user_alert in users:
                # Filter jobs based on user preferences
                relevant_jobs = [
                    j for j in jobs
                    if not user_alert.airlines or j.airline_code in user_alert.airlines
                ]
                if relevant_jobs:
                    results[key] += 1
                    # In production, send notification
                    logger.debug(f"Deadline alert for user {user_alert.user_id}: {len(relevant_jobs)} jobs")

        return results

    # =====================
    # Statistics
    # =====================

    def get_stats(self) -> Dict[str, Any]:
        """Get job posting statistics."""
        return self.job_repo.get_stats()

    def get_airline_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary by airline."""
        stats = self.job_repo.get_stats()
        by_airline = stats.get("by_airline", {})

        summary = {}
        for code, count in by_airline.items():
            summary[code] = {
                "code": code,
                "name": self.AIRLINE_NAMES.get(code, code),
                "total_postings": count,
                "open": len([j for j in self.job_repo.get_by_airline(code) if j.is_open])
            }

        return summary
