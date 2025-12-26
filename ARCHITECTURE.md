# System Architecture

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Database Architecture](#database-architecture)
6. [Authentication & Authorization](#authentication--authorization)
7. [Background Job Processing](#background-job-processing)
8. [API Design](#api-design)
9. [Error Handling](#error-handling)
10. [Logging & Observability](#logging--observability)
11. [Security](#security)
12. [Performance](#performance)
13. [Deployment Architecture](#deployment-architecture)

## Overview

The LLM Financial Document Processing Pipeline is an async-first, microservice-ready application built with FastAPI. It processes financial PDF documents through a multi-stage pipeline: extraction → detection → parsing → consolidation → export.

### High-Level Architecture

```
┌─────────────┐
│   Client    │
│  (Browser,  │
│  API, CLI)  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌───────────────────────────────────┐  │
│  │   Middleware Layer                │  │
│  │  - CORS                           │  │
│  │  - Request ID                     │  │
│  │  - Logging                        │  │
│  │  - Exception Handling             │  │
│  └───────────────────────────────────┘  │
│                  │                       │
│  ┌───────────────┴───────────────────┐  │
│  │       API Router Layer            │  │
│  │  /auth  /extraction  /jobs        │  │
│  │  /detection  /statements          │  │
│  │  /consolidation  /health          │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────┴───────────────────┐  │
│  │      Service Layer                │  │
│  │  - AuthService                    │  │
│  │  - ExtractionService              │  │
│  │  - DetectionService               │  │
│  │  - StatementService               │  │
│  │  - JobService                     │  │
│  │  - ConsolidationService           │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────┴───────────────────┐  │
│  │      Data Access Layer            │  │
│  │  - SQLAlchemy Models              │  │
│  │  - Async Sessions                 │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌─────▼──────┐
   │PostgreSQL│          │  External  │
   │ Database │          │  Services  │
   │         │          │ LLMWhisperer│
   │         │          │   OpenAI   │
   └─────────┘          └────────────┘

┌─────────────────────────────────────────┐
│     Background Worker (Async)           │
│  - Polls job queue                      │
│  - Processes extraction tasks           │
│  - Updates job status                   │
│  - Handles retries                      │
└─────────────────────────────────────────┘
```

## Architecture Patterns

### 1. Layered Architecture

The application follows a strict layered architecture:

```
Routes (API Layer)
    ↓ calls
Services (Business Logic Layer)
    ↓ uses
Models (Data Access Layer)
    ↓ queries
Database (PostgreSQL)
```

**Benefits:**
- Clear separation of concerns
- Easy to test each layer independently
- Changes to one layer don't ripple to others
- Business logic is reusable across different interfaces

### 2. Service Layer Pattern

All business logic resides in service classes:

```python
class ExtractionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def extract_from_pdf(self, file_path: str) -> Extraction:
        # Business logic here
        pass
```

**Benefits:**
- Routes are thin and focused on HTTP concerns
- Services can be reused in background jobs, CLI, etc.
- Easy to mock services for testing routes
- Business logic is centralized and maintainable

### 3. Dependency Injection

FastAPI's dependency injection system is used throughout:

```python
@router.post("/extract")
async def extract(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExtractionService(db)
    return await service.extract_from_pdf(file)
```

**Benefits:**
- Decouples components
- Makes testing easy (inject mocks)
- Centralized configuration
- Automatic resource cleanup

### 4. Repository Pattern (Implicit)

Services act as repositories, encapsulating data access:

```python
class StatementService:
    async def get_statement(self, statement_id: int) -> Statement | None:
        stmt = select(Statement).where(Statement.id == statement_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

### 5. Async-First Design

All I/O operations use async/await:

```python
# Database operations
async with AsyncSession() as session:
    result = await session.execute(query)

# HTTP requests
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# File I/O (where possible)
async with aiofiles.open(path, "r") as f:
    content = await f.read()
```

**Benefits:**
- High concurrency without threads
- Efficient resource usage
- Non-blocking I/O
- Better performance under load

## System Components

### Core Infrastructure (`app/core/`)

**Purpose:** Foundation services used across the application.

#### `config.py` - Configuration Management
- Pydantic Settings for type-safe config
- Environment variable loading
- Validation on startup
- Singleton pattern with `@lru_cache`

#### `database.py` - Database Connection
- Async SQLAlchemy engine
- Connection pooling
- Session management
- Dependency injection helper

#### `logging.py` - Structured Logging
- Structlog for JSON logging
- Request ID injection
- Context binding
- Performance tracking

#### `middleware.py` - Request Processing
- **RequestIDMiddleware**: Adds unique ID to each request
- **LoggingMiddleware**: Logs request/response with timing
- **CORS**: Cross-origin resource sharing

#### `exceptions.py` - Error Handling
- Custom exception classes
- Exception handlers for FastAPI
- Structured error responses
- Logging integration

#### `health.py` - Health Checks
- Basic health endpoint (`GET /health`)
- Detailed health with DB check (`GET /health/detailed`)
- Used by load balancers and monitoring

### Authentication Module (`app/auth/`)

**Purpose:** User management and JWT authentication.

#### Components:
- **models.py**: User model with hashed passwords
- **schemas.py**: Pydantic schemas for requests/responses
- **service.py**: User CRUD and authentication logic
- **dependencies.py**: Auth dependencies (`get_current_user`, `get_current_superuser`)
- **routes.py**: Auth endpoints (`/register`, `/login`, `/me`, `/refresh`)

#### Flow:
```
1. User registers → Password hashed with bcrypt → Stored in DB
2. User logs in → Password verified → JWT token generated
3. User makes request → Token in Authorization header → Validated
4. Token decoded → User loaded from DB → Injected into route
```

### Detection Module (`app/detection/`)

**Purpose:** Automatically detect financial statement type from text.

#### Components:
- **detector.py**: Keyword-based detection algorithm
- **service.py**: Detection business logic
- **routes.py**: Detection API endpoints
- **models.py**: Detection result storage

#### Detection Algorithm:
```python
1. Extract keywords from document text
2. Score against known patterns:
   - Income Statement: "revenue", "expenses", "net income"
   - Balance Sheet: "assets", "liabilities", "equity"
   - Cash Flow: "operating activities", "cash flows"
3. Return type with highest confidence score
```

### Extraction Module (`app/extraction/`)

**Purpose:** Extract structured data from PDF financial documents.

#### Components:
- **parser.py**: Direct parsing logic for tables
- **service.py**: Extraction orchestration
- **routes.py**: Upload and extraction endpoints
- **models.py**: Extraction job tracking

#### Extraction Pipeline:
```
1. PDF Upload → Saved to disk
2. LLMWhisperer API → Raw pipe-separated text
3. Detection Service → Identify statement type
4. Direct Parser → Extract account names and values
5. Validation → Pydantic schema
6. Storage → Database + cache
```

### Statements Module (`app/statements/`)

**Purpose:** Manage financial statement records.

#### Components:
- **models.py**: Statement models (IncomeStatement, BalanceSheet, etc.)
- **service.py**: CRUD operations for statements
- **routes.py**: Statement API endpoints
- **schemas.py**: Pydantic schemas

### Consolidation Module (`app/consolidation/`)

**Purpose:** Consolidate multi-period financial data and export to Excel.

#### Components:
- **service.py**: Multi-period aggregation logic
- **exporter.py**: Excel file generation
- **routes.py**: Consolidation and export endpoints
- **models.py**: Consolidation configuration

#### Consolidation Flow:
```
1. Query multiple statement periods
2. Align accounts across periods
3. Calculate variances and trends
4. Format with visual indentation
5. Export to Excel with formulas
```

### Jobs Module (`app/jobs/`)

**Purpose:** Background job processing for long-running tasks.

#### Components:
- **models.py**: Job model with status tracking
- **service.py**: Job CRUD operations
- **tasks.py**: Task function registry
- **worker.py**: Background worker implementation
- **routes.py**: Job management API

#### Worker Architecture:
```python
class BackgroundWorker:
    - Concurrency: 3 jobs simultaneously
    - Poll Interval: 1 second
    - Task Timeout: 5 minutes
    - Retry Logic: Exponential backoff
    - Cancellation: Graceful task cancellation
```

#### Job Lifecycle:
```
PENDING → Worker polls → RUNNING → Task executes
         ↓                         ↓
    No jobs available       Success or Error
         ↓                         ↓
    Sleep 1s              COMPLETED / FAILED
                                  ↓
                          Retry if max not reached
```

### LLM Module (`app/llm/`)

**Purpose:** Interface with external LLM services.

#### Components:
- **clients.py**: LLMWhisperer and OpenAI clients
- **cache.py**: Response caching for API calls
- **schemas.py**: API request/response schemas

### Notifications Module (`app/notifications/`)

**Purpose:** Email notifications for job completion.

#### Components:
- **service.py**: Email sending logic
- **notifications.py**: Email templates
- **SMTP integration**: Async email sending

### Shared Module (`app/shared/`)

**Purpose:** Common models and schemas used across modules.

#### Components:
- **models.py**: Base model with timestamps
- **schemas.py**: BaseResponse for consistent API responses

## Data Flow

### Document Processing Flow

```
┌─────────────┐
│   Upload    │ POST /extraction/extract
│     PDF     │ (multipart/form-data)
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Save to Disk    │ uploads/20251226_103000_statement.pdf
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Create Job      │ JobType.EXTRACTION, status=PENDING
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Return Job ID    │ {"job_id": 123, "status": "pending"}
└──────────────────┘

         ... Meanwhile in Background Worker ...

┌──────────────────┐
│  Poll for Jobs   │ SELECT * FROM jobs WHERE status='pending'
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Mark RUNNING     │ UPDATE jobs SET status='running'
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Call LLMWhisperer│ Extract pipe-separated text
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Detect Type      │ Identify: "Balance Sheet" (95% confidence)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Parse Tables     │ Direct parsing → structured data
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Validate Schema  │ BalanceSheetSchema.model_validate()
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Store Results    │ Save to statements table
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Mark COMPLETED   │ UPDATE jobs SET status='completed'
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Send Email       │ (if enabled) Notify user
└──────────────────┘
```

### Authentication Flow

```
┌─────────────┐
│  Register   │ POST /auth/register
└──────┬──────┘
       │ {email, password, username}
       ▼
┌──────────────┐
│ Hash Password│ bcrypt.hashpw()
└──────┬───────┘
        │
        ▼
┌──────────────┐
│ Create User  │ INSERT INTO users
└──────┬───────┘
        │
        ▼
┌──────────────┐
│Return UserData│ {id, email, username, created_at}
└──────────────┘

... Later: Login ...

┌─────────────┐
│   Login     │ POST /auth/login
└──────┬──────┘
       │ {email, password}
       ▼
┌──────────────┐
│ Verify Pass  │ bcrypt.checkpw()
└──────┬───────┘
        │ ✓
        ▼
┌──────────────┐
│ Create Token │ JWT with {user_id, email, exp}
└──────┬───────┘
        │
        ▼
┌──────────────┐
│Return Token  │ {access_token, token_type, expires_in}
└──────────────┘

... Authenticated Request ...

┌─────────────┐
│ API Request │ GET /auth/me
└──────┬──────┘
       │ Authorization: Bearer <token>
       ▼
┌──────────────┐
│ Decode Token │ jwt.decode(verify_signature=True)
└──────┬───────┘
        │ {user_id: 123}
        ▼
┌──────────────┐
│  Load User   │ SELECT * FROM users WHERE id=123
└──────┬───────┘
        │
        ▼
┌──────────────┐
│ Inject User  │ current_user: User = Depends(get_current_user)
└──────┬───────┘
        │
        ▼
┌──────────────┐
│Return UserData│ {id, email, username, ...}
└──────────────┘
```

## Database Architecture

### Schema Overview

```sql
-- Users table (authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Extraction jobs table
CREATE TABLE extractions (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    statement_type VARCHAR(100),
    confidence NUMERIC(5,2),
    company_name VARCHAR(255),
    fiscal_year INTEGER,
    processing_time NUMERIC(10,2),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Financial statements table
CREATE TABLE statements (
    id SERIAL PRIMARY KEY,
    extraction_id INTEGER REFERENCES extractions(id),
    statement_type VARCHAR(100) NOT NULL,
    company_name VARCHAR(255),
    period_start DATE,
    period_end DATE,
    fiscal_year INTEGER,
    raw_text TEXT,
    structured_data JSONB,  -- Full JSON data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Background jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,  -- extraction, consolidation, etc.
    task_name VARCHAR(100) NOT NULL,
    task_args JSONB,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed, cancelled
    progress INTEGER DEFAULT 0,
    result JSONB,
    error TEXT,
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Consolidations table (multi-period analysis)
CREATE TABLE consolidations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    statement_ids INTEGER[],  -- Array of statement IDs
    created_by INTEGER REFERENCES users(id),
    settings JSONB,  -- Consolidation configuration
    result JSONB,  -- Consolidated data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_extractions_status ON extractions(status);
CREATE INDEX idx_extractions_created_at ON extractions(created_at DESC);
CREATE INDEX idx_statements_company ON statements(company_name);
CREATE INDEX idx_statements_fiscal_year ON statements(fiscal_year);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_users_email ON users(email);
```

### Connection Pooling

```python
# app/core/database.py
engine = create_async_engine(
    str(settings.database_url),
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,           # Keep 5 connections open
    max_overflow=10,       # Allow 10 additional connections
    pool_pre_ping=True,    # Test connections before use
    echo=settings.database_echo,
)
```

**Pool Configuration:**
- **pool_size=5**: Maintain 5 persistent connections
- **max_overflow=10**: Up to 15 total connections (5 + 10)
- **pool_pre_ping=True**: Detect stale connections
- **pool_recycle=3600**: Recycle connections every hour

## Authentication & Authorization

### JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "123",           // User ID
    "email": "user@example.com",
    "exp": 1735305600,      // Expiration timestamp
    "iat": 1735303800       // Issued at
  },
  "signature": "..."
}
```

### Token Generation

```python
def create_access_token(user_id: int, email: str) -> str:
    expires = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expires,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
```

### Token Validation

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = int(payload.get("sub"))

        # Load user from database
        user = await get_user_by_id(db, user_id)

        if not user or not user.is_active:
            raise HTTPException(401, "Invalid or inactive user")

        return user

    except JWTError:
        raise HTTPException(401, "Could not validate credentials")
```

### Role-Based Access Control

```python
# Public endpoint - no auth required
@router.post("/auth/register")
async def register(user_data: RegisterRequest):
    pass

# Authenticated endpoint - requires valid token
@router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    pass

# Admin endpoint - requires superuser role
@router.get("/auth/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
):
    pass
```

## Background Job Processing

### Worker Architecture

```python
class BackgroundWorker:
    - Runs in separate asyncio task during app lifespan
    - Polls job queue every 1 second
    - Processes up to 3 jobs concurrently
    - Implements exponential backoff retry logic
    - Graceful shutdown on app termination
```

### Task Registry

```python
# app/jobs/tasks.py
TASK_REGISTRY = {
    "extract_pdf": extract_pdf_task,
    "consolidate_statements": consolidate_statements_task,
    "generate_excel": generate_excel_task,
}

async def extract_pdf_task(file_path: str, **kwargs):
    # Task implementation
    pass
```

### Retry Logic

```python
if job.retries < job.max_retries:
    # Exponential backoff: 2^(retry+1) seconds
    delay = min(300, 2 ** (job.retries + 1))
    await asyncio.sleep(delay)

    # Reset to pending for retry
    job.status = JobStatus.PENDING
    job.retries += 1
else:
    # Max retries exceeded
    job.status = JobStatus.FAILED
```

**Retry Delays:**
- Retry 1: 2 seconds
- Retry 2: 4 seconds
- Retry 3: 8 seconds
- Max delay: 300 seconds (5 minutes)

## API Design

### RESTful Principles

```
GET    /auth/users       - List users
POST   /auth/users       - Create user
GET    /auth/users/{id}  - Get user
PATCH  /auth/users/{id}  - Update user
DELETE /auth/users/{id}  - Delete user
```

### Response Format

All endpoints return consistent format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    "id": 123,
    "email": "user@example.com",
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

Error format:

```json
{
  "detail": "User not found",
  "status_code": 404,
  "request_id": "abc-123-def-456"
}
```

### Pagination

```python
@router.get("/statements")
async def list_statements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    statements = await service.get_statements(skip=skip, limit=limit)
    return {"data": statements, "skip": skip, "limit": limit}
```

## Error Handling

### Exception Hierarchy

```python
# Base exceptions
class AppError(Exception):
    """Base application error"""

class AuthServiceError(AppError):
    """Authentication/authorization errors"""

class ExtractionServiceError(AppError):
    """Extraction processing errors"""

class JobServiceError(AppError):
    """Background job errors"""
```

### Exception Handlers

```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error("Database error", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"},
    )
```

## Logging & Observability

### Structured Logging

```json
{
  "timestamp": "2025-12-26T10:30:00.123Z",
  "level": "info",
  "message": "User registered successfully",
  "request_id": "abc-123-def-456",
  "user_id": 1,
  "email": "user@example.com",
  "duration_ms": 45.2
}
```

### Log Levels

- **DEBUG**: Development diagnostics
- **INFO**: Normal operations (user actions, API calls)
- **WARNING**: Recoverable issues
- **ERROR**: Errors requiring attention
- **CRITICAL**: System failures

### Metrics

Key metrics to monitor:
- **Request rate**: Requests per second
- **Response time**: p50, p95, p99 latencies
- **Error rate**: 4xx and 5xx responses
- **Database connections**: Active, idle, max
- **Job queue**: Pending jobs, processing time
- **Worker health**: Active workers, failed jobs

## Security

### Password Security

- **Hashing**: bcrypt with salt rounds=12
- **No plaintext**: Passwords never stored unencrypted
- **Validation**: Minimum 8 characters, complexity rules

### JWT Security

- **Secret key**: 32+ character random string
- **Algorithm**: HS256 (HMAC-SHA256)
- **Expiration**: 30 minutes default
- **Validation**: Signature verification on every request

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### File Upload Security

- **Type validation**: Only allowed file types (.pdf)
- **Size limits**: Max 50MB by default
- **Filename sanitization**: Prevent directory traversal
- **Virus scanning**: (Future) Integrate ClamAV

## Performance

### Async I/O

All I/O operations are async:
- Database queries (asyncpg)
- HTTP requests (httpx)
- File operations (aiofiles where applicable)
- Background tasks (asyncio)

### Database Optimizations

- **Connection pooling**: Reuse connections
- **Prepared statements**: SQLAlchemy caching
- **Indexes**: On frequently queried columns
- **JSONB fields**: Efficient JSON storage and querying

### Caching

```python
# LLM API response caching
cache_key = f"llmwhisperer_{file_hash}"
if cached := await cache.get(cache_key):
    return cached

result = await llmwhisperer.extract(file_path)
await cache.set(cache_key, result, ttl=3600)
```

### Background Processing

Long-running tasks moved to background:
- PDF extraction (5-60 seconds)
- Multi-period consolidation (10-30 seconds)
- Excel generation (5-15 seconds)

## Deployment Architecture

### Development

```
Local Machine:
- Python 3.12 venv
- PostgreSQL in Docker
- uvicorn --reload
- SQLite for tests
```

### Production

```
┌─────────────┐
│Load Balancer│ (nginx, ALB)
└──────┬──────┘
       │
  ┌────┴────┐
  │         │
┌─▼─┐     ┌─▼─┐
│API│     │API│  (uvicorn workers)
│ 1 │     │ 2 │
└─┬─┘     └─┬─┘
  │         │
  └────┬────┘
       │
  ┌────▼────┐
  │PostgreSQL│ (managed service: RDS, Cloud SQL)
  │+ Replica │
  └─────────┘

  ┌─────────────┐
  │Worker Node  │ (Background jobs)
  └─────────────┘
```

### Environment Variables

```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=<strong-random-key>
ALLOWED_ORIGINS=https://app.example.com
```

### Container Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8123

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]
```

### Health Checks

```yaml
# Docker Compose health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8123/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Future Enhancements

1. **Redis**: Distributed caching and session storage
2. **Celery**: Alternative to custom background worker
3. **WebSockets**: Real-time job progress updates
4. **Prometheus**: Metrics collection and alerting
5. **Elasticsearch**: Full-text search across documents
6. **S3**: Cloud storage for uploaded files
7. **Rate Limiting**: Prevent abuse
8. **API Versioning**: /api/v1/, /api/v2/
