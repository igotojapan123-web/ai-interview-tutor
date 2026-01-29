"""
Job posting endpoints.

Handles job listings and alerts.
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.api.v1.deps import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    job_service
)
from src.services.job_service import JobService
from src.core.models.job import JobType, RecruitmentStatus, JobSearchCriteria
from src.core.models.user import User
from src.core.exceptions import NotFoundError

router = APIRouter()


# =====================
# Request/Response Schemas
# =====================

class JobPostingResponse(BaseModel):
    id: str
    airline_code: str
    airline_name: str
    title: str
    job_type: str
    status: str
    start_date: Optional[str]
    end_date: Optional[str]
    description: str
    requirements: List[str]
    source_url: Optional[str]
    is_open: bool
    days_until_deadline: Optional[int]


class JobListResponse(BaseModel):
    items: List[JobPostingResponse]
    total: int
    page: int
    page_size: int


class JobAlertRequest(BaseModel):
    airlines: List[str] = []
    job_types: List[str] = []
    notify_new_posting: bool = True
    notify_deadline_7_days: bool = True
    notify_deadline_3_days: bool = True
    notify_deadline_1_day: bool = True


class JobAlertResponse(BaseModel):
    id: str
    airlines: List[str]
    job_types: List[str]
    notify_new_posting: bool
    notify_deadline_7_days: bool
    notify_deadline_3_days: bool
    notify_deadline_1_day: bool


class AirlineSummaryResponse(BaseModel):
    code: str
    name: str
    total_postings: int
    open_postings: int


# =====================
# Endpoints
# =====================

@router.get("/", response_model=JobListResponse)
async def list_jobs(
    airline: Optional[str] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    is_domestic: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    job_svc: JobService = Depends(job_service)
):
    """List job postings with filters."""
    criteria = JobSearchCriteria(
        airline_code=airline,
        job_type=JobType(job_type) if job_type else None,
        status=RecruitmentStatus(status) if status else None,
        is_domestic=is_domestic,
        page=page,
        page_size=page_size
    )

    result = job_svc.search_jobs(criteria)

    items = []
    for job in result["items"]:
        airline_name = job_svc.AIRLINE_NAMES.get(job.airline_code, job.airline_code)
        items.append(JobPostingResponse(
            id=job.id,
            airline_code=job.airline_code,
            airline_name=airline_name,
            title=job.title,
            job_type=job.job_type.value if hasattr(job.job_type, 'value') else job.job_type,
            status=job.status.value if hasattr(job.status, 'value') else job.status,
            start_date=job.start_date.isoformat() if job.start_date else None,
            end_date=job.end_date.isoformat() if job.end_date else None,
            description=job.description,
            requirements=job.requirements,
            source_url=job.source_url,
            is_open=job.is_open,
            days_until_deadline=job.days_until_deadline
        ))

    return JobListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/open")
async def get_open_jobs(
    job_svc: JobService = Depends(job_service)
):
    """Get all currently open job postings."""
    jobs = job_svc.get_open_jobs()
    items = []
    for job in jobs:
        airline_name = job_svc.AIRLINE_NAMES.get(job.airline_code, job.airline_code)
        items.append(JobPostingResponse(
            id=job.id,
            airline_code=job.airline_code,
            airline_name=airline_name,
            title=job.title,
            job_type=job.job_type.value if hasattr(job.job_type, 'value') else job.job_type,
            status=job.status.value if hasattr(job.status, 'value') else job.status,
            start_date=job.start_date.isoformat() if job.start_date else None,
            end_date=job.end_date.isoformat() if job.end_date else None,
            description=job.description,
            requirements=job.requirements,
            source_url=job.source_url,
            is_open=job.is_open,
            days_until_deadline=job.days_until_deadline
        ))
    return items


@router.get("/upcoming-deadlines")
async def get_upcoming_deadlines(
    days: int = Query(7, ge=1, le=30),
    job_svc: JobService = Depends(job_service)
):
    """Get jobs with deadlines within N days."""
    jobs = job_svc.get_upcoming_deadlines(days)
    items = []
    for job in jobs:
        airline_name = job_svc.AIRLINE_NAMES.get(job.airline_code, job.airline_code)
        items.append(JobPostingResponse(
            id=job.id,
            airline_code=job.airline_code,
            airline_name=airline_name,
            title=job.title,
            job_type=job.job_type.value if hasattr(job.job_type, 'value') else job.job_type,
            status=job.status.value if hasattr(job.status, 'value') else job.status,
            start_date=job.start_date.isoformat() if job.start_date else None,
            end_date=job.end_date.isoformat() if job.end_date else None,
            description=job.description,
            requirements=job.requirements,
            source_url=job.source_url,
            is_open=job.is_open,
            days_until_deadline=job.days_until_deadline
        ))
    return items


@router.get("/airlines", response_model=List[AirlineSummaryResponse])
async def get_airline_summary(
    job_svc: JobService = Depends(job_service)
):
    """Get summary of job postings by airline."""
    summary = job_svc.get_airline_summary()
    return [
        AirlineSummaryResponse(
            code=data["code"],
            name=data["name"],
            total_postings=data["total_postings"],
            open_postings=data["open"]
        )
        for data in summary.values()
    ]


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_job(
    job_id: str,
    job_svc: JobService = Depends(job_service)
):
    """Get job posting details."""
    try:
        job = job_svc.get_job(job_id)
        airline_name = job_svc.AIRLINE_NAMES.get(job.airline_code, job.airline_code)
        return JobPostingResponse(
            id=job.id,
            airline_code=job.airline_code,
            airline_name=airline_name,
            title=job.title,
            job_type=job.job_type.value if hasattr(job.job_type, 'value') else job.job_type,
            status=job.status.value if hasattr(job.status, 'value') else job.status,
            start_date=job.start_date.isoformat() if job.start_date else None,
            end_date=job.end_date.isoformat() if job.end_date else None,
            description=job.description,
            requirements=job.requirements,
            source_url=job.source_url,
            is_open=job.is_open,
            days_until_deadline=job.days_until_deadline
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )


# =====================
# Job Alert Endpoints
# =====================

@router.get("/alerts/my", response_model=Optional[JobAlertResponse])
async def get_my_alert(
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(job_service)
):
    """Get current user's job alert preferences."""
    alert = job_svc.get_user_alert(current_user.id)
    if not alert:
        return None

    return JobAlertResponse(
        id=alert.id,
        airlines=alert.airlines,
        job_types=[jt.value if hasattr(jt, 'value') else jt for jt in alert.job_types],
        notify_new_posting=alert.notify_new_posting,
        notify_deadline_7_days=alert.notify_deadline_7_days,
        notify_deadline_3_days=alert.notify_deadline_3_days,
        notify_deadline_1_day=alert.notify_deadline_1_day
    )


@router.put("/alerts/my", response_model=JobAlertResponse)
async def save_my_alert(
    request: JobAlertRequest,
    current_user: User = Depends(get_current_active_user),
    job_svc: JobService = Depends(job_service)
):
    """Save current user's job alert preferences."""
    alert_data = {
        "airlines": request.airlines,
        "job_types": [JobType(jt) for jt in request.job_types],
        "notify_new_posting": request.notify_new_posting,
        "notify_deadline_7_days": request.notify_deadline_7_days,
        "notify_deadline_3_days": request.notify_deadline_3_days,
        "notify_deadline_1_day": request.notify_deadline_1_day
    }

    alert = job_svc.save_user_alert(current_user.id, alert_data)

    return JobAlertResponse(
        id=alert.id,
        airlines=alert.airlines,
        job_types=[jt.value if hasattr(jt, 'value') else jt for jt in alert.job_types],
        notify_new_posting=alert.notify_new_posting,
        notify_deadline_7_days=alert.notify_deadline_7_days,
        notify_deadline_3_days=alert.notify_deadline_3_days,
        notify_deadline_1_day=alert.notify_deadline_1_day
    )


# =====================
# Admin Endpoints
# =====================

@router.get("/stats")
async def get_job_stats(
    admin_user: User = Depends(get_admin_user),
    job_svc: JobService = Depends(job_service)
):
    """Get job posting statistics (admin only)."""
    return job_svc.get_stats()


@router.post("/close-expired")
async def close_expired_jobs(
    admin_user: User = Depends(get_admin_user),
    job_svc: JobService = Depends(job_service)
):
    """Close expired job postings (admin only)."""
    count = job_svc.close_expired_jobs()
    return {"message": f"Closed {count} expired job postings"}


@router.post("/process-alerts")
async def process_deadline_alerts(
    admin_user: User = Depends(get_admin_user),
    job_svc: JobService = Depends(job_service)
):
    """Process and send deadline alerts (admin only)."""
    results = job_svc.process_deadline_alerts()
    return results
