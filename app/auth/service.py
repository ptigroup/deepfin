"""Authentication service for user management and JWT tokens."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import TokenData, UserCreate
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


class AuthServiceError(Exception):
    """Authentication service errors."""

    pass


class AuthService:
    """Service for user authentication and management.

    Handles:
    - Password hashing and verification
    - JWT token creation and validation
    - User registration and login
    - User CRUD operations
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize auth service.

        Args:
            db_session: Database session
        """
        self.db = db_session

    # =========================================================================
    # PASSWORD OPERATIONS
    # =========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt-hashed password

        Example:
            >>> hashed = AuthService.hash_password("secret123")
            >>> print(hashed)
            $2b$12$...  # Bcrypt hash
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hash to compare against

        Returns:
            True if password matches hash, False otherwise

        Example:
            >>> hashed = AuthService.hash_password("secret123")
            >>> AuthService.verify_password("secret123", hashed)
            True
            >>> AuthService.verify_password("wrong", hashed)
            False
        """
        return pwd_context.verify(plain_password, hashed_password)

    # =========================================================================
    # JWT TOKEN OPERATIONS
    # =========================================================================

    @staticmethod
    def create_access_token(user_id: int, email: str) -> str:
        """Create a JWT access token.

        Args:
            user_id: User ID to encode in token
            email: User email to encode in token

        Returns:
            JWT token string

        Example:
            >>> token = AuthService.create_access_token(user_id=1, email="user@example.com")
            >>> print(token)
            eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        """
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        expire = datetime.now(UTC) + expires_delta

        to_encode = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,
            "exp": expire,  # Expiration time
            "iat": datetime.now(UTC),  # Issued at
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )

        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> TokenData:
        """Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData with user_id and email

        Raises:
            AuthServiceError: If token is invalid or expired

        Example:
            >>> token = AuthService.create_access_token(1, "user@example.com")
            >>> data = AuthService.decode_access_token(token)
            >>> print(data.user_id)
            1
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )

            user_id = int(payload.get("sub"))
            email = payload.get("email")

            if user_id is None or email is None:
                raise AuthServiceError("Invalid token payload")

            return TokenData(
                user_id=user_id,
                email=email,
                exp=datetime.fromtimestamp(payload.get("exp"), tz=UTC),
            )

        except JWTError as e:
            logger.error("JWT decode error", extra={"error": str(e)}, exc_info=True)
            raise AuthServiceError("Could not validate credentials") from e

    # =========================================================================
    # USER CRUD OPERATIONS
    # =========================================================================

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            AuthServiceError: If user creation fails
        """
        try:
            # Check if email already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise AuthServiceError(f"User with email {user_data.email} already exists")

            # Check if username already exists (if provided)
            if user_data.username:
                existing_username = await self.get_user_by_username(user_data.username)
                if existing_username:
                    raise AuthServiceError(f"Username {user_data.username} already taken")

            # Hash password
            hashed_password = self.hash_password(user_data.password)

            # Create user
            user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                is_active=user_data.is_active,
                is_superuser=user_data.is_superuser,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(
                "User created successfully",
                extra={"user_id": user.id, "email": user.email},
            )

            return user

        except AuthServiceError:
            await self.db.rollback()
            raise

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to create user",
                extra={"email": user_data.email, "error": str(e)},
                exc_info=True,
            )
            raise AuthServiceError(f"Failed to create user: {str(e)}") from e

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None if not found
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User or None if not found
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User or None if not found
        """
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # =========================================================================
    # AUTHENTICATION OPERATIONS
    # =========================================================================

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise

        Example:
            >>> user = await auth_service.authenticate_user(
            ...     email="user@example.com",
            ...     password="secret123"
            ... )
            >>> if user:
            ...     print("Login successful!")
        """
        user = await self.get_user_by_email(email)
        if not user:
            logger.warning("Login attempt for non-existent user", extra={"email": email})
            return None

        if not user.is_active:
            logger.warning("Login attempt for inactive user", extra={"email": email})
            return None

        if not self.verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt (wrong password)", extra={"email": email})
            return None

        logger.info("User authenticated successfully", extra={"user_id": user.id, "email": email})
        return user

    async def login(self, email: str, password: str) -> tuple[str, int]:
        """Login user and create access token.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (access_token, expires_in_seconds)

        Raises:
            AuthServiceError: If authentication fails

        Example:
            >>> token, expires_in = await auth_service.login(
            ...     email="user@example.com",
            ...     password="secret123"
            ... )
            >>> print(f"Token: {token}")
            >>> print(f"Expires in: {expires_in} seconds")
        """
        user = await self.authenticate_user(email, password)
        if not user:
            raise AuthServiceError("Incorrect email or password")

        access_token = self.create_access_token(user_id=user.id, email=user.email)
        expires_in = settings.access_token_expire_minutes * 60

        return access_token, expires_in
