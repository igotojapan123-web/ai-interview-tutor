"""
Logging Configuration.

Comprehensive logging setup for the application.
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "__dict__"):
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in (
                    "name", "msg", "args", "created", "filename",
                    "funcName", "levelname", "levelno", "lineno",
                    "module", "msecs", "pathname", "process",
                    "processName", "relativeCreated", "stack_info",
                    "exc_info", "exc_text", "thread", "threadName",
                    "message", "asctime"
                )
            }
            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.

    Adds color codes to log messages based on level.
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # Get color for level
        color = self.COLORS.get(record.levelname, self.RESET)

        # Format the record
        formatted = super().format(record)

        # Add color
        return f"{color}{formatted}{self.RESET}"


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    json_logs: bool = False
) -> None:
    """
    Setup application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format string (ignored if json_logs=True)
        log_file: Path to log file (optional)
        json_logs: Whether to use JSON format for logs
    """
    settings = get_settings()

    # Use settings if not provided
    level = log_level or settings.logging.level
    format_str = log_format or settings.logging.format

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_logs or settings.environment == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter(format_str))

    root_logger.addHandler(console_handler)

    # File handler (if specified)
    file_path = log_file or settings.logging.file_path
    if file_path:
        _setup_file_handler(root_logger, file_path, level, json_logs)

    # Set levels for third-party loggers
    _configure_library_loggers()

    logging.info(
        "Logging configured",
        extra={
            "level": level,
            "json_logs": json_logs,
            "file": file_path
        }
    )


def _setup_file_handler(
    logger: logging.Logger,
    file_path: str,
    level: str,
    json_logs: bool
) -> None:
    """Setup rotating file handler."""
    # Ensure directory exists
    log_dir = Path(file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, level.upper()))

    if json_logs:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    logger.addHandler(file_handler)


def _configure_library_loggers() -> None:
    """Configure logging levels for third-party libraries."""
    # Reduce noise from chatty libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter with context support.

    Allows adding context to all log messages.
    """

    def __init__(self, logger: logging.Logger, context: Dict[str, Any] = None):
        super().__init__(logger, context or {})

    def process(self, msg, kwargs):
        # Merge context with extra
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with context.

    Args:
        name: Logger name
        **context: Context key-value pairs to include in all logs

    Returns:
        Logger adapter with context
    """
    base_logger = logging.getLogger(name)
    return LoggerAdapter(base_logger, context)


# Audit logging for sensitive operations
class AuditLogger:
    """
    Specialized logger for audit trail.

    Logs security-sensitive operations with structured data.
    """

    def __init__(self):
        self.logger = logging.getLogger("audit")

    def log_auth_event(
        self,
        event_type: str,
        user_id: Optional[str],
        success: bool,
        details: Dict[str, Any] = None
    ) -> None:
        """Log authentication event."""
        self.logger.info(
            f"Auth event: {event_type}",
            extra={
                "audit_type": "authentication",
                "event_type": event_type,
                "user_id": user_id,
                "success": success,
                "details": details or {}
            }
        )

    def log_access_event(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        details: Dict[str, Any] = None
    ) -> None:
        """Log resource access event."""
        self.logger.info(
            f"Access event: {user_id} {action} {resource}",
            extra={
                "audit_type": "access",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "success": success,
                "details": details or {}
            }
        )

    def log_data_change(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        changes: Dict[str, Any] = None
    ) -> None:
        """Log data modification event."""
        self.logger.info(
            f"Data change: {entity_type}/{entity_id} {action}",
            extra={
                "audit_type": "data_change",
                "user_id": user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "changes": changes or {}
            }
        )


# Singleton audit logger
audit_logger = AuditLogger()
