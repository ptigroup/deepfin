"""
Session Data for All 18 Sessions

Contains detailed information for creating Linear issues.
"""

from typing import List, Dict, Any

# Each session is defined with all necessary metadata
SESSIONS: List[Dict[str, Any]] = [
    # ========================================================================
    # SESSION 1: Core Configuration & Logging (COMPLETE)
    # ========================================================================
    {
        "number": 1,
        "title": "Session 1: Core Configuration & Logging",
        "description": "Build foundational configuration and logging infrastructure using professional patterns.",
        "phase_label": "phase-1-foundation",
        "priority": 2,  # High
        "duration": "1.5 hours",
        "token_estimate": "~8K",
        "test_count": 25,
        "files": [
            "app/__init__.py",
            "app/core/__init__.py",
            "app/core/config.py",
            "app/core/logging.py",
            "app/core/tests/test_config.py",
            "app/core/tests/test_logging.py",
        ],
        "concepts": [
            "Pydantic Settings for type-safe configuration",
            "Singleton pattern with @lru_cache",
            "Structured logging with structlog",
            "Correlation IDs for request tracking",
            "Environment-based configuration",
            "pytest testing patterns",
        ],
        "prerequisites": ["Setup complete (all tests passing)"],
        "acceptance_criteria": [
            "Settings load from .env file",
            "Validation works for required fields",
            "Structured logging outputs JSON",
            "All 25 tests pass",
            "Checkpoint document created",
        ],
        "checkpoint_file": "CHECKPOINT_01_Config_Logging.md",
        "status": "done",  # Already complete
    },

    # ========================================================================
    # SESSION 2: Database & Shared Models
    # ========================================================================
    {
        "number": 2,
        "title": "Session 2: Database & Shared Models",
        "description": "Set up async database connection, create base models with mixins, and establish migration system.",
        "phase_label": "phase-1-foundation",
        "priority": 2,  # High
        "duration": "1.5 hours",
        "token_estimate": "~10K",
        "test_count": 20,
        "files": [
            "app/core/database.py",
            "app/shared/__init__.py",
            "app/shared/models.py",
            "app/shared/schemas.py",
            "app/core/tests/test_database.py",
            "app/shared/tests/test_models.py",
            "alembic.ini",
            "alembic/env.py",
        ],
        "concepts": [
            "Async SQLAlchemy 2.0",
            "Database connection pooling",
            "Alembic migrations",
            "Base models with mixins",
            "Async context managers",
            "Database session management",
        ],
        "prerequisites": ["Session 1 complete (all tests passing)"],
        "acceptance_criteria": [
            "Database connects successfully",
            "Async sessions work correctly",
            "TimestampMixin auto-populates timestamps",
            "Base schemas validate properly",
            "All 15-20 tests pass",
            "Alembic migrations configured",
            "Checkpoint document created",
        ],
        "checkpoint_file": "CHECKPOINT_02_Database_Models.md",
        "status": "in_progress",  # Currently working on
    },

    # ========================================================================
    # SESSION 3: FastAPI Application & Health Checks
    # ========================================================================
    {
        "number": 3,
        "title": "Session 3: FastAPI Application & Health Checks",
        "description": "Create the FastAPI application with health endpoints, middleware, and exception handling.",
        "phase_label": "phase-1-foundation",
        "priority": 2,  # High
        "duration": "1.5 hours",
        "token_estimate": "~9K",
        "test_count": 12,
        "files": [
            "app/core/health.py",
            "app/core/middleware.py",
            "app/core/exceptions.py",
            "app/main.py",
            "tests/test_main.py",
        ],
        "concepts": [
            "FastAPI application setup",
            "Dependency injection",
            "Middleware implementation",
            "Exception handlers",
            "Lifespan events",
            "CORS configuration",
        ],
        "prerequisites": ["Session 2 complete (all tests passing)"],
        "acceptance_criteria": [
            "API starts successfully",
            "/health returns 200",
            "/health/db checks database",
            "Middleware logs requests",
            "Exception handlers work",
            "All tests pass",
            "MILESTONE: Working API at http://localhost:8123",
        ],
        "checkpoint_file": "CHECKPOINT_03_FastAPI_Health.md",
        "status": "todo",
    },

    # ========================================================================
    # SESSION 4: LLMWhisperer Client
    # ========================================================================
    {
        "number": 4,
        "title": "Session 4: LLMWhisperer Client",
        "description": "Create LLMWhisperer API client with caching and error handling.",
        "phase_label": "phase-2-llm",
        "priority": 2,  # High
        "duration": "1.5 hours",
        "token_estimate": "~10K",
        "test_count": 10,
        "files": [
            "app/llm/__init__.py",
            "app/llm/clients.py",
            "app/llm/schemas.py",
            "app/llm/cache.py",
            "app/llm/tests/test_clients.py",
        ],
        "concepts": [
            "HTTP client configuration (httpx)",
            "API key management",
            "File caching strategies",
            "Async file operations",
            "Error handling and retries",
        ],
        "prerequisites": ["Session 3 complete (API running)"],
        "acceptance_criteria": [
            "Client can call LLMWhisperer API",
            "Caching works correctly",
            "Error handling robust",
            "All tests pass",
        ],
        "checkpoint_file": "CHECKPOINT_04_LLM_Client.md",
        "status": "todo",
    },

    # ========================================================================
    # SESSIONS 5-18: Additional sessions
    # ========================================================================
    # (Abbreviated for brevity - follow same pattern)

    {
        "number": 5,
        "title": "Session 5: Detection Models",
        "description": "Create database models for table detection feature.",
        "phase_label": "phase-3-detection",
        "priority": 3,
        "duration": "1 hour",
        "token_estimate": "~8K",
        "test_count": 8,
        "files": ["app/detection/__init__.py", "app/detection/models.py", "app/detection/schemas.py", "alembic/versions/XXX_detection_tables.py"],
        "concepts": ["SQLAlchemy models", "Relationship definitions", "Enum types", "Alembic migrations"],
        "prerequisites": ["Session 4 complete"],
        "acceptance_criteria": ["Models defined", "Migration applied", "Schemas validate", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_05_Detection_Models.md",
        "status": "todo",
    },

    {
        "number": 6,
        "title": "Session 6: Detection Service",
        "description": "Implement table detection service and API endpoints.",
        "phase_label": "phase-3-detection",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~11K",
        "test_count": 12,
        "files": ["app/detection/service.py", "app/detection/detector.py", "app/detection/routes.py", "app/detection/tests/test_service.py"],
        "concepts": ["Service layer pattern", "File upload handling", "PyMuPDF integration", "API endpoint design"],
        "prerequisites": ["Session 5 complete"],
        "acceptance_criteria": ["POST /api/detection/analyze works", "Files upload and process", "Detection returns results", "Tests pass", "MILESTONE: Can detect tables in PDFs"],
        "checkpoint_file": "CHECKPOINT_06_Detection_Complete.md",
        "status": "todo",
    },

    # Sessions 7-18 follow similar pattern...
    # (For brevity, showing condensed versions)

    {
        "number": 7,
        "title": "Session 7: Statements Models",
        "description": "Create database models for financial statements feature.",
        "phase_label": "phase-4-statements",
        "priority": 3,
        "duration": "1 hour",
        "token_estimate": "~8K",
        "test_count": 8,
        "files": ["app/statements/__init__.py", "app/statements/models.py", "app/statements/schemas.py"],
        "concepts": ["Financial statement schemas", "Data validation", "Model relationships"],
        "prerequisites": ["Session 6 complete"],
        "acceptance_criteria": ["Models defined", "Schemas validate", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_07_Statements_Models.md",
        "status": "todo",
    },

    {
        "number": 8,
        "title": "Session 8: Statements Service",
        "description": "Implement statements processing service and API.",
        "phase_label": "phase-4-statements",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~12K",
        "test_count": 15,
        "files": ["app/statements/service.py", "app/statements/routes.py", "app/statements/tests/"],
        "concepts": ["Statement processing", "API design", "Service patterns"],
        "prerequisites": ["Session 7 complete"],
        "acceptance_criteria": ["API endpoints work", "Processing complete", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_08_Statements_Complete.md",
        "status": "todo",
    },

    {
        "number": 9,
        "title": "Session 9: Extraction Models",
        "description": "Create models for data extraction feature.",
        "phase_label": "phase-5-extraction",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~10K",
        "test_count": 10,
        "files": ["app/extraction/__init__.py", "app/extraction/models.py", "app/extraction/schemas.py"],
        "concepts": ["Extraction schemas", "Complex validation", "Data models"],
        "prerequisites": ["Session 8 complete"],
        "acceptance_criteria": ["Models created", "Validation works", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_09_Extraction_Models.md",
        "status": "todo",
    },

    {
        "number": 10,
        "title": "Session 10: Extraction Service",
        "description": "Implement extraction service with direct parsing.",
        "phase_label": "phase-5-extraction",
        "priority": 3,
        "duration": "2 hours",
        "token_estimate": "~15K",
        "test_count": 18,
        "files": ["app/extraction/service.py", "app/extraction/parser.py", "app/extraction/routes.py"],
        "concepts": ["Direct parsing", "Data extraction", "Complex service logic"],
        "prerequisites": ["Session 9 complete"],
        "acceptance_criteria": ["Extraction works", "Parsing accurate", "API complete", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_10_Extraction_Complete.md",
        "status": "todo",
    },

    {
        "number": 11,
        "title": "Session 11: Consolidation Models",
        "description": "Create models for data consolidation.",
        "phase_label": "phase-6-consolidation",
        "priority": 3,
        "duration": "1 hour",
        "token_estimate": "~8K",
        "test_count": 8,
        "files": ["app/consolidation/__init__.py", "app/consolidation/models.py", "app/consolidation/schemas.py"],
        "concepts": ["Data consolidation", "Aggregation models"],
        "prerequisites": ["Session 10 complete"],
        "acceptance_criteria": ["Models created", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_11_Consolidation_Models.md",
        "status": "todo",
    },

    {
        "number": 12,
        "title": "Session 12: Consolidation Service",
        "description": "Implement consolidation service and Excel export.",
        "phase_label": "phase-6-consolidation",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~12K",
        "test_count": 12,
        "files": ["app/consolidation/service.py", "app/consolidation/exporter.py", "app/consolidation/routes.py"],
        "concepts": ["Data aggregation", "Excel export", "Service patterns"],
        "prerequisites": ["Session 11 complete"],
        "acceptance_criteria": ["Consolidation works", "Excel export works", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_12_Consolidation_Complete.md",
        "status": "todo",
    },

    {
        "number": 13,
        "title": "Session 13: Background Jobs",
        "description": "Implement background job processing.",
        "phase_label": "phase-7-jobs-auth",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~10K",
        "test_count": 10,
        "files": ["app/jobs/__init__.py", "app/jobs/worker.py", "app/jobs/tasks.py"],
        "concepts": ["Background tasks", "Job queues", "Task scheduling"],
        "prerequisites": ["Session 12 complete"],
        "acceptance_criteria": ["Jobs process", "Scheduling works", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_13_Background_Jobs.md",
        "status": "todo",
    },

    {
        "number": 14,
        "title": "Session 14: Authentication",
        "description": "Implement JWT authentication and authorization.",
        "phase_label": "phase-7-jobs-auth",
        "priority": 2,
        "duration": "2 hours",
        "token_estimate": "~15K",
        "test_count": 15,
        "files": ["app/auth/__init__.py", "app/auth/models.py", "app/auth/service.py", "app/auth/routes.py"],
        "concepts": ["JWT tokens", "Password hashing", "OAuth2", "Protected routes"],
        "prerequisites": ["Session 13 complete"],
        "acceptance_criteria": ["Auth works", "JWT secure", "Routes protected", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_14_Authentication.md",
        "status": "todo",
    },

    {
        "number": 15,
        "title": "Session 15: Email & Notifications",
        "description": "Implement email notifications for job completion.",
        "phase_label": "phase-8-testing",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~9K",
        "test_count": 8,
        "files": ["app/email/__init__.py", "app/email/service.py", "app/email/templates/"],
        "concepts": ["Email sending", "Template rendering", "Notifications"],
        "prerequisites": ["Session 14 complete"],
        "acceptance_criteria": ["Emails send", "Templates work", "Tests pass"],
        "checkpoint_file": "CHECKPOINT_15_Email_Notifications.md",
        "status": "todo",
    },

    {
        "number": 16,
        "title": "Session 16: Integration Tests",
        "description": "Write end-to-end integration tests.",
        "phase_label": "phase-8-testing",
        "priority": 2,
        "duration": "2 hours",
        "token_estimate": "~12K",
        "test_count": 20,
        "files": ["tests/integration/", "tests/conftest.py"],
        "concepts": ["Integration testing", "End-to-end tests", "Test fixtures"],
        "prerequisites": ["Session 15 complete"],
        "acceptance_criteria": ["Full pipeline tests", "Integration works", "Tests pass", "80%+ coverage"],
        "checkpoint_file": "CHECKPOINT_16_Integration_Tests.md",
        "status": "todo",
    },

    {
        "number": 17,
        "title": "Session 17: Documentation & Polish",
        "description": "Polish codebase and add comprehensive documentation.",
        "phase_label": "phase-9-deploy",
        "priority": 3,
        "duration": "1.5 hours",
        "token_estimate": "~8K",
        "test_count": 5,
        "files": ["README.md", "ARCHITECTURE.md", "API.md"],
        "concepts": ["Documentation", "Code polish", "API docs"],
        "prerequisites": ["Session 16 complete"],
        "acceptance_criteria": ["Docs complete", "Code polished", "API documented"],
        "checkpoint_file": "CHECKPOINT_17_Documentation_Polish.md",
        "status": "todo",
    },

    {
        "number": 18,
        "title": "Session 18: Deployment & CI/CD",
        "description": "Deploy to cloud and set up CI/CD pipeline.",
        "phase_label": "phase-9-deploy",
        "priority": 2,
        "duration": "2 hours",
        "token_estimate": "~12K",
        "test_count": 10,
        "files": ["Dockerfile", "docker-compose.yml", ".github/workflows/"],
        "concepts": ["Docker deployment", "CI/CD", "Cloud deployment"],
        "prerequisites": ["Session 17 complete"],
        "acceptance_criteria": ["Docker builds", "Deployed to cloud", "CI/CD works", "Live demo accessible", "FINAL MILESTONE: Project Complete!"],
        "checkpoint_file": "CHECKPOINT_18_Deployment_Complete.md",
        "status": "todo",
    },
]


def get_session(session_number: int) -> Dict[str, Any]:
    """
    Get session data by number.

    Args:
        session_number: Session number (1-18)

    Returns:
        Session data dictionary

    Raises:
        ValueError: If session number invalid
    """
    for session in SESSIONS:
        if session["number"] == session_number:
            return session
    raise ValueError(f"Session {session_number} not found. Valid range: 1-18")


def get_all_sessions() -> List[Dict[str, Any]]:
    """Get all session data."""
    return SESSIONS
