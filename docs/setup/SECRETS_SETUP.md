# GitHub Secrets Setup Guide

This guide explains how to configure the required GitHub Secrets for the LLM Financial Pipeline v2.0 GitHub Actions workflows.

## Overview

The GitHub Spec Kit automation requires two secrets to be configured in your GitHub repository:

1. **CLAUDE_CODE_OAUTH_TOKEN** - For AI-powered code reviews via @claude-review
2. **LINEAR_API_KEY** - For automatic Linear issue synchronization

## Prerequisites

- Admin access to the GitHub repository
- Claude Code account (https://claude.ai)
- Linear workspace access with API permissions

---

## Setup Instructions

### 1. Claude Code OAuth Token

**Purpose:** Enables automated AI code reviews when you comment `@claude-review` on PRs.

**Steps:**

1. **Navigate to Claude OAuth Settings**
   - Go to: https://claude.ai/settings/oauth
   - Sign in with your Claude account

2. **Create New OAuth Token**
   - Click "Create OAuth Token" or "New Token"
   - Name: `GitHub Code Review - deepfin`
   - Description: `OAuth token for AI code reviews in deepfin repository`
   - Permissions: Ensure code review permissions are enabled
   - Click "Create"

3. **Copy the Token**
   - Copy the generated token (starts with `sk-ant-...`)
   - ⚠️ **Important:** You'll only see this once - save it securely

4. **Add to GitHub Secrets**
   - Go to your GitHub repository: https://github.com/ptigroup/deepfin
   - Navigate to: `Settings` → `Secrets and variables` → `Actions`
   - Click `New repository secret`
   - Name: `CLAUDE_CODE_OAUTH_TOKEN`
   - Value: Paste the OAuth token
   - Click `Add secret`

**Verification:**
```bash
# The secret should now appear in:
# Settings → Secrets and variables → Actions → Repository secrets
# You'll see: CLAUDE_CODE_OAUTH_TOKEN (Updated: [date])
```

---

### 2. Linear API Key

**Purpose:** Automatically updates Linear issues when PRs are merged.

**Steps:**

1. **Navigate to Linear API Settings**
   - Go to your Linear workspace
   - Click your avatar (bottom left) → `Settings`
   - Navigate to: `API` section

2. **Create Personal API Key**
   - Scroll to "Personal API keys"
   - Click `Create key`
   - Name: `GitHub Actions - deepfin`
   - Description: `API key for automatic Linear sync from GitHub PRs`
   - Click `Create key`

3. **Copy the Token**
   - Copy the generated key (starts with `lin_api_...`)
   - ⚠️ **Important:** Save this securely - you'll only see it once

4. **Add to GitHub Secrets**
   - Go to your GitHub repository: https://github.com/ptigroup/deepfin
   - Navigate to: `Settings` → `Secrets and variables` → `Actions`
   - Click `New repository secret`
   - Name: `LINEAR_API_KEY`
   - Value: Paste the Linear API key
   - Click `Add secret`

**Verification:**
```bash
# The secret should now appear in:
# Settings → Secrets and variables → Actions → Repository secrets
# You'll see: LINEAR_API_KEY (Updated: [date])
```

---

## Verification Checklist

After setup, verify both secrets are configured:

- [ ] Navigate to: https://github.com/ptigroup/deepfin/settings/secrets/actions
- [ ] Confirm `CLAUDE_CODE_OAUTH_TOKEN` exists
- [ ] Confirm `LINEAR_API_KEY` exists
- [ ] Both secrets show recent "Updated" timestamp

**Expected State:**
```
Repository secrets (2)

CLAUDE_CODE_OAUTH_TOKEN     Updated 1 minute ago      Update  Remove
LINEAR_API_KEY              Updated 1 minute ago      Update  Remove
```

---

## Testing the Setup

### Test 1: Claude Code Review

1. Create a test PR (or use existing PR)
2. Add a comment: `@claude-review`
3. Wait ~30 seconds for GitHub Actions to trigger
4. Check the Actions tab for `Claude Code Review` workflow
5. Claude should post a review comment on the PR

**Expected Behavior:**
- Workflow triggers automatically
- Claude analyzes code changes
- Review comment appears on PR

**Troubleshooting:**
- If workflow doesn't trigger: Check `CLAUDE_CODE_OAUTH_TOKEN` is set correctly
- If workflow fails: Check Actions logs for authentication errors

### Test 2: Linear Sync

1. Create a test PR with title: `Session 2: Database & Shared Models`
2. Get PR approved and merge
3. Check Linear: Issue BUD-6 should update to "Done"
4. Issue BUD-7 should move to "In Progress"

**Expected Behavior:**
- Workflow triggers on PR merge
- Linear issue updated automatically
- Comment added with PR link

**Troubleshooting:**
- If workflow doesn't trigger: Check PR title matches `Session X:` pattern
- If Linear doesn't update: Check `LINEAR_API_KEY` permissions
- Check Actions logs for error messages

---

## Security Best Practices

### Token Management

1. **Never Commit Secrets**
   - ❌ Don't add secrets to `.env` that gets committed
   - ✅ Use GitHub Secrets for automation
   - ✅ Use local `.env` (gitignored) for development

2. **Token Rotation**
   - Rotate tokens every 90 days for security
   - Update GitHub Secrets when rotating
   - Test workflows after rotation

3. **Access Control**
   - Limit GitHub repo admin access
   - Use Personal API Keys (not workspace keys) in Linear
   - Revoke tokens immediately if compromised

4. **Audit Regularly**
   - Check GitHub Actions logs monthly
   - Review Linear API usage
   - Monitor for unauthorized access

### What to Do if Token is Compromised

**If CLAUDE_CODE_OAUTH_TOKEN is compromised:**
1. Go to https://claude.ai/settings/oauth
2. Revoke the compromised token
3. Create new OAuth token
4. Update GitHub Secret with new value
5. Test @claude-review functionality

**If LINEAR_API_KEY is compromised:**
1. Go to Linear Settings → API
2. Revoke the compromised key
3. Create new Personal API key
4. Update GitHub Secret with new value
5. Test Linear sync with test PR

---

## Troubleshooting

### Common Issues

#### Issue 1: `CLAUDE_CODE_OAUTH_TOKEN` not working

**Symptoms:**
- @claude-review doesn't trigger workflow
- Workflow fails with authentication error

**Solutions:**
1. Verify token is correct (starts with `sk-ant-`)
2. Check token hasn't expired
3. Ensure token has code review permissions
4. Re-create OAuth token if needed

**Check logs:**
```bash
# Go to: GitHub → Actions → Claude Code Review → [Latest run]
# Look for authentication errors in step: "Run Claude Code Review"
```

#### Issue 2: `LINEAR_API_KEY` not working

**Symptoms:**
- Linear issues don't update after PR merge
- Workflow fails with API errors

**Solutions:**
1. Verify key is correct (starts with `lin_api_`)
2. Check Linear API key has write permissions
3. Verify Linear workspace access
4. Ensure issue identifiers correct (BUD-5, BUD-6, etc.)

**Check logs:**
```bash
# Go to: GitHub → Actions → Linear Sync → [Latest run]
# Look for API errors in step: "Sync with Linear"
```

#### Issue 3: Secrets not visible in Actions

**Symptoms:**
- Workflows can't access secrets
- Environment variables empty

**Solutions:**
1. Check secret names match exactly (case-sensitive)
2. Verify secrets are in "Repository secrets" not "Environment secrets"
3. Re-add secrets if needed
4. Check repository permissions

---

## Maintenance

### Regular Checks (Monthly)

- [ ] Verify both secrets still exist
- [ ] Check GitHub Actions usage (should be within free tier)
- [ ] Review Linear API usage
- [ ] Test @claude-review on a small PR
- [ ] Verify Linear sync with test PR

### Updates Required When

1. **Token Expiration**: Rotate and update secrets
2. **Workflow Changes**: Update if new workflows added
3. **Linear Project Changes**: Update issue identifiers if Linear project restructured
4. **Security Audit**: Review access and rotate tokens

---

## Additional Resources

### Documentation
- **GitHub Secrets Docs**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Claude Code OAuth**: https://claude.ai/settings/oauth
- **Linear API Docs**: https://developers.linear.app/docs/graphql/working-with-the-graphql-api

### Workflow Files
- Claude Review: `.github/workflows/claude-review.yml`
- Linear Sync: `.github/workflows/linear-sync.yml`
- Validation: `.github/workflows/validation.yml`
- Checkpoint Generator: `.github/workflows/checkpoint-generator.yml`

### Related Docs
- [CONTRIBUTING.md](CONTRIBUTING.md) - Full development workflow
- [.github/workflows/README.md](.github/workflows/README.md) - Workflow documentation
- [GITHUB_SPEC_KIT_IMPLEMENTATION_PLAN.md](GITHUB_SPEC_KIT_IMPLEMENTATION_PLAN.md) - Implementation plan

---

## Support

**Questions or Issues?**
1. Check troubleshooting section above
2. Review GitHub Actions logs
3. Check Linear API status: https://status.linear.app
4. Review workflow documentation in `.github/workflows/README.md`

**Need Help?**
- Comment on PR with issues
- Check Linear issue comments
- Tag @claude-review for AI assistance

---

**Setup Version:** 1.0
**Last Updated:** 2025-12-16
**Maintained By:** DevOps Team

---

_🤖 This guide is part of the GitHub Spec Kit automation system._
_See CONTRIBUTING.md for the full development workflow._
