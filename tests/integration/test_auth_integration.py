"""Integration tests for authentication flow.

Tests the complete authentication workflow:
- User registration
- Login with credentials
- Token generation and validation
- Access to protected endpoints
- Token expiration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    def test_user_registration_and_login(self, client: TestClient) -> None:
        """Test user can register and then login."""
        # Register new user
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "username": "newuser",
            },
        )
        
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "newuser@example.com"
        assert user_data["username"] == "newuser"
        assert "id" in user_data
        assert "password" not in user_data  # Password should not be returned
        
        # Login with new credentials
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": "newuser@example.com",
                "password": "SecurePassword123!",
            },
        )
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_login_with_invalid_credentials(self, client: TestClient, test_user: dict) -> None:
        """Test login fails with wrong password."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["email"],
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_protected_endpoint_requires_auth(self, client: TestClient) -> None:
        """Test protected endpoints reject requests without token."""
        # Try to access protected endpoint without token
        response = client.get("/api/jobs/")
        
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(
        self, 
        client: TestClient,
        auth_headers: dict[str, str]
    ) -> None:
        """Test protected endpoints work with valid token."""
        response = client.get("/api/jobs/", headers=auth_headers)
        
        assert response.status_code == 200

    def test_protected_endpoint_with_invalid_token(self, client: TestClient) -> None:
        """Test protected endpoints reject invalid tokens."""
        response = client.get(
            "/api/jobs/",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401

    def test_duplicate_email_registration(self, client: TestClient, test_user: dict) -> None:
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user["email"],  # Already exists
                "password": "AnotherPassword123!",
                "username": "anotheruser",
            },
        )
        
        assert response.status_code == 400

    def test_get_current_user(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_user: dict
    ) -> None:
        """Test getting current user info with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == test_user["email"]
        assert user_data["username"] == test_user["username"]
        assert "password" not in user_data


@pytest.mark.integration
class TestPasswordValidation:
    """Test password validation rules."""

    def test_weak_password_rejected(self, client: TestClient) -> None:
        """Test registration fails with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "username": "testuser",
            },
        )
        
        assert response.status_code == 400

    def test_password_without_number_rejected(self, client: TestClient) -> None:
        """Test password must contain numbers."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoNumbersHere!",
                "username": "testuser",
            },
        )
        
        assert response.status_code == 400


@pytest.mark.integration
class TestUserManagement:
    """Test user management operations."""

    @pytest.mark.asyncio
    async def test_user_creation_in_database(self, db_session: AsyncSession) -> None:
        """Test user is actually created in database."""
        from app.auth.models import User
        from app.auth.service import AuthService
        
        auth_service = AuthService(db_session)
        
        # Create user
        user = await auth_service.create_user(
            email="dbtest@example.com",
            password="Password123!",
            username="dbtest",
        )
        
        # Verify user exists in database
        assert user.id is not None
        assert user.email == "dbtest@example.com"
        assert user.username == "dbtest"
        assert user.hashed_password != "Password123!"  # Should be hashed
        
        # Retrieve user by email
        retrieved = await auth_service.get_user_by_email("dbtest@example.com")
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == user.email

    @pytest.mark.asyncio
    async def test_password_hashing(self, db_session: AsyncSession) -> None:
        """Test passwords are properly hashed."""
        from app.auth.service import AuthService
        
        auth_service = AuthService(db_session)
        
        password = "TestPassword123!"
        user = await auth_service.create_user(
            email="hashtest@example.com",
            password=password,
            username="hashtest",
        )
        
        # Password should be hashed
        assert user.hashed_password != password
        
        # Verify password works
        is_valid = auth_service.verify_password(password, user.hashed_password)
        assert is_valid is True
        
        # Wrong password should fail
        is_valid = auth_service.verify_password("WrongPassword", user.hashed_password)
        assert is_valid is False
