#!/bin/bash
# Quick validation - just linting and formatting
# Use this during development for fast feedback

echo ""
echo "🔍 Running quick checks (linting + formatting)..."
echo ""

echo "📋 Checking code style..."
uv run ruff check app/ tests/ --fix

echo ""
echo "🎨 Checking formatting..."
uv run ruff format app/ tests/

echo ""
echo "✅ Quick checks complete!"
echo "💡 Run 'bash scripts/validate.sh' for full validation before committing."
echo ""
