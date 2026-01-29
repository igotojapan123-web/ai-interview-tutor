"""
Authentication endpoints.

Handles user authentication, registration, and OAuth flows.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr

from src.api.v1.deps import (
    get_current_user,
    get_current_active_user,
    auth_service,
    user_service
)
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.core.models.user import User, AuthProvider
from src.core.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError
)

router = APIRouter()


# =====================
# Request/Response Schemas
# =====================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    profile_image: Optional[str]
    subscription_tier: str
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


# =====================
# Endpoints
# =====================

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_svc: AuthService = Depends(auth_service)
):
    """Authenticate user with email and password."""
    try:
        user, tokens = auth_svc.authenticate(request.email, request.password)
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=3600
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_svc: AuthService = Depends(auth_service)
):
    """Register new user with email and password."""
    try:
        user = auth_svc.register(
            email=request.email,
            password=request.password,
            name=request.name
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_image=user.profile_image,
            subscription_tier=user.subscription_tier.value,
            is_active=user.is_active
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_svc: AuthService = Depends(auth_service)
):
    """Refresh access token using refresh token."""
    try:
        tokens = auth_svc.refresh_token(request.refresh_token)
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=3600
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(
    provider: str,
    redirect_uri: Optional[str] = Query(None),
    auth_svc: AuthService = Depends(auth_service)
):
    """Get OAuth authorization URL for provider."""
    try:
        provider_enum = AuthProvider(provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )

    auth_url = auth_svc.get_oauth_url(provider_enum, redirect_uri)
    return {"authorization_url": auth_url}


@router.post("/oauth/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    request: OAuthCallbackRequest,
    auth_svc: AuthService = Depends(auth_service)
):
    """Process OAuth callback and return tokens."""
    try:
        provider_enum = AuthProvider(provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )

    try:
        user, tokens = await auth_svc.process_oauth_callback(
            provider_enum,
            request.code
        )
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=3600
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        profile_image=current_user.profile_image,
        subscription_tier=current_user.subscription_tier.value,
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_svc: AuthService = Depends(auth_service)
):
    """Logout current user (invalidate tokens)."""
    auth_svc.logout(current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/password/change")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    auth_svc: AuthService = Depends(auth_service)
):
    """Change current user's password."""
    try:
        auth_svc.change_password(
            current_user.id,
            request.current_password,
            request.new_password
        )
        return {"message": "Password changed successfully"}
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/password/reset")
async def request_password_reset(
    request: PasswordResetRequest,
    auth_svc: AuthService = Depends(auth_service)
):
    """Request password reset email."""
    try:
        auth_svc.request_password_reset(request.email)
        return {"message": "Password reset email sent if account exists"}
    except Exception:
        # Don't reveal if email exists
        return {"message": "Password reset email sent if account exists"}
