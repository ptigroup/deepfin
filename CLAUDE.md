# Financial Document Processing Pipeline - Project Guide

> **Project**: Production-ready async financial document processing using FastAPI
> **Status**: 94% Complete (Session 17/18 done)
> **Stack**: FastAPI 0.115+ | SQLAlchemy 2.0 | PostgreSQL | Python 3.12

---

## WHY: Project Purpose

**Business Goal**: Convert financial PDFs (balance sheets, income statements, cash flows) into structured JSON/Excel with 100% accuracy for downstream analysis.

**Technical Approach**: Modern async-first FastAPI microservices architecture with background job processing, JWT authentication, and horizontal scalability.

---

## WHAT: Tech Stack

### Core Framework
- **FastAPI 0.115+**: Async web framework with auto-generated OpenAPI docs
- **Python 3.12**: Type hints, async/await, pattern matching
- **UV**: Fast Python package manager and task runner
- **Pydantic 2.10+**: Data validation and settings management

### Database
- **PostgreSQL**: Primary datastore (via asyncpg)
- **SQLAlchemy 2.0**: Async ORM with type hints
- **Alembic**: Database migrations
- **SQLite**: Testing (via aiosqlite)

### LLM & Document Processing
- **LLMWhisperer (Unstract SDK 0.79+)**: PDF text extraction with table preservation
- **OpenAI GPT-4**: Document type detection and data extraction
- **PyMuPDF**: PDF handling
- **openpyxl**: Excel export

### Infrastructure
- **Uvicorn**: ASGI server
- **Structlog**: Structured JSON logging
- **JWT**: Token-based authentication (python-jose, passlib, bcrypt)
- **Background Jobs**: Async worker pattern with retry logic

### Development
- **Pytest 8.3+**: Testing framework with async support
- **pytest-asyncio**: Async test fixtures
- **MyPy**: Static type checking (strict mode)
- **Ruff**: Fast linter and formatter

---

## HOW: Development Workflow

### Running the Application

**Development**:
```bash
# Start server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123

# Access API docs
open http://localhost:8123/docs        # Swagger UI
open http://localhost:8123/redoc       # ReDoc
```

**Production**:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8123 --workers 4
```

### Testing

```bash
# Run all tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run integration tests only
uv run pytest tests/integration/

# Run specific test file
uv run pytest app/auth/tests/test_service.py

# Run with verbose output
uv run pytest -v
```

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### Code Quality

```bash
# Lint and format
uv run ruff check app/
uv run ruff format app/

# Type checking
uv run mypy app/

# Auto-fix linting issues
uv run ruff check --fix app/
```

---

## Project Structure

```
app/                           # Main FastAPI application
├── main.py                    # Application entry point, lifespan management
├── __init__.py               # Package metadata
│
├── core/                      # Core infrastructure
│   ├── config.py             # Pydantic settings (env-based)
│   ├── database.py           # SQLAlchemy async engine & session
│   ├── logging.py            # Structlog configuration
│   ├── middleware.py         # Request ID, logging middleware
│   ├── exceptions.py         # Custom exceptions & handlers
│   └── health.py             # Health check endpoints
│
├── shared/                    # Shared utilities
│   ├── models.py             # Base SQLAlchemy model with timestamps
│   └── schemas.py            # BaseResponse wrapper
│
├── auth/                      # Authentication & Authorization
│   ├── models.py             # User model
│   ├── schemas.py            # Login, token, user schemas
│   ├── service.py            # JWT token generation, password hashing
│   ├── dependencies.py       # get_current_user dependency
│   └── routes.py             # /auth/register, /auth/login endpoints
│
├── detection/                 # Document type detection
│   ├── models.py             # Detection result storage
│   ├── schemas.py            # Detection request/response
│   ├── detector.py           # OpenAI-based document type detection
│   ├── service.py            # Detection orchestration
│   └── routes.py             # POST /detection/detect
│
├── extraction/                # Financial data extraction
│   ├── models.py             # Extraction result storage
│   ├── schemas.py            # Extraction schemas (balance sheet, income statement, etc.)
│   ├── parser.py             # LLMWhisperer + OpenAI extraction logic
│   ├── service.py            # Extraction orchestration
│   └── routes.py             # POST /extraction/extract
│
├── statements/                # Financial statements management
│   ├── models.py             # Statement storage
│   ├── schemas.py            # Statement CRUD schemas
│   ├── service.py            # Statement CRUD operations
│   └── routes.py             # GET/POST/PUT/DELETE /statements
│
├── consolidation/             # Multi-period analysis & Excel export
│   ├── models.py             # Consolidation result storage
│   ├── schemas.py            # Consolidation request/response
│   ├── exporter.py           # Excel export with formatting
│   ├── service.py            # Multi-period consolidation logic
│   └── routes.py             # POST /consolidation/consolidate
│
├── jobs/                      # Background job processing
│   ├── models.py             # Job model (status, retries, progress)
│   ├── schemas.py            # Job schemas
│   ├── tasks.py              # Registered background tasks
│   ├── worker.py             # Background worker with concurrency control
│   ├── service.py            # Job CRUD and management
│   └── routes.py             # Job endpoints with auth
│
├── notifications/             # Email notifications (future: webhooks)
│   ├── service.py            # Email sending service
│   └── notifications.py      # Notification templates
│
└── llm/                       # LLM client abstractions
    ├── clients.py            # OpenAI, LLMWhisperer clients
    ├── cache.py              # LLM response caching
    └── schemas.py            # LLM request/response schemas

tests/                         # Integration tests
├── conftest.py               # Pytest fixtures (test DB, client, auth)
└── integration/
    ├── test_auth_integration.py
    ├── test_jobs_integration.py
    └── ...

alembic/                       # Database migrations
├── versions/                  # Migration files
└── env.py                    # Alembic configuration

brownfield/                    # Legacy codebase archive (reference only)
```

---

## Architecture Patterns

### 1. **Vertical Slice Architecture**
Each domain module (`auth/`, `detection/`, `extraction/`) is self-contained with:
- `models.py`: SQLAlchemy models
- `schemas.py`: Pydantic request/response schemas
- `service.py`: Business logic
- `routes.py`: FastAPI endpoints
- `tests/`: Module-specific tests

### 2. **Async-First**
- All I/O operations are async (database, HTTP, LLM calls)
- Uses SQLAlchemy 2.0 async engine
- AsyncSession for database transactions
- Background worker uses asyncio.create_task()

### 3. **Dependency Injection**
- FastAPI's `Depends()` for database sessions, auth
- Example: `get_current_user` dependency for protected endpoints
- Scoped sessions (request-scoped) for transaction safety

### 4. **BaseResponse Pattern**
All endpoints return `BaseResponse[T]`:
```python
{
  "success": true,
  "data": { ... },      # Typed Pydantic model
  "message": "Success",
  "error": null
}
```

### 5. **Background Job Pattern**
Long-running tasks (PDF extraction, multi-document processing):
1. Client POSTs to endpoint → Returns job ID immediately
2. Background worker picks up job from database
3. Client polls GET /jobs/{job_id} for status/results
4. Supports retries with exponential backoff

### 6. **Structured Logging**
Uses structlog for JSON logs:
```python
logger.info("Job completed", extra={"job_id": 123, "duration": 45.2})
# Output: {"event": "Job completed", "job_id": 123, "duration": 45.2, "timestamp": "..."}
```

### 7. **Exception Handling**
Global exception handlers convert errors to consistent JSON:
- `ValidationError` → 422 Unprocessable Entity
- `SQLAlchemyError` → 500 Internal Server Error
- Custom exceptions in `core/exceptions.py`

### 8. **JWT Authentication**
- POST `/auth/login` → JWT access token (1 day expiry)
- Protected routes: `Depends(get_current_user)`
- Password hashing: bcrypt (cost factor 12)

### 9. **Database Connection Pooling**
- Async connection pool (asyncpg)
- Pool size: 10 (configurable via env)
- Graceful shutdown on app lifespan

### 10. **Environment-Based Configuration**
- Pydantic Settings with `.env` file
- Environment-specific configs (dev/prod)
- Required: `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `LLMWHISPERER_API_KEY`

---

## Code Conventions

### Imports
- Standard library first, then third-party, then app imports
- Use `from app.module import Class` (not relative imports)
- Group by category, alphabetize within groups

### Type Hints
- **Required** for all functions (enforced by MyPy strict mode)
- Use modern Python 3.12+ syntax: `list[str]` not `List[str]`
- Return types required, including `None`

### Naming
- **Functions/methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: prefix with `_`

### Docstrings
- Required for public functions/classes
- Use Google style: `Args:`, `Returns:`, `Raises:`
- Include usage examples for complex functions

### Error Handling
- Raise custom exceptions from `core/exceptions.py`
- Let global handlers format JSON responses
- Log errors with context: `logger.error("message", extra={...})`

### Testing
- One test file per module: `test_service.py`, `test_routes.py`
- Use descriptive test names: `test_create_user_with_duplicate_email_raises_error`
- Fixtures in `conftest.py` for shared setup (DB, client)
- Async tests: `async def test_...()` with `@pytest.mark.asyncio` (auto-detected)

---

## Database Conventions

### Models
- Inherit from `app.shared.models.BaseModel` (auto-adds `id`, `created_at`, `updated_at`)
- Use SQLAlchemy 2.0 declarative syntax: `Mapped[str]`, `mapped_column()`
- Relationships: `relationship()` with `back_populates`
- Enums: Python `enum.Enum` with SQLAlchemy `Enum` column

### Migrations
- **Always** use `alembic revision --autogenerate`
- Review generated migrations before applying
- Never edit applied migrations (create new ones)
- Add index for frequently queried columns

### Queries
- Use `select()` not `Query` (SQLAlchemy 2.0 style)
- Example: `stmt = select(User).where(User.email == email)`
- Execute with: `result = await session.execute(stmt)`
- Get results: `user = result.scalar_one_or_none()`

---

## API Design Principles

### RESTful Routes
- **GET** `/resource` - List all (with pagination)
- **GET** `/resource/{id}` - Get one
- **POST** `/resource` - Create
- **PUT** `/resource/{id}` - Update (full replace)
- **PATCH** `/resource/{id}` - Partial update
- **DELETE** `/resource/{id}` - Delete

### Response Format
```python
# Success
{
  "success": true,
  "data": { ... },
  "message": "Resource created successfully"
}

# Error
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { ... }
  }
}
```

### Authentication
- Protected routes: Add `user: User = Depends(get_current_user)` parameter
- Header: `Authorization: Bearer <token>`
- Unauthenticated → 401
- Forbidden → 403

### Pagination
- Query params: `?limit=10&offset=0`
- Response includes: `data`, `total`, `limit`, `offset`

---

## Financial Document Processing Specifics

### Document Types
- Balance Sheet
- Income Statement (P&L)
- Cash Flow Statement
- Statement of Shareholders' Equity
- Trial Balance

### Processing Pipeline
1. **PDF Upload** → Store in uploads/ (or cloud storage)
2. **Detection** → OpenAI determines document type
3. **Extraction** → LLMWhisperer extracts raw text → OpenAI structures data
4. **Storage** → Save structured JSON to database
5. **Consolidation** → Multi-period analysis across statements
6. **Export** → Generate Excel with proper formatting & indentation

### LLMWhisperer Configuration
- Mode: `form` (preserves table structure)
- Use caching to avoid re-processing same PDFs
- Fallback: Retry with `text` mode if `form` fails

### OpenAI Best Practices
- Use GPT-4 for accuracy (GPT-3.5 for speed/cost)
- Include examples in system prompts
- Validate outputs with Pydantic schemas
- Implement retry logic for rate limits

---

## Important Files Reference

### Configuration
- `.env`: Environment variables (don't commit!)
- `pyproject.toml`: Dependencies, tool config (pytest, mypy, ruff)
- `alembic.ini`: Database migration config

### Entry Points
- `app/main.py`: FastAPI application
- `app/jobs/worker.py`: Background worker

### Critical Dependencies
- `app/core/database.py`: Database session management
- `app/core/config.py`: Settings singleton
- `app/core/logging.py`: Logger configuration
- `app/auth/dependencies.py`: Auth middleware

---

## Common Tasks

### Add New Endpoint
1. Create route in `module/routes.py`
2. Add service function in `module/service.py`
3. Define request/response schemas in `module/schemas.py`
4. Add tests in `module/tests/test_routes.py`
5. Include router in `app/main.py`

### Add Database Model
1. Define model in `module/models.py` (inherit from `BaseModel`)
2. Create migration: `uv run alembic revision --autogenerate -m "Add table"`
3. Review migration, apply: `uv run alembic upgrade head`
4. Add corresponding Pydantic schemas in `module/schemas.py`

### Add Background Job Task
1. Define task function in `app/jobs/tasks.py`
2. Register in `TASK_REGISTRY` dict
3. Create job via `POST /jobs` with `task_name` and `task_args`
4. Worker picks up automatically

---

## Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Check connection pool exhaustion (increase pool size)

### Authentication Failures
- Verify `SECRET_KEY` is set
- Check token expiry (default: 1 day)
- Ensure bcrypt is installed correctly (C extension)

### Background Jobs Not Processing
- Check worker is running (started in app lifespan)
- Verify job status is `PENDING` in database
- Check worker logs for errors
- Ensure task is registered in `TASK_REGISTRY`

### Type Checking Errors
- Run `uv run mypy app/` to see all issues
- Common fix: Add return type hints
- Ignore third-party libs: Add to `[[tool.mypy.overrides]]` in `pyproject.toml`

---

## Reference Documentation

**Brownfield Code**: Old implementation in `/brownfield` (for reference only)
- Direct parsing logic: `brownfield/parsers/`
- Original pipeline: `brownfield/pipelines/`
- Legacy schemas: `brownfield/schemas/`

**Progress Tracking**: See `JOURNEY.md` for session-by-session development history

**Contributing**: See `CONTRIBUTING.md` for contribution guidelines

---

## Environment Variables

**Required**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# Security
SECRET_KEY=your-secret-key-min-32-chars

# LLM APIs
OPENAI_API_KEY=sk-...
LLMWHISPERER_API_KEY=...

# Application
ENVIRONMENT=development  # or production
DEBUG=true
LOG_LEVEL=INFO
```

**Optional**:
```bash
# Server
PORT=8123
WORKERS=4

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://example.com

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
```

---

## Progressive Disclosure

For deep implementation details, consult:
- API documentation: `/docs` (Swagger UI when server running)
- Module README files (if added in future)
- Inline code documentation (docstrings)
- Architecture diagrams (Session 17 branch - not yet merged)

When unsure about a pattern, search the codebase for existing examples:
```bash
# Find similar functionality
grep -r "async def create_" app/

# Find usage of a dependency
grep -r "Depends(get_current_user)" app/
```

---

**Last Updated**: 2025-12-27 (aligned with Session 17 completion)
**Project Status**: 94% Complete - Production-ready architecture, awaiting deployment (Session 18)
