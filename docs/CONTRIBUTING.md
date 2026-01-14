# Contributing to LLM Financial Pipeline v2.0

Welcome! This document explains how to contribute to the project using our PRP-driven development workflow.

## 📋 Overview

This project uses a structured 18-session development approach with:
- **PRPs (Pull Request Proposals)** - Specifications before implementation
- **Linear Integration** - Automated issue tracking
- **GitHub Actions** - Automated reviews and validation
- **4-Level Validation** - Comprehensive quality checks

## 🚀 Quick Start for Contributors

### 1. Set Up Your Environment

```bash
# Clone repository
git clone https://github.com/ptigroup/deepfin.git
cd deepfin

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Start PostgreSQL
docker-compose up -d

# Verify setup
uv run pytest app/ -v
```

### 2. Understanding the Workflow

Our workflow follows this pattern:

```
PRP Created → Branch → Implement → Test → PR → Review → Merge → Linear Update
```

**For Each Session:**
1. Read the PRP document (`docs/PRPs/session_XX.md`)
2. Create feature branch
3. Implement following PRP blueprint
4. Run 4-level validation
5. Create PR using template
6. Request @claude-review
7. Address feedback
8. Merge (auto-updates Linear)

## 📖 Detailed Workflow

### Step 1: Read the PRP

Before starting any session, read the corresponding PRP:

```bash
# PRPs are in docs/PRPs/
# Example: docs/PRPs/session_02_database_models.md
```

**PRP Contains:**
- Goal and deliverables
- Implementation blueprint (ordered tasks)
- Validation requirements
- Anti-patterns to avoid

### Step 2: Create Feature Branch

```bash
# Create branch from main
git checkout main
git pull origin main

# Create feature branch
# Format: session-XX-feature-name
git checkout -b session-02-database-models
```

### Step 3: Implement Following PRP

**Implementation Order:**
1. Create files in order specified in PRP
2. Run validation after each file
3. Follow existing patterns (config.py, logging.py)
4. Write tests as you go

**Critical Rules:**
- Use async/await for all database operations
- Add type hints (MyPy strict mode)
- Follow Google-style docstrings
- No hardcoded values (use Settings)
- Inherit TimestampMixin on models

### Step 4: Run 4-Level Validation

**Level 1: Syntax & Style**
```bash
uv run mypy app/
uv run ruff check app/
uv run ruff format app/
```

**Level 2: Unit Tests**
```bash
uv run pytest app/ -v --ignore=app/tests/integration
```

**Level 3: Integration Tests**
```bash
uv run pytest -v -m integration
```

**Level 4: Manual Validation**
- Test key functionality manually
- Verify database migrations work
- Check API endpoints (if applicable)

**All levels must pass before creating PR.**

### Step 5: Create Pull Request

```bash
# Commit your changes
git add .
git commit -m "Session X: [Session Name]

- [Key deliverable 1]
- [Key deliverable 2]
- Tests: X/X passing

🤖 Generated with Claude Code"

# Push to GitHub
git push origin session-XX-feature-name

# Create PR
gh pr create --title "Session X: [Session Name]" \
  --body "Implements PRP #X. Closes linear://issue/BUD-X"
```

**Or use GitHub UI:**
1. Go to repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill in PR template (auto-populated)

### Step 6: Request Code Review

**Automated Review:**
```
# Comment on your PR:
@claude-review
```

This triggers GitHub Actions to:
- Review all code changes
- Check PRP compliance
- Validate tests and coverage
- Post detailed feedback

**Human Review:**
- Tag team members
- Address feedback
- Update code as needed

### Step 7: Address Feedback

If reviewers request changes:
```bash
# Make changes
# Re-run validation (all 4 levels)

# Commit fixes
git add .
git commit -m "Address review feedback: [what was fixed]"
git push origin session-XX-feature-name

# Request re-review
# Comment on PR: "Ready for re-review @username"
```

### Step 8: Merge

When approved:
1. Ensure all checks passing (GitHub Actions)
2. Ensure all review comments resolved
3. Click "Merge pull request"

**Auto-magic happens:**
- Linear issue updated to "Done"
- Next Linear issue moved to "In Progress"
- Checkpoint document auto-generated
- Tracking files notified

## 📁 Project Structure

```
├── app/                        # Main application
│   ├── core/                   # Core infrastructure
│   │   ├── config.py          # Pydantic Settings
│   │   ├── logging.py         # Structured logging
│   │   └── database.py        # Async SQLAlchemy
│   ├── shared/                 # Shared utilities
│   │   ├── models.py          # TimestampMixin
│   │   └── schemas.py         # Base schemas
│   └── [features]/             # Feature modules (future)
│
├── docs/                       # Documentation
│   ├── PRPs/                   # Pull Request Proposals
│   │   ├── templates/          # PRP templates
│   │   └── session_XX.md       # Session specifications
│   └── checkpoints/            # Session checkpoints
│
├── .github/                    # GitHub configuration
│   ├── workflows/              # GitHub Actions
│   │   ├── claude-review.yml   # Automated code review
│   │   ├── linear-sync.yml     # Linear integration
│   │   ├── validation.yml      # Test runner
│   │   └── checkpoint-generator.yml
│   └── pull_request_template.md
│
├── CLAUDE.md                   # AI assistant guide
├── CONTRIBUTING.md             # This file
└── session_data.py             # Session metadata
```

## 🧪 Testing Guidelines

### Writing Tests

**Test File Location:**
- Unit tests: `app/MODULE/tests/test_FILE.py`
- Integration tests: `app/tests/integration/`

**Test Naming:**
```python
def test_feature_happy_path():
    """Test normal operation."""

def test_feature_edge_case_empty_input():
    """Test edge case with empty input."""

def test_feature_error_invalid_data():
    """Test error handling with invalid data."""
```

**Integration Test Marker:**
```python
@pytest.mark.integration
async def test_database_connection():
    """Integration test requiring real database."""
```

### Running Tests

```bash
# All tests
uv run pytest app/ -v

# Specific module
uv run pytest app/core/tests/test_database.py -v

# Integration only
uv run pytest -v -m integration

# With coverage
uv run pytest app/ -v --cov=app --cov-report=term-missing
```

## 🔧 Development Patterns

### Configuration Pattern

```python
from app.core.config import get_settings

settings = get_settings()  # Singleton
database_url = settings.database_url
```

### Logging Pattern

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("feature.action_started", user_id=123)
logger.error("feature.action_failed", exc_info=True)
```

### Database Pattern

```python
from app.core.database import Base, get_db
from app.shared.models import TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"
    # ... fields

# In FastAPI route:
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### Schema Pattern

```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
```

## ❌ Anti-Patterns to Avoid

### Code Anti-Patterns
- ❌ Sync database calls (must use async/await)
- ❌ Missing type hints
- ❌ Hardcoded values (use Settings)
- ❌ Catching all exceptions without logging
- ❌ SQLAlchemy 1.x patterns (use 2.0)

### Workflow Anti-Patterns
- ❌ Skipping validation levels
- ❌ Creating PR without reading PRP
- ❌ Committing without running tests
- ❌ Ignoring @claude-review feedback
- ❌ Merging with failing checks

## 🔗 Helpful Links

### Project Resources
- [Progress Tracker](PROGRESS_TRACKER.md) - Overall progress
- [Session Manifest](SESSION_MANIFEST.md) - All 18 sessions
- [Linear Project](https://linear.app/deepfin/project/deep-fin-17d251686130)

### Documentation
- [CLAUDE.md](CLAUDE.md) - AI assistant guide
- [PRPs](docs/PRPs/) - Implementation specs
- [Checkpoints](docs/checkpoints/) - Session summaries

### External Resources
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic](https://docs.pydantic.dev/)
- [Alembic](https://alembic.sqlalchemy.org/)

## 💬 Getting Help

### Questions About:
- **Workflow:** Read this CONTRIBUTING.md again
- **Session Requirements:** Check the PRP document
- **Code Patterns:** Look at existing code (config.py, logging.py)
- **Test Requirements:** Check PRP validation section

### Still Stuck?
1. Check Linear issue comments
2. Review related checkpoint documents
3. Ask in PR comments
4. Tag @claude-review for AI assistance

## 🎯 Session Checklist

Before marking session complete:

**Implementation:**
- [ ] All files from PRP created
- [ ] All tasks from PRP completed
- [ ] Follows existing patterns
- [ ] No anti-patterns

**Testing:**
- [ ] All 4 validation levels passed
- [ ] All tests passing (XX/XX)
- [ ] Coverage adequate (80%+ goal)
- [ ] Manual testing done

**Documentation:**
- [ ] Checkpoint created
- [ ] PROGRESS_TRACKER updated
- [ ] Linear issue updated
- [ ] PR description complete

**Quality:**
- [ ] Code reviewed
- [ ] Feedback addressed
- [ ] No known issues
- [ ] Ready for next session

## 📊 Progress Tracking

Track project progress in multiple places:

1. **Linear:** https://linear.app/deepfin/project/deep-fin-17d251686130
   - Real-time issue status
   - Team collaboration
   - Comments and updates

2. **GitHub:** PROGRESS_TRACKER.md
   - Detailed metrics
   - Test coverage
   - File counts

3. **Checkpoints:** docs/checkpoints/
   - Session summaries
   - Key learnings
   - What's ready for next

## 🤝 Code Review Guidelines

### For Reviewers

**Check:**
1. PRP compliance (all requirements met)
2. Code quality (type hints, docstrings, patterns)
3. Tests (comprehensive, passing, coverage)
4. Documentation (checkpoint, tracking files)
5. No anti-patterns

**Provide:**
- Constructive feedback
- Specific suggestions
- Reference to existing patterns
- Appreciation for good work

### For Authors

**Respond to:**
- All review comments
- Run validation after fixes
- Update PR description if needed
- Request re-review when ready

## 🚢 Release Process

(To be defined in Session 18: Deployment & CI/CD)

---

**Version:** 1.0
**Last Updated:** 2025-12-16
**Maintained By:** Project Team + Claude Sonnet 4.5

---

_🤖 This workflow is optimized for AI-assisted development with Claude Code._
_For questions about this process, check CLAUDE.md or PRPs/templates/._
