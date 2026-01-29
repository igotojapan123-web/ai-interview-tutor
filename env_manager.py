# env_manager.py
# FlyReady Lab - Enterprise Environment Configuration Management
# Stage 5: Samsung-level environment configuration

import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
from enum import Enum

from logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# Environment Types
# =============================================================================

class Environment(Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


# =============================================================================
# Configuration Dataclasses
# =============================================================================

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    json_format: bool = False


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = ""
    token_expiry: int = 3600  # seconds
    max_login_attempts: int = 5
    lockout_duration: int = 300  # seconds
    csrf_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    allowed_hosts: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1
    metrics_enabled: bool = True
    health_check_interval: int = 30  # seconds


@dataclass
class APIConfig:
    """API keys configuration"""
    openai_api_key: str = ""
    google_tts_api_key: str = ""
    did_api_key: str = ""
    clova_client_id: str = ""
    clova_client_secret: str = ""


@dataclass
class AppConfig:
    """Main application configuration"""
    env: Environment = Environment.DEVELOPMENT
    debug: bool = False
    app_name: str = "FlyReady Lab"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8501

    # Sub-configurations
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    api: APIConfig = field(default_factory=APIConfig)

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent / "data")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent / "logs")


# =============================================================================
# Environment-specific Configurations
# =============================================================================

def get_development_config() -> AppConfig:
    """Development environment configuration"""
    return AppConfig(
        env=Environment.DEVELOPMENT,
        debug=True,
        logging=LoggingConfig(
            level="DEBUG",
            json_format=False
        ),
        security=SecurityConfig(
            csrf_enabled=False,
            rate_limit_requests=1000
        ),
        monitoring=MonitoringConfig(
            sentry_traces_sample_rate=1.0,
            metrics_enabled=True
        )
    )


def get_staging_config() -> AppConfig:
    """Staging environment configuration"""
    return AppConfig(
        env=Environment.STAGING,
        debug=False,
        logging=LoggingConfig(
            level="INFO",
            json_format=True,
            file_path="logs/app.log"
        ),
        security=SecurityConfig(
            csrf_enabled=True,
            rate_limit_requests=200
        ),
        monitoring=MonitoringConfig(
            sentry_traces_sample_rate=0.5,
            metrics_enabled=True
        )
    )


def get_production_config() -> AppConfig:
    """Production environment configuration"""
    return AppConfig(
        env=Environment.PRODUCTION,
        debug=False,
        logging=LoggingConfig(
            level="WARNING",
            json_format=True,
            file_path="logs/app.log"
        ),
        security=SecurityConfig(
            csrf_enabled=True,
            rate_limit_requests=100,
            allowed_hosts=["flyreadylab.com", "www.flyreadylab.com"]
        ),
        monitoring=MonitoringConfig(
            sentry_traces_sample_rate=0.1,
            metrics_enabled=True
        )
    )


def get_test_config() -> AppConfig:
    """Test environment configuration"""
    return AppConfig(
        env=Environment.TEST,
        debug=True,
        logging=LoggingConfig(
            level="DEBUG",
            json_format=False
        ),
        security=SecurityConfig(
            csrf_enabled=False,
            rate_limit_requests=10000
        ),
        monitoring=MonitoringConfig(
            metrics_enabled=False
        )
    )


# =============================================================================
# Configuration Factory
# =============================================================================

_CONFIG_MAP = {
    "development": get_development_config,
    "staging": get_staging_config,
    "production": get_production_config,
    "test": get_test_config,
}

_current_config: Optional[AppConfig] = None


def get_config(env: str = None) -> AppConfig:
    """
    Get configuration for the specified environment.

    Args:
        env: Environment name. If None, reads from ENV environment variable.

    Returns:
        AppConfig instance for the specified environment.
    """
    global _current_config

    if env is None:
        env = os.environ.get("ENV", "development").lower()

    if env not in _CONFIG_MAP:
        logger.warning(f"Unknown environment: {env}. Falling back to development.")
        env = "development"

    config = _CONFIG_MAP[env]()

    # Override with environment variables
    _apply_env_overrides(config)

    # Ensure directories exist
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)

    _current_config = config
    logger.info(f"Configuration loaded for environment: {env}")
    return config


def _apply_env_overrides(config: AppConfig):
    """Apply environment variable overrides to configuration"""

    # API Keys
    config.api.openai_api_key = os.environ.get("OPENAI_API_KEY", config.api.openai_api_key)
    config.api.google_tts_api_key = os.environ.get("GOOGLE_TTS_API_KEY", config.api.google_tts_api_key)
    config.api.did_api_key = os.environ.get("DID_API_KEY", config.api.did_api_key)
    config.api.clova_client_id = os.environ.get("CLOVA_CLIENT_ID", config.api.clova_client_id)
    config.api.clova_client_secret = os.environ.get("CLOVA_CLIENT_SECRET", config.api.clova_client_secret)

    # Security
    config.security.secret_key = os.environ.get("SECRET_KEY", config.security.secret_key)

    # Monitoring
    config.monitoring.sentry_dsn = os.environ.get("SENTRY_DSN", config.monitoring.sentry_dsn)


def get_current_config() -> AppConfig:
    """Get the current configuration (must call get_config first)"""
    global _current_config
    if _current_config is None:
        return get_config()
    return _current_config


# =============================================================================
# Configuration Validation
# =============================================================================

def validate_config(config: AppConfig) -> List[str]:
    """
    Validate configuration and return list of warnings/errors.

    Returns:
        List of validation messages (empty if all OK)
    """
    messages = []

    # Check required API keys
    if not config.api.openai_api_key:
        messages.append("WARNING: OPENAI_API_KEY is not set")

    # Check security in production
    if config.env == Environment.PRODUCTION:
        if not config.security.secret_key:
            messages.append("ERROR: SECRET_KEY must be set in production")
        if config.debug:
            messages.append("ERROR: Debug mode should be disabled in production")
        if "*" in config.security.allowed_hosts:
            messages.append("WARNING: Wildcard in allowed_hosts is not recommended for production")

    # Check Sentry in production
    if config.env == Environment.PRODUCTION and not config.monitoring.sentry_dsn:
        messages.append("WARNING: SENTRY_DSN is not set for production monitoring")

    return messages


# =============================================================================
# Convenience Functions
# =============================================================================

def is_development() -> bool:
    """Check if running in development environment"""
    return get_current_config().env == Environment.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production environment"""
    return get_current_config().env == Environment.PRODUCTION


def is_test() -> bool:
    """Check if running in test environment"""
    return get_current_config().env == Environment.TEST


def get_env_name() -> str:
    """Get current environment name"""
    return get_current_config().env.value
