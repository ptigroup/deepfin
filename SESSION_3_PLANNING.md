# Session 3: FastAPI Application & Health Checks - Planning

## 🎯 Big Picture Goal

**Create a working FastAPI application that can start, respond to requests, and report its health status.**

This is our first **MILESTONE**: After this session, you'll be able to run:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8123
```

And visit `http://localhost:8123/health` to see a working API!

---

## 📦 What We're Building (5 Files)

### 1. `app/main.py` - The Application Entry Point
**What:** The FastAPI application instance and configuration
**Why:** This is the main file that starts your entire API

**Key Components:**
- Create FastAPI app instance with metadata (title, version, description)
- Register middleware (logging, CORS, request IDs)
- Register exception handlers (convert Python exceptions to HTTP responses)
- Register routers (health check endpoints)
- Lifespan events (startup: connect to DB, shutdown: close DB)

**Mental Model:**
```
main.py is like the "main()" function in a traditional app
├── Setup phase: Create app, add middleware, add routes
├── Startup phase: Connect to database, initialize resources
├── Running phase: Handle HTTP requests
└── Shutdown phase: Close database, cleanup resources
```

### 2. `app/core/health.py` - Health Check Endpoints
**What:** API endpoints to check if the service is alive and healthy
**Why:** Production monitoring systems (Kubernetes, AWS ELB, monitoring tools) need to know if your service is working

**Endpoints:**
- `GET /health` - Simple "I'm alive" check (returns 200 OK)
- `GET /health/db` - Database connectivity check (queries DB, returns status)

**Real-World Use Case:**
```
Load Balancer: "Is this server healthy?"
    → Calls /health/db
    → If 200 OK: Keep sending traffic
    → If 500 Error: Stop sending traffic, server has issues
```

**Mental Model:**
```
Health Check = "Is the service working?"
├── Basic Health: Process is running (fast, always works)
├── Database Health: Can we connect to PostgreSQL? (slower, can fail)
└── Future: Can we reach external APIs? (LLMWhisperer, OpenAI)
```

### 3. `app/core/middleware.py` - Request Logging & Tracing
**What:** Code that runs BEFORE and AFTER every request
**Why:** Observability - you need to see what's happening in production

**Middleware Functions:**
1. **Request ID Middleware** - Adds unique ID to every request for tracking
   ```
   Request comes in → Generate UUID → Add to request → Add to logs → Add to response headers
   ```

2. **Logging Middleware** - Logs every request with timing
   ```
   Request starts → Log: "GET /health started, request_id=abc123"
   Request ends → Log: "GET /health completed in 45ms, status=200"
   ```

**Why Request IDs Matter:**
```
User: "I got an error at 2:34 PM!"
You: *search logs for request_id=xyz789*
    → See entire request flow
    → "Ah, database timeout on line 42"
    → Fix the issue

Without request IDs:
    → 1000 requests per minute
    → Which one failed?
    → Impossible to debug
```

**Mental Model:**
```
Every HTTP Request:
1. Middleware runs BEFORE endpoint (add request_id, start timer)
2. Your endpoint code runs (GET /health/db)
3. Middleware runs AFTER endpoint (log duration, add headers)
4. Response sent to client
```

### 4. `app/core/exceptions.py` - Error Handling
**What:** Converts Python exceptions into nice HTTP error responses
**Why:** API should return consistent error format (not ugly stack traces)

**Exception Handlers:**
- `ValidationError` (from Pydantic) → 422 Unprocessable Entity
- `SQLAlchemyError` (database errors) → 500 Internal Server Error
- `Generic Exception` → 500 with safe error message

**Before Exception Handler:**
```json
HTTP 500 Internal Server Error
Traceback (most recent call last):
  File "app/main.py", line 42, in process_document
    result = await db.execute(query)
    ...
sqlalchemy.exc.OperationalError: connection to server failed
```

**After Exception Handler:**
```json
HTTP 500 Internal Server Error
{
  "success": false,
  "message": "Database connection failed",
  "timestamp": "2025-12-18T10:30:00Z",
  "request_id": "abc-123-xyz"
}
```

**Mental Model:**
```
Exception Raised → FastAPI catches it → Calls your handler → Returns nice JSON
```

### 5. `tests/test_main.py` - API Integration Tests
**What:** Tests that verify the entire API works end-to-end
**Why:** Confidence that the API actually starts and responds correctly

**Test Scenarios:**
1. App starts without errors
2. GET /health returns 200
3. GET /health/db returns 200 when DB connected
4. GET /health/db returns 503 when DB down
5. Middleware adds request_id header
6. Exceptions return proper error format
7. CORS headers present

**Mental Model:**
```
Integration Tests = "Does it work when all pieces work together?"
├── Unit tests: Test individual functions
└── Integration tests: Test HTTP requests through the entire app
```

---

## 🧩 Key Concepts Explained

### 1. FastAPI Application Setup

**Code Pattern:**
```python
from fastapi import FastAPI

app = FastAPI(
    title="LLM Financial Pipeline",
    version="1.0.0",
    description="Financial document processing API",
)
```

**What This Gives You:**
- Automatic OpenAPI/Swagger docs at `/docs`
- Automatic ReDoc at `/redoc`
- Input validation via Pydantic
- Async request handling

### 2. Dependency Injection

**Pattern:**
```python
@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    # db is automatically injected by FastAPI
    result = await db.execute(select(Item))
    return result.scalars().all()
```

**Why This is Powerful:**
- FastAPI calls `get_db()` for you
- Guarantees database session cleanup
- Easy to mock in tests: `app.dependency_overrides[get_db] = mock_db`
- DRY: Write `Depends(get_db)` instead of manual session management

**Mental Model:**
```
Request comes in
    → FastAPI sees: db = Depends(get_db)
    → FastAPI calls: get_db()
    → Result injected into function parameter
    → Your code runs
    → FastAPI cleans up (calls finally block in get_db)
```

### 3. Middleware Implementation

**What is Middleware?**
Middleware is code that wraps around your request handlers.

**Execution Order:**
```
1. Request arrives
2. Middleware #1 (before)
3. Middleware #2 (before)
4. Your endpoint handler runs
5. Middleware #2 (after)
6. Middleware #1 (after)
7. Response sent
```

**Real Example:**
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    # Before endpoint
    request.state.request_id = request_id

    # Call endpoint
    response = await call_next(request)

    # After endpoint
    response.headers["X-Request-ID"] = request_id
    return response
```

### 4. Exception Handlers

**Pattern:**
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
    )
```

**When to Use:**
- Convert known exceptions to proper HTTP status codes
- Hide sensitive error details from API responses
- Add consistent error response format
- Log errors with context

### 5. Lifespan Events

**What:** Code that runs once at startup and once at shutdown
**Why:** Initialize resources (DB connections) and clean up

**Pattern:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")

    yield  # App runs here

    # Shutdown
    await close_db()
    logger.info("Database connections closed")

app = FastAPI(lifespan=lifespan)
```

**Mental Model:**
```
Server starts → Run startup code → Handle requests → Server stops → Run shutdown code
```

### 6. CORS Configuration

**What:** Cross-Origin Resource Sharing
**Why:** Allow frontend (http://localhost:3000) to call your API (http://localhost:8123)

**Without CORS:**
```
Frontend: "Call GET http://localhost:8123/health"
Browser: "BLOCKED! Different origin, no CORS headers"
```

**With CORS:**
```
Frontend: "Call GET http://localhost:8123/health"
API Response includes: Access-Control-Allow-Origin: http://localhost:3000
Browser: "OK, allowed!"
```

**Pattern:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🎓 Why This Session Matters

### Milestone Achievement
After this session, you have a **working API** that:
- Starts successfully
- Responds to HTTP requests
- Can be tested with browser/Postman/curl
- Has observability (logs, request IDs)
- Handles errors gracefully

### Foundation for Future Sessions
All future endpoints will use this foundation:
- Session 6-9: Document processing endpoints
- Session 10-14: Job management endpoints
- Every endpoint benefits from: logging, error handling, CORS

### Production-Ready Patterns
- Health checks: Required for Kubernetes, ECS, load balancers
- Request IDs: Essential for debugging in production
- Exception handlers: Prevent leaking sensitive data
- CORS: Enable frontend integration

---

## 🚧 Potential Challenges

### Challenge 1: Understanding Middleware Order
**Issue:** Middleware runs in reverse order (first added runs last on response)
**Solution:** Document middleware order clearly in comments

### Challenge 2: Testing Lifespan Events
**Issue:** TestClient may not trigger lifespan events properly
**Solution:** Use `with TestClient(app)` context manager or test manually

### Challenge 3: Database Health Check Timeouts
**Issue:** If DB is slow, health check takes too long
**Solution:** Add timeout to database health check query

### Challenge 4: CORS in Development vs Production
**Issue:** Allow all origins in dev, specific origins in prod
**Solution:** Use `settings.allowed_origins_list` from config

---

## 📋 Implementation Checklist

### Phase 1: Basic App Setup
- [ ] Create `app/main.py` with FastAPI instance
- [ ] Add app metadata (title, version, description)
- [ ] Verify app starts: `uvicorn app.main:app --reload`

### Phase 2: Health Endpoints
- [ ] Create `app/core/health.py`
- [ ] Implement `GET /health` (simple check)
- [ ] Implement `GET /health/db` (database check)
- [ ] Test endpoints manually

### Phase 3: Middleware
- [ ] Create `app/core/middleware.py`
- [ ] Implement request ID middleware
- [ ] Implement logging middleware
- [ ] Add CORS middleware
- [ ] Verify in logs

### Phase 4: Exception Handling
- [ ] Create `app/core/exceptions.py`
- [ ] Add exception handler for ValidationError
- [ ] Add exception handler for SQLAlchemyError
- [ ] Add generic exception handler
- [ ] Test error responses

### Phase 5: Lifespan Events
- [ ] Add lifespan context manager
- [ ] Call `init_db()` on startup
- [ ] Call `close_db()` on shutdown
- [ ] Verify in logs

### Phase 6: Testing
- [ ] Create `tests/test_main.py`
- [ ] Test GET /health returns 200
- [ ] Test GET /health/db returns 200
- [ ] Test middleware adds request_id
- [ ] Test exception handlers
- [ ] Test CORS headers
- [ ] All tests pass: `uv run pytest tests/test_main.py -v`

### Phase 7: Integration Check
- [ ] Start server: `uv run uvicorn app.main:app --port 8123`
- [ ] Browser test: http://localhost:8123/docs (Swagger UI)
- [ ] Browser test: http://localhost:8123/health
- [ ] Browser test: http://localhost:8123/health/db
- [ ] Check logs for request IDs

---

## 🔍 Questions to Consider

### Architecture Questions
1. **Where should routers be registered?**
   - In `main.py` or separate router files?
   - Decision: Register in main.py, define in separate files (health.py)

2. **Should health endpoints be public or require auth?**
   - Decision: Public (needed by load balancers)

3. **What information should /health return?**
   - Basic: `{"status": "healthy"}`
   - Or detailed: `{"status": "healthy", "version": "1.0.0", "uptime": 3600}`
   - Decision: Start simple, add details later

### Error Handling Questions
1. **How much error detail to expose?**
   - Development: Full stack traces
   - Production: Generic messages, log details
   - Decision: Use `settings.is_development` to control detail level

2. **Should we return 500 or 503 when DB is down?**
   - 500 = Internal Server Error (generic)
   - 503 = Service Unavailable (temporary, try again later)
   - Decision: 503 for DB health check (tells load balancer to retry)

### Logging Questions
1. **What should we log?**
   - Every request? (could be noisy)
   - Only errors? (miss important context)
   - Decision: Log all requests with INFO level, errors with ERROR level

2. **Log before or after response?**
   - Before: Can log request details
   - After: Can log response status and duration
   - Decision: Both (request start and request end)

---

## 🎯 Success Criteria

After Session 3, you should be able to:

1. ✅ Run `uv run uvicorn app.main:app --port 8123`
2. ✅ Visit http://localhost:8123/docs and see Swagger UI
3. ✅ Call `GET /health` and get `200 OK`
4. ✅ Call `GET /health/db` and get `200 OK` (DB healthy)
5. ✅ See request IDs in response headers: `X-Request-ID: <uuid>`
6. ✅ See structured logs for every request
7. ✅ Trigger an error and see consistent JSON error response
8. ✅ All 12 tests pass: `uv run pytest tests/test_main.py -v`

---

## 💡 Key Takeaways

### What Makes This Different from Flask/Django?
- **Async-first:** `async def` everywhere for high performance
- **Type hints:** Python types used for validation and docs
- **Automatic docs:** Swagger UI generated from code
- **Dependency injection:** Built-in, not an add-on

### What You'll Learn
- How to structure a production FastAPI app
- Middleware patterns for cross-cutting concerns
- Exception handling best practices
- Health check implementation for production monitoring

### What You'll Reuse
- Every future endpoint will use this app instance
- Middleware will run on all requests automatically
- Exception handlers will catch all errors
- Health checks will remain for production deployment

---

## 📚 Next Steps After Session 3

**Session 4:** Document Models
- Create SQLAlchemy models for documents, processing jobs
- Add database migrations

**Session 5:** LLMWhisperer Client
- Implement PDF extraction
- Handle API calls, retries, caching

**Session 6:** Schema Detection
- Auto-detect document types
- Map to appropriate Pydantic schemas

---

## 🤔 Discussion Questions for You

Before we implement, let's discuss:

1. **Health Check Detail Level**
   - Should `/health` return just `{"status": "ok"}` or include more info like version, uptime?

2. **Request ID Format**
   - UUID4 (random) or time-based UUID1 (sortable)?

3. **Error Message Detail**
   - In development, show full stack traces or keep them hidden?

4. **CORS Origins**
   - For now, just localhost:3000 or allow multiple origins from config?

5. **Logging Level**
   - INFO for all requests or DEBUG for detailed info?

What are your thoughts on these decisions?
