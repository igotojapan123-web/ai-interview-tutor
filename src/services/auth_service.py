"""
Authentication service.

Handles user authentication, JWT tokens, and OAuth flows.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import logging

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from src.config.settings import get_settings
from src.core.models.user import User, UserCreate, AuthProvider, UserStatus
from src.core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    OAuthError,
    AlreadyExistsError
)
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service.

    Provides methods for user authentication, token management,
    and OAuth integration.
    """

    def __init__(self, user_repository: Optional[UserRepository] = None):
        """
        Initialize auth service.

        Args:
            user_repository: User repository instance (optional, creates default if not provided)
        """
        self.settings = get_settings()
        self.user_repo = user_repository or UserRepository()
        self._secret_key = self.settings.auth.jwt_secret_key
        self._algorithm = self.settings.auth.jwt_algorithm

    # =====================
    # Password Handling
    # =====================

    def hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256 with salt.

        In production, use bcrypt or argon2.
        """
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}${hashed}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, stored_hash = hashed_password.split("$")
            computed_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            return secrets.compare_digest(computed_hash, stored_hash)
        except ValueError:
            return False

    # =====================
    # JWT Token Management
    # =====================

    def create_access_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User ID to encode
            additional_claims: Additional claims to include

        Returns:
            JWT token string
        """
        if not JWT_AVAILABLE:
            # Fallback simple token
            return f"token_{user_id}_{secrets.token_hex(16)}"

        expire = datetime.utcnow() + timedelta(
            minutes=self.settings.auth.access_token_expire_minutes
        )

        payload = {
            "sub": user_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
            **(additional_claims or {})
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        if not JWT_AVAILABLE:
            return f"refresh_{user_id}_{secrets.token_hex(32)}"

        expire = datetime.utcnow() + timedelta(
            days=self.settings.auth.refresh_token_expire_days
        )

        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            token_type: Expected token type (access/refresh)

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token is expired
            InvalidTokenError: If token is invalid
        """
        if not JWT_AVAILABLE:
            # Simple validation for fallback tokens
            if token.startswith(f"{token_type}_"):
                parts = token.split("_")
                if len(parts) >= 3:
                    return {"sub": parts[1], "type": token_type}
            raise InvalidTokenError()

        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

            if payload.get("type") != token_type:
                raise InvalidTokenError(f"Expected {token_type} token")

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(str(e))

    def create_token_pair(self, user: User) -> Dict[str, str]:
        """
        Create access and refresh token pair.

        Returns:
            Dict with access_token, refresh_token, and token_type
        """
        additional_claims = {
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "tier": user.subscription_tier.value if hasattr(user.subscription_tier, "value") else user.subscription_tier
        }

        return {
            "access_token": self.create_access_token(user.id, additional_claims),
            "refresh_token": self.create_refresh_token(user.id),
            "token_type": "bearer",
            "expires_in": self.settings.auth.access_token_expire_minutes * 60
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            TokenExpiredError: If refresh token is expired
            InvalidTokenError: If refresh token is invalid
        """
        payload = self.verify_token(refresh_token, "refresh")
        user_id = payload["sub"]

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidTokenError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is not active")

        return self.create_token_pair(user)

    # =====================
    # Authentication
    # =====================

    def authenticate(self, email: str, password: str) -> Tuple[User, Dict[str, str]]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (User, token_dict)

        Raises:
            InvalidCredentialsError: If credentials are invalid
            AuthenticationError: If user is not active
        """
        user = self.user_repo.get_by_email(email)

        if not user:
            raise InvalidCredentialsError()

        if user.auth_provider != AuthProvider.LOCAL:
            raise InvalidCredentialsError(
                f"Please use {user.auth_provider.value} to login"
            )

        if not user.hashed_password or not self.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            if user.status == UserStatus.PENDING:
                raise AuthenticationError("Please verify your email first")
            elif user.status == UserStatus.SUSPENDED:
                raise AuthenticationError(f"Account suspended: {user.status_reason}")
            else:
                raise AuthenticationError("Account is not active")

        # Record login
        user.record_login()
        self.user_repo.update(user)

        tokens = self.create_token_pair(user)
        logger.info(f"User authenticated: {user.id}")

        return user, tokens

    def register(self, user_data: UserCreate) -> Tuple[User, Dict[str, str]]:
        """
        Register a new user.

        Args:
            user_data: User creation data

        Returns:
            Tuple of (User, token_dict)

        Raises:
            AlreadyExistsError: If email already exists
        """
        # Check if email exists
        if self.user_repo.email_exists(user_data.email):
            raise AlreadyExistsError("User", user_data.email, "Email already registered")

        # Create user
        user = User(
            email=user_data.email,
            name=user_data.name,
            auth_provider=user_data.auth_provider,
            provider_id=user_data.provider_id,
            phone=user_data.phone,
            profile_image=user_data.profile_image,
            status=UserStatus.ACTIVE if user_data.auth_provider != AuthProvider.LOCAL else UserStatus.PENDING
        )

        # Hash password for local auth
        if user_data.password and user_data.auth_provider == AuthProvider.LOCAL:
            user.hashed_password = self.hash_password(user_data.password)

        # Save user
        user = self.user_repo.create(user)
        logger.info(f"New user registered: {user.id}")

        # For OAuth users, automatically activate
        if user_data.auth_provider != AuthProvider.LOCAL:
            user.activate()
            self.user_repo.update(user)

        tokens = self.create_token_pair(user)

        return user, tokens

    # =====================
    # OAuth
    # =====================

    def get_oauth_url(self, provider: AuthProvider) -> str:
        """
        Get OAuth authorization URL.

        Args:
            provider: OAuth provider

        Returns:
            Authorization URL
        """
        if provider == AuthProvider.KAKAO:
            return (
                f"https://kauth.kakao.com/oauth/authorize"
                f"?client_id={self.settings.auth.kakao_client_id}"
                f"&redirect_uri={self.settings.auth.kakao_redirect_uri}"
                f"&response_type=code"
            )
        elif provider == AuthProvider.GOOGLE:
            return (
                f"https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={self.settings.auth.google_client_id}"
                f"&redirect_uri={self.settings.auth.google_redirect_uri}"
                f"&response_type=code"
                f"&scope=email%20profile"
            )
        elif provider == AuthProvider.APPLE:
            return (
                f"https://appleid.apple.com/auth/authorize"
                f"?client_id={self.settings.auth.apple_client_id}"
                f"&redirect_uri={self.settings.auth.kakao_redirect_uri}"
                f"&response_type=code"
                f"&scope=email%20name"
            )

        raise OAuthError(provider.value, "Unsupported provider")

    async def process_oauth_callback(
        self,
        provider: AuthProvider,
        code: str
    ) -> Tuple[User, Dict[str, str]]:
        """
        Process OAuth callback.

        Args:
            provider: OAuth provider
            code: Authorization code

        Returns:
            Tuple of (User, token_dict)

        Raises:
            OAuthError: If OAuth process fails
        """
        try:
            # Exchange code for token and get user info
            # This would call the actual OAuth APIs
            user_info = await self._fetch_oauth_user_info(provider, code)

            # Check if user exists
            existing_user = self.user_repo.get_by_provider(provider, user_info["id"])

            if existing_user:
                existing_user.record_login()
                self.user_repo.update(existing_user)
                tokens = self.create_token_pair(existing_user)
                return existing_user, tokens

            # Check if email is already registered with different provider
            if user_info.get("email"):
                email_user = self.user_repo.get_by_email(user_info["email"])
                if email_user and email_user.auth_provider != provider:
                    raise OAuthError(
                        provider.value,
                        f"Email already registered with {email_user.auth_provider.value}"
                    )

            # Create new user
            user_data = UserCreate(
                email=user_info.get("email", f"{provider.value}_{user_info['id']}@oauth.local"),
                name=user_info.get("name", "User"),
                auth_provider=provider,
                provider_id=user_info["id"],
                profile_image=user_info.get("picture")
            )

            return self.register(user_data)

        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            raise OAuthError(provider.value, str(e))

    async def _fetch_oauth_user_info(self, provider: AuthProvider, code: str) -> Dict[str, Any]:
        """
        Fetch user info from OAuth provider.

        This is a placeholder - implement actual API calls.
        """
        # In production, make actual HTTP requests to OAuth providers
        # For now, return mock data
        return {
            "id": f"{provider.value}_{code[:8]}",
            "email": f"user_{code[:6]}@{provider.value}.com",
            "name": "OAuth User",
            "picture": None
        }

    # =====================
    # Utilities
    # =====================

    def get_current_user(self, token: str) -> User:
        """
        Get current user from token.

        Args:
            token: JWT access token

        Returns:
            User object

        Raises:
            AuthenticationError: If user not found or not active
        """
        payload = self.verify_token(token, "access")
        user_id = payload["sub"]

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is not active")

        return user

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Returns:
            True if successful

        Raises:
            InvalidCredentialsError: If current password is wrong
        """
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.hashed_password:
            raise InvalidCredentialsError()

        if not self.verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")

        user.hashed_password = self.hash_password(new_password)
        self.user_repo.update(user)

        logger.info(f"Password changed for user: {user_id}")
        return True

    def request_password_reset(self, email: str) -> str:
        """
        Request password reset.

        Returns:
            Reset token (in production, send via email)
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal if email exists
            return secrets.token_urlsafe(32)

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)

        # Store token (in production, save to database with expiry)
        # For now, just return it
        logger.info(f"Password reset requested for: {email}")

        return reset_token
