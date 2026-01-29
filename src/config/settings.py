"""
FlyReady Lab - Configuration Management
Enterprise-grade settings with environment variable support and validation.
"""

from functools import lru_cache
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_V2 = False


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    type: str = Field(default="json", description="Database type: json, sqlite, postgresql")
    host: Optional[str] = Field(default=None, description="Database host")
    port: Optional[int] = Field(default=None, description="Database port")
    name: str = Field(default="flyready", description="Database name")
    user: Optional[str] = Field(default=None, description="Database user")
    password: Optional[str] = Field(default=None, description="Database password")

    # JSON file database paths
    data_dir: str = Field(default="data", description="Data directory for JSON storage")

    @property
    def connection_string(self) -> Optional[str]:
        """Generate database connection string."""
        if self.type == "postgresql":
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        elif self.type == "sqlite":
            return f"sqlite:///{self.data_dir}/{self.name}.db"
        return None

    if PYDANTIC_V2:
        model_config = {"env_prefix": "DB_"}
    else:
        class Config:
            env_prefix = "DB_"


class AuthSettings(BaseSettings):
    """Authentication configuration."""

    # JWT Settings
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key for token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")

    # Kakao OAuth
    kakao_client_id: Optional[str] = Field(default=None, description="Kakao OAuth client ID")
    kakao_client_secret: Optional[str] = Field(default=None, description="Kakao OAuth client secret")
    kakao_redirect_uri: str = Field(
        default="http://localhost:8501/callback/kakao",
        description="Kakao OAuth redirect URI"
    )

    # Google OAuth
    google_client_id: Optional[str] = Field(default=None, description="Google OAuth client ID")
    google_client_secret: Optional[str] = Field(default=None, description="Google OAuth client secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8501/callback/google",
        description="Google OAuth redirect URI"
    )

    # Apple OAuth
    apple_client_id: Optional[str] = Field(default=None, description="Apple OAuth client ID")
    apple_team_id: Optional[str] = Field(default=None, description="Apple Team ID")
    apple_key_id: Optional[str] = Field(default=None, description="Apple Key ID")
    apple_private_key: Optional[str] = Field(default=None, description="Apple private key")

    if PYDANTIC_V2:
        model_config = {"env_prefix": "AUTH_"}
    else:
        class Config:
            env_prefix = "AUTH_"


class PaymentSettings(BaseSettings):
    """Payment gateway configuration."""

    # KakaoPay
    kakaopay_cid: str = Field(default="TC0ONETIME", description="KakaoPay CID")
    kakaopay_admin_key: Optional[str] = Field(default=None, description="KakaoPay Admin Key")
    kakaopay_secret_key: Optional[str] = Field(default=None, description="KakaoPay Secret Key")

    # Toss Payments
    toss_client_key: Optional[str] = Field(default=None, description="Toss client key")
    toss_secret_key: Optional[str] = Field(default=None, description="Toss secret key")

    # Common
    payment_callback_url: str = Field(
        default="http://localhost:8501/payment/callback",
        description="Payment callback URL"
    )
    payment_cancel_url: str = Field(
        default="http://localhost:8501/payment/cancel",
        description="Payment cancel URL"
    )
    payment_fail_url: str = Field(
        default="http://localhost:8501/payment/fail",
        description="Payment fail URL"
    )

    if PYDANTIC_V2:
        model_config = {"env_prefix": "PAYMENT_"}
    else:
        class Config:
            env_prefix = "PAYMENT_"


class NotificationSettings(BaseSettings):
    """Notification service configuration."""

    # Kakao Alimtalk
    kakao_alimtalk_sender_key: Optional[str] = Field(default=None)
    kakao_alimtalk_template_codes: Dict[str, str] = Field(default_factory=dict)

    # Email (SMTP)
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: str = Field(default="noreply@flyreadylab.com")
    smtp_from_name: str = Field(default="FlyReady Lab")
    smtp_use_tls: bool = Field(default=True)

    # Firebase Cloud Messaging
    fcm_server_key: Optional[str] = Field(default=None)
    fcm_project_id: Optional[str] = Field(default=None)

    if PYDANTIC_V2:
        model_config = {"env_prefix": "NOTIFICATION_"}
    else:
        class Config:
            env_prefix = "NOTIFICATION_"


class AISettings(BaseSettings):
    """AI/ML service configuration."""

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4")
    model: str = Field(default="gpt-4")
    openai_max_tokens: int = Field(default=2000)
    max_tokens: int = Field(default=2000)
    openai_temperature: float = Field(default=0.7)

    # Claude (Anthropic)
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-3-opus-20240229")

    # Default provider
    default_provider: str = Field(default="openai", description="Default AI provider")

    if PYDANTIC_V2:
        model_config = {"env_prefix": "AI_"}
    else:
        class Config:
            env_prefix = "AI_"


class SecuritySettings(BaseSettings):
    """Security configuration."""

    # JWT Settings
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60)
    rate_limit_requests_per_hour: int = Field(default=1000)
    rate_limit_burst: int = Field(default=10)

    # Security Headers
    enable_hsts: bool = Field(default=True)
    enable_csp: bool = Field(default=True)
    cors_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"]
    )

    # Password Policy
    password_min_length: int = Field(default=8)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_digit: bool = Field(default=True)
    password_require_special: bool = Field(default=True)

    # Session
    session_timeout_minutes: int = Field(default=60)
    max_sessions_per_user: int = Field(default=5)

    # IP Blocking
    max_failed_login_attempts: int = Field(default=5)
    lockout_duration_minutes: int = Field(default=30)

    # Encryption
    encryption_key: Optional[str] = Field(default=None, description="Data encryption key")

    if PYDANTIC_V2:
        model_config = {"env_prefix": "SECURITY_"}
    else:
        class Config:
            env_prefix = "SECURITY_"


class CacheSettings(BaseSettings):
    """Caching configuration."""

    type: str = Field(default="memory", description="Cache type: memory, redis")
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    default_ttl: int = Field(default=3600, description="Default cache TTL in seconds")

    if PYDANTIC_V2:
        model_config = {"env_prefix": "CACHE_"}
    else:
        class Config:
            env_prefix = "CACHE_"


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        description="Log format"
    )
    file_path: Optional[str] = Field(default="logs/app.log", description="Log file path")
    max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")
    json_format: bool = Field(default=False, description="Use JSON log format")

    if PYDANTIC_V2:
        model_config = {"env_prefix": "LOG_"}
    else:
        class Config:
            env_prefix = "LOG_"


class Settings(BaseSettings):
    """
    Main application settings.

    All settings can be overridden via environment variables.
    Example: APP_NAME=MyApp or AUTH_JWT_SECRET_KEY=mysecret
    """

    # Application
    app_name: str = Field(default="FlyReady Lab", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment: development, staging, production")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")

    # Base paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    static_dir: str = Field(default="static", description="Static files directory")
    templates_dir: str = Field(default="templates", description="Templates directory")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, description="Requests per window")
    rate_limit_window: int = Field(default=60, description="Window in seconds")

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    payment: PaymentSettings = Field(default_factory=PaymentSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    ai: AISettings = Field(default_factory=AISettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    if PYDANTIC_V2:
        model_config = {
            "env_prefix": "APP_",
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": False,
            "extra": "ignore"
        }
    else:
        class Config:
            env_prefix = "APP_"
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure only one Settings instance is created.
    Call get_settings.cache_clear() to reload settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience function for accessing settings
settings = get_settings()
