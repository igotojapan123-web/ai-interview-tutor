"""
FlyReady Lab - Main Application Entry Point.

This module initializes and runs the FastAPI application.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.utils.logging import setup_logging
from src.api.v1.router import api_router
from src.api.v1.middleware import (
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    setup_cors
)
from src.api.v1.middleware.error_handler import setup_exception_handlers
from src.infrastructure.container import get_container, Container

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting FlyReady Lab API...")

    settings = get_settings()

    # Initialize container
    container = get_container()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Additional startup tasks can go here
    # - Database connections
    # - Cache initialization
    # - Background task schedulers

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down FlyReady Lab API...")

    # Cleanup tasks
    Container.reset()

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    # Setup logging
    setup_logging(
        log_level=settings.logging.level,
        json_logs=settings.environment == "production"
    )

    # Create FastAPI app
    app = FastAPI(
        title="FlyReady Lab API",
        description=(
            "AI-powered Flight Attendant Interview Preparation Platform.\n\n"
            "Features:\n"
            "- AI Mock Interviews\n"
            "- Personalized Learning Recommendations\n"
            "- Mentor Matching & Booking\n"
            "- Job Posting Alerts\n"
            "- Cover Letter Review"
        ),
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )

    # Setup CORS
    setup_cors(app)

    # Add middleware (order matters - first added = last executed)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include API router
    app.include_router(
        api_router,
        prefix="/api/v1"
    )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.environment
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "name": "FlyReady Lab API",
            "version": "1.0.0",
            "docs": "/docs" if settings.debug else None,
            "health": "/health"
        }

    return app


# Create app instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.logging.level.lower(),
        access_log=True
    )
