"""
Integration Tests for API Endpoints.

Tests API endpoints with real HTTP requests.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# =============================================================================
# API Test Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def test_app():
    """Create test FastAPI app."""
    from fastapi.testclient import TestClient
    from main import create_application

    app = create_application()
    return app


@pytest.fixture(scope="module")
def client(test_app):
    """Create test client."""
    from fastapi.testclient import TestClient

    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def registered_user(client):
    """Register a user and return credentials."""
    import secrets
    email = f"test_{secrets.token_hex(4)}@test.com"

    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "name": "Test User"
    })

    if response.status_code == 201:
        return {"email": email, "password": "TestPass123!"}

    # User might already exist, return default
    return {"email": email, "password": "TestPass123!"}


@pytest.fixture
def auth_token(client, registered_user):
    """Get authentication token."""
    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })

    if response.status_code == 200:
        return response.json()["access_token"]

    return None


@pytest.fixture
def auth_headers(auth_token):
    """Create auth headers."""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


# =============================================================================
# Health & Root Tests
# =============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.integration
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.integration
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "FlyReady Lab API"


# =============================================================================
# Authentication API Tests
# =============================================================================

class TestAuthAPI:
    """Tests for authentication endpoints."""

    @pytest.mark.integration
    @pytest.mark.auth
    def test_register_new_user(self, client):
        """Test user registration via API."""
        import secrets
        email = f"newuser_{secrets.token_hex(4)}@test.com"

        response = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "SecurePass123!",
            "name": "New User"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["name"] == "New User"
        assert "id" in data

    @pytest.mark.integration
    @pytest.mark.auth
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "SecurePass123!",
            "name": "Test"
        })

        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    @pytest.mark.auth
    def test_login_success(self, client, registered_user):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.integration
    @pytest.mark.auth
    def test_login_wrong_password(self, client, registered_user):
        """Test login with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.auth
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data

    @pytest.mark.integration
    @pytest.mark.auth
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoint without auth."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401


# =============================================================================
# User API Tests
# =============================================================================

class TestUserAPI:
    """Tests for user endpoints."""

    @pytest.mark.integration
    def test_get_user_profile(self, client, auth_headers):
        """Test getting user profile."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "subscription_tier" in data

    @pytest.mark.integration
    def test_update_user_profile(self, client, auth_headers):
        """Test updating user profile."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.integration
    def test_get_usage_stats(self, client, auth_headers):
        """Test getting usage statistics."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.get("/api/v1/users/me/usage", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "interview_sessions_today" in data
        assert "interview_limit_daily" in data


# =============================================================================
# Payment API Tests
# =============================================================================

class TestPaymentAPI:
    """Tests for payment endpoints."""

    @pytest.mark.integration
    @pytest.mark.payment
    def test_list_products(self, client):
        """Test listing available products."""
        response = client.get("/api/v1/payments/products")

        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0

        # Check product structure
        product = products[0]
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "features" in product

    @pytest.mark.integration
    @pytest.mark.payment
    def test_get_product_detail(self, client):
        """Test getting product details."""
        response = client.get("/api/v1/payments/products/standard_monthly")

        assert response.status_code == 200
        product = response.json()
        assert product["id"] == "standard_monthly"
        assert product["tier"] == "standard"

    @pytest.mark.integration
    @pytest.mark.payment
    def test_initiate_payment(self, client, auth_headers):
        """Test payment initiation."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.post(
            "/api/v1/payments/initiate",
            headers=auth_headers,
            json={
                "product_id": "standard_monthly",
                "payment_method": "kakaopay"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "payment_id" in data
        assert "order_id" in data
        assert "redirect_url" in data


# =============================================================================
# Mentor API Tests
# =============================================================================

class TestMentorAPI:
    """Tests for mentor endpoints."""

    @pytest.mark.integration
    @pytest.mark.mentor
    def test_search_mentors(self, client):
        """Test searching mentors."""
        response = client.get("/api/v1/mentors/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.integration
    @pytest.mark.mentor
    def test_search_mentors_with_filters(self, client):
        """Test searching mentors with filters."""
        response = client.get(
            "/api/v1/mentors/",
            params={
                "mentor_type": "current_crew",
                "airline": "KE",
                "max_rate": 100000
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


# =============================================================================
# Job API Tests
# =============================================================================

class TestJobAPI:
    """Tests for job posting endpoints."""

    @pytest.mark.integration
    def test_list_jobs(self, client):
        """Test listing job postings."""
        response = client.get("/api/v1/jobs/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.integration
    def test_get_open_jobs(self, client):
        """Test getting open job postings."""
        response = client.get("/api/v1/jobs/open")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_airline_summary(self, client):
        """Test getting airline summary."""
        response = client.get("/api/v1/jobs/airlines")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# =============================================================================
# Recommendation API Tests
# =============================================================================

class TestRecommendationAPI:
    """Tests for recommendation endpoints."""

    @pytest.mark.integration
    def test_get_skill_profile(self, client, auth_headers):
        """Test getting skill profile."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.get(
            "/api/v1/recommendations/profile",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "readiness_score" in data
        assert "skills" in data

    @pytest.mark.integration
    def test_get_recommendations(self, client, auth_headers):
        """Test getting recommendations."""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = client.get(
            "/api/v1/recommendations/",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_search_content(self, client):
        """Test searching learning content."""
        response = client.get("/api/v1/recommendations/content")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.integration
    def test_not_found_error(self, client):
        """Test 404 error response format."""
        response = client.get("/api/v1/nonexistent/endpoint")

        assert response.status_code == 404

    @pytest.mark.integration
    def test_validation_error_format(self, client):
        """Test validation error response format."""
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "x",  # Too short
            "name": ""  # Empty
        })

        assert response.status_code == 422
        data = response.json()
        # Should have structured error response
        assert "detail" in data or "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
