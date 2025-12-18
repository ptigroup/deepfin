"""
📁 File: app/core/logging.py
📝 Purpose: Structured logging configuration using structlog

🎯 What This File Does:
This module sets up structured logging for the application using structlog.
Structured logging means log messages are in JSON format with named fields,
making them easy to search, filter, and analyze in production.

💡 Key Concepts You'll Learn:

1. **Structured Logging** - JSON logs instead of text
   - Traditional: "User john@example.com logged in from 192.168.1.1"
   - Structured: {"event": "user_login", "email": "john@example.com", "ip": "192.168.1.1"}
   - Why? Easily searchable, filterable, and analyzable

2. **Correlation IDs** - Track requests across the system
   - Each request gets a unique ID (UUID)
   - All logs for that request have the same correlation_id
   - Makes debugging SO much easier in production
   - Example: "Show me all logs for request abc-123-def"

3. **Log Levels** - Control verbosity
   - DEBUG: Everything (development only)
   - INFO: Important events (default)
   - WARNING: Warning messages
   - ERROR: Error messages
   - CRITICAL: System is broken

4. **Context Binding** - Add data to all logs
   - Bind user_id once, appears in all subsequent logs
   - Automatically reset between requests
   - Reduces code duplication

🔗 Related Files:
- app/core/config.py - Provides LOG_LEVEL setting
- app/core/middleware.py - Injects correlation_id into requests
- app/main.py - Initializes logging on startup

📚 Learn More:
- structlog: https://www.structlog.org/en/stable/
- Why structured logging: https://www.structlog.org/en/stable/why.html
- JSON Lines format: http://jsonlines.org/
- Correlation IDs: https://hilton.org.uk/blog/microservices-correlation-id

🏗️ How This Works:

Step 1: Configure structlog processors (format, add timestamps, etc.)
Step 2: Setup standard library logging integration
Step 3: Provide get_logger() function for application code
Step 4: Middleware injects correlation_id for each request

Example Usage:
    >>> from app.core.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("user_login", user_id=123, ip="192.168.1.1")

    Output (JSON):
    {
        "event": "user_login",
        "user_id": 123,
        "ip": "192.168.1.1",
        "timestamp": "2025-12-15T12:55:40.123Z",
        "level": "info",
        "logger": "app.auth.service"
    }
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import get_settings

# ============================================================================
# STRUCTLOG PROCESSORS
# ============================================================================


def add_app_context(_logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to every log entry.

    This processor runs for EVERY log message and adds standard fields
    like app_name and environment. This makes it easy to filter logs
    by application when you have multiple services.

    Args:
        logger: The logger instance (from structlog)
        method_name: The log level method called (info, error, etc.)
        event_dict: Dictionary of log data (modified in-place)

    Returns:
        EventDict: Modified event dict with app context added

    Example:
        Input event_dict:  {"event": "user_login", "user_id": 123}
        Output event_dict: {
            "event": "user_login",
            "user_id": 123,
            "app": "LLM Financial Pipeline",
            "environment": "development"
        }

    Why this is useful:
        When you have multiple applications logging to the same system,
        you can filter by app="LLM Financial Pipeline" to see only
        logs from this application.
    """
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["environment"] = settings.environment
    return event_dict


def rename_event_key(
    _logger: logging.Logger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Rename structlog's 'event' key to 'message' for clarity.

    structlog uses "event" by default, but "message" is more intuitive
    when reading logs. This processor renames the key.

    Args:
        logger: The logger instance
        method_name: The log level method called
        event_dict: Dictionary of log data

    Returns:
        EventDict: Modified event dict with 'event' renamed to 'message'

    Example:
        Input:  {"event": "user_login", "user_id": 123}
        Output: {"message": "user_login", "user_id": 123}
    """
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


def configure_logging() -> None:
    """
    Configure structured logging for the entire application.

    This function sets up both structlog (modern structured logging) and
    the standard library logging module (used by third-party packages).

    What it configures:

    1. **Structlog Processors** (run on every log message in order):
       - add_log_level: Adds "level": "info" field
       - add_logger_name: Adds "logger": "app.module.name" field
       - add_app_context: Adds app name and environment
       - TimeStamper: Adds ISO 8601 timestamp
       - StackInfoRenderer: Formats stack traces nicely
       - format_exc_info: Formats exception info
       - rename_event_key: Renames 'event' to 'message'
       - UnicodeDecoder: Ensures everything is proper Unicode
       - JSONRenderer: Outputs as JSON (production) or KeyValueRenderer (dev)

    2. **Standard Library Logging**:
       - Configures root logger to use structlog
       - Sets log level from config (DEBUG, INFO, etc.)
       - Third-party packages (SQLAlchemy, etc.) use this

    3. **Output Format**:
       - Development: Human-readable key=value format
       - Production: JSON Lines format (one JSON object per line)

    Development Output Example:
        2025-12-15T12:55:40.123Z [info] user_login user_id=123 ip=192.168.1.1

    Production Output Example:
        {"timestamp":"2025-12-15T12:55:40.123Z","level":"info","message":"user_login","user_id":123,"ip":"192.168.1.1"}

    Called from:
        app/main.py - During FastAPI application startup

    Example:
        >>> configure_logging()  # Call once at startup
        >>> logger = get_logger(__name__)
        >>> logger.info("app_started")
    """
    settings = get_settings()

    # Determine output format based on environment
    # Development: Human-readable colored output
    # Production: JSON for machine parsing
    if settings.is_development:
        # ConsoleRenderer produces colored, human-friendly output
        # Example: 2025-12-15 12:55:40 [info] user_login user_id=123
        renderer: Processor = structlog.dev.ConsoleRenderer(
            colors=True,  # Colorize log levels (info=green, error=red, etc.)
            exception_formatter=structlog.dev.RichTracebackFormatter(),  # Pretty exceptions
        )
    else:
        # JSONRenderer produces JSON Lines format (one JSON per line)
        # Example: {"timestamp":"2025-12-15T12:55:40Z","level":"info",...}
        renderer = structlog.processors.JSONRenderer()

    # Configure structlog with processors pipeline
    # These run IN ORDER on every log message
    structlog.configure(
        processors=[
            # Add log level (debug, info, warning, error, critical)
            structlog.stdlib.add_log_level,
            # Add logger name (e.g., "app.detection.service")
            structlog.stdlib.add_logger_name,
            # Add our custom app context (app name, environment)
            add_app_context,
            # Add timestamp in ISO 8601 format
            structlog.processors.TimeStamper(fmt="iso"),
            # If log.info("msg", stack_info=True), format the stack trace
            structlog.processors.StackInfoRenderer(),
            # Format exception info nicely
            structlog.processors.format_exc_info,
            # Rename 'event' key to 'message'
            rename_event_key,
            # Ensure all strings are proper Unicode
            structlog.processors.UnicodeDecoder(),
            # Final step: Render as JSON or console output
            renderer,
        ],
        # Wrapper class for standard library integration
        wrapper_class=structlog.stdlib.BoundLogger,
        # Logger factory creates standard library loggers
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Clear context between requests (important for servers!)
        cache_logger_on_first_use=False,
    )

    # Configure standard library logging (used by third-party packages)
    # This ensures libraries like SQLAlchemy, httpx, etc. log properly
    logging.basicConfig(
        format="%(message)s",  # structlog handles formatting
        stream=sys.stdout,  # Log to stdout (not stderr)
        level=getattr(logging, settings.log_level),  # From config (DEBUG, INFO, etc.)
    )

    # Configure specific library log levels
    # These libraries are VERY verbose on DEBUG, so we reduce them
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    # SQLAlchemy logs every SQL query on INFO - too much!

    logging.getLogger("httpx").setLevel(logging.WARNING)
    # httpx logs every HTTP request on DEBUG - too much!

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # Uvicorn access logs are handled by our middleware instead


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance for the given module.

    This is the main function you'll use throughout the application to get
    a logger. It returns a structlog BoundLogger that supports method chaining
    and structured data.

    Args:
        name: Logger name (usually __name__ from the calling module)
              If None, uses root logger

    Returns:
        structlog.stdlib.BoundLogger: Logger instance with structured logging

    Example Usage:
        >>> # In your module
        >>> logger = get_logger(__name__)
        >>> logger.info("user_login", user_id=123, email="user@example.com")
        >>>
        >>> # With exception logging
        >>> try:
        >>>     risky_operation()
        >>> except Exception as e:
        >>>     logger.error("operation_failed", exc_info=e)
        >>>
        >>> # With context binding (all subsequent logs include user_id)
        >>> logger = logger.bind(user_id=123)
        >>> logger.info("profile_viewed")  # Includes user_id=123
        >>> logger.info("settings_changed")  # Also includes user_id=123

    Log Output (JSON in production):
        {
            "timestamp": "2025-12-15T12:55:40.123Z",
            "level": "info",
            "message": "user_login",
            "user_id": 123,
            "email": "user@example.com",
            "logger": "app.auth.service",
            "app": "LLM Financial Pipeline",
            "environment": "production"
        }

    Log Output (colored console in development):
        2025-12-15 12:55:40 [info] user_login user_id=123 email=user@example.com

    Best Practices:
        1. Create logger at module level:
           logger = get_logger(__name__)

        2. Use keyword arguments for structured data:
           logger.info("event_name", key1=value1, key2=value2)

        3. Include correlation_id in web requests (done by middleware)

        4. Bind context for related operations:
           logger = logger.bind(user_id=user.id)

        5. Always log exceptions with exc_info:
           logger.error("something_failed", exc_info=e)

    Why __name__?
        Using __name__ makes the logger name match the module path:
        - In app/auth/service.py: logger name is "app.auth.service"
        - In app/detection/routes.py: logger name is "app.detection.routes"
        This makes it easy to filter logs by module!
    """
    return structlog.get_logger(name)


# ============================================================================
# CORRELATION ID UTILITIES
# ============================================================================


def bind_correlation_id(correlation_id: str) -> None:
    """
    Bind a correlation ID to the current context.

    Correlation IDs allow you to track a single request through the entire
    system. Every log message for that request will include the same
    correlation_id, making debugging much easier.

    This is typically called by middleware for each incoming HTTP request,
    but can also be used for background jobs.

    Args:
        correlation_id: Unique identifier for this request/operation (usually UUID)

    Example (in middleware):
        >>> import uuid
        >>> correlation_id = str(uuid.uuid4())  # Generate unique ID
        >>> bind_correlation_id(correlation_id)
        >>> # All logs from this point include correlation_id
        >>> logger.info("request_received")
        >>> # {"message": "request_received", "correlation_id": "abc-123-def"}

    Example (finding related logs in production):
        $ grep "abc-123-def" logs.jsonl
        {"correlation_id":"abc-123-def","message":"request_received",...}
        {"correlation_id":"abc-123-def","message":"database_query",...}
        {"correlation_id":"abc-123-def","message":"response_sent",...}

    Note:
        This binding is thread-local, so it won't affect other concurrent requests.
        Remember to call clear_correlation_id() after the request completes to
        prevent correlation_id from leaking to the next request!
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def unbind_correlation_id() -> None:
    """
    Remove correlation ID from the current context.

    This should be called after a request completes to ensure the
    correlation_id doesn't leak into subsequent requests.

    Typically called by middleware in a finally block.

    Example (in middleware):
        >>> try:
        >>>     correlation_id = str(uuid.uuid4())
        >>>     bind_correlation_id(correlation_id)
        >>>     # Handle request
        >>>     process_request()
        >>> finally:
        >>>     # Always clean up, even if request failed
        >>>     unbind_correlation_id()
    """
    structlog.contextvars.unbind_contextvars("correlation_id")


def bind_user_context(user_id: int, email: str | None = None) -> None:
    """
    Bind user information to the current logging context.

    Similar to correlation_id, but for user information. All subsequent
    logs will include the user_id and email (if provided).

    Typically called after successful authentication.

    Args:
        user_id: Authenticated user's ID
        email: User's email address (optional)

    Example:
        >>> # After authentication succeeds
        >>> bind_user_context(user_id=123, email="user@example.com")
        >>> logger.info("profile_updated")
        >>> # {"message": "profile_updated", "user_id": 123, "email": "user@example.com"}
        >>>
        >>> # Unbind when request completes (in middleware)
        >>> unbind_user_context()
    """
    context: dict[str, Any] = {"user_id": user_id}
    if email:
        context["email"] = email
    structlog.contextvars.bind_contextvars(**context)


def unbind_user_context() -> None:
    """
    Remove user information from the current logging context.

    Called at the end of a request to prevent user info from leaking
    into subsequent requests.

    Example (in middleware):
        >>> try:
        >>>     # Authenticate and bind user context
        >>>     user = authenticate(token)
        >>>     bind_user_context(user.id, user.email)
        >>>     # Handle request
        >>>     process_request()
        >>> finally:
        >>>     unbind_user_context()
    """
    structlog.contextvars.unbind_contextvars("user_id", "email")


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "configure_logging",
    "get_logger",
    "bind_correlation_id",
    "unbind_correlation_id",
    "bind_user_context",
    "unbind_user_context",
]

"""
📚 What You Learned:

1. **Structured Logging** - JSON instead of plain text
   - Easier to search and filter in production
   - Machine-readable for log aggregation tools
   - Consistent format across all services

2. **Correlation IDs** - Track requests through the system
   - Each request gets a unique UUID
   - All logs for that request share the correlation_id
   - Essential for debugging distributed systems

3. **Processors** - Transform log data
   - Run in order on every log message
   - Can add fields, rename keys, format output
   - Highly customizable pipeline

4. **Context Binding** - Add data to multiple logs
   - Bind once, appears in all subsequent logs
   - Thread-safe (won't affect other requests)
   - Must unbind to prevent data leaking

5. **Development vs Production** - Different formats
   - Development: Human-readable with colors
   - Production: JSON Lines for aggregation
   - Configured automatically based on environment

🎯 Next Steps:

1. Read this file carefully (understand each processor)
2. Try logging in Python REPL:
   >>> from app.core.logging import configure_logging, get_logger
   >>> configure_logging()
   >>> logger = get_logger(__name__)
   >>> logger.info("test_message", key1="value1", key2=123)

3. Look for log output - see the structured format?
4. Next: Write tests for config and logging!

💡 Key Takeaway:
Structured logging is a GAME CHANGER in production. Being able to search
logs by correlation_id, user_id, or any other field makes debugging 10x
faster than grepping through plain text logs. This is industry best practice!
"""
