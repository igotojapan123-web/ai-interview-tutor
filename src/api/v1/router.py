"""
API v1 Router.

Aggregates all endpoint routers.
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    auth,
    users,
    payments,
    mentors,
    jobs,
    recommendations
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["Payments"]
)

api_router.include_router(
    mentors.router,
    prefix="/mentors",
    tags=["Mentors"]
)

api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"]
)

api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["Recommendations"]
)
