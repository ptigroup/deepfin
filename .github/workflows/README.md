# GitHub Actions Workflows

This directory contains automated workflows for the LLM Financial Pipeline v2.0 project.

## 🤖 Available Workflows

### 1. Claude Code Review (`claude-review.yml`)

**Trigger:** Comment `@claude-review` on any PR
**Purpose:** Automated AI code review using Claude Code

**What it does:**
- Reviews all code changes in the PR
- Checks PRP (Pull Request Proposal) compliance
- Validates code quality and patterns
- Checks test coverage
- Posts detailed review comments

**Requirements:**
- `CLAUDE_CODE_OAUTH_TOKEN` secret configured
- PR must have associated PRP document

**Example:**
```
# In PR comment:
@claude-review
```

---

### 2. Linear Sync (`linear-sync.yml`)

**Trigger:** PR merged to main
**Purpose:** Automatically update Linear issues when sessions complete

**What it does:**
- Extracts session number from PR title
- Updates Linear issue to "Done"
- Adds comment with PR link and completion date
- Moves next session to "In Progress"

**Requirements:**
- `LINEAR_API_KEY` secret configured
- PR title must follow format: `Session X: [Name]`

**Example PR Title:**
```
Session 2: Database & Shared Models
```

**Auto-updates:**
- BUD-6 → "Done" (with comment)
- BUD-7 → "In Progress"

---

### 3. Validation (`validation.yml`)

**Trigger:** PR opened/updated or push to main
**Purpose:** Run comprehensive validation suite

**What it does:**
- Runs MyPy type checking
- Runs Ruff linting
- Checks code formatting
- Runs all unit tests
- Runs integration tests
- Generates coverage report

**Services Used:**
- PostgreSQL 16 (test database)

**Artifacts:**
- HTML coverage report (7-day retention)

**Validation Levels:**
1. **Syntax & Style:** MyPy, Ruff
2. **Unit Tests:** Pytest (unit tests only)
3. **Integration Tests:** Pytest (integration tests)
4. **Coverage:** HTML report uploaded

**Requirements:**
- All checks must pass to merge

---

### 4. Checkpoint Generator (`checkpoint-generator.yml`)

**Trigger:** PR merged to main
**Purpose:** Auto-generate checkpoint document template

**What it does:**
- Extracts session info from PR
- Generates checkpoint template
- Pre-fills known information (date, PR link, commit hash)
- Commits checkpoint to `docs/checkpoints/`

**Requirements:**
- PR title must follow format: `Session X: [Name]`

**Generated File:**
```
docs/checkpoints/CHECKPOINT_XX_session_name.md
```

**Template includes:**
- Session summary (to be filled)
- Files created/modified (to be filled)
- Test results (partially auto-filled)
- Key learnings (to be filled)
- Validation checklist (auto-filled)

**Note:** Template requires manual completion of some sections.

---

## 🔧 Configuration

### GitHub Secrets Required

Add these in: `Settings → Secrets and variables → Actions`

| Secret Name | Purpose | How to Get |
|-------------|---------|------------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code review automation | https://claude.ai/settings/oauth |
| `LINEAR_API_KEY` | Linear issue sync | Linear Settings → API |

### Environment Variables

Workflows use these environment variables (automatically set):

- `DATABASE_URL` - Test database connection (PostgreSQL service)
- `SECRET_KEY` - Test secret key (not for production)
- `LLMWHISPERER_API_KEY` - Test API key
- `DATABASE_ECHO` - SQL query logging (false)

## 📋 Workflow Dependencies

```mermaid
graph TD
    A[PR Created] --> B[Validation]
    B --> C{Tests Pass?}
    C -->|Yes| D[Ready for Review]
    C -->|No| E[Fix Issues]
    E --> B
    D --> F[@claude-review Comment]
    F --> G[Claude Review]
    G --> H{Approved?}
    H -->|Yes| I[Merge PR]
    H -->|No| E
    I --> J[Linear Sync]
    I --> K[Checkpoint Generator]
```

## 🎯 Best Practices

### For PR Authors

1. **Before Creating PR:**
   - Run validation locally first
   - Ensure all tests pass
   - Create from PRP document

2. **PR Title Format:**
   - Use: `Session X: Description`
   - Example: `Session 2: Database & Shared Models`
   - This enables Linear sync and checkpoint generation

3. **Request Review:**
   - Comment `@claude-review` for AI review
   - Tag human reviewers if needed

4. **After Merge:**
   - Verify Linear issue updated
   - Complete checkpoint template (auto-generated)
   - Check PROGRESS_TRACKER.md

### For Reviewers

1. **Use @claude-review:**
   - Let AI do first pass review
   - Focus on architecture and design
   - Verify PRP compliance

2. **Check Workflow Status:**
   - Ensure validation workflow passed
   - Review coverage report
   - Verify no security issues

3. **Approve When:**
   - All checks green
   - Code quality excellent
   - Tests comprehensive
   - Documentation complete

## 🐛 Troubleshooting

### Validation Fails

**Problem:** Validation workflow fails

**Solutions:**
```bash
# Run validation locally first:
uv run mypy app/
uv run ruff check app/
uv run pytest app/ -v
```

**Common Issues:**
- Type errors (add type hints)
- Linting errors (run `ruff check app/ --fix`)
- Test failures (check test output)

### Linear Sync Doesn't Trigger

**Problem:** PR merged but Linear not updated

**Causes:**
1. PR title doesn't match `Session X:` format
2. `LINEAR_API_KEY` secret not configured
3. Session number invalid (not 1-18)

**Solutions:**
- Check workflow run logs
- Verify PR title format
- Ensure secrets configured

### Claude Review Doesn't Work

**Problem:** @claude-review comment doesn't trigger

**Causes:**
1. `CLAUDE_CODE_OAUTH_TOKEN` not configured
2. Comment format incorrect
3. Permissions issue

**Solutions:**
- Verify secret configured
- Comment exactly: `@claude-review`
- Check workflow permissions

### Checkpoint Not Generated

**Problem:** No checkpoint file after merge

**Causes:**
1. PR title format incorrect
2. Workflow failed
3. Git push permission issue

**Solutions:**
- Check workflow run logs
- Verify PR title format: `Session X: Name`
- Check repository permissions

## 📊 Workflow Status

View workflow status:
- **GitHub UI:** Actions tab
- **PR Checks:** Bottom of PR page
- **Status Badge:** (To be added)

## 🔗 Related Documentation

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Development workflow
- [CLAUDE.md](../../CLAUDE.md) - AI assistant guide
- [PRPs](../../docs/PRPs/) - Session specifications

---

**Workflow Version:** 1.0
**Last Updated:** 2025-12-16
**Maintained By:** DevOps Team + Claude Sonnet 4.5
