# LLMWhisperer Financial Pipeline - AI-Optimized Refactoring Plan

**Project:** Transform brownfield financial document processing system into AI-optimized vertical slice architecture
**Created:** 2025-12-14
**Approach:** Complete Rebuild with Feature Migration
**Timeline:** 2-4 weeks full-time development

---

## Executive Summary

This plan transforms the existing 5-stage modular pipeline into a production-ready, AI-optimized vertical slice architecture with FastAPI, PostgreSQL hybrid persistence, strict type safety, and comprehensive testing infrastructure.

**Current State:** 5-stage file-based pipeline (Input → Detection → Extraction → Processing → Consolidation)
**Target State:** Vertical slice FastAPI application with database persistence, maintaining file-based caching

**Key Principles:**
- ✅ Preserve all existing functionality (100% feature parity)
- ✅ Enhance with AI-optimized patterns (type safety, structured logging, validation)
- ✅ Add FastAPI REST API for programmatic access
- ✅ Hybrid persistence: PostgreSQL + file cache
- ✅ Vertical slice architecture for feature isolation

---

## Table of Contents

1. [Gap Analysis](#gap-analysis)
2. [Target Architecture](#target-architecture)
3. [Implementation Phases](#implementation-phases)
4. [AST Grep Refactoring Strategy](#ast-grep-refactoring-strategy)
5. [Feature Migration Map](#feature-migration-map)
6. [Detailed Implementation Steps](#detailed-implementation-steps)
7. [Testing Strategy](#testing-strategy)
8. [Migration Checklist](#migration-checklist)
9. [Risk Mitigation](#risk-mitigation)

---

## Gap Analysis

### Current State Assessment

**Strengths:**
- ✅ Well-documented 5-stage modular pipeline
- ✅ Comprehensive schema system (5 financial statement types)
- ✅ Direct parsing engines (100% data accuracy)
- ✅ Enterprise output management with run tracking
- ✅ Cross-platform path handling (Windows/WSL)
- ✅ Professional logging system
- ✅ Cost-optimized (PyMuPDF detection before LLMWhisperer)

**Gaps vs. AI-Optimized Target:**

| Area | Current State | Target State | Priority |
|------|--------------|--------------|----------|
| **Architecture** | Layered pipeline stages | Vertical slice features | 🔴 High |
| **Type Safety** | Partial type hints | Strict MyPy + Pyright | 🔴 High |
| **Logging** | Custom logger, unstructured | structlog, JSON, dotted namespace | 🔴 High |
| **Testing** | Minimal test infrastructure | pytest + async + integration | 🔴 High |
| **API Layer** | CLI/script only | FastAPI REST API + Swagger | 🔴 High |
| **Database** | File-based only | Hybrid: PostgreSQL + files | 🟡 Medium |
| **Validation** | Manual testing | Automated: Ruff + MyPy + Pyright | 🔴 High |
| **Documentation** | Extensive markdown | + OpenAPI, docstrings, CLAUDE.md | 🟡 Medium |
| **Error Handling** | Try/except patterns | Global handlers + custom exceptions | 🟡 Medium |
| **Health Checks** | None | /health, /health/db, /health/ready | 🟡 Medium |
| **Containerization** | None | Docker multi-stage builds | 🟢 Low |
| **Migrations** | N/A | Alembic async migrations | 🟡 Medium |

### Critical Incompatibilities

**1. Console Logging → Structured Logging**
- Current: Custom `pipeline_logger.py` with print statements
- Target: `structlog` with JSON output and dotted namespace events
- Strategy: Complete replacement, AST Grep to find all logger usage

**2. File Paths → Centralized Config**
- Current: `project_paths.py` with manual path construction
- Target: Pydantic Settings with `.env` configuration
- Strategy: Migrate path logic, use AST Grep for path references

**3. Direct Script Execution → FastAPI Lifecycle**
- Current: `main.py` runs pipeline directly
- Target: FastAPI app with lifespan events, background tasks
- Strategy: Wrap pipeline stages as async services

**4. Schema Registry → Vertical Slice Models**
- Current: Central `schemas/` directory with all statement types
- Target: Feature-specific models in each slice
- Strategy: Extract schemas into feature directories

---

## Target Architecture

### Directory Structure

```
llm-financial-pipeline/
├── .claude/                          # Claude Code configuration
│   ├── commands/
│   │   ├── commit.md                # Atomic commit command
│   │   ├── validate.md              # Full validation suite
│   │   └── check-ignore-comments.md # Type suppression review
│   └── skills/                      # Optional: AST Grep skill
│
├── .agents/                         # AI agent context (gitignored)
│   ├── external-docs/               # Reference documentation
│   └── reports/                     # Analysis reports
│
├── app/
│   ├── core/                        # Universal infrastructure
│   │   ├── config.py                # Pydantic settings from .env
│   │   ├── database.py              # Async SQLAlchemy + session management
│   │   ├── logging.py               # structlog with request correlation
│   │   ├── middleware.py            # Request logging, CORS
│   │   ├── exceptions.py            # Global exception handlers
│   │   ├── health.py                # Health check endpoints
│   │   └── tests/                   # Core infrastructure tests
│   │
│   ├── shared/                      # Cross-feature utilities (3+ features)
│   │   ├── models.py                # TimestampMixin, base models
│   │   ├── schemas.py               # PaginationParams, ErrorResponse
│   │   ├── utils.py                 # Date/time utilities
│   │   └── tests/                   # Shared utilities tests
│   │
│   ├── llm/                         # LLM infrastructure
│   │   ├── clients.py               # LLMWhisperer client wrapper
│   │   ├── schemas.py               # LLM-specific schemas
│   │   └── cache.py                 # Extraction result caching
│   │
│   ├── detection/                   # Feature: Table Detection (was pipeline_02)
│   │   ├── routes.py                # POST /api/detection/analyze
│   │   ├── service.py               # PyMuPDF detection logic
│   │   ├── models.py                # DetectionResult DB model
│   │   ├── schemas.py               # Request/response schemas
│   │   ├── detector.py              # Core detection algorithm
│   │   ├── tests/                   # Feature-specific tests
│   │   └── README.md                # Feature documentation
│   │
│   ├── extraction/                  # Feature: Data Extraction (was pipeline_03)
│   │   ├── routes.py                # POST /api/extraction/extract
│   │   ├── service.py               # Orchestrates extraction workflow
│   │   ├── models.py                # ExtractionJob, RawExtract DB models
│   │   ├── schemas.py               # Request/response schemas
│   │   ├── extractors/              # Extraction engines
│   │   │   ├── targeted.py          # LLMWhisperer targeted extraction
│   │   │   ├── direct_parser.py     # Direct parsing base class
│   │   │   └── schema_processor.py  # Schema-based processing
│   │   ├── parsers/                 # Statement-specific parsers
│   │   │   ├── income_statement.py
│   │   │   ├── balance_sheet.py
│   │   │   ├── cash_flow.py
│   │   │   ├── comprehensive_income.py
│   │   │   └── shareholders_equity.py
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── statements/                  # Feature: Financial Statements (was schemas/)
│   │   ├── routes.py                # GET /api/statements, CRUD operations
│   │   ├── service.py               # Statement CRUD logic
│   │   ├── models.py                # FinancialStatement, LineItem DB models
│   │   ├── schemas/                 # Statement type schemas
│   │   │   ├── base.py              # BaseFinancialSchema
│   │   │   ├── income_statement.py  # IncomeStatementSchema
│   │   │   ├── balance_sheet.py     # BalanceSheetSchema
│   │   │   ├── cash_flow.py         # CashFlowSchema
│   │   │   ├── comprehensive_income.py
│   │   │   └── shareholders_equity.py
│   │   ├── detector.py              # Document type detection
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── consolidation/               # Feature: Data Consolidation (was pipeline_04/05)
│   │   ├── routes.py                # POST /api/consolidation/merge
│   │   ├── service.py               # Intelligent consolidation logic
│   │   ├── models.py                # ConsolidationJob DB model
│   │   ├── schemas.py               # Request/response schemas
│   │   ├── merger.py                # Multi-PDF consolidation
│   │   ├── excel_exporter.py        # Excel export engine
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── jobs/                        # Feature: Pipeline Orchestration (was main.py)
│   │   ├── routes.py                # POST /api/jobs/run, GET /api/jobs/{id}
│   │   ├── service.py               # Orchestrates full pipeline
│   │   ├── models.py                # PipelineJob, JobStatus DB models
│   │   ├── schemas.py               # Job request/response schemas
│   │   ├── orchestrator.py          # End-to-end pipeline logic
│   │   ├── tasks.py                 # Background async tasks
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── main.py                      # FastAPI application entry point
│   └── __init__.py
│
├── tests/                           # Integration & E2E tests
│   ├── conftest.py                  # Test fixtures (DB, client)
│   ├── integration/                 # Cross-feature integration tests
│   │   ├── test_full_pipeline.py
│   │   ├── test_extraction_flow.py
│   │   └── test_consolidation_flow.py
│   └── e2e/                         # End-to-end scenarios
│       └── test_nvidia_10k.py       # Real NVIDIA 10K processing
│
├── alembic/                         # Database migrations
│   ├── env.py                       # Async migration environment
│   ├── versions/                    # Migration files
│   └── script.py.mako
│
├── input/                           # PDF input files (preserved)
├── output/                          # Pipeline outputs (preserved structure)
│   ├── runs/                        # Run-specific outputs
│   ├── cache/                       # LLMWhisperer cache
│   └── STATUS.json
│
├── docs/                            # Documentation
│   ├── logging-standard.md          # Event taxonomy
│   ├── api-guide.md                 # API usage guide
│   └── architecture.md              # Architecture overview
│
├── migration_backup/                # Safety backup during migration
├── dump/                            # Preserved legacy code for reference
│
├── .env.example                     # Environment template
├── .env                             # Local environment (gitignored)
├── .dockerignore
├── .gitignore
├── .python-version                  # Python 3.12
├── alembic.ini                      # Alembic configuration
├── docker-compose.yml               # Local development services
├── Dockerfile                       # Multi-stage production build
├── pyproject.toml                   # Dependencies + tooling config
├── uv.lock                          # Locked dependencies
├── CLAUDE.md                        # Claude Code project guide
├── README.md                        # Project overview
└── REFACTORING_PLAN.md             # This document
```

### Vertical Slice Features

Each feature slice is self-contained with:
- **routes.py**: FastAPI endpoints
- **service.py**: Business logic orchestration
- **models.py**: SQLAlchemy database models
- **schemas.py**: Pydantic request/response validation
- **tests/**: Feature-specific unit tests
- **README.md**: Feature documentation (flows, rules, integration points)

**Feature Mapping:**

| New Feature Slice | Current Components | Responsibility |
|-------------------|-------------------|----------------|
| **detection/** | `pipeline_02_table_detection/`, `pipeline_02_1_ai_detector.py` | AI-powered table detection using PyMuPDF |
| **extraction/** | `pipeline_03_extraction/`, `parsers/`, `utilities/financial_table_extractor.py` | LLMWhisperer extraction + direct parsing |
| **statements/** | `schemas/`, document detection | Financial statement schemas + type detection |
| **consolidation/** | `pipeline_04_processing/`, `pipeline_05_consolidation/`, `schemas/excel_exporter.py` | Multi-PDF consolidation + Excel export |
| **jobs/** | `main.py`, `pipeline_01_input_discovery/` | Full pipeline orchestration + job management |

---

## Implementation Phases

### Phase 1: Foundation Infrastructure (Week 1, Days 1-3)

**Objective:** Set up AI-optimized infrastructure before any features

**Steps:**

1. **Initialize New Project Structure**
   - Use FastAPI starter template as base
   - `uv init llm-financial-pipeline`
   - Install core dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic-settings`, `structlog`
   - Install dev dependencies: `ruff`, `mypy`, `pyright`, `pytest`, `pytest-asyncio`, `httpx`

2. **Configure Tooling & Validation**
   - Set up `pyproject.toml` with strict linting/typing rules
   - Configure Ruff: line length 100, strict mode, security checks
   - Configure MyPy: strict mode, disallow untyped defs
   - Configure Pyright: strict mode, all diagnostic rules
   - pytest configuration: async mode auto, integration markers

3. **Core Infrastructure (`app/core/`)**
   - `config.py`: Pydantic Settings (DATABASE_URL, LOG_LEVEL, API keys, file paths)
   - `logging.py`: structlog with JSON output, request correlation, dotted namespace
   - `database.py`: Async SQLAlchemy engine, Base model, session management
   - `middleware.py`: Request logging middleware with correlation IDs
   - `exceptions.py`: Custom exception classes + global handlers
   - `health.py`: Health check endpoints (/health, /health/db, /health/ready)

4. **Shared Utilities (`app/shared/`)**
   - `models.py`: TimestampMixin for created_at/updated_at
   - `schemas.py`: PaginationParams, PaginatedResponse, ErrorResponse
   - `utils.py`: Date/time helpers (utcnow, format_iso)

5. **FastAPI Application (`app/main.py`)**
   - Create FastAPI app with lifespan events
   - Setup middleware (request logging, CORS)
   - Register exception handlers
   - Include health router
   - Configure Swagger UI

6. **Database Setup**
   - Initialize Alembic for migrations
   - Configure async migration environment
   - Create PostgreSQL tables schema (initial migration)

7. **Docker Configuration**
   - `docker-compose.yml`: PostgreSQL service + app service
   - `Dockerfile`: Multi-stage build with uv
   - `.dockerignore`: Exclude .venv, cache directories

8. **Validation & Testing**
   - Write tests for core infrastructure
   - Ensure all tooling passes (Ruff, MyPy, Pyright)
   - Test Docker build and services
   - Validate health endpoints

**Deliverables:**
- ✅ FastAPI application running on port 8123
- ✅ PostgreSQL database accessible
- ✅ Health endpoints responding
- ✅ All linters/type checkers passing
- ✅ Core infrastructure tests passing
- ✅ Docker services running successfully

---

### Phase 2: LLM Infrastructure (Week 1, Days 4-5)

**Objective:** Set up LLMWhisperer client and caching infrastructure

**Steps:**

1. **LLM Module (`app/llm/`)**
   - `clients.py`: LLMWhispererClient wrapper with unified interface
   - `schemas.py`: ExtractionRequest, ExtractionResponse schemas
   - `cache.py`: File-based caching for raw extraction results
   - `config.py`: LLM-specific settings (API key, cache path, retry config)

2. **Client Wrapper Pattern**
   ```python
   class LLMWhispererClient:
       """Wrapper for LLMWhisperer with caching and retry logic."""

       async def extract_text(self, file_path: str, ...) -> ExtractionResult:
           # Check cache first
           # Call LLMWhisperer API if not cached
           # Save to cache
           # Return structured result
   ```

3. **File Cache Strategy**
   - Cache structure: `output/cache/{pdf_hash}/{page_range}.txt`
   - Metadata: `output/cache/{pdf_hash}/metadata.json`
   - Preserve existing cache compatibility

4. **Testing**
   - Mock LLMWhisperer API responses
   - Test caching logic (hit/miss scenarios)
   - Test retry mechanisms
   - Integration test with real API (optional, cost consideration)

**Deliverables:**
- ✅ LLMWhisperer client wrapper tested
- ✅ Caching system functional
- ✅ Compatible with existing cached data
- ✅ All tests passing

---

### Phase 3: Detection Feature (Week 2, Days 1-2)

**Objective:** Migrate table detection to vertical slice architecture

**Steps:**

1. **Database Models (`app/detection/models.py`)**
   ```python
   class DetectionJob(Base, TimestampMixin):
       id: UUID primary key
       pdf_path: str
       status: enum (pending, processing, completed, failed)
       detected_pages: JSON (list of page numbers with confidence scores)
       error_message: str (nullable)
   ```

2. **Pydantic Schemas (`app/detection/schemas.py`)**
   - `DetectionRequest`: PDF path, detection parameters
   - `DetectionResponse`: Job ID, detected pages, confidence scores
   - `PageDetection`: Page number, table type, confidence

3. **Service Layer (`app/detection/service.py`)**
   - Migrate `pipeline_02_detect_tables.py` logic
   - Use async/await patterns
   - Structured logging with events: `detection.analyze_started`, `detection.analyze_completed`
   - Error handling with custom exceptions

4. **Detector Engine (`app/detection/detector.py`)**
   - Migrate `pipeline_02_1_ai_detector.py` logic
   - 3-step validation: keyword search → structural validation → content disambiguation
   - PyMuPDF integration (cost-free)

5. **FastAPI Routes (`app/detection/routes.py`)**
   - `POST /api/detection/analyze`: Submit PDF for detection
   - `GET /api/detection/jobs/{job_id}`: Get detection results
   - `GET /api/detection/jobs`: List detection jobs (with pagination)

6. **Alembic Migration**
   - Create `detection_jobs` table migration

7. **Testing**
   - Unit tests for detection logic
   - Integration tests with test PDFs
   - API endpoint tests

**Deliverables:**
- ✅ Detection feature fully migrated
- ✅ API endpoints functional
- ✅ Database persistence working
- ✅ All tests passing

---

### Phase 4: Statements Feature (Week 2, Days 3-4)

**Objective:** Migrate schema system to vertical slice

**Steps:**

1. **Database Models (`app/statements/models.py`)**
   ```python
   class FinancialStatement(Base, TimestampMixin):
       id: UUID primary key
       document_type: enum (income_statement, balance_sheet, cash_flow, etc.)
       reporting_period_start: date
       reporting_period_end: date
       company_name: str
       metadata: JSON
       extraction_job_id: UUID (foreign key)

   class LineItem(Base, TimestampMixin):
       id: UUID primary key
       statement_id: UUID (foreign key)
       account_name: str
       value: Decimal
       indent_level: int
       parent_section: str
       line_order: int
   ```

2. **Schema Migration (`app/statements/schemas/`)**
   - Migrate all 5 financial statement schemas from `schemas/`
   - Keep Pydantic validation logic
   - Update imports to new structure
   - Use AST Grep to find all schema references in codebase

3. **Document Detector (`app/statements/detector.py`)**
   - Migrate `document_detector.py` logic
   - Keyword-based detection with confidence scoring

4. **Service Layer (`app/statements/service.py`)**
   - CRUD operations for financial statements
   - Type detection workflow
   - Schema validation and categorization

5. **FastAPI Routes (`app/statements/routes.py`)**
   - `POST /api/statements`: Create financial statement
   - `GET /api/statements/{id}`: Retrieve statement
   - `GET /api/statements`: List statements (paginated)
   - `PUT /api/statements/{id}`: Update statement
   - `DELETE /api/statements/{id}`: Delete statement (soft delete)

6. **Alembic Migration**
   - Create `financial_statements` and `line_items` tables

7. **Testing**
   - Test schema validation for all 5 statement types
   - Test document type detection
   - Test CRUD operations
   - Test API endpoints

**Deliverables:**
- ✅ Statements feature fully migrated
- ✅ All 5 schema types working
- ✅ Document detection functional
- ✅ API endpoints tested
- ✅ Database persistence complete

---

### Phase 5: Extraction Feature (Week 2, Days 5-7)

**Objective:** Migrate extraction pipeline to vertical slice

**Steps:**

1. **Database Models (`app/extraction/models.py`)**
   ```python
   class ExtractionJob(Base, TimestampMixin):
       id: UUID primary key
       pdf_path: str
       detection_job_id: UUID (foreign key)
       status: enum
       extracted_pages: JSON
       schema_type: str
       error_message: str (nullable)

   class RawExtract(Base, TimestampMixin):
       id: UUID primary key
       extraction_job_id: UUID (foreign key)
       page_number: int
       raw_text: Text
       cache_path: str
   ```

2. **Extractors Module (`app/extraction/extractors/`)**
   - Migrate `pipeline_03_1_targeted_extractor.py` → `targeted.py`
   - Migrate `pipeline_03_2_schema_processor.py` → `schema_processor.py`
   - Create base `DirectParser` class

3. **Parsers Module (`app/extraction/parsers/`)**
   - Migrate all 5 direct parsers from `parsers/`:
     - `direct_income_statement_parser.py` → `income_statement.py`
     - `direct_balance_sheet_parser.py` → `balance_sheet.py`
     - `direct_cash_flow_parser.py` → `cash_flow.py`
     - `direct_comprehensive_income_parser.py` → `comprehensive_income.py`
     - `direct_shareholders_equity_parser.py` → `shareholders_equity.py`
   - Preserve 100% data accuracy (direct parsing logic)
   - Add type hints and async support

4. **Service Layer (`app/extraction/service.py`)**
   - Orchestrate extraction workflow:
     1. Get detection results
     2. Call LLMWhisperer for targeted pages
     3. Run direct parser for detected schema type
     4. Validate against Pydantic schema
     5. Save to database
     6. Cache raw text
   - Structured logging for each step
   - Error handling and retry logic

5. **FastAPI Routes (`app/extraction/routes.py`)**
   - `POST /api/extraction/extract`: Submit extraction job
   - `GET /api/extraction/jobs/{job_id}`: Get extraction results
   - `POST /api/extraction/parse`: Parse existing raw text
   - `GET /api/extraction/cache/{pdf_hash}`: Retrieve cached extracts

6. **Alembic Migration**
   - Create `extraction_jobs` and `raw_extracts` tables

7. **Testing**
   - Test each parser with known good data
   - Test LLMWhisperer integration (mocked)
   - Test extraction workflow end-to-end
   - Test caching behavior
   - Integration tests with real PDFs

**Deliverables:**
- ✅ Extraction feature fully migrated
- ✅ All 5 parsers working with 100% accuracy
- ✅ LLMWhisperer integration tested
- ✅ Caching system validated
- ✅ API endpoints functional

---

### Phase 6: Consolidation Feature (Week 3, Days 1-2)

**Objective:** Migrate consolidation and Excel export

**Steps:**

1. **Database Models (`app/consolidation/models.py`)**
   ```python
   class ConsolidationJob(Base, TimestampMixin):
       id: UUID primary key
       statement_ids: ARRAY[UUID] (statements to consolidate)
       status: enum
       consolidated_statement_id: UUID (result)
       excel_path: str
       summary: JSON (consolidation details)
   ```

2. **Merger Module (`app/consolidation/merger.py`)**
   - Migrate `pipeline_03_3_intelligent_merger.py` logic
   - Migrate `pipeline_04_2_universal_consolidator.py` logic
   - Fuzzy matching for account names
   - Multi-PDF consolidation

3. **Excel Exporter (`app/consolidation/excel_exporter.py`)**
   - Migrate `schemas/excel_exporter.py`
   - Schema-driven Excel export
   - Visual indentation formatting
   - Multi-sheet support

4. **Service Layer (`app/consolidation/service.py`)**
   - Orchestrate consolidation workflow
   - Generate consolidation summary
   - Export to Excel with formatting

5. **FastAPI Routes (`app/consolidation/routes.py`)**
   - `POST /api/consolidation/merge`: Submit consolidation job
   - `GET /api/consolidation/jobs/{job_id}`: Get results
   - `GET /api/consolidation/download/{job_id}`: Download Excel file

6. **Alembic Migration**
   - Create `consolidation_jobs` table

7. **Testing**
   - Test multi-statement consolidation
   - Test fuzzy account matching
   - Test Excel export formatting
   - Verify consolidation summaries

**Deliverables:**
- ✅ Consolidation feature migrated
- ✅ Excel export functional
- ✅ Multi-PDF merging tested
- ✅ API endpoints working

---

### Phase 7: Jobs Orchestration (Week 3, Days 3-4)

**Objective:** Create full pipeline orchestration feature

**Steps:**

1. **Database Models (`app/jobs/models.py`)**
   ```python
   class PipelineJob(Base, TimestampMixin):
       id: UUID primary key
       input_pdfs: ARRAY[str]
       status: enum (queued, running, completed, failed)
       detection_job_id: UUID
       extraction_job_ids: ARRAY[UUID]
       consolidation_job_id: UUID
       output_path: str
       run_summary: JSON
       error_message: str (nullable)
   ```

2. **Orchestrator (`app/jobs/orchestrator.py`)**
   - Migrate `main.py` pipeline logic
   - Async workflow:
     1. Scan input folder → Detection → Extraction → Consolidation
   - Progress tracking
   - Error recovery

3. **Background Tasks (`app/jobs/tasks.py`)**
   - Celery/ARQ integration (optional for async processing)
   - Or use FastAPI BackgroundTasks for simple workflows

4. **Service Layer (`app/jobs/service.py`)**
   - Job submission and management
   - Status monitoring
   - Output retrieval

5. **FastAPI Routes (`app/jobs/routes.py`)**
   - `POST /api/jobs/run`: Submit full pipeline job
   - `GET /api/jobs/{job_id}`: Get job status and results
   - `GET /api/jobs`: List all jobs (paginated)
   - `DELETE /api/jobs/{job_id}`: Cancel running job

6. **Input Discovery**
   - Migrate `pipeline_01_read_input.py` logic
   - Scan input folder for PDFs
   - Validate PDF files

7. **Output Management**
   - Migrate `pipeline_01_2_enterprise_manager.py` logic
   - Run tracking with unique IDs
   - STATUS.json, METADATA.json generation
   - Preserve output structure

8. **Alembic Migration**
   - Create `pipeline_jobs` table

9. **Testing**
   - Test full pipeline with NVIDIA test data
   - Test error handling at each stage
   - Test status updates and progress tracking
   - Integration tests end-to-end

**Deliverables:**
- ✅ Jobs feature complete
- ✅ Full pipeline orchestration working
- ✅ Output management preserved
- ✅ End-to-end tests passing

---

### Phase 8: Testing & Documentation (Week 3, Days 5-7)

**Objective:** Comprehensive testing and documentation

**Steps:**

1. **Integration Tests (`tests/integration/`)**
   - `test_full_pipeline.py`: Complete NVIDIA 10K workflow
   - `test_extraction_flow.py`: Detection → Extraction
   - `test_consolidation_flow.py`: Multi-PDF consolidation

2. **E2E Tests (`tests/e2e/`)**
   - `test_nvidia_10k.py`: Real-world NVIDIA processing
   - Verify output matches expected results
   - Performance benchmarks

3. **API Documentation**
   - Ensure all endpoints have docstrings
   - OpenAPI schema validation
   - Add usage examples to Swagger UI

4. **Feature READMEs**
   - Document each feature slice:
     - Key flows
     - Database schema
     - Business rules
     - Integration points
   - Following vertical slice documentation pattern

5. **CLAUDE.md**
   - Create comprehensive guide for AI agents
   - Document architecture decisions
   - List essential commands
   - Explain logging patterns
   - Include troubleshooting guide

6. **Migration Guide**
   - Document differences from old structure
   - Provide migration examples
   - Explain new patterns

7. **Logging Standard (`docs/logging-standard.md`)**
   - Define event taxonomy
   - Provide examples for each domain
   - Explain hybrid dotted namespace pattern

**Deliverables:**
- ✅ All tests passing (unit + integration + e2e)
- ✅ Test coverage > 80%
- ✅ Complete API documentation
- ✅ All READMEs written
- ✅ CLAUDE.md comprehensive
- ✅ Logging standard defined

---

### Phase 9: Validation & Polish (Week 4, Days 1-2)

**Objective:** Final validation and production readiness

**Steps:**

1. **Slash Commands**
   - Create `/commit` command for atomic commits
   - Create `/validate` command for full validation suite
   - Create `/check-ignore-comments` for type suppression review

2. **CI/CD Validation**
   - Ensure all tests pass: `pytest -v`
   - Ensure type checking passes: `mypy app/`, `pyright app/`
   - Ensure linting passes: `ruff check .`
   - Docker build succeeds
   - Docker services start successfully

3. **Performance Testing**
   - Benchmark pipeline performance
   - Compare with original implementation
   - Optimize slow queries

4. **Security Review**
   - Review SQL injection risks
   - Check authentication/authorization (if needed)
   - Validate input sanitization
   - Review secret management

5. **Production Configuration**
   - Production `.env.example` with all variables
   - Docker production configuration
   - Database migration strategy
   - Backup and recovery plan

**Deliverables:**
- ✅ All validation passing
- ✅ Performance acceptable
- ✅ Security review complete
- ✅ Production config ready

---

### Phase 10: Migration & Deployment (Week 4, Days 3-5)

**Objective:** Deploy new system and verify

**Steps:**

1. **Data Migration**
   - Migrate existing output data to database (optional)
   - Preserve file-based outputs as backup
   - Validate data integrity

2. **Parallel Running**
   - Run old and new systems side-by-side
   - Compare outputs for consistency
   - Identify discrepancies

3. **Cutover**
   - Switch primary system to new architecture
   - Archive old codebase to `migration_backup/`
   - Update documentation

4. **Monitoring**
   - Monitor logs for errors
   - Track API usage
   - Monitor database performance

5. **User Training**
   - Document new API usage
   - Provide migration examples
   - Answer questions

**Deliverables:**
- ✅ New system deployed
- ✅ Old system archived
- ✅ Data migrated and validated
- ✅ Users trained
- ✅ Monitoring in place

---

## AST Grep Refactoring Strategy

AST Grep ensures we find 100% of code patterns during refactoring, preventing missed instances that cause runtime errors.

### Installation

```bash
# Install AST Grep
cargo install ast-grep

# Or add as Claude Code skill
mkdir -p .claude/skills/ast-grep
# Add skill.md with AST Grep documentation
```

### Critical Refactoring Patterns

#### 1. Logging Migration: Console → structlog

**Find all logger usage:**

```bash
# Pattern 1: Find all logger.info/error/warning calls
ast-grep --pattern 'logger.$METHOD($$$)' --output-mode content

# Pattern 2: Find logger initialization
ast-grep --pattern '$VAR = get_logger($$$)' --output-mode files_with_matches

# Pattern 3: Find print statements (debugging code)
ast-grep --pattern 'print($$$)' --output-mode content
```

**Verification after migration:**

```bash
# Ensure no old logger usage remains
ast-grep --pattern 'from app.core.pipeline_logger import $$$'
# Expected: 0 matches

# Verify new logger usage
ast-grep --pattern 'from app.core.logging import get_logger'
# Expected: All feature files
```

#### 2. Path Management: project_paths.py → config.py

**Find all path references:**

```bash
# Pattern 1: Find all imports from project_paths
ast-grep --pattern 'from $MODULE.project_paths import $$$' --output-mode content

# Pattern 2: Find all path construction
ast-grep --pattern 'os.path.join($$$)' --output-mode content

# Pattern 3: Find hardcoded paths
ast-grep --pattern '"$PATH"' --glob "**/*.py" | grep -E '(input/|output/|dump/)'
```

**Replacement:**

```python
# Before
from core.project_paths import INPUT_PATH, OUTPUT_PATH

# After
from app.core.config import get_settings
settings = get_settings()
input_path = settings.input_path
output_path = settings.output_path
```

#### 3. Schema Imports: Central → Feature-Specific

**Find all schema imports:**

```bash
# Find all schema imports
ast-grep --pattern 'from schemas.$MODULE import $$$' --output-mode content

# Find specific schema usage
ast-grep --pattern 'IncomeStatementSchema' --output-mode files_with_matches
ast-grep --pattern 'BalanceSheetSchema' --output-mode files_with_matches
```

**Replacement mapping:**

```python
# Before
from schemas.income_statement_schema import IncomeStatementSchema

# After
from app.statements.schemas.income_statement import IncomeStatementSchema
```

#### 4. Exception Handling: Custom Exceptions

**Find all try/except blocks:**

```bash
# Find all generic Exception catches
ast-grep --pattern 'except Exception as $VAR: $$$' --output-mode content

# Find all raise statements
ast-grep --pattern 'raise Exception($$$)' --output-mode content

# Find specific exception types to migrate
ast-grep --pattern 'except $EXCEPTION: $$$' --output-mode content
```

**Create custom exceptions:**

```python
# app/detection/exceptions.py
class DetectionError(Exception):
    """Base exception for detection errors."""
    pass

class PDFNotFoundError(DetectionError):
    """Raised when PDF file not found."""
    pass

class DetectionTimeoutError(DetectionError):
    """Raised when detection times out."""
    pass
```

#### 5. Async Conversion: Sync → Async

**Find all synchronous file operations:**

```bash
# Find synchronous file reads
ast-grep --pattern 'open($$$)' --output-mode content

# Find synchronous database queries (if any future DB usage)
ast-grep --pattern 'session.query($$$)' --output-mode content

# Find blocking operations in functions
ast-grep --pattern 'def $NAME($$$): $$$ $BLOCKING_CALL $$$' --output-mode content
```

**Conversion pattern:**

```python
# Before
def read_file(path):
    with open(path, 'r') as f:
        return f.read()

# After
async def read_file(path):
    async with aiofiles.open(path, 'r') as f:
        return await f.read()
```

### AST Grep Validation Workflow

**Step 1: Discovery (Find all instances)**

```bash
# Run comprehensive search for pattern
ast-grep --pattern '<pattern>' --output-mode content > migration_targets.txt

# Count instances
ast-grep --pattern '<pattern>' --output-mode files_with_matches | wc -l
```

**Step 2: Migration (Refactor each instance)**

- Use AST Grep output as checklist
- Refactor each file
- Mark as complete in tracking document

**Step 3: Verification (Ensure zero missed)**

```bash
# Verify old pattern is gone
ast-grep --pattern '<old_pattern>'
# Expected: 0 matches

# Verify new pattern exists
ast-grep --pattern '<new_pattern>' | wc -l
# Expected: Same count as Step 1
```

**Step 4: CI/CD Enforcement (Prevent regressions)**

```yaml
# .github/workflows/ast-grep-checks.yml
- name: Check for old logger usage
  run: |
    if ast-grep --pattern 'from core.pipeline_logger import $$$'; then
      echo "Error: Found old logger imports"
      exit 1
    fi

- name: Check for hardcoded paths
  run: |
    if ast-grep --pattern '"input/"' --glob "app/**/*.py"; then
      echo "Error: Found hardcoded paths"
      exit 1
    fi
```

---

## Feature Migration Map

Detailed mapping of current components → new vertical slices

### Migration Table

| Current File | Lines | Target Location | Migration Complexity | Notes |
|--------------|-------|----------------|----------------------|-------|
| **Core Infrastructure** |
| `core/project_paths.py` | 146 | `app/core/config.py` | 🟡 Medium | Merge into Pydantic Settings |
| `core/pipeline_logger.py` | 10.8KB | `app/core/logging.py` | 🔴 High | Complete replacement with structlog |
| `core/cross_platform_paths.py` | 12.4KB | `app/core/config.py` + utils | 🟡 Medium | Integrate path normalization |
| `core/migration_safety.py` | 12.6KB | Archive (no longer needed) | 🟢 Low | One-time migration tool |
| `core/pipeline_01_2_enterprise_manager.py` | 36.8KB | `app/jobs/output_manager.py` | 🟡 Medium | Preserve output structure |
| **Detection Feature** |
| `pipeline_02_table_detection/pipeline_02_detect_tables.py` | 1,865 lines | `app/detection/service.py` + `detector.py` | 🔴 High | Major refactor to async |
| `pipeline_02_table_detection/pipeline_02_1_ai_detector.py` | 15.8KB | `app/detection/detector.py` | 🟡 Medium | Extract core algorithm |
| **Extraction Feature** |
| `pipeline_03_extraction/pipeline_03_extract_tables.py` | 673 lines | `app/extraction/service.py` | 🔴 High | Orchestration layer |
| `pipeline_03_extraction/pipeline_03_1_targeted_extractor.py` | 26.6KB | `app/extraction/extractors/targeted.py` | 🟡 Medium | LLMWhisperer integration |
| `pipeline_03_extraction/pipeline_03_2_schema_processor.py` | 31KB | `app/extraction/extractors/schema_processor.py` | 🟡 Medium | Schema validation |
| `pipeline_03_extraction/pipeline_03_3_intelligent_merger.py` | 36.1KB | `app/consolidation/merger.py` | 🟡 Medium | Consolidation logic |
| `utilities/financial_table_extractor.py` | 48.1KB | `app/llm/clients.py` | 🔴 High | Extract to LLM module |
| **Parser Migration** |
| `parsers/direct_income_statement_parser.py` | 12.4KB | `app/extraction/parsers/income_statement.py` | 🟢 Low | Direct copy + type hints |
| `parsers/direct_balance_sheet_parser.py` | 14.6KB | `app/extraction/parsers/balance_sheet.py` | 🟢 Low | Direct copy + type hints |
| `parsers/direct_cash_flow_parser.py` | 15.9KB | `app/extraction/parsers/cash_flow.py` | 🟢 Low | Direct copy + type hints |
| `parsers/direct_comprehensive_income_parser.py` | 13.4KB | `app/extraction/parsers/comprehensive_income.py` | 🟢 Low | Direct copy + type hints |
| `parsers/direct_shareholders_equity_parser.py` | 10KB | `app/extraction/parsers/shareholders_equity.py` | 🟢 Low | Direct copy + type hints |
| **Schema Migration** |
| `schemas/__init__.py` | - | `app/statements/schemas/__init__.py` | 🟢 Low | Update imports |
| `schemas/base_schema.py` | 102 lines | `app/statements/schemas/base.py` | 🟢 Low | Direct copy |
| `schemas/document_detector.py` | - | `app/statements/detector.py` | 🟢 Low | Direct copy + tests |
| `schemas/excel_exporter.py` | 20.6KB | `app/consolidation/excel_exporter.py` | 🟡 Medium | Preserve formatting logic |
| `schemas/income_statement_schema.py` | - | `app/statements/schemas/income_statement.py` | 🟢 Low | Direct copy |
| `schemas/balance_sheet_schema.py` | - | `app/statements/schemas/balance_sheet.py` | 🟢 Low | Direct copy |
| `schemas/cash_flow_schema.py` | - | `app/statements/schemas/cash_flow.py` | 🟢 Low | Direct copy |
| `schemas/comprehensive_income_schema.py` | - | `app/statements/schemas/comprehensive_income.py` | 🟢 Low | Direct copy |
| `schemas/shareholders_equity_schema.py` | - | `app/statements/schemas/shareholders_equity.py` | 🟢 Low | Direct copy |
| **Processing & Consolidation** |
| `pipeline_04_processing/pipeline_04_process_all_pdfs.py` | 12KB | `app/jobs/orchestrator.py` | 🟡 Medium | Merge into orchestration |
| `pipeline_04_processing/pipeline_04_2_universal_consolidator.py` | 40.6KB | `app/consolidation/service.py` | 🟡 Medium | Fuzzy matching logic |
| `pipeline_05_consolidation/pipeline_05_merge_excel_files.py` | 29.2KB | `app/consolidation/excel_merger.py` | 🟡 Medium | Excel consolidation |
| **Input Discovery** |
| `pipeline_01_input_discovery/pipeline_01_read_input.py` | 177 lines | `app/jobs/input_scanner.py` | 🟢 Low | PDF scanning logic |
| **Main Orchestration** |
| `main.py` | 276 lines | `app/jobs/orchestrator.py` + `app/main.py` | 🔴 High | Split: FastAPI app + pipeline logic |

**Complexity Legend:**
- 🟢 Low: Direct copy with minimal changes (type hints, imports)
- 🟡 Medium: Moderate refactoring (async patterns, new structure)
- 🔴 High: Major refactoring (architecture changes, new patterns)

### Preserved Components

These components are **preserved as-is** in the new structure:

- `input/` directory → Unchanged
- `output/runs/` structure → Maintained for compatibility
- `dump/` archived code → Reference only
- Test PDFs (NVIDIA 10K) → Same location
- `.env` structure → Expanded with new variables

---

## Detailed Implementation Steps

### Step-by-Step Guide for Each Phase

#### Phase 1 Implementation Details

**Day 1: Project Initialization**

```bash
# 1. Clone FastAPI starter template
git clone <fastapi-starter-repo> llm-financial-pipeline
cd llm-financial-pipeline

# 2. Initialize uv project
uv init

# 3. Install dependencies
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings structlog python-dotenv

# 4. Install dev dependencies
uv add --dev ruff mypy pyright pytest pytest-asyncio pytest-cov httpx

# 5. Create directory structure
mkdir -p app/core app/shared app/llm tests/integration tests/e2e
mkdir -p app/detection app/extraction app/statements app/consolidation app/jobs
mkdir -p alembic/versions docs .claude/commands

# 6. Initialize git
git init
git remote add origin <your-repo-url>
git add .
git commit -m "Initial project structure"
```

**Day 1-2: Core Infrastructure**

Create each file systematically:

1. **`app/core/config.py`**
   ```python
   from functools import lru_cache
   from pydantic_settings import BaseSettings, SettingsConfigDict
   from pathlib import Path

   class Settings(BaseSettings):
       model_config = SettingsConfigDict(
           env_file=".env",
           env_file_encoding="utf-8",
           case_sensitive=False
       )

       # Application
       app_name: str = "LLM Financial Pipeline"
       version: str = "2.0.0"
       environment: str = "development"
       log_level: str = "INFO"
       api_prefix: str = "/api"

       # Database
       database_url: str

       # Paths
       input_path: Path = Path("input")
       output_path: Path = Path("output")
       cache_path: Path = Path("output/cache")

       # LLMWhisperer
       llmwhisperer_api_key: str
       llmwhisperer_base_url: str = "https://api.llmwhisperer.com"

       # CORS
       allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8123"]

   @lru_cache()
   def get_settings() -> Settings:
       return Settings()
   ```

2. **`app/core/logging.py`**
   ```python
   import structlog
   from contextvars import ContextVar
   import uuid
   from typing import Any
   from app.core.config import get_settings

   request_id_var: ContextVar[str] = ContextVar("request_id", default="")

   def get_request_id() -> str:
       return request_id_var.get()

   def set_request_id(request_id: str | None = None) -> str:
       if not request_id:
           request_id = str(uuid.uuid4())
       request_id_var.set(request_id)
       return request_id

   def add_request_id(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
       request_id = get_request_id()
       if request_id:
           event_dict["request_id"] = request_id
       return event_dict

   def setup_logging(log_level: str = "INFO") -> None:
       structlog.configure(
           processors=[
               add_request_id,
               structlog.contextvars.merge_contextvars,
               structlog.processors.add_log_level,
               structlog.processors.TimeStamper(fmt="iso"),
               structlog.processors.StackInfoRenderer(),
               structlog.processors.format_exc_info,
               structlog.processors.JSONRenderer()
           ],
           wrapper_class=structlog.make_filtering_bound_logger(log_level),
           context_class=dict,
           logger_factory=structlog.PrintLoggerFactory(),
           cache_logger_on_first_use=True,
       )

   def get_logger(name: str) -> Any:
       return structlog.get_logger(name)
   ```

3. **`app/core/database.py`**
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import DeclarativeBase
   from typing import AsyncGenerator
   from app.core.config import get_settings

   settings = get_settings()

   engine = create_async_engine(
       settings.database_url,
       pool_pre_ping=True,
       pool_size=5,
       max_overflow=10,
       echo=settings.environment == "development"
   )

   AsyncSessionLocal = async_sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False,
       autocommit=False,
       autoflush=False,
   )

   class Base(DeclarativeBase):
       pass

   async def get_db() -> AsyncGenerator[AsyncSession, None]:
       async with AsyncSessionLocal() as session:
           try:
               yield session
           finally:
               await session.close()
   ```

Continue similarly for remaining core files...

**Day 2-3: Testing Setup**

1. **Configure pytest in `pyproject.toml`**
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   testpaths = ["app", "tests"]
   markers = [
       "integration: marks tests requiring real database",
   ]
   ```

2. **Create `tests/conftest.py`**
   ```python
   import pytest
   from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
   from app.core.config import get_settings

   @pytest.fixture(scope="function")
   async def test_db_engine():
       settings = get_settings()
       engine = create_async_engine(
           settings.database_url,
           pool_pre_ping=True,
           echo=False,
       )
       yield engine
       await engine.dispose()

   @pytest.fixture(scope="function")
   async def test_db_session(test_db_engine):
       async_session = async_sessionmaker(
           test_db_engine,
           class_=AsyncSession,
           expire_on_commit=False,
       )
       async with async_session() as session:
           yield session
   ```

3. **Write core infrastructure tests**

Continue this pattern for each phase...

---

## Testing Strategy

### Test Pyramid

```
       /\
      /E2E\      End-to-End: 5% (Full pipeline, real PDFs)
     /------\
    /  Integ \   Integration: 15% (Cross-feature, real DB)
   /----------\
  /    Unit    \ Unit: 80% (Feature-specific, mocked)
 /--------------\
```

### Test Categories

**1. Unit Tests (app/*/tests/)**
- Test individual functions and classes
- Mock external dependencies (DB, LLMWhisperer API, file system)
- Fast execution (< 1 second total)
- 80% of test suite

Example:
```python
# app/detection/tests/test_detector.py
def test_detect_financial_tables_from_text():
    detector = FinancialTableDetector()
    text = "Income Statement\nRevenue  $100"
    result = detector.detect(text)
    assert result.table_type == "income_statement"
    assert result.confidence > 0.8
```

**2. Integration Tests (tests/integration/)**
- Test feature interactions
- Use real database (test instance)
- Mock external APIs
- 15% of test suite

Example:
```python
# tests/integration/test_extraction_flow.py
@pytest.mark.integration
async def test_detection_to_extraction_flow(test_db_session):
    # Submit detection job
    detection_result = await detection_service.analyze(pdf_path)

    # Use detection results for extraction
    extraction_result = await extraction_service.extract(
        pdf_path,
        detected_pages=detection_result.pages
    )

    assert extraction_result.status == "completed"
```

**3. E2E Tests (tests/e2e/)**
- Test complete workflows
- Use real services (DB, file system)
- Real test data (NVIDIA 10K PDFs)
- 5% of test suite

Example:
```python
# tests/e2e/test_nvidia_10k.py
@pytest.mark.e2e
async def test_full_nvidia_10k_pipeline():
    # Run complete pipeline
    job = await pipeline_service.run(["input/NVIDIA 10K 2020-2019.pdf"])

    # Verify outputs
    assert job.status == "completed"
    assert Path(job.output_path).exists()

    # Verify extracted data matches expected
    statement = await statements_service.get(job.statement_id)
    assert statement.document_type == "income_statement"
    assert statement.company_name == "NVIDIA"
```

### Test Coverage Goals

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| Core infrastructure | 90% | - |
| Feature services | 85% | - |
| Parsers | 95% | - |
| API routes | 80% | - |
| Database models | 70% | - |
| Overall | 80%+ | - |

### Testing Commands

```bash
# Run all tests
pytest -v

# Run only unit tests (fast)
pytest -v -m "not integration"

# Run integration tests
pytest -v -m integration

# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific feature tests
pytest app/detection/tests/ -v

# Run E2E tests only
pytest tests/e2e/ -v
```

---

## Migration Checklist

### Pre-Migration

- [ ] Backup existing codebase to `migration_backup/`
- [ ] Document current output format for comparison
- [ ] Run existing system and save outputs as baseline
- [ ] Create test cases from current successful runs

### Infrastructure Phase

- [ ] FastAPI application starts successfully
- [ ] PostgreSQL database accessible
- [ ] Health endpoints responding (/, /health, /health/db, /health/ready)
- [ ] Logging outputs JSON with request IDs
- [ ] All linters pass (Ruff check)
- [ ] All type checkers pass (MyPy + Pyright)
- [ ] Core infrastructure tests pass
- [ ] Docker services start successfully

### Feature Migration (Per Feature)

- [ ] Database models created and migrated
- [ ] Pydantic schemas validated
- [ ] Service layer implemented with async patterns
- [ ] API routes functional with Swagger docs
- [ ] Unit tests passing (80%+ coverage)
- [ ] Integration tests passing
- [ ] Feature README documented
- [ ] Logging events use dotted namespace pattern
- [ ] Type hints complete (no suppressions)

### Validation Phase

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] E2E tests with real PDFs passing
- [ ] Output matches original system (data parity)
- [ ] Performance acceptable (within 20% of original)
- [ ] Memory usage reasonable
- [ ] No type errors (MyPy + Pyright clean)
- [ ] No linting errors (Ruff clean)
- [ ] Swagger UI accessible and documented
- [ ] All health checks passing

### Production Readiness

- [ ] `.env.example` complete with all variables
- [ ] Docker multi-stage build optimized
- [ ] Database migrations tested (up and down)
- [ ] Error handling comprehensive
- [ ] Logging complete for all operations
- [ ] API documentation complete
- [ ] User migration guide written
- [ ] Security review complete
- [ ] Performance benchmarks documented

### Post-Migration

- [ ] Old codebase archived to `dump/`
- [ ] Git history preserved
- [ ] Documentation updated
- [ ] Team trained on new system
- [ ] Monitoring configured
- [ ] Backup strategy implemented

---

## Risk Mitigation

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Data loss during migration** | Low | Critical | Complete backup before migration, parallel running |
| **Performance degradation** | Medium | High | Benchmark early, optimize queries, use async patterns |
| **LLMWhisperer API compatibility** | Low | High | Maintain wrapper abstraction, test with real API early |
| **Schema validation failures** | Medium | Medium | Preserve existing Pydantic logic, comprehensive testing |
| **Type checking too strict** | Medium | Low | Gradual strictness increase, document suppressions |
| **Database migration errors** | Low | High | Test migrations thoroughly, have rollback plan |
| **Output format changes** | Low | High | Preserve output structure, validate against baseline |
| **Missed functionality** | Medium | High | Feature parity checklist, parallel testing |

### Mitigation Strategies

**1. Parallel Running (Week 4)**
- Run old and new systems side-by-side
- Compare outputs for every test case
- Identify discrepancies before cutover

**2. Incremental Migration**
- Complete one feature at a time
- Test each feature independently
- Don't move to next feature until current is validated

**3. Rollback Plan**
- Keep old codebase in `migration_backup/`
- Document rollback procedure
- Test rollback before cutover

**4. Comprehensive Testing**
- Write tests BEFORE migration
- Maintain test coverage > 80%
- Use real test data (NVIDIA 10K PDFs)

**5. Feature Parity Validation**
- Create checklist of all current features
- Verify each feature in new system
- Document any changes or improvements

**6. Performance Monitoring**
- Benchmark original system
- Compare new system performance
- Optimize if performance degrades > 20%

**7. Data Validation**
- Save baseline outputs from current system
- Compare new system outputs byte-by-byte
- Investigate any differences

---

## Success Criteria

### Functional Requirements

- ✅ 100% feature parity with existing system
- ✅ All 5 financial statement types supported
- ✅ Direct parsing maintains 100% data accuracy
- ✅ Multi-PDF consolidation works correctly
- ✅ Excel export preserves formatting
- ✅ Cost optimization maintained (PyMuPDF before LLMWhisperer)

### Non-Functional Requirements

- ✅ Type safety: Zero MyPy/Pyright errors
- ✅ Code quality: Zero Ruff violations
- ✅ Test coverage: > 80% overall
- ✅ Performance: Within 20% of original system
- ✅ API documentation: Complete Swagger UI
- ✅ Logging: JSON structured with request correlation
- ✅ Health checks: All endpoints responding

### AI-Optimization Requirements

- ✅ Vertical slice architecture implemented
- ✅ Structured logging with dotted namespace
- ✅ Strict type checking (MyPy + Pyright)
- ✅ Comprehensive testing (unit + integration + e2e)
- ✅ FastAPI with automatic documentation
- ✅ CLAUDE.md complete for AI agents
- ✅ Automated validation loops (Ruff + MyPy + Pyright)

---

## Next Steps

1. **Review this plan** and provide feedback
2. **Prioritize features** if timeline needs adjustment
3. **Set up development environment** (Python 3.12, uv, Docker, PostgreSQL)
4. **Start Phase 1** (Foundation Infrastructure)
5. **Iterate and validate** after each phase

---

## Questions for You

Before starting implementation, please clarify:

1. **Database Provider:** Local PostgreSQL in Docker, or cloud provider (Supabase, Neon, Railway)?
2. **API Authentication:** Do you need authentication/authorization for API endpoints?
3. **Background Jobs:** Should long-running pipeline jobs use background task queue (Celery/ARQ)?
4. **Existing Data:** Do you need to migrate existing output data to the database?
5. **Test Data:** Besides NVIDIA 10K PDFs, do you have other test cases to validate?
6. **Deployment Target:** Local development only, or production deployment (cloud/on-premise)?
7. **Team Size:** Will you be the only developer, or are there multiple people working on this?
8. **Timeline Flexibility:** Is the 2-4 week timeline flexible if we discover complexity?

---

## Appendix A: Technology Stack

### Backend Framework
- **FastAPI** 0.120+ - Modern async web framework
- **Uvicorn** - ASGI server with hot reload

### Database
- **PostgreSQL** 18+ - Hybrid persistence with files
- **SQLAlchemy** 2.0+ (async) - ORM with async support
- **Alembic** - Database migrations
- **asyncpg** - Async PostgreSQL driver

### Data Validation
- **Pydantic** 2.0+ - Runtime validation and settings
- **pydantic-settings** - Environment-based configuration

### Logging & Observability
- **structlog** - Structured JSON logging
- **python-json-logger** - JSON log formatting

### Type Safety & Validation
- **Ruff** - Fast Python linter and formatter
- **MyPy** - Static type checker (pragmatic)
- **Pyright** - Static type checker (strict)

### Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage
- **httpx** - Async HTTP client for API tests

### LLM Integration
- **unstract-llmwhisperer** - PDF text extraction
- **openai** - ChatOpenAI fallback (optional)

### File Processing
- **PyMuPDF** (fitz) - Cost-free table detection
- **openpyxl** - Excel file manipulation
- **pandas** - Data manipulation

### Development Tools
- **uv** - Fast Python package manager
- **Docker** + **Docker Compose** - Containerization
- **python-dotenv** - Environment variable management

---

## Appendix B: File Size Estimates

| Directory | Estimated Files | Estimated LOC |
|-----------|----------------|---------------|
| app/core/ | 8 files | ~800 lines |
| app/shared/ | 5 files | ~200 lines |
| app/llm/ | 4 files | ~400 lines |
| app/detection/ | 8 files | ~1,200 lines |
| app/extraction/ | 15 files | ~3,500 lines |
| app/statements/ | 12 files | ~2,000 lines |
| app/consolidation/ | 8 files | ~1,800 lines |
| app/jobs/ | 8 files | ~1,000 lines |
| tests/ | 30 files | ~2,500 lines |
| docs/ | 5 files | ~1,500 words |
| **Total** | **~103 files** | **~13,900 lines** |

This represents a ~40% reduction from the current 20K+ lines while adding FastAPI, database persistence, and comprehensive testing.

---

## Appendix C: Glossary

- **Vertical Slice Architecture (VSA):** Organizing code by feature/capability rather than technical layer
- **Direct Parsing:** Extracting data from raw text without LLM interpretation (100% accuracy)
- **Hybrid Persistence:** Using both files (cache) and database (structured queries)
- **Structured Logging:** JSON-formatted logs with consistent event naming
- **Dotted Namespace:** Event naming pattern `domain.component.action_state`
- **AST Grep:** Abstract Syntax Tree pattern matching for comprehensive refactoring
- **LLMWhisperer:** PDF text extraction service with layout preservation
- **Strangler Fig Pattern:** Gradually replacing old system by wrapping with new code
- **Type Safety:** Static type checking to catch errors before runtime

---

**Document Version:** 1.0
**Last Updated:** 2025-12-14
**Author:** AI-Assisted Refactoring Planning
**Status:** Ready for Review
