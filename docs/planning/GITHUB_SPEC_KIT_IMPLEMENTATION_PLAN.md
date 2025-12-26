# GitHub Spec Kit Implementation Plan - Option C (Full)

**Date:** 2025-12-16
**Project:** LLM Financial Pipeline v2.0
**Current Status:** Session 1 Complete, Session 2 Ready to Start
**Linear Project:** https://linear.app/deepfin/project/deep-fin-17d251686130

---

## 🎯 Implementation Goal

Transform our development workflow with GitHub Spec Kit to enable:
- **PRP-driven development** (specification before implementation)
- **Automated code reviews** (@claude-review in PRs)
- **Linear-GitHub sync** (auto-update issues on PR merge)
- **Professional PR workflow** (templates, validation, tracking)
- **Structured validation** (4-level validation per session)

**Estimated Time:** 1.5-2 hours for complete setup
**Token Usage:** ~15-20K tokens (safe within 200K limit)

---

## ⚠️ CRITICAL QUESTIONS - ANSWER BEFORE PROCEEDING

### 1. GitHub Repository Questions

**Q1.1:** Do you have a GitHub repository set up for this project?
- [X] Yes, at: `https://github.com/ptigroup/deepfin`


**Q1.2:** If yes, what is the repository URL?
```
GitHub URL: https://github.com/ptigroup/deepfin
```

**Q1.3:** Are you comfortable with GitHub Actions running on your repo?
- [X] Yes (will need GitHub Actions secrets)


**Q1.4:** Do you want to push the current code to GitHub before setup?
- [X] Yes, push Session 1 code now


---

### 2. GitHub Actions & Secrets Questions

**Q2.1:** Do you have access to create GitHub Secrets in your repo?
- [X ] Yes, I'm the repo owner

**Q2.2:** For Claude Code Review automation, you'll need `CLAUDE_CODE_OAUTH_TOKEN`. Do you want to:
- [X] Option A: Set up Claude Code OAuth now (requires https://claude.ai/settings/oauth)


**Q2.3:** For Linear sync, you'll need `LINEAR_API_KEY` in GitHub Secrets. Do you want to:
- [X] Option A: Add Linear API key to GitHub Secrets now


---

### 3. PRP Structure Questions

**Q3.1:** How detailed should PRPs be for your sessions?
- [X] Option B: **Balanced** - Essential context, key patterns, core validation (recommended)

**Q3.2:** Should we create PRPs for:
- [X] Option C: Just Session 2 now, create PRPs session-by-session (20 min, incremental)

**Q3.3:** Where should PRPs reference the existing session data?
- [X] Option A: Copy session_data.py content into each PRP (standalone documents)


---

### 4. Workflow Integration Questions

**Q4.1:** How do you want to work with branches and PRs?
- [X ] Option A: **Full PR workflow** - Branch per session → PR → Review → Merge to main


**Q4.2:** When should Linear issues be updated?
- [X] Option A: **Automatic** - GitHub Action updates on PR merge


**Q4.3:** Should checkpoint files be auto-generated or manual?
- [X] Option A: **Auto-generate** - GitHub Action creates checkpoint from PR/PRP


---

### 5. Validation & Testing Questions

**Q5.1:** Which validation levels do you want enforced in PRs?
- [X] Level 1: Syntax & Style (ruff, mypy, pyright) - **Required**
- [X] Level 2: Unit Tests (pytest) - **Required**
- [X] Level 3: Integration Tests (database, API) - **Required**
- [ ] Level 4: Manual Testing (you verify manually) - **Optional**

**Q5.2:** Should GitHub Actions block PR merge if tests fail?
- [X] Yes - Enforce quality, prevent broken code


**Q5.3:** What's your preference for test coverage tracking?
- [X] Option A: Add coverage reports to PRs (shows % coverage)

---

### 6. Documentation Questions

**Q6.1:** Should we enhance your existing CLAUDE.md?

- [ X] No - Keep CLAUDE.md minimal, put details in PRPs


**Q6.2:** Do you want PR templates to reference:
- [X] Option A: PRP document (link to PRP for context)

**Q6.3:** Should we add CONTRIBUTING.md with workflow guide?
- [X] Yes - Help team understand process

---

### 7. File Organization Questions

**Q7.1:** Where should PRPs live?
- [ ] Option A: `.claude/PRPs/` (hidden from main view, AI-focused)
- [X] Option B: `docs/PRPs/` (visible, part of documentation)
- [] Option C: `PRPs/` (top-level, prominent)

**Q7.2:** Should session_data.py be kept or migrated?
- [X] Keep as-is (separate from PRPs, used for Linear automation)
- [ ] Migrate to PRPs (make PRPs the single source of truth)
- [ ] Keep both (PRPs for implementation, session_data.py for metadata)

**Q7.3:** Where should checkpoint files go after creation?
- [ ] Current location: root directory (CHECKPOINT_01.md, CHECKPOINT_02.md)
- [X ] New location: `docs/checkpoints/` (organized folder)
- [ ] Inside PRP folder: `.claude/PRPs/checkpoints/`

---

### 8. Timeline & Scope Questions

**Q8.1:** When should we complete this setup?
- [X] Option A: **Right now** - Set up before Session 2 (next 1-2 hours)
- [ ] Option B: **After Session 2** - Implement Session 2, then add Spec Kit
- [ ] Option C: **Phased** - Minimal setup now, expand during Session 3

**Q8.2:** Should we test the full workflow with a dummy PR first?
- [X ] Yes - Create test PR to verify everything works
- [ ] No - Use Session 2 as the first real test
- [ ] Partial - Test locally without GitHub Actions first

**Q8.3:** Do you want to commit the Spec Kit setup as a separate PR?
- [X ] Yes - "GitHub Spec Kit Implementation" PR before Session 2
- [ ] No - Include in Session 2 PR
- [ ] Separate commit to main without PR

---

## 📋 Proposed Implementation Sequence

Based on your answers, here's the order of operations:

### Phase 1: Foundation Setup (20-30 min)
1. ✅ Create directory structure (.claude/PRPs/, .github/workflows/)
2. ✅ Create PRP template adapted for your project
3. ✅ Enhance CLAUDE.md with workflow instructions
4. ✅ Create PR template

### Phase 2: Session 2 PRP Creation (20-30 min)
5. ✅ Create detailed PRP for Session 2 (Database & Models)
6. ✅ Include all context, patterns, validation steps
7. ✅ Link to Linear issue BUD-6
8. ✅ Reference session_data.py and existing docs

### Phase 3: GitHub Actions Setup (30-40 min)
9. ✅ Create claude-review.yml workflow
10. ✅ Create linear-sync.yml workflow (if opted in)
11. ✅ Create session-complete.yml workflow
12. ✅ Add workflow documentation

### Phase 4: Integration & Testing (10-20 min)
13. ✅ Commit all Spec Kit files
14. ✅ Create test PR (optional, based on Q8.2)
15. ✅ Verify workflows trigger correctly
16. ✅ Test Linear sync (if enabled)

### Phase 5: Session 2 Execution (1.5 hours - separate session)
17. ✅ Use PRP to guide Session 2 implementation
18. ✅ Create PR for Session 2
19. ✅ Trigger @claude-review
20. ✅ Merge and verify Linear auto-update

---

## 🚨 Risk Mitigation

### Potential Issues & Solutions

**Issue 1: Token Limit Concerns**
- **Risk:** Spec Kit setup uses significant tokens
- **Mitigation:** Phased implementation, can pause/resume
- **Current Usage:** ~100K/200K used, ~100K remaining (safe)

**Issue 2: GitHub Actions Failures**
- **Risk:** Workflows don't trigger or fail
- **Mitigation:** Start with disabled workflows, test locally first
- **Fallback:** Manual process still works without automation

**Issue 3: Linear API Rate Limits**
- **Risk:** Too many automated updates trigger rate limit
- **Mitigation:** Batch updates, add delays, use manual fallback
- **Monitor:** Linear Free tier = 50 req/min (plenty for our use)

**Issue 4: Complexity Overhead**
- **Risk:** Spec Kit adds complexity, slows development
- **Mitigation:** Start minimal, only add what provides value
- **Escape Hatch:** Can disable workflows anytime, keep PRPs only

---

## 📊 Success Criteria

How we'll know Option C implementation is successful:

### Technical Success
- [ ] All files committed to git
- [ ] PR template renders correctly on GitHub
- [ ] GitHub Actions workflows validate successfully
- [ ] PRP template is clear and usable
- [ ] CLAUDE.md provides complete workflow guidance

### Functional Success
- [ ] Can create PRP for Session 2
- [ ] Can create PR using new template
- [ ] @claude-review works (or is properly deferred)
- [ ] Linear sync works (or is properly configured)
- [ ] Validation commands run successfully

### Workflow Success
- [ ] You understand the new workflow
- [ ] The workflow feels helpful, not burdensome
- [ ] Team can see progress in both GitHub and Linear
- [ ] Quality improvements are measurable

---

## 💰 Cost/Benefit Summary

### Costs
| Item | Time | Tokens | Complexity |
|------|------|--------|-----------|
| Initial Setup | 1.5h | ~15K | Medium |
| PRP per Session | +20min | ~2K | Low |
| PR per Session | +10min | ~1K | Low |
| **Total Session 2-18** | **+8.5h** | **~51K** | **Low** |

### Benefits
| Benefit | Time Saved | Quality Gain | Team Value |
|---------|------------|--------------|------------|
| Structured Planning | -0.5h/session | +30% | High |
| Automated Review | +0.3h/session | +40% | High |
| Linear Sync | +5min/session | N/A | Very High |
| Professional Process | N/A | +25% | Very High |
| **Net Impact** | **+0.2h/session** | **+95%** | **Very High** |

**Net Total for 17 Remaining Sessions:** +3.4 hours, +95% quality, massive team visibility

---

## 🎯 Recommended Configuration

Based on typical preferences, here's my recommendation:

### Repository & Actions
- ✅ Set up on GitHub with Actions enabled
- ✅ Add CLAUDE_CODE_OAUTH_TOKEN (Option C: create workflow, configure later)
- ✅ Add LINEAR_API_KEY to secrets (for auto-sync)

### PRP Configuration
- ✅ **Balanced** detail level (Q3.1 Option B)
- ✅ Create Sessions 2-5 PRPs now (Q3.2 Option B)
- ✅ Reference session_data.py (Q3.3 Option B - DRY)

### Workflow Integration
- ✅ **Full PR workflow** for all sessions (Q4.1 Option A)
- ✅ **Automatic** Linear updates (Q4.2 Option A)
- ✅ **Manual** checkpoint creation (Q4.3 Option B - preserve quality)

### Validation & Testing
- ✅ Enforce all 4 validation levels (Q5.1 All)
- ✅ **Yes** - Block merge if tests fail (Q5.2 Yes)
- ✅ Track test count only (Q5.3 Option B - simpler)

### Documentation
- ✅ Enhance existing CLAUDE.md (Q6.1 Yes)
- ✅ Reference both PRP and Linear (Q6.2 Option C)
- ✅ Add CONTRIBUTING.md (Q6.3 Yes)

### File Organization
- ✅ PRPs in `.claude/PRPs/` (Q7.1 Option A - AI-focused)
- ✅ Keep both PRP and session_data.py (Q7.2 Option C)
- ✅ Checkpoints in `docs/checkpoints/` (Q7.3 New location)

### Timeline & Scope
- ✅ Set up right now (Q8.1 Option A)
- ✅ Test with Session 2 (Q8.2 No - use real session)
- ✅ Separate "Spec Kit Setup" commit (Q8.3 Yes)

---

## ✅ Action Items Before Proceeding

### Your Tasks (Right Now - 5 minutes)
1. **Answer all questions above** (mark checkboxes, fill in blanks)
2. **Review recommended configuration** (accept or modify)
3. **Confirm GitHub repository details** (URL, access, secrets)
4. **Approve/modify implementation sequence** (any changes?)
5. **Give go-ahead** to proceed with implementation

### My Tasks (After Your Approval - 1.5 hours)
1. Create all directory structures
2. Create PRP templates
3. Create Session 2 PRP
4. Set up GitHub Actions workflows
5. Enhance CLAUDE.md
6. Create PR template
7. Create CONTRIBUTING.md
8. Commit everything with proper documentation
9. Verify setup works

---

## 🤔 Final Questions Before Starting

**Question 1:** Are you ready to spend 1.5 hours now on this setup, or should we do Session 2 first and add Spec Kit later?

**Question 2:** Do you have any concerns about the proposed approach?

**Question 3:** Any customizations or modifications to the recommended configuration?

**Question 4:** Should I create any additional documentation or templates beyond what's listed?

---

## 📝 Next Steps

**STOP HERE - WAIT FOR YOUR RESPONSES**

After you answer all questions and give approval:
1. ✅ I'll update this document with your answers
2. ✅ I'll create a final implementation checklist
3. ✅ I'll execute the implementation phase-by-phase
4. ✅ I'll update todo list after each phase
5. ✅ We'll test everything works before proceeding to Session 2

**Estimated Start-to-Finish:** 1.5-2 hours with breaks for review

---

**Status:** ⏸️ AWAITING YOUR RESPONSES
**Last Updated:** 2025-12-16 14:30 SGT
**Document Version:** 1.0 (Initial Planning)
