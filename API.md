# API Documentation

Complete REST API reference for the LLM Financial Document Processing Pipeline.

## Base URL

```
Development: http://localhost:8123
Production: https://your-domain.com
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting a Token

1. Register a user account
2. Login with credentials
3. Use the returned `access_token` in subsequent requests

Tokens expire after 30 minutes by default. Use the `/auth/refresh` endpoint to get a new token.

## Response Format

All endpoints return JSON with a consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

---

## Authentication Endpoints

### Register User

Create a new user account.

**Endpoint:** `POST /auth/register`

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "username": "johndoe"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-26T10:30:00Z",
    "updated_at": "2025-12-26T10:30:00Z"
  }
}
```

**Errors:**
- `400 Bad Request` - Email already exists
- `422 Unprocessable Entity` - Validation error

---

### Login

Authenticate and receive JWT access token.

**Endpoint:** `POST /auth/login`

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials

**Usage:**
```bash
# Login and save token
curl -X POST http://localhost:8123/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePassword123!"}' \
  | jq -r '.access_token' > token.txt

# Use token in subsequent requests
curl -H "Authorization: Bearer $(cat token.txt)" \
  http://localhost:8123/auth/me
```

---

### Get Current User

Get details about the currently authenticated user.

**Endpoint:** `GET /auth/me`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-26T10:30:00Z",
    "updated_at": "2025-12-26T10:30:00Z"
  }
}
```

---

### Refresh Token

Generate a new JWT token using an existing valid token.

**Endpoint:** `POST /auth/refresh`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### Get User (Admin Only)

Get any user's details by ID.

**Endpoint:** `GET /auth/users/{user_id}`

**Authentication:** Required (Superuser only)

**Parameters:**
- `user_id` (path) - User ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 2,
    "email": "otheruser@example.com",
    "username": "janedoe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-26T11:00:00Z",
    "updated_at": "2025-12-26T11:00:00Z"
  }
}
```

**Errors:**
- `403 Forbidden` - Not a superuser
- `404 Not Found` - User not found

---

## Extraction Endpoints

### Upload PDF for Extraction

Upload a PDF document and create a background job to extract financial data.

**Endpoint:** `POST /extraction/extract`

**Authentication:** Required

**Request:** `multipart/form-data`
- `file` - PDF file to upload
- `company_name` (optional) - Override company name
- `fiscal_year` (optional) - Override fiscal year

**Response:** `202 Accepted`
```json
{
  "success": true,
  "message": "Extraction job created successfully",
  "data": {
    "job_id": 1,
    "status": "pending",
    "task_name": "extract_pdf",
    "file_name": "financial_statement.pdf"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8123/extraction/extract \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@statement.pdf" \
  -F "company_name=Acme Corp" \
  -F "fiscal_year=2024"
```

---

### Get Extraction Job

Get details about an extraction job.

**Endpoint:** `GET /extraction/jobs/{job_id}`

**Authentication:** Required

**Parameters:**
- `job_id` (path) - Job ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "file_name": "financial_statement.pdf",
    "status": "completed",
    "statement_type": "balance_sheet",
    "confidence": 0.95,
    "company_name": "Acme Corp",
    "fiscal_year": 2024,
    "processing_time": 45.2,
    "error_message": null,
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

**Status Values:**
- `pending` - Waiting to be processed
- `running` - Currently processing
- `completed` - Successfully completed
- `failed` - Processing failed
- `cancelled` - Manually cancelled

---

### List Extraction Jobs

Get a list of extraction jobs with optional filtering.

**Endpoint:** `GET /extraction/jobs`

**Authentication:** Required

**Query Parameters:**
- `status` (optional) - Filter by status
- `skip` (default: 0) - Number of records to skip
- `limit` (default: 100, max: 1000) - Maximum records to return

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "file_name": "statement1.pdf",
      "status": "completed",
      "statement_type": "balance_sheet",
      "confidence": 0.95,
      "company_name": "Acme Corp",
      "fiscal_year": 2024,
      "created_at": "2025-12-26T10:30:00Z"
    },
    {
      "id": 2,
      "file_name": "statement2.pdf",
      "status": "pending",
      "statement_type": null,
      "confidence": null,
      "company_name": "TechCo Inc",
      "fiscal_year": 2024,
      "created_at": "2025-12-26T10:35:00Z"
    }
  ],
  "total": 2
}
```

---

## Job Queue Endpoints

### Create Job

Create a new background job.

**Endpoint:** `POST /jobs/`

**Authentication:** Required

**Request Body:**
```json
{
  "job_type": "extraction",
  "task_name": "extract_pdf",
  "task_args": "{\"file_path\": \"/path/to/file.pdf\"}",
  "max_retries": 3
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Job created successfully",
  "data": {
    "id": 1,
    "job_type": "extraction",
    "task_name": "extract_pdf",
    "status": "pending",
    "progress": 0,
    "retries": 0,
    "max_retries": 3,
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

---

### Get Job

Get details about a specific job.

**Endpoint:** `GET /jobs/{job_id}`

**Authentication:** Required

**Parameters:**
- `job_id` (path) - Job ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "job_type": "extraction",
    "task_name": "extract_pdf",
    "status": "completed",
    "progress": 100,
    "result": "{\"statement_id\": 123}",
    "error": null,
    "retries": 0,
    "max_retries": 3,
    "started_at": "2025-12-26T10:30:05Z",
    "completed_at": "2025-12-26T10:30:50Z",
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

---

### List Jobs

List jobs with optional filtering.

**Endpoint:** `GET /jobs/`

**Authentication:** Required

**Query Parameters:**
- `status` (optional) - Filter by status (pending, running, completed, failed, cancelled)
- `type` (optional) - Filter by job type (extraction, consolidation)
- `skip` (default: 0) - Number of records to skip
- `limit` (default: 100, max: 1000) - Maximum records to return

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "job_type": "extraction",
      "task_name": "extract_pdf",
      "status": "completed",
      "progress": 100,
      "created_at": "2025-12-26T10:30:00Z"
    }
  ]
}
```

---

### Update Job

Update job status and progress (typically used by the worker).

**Endpoint:** `PATCH /jobs/{job_id}`

**Authentication:** Required

**Parameters:**
- `job_id` (path) - Job ID

**Request Body:**
```json
{
  "status": "running",
  "progress": 50
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Job updated successfully",
  "data": {
    "id": 1,
    "status": "running",
    "progress": 50
  }
}
```

---

### Cancel Job

Cancel a pending or running job.

**Endpoint:** `POST /jobs/{job_id}/cancel`

**Authentication:** Required

**Parameters:**
- `job_id` (path) - Job ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Job 1 cancelled successfully"
}
```

**Errors:**
- `400 Bad Request` - Job cannot be cancelled (already completed)

---

### Delete Job

Delete a job record.

**Endpoint:** `DELETE /jobs/{job_id}`

**Authentication:** Required

**Parameters:**
- `job_id` (path) - Job ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Job 1 deleted successfully"
}
```

---

### Get Job Statistics

Get aggregated job statistics.

**Endpoint:** `GET /jobs/stats/summary`

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "pending": 5,
    "running": 2,
    "completed": 150,
    "failed": 3,
    "cancelled": 1
  }
}
```

---

## Statement Endpoints

### Create Statement

Create a new financial statement record.

**Endpoint:** `POST /statements/`

**Authentication:** Required

**Request Body:**
```json
{
  "statement_type": "balance_sheet",
  "company_name": "Acme Corp",
  "period_start": "2024-01-01",
  "period_end": "2024-12-31",
  "fiscal_year": 2024,
  "currency": "USD",
  "extra_metadata": {}
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Statement created successfully",
  "data": {
    "id": 1,
    "statement_type": "balance_sheet",
    "company_name": "Acme Corp",
    "period_start": "2024-01-01",
    "period_end": "2024-12-31",
    "fiscal_year": 2024,
    "currency": "USD",
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

**Statement Types:**
- `balance_sheet`
- `income_statement`
- `cash_flow`
- `statement_of_changes_in_equity`

---

### Get Statement

Get a financial statement by ID.

**Endpoint:** `GET /statements/{statement_id}`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Statement ID
- `include_line_items` (query, default: false) - Include line items in response

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "statement_type": "balance_sheet",
    "company_name": "Acme Corp",
    "period_start": "2024-01-01",
    "period_end": "2024-12-31",
    "fiscal_year": 2024,
    "currency": "USD",
    "created_at": "2025-12-26T10:30:00Z",
    "line_items": [
      {
        "id": 1,
        "line_item_name": "Total Assets",
        "value": "1500000.00",
        "order": 1,
        "category": "assets",
        "indent_level": 0
      }
    ]
  }
}
```

---

### List Statements

List financial statements with optional filtering.

**Endpoint:** `GET /statements/`

**Authentication:** Required

**Query Parameters:**
- `statement_type` (optional) - Filter by statement type
- `company_name` (optional) - Filter by company name (partial match)
- `fiscal_year` (optional) - Filter by fiscal year
- `limit` (default: 100, max: 1000) - Maximum records to return
- `offset` (default: 0) - Number of records to skip

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "statement_type": "balance_sheet",
      "company_name": "Acme Corp",
      "fiscal_year": 2024
    }
  ],
  "total": 1
}
```

---

### Delete Statement

Delete a financial statement and its line items.

**Endpoint:** `DELETE /statements/{statement_id}`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Statement ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Statement 1 deleted successfully"
}
```

---

### Add Line Item

Add a line item to a financial statement.

**Endpoint:** `POST /statements/{statement_id}/line-items`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Statement ID

**Request Body:**
```json
{
  "line_item_name": "Cash and Cash Equivalents",
  "value": "250000.00",
  "order": 1,
  "category": "assets",
  "indent_level": 1,
  "parent_id": null,
  "notes": "Includes checking and savings accounts"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Line item added successfully",
  "data": {
    "id": 1,
    "statement_id": 1,
    "line_item_name": "Cash and Cash Equivalents",
    "value": "250000.00",
    "order": 1,
    "category": "assets",
    "indent_level": 1,
    "parent_id": null,
    "notes": "Includes checking and savings accounts"
  }
}
```

---

### Get Line Items

Get all line items for a statement.

**Endpoint:** `GET /statements/{statement_id}/line-items`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Statement ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "line_item_name": "Cash and Cash Equivalents",
      "value": "250000.00",
      "order": 1,
      "category": "assets",
      "indent_level": 1
    }
  ],
  "total": 1
}
```

---

### Detect Statement Type

Detect the type of financial statement from extracted text.

**Endpoint:** `POST /statements/detect-type`

**Authentication:** Required

**Query Parameters:**
- `text` (required) - Extracted text from statement

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "statement_type": "balance_sheet",
    "confidence": 0.95
  }
}
```

---

## Detection Endpoints

### Upload Document for Detection

Upload a PDF for table detection.

**Endpoint:** `POST /detection/upload`

**Authentication:** Not required

**Request:** `multipart/form-data`
- `file` - PDF file (max 10MB)

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Document uploaded successfully: statement.pdf",
  "data": {
    "id": 1,
    "filename": "statement.pdf",
    "file_path": "uploads/abc12345_statement.pdf",
    "file_size": 524288,
    "mime_type": "application/pdf",
    "status": "uploaded",
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

---

### Process Document

Process a document for table detection.

**Endpoint:** `POST /detection/documents/{document_id}/process`

**Authentication:** Not required

**Parameters:**
- `document_id` (path) - Document ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Document processed successfully. Status: completed",
  "data": {
    "id": 1,
    "filename": "statement.pdf",
    "status": "completed",
    "results": {
      "tables_found": 2,
      "confidence": 0.95
    }
  }
}
```

---

### List Documents

List all detection documents.

**Endpoint:** `GET /detection/documents`

**Authentication:** Not required

**Query Parameters:**
- `status_filter` (optional) - Filter by status
- `limit` (default: 100) - Maximum records to return
- `offset` (default: 0) - Number of records to skip

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Found 2 documents",
  "data": [
    {
      "id": 1,
      "filename": "statement1.pdf",
      "status": "completed"
    },
    {
      "id": 2,
      "filename": "statement2.pdf",
      "status": "uploaded"
    }
  ],
  "total": 2
}
```

---

### Get Document

Get a specific document with detection results.

**Endpoint:** `GET /detection/documents/{document_id}`

**Authentication:** Not required

**Parameters:**
- `document_id` (path) - Document ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Document retrieved successfully",
  "data": {
    "id": 1,
    "filename": "statement.pdf",
    "status": "completed",
    "results": {
      "tables_found": 2,
      "confidence": 0.95
    }
  }
}
```

---

### Delete Document

Delete a document and its detection results.

**Endpoint:** `DELETE /detection/documents/{document_id}`

**Authentication:** Not required

**Parameters:**
- `document_id` (path) - Document ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Document 1 deleted successfully"
}
```

---

## Consolidation Endpoints

### Create Consolidated Statement

Create a new consolidated statement combining multiple periods.

**Endpoint:** `POST /consolidation/`

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Acme Corp 2022-2024 Analysis",
  "company_name": "Acme Corp",
  "start_fiscal_year": 2022,
  "end_fiscal_year": 2024,
  "statement_ids": [1, 2, 3]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Consolidated statement created successfully",
  "data": {
    "id": 1,
    "name": "Acme Corp 2022-2024 Analysis",
    "company_name": "Acme Corp",
    "start_fiscal_year": 2022,
    "end_fiscal_year": 2024,
    "created_at": "2025-12-26T10:30:00Z"
  }
}
```

---

### Get Consolidated Statement

Get a consolidated statement by ID.

**Endpoint:** `GET /consolidation/{statement_id}`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Consolidated statement ID
- `include_comparisons` (query, default: false) - Include period comparisons

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Acme Corp 2022-2024 Analysis",
    "company_name": "Acme Corp",
    "start_fiscal_year": 2022,
    "end_fiscal_year": 2024,
    "period_comparisons": [
      {
        "id": 1,
        "period1_name": "2023",
        "period2_name": "2024",
        "variance_data": {
          "total_assets": {
            "period1": 1000000,
            "period2": 1500000,
            "variance": 500000,
            "variance_percent": 50.0
          }
        }
      }
    ]
  }
}
```

---

### List Consolidated Statements

List consolidated statements with optional filtering.

**Endpoint:** `GET /consolidation/`

**Authentication:** Required

**Query Parameters:**
- `company_name` (optional) - Filter by company name
- `skip` (default: 0) - Number of records to skip
- `limit` (default: 100, max: 1000) - Maximum records to return

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Acme Corp 2022-2024 Analysis",
      "company_name": "Acme Corp",
      "start_fiscal_year": 2022,
      "end_fiscal_year": 2024
    }
  ]
}
```

---

### Delete Consolidated Statement

Delete a consolidated statement and related comparisons.

**Endpoint:** `DELETE /consolidation/{statement_id}`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Consolidated statement ID

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Consolidated statement 1 deleted successfully"
}
```

---

### Add Period Comparison

Add a period comparison to a consolidated statement.

**Endpoint:** `POST /consolidation/{statement_id}/comparisons`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Consolidated statement ID

**Request Body:**
```json
{
  "consolidated_statement_id": 1,
  "period1_id": 1,
  "period2_id": 2,
  "period1_name": "2023",
  "period2_name": "2024",
  "variance_data": {}
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Period comparison added successfully",
  "data": {
    "id": 1,
    "period1_name": "2023",
    "period2_name": "2024"
  }
}
```

---

### Get Period Comparisons

Get all period comparisons for a consolidated statement.

**Endpoint:** `GET /consolidation/{statement_id}/comparisons`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Consolidated statement ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "period1_name": "2023",
      "period2_name": "2024"
    }
  ]
}
```

---

### Export to Excel

Export consolidated statement to Excel file.

**Endpoint:** `GET /consolidation/{statement_id}/export`

**Authentication:** Required

**Parameters:**
- `statement_id` (path) - Consolidated statement ID

**Response:** `200 OK` (Excel file download)

**Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="Acme_Corp_2022-2024_Analysis_1.xlsx"
```

---

## Health Check Endpoints

### Basic Health Check

Check if the application is running.

**Endpoint:** `GET /health`

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-12-26T10:30:00Z"
}
```

---

### Detailed Health Check

Check application health including database connectivity.

**Endpoint:** `GET /health/detailed`

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-12-26T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5.2
    },
    "worker": {
      "status": "running",
      "active_jobs": 2
    }
  }
}
```

---

## Error Codes

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for async processing
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate email)
- `413 Payload Too Large` - File upload exceeds size limit
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Common Error Responses

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Authentication Error (401):**
```json
{
  "detail": "Could not validate credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

**Not Found Error (404):**
```json
{
  "detail": "Statement 123 not found"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Future versions will include:
- 100 requests per minute per IP for unauthenticated endpoints
- 1000 requests per minute per user for authenticated endpoints
- Separate limits for file uploads (10 per hour)

---

## Pagination

List endpoints support offset-based pagination:

**Query Parameters:**
- `skip` or `offset` - Number of records to skip (default: 0)
- `limit` - Maximum number of records to return (default: 100, max: 1000)

**Example:**
```bash
# Get first page (records 0-99)
GET /statements?limit=100&offset=0

# Get second page (records 100-199)
GET /statements?limit=100&offset=100
```

---

## Webhooks

Not currently implemented. Future versions will support webhooks for:
- Job completion notifications
- Extraction completion
- Statement processing events

---

## SDKs and Client Libraries

Coming soon:
- Python SDK
- JavaScript/TypeScript SDK
- Command-line interface (CLI)

For now, use standard HTTP clients:

### Python (httpx)
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8123/auth/login",
        json={"email": "user@example.com", "password": "pass"},
    )
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(
        "http://localhost:8123/auth/me",
        headers=headers,
    )
    print(response.json())
```

### JavaScript (fetch)
```javascript
const response = await fetch('http://localhost:8123/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'pass'
  })
});

const { access_token } = await response.json();

const meResponse = await fetch('http://localhost:8123/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

const userData = await meResponse.json();
console.log(userData);
```

---

## Interactive Documentation

For interactive API exploration, visit:
- **Swagger UI**: http://localhost:8123/docs
- **ReDoc**: http://localhost:8123/redoc

Both provide:
- Try-it-out functionality
- Request/response examples
- Schema documentation
- Authentication testing
