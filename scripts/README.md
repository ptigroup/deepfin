# Validation Scripts

These scripts help catch issues **before** pushing to GitHub, saving time and avoiding CI failures.

## 🚀 Quick Usage

**Before every commit:**
```powershell
# Windows
.\scripts\validate.bat

# Or on Unix/Mac
bash scripts/validate.sh
```

**During development (fast feedback):**
```powershell
# Windows
.\scripts\quick-check.bat

# Or on Unix/Mac
bash scripts/quick-check.sh
```

## 📋 What Each Script Does

### `validate.bat` / `validate.sh` - Full Validation

Runs the **complete validation suite** that matches CI:

1. **Ruff Linting** - Checks code quality, auto-fixes issues
2. **Ruff Formatting** - Ensures consistent code style
3. **MyPy Type Checking** - Validates type hints
4. **Unit Tests** - Runs all unit tests
5. **Integration Tests** - Tests database integration

**When to use:** Before committing and pushing

**Time:** ~1-2 minutes (depending on test suite size)

### `quick-check.bat` / `quick-check.sh` - Fast Checks

Runs **only linting and formatting**:

1. **Ruff Linting** - Auto-fixes code quality issues
2. **Ruff Formatting** - Formats code

**When to use:** During development, after writing code

**Time:** ~5-10 seconds

## 🎯 Recommended Workflow

```
Write code
    ↓
Run: .\scripts\quick-check.bat  ← Fast feedback
    ↓
Continue coding / fix issues
    ↓
Ready to commit?
    ↓
Run: .\scripts\validate.bat     ← Full validation
    ↓
All checks pass?
    ↓
git add . && git commit -m "..."
    ↓
git push
```

## ❌ Why We Need This

**The Problem We Had (Sessions 1-3):**

- Write code → commit → push → **CI fails** → fix → push again
- Wasted time waiting for CI
- Multiple commits to fix simple formatting issues

**With Validation Scripts:**

- Write code → **validate locally** → commit → push → **CI passes** ✅
- Catch issues in 10 seconds instead of 2 minutes
- Clean git history with fewer "fix linting" commits

## 🔧 Advanced: Pre-Commit Hooks (Optional)

To **automatically** run validation before every commit, we can set up pre-commit hooks.

This would **prevent** commits if validation fails.

Ask if you want to set this up!

## 📚 What Each Check Does

### Ruff Linting (`ruff check`)

Catches:
- Unused imports
- Undefined variables
- Style violations (PEP 8)
- Code smells
- Complexity issues

Auto-fixes most issues with `--fix` flag.

### Ruff Formatting (`ruff format`)

Ensures:
- Consistent indentation
- Proper line lengths
- Correct quote styles
- Clean spacing

Automatically reformats code.

### MyPy Type Checking (`mypy`)

Validates:
- Type hints are correct
- Function signatures match
- No type mismatches
- Proper async/await usage

Helps catch bugs before runtime.

### Pytest (`pytest`)

Runs:
- Unit tests (fast, isolated)
- Integration tests (slower, database required)

Ensures code works as expected.

## 🎓 Key Takeaway

**CI should confirm, not discover.**

- ✅ Use these scripts to **discover** issues locally
- ✅ Let CI **confirm** everything is correct
- ❌ Don't let CI be your first line of defense

---

**Quick Reference:**

```powershell
# During development
.\scripts\quick-check.bat

# Before committing
.\scripts\validate.bat

# If all passes, commit and push!
git add .
git commit -m "Your message"
git push
```
