"""
📁 File: app/core/tests/test_config.py
📝 Purpose: Tests for the configuration module

🎯 What This File Does:
This file contains tests for the Settings class and get_settings() function.
Tests verify that configuration loads correctly from .env, validates properly,
and behaves as expected.

💡 Key Testing Concepts:

1. **Unit Tests** - Test individual components in isolation
   - Each test function tests one specific behavior
   - Tests are independent (don't affect each other)
   - Fast to run (no external dependencies)

2. **Test Fixtures** - Reusable test setup code
   - @pytest.fixture decorator creates setup functions
   - Fixtures can clean up resources automatically
   - Fixtures can be shared across tests

3. **Monkeypatching** - Temporarily replace environment variables
   - monkeypatch.setenv() sets env vars for test only
   - Automatically cleaned up after test
   - Prevents tests from affecting each other

4. **Assertions** - Verify expected behavior
   - assert condition, "error message"
   - pytest provides better error messages than plain assert
   - Tests fail if any assertion fails

📚 Learn More:
- pytest: https://docs.pytest.org/
- pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
- Monkeypatching: https://docs.pytest.org/en/stable/monkeypatch.html
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestSettings:
    """
    Test suite for the Settings class.

    This class groups related tests together. Each test method (starting
    with 'test_') tests a specific aspect of the Settings class.

    Why group tests in classes?
    - Organization: Related tests stay together
    - Shared fixtures: Can create class-level fixtures
    - Clearer test reports: Tests grouped by class name
    """

    def test_settings_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that Settings correctly loads values from environment variables.

        This test verifies the core functionality: reading .env file and
        creating a Settings object with the correct values.

        Args:
            monkeypatch: pytest fixture for modifying environment

        What this test does:
        1. Set environment variables for all required settings
        2. Create a Settings instance
        3. Verify each setting has the expected value

        Why this test is important:
            If this fails, the basic configuration system is broken!
        """
        # Arrange: Set up test environment variables
        # These override anything in your .env file for this test only
        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Act: Create Settings instance
        # This reads from environment variables we just set
        settings = Settings()

        # Assert: Verify values are correctly loaded
        assert settings.app_name == "Test App"
        assert settings.environment == "development"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert "test_db" in str(settings.database_url)
        assert settings.secret_key == "test-secret-key-min-32-chars-long"
        assert settings.llmwhisperer_api_key == "test-api-key"

    def test_settings_has_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that Settings uses default values for optional fields.

        Not all settings are required. Some have sensible defaults that
        should be used if not specified in .env file.

        This test verifies default values work correctly.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set only REQUIRED settings
        # Don't set optional settings - they should use defaults
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Act: Create Settings instance
        settings = Settings()

        # Assert: Verify default values are used
        assert settings.app_name == "LLM Financial Pipeline"  # Default
        assert settings.environment == "development"  # Default
        assert settings.debug is True  # Default
        assert settings.api_prefix == "/api"  # Default
        assert settings.database_pool_size == 5  # Default
        assert settings.email_enabled is False  # Default

    def test_settings_validates_log_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that Settings validates log level is a known value.

        The @field_validator decorator on log_level ensures only valid
        logging levels are accepted. This test verifies that validation.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set required settings
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Test 1: Valid log level should work
        monkeypatch.setenv("LOG_LEVEL", "info")  # lowercase
        settings = Settings()
        assert settings.log_level == "INFO"  # Converted to uppercase

        # Test 2: Invalid log level should raise ValidationError
        monkeypatch.setenv("LOG_LEVEL", "invalid")
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # Verify error message is helpful
        error = str(exc_info.value)
        assert "Invalid log level" in error
        assert "Must be one of" in error

    def test_settings_validates_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that Settings validates environment is a known value.

        Only 'development', 'staging', or 'production' should be allowed.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set required settings
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Test 1: Valid environment should work
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = Settings()
        assert settings.environment == "production"

        # Test 2: Invalid environment should raise ValidationError
        monkeypatch.setenv("ENVIRONMENT", "invalid")
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error = str(exc_info.value)
        assert "Invalid environment" in error

    def test_settings_requires_database_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that Settings requires DATABASE_URL to be set.

        DATABASE_URL is marked as required (no default value).
        If it's missing, Pydantic should raise a ValidationError.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set all required settings EXCEPT DATABASE_URL
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Act & Assert: Creating Settings should fail
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # Verify error mentions database_url field
        error = str(exc_info.value)
        assert "database_url" in error.lower()

    def test_settings_requires_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that Settings requires SECRET_KEY to be set.

        SECRET_KEY is critical for security. It must be provided.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set all required settings EXCEPT SECRET_KEY
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Act & Assert: Creating Settings should fail
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error = str(exc_info.value)
        assert "secret_key" in error.lower()

    def test_allowed_origins_list_property(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that allowed_origins_list property correctly parses comma-separated string.

        The allowed_origins setting is stored as a comma-separated string but
        FastAPI needs a list. The property should convert it.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")
        monkeypatch.setenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,https://example.com,http://localhost:8123",
        )

        # Act
        settings = Settings()

        # Assert
        expected = [
            "http://localhost:3000",
            "https://example.com",
            "http://localhost:8123",
        ]
        assert settings.allowed_origins_list == expected

    def test_is_development_property(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test the is_development convenience property.

        This property makes it easy to check if running in development mode.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Test development
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False

        # Test production
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = Settings()
        assert settings.is_development is False
        assert settings.is_production is True


class TestGetSettings:
    """
    Test suite for the get_settings() singleton factory function.

    These tests verify that get_settings() correctly implements the
    singleton pattern using @lru_cache.
    """

    def test_get_settings_returns_settings_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that get_settings() returns a Settings instance.

        Basic smoke test to verify the function works.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set required environment variables
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Act: Call get_settings()
        settings = get_settings()

        # Assert: Should be a Settings instance
        assert isinstance(settings, Settings)

    def test_get_settings_returns_same_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that get_settings() implements singleton pattern.

        The @lru_cache decorator should ensure the same Settings instance
        is returned on multiple calls. This test verifies that behavior.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set required environment variables
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")

        # Clear any existing cache from previous tests
        get_settings.cache_clear()

        # Act: Call get_settings() twice
        settings1 = get_settings()
        settings2 = get_settings()

        # Assert: Should be the EXACT SAME object (same memory address)
        assert settings1 is settings2  # 'is' checks identity, not equality

    def test_cache_clear_creates_new_instance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that cache_clear() allows creating a new Settings instance.

        This is important for tests that need to reload settings with
        different environment variables.

        Args:
            monkeypatch: pytest fixture for modifying environment
        """
        # Arrange: Set initial environment
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost:5433/test_db",
        )
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
        monkeypatch.setenv("LLMWHISPERER_API_KEY", "test-api-key")
        monkeypatch.setenv("APP_NAME", "First App")

        # Act: Get first settings instance
        get_settings.cache_clear()
        settings1 = get_settings()
        assert settings1.app_name == "First App"

        # Change environment and clear cache
        monkeypatch.setenv("APP_NAME", "Second App")
        get_settings.cache_clear()

        # Act: Get new settings instance
        settings2 = get_settings()

        # Assert: Should be a different object with new value
        assert settings1 is not settings2
        assert settings2.app_name == "Second App"


"""
📚 What You Learned About Testing:

1. **Test Structure** - Arrange, Act, Assert (AAA) pattern
   - Arrange: Set up test data and conditions
   - Act: Execute the code being tested
   - Assert: Verify the results are correct

2. **Test Fixtures** - Reusable setup code
   - monkeypatch: Safely modify environment for tests
   - Automatic cleanup after each test
   - Prevents test pollution

3. **Test Coverage** - What to test
   - Happy path: Normal usage works
   - Error cases: Validation works
   - Edge cases: Boundary conditions
   - Singleton behavior: Cache works

4. **pytest Features** - Modern testing tools
   - Descriptive test names (test_verb_expected_behavior)
   - pytest.raises() for exception testing
   - Helpful error messages
   - Class-based test organization

5. **Why Test Configuration?** - Catch errors early
   - Missing environment variables found at startup
   - Invalid values rejected before causing problems
   - Documentation: Tests show how to use the code
   - Refactoring safety: Tests catch breaking changes

🎯 Running These Tests:

From project root:
    pytest app/core/tests/test_config.py -v

Expected output:
    test_config.py::TestSettings::test_settings_loads_from_env PASSED
    test_config.py::TestSettings::test_settings_has_defaults PASSED
    test_config.py::TestSettings::test_settings_validates_log_level PASSED
    ... (all tests should pass)

    ============ X passed in Y.YYs ============

If tests fail:
    - Read the error message carefully
    - Check that .env file has required variables
    - Verify environment variables are set correctly

💡 Key Takeaway:
Good tests are like insurance - you hope you don't need them, but when
something breaks, you're very glad they're there! These tests document
how configuration should work and catch bugs before they reach production.
"""
