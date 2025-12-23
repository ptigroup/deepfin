# Session Completion Checklist

This checklist ensures consistency across all session completions. **Run this checklist at the end of EVERY session before starting the next one.**

## Pre-Session Checklist

Before starting any session:

- [ ] On `main` branch
- [ ] Working tree is clean (`git status`)
- [ ] All tests passing locally
- [ ] Previous session fully complete (check all items below)

## Session Completion Checklist

After merging a PR, **ALWAYS verify all 3 systems are updated:**

### 1. GitHub ✅

- [ ] PR created with title format: `Session N: Description`
- [ ] CI passing (all checks green)
- [ ] PR merged to `main`
- [ ] Branch deleted (automatic on merge)
- [ ] Local `main` branch updated (`git checkout main && git pull`)

**Verify:** Check https://github.com/ptigroup/deepfin/pulls?q=is%3Apr+is%3Aclosed

### 2. JOURNEY.md ✅

- [ ] Session section updated with:
  - **Completed date**
  - **PR link** (format: `[#N](https://github.com/ptigroup/deepfin/pull/N)`)
  - **Linear status** (` Linear: BUD-N → Done`)
  - Comprehensive documentation (What We Built, Key Decisions, etc.)
- [ ] Progress Tracker table updated with PR link
- [ ] Completion percentage updated
- [ ] Phase progress updated
- [ ] "Last Updated" date at bottom
- [ ] "Current Session" updated to next session
- [ ] Changes committed and pushed to `main`

**Verify:** Check https://github.com/ptigroup/deepfin/blob/main/JOURNEY.md

### 3. Linear ✅

- [ ] **Current session** (BUD-N) moved to **Done**
- [ ] **Next session** (BUD-N+1) moved to **In Progress** or **In Review**
- [ ] Comment added with PR link (optional, but nice to have)

**Verify:** Check https://linear.app/deepfin/team/BUD/active

---

## Quick Verification Script

Run this after every session to verify all systems:

```bash
# 1. Check GitHub PR status
gh pr view <PR_NUMBER> --json state,mergedAt

# 2. Check JOURNEY.md has PR link
grep "Session <N>.*#<PR_NUMBER>" JOURNEY.md

# 3. Check Linear status (manual check or use script below)
```

## Linear Verification Script

Save this as `scripts/verify-linear.py`:

```python
#!/usr/bin/env python3
import requests
import sys
import os

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")

headers = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

session_num = int(sys.argv[1]) if len(sys.argv) > 1 else 5
issue_id = f"BUD-{session_num + 4}"

query = f'''
{{
  issue(id: "{issue_id}") {{
    identifier
    title
    state {{
      name
      type
    }}
  }}
}}
'''

response = requests.post("https://api.linear.app/graphql",
                        json={"query": query},
                        headers=headers)

if response.status_code == 200:
    data = response.json()["data"]["issue"]
    print(f"{data['identifier']}: {data['state']['name']} ({data['state']['type']})")
    if data['state']['type'] == 'completed':
        print("✅ Session marked as Done")
        sys.exit(0)
    else:
        print("❌ Session NOT marked as Done")
        sys.exit(1)
else:
    print(f"❌ Error: {response.text}")
    sys.exit(1)
```

**Setup:**
```bash
export LINEAR_API_KEY='your_key_here'
# Or add to .env file and use: source .env
```

**Usage:**
```bash
python scripts/verify-linear.py 5  # For Session 5
```

---

## Session Mapping

| Session | Linear Issue | Offset Formula |
|---------|--------------|----------------|
| Session 1 | BUD-5 | Session + 4 |
| Session 2 | BUD-6 | Session + 4 |
| Session 3 | BUD-7 | Session + 4 |
| Session 4 | BUD-8 | Session + 4 |
| Session 5 | BUD-9 | Session + 4 |
| ... | ... | ... |
| Session N | BUD-(N+4) | Session + 4 |

---

## Current Session Status

**Last Completed:** Session 5 (2025-12-22)

- ✅ GitHub: PR #5 merged
- ✅ JOURNEY.md: Updated
- ✅ Linear: BUD-9 → Done, BUD-10 → In Review

**Next Session:** Session 6: Detection Service (BUD-10)

---

## Automation Status

### GitHub Actions Workflows

1. **`.github/workflows/validate.yml`**
   - Runs on every PR
   - Validates: ruff format, ruff lint, pytest
   - Status: ✅ Working

2. **`.github/workflows/linear-sync.yml`**
   - Runs when PR is merged
   - Updates Linear issue to Done
   - Moves next issue to In Progress
   - **Status: ⚠️ Was failing (API key expired) - FIXED as of 2025-12-23**
   - **Action Required:** Verify it works on next PR merge

### What's Automated

✅ PR merge → Linear status update (via GitHub Actions)
✅ CI validation (ruff format, ruff lint, pytest)
❌ JOURNEY.md update (manual - requires human judgment on what to write)

### What's Manual

- JOURNEY.md comprehensive documentation (intentionally manual)
- Session planning and implementation
- PR description writing

---

## Troubleshooting

### Linear Not Updated After PR Merge

1. Check GitHub Actions run: https://github.com/ptigroup/deepfin/actions/workflows/linear-sync.yml
2. If workflow failed:
   - Check error logs
   - Verify LINEAR_API_KEY secret is valid
   - Run manual update (see Linear Verification Script above)

### JOURNEY.md Missing PR Link

1. Check if PR was merged
2. Update manually: Find the session section and update the PR line
3. Commit and push

### GitHub PR Not Found

1. Verify you created the PR (not just pushed the branch)
2. Check PR was merged (not closed without merge)

---

## History of Issues

| Date | Issue | Resolution |
|------|-------|------------|
| 2025-12-23 | Linear sync failing for Sessions 2-5 | API key expired. Updated to new key. BUD-9 manually updated to Done. |
| 2025-12-23 | Lack of tracking/checklist | Created this SESSION_CHECKLIST.md document |

---

**Remember:** If you have to ask "Did I update X?", you probably didn't. **Use this checklist!**
