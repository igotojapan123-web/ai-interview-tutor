"""
CORS Configuration.

Cross-Origin Resource Sharing setup for the API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.

    In production, restrict origins to specific domains.
    In development, allow all origins for convenience.
    """
    settings = get_settings()

    # Define allowed origins based on environment
    if settings.environment == "production":
        # Production: restrict to specific domains
        allowed_origins = [
            "https://flyreadylab.com",
            "https://www.flyreadylab.com",
            "https://app.flyreadylab.com",
        ]
    else:
        # Development: allow all origins
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ],
        max_age=600  # Cache preflight requests for 10 minutes
    )
