"""
Job posting repository implementation.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List

from src.repositories.base import JSONRepository
from src.core.models.job import JobPosting, JobType, RecruitmentStatus, JobAlert, JobSearchCriteria


class JobRepository(JSONRepository[JobPosting]):
    """Repository for JobPosting entities."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="job_postings.json",
            entity_class=JobPosting
        )

    def get_open_jobs(self) -> List[JobPosting]:
        """Get all open job postings."""
        return self.find(
            status=lambda s: s in [RecruitmentStatus.OPEN.value, RecruitmentStatus.EXTENDED.value]
        )

    def get_by_airline(self, airline_code: str) -> List[JobPosting]:
        """Get job postings for a specific airline."""
        return self.find(airline_code=airline_code)

    def get_by_job_type(self, job_type: JobType) -> List[JobPosting]:
        """Get job postings by job type."""
        return self.find(job_type=job_type.value)

    def get_upcoming_deadlines(self, days: int = 7) -> List[JobPosting]:
        """Get job postings with deadlines within N days."""
        jobs = self.get_open_jobs()
        today = date.today()
        deadline = today + timedelta(days=days)

        return [
            job for job in jobs
            if job.end_date and today <= job.end_date <= deadline
        ]

    def get_urgent_deadlines(self) -> List[JobPosting]:
        """Get job postings with deadlines within 3 days."""
        return self.get_upcoming_deadlines(3)

    def search(self, criteria: JobSearchCriteria) -> dict:
        """
        Search job postings with criteria.

        Args:
            criteria: Search criteria object

        Returns:
            Paginated results
        """
        jobs = self.get_all()

        # Apply filters
        if criteria.airline_codes:
            jobs = [j for j in jobs if j.airline_code in criteria.airline_codes]

        if criteria.job_types:
            type_values = [t.value for t in criteria.job_types]
            jobs = [j for j in jobs if j.job_type in type_values]

        if criteria.status:
            status_values = [s.value for s in criteria.status]
            jobs = [j for j in jobs if j.status in status_values]

        if criteria.deadline_within_days:
            deadline = date.today() + timedelta(days=criteria.deadline_within_days)
            jobs = [j for j in jobs if j.end_date and j.end_date <= deadline]

        if criteria.posted_after:
            jobs = [j for j in jobs if j.announcement_date and j.announcement_date >= criteria.posted_after]

        if criteria.query:
            query_lower = criteria.query.lower()
            jobs = [
                j for j in jobs
                if query_lower in j.title.lower()
                or query_lower in j.airline_name.lower()
                or (j.description and query_lower in j.description.lower())
            ]

        # Sort
        if criteria.sort_by == "deadline":
            jobs.sort(key=lambda j: j.end_date or date.max, reverse=(criteria.sort_order == "desc"))
        elif criteria.sort_by == "posted":
            jobs.sort(key=lambda j: j.announcement_date or date.min, reverse=(criteria.sort_order == "desc"))
        elif criteria.sort_by == "airline":
            jobs.sort(key=lambda j: j.airline_name, reverse=(criteria.sort_order == "desc"))

        # Paginate
        total = len(jobs)
        start = (criteria.page - 1) * criteria.page_size
        end = start + criteria.page_size

        return {
            "items": jobs[start:end],
            "total": total,
            "page": criteria.page,
            "page_size": criteria.page_size,
            "total_pages": (total + criteria.page_size - 1) // criteria.page_size
        }

    def get_by_content_hash(self, content_hash: str) -> Optional[JobPosting]:
        """Find job posting by content hash (for deduplication)."""
        return self.find_one(content_hash=content_hash)

    def mark_closed_if_expired(self) -> int:
        """Mark expired job postings as closed. Returns count of updated postings."""
        jobs = self.get_open_jobs()
        today = date.today()
        updated = 0

        for job in jobs:
            if job.end_date and job.end_date < today:
                job.mark_closed()
                self.update(job)
                updated += 1

        return updated

    def get_stats(self) -> dict:
        """Get job posting statistics."""
        jobs = self.get_all()

        by_status = {}
        by_airline = {}
        by_type = {}

        for job in jobs:
            status = job.status.value if hasattr(job.status, "value") else job.status
            by_status[status] = by_status.get(status, 0) + 1

            by_airline[job.airline_code] = by_airline.get(job.airline_code, 0) + 1

            jtype = job.job_type.value if hasattr(job.job_type, "value") else job.job_type
            by_type[jtype] = by_type.get(jtype, 0) + 1

        open_count = by_status.get(RecruitmentStatus.OPEN.value, 0)
        upcoming = len(self.get_upcoming_deadlines(7))
        urgent = len(self.get_urgent_deadlines())

        return {
            "total": len(jobs),
            "open": open_count,
            "upcoming_deadlines": upcoming,
            "urgent_deadlines": urgent,
            "by_status": by_status,
            "by_airline": by_airline,
            "by_type": by_type,
            "airlines_count": len(by_airline)
        }


class JobAlertRepository(JSONRepository[JobAlert]):
    """Repository for JobAlert preferences."""

    def __init__(self, data_dir: str = "data"):
        super().__init__(
            data_dir=data_dir,
            filename="job_alerts.json",
            entity_class=JobAlert,
            id_field="user_id"
        )

    def get_by_user(self, user_id: str) -> Optional[JobAlert]:
        """Get alert preferences for a user."""
        return self.find_one(user_id=user_id)

    def get_users_interested_in_airline(self, airline_code: str) -> List[JobAlert]:
        """Get users interested in a specific airline."""
        alerts = self.get_all()
        return [a for a in alerts if airline_code in a.airlines]

    def get_users_for_deadline_notification(self, days: int) -> List[JobAlert]:
        """Get users who want notification for deadline within N days."""
        alerts = self.get_all()

        if days == 7:
            return [a for a in alerts if a.notify_deadline_7_days]
        elif days == 3:
            return [a for a in alerts if a.notify_deadline_3_days]
        elif days == 1:
            return [a for a in alerts if a.notify_deadline_1_day]

        return []

    def get_users_for_new_posting(self, airline_code: str, job_type: JobType) -> List[JobAlert]:
        """Get users who want notification for new postings."""
        alerts = self.get_all()

        return [
            a for a in alerts
            if a.notify_new_posting
            and (not a.airlines or airline_code in a.airlines)
            and (not a.job_types or job_type in a.job_types)
        ]
