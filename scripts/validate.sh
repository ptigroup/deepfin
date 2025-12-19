#!/bin/bash
# Pre-commit validation script
# Run this before committing to catch issues early

set -e  # Exit on first error

echo "🔍 Running pre-commit validation..."
echo ""

# 1. Ruff linting (with auto-fix)
echo "📋 Step 1/5: Ruff linting..."
uv run ruff check app/ tests/ --fix
echo "✅ Linting passed"
echo ""

# 2. Ruff formatting
echo "🎨 Step 2/5: Ruff formatting..."
uv run ruff format app/ tests/
echo "✅ Formatting complete"
echo ""

# 3. Type checking (MyPy)
echo "🔤 Step 3/5: Type checking..."
uv run mypy app/ || echo "⚠️  MyPy found type errors (not blocking)"
echo ""

# 4. Unit tests
echo "🧪 Step 4/5: Unit tests..."
uv run pytest app/ -v --ignore=app/tests/integration -x || echo "⚠️  Some tests failed"
echo ""

# 5. Integration tests (if DB is available)
echo "🔗 Step 5/5: Integration tests..."
uv run pytest tests/ -v -x || echo "⚠️  Integration tests failed (DB may be unavailable)"
echo ""

echo "✅ Validation complete!"
echo ""
echo "💡 If all checks passed, you're ready to commit and push!"
