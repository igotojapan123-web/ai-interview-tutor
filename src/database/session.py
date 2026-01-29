"""
Database Session Management.

Handles database connections, session lifecycle, and initialization.
"""

import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Determine database URL
if settings.database.url:
    DATABASE_URL = settings.database.url
else:
    # Use SQLite as default
    db_path = settings.base_dir / settings.database.data_dir / "flyready.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.debug
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Database session context manager.

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in models.
    Should be called on application startup.
    """
    # Import models to register them with Base
    from src.database import models  # noqa: F401

    logger.info(f"Initializing database: {DATABASE_URL}")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized successfully")


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    Use only for testing or development.
    """
    logger.warning("Dropping all database tables!")
    Base.metadata.drop_all(bind=engine)


def health_check() -> bool:
    """
    Check database connectivity.

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


class DatabaseManager:
    """
    Database management utilities.

    Provides methods for database maintenance tasks.
    """

    @staticmethod
    def vacuum() -> None:
        """Vacuum database (SQLite only)."""
        if DATABASE_URL.startswith("sqlite"):
            with engine.connect() as conn:
                conn.execute(text("VACUUM"))
                logger.info("Database vacuumed")

    @staticmethod
    def get_table_stats() -> dict:
        """Get table row counts."""
        stats = {}
        with get_db_context() as db:
            for table in Base.metadata.tables.keys():
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[table] = result.scalar()
                except Exception:
                    stats[table] = -1
        return stats

    @staticmethod
    def backup(filepath: str) -> None:
        """
        Backup database to file (SQLite only).

        Args:
            filepath: Path to backup file
        """
        import shutil

        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            shutil.copy2(db_path, filepath)
            logger.info(f"Database backed up to {filepath}")
        else:
            raise NotImplementedError("Backup only supported for SQLite")
