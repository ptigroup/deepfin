# Development Environment Setup Guide

**Project:** LLM Financial Pipeline - AI-Optimized Refactoring
**Your Setup:** WSL2 on Windows | Python Installed | Learning-Focused
**Created:** 2025-12-14

---

## 🎯 Overview

This guide will help you set up your complete development environment for building a professional, portfolio-worthy financial document processing platform.

**What we're setting up:**
- ✅ WSL2 (Windows Subsystem for Linux)
- ✅ Python 3.12 with uv (modern package manager)
- ✅ Docker Desktop (for PostgreSQL and containerization)
- ✅ VS Code with essential extensions
- ✅ Git configuration
- ✅ PostgreSQL database
- ✅ Project dependencies

**Estimated time:** 1-2 hours

---

## Prerequisites Check

Before starting, verify you have:
- [x] Windows 10/11 (Build 19041 or higher)
- [x] WSL2 installed
- [x] Python installed in WSL2
- [ ] At least 20GB free disk space
- [ ] Stable internet connection

---

## Step 1: Verify WSL2 Setup (15 minutes)

### 1.1 Check WSL2 Version

Open PowerShell (Windows, not WSL) and run:

```powershell
wsl --list --verbose
```

**Expected output:**
```
NAME            STATE       VERSION
Ubuntu          Running     2
```

If VERSION shows "1", upgrade to WSL2:
```powershell
wsl --set-version Ubuntu 2
```

### 1.2 Update WSL2 Ubuntu

Open Ubuntu (from Start menu or Windows Terminal), then run:

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Verify Ubuntu version (should be 20.04 or 22.04)
lsb_release -a
```

**Why this matters:** Ensures you have latest security updates and compatible packages.

---

## Step 2: Install Development Tools (30 minutes)

### 2.1 Install Essential Build Tools

In WSL2 Ubuntu terminal:

```bash
# Install build essentials (compilers, libraries)
sudo apt install -y build-essential curl git wget

# Install Python development headers
sudo apt install -y python3-dev python3-pip python3-venv

# Verify installations
gcc --version        # Should show gcc version
git --version        # Should show git version
python3 --version    # Should show Python 3.10+
```

**What this does:**
- `build-essential`: Compilers needed for some Python packages
- `curl/wget`: Download tools for fetching packages
- `git`: Version control (critical for development)
- `python3-dev`: Headers needed to build Python extensions

### 2.2 Install uv (Modern Python Package Manager)

```bash
# Install uv (replaces pip, much faster)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH (make it available in terminal)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

**Expected output:** `uv 0.x.x`

**Why uv instead of pip?**
- ⚡ 10-100x faster than pip
- 🔒 Better dependency resolution
- 📦 Built-in virtual environment management
- 🎯 Industry standard for modern Python projects

### 2.3 Install Docker Desktop for Windows

**Important:** Docker Desktop runs on Windows but integrates with WSL2.

1. **Download Docker Desktop:**
   - Go to https://www.docker.com/products/docker-desktop/
   - Download "Docker Desktop for Windows"
   - Run the installer (Docker Desktop Installer.exe)

2. **Installation steps:**
   - ✅ Enable "Use WSL 2 instead of Hyper-V" (should be default)
   - ✅ Install
   - ⚠️ Restart Windows when prompted

3. **Configure Docker for WSL2:**
   - Open Docker Desktop (from Windows Start menu)
   - Go to Settings → Resources → WSL Integration
   - ✅ Enable "Ubuntu" (or your WSL distro)
   - Click "Apply & Restart"

4. **Verify in WSL2:**

```bash
# This should work in WSL2 Ubuntu terminal
docker --version
docker compose version

# Test Docker is working
docker run hello-world
```

**Expected output:** "Hello from Docker!" message

**What is Docker?**
- 🐳 Runs applications in isolated containers
- 💾 We'll use it for PostgreSQL database
- 📦 Makes deployment easy (same environment everywhere)
- 🎓 Essential skill for modern developers

---

## Step 3: Install VS Code and Extensions (20 minutes)

### 3.1 Install VS Code

1. Download from https://code.visualstudio.com/
2. Install on Windows (not in WSL)
3. Launch VS Code

### 3.2 Install WSL Extension

1. Open VS Code
2. Press `Ctrl+Shift+X` (Extensions panel)
3. Search "WSL"
4. Install "WSL" by Microsoft
5. Click "Reload Required" if prompted

### 3.3 Open WSL2 from VS Code

1. Press `Ctrl+Shift+P` (Command Palette)
2. Type "WSL: Connect to WSL"
3. VS Code will reopen connected to Ubuntu

**You should see:** "WSL: Ubuntu" in bottom-left corner of VS Code

### 3.4 Install Essential Extensions (in WSL)

With VS Code connected to WSL, install these extensions:

**Python Development:**
- "Python" by Microsoft
- "Pylance" by Microsoft (IntelliSense)
- "Python Test Explorer" by Little Fox Team

**Code Quality:**
- "Ruff" by Astral Software (linter/formatter)
- "Error Lens" by Alexander (inline errors)

**Docker:**
- "Docker" by Microsoft

**Utilities:**
- "GitLens" by GitKraken (advanced git features)
- "Thunder Client" by Thunder Client (API testing, like Postman)
- "PostgreSQL" by Chris Kolkman (database management)

**Theme (optional but recommended):**
- "One Dark Pro" by binaryify (nice dark theme)

**How to install extensions:**
1. Press `Ctrl+Shift+X`
2. Search extension name
3. Click "Install in WSL: Ubuntu"

---

## Step 4: Configure Git (10 minutes)

### 4.1 Set Up Git Identity

In WSL2 terminal:

```bash
# Set your name (will appear in commits)
git config --global user.name "Your Name"

# Set your email (use GitHub email if you have one)
git config --global user.email "your.email@example.com"

# Set default branch name to 'main'
git config --global init.defaultBranch main

# Verify configuration
git config --list
```

### 4.2 Generate SSH Key for GitHub (Optional but Recommended)

```bash
# Generate SSH key (press Enter for all prompts)
ssh-keygen -t ed25519 -C "your.email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub
```

**Add to GitHub:**
1. Go to https://github.com/settings/keys
2. Click "New SSH key"
3. Paste the key (starts with `ssh-ed25519`)
4. Save

**Test connection:**
```bash
ssh -T git@github.com
```

Expected: "Hi username! You've successfully authenticated..."

**Why SSH keys?**
- 🔐 More secure than passwords
- 🚀 No need to type password every push
- 🎓 Professional standard

---

## Step 5: Set Up PostgreSQL with Docker (15 minutes)

### 5.1 Create Project Directory

```bash
# Create project folder in your home directory
cd ~
mkdir llm-financial-pipeline
cd llm-financial-pipeline

# Initialize git repository
git init
```

### 5.2 Create Docker Compose File

Create a file to define PostgreSQL service:

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: llm-pipeline-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: llm_pipeline
    ports:
      - "5433:5432"  # Use 5433 to avoid conflicts
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local
EOF
```

**What this does:**
- 🐘 PostgreSQL 16 database
- 📦 Lightweight Alpine Linux image
- 💾 Persistent data storage (survives container restarts)
- 🏥 Health checks (ensure database is ready)
- 🔌 Port 5433 (so it doesn't conflict if you have other databases)

### 5.3 Start PostgreSQL

```bash
# Start database in background
docker compose up -d

# Check it's running
docker compose ps

# View logs
docker compose logs postgres
```

**Expected output:**
```
NAME                IMAGE               STATUS
llm-pipeline-db     postgres:16-alpine  Up (healthy)
```

### 5.4 Test Database Connection

```bash
# Connect to database
docker exec -it llm-pipeline-db psql -U postgres -d llm_pipeline

# You should see PostgreSQL prompt:
# llm_pipeline=#

# Run test query
SELECT version();

# Exit
\q
```

**Congratulations!** PostgreSQL is running.

**Useful commands:**
```bash
# Stop database
docker compose stop

# Start database
docker compose start

# Stop and remove (data persists in volume)
docker compose down

# Stop and remove including data (⚠️ destroys data)
docker compose down -v
```

---

## Step 6: Create .env File (5 minutes)

Create environment configuration file:

```bash
# Still in ~/llm-financial-pipeline directory
cat > .env << 'EOF'
# Application
APP_NAME=LLM Financial Pipeline
ENVIRONMENT=development
LOG_LEVEL=INFO
API_PREFIX=/api

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/llm_pipeline

# LLMWhisperer
LLMWHISPERER_API_KEY=your_api_key_here
LLMWHISPERER_BASE_URL=https://api.llmwhisperer.com

# Authentication (generate new secret key below)
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (we'll configure later)
EMAIL_ENABLED=false
EMAIL_FROM=noreply@yourapp.com

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8123

# File Upload
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_TYPES=.pdf
EOF
```

### Generate Secure SECRET_KEY

```bash
# Generate random secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** and replace `your-super-secret-key-change-this` in .env file.

**Edit .env file:**
```bash
# Open in VS Code
code .env
```

Update:
1. `LLMWHISPERER_API_KEY` → your actual API key
2. `SECRET_KEY` → the generated secret key

Save and close.

---

## Step 7: Install Python Dependencies (10 minutes)

### 7.1 Create pyproject.toml

This file defines project dependencies.

```bash
cat > pyproject.toml << 'EOF'
[project]
name = "llm-financial-pipeline"
version = "2.0.0"
description = "AI-Optimized Financial Document Processing Platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.27",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "structlog>=24.1.0",
    "python-dotenv>=1.0.0",
    "python-multipart>=0.0.9",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "aiofiles>=23.2.0",
    "openpyxl>=3.1.0",
    "pandas>=2.2.0",
    "pymupdf>=1.23.0",
    "unstract-llmwhisperer>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pyright>=1.1.350",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.26.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ANN", "S", "RUF"]
ignore = ["ANN101", "ANN102", "S311"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["app", "tests"]
markers = [
    "integration: marks tests requiring real database",
]
EOF
```

### 7.2 Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# This creates .venv and installs everything
# Takes 1-2 minutes
```

### 7.3 Activate Virtual Environment

```bash
# Activate environment
source .venv/bin/activate

# You should see (.venv) in your prompt

# Verify installations
python --version  # Should be 3.12.x
fastapi --version
pytest --version
```

**What is a virtual environment?**
- 📦 Isolated Python packages for this project
- 🔒 Doesn't affect other Python projects
- 🎯 Ensures everyone uses same package versions

**Always activate before working:**
```bash
cd ~/llm-financial-pipeline
source .venv/bin/activate
```

---

## Step 8: Verify Everything Works (10 minutes)

### 8.1 Create Test Script

```bash
cat > test_setup.py << 'EOF'
"""Test script to verify all dependencies are installed correctly."""

import sys


def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")

    packages = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "structlog",
        "pytest",
        "pandas",
        "openpyxl",
    ]

    failed = []
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError as e:
            print(f"  ✗ {package}: {e}")
            failed.append(package)

    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False

    print("\n✅ All imports successful!")
    return True


def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine

        async def check_db():
            engine = create_async_engine(
                "postgresql+asyncpg://postgres:postgres@localhost:5433/llm_pipeline"
            )
            async with engine.connect() as conn:
                result = await conn.execute("SELECT 1")
                return result.scalar()

        result = asyncio.run(check_db())
        if result == 1:
            print("  ✓ Database connection successful")
            return True
        else:
            print("  ✗ Unexpected database response")
            return False

    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False


def test_environment():
    """Test environment configuration."""
    print("\nTesting environment...")

    try:
        from dotenv import load_dotenv
        import os

        load_dotenv()

        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "LLMWHISPERER_API_KEY",
        ]

        missing = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith("your"):
                missing.append(var)
                print(f"  ✗ {var}: not set or placeholder")
            else:
                print(f"  ✓ {var}: configured")

        if missing:
            print(f"\n⚠️  Please update these variables in .env: {', '.join(missing)}")
            return False

        print("\n✅ Environment configured!")
        return True

    except Exception as e:
        print(f"  ✗ Environment check failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LLM Financial Pipeline - Setup Verification")
    print("=" * 60)

    results = []
    results.append(test_imports())
    results.append(test_database_connection())
    results.append(test_environment())

    print("\n" + "=" * 60)
    if all(results):
        print("🎉 Setup complete! You're ready to start development.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("=" * 60)
        sys.exit(1)
EOF
```

### 8.2 Run Test Script

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run test
python test_setup.py
```

**Expected output:**
```
============================================================
LLM Financial Pipeline - Setup Verification
============================================================
Testing imports...
  ✓ fastapi
  ✓ sqlalchemy
  ✓ pydantic
  ✓ structlog
  ✓ pytest
  ✓ pandas
  ✓ openpyxl

✅ All imports successful!

Testing database connection...
  ✓ Database connection successful

Testing environment...
  ✓ DATABASE_URL: configured
  ✓ SECRET_KEY: configured
  ✓ LLMWHISPERER_API_KEY: configured

✅ Environment configured!

============================================================
🎉 Setup complete! You're ready to start development.
============================================================
```

---

## Step 9: VS Code Workspace Configuration (5 minutes)

### 9.1 Create Workspace Settings

```bash
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
  // Python
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,

  // Formatting
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },

  // Ruff (linter + formatter)
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },

  // Type checking
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.diagnosticMode": "workspace",

  // Testing
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["-v"],

  // Editor
  "editor.rulers": [100],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,

  // Exclude from file explorer
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".mypy_cache": true,
    ".ruff_cache": true
  }
}
EOF
```

### 9.2 Create Launch Configuration (for debugging)

```bash
cat > .vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Run Application",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8123"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Pytest: Current File",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${file}",
        "-v"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
EOF
```

### 9.3 Reload VS Code

Press `Ctrl+Shift+P` → "Developer: Reload Window"

---

## Troubleshooting Common Issues

### Docker not working in WSL

**Symptom:** `docker: command not found`

**Fix:**
1. Check Docker Desktop is running (Windows system tray)
2. Settings → Resources → WSL Integration → Enable Ubuntu
3. Restart WSL: `wsl --shutdown` in PowerShell, then reopen

### Port 5433 already in use

**Symptom:** `Error: port is already allocated`

**Fix:**
```bash
# Find what's using port 5433
sudo lsof -i :5433

# Or change port in docker-compose.yml
# Change "5433:5432" to "5434:5432"
```

### Python version issues

**Symptom:** `requires-python >=3.12` error

**Fix:**
```bash
# Install Python 3.12 via deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Use with uv
uv python install 3.12
```

### uv command not found

**Symptom:** `uv: command not found`

**Fix:**
```bash
# Ensure .bashrc is sourced
source ~/.bashrc

# Or add manually
export PATH="$HOME/.cargo/bin:$PATH"
```

---

## Next Steps

✅ **You're all set!** Your development environment is ready.

**What to do next:**

1. **Review the REFACTORING_PLAN.md** to understand the project structure
2. **Wait for me to start Phase 1** - I'll create the foundation infrastructure with detailed explanations
3. **Study each file I create** - Read comments, ask questions
4. **Run tests regularly** - Use `pytest -v` to verify everything works

**Useful daily commands:**

```bash
# Start your dev session
cd ~/llm-financial-pipeline
source .venv/bin/activate
docker compose up -d  # Start database

# Run application (once we build it)
uvicorn app.main:app --reload --port 8123

# Run tests
pytest -v

# Check code quality
ruff check .
mypy app/
pyright app/

# End session
docker compose stop  # Stop database
deactivate  # Exit virtual environment
```

---

## Cheat Sheet

### Essential Commands

| Task | Command |
|------|---------|
| Activate environment | `source .venv/bin/activate` |
| Start database | `docker compose up -d` |
| Stop database | `docker compose stop` |
| Run tests | `pytest -v` |
| Format code | `ruff format .` |
| Check linting | `ruff check .` |
| Type checking | `mypy app/` |
| Git status | `git status` |
| Git commit | `git add . && git commit -m "message"` |

### VS Code Shortcuts

| Action | Shortcut |
|--------|----------|
| Command palette | `Ctrl+Shift+P` |
| Terminal | `Ctrl+` ` |
| File search | `Ctrl+P` |
| Code search | `Ctrl+Shift+F` |
| Run file | `F5` |
| Format document | `Shift+Alt+F` |

---

**Questions?** Ask anytime! I'm here to help.

**Ready to start building?** Let me know when you've completed this setup!
