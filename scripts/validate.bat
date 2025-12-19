@echo off
REM Pre-commit validation script for Windows
REM Run this before committing to catch issues early

echo.
echo Running pre-commit validation...
echo.

REM 1. Ruff linting (with auto-fix)
echo Step 1/5: Ruff linting...
uv run ruff check app/ tests/ --fix
if errorlevel 1 (
    echo ERROR: Linting failed
    exit /b 1
)
echo OK: Linting passed
echo.

REM 2. Ruff formatting
echo Step 2/5: Ruff formatting...
uv run ruff format app/ tests/
if errorlevel 1 (
    echo ERROR: Formatting failed
    exit /b 1
)
echo OK: Formatting complete
echo.

REM 3. Type checking (MyPy) - non-blocking
echo Step 3/5: Type checking...
uv run mypy app/
echo.

REM 4. Unit tests
echo Step 4/5: Unit tests...
uv run pytest app/ -v --ignore=app/tests/integration -x
echo.

REM 5. Integration tests
echo Step 5/5: Integration tests...
uv run pytest tests/ -v -x
echo.

echo.
echo ========================================
echo    Validation complete!
echo ========================================
echo.
echo If all checks passed, you're ready to commit and push!
echo.
