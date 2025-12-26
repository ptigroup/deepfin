# 📊 Linear Integration Setup Guide

**Purpose:** Mirror your LLM Financial Pipeline progress in Linear for team visibility
**Time Required:** 20-25 minutes
**Complexity:** Medium

---

## 🎯 What You'll Achieve

After this setup, your team will see:
- **Linear Project:** "LLM Financial Pipeline v2.0"
- **18 Issues:** One per development session
- **Visual Board:** Todo / In Progress / Done columns
- **Real-time Updates:** Status changes as you complete sessions
- **Collaboration:** Team can comment, track, and see progress

---

## ✅ Prerequisites

Before starting, ensure you have:
- [x] Linear account (free tier is fine)
- [x] LINEAR_API_KEY (we'll get this in Step 1)
- [x] GitHub tracking files committed (just done ✅)

---

## 📋 Step-by-Step Setup

### Step 1: Get Your Linear API Key (5 minutes)

1. **Log in to Linear:** https://linear.app/
2. **Go to Settings:**
   - Click your profile icon (bottom left)
   - Click "Settings"
3. **Navigate to API:**
   - In left sidebar, click "API"
   - Click "Personal API keys"
4. **Create New Key:**
   - Click "Create key"
   - Name: "LLM Financial Pipeline Bot"
   - Click "Create"
   - **Copy the key immediately** (you won't see it again!)
5. **Save to .env file:**
   ```bash
   # Add to your .env file
   LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxx
   ```

**Important:** The API key starts with `lin_api_` and is very long.

---

### Step 2: Create Linear Project (5 minutes)

1. **Go to Linear:** https://linear.app/
2. **Create New Project:**
   - Click "+ New" → "Project"
   - Or go to Projects → "New project"
3. **Project Details:**
   - **Name:** `LLM Financial Pipeline v2.0`
   - **Key:** `LLMFP` (or auto-generated)
   - **Description:**
     ```
     Refactoring brownfield financial document processing pipeline
     to production-ready FastAPI application with Vertical Slice Architecture.

     18 sessions, ~30 hours total
     Stack: FastAPI, PostgreSQL, Pydantic, structlog, pytest
     ```
   - **Icon:** Choose something (💰 or 🤖 or 📊)
   - **Color:** Your choice
4. **Click "Create project"**
5. **Note your Project ID:**
   - URL will be: `https://linear.app/<workspace>/project/<project-id>`
   - Save this project ID (you'll need it)

---

### Step 3: Set Up Issue Labels (3 minutes)

Create labels for better organization:

1. **Go to Project Settings:**
   - Click project name → "Settings"
2. **Create Labels:**
   Click "Labels" → "New label"

   Create these labels:
   - `phase-1-foundation` (blue)
   - `phase-2-llm` (purple)
   - `phase-3-detection` (green)
   - `phase-4-statements` (yellow)
   - `phase-5-extraction` (orange)
   - `phase-6-consolidation` (pink)
   - `phase-7-jobs-auth` (red)
   - `phase-8-testing` (teal)
   - `phase-9-deploy` (gray)
   - `session-complete` (green) ✅
   - `tests-passing` (green) ✓

---

### Step 4: Create the 18 Session Issues (10 minutes)

You have 2 options:

#### Option A: Manual Creation (Recommended for learning)

For each of the 18 sessions, create an issue:

1. **Click "New Issue"** (or press `C`)
2. **Fill in details:**

**Example for Session 1:**
```
Title: Session 1: Core Configuration & Logging
Project: LLM Financial Pipeline v2.0
Status: Done (already complete)
Priority: High
Labels: phase-1-foundation, session-complete, tests-passing

Description:
Build foundational configuration and logging infrastructure using professional patterns.

## Files to Create (6 files)
- app/__init__.py - Main application package
- app/core/__init__.py - Core infrastructure package
- app/core/config.py - Pydantic Settings configuration (550 lines)
- app/core/logging.py - Structured logging with structlog (450 lines)
- app/core/tests/test_config.py - Configuration tests (11 tests)
- app/core/tests/test_logging.py - Logging tests (14 tests)

## Key Concepts
- Pydantic Settings for type-safe configuration
- Singleton pattern with @lru_cache
- Structured logging with structlog
- Correlation IDs for request tracking

## Acceptance Criteria
- [ ] Settings load from .env file
- [ ] Validation works for required fields
- [ ] Structured logging outputs JSON
- [ ] All 25 tests pass
- [ ] Checkpoint document created

## Links
- Checkpoint: [CHECKPOINT_01_Config_Logging.md](https://github.com/<your-username>/<repo>/blob/main/CHECKPOINT_01_Config_Logging.md)
- Git Commit: d07dab0
```

3. **Create remaining 17 issues** following this pattern
   - Use SESSION_MANIFEST.md as your source
   - Set Sessions 2-18 to "Todo" status
   - Session 1 to "Done" status

**Time-saving tip:** Copy/paste from SESSION_MANIFEST.md!

#### Option B: Use the Linear API Script (Automated)

I can create a Python script that automatically creates all 18 issues. Would you like me to create this script?

---

### Step 5: Set Up Issue Workflow (2 minutes)

1. **Configure Workflow States:**
   - Go to Project Settings → "Workflows"
   - Ensure you have these states:
     - **Todo** (backlog)
     - **In Progress** (active work)
     - **Done** (completed)

2. **Optional: Add custom states:**
   - **Blocked** (waiting on something)
   - **Testing** (in QA/testing phase)

---

### Step 6: Test Your Setup (2 minutes)

1. **View your board:**
   - Click "Board" view
   - You should see:
     - Session 1 in "Done" column
     - Sessions 2-18 in "Todo" column

2. **Try moving an issue:**
   - Drag Session 2 to "In Progress"
   - Verify it updates

3. **Add a comment:**
   - Click Session 1
   - Add comment: "Completed on 2025-12-15. All 25 tests passing!"

---

## 🔄 Daily Workflow: Updating Linear

After completing each session, update Linear:

### Manual Update (2 minutes per session)

1. **Open Linear** → Find the session issue
2. **Update Status:**
   - Drag to "Done" column
   - Or click issue → Change status to "Done"
3. **Add Comment:**
   ```
   Session complete! ✅

   - All tests passing: X/X
   - Files created: Y files
   - Checkpoint: [link to checkpoint]
   - Git commit: <commit-hash>

   Next: Session N+1
   ```
4. **Add Labels:**
   - Add `session-complete` label
   - Add `tests-passing` label
5. **Move Next Issue:**
   - Drag Session N+1 to "In Progress"

### Semi-Automated Update (Using Script)

Would you like me to create a Python script that updates Linear via API? It would:
- Mark session as done
- Add test results
- Link to checkpoint
- Add labels
- Move next session to "In Progress"

Let me know if you want this script!

---

## 📊 Team Collaboration Features

### For Your Team Members

**Viewing Progress:**
1. Share Linear project link with team
2. They can see the board without making changes
3. Real-time updates as you work

**Commenting:**
- Team can add comments to any issue
- You'll get notifications
- Great for questions, feedback, blockers

**Priority Changes:**
- Product manager can adjust priorities
- You'll see which sessions are most important

**Tracking:**
- Team sees what you're working on
- Can see test results
- Can see git commits

---

## 🔗 Integration with GitHub

### Link GitHub Commits to Linear

In your git commit messages, reference Linear issues:

```bash
git commit -m "Session 2: Add database and models

Completes LLMFP-2

- Created app/core/database.py
- Created app/shared/models.py
- All 20 tests passing

[Linear Link: https://linear.app/.../LLMFP-2]"
```

Linear will automatically link the commit to the issue!

---

## 📱 Linear Features to Explore

### Views
- **Board View:** Kanban-style board (default)
- **List View:** Spreadsheet-style list
- **Timeline:** Gantt chart view
- **Roadmap:** High-level timeline

### Notifications
- **Slack Integration:** Get updates in Slack
- **Email Notifications:** Updates via email
- **In-app Notifications:** Bell icon

### Filters
- Filter by: Status, Label, Priority, Assignee
- Create custom views
- Save favorite filters

---

## 🎯 Quick Reference

### Linear Issue Template

For each session, use this template:

```
Title: Session X: [Name]

Description:
[Brief description]

## Deliverables
- [ ] File 1
- [ ] File 2
- [ ] Tests (X tests)

## Prerequisites
- Session X-1 must pass all tests

## Acceptance Criteria
- [ ] Criterion 1
- [ ] All tests pass
- [ ] Checkpoint created

## Links
- Checkpoint: [link]
- Commit: [hash]
```

### Status Meanings

| Status | Meaning | When to Use |
|--------|---------|-------------|
| **Todo** | Not started | Sessions not yet begun |
| **In Progress** | Working on it | Current session you're doing |
| **Done** | Completed | Session finished, tests passing |
| **Blocked** | Can't proceed | Missing dependencies, errors |

---

## 🐛 Troubleshooting

### Issue: API Key Not Working
**Solution:**
- Verify key starts with `lin_api_`
- Check you copied entire key
- Ensure key has correct permissions
- Try creating a new key

### Issue: Can't See Project
**Solution:**
- Check you're in correct workspace
- Verify project wasn't archived
- Check project permissions

### Issue: Team Can't See Issues
**Solution:**
- Share project link explicitly
- Check team has workspace access
- Verify privacy settings

---

## 📈 Advanced: Automation Options

### Option 1: Linear API Script (Python)

I can create a script that:
```python
# update_linear.py
# Updates Linear after each session
# Usage: python update_linear.py --session 2 --status done --tests 20/20
```

### Option 2: GitHub Actions Integration

Auto-update Linear when you push commits:
```yaml
# .github/workflows/update-linear.yml
# Automatically updates Linear on git push
```

### Option 3: Linear MCP Integration

Use the Linear Coding Agent Harness (from the docs you showed me):
- Full automation
- AI agents update Linear
- Requires more setup

**Which automation level do you want?** Let me know!

---

## ✅ Setup Complete Checklist

After completing this guide, verify:

- [ ] Linear account created
- [ ] API key saved in .env
- [ ] Project "LLM Financial Pipeline v2.0" created
- [ ] Labels created (9 phase labels + 2 status labels)
- [ ] 18 session issues created
- [ ] Session 1 marked as "Done"
- [ ] Session 2 in "In Progress"
- [ ] Team invited to project (if applicable)
- [ ] Tested moving issues and commenting
- [ ] GitHub repo link added to project

---

## 🚀 Next Steps

1. **Complete this Linear setup** (~20 mins)
2. **Test by updating Session 1** in Linear (practice)
3. **Share Linear link with team**
4. **Continue to Session 2** (database work)
5. **Update Linear after Session 2 completes**

---

## 💡 Pro Tips

### Keep It Simple
- Don't over-complicate with too many labels
- Use comments for details, not issue titles
- Update Linear after session, not during

### Team Communication
- Use Linear for "what" (tasks, status)
- Use GitHub for "how" (code, technical details)
- Use Slack/email for "why" (decisions, discussions)

### Consistency
- Update Linear every session
- Use same format for all issues
- Link to checkpoints and commits

---

## 📞 Need Help?

**Linear Documentation:**
- https://linear.app/docs
- https://linear.app/docs/api

**Linear API:**
- https://developers.linear.app/docs/graphql/working-with-the-graphql-api

**Questions?**
Ask me! I can help with:
- Creating the automation script
- Setting up GitHub Actions
- Troubleshooting Linear issues
- Optimizing your workflow

---

**Ready to set up Linear?** Let me know when you complete each step or if you need help!

**Prefer automation?** Tell me and I'll create the Python script to auto-create all 18 issues!

**Want to skip Linear for now?** No problem! The GitHub tracking files work perfectly on their own. You can add Linear later.

What would you like to do next?

---

**Document Version:** 1.0
**Created:** 2025-12-16
**Maintained By:** Marconi Sim + Claude Sonnet 4.5
