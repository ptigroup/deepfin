# Session [NUMBER]: [SESSION_NAME]

**PRP Version:** 1.0
**Created:** [DATE]
**Linear Issue:** [BUD-X](https://linear.app/deepfin/issue/BUD-X)
**Session Duration:** [X] hours
**Token Estimate:** ~[X]K tokens

---

## Goal

**Feature Goal:** [Specific, measurable end state of what needs to be built in this session]

**Deliverable:** [Concrete files/features - e.g., "Async database layer with SQLAlchemy 2.0"]

**Success Definition:** [How you'll know this session is complete - e.g., "All 20 database tests passing, migrations working"]

---

## Why

**Business Value:**
- [Why this session matters for the project]

**Integration:**
- [How this builds on previous sessions]
- [What this enables for future sessions]

**Problems Solved:**
- [Specific issues this addresses]

---

## What

### User-Visible Behavior
[If applicable - what changes for users/developers using this system]

### Technical Requirements
[Specific technical deliverables]

### Success Criteria

- [ ] [Specific measurable outcome 1]
- [ ] [Specific measurable outcome 2]
- [ ] [Specific measurable outcome 3]
- [ ] All tests passing ([X]/[X] tests)
- [ ] Checkpoint document created
- [ ] Linear issue BUD-X updated to "Done"

---

## Context

### Prerequisites

**Required Sessions:**
- [ ] Session [X] must be complete

**Required Setup:**
- [ ] [Any environment/tools needed]

### Session Data Reference

**From session_data.py:**
```python
{
    "number": [X],
    "title": "[TITLE]",
    "description": "[DESCRIPTION]",
    "files": ["file1.py", "file2.py", ...],
    "concepts": ["Concept 1", "Concept 2", ...],
    "test_count": [X],
    "duration": "[X] hours",
    "token_estimate": "~[X]K",
}
```

### Documentation References

**MUST READ:**
```yaml
- url: https://docs.pydantic.dev/latest/
  why: [Specific feature/pattern needed]

- file: app/core/config.py
  why: [Pattern to follow - e.g., Settings class structure]
  pattern: [What to extract - e.g., @lru_cache singleton pattern]

- file: CLAUDE.md
  why: [Project-specific requirements]
```

### Current Codebase Structure

```bash
app/
├── __init__.py
├── core/
│   ├── config.py (✅ Session 1)
│   └── logging.py (✅ Session 1)
└── [other modules as they're created]
```

### Desired Codebase After This Session

```bash
app/
├── [new files/modules to be created]
└── [existing modules - mark if modified]
```

### Known Gotchas

```python
# CRITICAL: FastAPI specific patterns
# - All database operations MUST be async
# - Use `async with get_db() as session` pattern
# - SQLAlchemy 2.0 uses select() not .query()

# GOTCHA: Environment variables
# - Database URL must use asyncpg driver (postgresql+asyncpg://)
# - Don't forget to add new config to Settings class

# PATTERN: Testing
# - Integration tests use @pytest.mark.integration
# - Mock external dependencies in unit tests
```

---

## Implementation Blueprint

### Data Models & Structure

```python
# Example: ORM Models
class Example(Base, TimestampMixin):
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

# Example: Pydantic Schemas
class ExampleCreate(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)
```

### Implementation Tasks (Ordered by Dependencies)

```yaml
Task 1: CREATE [file_path]
  - IMPLEMENT: [Specific classes/functions]
  - FOLLOW pattern: [existing_file.py] ([what pattern to copy])
  - NAMING: [naming conventions]
  - PLACEMENT: [where in directory structure]
  - DEPENDENCIES: [what must exist first]

Task 2: MODIFY [existing_file]
  - ADD: [what to add]
  - PRESERVE: [what not to change]
  - PATTERN: [existing pattern to follow]

Task 3: CREATE [test_file.py]
  - IMPLEMENT: [test scenarios]
  - COVERAGE: [what must be tested]
  - FIXTURES: [what fixtures to use/create]
```

### Critical Implementation Patterns

```python
# Show non-obvious patterns, gotchas, and critical details

# Example: Async database pattern
async def get_items(db: AsyncSession) -> list[Item]:
    """
    PATTERN: SQLAlchemy 2.0 async query
    GOTCHA: Must use select() not .query()
    """
    result = await db.execute(select(Item))
    return result.scalars().all()

# Example: Configuration pattern
class Settings(BaseSettings):
    """
    PATTERN: Pydantic Settings singleton
    CRITICAL: Use @lru_cache on get_settings()
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
```

### Integration Points

```yaml
DATABASE:
  - migration: "alembic revision --autogenerate -m 'description'"
  - apply: "alembic upgrade head"
  - verify: "Check database has new tables/columns"

CONFIG:
  - add to: app/core/config.py
  - pattern: "new_setting: str = Field(default='value')"
  - env var: "NEW_SETTING=value in .env"

ROUTES:
  - add to: app/main.py
  - pattern: "app.include_router(router, prefix='/api')"
```

---

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Run after creating each file - fix before proceeding

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/

# Formatting
uv run ruff format app/

# Expected: Zero errors. If errors exist, READ and fix before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Test each component as created

# Run specific test file
uv run pytest app/core/tests/test_[module].py -v

# Run all unit tests
uv run pytest app/ -v --ignore=app/tests/integration

# Expected: All tests pass. If failing, debug and fix implementation.
```

### Level 3: Integration Testing (System Validation)

```bash
# Test with real database

# Run integration tests
uv run pytest -v -m integration

# Verify database
docker exec -it llm_postgres psql -U postgres -d llm_pipeline -c "\dt"

# Test database migrations
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head

# Expected: All integrations working, migrations apply cleanly
```

### Level 4: Manual Validation

```bash
# Manual verification steps

1. Start FastAPI server (if applicable):
   uv run uvicorn app.main:app --reload

2. Check health endpoint (if applicable):
   curl http://localhost:8123/health

3. Test specific functionality:
   [Session-specific manual tests]

4. Verify Linear issue updated:
   - Check https://linear.app/deepfin/issue/BUD-[X]
   - Status should be "In Progress" → "Done"

# Expected: Manual testing confirms everything works as designed
```

---

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] All tests pass: `uv run pytest app/ -v`
- [ ] No type errors: `uv run mypy app/`
- [ ] No linting errors: `uv run ruff check app/`
- [ ] No formatting issues: `uv run ruff format app/ --check`

### Feature Validation

- [ ] All success criteria from "What" section met
- [ ] All files from session_data.py created
- [ ] All concepts from session_data.py demonstrated in code
- [ ] Integration points work as specified
- [ ] No regressions in existing functionality

### Code Quality Validation

- [ ] Follows existing codebase patterns (config.py, logging.py)
- [ ] File placement matches project structure
- [ ] Naming conventions consistent (snake_case, descriptive)
- [ ] Documentation complete (Google-style docstrings)
- [ ] No hardcoded values (use config instead)

### Session Completion

- [ ] Checkpoint document created in `docs/checkpoints/`
- [ ] Linear issue BUD-[X] updated to "Done"
- [ ] Next session's Linear issue moved to "In Progress"
- [ ] Git commit created with proper message
- [ ] PR created (if using PR workflow)
- [ ] PROGRESS_TRACKER.md updated

---

## Anti-Patterns to Avoid

### For This Project Specifically

- ❌ **Don't skip type hints** - MyPy strict mode enforced
- ❌ **Don't use sync database calls** - Must be async/await
- ❌ **Don't hardcode paths** - Use Pydantic Settings
- ❌ **Don't skip tests** - 80%+ coverage goal
- ❌ **Don't use SQLAlchemy 1.x patterns** - Must use 2.0 style
- ❌ **Don't create new logging patterns** - Follow app/core/logging.py
- ❌ **Don't skip validation levels** - Run all 4 before completing session

### General Anti-Patterns

- ❌ Don't create new patterns when existing ones work
- ❌ Don't skip validation because "it should work"
- ❌ Don't ignore failing tests - fix them
- ❌ Don't catch all exceptions - be specific
- ❌ Don't commit commented-out code
- ❌ Don't use `Any` type without justification

---

## Session Completion Steps

When this session is complete:

1. **Run Final Validation**
   ```bash
   uv run pytest app/ -v
   uv run mypy app/
   uv run ruff check app/
   ```

2. **Create Checkpoint Document**
   ```bash
   # Create docs/checkpoints/CHECKPOINT_0[X]_[SESSION_NAME].md
   # Include: summary, files created, tests passing, learnings, next steps
   ```

3. **Update Tracking**
   - [ ] Update PROGRESS_TRACKER.md (test counts, files created)
   - [ ] Update Linear issue to "Done"
   - [ ] Move next Linear issue to "In Progress"

4. **Git Commit**
   ```bash
   git add .
   git commit -m "Session [X]: [SESSION_NAME]

   - [List key deliverables]
   - Tests: [X]/[X] passing
   - Checkpoint: CHECKPOINT_0[X]_[SESSION_NAME].md

   🤖 Generated with Claude Code

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

5. **Create PR (if using PR workflow)**
   ```bash
   git checkout -b session-0[X]-[feature-name]
   git push origin session-0[X]-[feature-name]
   gh pr create --title "Session [X]: [SESSION_NAME]" \
     --body "Implements PRP #[X]. Closes linear://issue/BUD-[X]"
   ```

---

**Template Version:** 1.0
**Last Updated:** 2025-12-16
**For Project:** LLM Financial Pipeline v2.0
