# Brownfield Project Archive

This directory contains the **original brownfield codebase** developed before the refactoring to the FastAPI-based architecture (pre-October 2025).

## Purpose

This code is **preserved for reference** when working on the current `/app` project. Use this when:

- Debugging issues in the new extraction pipeline (reference old parsers)
- Understanding LLMWhisperer integration patterns (check `core/`)
- Comparing old vs new table detection logic
- Finding implementation details from the original pipeline architecture

## ⚠️ Important Notes

- **DO NOT modify code in this directory** - it's archived for reference only
- **Active development happens in `/app`** - all new work goes there
- **Git history is preserved** - you can trace file evolution from brownfield → current project
- This code is dated **September 2025** (before refactoring started)

---

## Directory Structure

### `/pipelines/` - Original 5-Stage Pipeline

The original sequential processing pipeline architecture:

- **`pipeline_01_input_discovery/`** - PDF discovery and validation
- **`pipeline_02_table_detection/`** - AI-based table detection using LLMWhisperer
- **`pipeline_03_extraction/`** - Raw text extraction and parsing
- **`pipeline_04_processing/`** - Data validation and transformation
- **`pipeline_05_consolidation/`** - Multi-period consolidation and Excel export

**When to reference:**
- Understanding the original LLMWhisperer settings and parameters
- Comparing old vs new extraction logic
- Reviewing original table detection algorithms

---

### `/core/` - Core Infrastructure

Shared infrastructure for the original pipeline:

- `pipeline_01_2_enterprise_manager.py` - Central pipeline orchestration
- `pipeline_logger.py` - Original logging implementation
- `project_paths.py` - Path management utilities
- `cross_platform_paths.py` - Windows/Unix path handling
- `migration_safety.py` - Migration utilities

**When to reference:**
- LLMWhisperer client configuration
- Original logging patterns
- Path management approaches

---

### `/parsers/` - Direct Table Parsers

Original parser implementations for financial statements:

**When to reference:**
- Understanding context-based indentation logic
- Reviewing section header detection patterns
- Comparing direct parsing vs LLM-based extraction approaches

---

### `/schemas/` - Original Pydantic Schemas

Original schema definitions for financial statements:

**When to reference:**
- Understanding the evolution of data models
- Comparing old vs new field structures
- Reviewing original validation logic

---

### `/utilities/` - Utility Scripts

Helper scripts and utilities from the original project:

**When to reference:**
- Understanding original helper functions
- Reviewing data transformation utilities

---

### `/data/` - Original Data Directories

**`/data/input/`** - Original input PDFs
- Sample financial statements
- Test documents

**`/data/output/`** - Original output files
- Generated JSON extractions
- Excel exports
- Raw text files

**`/data/dump/`** - Development dumps and backups
- Legacy extractors (`legacy_extractors/`)
- Legacy parsers (`legacy_parsers/`)
- Backup files (`backup_files/`)
- Virtual environment backups (`virtual_env/`)
- Test output and debug files

**`/data/migration_backup/`** - Migration safety backups

**When to reference:**
- Comparing old vs new extraction results
- Understanding test data structure
- Reviewing extraction accuracy

---

### `/scripts/` - Audit & Fix Scripts

Original audit, testing, and fix scripts:

**Audit Scripts:**
- `audit_balance_sheet.py` - Balance sheet validation
- `audit_cash_flow_fix.py` - Cash flow statement fixes
- `audit_comprehensive_income.py` - Comprehensive income validation
- `rigorous_balance_sheet_audit.py` - Detailed balance sheet audit
- `rigorous_comprehensive_audit.py` - Detailed comprehensive income audit

**Processing Scripts:**
- `final_audit.py` - Final validation pipeline
- `final_cash_flow_fix.py` - Cash flow fix implementation
- `fix_cash_flow_consolidation.py` - Consolidation fixes
- `reconstruct_cash_flow_2020_2019.py` - Historical data reconstruction

**Test Scripts:**
- `test_comprehensive_fix.py` - Comprehensive fix testing
- `test_fixes.py` - General fix validation

**Main Entry Point:**
- `main.py` - Original pipeline entry point

**When to reference:**
- Understanding validation approaches
- Reviewing fix patterns for data issues
- Comparing test strategies

---

### `/old_docs/` - Original Documentation

Original project documentation:

- `CASH_FLOW_PIPELINE_FIX_SUMMARY.md` - Cash flow fix documentation
- `Financial_Pipeline_Documentation.md` - Complete pipeline documentation
- `PIPELINE_ARCHITECTURE_FLOW.md` - Architecture diagrams and flows
- `PROJECT_CAPABILITIES_DOCUMENTATION.md` - Feature documentation
- `PROJECT_STRUCTURE.md` - Original project structure

**When to reference:**
- Understanding original architecture decisions
- Reviewing pipeline flow diagrams
- Comparing capabilities before/after refactoring

---

## Migration History

**Reorganization Date:** December 27, 2025
**Reason:** Separate brownfield (pre-Oct 2025) from refactored FastAPI project (`/app`)

**What happened:**
1. All brownfield code (dated Sept 2025) moved to `/brownfield/`
2. Current FastAPI project remains in `/app/`
3. Git history preserved for all files
4. Clear separation between reference code and active development

---

## Current Project vs Brownfield

| Aspect | Brownfield (`/brownfield/`) | Current Project (`/app/`) |
|--------|----------------------------|---------------------------|
| **Architecture** | 5-stage sequential pipeline | FastAPI microservices |
| **Entry Point** | `scripts/main.py` | `app/main.py` |
| **Database** | File-based | PostgreSQL + SQLAlchemy |
| **API** | None | REST API with OpenAPI docs |
| **Authentication** | None | JWT-based auth |
| **Background Jobs** | Synchronous | Async worker pattern |
| **Testing** | Ad-hoc scripts | Pytest with 42%+ coverage |
| **Deployment** | Manual | Docker + CI/CD (Session 18) |
| **Documentation** | Markdown files | README + ARCHITECTURE + API docs |

---

## How to Use This Archive

### Example: Debugging Extraction Issues

```python
# Problem: New extraction logic in /app/extraction/parser.py not working

# Step 1: Check old working parser
# Open: brownfield/parsers/direct_income_statement_parser.py

# Step 2: Compare approaches
# Old: Context-based indentation detection
# New: LLM-based extraction

# Step 3: Reference old LLMWhisperer settings
# Check: brownfield/core/pipeline_01_2_enterprise_manager.py

# Step 4: Compare output formats
# Old output: brownfield/data/output/
# New output: app/extraction/service.py
```

### Example: Understanding Pipeline Evolution

```bash
# Trace a file's history from brownfield to current
git log --follow --all -- app/extraction/parser.py

# Compare old vs new parser
git diff brownfield/parsers/direct_income_statement_parser.py app/extraction/parser.py
```

---

## Questions?

- **For current project:** See `/README.md`, `/docs/ARCHITECTURE.md`
- **For API reference:** See `/docs/API.md`
- **For development guide:** See `/JOURNEY.md`
- **For methodology:** See `/CLAUDE.md` (shared across both projects)

**Last Updated:** December 27, 2025
