"""Tests for auth service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserCreate
from app.auth.service import AuthService, AuthServiceError


class TestPasswordOperations:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing produces different hashes for same password."""
        password = "SecurePass123"

        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Hashes should be different (bcrypt uses salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)

    def test_verify_password_success(self):
        """Test password verification with correct password."""
        password = "MySecret456"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification with incorrect password."""
        password = "MySecret456"
        wrong_password = "WrongPassword"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False


class TestJWTOperations:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = 1
        email = "test@example.com"

        token = AuthService.create_access_token(user_id, email)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert token.count(".") == 2

    def test_decode_access_token_success(self):
        """Test JWT token decoding with valid token."""
        user_id = 123
        email = "user@example.com"

        token = AuthService.create_access_token(user_id, email)
        token_data = AuthService.decode_access_token(token)

        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.exp is not None

    def test_decode_access_token_invalid(self):
        """Test JWT token decoding with invalid token."""
        with pytest.raises(AuthServiceError, match="Could not validate credentials"):
            AuthService.decode_access_token("invalid.token.here")

    def test_decode_access_token_malformed(self):
        """Test JWT token decoding with malformed token."""
        with pytest.raises(AuthServiceError):
            AuthService.decode_access_token("not-a-jwt-token")


@pytest.mark.asyncio
class TestUserCRUD:
    """Test user CRUD operations."""

    async def test_create_user(self, mock_db: AsyncSession):
        """Test user creation with valid data."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="newuser@example.com",
            password="SecurePass123",
            username="newuser",
            is_active=True,
            is_superuser=False,
        )

        user = await service.create_user(user_data)

        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.is_active is True
        assert user.is_superuser is False
        # Password should be hashed, not plain text
        assert user.hashed_password != "SecurePass123"
        assert len(user.hashed_password) > 50  # Bcrypt hashes are long

    async def test_create_user_duplicate_email(self, mock_db: AsyncSession):
        """Test user creation with duplicate email fails."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="duplicate@example.com",
            password="SecurePass123",
            is_active=True,
            is_superuser=False,
        )

        # Create first user
        await service.create_user(user_data)

        # Try to create another user with same email
        with pytest.raises(AuthServiceError, match="already exists"):
            await service.create_user(user_data)

    async def test_create_user_duplicate_username(self, mock_db: AsyncSession):
        """Test user creation with duplicate username fails."""
        service = AuthService(mock_db)

        user_data1 = UserCreate(
            email="user1@example.com",
            password="SecurePass123",
            username="johndoe",
            is_active=True,
            is_superuser=False,
        )

        user_data2 = UserCreate(
            email="user2@example.com",
            password="SecurePass123",
            username="johndoe",  # Same username
            is_active=True,
            is_superuser=False,
        )

        await service.create_user(user_data1)

        with pytest.raises(AuthServiceError, match="already taken"):
            await service.create_user(user_data2)

    async def test_get_user_by_id(self, mock_db: AsyncSession):
        """Test getting user by ID."""
        service = AuthService(mock_db)

        # Create user first
        user_data = UserCreate(
            email="findme@example.com",
            password="SecurePass123",
            is_active=True,
            is_superuser=False,
        )
        created_user = await service.create_user(user_data)

        # Find by ID
        found_user = await service.get_user_by_id(created_user.id)

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"

    async def test_get_user_by_id_not_found(self, mock_db: AsyncSession):
        """Test getting non-existent user by ID returns None."""
        service = AuthService(mock_db)

        user = await service.get_user_by_id(99999)

        assert user is None

    async def test_get_user_by_email(self, mock_db: AsyncSession):
        """Test getting user by email."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="findbyemail@example.com",
            password="SecurePass123",
            is_active=True,
            is_superuser=False,
        )
        await service.create_user(user_data)

        found_user = await service.get_user_by_email("findbyemail@example.com")

        assert found_user is not None
        assert found_user.email == "findbyemail@example.com"

    async def test_get_user_by_username(self, mock_db: AsyncSession):
        """Test getting user by username."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="withusername@example.com",
            password="SecurePass123",
            username="johndoe",
            is_active=True,
            is_superuser=False,
        )
        await service.create_user(user_data)

        found_user = await service.get_user_by_username("johndoe")

        assert found_user is not None
        assert found_user.username == "johndoe"


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication operations."""

    async def test_authenticate_user_success(self, mock_db: AsyncSession):
        """Test successful user authentication."""
        service = AuthService(mock_db)

        # Create user
        password = "MyPassword123"
        user_data = UserCreate(
            email="auth@example.com",
            password=password,
            is_active=True,
            is_superuser=False,
        )
        await service.create_user(user_data)

        # Authenticate
        user = await service.authenticate_user("auth@example.com", password)

        assert user is not None
        assert user.email == "auth@example.com"

    async def test_authenticate_user_wrong_password(self, mock_db: AsyncSession):
        """Test authentication with wrong password."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="wrongpass@example.com",
            password="CorrectPassword123",
            is_active=True,
            is_superuser=False,
        )
        await service.create_user(user_data)

        user = await service.authenticate_user("wrongpass@example.com", "WrongPassword")

        assert user is None

    async def test_authenticate_user_nonexistent(self, mock_db: AsyncSession):
        """Test authentication with non-existent user."""
        service = AuthService(mock_db)

        user = await service.authenticate_user("nonexistent@example.com", "password")

        assert user is None

    async def test_authenticate_user_inactive(self, mock_db: AsyncSession):
        """Test authentication with inactive user."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="inactive@example.com",
            password="Password123",
            is_active=False,  # Inactive
            is_superuser=False,
        )
        await service.create_user(user_data)

        user = await service.authenticate_user("inactive@example.com", "Password123")

        assert user is None

    async def test_login_success(self, mock_db: AsyncSession):
        """Test successful login returns token."""
        service = AuthService(mock_db)

        password = "LoginTest123"
        user_data = UserCreate(
            email="login@example.com",
            password=password,
            is_active=True,
            is_superuser=False,
        )
        await service.create_user(user_data)

        access_token, expires_in = await service.login("login@example.com", password)

        assert isinstance(access_token, str)
        assert len(access_token) > 0
        assert expires_in > 0
        # Should be able to decode the token
        token_data = AuthService.decode_access_token(access_token)
        assert token_data.email == "login@example.com"

    async def test_login_wrong_credentials(self, mock_db: AsyncSession):
        """Test login with wrong credentials raises error."""
        service = AuthService(mock_db)

        user_data = UserCreate(
            email="faillogin@example.com",
            password="CorrectPassword123",
            is_active=True,
            is_superuser=False,
        )
        await service.create_user(user_data)

        with pytest.raises(AuthServiceError, match="Incorrect email or password"):
            await service.login("faillogin@example.com", "WrongPassword")
