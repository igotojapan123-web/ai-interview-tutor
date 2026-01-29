"""
Security Module.

Enterprise-grade security components for FlyReady Lab.
"""

from src.security.encryption import (
    EncryptionService,
    encryption_service,
    hash_password,
    verify_password,
)
from src.security.authentication import (
    JWTService,
    jwt_service,
    get_current_user,
    require_auth,
    require_role,
)
from src.security.middleware import (
    SecurityMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
)
from src.security.validators import (
    InputValidator,
    sanitize_input,
    validate_email,
    validate_password_strength,
)

__all__ = [
    # Encryption
    "EncryptionService",
    "encryption_service",
    "hash_password",
    "verify_password",
    # Authentication
    "JWTService",
    "jwt_service",
    "get_current_user",
    "require_auth",
    "require_role",
    # Middleware
    "SecurityMiddleware",
    "RateLimitMiddleware",
    "RequestValidationMiddleware",
    # Validators
    "InputValidator",
    "sanitize_input",
    "validate_email",
    "validate_password_strength",
]
