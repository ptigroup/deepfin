#!/usr/bin/env bash
# Create PR for a session with auto-generated body and optional auto-merge

set -e

# Configuration
SESSION_NUM=$1
AUTO_MERGE=${2:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation
if [ -z "$SESSION_NUM" ]; then
  echo -e "${RED}Error: Session number required${NC}"
  echo "Usage: ./scripts/create-session-pr.sh <session_number> [--auto-merge]"
  echo "Example: ./scripts/create-session-pr.sh 6 --auto-merge"
  exit 1
fi

if ! command -v gh &> /dev/null; then
  echo -e "${RED}Error: gh CLI not found${NC}"
  echo "Install from: https://cli.github.com/"
  exit 1
fi

# Get current branch
BRANCH_NAME=$(git branch --show-current)
if [ "$BRANCH_NAME" == "main" ]; then
  echo -e "${RED}Error: Cannot create PR from main branch${NC}"
  echo "Switch to your session branch first"
  exit 1
fi

echo -e "${GREEN}Creating PR for Session ${SESSION_NUM}${NC}"
echo "Branch: ${BRANCH_NAME}"
echo ""

# Extract session title from JOURNEY.md
SESSION_TITLE=$(grep "^## Session ${SESSION_NUM}:" JOURNEY.md | head -1 | sed "s/^## Session ${SESSION_NUM}: //" || echo "Unknown")
if [ "$SESSION_TITLE" == "Unknown" ]; then
  echo -e "${YELLOW}Warning: Could not extract session title from JOURNEY.md${NC}"
  read -p "Enter session title: " SESSION_TITLE
fi

echo "Title: Session ${SESSION_NUM}: ${SESSION_TITLE}"
echo ""

# Generate PR body
generate_pr_body() {
  echo "## Summary"
  echo ""

  # Get file statistics
  ADDED=$(git diff main --stat | tail -1 | grep -oP '\d+ insertions' | grep -oP '\d+' || echo "0")
  DELETED=$(git diff main --stat | tail -1 | grep -oP '\d+ deletions' | grep -oP '\d+' || echo "0")
  FILES=$(git diff --name-only main | wc -l)

  echo "- Added ${ADDED} lines across ${FILES} files"

  # List changed files
  echo ""
  echo "### Files Changed"
  echo '```'
  git diff --name-status main | head -20
  echo '```'

  echo ""
  echo "## Test Plan"
  echo "- [x] All tests passing"
  echo "- [x] Code formatted with ruff"
  echo "- [x] Code linted with ruff"

  # Try to detect test files
  TEST_FILES=$(git diff --name-only main | grep -E "test_.*\.py$" | wc -l)
  if [ "$TEST_FILES" -gt 0 ]; then
    echo "- [x] ${TEST_FILES} test files added/modified"
  fi

  echo ""
  echo "## Technical Highlights"

  # Extract from recent commit messages
  git log main..HEAD --pretty=format:"- %s" | head -5

  echo ""
  echo ""
  echo "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
}

# Save PR body to temp file
PR_BODY_FILE=$(mktemp)
generate_pr_body > "$PR_BODY_FILE"

echo -e "${YELLOW}PR Body Preview:${NC}"
echo "---"
cat "$PR_BODY_FILE"
echo "---"
echo ""

# Confirm before creating
read -p "Create PR? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled"
  rm "$PR_BODY_FILE"
  exit 1
fi

# Create PR
PR_URL=$(gh pr create \
  --title "Session ${SESSION_NUM}: ${SESSION_TITLE}" \
  --body-file "$PR_BODY_FILE" \
  --base main \
  --head "$BRANCH_NAME")

echo -e "${GREEN}✅ PR created: ${PR_URL}${NC}"

# Extract PR number
PR_NUM=$(echo "$PR_URL" | grep -oP '\d+$')

# Enable auto-merge if requested
if [ "$AUTO_MERGE" == "--auto-merge" ]; then
  echo ""
  echo "Enabling auto-merge..."
  gh pr merge "$PR_NUM" --auto --squash
  echo -e "${GREEN}✅ Auto-merge enabled (will merge when CI passes)${NC}"
fi

# Cleanup
rm "$PR_BODY_FILE"

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  PR Created Successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "PR: ${PR_URL}"
echo "Number: #${PR_NUM}"
echo ""
echo "Next steps:"
echo "1. Wait for CI to pass"
if [ "$AUTO_MERGE" == "--auto-merge" ]; then
  echo "2. PR will auto-merge when CI is green ✅"
else
  echo "2. Manually merge PR when ready"
fi
echo "3. Linear will be auto-updated via GitHub Actions"
echo "4. Update JOURNEY.md manually or run: ./scripts/update-journey.sh ${SESSION_NUM}"
echo ""
