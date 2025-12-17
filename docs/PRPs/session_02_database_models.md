# Session 2: Database & Shared Models

**PRP Version:** 1.0
**Created:** 2025-12-16
**Linear Issue:** [BUD-6](https://linear.app/deepfin/issue/BUD-6)
**Session Duration:** 1.5 hours
**Token Estimate:** ~10K tokens

---

## Goal

**Feature Goal:** Establish async database infrastructure with SQLAlchemy 2.0, create reusable base models, and set up Alembic migration system.

**Deliverable:** Production-ready async database layer with connection pooling, base models with timestamp tracking, and automated migration system.

**Success Definition:** Database connects successfully, all 20 tests passing, migrations apply cleanly, and reusable patterns established for future sessions.

---

## Why

**Business Value:**
- Enables persistent storage for all future features (detection, statements, extraction)
- Establishes professional database patterns for the entire project
- Provides audit trail with automatic timestamp tracking

**Integration:**
- Builds on Session 1's configuration system (DATABASE_URL from config.py)
- Uses Session 1's logging infrastructure for database operation tracking
- Creates foundation for Sessions 3-18 (all require database models)

**Problems Solved:**
- No current database layer exists (brownfield code uses direct file operations)
- Need type-safe, async-first database access for FastAPI
- Require automated migrations for team collaboration and deployment

---

## What

### User-Visible Behavior
- Database operations are transparent to users
- Fast async operations (no blocking)
- Automatic created_at/updated_at timestamps on all models

### Technical Requirements

**Core Infrastructure:**
1. Async SQLAlchemy 2.0 engine with connection pooling
2. Database session dependency injection for FastAPI
3. Alembic migration system configured
4. Base model with TimestampMixin
5. Base Pydantic schemas for API responses

**Files to Create (8 files):**
- `app/core/database.py` - Database engine, session factory, Base model
- `app/shared/__init__.py` - Shared utilities package
- `app/shared/models.py` - TimestampMixin and utilities
- `app/shared/schemas.py` - Base Pydantic schemas
- `app/core/tests/test_database.py` - Database connection tests (8 tests)
- `app/shared/tests/test_models.py` - TimestampMixin tests (7 tests)
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Alembic environment setup

### Success Criteria

- [ ] Database engine creates connections successfully
- [ ] Async sessions work with FastAPI dependency injection
- [ ] TimestampMixin auto-populates created_at/updated_at
- [ ] Base Pydantic schemas validate properly
- [ ] All 20 tests pass (8 database + 7 models + 5 schemas)
- [ ] Alembic migrations run successfully (upgrade/downgrade)
- [ ] Connection pooling configured (pool_size=5, max_overflow=10)
- [ ] Checkpoint document created
- [ ] Linear issue BUD-6 updated to "Done"

---

## Context

### Prerequisites

**Required Sessions:**
- [x] Session 1 complete (all 25 tests passing)
- [x] `.env` configured with `DATABASE_URL`
- [x] PostgreSQL running in Docker (port 5433)

**Required Setup:**
```bash
# Verify PostgreSQL is running
docker ps | grep llm_postgres

# Verify DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/llm_pipeline
```

### Session Data Reference

```python
{
    "number": 2,
    "title": "Session 2: Database & Shared Models",
    "description": "Set up async database connection, create base models with mixins, and establish migration system.",
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
    "test_count": 20,
    "duration": "1.5 hours",
    "token_estimate": "~10K",
}
```

### Documentation References

**MUST READ:**
```yaml
- url: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
  why: Async SQLAlchemy patterns and session management
  critical: Must use AsyncSession, not Session

- url: https://alembic.sqlalchemy.org/en/latest/tutorial.html
  why: Migration system setup and autogenerate patterns
  critical: env.py must import all models for autogenerate

- file: app/core/config.py
  why: DATABASE_URL configuration and Settings pattern
  pattern: Use get_settings() singleton for database URL

- file: app/core/logging.py
  why: Logging pattern for database operations
  pattern: Use get_logger(__name__) for structured logging

- url: https://docs.pydantic.dev/latest/concepts/models/
  why: Base schema patterns with ConfigDict
  critical: Use ConfigDict(from_attributes=True) for ORM models
```

### Current Codebase Structure

```bash
app/
├── __init__.py (✅ Session 1)
└── core/
    ├── __init__.py (✅ Session 1)
    ├── config.py (✅ Session 1 - 11 tests)
    ├── logging.py (✅ Session 1 - 14 tests)
    └── tests/
        ├── __init__.py
        ├── test_config.py (✅ 11 tests)
        └── test_logging.py (✅ 14 tests)
```

### Desired Codebase After This Session

```bash
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py (✅ existing)
│   ├── logging.py (✅ existing)
│   ├── database.py (🆕 NEW - engine, session, Base)
│   └── tests/
│       ├── __init__.py
│       ├── test_config.py (✅ existing)
│       ├── test_logging.py (✅ existing)
│       └── test_database.py (🆕 NEW - 8 tests)
└── shared/
    ├── __init__.py (🆕 NEW)
    ├── models.py (🆕 NEW - TimestampMixin, utcnow)
    ├── schemas.py (🆕 NEW - Base schemas)
    └── tests/
        ├── __init__.py (🆕 NEW)
        └── test_models.py (🆕 NEW - 7 tests)

alembic/
├── env.py (🆕 NEW - migration environment)
├── script.py.mako (🆕 AUTO-GENERATED)
└── versions/ (🆕 NEW - migrations go here)

alembic.ini (🆕 NEW - Alembic configuration)
```

### Known Gotchas

```python
# CRITICAL: SQLAlchemy 2.0 Async Patterns
# ❌ WRONG (SQLAlchemy 1.x pattern):
session.query(User).filter_by(id=1).first()

# ✅ CORRECT (SQLAlchemy 2.0 async pattern):
result = await session.execute(select(User).where(User.id == 1))
user = result.scalar_one_or_none()

# GOTCHA: Database URL must use asyncpg driver
# ❌ WRONG: postgresql://...
# ✅ CORRECT: postgresql+asyncpg://...

# CRITICAL: Session management in FastAPI
# Must use async with pattern for proper cleanup
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# GOTCHA: Alembic autogenerate requires all models imported
# In alembic/env.py, must import Base AFTER all models defined:
from app.core.database import Base  # This imports all models
target_metadata = Base.metadata

# PATTERN: Type hints with Mapped[]
# SQLAlchemy 2.0 uses Mapped[] for type safety
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
```

---

## Implementation Blueprint

### Data Models & Structure

```python
# app/core/database.py - Core database infrastructure

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

# Engine with connection pooling
settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=5,
    max_overflow=10,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

```python
# app/shared/models.py - Reusable model mixins

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()

class TimestampMixin:
    """Mixin for automatic timestamp tracking."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

```python
# app/shared/schemas.py - Base Pydantic schemas

from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TimestampSchema(BaseModel):
    """Base schema with timestamps."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = 1
    page_size: int = 50

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
```

### Implementation Tasks (Ordered by Dependencies)

```yaml
Task 1: CREATE app/core/database.py
  - IMPLEMENT: Base, engine, AsyncSessionLocal, get_db()
  - FOLLOW pattern: Async context manager pattern
  - NAMING: Base (class), engine (module-level), get_db (function)
  - DEPENDENCIES: Requires app/core/config.py (DATABASE_URL)
  - CRITICAL: Must use create_async_engine, not create_engine

Task 2: CREATE app/shared/__init__.py
  - IMPLEMENT: Empty package init (just docstring)
  - NAMING: Package name: "shared" (cross-feature utilities)

Task 3: CREATE app/shared/models.py
  - IMPLEMENT: TimestampMixin, utcnow()
  - FOLLOW pattern: SQLAlchemy 2.0 Mapped[] type hints
  - NAMING: TimestampMixin (class), utcnow (function)
  - DEPENDENCIES: None (pure SQLAlchemy)

Task 4: CREATE app/shared/schemas.py
  - IMPLEMENT: TimestampSchema, PaginationParams
  - FOLLOW pattern: Pydantic BaseModel with ConfigDict
  - NAMING: *Schema suffix for response models
  - DEPENDENCIES: None (pure Pydantic)

Task 5: CONFIGURE Alembic (alembic init)
  - RUN: alembic init alembic
  - MODIFY: alembic.ini (set sqlalchemy.url to use config)
  - MODIFY: alembic/env.py (import Base, async config)
  - CRITICAL: env.py must support async migrations

Task 6: CREATE app/core/tests/test_database.py
  - IMPLEMENT: 8 tests (connection, session, get_db dependency)
  - FIXTURES: async_engine, async_session, test database
  - COVERAGE: Engine creation, session lifecycle, error handling
  - MARKER: @pytest.mark.asyncio for async tests

Task 7: CREATE app/shared/tests/test_models.py
  - IMPLEMENT: 7 tests (TimestampMixin, utcnow)
  - FIXTURES: test_db with tables created
  - COVERAGE: Auto-populate timestamps, utcnow function
  - CRITICAL: Test that timestamps are UTC
```

### Critical Implementation Patterns

```python
# Pattern 1: Async database session dependency
from typing import AsyncGenerator
from fastapi import Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    PATTERN: Async context manager with proper cleanup
    CRITICAL: Must commit/rollback, don't leave transactions open
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Usage in route:
@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

```python
# Pattern 2: Model with TimestampMixin
from app.core.database import Base
from app.shared.models import TimestampMixin

class User(Base, TimestampMixin):
    """
    PATTERN: Inherit Base first, then mixins
    GOTCHA: TimestampMixin uses server_default, automatically set by DB
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

```python
# Pattern 3: Alembic env.py async configuration
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import get_settings
from app.core.database import Base

# CRITICAL: This imports all models via Base
target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_settings().database_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Async migration execution
    async def do_run_migrations(connection: Connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

### Integration Points

```yaml
DATABASE:
  - verify: "docker ps | grep llm_postgres"
  - connect: "Use DATABASE_URL from settings"
  - migration create: "alembic revision --autogenerate -m 'initial schema'"
  - migration apply: "alembic upgrade head"
  - migration rollback: "alembic downgrade -1"

CONFIG:
  - add to: app/core/config.py (if needed)
  - settings: "database_echo: bool = False  # SQL query logging"
  - env var: "DATABASE_ECHO=true for debugging"

LOGGING:
  - pattern: "logger.info('database.connection_initialized', pool_size=5)"
  - pattern: "logger.error('database.connection_failed', exc_info=True)"
  - events: "database.connection_initialized, database.session_created"
```

---

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Run after creating each file - fix before proceeding

# Type checking (strict mode)
uv run mypy app/core/database.py
uv run mypy app/shared/models.py
uv run mypy app/shared/schemas.py

# Linting
uv run ruff check app/core/database.py
uv run ruff check app/shared/

# Formatting
uv run ruff format app/core/database.py
uv run ruff format app/shared/

# Expected: Zero errors. Fix any issues immediately.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Test each module as created

# Database tests (8 tests)
uv run pytest app/core/tests/test_database.py -v

# Models tests (7 tests)
uv run pytest app/shared/tests/test_models.py -v

# All new tests together (15 tests)
uv run pytest app/core/tests/test_database.py app/shared/tests/test_models.py -v

# Expected: All 15+ tests pass (may be more with schema tests)
```

### Level 3: Integration Testing (System Validation)

```bash
# Test with real PostgreSQL database

# Run integration tests
uv run pytest -v -m integration

# Verify database connection manually
python -c "
from app.core.database import engine
from sqlalchemy import text
import asyncio

async def test_connection():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        print(f'Database connected: {result.scalar()}')

asyncio.run(test_connection())
"

# Test Alembic migrations
uv run alembic upgrade head    # Apply migrations
uv run alembic downgrade base  # Rollback all
uv run alembic upgrade head    # Reapply

# Verify tables created
docker exec -it llm_postgres psql -U postgres -d llm_pipeline -c "\dt"

# Expected: All tables exist, migrations work both directions
```

### Level 4: Manual Validation

```bash
# Manual verification steps

1. Check database connection:
   - PostgreSQL container running
   - Can connect from host machine
   - Database 'llm_pipeline' exists

2. Verify configuration:
   - DATABASE_URL in .env is correct
   - Settings load database_url properly
   - Echo mode works (if enabled)

3. Test migrations:
   - alembic current shows version
   - alembic history shows migration
   - Can upgrade and downgrade

4. Verify Linear issue:
   - https://linear.app/deepfin/issue/BUD-6
   - Status: "In Progress" → "Done"
   - Comment added with test results

# Expected: All manual checks pass, ready for next session
```

---

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] All 20 tests pass: `uv run pytest app/ -v`
- [ ] No type errors: `uv run mypy app/`
- [ ] No linting errors: `uv run ruff check app/`
- [ ] No formatting issues: `uv run ruff format app/ --check`
- [ ] Database migrations work: `alembic upgrade head` succeeds

### Feature Validation

- [ ] Database engine creates connections successfully
- [ ] Async sessions work with context manager
- [ ] TimestampMixin auto-populates timestamps (tested)
- [ ] Base schemas validate ORM models (from_attributes=True)
- [ ] Connection pooling configured (pool_size=5, max_overflow=10)
- [ ] Alembic autogenerate detects model changes
- [ ] All 8 files created as specified

### Code Quality Validation

- [ ] Follows Session 1 patterns (config, logging)
- [ ] File placement correct (core/, shared/, tests/)
- [ ] Naming conventions consistent (snake_case, async_ prefix)
- [ ] Documentation complete (Google-style docstrings)
- [ ] No hardcoded values (uses get_settings())
- [ ] Error handling proper (rollback on exception)

### Session Completion

- [ ] Checkpoint document created in `docs/checkpoints/CHECKPOINT_02_Database_Models.md`
- [ ] Linear issue BUD-6 updated to "Done"
- [ ] Linear issue BUD-7 moved to "In Progress"
- [ ] PROGRESS_TRACKER.md updated (20 tests, 8 files)
- [ ] Git commit created with proper message
- [ ] PR created for review (if using PR workflow)

---

## Anti-Patterns to Avoid

### Session 2 Specific Anti-Patterns

- ❌ **Don't use sync SQLAlchemy** - Must use AsyncSession, create_async_engine
- ❌ **Don't forget asyncpg driver** - URL must be `postgresql+asyncpg://`
- ❌ **Don't leave sessions open** - Always use async with or proper cleanup
- ❌ **Don't skip TimestampMixin** - All future models should inherit it
- ❌ **Don't hardcode database URL** - Use get_settings().database_url
- ❌ **Don't skip migrations** - Always run alembic for schema changes
- ❌ **Don't mix SQLAlchemy 1.x/2.0 patterns** - Use Mapped[], select(), not query()

### General Anti-Patterns

- ❌ Don't commit without running tests
- ❌ Don't skip type checking
- ❌ Don't use `Any` type for database models
- ❌ Don't catch Exception without logging
- ❌ Don't skip docstrings on public functions
- ❌ Don't create duplicate patterns (reuse TimestampMixin)

---

## Session Completion Steps

When this session is complete:

1. **Run Final Validation**
   ```bash
   # All tests
   uv run pytest app/ -v

   # Type checking
   uv run mypy app/

   # Linting
   uv run ruff check app/

   # Verify migrations
   uv run alembic upgrade head
   ```

2. **Create Checkpoint Document**
   ```bash
   # Create docs/checkpoints/CHECKPOINT_02_Database_Models.md
   # Include:
   # - Summary of what was built
   # - All 8 files created with descriptions
   # - 20 tests passing breakdown
   # - Key learnings about async SQLAlchemy
   # - Migration system setup
   # - What's ready for Session 3
   ```

3. **Update Tracking Files**
   ```bash
   # Update PROGRESS_TRACKER.md:
   # - Session 2 status: Complete
   # - Files created: 8 files
   # - Tests passing: 45/45 (25 from Session 1 + 20 new)
   # - Test coverage: Updated percentage

   # Update SESSION_MANIFEST.md:
   # - Session 2 status: Complete
   # - Add completion date and commit hash
   ```

4. **Update Linear**
   ```bash
   # Manual or automated (GitHub Action):
   # - BUD-6: Status "Done"
   # - BUD-6: Add comment with test results and checkpoint link
   # - BUD-7: Status "In Progress"
   ```

5. **Git Commit**
   ```bash
   git add .
   git commit -m "Session 2: Database & Shared Models

   - Async SQLAlchemy 2.0 engine with connection pooling
   - TimestampMixin for automatic audit trails
   - Base Pydantic schemas for API responses
   - Alembic migration system configured
   - Tests: 20/20 passing (45/45 total)
   - Checkpoint: CHECKPOINT_02_Database_Models.md
   - Linear: BUD-6 complete

   🤖 Generated with Claude Code

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

6. **Create PR (If Using PR Workflow)**
   ```bash
   git checkout -b session-02-database-models
   git push origin session-02-database-models

   gh pr create \
     --title "Session 2: Database & Shared Models" \
     --body "Implements Session 2 PRP. Closes linear://issue/BUD-6

   ## Summary
   Sets up async database layer with SQLAlchemy 2.0, shared models, and Alembic migrations.

   ## Files Created (8)
   - app/core/database.py
   - app/shared/models.py
   - app/shared/schemas.py
   - alembic.ini, alembic/env.py
   - Tests (15 new tests)

   ## Tests
   - Database tests: 8/8 ✅
   - Models tests: 7/7 ✅
   - Total project tests: 45/45 ✅

   ## Validation
   - [x] All 4 validation levels passed
   - [x] Type checking passed (mypy)
   - [x] Linting passed (ruff)
   - [x] Migrations work (alembic)

   ## Links
   - PRP: docs/PRPs/session_02_database_models.md
   - Checkpoint: docs/checkpoints/CHECKPOINT_02_Database_Models.md
   - Linear: https://linear.app/deepfin/issue/BUD-6"
   ```

7. **Request Review (If Automated)**
   ```bash
   # Comment on PR: @claude-review
   # GitHub Action will:
   # - Review all code changes
   # - Verify PRP requirements met
   # - Check test coverage
   # - Post review comments
   ```

---

**PRP Status:** ✅ Ready for Implementation
**Next Session:** Session 3 - FastAPI Application & Health Checks
**Linear:** https://linear.app/deepfin/issue/BUD-6
**Created:** 2025-12-16
**Version:** 1.0
