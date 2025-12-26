# LLM Financial Document Processing Pipeline

A production-ready FastAPI application for automated financial document processing using LLMWhisperer and OpenAI. The system extracts, analyzes, and consolidates financial data from PDF statements with high accuracy.

## Overview

This application provides a complete pipeline for processing financial documents:
- **PDF Extraction**: Uses LLMWhisperer to extract structured text from financial PDFs
- **Document Detection**: Automatically identifies statement types (income statement, balance sheet, cash flow, etc.)
- **Direct Parsing**: Processes raw text with 100% accuracy, bypassing LLM interpretation for table data
- **Background Processing**: Async job queue for handling large documents
- **Multi-Period Analysis**: Consolidates data across multiple reporting periods
- **Excel Export**: Generates formatted spreadsheets with visual hierarchy
- **RESTful API**: Complete REST API with authentication and authorization

## Features

- **Automated Extraction**: Upload PDFs and get structured JSON + Excel output
- **Universal Document Support**: Handles any financial table format
- **High Accuracy**: Direct parsing ensures 100% data accuracy
- **Async Processing**: Background job queue with retry logic
- **Authentication**: JWT-based auth with role-based access control
- **Email Notifications**: Optional email alerts for job completion
- **Comprehensive Testing**: Unit and integration tests with 42%+ coverage
- **Type Safety**: Full type hints with strict MyPy checking
- **Structured Logging**: JSON logs with request IDs for observability
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Technology Stack

### Core Framework
- **FastAPI** 0.115+ - Modern async web framework
- **Python** 3.12+ - Latest Python with enhanced type hints
- **Pydantic** 2.10+ - Data validation and settings management
- **Uvicorn** - ASGI server with auto-reload

### Database
- **PostgreSQL** 14+ - Primary data store
- **SQLAlchemy** 2.0+ - Async ORM
- **Asyncpg** - High-performance async PostgreSQL driver
- **Alembic** - Database migrations

### Document Processing
- **LLMWhisperer** (Unstract SDK) - PDF text extraction
- **OpenAI** API - LLM integration (optional)
- **PyMuPDF** - PDF manipulation
- **OpenPyXL** - Excel file generation

### Development Tools
- **Pytest** - Testing framework with async support
- **MyPy** - Static type checker
- **Ruff** - Fast Python linter and formatter
- **Structlog** - Structured logging

## Prerequisites

- **Python 3.12+** (required for latest type hints)
- **PostgreSQL 14+** (database server)
- **uv** (recommended) or pip for package management
- **LLMWhisperer API key** - Get from [Unstract](https://unstract.com/llmwhisperer/)
- **OpenAI API key** (optional) - For LLM features

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd LLM-1
```

### 2. Install Dependencies

#### Using uv (recommended):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

#### Using pip:
```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
createdb llm_pipeline

# Or using psql:
psql -U postgres -c "CREATE DATABASE llm_pipeline;"
```

### 4. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```ini
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/llm_pipeline

# LLMWhisperer API
LLMWHISPERER_API_KEY=your_llmwhisperer_api_key_here

# Security (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your_secure_random_secret_key_here

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Optional: Email Configuration
EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 5. Run Database Migrations

```bash
# Apply migrations
uv run alembic upgrade head
```

## Running the Application

### Development Server

```bash
# Using uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123

# Or using python
python -m app.main
```

The application will be available at:
- **API**: http://localhost:8123
- **Swagger UI**: http://localhost:8123/docs
- **ReDoc**: http://localhost:8123/redoc
- **Health Check**: http://localhost:8123/health

### Production Deployment

```bash
# Run with multiple workers
uv run uvicorn app.main:app --host 0.0.0.0 --port 8123 --workers 4

# Or using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8123
```

## Quick Start

### 1. Register a User

```bash
curl -X POST http://localhost:8123/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "username": "johndoe"
  }'
```

### 2. Login to Get Token

```bash
curl -X POST http://localhost:8123/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Upload a PDF for Extraction

```bash
curl -X POST http://localhost:8123/extraction/extract \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@financial_statement.pdf"
```

Response:
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

### 4. Check Job Status

```bash
curl -X GET http://localhost:8123/jobs/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Get Extracted Data

```bash
curl -X GET http://localhost:8123/extraction/jobs/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing

### Run All Tests

```bash
# Run all tests with coverage
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=html --cov-report=term

# Run only unit tests
uv run pytest -m "not integration"

# Run only integration tests
uv run pytest -m integration
```

### Run Specific Tests

```bash
# Test specific module
uv run pytest app/auth/tests/

# Test specific file
uv run pytest app/auth/tests/test_service.py

# Test specific function
uv run pytest app/auth/tests/test_service.py::test_create_user
```

### Type Checking

```bash
# Run MyPy type checker
uv run mypy app
```

### Linting and Formatting

```bash
# Check code style
uv run ruff check app

# Format code
uv run ruff format app

# Auto-fix issues
uv run ruff check --fix app
```

## Project Structure

```
LLM-1/
├── app/                          # Application code
│   ├── auth/                     # Authentication & authorization
│   │   ├── dependencies.py       # Auth dependencies (get_current_user)
│   │   ├── models.py             # User model
│   │   ├── routes.py             # Auth endpoints (/register, /login)
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── service.py            # Auth business logic
│   │   └── tests/                # Auth tests
│   ├── consolidation/            # Multi-period consolidation
│   │   ├── exporter.py           # Excel export logic
│   │   ├── models.py             # Consolidation models
│   │   ├── routes.py             # Consolidation endpoints
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── service.py            # Consolidation logic
│   │   └── tests/                # Consolidation tests
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Application settings
│   │   ├── database.py           # Database connection
│   │   ├── exceptions.py         # Exception handlers
│   │   ├── health.py             # Health check endpoints
│   │   ├── logging.py            # Structured logging
│   │   ├── middleware.py         # Custom middleware
│   │   └── tests/                # Core tests
│   ├── detection/                # Document type detection
│   │   ├── detector.py           # Detection logic
│   │   ├── models.py             # Detection models
│   │   ├── routes.py             # Detection endpoints
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── service.py            # Detection service
│   │   └── tests/                # Detection tests
│   ├── extraction/               # PDF extraction & parsing
│   │   ├── models.py             # Extraction models
│   │   ├── parser.py             # Direct parsing logic
│   │   ├── routes.py             # Extraction endpoints
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── service.py            # Extraction service
│   │   └── tests/                # Extraction tests
│   ├── jobs/                     # Background job processing
│   │   ├── models.py             # Job models
│   │   ├── routes.py             # Job endpoints
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── service.py            # Job service
│   │   ├── tasks.py              # Task definitions
│   │   ├── worker.py             # Background worker
│   │   └── tests/                # Job tests
│   ├── llm/                      # LLM clients & caching
│   │   ├── cache.py              # Response caching
│   │   ├── clients.py            # LLM client wrappers
│   │   ├── schemas.py            # Pydantic schemas
│   │   └── tests/                # LLM tests
│   ├── notifications/            # Email notifications
│   │   ├── notifications.py      # Email templates
│   │   ├── service.py            # Notification service
│   │   └── tests/                # Notification tests
│   ├── shared/                   # Shared models & schemas
│   │   ├── models.py             # Base models
│   │   ├── schemas.py            # Base schemas
│   │   └── tests/                # Shared tests
│   ├── statements/               # Financial statements
│   │   ├── models.py             # Statement models
│   │   ├── routes.py             # Statement endpoints
│   │   ├── schemas.py            # Pydantic schemas
│   │   ├── service.py            # Statement service
│   │   └── tests/                # Statement tests
│   └── main.py                   # FastAPI application entry point
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   └── env.py                    # Alembic configuration
├── tests/                        # Integration tests
│   ├── conftest.py               # Shared test fixtures
│   └── integration/              # Integration test suites
├── .env.example                  # Example environment configuration
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project dependencies & config
└── README.md                     # This file
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8123/docs - Interactive API documentation
- **ReDoc**: http://localhost:8123/redoc - Alternative documentation view

For detailed API documentation, see [API.md](API.md).

## Architecture

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

Key architectural patterns:
- **Async-first**: All I/O operations use async/await
- **Service Layer**: Business logic separated from routes
- **Repository Pattern**: Data access abstracted in service layer
- **Dependency Injection**: FastAPI dependencies for database, auth, etc.
- **Background Jobs**: Long-running tasks processed asynchronously
- **Structured Logging**: JSON logs with request IDs and context

## Configuration

The application uses Pydantic Settings for configuration management. All settings can be configured via:
1. `.env` file (recommended for local development)
2. Environment variables (recommended for production)
3. Default values (defined in `app/core/config.py`)

Key configuration sections:
- **Application**: App name, environment, debug mode, log level
- **Database**: Connection URL, pool size, echo SQL
- **Security**: JWT secret, algorithm, token expiration
- **LLMWhisperer**: API key, base URL, timeout
- **Email**: SMTP configuration for notifications
- **File Upload**: Max size, allowed types, upload directory
- **CORS**: Allowed origins for cross-origin requests

See `.env.example` for all available configuration options.

## Database Migrations

### Create a New Migration

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Add new table"

# Create empty migration
uv run alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
uv run alembic upgrade head

# Upgrade to specific revision
uv run alembic upgrade abc123

# Downgrade one revision
uv run alembic downgrade -1

# Show current revision
uv run alembic current

# Show migration history
uv run alembic history
```

## Monitoring and Observability

### Health Checks

- **Basic Health**: `GET /health` - Returns 200 if app is running
- **Detailed Health**: `GET /health/detailed` - Includes database connectivity

### Logging

The application uses structured logging with JSON output:
```json
{
  "timestamp": "2025-12-26T10:30:00Z",
  "level": "info",
  "message": "User registered successfully",
  "request_id": "abc-123-def-456",
  "user_id": 1,
  "email": "user@example.com"
}
```

Logs include:
- Request/response logging with timing
- Database query logging (when `DATABASE_ECHO=true`)
- Error logging with stack traces
- Business event logging (user actions, job status changes)

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection manually
psql -U postgres -d llm_pipeline -c "SELECT 1;"

# Verify DATABASE_URL format
# Should be: postgresql+asyncpg://user:password@host:port/database
```

### Migration Issues

```bash
# Reset database (WARNING: destroys all data)
uv run alembic downgrade base
uv run alembic upgrade head

# Check current migration state
uv run alembic current
uv run alembic history
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall

# Or with pip
pip install -e ".[dev]" --force-reinstall
```

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes with tests
3. Run tests and linting: `pytest && mypy app && ruff check app`
4. Commit your changes: `git commit -m "Add my feature"`
5. Push to the branch: `git push origin feature/my-feature`
6. Create a Pull Request

### Code Standards

- Write type hints for all functions
- Add docstrings to all public functions and classes
- Maintain test coverage above 40%
- Follow PEP 8 style (enforced by Ruff)
- Use async/await for all I/O operations
- Add integration tests for new endpoints

## License

[Add your license here]

## Support

For questions or issues:
- Open an issue on GitHub
- Check existing documentation
- Review API docs at `/docs`

## Acknowledgments

- **LLMWhisperer** (Unstract) - PDF extraction
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM
