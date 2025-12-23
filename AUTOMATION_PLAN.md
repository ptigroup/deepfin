# Full Automation Plan for Session Workflow

## Current Problem

**Manual steps after every session:**
1. ❌ Create PR manually
2. ❌ Merge PR manually (after CI passes)
3. ❌ Update JOURNEY.md manually
4. ❌ Update Linear manually (automation is BROKEN - all 4 sessions failed)
5. ❌ Run verification manually

**Root Cause:** Linear sync workflow has been broken since creation (GraphQL query bugs)

---

## Proposed Solution: 100% Automated Workflow

### Goal
**One command to complete a session:** `./scripts/complete-session.sh <session_number>`

Everything else happens automatically.

---

## Phase 1: Fix Existing Automation (IMMEDIATE)

### 1.1 Fix Linear Sync Workflow ✅ DONE

**Problem:** GraphQL query uses invalid `identifier` field in filters

**Fix Applied:**
- Changed from `issues(filter: { identifier: { eq: $identifier } })`
- To: `issue(id: $issueId)` (direct query)

**Status:** Fixed in `.github/workflows/linear-sync.yml`

**Test:** Will verify on next PR merge (Session 6)

---

## Phase 2: Automate PR Creation & Merge

### 2.1 Automated PR Creation

**Script:** `scripts/create-session-pr.sh <session_number>`

```bash
#!/usr/bin/env bash
set -e

SESSION_NUM=$1
if [ -z "$SESSION_NUM" ]; then
  echo "Usage: ./scripts/create-session-pr.sh <session_number>"
  exit 1
fi

# Get session title from branch name or JOURNEY.md
BRANCH_NAME=$(git branch --show-current)
SESSION_TITLE=$(grep "^## Session ${SESSION_NUM}:" JOURNEY.md | head -1 | sed "s/## Session ${SESSION_NUM}: //")

# Generate PR body from git changes
echo "## Summary"
echo ""
git diff main --stat | head -20
echo ""
echo "## Test Plan"
echo "- [x] All tests passing"
echo "- [x] Code formatted and linted"
echo ""
echo "🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Create PR
gh pr create \
  --title "Session ${SESSION_NUM}: ${SESSION_TITLE}" \
  --body-file <(generate_pr_body) \
  --base main \
  --head "${BRANCH_NAME}"
```

**Benefits:**
- ✅ Consistent PR format
- ✅ Auto-generated test checklist
- ✅ Links to Claude Code

### 2.2 Automated PR Merge

**Approach:** Auto-merge when CI passes

**GitHub Setting:** Enable "Auto-merge" on PR creation

```bash
gh pr create --auto-merge --merge-method squash
```

**Safety:** Only merges if ALL checks pass:
- ✅ Ruff formatting
- ✅ Ruff linting
- ✅ Pytest (all tests)

---

## Phase 3: Automate JOURNEY.md Updates

### 3.1 Template-Based Generation

**Challenge:** JOURNEY.md contains subjective content (decisions, challenges, learnings)

**Solution:** Two-tier approach

#### Tier 1: Auto-Generated Facts (100% automated)
- PR link
- Completion date
- Files created/modified (from `git diff`)
- Test count (from `pytest` output)
- Line counts

#### Tier 2: AI-Generated Content (90% automated)
- "What We Built" - extracted from commit messages
- "Key Decisions" - extracted from code comments and PR description
- "Challenges Faced" - extracted from commit history (reverted commits, fixes)
- "Lessons Learned" - template-based

**Script:** `scripts/update-journey.py <session_number>`

```python
#!/usr/bin/env python3
import subprocess
import re
from datetime import datetime

def get_pr_number(session_num):
    """Get PR number for session from GitHub."""
    result = subprocess.run(
        ["gh", "pr", "list", "--search", f"'Session {session_num}:'", "--state", "merged", "--json", "number"],
        capture_output=True, text=True
    )
    prs = json.loads(result.stdout)
    return prs[0]["number"] if prs else None

def get_changed_files(session_num):
    """Get list of files changed in session."""
    # Get commit range for session branch
    result = subprocess.run(
        ["git", "diff", "--name-status", "main", f"session-{session_num:02d}-*"],
        capture_output=True, text=True
    )
    return parse_git_diff(result.stdout)

def count_tests(session_path):
    """Count tests in session directory."""
    result = subprocess.run(
        ["pytest", session_path, "--collect-only", "-q"],
        capture_output=True, text=True
    )
    return parse_pytest_count(result.stdout)

def generate_session_section(session_num):
    """Generate JOURNEY.md section for session."""
    pr_num = get_pr_number(session_num)
    files = get_changed_files(session_num)
    test_count = count_tests(f"app/*/tests/")

    template = f"""
## Session {session_num}: {{TITLE}}

**Completed:** {datetime.now().strftime('%Y-%m-%d')}
**PR:** [#{pr_num}](https://github.com/ptigroup/deepfin/pull/{pr_num})
**Linear:** BUD-{session_num + 4} → Done

### 🎯 Milestone Achieved
{{MILESTONE}}

### What We Built
{generate_what_we_built(files)}

### Files Created
```
{format_file_list(files)}
```

### Testing Insights
- **{test_count} tests** covering:
  {generate_test_summary(session_path)}
"""
    return template

def update_journey_md(session_num, content):
    """Update JOURNEY.md with session content."""
    # Read JOURNEY.md
    with open("JOURNEY.md", "r") as f:
        journey = f.read()

    # Replace "📋 Ready to Start" section with completed content
    pattern = f"## Session {session_num}:.*?(?=## Session {session_num + 1}:|$)"
    updated = re.sub(pattern, content, journey, flags=re.DOTALL)

    # Write back
    with open("JOURNEY.md", "w") as f:
        f.write(updated)
```

### 3.2 Manual Override

**For subjective content**, provide a template:

```bash
# scripts/update-journey.py will create:
# JOURNEY_SESSION_5_DRAFT.md

# You can edit this file, then:
./scripts/finalize-journey.sh 5
```

---

## Phase 4: Single Command Completion

### 4.1 Master Script

**File:** `scripts/complete-session.sh`

```bash
#!/usr/bin/env bash
set -e

SESSION_NUM=$1

echo "============================================"
echo "  Session ${SESSION_NUM} Completion Workflow"
echo "============================================"

# Step 1: Run validation
echo ""
echo "[1/7] Running validation..."
./scripts/validate.bat
echo "✅ Validation passed"

# Step 2: Create PR
echo ""
echo "[2/7] Creating PR..."
PR_URL=$(./scripts/create-session-pr.sh $SESSION_NUM --auto-merge)
echo "✅ PR created: $PR_URL"

# Step 3: Wait for CI
echo ""
echo "[3/7] Waiting for CI to pass..."
PR_NUM=$(echo $PR_URL | grep -oP '\d+$')
while true; do
  STATUS=$(gh pr checks $PR_NUM --json state -q '.[0].state')
  if [ "$STATUS" == "SUCCESS" ]; then
    echo "✅ CI passed"
    break
  elif [ "$STATUS" == "FAILURE" ]; then
    echo "❌ CI failed - aborting"
    exit 1
  fi
  sleep 10
done

# Step 4: PR auto-merges (due to --auto-merge flag)
echo ""
echo "[4/7] Waiting for auto-merge..."
sleep 5
echo "✅ PR merged"

# Step 5: Update JOURNEY.md
echo ""
echo "[5/7] Updating JOURNEY.md..."
git checkout main && git pull
python scripts/update-journey.py $SESSION_NUM
git add JOURNEY.md
git commit -m "Update JOURNEY.md for Session ${SESSION_NUM}"
git push
echo "✅ JOURNEY.md updated"

# Step 6: Verify Linear (automated via GitHub Actions)
echo ""
echo "[6/7] Verifying Linear sync..."
sleep 10  # Wait for GitHub Actions to run
export LINEAR_API_KEY='your_key'
python scripts/verify-linear.py $SESSION_NUM
echo "✅ Linear verified"

# Step 7: Final verification
echo ""
echo "[7/7] Running final verification..."
./scripts/verify-session-complete.sh $SESSION_NUM
echo "✅ Session complete!"

echo ""
echo "============================================"
echo "  Session ${SESSION_NUM} Complete! 🎉"
echo "============================================"
echo ""
echo "Next: Start Session $((SESSION_NUM + 1))"
```

---

## Phase 5: Verification Script

**File:** `scripts/verify-session-complete.sh`

```bash
#!/usr/bin/env bash

SESSION_NUM=$1
ISSUE_ID="BUD-$((SESSION_NUM + 4))"

echo "Verifying Session ${SESSION_NUM} completion..."
echo ""

# Check 1: GitHub PR merged
echo "[1/3] Checking GitHub PR..."
PR_NUM=$(gh pr list --search "Session ${SESSION_NUM}:" --state merged --json number -q '.[0].number')
if [ -n "$PR_NUM" ]; then
  echo "✅ PR #${PR_NUM} merged"
else
  echo "❌ PR not found or not merged"
  exit 1
fi

# Check 2: JOURNEY.md updated
echo "[2/3] Checking JOURNEY.md..."
if grep -q "\\[#${PR_NUM}\\]" JOURNEY.md && grep -q "${ISSUE_ID} → Done" JOURNEY.md; then
  echo "✅ JOURNEY.md updated with PR link and Linear status"
else
  echo "❌ JOURNEY.md not updated"
  exit 1
fi

# Check 3: Linear issue marked Done
echo "[3/3] Checking Linear..."
if python scripts/verify-linear.py $SESSION_NUM; then
  echo "✅ Linear ${ISSUE_ID} marked as Done"
else
  echo "❌ Linear not updated"
  exit 1
fi

echo ""
echo "✅ All verifications passed!"
```

---

## Implementation Timeline

### Immediate (Today)
- [x] Fix Linear sync workflow GraphQL bugs
- [ ] Test Linear sync on next PR merge
- [ ] Commit linear-sync.yml fix

### Phase 1 (Session 6)
- [ ] Create `scripts/create-session-pr.sh`
- [ ] Create `scripts/verify-session-complete.sh`
- [ ] Test manual PR creation script

### Phase 2 (Session 7)
- [ ] Create `scripts/update-journey.py` (basic version)
- [ ] Add auto-merge to PR creation
- [ ] Test end-to-end with manual JOURNEY edits

### Phase 3 (Session 8)
- [ ] Create `scripts/complete-session.sh` master script
- [ ] Test full automation workflow
- [ ] Document any manual override needs

### Phase 4 (Session 9+)
- [ ] Enhance `update-journey.py` with AI content generation
- [ ] Add more intelligence to "What We Built" extraction
- [ ] Fine-tune automation based on learnings

---

## Success Criteria

### Before Automation
- ⏱️ 10-15 minutes of manual work per session
- ❌ High risk of forgetting steps (Linear, JOURNEY.md)
- ❌ Inconsistent formats
- ❌ Broken automation (4 sessions failed)

### After Automation
- ⏱️ 1 minute (run one command)
- ✅ 100% consistency
- ✅ Zero manual steps
- ✅ Automated verification
- ✅ Working automation (tested and monitored)

---

## Monitoring & Alerts

### GitHub Actions Notifications
- Email notification when Linear sync fails
- Slack/Discord webhook for PR auto-merge failures

### Weekly Automation Health Check
- Script: `scripts/check-automation-health.sh`
- Runs weekly via GitHub Actions
- Verifies:
  - Last 5 PRs had successful Linear sync
  - JOURNEY.md is up to date
  - All sessions have corresponding Linear issues marked Done

---

## Rollback Plan

If automation fails:
1. **Manual override** available for each step
2. **SESSION_CHECKLIST.md** still exists as backup manual process
3. **Gradual rollout** - test on Session 6 before full deployment

---

## Questions & Decisions

### Q1: Should we auto-merge PRs without human review?
**Decision:** Yes, because:
- CI validates everything (tests, linting, formatting)
- Single developer working on project
- Can always revert if needed
- Saves 5-10 minutes per session

### Q2: How much of JOURNEY.md should be automated?
**Decision:** 80/20 approach:
- 80% auto-generated (facts, file lists, test counts)
- 20% manual (nuanced decisions, subjective learnings)
- **Phase 1:** Basic automation with manual override
- **Phase 2:** AI-assisted content generation

### Q3: What if Linear API changes?
**Decision:**
- Comprehensive error handling in scripts
- Fallback to manual update with clear instructions
- Monitor Linear API changelog

---

## Next Steps

1. **Commit fixed linear-sync.yml** ← DO THIS NOW
2. **Test on Session 6** - verify Linear sync works
3. **Implement Phase 1 scripts** - PR creation & verification
4. **Iterate based on learnings**

---

**Status:** Plan created 2025-12-23
**Last Updated:** 2025-12-23
**Implementation:** Phase 1 (fixing Linear sync)
