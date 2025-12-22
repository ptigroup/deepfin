"""
📁 File: app/core/config.py
📝 Purpose: Centralized application configuration using Pydantic Settings

🎯 What This File Does:
This module manages ALL application settings (database URLs, API keys, feature
flags, etc.) using Pydantic Settings. It automatically reads from your .env file
and validates that all required settings are present and correctly typed.

💡 Key Concepts You'll Learn:

1. **Environment Variables** - Configuration stored outside code
   - Why? So you can change settings without modifying code
   - Example: Different DATABASE_URL for development vs production
   - Security: API keys never committed to git!

2. **Pydantic BaseSettings** - Type-safe config with validation
   - Automatically reads from .env file
   - Validates types (ensures DATABASE_URL is a string, not a number)
   - Provides defaults for optional settings
   - Raises errors if required settings are missing

3. **Singleton Pattern** - Only one settings instance exists
   - We use @lru_cache decorator to cache the Settings object
   - First call creates it, subsequent calls return the same instance
   - Why? Prevents re-reading .env file on every import
   - Memory efficient and fast

4. **Type Safety** - Settings have proper type hints
   - IDE autocomplete works perfectly
   - Catches typos at development time
   - MyPy/Pyright can verify correct usage

🔗 Related Files:
- .env - Contains actual values (never commit to git!)
- .env.example - Template for other developers (safe to commit)
- app/main.py - FastAPI app that uses these settings
- pyproject.toml - Defines pydantic-settings dependency

📚 Learn More:
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Twelve-Factor App Config: https://12factor.net/config
- Python Type Hints: https://docs.python.org/3/library/typing.html
- Singleton Pattern: https://refactoring.guru/design-patterns/singleton

🏗️ How This Works:

Step 1: Define Settings class with all configuration
Step 2: Use get_settings() function to access configuration
Step 3: Settings are loaded from .env automatically
Step 4: Validation ensures everything is correct

Example:
    >>> from app.core.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.app_name)
    "LLM Financial Pipeline"
    >>> print(settings.database_url)
    "postgresql+asyncpg://postgres:postgres@localhost:5433/llm_pipeline"
"""

from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class automatically reads from the .env file and validates that all
    required settings are present and correctly typed. It uses Pydantic's
    BaseSettings which provides:

    - Automatic environment variable loading
    - Type validation
    - Default values
    - Custom validators
    - Helpful error messages

    Attributes (grouped by category):

    Application Settings:
        app_name: Display name for the application
        environment: Current environment (development, staging, production)
        debug: Enable debug mode (more verbose logging, error details)
        api_prefix: URL prefix for all API routes (e.g., "/api")
        log_level: Minimum log level to output (DEBUG, INFO, WARNING, ERROR)

    Database Settings:
        database_url: PostgreSQL connection string (required, no default)
        database_pool_size: Number of database connections to maintain
        database_max_overflow: Additional connections to create when needed

    Security Settings:
        secret_key: Secret for JWT token signing (MUST be random and secret!)
        algorithm: Algorithm for JWT encoding (HS256 is standard)
        access_token_expire_minutes: How long JWT tokens remain valid

    LLMWhisperer Settings:
        llmwhisperer_api_key: API key for LLMWhisperer service (required)
        llmwhisperer_base_url: Base URL for LLMWhisperer API
        llmwhisperer_timeout: Request timeout in seconds

    Email Settings:
        email_enabled: Whether to send emails (False for development)
        email_from: Sender email address
        smtp_host: Email server hostname
        smtp_port: Email server port
        smtp_user: Email authentication username
        smtp_password: Email authentication password

    File Upload Settings:
        max_upload_size_mb: Maximum allowed file upload size in MB
        allowed_file_types: Comma-separated list of allowed extensions
        upload_dir: Directory to store uploaded files

    CORS Settings:
        allowed_origins: Comma-separated list of allowed origins for CORS

    Type Safety Note:
        Every attribute has a type hint. This means:
        - Your IDE will autocomplete these fields
        - Type checkers (MyPy, Pyright) can catch mistakes
        - You get validation errors if types don't match

    Validation Note:
        Pydantic validates all values when Settings is created. If any
        required field is missing or has the wrong type, you'll get a
        clear error message telling you exactly what's wrong.

    Example:
        >>> settings = Settings()  # Reads from .env automatically
        >>> print(settings.app_name)
        "LLM Financial Pipeline"
        >>> print(settings.debug)
        True  # In development
    """

    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================

    app_name: str = Field(
        default="LLM Financial Pipeline",
        description="Application display name",
    )
    """Application name shown in logs, API docs, and responses."""

    environment: str = Field(
        default="development",
        description="Current environment: development, staging, or production",
    )
    """
    Environment determines behavior:
    - development: Debug on, verbose logs, detailed errors
    - staging: Testing with production-like settings
    - production: Optimized for performance, minimal logs
    """

    debug: bool = Field(
        default=True,
        description="Enable debug mode with verbose logging",
    )
    """
    Debug mode enables:
    - Detailed error messages (stack traces visible to clients)
    - Verbose logging (more log output)
    - Auto-reload on code changes (uvicorn --reload)
    WARNING: Always set to False in production for security!
    """

    api_prefix: str = Field(
        default="/api",
        description="URL prefix for all API routes",
    )
    """
    API prefix groups all API endpoints under one path:
    - /api/health
    - /api/detection/analyze
    - /api/statements/upload
    This separates API from other routes (docs, admin, etc.)
    """

    log_level: str = Field(
        default="INFO",
        description="Minimum log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    """
    Log level controls verbosity:
    - DEBUG: Everything (use during development)
    - INFO: General informational messages (default)
    - WARNING: Warning messages only
    - ERROR: Error messages only
    - CRITICAL: Critical errors only
    """

    # ============================================================================
    # DATABASE SETTINGS
    # ============================================================================

    database_url: PostgresDsn = Field(
        description="PostgreSQL connection URL",
    )
    """
    Database connection string in format:
    postgresql+asyncpg://user:password@host:port/database

    Example from .env:
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/llm_pipeline

    Parts explained:
    - postgresql+asyncpg: PostgreSQL with async driver
    - postgres:postgres: username:password
    - localhost:5433: host:port
    - llm_pipeline: database name

    REQUIRED: This field has no default, must be in .env file!
    """

    database_pool_size: int = Field(
        default=5,
        description="Number of database connections to maintain in pool",
    )
    """
    Connection pool size controls how many concurrent database operations
    can happen. Higher = more concurrent queries, but uses more memory.
    Default of 5 is good for small applications.
    """

    database_max_overflow: int = Field(
        default=10,
        description="Additional connections to create when pool is exhausted",
    )
    """
    When all pool connections are in use, SQLAlchemy can create up to this
    many additional temporary connections. They're closed when no longer needed.
    Total possible connections = pool_size + max_overflow = 15
    """

    database_echo: bool = Field(
        default=False,
        description="Log all SQL statements (useful for debugging)",
    )
    """
    When True, SQLAlchemy logs all SQL statements to stdout.
    Useful for development and debugging, but should be False in production
    for performance and to avoid logging sensitive data.

    Example log output when True:
    INFO sqlalchemy.engine.Engine SELECT users.id, users.email FROM users
    INFO sqlalchemy.engine.Engine [cached since 0.001s ago] {}
    """

    # ============================================================================
    # SECURITY SETTINGS
    # ============================================================================

    secret_key: str = Field(
        description="Secret key for JWT token signing (MUST be random!)",
    )
    """
    Secret key used to sign JWT tokens for authentication.

    CRITICAL SECURITY REQUIREMENTS:
    1. MUST be random (use secrets.token_urlsafe(32))
    2. MUST be kept secret (never commit to git!)
    3. MUST be at least 32 characters long
    4. MUST be different in each environment

    Generate a secure secret key:
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"

    Then add to .env:
    SECRET_KEY=your_generated_random_string_here

    If someone gets your secret key, they can create fake authentication
    tokens and impersonate users!

    REQUIRED: This field has no default, must be in .env file!
    """

    algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT encoding",
    )
    """
    JWT signing algorithm. HS256 (HMAC with SHA-256) is the standard for
    symmetric key signing. Don't change this unless you know what you're doing.
    """

    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration time in minutes",
    )
    """
    How long a JWT token remains valid after creation.
    - Shorter = more secure (tokens expire quickly)
    - Longer = better UX (users don't have to re-login often)
    30 minutes is a good balance.
    """

    # ============================================================================
    # LLMWHISPERER SETTINGS
    # ============================================================================

    llmwhisperer_api_key: str = Field(
        description="API key for LLMWhisperer PDF extraction service",
    )
    """
    Your LLMWhisperer API key for PDF text extraction.

    Get your API key from: https://unstract.com/llmwhisperer/
    Then add to .env:
    LLMWHISPERER_API_KEY=your_actual_api_key_here

    REQUIRED: This field has no default, must be in .env file!
    """

    llmwhisperer_base_url: str = Field(
        default="https://api.llmwhisperer.com",
        description="Base URL for LLMWhisperer API",
    )
    """Base URL for LLMWhisperer API. Usually don't need to change this."""

    llmwhisperer_timeout: int = Field(
        default=300,
        description="Request timeout for LLMWhisperer API in seconds",
    )
    """
    How long to wait for LLMWhisperer API responses before timing out.
    300 seconds (5 minutes) allows for processing large PDFs.
    """

    # ============================================================================
    # EMAIL SETTINGS
    # ============================================================================

    email_enabled: bool = Field(
        default=False,
        description="Enable email notifications",
    )
    """
    Whether to send email notifications.
    Set to False during development (no email server needed).
    Set to True in production (requires SMTP configuration).
    """

    email_from: str = Field(
        default="noreply@llmpipeline.com",
        description="Sender email address",
    )
    """Email address that notifications are sent from."""

    smtp_host: str | None = Field(
        default=None,
        description="SMTP server hostname",
    )
    """SMTP server for sending emails (e.g., smtp.gmail.com)."""

    smtp_port: int = Field(
        default=587,
        description="SMTP server port (587 for TLS)",
    )
    """SMTP server port. 587 is standard for TLS."""

    smtp_user: str | None = Field(
        default=None,
        description="SMTP authentication username",
    )
    """Username for SMTP authentication."""

    smtp_password: str | None = Field(
        default=None,
        description="SMTP authentication password",
    )
    """Password for SMTP authentication. Keep this secret!"""

    @property
    def unstract_api_key(self) -> str:
        """Alias for llmwhisperer_api_key for compatibility."""
        return self.llmwhisperer_api_key

    # ============================================================================
    # CACHE SETTINGS
    # ============================================================================

    cache_dir: str = Field(
        default=".cache",
        description="Directory to store cache files",
    )
    """
    Directory where cache files are stored (e.g., LLMWhisperer API responses).
    Created automatically if it doesn't exist.
    Relative to project root.

    Caching expensive API calls saves time and money on reprocessing.
    """

    # ============================================================================
    # FILE UPLOAD SETTINGS
    # ============================================================================

    max_upload_size_mb: int = Field(
        default=50,
        description="Maximum file upload size in megabytes",
    )
    """
    Maximum allowed file upload size in MB.
    50MB is enough for most PDF files.
    Larger files are rejected with an error.
    """

    allowed_file_types: str = Field(
        default=".pdf",
        description="Comma-separated list of allowed file extensions",
    )
    """
    Allowed file extensions for uploads.
    Default is PDF only. To allow multiple types:
    ALLOWED_FILE_TYPES=.pdf,.xlsx,.csv
    """

    upload_dir: str = Field(
        default="uploads",
        description="Directory to store uploaded files",
    )
    """
    Directory where uploaded files are stored.
    Created automatically if it doesn't exist.
    Relative to project root.
    """

    # ============================================================================
    # CORS SETTINGS
    # ============================================================================

    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8123",
        description="Comma-separated list of allowed CORS origins",
    )
    """
    CORS (Cross-Origin Resource Sharing) settings.
    Allows frontend apps from these URLs to call your API.

    Example:
    ALLOWED_ORIGINS=http://localhost:3000,https://myapp.com

    Default allows:
    - http://localhost:3000 (React/Vue dev server)
    - http://localhost:8123 (API docs)

    In production, set this to your actual frontend URL!
    """

    # ============================================================================
    # PYDANTIC CONFIGURATION
    # ============================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    """
    Pydantic Settings configuration:

    - env_file=".env": Read from .env file
    - env_file_encoding="utf-8": Handle international characters
    - case_sensitive=False: Allow DATABASE_URL or database_url
    - extra="ignore": Ignore unknown variables in .env
    """

    # ============================================================================
    # CUSTOM VALIDATORS
    # ============================================================================

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate that log_level is a valid Python logging level.

        This validator runs automatically when Settings is created.
        It ensures LOG_LEVEL in .env is one of the allowed values.

        Args:
            v: The log level value from .env

        Returns:
            str: Uppercase log level (e.g., "INFO")

        Raises:
            ValueError: If log level is not valid

        Example:
            .env has: LOG_LEVEL=info
            This validates it and returns "INFO"

            .env has: LOG_LEVEL=invalid
            This raises: ValueError with helpful message
        """
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()

        if v_upper not in allowed_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of: {', '.join(allowed_levels)}")

        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate that environment is a known environment type.

        Args:
            v: The environment value from .env

        Returns:
            str: Lowercase environment name

        Raises:
            ValueError: If environment is not valid
        """
        allowed_envs = {"development", "staging", "production"}
        v_lower = v.lower()

        if v_lower not in allowed_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of: {', '.join(allowed_envs)}")

        return v_lower

    # ============================================================================
    # COMPUTED PROPERTIES
    # ============================================================================

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Get allowed CORS origins as a list.

        Converts the comma-separated string into a list for FastAPI CORS middleware.

        Returns:
            list[str]: List of allowed origin URLs

        Example:
            >>> settings = Settings()
            >>> print(settings.allowed_origins)
            "http://localhost:3000,http://localhost:8123"
            >>> print(settings.allowed_origins_list)
            ["http://localhost:3000", "http://localhost:8123"]
        """
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_file_types_list(self) -> list[str]:
        """
        Get allowed file types as a list.

        Converts the comma-separated string into a list for validation.

        Returns:
            list[str]: List of allowed file extensions

        Example:
            >>> settings = Settings()
            >>> print(settings.allowed_file_types)
            ".pdf,.xlsx"
            >>> print(settings.allowed_file_types_list)
            [".pdf", ".xlsx"]
        """
        return [ext.strip() for ext in self.allowed_file_types.split(",")]


# ============================================================================
# SINGLETON FACTORY FUNCTION
# ============================================================================


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings (singleton pattern using cache).

    This function uses the @lru_cache decorator to implement the singleton
    pattern. The first time it's called, it creates a Settings object by
    reading the .env file. Subsequent calls return the same cached instance.

    Why use a singleton?
    - Performance: Only read .env file once, not on every import
    - Consistency: Everyone gets the same settings object
    - Memory: Only one Settings object in memory

    How @lru_cache works:
    1. First call: Execute function body, cache result
    2. Subsequent calls: Return cached result without executing
    3. Cache key: Function arguments (none in this case)

    Returns:
        Settings: Application settings loaded from .env

    Raises:
        ValidationError: If .env is missing required variables or has invalid values

    Example:
        >>> from app.core.config import get_settings
        >>> settings = get_settings()  # First call: reads .env
        >>> print(settings.app_name)
        "LLM Financial Pipeline"
        >>> settings2 = get_settings()  # Second call: returns cached object
        >>> assert settings is settings2  # Same object!

    Usage in FastAPI:
        FastAPI has built-in dependency injection that works with this:

        >>> from fastapi import Depends
        >>> from app.core.config import get_settings, Settings
        >>>
        >>> @app.get("/info")
        >>> async def get_info(settings: Settings = Depends(get_settings)):
        >>>     return {"app_name": settings.app_name}

    Clearing the cache (for tests):
        >>> get_settings.cache_clear()  # Clears cached settings
        >>> settings = get_settings()  # Will read .env again
    """
    return Settings()


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ["Settings", "get_settings"]

"""
📚 What You Learned:

1. **Pydantic Settings** - Type-safe configuration management
   - Automatically reads from .env file
   - Validates all settings
   - Provides helpful error messages

2. **Environment Variables** - Configuration outside code
   - Different settings per environment (dev/staging/prod)
   - Security: API keys never in code
   - Flexibility: Change settings without code changes

3. **Singleton Pattern** - One shared instance
   - @lru_cache decorator creates singleton
   - Efficient: Read .env file only once
   - Consistent: Everyone gets same settings

4. **Type Safety** - Type hints everywhere
   - IDE autocomplete works
   - Type checkers catch errors
   - Self-documenting code

5. **Validators** - Custom validation logic
   - @field_validator decorator
   - Runs automatically on Settings creation
   - Ensures data integrity

🎯 Next Steps:

1. Read this file carefully (3-pass method from START_HERE.md)
2. Look at your .env file - see how values match field names?
3. Try using settings in Python REPL:
   >>> from app.core.config import get_settings
   >>> settings = get_settings()
   >>> print(settings.database_url)

4. Next file: app/core/logging.py (structured logging!)

💡 Key Takeaway:
Configuration management might seem simple, but doing it RIGHT (type-safe,
validated, environment-based) is what separates hobby projects from
production-ready applications. You're learning professional practices!
"""
