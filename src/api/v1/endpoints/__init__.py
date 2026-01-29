"""API v1 endpoints package."""

from src.api.v1.endpoints import (
    auth,
    users,
    payments,
    mentors,
    jobs,
    recommendations
)

__all__ = [
    "auth",
    "users",
    "payments",
    "mentors",
    "jobs",
    "recommendations"
]
