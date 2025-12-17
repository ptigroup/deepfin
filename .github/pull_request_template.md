# Pull Request: [Session Name]

## Summary
<!-- Brief description of what this PR accomplishes -->

**Session:** [Session Number]
**PRP Document:** [Link to docs/PRPs/session_XX.md]
**Linear Issue:** [Link to Linear issue BUD-X]

## Changes Made
<!-- List the main changes in this PR -->
-
-
-

## Files Created/Modified
<!-- Auto-filled from commit or manual -->
**Total:** X files

### New Files
- `app/file1.py` - [Purpose]
- `app/file2.py` - [Purpose]

### Modified Files
- `existing_file.py` - [What changed]

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] New feature (Session implementation)
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring
- [ ] Infrastructure/tooling

## Testing
<!-- Describe how you tested your changes -->

### Test Results
**Tests Written:** [X] new tests
**Tests Passing:** [X]/[X] (100%)
**Total Project Tests:** [X]/[X]

### Test Evidence
```bash
# Example test commands run
uv run pytest app/ -v
# Output: X passed in Y.Ys

uv run mypy app/
# Output: Success: no issues found

uv run ruff check app/
# Output: All checks passed
```

### Coverage
- Unit tests: [X]/[X] passing
- Integration tests: [X]/[X] passing
- Code coverage: [XX]%

## PRP Compliance
<!-- Verify PRP requirements met -->

### Success Criteria from PRP
- [ ] [Criterion 1 from PRP]
- [ ] [Criterion 2 from PRP]
- [ ] [Criterion 3 from PRP]
- [ ] All tests passing
- [ ] Checkpoint document created

### Implementation Blueprint
- [ ] All tasks from PRP completed
- [ ] Followed existing patterns
- [ ] No anti-patterns introduced

## Validation Checklist
<!-- Mark completed items with an "x" -->

### Level 1: Syntax & Style
- [ ] MyPy type checking passes (`uv run mypy app/`)
- [ ] Ruff linting passes (`uv run ruff check app/`)
- [ ] Ruff formatting passes (`uv run ruff format app/ --check`)

### Level 2: Unit Tests
- [ ] All new unit tests passing
- [ ] Existing tests still pass
- [ ] Edge cases covered

### Level 3: Integration Tests
- [ ] Integration tests passing (if applicable)
- [ ] Database migrations work (if applicable)
- [ ] API endpoints work (if applicable)

### Level 4: Manual Validation
- [ ] Manually tested key functionality
- [ ] Verified no regressions
- [ ] Tested error handling

## Code Quality
<!-- Ensure code quality standards -->
- [ ] Code follows project patterns (config.py, logging.py style)
- [ ] Google-style docstrings on all public functions
- [ ] Type hints complete (no `Any` without justification)
- [ ] No hardcoded values (uses Settings)
- [ ] Error handling proper (specific exceptions, logging)
- [ ] No commented-out code

## Database Changes
<!-- If this PR includes database changes -->
- [ ] Migration created (`alembic revision --autogenerate`)
- [ ] Migration tested (upgrade/downgrade)
- [ ] Uses TimestampMixin on models
- [ ] Async SQLAlchemy 2.0 patterns used

## Documentation
<!-- Ensure documentation is updated -->
- [ ] Checkpoint document created (`docs/checkpoints/CHECKPOINT_XX.md`)
- [ ] PROGRESS_TRACKER.md updated
- [ ] Linear issue updated to "Done"
- [ ] README updated (if needed)
- [ ] CLAUDE.md updated (if patterns changed)

## Breaking Changes
<!-- If this PR introduces breaking changes, describe them here -->
<!-- Include migration steps if applicable -->

N/A

## Session Completion
<!-- Final checklist for session completion -->
- [ ] All acceptance criteria from session_data.py met
- [ ] All concepts from session_data.py demonstrated
- [ ] Ready for next session to begin
- [ ] No known issues or blockers

## Additional Notes
<!-- Any additional information that reviewers should know -->
<!-- Screenshots, performance metrics, dependencies added, etc. -->

---

## Reviewer Checklist
<!-- For code reviewers -->
- [ ] PRP requirements verified
- [ ] Code quality standards met
- [ ] Tests comprehensive and passing
- [ ] Documentation complete
- [ ] No security issues
- [ ] Ready to merge

---

**🤖 Ready for @claude-review**
Comment `@claude-review` to trigger automated code review

**🔗 Links:**
- PRP: [Link to PRP document]
- Linear: [Link to Linear issue]
- Checkpoint: [Link to checkpoint when created]
